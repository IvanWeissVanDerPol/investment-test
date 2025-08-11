"""
Monitoring and metrics collection system for performance tracking.
"""

import time
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass, field
from collections import defaultdict, deque
import asyncio

from investment_system.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    method: str
    path: str
    status_code: int
    duration_ms: float
    timestamp: datetime
    user_id: Optional[str] = None
    error_type: Optional[str] = None
    correlation_id: Optional[str] = None


@dataclass
class SystemMetrics:
    """System-wide metrics."""
    request_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    avg_response_time_ms: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    uptime_seconds: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class EndpointMetrics:
    """Metrics for a specific endpoint."""
    path: str
    method: str
    request_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    p95_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0
    recent_durations: deque = field(default_factory=lambda: deque(maxlen=1000))


class MetricsCollector:
    """Collects and aggregates application metrics."""
    
    def __init__(self, max_requests_history: int = 10000):
        self.start_time = datetime.now(timezone.utc)
        self.max_requests_history = max_requests_history
        
        # Request history (circular buffer)
        self.request_history: deque = deque(maxlen=max_requests_history)
        
        # Endpoint-specific metrics
        self.endpoint_metrics: Dict[str, EndpointMetrics] = {}
        
        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        
        # Custom metrics
        self.custom_metrics: Dict[str, Any] = {}
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def record_request(self, metrics: RequestMetrics) -> None:
        """Record metrics for a completed request."""
        self.request_history.append(metrics)
        
        # Update endpoint metrics
        endpoint_key = f"{metrics.method}:{metrics.path}"
        if endpoint_key not in self.endpoint_metrics:
            self.endpoint_metrics[endpoint_key] = EndpointMetrics(
                path=metrics.path,
                method=metrics.method
            )
        
        endpoint = self.endpoint_metrics[endpoint_key]
        endpoint.request_count += 1
        endpoint.total_duration_ms += metrics.duration_ms
        endpoint.recent_durations.append(metrics.duration_ms)
        
        # Update min/max
        endpoint.min_duration_ms = min(endpoint.min_duration_ms, metrics.duration_ms)
        endpoint.max_duration_ms = max(endpoint.max_duration_ms, metrics.duration_ms)
        
        # Update average
        endpoint.avg_duration_ms = endpoint.total_duration_ms / endpoint.request_count
        
        # Update percentiles
        if endpoint.recent_durations:
            sorted_durations = sorted(endpoint.recent_durations)
            length = len(sorted_durations)
            endpoint.p95_duration_ms = sorted_durations[int(length * 0.95)]
            endpoint.p99_duration_ms = sorted_durations[int(length * 0.99)]
        
        # Count errors
        if metrics.status_code >= 400:
            endpoint.error_count += 1
            if metrics.error_type:
                self.error_counts[metrics.error_type] += 1
        
        logger.debug(
            "Request metrics recorded",
            endpoint=endpoint_key,
            duration_ms=metrics.duration_ms,
            status_code=metrics.status_code
        )
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system-wide metrics."""
        if not self.request_history:
            return SystemMetrics()
        
        total_requests = len(self.request_history)
        error_requests = sum(1 for r in self.request_history if r.status_code >= 400)
        total_duration = sum(r.duration_ms for r in self.request_history)
        
        # Calculate uptime
        uptime_seconds = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        # Calculate requests per second (last minute)
        now = datetime.now(timezone.utc)
        recent_requests = [
            r for r in self.request_history
            if (now - r.timestamp).total_seconds() <= 60
        ]
        requests_per_second = len(recent_requests) / 60 if recent_requests else 0
        
        return SystemMetrics(
            request_count=total_requests,
            error_count=error_requests,
            total_duration_ms=total_duration,
            avg_response_time_ms=total_duration / total_requests if total_requests > 0 else 0,
            requests_per_second=requests_per_second,
            error_rate=error_requests / total_requests if total_requests > 0 else 0,
            uptime_seconds=uptime_seconds
        )
    
    def get_endpoint_metrics(self, limit: int = 50) -> List[EndpointMetrics]:
        """Get metrics for all endpoints, sorted by request count."""
        return sorted(
            self.endpoint_metrics.values(),
            key=lambda x: x.request_count,
            reverse=True
        )[:limit]
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors."""
        total_errors = sum(self.error_counts.values())
        return {
            "total_errors": total_errors,
            "error_types": dict(self.error_counts),
            "top_errors": sorted(
                self.error_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
    
    def set_custom_metric(self, name: str, value: Any) -> None:
        """Set a custom metric value."""
        self.custom_metrics[name] = {
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def increment_counter(self, name: str, amount: int = 1) -> None:
        """Increment a counter metric."""
        if name not in self.custom_metrics:
            self.custom_metrics[name] = {"value": 0, "timestamp": datetime.now(timezone.utc).isoformat()}
        self.custom_metrics[name]["value"] += amount
        self.custom_metrics[name]["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of the system."""
        system_metrics = self.get_system_metrics()
        
        # Determine health based on metrics
        health_status = "healthy"
        issues = []
        
        # Check error rate
        if system_metrics.error_rate > 0.05:  # 5% error rate threshold
            health_status = "degraded"
            issues.append(f"High error rate: {system_metrics.error_rate:.2%}")
        
        # Check average response time
        if system_metrics.avg_response_time_ms > 1000:  # 1 second threshold
            health_status = "degraded"
            issues.append(f"High response time: {system_metrics.avg_response_time_ms:.0f}ms")
        
        # Check if system is overloaded
        if system_metrics.requests_per_second > 100:  # Adjust based on capacity
            health_status = "warning"
            issues.append(f"High load: {system_metrics.requests_per_second:.1f} req/s")
        
        return {
            "status": health_status,
            "issues": issues,
            "metrics": system_metrics,
            "uptime_seconds": system_metrics.uptime_seconds,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def start_background_tasks(self) -> None:
        """Start background monitoring tasks."""
        self._cleanup_task = asyncio.create_task(self._cleanup_old_data())
        logger.info("Background monitoring tasks started")
    
    async def stop_background_tasks(self) -> None:
        """Stop background monitoring tasks."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        logger.info("Background monitoring tasks stopped")
    
    async def _cleanup_old_data(self) -> None:
        """Background task to clean up old metrics data."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up old request history (older than 1 hour)
                cutoff_time = datetime.now(timezone.utc).timestamp() - 3600
                self.request_history = deque(
                    (r for r in self.request_history 
                     if r.timestamp.timestamp() > cutoff_time),
                    maxlen=self.max_requests_history
                )
                
                logger.debug("Old metrics data cleaned up")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Error in metrics cleanup task", error=str(e))


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def setup_monitoring(settings) -> MetricsCollector:
    """Set up the monitoring system."""
    global _metrics_collector
    
    _metrics_collector = MetricsCollector(
        max_requests_history=getattr(settings, 'metrics_history_size', 10000)
    )
    
    logger.info("Monitoring system initialized")
    return _metrics_collector


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance."""
    if _metrics_collector is None:
        raise RuntimeError("Monitoring system not initialized. Call setup_monitoring() first.")
    return _metrics_collector


async def track_request(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    user_id: Optional[str] = None,
    error_type: Optional[str] = None,
    correlation_id: Optional[str] = None
) -> None:
    """Track a completed request."""
    try:
        collector = get_metrics_collector()
        metrics = RequestMetrics(
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=duration_ms,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            error_type=error_type,
            correlation_id=correlation_id
        )
        collector.record_request(metrics)
    except Exception as e:
        logger.error("Failed to track request metrics", error=str(e))


def track_custom_metric(name: str, value: Any) -> None:
    """Track a custom metric."""
    try:
        collector = get_metrics_collector()
        collector.set_custom_metric(name, value)
    except Exception as e:
        logger.error("Failed to track custom metric", metric=name, error=str(e))


def increment_counter(name: str, amount: int = 1) -> None:
    """Increment a counter metric."""
    try:
        collector = get_metrics_collector()
        collector.increment_counter(name, amount)
    except Exception as e:
        logger.error("Failed to increment counter", counter=name, error=str(e))


class MetricsContext:
    """Context manager for timing operations."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration_ms = (time.time() - self.start_time) * 1000
            track_custom_metric(f"{self.name}_duration_ms", duration_ms)
            
            if exc_type:
                increment_counter(f"{self.name}_errors")
            else:
                increment_counter(f"{self.name}_success")


def time_operation(name: str):
    """Decorator to time function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with MetricsContext(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator


async def async_time_operation(name: str):
    """Decorator to time async function execution."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            with MetricsContext(name):
                return await func(*args, **kwargs)
        return wrapper
    return decorator
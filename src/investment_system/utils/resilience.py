"""
Resilience utilities for error recovery and monitoring.
Provides retry logic, circuit breakers, and health checks.
"""

import asyncio
import time
from typing import Callable, Any, Optional, Dict, List
from functools import wraps
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreaker:
    """
    Circuit breaker pattern for fault tolerance.
    Prevents cascading failures by stopping calls to failing services.
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: type = Exception
    ):
        """
        Initialize circuit breaker.
        
        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before attempting recovery
            expected_exception: Exception type to catch
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function through circuit breaker.
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self.last_failure_time is None:
            return False
        
        return (datetime.now() - self.last_failure_time).seconds >= self.recovery_timeout
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


def retry_with_backoff(
    retries: int = 3,
    backoff_in_seconds: float = 1.0,
    exponential: bool = True,
    exceptions: tuple = (Exception,)
):
    """
    Decorator for retrying functions with exponential backoff.
    
    Args:
        retries: Maximum number of retry attempts
        backoff_in_seconds: Initial backoff time
        exponential: Use exponential backoff if True
        exceptions: Tuple of exceptions to catch
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            x = backoff_in_seconds
            attempt = 0
            
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= retries:
                        logger.error(f"Max retries ({retries}) exceeded for {func.__name__}")
                        raise e
                    
                    logger.warning(f"Retry {attempt}/{retries} for {func.__name__} after {x}s")
                    time.sleep(x)
                    
                    if exponential:
                        x *= 2  # Exponential backoff
            
            return None
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            x = backoff_in_seconds
            attempt = 0
            
            while attempt < retries:
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= retries:
                        logger.error(f"Max retries ({retries}) exceeded for {func.__name__}")
                        raise e
                    
                    logger.warning(f"Retry {attempt}/{retries} for {func.__name__} after {x}s")
                    await asyncio.sleep(x)
                    
                    if exponential:
                        x *= 2
            
            return None
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


class HealthCheck:
    """
    Health check system for monitoring service health.
    """
    
    def __init__(self):
        self.checks: Dict[str, Callable] = {}
        self.results: Dict[str, Dict[str, Any]] = {}
    
    def register_check(self, name: str, check_func: Callable) -> None:
        """
        Register a health check.
        
        Args:
            name: Name of the check
            check_func: Function that returns True if healthy
        """
        self.checks[name] = check_func
    
    async def run_checks(self) -> Dict[str, Any]:
        """
        Run all registered health checks.
        
        Returns:
            Health check results
        """
        overall_healthy = True
        checks_results = {}
        
        for name, check_func in self.checks.items():
            try:
                start_time = time.time()
                
                # Run check (support both sync and async)
                if asyncio.iscoroutinefunction(check_func):
                    result = await check_func()
                else:
                    result = check_func()
                
                duration_ms = (time.time() - start_time) * 1000
                
                checks_results[name] = {
                    "healthy": result,
                    "duration_ms": round(duration_ms, 2),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                if not result:
                    overall_healthy = False
                    
            except Exception as e:
                checks_results[name] = {
                    "healthy": False,
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
                overall_healthy = False
        
        self.results = {
            "status": "healthy" if overall_healthy else "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "checks": checks_results
        }
        
        return self.results
    
    def get_status(self) -> Dict[str, Any]:
        """Get last health check results."""
        return self.results


# Global health check instance
health_check = HealthCheck()


# Pre-configured circuit breakers for critical services
circuit_breakers = {
    "database": CircuitBreaker(failure_threshold=3, recovery_timeout=30),
    "redis": CircuitBreaker(failure_threshold=5, recovery_timeout=20),
    "market_data": CircuitBreaker(failure_threshold=10, recovery_timeout=60),
    "stripe": CircuitBreaker(failure_threshold=3, recovery_timeout=120),
}


def with_circuit_breaker(service_name: str):
    """
    Decorator to apply circuit breaker to a function.
    
    Args:
        service_name: Name of the service (must be in circuit_breakers dict)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            breaker = circuit_breakers.get(service_name)
            if not breaker:
                return func(*args, **kwargs)
            
            return breaker.call(func, *args, **kwargs)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            breaker = circuit_breakers.get(service_name)
            if not breaker:
                return await func(*args, **kwargs)
            
            # For async, we need to wrap in sync call
            def sync_call():
                return asyncio.run(func(*args, **kwargs))
            
            return breaker.call(sync_call)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


# Error recovery strategies
class RecoveryStrategy:
    """Base class for error recovery strategies."""
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        """Attempt to recover from error."""
        raise NotImplementedError


class FallbackRecovery(RecoveryStrategy):
    """Fallback to default value on error."""
    
    def __init__(self, fallback_value: Any):
        self.fallback_value = fallback_value
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        logger.warning(f"Using fallback value due to error: {error}")
        return self.fallback_value


class CacheRecovery(RecoveryStrategy):
    """Recover using cached value."""
    
    def __init__(self, cache_client):
        self.cache = cache_client
    
    def recover(self, error: Exception, context: Dict[str, Any]) -> Any:
        cache_key = context.get("cache_key")
        if cache_key:
            cached_value = self.cache.get(cache_key)
            if cached_value:
                logger.warning(f"Using cached value due to error: {error}")
                return cached_value
        
        raise error  # Re-raise if no cache available


def with_recovery(strategy: RecoveryStrategy, **context):
    """
    Decorator to apply recovery strategy on error.
    
    Args:
        strategy: Recovery strategy to use
        **context: Context for recovery
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                return strategy.recover(e, context)
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                return strategy.recover(e, context)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator
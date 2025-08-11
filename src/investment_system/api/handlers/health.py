"""
Health monitoring endpoint with comprehensive checks.
"""

from typing import Dict, Any
from datetime import datetime
from fastapi import HTTPException
import psutil
import logging

from investment_system.utils.resilience import health_check
from investment_system.cache import get_cache

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitors system health and dependencies."""
    
    def __init__(self):
        self._register_checks()
    
    def _register_checks(self):
        """Register all health checks."""
        
        # Database check
        health_check.register_check("database", self._check_database)
        
        # Redis check
        health_check.register_check("redis", self._check_redis)
        
        # API check
        health_check.register_check("api", self._check_api)
        
        # Disk space check
        health_check.register_check("disk", self._check_disk_space)
        
        # Memory check
        health_check.register_check("memory", self._check_memory)
    
    async def _check_database(self) -> bool:
        """Check database connectivity."""
        try:
            from investment_system.infrastructure.database import get_session
            
            # Try to execute a simple query
            async with get_session() as session:
                result = await session.execute("SELECT 1")
                return result.scalar() == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    async def _check_redis(self) -> bool:
        """Check Redis connectivity."""
        try:
            cache = get_cache()
            
            # Try to set and get a test key
            test_key = "health:check"
            cache.set(test_key, "ok", ttl=10)
            result = cache.get(test_key)
            cache.delete(test_key)
            
            return result == "ok"
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def _check_api(self) -> bool:
        """Check API responsiveness."""
        try:
            # Check if core modules are importable
            from investment_system.api.router import EndpointCatalog
            from investment_system.core.contracts import User
            
            # Verify endpoint catalog
            catalog = EndpointCatalog()
            endpoints = catalog.get_all_endpoints()
            
            return len(endpoints) > 0
        except Exception as e:
            logger.error(f"API health check failed: {e}")
            return False
    
    async def _check_disk_space(self) -> bool:
        """Check available disk space."""
        try:
            disk = psutil.disk_usage("/")
            # Alert if less than 10% free
            return disk.percent < 90
        except Exception as e:
            logger.error(f"Disk space check failed: {e}")
            return True  # Don't fail health check on monitoring error
    
    async def _check_memory(self) -> bool:
        """Check available memory."""
        try:
            memory = psutil.virtual_memory()
            # Alert if less than 10% free
            return memory.percent < 90
        except Exception as e:
            logger.error(f"Memory check failed: {e}")
            return True  # Don't fail health check on monitoring error
    
    async def get_health_status(self, detailed: bool = False) -> Dict[str, Any]:
        """
        Get comprehensive health status.
        
        Args:
            detailed: Include detailed metrics
            
        Returns:
            Health status dictionary
        """
        # Run all health checks
        results = await health_check.run_checks()
        
        # Add system metrics if detailed
        if detailed:
            try:
                cpu = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage("/")
                
                results["metrics"] = {
                    "cpu_percent": cpu,
                    "memory_percent": memory.percent,
                    "memory_available_mb": memory.available / (1024 * 1024),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024 * 1024 * 1024)
                }
                
                # Add cache metrics
                cache_stats = get_cache().get_stats()
                results["cache"] = cache_stats
                
            except Exception as e:
                logger.error(f"Failed to collect system metrics: {e}")
                results["metrics"] = {"error": str(e)}
        
        # Add version info
        results["version"] = {
            "api": "1.0.0",
            "deployment": "dev"
        }
        
        return results
    
    async def get_readiness(self) -> Dict[str, Any]:
        """
        Check if service is ready to handle requests.
        
        Returns:
            Readiness status
        """
        # Quick checks only
        checks = {
            "database": await self._check_database(),
            "api": await self._check_api()
        }
        
        ready = all(checks.values())
        
        return {
            "ready": ready,
            "checks": checks,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_liveness(self) -> Dict[str, Any]:
        """
        Check if service is alive (basic check).
        
        Returns:
            Liveness status
        """
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat()
        }


# Global monitor instance
_health_monitor: HealthMonitor = None


def get_health_monitor() -> HealthMonitor:
    """Get global health monitor instance."""
    global _health_monitor
    if _health_monitor is None:
        _health_monitor = HealthMonitor()
    return _health_monitor


# FastAPI endpoints
from fastapi import APIRouter

health_router = APIRouter(prefix="/health", tags=["health"])


@health_router.get("/")
async def health_check_endpoint(detailed: bool = False):
    """Comprehensive health check endpoint."""
    monitor = get_health_monitor()
    status = await monitor.get_health_status(detailed=detailed)
    
    # Return 503 if unhealthy
    if status.get("status") != "healthy":
        raise HTTPException(status_code=503, detail=status)
    
    return status


@health_router.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe endpoint."""
    monitor = get_health_monitor()
    status = await monitor.get_readiness()
    
    if not status["ready"]:
        raise HTTPException(status_code=503, detail=status)
    
    return status


@health_router.get("/live")
async def liveness_check():
    """Kubernetes liveness probe endpoint."""
    monitor = get_health_monitor()
    return await monitor.get_liveness()
"""
Enterprise-grade rate limiting with DDoS protection.
Implements token bucket algorithm with Redis backend.
"""

import time
import hashlib
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import redis
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from investment_system.core.contracts import UserTier
from investment_system.security.audit import security_logger


class RateLimiter:
    """
    Token bucket rate limiter with Redis backend.
    Supports per-user, per-tier, and per-IP rate limiting.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize rate limiter.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url or "redis://localhost:6379/1"
        try:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            self.redis.ping()
            self.redis_available = True
        except:
            # Fallback to in-memory if Redis unavailable
            self.redis_available = False
            self.memory_store = {}
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        burst_size: Optional[int] = None
    ) -> tuple[bool, int, datetime]:
        """
        Check if request is within rate limit using token bucket algorithm.
        
        Args:
            key: Unique identifier for rate limit bucket
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds
            burst_size: Maximum burst size (optional)
            
        Returns:
            Tuple of (allowed, remaining_requests, reset_time)
        """
        if self.redis_available:
            return self._check_redis(key, max_requests, window_seconds, burst_size)
        else:
            return self._check_memory(key, max_requests, window_seconds, burst_size)
    
    def _check_redis(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        burst_size: Optional[int] = None
    ) -> tuple[bool, int, datetime]:
        """Check rate limit using Redis."""
        now = time.time()
        bucket_key = f"rate_limit:{key}"
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()
        
        # Remove old entries outside window
        pipe.zremrangebyscore(bucket_key, 0, now - window_seconds)
        
        # Count current requests in window
        pipe.zcard(bucket_key)
        
        # Add current request
        pipe.zadd(bucket_key, {str(now): now})
        
        # Set expiry
        pipe.expire(bucket_key, window_seconds + 1)
        
        results = pipe.execute()
        request_count = results[1]
        
        # Check burst protection if enabled
        if burst_size:
            burst_key = f"burst:{key}"
            burst_count = self.redis.incr(burst_key)
            if burst_count == 1:
                self.redis.expire(burst_key, 1)
            if burst_count > burst_size:
                return False, 0, datetime.utcnow() + timedelta(seconds=1)
        
        # Check if within limit
        allowed = request_count <= max_requests
        remaining = max(0, max_requests - request_count)
        reset_time = datetime.utcnow() + timedelta(seconds=window_seconds)
        
        return allowed, remaining, reset_time
    
    def _check_memory(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
        burst_size: Optional[int] = None
    ) -> tuple[bool, int, datetime]:
        """Fallback in-memory rate limiting."""
        now = time.time()
        
        # Initialize bucket if not exists
        if key not in self.memory_store:
            self.memory_store[key] = []
        
        # Remove old entries
        self.memory_store[key] = [
            timestamp for timestamp in self.memory_store[key]
            if timestamp > now - window_seconds
        ]
        
        # Check if within limit
        request_count = len(self.memory_store[key])
        
        if request_count >= max_requests:
            return False, 0, datetime.utcnow() + timedelta(seconds=window_seconds)
        
        # Add current request
        self.memory_store[key].append(now)
        
        remaining = max_requests - request_count - 1
        reset_time = datetime.utcnow() + timedelta(seconds=window_seconds)
        
        return True, remaining, reset_time
    
    def get_tier_limits(self, tier: UserTier) -> Dict[str, int]:
        """
        Get rate limits for user tier.
        
        Args:
            tier: User subscription tier
            
        Returns:
            Dictionary of limits
        """
        limits = {
            UserTier.FREE: {
                "per_minute": 10,
                "per_hour": 100,
                "per_day": 500,
                "burst": 5
            },
            UserTier.STARTER: {
                "per_minute": 60,
                "per_hour": 1000,
                "per_day": 10000,
                "burst": 20
            },
            UserTier.PRO: {
                "per_minute": 300,
                "per_hour": 10000,
                "per_day": 100000,
                "burst": 50
            },
            UserTier.ENTERPRISE: {
                "per_minute": 1000,
                "per_hour": 100000,
                "per_day": 1000000,
                "burst": 100
            }
        }
        return limits.get(tier, limits[UserTier.FREE])


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for automatic rate limiting on all endpoints.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limiter = RateLimiter()
        
        # Endpoint-specific limits (requests per minute)
        self.endpoint_limits = {
            "/auth/login": 5,
            "/auth/register": 3,
            "/auth/reset-password": 3,
            "/signals": 60,
            "/export": 10,
            "/api": 100  # Default for API endpoints
        }
    
    async def dispatch(self, request: Request, call_next):
        """Apply rate limiting to request."""
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/healthz", "/docs", "/redoc"]:
            return await call_next(request)
        
        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)
        
        # Determine rate limit key
        if user_id:
            # Authenticated user - use user ID
            key = f"user:{user_id}"
            tier = getattr(request.state, "user_tier", UserTier.FREE)
            limits = self.rate_limiter.get_tier_limits(tier)
            max_requests = limits["per_minute"]
            window = 60
        else:
            # Anonymous user - use IP address
            key = f"ip:{self._hash_ip(client_ip)}"
            max_requests = 30  # Stricter limit for anonymous
            window = 60
        
        # Check endpoint-specific limits
        for path_prefix, limit in self.endpoint_limits.items():
            if request.url.path.startswith(path_prefix):
                max_requests = min(max_requests, limit)
                break
        
        # Check rate limit
        allowed, remaining, reset_time = self.rate_limiter.check_rate_limit(
            key=key,
            max_requests=max_requests,
            window_seconds=window
        )
        
        if not allowed:
            # Log rate limit violation
            security_logger.log_rate_limit_exceeded(
                user_id=user_id,
                ip_address=client_ip,
                endpoint=request.url.path,
                limit=max_requests
            )
            
            # Return 429 Too Many Requests
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Please retry after {reset_time.isoformat()}",
                    "retry_after": reset_time.isoformat()
                },
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_time.timestamp())),
                    "Retry-After": str(window)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_time.timestamp()))
        
        return response
    
    def _hash_ip(self, ip: str) -> str:
        """Hash IP for privacy."""
        return hashlib.sha256(ip.encode()).hexdigest()[:16]


class DDoSProtection:
    """
    Advanced DDoS protection with pattern detection.
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.rate_limiter = RateLimiter(redis_url)
        self.suspicious_patterns = [
            r"\.\.\/",  # Directory traversal
            r"<script",  # XSS attempt
            r"union.*select",  # SQL injection
            r"eval\(",  # Code injection
            r"base64_decode",  # Encoded payload
        ]
    
    def check_request_pattern(self, request: Request) -> bool:
        """
        Check request for suspicious patterns.
        
        Args:
            request: FastAPI request object
            
        Returns:
            True if suspicious pattern detected
        """
        # Check URL path
        path = request.url.path.lower()
        query = str(request.url.query).lower()
        
        # Check for suspicious patterns
        for pattern in self.suspicious_patterns:
            import re
            if re.search(pattern, path + query, re.IGNORECASE):
                return True
        
        # Check for unusually long URLs
        if len(str(request.url)) > 2000:
            return True
        
        # Check for too many parameters
        if len(request.query_params) > 20:
            return True
        
        return False
    
    def apply_tarpit(self, delay_seconds: float = 10.0):
        """
        Apply tarpit delay to slow down attackers.
        
        Args:
            delay_seconds: Delay in seconds
        """
        time.sleep(delay_seconds)
    
    async def protect(self, request: Request) -> Optional[JSONResponse]:
        """
        Apply DDoS protection to request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Error response if blocked, None otherwise
        """
        client_ip = request.client.host if request.client else "unknown"
        
        # Check for suspicious patterns
        if self.check_request_pattern(request):
            # Log suspicious activity
            security_logger.log_suspicious_activity(
                description="Suspicious request pattern detected",
                user_id=None,
                ip_address=client_ip,
                details={
                    "path": request.url.path,
                    "query": str(request.url.query),
                    "method": request.method
                }
            )
            
            # Apply tarpit to slow down attacker
            self.apply_tarpit(5.0)
            
            # Return 403 Forbidden
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"error": "Forbidden", "message": "Access denied"}
            )
        
        # Check for request flooding (more than 10 requests per second)
        flood_key = f"flood:{client_ip}"
        allowed, _, _ = self.rate_limiter.check_rate_limit(
            key=flood_key,
            max_requests=10,
            window_seconds=1,
            burst_size=15
        )
        
        if not allowed:
            # Apply progressive delay
            self.apply_tarpit(10.0)
            
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "error": "Service temporarily unavailable",
                    "message": "Please try again later"
                }
            )
        
        return None


# Global instances
rate_limiter = RateLimiter()
ddos_protection = DDoSProtection()
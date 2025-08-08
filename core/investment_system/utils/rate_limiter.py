"""
Advanced Rate Limiting System
Implements multiple rate limiting strategies with Redis backend and fallbacks
"""

import time
import logging
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import redis
from functools import wraps
from flask import request, jsonify, g
import hashlib

from .secure_config_manager import get_config_manager
from ..monitoring.audit_logger import get_audit_logger, EventType, SeverityLevel

logger = logging.getLogger(__name__)


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window" 
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"


@dataclass
class RateLimitConfig:
    """Rate limit configuration"""
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    requests_per_day: int = 10000
    burst_limit: int = 10
    strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW
    whitelist_ips: List[str] = None
    blacklist_ips: List[str] = None


@dataclass
class RateLimitStatus:
    """Rate limit status"""
    allowed: bool
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None
    current_usage: int = 0


class RateLimiter:
    """
    Advanced rate limiter with multiple strategies and Redis backend
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """Initialize rate limiter"""
        self.config_manager = get_config_manager()
        self.audit_logger = get_audit_logger()
        
        # Redis setup
        self.redis_client = redis_client
        if not self.redis_client:
            try:
                import os
                redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/1')
                self.redis_client = redis.from_url(redis_url)
                # Test connection
                self.redis_client.ping()
            except Exception as e:
                logger.warning(f"Redis connection failed, using in-memory fallback: {e}")
                self.redis_client = None
        
        # In-memory fallback for rate limiting
        self.memory_store: Dict[str, List[float]] = {}
        self.token_buckets: Dict[str, Dict[str, Any]] = {}
        
        # Default configurations
        self.default_config = RateLimitConfig()
        
        # Load rate limit configurations from environment
        rate_limit_config = self.config_manager.get_rate_limit_config()
        self.default_config.requests_per_minute = rate_limit_config.per_minute
        self.default_config.requests_per_hour = rate_limit_config.per_hour
        self.default_config.requests_per_day = rate_limit_config.per_day
    
    def _get_key(self, identifier: str, window: str, endpoint: str = None) -> str:
        """Generate Redis key for rate limiting"""
        base_key = f"rate_limit:{identifier}:{window}"
        if endpoint:
            base_key += f":{endpoint}"
        return base_key
    
    def _get_current_window(self, window_size: int) -> int:
        """Get current time window"""
        return int(time.time()) // window_size
    
    def check_rate_limit(self, identifier: str, config: RateLimitConfig = None, 
                        endpoint: str = None) -> RateLimitStatus:
        """Check if request should be rate limited"""
        
        if not config:
            config = self.default_config
        
        # Check whitelist/blacklist
        if self._is_whitelisted(identifier, config):
            return RateLimitStatus(
                allowed=True,
                remaining=config.requests_per_minute,
                reset_time=datetime.utcnow() + timedelta(minutes=1)
            )
        
        if self._is_blacklisted(identifier, config):
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=datetime.utcnow() + timedelta(hours=24),
                retry_after=86400  # 24 hours
            )
        
        # Apply rate limiting strategy
        if config.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return self._sliding_window_check(identifier, config, endpoint)
        elif config.strategy == RateLimitStrategy.FIXED_WINDOW:
            return self._fixed_window_check(identifier, config, endpoint)
        elif config.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return self._token_bucket_check(identifier, config, endpoint)
        else:
            return self._sliding_window_check(identifier, config, endpoint)
    
    def _is_whitelisted(self, identifier: str, config: RateLimitConfig) -> bool:
        """Check if identifier is whitelisted"""
        if not config.whitelist_ips:
            return False
        return identifier in config.whitelist_ips
    
    def _is_blacklisted(self, identifier: str, config: RateLimitConfig) -> bool:
        """Check if identifier is blacklisted"""
        if not config.blacklist_ips:
            return False
        return identifier in config.blacklist_ips
    
    def _sliding_window_check(self, identifier: str, config: RateLimitConfig, 
                            endpoint: str = None) -> RateLimitStatus:
        """Sliding window rate limit check"""
        
        now = time.time()
        windows = [
            (60, config.requests_per_minute, "minute"),
            (3600, config.requests_per_hour, "hour"),
            (86400, config.requests_per_day, "day")
        ]
        
        # Check all time windows
        for window_seconds, limit, window_name in windows:
            if self.redis_client:
                status = self._redis_sliding_window_check(
                    identifier, window_seconds, limit, window_name, endpoint, now
                )
            else:
                status = self._memory_sliding_window_check(
                    identifier, window_seconds, limit, window_name, now
                )
            
            if not status.allowed:
                return status
        
        # All windows passed
        return RateLimitStatus(
            allowed=True,
            remaining=min(
                config.requests_per_minute,
                config.requests_per_hour,
                config.requests_per_day
            ),
            reset_time=datetime.utcnow() + timedelta(minutes=1)
        )
    
    def _redis_sliding_window_check(self, identifier: str, window_seconds: int, 
                                   limit: int, window_name: str, endpoint: str,
                                   now: float) -> RateLimitStatus:
        """Redis-based sliding window check"""
        
        try:
            key = self._get_key(identifier, window_name, endpoint)
            pipe = self.redis_client.pipeline()
            
            # Remove expired entries
            pipe.zremrangebyscore(key, 0, now - window_seconds)
            
            # Count current requests
            pipe.zcard(key)
            
            # Add current request
            pipe.zadd(key, {str(now): now})
            
            # Set expiration
            pipe.expire(key, window_seconds)
            
            results = pipe.execute()
            current_count = results[1] + 1  # +1 for current request
            
            if current_count > limit:
                # Remove the request we just added since it's rejected
                self.redis_client.zrem(key, str(now))
                
                return RateLimitStatus(
                    allowed=False,
                    remaining=0,
                    reset_time=datetime.fromtimestamp(now + window_seconds),
                    retry_after=window_seconds,
                    current_usage=current_count - 1
                )
            
            return RateLimitStatus(
                allowed=True,
                remaining=limit - current_count,
                reset_time=datetime.fromtimestamp(now + window_seconds),
                current_usage=current_count
            )
            
        except Exception as e:
            logger.error(f"Redis sliding window error: {e}")
            # Fallback to memory check
            return self._memory_sliding_window_check(identifier, window_seconds, limit, window_name, now)
    
    def _memory_sliding_window_check(self, identifier: str, window_seconds: int,
                                   limit: int, window_name: str, now: float) -> RateLimitStatus:
        """Memory-based sliding window check"""
        
        key = f"{identifier}:{window_name}"
        
        if key not in self.memory_store:
            self.memory_store[key] = []
        
        # Remove expired requests
        cutoff_time = now - window_seconds
        self.memory_store[key] = [
            req_time for req_time in self.memory_store[key]
            if req_time > cutoff_time
        ]
        
        current_count = len(self.memory_store[key])
        
        if current_count >= limit:
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=datetime.fromtimestamp(now + window_seconds),
                retry_after=window_seconds,
                current_usage=current_count
            )
        
        # Add current request
        self.memory_store[key].append(now)
        
        return RateLimitStatus(
            allowed=True,
            remaining=limit - current_count - 1,
            reset_time=datetime.fromtimestamp(now + window_seconds),
            current_usage=current_count + 1
        )
    
    def _fixed_window_check(self, identifier: str, config: RateLimitConfig,
                           endpoint: str = None) -> RateLimitStatus:
        """Fixed window rate limit check"""
        
        now = time.time()
        current_minute = self._get_current_window(60)
        current_hour = self._get_current_window(3600)
        current_day = self._get_current_window(86400)
        
        windows = [
            (current_minute, 60, config.requests_per_minute, "minute"),
            (current_hour, 3600, config.requests_per_hour, "hour"),
            (current_day, 86400, config.requests_per_day, "day")
        ]
        
        for window, window_seconds, limit, window_name in windows:
            if self.redis_client:
                status = self._redis_fixed_window_check(
                    identifier, window, window_seconds, limit, window_name, endpoint
                )
            else:
                status = self._memory_fixed_window_check(
                    identifier, window, window_seconds, limit, window_name
                )
            
            if not status.allowed:
                return status
        
        return RateLimitStatus(
            allowed=True,
            remaining=min(
                config.requests_per_minute,
                config.requests_per_hour,
                config.requests_per_day
            ),
            reset_time=datetime.fromtimestamp((current_minute + 1) * 60)
        )
    
    def _redis_fixed_window_check(self, identifier: str, window: int, window_seconds: int,
                                 limit: int, window_name: str, endpoint: str) -> RateLimitStatus:
        """Redis-based fixed window check"""
        
        try:
            key = f"{self._get_key(identifier, window_name, endpoint)}:{window}"
            
            pipe = self.redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, window_seconds)
            
            results = pipe.execute()
            current_count = results[0]
            
            if current_count > limit:
                return RateLimitStatus(
                    allowed=False,
                    remaining=0,
                    reset_time=datetime.fromtimestamp((window + 1) * window_seconds),
                    retry_after=window_seconds - (time.time() % window_seconds),
                    current_usage=current_count
                )
            
            return RateLimitStatus(
                allowed=True,
                remaining=limit - current_count,
                reset_time=datetime.fromtimestamp((window + 1) * window_seconds),
                current_usage=current_count
            )
            
        except Exception as e:
            logger.error(f"Redis fixed window error: {e}")
            return self._memory_fixed_window_check(identifier, window, window_seconds, limit, window_name)
    
    def _memory_fixed_window_check(self, identifier: str, window: int, window_seconds: int,
                                  limit: int, window_name: str) -> RateLimitStatus:
        """Memory-based fixed window check"""
        
        key = f"{identifier}:{window_name}:{window}"
        
        if key not in self.memory_store:
            self.memory_store[key] = [0]  # [count]
        
        current_count = self.memory_store[key][0] + 1
        self.memory_store[key][0] = current_count
        
        if current_count > limit:
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=datetime.fromtimestamp((window + 1) * window_seconds),
                retry_after=window_seconds - (time.time() % window_seconds),
                current_usage=current_count
            )
        
        return RateLimitStatus(
            allowed=True,
            remaining=limit - current_count,
            reset_time=datetime.fromtimestamp((window + 1) * window_seconds),
            current_usage=current_count
        )
    
    def _token_bucket_check(self, identifier: str, config: RateLimitConfig,
                           endpoint: str = None) -> RateLimitStatus:
        """Token bucket rate limit check"""
        
        now = time.time()
        bucket_key = f"{identifier}:{endpoint}" if endpoint else identifier
        
        if bucket_key not in self.token_buckets:
            self.token_buckets[bucket_key] = {
                'tokens': config.requests_per_minute,
                'last_update': now,
                'capacity': config.requests_per_minute,
                'refill_rate': config.requests_per_minute / 60.0  # tokens per second
            }
        
        bucket = self.token_buckets[bucket_key]
        
        # Calculate tokens to add
        time_passed = now - bucket['last_update']
        tokens_to_add = time_passed * bucket['refill_rate']
        bucket['tokens'] = min(bucket['capacity'], bucket['tokens'] + tokens_to_add)
        bucket['last_update'] = now
        
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return RateLimitStatus(
                allowed=True,
                remaining=int(bucket['tokens']),
                reset_time=datetime.fromtimestamp(now + (bucket['capacity'] - bucket['tokens']) / bucket['refill_rate']),
                current_usage=bucket['capacity'] - bucket['tokens']
            )
        else:
            retry_after = (1 - bucket['tokens']) / bucket['refill_rate']
            return RateLimitStatus(
                allowed=False,
                remaining=0,
                reset_time=datetime.fromtimestamp(now + retry_after),
                retry_after=int(retry_after),
                current_usage=bucket['capacity']
            )
    
    def reset_rate_limit(self, identifier: str, endpoint: str = None):
        """Reset rate limit for identifier"""
        
        if self.redis_client:
            try:
                # Delete all rate limit keys for this identifier
                pattern = f"rate_limit:{identifier}:*"
                if endpoint:
                    pattern += f":{endpoint}*"
                
                keys = self.redis_client.keys(pattern)
                if keys:
                    self.redis_client.delete(*keys)
                    
            except Exception as e:
                logger.error(f"Redis reset error: {e}")
        
        # Clear memory store
        keys_to_remove = []
        for key in self.memory_store.keys():
            if key.startswith(f"{identifier}:"):
                if not endpoint or endpoint in key:
                    keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.memory_store[key]
        
        # Clear token buckets
        bucket_key = f"{identifier}:{endpoint}" if endpoint else identifier
        if bucket_key in self.token_buckets:
            del self.token_buckets[bucket_key]
    
    def get_rate_limit_info(self, identifier: str, endpoint: str = None) -> Dict[str, Any]:
        """Get current rate limit information"""
        
        info = {}
        
        if self.redis_client:
            try:
                pattern = f"rate_limit:{identifier}:*"
                if endpoint:
                    pattern += f":{endpoint}*"
                
                keys = self.redis_client.keys(pattern)
                for key in keys:
                    if self.redis_client.type(key) == b'zset':
                        count = self.redis_client.zcard(key)
                        info[key.decode()] = count
                    else:
                        count = self.redis_client.get(key)
                        info[key.decode()] = int(count) if count else 0
                        
            except Exception as e:
                logger.error(f"Redis info error: {e}")
        
        # Add memory store info
        for key, value in self.memory_store.items():
            if key.startswith(f"{identifier}:"):
                if not endpoint or endpoint in key:
                    info[f"memory:{key}"] = len(value) if isinstance(value, list) else value[0]
        
        return info


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limit(requests_per_minute: int = 60, requests_per_hour: int = 1000,
               requests_per_day: int = 10000, per_user: bool = True,
               strategy: RateLimitStrategy = RateLimitStrategy.SLIDING_WINDOW):
    """
    Rate limiting decorator for Flask routes
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rate_limiter = get_rate_limiter()
            audit_logger = get_audit_logger()
            
            # Determine identifier
            if per_user and hasattr(g, 'current_user') and g.current_user:
                identifier = f"user:{g.current_user.user_id}"
            else:
                identifier = f"ip:{request.remote_addr}"
            
            # Get endpoint name
            endpoint = request.endpoint or f.__name__
            
            # Configure rate limit
            config = RateLimitConfig(
                requests_per_minute=requests_per_minute,
                requests_per_hour=requests_per_hour,
                requests_per_day=requests_per_day,
                strategy=strategy
            )
            
            # Check rate limit
            status = rate_limiter.check_rate_limit(identifier, config, endpoint)
            
            if not status.allowed:
                # Audit log rate limit exceeded
                audit_logger.log_event(
                    EventType.RATE_LIMIT_EXCEEDED,
                    SeverityLevel.MEDIUM,
                    user_id=getattr(g.current_user, 'user_id', None) if hasattr(g, 'current_user') else None,
                    resource=endpoint,
                    details={
                        'identifier': identifier,
                        'current_usage': status.current_usage,
                        'retry_after': status.retry_after
                    }
                )
                
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': status.retry_after,
                    'reset_time': status.reset_time.isoformat()
                })
                response.status_code = 429
                response.headers['Retry-After'] = str(status.retry_after or 60)
                response.headers['X-RateLimit-Remaining'] = str(status.remaining)
                response.headers['X-RateLimit-Reset'] = str(int(status.reset_time.timestamp()))
                
                return response
            
            # Add rate limit headers to response
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Remaining'] = str(status.remaining)
                response.headers['X-RateLimit-Reset'] = str(int(status.reset_time.timestamp()))
            
            return response
        
        return decorated_function
    return decorator


if __name__ == "__main__":
    # Test rate limiter
    limiter = RateLimiter()
    
    # Test different strategies
    config = RateLimitConfig(requests_per_minute=5, strategy=RateLimitStrategy.SLIDING_WINDOW)
    
    for i in range(10):
        status = limiter.check_rate_limit("test_user", config)
        print(f"Request {i+1}: Allowed={status.allowed}, Remaining={status.remaining}")
        time.sleep(0.1)
        
        if not status.allowed:
            print(f"Rate limited! Retry after {status.retry_after} seconds")
            break
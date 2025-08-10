"""
Caching infrastructure with Redis support and fallback to memory.
Modular design allows switching cache backends without changing business logic.
"""

import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional, Dict
from abc import ABC, abstractmethod
import hashlib

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class CacheBackend(ABC):
    """Abstract cache backend"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in cache with TTL in seconds"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache"""
        pass


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend for development"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        if key not in self._cache:
            return None
        
        entry = self._cache[key]
        if entry['expires_at'] and datetime.utcnow() > entry['expires_at']:
            del self._cache[key]
            return None
        
        return entry['value']
    
    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in memory cache"""
        expires_at = None
        if ttl > 0:
            expires_at = datetime.utcnow() + timedelta(seconds=ttl)
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.utcnow()
        }
        return True
    
    def delete(self, key: str) -> bool:
        """Delete from memory cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in memory"""
        if key not in self._cache:
            return False
        
        entry = self._cache[key]
        if entry['expires_at'] and datetime.utcnow() > entry['expires_at']:
            del self._cache[key]
            return False
        
        return True
    
    def clear(self) -> bool:
        """Clear memory cache"""
        self._cache.clear()
        return True


class RedisCacheBackend(CacheBackend):
    """Redis cache backend for production"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        if not REDIS_AVAILABLE:
            raise ImportError("Redis not installed. Run: pip install redis")
        
        self.client = redis.from_url(redis_url, decode_responses=False)
        self._test_connection()
    
    def _test_connection(self):
        """Test Redis connection"""
        try:
            self.client.ping()
        except Exception as e:
            raise ConnectionError(f"Cannot connect to Redis: {e}")
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Redis"""
        try:
            value = self.client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int) -> bool:
        """Set value in Redis"""
        try:
            serialized = pickle.dumps(value)
            if ttl > 0:
                return self.client.setex(key, ttl, serialized)
            else:
                return self.client.set(key, serialized)
        except Exception as e:
            print(f"Redis set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete from Redis"""
        try:
            return self.client.delete(key) > 0
        except Exception as e:
            print(f"Redis delete error: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return self.client.exists(key) > 0
        except Exception as e:
            print(f"Redis exists error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all Redis cache (use with caution)"""
        try:
            self.client.flushdb()
            return True
        except Exception as e:
            print(f"Redis clear error: {e}")
            return False


class CacheManager:
    """Main cache manager with fallback support"""
    
    # Default TTLs for different data types (seconds)
    DEFAULT_TTLS = {
        'market_data': 600,      # 10 minutes
        'signals': 300,          # 5 minutes
        'user_data': 3600,       # 1 hour
        'api_response': 60,      # 1 minute
        'analysis': 900,         # 15 minutes
    }
    
    def __init__(self, backend: Optional[CacheBackend] = None):
        self.backend = backend or MemoryCacheBackend()
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
    
    @classmethod
    def create_from_url(cls, cache_url: Optional[str] = None) -> 'CacheManager':
        """Create cache manager from URL"""
        if cache_url and cache_url.startswith("redis://"):
            try:
                backend = RedisCacheBackend(cache_url)
                return cls(backend)
            except Exception as e:
                print(f"Failed to connect to Redis, using memory cache: {e}")
        
        return cls(MemoryCacheBackend())
    
    def _make_key(self, prefix: str, *args) -> str:
        """Create cache key from prefix and arguments"""
        # Create a deterministic key
        parts = [prefix] + [str(arg) for arg in args]
        raw_key = ":".join(parts)
        
        # Hash if too long
        if len(raw_key) > 250:
            hash_suffix = hashlib.md5(raw_key.encode()).hexdigest()[:8]
            return f"{prefix}:{hash_suffix}"
        
        return raw_key
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        value = self.backend.get(key)
        if value is not None:
            self._stats['hits'] += 1
        else:
            self._stats['misses'] += 1
        return value
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None, data_type: Optional[str] = None) -> bool:
        """Set value in cache with optional TTL"""
        if ttl is None and data_type:
            ttl = self.DEFAULT_TTLS.get(data_type, 300)
        elif ttl is None:
            ttl = 300  # Default 5 minutes
        
        result = self.backend.set(key, value, ttl)
        if result:
            self._stats['sets'] += 1
        return result
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        result = self.backend.delete(key)
        if result:
            self._stats['deletes'] += 1
        return result
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        return self.backend.exists(key)
    
    def clear(self) -> bool:
        """Clear all cache"""
        return self.backend.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = self._stats['hits'] / total_requests if total_requests > 0 else 0
        
        return {
            **self._stats,
            'hit_rate': round(hit_rate, 4),
            'backend': self.backend.__class__.__name__
        }
    
    # Convenience methods for specific data types
    
    def get_market_data(self, symbol: str, lookback_days: int) -> Optional[Any]:
        """Get cached market data"""
        key = self._make_key("market", symbol, lookback_days)
        return self.get(key)
    
    def set_market_data(self, symbol: str, lookback_days: int, data: Any) -> bool:
        """Cache market data"""
        key = self._make_key("market", symbol, lookback_days)
        return self.set(key, data, data_type='market_data')
    
    def get_signals(self, symbols: list, user_tier: str) -> Optional[Any]:
        """Get cached signals"""
        symbols_hash = hashlib.md5(":".join(sorted(symbols)).encode()).hexdigest()[:8]
        key = self._make_key("signals", symbols_hash, user_tier)
        return self.get(key)
    
    def set_signals(self, symbols: list, user_tier: str, signals: Any) -> bool:
        """Cache signals"""
        symbols_hash = hashlib.md5(":".join(sorted(symbols)).encode()).hexdigest()[:8]
        key = self._make_key("signals", symbols_hash, user_tier)
        return self.set(key, signals, data_type='signals')
    
    def get_user(self, user_id: str) -> Optional[Any]:
        """Get cached user data"""
        key = self._make_key("user", user_id)
        return self.get(key)
    
    def set_user(self, user_id: str, user_data: Any) -> bool:
        """Cache user data"""
        key = self._make_key("user", user_id)
        return self.set(key, user_data, data_type='user_data')
    
    def invalidate_user(self, user_id: str) -> bool:
        """Invalidate user cache"""
        key = self._make_key("user", user_id)
        return self.delete(key)


# Global cache instance (created on first use)
_cache_instance: Optional[CacheManager] = None


def get_cache() -> CacheManager:
    """Get global cache instance"""
    global _cache_instance
    if _cache_instance is None:
        # Try to get Redis URL from settings
        try:
            from config.settings import get_settings
            settings = get_settings()
            _cache_instance = CacheManager.create_from_url(settings.redis_url)
        except Exception:
            # Fallback to memory cache
            _cache_instance = CacheManager()
    
    return _cache_instance


# Decorator for caching function results
def cache_result(ttl: int = 300, key_prefix: Optional[str] = None):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache()
            
            # Create cache key
            prefix = key_prefix or f"func:{func.__name__}"
            cache_key = cache._make_key(
                prefix,
                *[str(arg) for arg in args],
                *[f"{k}={v}" for k, v in sorted(kwargs.items())]
            )
            
            # Try to get from cache
            cached = cache.get(cache_key)
            if cached is not None:
                return cached
            
            # Execute function
            result = func(*args, **kwargs)
            
            # Cache result
            cache.set(cache_key, result, ttl)
            
            return result
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator
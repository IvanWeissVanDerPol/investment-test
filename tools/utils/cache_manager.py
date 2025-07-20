"""
Cache Manager for Investment Analysis System
Implements caching to improve performance and reduce API calls
"""

import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import hashlib
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    def __init__(self, cache_dir: str = "cache"):
        """Initialize cache manager"""
        self.cache_dir = cache_dir
        self.ensure_cache_dir()
        
        # Cache expiration times (in hours)
        self.cache_expiry = {
            'stock_data': 1,      # Stock prices update frequently
            'news': 4,            # News updates several times per day
            'social': 6,          # Social sentiment changes slowly
            'options': 2,         # Options data updates during market hours
            'ai_predictions': 12, # AI predictions can be cached longer
            'forex': 4,           # Forex updates frequently
            'bonds': 24,          # Bond yields change slowly
            'sector': 8           # Sector data updates less frequently
        }
    
    def ensure_cache_dir(self):
        """Ensure cache directory exists"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
            logger.info(f"Created cache directory: {self.cache_dir}")
    
    def get_cache_key(self, data_type: str, identifier: str, params: Dict = None) -> str:
        """Generate cache key from data type, identifier, and parameters"""
        if params:
            param_str = json.dumps(params, sort_keys=True)
            identifier = f"{identifier}_{hashlib.md5(param_str.encode()).hexdigest()[:8]}"
        
        return f"{data_type}_{identifier}.json"
    
    def get_cache_path(self, cache_key: str) -> str:
        """Get full cache file path"""
        return os.path.join(self.cache_dir, cache_key)
    
    def is_cache_valid(self, cache_key: str, data_type: str) -> bool:
        """Check if cache is still valid based on expiry time"""
        cache_path = self.get_cache_path(cache_key)
        
        if not os.path.exists(cache_path):
            return False
        
        # Check file modification time
        file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
        expiry_hours = self.cache_expiry.get(data_type, 24)
        expiry_time = datetime.now() - timedelta(hours=expiry_hours)
        
        return file_time > expiry_time
    
    def get_cached_data(self, data_type: str, identifier: str, params: Dict = None) -> Optional[Dict]:
        """Retrieve cached data if valid"""
        try:
            cache_key = self.get_cache_key(data_type, identifier, params)
            
            if not self.is_cache_valid(cache_key, data_type):
                return None
            
            cache_path = self.get_cache_path(cache_key)
            
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            
            logger.debug(f"Cache hit for {data_type}:{identifier}")
            return cached_data
            
        except Exception as e:
            logger.warning(f"Error reading cache for {data_type}:{identifier}: {e}")
            return None
    
    def cache_data(self, data_type: str, identifier: str, data: Any, params: Dict = None):
        """Cache data to file"""
        try:
            cache_key = self.get_cache_key(data_type, identifier, params)
            cache_path = self.get_cache_path(cache_key)
            
            # Add timestamp to cached data
            cache_entry = {
                'timestamp': datetime.now().isoformat(),
                'data_type': data_type,
                'identifier': identifier,
                'data': data
            }
            
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2, default=str)
            
            logger.debug(f"Cached {data_type}:{identifier}")
            
        except Exception as e:
            logger.warning(f"Error caching data for {data_type}:{identifier}: {e}")
    
    def invalidate_cache(self, data_type: str = None, identifier: str = None):
        """Invalidate cache entries"""
        try:
            cache_files = os.listdir(self.cache_dir)
            
            for cache_file in cache_files:
                should_delete = False
                
                if data_type and identifier:
                    # Delete specific cache entry
                    cache_key = self.get_cache_key(data_type, identifier)
                    should_delete = cache_file == cache_key
                elif data_type:
                    # Delete all entries of specific type
                    should_delete = cache_file.startswith(f"{data_type}_")
                elif identifier:
                    # Delete all entries for specific identifier
                    should_delete = identifier in cache_file
                
                if should_delete:
                    cache_path = self.get_cache_path(cache_file)
                    os.remove(cache_path)
                    logger.info(f"Invalidated cache: {cache_file}")
            
        except Exception as e:
            logger.warning(f"Error invalidating cache: {e}")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        try:
            cache_files = os.listdir(self.cache_dir)
            
            stats = {
                'total_files': len(cache_files),
                'total_size_mb': 0,
                'by_type': {},
                'oldest_file': None,
                'newest_file': None
            }
            
            oldest_time = datetime.now()
            newest_time = datetime.min
            
            for cache_file in cache_files:
                cache_path = self.get_cache_path(cache_file)
                
                # File size
                file_size = os.path.getsize(cache_path)
                stats['total_size_mb'] += file_size
                
                # File times
                file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
                
                if file_time < oldest_time:
                    oldest_time = file_time
                    stats['oldest_file'] = cache_file
                
                if file_time > newest_time:
                    newest_time = file_time
                    stats['newest_file'] = cache_file
                
                # By type
                data_type = cache_file.split('_')[0]
                if data_type not in stats['by_type']:
                    stats['by_type'][data_type] = {'count': 0, 'size_mb': 0}
                
                stats['by_type'][data_type]['count'] += 1
                stats['by_type'][data_type]['size_mb'] += file_size
            
            # Convert to MB
            stats['total_size_mb'] = round(stats['total_size_mb'] / (1024 * 1024), 2)
            for type_stats in stats['by_type'].values():
                type_stats['size_mb'] = round(type_stats['size_mb'] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
    
    def cleanup_old_cache(self, days_old: int = 7):
        """Remove cache files older than specified days"""
        try:
            cutoff_time = datetime.now() - timedelta(days=days_old)
            cache_files = os.listdir(self.cache_dir)
            removed_count = 0
            
            for cache_file in cache_files:
                cache_path = self.get_cache_path(cache_file)
                file_time = datetime.fromtimestamp(os.path.getmtime(cache_path))
                
                if file_time < cutoff_time:
                    os.remove(cache_path)
                    removed_count += 1
            
            logger.info(f"Cleaned up {removed_count} old cache files")
            return removed_count
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
            return 0

# Global cache instance
cache_manager = CacheManager("C:\\Users\\jandr\\Documents\\ivan\\cache")
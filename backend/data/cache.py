"""
Caching layer for data with TTL support.
Uses in-memory cache with fallback to Redis if available.
"""

import hashlib
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional
from logger_config import get_logger

logger = get_logger(__name__)

class CacheManager:
    """Cache manager with TTL support."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.memory_cache = {}
        self.redis_client = None
        
        # Try to import and initialize Redis
        try:
            import redis
            self.redis_client = redis.from_url('redis://localhost:6379/0')
            self.redis_client.ping()
            logger.info("Redis cache initialized")
        except:
            logger.warning("Redis not available, using in-memory cache only")
    
    def _get_cache_key(self, prefix: str, *args) -> str:
        """Generate cache key from prefix and arguments."""
        key_str = f"{prefix}:" + ":".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, prefix: str, *args) -> Optional[Any]:
        """Get value from cache."""
        key = self._get_cache_key(prefix, *args)
        
        # Try memory cache first
        if key in self.memory_cache:
            value, expiry = self.memory_cache[key]
            if datetime.utcnow() < expiry:
                logger.debug(f"Cache hit (memory): {key}")
                return value
            else:
                del self.memory_cache[key]
        
        # Try Redis
        if self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    logger.debug(f"Cache hit (redis): {key}")
                    return pickle.loads(value)
            except Exception as e:
                logger.warning(f"Redis get error: {str(e)}")
        
        logger.debug(f"Cache miss: {key}")
        return None
    
    def set(self, prefix: str, value: Any, *args, ttl_seconds: int = None) -> bool:
        """Set value in cache."""
        key = self._get_cache_key(prefix, *args)
        ttl = ttl_seconds or self.ttl_seconds
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        
        # Set in memory cache
        self.memory_cache[key] = (value, expiry)
        
        # Set in Redis
        if self.redis_client:
            try:
                self.redis_client.setex(key, ttl, pickle.dumps(value))
                logger.debug(f"Cached: {key}")
            except Exception as e:
                logger.warning(f"Redis set error: {str(e)}")
        
        return True
    
    def delete(self, prefix: str, *args) -> bool:
        """Delete from cache."""
        key = self._get_cache_key(prefix, *args)
        
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except Exception as e:
                logger.warning(f"Redis delete error: {str(e)}")
        
        return True
    
    def clear(self, prefix: str = None) -> bool:
        """Clear cache (all or by prefix)."""
        if prefix is None:
            self.memory_cache.clear()
            if self.redis_client:
                try:
                    self.redis_client.flushdb()
                except Exception as e:
                    logger.warning(f"Redis flush error: {str(e)}")
        else:
            # Clear matching keys
            keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(prefix)]
            for k in keys_to_delete:
                del self.memory_cache[k]
        
        return True

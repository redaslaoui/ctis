"""
Redis caching service for clinical trial queries
"""

import redis
import json
import hashlib
from typing import Any, Optional, Dict, List
from functools import wraps
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """Redis caching service with TTL support"""

    def __init__(self):
        """Initialize Redis connection"""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                decode_responses=True
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a unique cache key from function arguments

        Args:
            prefix: Cache key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Unique cache key
        """
        # Create a string representation of arguments
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"

        # Hash the key to keep it short
        key_hash = hashlib.md5(key_data.encode()).hexdigest()

        return f"{prefix}:{key_hash}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if not self.redis_client:
            return None

        try:
            value = self.redis_client.get(key)
            if value:
                logger.debug(f"Cache hit for key: {key}")
                return json.loads(value)
            logger.debug(f"Cache miss for key: {key}")
            return None
        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache with TTL

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (default 1 hour)

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            logger.debug(f"Cached value for key: {key} with TTL: {ttl}s")
            return True
        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from cache

        Args:
            key: Cache key

        Returns:
            True if successful, False otherwise
        """
        if not self.redis_client:
            return False

        try:
            self.redis_client.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching a pattern

        Args:
            pattern: Key pattern (e.g., "trials:*")

        Returns:
            Number of keys deleted
        """
        if not self.redis_client:
            return 0

        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                count = self.redis_client.delete(*keys)
                logger.info(f"Cleared {count} keys matching pattern: {pattern}")
                return count
            return 0
        except Exception as e:
            logger.error(f"Error clearing cache pattern: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        if not self.redis_client:
            return {"status": "disconnected"}

        try:
            info = self.redis_client.info("stats")
            return {
                "status": "connected",
                "total_connections": info.get("total_connections_received", 0),
                "total_commands": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                )
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"status": "error", "error": str(e)}

    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """Calculate cache hit rate"""
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)


# Global cache instance
cache_service = CacheService()


def cached(prefix: str, ttl: int = 3600):
    """
    Decorator for caching function results

    Args:
        prefix: Cache key prefix
        ttl: Time to live in seconds

    Example:
        @cached("trial_search", ttl=1800)
        def search_trials(query):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_service._generate_cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function
            result = func(*args, **kwargs)

            # Cache the result
            cache_service.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator

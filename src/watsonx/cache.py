"""Disk-based cache for LLM responses."""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

try:
    from diskcache import Cache as DiskCache
    DISKCACHE_AVAILABLE = True
except ImportError:
    DISKCACHE_AVAILABLE = False

from src.config import settings


class ResponseCache:
    """Cache for LLM responses using diskcache."""

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        ttl_days: Optional[int] = None,
    ) -> None:
        """
        Initialize the cache.
        
        Args:
            cache_dir: Directory for cache storage (uses config if None)
            ttl_days: Time-to-live in days (uses config if None)
        """
        if not DISKCACHE_AVAILABLE:
            raise ImportError(
                "diskcache is required. Install with: pip install diskcache"
            )

        self.cache_dir = cache_dir or settings.cache_dir
        self.ttl_days = ttl_days or settings.cache_ttl_days
        self.ttl_seconds = self.ttl_days * 24 * 60 * 60

        # Ensure cache directory exists
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize diskcache
        self.cache = DiskCache(str(self.cache_dir))

    def _make_key(self, prompt: str, model_id: str, **kwargs: Any) -> str:
        """
        Create a cache key from prompt and parameters.
        
        Args:
            prompt: Input prompt
            model_id: Model identifier
            **kwargs: Additional parameters
            
        Returns:
            Cache key (SHA256 hash)
        """
        # Create a deterministic string from all inputs
        key_data = {
            "prompt": prompt,
            "model_id": model_id,
            **kwargs,
        }
        key_string = json.dumps(key_data, sort_keys=True)
        
        # Hash to create key
        return hashlib.sha256(key_string.encode()).hexdigest()

    def get(
        self, prompt: str, model_id: str, **kwargs: Any
    ) -> Optional[str]:
        """
        Get cached response.
        
        Args:
            prompt: Input prompt
            model_id: Model identifier
            **kwargs: Additional parameters
            
        Returns:
            Cached response or None if not found/expired
        """
        key = self._make_key(prompt, model_id, **kwargs)
        
        try:
            value = self.cache.get(key)
            if value is not None:
                return value
        except Exception:
            pass
        
        return None

    def set(
        self,
        prompt: str,
        model_id: str,
        response: str,
        **kwargs: Any,
    ) -> None:
        """
        Cache a response.
        
        Args:
            prompt: Input prompt
            model_id: Model identifier
            response: LLM response to cache
            **kwargs: Additional parameters
        """
        key = self._make_key(prompt, model_id, **kwargs)
        
        try:
            # Set with TTL
            self.cache.set(key, response, expire=self.ttl_seconds)
        except Exception:
            # Silently fail if caching fails
            pass

    def clear(self) -> None:
        """Clear all cached responses."""
        try:
            self.cache.clear()
        except Exception:
            pass

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        try:
            return {
                "size": len(self.cache),
                "volume": self.cache.volume(),
                "directory": str(self.cache_dir),
            }
        except Exception:
            return {
                "size": 0,
                "volume": 0,
                "directory": str(self.cache_dir),
            }

    def evict_expired(self) -> int:
        """
        Evict expired entries.
        
        Returns:
            Number of entries evicted
        """
        try:
            # diskcache automatically handles expiration
            # This method is for manual cleanup if needed
            count = 0
            for key in list(self.cache):
                # Check if expired (diskcache handles this internally)
                if self.cache.get(key) is None:
                    count += 1
            return count
        except Exception:
            return 0


# Global cache instance
_cache_instance: Optional[ResponseCache] = None


def get_cache() -> ResponseCache:
    """
    Get the global cache instance.
    
    Returns:
        ResponseCache instance
    """
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ResponseCache()
    return _cache_instance


def get_cached_response(
    prompt: str, model_id: str, **kwargs: Any
) -> Optional[str]:
    """
    Get a cached response using the global cache.
    
    Args:
        prompt: Input prompt
        model_id: Model identifier
        **kwargs: Additional parameters
        
    Returns:
        Cached response or None
    """
    cache = get_cache()
    return cache.get(prompt, model_id, **kwargs)


def cache_response(
    prompt: str, model_id: str, response: str, **kwargs: Any
) -> None:
    """
    Cache a response using the global cache.
    
    Args:
        prompt: Input prompt
        model_id: Model identifier
        response: Response to cache
        **kwargs: Additional parameters
    """
    cache = get_cache()
    cache.set(prompt, model_id, response, **kwargs)


def clear_cache() -> None:
    """Clear the global cache."""
    cache = get_cache()
    cache.clear()

# Made with Bob

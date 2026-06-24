from cachetools import TTLCache
from typing import Any, Optional, cast
import threading


class CacheService:
    """Thread-safe TTL cache service for storing temporary data.

    Uses a class-level cache shared across all instances to ensure
    cached data is accessible globally across the application.
    """

    _cache: TTLCache[str, Any] = cast(
        TTLCache[str, Any], TTLCache(maxsize=100, ttl=300)
    )
    _lock = threading.Lock()

    def __init__(self, maxsize: int = 100, ttl: int = 300):
        with self._lock:
            if hasattr(CacheService._cache, "maxsize") and hasattr(
                CacheService._cache, "ttl"
            ):
                if (
                    CacheService._cache.maxsize != maxsize
                    or CacheService._cache.ttl != ttl
                ):
                    CacheService._cache = cast(
                        TTLCache[str, Any], TTLCache(maxsize=maxsize, ttl=ttl)
                    )

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            CacheService._cache[key] = value

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        with self._lock:
            return CacheService._cache.get(key, default)

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in CacheService._cache:
                del CacheService._cache[key]
                return True
            return False

    def clear(self) -> None:
        with self._lock:
            CacheService._cache.clear()

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in CacheService._cache

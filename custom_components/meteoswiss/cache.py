"""Caching module for MeteoSwiss API calls."""

from __future__ import annotations

import hashlib
import json
import logging
import math
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass
from typing import Any

_LOGGER = logging.getLogger(__name__)


def _validate_ttl(raw: float) -> float:
    """An invalid lifetime must never create an immortal cache entry."""
    if isinstance(raw, bool):
        raise TypeError("Cache TTL must be finite and non-negative")
    try:
        value = float(raw)
    except (ValueError, TypeError, OverflowError):
        raise ValueError("Cache TTL must be finite and non-negative") from None
    if not math.isfinite(value) or value < 0:
        raise ValueError("Cache TTL must be finite and non-negative")
    return value


@dataclass
class CacheEntry:
    """Cache entry with TTL."""

    key: str
    value: Any
    timestamp: float
    ttl: float  # Time to live in seconds

    def __post_init__(self) -> None:
        self.ttl = _validate_ttl(self.ttl)

    def is_expired(self) -> bool:
        """Check if cache entry is expired."""
        return time.monotonic() - self.timestamp >= self.ttl

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)


class MeteoSwissCache:
    """Intelligent cache for MeteoSwiss and Open-Meteo API calls."""

    def __init__(self, default_ttl: float = 300.0) -> None:
        """Initialize cache.

        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: dict[str, CacheEntry] = {}
        self._default_ttl = _validate_ttl(default_ttl)
        self._hits = 0
        self._misses = 0
        self._evictions = 0

    def make_key(self, prefix: str, *args: Any, **kwargs: Any) -> str:
        """Canonical keys isolate types/arguments and bound very long URLs."""
        key = json.dumps(
            [prefix, args, kwargs],
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
        return hashlib.sha256(key.encode()).hexdigest() if len(key) > 200 else key

    def get(self, key: str) -> Any | None:
        """Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        entry = self._cache.get(key)

        if entry is None:
            self._misses += 1
            return None

        if entry.is_expired():
            _LOGGER.debug("Cache entry expired")
            self._evictions += 1
            del self._cache[key]
            self._misses += 1
            return None

        self._hits += 1
        _LOGGER.debug("Cache hit")
        return entry.value

    def set(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (optional, uses default if not specified)
        """
        if ttl is None:
            ttl = self._default_ttl

        entry = CacheEntry(
            key=key,
            value=value,
            timestamp=time.monotonic(),
            ttl=ttl,
        )

        self.cleanup_expired()
        if value is None:
            self.invalidate(key)
            return
        self._cache[key] = entry
        _LOGGER.debug("Cache set (TTL: %s sec)", ttl)

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: float | None = None,
    ) -> Any:
        """Get value from cache or set using factory function.

        Args:
            key: Cache key
            factory: Function to call if cache miss
            ttl: Time-to-live in seconds (optional)

        Returns:
            Cached or freshly computed value
        """
        value = self.get(key)

        if value is not None:
            return value

        # Cache miss, call factory
        value = factory()
        self.set(key, value, ttl)
        return value

    def invalidate(self, key: str) -> None:
        """Invalidate a cache entry.

        Args:
            key: Cache key
        """
        if key in self._cache:
            del self._cache[key]
            _LOGGER.debug("Cache invalidated")

    def clear(self) -> None:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        _LOGGER.debug("Cache cleared: %d entries removed", count)

    def cleanup_expired(self) -> int:
        """Remove all expired entries from cache.

        Returns:
            Number of expired entries removed
        """
        expired_keys = [key for key, entry in self._cache.items() if entry.is_expired()]

        for key in expired_keys:
            del self._cache[key]

        if expired_keys:
            self._evictions += len(expired_keys)
            _LOGGER.debug(
                "Cache cleanup: %d expired entries removed", len(expired_keys)
            )

        return len(expired_keys)

    def get_stats(self) -> dict:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        self.cleanup_expired()
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0.0

        return {
            "entries": len(self._cache),
            "hits": self._hits,
            "misses": self._misses,
            "evictions": self._evictions,
            "hit_rate": round(hit_rate, 2),
            "total_requests": total,
        }

    def reset_stats(self) -> None:
        """Reset cache statistics."""
        self._hits = 0
        self._misses = 0
        self._evictions = 0


# Global cache instances
_current_weather_cache: MeteoSwissCache | None = None
_forecast_cache: MeteoSwissCache | None = None
_stations_cache: MeteoSwissCache | None = None


def get_current_weather_cache() -> MeteoSwissCache:
    """Get or create current weather cache.

    Current weather updates every 10 minutes, so cache for 10 minutes.
    """
    global _current_weather_cache
    if _current_weather_cache is None:
        _current_weather_cache = MeteoSwissCache(default_ttl=600.0)  # 10 minutes
    return _current_weather_cache


def get_forecast_cache() -> MeteoSwissCache:
    """Get or create forecast cache.

    Forecast updates every hour, so cache for 30 minutes.
    """
    global _forecast_cache
    if _forecast_cache is None:
        _forecast_cache = MeteoSwissCache(default_ttl=1800.0)  # 30 minutes
    return _forecast_cache


def get_stations_cache() -> MeteoSwissCache:
    """Get or create stations metadata cache.

    Stations metadata rarely changes, cache for 24 hours.
    """
    global _stations_cache
    if _stations_cache is None:
        _stations_cache = MeteoSwissCache(default_ttl=86400.0)  # 24 hours
    return _stations_cache


def clear_all_caches() -> None:
    """Clear all global caches."""
    if _current_weather_cache:
        _current_weather_cache.clear()
    if _forecast_cache:
        _forecast_cache.clear()
    if _stations_cache:
        _stations_cache.clear()

    _LOGGER.debug("All caches cleared")


def get_all_cache_stats() -> dict:
    """Get statistics for all caches.

    Returns:
        Dictionary with statistics for all caches
    """
    return {
        "current_weather": get_current_weather_cache().get_stats(),
        "forecast": get_forecast_cache().get_stats(),
        "stations": get_stations_cache().get_stats(),
    }

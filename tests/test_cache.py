"""Cache deadlines, isolation, failed factories and accurate diagnostics."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest

from custom_components.meteoswiss import cache as cache_module
from custom_components.meteoswiss.cache import CacheEntry, MeteoSwissCache


@pytest.mark.parametrize(
    "ttl",
    [
        float("nan"),
        float("inf"),
        -float("inf"),
        -1,
        True,
        False,
        "bad",
        object(),
        10**1000,
    ],
)
def test_invalid_lifetimes_never_replace_valid_data(ttl):
    with pytest.raises((ValueError, TypeError)):
        MeteoSwissCache(ttl)
    cache = MeteoSwissCache()
    cache.set("same", 0)
    with pytest.raises((ValueError, TypeError)):
        cache.set("same", 1, ttl=ttl)
    assert cache.get("same") == 0


def test_zero_lifetime_is_immediately_expired_and_none_is_not_negative_cached():
    cache = MeteoSwissCache(default_ttl=0)
    cache.set("zero", 0)
    assert cache.get("zero") is None
    cache = MeteoSwissCache()
    factory = Mock(return_value=None)
    assert cache.get_or_set("missing", factory) is None
    assert cache.get_or_set("missing", factory) is None
    assert factory.call_count == 2
    assert cache.get_stats()["entries"] == 0
    cache.set("replace", 1)
    cache.set("replace", None)
    assert cache.get("replace") is None


@pytest.mark.parametrize("value", [0, False, [], {}])
def test_falsey_values_are_cached_without_recomputing(value):
    cache = MeteoSwissCache()
    factory = Mock(return_value=value)
    assert cache.get_or_set("key", factory) == value
    assert cache.get_or_set("key", factory) == value
    factory.assert_called_once()


def test_failed_factory_does_not_store_partial_data():
    cache = MeteoSwissCache()
    factory = Mock(side_effect=ValueError("invalid source response"))
    with pytest.raises(ValueError):
        cache.get_or_set("data", factory)
    assert cache.get_stats()["entries"] == 0
    assert cache.get_or_set("data", lambda: {"temperature": 0}) == {"temperature": 0}


def test_expired_unrequested_entries_are_cleaned_and_stats_reset_keeps_values():
    with patch(
        "custom_components.meteoswiss.cache.time.monotonic", return_value=10
    ) as clock:
        cache = MeteoSwissCache(default_ttl=10)
        cache.set("old", 1)
        assert cache.get("absent") is None
        assert cache.get("old") == 1
        clock.return_value = 20
        cache.set("new", 0)
        stats = cache.get_stats()
        assert stats == {
            "entries": 1,
            "hits": 1,
            "misses": 1,
            "evictions": 1,
            "hit_rate": 50,
            "total_requests": 2,
        }
        cache.reset_stats()
        assert cache.get_stats()["total_requests"] == 0
        assert cache.get("new") == 0
        cache.clear()
        assert cache.get_stats()["entries"] == 0
        cache.invalidate("absent")
        cache.set("new", 2)
        cache.invalidate("new")
        assert cache.get("new") is None
        cache.set("expired", 1, ttl=1)
        clock.return_value = 21
        assert cache.get_stats()["entries"] == 0
        assert cache.cleanup_expired() == 0


def test_key_boundaries_types_and_keyword_order_cannot_mix_sources():
    cache = MeteoSwissCache()
    assert cache.make_key("source", a=1, b=2) == cache.make_key("source", b=2, a=1)
    keys = [
        cache.make_key("source:a", "b"),
        cache.make_key("source", "a:b"),
        cache.make_key("source", 1),
        cache.make_key("source", "1"),
    ]
    assert len(set(keys)) == 4
    for i, key in enumerate(keys):
        cache.set(key, i)
    assert [cache.get(key) for key in keys] == list(range(4))
    long_key = cache.make_key("source", "https://example.invalid/" + "x" * 500)
    assert len(long_key) <= 200
    assert long_key != cache.make_key("other", "https://example.invalid/" + "x" * 500)
    assert "example.invalid" not in long_key


def test_entry_snapshot_roundtrip_preserves_deadline_and_copies_nested_values():
    with patch(
        "custom_components.meteoswiss.cache.time.monotonic", return_value=10
    ) as clock:
        entry = CacheEntry("data", {"values": [0]}, 10, 5)
        exported = entry.to_dict()
        restored = CacheEntry(**exported)
        assert not restored.is_expired()
        exported["value"]["values"].append(1)
        assert entry.value == {"values": [0]}
        clock.return_value = 15
        assert restored.is_expired()


def test_global_cache_lifetimes_and_clear_are_independent(monkeypatch):
    for name in ("_current_weather_cache", "_forecast_cache", "_stations_cache"):
        monkeypatch.setattr(cache_module, name, None)
    cache_module.clear_all_caches()
    with patch(
        "custom_components.meteoswiss.cache.time.monotonic", return_value=10
    ) as clock:
        weather = cache_module.get_current_weather_cache()
        forecast = cache_module.get_forecast_cache()
        stations = cache_module.get_stations_cache()
        assert weather is cache_module.get_current_weather_cache()
        assert forecast is cache_module.get_forecast_cache()
        assert stations is cache_module.get_stations_cache()
        for cache in (weather, forecast, stations):
            cache.set("same", 0)
        clock.return_value = 610
        assert weather.get("same") is None
        assert forecast.get("same") == stations.get("same") == 0
        clock.return_value = 1810
        assert forecast.get("same") is None
        assert stations.get("same") == 0
        assert set(cache_module.get_all_cache_stats()) == {
            "current_weather",
            "forecast",
            "stations",
        }
        cache_module.clear_all_caches()
        assert all(
            stats["entries"] == 0
            for stats in cache_module.get_all_cache_stats().values()
        )

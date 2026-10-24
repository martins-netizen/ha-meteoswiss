"""Diagnostics support for MeteoSwiss."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.redact import async_redact_data
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .cache import get_all_cache_stats
from .const import (
    CONF_FORECAST_LOCATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POLLEN_STATION,
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DATA_SOURCE_METEOSWISS,
    DATA_SOURCE_OPENMETEO,
)
from .forecast_location_config import resolve_forecast_target
from .runtime_data import MeteoSwissConfigEntry
from .stations_map import get_stations_map
from .version import __version__
from .weather_data import forecast_datetime

TO_REDACT = {
    CONF_FORECAST_LOCATION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POLLEN_STATION,
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
}

COORDINATORS = (
    "coordinator",
    "forecast_coordinator",
    "station_condition_coordinator",
    "alerts_coordinator",
    "pollen_coordinator",
    "meteoswiss_pollen_coordinator",
    "hourly_precipitation_coordinator",
    "precipitation_archive_coordinator",
)


def _location_sources(data_source: str | None) -> dict[str, str]:
    # Describe where each data family is geographically anchored without
    # exposing coordinates, postal codes, or station identifiers.
    if data_source == DATA_SOURCE_METEOSWISS:
        return {
            "observations": "meteoswiss_station",
            "weather_forecast": "home_assistant",
            "pollen_forecast": "home_assistant",
            "weather_alerts": "postal_code",
            "measured_pollen": "meteoswiss_pollen_station",
        }

    if data_source == DATA_SOURCE_OPENMETEO:
        return {
            "observations": "configured_location",
            "weather_forecast": "configured_location",
            "pollen_forecast": "configured_location",
            "weather_alerts": "postal_code",
            "measured_pollen": "meteoswiss_pollen_station",
        }

    return {
        "observations": "unknown",
        "weather_forecast": "unknown",
        "pollen_forecast": "unknown",
        "weather_alerts": "postal_code",
        "measured_pollen": "meteoswiss_pollen_station",
    }


def _summarize_data(data: Any) -> dict[str, Any]:
    """Return non-sensitive information about coordinator data."""
    if data is None:
        return {
            "type": "none",
            "item_count": 0,
        }

    if isinstance(data, dict):
        return {
            "type": "dict",
            "item_count": len(data),
        }

    if isinstance(data, (list, tuple, set, frozenset)):
        return {
            "type": type(data).__name__,
            "item_count": len(data),
        }

    return {
        "type": type(data).__name__,
    }


def _coordinator_diagnostics(
    coordinator: DataUpdateCoordinator[Any],
    role: str,
) -> dict[str, Any]:
    """Return non-sensitive diagnostics for a coordinator."""
    update_interval = coordinator.update_interval

    diagnostics: dict[str, Any] = {
        "name": role,
        "last_update_success": coordinator.last_update_success,
        "update_interval_seconds": (
            update_interval.total_seconds() if update_interval is not None else None
        ),
        "data": _summarize_data(coordinator.data),
    }

    if coordinator.last_exception is not None:
        diagnostics["last_exception"] = type(coordinator.last_exception).__name__

    data_source = getattr(coordinator, "data_source", None)
    if data_source is not None:
        diagnostics["data_source"] = _data_source(data_source)

    sample = coordinator.data
    if isinstance(sample, (list, tuple)):
        sample = next((item for item in sample if isinstance(item, dict)), {})
    if isinstance(sample, dict):
        timestamp = _safe_timestamp(
            sample.get("last_update") or sample.get("fetched_at")
        )
        if timestamp is not None:
            diagnostics["data_timestamp"] = timestamp
    last_success = _safe_timestamp(getattr(coordinator, "last_successful_update", None))
    if last_success is not None:
        diagnostics["last_successful_update"] = last_success
    return diagnostics


def _data_source(value: Any) -> str:
    return (
        value
        if isinstance(value, str)
        and value in {DATA_SOURCE_METEOSWISS, DATA_SOURCE_OPENMETEO, "open-meteo"}
        else "unknown"
    )


def _safe_timestamp(value: Any) -> str | None:
    if isinstance(value, datetime):
        return value.astimezone(UTC).isoformat() if value.tzinfo is not None else None
    timestamp = forecast_datetime(value)
    return timestamp.isoformat() if timestamp is not None else None


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: MeteoSwissConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a MeteoSwiss config entry."""
    entry_data = getattr(entry, "runtime_data", None)
    data_source = _data_source(
        getattr(
            entry_data,
            "data_source",
            entry.data.get("data_source", DATA_SOURCE_METEOSWISS),
        )
    )

    coordinators: dict[str, Any] = {}

    for key in COORDINATORS:
        coordinator = getattr(entry_data, key, None)
        if coordinator is None:
            coordinators[key] = {"available": False}
            continue

        coordinators[key] = {
            "available": True,
            **_coordinator_diagnostics(coordinator, key),
        }

    target = resolve_forecast_target(entry.data, None, None)
    location_sources = _location_sources(data_source)
    if target.status == "catalogue":
        location_sources["weather_forecast"] = "meteoswiss_catalogue"
    elif target.status == "invalid":
        location_sources["weather_forecast"] = "invalid_selection"

    return {
        "integration_version": __version__,
        "config_entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": async_redact_data(dict(entry.options), TO_REDACT),
            "version": entry.version,
            "minor_version": entry.minor_version,
        },
        "data_source": data_source,
        "location_sources": location_sources,
        "forecast_location": {
            "status": target.status,
            "elevation_mode": target.elevation_mode,
        },
        "runtime_data_present": entry_data is not None,
        "cache": get_all_cache_stats(),
        "station_catalogue": (await get_stations_map(load=False)).get_status(),
        "coordinators": coordinators,
    }

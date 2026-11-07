"""Shared entity metadata without changing source or coordinator behaviour."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, Entity
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .forecast_location_config import ForecastTarget

from .const import (
    ATTRIBUTION,
    DATA_SOURCE_METEOSWISS,
    DATA_SOURCE_OPENMETEO,
    DOMAIN,
    OPENMETEO_CURRENT_ATTRIBUTION,
    OPENMETEO_AIR_QUALITY_DEVICE_NAME,
    OPENMETEO_AIR_QUALITY_MANUFACTURER,
    OPENMETEO_AIR_QUALITY_MODEL,
)


class MeteoSwissEntity(Entity):
    """Common naming and default attribution; source families retain overrides."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION


class MeteoSwissCoordinatorEntity[CoordinatorT: DataUpdateCoordinator[Any]](
    CoordinatorEntity[CoordinatorT], MeteoSwissEntity
):
    """Retain HA coordinator availability, polling and listener lifecycle."""


def current_weather_attribution(data_source: str) -> str:
    """Name the selected current source, independently of forecast/pollen."""
    return (
        OPENMETEO_CURRENT_ATTRIBUTION
        if data_source == DATA_SOURCE_OPENMETEO
        else ATTRIBUTION
    )


def weather_device_info(
    entry_id: str, station_name: str, *, data_source: str = DATA_SOURCE_METEOSWISS
) -> DeviceInfo:
    """Keep one current-weather identity with provider-specific default labels."""
    if data_source == DATA_SOURCE_OPENMETEO:
        return DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, entry_id)},
            name="Open-Meteo Current Weather",
            manufacturer="Open-Meteo",
            model="Weather Forecast API",
        )
    return DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, entry_id)},
        name=f"MeteoSwiss {station_name}",
        manufacturer="MeteoSwiss",
        model="SwissMetNet",
    )


def air_quality_device_info(entry_id: str) -> DeviceInfo:
    """Keep modelled pollen/AQ on their existing shared provider device."""
    return DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, f"pollen_{entry_id}")},
        name=OPENMETEO_AIR_QUALITY_DEVICE_NAME,
        manufacturer=OPENMETEO_AIR_QUALITY_MANUFACTURER,
        model=OPENMETEO_AIR_QUALITY_MODEL,
    )


def forecast_device_info(entry_id: str, target: ForecastTarget) -> DeviceInfo:
    """Reuse the HGT device identity for one explicitly labelled forecast group."""
    if target.location is not None:
        key = "forecast_catalogue"
        placeholders = {"location": target.location.point.name}
    else:
        key = "forecast_base" if target.status == "legacy" else "forecast_invalid"
        placeholders = {}
    return DeviceInfo(
        entry_type=DeviceEntryType.SERVICE,
        identifiers={(DOMAIN, f"calculated_{entry_id}")},
        manufacturer="MeteoSwiss",
        model="ICON Seamless via Open-Meteo",
        translation_key=key,
        translation_placeholders=placeholders,
    )

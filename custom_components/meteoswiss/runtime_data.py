"""Typed, entry-owned runtime state; nothing here is persisted in config data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from homeassistant.config_entries import ConfigEntry

if TYPE_CHECKING:
    from aiohttp import ClientSession

    from .coordinator import (
        MeteoSwissAlertsCoordinator,
        MeteoSwissDataUpdateCoordinator,
        MeteoSwissForecastCoordinator,
        MeteoSwissHourlyPrecipitationCoordinator,
        MeteoSwissPollenCoordinator,
        MeteoSwissStationConditionCoordinator,
        OpenMeteoDataUpdateCoordinator,
        OpenMeteoPollenCoordinator,
    )
    from .forecast_location_config import ForecastTarget


@dataclass(slots=True)
class MeteoSwissRuntimeData:
    """Coordinators and the borrowed HA session for a single config entry."""

    coordinator: MeteoSwissDataUpdateCoordinator | OpenMeteoDataUpdateCoordinator
    data_source: str
    session: ClientSession
    forecast_target: ForecastTarget | None = None
    forecast_coordinator: MeteoSwissForecastCoordinator | None = None
    station_condition_coordinator: MeteoSwissStationConditionCoordinator | None = None
    alerts_coordinator: MeteoSwissAlertsCoordinator | None = None
    pollen_coordinator: OpenMeteoPollenCoordinator | None = None
    meteoswiss_pollen_coordinator: MeteoSwissPollenCoordinator | None = None
    hourly_precipitation_coordinator: (
        MeteoSwissHourlyPrecipitationCoordinator | None
    ) = None
    precipitation_archive_coordinator: (
        MeteoSwissHourlyPrecipitationCoordinator | None
    ) = None


type MeteoSwissConfigEntry = ConfigEntry[MeteoSwissRuntimeData]

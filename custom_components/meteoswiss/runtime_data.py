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
        MeteoSwissPollenCoordinator,
    )
    from .forecast_coordinator import MeteoSwissForecastCoordinator
    from .openmeteo_coordinator import OpenMeteoDataUpdateCoordinator
    from .pollen_coordinator_openmeteo import OpenMeteoPollenCoordinator
    from .precipitation import MeteoSwissHourlyPrecipitationCoordinator


@dataclass(slots=True)
class MeteoSwissRuntimeData:
    """Coordinators and the borrowed HA session for a single config entry."""

    coordinator: MeteoSwissDataUpdateCoordinator | OpenMeteoDataUpdateCoordinator
    data_source: str
    session: ClientSession
    forecast_coordinator: MeteoSwissForecastCoordinator | None = None
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

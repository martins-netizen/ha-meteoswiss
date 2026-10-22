"""The meteoswiss integration."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .alerts import MeteoSwissAlertsAPI
from .const import (
    CONF_DATA_SOURCE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POLLEN_STATION,
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    CONF_UPDATE_INTERVAL,
    DATA_SOURCE_METEOSWISS,
    DATA_SOURCE_OPENMETEO,
    DEFAULT_POLLEN_STATION,
    DEFAULT_UPDATE_INTERVAL_SEC,
    DOMAIN,
)
from .coordinator import (
    MeteoSwissAlertsCoordinator,
    MeteoSwissDataUpdateCoordinator,
    MeteoSwissPollenCoordinator,
    OpenMeteoDataUpdateCoordinator,
)
from .forecast_coordinator import MeteoSwissForecastCoordinator
from .localization import async_load_warning_labels
from .precipitation import (
    ARCHIVE_LOOKBACK_MONTHS,
    ARCHIVE_UPDATE_INTERVAL,
    MeteoSwissHourlyPrecipitationCoordinator,
)
from .runtime_data import MeteoSwissConfigEntry, MeteoSwissRuntimeData

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.WEATHER,
    Platform.BINARY_SENSOR,
]


def _get_forecast_coordinates(
    hass: HomeAssistant,
    entry: MeteoSwissConfigEntry,
    data_source: str,
) -> tuple[float, float]:
    """Return coordinates used for forecasts and location-based pollen data."""
    if data_source == DATA_SOURCE_METEOSWISS:
        # Observations are station-based, while forecasts should describe
        # the Home Assistant installation location.
        return hass.config.latitude, hass.config.longitude

    latitude = entry.data.get(CONF_LATITUDE)
    longitude = entry.data.get(CONF_LONGITUDE)

    # Open-Meteo entries are explicitly location-based. Fall back to the
    # Home Assistant location only for older/incomplete entries.
    if latitude is None:
        latitude = hass.config.latitude
    if longitude is None:
        longitude = hass.config.longitude

    return latitude, longitude


async def _async_refresh_optional_coordinators(*coordinators) -> None:
    """Refresh optional coordinators without delaying config entry setup."""
    await asyncio.gather(
        *(coordinator.async_refresh() for coordinator in coordinators),
        return_exceptions=True,
    )


def _keep_coordinator_polling(
    entry: MeteoSwissConfigEntry,
    coordinator: MeteoSwissHourlyPrecipitationCoordinator,
) -> None:
    """Keep a coordinator without entity listeners polling until unload."""
    entry.async_on_unload(coordinator.async_add_listener(lambda: None))


async def async_setup_entry(hass: HomeAssistant, entry: MeteoSwissConfigEntry) -> bool:
    """Set up MeteoSwiss integration from a config entry."""
    _LOGGER.info("Setting up MeteoSwiss integration")

    hass.data.setdefault(DOMAIN, {})
    # HA owns this verified-TLS session, including when initial setup fails.
    # Coordinators borrow it and must never close it themselves.
    shared_session = async_get_clientsession(hass)

    # Create coordinator based on data source
    update_interval = entry.options.get(
        CONF_UPDATE_INTERVAL,
        entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL_SEC),
    )
    data_source = entry.data.get(CONF_DATA_SOURCE, DATA_SOURCE_METEOSWISS)
    station_id = entry.data.get(CONF_STATION_ID)
    post_code = entry.data.get(CONF_POSTAL_CODE)
    lat, lon = _get_forecast_coordinates(hass, entry, data_source)

    if data_source == DATA_SOURCE_OPENMETEO:
        # Alternative modelled current conditions; ICON forecasts stay separate.
        coordinator = OpenMeteoDataUpdateCoordinator(
            hass,
            latitude=lat,
            longitude=lon,
            update_interval=update_interval,
            session=shared_session,
        )
        _LOGGER.debug("Using Open-Meteo current conditions")

        forecast_coordinator = MeteoSwissForecastCoordinator(
            hass,
            latitude=lat,
            longitude=lon,
            post_code=post_code,
            update_interval=3600,
            session=shared_session,
        )
        hourly_precipitation_coordinator = None
        precipitation_archive_coordinator = None

    else:
        # Use MeteoSwiss API for current weather
        coordinator = MeteoSwissDataUpdateCoordinator(
            hass,
            station_id=station_id,
            update_interval=update_interval,
            session=shared_session,
        )
        _LOGGER.debug("Using MeteoSwiss station observations")

        # Forecasts are location-based and intentionally independent from
        # the selected observation station.
        forecast_coordinator = MeteoSwissForecastCoordinator(
            hass,
            station_id=station_id,
            latitude=lat,
            longitude=lon,
            post_code=post_code,
            update_interval=3600,
            session=shared_session,
        )
        _LOGGER.debug("Forecast coordinator uses Home Assistant location")
        hourly_precipitation_coordinator = None
        precipitation_archive_coordinator = None
        if "recorder" in hass.config.components:
            hourly_precipitation_coordinator = MeteoSwissHourlyPrecipitationCoordinator(
                hass,
                station_id=station_id,
                session=shared_session,
            )
            precipitation_archive_coordinator = (
                MeteoSwissHourlyPrecipitationCoordinator(
                    hass,
                    station_id=station_id,
                    session=shared_session,
                    asset_periods=("historical", "recent"),
                    update_interval=ARCHIVE_UPDATE_INTERVAL,
                    lookback_months=ARCHIVE_LOOKBACK_MONTHS,
                )
            )

    # Fetch initial data for current weather
    await coordinator.async_config_entry_first_refresh()

    # Create alerts API and coordinator
    alerts_api = MeteoSwissAlertsAPI(session=shared_session)
    alerts_api.postal_code = post_code

    alerts_coordinator = MeteoSwissAlertsCoordinator(
        hass,
        alerts_api=alerts_api,
        update_interval=600,  # 10 minutes
        warning_labels=await async_load_warning_labels(hass),
    )

    # Create pollen API and coordinator (using Open-Meteo Air Quality API)
    from .pollen_coordinator_openmeteo import OpenMeteoPollenCoordinator

    # Location-based pollen forecast follows the same coordinates as weather.
    pollen_coordinator = OpenMeteoPollenCoordinator(
        hass,
        latitude=lat,
        longitude=lon,
        update_interval=1800,  # 30 minutes
        session=shared_session,
    )

    # Create MeteoSwiss measured pollen coordinator
    pollen_station = entry.options.get(CONF_POLLEN_STATION, DEFAULT_POLLEN_STATION)
    meteoswiss_pollen_coordinator = MeteoSwissPollenCoordinator(
        hass,
        station_id=pollen_station,
        update_interval=3600,  # 1 hour
        session=shared_session,
    )

    entry.runtime_data = MeteoSwissRuntimeData(
        coordinator=coordinator,
        forecast_coordinator=forecast_coordinator,
        alerts_coordinator=alerts_coordinator,
        pollen_coordinator=pollen_coordinator,
        meteoswiss_pollen_coordinator=meteoswiss_pollen_coordinator,
        hourly_precipitation_coordinator=hourly_precipitation_coordinator,
        precipitation_archive_coordinator=precipitation_archive_coordinator,
        data_source=data_source,
        session=shared_session,
    )

    # Set up platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Refresh optional data in parallel after entities are registered
    optional_coordinators = [
        forecast_coordinator,
        alerts_coordinator,
        pollen_coordinator,
        meteoswiss_pollen_coordinator,
    ]
    if hourly_precipitation_coordinator is not None:
        optional_coordinators.append(hourly_precipitation_coordinator)
        # External Recorder statistics have no CoordinatorEntity listener.
        # DataUpdateCoordinator only schedules periodic refreshes while at
        # least one listener is registered.
        _keep_coordinator_polling(entry, hourly_precipitation_coordinator)
    if precipitation_archive_coordinator is not None:
        optional_coordinators.append(precipitation_archive_coordinator)
        _keep_coordinator_polling(entry, precipitation_archive_coordinator)

    entry.async_create_background_task(
        hass,
        _async_refresh_optional_coordinators(*optional_coordinators),
        "MeteoSwiss optional initial refresh",
    )

    # Update listeners for reload
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_migrate_entry(
    hass: HomeAssistant, entry: MeteoSwissConfigEntry
) -> bool:
    """Move the legacy polling setting to options without changing its value.

    Schema 1.2 remains readable by 8.2.0: its runtime already prefers options.
    New entries need no saved interval and use the developer-selected default.
    """
    if entry.version != 1:
        return False
    if entry.minor_version < 2:
        data = dict(entry.data)
        options = dict(entry.options)
        if CONF_UPDATE_INTERVAL in data:
            options.setdefault(CONF_UPDATE_INTERVAL, data.pop(CONF_UPDATE_INTERVAL))
        hass.config_entries.async_update_entry(
            entry, data=data, options=options, minor_version=2
        )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: MeteoSwissConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading MeteoSwiss integration")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok and hass.data[DOMAIN].get("diagnostic_owner") == entry.entry_id:
        for key in (
            "diagnostic_owner",
            "stations_map_sensor_added",
            "cache_stats_sensor_added",
        ):
            hass.data[DOMAIN].pop(key, None)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: MeteoSwissConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)

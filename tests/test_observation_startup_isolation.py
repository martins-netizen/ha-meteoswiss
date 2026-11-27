"""A current-weather outage leaves independent services available on startup."""

from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
import logging
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OFF, STATE_UNAVAILABLE
from homeassistant.helpers import entity_registry as er
from ha_helpers import MockConfigEntry, async_fire_time_changed

from custom_components.meteoswiss.alerts import MeteoSwissAlertsAPI
from custom_components.meteoswiss.cache import clear_all_caches
from custom_components.meteoswiss.const import (
    CONF_DATA_SOURCE,
    DATA_SOURCE_METEOSWISS,
    DATA_SOURCE_OPENMETEO,
    DOMAIN,
)
from custom_components.meteoswiss.coordinator import (
    MeteoSwissDataUpdateCoordinator,
    MeteoSwissPollenCoordinator,
)
from custom_components.meteoswiss.forecast import OPEN_METEO_BASE_URL
from custom_components.meteoswiss.openmeteo import OpenMeteoCurrentClient
from custom_components.meteoswiss.pollen_openmeteo import OpenMeteoPollenClient
from custom_components.meteoswiss.stations_map import MeteoSwissStationsMap

NOW = datetime(2026, 11, 27, 7, 20, tzinfo=UTC)
HOUR = int(NOW.replace(minute=0).timestamp())
CSV_URL = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/klo/ogd-smn_klo_t_now.csv"


def _station_csv(observed_at: datetime) -> str:
    return (
        "station_abbr;reference_timestamp;tre200s0;ure200s0;wcc006s0\n"
        f"KLO;{observed_at:%d.%m.%Y %H:%M};12.5;90;\n"
    )


@pytest.fixture(autouse=True)
def _isolated_provider_cache(freezer):
    freezer.move_to(NOW)
    clear_all_caches()
    yield
    clear_all_caches()


@pytest.mark.parametrize("source", [DATA_SOURCE_METEOSWISS, DATA_SOURCE_OPENMETEO])
async def test_startup_observation_failure_isolated_until_scheduled_recovery(
    hass, enable_custom_integrations, aioclient_mock, freezer, caplog, source
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_DATA_SOURCE: source,
            "station_id": "KLO",
            "station_name": "Kloten",
            "postal_code": "8302",
            "latitude": 47.45,
            "longitude": 8.56,
        },
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    aioclient_mock.get(
        OPEN_METEO_BASE_URL,
        json={
            "hourly": {
                "time": [HOUR, HOUR + 3600],
                "temperature_2m": [-10, -9],
                "weather_code": [71, 71],
            },
        },
    )
    # A new file was downloaded successfully, but its sole real measurement
    # is four hours old. The next publication is available on the regular poll.
    aioclient_mock.get(CSV_URL, text=_station_csv(NOW - timedelta(hours=4)))
    current_payload = {"current": {}}

    async def read_current(_client):
        return current_payload

    registry = er.async_get(hass)

    def entity_id(platform, key):
        resolved = registry.async_get_entity_id(
            platform, DOMAIN, f"{DOMAIN}_{entry.entry_id}_{key}"
        )
        assert resolved is not None
        return resolved

    def entity_ids():
        return {
            item.unique_id: item.entity_id
            for item in er.async_entries_for_config_entry(registry, entry.entry_id)
        }

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(MeteoSwissStationsMap, "load_stations", return_value={})
        )
        stack.enter_context(
            patch.object(
                MeteoSwissDataUpdateCoordinator,
                "_async_get_station_data_url",
                return_value=CSV_URL,
            )
        )
        stack.enter_context(
            patch.object(OpenMeteoCurrentClient, "_async_request", read_current)
        )
        stack.enter_context(
            patch.object(MeteoSwissAlertsAPI, "get_alerts", return_value=[])
        )
        stack.enter_context(
            patch.object(
                OpenMeteoPollenClient,
                "async_get_data",
                return_value={
                    "pm10": 14.0,
                    "uv_available": True,
                    "last_update": NOW.isoformat(),
                },
            )
        )
        stack.enter_context(
            patch.object(MeteoSwissPollenCoordinator, "_async_update_data", return_value={})
        )

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert entry.state is ConfigEntryState.LOADED
        runtime = entry.runtime_data
        assert runtime.coordinator.data is None
        assert not runtime.coordinator.last_update_success
        startup_warnings = [
            record.getMessage()
            for record in caplog.records
            if record.name == "custom_components.meteoswiss"
            and record.levelno == logging.WARNING
            and record.getMessage().startswith("Current weather is temporarily unavailable")
        ]
        assert len(startup_warnings) == 1
        message = startup_warnings[0]
        assert all(private_value not in message for private_value in ("https://", "47.45", "8.56"))
        if source == DATA_SOURCE_METEOSWISS:
            assert "240 minutes old" in message
        observed_id = entity_id("sensor", "temperature")
        assert hass.states.get(observed_id).state == STATE_UNAVAILABLE
        current_weather_id = entity_id("weather", "weather")
        assert hass.states.get(current_weather_id).state == STATE_UNAVAILABLE
        identities = entity_ids()

        forecast_id = entity_id("weather", "forecast_weather")
        forecast = await hass.services.async_call(
            "weather",
            "get_forecasts",
            {"entity_id": forecast_id, "type": "hourly"},
            blocking=True,
            return_response=True,
        )
        assert forecast[forecast_id]["forecast"][0]["temperature"] == -10
        assert float(hass.states.get(entity_id("sensor", "pm10")).state) == 14
        assert hass.states.get(entity_id("binary_sensor", "any_alert")).state == STATE_OFF

        upcoming = NOW + timedelta(minutes=11)
        aioclient_mock.clear_requests()
        aioclient_mock.get(CSV_URL, text=_station_csv(upcoming))
        current_payload = {
            "current": {
                "time": int(upcoming.timestamp()),
                "temperature_2m": 12.5,
                "weather_code": 3,
            }
        }
        freezer.move_to(upcoming)
        async_fire_time_changed(hass, upcoming)
        await hass.async_block_till_done(wait_background_tasks=True)

        assert entry.state is ConfigEntryState.LOADED
        assert runtime.coordinator.last_update_success
        assert float(hass.states.get(observed_id).state) == 12.5
        assert entity_ids() == identities

        assert await hass.config_entries.async_unload(entry.entry_id)
        assert not runtime.coordinator._listeners
        assert not runtime.session.closed

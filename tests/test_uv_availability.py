"""A failed optional UV source must not look like a missing valid value."""

from __future__ import annotations

import logging
from contextlib import ExitStack
from unittest.mock import patch

import aiohttp
import pytest
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.cache import clear_all_caches
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.pollen_coordinator_openmeteo import (
    OPENMETEO_AQ_BASE_URL,
    OPENMETEO_FORECAST_URL,
)


@pytest.fixture
async def uv_entry(hass, aioclient_mock, enable_custom_integrations, freezer):
    freezer.move_to("2026-10-17T10:20:00+00:00")
    clear_all_caches()
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"data_source": "meteoswiss", "station_id": "KLO",
              "station_name": "Kloten", "postal_code": "8302"},
    )
    entry.add_to_hass(hass)
    # An AQ zero is valid and must survive a separate UV outage.
    aioclient_mock.get(OPENMETEO_AQ_BASE_URL, json={"hourly": {
        "time": [1792231200], "pm10": [0], "birch_pollen": [0]}})
    aioclient_mock.get(OPENMETEO_FORECAST_URL, json={"current": {"uv_index": 0}})
    with ExitStack() as stack:
        stack.enter_context(patch(
            "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
            return_value={},
        ))
        for target, data in {
            "coordinator.MeteoSwissDataUpdateCoordinator": {"temperature": 12},
            "forecast_coordinator.MeteoSwissForecastCoordinator": [],
            "binary_sensor.MeteoSwissAlertsCoordinator": [],
            "pollen_meteoswiss.MeteoSwissPollenCoordinator": {"birch": {"current": 0}},
        }.items():
            stack.enter_context(patch(
                f"custom_components.meteoswiss.{target}._async_update_data",
                return_value=data,
            ))
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        ids = {key: registry.async_get_entity_id(
            "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_{suffix}"
        ) for key, suffix in {"uv": "uv_index", "aq": "pm10",
                             "pollen": "pollen_birch_pollen"}.items()}
        assert all(ids.values())
        coordinator = entry.runtime_data.pollen_coordinator
        yield coordinator, ids
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert not coordinator._listeners
    clear_all_caches()


@pytest.mark.parametrize("failed_response", [
    {"status": 503},
    {"exc": TimeoutError("https://private.example/47.451234/8.561234")},
    {"exc": aiohttp.ClientConnectionError("private_uv_marker")},
    {"text": "private_uv_marker is not JSON"},
    {"json": {"current": []}},
    {"json": []},
])
async def test_uv_outage_is_local_private_once_and_recovers(
    hass, aioclient_mock, uv_entry, caplog, failed_response
):
    coordinator, ids = uv_entry
    assert hass.states.get(ids["uv"]).state == "0.0"
    caplog.clear()
    with caplog.at_level(logging.DEBUG, logger=coordinator.logger.name):
        for index in range(3):
            # The third call uses the cached failed UV result.
            if index < 2:
                clear_all_caches()
                aioclient_mock.clear_requests()
                aioclient_mock.get(OPENMETEO_AQ_BASE_URL, json={"hourly": {
                    "time": [1792231200], "pm10": [0], "birch_pollen": [0]}})
                aioclient_mock.get(OPENMETEO_FORECAST_URL, **failed_response)
            await coordinator.async_refresh()
            assert coordinator.last_update_success
            assert hass.states.get(ids["uv"]).state == "unavailable"
            assert hass.states.get(ids["aq"]).state == "0.0"
            assert hass.states.get(ids["pollen"]).state == "0.0"
        messages = [r.getMessage() for r in caplog.records
                    if r.name == coordinator.logger.name]
        assert messages.count("Optional UV response unavailable") == 1
        # Successful request, missing single value: unknown is now meaningful.
        clear_all_caches()
        aioclient_mock.clear_requests()
        aioclient_mock.get(OPENMETEO_AQ_BASE_URL, json={"hourly": {
            "time": [1792231200], "pm10": [0]}})
        aioclient_mock.get(OPENMETEO_FORECAST_URL, json={"current": {}})
        await coordinator.async_refresh()
        assert hass.states.get(ids["uv"]).state == "unknown"
        clear_all_caches()
        aioclient_mock.clear_requests()
        aioclient_mock.get(OPENMETEO_AQ_BASE_URL, json={"hourly": {
            "time": [1792231200], "pm10": [0]}})
        aioclient_mock.get(OPENMETEO_FORECAST_URL, json={"current": {"uv_index": 2.5}})
        await coordinator.async_refresh()
        assert hass.states.get(ids["uv"]).state == "2.5"
        messages = [r.getMessage() for r in caplog.records
                    if r.name == coordinator.logger.name]
        assert messages.count("Optional UV response recovered") == 1
    logs = "\n".join(logging.Formatter().format(r) for r in caplog.records
                     if r.name.startswith("custom_components.meteoswiss"))
    assert all(secret not in logs for secret in (
        "47.451234", "8.561234", "private_uv_marker", "private.example"))
    registry = er.async_get(hass)
    assert registry.async_get(ids["uv"]).unique_id.endswith("_uv_index")

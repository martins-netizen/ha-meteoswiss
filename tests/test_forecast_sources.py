"""Forecast validity, transport, private logging and HA recovery contracts."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.cache import clear_all_caches, get_forecast_cache
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.forecast_coordinator import (
    OPEN_METEO_BASE_URL,
    MeteoSwissForecastCoordinator,
)

NOW = datetime(2026, 10, 16, 7, 20, tzinfo=UTC)
HOUR = int(NOW.replace(minute=0).timestamp())
CACHE_KEY = "forecast:v3:icon-seamless:47.451234,8.561234"


@pytest.fixture(autouse=True)
def isolated_clock_and_cache(freezer):
    clear_all_caches()
    freezer.move_to(NOW)
    yield
    clear_all_caches()


def payload(**series):
    return {
        "hourly": {"time": [HOUR, HOUR + 3600], "temperature_2m": [0, -2], **series}
    }


def coordinator(hass):
    return MeteoSwissForecastCoordinator(
        hass,
        latitude=47.451234,
        longitude=8.561234,
        session=async_get_clientsession(hass),
    )


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {},
        {"hourly": None},
        {"hourly": []},
        {"hourly": {"time": []}},
        {"hourly": {"time": "broken"}},
        payload(time=[True]),
        payload(time=["bad"]),
        payload(time=[float("inf")]),
        payload(time=[HOUR, HOUR]),
        payload(time=[HOUR + 3600, HOUR]),
        payload(time=[HOUR - 3600]),
        payload(time=[HOUR + 7200]),
        payload(temperature_2m=None),
        payload(temperature_2m="12"),
        payload(temperature_2m=[None, None]),
        payload(temperature_2m=[True, "nan"]),
        payload(time=[HOUR - 3600, HOUR], temperature_2m=[5, None]),
        {**payload(), "daily": []},
        {**payload(), "daily": {"time": ["bad"]}},
        {**payload(), "daily": {"time": [HOUR], "temperature_2m_min": 3}},
        {**payload(), "utc_offset_seconds": float("nan")},
        {**payload(), "utc_offset_seconds": 86400},
        {**payload(), "utc_offset_seconds": True},
    ],
)
async def test_invalid_response_fails_once_without_caching(hass, aioclient_mock, data):
    aioclient_mock.get(OPEN_METEO_BASE_URL, text=json.dumps(data))
    with pytest.raises(UpdateFailed):
        await coordinator(hass)._async_update_data()
    assert len(aioclient_mock.mock_calls) == 1
    assert get_forecast_cache().get(CACHE_KEY) is None


@pytest.mark.parametrize(
    "response,attempts",
    [
        ({"status": 404}, 1),
        ({"status": 429}, 3),
        ({"status": 503}, 3),
        ({"exc": TimeoutError()}, 3),
        ({"exc": aiohttp.ClientConnectionError("connection failed")}, 3),
        ({"text": "broken JSON"}, 1),
        ({"exc": UnicodeError("invalid encoding")}, 1),
    ],
)
async def test_transport_retry_policy_and_private_errors(
    hass, aioclient_mock, caplog, response, attempts
):
    aioclient_mock.get(OPEN_METEO_BASE_URL, **response)
    source = coordinator(hass)
    with (
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ),
        caplog.at_level(logging.DEBUG, logger=source.logger.name),
    ):
        await source.async_refresh()
    assert not source.last_update_success
    assert len(aioclient_mock.mock_calls) == attempts
    logs = "\n".join(
        logging.Formatter().format(r)
        for r in caplog.records
        if r.name == source.logger.name
    )
    assert "47.451234" not in logs
    assert "8.561234" not in logs
    assert "latitude=" not in logs
    assert "Failed to fetch Open-Meteo forecast" in logs


async def test_zero_partial_numeric_and_daily_values_keep_their_meaning(
    hass, aioclient_mock
):
    data = payload(
        relative_humidity_2m=[0, 101],
        precipitation_probability=[0, -1],
        precipitation=[0],
        windspeed_10m=[0, -1],
        winddirection_10m=[360, 361],
        snowfall=[0, "inf"],
        freezing_level_height=[-20, None],
        weather_code=[0, {"bad": 0}],
        is_day=[0, 2],
    )
    data.update(
        utc_offset_seconds=7200,
        daily={
            "time": [datetime(2026, 10, 15, 22, tzinfo=UTC).timestamp()],
            "temperature_2m_max": [0],
            "temperature_2m_min": [-3],
            "temperature_2m_mean": [-1],
            "precipitation_sum": [0],
            "precipitation_probability_max": [0],
        },
    )
    aioclient_mock.get(OPEN_METEO_BASE_URL, json=data)
    first, second = await coordinator(hass)._async_update_data()
    assert first["temperature"] == 0
    assert first["humidity"] == 0
    assert first["precipitation"] == 0
    assert first["wind_speed"] == 0
    assert first["wind_direction"] == 360
    assert first["freezing_level_height"] == -20
    assert first["condition"] == "clear-night"
    assert first["daily_temperature_min"] == -3
    assert first["daily_temperature_max"] == 0
    assert first["daily_temperature_mean"] == -1
    assert first["daily_precipitation"] == 0
    assert first["daily_precipitation_probability"] == 0
    assert second["temperature"] == -2
    assert all(
        second[key] is None
        for key in [
            "humidity",
            "precipitation_probability",
            "precipitation",
            "wind_speed",
            "wind_direction",
            "snowfall",
            "condition",
            "is_day",
        ]
    )
    assert first["datetime"] == "2026-10-16T07:00:00+00:00"
    assert first["fetched_at"] == NOW.isoformat()
    assert first["source"] == "meteoswiss_icon_seamless_via_open_meteo"


@pytest.mark.parametrize(
    "invalid", [None, True, "bad", {}, [], float("nan"), float("inf"), 10**400]
)
def test_invalid_individual_values_remain_missing(hass, invalid):
    rows = MeteoSwissForecastCoordinator(
        hass, latitude=47.45, longitude=8.56
    )._parse_response(payload(temperature_2m=[invalid, 0]))
    assert rows[0]["temperature"] is None
    assert rows[1]["temperature"] == 0


async def test_empty_cache_cannot_rescue_failed_feed(hass, aioclient_mock):
    get_forecast_cache().set(CACHE_KEY, [])
    aioclient_mock.get(OPEN_METEO_BASE_URL, json={})
    with pytest.raises(UpdateFailed):
        await coordinator(hass)._async_update_data()
    assert len(aioclient_mock.mock_calls) == 1


async def test_valid_cache_is_shared_and_expiry_fetches_again(
    hass, aioclient_mock, freezer
):
    aioclient_mock.get(OPEN_METEO_BASE_URL, json=payload())
    first, second = coordinator(hass), coordinator(hass)
    rows = await first._async_update_data()
    second._consecutive_failures = 4
    assert await second._async_update_data() == rows
    assert second._consecutive_failures == 0
    assert len(aioclient_mock.mock_calls) == 1
    freezer.move_to(NOW + timedelta(minutes=31))
    refreshed = await second._async_update_data()
    assert len(aioclient_mock.mock_calls) == 2
    assert refreshed[0]["fetched_at"] != rows[0]["fetched_at"]


async def test_circuit_breaker_defers_requests_and_recovers(
    hass, aioclient_mock, freezer
):
    source = coordinator(hass)
    aioclient_mock.get(OPEN_METEO_BASE_URL, json={})
    for _ in range(5):
        await source.async_refresh()
    assert not source.last_update_success
    assert len(aioclient_mock.mock_calls) == 5
    with pytest.raises(UpdateFailed, match="Circuit breaker open"):
        await source._async_update_data()
    assert len(aioclient_mock.mock_calls) == 5
    freezer.move_to(NOW + timedelta(minutes=5))
    aioclient_mock.clear_requests()
    aioclient_mock.get(OPEN_METEO_BASE_URL, json=payload())
    await source.async_refresh()
    assert source.last_update_success
    assert source._circuit_open_until is None
    assert source._consecutive_failures == 0


async def test_cancellation_and_setup_errors_are_not_retried(hass, aioclient_mock):
    source = coordinator(hass)
    aioclient_mock.get(OPEN_METEO_BASE_URL, exc=asyncio.CancelledError())
    with pytest.raises(asyncio.CancelledError):
        await source._async_update_data()
    assert len(aioclient_mock.mock_calls) == 1
    assert source._consecutive_failures == 0
    with pytest.raises(RuntimeError, match="No session"):
        await MeteoSwissForecastCoordinator(
            hass, latitude=47.45, longitude=8.56
        )._async_update_data()
    with pytest.raises(UpdateFailed):
        await MeteoSwissForecastCoordinator(
            hass, session=async_get_clientsession(hass)
        )._async_update_data()
    assert len(aioclient_mock.mock_calls) == 1
    await source.async_close()
    assert not source._session.closed
    assert source.data_source == "open-meteo"
    assert source._map_open_meteo_condition(0, is_night=True) == "clear-night"
    assert source._map_open_meteo_condition(999) is None


async def test_registered_weather_survives_forecast_failure_and_recovers(
    hass,
    aioclient_mock,
    enable_custom_integrations,
    caplog,
):
    hass.config.latitude, hass.config.longitude = 47.451234, 8.561234
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "station_id": "KLO",
            "station_name": "Kloten",
            "postal_code": "8302",
            "data_source": "meteoswiss",
        },
    )
    entry.add_to_hass(hass)
    aioclient_mock.get(OPEN_METEO_BASE_URL, json=payload())
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
                return_value={},
            )
        )
        for target, data in {
            "coordinator.MeteoSwissDataUpdateCoordinator": {
                "temperature": 12,
                "last_update": NOW.isoformat(),
            },
            "binary_sensor.MeteoSwissAlertsCoordinator": [],
            "pollen_coordinator_openmeteo.OpenMeteoPollenCoordinator": {},
            "pollen_meteoswiss.MeteoSwissPollenCoordinator": {},
        }.items():
            stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.{target}._async_update_data",
                    return_value=data,
                )
            )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        entity_id = next(
            row.entity_id
            for row in er.async_entries_for_config_entry(
                er.async_get(hass), entry.entry_id
            )
            if row.domain == "weather"
        )

        async def forecasts(kind):
            result = await hass.services.async_call(
                "weather",
                "get_forecasts",
                {"entity_id": entity_id, "type": kind},
                blocking=True,
                return_response=True,
            )
            return result[entity_id]["forecast"]

        assert (await forecasts("hourly"))[0]["temperature"] == 0
        assert await forecasts("daily")
        source = entry.runtime_data.forecast_coordinator
        saved = source.data
        clear_all_caches()
        aioclient_mock.clear_requests()
        aioclient_mock.get(OPEN_METEO_BASE_URL, json={})
        caplog.clear()
        for _ in range(2):
            await source.async_refresh()
        assert source.data == saved
        assert hass.states.get(entity_id).state != "unavailable"
        assert await forecasts("hourly") == []
        assert await forecasts("daily") == []
        errors = [
            r
            for r in caplog.records
            if r.name == source.logger.name and r.levelno == logging.ERROR
        ]
        assert len(errors) == 1
        aioclient_mock.clear_requests()
        aioclient_mock.get(OPEN_METEO_BASE_URL, json=payload(temperature_2m=[4, 3]))
        await source.async_refresh()
        assert (await forecasts("hourly"))[0]["temperature"] == 4
        assert await forecasts("daily")
        assert (
            len(
                [
                    r
                    for r in caplog.records
                    if r.name == source.logger.name
                    and r.levelno == logging.INFO
                    and "recovered" in r.getMessage()
                ]
            )
            == 1
        )
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert not source._listeners

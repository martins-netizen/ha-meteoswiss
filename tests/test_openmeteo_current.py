"""Alternative current source: payload, privacy, retries and HA recovery."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from zoneinfo import ZoneInfo

import aiohttp
import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.cache import (
    clear_all_caches,
    get_current_weather_cache,
)
from custom_components.meteoswiss.const import DATA_SOURCE_OPENMETEO, DOMAIN
from custom_components.meteoswiss.openmeteo_coordinator import (
    OPENMETEO_BASE_URL,
    OpenMeteoDataUpdateCoordinator,
)

NOW = datetime(2026, 10, 16, 7, 20, tzinfo=UTC)
HOUR = int(NOW.replace(minute=0).timestamp())
CACHE_KEY = "openmeteo:v2:47.451234,8.561234"


@pytest.fixture(autouse=True)
def isolated_clock_and_cache(freezer):
    clear_all_caches()
    freezer.move_to(NOW)
    yield
    clear_all_caches()


def payload(**current):
    return {
        "current": {
            "time": int(NOW.timestamp()),
            "temperature_2m": 0,
            "relative_humidity_2m": 0,
            "wind_speed_10m": 0,
            "wind_direction_10m": 360,
            "pressure_msl": 1013,
            "precipitation": 0.2,
            "interval": 900,
            "weather_code": 0,
            "is_day": 0,
            "uv_index": 0,
            **current,
        },
    }


def coordinator(hass, **kwargs):
    return OpenMeteoDataUpdateCoordinator(
        hass,
        47.451234,
        8.561234,
        600,
        session=async_get_clientsession(hass),
        **kwargs,
    )


async def test_request_units_time_interval_and_session_ownership(hass, aioclient_mock):
    aioclient_mock.get(OPENMETEO_BASE_URL, json=payload(temperature_2m=-2))
    source = coordinator(hass)
    data = await source._async_update_data()
    query = aioclient_mock.mock_calls[0][1].query
    assert "precipitation" in query["current"].split(",")
    assert query["timeformat"] == "unixtime"
    assert query["forecast_hours"] == "24"
    assert query["timezone"] == "Europe/Zurich"
    assert query["temperature_unit"] == "celsius"
    assert query["wind_speed_unit"] == "kmh"
    assert query["precipitation_unit"] == "mm"
    assert "models" not in query  # Does not replace the independent ICON forecast.
    assert data["temperature"] == -2
    assert data["humidity"] == data["wind_speed"] == data["uv_index"] == 0
    assert data["wind_direction"] == 360
    assert data["precipitation"] == 0.2
    assert data["precipitation_interval_seconds"] == 900  # Not an hourly total.
    assert data["pressure"] == 1013
    assert data["last_update"] == NOW.isoformat()
    assert data["weather_condition"] == "clear-night"
    assert data["weather_description"] == "Clear sky"
    assert source.weather_code == 0
    await source.async_close()
    assert not source._session.closed


@pytest.mark.parametrize(
    "invalid", [None, True, "bad", {}, [], "nan", "inf", -float("inf")]
)
async def test_invalid_individual_measurements_do_not_discard_others(hass, invalid):
    data = coordinator(hass)._parse_response(
        payload(
            temperature_2m=invalid,
            relative_humidity_2m=invalid,
            wind_direction_10m=invalid,
            precipitation=invalid,
            pressure_msl=invalid,
            uv_index=invalid,
            weather_code=invalid,
        )
    )
    assert data["wind_speed"] == 0
    for key in (
        "temperature",
        "humidity",
        "wind_direction",
        "precipitation",
        "pressure",
        "uv_index",
    ):
        assert data[key] is None
    assert data["weather_code"] is None
    assert data["weather_condition"] is None
    assert data["weather_description"] == "Unknown"


async def test_ranges_and_unknown_conditions_keep_missing_values(hass):
    source = coordinator(hass)
    data = source._parse_response(
        payload(
            temperature_2m="-3.5",
            relative_humidity_2m=101,
            wind_speed_10m=-1,
            wind_direction_10m=361,
            precipitation=-1,
            pressure_msl=-1,
            uv_index=-1,
            weather_code=0.5,
            is_day=0.5,
        )
    )
    assert data["temperature"] == -3.5
    assert all(
        data[key] is None
        for key in (
            "humidity",
            "wind_speed",
            "wind_direction",
            "precipitation",
            "pressure",
            "uv_index",
            "weather_condition",
        )
    )
    assert source.get_weather_condition(None) == "unknown"
    assert source.get_weather_condition(999) == "unknown"
    assert source.get_weather_description(999) == "Unknown"
    assert source.get_weather_condition(63) == "rainy"
    assert (
        source._parse_response(payload(is_day="0"))["weather_condition"]
        == "clear-night"
    )
    assert source._parse_response(payload(is_day=1))["weather_condition"] == "sunny"
    assert source._parse_response(payload(is_day=None))["weather_condition"] == "sunny"


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {},
        {"current": None},
        {"current": []},
        {"current": {}},
        payload(time=True),
        payload(time="broken"),
        payload(time=float("inf")),
        payload(time=int((NOW - timedelta(hours=2)).timestamp())),
        payload(time=int((NOW + timedelta(minutes=11)).timestamp())),
        {"current": {"time": int(NOW.timestamp()), "weather_code": 0}},
        {"current": {"time": int(NOW.timestamp()), "temperature_2m": "nan"}},
    ],
)
async def test_invalid_response_fails_once_without_cache_or_state_mutation(
    hass, aioclient_mock, data
):
    source = coordinator(hass)
    source.weather_code = 63
    aioclient_mock.get(OPENMETEO_BASE_URL, text=json.dumps(data))
    with pytest.raises(UpdateFailed, match="current weather"):
        await source._async_update_data()
    assert len(aioclient_mock.mock_calls) == 1
    assert get_current_weather_cache().get(CACHE_KEY) is None
    assert source.weather_code == 63


@pytest.mark.parametrize(
    "response,attempts",
    [
        ({"status": 404}, 1),
        ({"status": 429}, 4),
        ({"status": 503}, 4),
        ({"exc": TimeoutError()}, 4),
        ({"exc": aiohttp.ClientConnectionError("47.451234 latitude=8.561234")}, 4),
        ({"text": "broken JSON"}, 1),
        ({"exc": UnicodeError("bad encoding")}, 1),
    ],
)
async def test_transport_errors_are_bounded_and_private(
    hass, aioclient_mock, caplog, response, attempts
):
    aioclient_mock.get(OPENMETEO_BASE_URL, **response)
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
    assert "Failed to fetch Open-Meteo current weather" in logs


async def test_missing_session_and_cancellation(hass, aioclient_mock):
    source = OpenMeteoDataUpdateCoordinator(hass, 47.451234, 8.561234, 1)
    assert source.update_interval == timedelta(seconds=600)
    with pytest.raises(UpdateFailed):
        await source._async_update_data()
    source = coordinator(hass)
    aioclient_mock.get(OPENMETEO_BASE_URL, exc=asyncio.CancelledError())
    with pytest.raises(asyncio.CancelledError):
        await source._async_update_data()
    assert source._consecutive_failures == 0


async def test_cache_age_original_ttl_and_circuit_recovery(
    hass, aioclient_mock, freezer
):
    source = coordinator(hass)
    aioclient_mock.get(OPENMETEO_BASE_URL, json=payload())
    original = await source._async_update_data()
    source._consecutive_failures = 3
    assert await source._async_update_data() == original
    assert source._consecutive_failures == 0
    assert len(aioclient_mock.mock_calls) == 1
    freezer.tick(timedelta(seconds=601))
    assert await source._async_update_data() == original
    assert len(aioclient_mock.mock_calls) == 2
    clear_all_caches()
    stale = {**original, "last_update": (NOW - timedelta(hours=2)).isoformat()}
    get_current_weather_cache().set(CACHE_KEY, stale)
    for _ in range(5):
        with pytest.raises(UpdateFailed):
            await source._async_update_data()
    clear_all_caches()
    with pytest.raises(UpdateFailed, match="Circuit breaker"):
        await source._async_update_data()
    assert len(aioclient_mock.mock_calls) == 2
    freezer.tick(timedelta(minutes=6))
    assert await source._async_update_data() == original
    assert source._consecutive_failures == 0
    assert source._circuit_open_until is None
    assert len(aioclient_mock.mock_calls) == 3


@pytest.mark.parametrize(
    "hourly",
    [
        None,
        [],
        {},
        {"time": "bad"},
        {"time": [True]},
        {"time": ["bad"]},
        {"time": [HOUR], "temperature_2m": 3},
        {"time": [HOUR + 1]},
        {"time": [HOUR, HOUR]},
        {"time": [HOUR + 3600, HOUR]},
    ],
)
async def test_optional_bad_hourly_data_does_not_hide_current(hass, hourly):
    data = coordinator(hass)._parse_response({**payload(), "hourly": hourly})
    assert data["temperature"] == 0
    assert data["hourly_forecast"] == []


async def test_hourly_preview_never_falls_back_to_midnight_or_bad_numbers(hass):
    source = coordinator(hass)
    data = source._parse_response(
        {
            **payload(),
            "hourly": {
                "time": [HOUR - 3600, HOUR + 3600, HOUR + 7200, HOUR + 86400],
                "temperature_2m": [12, -2, "nan", 14],
                "relative_humidity_2m": [80, 0],
                "precipitation_probability": [30, 0],
                "weather_code": [0, 63],
            },
        }
    )
    assert data["hourly_forecast"] == [
        {
            "datetime": datetime.fromtimestamp(HOUR + 3600, UTC).isoformat(),
            "temperature": -2,
            "humidity": 0,
            "precipitation_probability": 0,
            "weather_code": 63,
            "condition": "rainy",
        }
    ]
    missing = source._parse_response(
        {
            **payload(),
            "hourly": {
                "time": [HOUR],
                "temperature_2m": [0],
            },
        }
    )["hourly_forecast"][0]
    assert missing["humidity"] is None
    assert missing["precipitation_probability"] is None
    assert missing["condition"] == "unknown"


async def test_non_dict_fetch_cannot_be_cached(hass):
    source = coordinator(hass)
    with (
        patch.object(source, "_async_fetch_data", return_value=None),
        pytest.raises(UpdateFailed),
    ):
        await source._async_update_data()


async def test_registered_entities_fail_and_recover_without_duplicate_logs(
    hass,
    aioclient_mock,
    enable_custom_integrations,
    caplog,
):
    hass.config.latitude, hass.config.longitude = 47.451234, 8.561234
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "station_id": "openmeteo",
            "station_name": "Location",
            "postal_code": "8302",
            "data_source": DATA_SOURCE_OPENMETEO,
            "latitude": 47.451234,
            "longitude": 8.561234,
        },
    )
    entry.add_to_hass(hass)
    aioclient_mock.get(OPENMETEO_BASE_URL, json=payload())
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
                return_value={},
            )
        )
        for target, data in {
            "forecast_coordinator.MeteoSwissForecastCoordinator": [],
            "coordinator.MeteoSwissAlertsCoordinator": [],
            "pollen_coordinator_openmeteo.OpenMeteoPollenCoordinator": {},
            "coordinator.MeteoSwissPollenCoordinator": {},
        }.items():
            stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.{target}._async_update_data",
                    return_value=data,
                )
            )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        entities = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
        weather_id = next(row.entity_id for row in entities if row.domain == "weather")
        temp_id = next(
            row.entity_id for row in entities if row.translation_key == "temperature"
        )
        rain_id = next(
            row.entity_id for row in entities if row.translation_key == "precipitation_modelled"
        )
        assert hass.states.get(rain_id).state == "0.2"
        assert (
            hass.states.get(rain_id).attributes["measurement_interval_seconds"] == 900
        )
        assert hass.states.get(weather_id).state == "clear-night"
        assert hass.states.get(temp_id).state == "0.0"
        source = entry.runtime_data.coordinator
        saved = source.data
        clear_all_caches()
        aioclient_mock.clear_requests()
        aioclient_mock.get(OPENMETEO_BASE_URL, json={})
        caplog.clear()
        for _ in range(2):
            await source.async_refresh()
        await hass.async_block_till_done()
        assert source.data == saved
        assert hass.states.get(weather_id).state == "unavailable"
        assert hass.states.get(temp_id).state == "unavailable"
        assert (
            len(
                [
                    r
                    for r in caplog.records
                    if r.name == source.logger.name and r.levelno == logging.ERROR
                ]
            )
            == 1
        )
        aioclient_mock.clear_requests()
        aioclient_mock.get(OPENMETEO_BASE_URL, json=payload(temperature_2m=4, is_day=1))
        await source.async_refresh()
        await hass.async_block_till_done()
        assert hass.states.get(weather_id).state == "sunny"
        assert hass.states.get(temp_id).state == "4.0"
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


@pytest.mark.parametrize("age", [timedelta(hours=1), -timedelta(minutes=10)])
async def test_exact_freshness_limits_are_accepted(hass, aioclient_mock, age):
    aioclient_mock.get(OPENMETEO_BASE_URL, json=payload(time=(NOW - age).timestamp()))
    assert (await coordinator(hass)._async_update_data())["temperature"] == 0


@pytest.mark.parametrize("interval", [None, 0, -900, "nan"])
async def test_missing_or_invalid_rain_duration_never_assumes_an_hour(hass, interval):
    data = coordinator(hass)._parse_response(payload(interval=interval))
    assert data["precipitation"] == 0.2
    assert data["precipitation_interval_seconds"] is None


async def test_both_autumn_dst_hours_remain_distinct(hass, freezer):
    autumn = datetime(2026, 10, 25, 0, 20, tzinfo=UTC)
    freezer.move_to(autumn)
    first = int(autumn.replace(minute=0).timestamp())
    rows = coordinator(hass)._parse_response(
        {
            **payload(time=autumn.timestamp()),
            "hourly": {"time": [first, first + 3600], "temperature_2m": [0, -1]},
        }
    )["hourly_forecast"]
    local = [
        datetime.fromisoformat(row["datetime"]).astimezone(ZoneInfo("Europe/Zurich"))
        for row in rows
    ]
    assert len(rows) == 2
    assert [value.hour for value in local] == [2, 2]
    assert local[0].utcoffset() != local[1].utcoffset()
    assert rows[0]["datetime"] != rows[1]["datetime"]

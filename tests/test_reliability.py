"""Failure, recovery and data-contract tests for the maintained fork."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from homeassistant.exceptions import ConfigEntryNotReady
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss import (
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.meteoswiss.alerts import MeteoSwissAlertsAPI, WeatherAlert
from custom_components.meteoswiss.binary_sensor import (
    ALERT_SENSOR_DESCRIPTIONS,
    MeteoSwissAlertsBinarySensor,
    MeteoSwissAlertsCoordinator,
)
from custom_components.meteoswiss.const import (
    DOMAIN,
    SENSOR_PRECIPITATION,
    SENSOR_TEMPERATURE,
)
from custom_components.meteoswiss.coordinator import MeteoSwissDataUpdateCoordinator
from custom_components.meteoswiss.forecast_coordinator import (
    MeteoSwissForecastCoordinator,
)
from custom_components.meteoswiss.localization import async_load_warning_labels
from custom_components.meteoswiss.retry import async_retry_with_backoff
from custom_components.meteoswiss.weather import MeteoSwissWeather
from custom_components.meteoswiss.weather_data import (
    FORECAST_TIME_ZONE,
    forecast_datetime,
)


class Response:
    """HTTP response fixture with real aiohttp error semantics."""

    def __init__(self, payload=None, status=200):
        self.payload, self.status = payload, status

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def raise_for_status(self):
        if self.status >= 400:
            raise aiohttp.ClientResponseError(
                SimpleNamespace(real_url="https://example.invalid"),
                (),
                status=self.status,
            )

    async def json(self):
        return self.payload


class Session:
    def __init__(self, response):
        self.response = response
        self.calls = 0
        self.url = None

    def get(self, url, **kwargs):
        self.calls += 1
        self.url = url
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


@pytest.mark.parametrize("payload", [{}, {"warnings": []}, {"warnings": None}])
async def test_successful_empty_warning_feed(payload):
    assert (
        await MeteoSwissAlertsAPI(Session(Response(payload))).get_alerts("8302") == []
    )


@pytest.mark.parametrize(
    "failure", [Response(status=503), Response(status=429), TimeoutError()]
)
async def test_warning_failures_propagate_after_bounded_retries(failure):
    session = Session(failure)
    with patch(
        "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
    ):
        with pytest.raises((aiohttp.ClientError, TimeoutError)):
            await MeteoSwissAlertsAPI(session).get_alerts("8302")
    assert session.calls == 4


async def test_permanent_http_error_is_not_retried():
    session = Session(Response(status=404))
    with pytest.raises(aiohttp.ClientResponseError):
        await MeteoSwissAlertsAPI(session).get_alerts("8302")
    assert session.calls == 1


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"warnings": ""},
        {"warnings": "broken"},
        {"warnings": [42]},
        {"warnings": [{"warnType": 5}]},
        {"warnings": [{"warnType": 5, "warnLevel": 2, "outlook": "false"}]},
    ],
)
async def test_malformed_warning_feed_is_not_an_all_clear(payload):
    session = Session(Response(payload))
    with pytest.raises(ValueError):
        await MeteoSwissAlertsAPI(session).get_alerts("8302")
    assert session.calls == 1


async def test_warning_feed_becomes_unavailable_and_recovers(hass):
    warning = WeatherAlert(
        "sample", 5, "Ground Frost", 2, "Moderate", "Ground frost", ""
    )
    api = SimpleNamespace(
        postal_code="8302",
        get_alerts=AsyncMock(side_effect=[[warning], TimeoutError(), []]),
    )
    coordinator = MeteoSwissAlertsCoordinator(hass, api)
    entry = MockConfigEntry(domain=DOMAIN)
    entity = MeteoSwissAlertsBinarySensor(
        coordinator, entry, ALERT_SENSOR_DESCRIPTIONS[0], "8302"
    )
    assert entity.is_on is None
    await coordinator.async_refresh()
    assert entity.available and entity.is_on is True
    successful = coordinator.last_successful_update
    await coordinator.async_refresh()
    assert not entity.available
    assert coordinator.data == [warning]
    assert coordinator.last_successful_update == successful
    assert entity.extra_state_attributes["data_status"] == "unavailable"
    await coordinator.async_refresh()
    assert entity.available and entity.is_on is False
    assert entity.extra_state_attributes["data_status"] == "current"


async def test_cancellation_and_programming_errors_are_not_retried():
    for error in [asyncio.CancelledError(), ValueError("invalid payload")]:
        method = AsyncMock(side_effect=error)
        with pytest.raises(type(error)):
            await async_retry_with_backoff()(method)()
        assert method.await_count == 1


async def test_initial_failure_does_not_close_ha_session_or_leave_entry_data(hass):
    session = SimpleNamespace(close=AsyncMock())
    coordinator = SimpleNamespace(
        async_config_entry_first_refresh=AsyncMock(side_effect=ConfigEntryNotReady)
    )
    entry = MockConfigEntry(
        domain=DOMAIN, data={"station_id": "KLO", "postal_code": "8302"}
    )
    with (
        patch(
            "custom_components.meteoswiss.async_get_clientsession", return_value=session
        ),
        patch(
            "custom_components.meteoswiss.MeteoSwissDataUpdateCoordinator",
            return_value=coordinator,
        ),
    ):
        with pytest.raises(ConfigEntryNotReady):
            await async_setup_entry(hass, entry)
    session.close.assert_not_called()
    assert getattr(entry, "runtime_data", None) is None
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_unload_preserves_ha_owned_session(hass):
    session = SimpleNamespace(close=AsyncMock())
    entry = MockConfigEntry(domain=DOMAIN)
    hass.data[DOMAIN] = {}
    with patch.object(hass.config_entries, "async_unload_platforms", return_value=True):
        assert await async_unload_entry(hass, entry)
    session.close.assert_not_called()
    assert entry.entry_id not in hass.data[DOMAIN]


async def test_reload_uses_managed_ha_lifecycle(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    with patch.object(
        hass.config_entries, "async_reload", return_value=False
    ) as reload:
        await async_reload_entry(hass, entry)
    reload.assert_awaited_once_with(entry.entry_id)


async def test_forecast_contract_preserves_repeated_dst_hour_and_daylight(hass, freezer):
    freezer.move_to("2026-10-25T00:20:00+00:00")
    times = [datetime(2026, 10, 25, hour, tzinfo=UTC).timestamp() for hour in (0, 1)]
    session = Session(
        Response(
            {
                "utc_offset_seconds": 7200,
                "hourly": {
                    "time": times,
                    "temperature_2m": [5, 4],
                    "weather_code": [0, 0],
                    "is_day": [0, 0],
                },
                "daily": {
                    "time": [datetime(2026, 10, 24, 22, tzinfo=UTC).timestamp()],
                    "temperature_2m_min": [3],
                },
            }
        )
    )
    coordinator = MeteoSwissForecastCoordinator(
        hass, latitude=47.45, longitude=8.56, session=session
    )
    rows = await coordinator._fetch_open_meteo_forecast()
    assert "timeformat=unixtime" in session.url
    assert len({row["datetime"] for row in rows}) == 2
    local = [
        forecast_datetime(row["datetime"]).astimezone(FORECAST_TIME_ZONE)
        for row in rows
    ]
    assert [value.hour for value in local] == [2, 2]
    assert [value.fold for value in local] == [0, 1]
    assert all(row["condition"] == "clear-night" for row in rows)
    assert all(row["weather_code"] == 0 for row in rows)
    assert all(row["daily_temperature_min"] == 3 for row in rows)
    assert all(forecast_datetime(row["fetched_at"]).tzinfo is not None for row in rows)


def test_naive_legacy_forecast_is_swiss_time_not_server_time():
    assert forecast_datetime("2026-07-01T12:00") == datetime(2026, 7, 1, 10, tzinfo=UTC)
    assert forecast_datetime("2026-01-01T12:00") == datetime(2026, 1, 1, 11, tzinfo=UTC)
    assert forecast_datetime("invalid") is None


async def test_current_condition_uses_normalized_current_forecast(hass, freezer):
    freezer.move_to("2026-10-15T12:20:00+00:00")
    current = MeteoSwissDataUpdateCoordinator(
        hass, station_id="KLO", update_interval=600
    )
    current.data = {SENSOR_TEMPERATURE: 12, SENSOR_PRECIPITATION: 0}
    forecast = MeteoSwissForecastCoordinator(hass)
    forecast.data = [
        {
            "datetime": "2026-10-15T12:00:00+00:00",
            "condition": "cloudy",
            "weather_code": 3,
        }
    ]
    entity = MeteoSwissWeather(
        current, forecast, MockConfigEntry(domain=DOMAIN), "Kloten"
    )
    assert entity.condition == "cloudy"
    forecast.last_update_success = False
    assert entity.condition is None
    forecast.last_update_success = True
    forecast.data[0]["datetime"] = "2026-10-14T12:00:00+00:00"
    assert entity.condition is None


def test_bad_observation_time_is_never_replaced_with_now(hass):
    coordinator = MeteoSwissDataUpdateCoordinator(
        hass, station_id="KLO", update_interval=600
    )
    assert (
        coordinator._parse_csv_row({"reference_timestamp": "bad"})["last_update"]
        is None
    )
    assert (
        coordinator._parse_csv_row({"reference_timestamp": "15.10.2026 12:00"})[
            "last_update"
        ]
        == "2026-10-15T12:00:00+00:00"
    )


async def test_warning_labels_ship_all_supported_languages(hass):
    labels = await async_load_warning_labels(hass)
    assert set(labels) == {"de", "en", "fr", "it"}
    assert labels["de"]["types"]["5"] == "Bodenfrost"
    for language in labels.values():
        assert set(language["types"]) == {
            "1",
            "2",
            "3",
            "4",
            "5",
            "10",
            "11",
            "unknown",
        }
        assert set(language["levels"]) == {"1", "2", "3", "4", "5", "unknown"}
        assert language["status"]["unavailable"]


async def test_stale_observations_are_not_reported_as_current(hass, freezer):
    from custom_components.meteoswiss.cache import get_current_weather_cache

    freezer.move_to("2026-10-15T12:00:00+00:00")
    coordinator = MeteoSwissDataUpdateCoordinator(
        hass, station_id="KLO", update_interval=600
    )
    get_current_weather_cache().clear()
    coordinator._async_get_station_data_url = AsyncMock(
        return_value="https://example.invalid"
    )
    coordinator._async_download_and_parse_csv = AsyncMock(
        return_value={"temperature": 12, "last_update": "2026-10-14T12:00:00+00:00"}
    )
    await coordinator.async_refresh()
    assert not coordinator.last_update_success
    assert coordinator.data is None


async def test_air_quality_uses_current_hour_and_preserves_missing_values(
    hass, freezer
):
    from custom_components.meteoswiss.pollen_coordinator_openmeteo import (
        OpenMeteoPollenCoordinator,
    )

    freezer.move_to("2026-10-15T10:20:00+00:00")
    coordinator = OpenMeteoPollenCoordinator(hass, latitude=47.45, longitude=8.56)
    data = coordinator._parse_response(
        {
            "hourly": {
                "time": ["2026-10-15T00:00", "2026-10-15T12:00", "2026-10-15T13:00"],
                "birch_pollen": [100, None, 300],
                "pm2_5": [11, None, 33],
                "pm10": [10, 20, 30],
            }
        }
    )
    assert data["birch_pollen"]["current"] is None
    assert data["pm25"] is None
    assert data["pm10"] == 20
    assert data["last_update"] == "2026-10-15T10:00:00+00:00"


async def test_server_retry_after_is_not_ignored():
    response_error = aiohttp.ClientResponseError(
        SimpleNamespace(real_url="https://example.invalid"),
        (),
        status=429,
        headers={"Retry-After": "60"},
    )
    method = AsyncMock(side_effect=response_error)
    with patch(
        "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
    ) as sleep:
        with pytest.raises(aiohttp.ClientResponseError):
            await async_retry_with_backoff()(method)()
    assert method.await_count == 1
    sleep.assert_not_awaited()


async def test_daily_missing_precipitation_is_not_zero(hass, freezer):
    freezer.move_to("2026-10-15T12:20:00Z")
    current = MeteoSwissDataUpdateCoordinator(
        hass, station_id="KLO", update_interval=600
    )
    current.data = {SENSOR_TEMPERATURE: 12}
    forecast = MeteoSwissForecastCoordinator(hass)
    forecast.data = [
        {
            "datetime": "2026-10-15T12:00:00+00:00",
            "temperature": 12,
            "precipitation": None,
        }
    ]
    entity = MeteoSwissWeather(
        current, forecast, MockConfigEntry(domain=DOMAIN), "Kloten"
    )
    daily = await entity.async_forecast_daily()
    assert daily[0]["native_precipitation"] is None
    assert daily[0]["precipitation_probability"] is None


def test_hgt_uses_local_calendar_date_after_utc_normalization():
    from custom_components.meteoswiss.sensor import _daily_mean_for_date

    rows = [
        {
            "datetime": "2026-10-14T22:00:00+00:00",
            "local_date": "2026-10-15",
            "daily_temperature_mean": 8,
        }
    ]
    assert _daily_mean_for_date(rows, "2026-10-15") == 8
    assert _daily_mean_for_date(rows, "2026-10-14") is None


async def test_complete_entry_setup_reload_and_unload(hass, enable_custom_integrations):
    from contextlib import ExitStack

    from homeassistant.helpers.aiohttp_client import async_get_clientsession
    from homeassistant.util import dt as dt_util

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
    targets = {
        "coordinator.MeteoSwissDataUpdateCoordinator": {
            SENSOR_TEMPERATURE: 12,
            "last_update": dt_util.utcnow().isoformat(),
        },
        "forecast_coordinator.MeteoSwissForecastCoordinator": [],
        "binary_sensor.MeteoSwissAlertsCoordinator": [],
        "pollen_coordinator_openmeteo.OpenMeteoPollenCoordinator": {},
        "pollen_meteoswiss.MeteoSwissPollenCoordinator": {},
        "precipitation.MeteoSwissHourlyPrecipitationCoordinator": {},
    }
    with ExitStack() as stack:
        stack.enter_context(patch("custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations", return_value={}))
        for target, data in targets.items():
            stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.{target}._async_update_data",
                    return_value=data,
                )
            )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        from homeassistant.helpers import entity_registry as er
        registry = er.async_get(hass)
        map_id = registry.async_get_entity_id("sensor", DOMAIN, f"{DOMAIN}_stations_map")
        assert map_id and hass.states.get(map_id) is not None
        assert entry.runtime_data.hourly_precipitation_coordinator is None
        session = async_get_clientsession(hass)
        assert entry.runtime_data.session is session
        assert not session.closed
        assert (
            entry.runtime_data.alerts_coordinator.warning_labels[
                "de"
            ]["types"]["5"]
            == "Bodenfrost"
        )
        previous_runtime = entry.runtime_data
        assert previous_runtime.coordinator._listeners
        assert previous_runtime.forecast_coordinator._listeners
        registry_ids = {item.unique_id: item.entity_id for item in er.async_entries_for_config_entry(registry, entry.entry_id)}
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert entry.runtime_data is not previous_runtime
        assert not previous_runtime.coordinator._listeners
        assert not previous_runtime.forecast_coordinator._listeners
        assert registry_ids == {item.unique_id: item.entity_id for item in er.async_entries_for_config_entry(registry, entry.entry_id)}
        assert not session.closed
        assert hass.states.get(map_id) is not None
        final_runtime = entry.runtime_data
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert not final_runtime.coordinator._listeners
        assert not final_runtime.forecast_coordinator._listeners
        assert entry.entry_id not in hass.data[DOMAIN]
        assert not session.closed


def test_cache_logging_never_contains_location_keys(caplog):
    import logging

    from custom_components.meteoswiss.cache import MeteoSwissCache
    key = 'forecast:47.451234,8.561234'
    cache = MeteoSwissCache()
    with caplog.at_level(logging.DEBUG, logger='custom_components.meteoswiss.cache'):
        cache.set(key, {'temperature': 12})
        assert cache.get(key) is not None
        cache.invalidate(key)
        cache.set(key, {'temperature': 12}, ttl=0)
        assert cache.get(key) is None
    assert key not in caplog.text
    assert '47.451234' not in caplog.text
    assert '8.561234' not in caplog.text

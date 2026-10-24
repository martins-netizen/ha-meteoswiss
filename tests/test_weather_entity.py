"""Native weather attributes, subscribed forecasts and calendar aggregation."""

from __future__ import annotations

import logging
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

import pytest
from homeassistant.components.weather.const import DATA_COMPONENT
from homeassistant.const import UnitOfPrecipitationDepth, UnitOfSpeed, UnitOfTemperature
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.cache import clear_all_caches
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.coordinator import (
    MeteoSwissDataUpdateCoordinator,
    MeteoSwissForecastCoordinator,
)
from custom_components.meteoswiss.weather import MeteoSwissWeather
from custom_components.meteoswiss.weather_data import (
    forecast_datetime,
    weather_condition,
    weather_number,
)

NOW = datetime(2026, 10, 16, 9, 20, tzinfo=UTC)
HOUR = NOW.replace(minute=0)


@pytest.fixture(autouse=True)
def isolated_clock_and_cache(freezer):
    clear_all_caches()
    freezer.move_to(NOW)
    yield
    clear_all_caches()


def row(at=HOUR, **values):
    return {
        "datetime": at.isoformat(),
        "fetched_at": NOW.isoformat(),
        "temperature": 0,
        "precipitation": 0,
        "precipitation_probability": 0,
        "humidity": 0,
        "wind_speed": 0,
        "wind_direction": 360,
        "condition": "cloudy",
        **values,
    }


@pytest.fixture
def weather_entity(hass):
    current = MeteoSwissDataUpdateCoordinator(
        hass, station_id="KLO", update_interval=600
    )
    current.data = {}
    forecast = MeteoSwissForecastCoordinator(hass, latitude=47.45, longitude=8.56)
    forecast.data = [row()]
    return MeteoSwissWeather(
        current, forecast, MockConfigEntry(domain=DOMAIN), "Kloten"
    )


@pytest.fixture
async def installed_weather(hass, enable_custom_integrations):
    hass.config.latitude, hass.config.longitude = 47.451234, 8.561234
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "station_id": "KLO",
            "station_name": "Kloten",
            "postal_code": "8302",
            "data_source": "meteoswiss",
            "latitude": 47.451234,
            "longitude": 8.561234,
        },
    )
    entry.add_to_hass(hass)
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
                return_value={},
            )
        )
        for target, data in {
            "coordinator.MeteoSwissDataUpdateCoordinator": {
                "temperature": 12.3,
                "humidity": 0,
                "pressure": 1000,
                "wind_speed": 0,
                "wind_direction": 360,
                "precipitation": 0.2,
                "last_update": NOW.isoformat(),
            },
            "coordinator.MeteoSwissForecastCoordinator": [row()],
            "coordinator.MeteoSwissStationConditionCoordinator": {
                "time": HOUR.isoformat(),
                "valid_until": (HOUR + timedelta(hours=1)).isoformat(),
                "fetched_at": NOW.isoformat(),
                "weather_code": 3,
                "is_day": True,
            },
            "coordinator.MeteoSwissAlertsCoordinator": [],
            "coordinator.OpenMeteoPollenCoordinator": {},
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
        weather_id = next(
            item.entity_id
            for item in er.async_entries_for_config_entry(
                er.async_get(hass), entry.entry_id
            )
            if item.domain == "weather"
        )
        yield entry, hass.data[DATA_COMPONENT].get_entity(weather_id)
        if getattr(entry, "runtime_data", None) is not None:
            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()


async def test_registered_weather_exposes_native_measurements(hass, installed_weather):
    _, entity = installed_weather
    attrs = hass.states.get(entity.entity_id).attributes
    assert attrs["temperature"] == 12.3
    assert attrs["pressure"] == 1000
    assert attrs["wind_speed"] == 0
    assert attrs["wind_bearing"] == 360
    assert attrs["humidity"] == 0


async def test_forecast_subscribers_receive_refresh_failure_and_recovery(
    hass, installed_weather
):
    entry, entity = installed_weather
    hourly, daily = [], []
    unsub_hourly = entity.async_subscribe_forecast("hourly", hourly.append)
    unsub_daily = entity.async_subscribe_forecast("daily", daily.append)
    forecast = entry.runtime_data.forecast_coordinator
    forecast.async_set_updated_data([row(temperature=4, daily_temperature_max=4)])
    await hass.async_block_till_done()
    assert hourly[-1][0]["temperature"] == 4
    assert daily[-1][0]["temperature"] == 4
    forecast.async_set_update_error(ValueError("source failed"))
    await hass.async_block_till_done()
    assert hourly[-1] == daily[-1] == []
    assert hass.states.get(entity.entity_id).state != "unavailable"
    forecast.async_set_updated_data([row(temperature=-2, daily_temperature_max=-2)])
    await hass.async_block_till_done()
    assert hourly[-1][0]["temperature"] == -2
    assert daily[-1][0]["temperature"] == -2
    unsub_hourly()
    unsub_daily()


async def test_native_units_are_converted_by_ha_and_missing_fields_clear(
    hass, installed_weather
):
    entry, entity = installed_weather
    entity._weather_option_temperature_unit = UnitOfTemperature.FAHRENHEIT
    entity._weather_option_wind_speed_unit = UnitOfSpeed.MILES_PER_HOUR
    entity._weather_option_precipitation_unit = UnitOfPrecipitationDepth.INCHES
    source = entry.runtime_data.coordinator
    source.async_set_updated_data(
        {"temperature": 0, "wind_speed": 16.09344, "wind_direction": 0, "humidity": 0}
    )
    await hass.async_block_till_done()
    attrs = hass.states.get(entity.entity_id).attributes
    assert attrs["temperature"] == 32
    assert attrs["wind_speed"] == pytest.approx(10)
    assert attrs["wind_bearing"] == 0
    assert "pressure" not in attrs
    entry.runtime_data.forecast_coordinator.async_set_updated_data(
        [
            row(
                temperature=0,
                precipitation=25.4,
                wind_speed=16.09344,
                daily_temperature_max=0,
                daily_temperature_min=-10,
                daily_precipitation=25.4,
            ),
        ]
    )
    for kind in ("hourly", "daily"):
        result = await hass.services.async_call(
            "weather",
            "get_forecasts",
            {
                "entity_id": entity.entity_id,
                "type": kind,
            },
            blocking=True,
            return_response=True,
        )
        item = result[entity.entity_id]["forecast"][0]
        assert item["temperature"] == 32
        assert item["precipitation"] == pytest.approx(1)
        assert item["wind_speed"] == pytest.approx(10)
        if kind == "daily":
            assert item["templow"] == 14


@pytest.mark.parametrize(
    "raw", [None, True, False, "nan", "inf", -float("inf"), {}, [], 10**1000]
)
def test_invalid_observation_values_are_not_exposed(weather_entity, raw):
    weather_entity.coordinator.data = {
        key: raw
        for key in (
            "temperature",
            "humidity",
            "pressure",
            "wind_speed",
            "wind_direction",
            "precipitation",
        )
    }
    assert all(
        getattr(weather_entity, prop) is None
        for prop in (
            "native_temperature",
            "humidity",
            "native_pressure",
            "native_wind_speed",
            "wind_bearing",
            "precipitation",
        )
    )
    weather_entity._forecast_coordinator = None
    assert weather_entity.condition is None


@pytest.mark.parametrize("symbol_key", ["symbol", "icon", "condition"])
def test_known_symbols_and_current_conditions_take_precedence(
    weather_entity, symbol_key
):
    weather_entity.coordinator.data = {
        "weather_condition": "unknown",
        symbol_key: "RaIn",
    }
    assert weather_entity.condition == "rainy"
    weather_entity.coordinator.data["weather_condition"] = "hail"
    assert weather_entity.condition == "hail"


def test_current_interval_unknown_and_rain_fallback(weather_entity):
    forecast = weather_entity._forecast_coordinator
    forecast.data = [
        row(HOUR - timedelta(hours=1), condition="sunny"),
        row(HOUR + timedelta(hours=1), condition="sunny"),
    ]
    assert weather_entity.condition is None
    weather_entity.coordinator.data = {"temperature": 0, "precipitation": 0}
    assert weather_entity.condition is None
    weather_entity.coordinator.data["precipitation"] = 0.1
    assert weather_entity.condition == "rainy"
    forecast.data = [row(condition=None, weather_code=0, is_day=False)]
    assert weather_entity.condition == "clear-night"
    forecast.data = [row(condition="unknown", weather_code={})]
    assert weather_entity.condition == "rainy"
    weather_entity.coordinator.last_update_success = False
    assert weather_entity.native_temperature is None
    assert weather_entity.condition is None
    weather_entity.coordinator = None
    assert weather_entity.coordinator_data == {}
    assert weather_entity._map_open_meteo_condition(None) is None
    assert weather_entity._map_open_meteo_condition(0) == "sunny"
    assert weather_entity.precipitation_unit == "mm"


@pytest.mark.parametrize(
    "fetched",
    [
        (NOW - timedelta(hours=3, seconds=1)).isoformat(),
        (NOW + timedelta(minutes=10, seconds=1)).isoformat(),
        "broken",
        True,
    ],
)
async def test_stale_invalid_and_future_forecasts_are_not_served(
    weather_entity, fetched
):
    weather_entity._forecast_coordinator.data = [row(fetched_at=fetched)]
    assert weather_entity.condition is None
    assert await weather_entity.async_forecast_hourly() == []
    assert await weather_entity.async_forecast_daily() == []


@pytest.mark.parametrize(
    "fetched",
    [
        None,
        (NOW - timedelta(hours=3)).isoformat(),
        (NOW + timedelta(minutes=10)).isoformat(),
    ],
)
async def test_forecast_age_boundaries_and_legacy_missing_metadata(
    weather_entity, fetched
):
    weather_entity._forecast_coordinator.data = [row(fetched_at=fetched)]
    assert (await weather_entity.async_forecast_hourly())[0]["native_temperature"] == 0


@pytest.mark.parametrize("data", [None, {}, [], "bad"])
async def test_empty_or_invalid_coordinator_data(weather_entity, data):
    weather_entity.coordinator.data = data
    weather_entity._forecast_coordinator.data = data
    assert weather_entity.native_temperature is None
    assert await weather_entity.async_forecast_hourly() == []
    assert await weather_entity.async_forecast_daily() == []


async def test_hourly_window_skips_expired_invalid_and_missing_rows(weather_entity):
    weather_entity._forecast_coordinator.data = [
        None,
        {},
        {"datetime": True},
        row(HOUR - timedelta(hours=1)),
        row(temperature=None),
        row(HOUR + timedelta(hours=1), temperature=-2),
        row(HOUR + timedelta(hours=2), temperature="nan"),
        row(
            HOUR + timedelta(hours=3),
            temperature=0,
            humidity=None,
            precipitation_probability=None,
        ),
        row(HOUR + timedelta(hours=24), temperature=99),
    ]
    items = await weather_entity.async_forecast_hourly()
    assert [item["native_temperature"] for item in items] == [-2, 0]
    assert items[0]["datetime"] == (HOUR + timedelta(hours=1)).isoformat()
    assert items[1]["humidity"] is None
    assert items[1]["precipitation_probability"] is None


async def test_only_upcoming_24_hourly_intervals_are_returned(weather_entity):
    weather_entity._forecast_coordinator.data = [
        row(HOUR + timedelta(hours=i)) for i in range(-2, 120)
    ]
    items = await weather_entity.async_forecast_hourly()
    assert len(items) == 24
    assert items[0]["datetime"] == HOUR.isoformat()
    assert items[-1]["datetime"] == (HOUR + timedelta(hours=23)).isoformat()


async def test_daily_prefers_full_native_extrema_and_valid_zero_rain(weather_entity):
    weather_entity._forecast_coordinator.data = [
        row(
            HOUR + timedelta(hours=1),
            temperature=4,
            daily_temperature_max=10,
            daily_temperature_min=-4,
            daily_precipitation=0,
            daily_precipitation_probability=0,
            precipitation=1,
            precipitation_probability=30,
            condition="rainy",
        ),
        row(
            HOUR + timedelta(hours=2),
            temperature=6,
            precipitation=2,
            precipitation_probability=50,
        ),
    ]
    item = (await weather_entity.async_forecast_daily())[0]
    assert item["native_temperature"] == 10
    assert item["native_templow"] == -4
    assert item["native_precipitation"] == 0
    assert item["precipitation_probability"] == 0
    assert item["condition"] == "rainy"  # First 12:00-14:00 Swiss hour.


async def test_daily_hourly_fallback_preserves_extrema_and_zero(weather_entity):
    start = datetime(2026, 10, 16, 22, tzinfo=UTC)  # Tomorrow's Swiss midnight.
    weather_entity._forecast_coordinator.data = [
        row(
            start + timedelta(hours=i),
            temperature=-2 if i == 0 else (99 if i == 24 else 0),
            precipitation=99 if i == 0 else 0,
            precipitation_probability=99 if i == 0 else 0,
        )
        for i in range(25)
    ]
    item = (await weather_entity.async_forecast_daily())[0]
    assert item["native_temperature"] == 0
    assert item["native_templow"] == -2
    assert item["native_precipitation"] == 0
    assert item["precipitation_probability"] == 0


async def test_partial_hours_cannot_claim_whole_day_aggregates(weather_entity):
    """Two dry hours do not prove a dry day, nor its temperature extrema."""
    weather_entity._forecast_coordinator.data = [
        row(temperature=-2),
        row(HOUR + timedelta(hours=1), temperature=0),
    ]
    item = (await weather_entity.async_forecast_daily())[0]
    for key in (
        "native_temperature", "native_templow", "native_precipitation",
        "precipitation_probability",
    ):
        assert item[key] is None


@pytest.mark.parametrize(
    "rows",
    [
        [row(precipitation=0.2), row(HOUR + timedelta(hours=1), precipitation=None)],
        [row(precipitation=0.2), row(HOUR + timedelta(hours=2), precipitation=0.3)],
        [row(temperature=None, precipitation=None, precipitation_probability=None)],
    ],
)
async def test_daily_missing_or_gapped_rain_is_not_a_complete_sum(weather_entity, rows):
    weather_entity._forecast_coordinator.data = rows
    item = (await weather_entity.async_forecast_daily())[0]
    assert item["native_precipitation"] is None
    if rows[0]["temperature"] is None:
        assert item["native_temperature"] is None
        assert item["native_templow"] is None
        assert item["precipitation_probability"] is None


async def test_daily_invalid_native_fields_do_not_rescue_partial_hours(
    weather_entity,
):
    weather_entity._forecast_coordinator.data = [
        row(
            temperature=-1,
            daily_temperature_max="nan",
            daily_temperature_min=True,
            daily_precipitation=-1,
            daily_precipitation_probability=101,
        )
    ]
    item = (await weather_entity.async_forecast_daily())[0]
    assert item["native_temperature"] is item["native_templow"] is None
    assert item["native_precipitation"] is item["precipitation_probability"] is None


@pytest.mark.parametrize(
    "field,value,affected",
    [
        ("temperature", None, ("native_temperature", "native_templow")),
        ("precipitation", -1, ("native_precipitation",)),
        ("precipitation_probability", 101, ("precipitation_probability",)),
    ],
)
async def test_one_invalid_hour_invalidates_only_its_daily_fallback(
    weather_entity, field, value, affected
):
    start = datetime(2026, 10, 16, 22, tzinfo=UTC)
    rows = [row(start + timedelta(hours=i)) for i in range(25)]
    rows[12][field] = value
    weather_entity._forecast_coordinator.data = rows
    item = (await weather_entity.async_forecast_daily())[0]
    for key in (
        "native_temperature", "native_templow", "native_precipitation",
        "precipitation_probability",
    ):
        assert item[key] == (None if key in affected else 0)


async def test_next_midnight_is_required_for_daily_rain_and_probability(weather_entity):
    start = datetime(2026, 10, 16, 22, tzinfo=UTC)
    weather_entity._forecast_coordinator.data = [
        row(start + timedelta(hours=i)) for i in range(24)
    ]
    item = (await weather_entity.async_forecast_daily())[0]
    assert item["native_temperature"] == item["native_templow"] == 0
    assert item["native_precipitation"] is item["precipitation_probability"] is None


async def test_swiss_midnight_and_five_day_limit_ignore_utc_and_legacy_labels(
    weather_entity, freezer
):
    freezer.move_to("2026-10-16T22:20:00Z")  # 17 Oct 00:20 in Switzerland.
    first = datetime(2026, 10, 16, 21, tzinfo=UTC)
    weather_entity._forecast_coordinator.data = [
        row(first + timedelta(hours=i), fetched_at=None, local_date="1900-01-01")
        for i in range(120)
    ]
    items = await weather_entity.async_forecast_daily()
    assert len(items) == 5
    local_dates = [
        forecast_datetime(item["datetime"])
        .astimezone(ZoneInfo("Europe/Zurich"))
        .date()
        .isoformat()
        for item in items
    ]
    assert local_dates == [f"2026-10-{day}" for day in range(17, 22)]


@pytest.mark.parametrize("day,hours", [("2026-03-29", 23), ("2026-10-25", 25)])
async def test_daily_rain_sum_handles_23_and_25_hour_dst_days(
    weather_entity, freezer, day, hours
):
    start = (
        datetime.fromisoformat(day)
        .replace(tzinfo=ZoneInfo("Europe/Zurich"))
        .astimezone(UTC)
    )
    freezer.move_to(start + timedelta(minutes=20))
    weather_entity._forecast_coordinator.data = [
        row(
            start + timedelta(hours=i), fetched_at=None,
            precipitation=99 if i == 0 else (3 if i == hours else 1),
            precipitation_probability=99 if i == 0 else (80 if i == hours else 20),
        )
        for i in range(hours + 1)
    ]
    items = await weather_entity.async_forecast_daily()
    assert items[0]["native_precipitation"] == hours + 2
    assert items[0]["precipitation_probability"] == 80
    hourly = await weather_entity.async_forecast_hourly()
    assert len({item["datetime"] for item in hourly}) == 24


@pytest.mark.parametrize("raw", [True, {}, [], "bad", float("nan"), float("inf")])
def test_shared_condition_and_time_contracts_reject_bad_values(raw):
    assert forecast_datetime(raw) is None
    assert weather_condition(raw) is None
    assert weather_number(raw) is None


async def test_weather_logs_do_not_dump_location_or_current_payload(hass, caplog):
    current = MeteoSwissDataUpdateCoordinator(
        hass, station_id="KLO", update_interval=600
    )
    current.data = {"temperature": 0, "private_marker": "private current payload"}
    entry = MockConfigEntry(
        domain=DOMAIN, data={"latitude": 47.451234, "longitude": 8.561234}
    )
    with caplog.at_level(logging.DEBUG, logger="custom_components.meteoswiss.weather"):
        entity = MeteoSwissWeather(current, None, entry, "Kloten")
        assert entity.condition is None
    logs = "\n".join(
        record.getMessage()
        for record in caplog.records
        if record.name == "custom_components.meteoswiss.weather"
    )
    assert "47.451234" not in logs
    assert "8.561234" not in logs
    assert "private current payload" not in logs


async def test_observation_only_weather_entity_can_be_added_and_removed(
    hass, weather_entity
):
    weather_entity._forecast_coordinator = None
    weather_entity.coordinator.data = {"temperature": 0, "weather_condition": "sunny"}
    assert await async_setup_component(hass, "weather", {})
    component = hass.data[DATA_COMPONENT]
    await component.async_add_entities([weather_entity])
    await hass.async_block_till_done()
    assert hass.states.get(weather_entity.entity_id).attributes["temperature"] == 0
    assert hass.states.get(weather_entity.entity_id).state == "sunny"
    assert await weather_entity.async_forecast_hourly() == []
    await component.async_remove_entity(weather_entity.entity_id)
    assert not weather_entity.coordinator._listeners


async def test_websocket_subscriber_receives_live_forecast_without_resubscribing(
    hass,
    installed_weather,
    hass_ws_client,
):
    entry, entity = installed_weather
    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "weather/subscribe_forecast",
            "entity_id": entity.entity_id,
            "forecast_type": "hourly",
        }
    )
    assert (await client.receive_json())["success"]
    initial = await client.receive_json()
    assert initial["event"]["forecast"][0]["temperature"] == 0
    forecast = entry.runtime_data.forecast_coordinator
    forecast.async_set_updated_data([row(temperature=7)])
    await hass.async_block_till_done()
    updated = await client.receive_json()
    assert updated["event"]["forecast"][0]["temperature"] == 7
    forecast.async_set_update_error(ValueError("source failed"))
    await hass.async_block_till_done()
    assert (await client.receive_json())["event"]["forecast"] == []
    forecast.async_set_updated_data([row(temperature=-3)])
    await hass.async_block_till_done()
    assert (await client.receive_json())["event"]["forecast"][0]["temperature"] == -3
    await client.send_json({"id": 2, "type": "unsubscribe_events", "subscription": 1})
    assert (await client.receive_json())["success"]
    assert not entity._forecast_listeners["hourly"]
    observation = entry.runtime_data.coordinator
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert not observation._listeners
    assert not forecast._listeners


async def test_invalid_prefix_cannot_hide_stale_forecast_metadata(weather_entity):
    weather_entity._forecast_coordinator.data = [
        {},
        row(fetched_at=(NOW - timedelta(hours=4)).isoformat()),
    ]
    assert await weather_entity.async_forecast_hourly() == []
    assert await weather_entity.async_forecast_daily() == []


async def test_observation_failure_clears_current_attributes_and_recovers_with_same_identity(
    hass,
    installed_weather,
):
    entry, entity = installed_weather
    source = entry.runtime_data.coordinator
    original = dict(source.data)
    entity_id, unique_id = entity.entity_id, entity.unique_id
    source.async_set_update_error(ValueError("current source failed"))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "unavailable"
    assert "temperature" not in hass.states.get(entity_id).attributes
    assert source.data == original
    source.async_set_updated_data({**original, "temperature": 0})
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "cloudy"
    assert hass.states.get(entity_id).attributes["temperature"] == 0
    assert entity.entity_id == entity_id
    assert entity.unique_id == unique_id

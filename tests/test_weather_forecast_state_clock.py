"""Registered forecast weather follows model hours and age without a fetch."""

from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from ha_helpers import MockConfigEntry, async_fire_time_changed
from homeassistant.components.weather.const import DATA_COMPONENT
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er

from custom_components.meteoswiss import weather as weather_module
from custom_components.meteoswiss.const import CONF_FORECAST_LOCATION, DOMAIN
from custom_components.meteoswiss.forecast_location_config import encode_forecast_location
from custom_components.meteoswiss.forecast_locations import (
    ForecastPointType,
    parse_forecast_catalogue,
)
from custom_components.meteoswiss.weather import MeteoSwissForecastWeather

NOW = datetime(2026, 10, 23, 10, 50, tzinfo=UTC)


def rows(fetched=NOW, *, legacy=False, temperature_shift=0):
    result = []
    for offset in range(-1, 9):
        stamp = NOW.replace(minute=0) + timedelta(hours=offset)
        result.append({
            "datetime": stamp.isoformat(), "fetched_at": fetched.isoformat(),
            "temperature": 10 + offset * 10 + temperature_shift,
            "condition": "sunny" if offset <= 0 else "rainy",
            "humidity": 50 + offset, "wind_speed": max(0, offset),
            "wind_direction": 90,
        })
    if legacy:
        for item in result:
            item.pop("fetched_at")
    return result


@pytest.fixture
async def clock_entry(hass, enable_custom_integrations, freezer, request):
    freezer.move_to(NOW)
    settings = getattr(request, "param", {})
    selected = settings.get("selected", True)
    data = {
        "data_source": "openmeteo", "latitude": 47.45, "longitude": 8.56,
        "station_name": "Open-Meteo", "postal_code": "8302",
    }
    if selected:
        snapshot = parse_forecast_catalogue(
            (Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv").read_bytes(),
            NOW,
        )
        data[CONF_FORECAST_LOCATION] = encode_forecast_location(
            snapshot.select(ForecastPointType.POINT_OF_INTEREST, "711")
        )
    entry = MockConfigEntry(domain=DOMAIN, data=data)
    entry.add_to_hass(hass)
    hass.config_entries.async_update_entry(
        entry, pref_disable_polling=not settings.get("polling", False)
    )
    with ExitStack() as stack:
        mocks = {}
        for name, value in {
            "OpenMeteoDataUpdateCoordinator": {"temperature": 12},
            "MeteoSwissForecastCoordinator": rows(),
            "MeteoSwissAlertsCoordinator": [],
            "OpenMeteoPollenCoordinator": {},
            "MeteoSwissPollenCoordinator": {},
        }.items():
            mocks[name] = stack.enter_context(patch(
                f"custom_components.meteoswiss.coordinator.{name}._async_update_data",
                return_value=value,
            ))
        stack.enter_context(patch(
            "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
            return_value={},
        ))
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        component = hass.data[DATA_COMPONENT]
        named = component.get_entity(registry.async_get_entity_id(
            "weather", DOMAIN, f"{DOMAIN}_{entry.entry_id}_forecast_weather"
        ))
        observed = component.get_entity(registry.async_get_entity_id(
            "weather", DOMAIN, f"{DOMAIN}_{entry.entry_id}_weather"
        ))
        yield entry, named, observed, mocks["MeteoSwissForecastCoordinator"]
        if entry.state is ConfigEntryState.LOADED:
            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()


async def advance(hass, freezer, instant):
    freezer.move_to(instant)
    async_fire_time_changed(hass, instant)
    await hass.async_block_till_done()


@pytest.mark.parametrize("clock_entry", [
    {"selected": True}, {"selected": False}, {"selected": True, "polling": True},
], indirect=True)
async def test_registered_hour_rollover_and_subscribers_use_retained_snapshot(
    hass, clock_entry, freezer
):
    entry, named, observed, fetch = clock_entry
    named_updates, observed_updates = [], []
    named_unsub = named.async_subscribe_forecast("hourly", named_updates.append)
    observed_unsub = observed.async_subscribe_forecast("hourly", observed_updates.append)
    count = fetch.await_count
    assert hass.states.get(named.entity_id).state == "sunny"
    assert hass.states.get(named.entity_id).attributes["temperature"] == 10
    assert hass.states.get(observed.entity_id).attributes["temperature"] == 12
    await advance(hass, freezer, NOW.replace(hour=11, minute=0))
    assert hass.states.get(named.entity_id).state == "rainy"
    assert hass.states.get(named.entity_id).attributes["temperature"] == 20
    assert named_updates[-1][0]["temperature"] == 20
    assert hass.states.get(observed.entity_id).attributes["temperature"] == 12
    if observed.supported_features:
        assert hass.states.get(observed.entity_id).state == "rainy"
        assert observed_updates[-1][0]["temperature"] == 20
        assert observed._forecast_clock_cancel is not None
    else:
        assert observed_updates == []
        assert observed._forecast_clock_cancel is None
    assert fetch.await_count == count
    named_unsub()
    observed_unsub()


@pytest.mark.parametrize("clock_entry", [{"selected": True}, {"selected": False}], indirect=True)
async def test_exact_snapshot_age_expiry_pushes_empty_forecasts_without_fetch(
    hass, clock_entry, freezer
):
    entry, named, observed, fetch = clock_entry
    named_updates, observed_updates = [], []
    named_daily, observed_daily = [], []
    named_unsub = named.async_subscribe_forecast("hourly", named_updates.append)
    observed_unsub = observed.async_subscribe_forecast("hourly", observed_updates.append)
    named_daily_unsub = named.async_subscribe_forecast("daily", named_daily.append)
    observed_daily_unsub = observed.async_subscribe_forecast("daily", observed_daily.append)
    assert entry.pref_disable_polling
    assert entry.runtime_data.forecast_coordinator._unsub_refresh is None
    count = fetch.await_count
    await advance(hass, freezer, NOW + timedelta(hours=3))
    assert hass.states.get(named.entity_id).state != "unavailable"
    await advance(hass, freezer, NOW + timedelta(hours=3, microseconds=1))
    assert hass.states.get(named.entity_id).state == "unavailable"
    assert named_updates[-1] == []
    assert named_daily[-1] == []
    assert named._forecast_clock_cancel is None
    assert observed.available
    assert hass.states.get(observed.entity_id).attributes["temperature"] == 12
    if observed.supported_features:
        assert observed_updates[-1] == []
        assert observed_daily[-1] == []
        assert observed._forecast_clock_cancel is None
    assert fetch.await_count == count
    named_unsub()
    observed_unsub()
    named_daily_unsub()
    observed_daily_unsub()


@pytest.mark.parametrize("bad", [
    [], [None, {}], [{"datetime": "bad"}],
    [{"datetime": NOW.isoformat(), "fetched_at": "bad"}],
    rows(NOW - timedelta(hours=4)), rows(NOW + timedelta(hours=1)),
])
async def test_invalid_empty_or_expired_updates_cancel_clock_and_recovery_reschedules(
    hass, clock_entry, freezer, bad
):
    entry, named, _, fetch = clock_entry
    source = entry.runtime_data.forecast_coordinator
    old_generation = named._forecast_clock_generation
    source.async_set_updated_data(bad)
    await hass.async_block_till_done()
    assert named._forecast_clock_cancel is None
    assert named._forecast_clock_generation > old_generation
    source.async_set_updated_data(rows())
    await hass.async_block_till_done()
    assert named._forecast_clock_cancel is not None
    count = fetch.await_count
    await advance(hass, freezer, NOW.replace(hour=11, minute=0))
    assert hass.states.get(named.entity_id).attributes["temperature"] == 20
    assert fetch.await_count == count


async def test_failed_source_does_not_rearm_or_change_observation_availability(
    hass, clock_entry, freezer
):
    entry, named, observed, fetch = clock_entry
    received = []
    unsub = named.async_subscribe_forecast("hourly", received.append)
    source = entry.runtime_data.forecast_coordinator
    source.async_set_update_error(ValueError("forecast unavailable"))
    await hass.async_block_till_done()
    assert named._forecast_clock_cancel is None
    assert received[-1] == []
    count = fetch.await_count
    await advance(hass, freezer, NOW.replace(hour=11, minute=0))
    assert hass.states.get(named.entity_id).state == "unavailable"
    assert observed.available
    assert hass.states.get(observed.entity_id).attributes["temperature"] == 12
    assert fetch.await_count == count
    source.async_set_updated_data(rows(NOW.replace(hour=11, minute=0)))
    await hass.async_block_till_done()
    assert named._forecast_clock_cancel is not None
    assert received[-1][0]["temperature"] == 20
    unsub()


async def test_legacy_snapshot_without_retrieval_time_keeps_hour_only_compatibility(
    hass, clock_entry, freezer
):
    entry, named, _, fetch = clock_entry
    entry.runtime_data.forecast_coordinator.async_set_updated_data(rows(legacy=True))
    await hass.async_block_till_done()
    count = fetch.await_count
    await advance(hass, freezer, NOW + timedelta(hours=4))
    assert named.available
    assert named._forecast_clock_cancel is not None
    assert hass.states.get(named.entity_id).attributes["temperature"] == 50
    assert fetch.await_count == count


async def test_source_replacement_invalidates_queued_old_clock_callback(
    hass, clock_entry, freezer
):
    entry, named, _, fetch = clock_entry
    received = []
    unsub = named.async_subscribe_forecast("hourly", received.append)
    source = entry.runtime_data.forecast_coordinator
    stale_generation = named._forecast_clock_generation
    source.async_set_updated_data(rows(temperature_shift=100))
    await hass.async_block_till_done()
    generation = named._forecast_clock_generation
    received_before = len(received)
    with patch.object(named, "async_write_ha_state", wraps=named.async_write_ha_state) as write:
        named._handle_forecast_clock(stale_generation, NOW.replace(hour=11, minute=0))
        await hass.async_block_till_done()
    write.assert_not_called()
    assert named._forecast_clock_generation == generation
    assert len(received) == received_before
    count = fetch.await_count
    await advance(hass, freezer, NOW.replace(hour=11, minute=0))
    assert hass.states.get(named.entity_id).attributes["temperature"] == 120
    assert received[-1][0]["temperature"] == 120
    assert fetch.await_count == count
    unsub()


@pytest.mark.parametrize("source_first", [True, False])
async def test_source_refresh_and_hour_boundary_overlap_keep_latest_projection(
    hass, clock_entry, freezer, source_first
):
    entry, named, _, fetch = clock_entry
    received = []
    unsub = named.async_subscribe_forecast("hourly", received.append)
    source = entry.runtime_data.forecast_coordinator
    count = fetch.await_count
    boundary = NOW.replace(hour=11, minute=0)
    freezer.move_to(boundary)
    if not source_first:
        async_fire_time_changed(hass, boundary)
    source.async_set_updated_data(rows(boundary, temperature_shift=100))
    if source_first:
        async_fire_time_changed(hass, boundary)
    await hass.async_block_till_done()
    assert hass.states.get(named.entity_id).attributes["temperature"] == 120
    assert received[-1][0]["temperature"] == 120
    assert named._forecast_clock_cancel is not None
    await advance(hass, freezer, boundary + timedelta(hours=1))
    assert hass.states.get(named.entity_id).attributes["temperature"] == 130
    assert received[-1][0]["temperature"] == 130
    assert fetch.await_count == count
    unsub()


async def test_swiss_midnight_removes_previous_day_from_daily_subscriber(
    hass, clock_entry, freezer
):
    entry, named, _, fetch = clock_entry
    before = NOW.replace(hour=21)
    boundary = NOW.replace(hour=22, minute=0)
    freezer.move_to(before)
    source = entry.runtime_data.forecast_coordinator
    source.async_set_updated_data([
        {
            "datetime": (boundary + timedelta(hours=offset)).isoformat(),
            "fetched_at": before.isoformat(), "temperature": temperature,
            "daily_temperature_max": temperature, "condition": "sunny",
        }
        for offset, temperature in ((-1, 10), (0, 20))
    ])
    await hass.async_block_till_done()
    received = []
    unsub = named.async_subscribe_forecast("daily", received.append)
    await named.async_update_listeners(("daily",))
    assert [row["temperature"] for row in received[-1]] == [10, 20]
    count = fetch.await_count
    await advance(hass, freezer, boundary)
    assert [row["temperature"] for row in received[-1]] == [20]
    assert fetch.await_count == count
    unsub()


@pytest.mark.parametrize("clock_entry", [{"selected": True}, {"selected": False}], indirect=True)
async def test_unload_and_reload_cannot_rearm_removed_entity_clock(
    hass, clock_entry, freezer
):
    entry, named, observed, fetch = clock_entry
    received = []
    unsub = named.async_subscribe_forecast("hourly", received.append)
    named_id, observed_id = named.entity_id, observed.entity_id
    generations = {entity: entity._forecast_clock_generation for entity in (named, observed)}
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    states = {entity_id: hass.states.get(entity_id) for entity_id in (named_id, observed_id)}
    before = len(received)
    count = fetch.await_count
    for entity in (named, observed):
        assert not entity._forecast_clock_active
        assert entity._forecast_clock_cancel is None
        with patch.object(entity, "async_write_ha_state", wraps=entity.async_write_ha_state) as write:
            entity._handle_forecast_clock(generations[entity], NOW + timedelta(hours=1))
            entity._schedule_forecast_clock()
        write.assert_not_called()
        assert entity._forecast_clock_cancel is None
    await advance(hass, freezer, NOW + timedelta(hours=1))
    assert len(received) == before and fetch.await_count == count
    assert {entity_id: hass.states.get(entity_id) for entity_id in states} == states
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    assert registry.async_get_entity_id("weather", DOMAIN, named.unique_id) == named_id
    assert registry.async_get_entity_id("weather", DOMAIN, observed.unique_id) == observed_id
    replacement = hass.data[DATA_COMPONENT].get_entity(named_id)
    assert replacement is not named and replacement._forecast_clock_cancel is not None
    unsub()


def test_unadded_forecast_entity_does_not_schedule_a_clock(hass):
    from custom_components.meteoswiss.coordinator import MeteoSwissForecastCoordinator

    source = MeteoSwissForecastCoordinator(hass, latitude=47.45, longitude=8.56)
    source.data = rows()
    entity = MeteoSwissForecastWeather(source, MockConfigEntry(domain=DOMAIN))
    with patch.object(weather_module, "async_track_point_in_utc_time") as track:
        entity._schedule_forecast_clock()
    track.assert_not_called()

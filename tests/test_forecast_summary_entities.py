"""Registered forecast sensor values, timer boundaries, recovery and cleanup."""

from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from test_forecast_summary import NOW, forecast_rows

from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.coordinator import MeteoSwissForecastCoordinator
from custom_components.meteoswiss.sensor import (
    FORECAST_SENSOR_DESCRIPTIONS,
    MeteoSwissForecastSensor,
)


@pytest.fixture
async def installed_summary(hass, enable_custom_integrations, freezer):
    freezer.move_to(NOW)
    hass.config.latitude, hass.config.longitude = 47.45, 8.56
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
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
                return_value={},
            )
        )
        mocks = {}
        for target, data in {
            "coordinator.MeteoSwissDataUpdateCoordinator": {
                "temperature": 12,
                "last_update": NOW.isoformat(),
            },
            "coordinator.MeteoSwissForecastCoordinator": forecast_rows(probability=0),
            "coordinator.MeteoSwissAlertsCoordinator": [],
            "coordinator.OpenMeteoPollenCoordinator": {},
            "coordinator.MeteoSwissPollenCoordinator": {},
        }.items():
            mocks[target] = stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.{target}._async_update_data",
                    return_value=data,
                )
            )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        ids = {
            description.key: registry.async_get_entity_id(
                "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_{description.key}"
            )
            for description in FORECAST_SENSOR_DESCRIPTIONS
        }
        yield entry, ids, mocks["coordinator.MeteoSwissForecastCoordinator"]
        if getattr(entry, "runtime_data", None) is not None:
            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()


def test_scalar_identity_units_precision_and_shared_device(hass, freezer):
    freezer.move_to(NOW)
    entry = MockConfigEntry(domain=DOMAIN, entry_id="forecast-identity")
    coordinator = MeteoSwissForecastCoordinator(hass, latitude=47.45, longitude=8.56)
    coordinator.data = forecast_rows()
    assert len(FORECAST_SENSOR_DESCRIPTIONS) == 8
    for description in FORECAST_SENSOR_DESCRIPTIONS:
        sensor = MeteoSwissForecastSensor(coordinator, entry, description, "Kloten")
        assert sensor.unique_id == f"meteoswiss_forecast-identity_{description.key}"
        assert sensor.device_info["identifiers"] == {(DOMAIN, entry.entry_id)}
        assert sensor.state_class is None
        assert sensor.native_unit_of_measurement in ("°C", "mm", "%")
        assert sensor.suggested_display_precision in (0, 1)
        assert sensor.available
        assert isinstance(sensor.native_value, (float, int))
        coordinator.last_update_success = False
        assert not sensor.available
        assert sensor.native_value is None
        coordinator.last_update_success = True


async def test_registered_numeric_values_unknown_fields_and_failure_recovery(
    hass, installed_summary
):
    entry, ids, mock = installed_summary
    assert all(ids.values()) and len(set(ids.values())) == 8
    assert hass.states.get(ids["forecast_maximum_temperature_today"]).state == "12.0"
    assert hass.states.get(ids["forecast_minimum_temperature_today"]).state == "-2.0"
    assert hass.states.get(ids["forecast_maximum_temperature_tomorrow"]).state == "13.0"
    probability = hass.states.get(ids["forecast_probability_today"])
    assert float(probability.state) == 0
    assert probability.attributes["peak_periods"] == []
    source = entry.runtime_data.forecast_coordinator
    broken = forecast_rows()
    for row in broken:
        row.pop("daily_temperature_max")
    source.async_set_updated_data(broken)
    await hass.async_block_till_done()
    assert hass.states.get(ids["forecast_maximum_temperature_today"]).state == "unknown"
    mock.side_effect = UpdateFailed("forecast unavailable")
    await source.async_refresh()
    await hass.async_block_till_done()
    assert all(
        hass.states.get(entity_id).state == "unavailable" for entity_id in ids.values()
    )
    assert (
        hass.states.get(ids["forecast_probability_today"]).attributes.get(
            "peak_periods", []
        )
        == []
    )
    mock.side_effect = None
    mock.return_value = forecast_rows()
    await source.async_refresh()
    await hass.async_block_till_done()
    assert hass.states.get(ids["forecast_maximum_temperature_today"]).state == "12.0"


async def test_hour_window_and_snapshot_expiry_update_without_fetching(
    hass, installed_summary, freezer
):
    entry, ids, mock = installed_summary
    source = entry.runtime_data.forecast_coordinator
    rows = forecast_rows()
    for row in rows:
        if row["datetime"] == "2026-10-23T11:00:00+00:00":
            row["precipitation_probability"] = 80
    source.async_set_updated_data(rows)
    await hass.async_block_till_done()
    assert float(hass.states.get(ids["forecast_probability_today"]).state) == 80
    # Remove the ordinary coordinator poller so only scalar clock timers run.
    source._unsub_refresh()
    source._unsub_refresh = None
    count = mock.await_count
    instant = NOW.replace(hour=11, minute=0)
    freezer.move_to(instant)
    async_fire_time_changed(hass, instant)
    await hass.async_block_till_done()
    assert float(hass.states.get(ids["forecast_probability_today"]).state) == 10
    assert mock.await_count == count
    expired = NOW + timedelta(hours=3, seconds=1)
    freezer.move_to(expired)
    async_fire_time_changed(hass, expired)
    await hass.async_block_till_done()
    assert all(
        hass.states.get(entity_id).state == "unavailable" for entity_id in ids.values()
    )
    assert mock.await_count == count


async def test_midnight_rollover_and_unload_cancel_scalar_listeners(
    hass, installed_summary, freezer
):
    entry, ids, mock = installed_summary
    source = entry.runtime_data.forecast_coordinator
    late = datetime(2026, 10, 23, 21, 20, tzinfo=UTC)
    freezer.move_to(late)
    source.async_set_updated_data(forecast_rows(late))
    await hass.async_block_till_done()
    source._unsub_refresh()
    source._unsub_refresh = None
    count = mock.await_count
    midnight = datetime(2026, 10, 23, 22, tzinfo=UTC)
    freezer.move_to(midnight)
    async_fire_time_changed(hass, midnight)
    await hass.async_block_till_done()
    state = hass.states.get(ids["forecast_maximum_temperature_today"])
    assert state.attributes["forecast_date"] == "2026-10-24"
    assert state.state == "13.0"
    assert hass.states.get(ids["forecast_maximum_temperature_tomorrow"]).state == "14.0"
    assert mock.await_count == count
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert not source._listeners
    assert all(
        hass.states.get(entity_id) is None
        or hass.states.get(entity_id).state == "unavailable"
        for entity_id in ids.values()
    )
    states_after_unload = {
        entity_id: hass.states.get(entity_id) for entity_id in ids.values()
    }
    later = midnight + timedelta(hours=1)
    freezer.move_to(later)
    async_fire_time_changed(hass, later)
    await hass.async_block_till_done()
    assert mock.await_count == count

    assert {
        entity_id: hass.states.get(entity_id) for entity_id in ids.values()
    } == states_after_unload


async def test_missing_snapshot_can_recover_without_new_entity_ids(
    hass, installed_summary
):
    entry, ids, _ = installed_summary
    source = entry.runtime_data.forecast_coordinator
    source.async_set_updated_data([])
    await hass.async_block_till_done()
    assert all(
        hass.states.get(entity_id).state == "unavailable" for entity_id in ids.values()
    )
    source.async_set_updated_data(forecast_rows())
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    for description in FORECAST_SENSOR_DESCRIPTIONS:
        assert (
            registry.async_get_entity_id(
                "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_{description.key}"
            )
            == ids[description.key]
        )
    assert hass.states.get(ids["forecast_precipitation_today"]).state == "0.0"


async def test_reload_keeps_all_scalar_entity_ids(hass, installed_summary):
    entry, ids, mock = installed_summary
    old_source = entry.runtime_data.forecast_coordinator
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert not old_source._listeners
    assert entry.runtime_data.forecast_coordinator is not old_source
    registry = er.async_get(hass)
    for description in FORECAST_SENSOR_DESCRIPTIONS:
        entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_{description.key}"
        )
        assert entity_id == ids[description.key]
        assert hass.states.get(entity_id).state not in ("unknown", "unavailable")
    assert mock.await_count >= 2

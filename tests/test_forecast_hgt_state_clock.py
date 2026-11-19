"""Registered forecast HGT follows the Swiss calendar without another fetch."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import UpdateFailed

from ha_helpers import async_fire_time_changed
from test_forecast_summary import forecast_rows
from test_provider_device_metadata import make_entry, provider_sources as provider_sources

from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.weather_data import FORECAST_TIME_ZONE

NOW = datetime(2026, 10, 23, 21, 20, tzinfo=UTC)


def daily_forecast(now):
    """Independent day means make yesterday's stale HA state observable."""
    rows = forecast_rows(now)
    today = now.astimezone(FORECAST_TIME_ZONE).date()
    for row in rows:
        offset = (datetime.fromisoformat(row["local_date"]).date() - today).days
        row["daily_temperature_mean"] = (5.0, 9.0, 13.0, 14.0)[offset]
    return rows


@pytest.fixture
async def hgt_clock_entry(hass, enable_custom_integrations, provider_sources, freezer, request):
    values = getattr(request, "param", {})
    now = values.get("now", NOW)
    freezer.move_to(now)
    entry = make_entry(hass, "meteoswiss")
    hass.config_entries.async_update_entry(
        entry, pref_disable_polling=values.get("disabled_polling", False)
    )
    with patch(
        "custom_components.meteoswiss.coordinator.MeteoSwissForecastCoordinator._async_update_data",
        return_value=daily_forecast(now),
    ) as fetch:
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        entity_id = er.async_get(hass).async_get_entity_id(
            "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_heating_degree_days"
        )
        yield entry, entity_id, fetch, now
        if entry.state is ConfigEntryState.LOADED:
            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done(wait_background_tasks=True)


@pytest.mark.parametrize("hgt_clock_entry", [
    {"now": now, "disabled_polling": disabled}
    for now in (
        NOW,
        # The following calendar day changes the Swiss UTC offset.
        datetime(2026, 3, 28, 22, 20, tzinfo=UTC),
        datetime(2026, 10, 24, 21, 20, tzinfo=UTC),
    )
    for disabled in (False, True)
], indirect=True)
async def test_swiss_midnight_updates_registered_hgt_without_fetch(
    hass, hgt_clock_entry, freezer
):
    entry, entity_id, fetch, now = hgt_clock_entry
    before = hass.states.get(entity_id)
    assert before.state == "15.0"
    assert before.attributes["daily_mean_temperature"] == 5.0
    assert "state_class" not in before.attributes
    if entry.pref_disable_polling:
        assert entry.runtime_data.forecast_coordinator._unsub_refresh is None
    count = fetch.await_count
    # The hourly source refresh is after midnight. The existing snapshot must
    # publish tomorrow's mean at exactly Swiss midnight, including DST dates.
    midnight = now + timedelta(minutes=40)
    freezer.move_to(midnight)
    async_fire_time_changed(hass, midnight)
    await hass.async_block_till_done(wait_background_tasks=True)
    after = hass.states.get(entity_id)
    assert after.state == "11.0"
    assert after.attributes["daily_mean_temperature"] == 9.0
    assert after.attributes["method"] == "HGT 12/20"
    assert after.attributes["value_type"] == "forecast"
    assert after.attributes["unit_of_measurement"] == "°C·d"
    assert "state_class" not in after.attributes
    assert fetch.await_count == count
    if entry.pref_disable_polling:
        # The next local day spans 24, 23 or 25 physical hours. These explicit
        # UTC boundaries also catch a timer implemented as a fixed 24h delay.
        next_midnight = {
            NOW: datetime(2026, 10, 24, 22, tzinfo=UTC),
            datetime(2026, 3, 28, 22, 20, tzinfo=UTC): datetime(2026, 3, 29, 22, tzinfo=UTC),
            datetime(2026, 10, 24, 21, 20, tzinfo=UTC): datetime(2026, 10, 25, 23, tzinfo=UTC),
        }[now]
        just_before = next_midnight - timedelta(minutes=30)
        freezer.move_to(just_before)
        async_fire_time_changed(hass, just_before)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert hass.states.get(entity_id).state == "11.0"
        freezer.move_to(next_midnight)
        async_fire_time_changed(hass, next_midnight)
        await hass.async_block_till_done(wait_background_tasks=True)
        second = hass.states.get(entity_id)
        assert second.state == "0.0"
        assert second.attributes["daily_mean_temperature"] == 13.0
        assert fetch.await_count == count


async def test_failed_or_empty_source_cancels_hgt_clock_and_recovery_keeps_identity(
    hass, hgt_clock_entry, freezer
):
    entry, entity_id, fetch, now = hgt_clock_entry
    source = entry.runtime_data.forecast_coordinator
    sensor = hass.data["sensor"].get_entity(entity_id)
    saved = er.async_get(hass).async_get(entity_id)
    old_callback = sensor._hgt_clock_cancel.__self__.job.target
    source.async_set_update_error(UpdateFailed("forecast unavailable"))
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "unavailable"
    assert sensor._hgt_clock_cancel is None
    # Retain the actual native timer target across its cancellation. Any old
    # work must not undo the source failure or install another calendar timer.
    with patch.object(sensor, "async_write_ha_state", wraps=sensor.async_write_ha_state) as write:
        old_callback(now + timedelta(minutes=40))
    write.assert_not_called()
    assert sensor._hgt_clock_cancel is None
    count = fetch.await_count
    midnight = now + timedelta(minutes=40)
    freezer.move_to(midnight)
    async_fire_time_changed(hass, midnight)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get(entity_id).state == "unavailable"
    assert fetch.await_count == count
    source.async_set_updated_data([])
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).state == "unknown"
    assert sensor._hgt_clock_cancel is None
    source.async_set_updated_data(daily_forecast(now))
    await hass.async_block_till_done()
    recovered = hass.states.get(entity_id)
    assert recovered.state == "11.0"
    assert recovered.attributes["daily_mean_temperature"] == 9.0
    assert sensor._hgt_clock_cancel is not None
    assert er.async_get(hass).async_get(entity_id).id == saved.id
    assert fetch.await_count == count


async def test_unload_cancels_hgt_midnight_callback_and_reload_retains_identity(
    hass, hgt_clock_entry, freezer
):
    entry, entity_id, fetch, now = hgt_clock_entry
    source = entry.runtime_data.forecast_coordinator
    sensor = hass.data["sensor"].get_entity(entity_id)
    saved = er.async_get(hass).async_get(entity_id)
    assert sensor._hgt_clock_cancel is not None
    old_callback = sensor._hgt_clock_cancel.__self__.job.target
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert sensor._hgt_clock_cancel is None
    assert not source._listeners
    with patch.object(sensor, "async_write_ha_state", wraps=sensor.async_write_ha_state) as write:
        old_callback(now + timedelta(minutes=40))
        sensor._schedule_hgt_clock()
    write.assert_not_called()
    assert sensor._hgt_clock_cancel is None
    removed = hass.states.get(entity_id)
    count = fetch.await_count
    midnight = now + timedelta(minutes=40)
    freezer.move_to(midnight)
    async_fire_time_changed(hass, midnight)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert hass.states.get(entity_id) is removed
    assert sensor._hgt_clock_cancel is None
    assert fetch.await_count == count
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    replacement = hass.data["sensor"].get_entity(entity_id)
    assert replacement is not sensor
    assert replacement._hgt_clock_cancel is not None
    assert er.async_get(hass).async_get(entity_id).id == saved.id
    assert hass.states.get(entity_id).state == "11.0"

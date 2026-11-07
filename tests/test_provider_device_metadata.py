"""Provider provenance and native registry preservation across source changes."""

from contextlib import ExitStack
import logging
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_RECONFIGURE
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from ha_helpers import MockConfigEntry

from custom_components.meteoswiss.config_flow import (
    MeteoSwissConfigFlow,
    MeteoSwissOptionsFlow,
)
from custom_components.meteoswiss.const import DOMAIN, POLLEN_STATIONS
from custom_components.meteoswiss.sensor import MeteoSwissSensor, SENSOR_DESCRIPTIONS
from custom_components.meteoswiss.weather import MeteoSwissWeather


@pytest.fixture
def provider_sources():
    """Keep real HA setup/reload/settings, replacing only provider I/O."""
    with ExitStack() as stack:
        for name, data in {
            "MeteoSwissDataUpdateCoordinator": {"temperature": 12},
            "OpenMeteoDataUpdateCoordinator": {"temperature": 12},
            "MeteoSwissStationConditionCoordinator": {},
            "MeteoSwissForecastCoordinator": [],
            "MeteoSwissAlertsCoordinator": [],
            "OpenMeteoPollenCoordinator": {},
            "MeteoSwissPollenCoordinator": {},
        }.items():
            stack.enter_context(patch(
                f"custom_components.meteoswiss.coordinator.{name}._async_update_data",
                return_value=data,
            ))
        stack.enter_context(patch(
            "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
            return_value={},
        ))
        for cls in (MeteoSwissConfigFlow, MeteoSwissOptionsFlow):
            stack.enter_context(patch.object(cls, "_load_stations", return_value=[]))
        yield


def make_entry(hass, source):
    entry = MockConfigEntry(domain=DOMAIN, data={
        "data_source": source, "station_id": "klo", "station_name": "Open-Meteo" if source == "openmeteo" else "Kloten",
        "latitude": 0, "longitude": 0, "postal_code": "9997",
    }, options={"pollen_station": "PZH"})
    entry.add_to_hass(hass)
    return entry


def device_by_key(hass, entry, key):
    found = [d for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
             if (DOMAIN, key) in d.identifiers]
    assert len(found) == 1
    return found[0]


@pytest.mark.parametrize("family", ["sensor", "weather"])
@pytest.mark.parametrize("source", [None, "meteoswiss", "openmeteo", "legacy"])
async def test_current_group_and_attribution_match_selected_provider(hass, family, source):
    entry = MockConfigEntry(domain=DOMAIN, data={} if source is None else {"data_source": source})
    coordinator = DataUpdateCoordinator(hass, logging.getLogger(__name__), name="source", config_entry=entry)
    coordinator.data = {"temperature": 12}
    entity = (MeteoSwissWeather(coordinator, None, entry, "Example station") if family == "weather"
              else MeteoSwissSensor(coordinator, entry, SENSOR_DESCRIPTIONS[0], "Example station"))
    info = entity.device_info
    assert info["identifiers"] == {(DOMAIN, entry.entry_id)}
    assert info["entry_type"] is dr.DeviceEntryType.SERVICE
    if source == "openmeteo":
        assert info["name"] == "Open-Meteo Current Weather"
        assert info["manufacturer"] == "Open-Meteo"
        assert info["model"] == "Weather Forecast API"
        assert entity.attribution == "Source: Open-Meteo Weather Forecast API (modelled current conditions)"
    else:
        assert info["name"] == "MeteoSwiss Example station"
        assert info["manufacturer"] == "MeteoSwiss"
        assert info["model"] == "SwissMetNet"
        assert entity.attribution == "Source: MeteoSwiss"


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize("disabled", [None, er.RegistryEntryDisabler.USER, er.RegistryEntryDisabler.INTEGRATION])
async def test_existing_current_group_is_corrected_in_place_without_losing_choices(
    hass, enable_custom_integrations, provider_sources, source, disabled
):
    entry = make_entry(hass, source)
    registry, devices = er.async_get(hass), dr.async_get(hass)
    old_device = devices.async_get_or_create(config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)}, name="MeteoSwiss Open-Meteo",
        manufacturer="MeteoSwiss", model="SwissMetNet")
    devices.async_update_device(old_device.id, name_by_user="My weather group")
    kept = registry.async_get_or_create("sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_temperature",
        config_entry=entry, suggested_object_id="my_temperature", device_id=old_device.id,
        disabled_by=disabled)
    kept = registry.async_update_entity(kept.entity_id, name="My temperature", icon="mdi:star",
                                        aliases={"Personal temperature"})
    for initial in (True, False):
        if initial:
            assert await hass.config_entries.async_setup(entry.entry_id)
        else:
            assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        current = registry.async_get(kept.entity_id)
        assert (current.unique_id, current.device_id, current.name, current.icon, current.aliases, current.disabled_by) == (
            kept.unique_id, kept.device_id, kept.name, kept.icon, kept.aliases, kept.disabled_by)
        device = device_by_key(hass, entry, entry.entry_id)
        assert device.id == old_device.id and device.name_by_user == "My weather group"
        assert device.manufacturer == ("Open-Meteo" if source == "openmeteo" else "MeteoSwiss")
        assert device.model == ("Weather Forecast API" if source == "openmeteo" else "SwissMetNet")
        if disabled is None:
            assert hass.states.get(kept.entity_id).state == "12"
        else:
            assert hass.states.get(kept.entity_id) is None
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize("route", ["configure", "reconfigure"])
async def test_pollen_station_round_trip_reuses_all_groups_and_entity_bindings(
    hass, enable_custom_integrations, provider_sources, source, route
):
    entry = make_entry(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry, devices = er.async_get(hass), dr.async_get(hass)
    pollen = device_by_key(hass, entry, f"ms_pollen_{entry.entry_id}")
    devices.async_update_device(pollen.id, name_by_user="My measured pollen")
    uid = f"{DOMAIN}_{entry.entry_id}_ms_pollen_birch"
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, uid)
    registry.async_update_entity(entity_id, name="My birch", icon="mdi:flower",
        disabled_by=er.RegistryEntryDisabler.USER, hidden_by=er.RegistryEntryHider.USER,
        aliases={"Birch alias"})
    registry.async_update_entity_options(entity_id, "sensor", {"display_precision": 1})

    def bindings():
        return {e.unique_id: (e.entity_id, e.device_id, e.name, e.icon, e.disabled_by,
                             e.hidden_by, e.aliases, e.options)
                for e in er.async_entries_for_config_entry(registry, entry.entry_id)}

    original = bindings()
    original_devices = {d.id: d.identifiers for d in dr.async_entries_for_config_entry(devices, entry.entry_id)}
    assert len(original_devices) == 7
    with patch.object(devices, "async_remove_device", wraps=devices.async_remove_device) as remove_device, \
         patch.object(registry, "async_remove", wraps=registry.async_remove) as remove_entity:
        for station in ("PBE", "PZH"):
            manager = hass.config_entries.options if route == "configure" else hass.config_entries.flow
            form = (await manager.async_init(entry.entry_id) if route == "configure" else
                    await manager.async_init(DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}))
            values = form["data_schema"]({"pollen_station": station})
            result = await manager.async_configure(form["flow_id"], values)
            assert result["type"] == ("create_entry" if route == "configure" else "abort")
            if route == "reconfigure":
                assert result["reason"] == "reconfigure_successful"
            await hass.async_block_till_done()
            assert entry.options["pollen_station"] == station
            assert entry.runtime_data.meteoswiss_pollen_coordinator.client.station_id == station.lower()
            current = device_by_key(hass, entry, f"ms_pollen_{entry.entry_id}")
            assert current.id == pollen.id and current.name_by_user == "My measured pollen"
            assert current.name == f"MeteoSwiss Pollen (Measured) - {POLLEN_STATIONS[station]}"
            assert bindings() == original
            assert {d.id: d.identifiers for d in dr.async_entries_for_config_entry(devices, entry.entry_id)} == original_devices
        remove_device.assert_not_called()
        remove_entity.assert_not_called()
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

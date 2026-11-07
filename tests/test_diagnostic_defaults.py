"""Native HA registration, retained choices and virtual service metadata."""

from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.sensor import DATA_COMPONENT
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from ha_helpers import MockConfigEntry

from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.sensor import (
    MeteoSwissCacheStatsSensor,
    MeteoSwissStationsMapSensor,
)

DIAGNOSTICS = ("stations_map", "cache_stats")


@pytest.fixture
def quiet_sources():
    """Mock provider transports and observe only the diagnostic polling."""
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
        updates = [stack.enter_context(patch.object(cls, "async_update", new_callable=AsyncMock))
                   for cls in (MeteoSwissStationsMapSensor, MeteoSwissCacheStatsSensor)]
        yield updates


def config_entry(hass, source):
    entry = MockConfigEntry(domain=DOMAIN, data={
        "data_source": source, "station_id": "KLO", "station_name": "Kloten",
        "latitude": 0, "longitude": 0, "postal_code": "9997",
    })
    entry.add_to_hass(hass)
    return entry


def diagnostic_entries(hass):
    registry = er.async_get(hass)
    return [registry.async_get(registry.async_get_entity_id("sensor", DOMAIN, f"{DOMAIN}_{key}"))
            for key in DIAGNOSTICS]


def service_device(devices, entry_id, key):
    """Keep lookup scoped to the owning entry on both supported HAs."""
    matches = [device for device in dr.async_entries_for_config_entry(devices, entry_id)
               if (DOMAIN, key) in device.identifiers]
    assert len(matches) == 1
    return matches[0]


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
async def test_new_diagnostics_are_registered_disabled_without_polling(
    hass, enable_custom_integrations, quiet_sources, source
):
    entry = config_entry(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for entity in diagnostic_entries(hass):
        assert entity.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        assert entity.entity_category is EntityCategory.DIAGNOSTIC
        assert hass.states.get(entity.entity_id) is None
    for update in quiet_sources:
        update.assert_not_awaited()
    registry = er.async_get(hass)
    for platform, suffix in [("weather", "weather"), ("sensor", "temperature"),
                             ("sensor", "ms_pollen_birch"), ("binary_sensor", "any_alert")]:
        entity_id = registry.async_get_entity_id(
            platform, DOMAIN, f"{DOMAIN}_{entry.entry_id}_{suffix}"
        )
        assert registry.async_get(entity_id).disabled_by is None
        assert hass.states.get(entity_id) is not None
    devices = dr.async_get(hass)
    for key in (entry.entry_id, f"calculated_{entry.entry_id}", f"pollen_{entry.entry_id}",
                f"ms_pollen_{entry.entry_id}", f"alerts_{entry.entry_id}", *DIAGNOSTICS):
        device = service_device(devices, entry.entry_id, key)
        assert device is not None and device.entry_type is dr.DeviceEntryType.SERVICE
        assert device.manufacturer and device.model
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize("disabled_by", [
    None, er.RegistryEntryDisabler.USER, er.RegistryEntryDisabler.INTEGRATION,
])
async def test_existing_choices_ids_and_device_overrides_survive_setup_and_reload(
    hass, enable_custom_integrations, quiet_sources, source, disabled_by
):
    entry = config_entry(hass, source)
    registry = er.async_get(hass)
    kept = []
    for key in DIAGNOSTICS:
        entity = registry.async_get_or_create(
            "sensor", DOMAIN, f"{DOMAIN}_{key}", config_entry=entry,
            suggested_object_id="kept_"+key, disabled_by=disabled_by,
        )
        kept.append(registry.async_update_entity(
            entity.entity_id, name="My "+key, icon="mdi:star"
        ))
    devices = dr.async_get(hass)
    device = devices.async_get_or_create(config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)}, name="Original weather", manufacturer="MeteoSwiss")
    devices.async_update_device(device.id, name_by_user="My weather service")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for reload in (False, True):
        if reload:
            assert await hass.config_entries.async_reload(entry.entry_id)
            await hass.async_block_till_done()
        for previous, current in zip(kept, diagnostic_entries(hass), strict=True):
            assert (
                current.entity_id, current.unique_id, current.name,
                current.icon, current.disabled_by,
            ) == (
                previous.entity_id, previous.unique_id, previous.name,
                previous.icon, previous.disabled_by,
            )
            assert (hass.states.get(current.entity_id) is not None) is (disabled_by is None)
        current_device = service_device(devices, entry.entry_id, entry.entry_id)
        assert current_device.id == device.id
        assert current_device.name_by_user == "My weather service"
        assert current_device.entry_type is dr.DeviceEntryType.SERVICE
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
async def test_new_diagnostics_can_be_enabled_without_new_entities_or_devices(
    hass, enable_custom_integrations, quiet_sources, source
):
    entry = config_entry(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry = er.async_get(hass)
    before = diagnostic_entries(hass)
    device_ids = {entity.device_id for entity in before}
    for entity in before:
        registry.async_update_entity(entity.entity_id, disabled_by=None)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    after = diagnostic_entries(hass)
    assert [entity.entity_id for entity in after] == [entity.entity_id for entity in before]
    assert {entity.device_id for entity in after} == device_ids
    for entity in after:
        assert entity.disabled_by is None and hass.states.get(entity.entity_id) is not None
        sensor = hass.data[DATA_COMPONENT].get_entity(entity.entity_id)
        await sensor.async_update_ha_state(force_refresh=True)
    for update in quiet_sources:
        assert update.await_count > 0
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

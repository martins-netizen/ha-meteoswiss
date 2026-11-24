"""Native fixed service roles across source, settings and ownership changes."""

from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.components.sensor import DATA_COMPONENT
from homeassistant.config_entries import SOURCE_RECONFIGURE
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.update_coordinator import UpdateFailed
from ha_helpers import MockConfigEntry

from custom_components.meteoswiss.config_flow import (
    MeteoSwissConfigFlow,
    MeteoSwissOptionsFlow,
)
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.diagnostic_lifecycle import DATA_SHARED_DIAGNOSTICS
from custom_components.meteoswiss.forecast_locations import parse_forecast_catalogue
from custom_components.meteoswiss.sensor import (
    MeteoSwissCacheStatsSensor,
    MeteoSwissStationsMapSensor,
)

NOW = datetime(2026, 11, 17, 10, 20, tzinfo=UTC)
SHARED_ROLES = {"stations_map", "cache_stats"}
STATIONS = [
    {"id": "klo", "name": "Kloten", "label": "Kloten (KLO)", "lat": 47.48, "lon": 8.53},
    {"id": "sma", "name": "Fluntern", "label": "Fluntern (SMA)", "lat": 47.38, "lon": 8.57},
]


@pytest.fixture
def service_sources(freezer):
    """Replace provider work, retaining native setup, entities and registries."""
    freezer.move_to(NOW)
    state = {"optional_failure": False}
    healthy = {
        "MeteoSwissDataUpdateCoordinator": {"temperature": 12, "last_update": NOW.isoformat()},
        "OpenMeteoDataUpdateCoordinator": {"temperature": 12, "last_update": NOW.isoformat()},
        "MeteoSwissStationConditionCoordinator": {},
        "MeteoSwissForecastCoordinator": [{
            "datetime": NOW.replace(minute=0).isoformat(),
            "fetched_at": NOW.isoformat(), "temperature": 4, "condition": "cloudy",
        }],
        "MeteoSwissAlertsCoordinator": [],
        "OpenMeteoPollenCoordinator": {"birch_pollen": {"current": 0}, "pm10": 4},
        "MeteoSwissPollenCoordinator": {"birch": {"current": 0}},
    }
    with ExitStack() as stack:
        for name, data in healthy.items():
            optional = name not in {"MeteoSwissDataUpdateCoordinator", "OpenMeteoDataUpdateCoordinator"}

            async def update(value=data, is_optional=optional):
                if is_optional and state["optional_failure"]:
                    raise UpdateFailed("source unavailable")
                return value

            stack.enter_context(patch(
                f"custom_components.meteoswiss.coordinator.{name}._async_update_data",
                side_effect=update,
            ))
        for cls in (MeteoSwissStationsMapSensor, MeteoSwissCacheStatsSensor):
            stack.enter_context(patch.object(cls, "async_update", new_callable=AsyncMock))
        for cls in (MeteoSwissConfigFlow, MeteoSwissOptionsFlow):
            stack.enter_context(patch.object(cls, "_load_stations", return_value=STATIONS))
            stack.enter_context(patch.object(cls, "_validate_source", return_value=True))
            stack.enter_context(patch.object(cls, "_validate_forecast", return_value=True))
        catalogue = parse_forecast_catalogue(
            (Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv")
            .read_text().encode("latin-1"), NOW,
        )
        stack.enter_context(patch(
            "custom_components.meteoswiss.config_flow.MeteoSwissForecastCatalogueClient.async_get_catalogue",
            return_value=catalogue,
        ))
        yield state


def entry_for(hass, source):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={"data_source": source, "station_id": "klo", "station_name": "Kloten",
              "latitude": 47.48, "longitude": 8.53, "postal_code": "8302"},
        options={"pollen_station": "PZH"}, version=1, minor_version=2,
    )
    entry.add_to_hass(hass)
    return entry


def expected_roles(entry):
    return {entry.entry_id, *(f"{prefix}_{entry.entry_id}" for prefix in (
        "calculated", "alerts", "pollen", "ms_pollen")), *SHARED_ROLES}


def role_devices(hass, entry):
    devices = dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)
    assert len(devices) == 7
    assert all(device.entry_type is dr.DeviceEntryType.SERVICE for device in devices)
    assert all(len(device.identifiers) == 1 for device in devices)
    result = {next(iter(device.identifiers))[1]: device for device in devices}
    assert {next(iter(device.identifiers))[0] for device in devices} == {DOMAIN}
    assert result.keys() == expected_roles(entry)
    return result


def bindings(hass, entry):
    return {row.unique_id: (
        row.id, row.entity_id, row.device_id, row.name, row.icon, row.aliases,
        row.hidden_by, row.disabled_by, row.options,
    ) for row in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)}


def device_choices(devices):
    return {key: (device.id, device.identifiers, device.name_by_user, device.area_id,
                  device.labels, device.disabled_by) for key, device in devices.items()}


def representative_ids(hass, entry):
    registry = er.async_get(hass)
    return {key: registry.async_get_entity_id(platform, DOMAIN, f"{DOMAIN}_{entry.entry_id}_{suffix}")
            for key, platform, suffix in (
                ("current", "sensor", "temperature"),
                ("forecast", "weather", "forecast_weather"),
                ("warnings", "binary_sensor", "any_alert"),
                ("modelled_pollen", "sensor", "pollen_birch_pollen"),
                ("measured_pollen", "sensor", "ms_pollen_birch"),
            )}


def optional_coordinators(entry):
    data = entry.runtime_data
    return [coordinator for coordinator in (
        data.forecast_coordinator, data.alerts_coordinator, data.pollen_coordinator,
        data.meteoswiss_pollen_coordinator, data.station_condition_coordinator,
    ) if coordinator is not None]


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
async def test_optional_failure_and_recovery_keep_all_service_roles(
    hass, enable_custom_integrations, service_sources, source,
):
    service_sources["optional_failure"] = True
    entry = entry_for(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    roles = device_choices(role_devices(hass, entry))
    original = bindings(hass, entry)
    ids = representative_ids(hass, entry)
    assert all(ids.values())
    assert hass.states.get(ids["current"]).state == "12"
    assert all(hass.states.get(entity_id).state == "unavailable"
               for key, entity_id in ids.items() if key != "current")
    registry, devices = er.async_get(hass), dr.async_get(hass)
    with patch.object(devices, "async_remove_device", wraps=devices.async_remove_device) as remove_device, \
         patch.object(registry, "async_remove", wraps=registry.async_remove) as remove_entity:
        for failure in (False, True):
            service_sources["optional_failure"] = failure
            for coordinator in optional_coordinators(entry):
                await coordinator.async_refresh()
            await hass.async_block_till_done()
            assert bindings(hass, entry) == original
            assert device_choices(role_devices(hass, entry)) == roles
            assert hass.states.get(ids["current"]).state == "12"
            for key, entity_id in ids.items():
                if key != "current":
                    assert (hass.states.get(entity_id).state == "unavailable") is failure
        remove_device.assert_not_called()
        remove_entity.assert_not_called()
    coordinators = optional_coordinators(entry) + [entry.runtime_data.coordinator]
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert all(not coordinator._listeners for coordinator in coordinators)
    assert DATA_SHARED_DIAGNOSTICS not in hass.data[DOMAIN]


async def settings(hass, entry, route, values):
    manager = hass.config_entries.options if route == "configure" else hass.config_entries.flow
    form = (await manager.async_init(entry.entry_id) if route == "configure" else
            await manager.async_init(DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}))
    form = await manager.async_configure(form["flow_id"], form["data_schema"](values))
    if values["forecast_action"] == "search":
        assert form["step_id"] == "forecast_select"
        form = await manager.async_configure(form["flow_id"], {"point": "3:711"})
    assert form["step_id"] in {"forecast_confirm", "settings_confirm"}
    result = await manager.async_configure(form["flow_id"], {})
    assert result["type"] == ("create_entry" if route == "configure" else "abort")
    if route == "reconfigure":
        assert result["reason"] == "reconfigure_successful"


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize("route", ["configure", "reconfigure"])
async def test_complete_settings_roundtrip_reuses_seven_groups_and_user_choices(
    hass, enable_custom_integrations, service_sources, source, route,
):
    entry = entry_for(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    registry, devices = er.async_get(hass), dr.async_get(hass)
    roles = role_devices(hass, entry)
    devices.async_update_device(roles[f"alerts_{entry.entry_id}"].id, name_by_user="My warnings")
    kept_id = representative_ids(hass, entry)["measured_pollen"]
    registry.async_update_entity(kept_id, name="My birch", icon="mdi:flower",
        aliases={"Birch alias"}, disabled_by=er.RegistryEntryDisabler.USER,
        hidden_by=er.RegistryEntryHider.USER)
    registry.async_update_entity_options(kept_id, "sensor", {"display_precision": 1})
    original = bindings(hass, entry)
    original_devices = device_choices(role_devices(hass, entry))
    changes = [
        {"station_id": "sma", "latitude": 46.95, "longitude": 7.44,
         "postal_code": "8001", "pollen_station": "PBE", "forecast_action": "search",
         "query": "Saentis"},
        {"station_id": "klo", "latitude": 47.48, "longitude": 8.53,
         "postal_code": "8302", "pollen_station": "PZH", "forecast_action": "base"},
    ]
    with patch.object(devices, "async_remove_device", wraps=devices.async_remove_device) as remove_device, \
         patch.object(registry, "async_remove", wraps=registry.async_remove) as remove_entity:
        for change in changes:
            values = {key: value for key, value in change.items() if (
                key not in {"latitude", "longitude"} if source == "meteoswiss" else key != "station_id"
            )}
            previous = entry.runtime_data
            with patch.object(hass.config_entries, "async_reload", wraps=hass.config_entries.async_reload) as reload:
                await settings(hass, entry, route, values)
                await hass.async_block_till_done()
                assert reload.await_count == 1
            current = entry.runtime_data
            assert current is not previous and not previous.session.closed
            assert all(not coordinator._listeners for coordinator in (
                previous.coordinator, previous.forecast_coordinator, previous.alerts_coordinator,
                previous.pollen_coordinator, previous.meteoswiss_pollen_coordinator,
            ))
            assert bindings(hass, entry) == original
            assert device_choices(role_devices(hass, entry)) == original_devices
            assert current.alerts_coordinator._alerts_api.postal_code == change["postal_code"]
            assert current.meteoswiss_pollen_coordinator.client.station_id == change["pollen_station"].lower()
            if source == "meteoswiss":
                assert current.coordinator.station_id == change["station_id"]
            else:
                assert (current.coordinator.latitude, current.coordinator.longitude) == (
                    change["latitude"], change["longitude"],
                )
            if change["forecast_action"] == "search":
                assert current.forecast_target.location.point.name == "Säntis"
            else:
                assert current.forecast_target.status == "legacy"
        remove_device.assert_not_called()
        remove_entity.assert_not_called()
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
async def test_native_entry_removal_transfers_only_shared_roles_without_peer_reload(
    hass, enable_custom_integrations, service_sources, source,
):
    owner = entry_for(hass, source)
    registry = er.async_get(hass)
    for key in SHARED_ROLES:
        registry.async_get_or_create("sensor", DOMAIN, f"{DOMAIN}_{key}", config_entry=owner,
                                     disabled_by=None)
    assert await hass.config_entries.async_setup(owner.entry_id)
    await hass.async_block_till_done()
    shared_devices = {key: device for key, device in role_devices(hass, owner).items() if key in SHARED_ROLES}
    shared_entities = {key: registry.async_get_entity_id("sensor", DOMAIN, f"{DOMAIN}_{key}")
                       for key in SHARED_ROLES}
    assert all(hass.data[DATA_COMPONENT].get_entity(entity_id) is not None
               for entity_id in shared_entities.values())
    peer = entry_for(hass, "openmeteo" if source == "meteoswiss" else "meteoswiss")
    assert await hass.config_entries.async_setup(peer.entry_id)
    await hass.async_block_till_done()
    runtime = peer.runtime_data
    peer_bindings = bindings(hass, peer)
    with ExitStack() as stack:
        reload = stack.enter_context(patch.object(hass.config_entries, "async_reload", wraps=hass.config_entries.async_reload))
        refreshes = [stack.enter_context(patch.object(coordinator, "async_refresh", wraps=coordinator.async_refresh))
                     for coordinator in optional_coordinators(peer) + [runtime.coordinator]]
        assert (await hass.config_entries.async_remove(owner.entry_id))["require_restart"] is False
        await hass.async_block_till_done()
        reload.assert_not_awaited()
        for refresh in refreshes:
            refresh.assert_not_awaited()
    assert peer.runtime_data is runtime
    roles = role_devices(hass, peer)
    for key in SHARED_ROLES:
        assert roles[key].id == shared_devices[key].id
        row = registry.async_get(shared_entities[key])
        assert row.config_entry_id == peer.entry_id
        assert row.device_id == shared_devices[key].id
        assert hass.data[DATA_COMPONENT].get_entity(row.entity_id) is not None
    assert {key: value for key, value in bindings(hass, peer).items()
            if key not in {f"{DOMAIN}_{role}" for role in SHARED_ROLES}} == peer_bindings
    assert not er.async_entries_for_config_entry(registry, owner.entry_id)
    assert not dr.async_entries_for_config_entry(dr.async_get(hass), owner.entry_id)
    assert len(dr.async_get(hass).devices) == 7
    assert (await hass.config_entries.async_remove(peer.entry_id))["require_restart"] is False
    await hass.async_block_till_done()
    assert not dr.async_get(hass).devices
    assert DATA_SHARED_DIAGNOSTICS not in hass.data[DOMAIN]

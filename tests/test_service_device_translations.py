"""Native service-group names with retained bindings, privacy and history."""

from datetime import UTC, datetime, timedelta
from functools import partial
import json

import pytest
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers import label_registry as lr
from homeassistant.helpers.translation import async_get_translations
from homeassistant.setup import async_setup_component
from ha_helpers import MockConfigEntry, async_wait_recording_done

from custom_components.meteoswiss.const import DOMAIN, POLLEN_STATIONS
from custom_components.meteoswiss.diagnostics import async_get_config_entry_diagnostics
from test_provider_device_metadata import provider_sources

STATION = "Example Zürich / Échallens"
POSTCODE = "0012"
NAMES = {
    "en": ("Open-Meteo Current Weather", "Open-Meteo Air Quality & Pollen",
           "MeteoSwiss Alerts - {postal_code}", "MeteoSwiss Pollen (Measured) - {station}"),
    "de": ("Open-Meteo Aktuelles Wetter", "Open-Meteo Luftqualität und Pollen",
           "MeteoSwiss Wetterwarnungen - {postal_code}", "MeteoSwiss Pollen (gemessen) - {station}"),
    "fr": ("Open-Meteo Météo actuelle", "Open-Meteo Qualité de l’air et pollen",
           "MeteoSwiss Alertes météo - {postal_code}", "MeteoSwiss Pollen (mesuré) - {station}"),
    "it": ("Open-Meteo Meteo attuale", "Open-Meteo Qualità dell’aria e pollini",
           "MeteoSwiss Allerte meteo - {postal_code}", "MeteoSwiss Pollini (misurati) - {station}"),
}


def entry_for(hass, source):
    entry = MockConfigEntry(domain=DOMAIN, data={
        "data_source": source, "station_id": "klo", "station_name": STATION,
        "latitude": 0, "longitude": 0, "postal_code": POSTCODE,
    }, options={"pollen_station": "PZH"})
    entry.add_to_hass(hass)
    return entry


def groups(hass, entry):
    return {next(iter(d.identifiers))[1]: d for d in
            dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)}


def expected_names(entry, language):
    current, air, warnings, measured = NAMES[language]
    return {
        entry.entry_id: current if entry.data["data_source"] == "openmeteo" else "MeteoSwiss " + STATION,
        f"pollen_{entry.entry_id}": air,
        f"alerts_{entry.entry_id}": warnings.format(postal_code=POSTCODE),
        f"ms_pollen_{entry.entry_id}": measured.format(station=POLLEN_STATIONS["PZH"]),
    }


def bindings(hass, entry):
    return {e.unique_id: (e.id, e.entity_id, e.device_id, e.name, e.icon, e.aliases,
                         e.area_id, e.labels, e.disabled_by, e.hidden_by, e.options)
            for e in er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)}


@pytest.mark.parametrize("language", NAMES)
@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
async def test_ha_loads_device_names_without_translating_places_or_exporting_them(
    hass, enable_custom_integrations, provider_sources, language, source
):
    await hass.config.async_update(language=language)
    assert await async_setup_component(hass, DOMAIN, {})
    entry = entry_for(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    current = groups(hass, entry)
    assert len(current) == 7
    for key, name in expected_names(entry, language).items():
        assert current[key].name == name
        assert current[key].entry_type is dr.DeviceEntryType.SERVICE
    texts = await async_get_translations(hass, language, "device", {DOMAIN})
    for key, expected in zip(
        ["current_openmeteo", "modelled_air_quality", "warnings", "measured_pollen"],
        NAMES[language], strict=True,
    ):
        assert texts[f"component.{DOMAIN}.device.{key}.name"] == expected
    assert texts[f"component.{DOMAIN}.device.current_meteoswiss.name"] == "MeteoSwiss {station}"
    assert current[entry.entry_id].manufacturer == ("Open-Meteo" if source == "openmeteo" else "MeteoSwiss")
    assert current[f"ms_pollen_{entry.entry_id}"].model == "Pollen Station"
    diagnostic_data = await async_get_config_entry_diagnostics(hass, entry)
    diagnostics = json.dumps(diagnostic_data, ensure_ascii=False)
    assert STATION not in diagnostics
    assert diagnostic_data["config_entry"]["data"]["station_name"] == "**REDACTED**"
    assert diagnostic_data["config_entry"]["data"]["postal_code"] == "**REDACTED**"
    assert "translation_placeholders" not in diagnostics
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize("disabled", [None, er.RegistryEntryDisabler.USER, er.RegistryEntryDisabler.INTEGRATION])
@pytest.mark.parametrize("personal_names", [False, True])
async def test_legacy_english_groups_and_all_personal_bindings_survive_language_round_trip(
    hass, enable_custom_integrations, provider_sources, source, disabled, personal_names
):
    assert await async_setup_component(hass, DOMAIN, {})
    entry = entry_for(hass, source)
    devices, entities = dr.async_get(hass), er.async_get(hass)
    area = ar.async_get(hass).async_create("Weather services")
    label = lr.async_get(hass).async_create("Retained services")
    old_devices = {}
    for key, name in expected_names(entry, "en").items():
        old = devices.async_get_or_create(config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, key)}, name=name, entry_type=dr.DeviceEntryType.SERVICE)
        old = devices.async_update_device(old.id, area_id=area.id, labels={label.label_id},
            name_by_user="Personal " + key if personal_names else None)
        old_devices[key] = (old.id, old.name_by_user, old.area_id, old.labels, old.disabled_by)
    families = [("sensor", "temperature", entry.entry_id),
                ("weather", "weather", entry.entry_id),
                ("sensor", "pollen_birch_pollen", f"pollen_{entry.entry_id}"),
                ("binary_sensor", "any_alert", f"alerts_{entry.entry_id}"),
                ("sensor", "ms_pollen_birch", f"ms_pollen_{entry.entry_id}")]
    for platform, suffix, key in families:
        saved = entities.async_get_or_create(platform, DOMAIN, f"{DOMAIN}_{entry.entry_id}_{suffix}",
            config_entry=entry, device_id=old_devices[key][0], suggested_object_id="retained_" + suffix,
            original_name=None if platform == "weather" else {
                "temperature": "Temperature", "pollen_birch_pollen": "Birch Pollen",
                "any_alert": "Weather Alert", "ms_pollen_birch": "Birch Pollen (Measured)",
            }[suffix], disabled_by=disabled)
        entities.async_update_entity(saved.entity_id,
            name="Personal " + suffix if personal_names else None, icon="mdi:star",
            aliases={"Alias " + suffix},
            area_id=None if platform == "weather" and not personal_names else area.id,
            labels={label.label_id},
            hidden_by=er.RegistryEntryHider.USER)
        if platform == "sensor":
            # A previously loaded temperature entity already has HA's precision
            # suggestion as well as the user's explicit precision override.
            options = {"display_precision": 1}
            if suffix == "temperature":
                options["suggested_display_precision"] = 1
            entities.async_update_entity_options(saved.entity_id, "sensor", options)
    before = bindings(hass, entry)
    for index, language in enumerate([*NAMES, "en"]):
        await hass.config.async_update(language=language)
        assert await (hass.config_entries.async_setup(entry.entry_id) if index == 0 else
                      hass.config_entries.async_reload(entry.entry_id))
        await hass.async_block_till_done()
        current_bindings = bindings(hass, entry)
        assert {uid: current_bindings[uid] for uid in before} == before, [
            (uid, position, old, current_bindings[uid][position])
            for uid, values in before.items() for position, old in enumerate(values)
            if old != current_bindings[uid][position]
        ]
        if index == 0:
            all_bindings, all_device_ids = current_bindings, {d.id for d in groups(hass, entry).values()}
        else:
            assert current_bindings == all_bindings
            assert {d.id for d in groups(hass, entry).values()} == all_device_ids
        for key, name in expected_names(entry, language).items():
            device = groups(hass, entry)[key]
            assert device.name == name
            assert (device.id, device.name_by_user, device.area_id, device.labels, device.disabled_by) == old_devices[key]
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
async def test_device_disablement_and_source_failure_do_not_change_identity_or_choices(
    hass, enable_custom_integrations, provider_sources, source
):
    assert await async_setup_component(hass, DOMAIN, {})
    entry = entry_for(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    devices = dr.async_get(hass)
    device = groups(hass, entry)[entry.entry_id]
    devices.async_update_device(device.id, disabled_by=dr.DeviceEntryDisabler.USER)
    await hass.async_block_till_done()
    before = bindings(hass, entry)
    entry.runtime_data.coordinator.async_set_update_error(ValueError("synthetic source failure"))
    await hass.async_block_till_done()
    await hass.config.async_update(language="de")
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    current = groups(hass, entry)[entry.entry_id]
    assert current.id == device.id and current.disabled_by is dr.DeviceEntryDisabler.USER
    assert current.name == expected_names(entry, "de")[entry.entry_id]
    assert bindings(hass, entry) == before
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
async def test_recorder_retains_old_rows_and_appends_at_same_entity_id_after_translation(
    recorder_mock, hass, enable_custom_integrations, provider_sources, freezer, source
):
    now = datetime(2026, 11, 12, 12, tzinfo=UTC)
    freezer.move_to(now)
    assert await async_setup_component(hass, DOMAIN, {})
    entry = entry_for(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    target = er.async_get(hass).async_get_entity_id("sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_temperature")
    await async_wait_recording_done(hass)

    async def history():
        data = await hass.async_add_executor_job(partial(get_significant_states,
            hass, now - timedelta(seconds=1), now + timedelta(minutes=4), entity_ids=[target]))
        return [(s.state, s.last_changed, dict(s.attributes)) for s in data[target]]

    before, identity = await history(), bindings(hass, entry)
    freezer.move_to(now + timedelta(minutes=1))
    await hass.config.async_update(language="de")
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    freezer.move_to(now + timedelta(minutes=2))
    entry.runtime_data.coordinator.async_set_updated_data({"temperature": 13})
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)
    after = await history()
    assert before and all(row in after for row in before)
    assert {row[0] for row in after} >= {"12", "13"}
    assert bindings(hass, entry) == identity
    assert await hass.config_entries.async_unload(entry.entry_id)

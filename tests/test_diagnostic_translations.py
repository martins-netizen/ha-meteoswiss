"""HA-loaded diagnostic names and retained registry choices in four languages."""

import pytest
from homeassistant.components.sensor import DATA_COMPONENT
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.translation import async_get_translations

from custom_components.meteoswiss.const import DOMAIN
from test_diagnostic_defaults import (
    DIAGNOSTICS,
    config_entry,
    diagnostic_entries,
    quiet_sources,
    service_device,
)

LABELS = {
    "en": ("Weather Stations", "Cache Statistics"),
    "de": ("Wetterstationen", "Cache-Statistik"),
    "fr": ("Stations météo", "Statistiques du cache"),
    "it": ("Stazioni meteo", "Statistiche della cache"),
}


@pytest.mark.parametrize("language", LABELS)
@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
async def test_new_names_are_loaded_by_ha_and_diagnostics_stay_disabled(
    hass, enable_custom_integrations, quiet_sources, language, source
):
    await hass.config.async_update(language=language)
    entry = config_entry(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    devices = dr.async_get(hass)
    translations = await async_get_translations(hass, language, "entity", {DOMAIN})
    device_texts = await async_get_translations(hass, language, "device", {DOMAIN})
    for key, saved, label in zip(
        DIAGNOSTICS, diagnostic_entries(hass), LABELS[language], strict=True
    ):
        assert saved.original_name == label
        assert saved.translation_key == key
        assert saved.disabled_by is er.RegistryEntryDisabler.INTEGRATION
        assert saved.entity_category is EntityCategory.DIAGNOSTIC
        assert hass.states.get(saved.entity_id) is None
        device = service_device(devices, entry.entry_id, key)
        assert device.name == "MeteoSwiss " + label
        assert translations[f"component.{DOMAIN}.entity.sensor.{key}.name"] == label
        assert device_texts[f"component.{DOMAIN}.device.{key}.name"] == "MeteoSwiss " + label
    for update in quiet_sources:
        update.assert_not_awaited()
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize("language", LABELS)
@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize("disabled", [None, er.RegistryEntryDisabler.USER, er.RegistryEntryDisabler.INTEGRATION])
@pytest.mark.parametrize("custom_name", [False, True])
async def test_legacy_identity_personal_choices_and_history_target_are_retained(
    hass, enable_custom_integrations, quiet_sources, language, source, disabled, custom_name
):
    await hass.config.async_update(language=language)
    entry = config_entry(hass, source)
    entities, devices = er.async_get(hass), dr.async_get(hass)
    area = ar.async_get(hass).async_create("Weather technical")
    before = []
    device_before = []
    for key in DIAGNOSTICS:
        device = devices.async_get_or_create(
            config_entry_id=entry.entry_id, identifiers={(DOMAIN, key)},
            name="MeteoSwiss " + LABELS["en"][DIAGNOSTICS.index(key)],
            manufacturer="MeteoSwiss",
        )
        device = devices.async_update_device(device.id, name_by_user="My " + key, area_id=area.id)
        saved = entities.async_get_or_create(
            "sensor", DOMAIN, f"{DOMAIN}_{key}", config_entry=entry,
            device_id=device.id, suggested_object_id="retained_" + key,
            original_name=LABELS["en"][DIAGNOSTICS.index(key)], disabled_by=disabled,
        )
        saved = entities.async_update_entity(
            saved.entity_id, name="Personal " + key if custom_name else None,
            icon="mdi:star", aliases={"Alias " + key}, area_id=area.id,
        )
        before.append(saved)
        device_before.append(device)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for reload in (False, True):
        if reload:
            assert await hass.config_entries.async_reload(entry.entry_id)
            await hass.async_block_till_done()
        for index, (old, new) in enumerate(zip(before, diagnostic_entries(hass), strict=True)):
            assert (new.id, new.entity_id, new.unique_id, new.device_id, new.name,
                    new.icon, new.aliases, new.area_id, new.disabled_by) == (
                        old.id, old.entity_id, old.unique_id, old.device_id, old.name,
                        old.icon, old.aliases, old.area_id, old.disabled_by)
            assert new.original_name == LABELS[language][index]
            device = devices.async_get(new.device_id)
            assert (device.id, device.name_by_user, device.area_id) == (
                device_before[index].id, device_before[index].name_by_user, area.id)
            state = hass.states.get(new.entity_id)
            assert (state is None) is (disabled is not None)
            if state is not None:
                expected = device.name_by_user + " " + (old.name if custom_name else LABELS[language][index])
                assert state.attributes["friendly_name"] == expected
                assert hass.data[DATA_COMPONENT].get_entity(new.entity_id).name == LABELS[language][index]
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize("custom_name", [False, True])
async def test_language_change_on_reload_keeps_entity_and_device_identity(
    hass, enable_custom_integrations, quiet_sources, custom_name
):
    entry = config_entry(hass, "meteoswiss")
    entities = er.async_get(hass)
    for key in DIAGNOSTICS:
        saved = entities.async_get_or_create(
            "sensor", DOMAIN, f"{DOMAIN}_{key}", config_entry=entry,
            suggested_object_id="language_retained_" + key,
        )
        if custom_name:
            entities.async_update_entity(saved.entity_id, name="Personal " + key)
    for language in LABELS:
        await hass.config.async_update(language=language)
        if language == "en":
            assert await hass.config_entries.async_setup(entry.entry_id)
        else:
            assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        current = diagnostic_entries(hass)
        if language == "en":
            kept = [(x.id, x.entity_id, x.device_id, x.name) for x in current]
        assert [(x.id, x.entity_id, x.device_id, x.name) for x in current] == kept
        assert [x.original_name for x in current] == list(LABELS[language])
        for index, saved in enumerate(current):
            assert dr.async_get(hass).async_get(saved.device_id).name == "MeteoSwiss " + LABELS[language][index]
    assert await hass.config_entries.async_unload(entry.entry_id)

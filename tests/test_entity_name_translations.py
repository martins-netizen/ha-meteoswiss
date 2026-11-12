"""Resolve every exposed entity name through HA, retaining registry contracts."""

import json
from pathlib import Path

import pytest
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers import label_registry as lr
from homeassistant.helpers.translation import async_get_translations

from custom_components.meteoswiss.const import DOMAIN
from test_provider_device_metadata import make_entry, provider_sources

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components" / DOMAIN
LANGUAGES = ("en", "de", "fr", "it")
OBSERVATIONS = {
    "temperature", "humidity", "wind_speed", "wind_direction", "pressure",
    "precipitation", "wind_gust", "dew_point", "sunshine_duration",
    "global_radiation", "snow_depth", "foehn_index",
}
FORECASTS = {
    f"forecast_{metric}_{day}"
    for metric in ("maximum_temperature", "minimum_temperature", "precipitation", "probability")
    for day in ("today", "tomorrow")
}
OTHER_SENSORS = {
    "pm25", "pm10", "nitrogen_dioxide", "ozone", "uv_index", "heating_degree_days",
    "pollen_birch", "pollen_alder", "pollen_grass", "pollen_mugwort", "pollen_ambrosia",
    "ms_pollen_birch", "ms_pollen_alder", "ms_pollen_hazel", "ms_pollen_grass",
    "ms_pollen_beech", "ms_pollen_ash", "ms_pollen_oak", "stations_map", "cache_stats",
}
ALERTS = {"any_alert", "critical_alert", "upcoming_alert"}
# Retain the old catalogue entries without inventing active entities for them.
INACTIVE_KEYS = {
    "soil_temperature_5cm", "soil_temperature_10cm", "soil_temperature_20cm",
    "season_heating_degree_days",
}


def registered(hass, entry):
    return er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)


def live_entity(hass, saved):
    return hass.data[saved.domain].get_entity(saved.entity_id)


def expected_keys(source):
    sensors = OBSERVATIONS | FORECASTS | OTHER_SENSORS
    if source == "openmeteo":
        sensors = sensors - {"precipitation"} | {"precipitation_modelled"}
    return {"sensor": sensors, "binary_sensor": ALERTS}


async def assert_native_names(hass, entry, language):
    """Check native registry/runtime names against each translated catalogue."""
    catalog = json.loads((COMPONENT / "translations" / f"{language}.json").read_text())
    texts = await async_get_translations(hass, language, "entity", {DOMAIN})
    seen = {"sensor": set(), "binary_sensor": set()}
    weather_ids = set()
    for saved in registered(hass, entry):
        state = hass.states.get(saved.entity_id)
        device = dr.async_get(hass).async_get(saved.device_id)
        if saved.domain == "weather":
            weather_ids.add(saved.unique_id)
            # These entities inherit their translated device name by design.
            assert saved.original_name is None and saved.translation_key is None
            if saved.disabled_by is None:
                entity = live_entity(hass, saved)
                assert entity.has_entity_name is True and entity.name is None
                device_name = device.name_by_user or device.name
                expected = f"{device_name} {saved.name}" if saved.name else device_name
                assert state.attributes["friendly_name"] == expected
            continue
        key = saved.translation_key
        assert key in expected_keys(entry.data["data_source"])[saved.domain]
        seen[saved.domain].add(key)
        expected = catalog["entity"][saved.domain][key]["name"]
        assert texts[f"component.{DOMAIN}.entity.{saved.domain}.{key}.name"] == expected
        assert saved.original_name == expected
        if saved.disabled_by is None:
            entity = live_entity(hass, saved)
            assert entity.has_entity_name is True
            assert entity.translation_key == key
            assert entity.name == expected
            assert state.attributes["friendly_name"] == f"{device.name_by_user or device.name} {saved.name or expected}"
        else:
            assert state is None
    assert seen == expected_keys(entry.data["data_source"])
    assert weather_ids == {
        f"{DOMAIN}_{entry.entry_id}_weather", f"{DOMAIN}_{entry.entry_id}_forecast_weather",
    }
    assert len(registered(hass, entry)) == 45


@pytest.mark.parametrize("language", LANGUAGES)
@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
async def test_every_exposed_name_is_resolved_by_ha_in_each_language(
    hass, enable_custom_integrations, provider_sources, language, source
):
    await hass.config.async_update(language=language)
    entry = make_entry(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    await assert_native_names(hass, entry, language)
    assert await hass.config_entries.async_unload(entry.entry_id)


def test_name_inventory_distinguishes_active_provider_keys_and_retained_legacy_keys():
    """Fail when a new catalogue name has no reviewed native coverage."""
    strings = json.loads((COMPONENT / "strings.json").read_text())
    active = expected_keys("meteoswiss")["sensor"] | expected_keys("openmeteo")["sensor"]
    assert len(active) == 41
    assert set(strings["entity"]["sensor"]) == active | INACTIVE_KEYS
    assert set(strings["entity"]["binary_sensor"]) == ALERTS
    assert set(strings["entity"]) == {"sensor", "binary_sensor"}
    for language in LANGUAGES:
        catalog = json.loads((COMPONENT / "translations" / f"{language}.json").read_text())
        assert set(catalog["entity"]["sensor"]) == active | INACTIVE_KEYS
        assert set(catalog["entity"]["binary_sensor"]) == ALERTS
    assert strings == json.loads((COMPONENT / "translations" / "en.json").read_text())


def retained_bindings(hass, entry):
    return {
        saved.unique_id: (saved.id, saved.entity_id, saved.device_id, saved.name,
                          saved.icon, saved.aliases, saved.disabled_by, saved.hidden_by,
                          saved.area_id, saved.labels, saved.options)
        for saved in registered(hass, entry)
    }


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize("personal_names", [False, True])
@pytest.mark.parametrize("disabled", [None, er.RegistryEntryDisabler.USER, er.RegistryEntryDisabler.INTEGRATION])
async def test_all_existing_entity_bindings_and_choices_survive_language_round_trip(
    hass, enable_custom_integrations, provider_sources, source, personal_names, disabled
):
    entry = make_entry(hass, source)
    registry = er.async_get(hass)
    area = ar.async_get(hass).async_create("Weather entities")
    label = lr.async_get(hass).async_create("Retained weather")
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    for saved in registered(hass, entry):
        registry.async_update_entity(
            saved.entity_id, name=f"Personal {saved.unique_id}" if personal_names else None,
            icon="mdi:star", aliases={f"Alias {saved.unique_id}"}, disabled_by=disabled,
            hidden_by=er.RegistryEntryHider.USER,
            area_id=area.id if saved.domain != "weather" or personal_names else None,
            labels={label.label_id},
        )
        if saved.domain == "sensor":
            registry.async_update_entity_options(saved.entity_id, "sensor", {
                **saved.options.get("sensor", {}), "display_precision": 1,
            })
    # Let HA apply enable/disable decisions through its normal reload path.
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    before = retained_bindings(hass, entry)
    devices_before = {d.id for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)}
    for language in (*LANGUAGES, "en"):
        await hass.config.async_update(language=language)
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        await assert_native_names(hass, entry, language)
        assert retained_bindings(hass, entry) == before
        assert {d.id for d in dr.async_entries_for_config_entry(dr.async_get(hass), entry.entry_id)} == devices_before
    assert await hass.config_entries.async_unload(entry.entry_id)

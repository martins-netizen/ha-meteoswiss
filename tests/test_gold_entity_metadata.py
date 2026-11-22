"""Review every native entity against an independent quantity/metadata inventory.

These expectations describe the public quantities, not the integration's entity
descriptions. Provider I/O is replaced; HA registration, disabled defaults,
reloads and the optional observed-HGT Recorder path remain real.
"""

from dataclasses import dataclass, replace

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import EntityCategory

from custom_components.meteoswiss.const import DOMAIN
from test_hgt_ogd_lifecycle import source_data as source_data
from test_provider_device_metadata import make_entry
from test_provider_device_metadata import provider_sources as provider_sources
from test_wind_statistics import initially_stopped as initially_stopped


@dataclass(frozen=True)
class ExpectedMetadata:
    """The semantic contract for one registered quantity or service helper."""

    translation_key: str | None
    device_class: str | None = None
    unit: str | None = None
    state_class: str | None = None
    category: EntityCategory | None = None
    enabled: bool = True

    @property
    def state_unit(self):
        """HA canonicalizes the density micro sign when publishing the unit."""
        return "μg/m³" if self.unit == "µg/m³" else self.unit


# Observation units describe the measured quantity. Wind direction deliberately
# starts without a statistics class: circular statistics require the separate
# verified Recorder migration, exercised by test_wind_* rather than bypassed here.
OBSERVATIONS = {
    "temperature": ("temperature", "°C", "measurement"),
    "humidity": ("humidity", "%", "measurement"),
    "wind_speed": ("wind_speed", "km/h", "measurement"),
    "wind_direction": ("wind_direction", "°", None),
    "pressure": ("pressure", "hPa", "measurement"),
    "precipitation": ("precipitation", "mm", "measurement"),
    "wind_gust": ("wind_speed", "km/h", "measurement"),
    "dew_point": ("temperature", "°C", "measurement"),
    "sunshine_duration": ("duration", "min", "measurement"),
    "global_radiation": ("irradiance", "W/m²", "measurement"),
    "snow_depth": ("distance", "cm", "measurement"),
    # A numeric Foehn category code is not wind speed, AQI or a textual HA enum.
    "foehn_index": (None, "Code", "measurement"),
}
AIR_QUALITY = {
    "pm25": ("pm25", "µg/m³", "measurement"),
    "pm10": ("pm10", "µg/m³", "measurement"),
    "nitrogen_dioxide": ("nitrogen_dioxide", "µg/m³", "measurement"),
    "ozone": ("ozone", "µg/m³", "measurement"),
    # UV Index is an index, not irradiance or power; HA has no fitting UV class.
    "uv_index": (None, "UV Index", "measurement"),
}
FORECAST_QUANTITIES = {
    "maximum_temperature": ("temperature", "°C"),
    "minimum_temperature": ("temperature", "°C"),
    "precipitation": ("precipitation", "mm"),
    # Rain probability in percent is not humidity and is not a measurement.
    "probability": (None, "%"),
}
MODELLED_POLLEN = {
    "birch_pollen": "pollen_birch",
    "alder_pollen": "pollen_alder",
    "grass_pollen": "pollen_grass",
    "mugwort_pollen": "pollen_mugwort",
    "ragweed_pollen": "pollen_ambrosia",
}
MEASURED_POLLEN = ("birch", "alder", "hazel", "grass", "beech", "ash", "oak")
DIAGNOSTICS = ("stations_map", "cache_stats")
WEATHER_UNITS = {
    "native_temperature_unit": "°C",
    "native_pressure_unit": "hPa",
    "native_wind_speed_unit": "km/h",
    "native_precipitation_unit": "mm",
}


def expected_metadata(source, *, observed_hgt=False, wind_ready=False):
    """Specify every existing entity, independently of descriptor collections."""
    expected = {
        ("sensor", key): ExpectedMetadata(key, *quantity)
        for key, quantity in (OBSERVATIONS | AIR_QUALITY).items()
    }
    if source == "openmeteo":
        key = ("sensor", "precipitation")
        expected[key] = replace(expected[key], translation_key="precipitation_modelled")
    if wind_ready:
        key = ("sensor", "wind_direction")
        expected[key] = replace(expected[key], state_class="measurement_angle")
    for day in ("today", "tomorrow"):
        for quantity, (device_class, unit) in FORECAST_QUANTITIES.items():
            key = f"forecast_{quantity}_{day}"
            expected["sensor", key] = ExpectedMetadata(key, device_class, unit)

    for key in ("forecast_global_radiation_next_hour", "forecast_diffuse_radiation_next_hour"):
        expected["sensor", key] = ExpectedMetadata(key, "irradiance", "W/m²")
    key = "forecast_peak_wind_gust_24h"
    expected["sensor", key] = ExpectedMetadata(key, "wind_speed", "km/h")

    # Degree days combine temperature difference and time. Neither temperature,
    # temperature_delta nor duration fits °C·d. Forecast HGT is not a measured
    # series; observed HGT uses separate station-specific external statistics.
    expected["sensor", "heating_degree_days"] = ExpectedMetadata(
        "heating_degree_days", unit="°C·d"
    )
    if observed_hgt:
        expected["sensor", "heating_degree_days_observed"] = ExpectedMetadata(
            "hgt_measured", unit="°C·d"
        )

    # Species-specific pollen counts have no fitting standard HA device class.
    # These existing sensors retain provider units in their extra attributes;
    # do not reinterpret them as particulate mass or invent measurement LTS.
    for species, translation_key in MODELLED_POLLEN.items():
        expected["sensor", f"pollen_{species}"] = ExpectedMetadata(translation_key)
    for species in MEASURED_POLLEN:
        key = f"ms_pollen_{species}"
        expected["sensor", key] = ExpectedMetadata(key)

    for key in DIAGNOSTICS:
        expected["sensor", key] = ExpectedMetadata(
            key, category=EntityCategory.DIAGNOSTIC, enabled=False
        )
    for key in ("any_alert", "critical_alert", "upcoming_alert"):
        expected["binary_sensor", key] = ExpectedMetadata(key, "safety")
    # Weather entities inherit their service-device name and expose platform
    # native units rather than a sensor-style unit/state/device class.
    for key in ("weather", "forecast_weather"):
        expected["weather", key] = ExpectedMetadata(None)
    return expected


def registered_entities(hass, entry):
    """Select actual HA registrations by domain and stable unique-ID suffix."""
    saved = er.async_entries_for_config_entry(er.async_get(hass), entry.entry_id)
    prefix = f"{DOMAIN}_{entry.entry_id}_"
    result = {}
    for entity in saved:
        if entity.unique_id in {f"{DOMAIN}_{key}" for key in DIAGNOSTICS}:
            suffix = entity.unique_id.removeprefix(f"{DOMAIN}_")
        else:
            assert entity.unique_id.startswith(prefix), entity.unique_id
            suffix = entity.unique_id.removeprefix(prefix)
        key = (entity.domain, suffix)
        assert key not in result, key
        result[key] = entity
    assert len(result) == len(saved)
    return result


def assert_native_metadata(hass, entry, expected, *, diagnostics_enabled=False):
    """Check HA registry, live entities and published attributes, not descriptors."""
    registered = registered_entities(hass, entry)
    assert registered.keys() == expected.keys()
    for key, metadata in expected.items():
        saved = registered[key]
        assert saved.original_device_class == metadata.device_class, key
        assert saved.unit_of_measurement == metadata.state_unit, key
        assert saved.entity_category is metadata.category, key
        assert saved.has_entity_name is True, key
        assert saved.translation_key == metadata.translation_key, key
        assert (saved.capabilities or {}).get("state_class") == metadata.state_class, key
        enabled = metadata.enabled or diagnostics_enabled
        assert saved.disabled_by is (None if enabled else er.RegistryEntryDisabler.INTEGRATION), key
        state = hass.states.get(saved.entity_id)
        if not enabled:
            assert state is None, key
            continue
        entity = hass.data[saved.domain].get_entity(saved.entity_id)
        assert entity is not None and state is not None, key
        assert entity.has_entity_name is True, key
        assert entity.entity_registry_enabled_default is metadata.enabled, key
        assert entity.entity_category is metadata.category, key
        assert entity.device_class == metadata.device_class, key
        assert getattr(entity, "native_unit_of_measurement", None) == metadata.unit, key
        assert getattr(entity, "state_class", None) == metadata.state_class, key
        assert state.attributes.get("device_class") == metadata.device_class, key
        assert state.attributes.get("state_class") == metadata.state_class, key
        assert state.attributes.get("unit_of_measurement") == metadata.state_unit, key
        if saved.domain == "weather":
            assert entity.name is None and saved.original_name is None, key
            for property_name, unit in WEATHER_UNITS.items():
                assert getattr(entity, property_name) == unit, (key, property_name)
        else:
            assert entity.translation_key == metadata.translation_key, key
            assert entity.name and entity.name == saved.original_name, key
        if key == ("sensor", "wind_direction"):
            assert state.attributes["wind_statistics_status"] == (
                "ready" if metadata.state_class == "measurement_angle" else "pending"
            )
    return registered


async def check_registered_inventory(hass, entry, *, observed_hgt, wind_ready=False):
    """Inspect disabled defaults first, then enable existing diagnostic helpers."""
    expected = expected_metadata(
        entry.data["data_source"], observed_hgt=observed_hgt, wind_ready=wind_ready
    )
    assert len(expected) == (49 if observed_hgt else 48)
    # No lifecycle shortcut may enable circular statistics before HA startup.
    assert hass.is_running is wind_ready
    initial = assert_native_metadata(hass, entry, expected)
    original_ids = {key: saved.entity_id for key, saved in initial.items()}
    registry = er.async_get(hass)
    for key in DIAGNOSTICS:
        registry.async_update_entity(initial["sensor", key].entity_id, disabled_by=None)
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done(wait_background_tasks=True)
    current = assert_native_metadata(hass, entry, expected, diagnostics_enabled=True)
    assert {key: saved.entity_id for key, saved in current.items()} == original_ids


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
async def test_all_45_base_entities_have_reviewed_native_metadata(
    initially_stopped, hass, enable_custom_integrations, provider_sources, source
):
    entry = make_entry(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    try:
        await hass.async_block_till_done(wait_background_tasks=True)
        await check_registered_inventory(hass, entry, observed_hgt=False)
    finally:
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
async def test_recorder_adds_observed_hgt_only_for_its_official_provider(
    recorder_mock, hass, enable_custom_integrations, source_data, source
):
    entry = make_entry(hass, source)
    assert await hass.config_entries.async_setup(entry.entry_id)
    try:
        await hass.async_block_till_done(wait_background_tasks=True)
        # Core and the real Recorder are running here. Do not patch or shortcut
        # wind preparation: only its verified ready path may expose circular LTS.
        await check_registered_inventory(
            hass, entry, observed_hgt=source == "meteoswiss", wind_ready=True
        )
        if source == "meteoswiss":
            assert source_data.await_count > 0
        else:
            source_data.assert_not_awaited()
    finally:
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)

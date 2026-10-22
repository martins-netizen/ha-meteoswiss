"""HA must serve help and localised source choices for actual setup fields."""

import pytest
from homeassistant.helpers.translation import async_get_translations

from custom_components.meteoswiss.const import DOMAIN


@pytest.mark.parametrize("language", ["en", "de", "fr", "it"])
async def test_ha_serves_field_help_for_every_setup_step(
    hass, enable_custom_integrations, language
):
    translated = await async_get_translations(hass, language, "config", {DOMAIN})
    for step, fields in {
        "user": ("data_source", "pollen_station", "update_interval"),
        "meteoswiss": ("postal_code", "station_id"),
        "openmeteo": ("postal_code", "latitude", "longitude"),
    }.items():
        for field in fields:
            key = f"component.{DOMAIN}.config.step.{step}.data_description.{field}"
            assert translated.get(key), key


@pytest.mark.parametrize("language", ["en", "de", "fr", "it"])
async def test_ha_serves_only_real_options_with_help(
    hass, enable_custom_integrations, language
):
    translated = await async_get_translations(hass, language, "options", {DOMAIN})
    for field in ("update_interval", "pollen_station"):
        assert translated.get(
            f"component.{DOMAIN}.options.step.init.data_description.{field}"
        )
    assert f"component.{DOMAIN}.options.step.init.data.data_source" not in translated


@pytest.mark.parametrize("language", ["en", "de", "fr", "it"])
async def test_ha_serves_both_localised_source_choices(
    hass, enable_custom_integrations, language
):
    translated = await async_get_translations(hass, language, "selector", {DOMAIN})
    for source in ("meteoswiss", "openmeteo"):
        assert translated.get(
            f"component.{DOMAIN}.selector.data_source.options.{source}"
        )

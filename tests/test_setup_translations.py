"""HA must serve help and localised source choices for actual setup fields."""

from unittest.mock import patch
from urllib.parse import urlsplit

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.config_flow import (
    MeteoSwissConfigFlow,
    MeteoSwissOptionsFlow,
)
from custom_components.meteoswiss.const import DOMAIN


@pytest.mark.parametrize("language", ["en", "de", "fr", "it"])
async def test_ha_serves_field_help_for_every_setup_step(
    hass, enable_custom_integrations, language
):
    translated = await async_get_translations(hass, language, "config", {DOMAIN})
    assert not any("update_interval" in key for key in translated)
    for step, fields in {
        "user": ("data_source", "pollen_station"),
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
    for field in ("pollen_station",):
        assert translated.get(
            f"component.{DOMAIN}.options.step.init.data_description.{field}"
        )
    assert f"component.{DOMAIN}.options.step.init.data.data_source" not in translated
    assert not any("update_interval" in key for key in translated)


@pytest.mark.parametrize("language", ["en", "de", "fr", "it"])
async def test_ha_serves_both_localised_source_choices(
    hass, enable_custom_integrations, language
):
    translated = await async_get_translations(hass, language, "selector", {DOMAIN})
    for source in ("meteoswiss", "openmeteo"):
        assert translated.get(
            f"component.{DOMAIN}.selector.data_source.options.{source}"
        )


@pytest.mark.parametrize(
    "language,expected_host",
    [
        ("de", "www.meteoschweiz.admin.ch"),
        ("en", "www.meteoswiss.admin.ch"),
        ("fr", "www.meteosuisse.admin.ch"),
        ("it", "www.meteosvizzera.admin.ch"),
        ("nl", "www.meteoswiss.admin.ch"),
        (None, "www.meteoschweiz.admin.ch"),
    ],
)
async def test_native_station_forms_supply_localised_link_placeholders(
    hass, enable_custom_integrations, language, expected_host
):
    """HA forms must supply URLs separately from translated help text."""
    hass.config.language = "de"
    context = {"language": language} if language is not None else {}
    stations = [{"id": "klo", "label": "Zürich/Kloten (KLO)"}]
    with (
        patch.object(MeteoSwissConfigFlow, "_load_stations", return_value=stations),
        patch.object(MeteoSwissOptionsFlow, "_load_stations", return_value=stations),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER, **context}
        )
        setup = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"data_source": "meteoswiss", "pollen_station": "PZH"},
        )
        entry = MockConfigEntry(
            domain=DOMAIN,
            data={"station_id": "klo", "postal_code": "8302"},
        )
        entry.add_to_hass(hass)
        options = await hass.config_entries.options.async_init(
            entry.entry_id, context=context
        )
    for category, step, form in (
        ("config", "meteoswiss", setup),
        ("options", "init", options),
    ):
        texts = await async_get_translations(
            hass, language or "de", category, {DOMAIN}
        )
        help_text = texts[
            f"component.{DOMAIN}.{category}.step.{step}.data_description.station_id"
        ]
        assert "https://" not in help_text
        placeholders = form["description_placeholders"]
        rendered = help_text.format(**placeholders)
        url = urlsplit(placeholders["station_map_url"])
        assert url.scheme == "https" and url.hostname == expected_host
        assert not url.query and not url.fragment
        assert f"]({url.geturl()})" in rendered
        assert "{station_map_url}" not in rendered
        if category == "options":
            assert placeholders["current_location"]
    assert entry.data == {"station_id": "klo", "postal_code": "8302"}

"""Keep existing visual contracts while using native frontend icon translations."""

import json
from pathlib import Path

import pytest
from homeassistant.helpers import entity_registry as er

from custom_components.meteoswiss.binary_sensor import ALERT_SENSOR_DESCRIPTIONS
from custom_components.meteoswiss.pollen_sensor import POLLEN_SENSOR_DESCRIPTIONS
from custom_components.meteoswiss.sensor import (
    FORECAST_SENSOR_DESCRIPTIONS,
    MS_POLLEN_SENSOR_DESCRIPTIONS,
)
from test_forecast_summary_entities import installed_summary  # noqa: F401

COMPONENT = Path(__file__).parents[1] / "custom_components" / "meteoswiss"
ICONS = json.loads((COMPONENT / "icons.json").read_text())["entity"]


@pytest.mark.parametrize("platform", ["sensor", "binary_sensor"])
def test_every_icon_uses_an_existing_translation_in_all_languages(platform):
    for language in ("en", "de", "fr", "it"):
        catalogue = json.loads((COMPONENT / "translations" / f"{language}.json").read_text())
        assert set(ICONS[platform]) <= set(catalogue["entity"][platform])
    assert all(set(value) == {"default"} for value in ICONS[platform].values())
    assert all(value["default"].startswith("mdi:") for value in ICONS[platform].values())


@pytest.mark.parametrize(
    "platform,descriptions",
    [
        ("sensor", FORECAST_SENSOR_DESCRIPTIONS),
        ("sensor", MS_POLLEN_SENSOR_DESCRIPTIONS),
        ("sensor", POLLEN_SENSOR_DESCRIPTIONS),
        ("binary_sensor", ALERT_SENSOR_DESCRIPTIONS),
    ],
)
def test_active_descriptions_allow_frontend_icon_resolution(platform, descriptions):
    for description in descriptions:
        assert description.translation_key in ICONS[platform]
        assert description.icon is None


def test_measured_hazel_keeps_the_existing_tree_outline():
    assert ICONS["sensor"]["ms_pollen_hazel"]["default"] == "mdi:tree-outline"
    assert ICONS["sensor"]["ms_pollen_oak"]["default"] == "mdi:tree-outline"


async def test_user_name_and_icon_survive_native_entry_reload(hass, installed_summary):
    entry, ids, _ = installed_summary
    entity_id = ids["forecast_probability_today"]
    registry = er.async_get(hass)
    before = registry.async_get(entity_id)
    unique_id = before.unique_id
    assert before.translation_key == "forecast_probability_today"
    assert "icon" not in hass.states.get(entity_id).attributes
    registry.async_update_entity(entity_id, name="Personal forecast", icon="mdi:star")
    await hass.async_block_till_done()
    assert hass.states.get(entity_id).attributes["icon"] == "mdi:star"
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    after = registry.async_get(entity_id)
    assert after.unique_id == unique_id
    assert after.name == "Personal forecast"
    assert after.icon == "mdi:star"
    assert hass.states.get(entity_id).attributes["icon"] == "mdi:star"

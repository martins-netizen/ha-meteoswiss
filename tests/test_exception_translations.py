"""User-facing source errors must be translated without leaking payloads."""

import ast
import json
from pathlib import Path

import pytest
from homeassistant.helpers.translation import async_get_translations

from custom_components.meteoswiss.const import DOMAIN

COMPONENT = Path(__file__).parents[1] / "custom_components" / "meteoswiss"


def update_error_calls():
    return [
        node
        for node in ast.walk(ast.parse((COMPONENT / "coordinator.py").read_text()))
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "UpdateFailed"
    ]


def test_all_update_failures_use_translation_metadata_without_raw_details():
    calls = update_error_calls()
    assert calls
    for call in calls:
        assert not call.args
        keywords = {kw.arg: kw.value for kw in call.keywords}
        assert set(keywords) == {"translation_domain", "translation_key"}
        assert isinstance(keywords["translation_domain"], ast.Name)
        assert keywords["translation_domain"].id == "DOMAIN"
        assert isinstance(keywords["translation_key"], ast.Constant)
        assert isinstance(keywords["translation_key"].value, str)


@pytest.mark.parametrize("language", ["en", "de", "fr", "it"])
async def test_ha_serves_every_actual_update_failure_message(
    hass, enable_custom_integrations, language
):
    translated = await async_get_translations(hass, language, "exceptions", {DOMAIN})
    keys = {
        next(kw.value.value for kw in call.keywords if kw.arg == "translation_key")
        for call in update_error_calls()
    }
    catalogue = json.loads((COMPONENT / "translations" / f"{language}.json").read_text())
    assert set(catalogue["exceptions"]) == keys
    for key in keys:
        message = translated[f"component.{DOMAIN}.exceptions.{key}.message"]
        assert message == catalogue["exceptions"][key]["message"]
        assert message.strip()
        assert not any(marker in message for marker in ("{", "http", "parsed_data", "[%key:"))

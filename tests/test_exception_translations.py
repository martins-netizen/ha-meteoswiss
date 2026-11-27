"""User-facing source errors must be translated without leaking payloads."""

import ast
import json
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.translation import async_get_translations
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.meteoswiss.cache import clear_all_caches
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.coordinator import MeteoSwissDataUpdateCoordinator

COMPONENT = Path(__file__).parents[1] / "custom_components" / "meteoswiss"
STALE_KEY = "station_observations_stale"


def update_error_calls():
    return [
        node
        for path in COMPONENT.glob("*.py")
        for node in ast.walk(ast.parse(path.read_text()))
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
        if "retry_after" in keywords:
            # Core's numeric retry hint adds no user-facing text. Admit only
            # this bounded HGT helper; keep every translation/privacy assertion.
            retry = keywords.pop("retry_after")
            assert ast.dump(retry) == ast.dump(
                ast.parse("self._transient_retry_delay()", mode="eval").body
            )
            assert keywords["translation_key"].value == "hgt_ogd_unavailable"
        if "translation_placeholders" in keywords:
            # Only the computed numeric age can enter the stale-station message.
            placeholders = keywords.pop("translation_placeholders")
            assert keywords["translation_key"].value == STALE_KEY
            assert ast.dump(placeholders) == ast.dump(
                ast.parse('{"age_minutes": str(err.age_minutes)}', mode="eval").body
            )
        assert set(keywords) == {"translation_domain", "translation_key"}
        assert isinstance(keywords["translation_domain"], ast.Name)
        assert keywords["translation_domain"].id == "DOMAIN"
        assert isinstance(keywords["translation_key"], ast.Constant)
        assert isinstance(keywords["translation_key"].value, str)


@pytest.fixture
async def stale_observation_failure(hass, aioclient_mock, freezer):
    csv_url = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/klo/ogd-smn_klo_t_now.csv"
    freezer.move_to("2026-10-15T18:40:00+00:00")
    aioclient_mock.get(
        csv_url,
        text="station_abbr;reference_timestamp;tre200s0\nKLO;15.10.2026 17:30;13\n",
    )
    station = MeteoSwissDataUpdateCoordinator(hass, "KLO", 600, async_get_clientsession(hass))
    clear_all_caches()
    try:
        with patch.object(station, "_async_get_station_data_url", return_value=csv_url):
            await station.async_refresh()
    finally:
        clear_all_caches()
    error = station.last_exception
    assert isinstance(error, UpdateFailed)
    assert error.translation_key == STALE_KEY
    assert error.translation_placeholders == {"age_minutes": "70"}
    return error


@pytest.mark.parametrize("language", ["en", "de", "fr", "it"])
async def test_ha_serves_every_actual_update_failure_message(
    hass, enable_custom_integrations, stale_observation_failure, language
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
        if key == STALE_KEY:
            assert message.count("{age_minutes}") == 1
            message = message.format_map(stale_observation_failure.translation_placeholders)
            assert "70" in message
        assert message.strip()
        assert not any(marker in message for marker in ("{", "http", "parsed_data", "[%key:"))

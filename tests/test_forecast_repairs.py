"""Real HA issue lifecycle, manual settings recovery and provider-outage boundaries."""

from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_RECONFIGURE, ConfigEntryDisabler
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.translation import async_get_translations
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.config_flow import MeteoSwissConfigFlow
from custom_components.meteoswiss.const import CONF_FORECAST_LOCATION, DOMAIN
from custom_components.meteoswiss.forecast_location_config import (
    encode_forecast_location,
)
from custom_components.meteoswiss.forecast_locations import (
    ForecastLocation,
    parse_forecast_catalogue,
)

BASE = {
    "data_source": "openmeteo",
    "latitude": 47.45,
    "longitude": 8.56,
    "postal_code": "8302",
    "station_name": "Home",
}
INVALID = {"private-point": "do-not-publish-this-payload"}


@pytest.fixture
def sources(hass, enable_custom_integrations):
    """Keep native entry/flow lifecycle while replacing external source work."""
    with ExitStack() as stack:
        mocks = {}
        for name, value in {
            "OpenMeteoDataUpdateCoordinator": {"temperature": 12},
            "MeteoSwissForecastCoordinator": [],
            "MeteoSwissAlertsCoordinator": [],
            "OpenMeteoPollenCoordinator": {},
            "MeteoSwissPollenCoordinator": {},
        }.items():
            mocks[name] = stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.coordinator."
                    f"{name}._async_update_data",
                    return_value=value,
                )
            )
        stack.enter_context(
            patch.object(
                hass.config_entries, "async_forward_entry_setups", return_value=None
            )
        )
        stack.enter_context(
            patch.object(
                hass.config_entries, "async_unload_platforms", return_value=True
            )
        )
        yield mocks


@pytest.fixture
def catalogue():
    raw = (
        (Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv")
        .read_text()
        .encode("latin-1")
    )
    return parse_forecast_catalogue(raw, datetime(2026, 10, 23, tzinfo=UTC))


def entry_for(hass, *, invalid=True, suffix="A"):
    data = {**BASE, "unrelated_setting": "retained"}
    if invalid:
        data[CONF_FORECAST_LOCATION] = dict(INVALID)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=f"Weather entry {suffix}",
        unique_id=f"retained-{suffix}",
        data=data,
        options={"pollen_station": "PZH", "update_interval": 900},
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    return entry


def issue_for(hass, entry):
    return ir.async_get(hass).async_get_issue(
        DOMAIN, f"invalid_forecast_location_{entry.entry_id}"
    )


async def start(hass, entry):
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return issue_for(hass, entry)


async def reconfigure(hass, entry):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )


async def configure(hass, result, data):
    values = result["data_schema"](data)
    return await hass.config_entries.flow.async_configure(result["flow_id"], values)


async def select_point(hass, result):
    result = await configure(hass, result, {"forecast_action": "search"})
    result = await configure(hass, result, {"query": "Säntis"})
    return await configure(hass, result, {"point": "3:711"})


async def test_entry_issues_are_private_deduplicated_and_removed_independently(
    hass, sources
):
    first = entry_for(hass)
    issue = await start(hass, first)
    second = entry_for(hass, suffix="B")
    await start(hass, second)
    assert not issue.is_fixable and not issue.is_persistent
    assert issue.data is None
    assert issue.translation_placeholders == {
        "entry_title": first.title,
        "configuration_url": "/config/integrations/integration/meteoswiss",
    }
    assert "private-point" not in repr(issue)
    assert "do-not-publish-this-payload" not in repr(issue)
    assert issue.learn_more_url.endswith("/docs/REPAIRS.md")
    registry = ir.async_get(hass)
    registry.async_ignore(DOMAIN, issue.issue_id, True)
    dismissed = issue_for(hass, first).dismissed_version
    assert dismissed is not None
    assert await hass.config_entries.async_reload(first.entry_id)
    await hass.async_block_till_done()
    assert issue_for(hass, first).created == issue.created
    assert issue_for(hass, first).dismissed_version == dismissed
    assert len([key for key in registry.issues if key[0] == DOMAIN]) == 2
    await hass.config_entries.async_remove(first.entry_id)
    await hass.async_block_till_done()
    assert issue_for(hass, first) is None
    assert issue_for(hass, second) is not None


@pytest.mark.parametrize("action", ["base", "point"])
async def test_reconfigure_cancellation_keeps_issue_until_explicit_commit(
    hass, sources, catalogue, action
):
    entry = entry_for(hass)
    await start(hass, entry)
    original_data, original_options = dict(entry.data), dict(entry.options)
    with (
        patch(
            "custom_components.meteoswiss.config_flow."
            "MeteoSwissForecastCatalogueClient.async_get_catalogue",
            return_value=catalogue,
        ),
        patch.object(MeteoSwissConfigFlow, "_validate_forecast", return_value=True),
    ):
        result = await reconfigure(hass, entry)
        result = (
            await select_point(hass, result)
            if action == "point"
            else await configure(hass, result, {"forecast_action": "base"})
        )
        assert result["step_id"] == "settings_confirm"
        assert issue_for(hass, entry) is not None and entry.data == original_data
        hass.config_entries.flow.async_abort(result["flow_id"])
        assert issue_for(hass, entry) is not None and entry.data == original_data
        result = await reconfigure(hass, entry)
        result = (
            await select_point(hass, result)
            if action == "point"
            else await configure(hass, result, {"forecast_action": "base"})
        )
        result = await configure(hass, result, {})
    assert result["type"] == "abort" and result["reason"] == "reconfigure_successful"
    assert issue_for(hass, entry) is None
    await hass.async_block_till_done()
    assert issue_for(hass, entry) is None
    assert entry.options == original_options and entry.unique_id == "retained-A"
    assert {
        k: v for k, v in entry.data.items() if k != CONF_FORECAST_LOCATION
    } == BASE | {"unrelated_setting": "retained"}
    assert (CONF_FORECAST_LOCATION in entry.data) == (action == "point")
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


@pytest.mark.parametrize("current_available", [True, False])
async def test_options_reset_clears_issue_only_after_confirmation(
    hass, sources, current_available
):
    entry = entry_for(hass)
    await start(hass, entry)
    original_data, original_options = dict(entry.data), dict(entry.options)
    if not current_available:
        sources["OpenMeteoDataUpdateCoordinator"].side_effect = UpdateFailed("Offline")
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            **{k: BASE[k] for k in ("latitude", "longitude", "postal_code")},
            "pollen_station": "PZH",
            "forecast_action": "base",
        },
    )
    assert result["step_id"] == "forecast_confirm"
    assert entry.data == original_data and issue_for(hass, entry) is not None
    result = await hass.config_entries.options.async_configure(result["flow_id"], {})
    assert result["type"] == "create_entry"
    assert issue_for(hass, entry) is None
    await hass.async_block_till_done()
    assert entry.options == original_options and entry.unique_id == "retained-A"
    assert CONF_FORECAST_LOCATION not in entry.data
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1


async def test_failed_selected_point_check_keeps_issue_and_original_data(
    hass, sources, catalogue
):
    entry = entry_for(hass)
    await start(hass, entry)
    original = dict(entry.data)
    with (
        patch(
            "custom_components.meteoswiss.config_flow."
            "MeteoSwissForecastCatalogueClient.async_get_catalogue",
            return_value=catalogue,
        ),
        patch.object(MeteoSwissConfigFlow, "_validate_forecast", return_value=False),
    ):
        result = await select_point(hass, await reconfigure(hass, entry))
        result = await configure(hass, result, {})
    assert result["errors"] == {"base": "cannot_connect"}
    assert issue_for(hass, entry) is not None and entry.data == original
    hass.config_entries.flow.async_abort(result["flow_id"])


@pytest.mark.parametrize(
    "failed_source",
    [
        "OpenMeteoDataUpdateCoordinator",
        "MeteoSwissForecastCoordinator",
        "MeteoSwissAlertsCoordinator",
        "OpenMeteoPollenCoordinator",
    ],
)
async def test_provider_outages_do_not_raise_configuration_repairs(
    hass, sources, catalogue, failed_source
):
    entry = entry_for(hass, invalid=False)
    point = next(p for p in catalogue.points if p.point_id == "711")
    hass.config_entries.async_update_entry(
        entry,
        data={
            **entry.data,
            CONF_FORECAST_LOCATION: encode_forecast_location(
                ForecastLocation(point, catalogue.sha256, catalogue.retrieved_at)
            ),
        },
    )
    sources[failed_source].side_effect = UpdateFailed("Temporary provider outage")
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert issue_for(hass, entry) is None


async def test_disabling_clears_issue_and_reenabling_checks_saved_data(hass, sources):
    entry = entry_for(hass)
    await start(hass, entry)
    await hass.config_entries.async_set_disabled_by(
        entry.entry_id, ConfigEntryDisabler.USER
    )
    await hass.async_block_till_done()
    assert issue_for(hass, entry) is None
    await hass.config_entries.async_set_disabled_by(entry.entry_id, None)
    await hass.async_block_till_done()
    assert issue_for(hass, entry) is not None
    assert entry.data[CONF_FORECAST_LOCATION] == INVALID


async def test_removing_entry_after_required_source_failure_clears_issue(hass, sources):
    entry = entry_for(hass)
    sources["OpenMeteoDataUpdateCoordinator"].side_effect = UpdateFailed("Offline")
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert issue_for(hass, entry) is not None
    await hass.config_entries.async_remove(entry.entry_id)
    assert issue_for(hass, entry) is None


@pytest.mark.parametrize(
    "language,word",
    [("en", "Configure"), ("de", "Konfigurieren"),
     ("fr", "Configurer"), ("it", "Configura")],
)
async def test_repair_text_is_loaded_by_ha_in_each_language(
    hass, sources, language, word
):
    entry = entry_for(hass)
    issue = await start(hass, entry)
    texts = await async_get_translations(hass, language, "issues", {DOMAIN})
    prefix = "component.meteoswiss.issues.invalid_forecast_location."
    title = texts[prefix + "title"].format(**issue.translation_placeholders)
    description = texts[prefix + "description"].format(**issue.translation_placeholders)
    assert entry.title in title and entry.title in description
    assert word in description
    assert "(/config/integrations/integration/meteoswiss)" in description
    assert "do-not-publish-this-payload" not in title + description

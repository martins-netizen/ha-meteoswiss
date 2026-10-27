"""Native Configure/Reconfigure routes share one complete settings transaction."""

from contextlib import ExitStack
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.config_entries import SOURCE_RECONFIGURE
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.config_flow import (
    MeteoSwissConfigFlow,
    MeteoSwissOptionsFlow,
)
from custom_components.meteoswiss.const import CONF_FORECAST_LOCATION, DOMAIN
from custom_components.meteoswiss.forecast_location_config import (
    decode_forecast_location,
    encode_forecast_location,
)
from custom_components.meteoswiss.forecast_locations import (
    ForecastLocation,
    parse_forecast_catalogue,
)

STATIONS = [
    {"id": "klo", "name": "Kloten", "label": "Kloten (KLO)", "lat": 47.48, "lon": 8.53},
    {"id": "sma", "name": "Fluntern", "label": "Fluntern (SMA)", "lat": 47.38, "lon": 8.57},
]


class SettingsRoute:
    """Drive the real HA manager, retaining each route's completion contract."""

    def __init__(self, hass, kind):
        self.hass = hass
        self.kind = kind

    @property
    def manager(self):
        if self.kind == "configure":
            return self.hass.config_entries.options
        return self.hass.config_entries.flow

    async def start(self, entry):
        if self.kind == "configure":
            return await self.manager.async_init(entry.entry_id)
        return await self.manager.async_init(
            DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
        )

    async def submit(self, form, values):
        return await self.manager.async_configure(
            form["flow_id"], form["data_schema"](values)
        )

    def assert_success(self, result):
        if self.kind == "configure":
            assert result["type"] == "create_entry"
        else:
            assert result["type"] == "abort"
            assert result["reason"] == "reconfigure_successful"


@pytest.fixture(params=("configure", "reconfigure"))
def route(hass, request):
    return SettingsRoute(hass, request.param)


@pytest.fixture
def catalogue():
    return parse_forecast_catalogue(
        (Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv")
        .read_text()
        .encode("latin-1"),
        datetime(2026, 10, 23, tzinfo=UTC),
    )


@pytest.fixture(autouse=True)
def source_boundaries(catalogue, enable_custom_integrations):
    """Only the external source work is mocked, not HA forms or entry writes."""
    source = AsyncMock(return_value=True)
    forecast = AsyncMock(return_value=True)
    with ExitStack() as stack:
        stack.enter_context(patch("custom_components.meteoswiss.async_setup_entry", return_value=True))
        for cls in (MeteoSwissConfigFlow, MeteoSwissOptionsFlow):
            stack.enter_context(patch.object(cls, "_load_stations", return_value=STATIONS))
            stack.enter_context(patch.object(cls, "_validate_source", source))
            stack.enter_context(patch.object(cls, "_validate_forecast", forecast))
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.config_flow."
                "MeteoSwissForecastCatalogueClient.async_get_catalogue",
                return_value=catalogue,
            )
        )
        yield source, forecast


@pytest.fixture(params=("meteoswiss", "openmeteo"))
def entry(hass, catalogue, request):
    source = request.param
    selected = next(point for point in catalogue.points if point.point_id == "711")
    saved = {
        "data_source": source,
        "latitude": 47.48,
        "longitude": 8.53,
        "postal_code": "8302",
        "foreign": {"retained": True},
        CONF_FORECAST_LOCATION: encode_forecast_location(
            ForecastLocation(selected, catalogue.sha256, catalogue.retrieved_at)
        ),
    }
    if source == "meteoswiss":
        saved.update(station_id="klo", station_name="Kloten")
        identity = "meteoswiss:klo:8302"
    else:
        saved["station_name"] = "Open-Meteo"
        identity = "openmeteo:47.48:8.53:8302"
    item = MockConfigEntry(
        domain=DOMAIN, data=saved,
        options={"pollen_station": "PZH", "update_interval": 900, "foreign_option": True},
        unique_id=identity, title="My weather", version=1, minor_version=2,
    )
    item.add_to_hass(hass)
    return item


def snapshot(entry):
    return deepcopy((dict(entry.data), dict(entry.options), entry.unique_id, entry.title))


def changed_observation(entry):
    if entry.data["data_source"] == "meteoswiss":
        return {"station_id": "sma"}
    return {"latitude": 47.0, "longitude": 9.0}


async def choose_forecast(route, form):
    form = await route.submit(form, {"query": "8302"})
    return await route.submit(form, {"point": "2:830200"})


async def test_all_locations_apply_together_without_replacing_entities(hass, route, entry):
    before = snapshot(entry)
    entity = er.async_get(hass).async_get_or_create(
        "sensor", DOMAIN, "retained-measurement", config_entry=entry,
        suggested_object_id="retained_measurement",
    )
    form = await route.start(entry)
    fields = form["data_schema"]({})
    assert {"pollen_station", "postal_code", "forecast_action"} <= fields.keys()
    assert ("station_id" in fields) == (entry.data["data_source"] == "meteoswiss")
    form = await route.submit(
        form, {**changed_observation(entry), "pollen_station": "PBE",
               "postal_code": "8000", "forecast_action": "search"},
    )
    assert snapshot(entry) == before
    form = await choose_forecast(route, form)
    assert form["description_placeholders"]["pollen_station"] == "Bern (PBE)"
    assert form["description_placeholders"]["postal_code"] == "8000"
    assert snapshot(entry) == before
    route.assert_success(await route.submit(form, {}))
    assert entry.data["postal_code"] == "8000"
    assert entry.options == {**before[1], "pollen_station": "PBE"}
    selected = decode_forecast_location(entry.data[CONF_FORECAST_LOCATION])
    assert selected.point.point_id == "830200"
    assert entry.data["foreign"] == {"retained": True}
    assert entry.title == "My weather"
    assert er.async_get(hass).async_get(entity.entity_id).unique_id == "retained-measurement"
    for key, value in changed_observation(entry).items():
        assert entry.data[key] == value


@pytest.mark.parametrize("stage", ("settings", "search", "select", "confirm"))
async def test_cancellation_at_every_stage_discards_all_pending_changes(route, entry, stage):
    before = snapshot(entry)
    form = await route.start(entry)
    if stage != "settings":
        form = await route.submit(
            form, {**changed_observation(entry), "pollen_station": "PBE",
                   "postal_code": "8000", "forecast_action": "search"},
        )
        if stage in {"select", "confirm"}:
            form = await route.submit(form, {"query": "8302"})
        if stage == "confirm":
            form = await route.submit(form, {"point": "2:830200"})
    route.manager.async_abort(form["flow_id"])
    assert snapshot(entry) == before


async def test_source_and_forecast_failures_retry_without_partial_writes(
    route, entry, source_boundaries
):
    source, forecast = source_boundaries
    before = snapshot(entry)
    source.return_value = False
    form = await route.start(entry)
    form = await route.submit(
        form, {**changed_observation(entry), "pollen_station": "PBE",
               "postal_code": "8000", "forecast_action": "search"},
    )
    assert form["errors"] == {"base": "cannot_connect"}
    assert snapshot(entry) == before
    source.return_value = True
    form = await route.submit(form, {})
    form = await choose_forecast(route, form)
    forecast.return_value = False
    form = await route.submit(form, {})
    assert form["errors"] == {"base": "cannot_connect"}
    assert snapshot(entry) == before
    forecast.return_value = True
    route.assert_success(await route.submit(form, {}))
    assert entry.options["pollen_station"] == "PBE"


@pytest.mark.parametrize("action", ("search", "base"))
async def test_source_retry_retains_the_selected_forecast_action(
    route, entry, source_boundaries, action
):
    source, _forecast = source_boundaries
    before = snapshot(entry)
    source.return_value = False
    form = await route.start(entry)
    form = await route.submit(
        form, {**changed_observation(entry), "forecast_action": action}
    )
    assert form["errors"] == {"base": "cannot_connect"}
    assert form["data_schema"]({})["forecast_action"] == action
    source.return_value = True
    form = await route.submit(form, {})
    expected = (
        "forecast_search" if action == "search"
        else "forecast_confirm" if route.kind == "configure" else "settings_confirm"
    )
    assert form["step_id"] == expected
    assert snapshot(entry) == before
    route.manager.async_abort(form["flow_id"])


@pytest.mark.parametrize("kind", ("data", "options"))
async def test_concurrent_external_settings_win_without_partial_commit(hass, route, entry, kind):
    form = await route.start(entry)
    form = await route.submit(form, {"pollen_station": "PBE", "forecast_action": "base"})
    changed = {**getattr(entry, kind), "external_change": True}
    hass.config_entries.async_update_entry(entry, **{kind: changed})
    before = snapshot(entry)
    result = await route.submit(form, {})
    assert result["type"] == "abort" and result["reason"] == "configuration_changed"
    assert snapshot(entry) == before


async def test_first_completed_route_prevents_the_other_route_overwriting_it(hass, route, entry):
    other = SettingsRoute(hass, "configure" if route.kind == "reconfigure" else "reconfigure")
    first, second = await route.start(entry), await other.start(entry)
    first = await route.submit(first, {"pollen_station": "PBE", "forecast_action": "base"})
    second = await other.submit(second, {"pollen_station": "PLU", "forecast_action": "base"})
    route.assert_success(await route.submit(first, {}))
    before = snapshot(entry)
    result = await other.submit(second, {})
    assert result["reason"] == "configuration_changed"
    assert snapshot(entry) == before and entry.options["pollen_station"] == "PBE"


async def test_duplicate_appearing_before_commit_is_rejected(hass, route, entry):
    original = snapshot(entry)
    form = await route.start(entry)
    form = await route.submit(form, {"postal_code": "8000", "forecast_action": "base"})
    duplicate = MockConfigEntry(domain=DOMAIN, data={**entry.data, "postal_code": "8000"})
    duplicate.add_to_hass(hass)
    result = await route.submit(form, {})
    assert result["reason"] == "already_configured"
    assert snapshot(entry) == original


async def test_keeping_every_setting_retains_identity_and_forecast(route, entry):
    before = snapshot(entry)
    form = await route.start(entry)
    route.assert_success(await route.submit(form, {}))
    assert snapshot(entry) == before


@pytest.mark.parametrize("language", ("en", "de", "fr", "it"))
async def test_full_fields_confirmation_and_concurrency_message_are_translated(
    hass, route, entry, language
):
    hass.config.language = language
    category = "options" if route.kind == "configure" else "config"
    form = await route.start(entry)
    texts = await async_get_translations(hass, language, category, {DOMAIN})
    prefix = f"component.{DOMAIN}.{category}"
    for field in form["data_schema"]({}):
        assert texts[f"{prefix}.step.{form['step_id']}.data.{field}"]
        assert texts[f"{prefix}.step.{form['step_id']}.data_description.{field}"]
    form = await route.submit(form, {"forecast_action": "base"})
    assert texts[f"{prefix}.step.{form['step_id']}.description"]
    fields = {"station", "pollen_station", "location", "postal_code"}
    assert fields <= form["description_placeholders"].keys()
    assert texts[f"{prefix}.abort.configuration_changed"]

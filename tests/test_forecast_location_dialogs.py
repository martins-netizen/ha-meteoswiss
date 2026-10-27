"""Actual HA flow transitions, explicit point consent and compatible reconfiguration."""

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import voluptuous as vol
from homeassistant.config_entries import SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.data_entry_flow import UnknownFlow
from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss import async_setup_entry as actual_setup_entry
from custom_components.meteoswiss.config_flow import MeteoSwissConfigFlow
from custom_components.meteoswiss.const import CONF_FORECAST_LOCATION, DOMAIN
from custom_components.meteoswiss.forecast import IconForecastError
from custom_components.meteoswiss.forecast_location_client import (
    ForecastCatalogueUnavailable,
)
from custom_components.meteoswiss.forecast_location_config import (
    decode_forecast_location,
    encode_forecast_location,
)
from custom_components.meteoswiss.forecast_locations import (
    FORECAST_CATALOGUE_URL,
    ForecastCatalogue,
    ForecastPointType,
    parse_forecast_catalogue,
)

NOW = datetime(2026, 10, 23, 19, 20, tzinfo=UTC)
BASE = {
    "data_source": "openmeteo",
    "latitude": 47.45,
    "longitude": 8.56,
    "postal_code": "8302",
    "station_name": "Home",
}


@pytest.fixture
def catalogue():
    raw = (
        (Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv")
        .read_text()
        .encode("latin-1")
    )
    return parse_forecast_catalogue(raw, NOW)


@pytest.fixture(autouse=True)
def setup_mock():
    with patch("custom_components.meteoswiss.async_setup_entry", return_value=True):
        yield


async def configure(hass, result, data):
    values = result["data_schema"](data) if "data_schema" in result else data
    return await hass.config_entries.flow.async_configure(result["flow_id"], values)


async def new_flow(hass, source="openmeteo"):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await configure(
        hass, result, {"data_source": source, "pollen_station": "PZH"}
    )
    data = (
        {"station_id": "klo", "postal_code": "8302"}
        if source == "meteoswiss"
        else {k: BASE[k] for k in ("postal_code", "latitude", "longitude")}
    )
    return await configure(hass, result, data)


async def reconfigure(hass, data):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        options={"pollen_station": "PZH", "update_interval": 900},
        unique_id="retained-id",
        title="Retained name",
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    return entry, result


@pytest.mark.parametrize(
    "language,category",
    [
        ("en", "Postal code"),
        ("de", "Postleitzahl"),
        ("fr", "Code postal"),
        ("it", "Codice postale"),
    ],
)
@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize(
    "query,identity",
    [
        ("8302", "2:830200"),
        ("Saentis", "3:711"),
        ("Gotthardpass", "3:594"),
        ("Albert Heim Hutte", "3:454"),
    ],
)
async def test_setup_requires_selection_then_confirmation_in_each_language(
    hass,
    enable_custom_integrations,
    catalogue,
    source,
    language,
    category,
    query,
    identity,
):
    hass.config.language = language
    stations = [
        {
            "id": "klo",
            "name": "Kloten",
            "lat": 47.45,
            "lon": 8.56,
            "label": "Kloten (KLO)",
        }
    ]
    with (
        patch.object(MeteoSwissConfigFlow, "_load_stations", return_value=stations),
        patch.object(MeteoSwissConfigFlow, "_validate_source", return_value=True),
        patch(
            "custom_components.meteoswiss.config_flow.MeteoSwissForecastCatalogueClient.async_get_catalogue",
            return_value=catalogue,
        ),
        patch.object(MeteoSwissConfigFlow, "_validate_forecast", return_value=True),
    ):
        result = await new_flow(hass, source)
        assert result["step_id"] == "forecast_location"
        assert not hass.config_entries.async_entries(DOMAIN)
        result = await configure(hass, result, {"action": "search"})
        result = await configure(hass, result, {"query": query})
        assert result["step_id"] == "forecast_select"
        with pytest.raises(vol.Invalid):
            result["data_schema"]({})
        labels = list(result["data_schema"].schema.values())[0].config["options"]
        if query == "8302":
            assert (
                category in labels[0]["label"] and "8302 Kloten" in labels[0]["label"]
            )
        result = await configure(hass, result, {"point": identity})
        assert result["step_id"] == "forecast_confirm"
        assert result["description_placeholders"]["postal_code"] == "8302"
        assert not hass.config_entries.async_entries(DOMAIN)
        result = await configure(hass, result, {})
    assert result["type"] == "create_entry"
    entry = result["result"]
    saved = decode_forecast_location(entry.data[CONF_FORECAST_LOCATION])
    assert f"{saved.point.point_type}:{saved.point.point_id}" == identity
    assert (
        entry.data["postal_code"] == "8302" and entry.options["pollen_station"] == "PZH"
    )
    assert entry.data["latitude"] == 47.45 and entry.data["longitude"] == 8.56
    await hass.async_block_till_done()


@pytest.mark.parametrize("state", ["legacy", "valid", "invalid"])
async def test_reconfigure_keep_cancel_and_reset_are_explicit(
    hass, enable_custom_integrations, catalogue, state
):
    data = dict(BASE)
    if state != "legacy":
        data[CONF_FORECAST_LOCATION] = (
            encode_forecast_location(
                catalogue.select(ForecastPointType.POINT_OF_INTEREST, "711")
            )
            if state == "valid"
            else {"broken": "private"}
        )
    entry, result = await reconfigure(hass, data)
    assert entry.data == data
    # HA flow cancellation leaves data/options/identity untouched.
    hass.config_entries.flow.async_abort(result["flow_id"])
    assert entry.data == data and entry.unique_id == "retained-id"
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
    )
    if state == "invalid":
        # The complete settings form excludes keeping an invalid forecast.
        with pytest.raises(vol.Invalid):
            await configure(hass, result, {"forecast_action": "keep"})
    else:
        result = await configure(hass, result, {"forecast_action": "keep"})
        assert result["type"] == "abort" and entry.data == data
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
        )
    if state != "legacy":
        result = await configure(hass, result, {"forecast_action": "base"})
        assert result["step_id"] == "settings_confirm" and entry.data == data
        result = await configure(hass, result, {})
        assert (
            result["type"] == "abort" and result["reason"] == "reconfigure_successful"
        )
        assert CONF_FORECAST_LOCATION not in entry.data
        assert entry.data == BASE
    assert entry.unique_id == "retained-id" and entry.title == "Retained name"
    assert entry.options == {"pollen_station": "PZH", "update_interval": 900}
    await hass.async_block_till_done()


@pytest.mark.parametrize("concurrent", [False, True])
async def test_failed_confirmation_retries_and_never_overwrites_concurrent_settings(
    hass, enable_custom_integrations, catalogue, concurrent
):
    entry, result = await reconfigure(hass, BASE)
    with (
        patch(
            "custom_components.meteoswiss.config_flow.MeteoSwissForecastCatalogueClient.async_get_catalogue",
            return_value=catalogue,
        ) as load,
        patch.object(
            MeteoSwissConfigFlow, "_validate_forecast", side_effect=[False, True]
        ),
    ):
        result = await configure(hass, result, {"forecast_action": "search"})
        result = await configure(hass, result, {"query": "Säntis"})
        result = await configure(hass, result, {"point": "3:711"})
        result = await configure(hass, result, {})
        assert result["errors"] == {"base": "cannot_connect"} and entry.data == BASE
        result = await configure(hass, result, {"search_again": True})
        result = await configure(hass, result, {"query": "8302"})
        result = await configure(hass, result, {"point": "2:830200"})
        if concurrent:
            hass.config_entries.async_update_entry(
                entry, data={**entry.data, "unrelated": "retain"}
            )
        result = await configure(hass, result, {})
        assert load.await_count == 2
    assert result["type"] == "abort"
    assert entry.data["postal_code"] == "8302"
    if concurrent:
        assert result["reason"] == "configuration_changed"
        assert entry.data["unrelated"] == "retain"
        assert CONF_FORECAST_LOCATION not in entry.data
    else:
        assert result["reason"] == "reconfigure_successful"
        assert entry.data[CONF_FORECAST_LOCATION]["point_id"] == "830200"
    assert entry.options["update_interval"] == 900
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    "query,error",
    [
        (None, "invalid_forecast_query"),
        ([], "invalid_forecast_query"),
        (" ", "invalid_forecast_query"),
        ("x" * 129, "invalid_forecast_query"),
        ("830", "forecast_no_matches"),
        ("nonexistent village", "forecast_no_matches"),
    ],
)
async def test_bad_or_empty_queries_are_correctable(
    hass, enable_custom_integrations, catalogue, query, error
):
    flow = MeteoSwissConfigFlow()
    flow.hass = hass
    with patch(
        "custom_components.meteoswiss.config_flow.MeteoSwissForecastCatalogueClient.async_get_catalogue",
        return_value=catalogue,
    ):
        result = await flow.async_step_forecast_search({"query": query})
    assert result["errors"] == {"base": error}
    assert flow._candidates == {} and flow._selected_location is None


async def test_catalogue_failure_ambiguity_and_injected_selection(
    hass, enable_custom_integrations, catalogue
):
    flow = MeteoSwissConfigFlow()
    flow.hass = hass
    with patch(
        "custom_components.meteoswiss.config_flow.MeteoSwissForecastCatalogueClient.async_get_catalogue",
        side_effect=[ForecastCatalogueUnavailable(), catalogue],
    ):
        result = await flow.async_step_forecast_search({"query": "Säntis"})
        assert result["errors"] == {"base": "forecast_catalogue_unavailable"}
        result = await flow.async_step_forecast_search({"query": "Säntis"})
        assert set(flow._candidates) == {"1:35", "3:711"}
        for key in ["3:35", "3:unknown", None, []]:
            result = await flow.async_step_forecast_select({"point": key})
            assert result["errors"] == {"base": "invalid_forecast_selection"}
    flow._candidates = {}
    assert (await flow.async_step_forecast_select())["step_id"] == "forecast_search"
    assert (await flow.async_step_forecast_location({"action": "injected"}))["errors"]
    many = ForecastCatalogue(
        tuple(
            replace(catalogue.points[0], point_id=str(i), name=f"Test area {i}")
            for i in range(21)
        ),
        catalogue.sha256,
        NOW,
        0,
    )
    with patch(
        "custom_components.meteoswiss.config_flow.MeteoSwissForecastCatalogueClient.async_get_catalogue",
        return_value=many,
    ):
        result = await flow.async_step_forecast_search({"query": "Test area"})
    assert result["errors"] == {"base": "forecast_too_many_matches"}
    assert flow._candidates == {}


@pytest.mark.parametrize(
    "error", [None, IconForecastError(), TimeoutError(), asyncio.CancelledError()]
)
async def test_forecast_validation_real_client_error_boundary(hass, catalogue, error):
    flow = MeteoSwissConfigFlow()
    flow.hass = hass
    flow._selected_location = catalogue.select(
        ForecastPointType.POINT_OF_INTEREST, "711"
    )
    with patch(
        "custom_components.meteoswiss.config_flow.IconForecastClient.async_get_data",
        side_effect=error,
        return_value=[{}],
    ) as source:
        if isinstance(error, asyncio.CancelledError):
            with pytest.raises(asyncio.CancelledError):
                await flow._validate_forecast()
        else:
            assert await flow._validate_forecast() is (error is None)
        source.assert_awaited_once()


async def test_one_real_catalogue_download_is_reused_and_search_stays_local(
    hass, enable_custom_integrations, aioclient_mock, catalogue
):
    raw = (
        (Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv")
        .read_text()
        .encode("latin-1")
    )
    aioclient_mock.get(FORECAST_CATALOGUE_URL, content=raw)
    flow = MeteoSwissConfigFlow()
    flow.hass = hass
    await flow.async_step_forecast_search({"query": "Saentis"})
    client = flow._catalogue_client
    await flow.async_step_forecast_search({"query": "8302"})
    assert flow._catalogue_client is client and len(aioclient_mock.mock_calls) == 1
    assert aioclient_mock.mock_calls[0][1].query_string == ""
    point = replace(catalogue.points[0], altitude_masl=None)
    label = flow._point_label(
        replace(catalogue.select(ForecastPointType.STATION, "35"), point=point),
        await flow._forecast_labels(),
    )
    assert "Height unavailable" in label


@pytest.mark.parametrize("language", ["de", "en", "fr", "it"])
async def test_ha_serves_all_new_dialog_help_and_preserves_place_names(
    hass, enable_custom_integrations, catalogue, language
):
    config = await async_get_translations(hass, language, "config", {DOMAIN})
    fields = {
        "forecast_location": "action",
        "forecast_search": "query",
        "forecast_select": "point",
        "forecast_confirm": "search_again",
    }
    for step, field in fields.items():
        assert config[f"component.{DOMAIN}.config.step.{step}.data_description.{field}"]
    flow = MeteoSwissConfigFlow()
    flow.hass = hass
    flow.context = {"language": language}
    labels = await flow._forecast_labels()
    assert "Säntis" in flow._point_label(
        catalogue.select(ForecastPointType.POINT_OF_INTEREST, "711"), labels
    )


async def test_confirmed_change_reloads_a_real_loaded_entry_once_and_keeps_ids(
    hass, enable_custom_integrations, catalogue, freezer
):
    from contextlib import ExitStack

    from homeassistant.helpers import entity_registry as er

    from custom_components.meteoswiss.cache import clear_all_caches

    freezer.move_to(NOW)
    clear_all_caches()
    rows = [
        {
            "datetime": NOW.replace(minute=0).isoformat(),
            "fetched_at": NOW.isoformat(),
            "temperature": -8,
            "condition": "snowy",
        }
    ]
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=BASE,
        options={"pollen_station": "PZH", "update_interval": 900},
        unique_id="retained-id",
        title="Home",
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.async_setup_entry", new=actual_setup_entry
            )
        )
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
                return_value={},
            )
        )
        for name, data in {
            "OpenMeteoDataUpdateCoordinator": {
                "temperature": 12,
                "last_update": NOW.isoformat(),
            },
            "MeteoSwissForecastCoordinator": rows,
            "MeteoSwissAlertsCoordinator": [],
            "OpenMeteoPollenCoordinator": {},
            "MeteoSwissPollenCoordinator": {},
        }.items():
            stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.coordinator.{name}._async_update_data",
                    return_value=data,
                )
            )
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.config_flow.MeteoSwissForecastCatalogueClient.async_get_catalogue",
                return_value=catalogue,
            )
        )
        stack.enter_context(
            patch.object(MeteoSwissConfigFlow, "_validate_forecast", return_value=True)
        )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        before = {
            row.entity_id: row.unique_id
            for row in er.async_entries_for_config_entry(registry, entry.entry_id)
        }
        runtime_before = entry.runtime_data
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
        )
        result = await configure(hass, result, {"forecast_action": "search"})
        result = await configure(hass, result, {"query": "Saentis"})
        result = await configure(hass, result, {"point": "3:711"})
        assert entry.runtime_data is runtime_before and entry.data == BASE
        with patch.object(
            hass.config_entries, "async_reload", wraps=hass.config_entries.async_reload
        ) as reload:
            result = await configure(hass, result, {})
            await hass.async_block_till_done()
            assert reload.await_count == 1
        assert result["type"] == "abort"
        runtime = entry.runtime_data
        assert runtime is not runtime_before
        assert runtime.forecast_target.location.point.name == "Säntis"
        assert runtime.forecast_coordinator._elevation == 2502
        assert (
            runtime.pollen_coordinator.latitude,
            runtime.pollen_coordinator.longitude,
        ) == (47.45, 8.56)
        assert runtime.alerts_coordinator._alerts_api.postal_code == "8302"
        assert {
            row.entity_id: row.unique_id
            for row in er.async_entries_for_config_entry(registry, entry.entry_id)
        } == before
        assert (
            entry.unique_id == "retained-id" and entry.options["update_interval"] == 900
        )
        assert not runtime_before.forecast_coordinator._listeners
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert (
            not runtime.forecast_coordinator._listeners and not runtime.session.closed
        )
    clear_all_caches()


def test_documented_murten_morat_limit_uses_an_actual_catalogue_row():
    from custom_components.meteoswiss.forecast_locations import (
        search_forecast_locations,
    )

    raw = (
        (Path(__file__).parent / "fixtures/forecast_point_murten_2026-10-23.csv")
        .read_text()
        .encode("latin-1")
    )
    snapshot = parse_forecast_catalogue(raw, NOW)
    by_name = search_forecast_locations(snapshot, "Murten")
    by_postcode = search_forecast_locations(snapshot, "3280")
    assert by_name.points == by_postcode.points
    assert by_name.points[0].identity == (ForecastPointType.POSTAL_CODE, "328000")
    assert not search_forecast_locations(snapshot, "Morat").points
    assert not search_forecast_locations(snapshot, "Môrat").points


async def test_second_inflight_setup_cannot_create_a_duplicate_after_location_dialog(
    hass, enable_custom_integrations
):
    with patch.object(MeteoSwissConfigFlow, "_validate_source", return_value=True):
        first = await new_flow(hass)
        second = await new_flow(hass)
        assert first["flow_id"] != second["flow_id"]
        assert (await configure(hass, first, {"action": "keep"}))[
            "type"
        ] == "create_entry"
        # HA closes another in-flight flow with the same unique ID on commit.
        with pytest.raises(UnknownFlow):
            await configure(hass, second, {"action": "keep"})
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    await hass.async_block_till_done()

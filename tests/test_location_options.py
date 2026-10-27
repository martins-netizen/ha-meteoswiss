"""One settings flow changes each location independently or all three atomically."""

from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.data_entry_flow import InvalidData
from homeassistant.config_entries import SOURCE_RECONFIGURE
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss import async_setup_entry as actual_setup_entry
from custom_components.meteoswiss.config_flow import MeteoSwissConfigFlow, MeteoSwissOptionsFlow
from custom_components.meteoswiss.const import CONF_FORECAST_LOCATION, DOMAIN
from custom_components.meteoswiss.forecast_location_config import (
    decode_forecast_location,
    encode_forecast_location,
)
from custom_components.meteoswiss.forecast_locations import (
    ForecastPointType,
    parse_forecast_catalogue,
)

STATIONS = [
    {
        "id": "klo",
        "name": "Zürich / Kloten",
        "label": "Zürich / Kloten (KLO)",
        "lat": 47.48,
        "lon": 8.53,
    },
    {
        "id": "sma",
        "name": "Zürich / Fluntern",
        "label": "Zürich / Fluntern (SMA)",
        "lat": 47.38,
        "lon": 8.57,
    },
]


@pytest.fixture(autouse=True)
def flows():
    with (
        patch("custom_components.meteoswiss.async_setup_entry", return_value=True),
        patch.object(
            MeteoSwissOptionsFlow, "_load_stations", return_value=STATIONS
        ) as stations,
        patch.object(
            MeteoSwissOptionsFlow, "_validate_source", return_value=True
        ) as source,
        patch.object(
            MeteoSwissOptionsFlow, "_validate_forecast", return_value=True
        ) as forecast,
    ):
        yield stations, source, forecast


@pytest.fixture
def catalogue():
    return parse_forecast_catalogue(
        (Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv")
        .read_text()
        .encode("latin-1"),
        datetime(2026, 10, 23, tzinfo=UTC),
    )


def entry_for(hass, catalogue, *, source="meteoswiss", title=None, unique_id="default"):
    data = {
        "data_source": source,
        "station_id": "klo",
        "station_name": "Zürich / Kloten",
        "latitude": 47.48,
        "longitude": 8.53,
        "postal_code": "8302",
        "foreign": {"retained": True},
        CONF_FORECAST_LOCATION: encode_forecast_location(
            catalogue.select(ForecastPointType.POINT_OF_INTEREST, "711")
        ),
    }
    if source == "openmeteo":
        data["station_name"] = "Open-Meteo"
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        options={
            "pollen_station": "PZH",
            "update_interval": 900,
            "foreign_option": True,
        },
        unique_id=(
            "meteoswiss:klo:8302"
            if source == "meteoswiss"
            else "openmeteo:47.48:8.53:8302"
        )
        if unique_id == "default"
        else unique_id,
        title=title
        or (
            "MeteoSwiss Zürich / Kloten (KLO)"
            if source == "meteoswiss"
            else "Open-Meteo (47.48, 8.53)"
        ),
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    return entry


async def submit(hass, form, values):
    values = form["data_schema"](values)
    return await hass.config_entries.options.async_configure(form["flow_id"], values)


async def search_selected(hass, form, catalogue):
    with patch(
        "custom_components.meteoswiss.config_flow.MeteoSwissForecastCatalogueClient.async_get_catalogue",
        return_value=catalogue,
    ):
        form = await submit(hass, form, {"query": "8302"})
    return await submit(hass, form, {"point": "2:830200"})


async def test_all_three_locations_are_on_the_same_form_and_apply_together(
    hass, enable_custom_integrations, catalogue, flows
):
    entry = entry_for(hass, catalogue)
    original = (dict(entry.data), dict(entry.options), entry.entry_id)
    registry = er.async_get(hass)
    entity = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        "kept-temperature",
        config_entry=entry,
        suggested_object_id="kept_temperature",
    )
    form = await hass.config_entries.options.async_init(entry.entry_id)
    fields = form["data_schema"]({})
    assert set(fields) == {
        "station_id",
        "pollen_station",
        "postal_code",
        "forecast_action",
    }
    form = await submit(
        hass,
        form,
        {
            "station_id": "sma",
            "pollen_station": "PBE",
            "postal_code": "8000",
            "forecast_action": "search",
        },
    )
    assert form["step_id"] == "forecast_search"
    assert (entry.data, entry.options, entry.entry_id) == original
    form = await search_selected(hass, form, catalogue)
    assert form["description_placeholders"]["station"] == "Zürich / Fluntern"
    assert form["description_placeholders"]["pollen_station"] == "Bern (PBE)"
    assert form["description_placeholders"]["postal_code"] == "8000"
    assert (entry.data, entry.options, entry.entry_id) == original
    result = await submit(hass, form, {})
    assert result["type"] == "create_entry"
    assert entry.entry_id == original[2]
    assert entry.data["station_id"] == "sma"
    assert entry.data["postal_code"] == "8000"
    assert entry.data["latitude"] == 47.38
    assert (
        decode_forecast_location(entry.data[CONF_FORECAST_LOCATION]).point.postal_code
        == "8302"
    )
    assert entry.options == {**original[1], "pollen_station": "PBE"}
    assert entry.data["foreign"] == {"retained": True}
    assert entry.unique_id == "meteoswiss:sma:8000"
    assert entry.title == "MeteoSwiss Zürich / Fluntern (SMA)"
    assert registry.async_get(entity.entity_id).unique_id == "kept-temperature"
    flows[1].assert_awaited_once_with(station_id="sma")


@pytest.mark.parametrize("stage", ["search", "select", "confirm"])
async def test_cancelling_never_saves_any_of_the_three_pending_locations(
    hass, enable_custom_integrations, catalogue, stage
):
    entry = entry_for(hass, catalogue)
    before = (
        deepcopy(dict(entry.data)),
        dict(entry.options),
        entry.unique_id,
        entry.title,
    )
    form = await hass.config_entries.options.async_init(entry.entry_id)
    form = await submit(
        hass,
        form,
        {"station_id": "sma", "pollen_station": "PBE", "forecast_action": "search"},
    )
    if stage != "search":
        with patch(
            "custom_components.meteoswiss.config_flow.MeteoSwissForecastCatalogueClient.async_get_catalogue",
            return_value=catalogue,
        ):
            form = await submit(hass, form, {"query": "8302"})
        if stage == "confirm":
            form = await submit(hass, form, {"point": "2:830200"})
    hass.config_entries.options.async_abort(form["flow_id"])
    assert (entry.data, entry.options, entry.unique_id, entry.title) == before


@pytest.mark.parametrize("unique_id", [None, "meteoswiss:klo:8302"])
async def test_station_change_retries_source_and_retains_custom_names_and_forecast(
    hass, enable_custom_integrations, catalogue, flows, unique_id
):
    entry = entry_for(hass, catalogue, title="My weather", unique_id=unique_id)
    before = dict(entry.data)
    flows[1].return_value = False
    form = await hass.config_entries.options.async_init(entry.entry_id)
    form = await submit(hass, form, {"station_id": "sma"})
    assert form["errors"] == {"base": "cannot_connect"}
    assert entry.data == before
    assert form["data_schema"]({})["station_id"] == "sma"
    flows[1].return_value = True
    result = await submit(hass, form, {})
    assert result["type"] == "create_entry"
    assert entry.title == "My weather"
    assert entry.unique_id == ("meteoswiss:sma:8302" if unique_id else None)
    assert entry.data[CONF_FORECAST_LOCATION] == before[CONF_FORECAST_LOCATION]


async def test_pollen_and_warning_changes_work_when_station_catalogue_is_unavailable(
    hass, enable_custom_integrations, catalogue, flows
):
    flows[0].return_value = []
    entry = entry_for(hass, catalogue)
    form = await hass.config_entries.options.async_init(entry.entry_id)
    result = await submit(hass, form, {"pollen_station": "PBE", "postal_code": "8000"})
    assert result["type"] == "create_entry"
    assert entry.data["station_id"] == "klo"
    assert entry.options["pollen_station"] == "PBE"
    flows[1].assert_not_awaited()


async def test_unavailable_catalogue_can_retry_a_changed_station_without_losing_choices(
    hass, enable_custom_integrations, catalogue, flows
):
    flows[0].return_value = []
    entry = entry_for(hass, catalogue)
    form = await hass.config_entries.options.async_init(entry.entry_id)
    form = await submit(hass, form, {"station_id": "sma", "pollen_station": "PBE"})
    assert form["errors"] == {"base": "station_not_found"}
    assert entry.data["station_id"] == "klo"
    flows[0].return_value = STATIONS
    result = await submit(hass, form, {})
    assert result["type"] == "create_entry"
    assert entry.data["station_id"] == "sma"


@pytest.mark.parametrize(
    "updates,error",
    [
        ({"postal_code": "123"}, {"postal_code": "invalid_postal_code"}),
        ({"pollen_station": None}, {"pollen_station": "invalid_pollen_station"}),
        ({"pollen_station": "INVALID"}, {"pollen_station": "invalid_pollen_station"}),
        ({"forecast_action": "invalid"}, {"base": "invalid_forecast_selection"}),
    ],
)
async def test_invalid_settings_keep_existing_values(
    hass, enable_custom_integrations, catalogue, updates, error
):
    entry = entry_for(hass, catalogue)
    before = (dict(entry.data), dict(entry.options))
    form = await hass.config_entries.options.async_init(entry.entry_id)
    # Validate defaults, then model an invalid programmatic submission too.
    payload = {**form["data_schema"]({}), **updates}
    if "postal_code" in updates:
        result = await hass.config_entries.options.async_configure(
            form["flow_id"], payload
        )
    else:
        with pytest.raises(InvalidData):
            await hass.config_entries.options.async_configure(form["flow_id"], payload)
        # Flow methods retain their own guards for direct API callers as well.
        flow = MeteoSwissOptionsFlow()
        flow.hass = hass
        flow.handler = entry.entry_id
        result = await flow.async_step_init(payload)
    assert result["errors"] == error
    assert (entry.data, entry.options) == before


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize("late", [False, True])
async def test_duplicate_locations_never_replace_or_partially_modify_an_entry(
    hass, enable_custom_integrations, catalogue, source, late
):
    entry = entry_for(hass, catalogue, source=source)
    before = (dict(entry.data), dict(entry.options))
    form = await hass.config_entries.options.async_init(entry.entry_id)
    if late:
        form = await submit(hass, form, {"forecast_action": "search"})
        form = await search_selected(hass, form, catalogue)
    duplicate = MockConfigEntry(domain=DOMAIN, data=dict(entry.data))
    duplicate.add_to_hass(hass)
    result = await submit(hass, form, {})
    assert (
        result.get("reason", result.get("errors", {}).get("base"))
        == "already_configured"
    )
    assert (entry.data, entry.options) == before


@pytest.mark.parametrize("kind", ["data", "options"])
async def test_concurrent_changes_are_preserved_instead_of_overwritten(
    hass, enable_custom_integrations, catalogue, kind
):
    entry = entry_for(hass, catalogue)
    form = await hass.config_entries.options.async_init(entry.entry_id)
    form = await submit(
        hass, form, {"forecast_action": "search", "pollen_station": "PBE"}
    )
    form = await search_selected(hass, form, catalogue)
    changed = {**getattr(entry, kind), "external_change": True}
    hass.config_entries.async_update_entry(entry, **{kind: changed})
    result = await submit(hass, form, {})
    assert result["reason"] == "configuration_changed"
    assert getattr(entry, kind) == changed


@pytest.mark.parametrize(
    "latitude,longitude,error",
    [
        (float("nan"), 8, "invalid_location"),
        (91, 8, "invalid_location"),
        (47, -181, "invalid_location"),
        (47, 9, None),
    ],
)
async def test_openmeteo_base_coordinates_are_independent_of_explicit_forecast(
    hass, enable_custom_integrations, catalogue, flows, latitude, longitude, error
):
    entry = entry_for(hass, catalogue, source="openmeteo")
    before = dict(entry.data)
    form = await hass.config_entries.options.async_init(entry.entry_id)
    result = await submit(hass, form, {"latitude": latitude, "longitude": longitude})
    if error:
        assert result["errors"]["base"] == error
        assert entry.data == before
    else:
        assert result["type"] == "create_entry"
        assert entry.data["latitude"] == latitude
        assert entry.data[CONF_FORECAST_LOCATION] == before[CONF_FORECAST_LOCATION]
        assert entry.title == "Open-Meteo (47.00, 9.00)"
        flows[1].assert_awaited_once_with(latitude=latitude, longitude=longitude)


async def test_reset_from_same_dialog_keeps_the_other_locations(
    hass, enable_custom_integrations, catalogue
):
    entry = entry_for(hass, catalogue)
    form = await hass.config_entries.options.async_init(entry.entry_id)
    form = await submit(hass, form, {"forecast_action": "base"})
    assert CONF_FORECAST_LOCATION in entry.data
    result = await submit(hass, form, {})
    assert result["type"] == "create_entry"
    assert CONF_FORECAST_LOCATION not in entry.data
    assert entry.data["station_id"] == "klo"
    assert entry.options["pollen_station"] == "PZH"


async def test_openmeteo_source_failure_is_retryable_without_partial_writes(
    hass, enable_custom_integrations, catalogue, flows
):
    entry = entry_for(hass, catalogue, source="openmeteo")
    original = dict(entry.data)
    flows[1].return_value = False
    form = await hass.config_entries.options.async_init(entry.entry_id)
    form = await submit(hass, form, {"latitude": 47, "longitude": 9})
    assert form["errors"] == {"base": "cannot_connect"}
    assert entry.data == original
    flows[1].return_value = True
    assert (await submit(hass, form, {}))["type"] == "create_entry"
    assert entry.data["latitude"] == 47


async def test_invalid_saved_forecast_can_be_reset_from_unified_settings(
    hass, enable_custom_integrations, catalogue
):
    entry = entry_for(hass, catalogue)
    hass.config_entries.async_update_entry(
        entry, data={**entry.data, CONF_FORECAST_LOCATION: {"broken": True}}
    )
    form = await hass.config_entries.options.async_init(entry.entry_id)
    assert form["data_schema"]({})["forecast_action"] == "search"
    flow = MeteoSwissOptionsFlow()
    flow.hass, flow.handler = hass, entry.entry_id
    rejected = await flow.async_step_init(
        {**form["data_schema"]({}), "forecast_action": "keep"}
    )
    assert rejected["errors"] == {"base": "invalid_forecast_selection"}
    form = await submit(hass, form, {"forecast_action": "base"})
    assert (await submit(hass, form, {}))["type"] == "create_entry"
    assert CONF_FORECAST_LOCATION not in entry.data


@pytest.mark.parametrize("route", ["configure", "reconfigure"])
async def test_station_change_reloads_once_with_new_readings_and_preserved_entity_ids(
    hass, enable_custom_integrations, catalogue, route
):
    from contextlib import ExitStack

    from homeassistant.helpers import device_registry as dr

    entry = entry_for(hass, catalogue)

    async def observations(source):
        return {"temperature": 12 if source.station_id == "klo" else 15}

    with ExitStack() as stack:
        stack.enter_context(
            patch.object(MeteoSwissConfigFlow, "_load_stations", return_value=STATIONS)
        )
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
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.coordinator.MeteoSwissDataUpdateCoordinator._async_update_data",
                new=observations,
            )
        )
        for coordinator, data in {
            "MeteoSwissForecastCoordinator": [],
            "MeteoSwissAlertsCoordinator": [],
            "OpenMeteoPollenCoordinator": {},
            "MeteoSwissPollenCoordinator": {},
        }.items():
            stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.coordinator.{coordinator}._async_update_data",
                    return_value=data,
                )
            )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry, devices = er.async_get(hass), dr.async_get(hass)
        before = {
            entity.unique_id: entity.entity_id
            for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
        }
        weather = registry.async_get_entity_id(
            "weather", DOMAIN, f"{DOMAIN}_{entry.entry_id}_weather"
        )
        assert hass.states.get(weather).attributes["temperature"] == 12
        registry.async_update_entity(weather, name="My measured weather")
        forecast_coordinates = (
            entry.runtime_data.forecast_coordinator._latitude,
            entry.runtime_data.forecast_coordinator._longitude,
        )
        with patch.object(
            hass.config_entries, "async_reload", wraps=hass.config_entries.async_reload
        ) as reload:
            if route == "configure":
                manager = hass.config_entries.options
                form = await manager.async_init(entry.entry_id)
            else:
                manager = hass.config_entries.flow
                form = await manager.async_init(
                    DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
                )
            values = form["data_schema"](
                {"station_id": "sma", "pollen_station": "PBE", "postal_code": "8000"}
            )
            result = await manager.async_configure(form["flow_id"], values)
            assert result["type"] == ("create_entry" if route == "configure" else "abort")
            if route == "reconfigure":
                assert result["reason"] == "reconfigure_successful"
            await hass.async_block_till_done()
            reload.assert_awaited_once_with(entry.entry_id)
        assert hass.states.get(weather).attributes["temperature"] == 15
        assert registry.async_get(weather).name == "My measured weather"
        assert {
            entity.unique_id: entity.entity_id
            for entity in er.async_entries_for_config_entry(registry, entry.entry_id)
        } == before
        assert entry.runtime_data.coordinator.station_id == "sma"
        assert (
            entry.runtime_data.meteoswiss_pollen_coordinator.client.station_id == "pbe"
        )
        assert (
            entry.runtime_data.forecast_coordinator._latitude,
            entry.runtime_data.forecast_coordinator._longitude,
        ) == forecast_coordinates
        observation_device = devices.async_get(registry.async_get(weather).device_id)
        forecast_weather = registry.async_get_entity_id(
            "weather", DOMAIN, f"{DOMAIN}_{entry.entry_id}_forecast_weather"
        )
        forecast_device = devices.async_get(
            registry.async_get(forecast_weather).device_id
        )
        assert "Fluntern" in observation_device.name
        assert "Säntis" in forecast_device.name
        warning_entity = registry.async_get_entity_id(
            "binary_sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_any_alert"
        )
        warning_device = devices.async_get(registry.async_get(warning_entity).device_id)
        assert "8000" in warning_device.name
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()


@pytest.mark.parametrize("language", ["en", "de", "fr", "it"])
async def test_all_settings_and_shared_search_steps_have_translations(
    hass, enable_custom_integrations, language
):
    translations = await async_get_translations(hass, language, "options", {DOMAIN})
    for field in ("station_id", "pollen_station", "forecast_action", "postal_code"):
        assert translations[f"component.{DOMAIN}.options.step.init.data.{field}"]
    for step in ("forecast_search", "forecast_select", "forecast_confirm"):
        assert translations[f"component.{DOMAIN}.options.step.{step}.title"]

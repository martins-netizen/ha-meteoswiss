"""Selected forecast coordinates/height stay independent of other HA source roles."""

from contextlib import ExitStack
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.redact import REDACTED
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.cache import clear_all_caches
from custom_components.meteoswiss.const import CONF_FORECAST_LOCATION, DOMAIN
from custom_components.meteoswiss.coordinator import MeteoSwissForecastCoordinator
from custom_components.meteoswiss.diagnostics import async_get_config_entry_diagnostics
from custom_components.meteoswiss.forecast import (
    OPEN_METEO_BASE_URL,
    IconForecastClient,
)
from custom_components.meteoswiss.forecast_location_config import (
    encode_forecast_location,
)
from custom_components.meteoswiss.forecast_locations import (
    ForecastPointType,
    parse_forecast_catalogue,
)
from custom_components.meteoswiss.sensor import MeteoSwissHeatingDegreeDaysSensor

NOW = datetime(2026, 10, 23, 10, 20, tzinfo=UTC)
HOUR = int(NOW.replace(minute=0).timestamp())


@pytest.fixture(autouse=True)
def isolated_cache_and_clock(freezer):
    clear_all_caches()
    freezer.move_to(NOW)
    yield
    clear_all_caches()


@pytest.fixture
def selected_location():
    raw = (
        Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv"
    ).read_text()
    return parse_forecast_catalogue(raw.encode("latin-1"), NOW).select(
        ForecastPointType.POINT_OF_INTEREST, "711"
    )


def payload():
    return {
        "hourly": {
            "time": [HOUR, HOUR + 3600],
            "temperature_2m": [-10, -9],
            "weather_code": [71, 71],
        },
        "daily": {
            "time": [HOUR - 12 * 3600],
            "temperature_2m_max": [-5],
            "temperature_2m_min": [-12],
            "temperature_2m_mean": [-8],
        },
    }


@pytest.mark.parametrize("height", [2502, 0, -5.2, None])
async def test_source_sends_explicit_height_or_preserves_automatic_dem(
    hass, aioclient_mock, height
):
    aioclient_mock.get(OPEN_METEO_BASE_URL, json=payload())
    client = IconForecastClient(
        47.2, 9.3, async_get_clientsession(hass), elevation=height
    )
    assert (await client.async_get_data())[0]["temperature"] == -10
    query = aioclient_mock.mock_calls[0][1].query
    assert query["models"] == "meteoswiss_icon_seamless"
    assert query["latitude"] == "47.2" and query["longitude"] == "9.3"
    assert query["timeformat"] == "unixtime"
    if height is None:
        assert "elevation" not in query
    else:
        assert query["elevation"] == str(float(height))
    assert not client._session.closed


@pytest.mark.parametrize(
    "height", [True, "private-point", float("nan"), float("inf"), 10**400]
)
def test_invalid_height_is_rejected_before_network_without_raw_input(height):
    with pytest.raises(ValueError, match="^Invalid forecast elevation$"):
        IconForecastClient(47.2, 9.3, elevation=height)


async def test_cache_separates_heights_from_each_other_and_legacy(hass, aioclient_mock):
    aioclient_mock.get(OPEN_METEO_BASE_URL, json=payload())
    session = async_get_clientsession(hass)
    for height in [None, 2502, 0, -5.2, 2502.0, None, 0.0]:
        source = MeteoSwissForecastCoordinator(
            hass, latitude=47.2, longitude=9.3, elevation=height, session=session
        )
        assert (await source._async_update_data())[0]["temperature"] == -10
    assert len(aioclient_mock.mock_calls) == 4
    assert [call[1].query.get("elevation") for call in aioclient_mock.mock_calls] == [
        None,
        "2502.0",
        "0.0",
        "-5.2",
    ]


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize(
    "selection", ["known_height", "missing_height", "invalid", "legacy"]
)
async def test_real_entry_routes_forecast_only_and_reload_preserves_ids(
    hass,
    aioclient_mock,
    enable_custom_integrations,
    selected_location,
    source,
    selection,
    caplog,
):
    hass.config.latitude, hass.config.longitude = 47.45, 8.56
    data = {
        "station_id": "KLO",
        "station_name": "Kloten",
        "postal_code": "8302",
        "data_source": source,
        "latitude": 46.2,
        "longitude": 6.1,
    }
    if selection == "missing_height":
        selected_location = replace(
            selected_location,
            point=replace(selected_location.point, altitude_masl=None),
        )
    if selection != "legacy":
        data[CONF_FORECAST_LOCATION] = (
            {"private-point": "do-not-log"}
            if selection == "invalid"
            else encode_forecast_location(selected_location)
        )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        options={"pollen_station": "PZH"},
        unique_id="existing-entry",
        version=1,
        minor_version=2,
    )
    entry.add_to_hass(hass)
    aioclient_mock.get(OPEN_METEO_BASE_URL, json=payload())
    original = dict(entry.data)
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
                return_value={},
            )
        )
        for name, result in {
            "MeteoSwissDataUpdateCoordinator": {
                "temperature": 12,
                "precipitation": 0,
                "last_update": NOW.isoformat(),
            },
            "OpenMeteoDataUpdateCoordinator": {
                "temperature": 12,
                "precipitation": 0,
                "last_update": NOW.isoformat(),
            },
            "MeteoSwissAlertsCoordinator": [],
            "OpenMeteoPollenCoordinator": {},
            "MeteoSwissPollenCoordinator": {},
        }.items():
            stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.coordinator.{name}._async_update_data",
                    return_value=result,
                )
            )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        runtime = entry.runtime_data
        forecast = runtime.forecast_coordinator
        base = (47.45, 8.56) if source == "meteoswiss" else (46.2, 6.1)
        assert (
            runtime.pollen_coordinator.latitude,
            runtime.pollen_coordinator.longitude,
        ) == base
        assert runtime.alerts_coordinator._alerts_api.postal_code == "8302"
        assert runtime.meteoswiss_pollen_coordinator.client.station_id == "pzh"
        if source == "openmeteo":
            assert (runtime.coordinator.latitude, runtime.coordinator.longitude) == base
        else:
            assert runtime.coordinator.station_id.lower() == "klo"
        if selection == "invalid":
            assert not forecast.last_update_success and forecast.data is None
            assert len(aioclient_mock.mock_calls) == 0
            assert runtime.forecast_target.status == "invalid"
            assert (
                "do-not-log" not in caplog.text and "private-point" not in caplog.text
            )
        else:
            expected = (
                base
                if selection == "legacy"
                else (
                    selected_location.point.latitude,
                    selected_location.point.longitude,
                )
            )
            query = aioclient_mock.mock_calls[0][1].query
            assert (float(query["latitude"]), float(query["longitude"])) == expected
            assert ("elevation" in query) == (selection == "known_height")
            assert (
                forecast.last_update_success and forecast.data[0]["temperature"] == -10
            )
            assert len(aioclient_mock.mock_calls) == 1
        registry = er.async_get(hass)
        ids = {
            row.entity_id: row.unique_id
            for row in er.async_entries_for_config_entry(registry, entry.entry_id)
        }
        weather_id = next(key for key in ids if key.startswith("weather."))
        state = hass.states.get(weather_id)
        assert state.state != "unavailable" and state.attributes["temperature"] == 12
        if selection != "legacy":
            assert state.state != "snowy"
            assert (
                state.attributes[CONF_FORECAST_LOCATION]["status"]
                == runtime.forecast_target.status
            )
        forecast_result = await hass.services.async_call(
            "weather",
            "get_forecasts",
            {"entity_id": weather_id, "type": "hourly"},
            blocking=True,
            return_response=True,
        )
        assert bool(forecast_result[weather_id]["forecast"]) == (selection != "invalid")
        if selection != "invalid":
            assert forecast_result[weather_id]["forecast"][0]["temperature"] == -10
        for entity_id in ids:
            if (
                "maximum_temperature_today_forecast" in entity_id
                or "heating_degree_days" in entity_id
            ):
                attrs = hass.states.get(entity_id).attributes
                if selection != "invalid":
                    assert (CONF_FORECAST_LOCATION in attrs) == (selection != "legacy")
        diagnostics = await async_get_config_entry_diagnostics(hass, entry)
        if selection != "legacy":
            assert (
                diagnostics["config_entry"]["data"][CONF_FORECAST_LOCATION] == REDACTED
            )
            assert selected_location.point.name not in repr(diagnostics)
            assert selected_location.catalogue_sha256 not in repr(diagnostics)
        assert diagnostics["location_sources"]["weather_alerts"] == "postal_code"
        assert entry.data == original and entry.unique_id == "existing-entry"
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        assert not forecast._listeners
        assert {
            row.entity_id: row.unique_id
            for row in er.async_entries_for_config_entry(registry, entry.entry_id)
        } == ids
        assert entry.data == original and (
            hass.config.latitude,
            hass.config.longitude,
        ) == (47.45, 8.56)
        if selection == "invalid":
            hass.config_entries.async_update_entry(
                entry,
                data={
                    **entry.data,
                    CONF_FORECAST_LOCATION: encode_forecast_location(selected_location),
                },
            )
            await hass.async_block_till_done()
            repaired = entry.runtime_data.forecast_coordinator
            assert (
                repaired.last_update_success and repaired.data[0]["temperature"] == -10
            )
            assert entry.runtime_data.forecast_target.location == selected_location
            assert {
                row.entity_id: row.unique_id
                for row in er.async_entries_for_config_entry(registry, entry.entry_id)
            } == ids
            assert (
                entry.runtime_data.pollen_coordinator.latitude,
                entry.runtime_data.pollen_coordinator.longitude,
            ) == base
        reloaded_forecast = entry.runtime_data.forecast_coordinator
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert not reloaded_forecast._listeners
        assert not runtime.session.closed


@pytest.mark.parametrize("valid", [True, False])
async def test_diagnostics_redact_entire_saved_contract_even_when_unloaded(
    hass, selected_location, valid
):
    saved = (
        encode_forecast_location(selected_location)
        if valid
        else {"nested-private-point": ["secret"]}
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_FORECAST_LOCATION: saved},
        options={CONF_FORECAST_LOCATION: {"another-private-point": 123}},
    )
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["config_entry"]["data"][CONF_FORECAST_LOCATION] == REDACTED
    assert result["config_entry"]["options"][CONF_FORECAST_LOCATION] == REDACTED
    assert result["forecast_location"] == {
        "status": "catalogue" if valid else "invalid",
        "elevation_mode": "catalogue" if valid else "unavailable",
    }
    assert result["location_sources"]["weather_forecast"] == (
        "meteoswiss_catalogue" if valid else "invalid_selection"
    )
    assert "private-point" not in repr(result) and "secret" not in repr(result)
    assert selected_location.point.name not in repr(
        result
    ) and selected_location.catalogue_sha256 not in repr(result)


def test_hgt_labels_selected_forecast_even_before_data_arrives(hass, selected_location):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_FORECAST_LOCATION: encode_forecast_location(selected_location)},
    )
    coordinator = MeteoSwissForecastCoordinator(hass, latitude=47.2, longitude=9.3)
    sensor = MeteoSwissHeatingDegreeDaysSensor(coordinator, entry)
    assert (
        sensor.extra_state_attributes[CONF_FORECAST_LOCATION]["name"]
        == selected_location.point.name
    )

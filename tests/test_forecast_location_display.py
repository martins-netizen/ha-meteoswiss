"""Keep Kloten observations and a selected mountain forecast visibly separate."""

from contextlib import ExitStack
from datetime import timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from homeassistant.components.weather.const import DATA_COMPONENT
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant_custom_component.common import MockConfigEntry
from test_forecast_summary import NOW, forecast_rows

from custom_components.meteoswiss.const import CONF_FORECAST_LOCATION, DOMAIN
from custom_components.meteoswiss.coordinator import MeteoSwissDataUpdateCoordinator
from custom_components.meteoswiss.forecast_location_config import (
    encode_forecast_location,
)
from custom_components.meteoswiss.forecast_locations import (
    ForecastPointType,
    parse_forecast_catalogue,
)
from custom_components.meteoswiss.sensor import FORECAST_SENSOR_DESCRIPTIONS
from custom_components.meteoswiss.weather import async_setup_entry


@pytest.fixture
async def separated_entry(hass, enable_custom_integrations, freezer, request):
    freezer.move_to(NOW)
    hass.config.latitude, hass.config.longitude = 47.45, 8.56
    language = getattr(request, "param", "en")
    hass.config.language = language
    catalogue = parse_forecast_catalogue(
        (Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv")
        .read_text()
        .encode("latin-1"),
        NOW,
    )
    selected = catalogue.select(ForecastPointType.POINT_OF_INTEREST, "711")
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "station_id": "KLO",
            "station_name": "Kloten",
            "postal_code": "8302",
            "data_source": "meteoswiss",
            CONF_FORECAST_LOCATION: encode_forecast_location(selected),
        },
    )
    entry.add_to_hass(hass)
    devices, entities = dr.async_get(hass), er.async_get(hass)
    observed = devices.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="MeteoSwiss Kloten",
        manufacturer="MeteoSwiss",
        model="SwissMetNet",
    )
    calculated = devices.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, f"calculated_{entry.entry_id}")},
        name="Calculated Weather Metrics",
    )
    # Existing b1 registry records, including a user-edited entity name/ID.
    kept = {}
    for description in FORECAST_SENSOR_DESCRIPTIONS:
        row = entities.async_get_or_create(
            "sensor",
            DOMAIN,
            f"{DOMAIN}_{entry.entry_id}_{description.key}",
            config_entry=entry,
            device_id=observed.id,
            suggested_object_id=f"retained_{description.key}",
        )
        kept[description.key] = row.entity_id
    entities.async_update_entity(kept["forecast_probability_today"], name="My rain")
    hgt = entities.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{DOMAIN}_{entry.entry_id}_heating_degree_days",
        config_entry=entry,
        device_id=calculated.id,
        suggested_object_id="retained_hgt",
    )
    observed_weather = entities.async_get_or_create(
        "weather",
        DOMAIN,
        f"{DOMAIN}_{entry.entry_id}_weather",
        config_entry=entry,
        device_id=observed.id,
        suggested_object_id="retained_kloten",
    )
    rows = forecast_rows()
    for row in rows:
        row.update(
            temperature=-8,
            condition="snowy",
            humidity=87,
            wind_speed=15,
            wind_direction=120,
            daily_temperature_max=-5,
            daily_temperature_min=-12,
        )
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
                return_value={},
            )
        )
        mocks = {}
        for name, data in {
            "MeteoSwissDataUpdateCoordinator": {
                "temperature": 12,
                "precipitation": 0,
                "last_update": NOW.isoformat(),
            },
            "MeteoSwissForecastCoordinator": rows,
            "MeteoSwissAlertsCoordinator": [],
            "OpenMeteoPollenCoordinator": {},
            "MeteoSwissPollenCoordinator": {},
        }.items():
            mocks[name] = stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.coordinator.{name}._async_update_data",
                    return_value=data,
                )
            )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        yield (
            entry,
            selected,
            observed,
            calculated,
            kept,
            hgt.entity_id,
            observed_weather.entity_id,
            mocks,
        )
        if getattr(entry, "runtime_data", None) is not None:
            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()


@pytest.mark.parametrize("separated_entry", ["en", "de", "fr", "it"], indirect=True)
async def test_forecast_device_names_and_weather_do_not_claim_station_measurements(
    hass,
    separated_entry,
):
    entry, selected, observed, calculated, kept, hgt, old_weather, mocks = (
        separated_entry
    )
    entities, devices = er.async_get(hass), dr.async_get(hass)
    forecast_device = devices.async_get(calculated.id)
    assert selected.point.name in forecast_device.name
    assert "Kloten" not in forecast_device.name
    assert devices.async_get(observed.id).name == "MeteoSwiss Kloten"
    for entity_id in (*kept.values(), hgt):
        assert entities.async_get(entity_id).device_id == calculated.id
    assert entities.async_get(kept["forecast_probability_today"]).name == "My rain"
    forecast_weather = entities.async_get_entity_id(
        "weather", DOMAIN, f"{DOMAIN}_{entry.entry_id}_forecast_weather"
    )
    assert forecast_weather and forecast_weather != old_weather
    measured = hass.states.get(old_weather)
    predicted = hass.states.get(forecast_weather)
    assert measured.attributes["temperature"] == 12
    assert measured.attributes["supported_features"] == 0
    assert predicted.attributes["temperature"] == -8
    assert predicted.attributes["humidity"] == 87
    assert predicted.attributes["wind_speed"] == 15
    assert predicted.attributes["wind_bearing"] == 120
    assert predicted.attributes["value_type"] == "forecast"
    assert predicted.state == "snowy"
    assert selected.point.name in predicted.name
    assert predicted.attributes[CONF_FORECAST_LOCATION]["name"] == selected.point.name
    assert "pressure" not in predicted.attributes
    response = await hass.services.async_call(
        "weather",
        "get_forecasts",
        {"entity_id": forecast_weather, "type": "hourly"},
        blocking=True,
        return_response=True,
    )
    assert response[forecast_weather]["forecast"][0]["temperature"] == -8
    # New display projections reuse the already-existing fetch and subscription.
    assert mocks["MeteoSwissForecastCoordinator"].await_count == 1


async def test_reset_and_reload_keep_ids_custom_names_and_existing_devices(
    hass, separated_entry
):
    entry, _, observed, calculated, kept, hgt, old_weather, mocks = separated_entry
    entities, devices = er.async_get(hass), dr.async_get(hass)
    forecast_id = entities.async_get_entity_id(
        "weather", DOMAIN, f"{DOMAIN}_{entry.entry_id}_forecast_weather"
    )
    assert forecast_id is not None
    before = {
        row.unique_id: row.entity_id
        for row in er.async_entries_for_config_entry(entities, entry.entry_id)
    }
    devices.async_update_device(calculated.id, name_by_user="My weather model")
    data = dict(entry.data)
    data.pop(CONF_FORECAST_LOCATION)
    hass.config_entries.async_update_entry(entry, data=data)
    await hass.async_block_till_done()
    assert {
        row.unique_id: row.entity_id
        for row in er.async_entries_for_config_entry(entities, entry.entry_id)
    } == before
    assert entities.async_get(old_weather).device_id == observed.id
    assert all(
        entities.async_get(item).device_id == calculated.id
        for item in (*kept.values(), hgt, forecast_id)
    )
    assert devices.async_get(calculated.id).name_by_user == "My weather model"
    assert "Säntis" not in devices.async_get(calculated.id).name
    assert entities.async_get(kept["forecast_probability_today"]).name == "My rain"
    assert hass.states.get(old_weather).attributes["supported_features"] != 0
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    assert {
        row.unique_id: row.entity_id
        for row in er.async_entries_for_config_entry(entities, entry.entry_id)
    } == before
    assert mocks["MeteoSwissForecastCoordinator"].await_count == 3


async def test_forecast_failure_and_stale_snapshot_do_not_use_station_as_fallback(
    hass,
    separated_entry,
    freezer,
):
    entry, _, _, _, _, _, old_weather, _ = separated_entry
    forecast_id = er.async_get(hass).async_get_entity_id(
        "weather", DOMAIN, f"{DOMAIN}_{entry.entry_id}_forecast_weather"
    )
    assert forecast_id is not None
    source = entry.runtime_data.forecast_coordinator
    entity = hass.data[DATA_COMPONENT].get_entity(forecast_id)
    source.async_set_update_error(ValueError("forecast unavailable"))
    await hass.async_block_till_done()
    assert hass.states.get(forecast_id).state == "unavailable"
    assert hass.states.get(old_weather).attributes["temperature"] == 12
    source.async_set_updated_data(source.data)
    await hass.async_block_till_done()
    assert hass.states.get(forecast_id).state == "snowy"
    current = entry.runtime_data.coordinator
    current.async_set_update_error(ValueError("station unavailable"))
    await hass.async_block_till_done()
    assert hass.states.get(old_weather).state == "unavailable"
    assert hass.states.get(forecast_id).state == "snowy"
    freezer.move_to(NOW + timedelta(hours=3, seconds=1))
    assert entity.available is False and entity.native_temperature is None


@pytest.mark.parametrize("language", ["en", "de", "fr", "it"])
async def test_ha_translates_forecast_device_roles(
    hass, enable_custom_integrations, language
):
    names = await async_get_translations(hass, language, "device", {DOMAIN})
    for key in ("forecast_catalogue", "forecast_base", "forecast_invalid"):
        assert names.get(f"component.{DOMAIN}.device.{key}.name")


async def test_weather_setup_without_optional_forecast_keeps_current_conditions(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"station_name": "Kloten"})
    current = MeteoSwissDataUpdateCoordinator(
        hass, station_id="KLO", update_interval=600
    )
    current.data = {"temperature": 12}
    entry.runtime_data = SimpleNamespace(coordinator=current, forecast_coordinator=None)
    captured = []
    await async_setup_entry(hass, entry, captured.extend)
    assert len(captured) == 1
    assert captured[0].unique_id == f"{DOMAIN}_{entry.entry_id}_weather"
    assert captured[0].native_temperature == 12


async def test_forecast_entity_pushes_only_its_model_updates_to_subscribers(
    hass, separated_entry
):
    entry, _, _, _, _, _, _, _ = separated_entry
    forecast_id = er.async_get(hass).async_get_entity_id(
        "weather", DOMAIN, f"{DOMAIN}_{entry.entry_id}_forecast_weather"
    )
    entity = hass.data[DATA_COMPONENT].get_entity(forecast_id)
    received = []
    unsubscribe = entity.async_subscribe_forecast("hourly", received.append)
    source = entry.runtime_data.forecast_coordinator
    rows = [{**row, "temperature": -15} for row in source.data]
    source.async_set_updated_data(rows)
    await hass.async_block_till_done()
    assert received[-1][0]["temperature"] == -15
    source.async_set_update_error(ValueError("forecast unavailable"))
    await hass.async_block_till_done()
    assert received[-1] == []
    source.async_set_updated_data(rows)
    await hass.async_block_till_done()
    assert received[-1][0]["temperature"] == -15
    unsubscribe()

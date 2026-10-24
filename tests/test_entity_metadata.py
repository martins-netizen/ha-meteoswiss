"""Compatibility contracts for existing device groups and entity identities."""

import logging

import pytest
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.binary_sensor import (
    ALERT_SENSOR_DESCRIPTIONS,
    MeteoSwissAlertsBinarySensor,
)
from custom_components.meteoswiss.const import (
    ATTRIBUTION,
    DOMAIN,
    OPENMETEO_AIR_QUALITY_ATTRIBUTION,
)
from custom_components.meteoswiss.pollen_sensor import (
    POLLEN_SENSOR_DESCRIPTIONS,
    MeteoSwissPollenSensor,
)
from custom_components.meteoswiss.sensor import (
    AIR_QUALITY_SENSOR_DESCRIPTIONS,
    MS_POLLEN_SENSOR_DESCRIPTIONS,
    SENSOR_DESCRIPTIONS,
    HGT_ATTRIBUTION,
    MeteoSwissAirQualitySensor,
    MeteoSwissCacheStatsSensor,
    MeteoSwissHeatingDegreeDaysSensor,
    MeteoSwissMeasuredPollenSensor,
    MeteoSwissSensor,
    MeteoSwissStationsMapSensor,
)
from custom_components.meteoswiss.stations_map import MeteoSwissStationsMap
from custom_components.meteoswiss.weather import MeteoSwissWeather


@pytest.mark.parametrize(
    "family",
    [
        "observation",
        "weather",
        "warning",
        "aq",
        "pollen",
        "measured_pollen",
        "hgt",
        "stations",
        "cache",
    ],
)
async def test_existing_entity_metadata_and_identity_contract(hass, family):
    entry = MockConfigEntry(domain=DOMAIN, entry_id="identity-contract")
    coordinator = DataUpdateCoordinator(
        hass, logging.getLogger(__name__), name="contract", config_entry=entry
    )
    coordinator.data = {}
    weather = {
        "identifiers": {(DOMAIN, entry.entry_id)},
        "name": "MeteoSwiss Example station",
        "manufacturer": "MeteoSwiss",
        "model": "SwissMetNet",
    }
    aq = {
        "identifiers": {(DOMAIN, f"pollen_{entry.entry_id}")},
        "name": "Open-Meteo Air Quality & Pollen",
        "manufacturer": "Open-Meteo",
        "model": "Air Quality API",
    }
    if family == "observation":
        entity = MeteoSwissSensor(
            coordinator, entry, SENSOR_DESCRIPTIONS[0], "Example station"
        )
        suffix, info, attribution = "temperature", weather, ATTRIBUTION
    elif family == "weather":
        entity = MeteoSwissWeather(coordinator, None, entry, "Example station")
        suffix, info, attribution = "weather", weather, ATTRIBUTION
        assert entity.name is None
    elif family == "warning":
        entity = MeteoSwissAlertsBinarySensor(
            coordinator, entry, ALERT_SENSOR_DESCRIPTIONS[0], "9997"
        )
        suffix, info, attribution = (
            "any_alert",
            {
                "identifiers": {(DOMAIN, f"alerts_{entry.entry_id}")},
                "name": "MeteoSwiss Alerts - 9997",
                "manufacturer": "MeteoSwiss",
                "model": "Alerts",
            },
            ATTRIBUTION,
        )
    elif family == "aq":
        entity = MeteoSwissAirQualitySensor(
            coordinator, entry, AIR_QUALITY_SENSOR_DESCRIPTIONS[0], "Example station"
        )
        suffix, info, attribution = "pm25", aq, OPENMETEO_AIR_QUALITY_ATTRIBUTION
    elif family == "pollen":
        entity = MeteoSwissPollenSensor(
            coordinator, entry, POLLEN_SENSOR_DESCRIPTIONS[0], "Example station"
        )
        suffix, info, attribution = (
            "pollen_birch_pollen",
            aq,
            OPENMETEO_AIR_QUALITY_ATTRIBUTION,
        )
    elif family == "measured_pollen":
        entity = MeteoSwissMeasuredPollenSensor(
            coordinator, entry, MS_POLLEN_SENSOR_DESCRIPTIONS[0], "Example pollen"
        )
        suffix, info, attribution = (
            "ms_pollen_birch",
            {
                "identifiers": {(DOMAIN, f"ms_pollen_{entry.entry_id}")},
                "name": "MeteoSwiss Pollen (Measured) - Example pollen",
                "manufacturer": "MeteoSwiss",
                "model": "Pollen Station",
            },
            "Source: MeteoSwiss ogd-pollen",
        )
    elif family == "hgt":
        entity = MeteoSwissHeatingDegreeDaysSensor(coordinator, entry)
        suffix, info, attribution = (
            "heating_degree_days",
            {
                "identifiers": {(DOMAIN, f"calculated_{entry.entry_id}")},
                "manufacturer": "MeteoSwiss",
                "model": "ICON Seamless via Open-Meteo",
                "translation_key": "forecast_base",
                "translation_placeholders": {},
            },
            HGT_ATTRIBUTION,
        )
    elif family == "stations":
        entity = MeteoSwissStationsMapSensor(MeteoSwissStationsMap())
        suffix, info, attribution = (
            "stations_map",
            {
                "identifiers": {(DOMAIN, "stations_map")},
                "name": "MeteoSwiss Weather Stations",
                "manufacturer": "MeteoSwiss",
                "model": "SwissMetNet",
            },
            ATTRIBUTION,
        )
    else:
        entity = MeteoSwissCacheStatsSensor()
        suffix, info, attribution = (
            "cache_stats",
            {
                "identifiers": {(DOMAIN, "cache_stats")},
                "name": "MeteoSwiss Cache Statistics",
                "manufacturer": "MeteoSwiss",
                "model": "Intelligent Caching",
            },
            ATTRIBUTION,
        )
    expected_id = (
        f"{DOMAIN}_{suffix}"
        if family in ("stations", "cache")
        else f"{DOMAIN}_{entry.entry_id}_{suffix}"
    )
    assert entity.unique_id == expected_id
    assert entity.device_info == info
    assert entity.has_entity_name is True
    assert entity.attribution == attribution
    assert entity.should_poll is (family in ("stations", "cache"))
    if family not in ("stations", "cache"):
        coordinator.last_update_success = False
        assert entity.available is False
        coordinator.last_update_success = True
        assert entity.available is True

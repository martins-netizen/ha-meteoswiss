"""Regression tests for locally validated MeteoSwiss fixes."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import UnitOfPrecipitationDepth
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.const import (
    CONF_STATION_NAME,
    DEFAULT_POLLEN_STATION,
    DOMAIN,
    OPENMETEO_AIR_QUALITY_DEVICE_NAME,
    POLLEN_STATIONS,
    SENSOR_PRECIPITATION,
    SENSOR_TEMPERATURE,
)
from custom_components.meteoswiss.coordinator import MeteoSwissDataUpdateCoordinator
from custom_components.meteoswiss.forecast_coordinator import (
    MeteoSwissForecastCoordinator,
)
from custom_components.meteoswiss.sensor import (
    SENSOR_DESCRIPTIONS,
    MeteoSwissSensor,
)
from custom_components.meteoswiss.weather import MeteoSwissWeather


def _sensor_description(key: str):
    """Return a sensor entity description by key."""
    return next(description for description in SENSOR_DESCRIPTIONS if description.key == key)


def test_precipitation_sensor_description() -> None:
    """The parsed precipitation value must be exposed as a HA sensor."""
    description = _sensor_description(SENSOR_PRECIPITATION)

    assert description.device_class is SensorDeviceClass.PRECIPITATION
    assert description.state_class is SensorStateClass.MEASUREMENT
    assert (
        description.native_unit_of_measurement
        == UnitOfPrecipitationDepth.MILLIMETERS
    )


async def test_sensor_initializes_from_existing_coordinator_data(hass) -> None:
    """A sensor created after first refresh must immediately expose its value."""
    coordinator = MeteoSwissDataUpdateCoordinator(
        hass,
        station_id="KLO",
        update_interval=600,
    )
    coordinator.data = {SENSOR_TEMPERATURE: 21.5}

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_STATION_NAME: "Kloten"},
    )

    entity = MeteoSwissSensor(
        coordinator,
        entry,
        _sensor_description(SENSOR_TEMPERATURE),
        "Kloten",
    )

    assert entity.native_value == 21.5


class _FakeResponse:
    """Minimal async response for the Open-Meteo request test."""

    status = 200

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def json(self):
        return {
            "hourly": {
                "time": ["2026-08-20T12:00"],
                "temperature_2m": [24.7],
                "weather_code": [3],
            },
            "daily": {
                "time": ["2026-08-20"],
                "temperature_2m_max": [28.8],
                "temperature_2m_min": [19.2],
            },
        }


class _FakeSession:
    """Capture the forecast URL without making a network request."""

    def __init__(self) -> None:
        self.requested_url: str | None = None

    def get(self, url, timeout=None):
        self.requested_url = url
        return _FakeResponse()


async def test_forecast_request_uses_rolling_meteoswiss_seamless_model(hass) -> None:
    """Forecast request must start now and explicitly use MeteoSwiss ICON Seamless."""
    session = _FakeSession()
    coordinator = MeteoSwissForecastCoordinator(
        hass,
        station_id="KLO",
        latitude=47.45,
        longitude=8.56,
        session=session,
    )

    forecast = await coordinator._fetch_open_meteo_forecast()

    assert forecast
    assert session.requested_url is not None
    assert "&forecast_hours=120" in session.requested_url
    assert "&forecast_days=" not in session.requested_url
    assert "&daily=temperature_2m_max,temperature_2m_min" in session.requested_url
    assert "&models=meteoswiss_icon_seamless" in session.requested_url
    assert forecast[0]["daily_temperature_max"] == 28.8
    assert forecast[0]["daily_temperature_min"] == 19.2


async def test_daily_forecast_uses_maximum_and_minimum_temperature(hass) -> None:
    """Daily forecast must expose max temperature and native minimum temperature."""
    current = MeteoSwissDataUpdateCoordinator(
        hass,
        station_id="KLO",
        update_interval=600,
    )
    current.data = {SENSOR_TEMPERATURE: 22.0}

    forecast = MeteoSwissForecastCoordinator(
        hass,
        station_id="KLO",
        latitude=47.45,
        longitude=8.56,
    )
    forecast.data = [
        {
            "datetime": "2026-08-20T07:00",
            "temperature": 19.2,
            "precipitation": 0,
            "precipitation_probability": 0,
        },
        {
            "datetime": "2026-08-20T12:00",
            "temperature": 24.7,
            "precipitation": 0,
            "precipitation_probability": 18,
        },
        {
            "datetime": "2026-08-20T15:00",
            "temperature": 28.8,
            "precipitation": 0,
            "precipitation_probability": 0,
        },
    ]

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_STATION_NAME: "Kloten"},
    )

    entity = MeteoSwissWeather(current, forecast, entry, "Kloten")
    daily = await entity.async_forecast_daily()

    assert len(daily) == 1
    assert daily[0]["temperature"] == 28.8
    assert daily[0]["native_templow"] == 19.2

async def test_daily_forecast_prefers_native_calendar_day_extrema(hass) -> None:
    """Current-day extrema must include hours before the rolling forecast starts."""
    current = MeteoSwissDataUpdateCoordinator(
        hass,
        station_id="KLO",
        update_interval=600,
    )
    current.data = {SENSOR_TEMPERATURE: 30.0}

    forecast = MeteoSwissForecastCoordinator(
        hass,
        station_id="KLO",
        latitude=47.45,
        longitude=8.56,
    )
    # Simulate a forecast fetched in the afternoon. The remaining hourly
    # values alone cannot know the morning minimum or an earlier maximum.
    forecast.data = [
        {
            "datetime": "2026-08-20T15:00",
            "temperature": 28.8,
            "daily_temperature_max": 33.3,
            "daily_temperature_min": 18.1,
            "precipitation": 0,
            "precipitation_probability": 0,
        },
        {
            "datetime": "2026-08-20T16:00",
            "temperature": 27.4,
            "daily_temperature_max": 33.3,
            "daily_temperature_min": 18.1,
            "precipitation": 0,
            "precipitation_probability": 0,
        },
    ]

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_STATION_NAME: "Kloten"},
    )

    entity = MeteoSwissWeather(current, forecast, entry, "Kloten")
    daily = await entity.async_forecast_daily()

    assert len(daily) == 1
    assert daily[0]["temperature"] == 33.3
    assert daily[0]["native_templow"] == 18.1

def test_measured_pollen_default_is_a_known_station() -> None:
    # Runtime and options flow must share one valid measured-pollen default.
    assert DEFAULT_POLLEN_STATION in POLLEN_STATIONS
    assert POLLEN_STATIONS[DEFAULT_POLLEN_STATION] == "Luzern (PLZ)"


def test_location_based_openmeteo_device_name_is_not_station_based() -> None:
    # Air quality and pollen forecasts must not be labelled as SwissMetNet.
    assert OPENMETEO_AIR_QUALITY_DEVICE_NAME == "Open-Meteo Air Quality & Pollen"
    assert "MeteoSwiss" not in OPENMETEO_AIR_QUALITY_DEVICE_NAME

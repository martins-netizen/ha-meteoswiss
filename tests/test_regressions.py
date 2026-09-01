"""Regression tests for locally validated MeteoSwiss fixes."""

from __future__ import annotations

from datetime import datetime, timezone

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
    SENSOR_PRECIPITATION_CURRENT_HOUR,
    SENSOR_TEMPERATURE,
)
from custom_components.meteoswiss.calc import calculate_heating_degree_days
from custom_components.meteoswiss.coordinator import (
    MeteoSwissDataUpdateCoordinator,
    _current_hour_precipitation,
)
from custom_components.meteoswiss.forecast_coordinator import (
    MeteoSwissForecastCoordinator,
)
from custom_components.meteoswiss.sensor import (
    SENSOR_DESCRIPTIONS,
    MeteoSwissSensor,
    _daily_mean_for_date,
)
from custom_components.meteoswiss.precipitation import (
    _asset_urls_for_period,
    _parse_hourly_statistics,
    _subtract_calendar_months,
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


def test_current_hour_precipitation_counts_every_published_interval() -> None:
    """All intervals published together must contribute to the current hour."""
    rows = [
        {"reference_timestamp": "31.08.2026 00:00", "rre150z0": "9.9"},
        {"reference_timestamp": "31.08.2026 00:10", "rre150z0": "2.3"},
        {"reference_timestamp": "31.08.2026 00:20", "rre150z0": "0.7"},
        {"reference_timestamp": "31.08.2026 00:30", "rre150z0": "0.6"},
        {"reference_timestamp": "31.08.2026 00:40", "rre150z0": "0.1"},
        {"reference_timestamp": "31.08.2026 01:00", "rre150z0": "8.8"},
    ]

    total = _current_hour_precipitation(
        rows,
        now=datetime(2026, 8, 31, 0, 45, tzinfo=timezone.utc),
    )

    assert total == 3.7


def test_current_hour_precipitation_counts_repeated_values() -> None:
    """Identical consecutive intervals are separate precipitation totals."""
    rows = [
        {"reference_timestamp": "31.08.2026 00:10", "rre150z0": "0.1"},
        {"reference_timestamp": "31.08.2026 00:20", "rre150z0": "0.1"},
    ]

    total = _current_hour_precipitation(
        rows,
        now=datetime(2026, 8, 31, 0, 25, tzinfo=timezone.utc),
    )

    assert total == 0.2


def test_official_hourly_precipitation_uses_interval_start() -> None:
    """OGD end timestamps must be shifted to HA's hourly start timestamp."""
    content = (
        "station_abbr;reference_timestamp;rre150h0\n"
        "KLO;31.08.2026 01:00;3.7\n"
        "KLO;31.08.2026 02:00;\n"
    )

    statistics = _parse_hourly_statistics(content)

    assert statistics == [
        {
            "start": datetime(2026, 8, 31, 0, 0, tzinfo=timezone.utc),
            "mean": 3.7,
            "min": 3.7,
            "max": 3.7,
        }
    ]


def test_hourly_archive_is_limited_to_thirteen_calendar_months() -> None:
    """Archive parsing must exclude data older than the rolling lookback."""
    now = datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc)
    earliest_start = _subtract_calendar_months(now, 13)
    content = (
        "station_abbr;reference_timestamp;rre150h0\n"
        "KLO;01.08.2025 00:00;9.9\n"
        "KLO;01.08.2025 01:00;1.2\n"
        "KLO;01.09.2026 18:00;0.0\n"
    )

    statistics = _parse_hourly_statistics(content, earliest_start)

    assert earliest_start == datetime(2025, 8, 1, 0, 0, tzinfo=timezone.utc)
    assert [statistic["start"] for statistic in statistics] == [
        datetime(2025, 8, 1, 0, 0, tzinfo=timezone.utc),
        datetime(2026, 9, 1, 17, 0, tzinfo=timezone.utc),
    ]


def test_calendar_month_lookback_handles_month_end() -> None:
    """Calendar subtraction must clamp dates to the target month."""
    value = datetime(2025, 3, 31, 12, 30, tzinfo=timezone.utc)

    assert _subtract_calendar_months(value, 1) == datetime(
        2025, 2, 28, 0, 0, tzinfo=timezone.utc
    )


def test_hourly_archive_selects_only_overlapping_decade_assets() -> None:
    """Archive lookup must handle MeteoSwiss' decade-based filenames."""
    assets = {
        "ogd-smn_klo_h_historical_2010-2019.csv": {"href": "2010.csv"},
        "ogd-smn_klo_h_historical_2020-2029.csv": {"href": "2020.csv"},
        "ogd-smn_klo_h_historical_2030-2039.csv": {"href": "2030.csv"},
        "ogd-smn_klo_h_recent.csv": {"href": "recent.csv"},
    }

    assert _asset_urls_for_period(assets, "klo", "historical", 2028) == [
        "2020.csv",
        "2030.csv",
    ]
    assert _asset_urls_for_period(assets, "klo", "recent", 2028) == [
        "recent.csv"
    ]


def test_current_hour_precipitation_sensor_description() -> None:
    """The running-hour total must be a separate precipitation measurement."""
    description = _sensor_description(SENSOR_PRECIPITATION_CURRENT_HOUR)

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
                "temperature_2m_mean": [24.1],
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
    assert (
        "&daily=temperature_2m_max,temperature_2m_min,temperature_2m_mean"
        in session.requested_url
    )
    assert "&models=meteoswiss_icon_seamless" in session.requested_url
    assert forecast[0]["daily_temperature_max"] == 28.8
    assert forecast[0]["daily_temperature_min"] == 19.2
    assert forecast[0]["daily_temperature_mean"] == 24.1


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

def test_swiss_hgt_12_20_formula() -> None:
    # Heating day <= 12 °C; contribution is the difference to 20 °C.
    assert calculate_heating_degree_days(7.0) == 13.0
    assert calculate_heating_degree_days(12.0) == 8.0
    assert calculate_heating_degree_days(13.0) == 0.0
    assert calculate_heating_degree_days(None) is None


def test_hgt_daily_mean_uses_native_calendar_day_value() -> None:
    # Remaining hourly values must not be averaged for today's HGT.
    forecast = [
        {
            "datetime": "2026-08-20T15:00",
            "temperature": 16.0,
            "daily_temperature_mean": 7.0,
        },
        {
            "datetime": "2026-08-20T16:00",
            "temperature": 15.0,
            "daily_temperature_mean": 7.0,
        },
    ]

    daily_mean = _daily_mean_for_date(forecast, "2026-08-20")
    assert daily_mean == 7.0
    assert calculate_heating_degree_days(daily_mean) == 13.0

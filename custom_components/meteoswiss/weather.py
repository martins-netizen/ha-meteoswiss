"""Weather platform for meteoswiss integration."""
from __future__ import annotations

import logging
from datetime import timedelta
from typing import Final

from homeassistant.components.weather import Forecast, WeatherEntity
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import (
    ATTRIBUTION,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_STATION_NAME,
    DOMAIN,
    SENSOR_HUMIDITY,
    SENSOR_PRECIPITATION,
    SENSOR_PRESSURE,
    SENSOR_TEMPERATURE,
    SENSOR_WIND_DIRECTION,
    SENSOR_WIND_SPEED,
)
from .coordinator import MeteoSwissDataUpdateCoordinator
from .forecast_coordinator import MeteoSwissForecastCoordinator
from .weather_data import FORECAST_TIME_ZONE, forecast_datetime, weather_condition

from .runtime_data import MeteoSwissConfigEntry

# Coordinators centralize refreshes; sensor diagnostics use bounded polling.
PARALLEL_UPDATES = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeteoSwissConfigEntry,
    async_add_entities,
) -> None:
    """Set up weather platform."""
    coordinator = entry.runtime_data.coordinator
    forecast_coordinator = entry.runtime_data.forecast_coordinator
    station_name = entry.data.get(CONF_STATION_NAME, "Unknown")

    entity = MeteoSwissWeather(coordinator, forecast_coordinator, entry, station_name)

    async_add_entities([entity])


class MeteoSwissWeather(CoordinatorEntity[MeteoSwissDataUpdateCoordinator], WeatherEntity):
    """Representation of meteoswiss weather data."""

    # MeteoSwiss symbol/condition mapping (if available)
    METEOSWISS_CONDITION_MAP: Final[dict[str, str]] = {
        "clear": "sunny",
        "sunny": "sunny",
        "partly-cloudy": "partlycloudy",
        "cloudy": "cloudy",
        "overcast": "cloudy",
        "rain": "rainy",
        "rainy": "rainy",
        "snow": "snowy",
        "snowy": "snowy",
        "fog": "fog",
        "mist": "fog",
        "thunderstorm": "lightning",
    }

    def __init__(
        self,
        coordinator: MeteoSwissDataUpdateCoordinator,
        forecast_coordinator: MeteoSwissForecastCoordinator,
        entry: MeteoSwissConfigEntry,
        station_name: str,
    ) -> None:
        """Initialize weather entity."""
        super().__init__(coordinator)
        self._station_name = station_name
        self._forecast_coordinator = forecast_coordinator
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"MeteoSwiss {station_name}",
            manufacturer="MeteoSwiss",
            model="SwissMetNet",
        )
        self._attr_has_entity_name = True
        self._attr_name = None
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_weather"
        self._attr_attribution = ATTRIBUTION
        self._attr_native_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_native_pressure_unit = UnitOfPressure.HPA
        self._attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
        self._attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS

        # Log coordinates for debug
        lat = entry.data.get(CONF_LATITUDE)
        lon = entry.data.get(CONF_LONGITUDE)
        _LOGGER.debug("WeatherEntity initialized - station: %s, lat/lon: %s/%s", station_name, lat, lon)

    async def async_added_to_hass(self) -> None:
        """Subscribe only while the entity is in Home Assistant."""
        await super().async_added_to_hass()
        if self._forecast_coordinator:
            self.async_on_remove(
                self._forecast_coordinator.async_add_listener(self._handle_forecast_update)
            )

    @property
    def coordinator_data(self) -> dict:
        """Return coordinator data."""
        if not self.coordinator:
            _LOGGER.debug("Current weather coordinator is None!")
            return {}

        data = self.coordinator.data
        if not data:
            _LOGGER.debug("Coordinator data is empty!")
            return {}

        _LOGGER.debug("MeteoSwiss coordinator data: %s", data)
        return data

    @property
    def forecast_coordinator_data(self) -> list:
        """Return forecast coordinator data."""
        if not self._forecast_coordinator:
            _LOGGER.debug("Forecast coordinator is None!")
            return []

        if not self._forecast_coordinator.last_update_success:
            return []
        data = self._forecast_coordinator.data
        if data:
            fetched_at = forecast_datetime(data[0].get("fetched_at"))
            if fetched_at is not None and dt_util.utcnow() - fetched_at > timedelta(hours=3):
                return []
        return data if data else []

    @callback
    def _handle_forecast_update(self) -> None:
        """Handle forecast coordinator update."""
        _LOGGER.debug("Forecast update triggered")
        self.async_write_ha_state()

    @property
    def supported_features(self) -> int:
        """Return supported features."""
        from homeassistant.components.weather import WeatherEntityFeature
        return WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY

    def _map_open_meteo_condition(self, weather_code: int | None) -> str | None:
        """Map known codes; missing weather is not partly cloudy."""
        return weather_condition(weather_code)

    def _resolve_condition(self) -> str | None:
        """Use a measured/current condition or the current forecast interval.

        Missing cloud information never implies a clear sky. A positive
        measured precipitation interval remains an explicitly documented
        fallback for rain.
        """
        current = self.coordinator_data
        condition = current.get("weather_condition")
        if condition:
            return condition
        for key in ("symbol", "icon", "condition"):
            symbol = current.get(key)
            if symbol and (condition := self.METEOSWISS_CONDITION_MAP.get(str(symbol).lower())):
                return condition

        now = dt_util.utcnow()
        for item in self.forecast_coordinator_data:
            timestamp = forecast_datetime(item.get("datetime"))
            if timestamp is not None and timestamp <= now < timestamp + timedelta(hours=1):
                condition = item.get("condition") or weather_condition(
                    item.get("weather_code"), item.get("is_day")
                )
                if condition:
                    return condition

        if (current.get(SENSOR_PRECIPITATION) or 0) > 0:
            return "rainy"
        return None

    @property
    def condition(self) -> str | None:
        """Return current condition with fallback logic."""
        return self._resolve_condition()

    @property
    def temperature(self) -> float | None:
        """Return temperature from coordinator data."""
        if not self.coordinator:
            _LOGGER.debug("Coordinator is None")
            return None

        data = self.coordinator.data
        if not data:
            _LOGGER.debug("Coordinator data is empty")
            return None

        temp = data.get(SENSOR_TEMPERATURE)
        if temp is not None:
            return temp

        _LOGGER.debug("Temperature not found in coordinator data")
        return None

    @property
    def humidity(self) -> int | None:
        """Return humidity from coordinator data."""
        if not self.coordinator:
            _LOGGER.debug("Coordinator is None")
            return None

        data = self.coordinator.data
        if not data:
            _LOGGER.debug("Coordinator data is empty")
            return None

        hum = data.get(SENSOR_HUMIDITY)
        if hum is not None:
            return hum

        _LOGGER.debug("Humidity not found in coordinator data")
        return None

    @property
    def pressure(self) -> float | None:
        """Return pressure from coordinator data."""
        if not self.coordinator:
            _LOGGER.debug("Coordinator is None")
            return None

        data = self.coordinator.data
        if not data:
            _LOGGER.debug("Coordinator data is empty")
            return None

        press = data.get(SENSOR_PRESSURE)
        if press is not None:
            return press

        _LOGGER.debug("Pressure not found in coordinator data")
        return None

    @property
    def wind_speed(self) -> float | None:
        """Return wind speed from coordinator data."""
        if not self.coordinator:
            _LOGGER.debug("Coordinator is None")
            return None

        data = self.coordinator.data
        if not data:
            _LOGGER.debug("Coordinator data is empty")
            return None

        speed = data.get(SENSOR_WIND_SPEED)
        if speed is not None:
            return speed

        _LOGGER.debug("Wind speed not found in coordinator data")
        return None

    @property
    def wind_bearing(self) -> float | None:
        """Return wind bearing from coordinator data."""
        if not self.coordinator:
            _LOGGER.debug("Coordinator is None")
            return None

        data = self.coordinator.data
        if not data:
            _LOGGER.debug("Coordinator data is empty")
            return None

        bearing = data.get(SENSOR_WIND_DIRECTION)
        if bearing is not None:
            return bearing

        _LOGGER.debug("Wind bearing not found in coordinator data")
        return None

    @property
    def precipitation_unit(self) -> str:
        """Return precipitation unit."""
        return UnitOfPrecipitationDepth.MILLIMETERS

    @property
    def precipitation(self) -> float | None:
        """Return precipitation."""
        if self.coordinator_data:
            return self.coordinator_data.get(SENSOR_PRECIPITATION)
        return None

    async def async_forecast_hourly(self) -> list[Forecast]:
        """Return hourly forecast (never None)."""
        _LOGGER.debug("=== HOURLY FORECAST REQUEST ===")

        forecast_data = self.forecast_coordinator_data

        if not forecast_data:
            _LOGGER.debug("No forecast data available for hourly forecast, returning empty list")
            return []

        _LOGGER.debug("Building hourly forecast from %d entries", len(forecast_data))

        ha_forecast = []
        for entry in forecast_data[:24]:  # Limit to 24 hours
            try:
                dt = entry.get("datetime")
                temp = entry.get("temperature")

                if dt and temp is not None:
                    ha_forecast.append(Forecast(
                        datetime=dt,
                        temperature=temp,
                        precipitation=entry.get("precipitation"),
                        precipitation_probability=entry.get("precipitation_probability"),
                        wind_speed=entry.get("wind_speed"),
                        wind_bearing=entry.get("wind_direction"),
                        condition=entry.get("condition"),
                    ))
            except Exception as err:
                _LOGGER.warning("Error building hourly forecast entry: %s", err)
                continue

        _LOGGER.debug("Returning %d hourly forecast entries", len(ha_forecast))
        return ha_forecast

    async def async_forecast_daily(self) -> list[Forecast]:
        """Return daily forecast (never None)."""
        _LOGGER.debug("=== DAILY FORECAST REQUEST ===")

        forecast_data = self.forecast_coordinator_data

        if not forecast_data:
            _LOGGER.debug("No forecast data available for daily forecast, returning empty list")
            return []

        _LOGGER.debug("Building daily forecast from %d hourly entries", len(forecast_data))

        # Group hourly data by day (up to 5 days = 120 hours)
        daily_data = {}
        for entry in forecast_data[:120]:
            try:
                dt_str = entry.get("datetime", "")
                if not dt_str:
                    continue

                timestamp = forecast_datetime(dt_str)
                if timestamp is None:
                    continue
                date_str = entry.get("local_date") or timestamp.astimezone(FORECAST_TIME_ZONE).date().isoformat()
                if date_str not in daily_data:
                    daily_data[date_str] = []
                daily_data[date_str].append(entry)
            except Exception as err:
                _LOGGER.warning("Error processing daily forecast entry: %s", err)
                continue

        def aggregate_known(entries, key, operation):
            values = [item[key] for item in entries if item.get(key) is not None]
            return operation(values) if values else None

        # Build daily forecast (one entry per day)
        ha_forecast = []
        for date_str, hourly_entries in list(daily_data.items())[:5]:  # Max 5 days
            try:
                if not hourly_entries:
                    continue

                midday_entries = [
                    item for item in hourly_entries
                    if (timestamp := forecast_datetime(item.get("datetime"))) is not None
                    and 12 <= timestamp.astimezone(FORECAST_TIME_ZONE).hour <= 14
                ]
                representative = midday_entries[0] if midday_entries else hourly_entries[0]

                temperatures = [
                    entry.get("temperature")
                    for entry in hourly_entries
                    if entry.get("temperature") is not None
                ]
                daily_temperature_max = next(
                    (
                        entry.get("daily_temperature_max")
                        for entry in hourly_entries
                        if entry.get("daily_temperature_max") is not None
                    ),
                    None,
                )
                daily_temperature_min = next(
                    (
                        entry.get("daily_temperature_min")
                        for entry in hourly_entries
                        if entry.get("daily_temperature_min") is not None
                    ),
                    None,
                )

                ha_forecast.append(Forecast(
                    datetime=representative.get("datetime"),
                    temperature=(
                        daily_temperature_max
                        if daily_temperature_max is not None
                        else max(temperatures) if temperatures
                        else representative.get("temperature")
                    ),
                    native_templow=(
                        daily_temperature_min
                        if daily_temperature_min is not None
                        else min(temperatures) if temperatures
                        else None
                    ),
                    precipitation=next(
                        (e["daily_precipitation"] for e in hourly_entries if e.get("daily_precipitation") is not None),
                        aggregate_known(hourly_entries, "precipitation", sum),
                    ),
                    precipitation_probability=next(
                        (e["daily_precipitation_probability"] for e in hourly_entries if e.get("daily_precipitation_probability") is not None),
                        aggregate_known(hourly_entries, "precipitation_probability", max),
                    ),
                    wind_speed=representative.get("wind_speed"),
                    wind_bearing=representative.get("wind_direction"),
                    condition=representative.get("condition"),
                ))
            except Exception as err:
                _LOGGER.warning("Error building daily forecast for %s: %s", date_str, err)
                continue

        _LOGGER.debug("Returning %d daily forecast entries", len(ha_forecast))
        return ha_forecast

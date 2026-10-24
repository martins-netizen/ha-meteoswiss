"""Native HA weather attributes and calendar-aware forecast projection."""

from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime, time, timedelta
from typing import Any, Final

from homeassistant.components.weather import (
    Forecast,
    WeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.util import dt as dt_util

from .const import (
    CONF_STATION_NAME,
    DOMAIN,
    SENSOR_HUMIDITY,
    SENSOR_PRECIPITATION,
    SENSOR_PRESSURE,
    SENSOR_TEMPERATURE,
    SENSOR_WIND_DIRECTION,
    SENSOR_WIND_SPEED,
)
from .coordinator import (
    MeteoSwissDataUpdateCoordinator,
    MeteoSwissForecastCoordinator,
    OpenMeteoDataUpdateCoordinator,
)
from .entity import MeteoSwissCoordinatorEntity, weather_device_info
from .forecast_location_config import resolve_forecast_target
from .runtime_data import MeteoSwissConfigEntry
from .weather_data import (
    FORECAST_TIME_ZONE,
    forecast_datetime,
    weather_condition,
    weather_number,
)

PARALLEL_UPDATES = 0

_VALID_CONDITIONS = frozenset(
    {
        "clear-night",
        "cloudy",
        "exceptional",
        "fog",
        "hail",
        "lightning",
        "lightning-rainy",
        "partlycloudy",
        "pouring",
        "rainy",
        "snowy",
        "snowy-rainy",
        "sunny",
        "windy",
        "windy-variant",
    }
)


def _condition(raw: Any) -> str | None:
    """Only HA condition names can become a weather state."""
    return raw if isinstance(raw, str) and raw in _VALID_CONDITIONS else None


def _known(entries: list[dict], key: str, minimum=None, maximum=None) -> list[float]:
    """Read only valid numbers, retaining zero and negative temperatures."""
    return [
        value
        for entry in entries
        if (value := weather_number(entry.get(key), minimum, maximum)) is not None
    ]


def _whole_day_values(
    entries: list[tuple[datetime, dict]],
    day: date,
    key: str,
    minimum=None,
    maximum=None,
    *,
    interval_end: bool = False,
) -> list[float]:
    """Require every Swiss calendar hour, respecting preceding-hour buckets."""
    first = datetime.combine(day, time.min, FORECAST_TIME_ZONE).astimezone(UTC)
    last = datetime.combine(
        day + timedelta(days=1), time.min, FORECAST_TIME_ZONE
    ).astimezone(UTC)
    expected = {
        first + timedelta(hours=i + int(interval_end))
        for i in range(int((last - first).total_seconds() // 3600))
    }
    values = {
        stamp: value
        for stamp, row in entries
        if stamp in expected
        and (value := weather_number(row.get(key), minimum, maximum)) is not None
    }
    return list(values.values()) if values.keys() == expected else []


def _forecast(timestamp: datetime, entry: dict) -> Forecast:
    """Project validated values into HA's native-unit forecast contract."""
    return Forecast(
        datetime=timestamp.isoformat(),
        native_temperature=weather_number(entry.get("temperature")),
        native_precipitation=weather_number(entry.get("precipitation"), 0),
        precipitation_probability=weather_number(
            entry.get("precipitation_probability"), 0, 100
        ),
        humidity=weather_number(entry.get("humidity"), 0, 100),
        native_wind_speed=weather_number(entry.get("wind_speed"), 0),
        wind_bearing=weather_number(entry.get("wind_direction"), 0, 360),
        condition=_condition(entry.get("condition"))
        or weather_condition(entry.get("weather_code"), entry.get("is_day")),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MeteoSwissConfigEntry,
    async_add_entities,
) -> None:
    """Set up weather platform without changing existing entity identity."""
    async_add_entities(
        [
            MeteoSwissWeather(
                entry.runtime_data.coordinator,
                entry.runtime_data.forecast_coordinator,
                entry,
                entry.data.get(CONF_STATION_NAME, "Unknown"),
            )
        ]
    )


class MeteoSwissWeather(
    MeteoSwissCoordinatorEntity[
        MeteoSwissDataUpdateCoordinator | OpenMeteoDataUpdateCoordinator
    ],
    WeatherEntity,
):
    """Observations and independent ICON forecasts for one existing entry."""

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
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_HOURLY | WeatherEntityFeature.FORECAST_DAILY
    )

    def __init__(
        self,
        coordinator: MeteoSwissDataUpdateCoordinator | OpenMeteoDataUpdateCoordinator,
        forecast_coordinator: MeteoSwissForecastCoordinator | None,
        entry: MeteoSwissConfigEntry,
        station_name: str,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._forecast_coordinator = forecast_coordinator
        self._forecast_target = resolve_forecast_target(entry.data, None, None)
        self._attr_device_info = weather_device_info(entry.entry_id, station_name)
        self._attr_name = None
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_weather"
        self._attr_native_temperature_unit = UnitOfTemperature.CELSIUS
        self._attr_native_pressure_unit = UnitOfPressure.HPA
        self._attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
        self._attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS

    async def async_added_to_hass(self) -> None:
        """Own both coordinator subscriptions for the entity's lifetime."""
        await super().async_added_to_hass()
        if self._forecast_coordinator:
            self.async_on_remove(
                self._forecast_coordinator.async_add_listener(
                    self._handle_forecast_update
                )
            )

    @callback
    def _handle_forecast_update(self) -> None:
        """Update current condition and push forecasts to active HA subscribers."""
        self.async_write_ha_state()
        self._entry.async_create_task(
            self.hass,
            self.async_update_listeners(("hourly", "daily")),
            "MeteoSwiss forecast listeners",
        )

    @property
    def coordinator_data(self) -> dict:
        """Only a successful observation source supplies current attributes."""
        if not self.coordinator or not self.coordinator.last_update_success:
            return {}
        data = self.coordinator.data
        return data if isinstance(data, dict) else {}

    @property
    def forecast_coordinator_data(self) -> list:
        """Retained failed/stale forecasts must not appear current."""
        source = self._forecast_coordinator
        if (
            not source
            or not source.last_update_success
            or not isinstance(source.data, list)
        ):
            return []
        data = source.data
        fetched_raw = next(
            (
                item.get("fetched_at")
                for item in data
                if isinstance(item, dict) and item.get("fetched_at") is not None
            ),
            None,
        )
        if fetched_raw is not None:
            fetched_at = forecast_datetime(fetched_raw)
            now = dt_util.utcnow()
            if (
                fetched_at is None
                or now - fetched_at > timedelta(hours=3)
                or fetched_at - now > timedelta(minutes=10)
            ):
                return []
        return data

    def _forecast_entries(self) -> Iterator[tuple[datetime, dict]]:
        """Skip invalid legacy entries without leaking raw payloads into logs."""
        for entry in self.forecast_coordinator_data[:120]:
            if not isinstance(entry, dict):
                continue
            if (timestamp := forecast_datetime(entry.get("datetime"))) is not None:
                yield timestamp, entry

    def _map_open_meteo_condition(self, weather_code: int | None) -> str | None:
        """Compatibility mapping; unknown input stays unknown."""
        return weather_condition(weather_code)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Explain an explicit forecast point without relabelling observations."""
        return self._forecast_target.state_attributes() or None

    def _current_forecast_condition(self) -> str | None:
        """A selected POI forecast must never become the home current condition."""
        if self._forecast_target.status != "legacy":
            return None
        now = dt_util.utcnow()
        for timestamp, item in self._forecast_entries():
            if timestamp <= now < timestamp + timedelta(hours=1) and (
                condition := _forecast(timestamp, item)["condition"]
            ):
                return condition
        return None

    def _resolve_condition(self) -> str | None:
        """Prefer current weather, then a current forecast interval, then rain."""
        current = self.coordinator_data
        if condition := _condition(current.get("weather_condition")):
            return condition
        for key in ("symbol", "icon", "condition"):
            symbol = current.get(key)
            if symbol and (
                condition := self.METEOSWISS_CONDITION_MAP.get(str(symbol).lower())
            ):
                return condition
        if condition := self._current_forecast_condition():
            return condition
        rain = weather_number(current.get(SENSOR_PRECIPITATION), 0)
        return "rainy" if rain is not None and rain > 0 else None

    @property
    def condition(self) -> str | None:
        return self._resolve_condition()

    @property
    def native_temperature(self) -> float | None:
        return weather_number(self.coordinator_data.get(SENSOR_TEMPERATURE))

    @property
    def humidity(self) -> float | None:
        return weather_number(self.coordinator_data.get(SENSOR_HUMIDITY), 0, 100)

    @property
    def native_pressure(self) -> float | None:
        return weather_number(self.coordinator_data.get(SENSOR_PRESSURE))

    @property
    def native_wind_speed(self) -> float | None:
        return weather_number(self.coordinator_data.get(SENSOR_WIND_SPEED), 0)

    @property
    def wind_bearing(self) -> float | None:
        return weather_number(self.coordinator_data.get(SENSOR_WIND_DIRECTION), 0, 360)

    @property
    def precipitation_unit(self) -> str:
        """Retain the old direct property; HA uses native_precipitation_unit."""
        return UnitOfPrecipitationDepth.MILLIMETERS

    @property
    def precipitation(self) -> float | None:
        """Compatibility value; not a fabricated hourly total or rate."""
        return weather_number(self.coordinator_data.get(SENSOR_PRECIPITATION), 0)

    async def async_forecast_hourly(self) -> list[Forecast]:
        """At most 24 valid temperatures in the current rolling 24-hour window."""
        now = dt_util.utcnow()
        end = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=24)
        return [
            _forecast(timestamp, entry)
            for timestamp, entry in self._forecast_entries()
            if timestamp + timedelta(hours=1) > now
            and timestamp < end
            and weather_number(entry.get("temperature")) is not None
        ][:24]

    async def async_forecast_daily(self) -> list[Forecast]:
        """Prefer provider calendar aggregates; never call missing rain zero."""
        today = dt_util.utcnow().astimezone(FORECAST_TIME_ZONE).date()
        days: dict[str, list[tuple[datetime, dict]]] = {}
        all_entries = list(self._forecast_entries())
        for timestamp, entry in all_entries:
            day = timestamp.astimezone(FORECAST_TIME_ZONE).date()
            if day >= today:
                days.setdefault(day.isoformat(), []).append((timestamp, entry))
        result = []
        for entries in list(days.values())[:5]:
            timestamp, representative = next(
                (
                    (stamp, item)
                    for stamp, item in entries
                    if 12 <= stamp.astimezone(FORECAST_TIME_ZONE).hour <= 14
                ),
                entries[0],
            )
            hourly = [item for _, item in entries]
            projected = _forecast(timestamp, representative)
            day = timestamp.astimezone(FORECAST_TIME_ZONE).date()
            temperatures = _whole_day_values(all_entries, day, "temperature")
            maxima = _known(hourly, "daily_temperature_max")
            minima = _known(hourly, "daily_temperature_min")
            projected["native_temperature"] = (
                maxima[0] if maxima else max(temperatures, default=None)
            )
            projected["native_templow"] = (
                minima[0] if minima else min(temperatures, default=None)
            )
            rain = _known(hourly, "daily_precipitation", 0)
            known_hourly_rain = _whole_day_values(
                all_entries, day, "precipitation", 0, interval_end=True
            )
            projected["native_precipitation"] = (
                rain[0]
                if rain
                else (
                    sum(known_hourly_rain)
                    if known_hourly_rain
                    else None
                )
            )
            probabilities = _known(hourly, "daily_precipitation_probability", 0, 100)
            projected["precipitation_probability"] = (
                probabilities[0]
                if probabilities
                else max(
                    _whole_day_values(
                        all_entries, day, "precipitation_probability", 0, 100,
                        interval_end=True,
                    ),
                    default=None,
                )
            )
            result.append(projected)
        return result

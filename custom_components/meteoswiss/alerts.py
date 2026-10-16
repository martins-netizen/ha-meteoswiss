"""MeteoSwiss Alerts Module using MeteoSwiss App API."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any

import aiohttp

from .const import DEFAULT_API_TIMEOUT
from .retry import async_retry_with_backoff
from .weather_data import weather_number

_LOGGER = logging.getLogger(__name__)

# MeteoSwiss App API
METEOSWISS_APP_API_URL = "https://app-prod-ws.meteoswiss-app.ch/v1/plzDetail"

# Proposed App API labels; provider-code verification is pending.
# See docs/WARNING_CODES.md. This branch is not approved for deployment.
WARN_TYPE_WIND = 0
WARN_TYPE_THUNDERSTORM = 1
WARN_TYPE_RAIN = 2
WARN_TYPE_SNOW = 3
WARN_TYPE_SLIPPERY_ROADS = 4
WARN_TYPE_GROUND_FROST = 5
WARN_TYPE_HEAT = 7
WARN_TYPE_AVALANCHES = 8
WARN_TYPE_EARTHQUAKES = 9
WARN_TYPE_FOREST_FIRE = 10
WARN_TYPE_FLOOD = 11
WARN_TYPE_DROUGHT = 12

# Warning levels
WARN_LEVEL_1 = 1  # No or minor danger
WARN_LEVEL_2 = 2  # Moderate danger
WARN_LEVEL_3 = 3  # Significant danger
WARN_LEVEL_4 = 4  # High danger
WARN_LEVEL_5 = 5  # Very high danger


def _warning_integer(raw: Any) -> int:
    """Reject boolean, fractional and non-finite provider codes."""
    value = weather_number(raw, 0)
    if value is None or not value.is_integer():
        raise ValueError("Invalid weather-warning integer")
    return int(value)


def _warning_timestamp(raw: Any) -> datetime | None:
    """Missing bounds stay missing; epoch zero is a real timestamp."""
    if raw is None:
        return None
    value = weather_number(raw)
    if value is None:
        raise ValueError("Invalid weather-warning time")
    return datetime.fromtimestamp(value / 1000, tz=UTC)


@dataclass
class WeatherAlert:
    """Weather alert from MeteoSwiss."""

    alert_id: str
    warn_type: int
    warn_type_name: str
    warn_level: int
    warn_level_name: str
    title: str
    description: str
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    outlook: bool = False

    def is_active(self) -> bool:
        """Check whether the alert is valid at the current time."""
        if self.outlook:
            return False

        now = datetime.now(UTC)

        if self.valid_from is not None and now < self.valid_from:
            return False

        return self.valid_to is None or now <= self.valid_to

    def is_upcoming(self) -> bool:
        """Check whether a published alert starts in the future."""
        if self.outlook or self.valid_from is None:
            return False

        now = datetime.now(UTC)
        if now >= self.valid_from:
            return False

        # Ignore malformed windows that end before they start.
        return self.valid_to is None or self.valid_to >= self.valid_from

    def is_critical(self) -> bool:
        """Check if alert is critical (level 3 or above)."""
        return self.warn_level >= WARN_LEVEL_3

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        # Convert datetime to ISO strings
        if self.valid_from:
            data["valid_from"] = self.valid_from.isoformat()
        if self.valid_to:
            data["valid_to"] = self.valid_to.isoformat()
        return data

    def to_sensor_state(self) -> str:
        """Convert to sensor state."""
        if self.outlook:
            return "outlook"

        if self.is_upcoming():
            return "upcoming"

        if self.is_active():
            if self.is_critical():
                return "critical"
            return "warning"

        return "clear"


class MeteoSwissAlertsAPI:
    """MeteoSwiss App API for weather warnings."""

    def __init__(self, session: aiohttp.ClientSession | None = None) -> None:
        """Initialize."""
        self._session = session

    async def get_alerts(
        self,
        postal_code: str,
    ) -> list[WeatherAlert]:
        """Get weather alerts for a postal code.

        Args:
            postal_code: Swiss postal code (e.g., "8001")

        Returns:
            List of weather alerts
        """
        if self._session is None:
            raise RuntimeError("No session provided")

        # Only an empty successful result means no warnings. Propagate errors
        # so Home Assistant cannot mistake an unavailable feed for an all-clear.
        if not postal_code:
            raise ValueError("A postal code is required for weather warnings")
        url = f"{METEOSWISS_APP_API_URL}?plz={postal_code}00"
        async with asyncio.timeout(DEFAULT_API_TIMEOUT.total):
            return await self._fetch_and_parse_alerts(url, postal_code)

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _fetch_and_parse_alerts(self, url: str, postal_code: str) -> list:
        """Fetch and parse alerts from API with retry logic."""
        _LOGGER.debug("Fetching weather warnings")

        async with self._session.get(url, timeout=DEFAULT_API_TIMEOUT) as response:
            response.raise_for_status()
            data = await response.json()
            return self._parse_alerts(data, postal_code)

    def _parse_alerts(
        self, data: dict[str, Any], postal_code: str
    ) -> list[WeatherAlert]:
        """Parse alerts from API response.

        The API returns data with optional 'warnings' field.
        The warnings field can be either a list (multiple alerts) or a dict (single alert).
        """
        alerts: list[WeatherAlert] = []

        if not isinstance(data, dict):
            raise ValueError("Expected a weather-warning response object")

        # Check for warnings field
        if "warnings" not in data:
            _LOGGER.debug("No warnings field in response")
            return alerts

        warnings_data = data["warnings"]

        if warnings_data is None or warnings_data == []:
            _LOGGER.debug("No warnings in response")
            return alerts

        # Handle both list and dict format
        if isinstance(warnings_data, list):
            # Multiple alerts
            for warning in warnings_data:
                if not isinstance(warning, dict):
                    raise ValueError("Invalid weather-warning entry")
                alert = self._parse_single_alert(warning, postal_code)
                if alert is None:
                    raise ValueError("Could not decode a published weather warning")
                alerts.append(alert)
        elif isinstance(warnings_data, dict):
            # Single alert
            alert = self._parse_single_alert(warnings_data, postal_code)
            if alert is None:
                raise ValueError("Could not decode a published weather warning")
            alerts.append(alert)
        else:
            raise ValueError("Unexpected weather-warning format")

        return alerts

    def _parse_single_alert(
        self, warning_data: dict[str, Any], postal_code: str
    ) -> WeatherAlert | None:
        """Parse a single alert from warning data.

        Args:
            warning_data: Single alert data (dict)
            postal_code: Postal code for alert ID generation

        Returns:
            WeatherAlert object or None if parsing fails
        """
        try:
            # Parse warning text (HTML or text format)
            warning_text = warning_data.get("text", "")
            if not isinstance(warning_text, str):
                raise ValueError("Invalid weather-warning text")

            # Parse warning level
            warn_level = _warning_integer(warning_data["warnLevel"])
            if not 1 <= warn_level <= 5:
                raise ValueError("Invalid weather-warning level")

            # Parse warning type
            warn_type = _warning_integer(warning_data["warnType"])

            # Parse valid from/to (Unix timestamps)
            valid_from_ts = warning_data.get("validFrom")
            valid_to_ts = warning_data.get("validTo")

            valid_from = _warning_timestamp(valid_from_ts)
            valid_to = _warning_timestamp(valid_to_ts)

            if valid_from and valid_to and valid_to < valid_from:
                raise ValueError("Weather-warning end precedes its start")

            # Parse outlook flag
            outlook = warning_data.get("outlook", False)
            if not isinstance(outlook, bool):
                raise ValueError("Invalid weather-warning outlook flag")

            # Generate alert ID
            alert_id = f"{postal_code}_{warn_level}_{warn_type}_{valid_from_ts if valid_from_ts is not None else 'now'}"

            # Create alert
            alert = WeatherAlert(
                alert_id=alert_id,
                warn_type=warn_type,
                warn_type_name=self._get_warn_type_name(warn_type),
                warn_level=warn_level,
                warn_level_name=self._get_warn_level_name(warn_level),
                title=f"{self._get_warn_type_name(warn_type)} - {self._get_warn_level_name(warn_level)}",
                description=warning_text,
                valid_from=valid_from,
                valid_to=valid_to,
                outlook=outlook,
            )

            return alert

        except (KeyError, TypeError, ValueError, OverflowError, OSError) as err:
            _LOGGER.debug("Invalid published weather warning (%s)", type(err).__name__)
            return None

    @staticmethod
    def _get_warn_type_name(warn_type: int) -> str:
        """Get warning type name."""
        warn_type_names = {
            WARN_TYPE_THUNDERSTORM: "Thunderstorm",
            WARN_TYPE_RAIN: "Rain",
            WARN_TYPE_SNOW: "Snow",
            WARN_TYPE_WIND: "Wind",
            WARN_TYPE_SLIPPERY_ROADS: "Slippery Roads",
            WARN_TYPE_GROUND_FROST: "Ground Frost",
            WARN_TYPE_HEAT: "Heat",
            WARN_TYPE_AVALANCHES: "Avalanches",
            WARN_TYPE_EARTHQUAKES: "Earthquakes",
            WARN_TYPE_FOREST_FIRE: "Forest Fire",
            WARN_TYPE_FLOOD: "Flood",
            WARN_TYPE_DROUGHT: "Drought",
        }
        return warn_type_names.get(warn_type, f"Unknown ({warn_type})")

    @staticmethod
    def _get_warn_level_name(warn_level: int) -> str:
        """Get warning level name."""
        warn_level_names = {
            WARN_LEVEL_1: "Level 1 - No/minor danger",
            WARN_LEVEL_2: "Level 2 - Moderate danger",
            WARN_LEVEL_3: "Level 3 - Significant danger",
            WARN_LEVEL_4: "Level 4 - High danger",
            WARN_LEVEL_5: "Level 5 - Very high danger",
        }
        return warn_level_names.get(warn_level, f"Level {warn_level}")

    async def close(self) -> None:
        """Close is handled centrally by the integration setup."""
        # Home Assistant owns the borrowed session.

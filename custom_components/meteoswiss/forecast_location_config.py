"""Versioned saved forecast location and explicit, compatible target resolution."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from .const import CONF_FORECAST_LOCATION
from .forecast_locations import (
    FORECAST_CATALOGUE_URL,
    FORECAST_LOCATION_PROVIDER,
    ForecastLocation,
    ForecastPoint,
    ForecastPointType,
)

LOCATION_SCHEMA_VERSION = 1
LOCATION_CRS = "EPSG:4326"
_FIELDS = frozenset(
    {
        "schema_version",
        "provider",
        "source_url",
        "point_type",
        "point_id",
        "name",
        "latitude",
        "longitude",
        "altitude_masl",
        "station_abbr",
        "postal_code",
        "crs",
        "catalogue_sha256",
        "catalogue_retrieved_at",
    }
)


class InvalidForecastLocation(ValueError):
    """Saved selection is invalid; never include its private raw fields."""


@dataclass(frozen=True, slots=True)
class ForecastTarget:
    """Resolved forecast-only request; legacy and invalid are distinct states."""

    status: Literal["legacy", "catalogue", "invalid"]
    latitude: float | None
    longitude: float | None
    elevation: float | None = None
    location: ForecastLocation | None = None

    @property
    def elevation_mode(self) -> str:
        if self.status == "invalid":
            return "unavailable"
        return "catalogue" if self.elevation is not None else "automatic_dem"

    def state_attributes(self) -> dict[str, Any]:
        """Identify the forecast point locally; diagnostics use status only."""
        if self.status == "legacy":
            return {}
        metadata: dict[str, Any] = {
            "status": self.status,
            "elevation_mode": self.elevation_mode,
        }
        if self.location is not None:
            point = self.location.point
            metadata.update(
                name=point.name,
                type=point.point_type.name.lower(),
                altitude_masl=point.altitude_masl,
            )
        return {"forecast_location": metadata}


def _text(value: Any, maximum: int) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= maximum:
        raise InvalidForecastLocation()
    if value != value.strip() or any(
        ord(char) < 32 or 127 <= ord(char) < 160 for char in value
    ):
        raise InvalidForecastLocation()
    return value


def _optional_text(value: Any, maximum: int) -> str | None:
    return None if value is None else _text(value, maximum)


def _number(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InvalidForecastLocation()
    number = float(value)
    if not math.isfinite(number):
        raise InvalidForecastLocation()
    return number


def _point(data: Mapping[str, Any]) -> ForecastPoint:
    point_type = ForecastPointType(_text(data["point_type"], 1))
    station = _optional_text(data["station_abbr"], 64)
    postal_code = _optional_text(data["postal_code"], 4)
    if (point_type == ForecastPointType.STATION) != bool(station):
        raise InvalidForecastLocation()
    if (point_type == ForecastPointType.POSTAL_CODE) != bool(postal_code):
        raise InvalidForecastLocation()
    if postal_code and not re.fullmatch(r"[0-9]{4}", postal_code):
        raise InvalidForecastLocation()
    latitude, longitude = _number(data["latitude"]), _number(data["longitude"])
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise InvalidForecastLocation()
    height = data["altitude_masl"]
    return ForecastPoint(
        point_type=point_type,
        point_id=_text(data["point_id"], 64),
        name=_text(data["name"], 256),
        latitude=latitude,
        longitude=longitude,
        altitude_masl=None if height is None else _number(height),
        station_abbr=station,
        postal_code=postal_code,
    )


def _decode(raw: Any) -> ForecastLocation:
    if not isinstance(raw, Mapping) or set(raw) != _FIELDS:
        raise InvalidForecastLocation()
    if (
        type(raw["schema_version"]) is not int
        or raw["schema_version"] != LOCATION_SCHEMA_VERSION
    ):
        raise InvalidForecastLocation()
    if (
        raw["provider"] != FORECAST_LOCATION_PROVIDER
        or raw["source_url"] != FORECAST_CATALOGUE_URL
        or raw["crs"] != LOCATION_CRS
    ):
        raise InvalidForecastLocation()
    digest = _text(raw["catalogue_sha256"], 64)
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        raise InvalidForecastLocation()
    retrieved_at = datetime.fromisoformat(_text(raw["catalogue_retrieved_at"], 64))
    if retrieved_at.tzinfo is None:
        raise InvalidForecastLocation()
    return ForecastLocation(_point(raw), digest, retrieved_at.astimezone(UTC))


def decode_forecast_location(raw: Any) -> ForecastLocation:
    """Read an offline selection without catalogue/network access or raw errors."""
    try:
        return _decode(raw)
    except (ValueError, TypeError, KeyError, OverflowError):
        raise InvalidForecastLocation() from None


def encode_forecast_location(location: ForecastLocation) -> dict[str, Any]:
    """Return detached JSON data; revalidate even manually constructed records."""
    point = location.point
    data = {
        "schema_version": LOCATION_SCHEMA_VERSION,
        "provider": location.provider,
        "source_url": location.source_url,
        "point_type": str(point.point_type),
        "point_id": point.point_id,
        "name": point.name,
        "latitude": point.latitude,
        "longitude": point.longitude,
        "altitude_masl": point.altitude_masl,
        "station_abbr": point.station_abbr,
        "postal_code": point.postal_code,
        "crs": LOCATION_CRS,
        "catalogue_sha256": location.catalogue_sha256,
        "catalogue_retrieved_at": location.catalogue_retrieved_at.isoformat(),
    }
    decode_forecast_location(data)
    return data


def resolve_forecast_target(
    data: Mapping[str, Any], latitude: float | None, longitude: float | None
) -> ForecastTarget:
    """Preserve legacy coordinates; never silently substitute for invalid saved data."""
    if CONF_FORECAST_LOCATION not in data:
        return ForecastTarget("legacy", latitude, longitude)
    try:
        location = decode_forecast_location(data[CONF_FORECAST_LOCATION])
    except InvalidForecastLocation:
        return ForecastTarget("invalid", None, None)
    point = location.point
    return ForecastTarget(
        "catalogue", point.latitude, point.longitude, point.altitude_masl, location
    )

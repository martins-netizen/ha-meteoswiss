"""Pure official forecast-point identity, catalogue parsing and local search."""

from __future__ import annotations

import csv
import hashlib
import io
import math
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from .http import MAX_CATALOGUE_BYTES

FORECAST_CATALOGUE_URL = (
    "https://data.geo.admin.ch/ch.meteoschweiz.ogd-local-forecasting/"
    "ogd-local-forecasting_meta_point.csv"
)
FORECAST_LOCATION_PROVIDER = "meteoswiss_ogd_local_forecast"
CATALOGUE_COLUMNS = (
    "point_id",
    "point_type_id",
    "station_abbr",
    "postal_code",
    "point_name",
    "point_type_de",
    "point_type_fr",
    "point_type_it",
    "point_type_en",
    "point_height_masl",
    "point_coordinates_lv95_east",
    "point_coordinates_lv95_north",
    "point_coordinates_wgs84_lat",
    "point_coordinates_wgs84_lon",
)


class ForecastPointType(StrEnum):
    """Provider types; a generic POI does not prove a summit/pass/hut subtype."""

    STATION = "1"
    POSTAL_CODE = "2"
    POINT_OF_INTEREST = "3"


class InvalidForecastCatalogue(ValueError):
    """Invalid catalogue, without including raw fields or source payloads."""


@dataclass(frozen=True, slots=True)
class ForecastPoint:
    """Public point metadata; the opaque ID is unique only within its type."""

    point_type: ForecastPointType
    point_id: str
    name: str
    latitude: float
    longitude: float
    altitude_masl: float | None
    station_abbr: str | None
    postal_code: str | None

    @property
    def identity(self) -> tuple[ForecastPointType, str]:
        return self.point_type, self.point_id


@dataclass(frozen=True, slots=True)
class ForecastLocation:
    """Explicitly selected point with catalogue provenance, not HA config yet."""

    point: ForecastPoint
    catalogue_sha256: str
    catalogue_retrieved_at: datetime
    source_url: str = FORECAST_CATALOGUE_URL
    provider: str = FORECAST_LOCATION_PROVIDER


@dataclass(frozen=True, slots=True)
class ForecastCatalogue:
    """Atomic immutable snapshot; hash identifies bytes, not provider issuance."""

    points: tuple[ForecastPoint, ...]
    sha256: str
    retrieved_at: datetime
    duplicate_rows: int

    def select(
        self, point_type: ForecastPointType, point_id: str
    ) -> ForecastLocation | None:
        """Resolve only the exact composite identity; never a nearest/name match."""
        for point in self.points:
            if point.identity == (point_type, point_id):
                return ForecastLocation(point, self.sha256, self.retrieved_at)
        return None


@dataclass(frozen=True, slots=True)
class ForecastSearchResult:
    """Bounded candidate list plus the full match count; selection stays explicit."""

    points: tuple[ForecastPoint, ...]
    total_matches: int

    @property
    def truncated(self) -> bool:
        return len(self.points) < self.total_matches


def _clean(value: str) -> str:
    if any(ord(char) < 32 or 127 <= ord(char) < 160 for char in value):
        raise InvalidForecastCatalogue()
    return value.strip()


def _number(value: str) -> float:
    number = float(value)
    if not math.isfinite(number):
        raise InvalidForecastCatalogue()
    return number


def _point(row: dict[str, str]) -> ForecastPoint:
    """Validate all named coordinates and each type's declared location role."""
    values = {key: _clean(value) for key, value in row.items()}
    point_type = ForecastPointType(values["point_type_id"])
    point_id, name = values["point_id"], values["point_name"]
    if not point_id or len(point_id) > 64 or not name or len(name) > 256:
        raise InvalidForecastCatalogue()
    station, postal_code = values["station_abbr"], values["postal_code"]
    if (point_type == ForecastPointType.STATION) != bool(station):
        raise InvalidForecastCatalogue()
    if (point_type == ForecastPointType.POSTAL_CODE) != bool(postal_code):
        raise InvalidForecastCatalogue()
    if postal_code and not re.fullmatch(r"[0-9]{4}", postal_code):
        raise InvalidForecastCatalogue()
    latitude = _number(values["point_coordinates_wgs84_lat"])
    longitude = _number(values["point_coordinates_wgs84_lon"])
    if not -90 <= latitude <= 90 or not -180 <= longitude <= 180:
        raise InvalidForecastCatalogue()
    # Validate the declared LV95 columns, without claiming a CRS cross-check.
    _number(values["point_coordinates_lv95_east"])
    _number(values["point_coordinates_lv95_north"])
    altitude = values["point_height_masl"]
    return ForecastPoint(
        point_type,
        point_id,
        name,
        latitude,
        longitude,
        _number(altitude) if altitude else None,
        station or None,
        postal_code or None,
    )


def _parse_points(
    rows: Iterable[list[str]], headers: list[str]
) -> tuple[tuple[ForecastPoint, ...], int]:
    """Collapse only full-row duplicates; a conflicting snapshot is atomic failure."""
    seen: dict[tuple[ForecastPointType, str], dict[str, str]] = {}
    points: list[ForecastPoint] = []
    duplicates = 0
    for fields in rows:
        if not fields:
            continue
        if len(fields) != len(headers):
            raise InvalidForecastCatalogue()
        row = dict(zip(headers, fields, strict=True))
        point = _point(row)
        previous = seen.get(point.identity)
        if previous is not None:
            if previous != row:
                raise InvalidForecastCatalogue()
            duplicates += 1
            continue
        seen[point.identity] = row
        points.append(point)
    if not points:
        raise InvalidForecastCatalogue()
    return tuple(points), duplicates


def _parse(content: bytes, retrieved_at: datetime) -> ForecastCatalogue:
    if not isinstance(content, bytes) or len(content) > MAX_CATALOGUE_BYTES:
        raise InvalidForecastCatalogue()
    if retrieved_at.tzinfo is None or retrieved_at.utcoffset() is None:
        raise InvalidForecastCatalogue()
    rows = csv.reader(
        io.StringIO(content.decode("latin-1"), newline=""), delimiter=";", strict=True
    )
    headers = next(rows, [])
    if len(headers) != len(CATALOGUE_COLUMNS) or set(headers) != set(CATALOGUE_COLUMNS):
        raise InvalidForecastCatalogue()
    points, duplicates = _parse_points(rows, headers)
    return ForecastCatalogue(
        points,
        hashlib.sha256(content).hexdigest(),
        retrieved_at.astimezone(UTC),
        duplicates,
    )


def parse_forecast_catalogue(
    content: bytes, retrieved_at: datetime
) -> ForecastCatalogue:
    """Apply the Latin1/semicolon contract; expose no invalid field in errors."""
    try:
        return _parse(content, retrieved_at)
    except (csv.Error, ValueError, TypeError):
        raise InvalidForecastCatalogue() from None


def _fold(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(re.findall(r"[^\W_]+", plain))


def _name_forms(point: ForecastPoint) -> tuple[str, str]:
    name = point.name.casefold()
    expanded = name.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    return _fold(name), _fold(expanded)


def _matches(point: ForecastPoint, query: str) -> bool:
    if query.isdecimal():
        return point.postal_code == query
    fields = (
        *_name_forms(point),
        _fold(point.station_abbr or ""),
        point.postal_code or "",
    )
    return all(any(token in field for field in fields) for token in query.split())


def _rank(point: ForecastPoint, query: str) -> tuple:
    names = _name_forms(point)
    if query in names:
        rank = 0
    elif any(name.startswith(query) for name in names):
        rank = 1
    else:
        rank = 2
    return rank, names[0], point.point_type, point.point_id


def search_forecast_locations(
    catalogue: ForecastCatalogue, query: str, *, limit: int = 20
) -> ForecastSearchResult:
    """Search public fields locally; return candidates, never an automatic choice."""
    if not isinstance(query, str) or len(query) > 128:
        raise ValueError("Invalid location search")
    if type(limit) is not int or not 1 <= limit <= 50:
        raise ValueError("Invalid location search limit")
    normal = _fold(query)
    if len(normal) < 2 or normal.isdecimal() and not re.fullmatch(r"[0-9]{4}", normal):
        return ForecastSearchResult((), 0)
    matches = [point for point in catalogue.points if _matches(point, normal)]
    matches.sort(key=lambda point: _rank(point, normal))
    return ForecastSearchResult(tuple(matches[:limit]), len(matches))

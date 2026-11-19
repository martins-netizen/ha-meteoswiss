"""Official station HGT products: bounded source reads and UTC period values."""

from __future__ import annotations

import csv
import io
import json
import math
import re
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import aiohttp

from .const import API_BASE, DOMAIN, STAC_COLLECTION
from .http import (
    MAX_CSV_BYTES,
    MAX_JSON_BYTES,
    OGD_HOST,
    CachedResource,
    async_get_resource,
)
from .retry import async_retry_with_backoff

if TYPE_CHECKING:
    from homeassistant.components.recorder.models import StatisticData
    from homeassistant.core import HomeAssistant

PERIODS = {"daily": "xno000d0", "monthly": "xno000m0", "annual": "xno000y0"}
MAX_POINTS = 100_000
REFRESH_INTERVAL = timedelta(hours=6)
HISTORY_INTERVAL = timedelta(days=7)
UNIT = "°C·d"
type HgtValues = dict[datetime, int | None]
type HgtProducts = dict[str, HgtValues]


class HgtError(Exception):
    """A fixed public category; never include provider payloads or private paths."""


def station_code(value: str) -> str:
    """Accept only the station identity used by SMN source filenames."""
    if not isinstance(value, str) or re.fullmatch(r"[a-zA-Z0-9]{3}", value) is None:
        raise HgtError("invalid_station")
    return value.lower()


def statistic_ids(station: str) -> dict[str, str]:
    return {
        period: f"{DOMAIN}:{station_code(station)}_hgt_12_20_{period}"
        for period in PERIODS
    }


def period_end(start: datetime, period: str) -> datetime:
    """The source timestamp starts the UTC day/month/year, without a DST shift."""
    if period == "daily":
        return start + timedelta(days=1)
    if period == "monthly":
        return start.replace(
            year=start.year + (start.month == 12), month=start.month % 12 + 1
        )
    return start.replace(year=start.year + 1)


def parse_hgt(content: bytes, station: str, period: str, now: datetime) -> HgtValues:
    """Keep explicit missing values, real zeroes and only completed periods."""
    parameter = PERIODS[period]
    text = content.decode(
        "utf-8-sig" if content.startswith(b"\xef\xbb\xbf") else "cp1252"
    )
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    required = {"station_abbr", "reference_timestamp", parameter}
    if (
        reader.fieldnames is None
        or len(reader.fieldnames) != len(set(reader.fieldnames))
        or not required <= set(reader.fieldnames)
    ):
        raise HgtError("invalid_source")
    values: HgtValues = {}
    for index, row in enumerate(reader):
        if index >= MAX_POINTS:
            raise HgtError("invalid_source")
        if (point := _read_hgt_row(row, station, period, now)) is None:
            continue
        start, amount = point
        if start in values and values[start] != amount:
            raise HgtError("ambiguous_source")
        values[start] = amount
    return values


def _read_hgt_row(
    row: Mapping[str | None, object], station: str, period: str, now: datetime
) -> tuple[datetime, int | None] | None:
    """Validate one official interval without inferring missing observations."""
    station_field = row.get("station_abbr")
    timestamp = row.get("reference_timestamp")
    amount = row.get(PERIODS[period])
    if (
        None in row
        or not isinstance(station_field, str)
        or not isinstance(timestamp, str)
        or not isinstance(amount, str)
    ):
        raise HgtError("invalid_source")
    if station_field.strip().lower() != station:
        raise HgtError("foreign_station")
    start = datetime.strptime(timestamp.strip(), "%d.%m.%Y %H:%M").replace(tzinfo=UTC)
    if (
        start.hour
        or start.minute
        or (period != "daily" and start.day != 1)
        or (period == "annual" and start.month != 1)
    ):
        raise HgtError("invalid_source")
    end = period_end(start, period)
    if end > now:
        return None
    raw = amount.strip()
    if not raw:
        return start, None
    number = float(raw)
    if (
        not math.isfinite(number)
        or number < 0
        or number > (end - start).days * 1000
        or not math.isclose(number * 10, round(number * 10), rel_tol=0, abs_tol=1e-6)
    ):
        raise HgtError("invalid_source")
    return start, round(number * 10)


def project_hgt(values: HgtValues) -> list[StatisticData]:
    """Raw official period amount plus cumulative known amounts; never fill gaps."""
    total = 0
    rows: list[StatisticData] = []
    for start, amount in sorted(values.items()):
        if amount is not None:
            total += amount
            rows.append({"start": start, "state": amount / 10, "sum": total / 10})
    return rows


class MeteoSwissHgtClient:
    """Revalidate exact source assets; cache only validated station representations."""

    def __init__(self, session: aiohttp.ClientSession, station: str) -> None:
        self.session = session
        self.station = station_code(station)
        self.resources: dict[str, CachedResource] = {}
        self.history_checked: datetime | None = None

    @async_retry_with_backoff(max_attempts=4, base_delay=1, max_delay=10)
    async def _resource(self, url: str, budget: int) -> CachedResource:
        return await async_get_resource(
            self.session,
            url,
            host=OGD_HOST,
            max_bytes=budget,
            cached=self.resources.get(url),
        )

    async def async_fetch(self, hass: HomeAssistant, now: datetime) -> HgtProducts:
        """Load all declared products before callers are allowed to change Recorder."""
        metadata_url = f"{API_BASE}/collections/{STAC_COLLECTION}/items/{self.station}"
        resource = await self._resource(metadata_url, MAX_JSON_BYTES)
        metadata = json.loads(resource.body)
        if (
            not isinstance(metadata, dict)
            or metadata.get("id") != self.station
            or not isinstance(metadata.get("assets"), dict)
        ):
            raise HgtError("invalid_source")
        self.resources[metadata_url] = resource
        result: HgtProducts = {p: {} for p in PERIODS}
        history_due = (
            self.history_checked is None
            or self.history_checked.year != now.year
            or now - self.history_checked >= HISTORY_INTERVAL
        )
        for suffix, period in [
            ("d_historical", "daily"),
            ("d_recent", "daily"),
            ("m", "monthly"),
            ("y", "annual"),
        ]:
            key = f"ogd-smn_{self.station}_{suffix}.csv"
            url = f"https://{OGD_HOST}/{STAC_COLLECTION}/{self.station}/{key}"
            asset = metadata["assets"].get(key)
            if not isinstance(asset, dict) or asset.get("href") != url:
                raise HgtError("source_incomplete")
            previous = self.resources.get(url)
            item = (
                previous
                if suffix == "d_historical" and not history_due and previous is not None
                else await self._resource(url, MAX_CSV_BYTES)
            )
            # Re-evaluate completed periods even after 304 or a UTC/year boundary.
            values = await hass.async_add_executor_job(
                parse_hgt, item.body, self.station, period, now
            )
            # Recent rows deliberately override history, including withdrawals.
            result[period].update(values)
            self.resources[url] = item
        if not any(v is not None for v in result["daily"].values()):
            raise HgtError("data_unavailable")
        if history_due:
            self.history_checked = now
        return result

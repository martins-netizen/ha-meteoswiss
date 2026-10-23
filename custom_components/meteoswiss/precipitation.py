"""Bounded official hourly precipitation source and pure amount parsing."""

from __future__ import annotations

import calendar
import csv
import io
import math
import re
from datetime import UTC, datetime, timedelta
from typing import Any, TypedDict

import aiohttp

from .const import API_BASE, STAC_COLLECTION
from .http import (
    MAX_ARCHIVE_BYTES,
    MAX_CSV_BYTES,
    OGD_HOST,
    async_get_bytes,
    async_get_json,
)
from .retry import async_retry_with_backoff
from .weather_data import parse_reference_timestamp

PARAM_PRECIPITATION_HOURLY = "rre150h0"
HOURLY_UPDATE_INTERVAL = timedelta(hours=1)
ARCHIVE_UPDATE_INTERVAL = timedelta(days=7)
ARCHIVE_LOOKBACK_MONTHS = 13


class HourlyPrecipitationValue(TypedDict):
    """One source amount, independent of Home Assistant statistics metadata."""

    start: datetime
    amount: float


def _asset_urls_for_period(
    assets: dict[str, Any],
    station_id: str,
    period: str,
    earliest_year: int | None = None,
) -> list[str]:
    """Return matching hourly asset URLs for a period."""
    prefix = f"ogd-smn_{station_id}_h_{period}"
    if period != "historical":
        asset = assets.get(f"{prefix}.csv")
        href = asset.get("href") if isinstance(asset, dict) else None
        return [href] if isinstance(href, str) and href.strip() else []

    historical_pattern = re.compile(rf"^{re.escape(prefix)}_(\d{{4}})-(\d{{4}})\.csv$")
    matches: list[tuple[int, str]] = []
    for asset_key, asset in assets.items():
        match = historical_pattern.fullmatch(asset_key)
        href = asset.get("href") if isinstance(asset, dict) else None
        if match is None or not isinstance(href, str) or not href.strip():
            continue
        start_year, end_year = (int(year) for year in match.groups())
        if earliest_year is None or end_year >= earliest_year:
            matches.append((start_year, href))

    return [href for _, href in sorted(matches)]


def _subtract_calendar_months(value: datetime, months: int) -> datetime:
    """Return the start of the day a number of calendar months earlier."""
    month_index = value.year * 12 + value.month - 1 - months
    year, zero_based_month = divmod(month_index, 12)
    month = zero_based_month + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(
        year=year,
        month=month,
        day=day,
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )


def parse_hourly_precipitation(
    content: str,
    earliest_start: datetime | None = None,
    station_id: str | None = None,
) -> list[HourlyPrecipitationValue]:
    """Normalize valid completed-hour amounts with UTC interval starts."""
    values_by_start: dict[datetime, float] = {}
    now = datetime.now(UTC)

    for row in csv.DictReader(io.StringIO(content), delimiter=";"):
        if (
            station_id is not None
            and (row.get("station_abbr") or "").strip().lower() != station_id.lower()
        ):
            continue
        reference = parse_reference_timestamp(row.get("reference_timestamp", ""))
        value = (row.get(PARAM_PRECIPITATION_HOURLY) or "").strip()
        if (
            reference is None
            or not value
            or reference > now
            or reference.minute
            or reference.second
            or reference.microsecond
        ):
            continue

        try:
            precipitation = float(value)
        except (TypeError, ValueError):
            continue

        if not math.isfinite(precipitation) or precipitation < 0:
            continue

        # MeteoSwiss timestamps mark the end of an aggregation interval;
        # Home Assistant statistics timestamps mark its start.
        start = reference - timedelta(hours=1)
        if earliest_start is not None and start < earliest_start:
            continue
        values_by_start[start] = precipitation

    return [
        {
            "start": start,
            "amount": value,
        }
        for start, value in sorted(values_by_start.items())
    ]


class PrecipitationSourceError(Exception):
    """A metadata/CSV source failed without exposing its URL or payload."""


class MeteoSwissHourlyPrecipitationClient:
    """Fetch station assets and CSV bytes with a borrowed session."""

    def __init__(
        self,
        station_id: str,
        session: aiohttp.ClientSession,
        *,
        asset_periods: tuple[str, ...] = ("now",),
    ) -> None:
        self.station_id = station_id.lower()
        self._session = session
        self.asset_periods = asset_periods

    async def async_get_urls(
        self, earliest_year: int | None = None
    ) -> dict[str, list[str]]:
        """Return requested metadata assets with a private error boundary."""
        try:
            return await self._async_get_hourly_urls(earliest_year)
        except (aiohttp.ClientError, TimeoutError, ValueError, TypeError):
            raise PrecipitationSourceError() from None

    async def async_get_csv(self, csv_url: str, period: str) -> str:
        """Return provider text; CSV validation is a separate pure operation."""
        try:
            return await self._async_download_hourly_csv(csv_url, period)
        except (aiohttp.ClientError, TimeoutError, ValueError, TypeError):
            raise PrecipitationSourceError() from None

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_get_hourly_urls(
        self,
        earliest_year: int | None = None,
    ) -> dict[str, list[str]]:
        """Return the requested station-specific hourly CSV URLs."""
        url = f"{API_BASE}/collections/{STAC_COLLECTION}/items/{self.station_id}"
        data = await async_get_json(self._session, url, host=OGD_HOST)
        if not isinstance(data, dict) or not isinstance(data.get("assets"), dict):
            raise TypeError("Invalid hourly station metadata")
        assets = data["assets"]
        urls: dict[str, list[str]] = {}
        for period in self.asset_periods:
            period_urls = _asset_urls_for_period(
                assets, self.station_id, period, earliest_year
            )
            if period_urls:
                urls[period] = period_urls
        return urls

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_download_hourly_csv(self, csv_url: str, period: str) -> str:
        """Retry transient HTTP failures; CSV validation belongs to the importer."""
        return (
            await async_get_bytes(
                self._session,
                csv_url,
                host=OGD_HOST,
                max_bytes=MAX_ARCHIVE_BYTES
                if period == "historical"
                else MAX_CSV_BYTES,
            )
        ).decode("cp1252")

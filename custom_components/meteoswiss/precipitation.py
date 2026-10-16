"""Official MeteoSwiss hourly precipitation statistics."""

from __future__ import annotations

import calendar
import csv
import io
import logging
import math
import re
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.const import UnitOfPrecipitationDepth
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_BASE, DEFAULT_API_TIMEOUT, DOMAIN, STAC_COLLECTION
from .coordinator import _parse_reference_timestamp
from .retry import async_retry_with_backoff

_LOGGER = logging.getLogger(__name__)

PARAM_PRECIPITATION_HOURLY = "rre150h0"
HOURLY_UPDATE_INTERVAL = timedelta(hours=1)
ARCHIVE_UPDATE_INTERVAL = timedelta(days=7)
ARCHIVE_LOOKBACK_MONTHS = 13


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


def _parse_hourly_statistics(
    content: str,
    earliest_start: datetime | None = None,
    station_id: str | None = None,
) -> list[StatisticData]:
    """Convert official hourly totals to Recorder statistics."""
    values_by_start: dict[datetime, float] = {}
    now = datetime.now(UTC)

    for row in csv.DictReader(io.StringIO(content), delimiter=";"):
        if (
            station_id is not None
            and (row.get("station_abbr") or "").strip().lower() != station_id.lower()
        ):
            continue
        reference = _parse_reference_timestamp(row.get("reference_timestamp", ""))
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
            "mean": value,
            "min": value,
            "max": value,
        }
        for start, value in sorted(values_by_start.items())
    ]


class MeteoSwissHourlyPrecipitationCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Import official, quality-controlled hourly precipitation totals."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        session: aiohttp.ClientSession,
        *,
        asset_periods: tuple[str, ...] = ("now",),
        update_interval: timedelta = HOURLY_UPDATE_INTERVAL,
        lookback_months: int | None = None,
    ) -> None:
        """Initialize the hourly precipitation coordinator."""
        self.station_id = station_id.lower()
        self._session = session
        self._asset_periods = asset_periods
        self._lookback_months = lookback_months
        self.statistic_id = f"{DOMAIN}:{self.station_id}_precipitation_hourly"
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_hourly_precipitation_{'_'.join(asset_periods)}",
            update_interval=update_interval,
        )

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_get_hourly_urls(
        self,
        earliest_year: int | None = None,
    ) -> dict[str, list[str]]:
        """Return the requested station-specific hourly CSV URLs."""
        url = f"{API_BASE}/collections/{STAC_COLLECTION}/items/{self.station_id}"
        async with self._session.get(url, timeout=DEFAULT_API_TIMEOUT) as response:
            response.raise_for_status()
            data = await response.json()
        if not isinstance(data, dict) or not isinstance(data.get("assets"), dict):
            raise TypeError("Invalid hourly station metadata")
        assets = data["assets"]
        urls: dict[str, list[str]] = {}
        for period in self._asset_periods:
            period_urls = _asset_urls_for_period(
                assets, self.station_id, period, earliest_year
            )
            if period_urls:
                urls[period] = period_urls
        return urls

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_download_hourly_csv(self, csv_url: str, period: str) -> str:
        """Retry transient HTTP failures; CSV validation belongs to the importer."""
        async with self._session.get(csv_url, timeout=DEFAULT_API_TIMEOUT) as response:
            response.raise_for_status()
            return await response.text(encoding="cp1252")

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch official hourly totals and queue them for Recorder import."""
        earliest_start = None
        if self._lookback_months is not None:
            earliest_start = _subtract_calendar_months(
                datetime.now(UTC),
                self._lookback_months,
            )

        try:
            csv_urls = await self._async_get_hourly_urls(
                earliest_start.year if earliest_start is not None else None
            )
        except (aiohttp.ClientError, TimeoutError, ValueError, TypeError):
            raise UpdateFailed("Hourly precipitation metadata unavailable") from None
        if not csv_urls:
            raise UpdateFailed("Could not find hourly precipitation URLs")

        statistics_by_start: dict[datetime, StatisticData] = {}
        imported_periods: list[str] = []
        failed_downloads = 0
        for period in self._asset_periods:
            period_urls = csv_urls.get(period)
            if period_urls is None:
                continue
            imported_period = False
            for csv_url in period_urls:
                try:
                    content = await self._async_download_hourly_csv(csv_url, period)
                    parsed = await self.hass.async_add_executor_job(
                        _parse_hourly_statistics,
                        content,
                        earliest_start,
                        self.station_id,
                    )
                except (
                    aiohttp.ClientError,
                    TimeoutError,
                    ValueError,
                    TypeError,
                    csv.Error,
                ):
                    failed_downloads += 1
                    continue
                for statistic in parsed:
                    statistics_by_start[statistic["start"]] = statistic
                imported_period = imported_period or bool(parsed)
            if imported_period:
                imported_periods.append(period)

        statistics = [
            statistics_by_start[start] for start in sorted(statistics_by_start)
        ]
        if not statistics:
            raise UpdateFailed("No valid hourly precipitation data")

        metadata: StatisticMetaData = {
            "mean_type": StatisticMeanType.ARITHMETIC,
            "has_sum": False,
            "name": f"MeteoSwiss {self.station_id.upper()} hourly precipitation",
            "source": DOMAIN,
            "statistic_id": self.statistic_id,
            "unit_class": "distance",
            "unit_of_measurement": UnitOfPrecipitationDepth.MILLIMETERS,
        }
        try:
            async_add_external_statistics(self.hass, metadata, statistics)
        except (ValueError, TypeError):
            raise UpdateFailed(
                "Could not queue hourly precipitation statistics"
            ) from None

        return {
            "statistic_id": self.statistic_id,
            "imported_hours": len(statistics),
            "imported_periods": imported_periods,
            "latest_start": statistics[-1]["start"].isoformat(),
            "failed_downloads": failed_downloads,
            "partial_import": bool(failed_downloads)
            or len(imported_periods) < len(self._asset_periods),
        }

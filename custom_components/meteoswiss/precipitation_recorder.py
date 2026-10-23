"""Recorder projection/import of validated official hourly precipitation."""

from __future__ import annotations

import csv
from datetime import UTC, datetime
from typing import Any

from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import async_add_external_statistics
from homeassistant.const import UnitOfPrecipitationDepth
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .precipitation import (
    HourlyPrecipitationValue,
    MeteoSwissHourlyPrecipitationClient,
    PrecipitationSourceError,
    _subtract_calendar_months,
    parse_hourly_precipitation,
)


class HourlyPrecipitationMetadataError(Exception):
    """The source metadata could not be read without leaking raw errors."""


class HourlyPrecipitationURLsMissing(Exception):
    """Valid metadata contained no requested hourly assets."""


class HourlyPrecipitationDataMissing(Exception):
    """No valid amounts are available to queue, including all-failed downloads."""


class HourlyPrecipitationQueueError(Exception):
    """Recorder rejected the queue request without leaking its raw error."""


class MeteoSwissPrecipitationImporter:
    """Merge source periods, project amounts and queue stable external statistics."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: MeteoSwissHourlyPrecipitationClient,
        *,
        asset_periods: tuple[str, ...],
        lookback_months: int | None,
    ) -> None:
        self.hass = hass
        self.client = client
        self.station_id = client.station_id
        self._asset_periods = asset_periods
        self._lookback_months = lookback_months
        self.statistic_id = f"{DOMAIN}:{self.station_id}_precipitation_hourly"

    async def _async_read_period(
        self, period: str, urls: list[str], earliest_start: datetime | None
    ) -> tuple[dict[datetime, HourlyPrecipitationValue], int]:
        """Keep valid files when another fails; parse CSV off the event loop."""
        values: dict[datetime, HourlyPrecipitationValue] = {}
        failed_downloads = 0
        for csv_url in urls:
            try:
                content = await self.client.async_get_csv(csv_url, period)
                parsed = await self.hass.async_add_executor_job(
                    parse_hourly_precipitation,
                    content,
                    earliest_start,
                    self.station_id,
                )
            except (PrecipitationSourceError, ValueError, TypeError, csv.Error):
                failed_downloads += 1
                continue
            for value in parsed:
                values[value["start"]] = value
        return values, failed_downloads

    async def _async_collect(
        self, csv_urls: dict[str, list[str]], earliest_start: datetime | None
    ) -> tuple[list[HourlyPrecipitationValue], list[str], int]:
        """Retain declared period order and later valid corrections per hour."""
        values_by_start: dict[datetime, HourlyPrecipitationValue] = {}
        imported_periods: list[str] = []
        failed_downloads = 0
        for period in self._asset_periods:
            period_urls = csv_urls.get(period)
            if period_urls is None:
                continue
            values, failed = await self._async_read_period(
                period, period_urls, earliest_start
            )
            values_by_start.update(values)
            failed_downloads += failed
            if values:
                imported_periods.append(period)
        return (
            [values_by_start[start] for start in sorted(values_by_start)],
            imported_periods,
            failed_downloads,
        )

    async def async_import(self) -> dict[str, Any]:
        """Queue the same mean/min/max series without manufacturing missing data."""
        earliest_start = None
        if self._lookback_months is not None:
            earliest_start = _subtract_calendar_months(
                datetime.now(UTC), self._lookback_months
            )
        try:
            csv_urls = await self.client.async_get_urls(
                earliest_start.year if earliest_start is not None else None
            )
        except PrecipitationSourceError:
            raise HourlyPrecipitationMetadataError() from None
        if not csv_urls:
            raise HourlyPrecipitationURLsMissing()
        values, imported_periods, failed_downloads = await self._async_collect(
            csv_urls, earliest_start
        )
        if not values:
            raise HourlyPrecipitationDataMissing()
        statistics: list[StatisticData] = [
            {
                "start": value["start"],
                "mean": value["amount"],
                "min": value["amount"],
                "max": value["amount"],
            }
            for value in values
        ]
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
            raise HourlyPrecipitationQueueError() from None
        return {
            "statistic_id": self.statistic_id,
            "imported_hours": len(statistics),
            "imported_periods": imported_periods,
            "latest_start": statistics[-1]["start"].isoformat(),
            "failed_downloads": failed_downloads,
            "partial_import": bool(failed_downloads)
            or len(imported_periods) < len(self._asset_periods),
        }

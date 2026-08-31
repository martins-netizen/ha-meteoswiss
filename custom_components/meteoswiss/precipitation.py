"""Official MeteoSwiss hourly precipitation statistics."""

from __future__ import annotations

import asyncio
import csv
import io
import logging
from datetime import datetime, timedelta
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

from .const import API_BASE, DOMAIN, STAC_COLLECTION
from .coordinator import _parse_reference_timestamp
from .retry import async_retry_with_backoff

_LOGGER = logging.getLogger(__name__)

PARAM_PRECIPITATION_HOURLY = "rre150h0"
HOURLY_UPDATE_INTERVAL = timedelta(hours=1)


def _parse_hourly_statistics(content: str) -> list[StatisticData]:
    """Convert official hourly totals to Recorder statistics."""
    values_by_start: dict[datetime, float] = {}

    for row in csv.DictReader(io.StringIO(content), delimiter=";"):
        reference = _parse_reference_timestamp(row.get("reference_timestamp", ""))
        value = (row.get(PARAM_PRECIPITATION_HOURLY) or "").strip()
        if reference is None or not value:
            continue

        try:
            precipitation = float(value)
        except (TypeError, ValueError):
            continue

        # MeteoSwiss timestamps mark the end of an aggregation interval;
        # Home Assistant statistics timestamps mark its start.
        values_by_start[reference - timedelta(hours=1)] = precipitation

    return [
        {
            "start": start,
            "mean": value,
            "min": value,
            "max": value,
        }
        for start, value in sorted(values_by_start.items())
    ]


class MeteoSwissHourlyPrecipitationCoordinator(
    DataUpdateCoordinator[dict[str, Any]]
):
    """Import official, quality-controlled hourly precipitation totals."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the hourly precipitation coordinator."""
        self.station_id = station_id.lower()
        self._session = session
        self.statistic_id = f"{DOMAIN}:{self.station_id}_precipitation_hourly"
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_hourly_precipitation",
            update_interval=HOURLY_UPDATE_INTERVAL,
        )

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_get_hourly_url(self) -> str | None:
        """Return the station-specific h_now CSV URL."""
        try:
            url = f"{API_BASE}/collections/{STAC_COLLECTION}/items/{self.station_id}"
            async with self._session.get(url) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to fetch hourly station info: %s", response.status
                    )
                    return None

                assets = (await response.json()).get("assets", {})

            asset_key = f"ogd-smn_{self.station_id}_h_now.csv"
            if asset_key not in assets:
                _LOGGER.warning("No h_now.csv found for station %s", self.station_id)
                return None
            return assets[asset_key].get("href")
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching hourly station info")
            return None

    @async_retry_with_backoff(max_attempts=4, base_delay=1.0, max_delay=10.0)
    async def _async_download_hourly_csv(self, csv_url: str) -> str | None:
        """Download the official hourly CSV."""
        try:
            async with self._session.get(csv_url) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Failed to download hourly CSV: %s", response.status
                    )
                    return None
                return await response.text()
        except asyncio.TimeoutError:
            _LOGGER.error("Timeout downloading hourly precipitation CSV")
            return None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch official hourly totals and queue them for Recorder import."""
        csv_url = await self._async_get_hourly_url()
        if not csv_url:
            raise UpdateFailed("Could not find hourly precipitation URL")

        content = await self._async_download_hourly_csv(csv_url)
        if content is None:
            raise UpdateFailed("Could not download hourly precipitation data")

        statistics = _parse_hourly_statistics(content)
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
        async_add_external_statistics(self.hass, metadata, statistics)

        return {
            "statistic_id": self.statistic_id,
            "imported_hours": len(statistics),
            "latest_start": statistics[-1]["start"].isoformat(),
        }

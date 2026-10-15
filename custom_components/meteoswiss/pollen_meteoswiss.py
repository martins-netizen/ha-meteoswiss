"""Pollen data coordinator using MeteoSwiss measured pollen data (ogd-pollen).

Fetches measured pollen concentrations from MeteoSwiss pollen stations
via the data.geo.admin.ch STAC API (ch.meteoschweiz.ogd-pollen).

Automatic stations across Switzerland provide hourly measured concentrations for:
  - Birch (Birke / Betula)
  - Alder (Erle / Alnus)
  - Hazel (Hasel / Corylus)
  - Beech (Buche / Fagus)
  - Common ash (Esche / Fraxinus)
  - Oak (Eiche / Quercus)
  - Grasses (Gräser / Poaceae)
  - Mugwort (Beifuss / Artemisia)
  - Ragweed (Ambrosia / Ambrosia)
  - Elm (Ulme / Ulmus)
  - Nettle (Nessel / Urtica)
  - Plantain (Wegerich / Plantago)
  - Sorrel (Sauerampfer / Rumex)

Data source: https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-pollen
"""

from __future__ import annotations

import csv
import io
import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_API_TIMEOUT, DOMAIN
from .coordinator import _parse_reference_timestamp
from .retry import async_retry_with_backoff

_LOGGER = logging.getLogger(__name__)

# STAC API for pollen collection
POLLEN_STAC_COLLECTION_URL = (
    "https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-pollen"
)
POLLEN_DATA_BASE_URL = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen"

# Hourly measurement end times, 20-minute publication and up to two-hour asset
# caching need their own policy, independent of the 10-minute weather feed.
# Four hours is our conservative acceptance window, not a provider SLA.
MAX_MEASUREMENT_AGE = timedelta(hours=4)
MAX_MEASUREMENT_FUTURE_SKEW = timedelta(minutes=10)

# Pollen parameter codes (MeteoSwiss naming convention)
# Format: ka{genus_abbrev}{time_resolution}{version}
POLLEN_PARAM_MAP: dict[str, str] = {
    # Common allergens → API column names (hourly data)
    "birch": "kabetuh0",  # Birke / Betula
    "alder": "kaalnuh0",  # Erle / Alnus
    "hazel": "kacoryh0",  # Hasel / Corylus
    "beech": "kafaguh0",  # Buche / Fagus
    "ash": "kafraxh0",  # Esche / Fraxinus
    "oak": "kaqueth0",  # Eiche / Quercus (if available)
    "grass": "khpoach0",  # Gräser / Poaceae
    "mugwort": "kaartuh0",  # Beifuss / Artemisia (if available)
    "ragweed": "kaambh0",  # Ambrosia (if available)
}

# All pollen types we track (matching the data columns actually present)
POLLEN_TRACKED = [
    "birch",
    "alder",
    "hazel",
    "beech",
    "ash",
    "grass",
]

# Mapping from our key → MeteoSwiss column name
# These are the columns typically present in the _h_now.csv files
POLLEN_CSV_COLUMNS: dict[str, str] = {
    "birch": "kabetuh0",
    "alder": "kaalnuh0",
    "hazel": "kacoryh0",
    "beech": "kafaguh0",
    "ash": "kafraxh0",
    "grass": "khpoach0",
}


def _count(raw: str | None) -> int | None:
    """Zero is a measurement; blank, invalid and negative counts are missing."""
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return None
    return value if value >= 0 else None


class MeteoSwissPollenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Class to manage fetching measured pollen data from MeteoSwiss."""

    def __init__(
        self,
        hass: HomeAssistant,
        station_id: str = "PBE",
        update_interval: int = 3600,  # 1 hour default
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        """Initialize."""
        self._station_id = station_id.lower()
        self._session = session

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_pollen_meteoswiss",
            update_interval=timedelta(seconds=update_interval),
        )

    @async_retry_with_backoff(max_attempts=3)
    async def _async_fetch_csv(self) -> str:
        """Retry only transient transport failures, before parsing the payload."""
        if self._session is None:
            raise RuntimeError(
                "No aiohttp session provided to MeteoSwissPollenCoordinator"
            )
        url = f"{POLLEN_DATA_BASE_URL}/{self._station_id}/ogd-pollen_{self._station_id}_h_now.csv"
        async with self._session.get(url, timeout=DEFAULT_API_TIMEOUT) as response:
            response.raise_for_status()
            return await response.text(encoding="cp1252")

    async def _async_update_data(self) -> dict[str, Any]:
        """A failed/invalid feed is unavailable, and a later valid feed recovers."""
        try:
            content = await self._async_fetch_csv()
        except (aiohttp.ClientError, TimeoutError, UnicodeError) as err:
            raise UpdateFailed("Measured pollen source unavailable") from err
        data = self._parse_csv(content)
        if not data:
            raise UpdateFailed("No valid measured pollen values")
        return data

    def _parse_csv(self, csv_text: str) -> dict[str, Any]:
        """Validate station/time and retain the existing output/history format."""
        rows = list(csv.DictReader(io.StringIO(csv_text), delimiter=";"))
        if not rows:
            return {}
        latest = rows[-1]
        timestamp = (latest.get("reference_timestamp") or "").strip()
        station = (latest.get("station_abbr") or "").strip().lower()
        measurement_time = _parse_reference_timestamp(timestamp)
        if station != self._station_id or measurement_time is None:
            return {}
        age = datetime.now(UTC) - measurement_time
        if age > MAX_MEASUREMENT_AGE or age < -MAX_MEASUREMENT_FUTURE_SKEW:
            return {}
        result: dict[str, Any] = {
            "station_id": self._station_id.upper(),
            "last_update": timestamp,
            "source": "MeteoSwiss ogd-pollen",
        }
        for pollen_key, column in POLLEN_CSV_COLUMNS.items():
            result[pollen_key] = {
                "current": _count(latest.get(column)),
                "unit": "No/m³",
                "source": "MeteoSwiss measured",
                "history_24h": [_count(row.get(column)) for row in rows[-24:]],
            }
        return (
            result
            if any(result[key]["current"] is not None for key in POLLEN_TRACKED)
            else {}
        )

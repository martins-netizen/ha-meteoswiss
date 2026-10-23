"""Lazy bounded official point-catalogue client, independent of HA objects."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from time import monotonic

import aiohttp

from .const import DEFAULT_API_TIMEOUT
from .forecast_locations import (
    FORECAST_CATALOGUE_URL,
    ForecastCatalogue,
    parse_forecast_catalogue,
)
from .http import MAX_CATALOGUE_BYTES, OGD_HOST, async_get_bytes
from .retry import async_retry_with_backoff

FORECAST_CATALOGUE_TTL = 86400.0
FORECAST_CATALOGUE_RETRY_DELAY = 300.0


class ForecastCatalogueUnavailable(Exception):
    """No current catalogue; hide raw HTTP, schema and request details."""


class MeteoSwissForecastCatalogueClient:
    """Borrow a session; coalesce requests and never silently return stale data."""

    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._session = session
        self._lock = asyncio.Lock()
        self._snapshot: ForecastCatalogue | None = None
        self._expires_at = 0.0
        self._retry_at = 0.0

    @property
    def last_good_snapshot(self) -> ForecastCatalogue | None:
        """Explicit fallback evidence, with original hash/time and possible age."""
        return self._snapshot

    @async_retry_with_backoff(max_attempts=3, base_delay=1.0, max_delay=10.0)
    async def _async_download(self) -> bytes:
        return await async_get_bytes(
            self._session,
            FORECAST_CATALOGUE_URL,
            host=OGD_HOST,
            max_bytes=MAX_CATALOGUE_BYTES,
        )

    async def async_get_catalogue(self) -> ForecastCatalogue:
        """Refresh only on demand; failed refresh cannot overwrite good metadata."""
        async with self._lock:
            now = monotonic()
            if self._snapshot is not None and now < self._expires_at:
                return self._snapshot
            if now < self._retry_at:
                raise ForecastCatalogueUnavailable()
            try:
                async with asyncio.timeout(DEFAULT_API_TIMEOUT.total):
                    content = await self._async_download()
                snapshot = await asyncio.to_thread(
                    parse_forecast_catalogue, content, datetime.now(UTC)
                )
            except (aiohttp.ClientError, TimeoutError, ValueError, TypeError):
                self._retry_at = monotonic() + FORECAST_CATALOGUE_RETRY_DELAY
                raise ForecastCatalogueUnavailable() from None
            self._snapshot = snapshot
            self._expires_at = monotonic() + FORECAST_CATALOGUE_TTL
            self._retry_at = 0.0
            return snapshot

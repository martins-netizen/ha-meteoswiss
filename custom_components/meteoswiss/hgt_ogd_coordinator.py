"""Entry-owned polling for shared, authoritative station HGT statistics."""

import logging
from datetime import UTC, datetime

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN
from .hgt_ogd import REFRESH_INTERVAL, HgtError, station_code
from .hgt_ogd_manager import get_hgt_manager
from .runtime_data import MeteoSwissConfigEntry

_LOGGER = logging.getLogger(__name__)
_INITIAL_RETRY_SECONDS = 60
_MAX_RETRY_SECONDS = 15 * 60


class MeteoSwissHgtCoordinator(DataUpdateCoordinator[dict]):
    """No new source coordinates, sessions or provider credentials."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: MeteoSwissConfigEntry,
        station: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self.station = station_code(station)
        self.manager = get_hgt_manager(hass)
        self.manager.register(entry.entry_id, self.station, session)
        entry.async_on_unload(
            lambda: self.manager.release(entry.entry_id, self.station)
        )
        self.issue_id = f"hgt_ogd_import_blocked_{entry.entry_id}"
        self._next_retry_seconds = _INITIAL_RETRY_SECONDS
        entry.async_on_unload(
            lambda: ir.async_delete_issue(hass, DOMAIN, self.issue_id)
        )
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_hgt_ogd",
            config_entry=entry,
            update_interval=REFRESH_INTERVAL,
        )

    async def _async_update_data(self) -> dict:
        try:
            data = await self.manager.async_refresh(self.station, datetime.now(UTC))
            ir.async_delete_issue(self.hass, DOMAIN, self.issue_id)
            self._next_retry_seconds = _INITIAL_RETRY_SECONDS
            return data
        except HgtError as error:
            if str(error) in {"statistics_conflict", "ownership_unavailable"}:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    self.issue_id,
                    is_fixable=False,
                    is_persistent=False,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key="hgt_ogd_import_blocked",
                )
                raise UpdateFailed(
                    translation_domain=DOMAIN, translation_key="hgt_ogd_conflict"
                ) from None
            raise UpdateFailed(
                retry_after=self._transient_retry_delay(),
                translation_domain=DOMAIN,
                translation_key="hgt_ogd_unavailable",
            ) from None
        except Exception:
            raise UpdateFailed(
                retry_after=self._transient_retry_delay(),
                translation_domain=DOMAIN,
                translation_key="hgt_ogd_unavailable",
            ) from None
        finally:
            await self.manager.async_sync_issue()

    def _transient_retry_delay(self) -> int:
        """Use Core's single polling timer; do not strand failures for six hours."""
        retry_after = self._next_retry_seconds
        self._next_retry_seconds = min(retry_after * 2, _MAX_RETRY_SECONDS)
        return retry_after

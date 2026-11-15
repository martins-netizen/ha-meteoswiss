"""Station ownership, shared source snapshots and explicit retired-data cleanup."""

from __future__ import annotations

import asyncio
from contextlib import AsyncExitStack
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiohttp
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.storage import Store

from .const import CONF_DATA_SOURCE, CONF_STATION_ID, DATA_SOURCE_OPENMETEO, DOMAIN
from .hgt_ogd import (
    REFRESH_INTERVAL,
    HgtError,
    MeteoSwissHgtClient,
    station_code,
)
from .hgt_ogd_recorder import async_clear_owned, async_import_products, async_metadata

DATA_KEY = "hgt_ogd_manager"
CLEANUP_ISSUE = "hgt_ogd_retired_cleanup"
BLOCKED_ISSUE = "hgt_ogd_cleanup_blocked"


@dataclass(frozen=True, slots=True)
class HgtRetiredPlan:
    stations: tuple[str, ...]
    metadata: dict


class HgtOgdManager:
    """Persist only owned station codes; source/history caches stay in memory."""

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self.store = Store(hass, 1, "meteoswiss_hgt_ogd")
        self.known: set[str] = set()
        self.loaded = False
        self.state_lock = asyncio.Lock()
        self.locks: dict[str, asyncio.Lock] = {}
        self.clients: dict[str, MeteoSwissHgtClient] = {}
        self.users: dict[str, set[str]] = {}
        self.snapshots: dict[str, tuple[datetime, dict]] = {}
        self.failures: dict[str, datetime] = {}

    async def async_load(self) -> None:
        async with self.state_lock:
            if self.loaded:
                return
            try:
                data = await self.store.async_load()
                if data is not None:
                    if (
                        not isinstance(data, dict)
                        or set(data) != {"stations"}
                        or not isinstance(data["stations"], list)
                        or len(data["stations"]) > 500
                    ):
                        raise HgtError("ownership_unavailable")
                    self.known = {station_code(s) for s in data["stations"]}
            except Exception:
                raise HgtError("ownership_unavailable") from None
            self.loaded = True

    async def _save(self, known: set[str]) -> None:
        try:
            if known:
                await self.store.async_save({"stations": sorted(known)})
            else:
                await self.store.async_remove()
        except Exception:
            raise HgtError("ownership_unavailable") from None
        self.known = known

    @callback
    def register(
        self, entry_id: str, station: str, session: aiohttp.ClientSession
    ) -> None:
        self.users.setdefault(station, set()).add(entry_id)
        if station not in self.clients:
            self.clients[station] = MeteoSwissHgtClient(session, station)

    @callback
    def release(self, entry_id: str, station: str) -> None:
        users = self.users.get(station, set())
        users.discard(entry_id)
        if not users:
            self.users.pop(station, None)
            self.clients.pop(station, None)
            self.snapshots.pop(station, None)
            self.failures.pop(station, None)

    def active_stations(self, exclude_entry_id: str | None = None) -> set[str]:
        result = set()
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if (
                entry.entry_id == exclude_entry_id
                or entry.data.get(CONF_DATA_SOURCE) == DATA_SOURCE_OPENMETEO
            ):
                continue
            try:
                result.add(station_code(entry.data.get(CONF_STATION_ID)))
            except HgtError:
                continue
        return result

    async def async_refresh(self, station: str, now: datetime) -> dict:
        await self.async_load()
        async with self.locks.setdefault(station, asyncio.Lock()):
            if (
                station in self.snapshots
                and now - self.snapshots[station][0] < REFRESH_INTERVAL
            ):
                return self.snapshots[station][1]
            if station in self.failures and now - self.failures[station] < timedelta(
                seconds=30
            ):
                raise HgtError("source_unavailable")
            try:
                async with asyncio.timeout(180):
                    products = await self.clients[station].async_fetch(self.hass, now)
                    metadata = await async_metadata(self.hass, {station})
                    if station not in self.known:
                        if metadata or len(self.known) >= 500:
                            raise HgtError("statistics_conflict")
                        # Persist provenance before queuing data, including when
                        # the caller subsequently cancels or Recorder times out.
                        async with self.state_lock:
                            await self._save(self.known | {station})
                    data = await async_import_products(
                        self.hass, station, products, metadata
                    )
                if station in self.users:
                    self.snapshots[station] = (now, data)
                self.failures.pop(station, None)
                return data
            except Exception:
                if station in self.users:
                    self.failures[station] = now
                raise

    async def async_retired_plan(
        self, exclude_entry_id: str | None = None
    ) -> HgtRetiredPlan:
        await self.async_load()
        stations = tuple(sorted(self.known - self.active_stations(exclude_entry_id)))
        metadata = await async_metadata(self.hass, set(stations)) if stations else {}
        if set(stations) != self.known - self.active_stations(exclude_entry_id):
            raise HgtError("cleanup_target_changed")
        return HgtRetiredPlan(stations, metadata)

    async def async_sync_issue(self, exclude_entry_id: str | None = None) -> None:
        """Keep every retired owned profile visible, also after its entry is gone."""
        try:
            plan = await self.async_retired_plan(exclude_entry_id)
            if not plan.metadata:
                if plan.stations:
                    async with self.state_lock:
                        await self._save(
                            self.known
                            - (
                                set(plan.stations)
                                - self.active_stations(exclude_entry_id)
                            )
                        )
                ir.async_delete_issue(self.hass, DOMAIN, CLEANUP_ISSUE)
            else:
                ir.async_create_issue(
                    self.hass,
                    DOMAIN,
                    CLEANUP_ISSUE,
                    is_fixable=True,
                    is_persistent=True,
                    severity=ir.IssueSeverity.WARNING,
                    translation_key=CLEANUP_ISSUE,
                    data={"kind": CLEANUP_ISSUE},
                    translation_placeholders={
                        "statistic_ids": "\n".join(sorted(plan.metadata))
                    },
                )
            ir.async_delete_issue(self.hass, DOMAIN, BLOCKED_ISSUE)
        except Exception:
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                BLOCKED_ISSUE,
                is_fixable=False,
                is_persistent=True,
                severity=ir.IssueSeverity.WARNING,
                translation_key=BLOCKED_ISSUE,
            )

    async def async_confirm_cleanup(self, expected: HgtRetiredPlan) -> None:
        """Lock target stations, recheck ownership/consent and verify full deletion."""

        async def finish():
            async with AsyncExitStack() as stack:
                for station in expected.stations:
                    await stack.enter_async_context(
                        self.locks.setdefault(station, asyncio.Lock())
                    )
                if await self.async_retired_plan() != expected:
                    raise HgtError("cleanup_target_changed")
                if expected.metadata:
                    await async_clear_owned(self.hass, sorted(expected.metadata))
                    if await async_metadata(self.hass, set(expected.stations)):
                        raise HgtError("cleanup_not_verified")
                async with self.state_lock:
                    # A newly reactivated station remains owned and may rebuild
                    # only after this native deletion completed under its lock.
                    await self._save(
                        self.known - (set(expected.stations) - self.active_stations())
                    )
            await self.async_sync_issue()

        await asyncio.shield(
            self.hass.async_create_background_task(
                finish(), "MeteoSwiss confirmed retired HGT cleanup"
            )
        )

    async def async_entry_removed(self, entry_id: str) -> None:
        """A confirmed removal of the final integration entry also removes its products.

        A custom repair cannot execute after restart with no integration loaded.
        Keep station-change cleanup consent separate while entries still exist;
        final native integration removal is the explicit removal action for all
        owned public-data projections. Never remove ordinary sensor history.
        """
        await self.async_sync_issue(exclude_entry_id=entry_id)
        if self.hass.config_entries.async_entries(DOMAIN):
            return
        try:
            await self.async_confirm_cleanup(await self.async_retired_plan())
        except Exception:
            # Do not leave a fixable notice that HA could satisfy with its
            # generic confirmation flow when our component is no longer loaded.
            ir.async_delete_issue(self.hass, DOMAIN, CLEANUP_ISSUE)
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                BLOCKED_ISSUE,
                is_fixable=False,
                is_persistent=True,
                severity=ir.IssueSeverity.WARNING,
                translation_key=BLOCKED_ISSUE,
            )


@callback
def get_hgt_manager(hass: HomeAssistant) -> HgtOgdManager:
    data = hass.data.setdefault(DOMAIN, {})
    if DATA_KEY not in data:
        data[DATA_KEY] = HgtOgdManager(hass)
    return data[DATA_KEY]

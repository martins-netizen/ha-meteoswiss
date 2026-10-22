"""UI setup with source validation, recoverable errors and duplicate guards."""

from __future__ import annotations

import asyncio
import math
import re
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    CONF_DATA_SOURCE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POLLEN_STATION,
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DATA_SOURCE_METEOSWISS,
    DATA_SOURCE_OPENMETEO,
    DEFAULT_API_TIMEOUT,
    DEFAULT_POLLEN_STATION,
    DEFAULT_UPDATE_INTERVAL_SEC,
    DOMAIN,
    POLLEN_STATIONS,
)
from .coordinator import MeteoSwissDataUpdateCoordinator
from .openmeteo_coordinator import OpenMeteoDataUpdateCoordinator
from .stations_map import WeatherStation, get_stations_map, parse_station_catalogue

WARNING_POSTCODE = re.compile(r"[1-9][0-9]{3}")


def _has_matching_meteoswiss_entry(
    entries: list[Any], station_id: str, postal_code: str
) -> bool:
    """Include legacy entries without unique IDs or an explicit source."""
    for entry in entries:
        data = entry.data
        if data.get(CONF_DATA_SOURCE, DATA_SOURCE_METEOSWISS) != DATA_SOURCE_METEOSWISS:
            continue
        if (
            str(data.get(CONF_STATION_ID, "")).strip().lower()
            == station_id.strip().lower()
            and str(data.get(CONF_POSTAL_CODE, "")).strip() == postal_code.strip()
        ):
            return True
    return False


def _has_matching_openmeteo_entry(
    entries: list[Any], latitude: float, longitude: float, postal_code: str
) -> bool:
    """Match existing location/postcode entries, including entries without IDs."""
    for entry in entries:
        data = entry.data
        if data.get(CONF_DATA_SOURCE) != DATA_SOURCE_OPENMETEO:
            continue
        if (
            data.get(CONF_LATITUDE) == latitude
            and data.get(CONF_LONGITUDE) == longitude
            and str(data.get(CONF_POSTAL_CODE, "")).strip() == postal_code
        ):
            return True
    return False


def _station_choices(stations: list[WeatherStation]) -> list[dict[str, Any]]:
    return [
        {
            "id": station.station_id.lower(),
            "name": station.name,
            "canton": station.canton or "",
            "label": f"{station.name} ({station.station_id.upper()})",
            "lat": station.latitude,
            "lon": station.longitude,
        }
        for station in sorted(stations, key=lambda item: item.name)
    ]


def _parse_stations(content: bytes) -> list[dict[str, Any]]:
    """Compatibility projection of the shared provider-column parser."""
    try:
        return _station_choices(list(parse_station_catalogue(content).values()))
    except (ValueError, UnicodeError):
        return []


class MeteoSwissConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle public APIs; no account or authentication is needed."""

    VERSION = 1
    MINOR_VERSION = 2

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return the HA-managed options flow."""
        return MeteoSwissOptionsFlow()

    def __init__(self) -> None:
        self._pollen_station = DEFAULT_POLLEN_STATION
        self._stations: list[dict[str, Any]] = []

    async def _load_stations(self) -> list[dict[str, Any]]:
        """Reuse HA's TLS-verified session; a failed catalogue remains retryable."""
        stations = await get_stations_map(
            session=async_get_clientsession(self.hass), retry=True
        )
        return _station_choices(stations.get_all_stations())

    async def _validate_source(
        self,
        *,
        station_id: str | None = None,
        latitude: float = 0,
        longitude: float = 0,
    ) -> bool:
        """Use the same observation contract as setup, with a bounded total wait."""
        session = async_get_clientsession(self.hass)
        if station_id is not None:
            coordinator = MeteoSwissDataUpdateCoordinator(
                self.hass, station_id, DEFAULT_UPDATE_INTERVAL_SEC, session=session
            )
        else:
            coordinator = OpenMeteoDataUpdateCoordinator(
                self.hass,
                latitude,
                longitude,
                DEFAULT_UPDATE_INTERVAL_SEC,
                session=session,
            )
        try:
            async with asyncio.timeout(DEFAULT_API_TIMEOUT.total):
                # No listeners are registered, so this schedules no polling.
                await coordinator.async_refresh()
        except TimeoutError:
            return False
        return coordinator.last_update_success

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Choose weather source and the independent measured-pollen station."""
        errors = {}
        if user_input is not None:
            pollen_station = user_input.get(CONF_POLLEN_STATION)
            if (
                not isinstance(pollen_station, str)
                or pollen_station not in POLLEN_STATIONS
            ):
                errors[CONF_POLLEN_STATION] = "invalid_pollen_station"
            else:
                self._pollen_station = pollen_station
                if user_input[CONF_DATA_SOURCE] == DATA_SOURCE_OPENMETEO:
                    return await self.async_step_openmeteo()
                return await self.async_step_meteoswiss()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_DATA_SOURCE, default=DATA_SOURCE_OPENMETEO
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[DATA_SOURCE_OPENMETEO, DATA_SOURCE_METEOSWISS],
                            translation_key="data_source",
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Required(CONF_POLLEN_STATION): vol.In(POLLEN_STATIONS),
                }
            ),
            errors=errors,
        )

    async def async_step_meteoswiss(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Validate the selected station before creating a config entry."""
        errors = {}
        if user_input is not None:
            station_id = user_input[CONF_STATION_ID].strip().lower()
            postcode = user_input[CONF_POSTAL_CODE].strip()
            if not WARNING_POSTCODE.fullmatch(postcode):
                errors[CONF_POSTAL_CODE] = "invalid_postal_code"
            else:
                if _has_matching_meteoswiss_entry(
                    self._async_current_entries(), station_id, postcode
                ):
                    return self.async_abort(reason="already_configured")
                await self.async_set_unique_id(
                    f"{DATA_SOURCE_METEOSWISS}:{station_id}:{postcode}"
                )
                self._abort_if_unique_id_configured()
        if not self._stations:
            self._stations = await self._load_stations()
        if not self._stations:
            errors["base"] = "cannot_connect"
        elif user_input is not None and not errors:
            station = next(
                (item for item in self._stations if item["id"] == station_id), None
            )
            if station is None:
                errors["base"] = "station_not_found"
            elif not await self._validate_source(station_id=station_id):
                errors["base"] = "cannot_connect"
            else:
                return self.async_create_entry(
                    title=f"MeteoSwiss {station['name']} ({station_id.upper()})",
                    data={
                        CONF_DATA_SOURCE: DATA_SOURCE_METEOSWISS,
                        CONF_POSTAL_CODE: postcode,
                        CONF_STATION_ID: station_id,
                        CONF_STATION_NAME: station["name"],
                        CONF_LATITUDE: station["lat"],
                        CONF_LONGITUDE: station["lon"],
                    },
                    options={CONF_POLLEN_STATION: self._pollen_station},
                )
        return self.async_show_form(
            step_id="meteoswiss",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POSTAL_CODE): str,
                    # Keep the field usable when loading the catalogue failed: the
                    # user can submit again to retry, rather than an empty dropdown.
                    vol.Required(CONF_STATION_ID): vol.In(
                        {s["id"]: s["label"] for s in self._stations}
                    )
                    if self._stations
                    else str,
                }
            ),
            errors=errors,
        )

    async def async_step_openmeteo(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Validate coordinates and availability, and reject duplicate entries."""
        errors = {}
        if user_input is not None:
            latitude, longitude = user_input[CONF_LATITUDE], user_input[CONF_LONGITUDE]
            postcode = user_input[CONF_POSTAL_CODE].strip()
            if not WARNING_POSTCODE.fullmatch(postcode):
                errors[CONF_POSTAL_CODE] = "invalid_postal_code"
            elif not (
                math.isfinite(latitude)
                and math.isfinite(longitude)
                and -90 <= latitude <= 90
                and -180 <= longitude <= 180
            ):
                errors["base"] = "invalid_location"
            else:
                if _has_matching_openmeteo_entry(
                    self._async_current_entries(), latitude, longitude, postcode
                ):
                    return self.async_abort(reason="already_configured")
                await self.async_set_unique_id(
                    f"{DATA_SOURCE_OPENMETEO}:{latitude}:{longitude}:{postcode}"
                )
                self._abort_if_unique_id_configured()
                if await self._validate_source(latitude=latitude, longitude=longitude):
                    return self.async_create_entry(
                        title=f"Open-Meteo ({latitude:.2f}, {longitude:.2f})",
                        data={
                            CONF_DATA_SOURCE: DATA_SOURCE_OPENMETEO,
                            CONF_POSTAL_CODE: postcode,
                            CONF_LATITUDE: latitude,
                            CONF_LONGITUDE: longitude,
                            CONF_STATION_NAME: "Open-Meteo",
                        },
                        options={CONF_POLLEN_STATION: self._pollen_station},
                    )
                errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="openmeteo",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_POSTAL_CODE): str,
                    vol.Required(CONF_LATITUDE, default=47.05): vol.Coerce(float),
                    vol.Required(CONF_LONGITUDE, default=8.31): vol.Coerce(float),
                }
            ),
            errors=errors,
        )


class MeteoSwissOptionsFlow(OptionsFlow):
    """Edit options without replacing the entry or its entity IDs."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            # The form edits one supported setting. Preserve legacy polling and
            # other saved options that are deliberately not exposed by this UI.
            options = dict(self.config_entry.options)
            options[CONF_POLLEN_STATION] = user_input.get(
                CONF_POLLEN_STATION,
                options.get(CONF_POLLEN_STATION, DEFAULT_POLLEN_STATION),
            )
            return self.async_create_entry(title="", data=options)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_POLLEN_STATION,
                        default=self.config_entry.options.get(
                            CONF_POLLEN_STATION, DEFAULT_POLLEN_STATION
                        ),
                    ): vol.In(POLLEN_STATIONS),
                }
            ),
        )

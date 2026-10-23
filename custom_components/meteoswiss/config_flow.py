"""UI setup with source validation, recoverable errors and duplicate guards."""

from __future__ import annotations

import asyncio
import math
import re
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import SOURCE_RECONFIGURE, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)
from homeassistant.helpers.translation import async_get_translations

from .const import (
    CONF_DATA_SOURCE,
    CONF_FORECAST_LOCATION,
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
from .coordinator import MeteoSwissDataUpdateCoordinator, OpenMeteoDataUpdateCoordinator
from .forecast import IconForecastClient, IconForecastError
from .forecast_location_client import (
    ForecastCatalogueUnavailable,
    MeteoSwissForecastCatalogueClient,
)
from .forecast_location_config import encode_forecast_location, resolve_forecast_target
from .forecast_locations import ForecastLocation, search_forecast_locations
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
        self._pending_data: dict[str, Any] = {}
        self._pending_title = ""
        self._catalogue_client: MeteoSwissForecastCatalogueClient | None = None
        self._candidates: dict[str, ForecastLocation] = {}
        self._candidate_labels: dict[str, str] = {}
        self._selected_location: ForecastLocation | None = None
        self._query = ""

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
                self._pending_title = (
                    f"MeteoSwiss {station['name']} ({station_id.upper()})"
                )
                self._pending_data = {
                    CONF_DATA_SOURCE: DATA_SOURCE_METEOSWISS,
                    CONF_POSTAL_CODE: postcode,
                    CONF_STATION_ID: station_id,
                    CONF_STATION_NAME: station["name"],
                    CONF_LATITUDE: station["lat"],
                    CONF_LONGITUDE: station["lon"],
                }
                return await self.async_step_forecast_location()
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
                    self._pending_title = (
                        f"Open-Meteo ({latitude:.2f}, {longitude:.2f})"
                    )
                    self._pending_data = {
                        CONF_DATA_SOURCE: DATA_SOURCE_OPENMETEO,
                        CONF_POSTAL_CODE: postcode,
                        CONF_LATITUDE: latitude,
                        CONF_LONGITUDE: longitude,
                        CONF_STATION_NAME: "Open-Meteo",
                    }
                    return await self.async_step_forecast_location()
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

    async def _forecast_labels(self) -> dict[str, str]:
        language = self.context.get("language", self.hass.config.language)
        translations = await async_get_translations(
            self.hass, language, "selector", {DOMAIN}
        )
        prefix = f"component.{DOMAIN}.selector.forecast_point_type.options."
        return {
            key.removeprefix(prefix): value
            for key, value in translations.items()
            if key.startswith(prefix)
        }

    @staticmethod
    def _point_label(location: ForecastLocation, labels: dict[str, str]) -> str:
        point = location.point
        name = f"{point.postal_code} {point.name}" if point.postal_code else point.name
        height = (
            labels["unknown_height"]
            if point.altitude_masl is None
            else f"{point.altitude_masl:g} m"
        )
        return f"{name} · {labels[str(point.point_type)]} · {height}"

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Change only forecast selection; keep current source/warning/pollen roles."""
        entry = self._get_reconfigure_entry()
        self._pending_data = dict(entry.data)
        self._pending_title = entry.title
        return await self.async_step_forecast_location(user_input)

    async def async_step_forecast_location(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Explain forecast purpose before accepting any search term."""
        errors = {}
        target = resolve_forecast_target(self._pending_data, None, None)
        if user_input is not None:
            action = user_input.get("action")
            if action == "search":
                return await self.async_step_forecast_search()
            if action == "keep" and target.status != "invalid":
                return self._finish_forecast_selection(change=False)
            if action == "base":
                self._selected_location = None
                return await self.async_step_forecast_confirm()
            errors["base"] = "invalid_forecast_selection"
        labels = await self._forecast_labels()
        current = (
            self._point_label(target.location, labels)
            if target.location
            else labels[target.status]
        )
        actions = ["keep", "search"]
        if CONF_FORECAST_LOCATION in self._pending_data:
            actions.append("base")
        return self.async_show_form(
            step_id="forecast_location",
            data_schema=vol.Schema(
                {
                    vol.Required("action"): SelectSelector(
                        SelectSelectorConfig(
                            options=actions,
                            translation_key="forecast_location_action",
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
            description_placeholders={"current_location": current},
            errors=errors,
        )

    async def async_step_forecast_search(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Reuse one bounded client; search the snapshot outside the event loop."""
        errors = {}
        self._candidates = {}
        self._candidate_labels = {}
        self._selected_location = None
        if user_input is not None:
            query = user_input.get("query")
            if not isinstance(query, str) or not 2 <= len(query.strip()) <= 128:
                errors["base"] = "invalid_forecast_query"
            else:
                self._query = query.strip()
                error = await self._async_find_candidates()
                if error is None:
                    return await self.async_step_forecast_select()
                errors["base"] = error
        return self.async_show_form(
            step_id="forecast_search",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "query", description={"suggested_value": self._query}
                    ): vol.All(str, vol.Length(min=2, max=128))
                }
            ),
        )

    async def _async_find_candidates(self) -> str | None:
        if self._catalogue_client is None:
            self._catalogue_client = MeteoSwissForecastCatalogueClient(
                async_get_clientsession(self.hass)
            )
        try:
            catalogue = await self._catalogue_client.async_get_catalogue()
            results = await self.hass.async_add_executor_job(
                search_forecast_locations, catalogue, self._query
            )
        except ForecastCatalogueUnavailable:
            return "forecast_catalogue_unavailable"
        if not results.points:
            return "forecast_no_matches"
        if results.truncated:
            return "forecast_too_many_matches"
        labels = await self._forecast_labels()
        for point in results.points:
            key = f"{point.point_type}:{point.point_id}"
            location = ForecastLocation(point, catalogue.sha256, catalogue.retrieved_at)
            self._candidates[key] = location
            # Coordinates distinguish equal name/type/height records.
            self._candidate_labels[key] = (
                f"{self._point_label(location, labels)} · {point.latitude}, {point.longitude}"
            )
        return None

    async def async_step_forecast_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Never select the first result automatically, even for a single match."""
        if not self._candidates:
            return await self.async_step_forecast_search()
        errors = {}
        if user_input is not None:
            key = user_input.get("point")
            if isinstance(key, str) and key in self._candidates:
                self._selected_location = self._candidates[key]
                return await self.async_step_forecast_confirm()
            errors["base"] = "invalid_forecast_selection"
        return self.async_show_form(
            step_id="forecast_select",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required("point"): SelectSelector(
                        SelectSelectorConfig(
                            options=[
                                {"value": key, "label": label}
                                for key, label in self._candidate_labels.items()
                            ],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def _validate_forecast(self) -> bool:
        """Check a chosen point with the actual client, without scheduling polling."""
        point = self._selected_location.point
        client = IconForecastClient(
            point.latitude,
            point.longitude,
            async_get_clientsession(self.hass),
            elevation=point.altitude_masl,
        )
        try:
            async with asyncio.timeout(DEFAULT_API_TIMEOUT.total):
                await client.async_get_data()
        except (IconForecastError, TimeoutError):
            return False
        return True

    async def async_step_forecast_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Only explicit submission may commit a changed location."""
        errors = {}
        if user_input is not None:
            if user_input.get("search_again", False):
                return await self.async_step_forecast_search()
            if self._selected_location is None or await self._validate_forecast():
                return self._finish_forecast_selection(change=True)
            errors["base"] = "cannot_connect"
        labels = await self._forecast_labels()
        description = (
            self._point_label(self._selected_location, labels)
            if self._selected_location
            else labels["legacy"]
        )
        return self.async_show_form(
            step_id="forecast_confirm",
            errors=errors,
            data_schema=vol.Schema({vol.Optional("search_again", default=False): bool}),
            description_placeholders={
                "location": description,
                "postal_code": self._pending_data.get(CONF_POSTAL_CODE, "—"),
            },
            last_step=True,
        )

    def _finish_forecast_selection(self, *, change: bool) -> FlowResult:
        if self.source == SOURCE_RECONFIGURE:
            if not change:
                return self.async_abort(reason="reconfigure_successful")
            entry = self._get_reconfigure_entry()
            # Merge into the latest data: another options flow may have finished.
            data = dict(entry.data)
        else:
            data = dict(self._pending_data)
        if change:
            data.pop(CONF_FORECAST_LOCATION, None)
            if self._selected_location is not None:
                data[CONF_FORECAST_LOCATION] = encode_forecast_location(
                    self._selected_location
                )
        if self.source == SOURCE_RECONFIGURE:
            # The registered entry update listener owns its single reload.
            return self.async_update_and_abort(entry, data=data)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=self._pending_title,
            data=data,
            options={CONF_POLLEN_STATION: self._pollen_station},
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

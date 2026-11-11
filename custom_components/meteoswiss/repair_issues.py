"""Actionable local configuration issues, independent of provider availability."""

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN
from .forecast_location_config import resolve_forecast_target
from .runtime_data import MeteoSwissConfigEntry

INVALID_FORECAST_LOCATION = "invalid_forecast_location"
WIND_STATISTICS_BLOCKED = "wind_statistics_blocked"


@callback
def async_sync_wind_statistics_issue(
    hass: HomeAssistant, entry: MeteoSwissConfigEntry, blocked: bool
) -> None:
    """A local migration problem must not look like a provider outage."""
    issue_id = f"{WIND_STATISTICS_BLOCKED}_{entry.entry_id}"
    if not blocked:
        ir.async_delete_issue(hass, DOMAIN, issue_id)
        return
    ir.async_create_issue(
        hass,
        DOMAIN,
        issue_id,
        is_fixable=False,
        is_persistent=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=WIND_STATISTICS_BLOCKED,
        learn_more_url=(
            "https://github.com/martins-netizen/ha-meteoswiss/"
            "blob/development/docs/WIND_STATISTICS_MIGRATION.md"
        ),
    )


@callback
def async_clear_forecast_location_issue(
    hass: HomeAssistant, entry: MeteoSwissConfigEntry
) -> None:
    """Remove only this entry's issue after correction, disablement or removal."""
    ir.async_delete_issue(
        hass, DOMAIN, f"{INVALID_FORECAST_LOCATION}_{entry.entry_id}"
    )


@callback
def async_sync_forecast_location_issue(
    hass: HomeAssistant, entry: MeteoSwissConfigEntry
) -> None:
    """Check saved data offline; never turn a provider outage into a repair."""
    if resolve_forecast_target(entry.data, None, None).status != "invalid":
        async_clear_forecast_location_issue(hass, entry)
        return

    ir.async_create_issue(
        hass,
        DOMAIN,
        f"{INVALID_FORECAST_LOCATION}_{entry.entry_id}",
        is_fixable=False,
        is_persistent=False,
        severity=ir.IssueSeverity.ERROR,
        translation_key=INVALID_FORECAST_LOCATION,
        translation_placeholders={
            "entry_title": entry.title,
            "configuration_url": f"/config/integrations/integration/{DOMAIN}",
        },
        learn_more_url=(
            "https://github.com/martins-netizen/ha-meteoswiss/"
            "blob/development/docs/REPAIRS.md"
        ),
    )

"""Binary sensor platform for MeteoSwiss weather alerts."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Final, Literal

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

from .alerts import MeteoSwissAlertsAPI, WeatherAlert
from .const import (
    ATTRIBUTION,
    CONF_POSTAL_CODE,
    CONF_STATION_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class MeteoSwissAlertsBinarySensorDescription(BinarySensorEntityDescription):
    """Describes MeteoSwiss alerts binary sensor."""

    warn_level: int | None = None
    warn_type: int | None = None
    alert_timing: Literal["active", "upcoming"] = "active"


ALERT_SENSOR_DESCRIPTIONS: Final[tuple[MeteoSwissAlertsBinarySensorDescription, ...]] = (
    MeteoSwissAlertsBinarySensorDescription(
        key="any_alert",
        translation_key="any_alert",
        device_class=BinarySensorDeviceClass.SAFETY,
        name="Weather Alert",
        icon="mdi:alert",
    ),
    MeteoSwissAlertsBinarySensorDescription(
        key="critical_alert",
        translation_key="critical_alert",
        device_class=BinarySensorDeviceClass.SAFETY,
        name="Critical Weather Alert",
        icon="mdi:alert-octagram",
        warn_level=3,  # Level 3 or above
    ),
    MeteoSwissAlertsBinarySensorDescription(
        key="upcoming_alert",
        translation_key="upcoming_alert",
        device_class=BinarySensorDeviceClass.SAFETY,
        name="Upcoming Weather Alert",
        icon="mdi:alert-outline",
        alert_timing="upcoming",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities,
) -> None:
    """Set up binary sensor platform."""
    _LOGGER.debug("Setting up MeteoSwiss alerts binary sensor platform for %s", entry.data.get(CONF_STATION_NAME))

    coordinator = hass.data[DOMAIN][entry.entry_id]["alerts_coordinator"]
    postal_code = entry.data.get(CONF_POSTAL_CODE)

    entities = [
        MeteoSwissAlertsBinarySensor(coordinator, entry, description, postal_code)
        for description in ALERT_SENSOR_DESCRIPTIONS
    ]

    async_add_entities(entities)


class MeteoSwissAlertsBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a MeteoSwiss weather alert binary sensor."""

    def __init__(
        self,
        coordinator: MeteoSwissAlertsCoordinator,
        entry: ConfigEntry,
        description: MeteoSwissAlertsBinarySensorDescription,
        postal_code: str,
    ) -> None:
        """Initialize binary sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"alerts_{entry.entry_id}")},
            name=f"MeteoSwiss Alerts - {postal_code}",
            manufacturer="MeteoSwiss",
            model="Alerts",
        )
        self._attr_has_entity_name = True
        self._attr_attribution = ATTRIBUTION
        self._postal_code = postal_code

    def _matches_alert_timing(self, alert: WeatherAlert) -> bool:
        """Return whether an alert matches this entity's timing mode."""
        if self.entity_description.alert_timing == "upcoming":
            return alert.is_upcoming()
        return alert.is_active()

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if self.coordinator.data is None:
            return False

        alerts = self.coordinator.data

        if not alerts:
            return False

        # Check if any alert matches the criteria
        warn_level = self.entity_description.warn_level
        warn_type = self.entity_description.warn_type

        for alert in alerts:
            if not self._matches_alert_timing(alert):
                continue

            if warn_level is not None and alert.warn_level < warn_level:
                continue

            if warn_type is not None and alert.warn_type != warn_type:
                continue

            return True  # Alert matches timing and criteria

        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return active and upcoming alert details."""
        alerts = self.coordinator.data

        if not alerts:
            return {
                "active_alerts_count": 0,
                "alerts": [],
                "upcoming_alerts_count": 0,
                "upcoming_alerts": [],
                "next_alert_start": None,
            }

        active_alerts = [a for a in alerts if not a.outlook and a.is_active()]
        upcoming_alerts = sorted(
            (a for a in alerts if a.is_upcoming()),
            key=lambda a: (
                a.valid_from.timestamp()
                if a.valid_from is not None
                else float("inf")
            ),
        )

        return {
            "active_alerts_count": len(active_alerts),
            "alerts": [a.to_dict() for a in active_alerts],
            "upcoming_alerts_count": len(upcoming_alerts),
            "upcoming_alerts": [a.to_dict() for a in upcoming_alerts],
            "next_alert_start": (
                upcoming_alerts[0].valid_from.isoformat()
                if upcoming_alerts and upcoming_alerts[0].valid_from is not None
                else None
            ),
        }

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from coordinator."""
        self.async_write_ha_state()


class MeteoSwissAlertsCoordinator(DataUpdateCoordinator[list[WeatherAlert]]):
    """Class to manage fetching MeteoSwiss alerts."""

    def __init__(
        self,
        hass: HomeAssistant,
        alerts_api: MeteoSwissAlertsAPI,
        update_interval: int = 600,
    ) -> None:
        """Initialize."""
        self._alerts_api = alerts_api

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_alerts",
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> list[WeatherAlert]:
        """Fetch alerts from MeteoSwiss App API."""
        _LOGGER.debug("Fetching MeteoSwiss alerts")

        alerts = await self._alerts_api.get_alerts(self._alerts_api.postal_code)

        _LOGGER.debug("Successfully fetched %d MeteoSwiss alerts", len(alerts))

        return alerts

    async def async_close(self) -> None:
        """Close alerts API session."""
        await self._alerts_api.close()

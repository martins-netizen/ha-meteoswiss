"""The HA translation loader supplies explicit warning state labels."""

from __future__ import annotations

import pytest
from homeassistant.helpers.translation import async_get_translations

from custom_components.meteoswiss.binary_sensor import ALERT_SENSOR_DESCRIPTIONS
from custom_components.meteoswiss.const import DOMAIN


@pytest.mark.parametrize(
    "language,labels",
    [
        ("de", [("Keine aktive Warnung", "Warnung aktiv"),
                ("Keine kritische Warnung", "Kritische Warnung aktiv"),
                ("Keine angekündigte Warnung", "Warnung angekündigt")]),
        ("en", [("No active warning", "Warning active"),
                ("No critical warning", "Critical warning active"),
                ("No upcoming warning", "Warning announced")]),
        ("fr", [("Aucune alerte active", "Alerte active"),
                ("Aucune alerte critique", "Alerte critique active"),
                ("Aucune alerte annoncée", "Alerte annoncée")]),
        ("it", [("Nessuna allerta attiva", "Allerta attiva"),
                ("Nessuna allerta critica", "Allerta critica attiva"),
                ("Nessuna allerta annunciata", "Allerta annunciata")]),
    ],
)
async def test_frontend_receives_warning_specific_state_labels(
    hass, enable_custom_integrations, language, labels
):
    translations = await async_get_translations(hass, language, "entity", {DOMAIN})
    for description, (off, on) in zip(ALERT_SENSOR_DESCRIPTIONS, labels, strict=True):
        prefix = f"component.{DOMAIN}.entity.binary_sensor.{description.translation_key}.state."
        assert translations.get(prefix + "off") == off
        assert translations.get(prefix + "on") == on
        # HA owns unknown/unavailable; neither is a negative warning response.
        assert prefix + "unknown" not in translations
        assert prefix + "unavailable" not in translations

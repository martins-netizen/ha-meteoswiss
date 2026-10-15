"""Warning labels shared by native selectors and dashboard templates."""

from __future__ import annotations

import json
from pathlib import Path

from homeassistant.core import HomeAssistant

SUPPORTED_LANGUAGES = ("de", "en", "fr", "it")


def _load_warning_labels() -> dict[str, dict[str, dict[str, str]]]:
    """Read bundled translations once, outside the event loop."""
    directory = Path(__file__).parent / "translations"
    labels = {}
    for language in SUPPORTED_LANGUAGES:
        translations = json.loads(
            (directory / f"{language}.json").read_text(encoding="utf-8")
        )
        selectors = translations["selector"]
        labels[language] = {
            "types": selectors["warning_type"]["options"],
            "levels": selectors["warning_level"]["options"],
            "status": selectors["warning_data_status"]["options"],
        }
    return labels


async def async_load_warning_labels(hass: HomeAssistant) -> dict:
    """Load the same catalogue used by HA translations for custom displays."""
    return await hass.async_add_executor_job(_load_warning_labels)

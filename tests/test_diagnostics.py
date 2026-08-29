"""Regression tests for MeteoSwiss diagnostics privacy and structure."""

from __future__ import annotations

from datetime import timedelta
from types import SimpleNamespace

from homeassistant.helpers.redact import REDACTED
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POLLEN_STATION,
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DATA_SOURCE_METEOSWISS,
    DATA_SOURCE_OPENMETEO,
    DOMAIN,
)
from custom_components.meteoswiss.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_redact_location_and_station_identifiers(hass) -> None:
    """Sensitive config entry fields must never appear in diagnostics."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_LATITUDE: 47.45,
            CONF_LONGITUDE: 8.56,
            CONF_POSTAL_CODE: "8302",
            CONF_STATION_ID: "KLO",
            CONF_STATION_NAME: "Zürich / Kloten",
            "safe_setting": "visible",
        },
        options={
            CONF_POLLEN_STATION: "PLZ",
            "safe_option": "visible-option",
        },
    )

    coordinator = SimpleNamespace(
        name="meteoswiss",
        last_update_success=True,
        update_interval=timedelta(seconds=600),
        data={"temperature": 22.5, "humidity": 48.0},
        last_exception=None,
        data_source="meteoswiss",
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "data_source": "meteoswiss",
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    config_data = diagnostics["config_entry"]["data"]
    config_options = diagnostics["config_entry"]["options"]

    for key in (
        CONF_LATITUDE,
        CONF_LONGITUDE,
        CONF_POSTAL_CODE,
        CONF_STATION_ID,
        CONF_STATION_NAME,
    ):
        assert config_data[key] == REDACTED

    assert config_options[CONF_POLLEN_STATION] == REDACTED
    assert config_data["safe_setting"] == "visible"
    assert config_options["safe_option"] == "visible-option"


async def test_diagnostics_summarize_data_without_exposing_values_or_errors(hass) -> None:
    """Diagnostics should expose shape/status, never raw coordinator values."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_STATION_ID: "KLO"},
    )

    coordinator = SimpleNamespace(
        name="meteoswiss",
        last_update_success=False,
        update_interval=timedelta(seconds=600),
        data={
            "temperature": 22.5,
            "internal_value": "do-not-expose",
        },
        last_exception=RuntimeError("private failure detail 8302"),
        data_source="meteoswiss",
    )

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "data_source": "meteoswiss",
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    current = diagnostics["coordinators"]["coordinator"]

    assert current["available"] is True
    assert current["last_update_success"] is False
    assert current["update_interval_seconds"] == 600
    assert current["last_exception"] == "RuntimeError"
    assert current["data_source"] == "meteoswiss"
    assert current["data"] == {
        "type": "dict",
        "item_count": 2,
        "keys": ["internal_value", "temperature"],
    }

    # Optional coordinators not present in hass.data must be represented
    # explicitly rather than causing diagnostics generation to fail.
    assert diagnostics["coordinators"]["forecast_coordinator"] == {
        "available": False
    }
    assert diagnostics["coordinators"]["alerts_coordinator"] == {
        "available": False
    }

    rendered = repr(diagnostics)
    assert "22.5" not in rendered
    assert "do-not-expose" not in rendered
    assert "private failure detail" not in rendered
    assert "8302" not in rendered

async def test_diagnostics_report_meteoswiss_location_sources(hass) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_STATION_ID: "KLO"})
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "data_source": DATA_SOURCE_METEOSWISS,
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["location_sources"] == {
        "observations": "meteoswiss_station",
        "weather_forecast": "home_assistant",
        "pollen_forecast": "home_assistant",
        "weather_alerts": "postal_code",
        "measured_pollen": "meteoswiss_pollen_station",
    }


async def test_diagnostics_report_openmeteo_location_sources(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_LATITUDE: 46.2, CONF_LONGITUDE: 6.1},
    )
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "data_source": DATA_SOURCE_OPENMETEO,
    }

    diagnostics = await async_get_config_entry_diagnostics(hass, entry)

    assert diagnostics["location_sources"] == {
        "observations": "configured_location",
        "weather_forecast": "configured_location",
        "pollen_forecast": "configured_location",
        "weather_alerts": "postal_code",
        "measured_pollen": "meteoswiss_pollen_station",
    }

    rendered = repr(diagnostics)
    assert "46.2" not in rendered
    assert "6.1" not in rendered

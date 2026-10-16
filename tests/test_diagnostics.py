"""Regression tests for MeteoSwiss diagnostics privacy and structure."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from homeassistant.helpers.redact import REDACTED
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.cache import MeteoSwissCache
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
from custom_components.meteoswiss.runtime_data import MeteoSwissRuntimeData


async def test_unloaded_config_entry_can_still_provide_diagnostics(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_STATION_ID: "KLO"})
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["coordinators"]["coordinator"] == {"available": False}


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

    entry.runtime_data = MeteoSwissRuntimeData(
        coordinator=coordinator, data_source="meteoswiss", session=None
    )

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


async def test_diagnostics_summarize_data_without_exposing_values_or_errors(
    hass,
) -> None:
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

    entry.runtime_data = MeteoSwissRuntimeData(
        coordinator=coordinator, data_source="meteoswiss", session=None
    )

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
    }

    # Optional coordinators not present in runtime_data must be represented
    # explicitly rather than causing diagnostics generation to fail.
    assert diagnostics["coordinators"]["forecast_coordinator"] == {"available": False}
    assert diagnostics["coordinators"]["alerts_coordinator"] == {"available": False}

    rendered = repr(diagnostics)
    assert "22.5" not in rendered
    assert "do-not-expose" not in rendered
    assert "private failure detail" not in rendered
    assert "8302" not in rendered


async def test_diagnostics_report_meteoswiss_location_sources(hass) -> None:
    entry = MockConfigEntry(domain=DOMAIN, data={CONF_STATION_ID: "KLO"})
    entry.runtime_data = MeteoSwissRuntimeData(
        coordinator=None, data_source=DATA_SOURCE_METEOSWISS, session=None
    )

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
    entry.runtime_data = MeteoSwissRuntimeData(
        coordinator=None, data_source=DATA_SOURCE_OPENMETEO, session=None
    )

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


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        ("private-value",),
        {"private-value"},
        frozenset({"private-value"}),
        22.5,
    ],
)
async def test_all_data_shapes_are_reported_without_raw_values(hass, data):
    entry = MockConfigEntry(domain=DOMAIN)
    current = SimpleNamespace(
        name="private station KLO",
        last_update_success=True,
        update_interval=None,
        data=data,
        last_exception=None,
    )
    entry.runtime_data = MeteoSwissRuntimeData(
        coordinator=current, data_source="unknown", session=None
    )
    result = await async_get_config_entry_diagnostics(hass, entry)
    assert result["coordinators"]["coordinator"]["name"] == "coordinator"
    assert result["coordinators"]["coordinator"]["update_interval_seconds"] is None
    assert "private" not in repr(result)
    assert "22.5" not in repr(result)
    assert result["location_sources"]["observations"] == "unknown"


@pytest.mark.parametrize(
    "time_value",
    [
        "2026-10-16T15:00:00+02:00",
        datetime(2026, 10, 16, 13, tzinfo=UTC),
        datetime(2026, 10, 16, 13),
        "private invalid date",
        True,
        None,
    ],
)
async def test_safe_times_do_not_serialize_arbitrary_strings(hass, time_value):
    entry = MockConfigEntry(domain=DOMAIN)
    current = SimpleNamespace(
        name="private",
        last_update_success=True,
        update_interval=None,
        data=[None, {"fetched_at": time_value, "temperature": 22.5}],
        last_exception=None,
        last_successful_update=time_value,
    )
    entry.runtime_data = MeteoSwissRuntimeData(
        coordinator=current, data_source="meteoswiss", session=None
    )
    result = (await async_get_config_entry_diagnostics(hass, entry))["coordinators"][
        "coordinator"
    ]
    assert "private" not in repr(result)
    if time_value == "2026-10-16T15:00:00+02:00":
        assert result["data_timestamp"] == "2026-10-16T13:00:00+00:00"
    if isinstance(time_value, datetime) and time_value.tzinfo:
        assert result["last_successful_update"] == time_value.isoformat()
    if (
        time_value is None
        or time_value is True
        or isinstance(time_value, datetime)
        and time_value.tzinfo is None
    ):
        assert "last_successful_update" not in result


async def test_nested_location_fields_names_keys_error_urls_and_cache_values_are_private(
    hass, monkeypatch
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "latitude": 47.451234,
            "nested": {"station_id": "KLO", "list": [{"postal_code": "8302"}]},
        },
        options={"pollen_station": "PLZ"},
    )
    current = SimpleNamespace(
        name="private coordinate 47.451234",
        last_update_success=False,
        update_interval=timedelta(seconds=600),
        data={"private key 8302": "private raw data"},
        last_exception=RuntimeError(
            "private request https://example.invalid/?latitude=47.451234"
        ),
        data_source="private raw source",
    )
    entry.runtime_data = MeteoSwissRuntimeData(
        coordinator=current, data_source="private raw source", session=None
    )
    cache = MeteoSwissCache()
    cache.set("private cache key 47.451234", "private cache value")
    monkeypatch.setattr(
        "custom_components.meteoswiss.cache._current_weather_cache", cache
    )
    result = await async_get_config_entry_diagnostics(hass, entry)
    rendered = repr(result)
    for secret in ("private", "47.451234", "8302", "KLO", "PLZ", "example.invalid"):
        assert secret not in rendered
    assert result["coordinators"]["coordinator"]["last_exception"] == "RuntimeError"
    assert result["coordinators"]["coordinator"]["data_source"] == "unknown"
    assert result["cache"]["current_weather"]["entries"] == 1
    assert result["station_catalogue"]["data_status"] == "unavailable"

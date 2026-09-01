"""Regression tests for MeteoSwiss startup behaviour."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

from custom_components.meteoswiss import (
    _async_refresh_optional_coordinators,
    _get_forecast_coordinates,
    _keep_coordinator_polling,
)
from custom_components.meteoswiss.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    DATA_SOURCE_METEOSWISS,
    DATA_SOURCE_OPENMETEO,
    DOMAIN,
)
from pytest_homeassistant_custom_component.common import MockConfigEntry


async def test_optional_coordinator_refresh_is_resilient() -> None:
    """One optional coordinator failure must not prevent the others refreshing."""
    first_refresh = AsyncMock()
    failing_refresh = AsyncMock(side_effect=RuntimeError("temporary failure"))
    third_refresh = AsyncMock()

    first = SimpleNamespace(async_refresh=first_refresh)
    failing = SimpleNamespace(async_refresh=failing_refresh)
    third = SimpleNamespace(async_refresh=third_refresh)

    # The helper deliberately uses gather(..., return_exceptions=True).
    # A failure in one optional data source must not abort startup or stop
    # the remaining optional coordinators from refreshing.
    await _async_refresh_optional_coordinators(first, failing, third)

    first_refresh.assert_awaited_once_with()
    failing_refresh.assert_awaited_once_with()
    third_refresh.assert_awaited_once_with()


def test_listener_keeps_hourly_statistics_coordinator_polling() -> None:
    """The statistics-only coordinator must poll without entity listeners."""
    remove_listener = Mock()
    entry = SimpleNamespace(async_on_unload=Mock())
    coordinator = SimpleNamespace(
        async_add_listener=Mock(return_value=remove_listener)
    )

    _keep_coordinator_polling(entry, coordinator)

    coordinator.async_add_listener.assert_called_once()
    listener = coordinator.async_add_listener.call_args.args[0]
    assert listener() is None
    entry.async_on_unload.assert_called_once_with(remove_listener)


def test_meteoswiss_forecast_uses_home_assistant_location() -> None:
    """Station observations must not force forecasts to station coordinates."""
    hass = SimpleNamespace(
        config=SimpleNamespace(latitude=47.451, longitude=8.562)
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_LATITUDE: 46.948,
            CONF_LONGITUDE: 7.447,
        },
    )

    assert _get_forecast_coordinates(
        hass, entry, DATA_SOURCE_METEOSWISS
    ) == (47.451, 8.562)


def test_openmeteo_forecast_keeps_configured_location() -> None:
    """Explicit Open-Meteo entries must keep configured coordinates."""
    hass = SimpleNamespace(
        config=SimpleNamespace(latitude=47.451, longitude=8.562)
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_LATITUDE: 46.204,
            CONF_LONGITUDE: 6.143,
        },
    )

    assert _get_forecast_coordinates(
        hass, entry, DATA_SOURCE_OPENMETEO
    ) == (46.204, 6.143)

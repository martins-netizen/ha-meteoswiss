"""Regression tests for MeteoSwiss startup behaviour."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock

from custom_components.meteoswiss import _async_refresh_optional_coordinators


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

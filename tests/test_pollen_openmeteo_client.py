"""Borrowed-session source boundary and unchanged atomic AQ/UV cache contract."""

import asyncio
import traceback
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from custom_components.meteoswiss.cache import clear_all_caches
from custom_components.meteoswiss.coordinator import OpenMeteoPollenCoordinator
from custom_components.meteoswiss.http import AIR_QUALITY_HOST, FORECAST_HOST
from custom_components.meteoswiss.pollen_openmeteo import (
    OPENMETEO_AQ_BASE_URL,
    OPENMETEO_FORECAST_URL,
    OpenMeteoPollenClient,
    OpenMeteoPollenError,
)


@pytest.fixture
def aq_source(freezer):
    freezer.move_to("2026-10-23T10:05:00+00:00")
    clear_all_caches()
    payload = {
        "hourly": {
            "time": [int(datetime(2026, 10, 23, 10, tzinfo=UTC).timestamp())],
            "pm10": [0],
            "birch_pollen": [None],
        }
    }
    session = Mock(spec=aiohttp.ClientSession)
    session.close = AsyncMock()
    yield OpenMeteoPollenClient(47.451234, 8.561234, session), payload, session
    session.close.assert_not_called()
    clear_all_caches()


async def test_direct_client_preserves_request_parameters_partial_values_and_uv(
    aq_source,
):
    client, payload, session = aq_source
    with patch(
        "custom_components.meteoswiss.pollen_openmeteo.async_get_json",
        side_effect=[payload, {"current": {"uv_index": 0}}],
    ) as request:
        result = await client.async_get_data()
    aq, uv = request.await_args_list
    assert aq.args == (session, OPENMETEO_AQ_BASE_URL)
    assert aq.kwargs["host"] == AIR_QUALITY_HOST
    assert aq.kwargs["params"] == {
        "latitude": 47.451234,
        "longitude": 8.561234,
        "hourly": "alder_pollen,birch_pollen,grass_pollen,mugwort_pollen,ragweed_pollen,pm2_5,pm10,nitrogen_dioxide,ozone",
        "forecast_days": 5,
        "timezone": "Europe/Zurich",
        "timeformat": "unixtime",
    }
    assert uv.args == (session, OPENMETEO_FORECAST_URL)
    assert uv.kwargs == {
        "host": FORECAST_HOST,
        "params": {
            "latitude": 47.451234,
            "longitude": 8.561234,
            "current": "uv_index",
            "timezone": "Europe/Zurich",
        },
    }
    assert result["pm10"] == result["uv_index"] == 0
    assert result["birch_pollen"]["current"] is None
    assert result["uv_available"] is True
    assert result["last_update"] == "2026-10-23T10:00:00+00:00"


@pytest.mark.parametrize(
    "error,attempts",
    [
        (aiohttp.ClientConnectionError("private_marker 47.451234"), 4),
        (TimeoutError("private_marker 8.561234"), 4),
        (ValueError("private_marker https://location.example"), 1),
    ],
)
async def test_direct_source_errors_are_empty_and_hide_raw_tracebacks(
    aq_source, error, attempts
):
    client, _, _ = aq_source
    with (
        patch(
            "custom_components.meteoswiss.pollen_openmeteo.async_get_json",
            side_effect=error,
        ) as request,
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ),
        pytest.raises(OpenMeteoPollenError) as caught,
    ):
        await client.async_get_data()
    assert request.await_count == attempts
    assert str(caught.value) == ""
    formatted = "".join(traceback.format_exception(caught.value))
    assert all(
        marker not in formatted
        for marker in ("private_marker", "47.451234", "8.561234", "location.example")
    )


async def test_invalid_aq_does_not_fetch_optional_uv(aq_source):
    client, payload, _ = aq_source
    payload["hourly"]["pm10"] = [None]
    with patch(
        "custom_components.meteoswiss.pollen_openmeteo.async_get_json",
        return_value=payload,
    ) as request:
        with pytest.raises(OpenMeteoPollenError):
            await client.async_get_data()
    assert request.await_count == 1


@pytest.mark.parametrize("cancel_uv", [False, True])
async def test_direct_cancellation_propagates_from_either_request(aq_source, cancel_uv):
    client, payload, _ = aq_source
    responses = (
        [payload, asyncio.CancelledError()] if cancel_uv else [asyncio.CancelledError()]
    )
    with patch(
        "custom_components.meteoswiss.pollen_openmeteo.async_get_json",
        side_effect=responses,
    ) as request:
        with pytest.raises(asyncio.CancelledError):
            await client.async_get_data()
    assert request.await_count == (2 if cancel_uv else 1)


async def test_direct_uv_failure_keeps_valid_zero_aq(aq_source):
    client, payload, _ = aq_source
    with patch(
        "custom_components.meteoswiss.pollen_openmeteo.async_get_json",
        side_effect=[payload, TimeoutError("private_uv_marker")],
    ) as request:
        result = await client.async_get_data()
    assert result["pm10"] == 0
    assert result["uv_index"] is None
    assert result["uv_available"] is False
    assert request.await_count == 2


async def test_direct_missing_session_is_a_setup_error():
    with pytest.raises(RuntimeError, match="No aiohttp session"):
        await OpenMeteoPollenClient(47.45, 8.56).async_get_data()


async def test_coordinator_cache_hit_preserves_original_ttl_and_uv_status(
    hass, aq_source, freezer
):
    client, payload, session = aq_source
    data = client.parse_response(payload)
    first = {**data, "uv_index": 0, "uv_available": True}
    second = {**data, "uv_index": None, "uv_available": False}
    coordinator = OpenMeteoPollenCoordinator(hass, 47.451234, 8.561234, session=session)
    with patch.object(
        coordinator.client, "async_get_data", side_effect=[first, second]
    ) as fetch:
        assert await coordinator._async_update_data() == first
        freezer.move_to("2026-10-23T10:20:00+00:00")
        assert await coordinator._async_update_data() == first
        assert fetch.await_count == 1
        freezer.move_to("2026-10-23T10:35:00+00:00")
        assert await coordinator._async_update_data() == second
        assert fetch.await_count == 2
    assert coordinator._uv_last_update_success is False

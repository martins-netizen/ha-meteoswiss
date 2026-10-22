"""Use the current-weather client without passing an HA coordinator/runtime."""

import asyncio
import traceback
from datetime import UTC, datetime

import pytest

from custom_components.meteoswiss.openmeteo import (
    OPENMETEO_BASE_URL,
    OpenMeteoCurrentClient,
    OpenMeteoCurrentError,
)


async def test_current_client_preserves_zero_partial_values_and_borrowed_session(
    aioclient_mock,
):
    stamp = int(datetime.now(UTC).timestamp())
    aioclient_mock.get(
        OPENMETEO_BASE_URL,
        json={
            "current": {
                "time": stamp,
                "temperature_2m": -2,
                "relative_humidity_2m": 0,
                "wind_speed_10m": 0,
                "precipitation": 0,
                "weather_code": 0,
                "is_day": 0,
                "interval": 900,
            }
        },
    )
    async with aioclient_mock.create_session(asyncio.get_running_loop()) as session:
        client = OpenMeteoCurrentClient(47.451234, 8.561234, session)
        data = await client.async_get_data()
        assert data["temperature"] == -2
        assert data["humidity"] == data["wind_speed"] == data["precipitation"] == 0
        assert data["pressure"] is None
        assert data["weather_condition"] == "clear-night"
        assert data["last_update"] == datetime.fromtimestamp(stamp, UTC).isoformat()
        assert data["precipitation_interval_seconds"] == 900
        assert data["hourly_forecast"] == []
        assert not session.closed
    assert session.closed
    assert len(aioclient_mock.mock_calls) == 1


@pytest.mark.parametrize(
    "response", [{"status": 404}, {"text": "47.451234 latitude=8.561234"}]
)
async def test_current_client_errors_hide_request_and_payload(aioclient_mock, response):
    aioclient_mock.get(OPENMETEO_BASE_URL, **response)
    async with aioclient_mock.create_session(asyncio.get_running_loop()) as session:
        client = OpenMeteoCurrentClient(47.451234, 8.561234, session)
        with pytest.raises(OpenMeteoCurrentError) as raised:
            await client.async_get_data()
        assert str(raised.value) == ""
        assert raised.value.__suppress_context__
        rendered = "".join(traceback.format_exception(raised.value))
        assert "47.451234" not in rendered
        assert "8.561234" not in rendered
        assert "latitude=" not in rendered
        assert not session.closed
    assert len(aioclient_mock.mock_calls) == 1


async def test_current_client_propagates_cancellation_without_closing_session(
    aioclient_mock,
):
    aioclient_mock.get(OPENMETEO_BASE_URL, exc=asyncio.CancelledError())
    async with aioclient_mock.create_session(asyncio.get_running_loop()) as session:
        client = OpenMeteoCurrentClient(47.451234, 8.561234, session)
        with pytest.raises(asyncio.CancelledError):
            await client.async_get_data()
        assert not session.closed
    assert len(aioclient_mock.mock_calls) == 1


async def test_current_client_reports_missing_session_as_a_source_error():
    client = OpenMeteoCurrentClient(47.451234, 8.561234)
    with pytest.raises(OpenMeteoCurrentError) as raised:
        await client.async_get_data()
    assert str(raised.value) == ""

"""Exercise the ICON source directly with only a borrowed HTTP session."""

import asyncio
import traceback
from datetime import UTC, datetime

import pytest

from custom_components.meteoswiss.forecast import (
    OPEN_METEO_BASE_URL,
    IconForecastClient,
    IconForecastError,
)


async def test_icon_client_preserves_model_partial_values_and_session(aioclient_mock):
    hour = int(datetime.now(UTC).replace(minute=0, second=0, microsecond=0).timestamp())
    aioclient_mock.get(
        OPEN_METEO_BASE_URL,
        json={
            "hourly": {
                "time": [hour, hour + 3600],
                "temperature_2m": [0, -2],
                "precipitation": [0],
                "relative_humidity_2m": [0],
                "weather_code": [0, 999],
                "is_day": [0, 1],
            }
        },
    )
    async with aioclient_mock.create_session(asyncio.get_running_loop()) as session:
        rows = await IconForecastClient(47.451234, 8.561234, session).async_get_data()
        assert [row["temperature"] for row in rows] == [0, -2]
        assert rows[0]["precipitation"] == rows[0]["humidity"] == 0
        assert rows[1]["precipitation"] is rows[1]["humidity"] is None
        assert rows[0]["condition"] == "clear-night"
        assert rows[1]["condition"] is None
        assert rows[0]["daily_temperature_min"] is None
        assert rows[0]["source"] == "meteoswiss_icon_seamless_via_open_meteo"
        assert datetime.fromisoformat(rows[0]["datetime"]) == datetime.fromtimestamp(
            hour, UTC
        )
        assert datetime.fromisoformat(rows[0]["fetched_at"]).tzinfo is not None
        assert not session.closed
    assert session.closed
    assert len(aioclient_mock.mock_calls) == 1
    url = str(aioclient_mock.mock_calls[0][1])
    assert "models=meteoswiss_icon_seamless" in url
    assert "forecast_hours=120" in url
    assert "past_hours=25" in url
    assert "timezone=Europe/Zurich" in url
    assert "timeformat=unixtime" in url


@pytest.mark.parametrize(
    "response", [{"status": 404}, {"text": "47.451234 latitude=8.561234"}]
)
async def test_icon_client_errors_hide_location_and_payload(aioclient_mock, response):
    aioclient_mock.get(OPEN_METEO_BASE_URL, **response)
    async with aioclient_mock.create_session(asyncio.get_running_loop()) as session:
        client = IconForecastClient(47.451234, 8.561234, session)
        with pytest.raises(IconForecastError) as raised:
            await client.async_get_data()
        assert str(raised.value) == ""
        assert raised.value.__suppress_context__
        rendered = "".join(traceback.format_exception(raised.value))
        assert "47.451234" not in rendered
        assert "8.561234" not in rendered
        assert "latitude=" not in rendered
        assert not session.closed
    assert len(aioclient_mock.mock_calls) == 1


async def test_icon_client_cancellation_keeps_borrowed_session_open(aioclient_mock):
    aioclient_mock.get(OPEN_METEO_BASE_URL, exc=asyncio.CancelledError())
    async with aioclient_mock.create_session(asyncio.get_running_loop()) as session:
        with pytest.raises(asyncio.CancelledError):
            await IconForecastClient(47.451234, 8.561234, session).async_get_data()
        assert not session.closed
    assert len(aioclient_mock.mock_calls) == 1


async def test_icon_client_missing_coordinates_are_a_private_source_error():
    with pytest.raises(IconForecastError) as raised:
        await IconForecastClient(None, 8.56).async_get_data()
    assert str(raised.value) == ""


async def test_icon_client_missing_session_keeps_the_setup_error():
    with pytest.raises(RuntimeError, match="No session provided"):
        await IconForecastClient(47.45, 8.56).async_get_data()

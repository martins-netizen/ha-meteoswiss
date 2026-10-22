"""Measured pollen can be consumed without an HA coordinator/runtime."""

import asyncio
from datetime import UTC, datetime

import pytest

import custom_components.meteoswiss.pollen_meteoswiss as measured


async def test_measured_client_uses_borrowed_session_and_preserves_zero(aioclient_mock):
    stamp = datetime.now(UTC).isoformat()
    url = f"{measured.POLLEN_DATA_BASE_URL}/pzh/ogd-pollen_pzh_h_now.csv"
    aioclient_mock.get(
        url, text=f"station_abbr;reference_timestamp;kaquerh0\nPZH;{stamp};0\n"
    )
    async with aioclient_mock.create_session(asyncio.get_running_loop()) as session:
        client = measured.MeteoSwissPollenClient("PZH", session=session)
        data = await client.async_get_data()
        assert client.station_id == "pzh"
        assert data["station_id"] == "PZH"
        assert data["oak"]["current"] == 0
        assert data["oak"]["history_24h"] == [0]
        assert data["birch"]["current"] is None
        assert data["last_update"] == stamp
        assert not session.closed
    assert session.closed
    assert len(aioclient_mock.mock_calls) == 1


@pytest.mark.parametrize(
    "response,error_name",
    [
        ({"status": 404}, "MeasuredPollenUnavailable"),
        ({"text": "<html>unavailable</html>"}, "InvalidMeasuredPollenData"),
    ],
)
async def test_measured_client_errors_do_not_require_ha_exceptions(
    aioclient_mock, response, error_name
):
    url = f"{measured.POLLEN_DATA_BASE_URL}/pzh/ogd-pollen_pzh_h_now.csv"
    aioclient_mock.get(url, **response)
    async with aioclient_mock.create_session(asyncio.get_running_loop()) as session:
        client = measured.MeteoSwissPollenClient("PZH", session=session)
        with pytest.raises(getattr(measured, error_name)) as raised:
            await client.async_get_data()
        assert raised.value.__class__.__module__ == measured.__name__
        assert str(raised.value) == ""
        assert not session.closed
    assert len(aioclient_mock.mock_calls) == 1


async def test_measured_client_propagates_cancellation_and_keeps_session_open(
    aioclient_mock,
):
    url = f"{measured.POLLEN_DATA_BASE_URL}/pzh/ogd-pollen_pzh_h_now.csv"
    aioclient_mock.get(url, exc=asyncio.CancelledError())
    async with aioclient_mock.create_session(asyncio.get_running_loop()) as session:
        client = measured.MeteoSwissPollenClient("PZH", session=session)
        with pytest.raises(asyncio.CancelledError):
            await client.async_get_data()
        assert not session.closed
    assert len(aioclient_mock.mock_calls) == 1

"""Borrowed-session catalogue, coalescing, TTL, failures and HTTP limits."""

import asyncio
import traceback
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest

from custom_components.meteoswiss.forecast_location_client import (
    FORECAST_CATALOGUE_RETRY_DELAY,
    FORECAST_CATALOGUE_TTL,
    ForecastCatalogueUnavailable,
    MeteoSwissForecastCatalogueClient,
)
from custom_components.meteoswiss.forecast_locations import FORECAST_CATALOGUE_URL
from custom_components.meteoswiss.http import MAX_CATALOGUE_BYTES, OGD_HOST

MODULE = "custom_components.meteoswiss.forecast_location_client"
FIXTURE = Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv"


@pytest.fixture
def source(monkeypatch, freezer):
    freezer.move_to("2026-10-23T17:26:49+00:00")
    session = Mock(spec=aiohttp.ClientSession)
    session.close = AsyncMock()
    clock = Mock(return_value=100.0)
    monkeypatch.setattr(MODULE + ".monotonic", clock)
    client = MeteoSwissForecastCatalogueClient(session)
    yield client, session, clock, FIXTURE.read_text().encode("latin-1")
    session.close.assert_not_called()


async def test_source_has_no_ha_object_and_fixed_bounded_destination(source):
    client, session, _, content = source
    assert client.last_good_snapshot is None
    with patch(MODULE + ".async_get_bytes", return_value=content) as download:
        snapshot = await client.async_get_catalogue()
    download.assert_awaited_once_with(
        session, FORECAST_CATALOGUE_URL, host=OGD_HOST, max_bytes=MAX_CATALOGUE_BYTES
    )
    assert snapshot.retrieved_at.isoformat() == "2026-10-23T17:26:49+00:00"
    assert snapshot.points[0].name == "Säntis"
    assert client.last_good_snapshot is snapshot


async def test_cache_hit_does_not_extend_original_ttl_and_boundary_refreshes(source):
    client, _, clock, content = source
    with patch(MODULE + ".async_get_bytes", return_value=content) as download:
        initial = await client.async_get_catalogue()
        clock.return_value = 100 + FORECAST_CATALOGUE_TTL - 1
        assert await client.async_get_catalogue() is initial
        clock.return_value += 1
        refreshed = await client.async_get_catalogue()
        assert refreshed is not initial
        assert refreshed.sha256 == initial.sha256
    assert download.await_count == 2


async def test_simultaneous_catalogue_users_share_one_download(source):
    client, _, _, content = source
    entered, release = asyncio.Event(), asyncio.Event()

    async def download(*args, **kwargs):
        entered.set()
        await release.wait()
        return content

    with patch(MODULE + ".async_get_bytes", side_effect=download) as request:
        first = asyncio.create_task(client.async_get_catalogue())
        await entered.wait()
        second = asyncio.create_task(client.async_get_catalogue())
        release.set()
        left, right = await asyncio.gather(first, second)
    assert left is right
    assert request.await_count == 1


@pytest.mark.parametrize(
    "error,attempts",
    [
        (aiohttp.ClientConnectionError("private_marker"), 3),
        (TimeoutError("private_marker"), 3),
        (aiohttp.InvalidURL("private_marker"), 1),
        (aiohttp.ClientSSLError(None, OSError("private_marker")), 1),
        (ValueError("private_marker"), 1),
        (TypeError("private_marker"), 1),
    ],
)
async def test_expected_errors_are_private_and_only_transport_is_retried(
    source, error, attempts
):
    client, _, _, _ = source
    with (
        patch(MODULE + ".async_get_bytes", side_effect=error) as request,
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ),
        pytest.raises(ForecastCatalogueUnavailable) as caught,
    ):
        await client.async_get_catalogue()
    assert str(caught.value) == ""
    assert "private_marker" not in "".join(traceback.format_exception(caught.value))
    assert request.await_count == attempts
    assert client.last_good_snapshot is None


async def test_failed_initial_load_is_throttled_then_recovers_at_retry_boundary(source):
    client, _, clock, content = source
    with patch(
        MODULE + ".async_get_bytes", side_effect=ValueError("private_marker")
    ) as request:
        with pytest.raises(ForecastCatalogueUnavailable):
            await client.async_get_catalogue()
        clock.return_value += FORECAST_CATALOGUE_RETRY_DELAY - 1
        with pytest.raises(ForecastCatalogueUnavailable):
            await client.async_get_catalogue()
    assert request.await_count == 1
    clock.return_value += 1
    with patch(MODULE + ".async_get_bytes", return_value=content):
        assert await client.async_get_catalogue() is client.last_good_snapshot


async def test_invalid_refresh_preserves_old_provenance_without_silent_stale_success(
    source,
):
    client, _, clock, content = source
    with patch(MODULE + ".async_get_bytes", return_value=content):
        initial = await client.async_get_catalogue()
    clock.return_value = 100 + FORECAST_CATALOGUE_TTL
    with patch(MODULE + ".async_get_bytes", return_value=b"private_marker") as request:
        with pytest.raises(ForecastCatalogueUnavailable):
            await client.async_get_catalogue()
    assert request.await_count == 1
    assert client.last_good_snapshot is initial
    assert client.last_good_snapshot.retrieved_at == initial.retrieved_at
    assert client.last_good_snapshot.sha256 == initial.sha256
    clock.return_value += FORECAST_CATALOGUE_RETRY_DELAY
    with patch(
        MODULE + ".async_get_bytes",
        return_value=content.replace(b"Kloten", b"Kloten updated"),
    ):
        updated = await client.async_get_catalogue()
    assert updated is client.last_good_snapshot and updated.sha256 != initial.sha256


@pytest.mark.parametrize("stage", ["download", "parse"])
async def test_cancellation_propagates_without_retries_or_cache_poisoning(
    source, stage
):
    client, _, _, content = source
    with patch(MODULE + ".async_get_bytes", return_value=content) as download:
        if stage == "download":
            download.side_effect = asyncio.CancelledError()
            with pytest.raises(asyncio.CancelledError):
                await client.async_get_catalogue()
        else:
            with patch(
                MODULE + ".asyncio.to_thread", side_effect=asyncio.CancelledError()
            ):
                with pytest.raises(asyncio.CancelledError):
                    await client.async_get_catalogue()
    assert download.await_count == 1
    assert client.last_good_snapshot is None
    with patch(MODULE + ".async_get_bytes", return_value=content):
        assert await client.async_get_catalogue()


async def test_total_deadline_includes_retry_waits(source, monkeypatch):
    client, _, _, _ = source
    monkeypatch.setattr(MODULE + ".DEFAULT_API_TIMEOUT", aiohttp.ClientTimeout(total=0))

    async def slow_download(*args, **kwargs):
        await asyncio.sleep(0)

    with (
        patch(MODULE + ".async_get_bytes", side_effect=slow_download) as request,
        pytest.raises(ForecastCatalogueUnavailable),
    ):
        await client.async_get_catalogue()
    assert request.await_count == 1
    assert client.last_good_snapshot is None


@pytest.mark.parametrize(
    "case", ["valid", "redirect", "oversized", "permanent", "retry_after"]
)
async def test_real_http_path_retains_destination_and_size_policy(aioclient_mock, case):
    body = FIXTURE.read_text().encode("latin-1")
    if case == "valid":
        aioclient_mock.get(FORECAST_CATALOGUE_URL, content=body)
    elif case == "redirect":
        aioclient_mock.get(
            FORECAST_CATALOGUE_URL,
            status=302,
            headers={"Location": "https://untrusted.invalid/private_marker"},
        )
    elif case == "oversized":
        aioclient_mock.get(
            FORECAST_CATALOGUE_URL, content=b"x" * (MAX_CATALOGUE_BYTES + 1)
        )
    elif case == "permanent":
        aioclient_mock.get(FORECAST_CATALOGUE_URL, status=404)
    else:
        aioclient_mock.get(
            FORECAST_CATALOGUE_URL, status=429, headers={"Retry-After": "20"}
        )
    async with aioclient_mock.create_session(asyncio.get_running_loop()) as session:
        client = MeteoSwissForecastCatalogueClient(session)
        if case == "valid":
            assert len((await client.async_get_catalogue()).points) == 7
        else:
            with pytest.raises(ForecastCatalogueUnavailable):
                await client.async_get_catalogue()
        assert not session.closed
    assert len(aioclient_mock.mock_calls) == 1

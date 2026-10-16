"""Provider throttling and bounded retry regressions, independent of warning codes."""

from __future__ import annotations

import asyncio
import ssl
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest

from custom_components.meteoswiss.retry import async_retry_with_backoff


def http_error(status=429, retry_after=None):
    return aiohttp.ClientResponseError(
        SimpleNamespace(real_url="https://example.invalid/private?location=hidden"),
        (),
        status=status,
        headers={} if retry_after is None else {"Retry-After": retry_after},
    )


@pytest.mark.parametrize("status", [408, 429, 500, 503, 599])
@pytest.mark.parametrize("header", ["60", "Fri, 16 Oct 2026 18:01:00 GMT", "9" * 400])
async def test_long_server_pause_prevents_an_early_retry(status, header, freezer):
    freezer.move_to("2026-10-16T18:00:00Z")
    error = http_error(status, header)
    call = AsyncMock(side_effect=[error, "must not be reached"])
    with (
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ) as sleep,
        pytest.raises(aiohttp.ClientResponseError) as raised,
    ):
        await async_retry_with_backoff()(call)()
    assert raised.value is error
    call.assert_awaited_once()
    sleep.assert_not_awaited()


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        ("5", 5),
        (" 5 ", 5),
        ("0", 1),
        ("10", 10),
        ("Fri, 16 Oct 2026 18:00:05 GMT", 5),
        ("Friday, 16-Oct-26 18:00:05 GMT", 5),
        ("Fri Oct 16 18:00:05 2026", 5),
        ("Fri, 16 Oct 2026 19:00:05 +0100", 5),
        ("Fri, 16 Oct 2026 17:59:59 GMT", 1),
        (None, 1),
        ("", 1),
        ("bad", 1),
        ("-5", 1),
        ("0.5", 1),
        ("nan", 1),
        ("inf", 1),
        ("-inf", 1),
        (5, 1),
    ],
)
async def test_server_pause_or_normal_backoff_is_used(header, expected, freezer):
    freezer.move_to("2026-10-16T18:00:00Z")
    call = AsyncMock(side_effect=[http_error(retry_after=header), 0])
    with patch(
        "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
    ) as sleep:
        assert await async_retry_with_backoff()(call)("value", keyword=False) == 0
    sleep.assert_awaited_once_with(expected)
    assert call.await_count == 2
    call.assert_awaited_with("value", keyword=False)


@pytest.mark.parametrize("status", [200, 301, 400, 401, 403, 404, 499, 600])
async def test_non_transient_http_status_never_retries(status):
    error = http_error(status, "5")
    call = AsyncMock(side_effect=error)
    with (
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ) as sleep,
        pytest.raises(aiohttp.ClientResponseError) as raised,
    ):
        await async_retry_with_backoff()(call)()
    assert raised.value is error
    call.assert_awaited_once()
    sleep.assert_not_awaited()


@pytest.mark.parametrize(
    "error",
    [
        aiohttp.InvalidURL("https://[invalid"),
        aiohttp.ClientSSLError(SimpleNamespace(), ssl.SSLError("TLS failed")),
        aiohttp.ServerFingerprintMismatch(
            b"expected", b"actual", "example.invalid", 443
        ),
        ValueError("invalid provider data"),
        asyncio.CancelledError(),
    ],
)
async def test_invalid_url_tls_data_and_cancellation_are_not_retried(error):
    call = AsyncMock(side_effect=error)
    with (
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ) as sleep,
        pytest.raises(type(error)) as raised,
    ):
        await async_retry_with_backoff()(call)()
    assert raised.value is error
    call.assert_awaited_once()
    sleep.assert_not_awaited()


@pytest.mark.parametrize(
    "error",
    [TimeoutError(), aiohttp.ClientConnectionError(), aiohttp.ClientPayloadError()],
)
async def test_attempt_count_backoff_cap_and_final_error_are_preserved(error):
    call = AsyncMock(side_effect=error)
    with (
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ) as sleep,
        pytest.raises(type(error)) as raised,
    ):
        await async_retry_with_backoff(max_attempts=5, base_delay=2, max_delay=5)(
            call
        )()
    assert raised.value is error
    assert call.await_count == 5
    assert [args.args[0] for args in sleep.await_args_list] == [2, 4, 5, 5]


async def test_cancel_while_waiting_stops_without_another_request():
    call = AsyncMock(side_effect=TimeoutError())
    with patch(
        "custom_components.meteoswiss.retry.asyncio.sleep",
        side_effect=asyncio.CancelledError(),
    ), pytest.raises(asyncio.CancelledError):
        await async_retry_with_backoff()(call)()
    call.assert_awaited_once()


async def test_outer_refresh_timeout_remains_the_total_budget():
    call = AsyncMock(side_effect=TimeoutError())
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.01):
            await async_retry_with_backoff(base_delay=1)(call)()
    call.assert_awaited_once()


@pytest.mark.parametrize("attempts", [0, -1, 1.5, True, "4"])
def test_invalid_attempt_count_is_rejected(attempts):
    with pytest.raises(ValueError):
        async_retry_with_backoff(max_attempts=attempts)


@pytest.mark.parametrize("field", ["base_delay", "max_delay"])
@pytest.mark.parametrize("value", [-1, float("nan"), float("inf"), True, "1"])
def test_invalid_delay_is_rejected(field, value):
    with pytest.raises(ValueError):
        async_retry_with_backoff(**{field: value})


async def test_zero_delay_and_single_attempt_are_supported():
    call = AsyncMock(side_effect=TimeoutError())
    with (
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ) as sleep,
        pytest.raises(TimeoutError),
    ):
        await async_retry_with_backoff(max_attempts=1, base_delay=0, max_delay=0)(
            call
        )()
    call.assert_awaited_once()
    sleep.assert_not_awaited()

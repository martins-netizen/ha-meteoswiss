"""Bounded retries for transient HTTP failures only."""

from __future__ import annotations

import asyncio
import math
from collections.abc import Callable
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from functools import wraps
from typing import Any

import aiohttp


def _retry_after_seconds(value: str | None) -> float | None:
    """Read RFC 9110 delay-seconds or an HTTP-date, without logging headers."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if value.isascii() and value.isdecimal():
        # An enormous valid value may become infinity; the caller will defer
        # instead of passing it to sleep or retrying earlier than requested.
        return float(value)
    try:
        deadline = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        return None
    if deadline.tzinfo is None:
        # The obsolete asctime HTTP-date form also denotes GMT.
        deadline = deadline.replace(tzinfo=UTC)
    return max(0.0, (deadline - datetime.now(UTC)).total_seconds())


def async_retry_with_backoff(
    max_attempts: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
) -> Callable:
    """Retry timeouts, connection errors, HTTP 408/429 and server errors.

    Invalid payloads/URLs, TLS failures and permanent HTTP errors propagate
    immediately. Retry-After accepts seconds or HTTP dates. A server pause
    beyond max_delay aborts this retry sequence; later coordinator refreshes
    keep their normal schedule. Cancellation is never intercepted.
    """
    if type(max_attempts) is not int or max_attempts < 1:
        raise ValueError("max_attempts must be a positive integer")
    for delay in (base_delay, max_delay):
        if (
            isinstance(delay, bool)
            or not isinstance(delay, (int, float))
            or not math.isfinite(delay)
            or delay < 0
        ):
            raise ValueError("retry delays must be finite non-negative numbers")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            attempt = 1
            backoff = min(base_delay, max_delay)
            while True:
                try:
                    return await func(*args, **kwargs)
                except (
                    aiohttp.InvalidURL,
                    aiohttp.ClientSSLError,
                    aiohttp.ServerFingerprintMismatch,
                ):
                    raise
                except (aiohttp.ClientError, TimeoutError) as err:
                    if (
                        isinstance(err, aiohttp.ClientResponseError)
                        and err.status not in (408, 429)
                        and not 500 <= err.status < 600
                    ):
                        raise
                    if attempt == max_attempts:
                        raise
                    delay = backoff
                    if isinstance(err, aiohttp.ClientResponseError) and err.headers:
                        retry_after = _retry_after_seconds(
                            err.headers.get("Retry-After")
                        )
                        if retry_after is not None:
                            if retry_after > max_delay:
                                raise
                            delay = max(retry_after, delay)
                    await asyncio.sleep(delay)
                    attempt += 1
                    backoff = min(backoff * 2, max_delay)

        return wrapper

    return decorator

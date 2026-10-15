"""Bounded retries for transient HTTP failures only."""

from __future__ import annotations

import asyncio
from functools import wraps
from typing import Any, Callable

import aiohttp


def async_retry_with_backoff(
    max_attempts: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 10.0,
) -> Callable:
    """Retry timeouts, connection errors, HTTP 408/429 and server errors.

    Invalid payloads and permanent HTTP errors propagate immediately.
    Cancellation is never intercepted.
    """
    if max_attempts < 1:
        raise ValueError("max_attempts must be positive")

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except (aiohttp.ClientError, TimeoutError) as err:
                    if isinstance(err, aiohttp.ClientResponseError):
                        if err.status not in (408, 429) and err.status < 500:
                            raise
                    if attempt + 1 == max_attempts:
                        raise
                    delay = min(base_delay * 2**attempt, max_delay)
                    if isinstance(err, aiohttp.ClientResponseError) and err.headers:
                        try:
                            retry_after = float(err.headers.get("Retry-After", delay))
                            if retry_after > max_delay:
                                # Defer to the next coordinator refresh rather
                                # than retrying earlier than the server allows.
                                raise err
                            delay = min(max(retry_after, delay), max_delay)
                        except (TypeError, ValueError):
                            pass
                    await asyncio.sleep(delay)

        return wrapper

    return decorator

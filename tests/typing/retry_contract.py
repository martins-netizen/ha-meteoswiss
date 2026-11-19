"""Static type contract for a retry decorator shared by different async callables."""

import asyncio
from typing import assert_type

from custom_components.meteoswiss.retry import async_retry_with_backoff

retry = async_retry_with_backoff()


@retry
async def temperature(station: str, /, *, hourly: bool) -> float:
    return 2.5


@retry
async def catalogue(index: int) -> bytes:
    return bytes(index)


async def check_retry_contract() -> None:
    assert_type(await temperature("KLO", hourly=True), float)
    assert_type(await asyncio.create_task(catalogue(index=2)), bytes)
    stacked = retry(func=temperature)
    assert_type(await asyncio.create_task(stacked("KLO", hourly=False)), float)

    # Strict mypy reports an unused ignore if the decorator starts accepting
    # any of these argument types or keyword spellings.
    await catalogue("KLO")  # type: ignore[arg-type]
    await temperature("KLO", hours=True)  # type: ignore[call-arg]
    await temperature(station="KLO", hourly=True)  # type: ignore[call-arg]

"""Fixed-destination, bounded HTTP reads shared by active data sources.

Callers retain their HA-owned session, retries and source-specific parsing.
Redirects are deliberately refused: provider moves need an explicit review.
"""

from __future__ import annotations

import json
import zlib
from typing import Any
from urllib.parse import urlsplit

import aiohttp

from .const import DEFAULT_API_TIMEOUT

OGD_HOST = "data.geo.admin.ch"
FORECAST_HOST = "api.open-meteo.com"
AIR_QUALITY_HOST = "air-quality-api.open-meteo.com"
WARNING_HOST = "app-prod-ws.meteoswiss-app.ch"

# Separate conservative budgets for metadata, observations and decade archives.
MAX_JSON_BYTES = 2 * 1024 * 1024
MAX_CSV_BYTES = 16 * 1024 * 1024
MAX_ARCHIVE_BYTES = 64 * 1024 * 1024
MAX_CATALOGUE_BYTES = 2 * 1024 * 1024
_READ_CHUNK = 64 * 1024


def validate_source_url(url: str, host: str) -> None:
    """Refuse ambiguous URLs before a request; never include the URL in errors."""
    if not isinstance(url, str) or any(
        ord(c) <= 32 or ord(c) == 127 or c == "\\" for c in url
    ):
        raise ValueError("Invalid source destination")
    try:
        parsed = urlsplit(url)
    except ValueError:
        raise ValueError("Invalid source destination") from None
    if (
        parsed.scheme != "https"
        or parsed.netloc.lower() not in (host, f"{host}:443")
        or parsed.fragment
    ):
        raise ValueError("Unapproved source destination")


async def async_get_bytes(
    session: aiohttp.ClientSession,
    url: str,
    *,
    host: str,
    max_bytes: int,
    params: dict[str, Any] | None = None,
) -> bytes:
    """Bound wire and decoded bytes without aiohttp's unbounded decompression.

    Advertise only supported encodings. Missing/dishonest Content-Length cannot
    bypass the streaming limits. Limit+1 detects excess without inflating a
    compression bomb fully. Cancellation and transport errors propagate.
    """
    validate_source_url(url, host)
    async with session.get(
        url,
        params=params,
        timeout=DEFAULT_API_TIMEOUT,
        allow_redirects=False,
        auto_decompress=False,
        headers={"Accept-Encoding": "gzip, deflate"},
    ) as response:
        response.raise_for_status()
        if not 200 <= response.status < 300:
            raise ValueError("Source redirect or unexpected HTTP status")
        encoding = response.headers.get("Content-Encoding", "identity").strip().lower()
        if encoding not in ("identity", "gzip", "deflate"):
            raise ValueError("Unsupported source content encoding")
        decoder = (
            zlib.decompressobj(31 if encoding == "gzip" else 15)
            if encoding != "identity"
            else None
        )
        body = bytearray()
        received = 0
        stream = response.content
        while chunk := await stream.read(min(_READ_CHUNK, max_bytes - received + 1)):
            received += len(chunk)
            if received > max_bytes:
                raise ValueError("Source response exceeds wire size limit")
            if decoder is not None:
                try:
                    chunk = decoder.decompress(chunk, max_bytes - len(body) + 1)
                except zlib.error:
                    raise ValueError("Invalid compressed source response") from None
            body.extend(chunk)
            if len(body) > max_bytes:
                raise ValueError("Source response exceeds decoded size limit")
        if decoder is not None and (not decoder.eof or decoder.unused_data):
            raise ValueError("Incomplete or trailing compressed source response")
        return bytes(body)


async def async_get_json(
    session: aiohttp.ClientSession,
    url: str,
    *,
    host: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """Decode only a complete, size-checked JSON body."""
    return json.loads(
        await async_get_bytes(
            session, url, host=host, max_bytes=MAX_JSON_BYTES, params=params
        )
    )

"""Destination, redirect, streaming and decompression trust boundaries."""

import asyncio
import gzip
import io
import zlib
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.meteoswiss import http
from custom_components.meteoswiss.alerts import MeteoSwissAlertsAPI
from custom_components.meteoswiss.coordinator import (
    MeteoSwissDataUpdateCoordinator,
    MeteoSwissHourlyPrecipitationCoordinator,
    MeteoSwissPollenCoordinator,
)

URL = "https://data.geo.admin.ch/data.csv"


def session_for(body=b"", *, encoding=None, status=200, failure=None):
    stream = AsyncMock()
    stream.read.side_effect = failure or io.BytesIO(body).read
    response = SimpleNamespace(
        status=status,
        headers={} if encoding is None else {"Content-Encoding": encoding},
        content=stream,
        raise_for_status=MagicMock(),
    )
    context = MagicMock()
    context.__aenter__ = AsyncMock(return_value=response)
    context.__aexit__ = AsyncMock(return_value=False)
    session = MagicMock()
    session.get.return_value = context
    return session, response


@pytest.mark.parametrize(
    "url",
    [
        None,
        "http://data.geo.admin.ch/a",
        "//data.geo.admin.ch/a",
        "https://127.0.0.1/a",
        "https://[::1]/a",
        "https://169.254.169.254/latest",
        "https://data.geo.admin.ch.evil.invalid/a",
        "https://evil.invalid/data.geo.admin.ch",
        "https://data.geo.admin.ch:444/a",
        "https://data.geo.admin.ch:0443/a",
        "https://user@data.geo.admin.ch/a",
        "https://data.geo.admin.ch@evil.invalid/a",
        "https://data.geo.admin.ch./a",
        "https://data%2egeo.admin.ch/a",
        " https://data.geo.admin.ch/a",
        "https://data.geo.admin.ch/a\n",
        "https://data.geo.admin.ch/\x00",
        "https://data.geo.admin.ch/\x7f",
        "https://data.geo.admin.ch\\@evil.invalid/a",
        "https://[broken/a",
        "https://data.geo.admin.ch/a#secret",
    ],
)
async def test_invalid_destination_never_starts_request(url):
    session, _ = session_for()
    with pytest.raises(ValueError) as error:
        await http.async_get_bytes(session, url, host=http.OGD_HOST, max_bytes=100)
    session.get.assert_not_called()
    assert "secret" not in str(error.value)
    assert "evil" not in str(error.value)


@pytest.mark.parametrize(
    "host",
    [http.OGD_HOST, http.FORECAST_HOST, http.AIR_QUALITY_HOST, http.WARNING_HOST],
)
async def test_each_source_has_only_its_own_destination(host):
    session, _ = session_for()
    other = http.FORECAST_HOST if host == http.OGD_HOST else http.OGD_HOST
    with pytest.raises(ValueError):
        await http.async_get_bytes(
            session, f"https://{other}/data", host=host, max_bytes=10
        )
    session.get.assert_not_called()
    await http.async_get_bytes(
        session, f"https://{host.upper()}:443/data", host=host, max_bytes=10
    )
    assert session.get.call_count == 1


@pytest.mark.parametrize("status", [201, 204, 200])
async def test_complete_bounded_read_preserves_session_and_request_options(status):
    body = b"x" * (http._READ_CHUNK + 5)
    session, response = session_for(body, status=status)
    result = await http.async_get_bytes(
        session, URL, host=http.OGD_HOST, max_bytes=len(body), params={"a": 2}
    )
    assert result == body
    assert response.content.read.call_count == 3
    options = session.get.call_args.kwargs
    assert options["allow_redirects"] is False
    assert options["auto_decompress"] is False
    assert options["headers"] == {"Accept-Encoding": "gzip, deflate"}
    assert options["timeout"].total == 30
    assert options["params"] == {"a": 2}
    session.close.assert_not_called()
    session.get.return_value.__aexit__.assert_awaited_once()


@pytest.mark.parametrize("status", [300, 301, 302, 303, 304, 307, 308])
async def test_redirect_is_refused_without_reading_or_following(status):
    session, response = session_for(status=status)
    response.headers["Location"] = "http://169.254.169.254/private"
    with pytest.raises(ValueError, match="redirect"):
        await http.async_get_bytes(session, URL, host=http.OGD_HOST, max_bytes=100)
    response.content.read.assert_not_called()
    assert session.get.call_count == 1


@pytest.mark.parametrize("length", [None, "1", "999999999"])
async def test_wire_limit_ignores_missing_or_dishonest_content_length(length):
    session, response = session_for(b"x" * 100)
    if length is not None:
        response.headers["Content-Length"] = length
    with pytest.raises(ValueError, match="wire size"):
        await http.async_get_bytes(session, URL, host=http.OGD_HOST, max_bytes=10)
    assert response.content.read.call_args.args == (11,)


@pytest.mark.parametrize(
    "encoding,compress", [("gzip", gzip.compress), ("deflate", zlib.compress)]
)
async def test_bounded_decompression_preserves_valid_bytes(encoding, compress):
    body = b"abc" * 50000
    session, _ = session_for(compress(body), encoding=encoding)
    assert (
        await http.async_get_bytes(
            session, URL, host=http.OGD_HOST, max_bytes=len(body)
        )
        == body
    )


@pytest.mark.parametrize(
    "encoding,compress", [("gzip", gzip.compress), ("deflate", zlib.compress)]
)
async def test_compression_bomb_is_stopped_at_decoded_budget(encoding, compress):
    session, response = session_for(compress(b"x" * 1000000), encoding=encoding)
    with pytest.raises(ValueError, match="decoded size"):
        await http.async_get_bytes(session, URL, host=http.OGD_HOST, max_bytes=2000)
    assert response.content.read.call_count == 1


@pytest.mark.parametrize(
    "body",
    [b"broken", gzip.compress(b"hello")[:-4], gzip.compress(b"hello") + b"trailing"],
)
async def test_corrupt_truncated_and_trailing_compressed_data_fail(body):
    session, _ = session_for(body, encoding="gzip")
    with pytest.raises(ValueError, match="compressed source"):
        await http.async_get_bytes(session, URL, host=http.OGD_HOST, max_bytes=100)


@pytest.mark.parametrize("encoding", ["br", "zstd", "gzip, deflate"])
async def test_unadvertised_or_stacked_encodings_fail_before_read(encoding):
    session, response = session_for(encoding=encoding)
    with pytest.raises(ValueError, match="encoding"):
        await http.async_get_bytes(session, URL, host=http.OGD_HOST, max_bytes=100)
    response.content.read.assert_not_called()


@pytest.mark.parametrize(
    "failure", [asyncio.CancelledError, TimeoutError, aiohttp.ClientConnectionError]
)
async def test_stream_failure_and_cancellation_propagate_and_close(failure):
    session, _ = session_for(failure=failure())
    with pytest.raises(failure):
        await http.async_get_bytes(session, URL, host=http.OGD_HOST, max_bytes=100)
    session.get.return_value.__aexit__.assert_awaited_once()


async def test_json_decoding_occurs_only_after_a_bounded_read():
    session, _ = session_for(b'{"value": 0}')
    assert await http.async_get_json(session, URL, host=http.OGD_HOST) == {"value": 0}
    session, _ = session_for(b"{} trailing")
    with pytest.raises(ValueError):
        await http.async_get_json(session, URL, host=http.OGD_HOST)


async def test_untrusted_stac_asset_cannot_fetch_or_import(hass, aioclient_mock):
    from custom_components.meteoswiss.const import API_BASE, STAC_COLLECTION

    metadata = f"{API_BASE}/collections/{STAC_COLLECTION}/items/klo"
    aioclient_mock.get(
        metadata,
        json={
            "assets": {
                "ogd-smn_klo_t_now.csv": {"href": "http://127.0.0.1/private"},
                "ogd-smn_klo_h_now.csv": {"href": "https://evil.invalid/private"},
            }
        },
    )
    session = async_get_clientsession(hass)
    current = MeteoSwissDataUpdateCoordinator(hass, "KLO", 600, session)
    with pytest.raises(UpdateFailed):
        await current._async_update_data()
    hourly = MeteoSwissHourlyPrecipitationCoordinator(hass, "KLO", session)
    with patch(
        "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
    ) as queue:
        with pytest.raises(UpdateFailed):
            await hourly._async_update_data()
    queue.assert_not_called()
    assert len(aioclient_mock.mock_calls) == 2  # Metadata only; neither asset fetched.


async def test_archive_has_a_separate_budget_and_keeps_provider_encoding(
    hass, aioclient_mock
):
    source = MeteoSwissHourlyPrecipitationCoordinator(
        hass, "KLO", async_get_clientsession(hass)
    )
    body = "Météo" * 20
    aioclient_mock.get(URL, content=body.encode("cp1252"))
    with (
        patch("custom_components.meteoswiss.precipitation.MAX_CSV_BYTES", 50),
        patch("custom_components.meteoswiss.precipitation.MAX_ARCHIVE_BYTES", 200),
    ):
        with pytest.raises(ValueError, match="size"):
            await source.client._async_download_hourly_csv(URL, "now")
        assert await source.client._async_download_hourly_csv(URL, "historical") == body


async def test_warning_redirect_is_unavailable_not_all_clear(hass, aioclient_mock):
    aioclient_mock.get(
        "https://app-prod-ws.meteoswiss-app.ch/v3/plzDetail",
        status=302,
        headers={"Location": "https://evil.invalid/"},
    )
    with pytest.raises(ValueError):
        await MeteoSwissAlertsAPI(async_get_clientsession(hass)).get_alerts("8302")
    assert len(aioclient_mock.mock_calls) == 1


async def test_measured_pollen_limit_is_a_source_failure_without_retry(
    hass, aioclient_mock
):
    aioclient_mock.get(
        "https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/pzh/ogd-pollen_pzh_h_now.csv",
        content=b"x" * 100,
    )
    source = MeteoSwissPollenCoordinator(
        hass, "PZH", session=async_get_clientsession(hass)
    )
    with patch("custom_components.meteoswiss.pollen_meteoswiss.MAX_CSV_BYTES", 50):
        with pytest.raises(UpdateFailed) as caught:
            await source._async_update_data()
        assert caught.value.translation_key == "measured_pollen_unavailable"
    assert len(aioclient_mock.mock_calls) == 1


@pytest.mark.parametrize(
    "encoding,compress", [("gzip", gzip.compress), ("deflate", zlib.compress)]
)
async def test_compressed_stream_survives_split_headers_and_trailers(
    encoding, compress
):
    body = b"station;rain\nKLO;0.1\n" * 20
    session, response = session_for(encoding=encoding)
    wire = io.BytesIO(compress(body))
    response.content.read.side_effect = lambda size: wire.read(min(size, 2))
    assert (
        await http.async_get_bytes(
            session, URL, host=http.OGD_HOST, max_bytes=len(body)
        )
        == body
    )
    assert response.content.read.call_count > 10

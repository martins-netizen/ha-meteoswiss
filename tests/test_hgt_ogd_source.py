"""Official HGT product semantics and bounded conditional source requests."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from test_http_sources import URL, session_for

from custom_components.meteoswiss import hgt_ogd as hgt
from custom_components.meteoswiss import http
from custom_components.meteoswiss.const import API_BASE, STAC_COLLECTION

NOW = datetime(2026, 11, 15, 12, tzinfo=UTC)
META = f"{API_BASE}/collections/{STAC_COLLECTION}/items/klo"
SUFFIXES = [
    ("d_historical", "daily"),
    ("d_recent", "daily"),
    ("m", "monthly"),
    ("y", "annual"),
]


def csv_data(period="daily", rows=None, station="klo"):
    rows = rows if rows is not None else [("14.11.2026 00:00", "19.1")]
    return (
        "station_abbr;reference_timestamp;"
        + hgt.PERIODS[period]
        + ";label\n"
        + "\n".join(f"{station};{day};{amount};Météo" for day, amount in rows)
    ).encode("cp1252")


def assets():
    return {
        f"ogd-smn_klo_{suffix}.csv": {
            "href": f"https://{http.OGD_HOST}/{STAC_COLLECTION}/klo/ogd-smn_klo_{suffix}.csv"
        }
        for suffix, _ in SUFFIXES
    }


def resources():
    result = {
        META: http.CachedResource(
            META, json.dumps({"id": "klo", "assets": assets()}).encode(), '"meta"'
        )
    }
    dates = {
        "d_historical": [("31.12.2025 00:00", "12.3")],
        "d_recent": [("01.01.2026 00:00", "0"), ("14.11.2026 00:00", "19.1")],
        "m": [("01.10.2026 00:00", "216.9"), ("01.11.2026 00:00", "250.0")],
        "y": [("01.01.2025 00:00", "3057.8"), ("01.01.2026 00:00", "2999.0")],
    }
    for suffix, period in SUFFIXES:
        url = assets()[f"ogd-smn_klo_{suffix}.csv"]["href"]
        result[url] = http.CachedResource(
            url, csv_data(period, dates[suffix]), '"asset"'
        )
    return result


@pytest.mark.parametrize("value", ["klo", "KLO", "kL0"])
def test_station_identity_only(value):
    assert hgt.station_code(value) == value.lower()
    assert len(hgt.statistic_ids(value)) == 3


@pytest.mark.parametrize(
    "value", [None, 1, "", "kl", "kloo", "../", "a_b", "K L", "klö", "klo\n"]
)
def test_invalid_station_refused(value):
    with pytest.raises(hgt.HgtError, match="invalid_station"):
        hgt.station_code(value)


@pytest.mark.parametrize(
    "period,stamp,expected",
    [
        ("daily", "29.02.2024 00:00", datetime(2024, 3, 1, tzinfo=UTC)),
        ("daily", "25.10.2026 00:00", datetime(2026, 10, 26, tzinfo=UTC)),
        ("monthly", "01.12.2025 00:00", datetime(2026, 1, 1, tzinfo=UTC)),
        ("annual", "01.01.2025 00:00", datetime(2026, 1, 1, tzinfo=UTC)),
    ],
)
def test_utc_period_starts_and_completed_boundaries(period, stamp, expected):
    body = csv_data(period, [(stamp, "0")])
    assert (
        hgt.parse_hgt(body, "klo", period, expected - timedelta(microseconds=1)) == {}
    )
    parsed = hgt.parse_hgt(body, "klo", period, expected)
    assert list(parsed.values()) == [0]
    assert hgt.period_end(next(iter(parsed)), period) == expected


def test_missing_is_not_zero_and_no_invented_baseline_or_interpolation():
    source = csv_data(
        rows=[
            ("11.11.2026 00:00", ""),
            ("12.11.2026 00:00", "0"),
            ("13.11.2026 00:00", ""),
            ("14.11.2026 00:00", "19.1"),
            ("15.11.2026 00:00", "20.0"),
        ]
    )
    parsed = hgt.parse_hgt(source, "klo", "daily", NOW)
    assert len(parsed) == 4 and list(parsed.values()) == [None, 0, None, 191]
    assert hgt.project_hgt(parsed) == [
        {"start": datetime(2026, 11, 12, tzinfo=UTC), "state": 0, "sum": 0},
        {"start": datetime(2026, 11, 14, tzinfo=UTC), "state": 19.1, "sum": 19.1},
    ]
    assert hgt.project_hgt({}) == []
    utf8 = b"\xef\xbb\xbf" + source.decode("cp1252").encode()
    assert hgt.parse_hgt(utf8, "klo", "daily", NOW) == parsed


@pytest.mark.parametrize(
    "value", ["nan", "inf", "-inf", "-1", "1.23", "1e308", "1000.1", "private_bad"]
)
def test_invalid_amounts_are_not_silently_coerced(value):
    with pytest.raises((hgt.HgtError, ValueError)):
        hgt.parse_hgt(csv_data(rows=[("14.11.2026 00:00", value)]), "klo", "daily", NOW)


@pytest.mark.parametrize(
    "body",
    [
        b"",
        b"a;b\n1;2",
        b"station_abbr;reference_timestamp;xno000d0;xno000d0\n",
        b"station_abbr;reference_timestamp;xno000d0\nklo;14.11.2026 00:00",
        b"xno000d0;station_abbr;reference_timestamp\n0;klo",
        b"reference_timestamp;xno000d0;station_abbr\n14.11.2026 00:00;0",
        b"station_abbr;reference_timestamp;xno000d0\nklo;14.11.2026 00:00;1;extra",
    ],
)
def test_invalid_csv_shape_is_refused(body):
    with pytest.raises(hgt.HgtError, match="invalid_source"):
        hgt.parse_hgt(body, "klo", "daily", NOW)


@pytest.mark.parametrize(
    "period,stamp",
    [
        ("daily", "14.11.2026 01:00"),
        ("daily", "14.11.2026 00:01"),
        ("monthly", "02.10.2026 00:00"),
        ("annual", "01.02.2025 00:00"),
        ("daily", "invalid"),
    ],
)
def test_invalid_period_alignment(period, stamp):
    with pytest.raises((hgt.HgtError, ValueError)):
        hgt.parse_hgt(csv_data(period, [(stamp, "1")]), "klo", period, NOW)


def test_foreign_duplicate_and_bounded_rows(monkeypatch):
    with pytest.raises(hgt.HgtError, match="foreign_station"):
        hgt.parse_hgt(csv_data(station="ber"), "klo", "daily", NOW)
    identical = [("14.11.2026 00:00", "1"), ("14.11.2026 00:00", "1.0")]
    assert len(hgt.parse_hgt(csv_data(rows=identical), "klo", "daily", NOW)) == 1
    with pytest.raises(hgt.HgtError, match="ambiguous_source"):
        hgt.parse_hgt(
            csv_data(rows=[*identical, ("14.11.2026 00:00", "")]), "klo", "daily", NOW
        )
    monkeypatch.setattr(hgt, "MAX_POINTS", 1)
    with pytest.raises(hgt.HgtError, match="invalid_source"):
        hgt.parse_hgt(csv_data(rows=identical), "klo", "daily", NOW)


async def test_client_gets_separate_authoritative_products_and_revalidates_history_weekly(
    hass,
):
    client = hgt.MeteoSwissHgtClient(None, "KLO")
    source = resources()
    with patch.object(
        client, "_resource", side_effect=lambda url, budget: source[url]
    ) as fetch:
        first = await client.async_fetch(hass, NOW)
        assert len(first["daily"]) == 3 and list(first["monthly"].values()) == [2169]
        assert list(first["annual"].values()) == [30578]
        assert fetch.await_count == 5 and client.history_checked == NOW
        fetch.reset_mock()
        assert await client.async_fetch(hass, NOW + timedelta(hours=6)) == first
        assert fetch.await_count == 4
        fetch.reset_mock()
        await client.async_fetch(hass, NOW + timedelta(days=7))
        assert fetch.await_count == 5
        # Even an unchanged representation can contain a newly completed month.
        result = await client.async_fetch(hass, datetime(2026, 12, 1, tzinfo=UTC))
        assert len(result["monthly"]) == 2


async def test_recent_withdrawals_override_history(hass):
    source = resources()
    historical = assets()["ogd-smn_klo_d_historical.csv"]["href"]
    source[historical] = http.CachedResource(
        historical, csv_data(rows=[("14.11.2026 00:00", "8")])
    )
    recent = assets()["ogd-smn_klo_d_recent.csv"]["href"]
    source[recent] = http.CachedResource(
        recent, csv_data(rows=[("13.11.2026 00:00", "1"), ("14.11.2026 00:00", "")])
    )
    client = hgt.MeteoSwissHgtClient(None, "klo")
    with patch.object(client, "_resource", side_effect=lambda url, budget: source[url]):
        data = await client.async_fetch(hass, NOW)
    assert list(data["daily"].values()) == [None, 10]


@pytest.mark.parametrize(
    "data", [[], {}, {"id": "ber", "assets": {}}, {"id": "klo", "assets": []}]
)
async def test_invalid_metadata_cannot_select_assets(hass, data):
    client = hgt.MeteoSwissHgtClient(None, "klo")
    with patch.object(
        client,
        "_resource",
        return_value=http.CachedResource(META, json.dumps(data).encode()),
    ) as fetch:
        with pytest.raises(hgt.HgtError, match="invalid_source"):
            await client.async_fetch(hass, NOW)
    assert fetch.await_count == 1 and client.resources == {}


@pytest.mark.parametrize(
    "asset",
    [
        None,
        {},
        {"href": "https://127.0.0.1/private"},
        {"href": assets()["ogd-smn_klo_d_recent.csv"]["href"]},
    ],
)
async def test_exact_asset_identity_required_before_request(hass, asset):
    data = {"id": "klo", "assets": {"ogd-smn_klo_d_historical.csv": asset}}
    client = hgt.MeteoSwissHgtClient(None, "klo")
    with patch.object(
        client,
        "_resource",
        return_value=http.CachedResource(META, json.dumps(data).encode()),
    ) as fetch:
        with pytest.raises(hgt.HgtError, match="source_incomplete"):
            await client.async_fetch(hass, NOW)
    assert fetch.await_count == 1


async def test_empty_daily_cannot_be_reported_ready_and_failed_bundle_not_fresh(hass):
    source = resources()
    for suffix in ["d_recent", "d_historical"]:
        url = assets()[f"ogd-smn_klo_{suffix}.csv"]["href"]
        source[url] = http.CachedResource(url, csv_data(rows=[]))
    client = hgt.MeteoSwissHgtClient(None, "klo")
    with patch.object(client, "_resource", side_effect=lambda url, budget: source[url]):
        with pytest.raises(hgt.HgtError, match="data_unavailable"):
            await client.async_fetch(hass, NOW)
    assert client.history_checked is None


async def test_real_session_conditional_requests_keep_tls_timeout_and_cancellation(
    hass, aioclient_mock
):
    aioclient_mock.get(URL, content=b"value", headers={"ETag": '"v1"'})
    client = hgt.MeteoSwissHgtClient(async_get_clientsession(hass), "klo")
    resource = await client._resource(URL, 10)
    client.resources[URL] = resource
    aioclient_mock.clear_requests()
    aioclient_mock.get(URL, status=304)
    assert await client._resource(URL, 10) is resource
    assert aioclient_mock.mock_calls[-1][3]["If-None-Match"] == '"v1"'
    with patch.object(hgt, "async_get_resource", side_effect=asyncio.CancelledError):
        with pytest.raises(asyncio.CancelledError):
            await client._resource(URL, 10)


@pytest.mark.parametrize(
    "cached,params",
    [
        (http.CachedResource(URL + "/other", b"old"), None),
        (http.CachedResource(URL, b"123456"), None),
        (http.CachedResource(URL, b"old"), {}),
        (http.CachedResource(URL, b"old", "x" * 513), None),
        (http.CachedResource(URL, b"old", "bad\nvalidator"), None),
        (http.CachedResource(URL, b"old", "é"), None),
    ],
)
async def test_conditional_cache_identity_budget_and_header_injection(cached, params):
    session, _ = session_for()
    with pytest.raises(ValueError):
        await http.async_get_resource(
            session, URL, host=http.OGD_HOST, max_bytes=5, cached=cached, params=params
        )
    session.get.assert_not_called()


@pytest.mark.parametrize("etag", [None, '"v2"', "x" * 513, "bad\rheader", "é"])
async def test_only_bounded_printable_response_validator_is_kept(etag):
    session, response = session_for(b"new")
    if etag is not None:
        response.headers["ETag"] = etag
    resource = await http.async_get_resource(
        session, URL, host=http.OGD_HOST, max_bytes=3
    )
    assert resource.body == b"new"
    assert resource.etag == ('"v2"' if etag == '"v2"' else None)


@pytest.mark.parametrize("etag", [None, '"old"'])
async def test_304_requires_an_actual_conditional_request_and_never_reads_body(etag):
    session, response = session_for(b"ignored", status=304)
    cached = http.CachedResource(URL, b"old", etag)
    if etag:
        assert (
            await http.async_get_resource(
                session, URL, host=http.OGD_HOST, max_bytes=3, cached=cached
            )
            is cached
        )
    else:
        with pytest.raises(ValueError):
            await http.async_get_resource(
                session, URL, host=http.OGD_HOST, max_bytes=3, cached=cached
            )
    response.content.read.assert_not_called()


async def test_utc_year_rollover_revalidates_history_even_inside_weekly_cache(hass):
    client = hgt.MeteoSwissHgtClient(None, "klo")
    source = resources()
    with patch.object(
        client, "_resource", side_effect=lambda url, budget: source[url]
    ) as fetch:
        await client.async_fetch(hass, datetime(2026, 12, 31, 12, tzinfo=UTC))
        fetch.reset_mock()
        await client.async_fetch(hass, datetime(2027, 1, 1, 6, tzinfo=UTC))
        assert fetch.await_count == 5

"""Station CSV, zero/missing values, bounded transport and cache recovery."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.meteoswiss import coordinator as m
from custom_components.meteoswiss.cache import (
    clear_all_caches,
    get_current_weather_cache,
)
from custom_components.meteoswiss.const import API_BASE, STAC_COLLECTION

STATION_URL = f"{API_BASE}/collections/{STAC_COLLECTION}/items/klo"
CSV_URL = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/klo/ogd-smn_klo_t_now.csv"
RECENT_URL = (
    "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/klo/ogd-smn_klo_t_recent.csv"
)
FIELDS = [
    (m.PARAM_TEMPERATURE, "temperature"),
    (m.PARAM_HUMIDITY, "humidity"),
    (m.PARAM_WIND_SPEED, "wind_speed"),
    (m.PARAM_WIND_DIR, "wind_direction"),
    (m.PARAM_PRESSURE, "pressure"),
    (m.PARAM_PRECIPITATION, "precipitation"),
    (m.PARAM_GUST_1S, "wind_gust"),
    (m.PARAM_SUNSHINE, "sunshine_duration"),
    (m.PARAM_GLOBAL_RAD, "global_radiation"),
    (m.PARAM_SNOW_DEPTH, "snow_depth"),
    (m.PARAM_FOEHN_INDEX, "foehn_index"),
    (m.PARAM_DEW_POINT, "dew_point"),
]


@pytest.fixture(autouse=True)
def isolated_clock_cache(freezer):
    clear_all_caches()
    freezer.move_to("2026-10-16T07:50:00+00:00")
    yield
    clear_all_caches()


def station(hass, interval=600):
    return m.MeteoSwissDataUpdateCoordinator(
        hass, "KLO", interval, async_get_clientsession(hass)
    )


def row(**values):
    return {
        "station_abbr": "KLO",
        "reference_timestamp": "16.10.2026 07:40",
        m.PARAM_TEMPERATURE: "12",
        m.PARAM_HUMIDITY: "50",
        **values,
    }


def csv_rows(*rows):
    import csv
    import io

    stream = io.StringIO()
    keys = list(dict.fromkeys(k for r in rows for k in r))
    writer = csv.DictWriter(stream, fieldnames=keys, delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def assets(url=CSV_URL, kind="now"):
    return {"assets": {f"ogd-smn_klo_t_{kind}.csv": {"href": url}}}


@pytest.mark.parametrize("parameter,key", FIELDS)
async def test_valid_zero_is_retained_in_each_measurement(hass, parameter, key):
    data = station(hass)._parse_csv_row(row(**{parameter: "0"}))
    assert data[key] == 0
    assert data["last_update"] == "2026-10-16T07:40:00+00:00"


@pytest.mark.parametrize("parameter,key", FIELDS)
@pytest.mark.parametrize("bad", ["bad", "nan", "inf", "-inf"])
async def test_bad_individual_measurement_cannot_poison_the_row(
    hass, parameter, key, bad
):
    data = station(hass)._parse_csv_row(row(**{parameter: bad}))
    if key == "dew_point":
        # The existing fallback derives dew point from valid T/RH.
        assert data[key] == 1.9
    else:
        assert data[key] is None
    assert data["last_update"] == "2026-10-16T07:40:00+00:00"
    assert data["humidity" if key == "temperature" else "temperature"] == (
        50 if key == "temperature" else 12
    )


async def test_negative_temperature_and_measured_dewpoint_are_preserved(hass):
    data = station(hass)._parse_csv_row(
        row(**{m.PARAM_TEMPERATURE: "-5.2", m.PARAM_DEW_POINT: "-7.25"})
    )
    assert data["temperature"] == -5.2
    assert data["dew_point"] == -7.2


@pytest.mark.parametrize("temperature", ["-243.04", "1e308"])
async def test_invalid_derived_dewpoint_does_not_poison_other_values(hass, temperature):
    data = station(hass)._parse_csv_row(row(**{m.PARAM_TEMPERATURE: temperature}))
    assert data["dew_point"] is None
    assert data["humidity"] == 50


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        ("", None),
        ("bad", None),
        ("16.10.2026 07:00", "2026-10-16T07:00:00+00:00"),
        ("2026-10-16T09:00:00+02:00", "2026-10-16T07:00:00+00:00"),
        ("2026-10-16T07:00:00", "2026-10-16T07:00:00+00:00"),
    ],
)
def test_provider_timestamps_are_utc(value, expected):
    parsed = m._parse_reference_timestamp(value)
    assert (parsed.isoformat() if parsed else None) == expected


def test_current_hour_counts_distinct_intervals_once_and_skips_bad_numbers():
    rows = [
        row(
            **{
                "reference_timestamp": "16.10.2026 " + stamp,
                m.PARAM_PRECIPITATION: amount,
            }
        )
        for stamp, amount in [
            ("07:00", "9"),
            ("07:10", "0.1"),
            ("07:20", "0.1"),
            ("07:20", "0.2"),
            ("07:30", "nan"),
            ("07:40", "inf"),
            ("07:50", "-1"),
            ("08:00", "8"),
        ]
    ]
    assert (
        m._current_hour_precipitation(rows, datetime(2026, 10, 16, 7, 50, tzinfo=UTC))
        == 0.3
    )


def test_running_hour_without_a_valid_interval_is_missing_not_dry():
    assert m._current_hour_precipitation([row(**{m.PARAM_PRECIPITATION: ""})]) is None
    assert m._current_hour_precipitation([row(**{m.PARAM_PRECIPITATION: "0"})]) == 0


async def test_sparse_fallback_skips_invalid_values_and_preserves_older_zero(hass):
    source = station(hass)
    rows = [
        row(),
        row(**{m.PARAM_FOEHN_INDEX: "nan", m.PARAM_SNOW_DEPTH: "inf"}),
        row(**{m.PARAM_FOEHN_INDEX: "bad", m.PARAM_SNOW_DEPTH: "bad"}),
        row(**{m.PARAM_FOEHN_INDEX: None, m.PARAM_SNOW_DEPTH: None}),
        row(**{m.PARAM_FOEHN_INDEX: "0", m.PARAM_SNOW_DEPTH: "0"}),
        row(**{m.PARAM_FOEHN_INDEX: "2", m.PARAM_SNOW_DEPTH: "8"}),
    ]
    data = source._parse_csv_row_with_fallback(rows)
    assert data["foehn_index"] == 0
    assert data["snow_depth"] == 0
    assert data["temperature"] == 12
    assert data["wind_gust"] is None


@pytest.mark.parametrize(
    "content,expected",
    [
        ("station_abbr;reference_timestamp;tre200s0\n", "parse station data"),
        (csv_rows(row(station_abbr="OTHER")), "different or missing station"),
        (
            csv_rows(
                {
                    "station_abbr": "KLO",
                    "reference_timestamp": "16.10.2026 07:40",
                    m.PARAM_TEMPERATURE: "nan",
                }
            ),
            "no valid measured observations",
        ),
        (
            "station_abbr;reference_timestamp;tre200s0\nKLO;16.10.2026 07:40;"
            + "x" * 150000,
            "parse station data",
        ),
    ],
)
async def test_invalid_csv_cannot_become_a_successful_refresh(
    hass, aioclient_mock, content, expected
):
    aioclient_mock.get(STATION_URL, json=assets())
    aioclient_mock.get(CSV_URL, text=content)
    with pytest.raises(UpdateFailed, match=expected):
        await station(hass)._async_update_data()
    assert len(aioclient_mock.mock_calls) == 2


async def test_provider_encoding_and_bad_rain_interval_are_local(hass, aioclient_mock):
    body = csv_rows(row(note="Météo", **{m.PARAM_PRECIPITATION: "bad"}))
    aioclient_mock.get(CSV_URL, content=body.encode("cp1252"))
    data = await station(hass)._async_download_and_parse_csv(CSV_URL)
    assert data["temperature"] == 12
    assert data["precipitation"] is None
    assert data["precipitation_current_hour"] is None


@pytest.mark.parametrize("kind", ["now", "recent", "missing", "broken"])
async def test_station_asset_selection_and_invalid_metadata(hass, aioclient_mock, kind):
    aioclient_mock.get(
        STATION_URL,
        json=assets(kind=kind)
        if kind in ("now", "recent")
        else {"assets": {}}
        if kind == "missing"
        else [],
    )
    result = await station(hass)._async_get_station_data_url()
    assert result == (CSV_URL if kind in ("now", "recent") else None)
    assert len(aioclient_mock.mock_calls) == 1


@pytest.mark.parametrize("stage", ["metadata", "csv"])
@pytest.mark.parametrize(
    "response,attempts",
    [
        ({"status": 404}, 1),
        ({"status": 429}, 4),
        ({"status": 503}, 4),
        ({"exc": TimeoutError()}, 4),
        ({"exc": aiohttp.ClientConnectionError()}, 4),
    ],
)
async def test_transport_retry_bounds(hass, aioclient_mock, stage, response, attempts):
    aioclient_mock.get(STATION_URL if stage == "metadata" else CSV_URL, **response)
    source = station(hass)
    with (
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ),
        pytest.raises((aiohttp.ClientError, TimeoutError)),
    ):
        if stage == "metadata":
            await source._async_get_station_data_url()
        else:
            await source._async_download_and_parse_csv(CSV_URL)
    assert len(aioclient_mock.mock_calls) == attempts


async def test_missing_session_and_minimum_interval(hass):
    source = m.MeteoSwissDataUpdateCoordinator(hass, "KLO", 1)
    assert source.update_interval == timedelta(seconds=600)
    with pytest.raises(RuntimeError):
        await source._async_get_station_data_url()
    with pytest.raises(RuntimeError):
        await source._async_download_and_parse_csv(CSV_URL)
    await source.async_close()


async def test_source_cache_expiry_and_breaker_recovery(hass, aioclient_mock, freezer):
    source = station(hass)
    aioclient_mock.get(STATION_URL, json=assets())
    aioclient_mock.get(CSV_URL, text=csv_rows(row()))
    first = await source._async_update_data()
    assert await source._async_update_data() == first
    assert len(aioclient_mock.mock_calls) == 2
    clear_all_caches()
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATION_URL, json={})
    for _ in range(5):
        await source.async_refresh()
    assert not source.last_update_success
    calls = len(aioclient_mock.mock_calls)
    with pytest.raises(UpdateFailed, match="Circuit breaker"):
        await source._async_update_data()
    assert len(aioclient_mock.mock_calls) == calls
    freezer.move_to("2026-10-16T07:55:00+00:00")
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATION_URL, json=assets())
    aioclient_mock.get(CSV_URL, text=csv_rows(row()))
    await source.async_refresh()
    assert source.last_update_success
    assert source._consecutive_failures == 0
    assert source._circuit_open_until is None


async def test_stale_cached_values_cannot_renew_measurement_time(hass):
    source = station(hass)
    get_current_weather_cache().set(
        "station:klo", {"last_update": "2026-10-16T05:00:00+00:00", "temperature": 12}
    )
    with pytest.raises(UpdateFailed):
        await source._async_update_data()

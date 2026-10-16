"""Station failure/recovery diagnostics omit selected locations and payloads."""

from __future__ import annotations

import logging
from unittest.mock import AsyncMock, patch

import pytest

from custom_components.meteoswiss import coordinator as m
from custom_components.meteoswiss.cache import clear_all_caches
from tests.test_measurement_sources import (
    CSV_URL,
    FIELDS,
    STATION_URL,
    assets,
    csv_rows,
    row,
    station,
)


@pytest.fixture(autouse=True)
def isolated_clock_cache(freezer):
    clear_all_caches()
    freezer.move_to("2026-10-16T07:50:00Z")
    yield
    clear_all_caches()


@pytest.mark.parametrize("parameter,key", FIELDS)
async def test_invalid_measurement_logs_no_raw_payload(hass, caplog, parameter, key):
    secret = "PRIVATE_PAYLOAD_47.451234_8.561234"
    with caplog.at_level(logging.DEBUG, logger="custom_components.meteoswiss"):
        data = station(hass)._parse_csv_row(row(**{parameter: secret}))
    assert data[key] is None or key == "dew_point"
    assert secret not in caplog.text
    assert all(
        record.levelno < logging.WARNING
        for record in caplog.records
        if record.name.startswith("custom_components.meteoswiss")
    )


@pytest.mark.parametrize("stage", ["metadata", "csv"])
async def test_http_failures_log_once_recover_and_hide_raw_url(
    hass, aioclient_mock, caplog, stage
):
    secret = "PRIVATE_SOURCE_LOCATION"
    csv_url = CSV_URL + "?token=" + secret
    if stage == "metadata":
        # The selected station URL itself must also be absent in debug logs.
        aioclient_mock.get(STATION_URL, status=503)
    else:
        aioclient_mock.get(STATION_URL, json=assets(csv_url))
        aioclient_mock.get(csv_url, status=503)
    source = station(hass)
    with (
        caplog.at_level(logging.DEBUG, logger="custom_components.meteoswiss"),
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ),
    ):
        await source.async_refresh()
        await source.async_refresh()
        assert not source.last_update_success and source.data is None
        assert (
            sum(
                "Error fetching meteoswiss data" in r.getMessage()
                for r in caplog.records
            )
            == 1
        )
        aioclient_mock.clear_requests()
        aioclient_mock.get(STATION_URL, json=assets(csv_url))
        aioclient_mock.get(csv_url, text=csv_rows(row()))
        await source.async_refresh()
        assert source.last_update_success and source.data["temperature"] == 12
    assert secret not in caplog.text
    assert STATION_URL not in caplog.text
    assert CSV_URL not in caplog.text
    assert "klo" not in caplog.text.lower()
    assert (
        sum(
            "Fetching meteoswiss data recovered" in r.getMessage()
            for r in caplog.records
        )
        == 1
    )


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"assets": []},
        *[
            {"assets": {f"ogd-smn_klo_{period}.csv": asset}}
            for period in ("t_now", "t_recent")
            for asset in (
                "PRIVATE_BAD_ASSET",
                {},
                {"href": None},
                {"href": 5},
                {"href": " "},
            )
        ],
    ],
)
async def test_invalid_metadata_is_private_and_not_error_logged(
    hass, aioclient_mock, caplog, payload
):
    aioclient_mock.get(STATION_URL, json=payload)
    with caplog.at_level(logging.DEBUG, logger="custom_components.meteoswiss"):
        assert await station(hass)._async_get_station_data_url() is None
    assert "PRIVATE_BAD_ASSET" not in caplog.text
    assert STATION_URL not in caplog.text
    assert "Traceback" not in caplog.text
    assert all(
        record.levelno < logging.WARNING
        for record in caplog.records
        if record.name.startswith("custom_components.meteoswiss")
    )


async def test_bad_rain_interval_does_not_leak_payload(caplog):
    secret = "PRIVATE_RAIN_PAYLOAD"
    with caplog.at_level(logging.DEBUG, logger="custom_components.meteoswiss"):
        assert (
            m._current_hour_precipitation([row(**{m.PARAM_PRECIPITATION: secret})])
            is None
        )
    assert secret not in caplog.text


async def test_optional_fallback_skips_non_finite_older_rows(hass):
    data = station(hass)._parse_csv_row_with_fallback(
        [
            row(**{m.PARAM_FOEHN_INDEX: "", m.PARAM_SNOW_DEPTH: ""}),
            row(**{m.PARAM_FOEHN_INDEX: "nan", m.PARAM_SNOW_DEPTH: "inf"}),
            row(**{m.PARAM_FOEHN_INDEX: "2", m.PARAM_SNOW_DEPTH: "8"}),
        ]
    )
    assert data["foehn_index"] == 2 and data["snow_depth"] == 8


async def test_empty_parser_output_is_unavailable(hass):
    from homeassistant.helpers.update_coordinator import UpdateFailed

    source = station(hass)
    source._async_get_station_data_url = AsyncMock(return_value=CSV_URL)
    source._async_download_and_parse_csv = AsyncMock(return_value={})
    with pytest.raises(UpdateFailed, match="parse station data"):
        await source._async_update_data()
    assert source._consecutive_failures == 1


async def test_malformed_csv_row_is_private(hass, caplog):
    with caplog.at_level(logging.DEBUG, logger="custom_components.meteoswiss"):
        assert station(hass)._parse_csv_row(None) == {}
    assert "Traceback" not in caplog.text


@pytest.mark.parametrize(
    "bad_row", [None, {m.PARAM_TEMPERATURE: 12}, {"extra": ["PRIVATE_EXTRA"]}]
)
async def test_invalid_row_shapes_do_not_hide_a_programming_failure(
    hass, caplog, bad_row
):
    with caplog.at_level(logging.DEBUG, logger="custom_components.meteoswiss"):
        assert station(hass)._parse_csv_row(bad_row) == {}
    assert "PRIVATE_EXTRA" not in caplog.text and "Traceback" not in caplog.text


async def test_none_csv_field_is_missing_not_zero(hass):
    data = station(hass)._parse_csv_row({m.PARAM_TEMPERATURE: None})
    assert data["temperature"] is None


@pytest.mark.parametrize("stage", ["metadata", "csv"])
async def test_unexpected_programming_failure_is_not_swallowed(
    hass, aioclient_mock, stage
):
    source = station(hass)
    if stage == "metadata":
        source._session.get = lambda *args, **kwargs: (_ for _ in ()).throw(
            RuntimeError("unexpected bug")
        )
        call = source._async_get_station_data_url()
    else:
        aioclient_mock.get(CSV_URL, text=csv_rows(row()))
        source._parse_csv_row_with_fallback = lambda *args: (_ for _ in ()).throw(
            RuntimeError("unexpected bug")
        )
        call = source._async_download_and_parse_csv(CSV_URL)
    with pytest.raises(RuntimeError, match="unexpected bug"):
        await call


async def test_missing_csv_rows_have_no_fabricated_measurements(hass):
    assert station(hass)._parse_csv_row_with_fallback([]) == {}

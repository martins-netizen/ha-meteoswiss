"""Hourly precipitation transport, archive merging and Recorder upserts."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_recorder_block_till_done,
)

from custom_components.meteoswiss import precipitation as p
from custom_components.meteoswiss.const import API_BASE, STAC_COLLECTION

STATION_URL = f"{API_BASE}/collections/{STAC_COLLECTION}/items/klo"
CSV_URL = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/klo/ogd-smn_klo_h_now.csv"
RECENT_URL = CSV_URL.replace("_now", "_recent")
HISTORY_URL = CSV_URL.replace("_now", "_historical_2020-2029")
HEADER = "station_abbr;reference_timestamp;rre150h0\n"
VALID = HEADER + "KLO;16.10.2026 06:00;0\nKLO;16.10.2026 07:00;0.4\n"


@pytest.fixture(autouse=True)
def fixed_clock(freezer):
    freezer.move_to("2026-10-16T07:50:00+00:00")


def coordinator(hass, **kwargs):
    return p.MeteoSwissHourlyPrecipitationCoordinator(
        hass, "KLO", async_get_clientsession(hass), **kwargs
    )


def metadata(**periods):
    return {
        "assets": {
            "ogd-smn_klo_h_" + period + ".csv": {"href": url}
            for period, url in periods.items()
        }
    }


def test_invalid_totals_cannot_enter_recorder_and_zero_is_preserved():
    content = HEADER + "\n".join(
        f"KLO;16.10.2026 0{i}:00;{value}"
        for i, value in enumerate(["nan", "inf", "-inf", "-1", "bad", "", "0"])
    )
    values = p._parse_hourly_statistics(content)
    assert len(values) == 1
    assert values[0]["start"] == datetime(2026, 10, 16, 5, tzinfo=UTC)
    assert values[0]["mean"] == 0


def test_corrected_duplicates_are_sorted_and_missing_values_do_not_erase_valid_ones():
    content = (
        HEADER
        + "KLO;16.10.2026 07:00;1.2\nKLO;16.10.2026 06:00;0.5\nKLO;16.10.2026 07:00;0.4\nKLO;16.10.2026 07:00;\n"
    )
    values = p._parse_hourly_statistics(content)
    assert [v["mean"] for v in values] == [0.5, 0.4]
    assert [v["start"].hour for v in values] == [5, 6]


def test_wrong_station_future_and_nonhourly_records_are_not_imported():
    content = (
        HEADER
        + "OTHER;16.10.2026 06:00;99\nKLO;16.10.2026 07:30;9\nKLO;16.10.2026 08:00;9\nKLO;16.10.2026 07:00;0\n"
    )
    values = p._parse_hourly_statistics(content, station_id="klo")
    assert len(values) == 1
    assert values[0]["mean"] == 0
    assert values[0]["start"] == datetime(2026, 10, 16, 6, tzinfo=UTC)


@pytest.mark.parametrize("period", ["now", "historical"])
def test_asset_selection_ignores_malformed_and_other_station_assets(period):
    name = (
        "ogd-smn_klo_h_"
        + period
        + ("_2020-2029" if period == "historical" else "")
        + ".csv"
    )
    assets = {
        name: {"href": CSV_URL},
        "other.csv": {},
        "ogd-smn_other_h_now.csv": {"href": "wrong"},
        "ogd-smn_klo_h_historical_2010-2019.csv": {"href": "old"},
        "ogd-smn_klo_h_historical_2030-2039.csv": None,
    }
    assert p._asset_urls_for_period(assets, "klo", period, 2025) == [CSV_URL]


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
async def test_statistics_transport_retries_are_bounded(
    hass, aioclient_mock, stage, response, attempts
):
    aioclient_mock.get(STATION_URL if stage == "metadata" else CSV_URL, **response)
    source = coordinator(hass)
    with (
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ),
        pytest.raises((aiohttp.ClientError, TimeoutError)),
    ):
        if stage == "metadata":
            await source._async_get_hourly_urls()
        else:
            await source._async_download_hourly_csv(CSV_URL, "now")
    assert len(aioclient_mock.mock_calls) == attempts


@pytest.mark.parametrize(
    "data",
    [[], {"assets": []}, {"assets": {}}, {"assets": {"other.csv": {"href": CSV_URL}}}],
)
async def test_bad_metadata_never_queues_statistics(hass, aioclient_mock, data):
    aioclient_mock.get(STATION_URL, json=data)
    with (
        patch(
            "custom_components.meteoswiss.precipitation.async_add_external_statistics"
        ) as queue,
        pytest.raises(UpdateFailed),
    ):
        await coordinator(hass)._async_update_data()
    queue.assert_not_called()
    assert len(aioclient_mock.mock_calls) == 1


@pytest.mark.parametrize(
    "content",
    [
        "",
        HEADER,
        "<html>error</html>",
        HEADER + "KLO;bad;0",
        HEADER + "KLO;16.10.2026 07:00;nan",
    ],
)
async def test_empty_or_invalid_csv_never_queues_statistics(
    hass, aioclient_mock, content
):
    aioclient_mock.get(STATION_URL, json=metadata(now=CSV_URL))
    aioclient_mock.get(CSV_URL, text=content)
    with (
        patch(
            "custom_components.meteoswiss.precipitation.async_add_external_statistics"
        ) as queue,
        pytest.raises(UpdateFailed),
    ):
        await coordinator(hass)._async_update_data()
    queue.assert_not_called()
    assert len(aioclient_mock.mock_calls) == 2


async def test_archive_partial_download_and_period_precedence(hass, aioclient_mock):
    # Use the provider's exact decade asset spelling.
    info = metadata(recent=RECENT_URL, now=CSV_URL)
    info["assets"]["ogd-smn_klo_h_historical_2020-2029.csv"] = {"href": HISTORY_URL}
    aioclient_mock.get(STATION_URL, json=info)
    aioclient_mock.get(HISTORY_URL, text=VALID.replace("0.4", "2.5"))
    aioclient_mock.get(RECENT_URL, status=503)
    aioclient_mock.get(CSV_URL, text=VALID)
    source = coordinator(
        hass, asset_periods=("historical", "recent", "now"), lookback_months=13
    )
    with (
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ),
        patch(
            "custom_components.meteoswiss.precipitation.async_add_external_statistics"
        ) as queue,
    ):
        data = await source._async_update_data()
    metadata_value, statistics = queue.call_args.args[1:]
    assert metadata_value["statistic_id"] == "meteoswiss:klo_precipitation_hourly"
    assert metadata_value["has_sum"] is False
    assert metadata_value["unit_of_measurement"] == "mm"
    assert [v["mean"] for v in statistics] == [0, 0.4]
    assert data["imported_hours"] == 2
    assert data["imported_periods"] == ["historical", "now"]
    assert data["failed_downloads"] == 1
    assert data["partial_import"] is True


async def test_missing_or_empty_archive_period_does_not_erase_current_data(
    hass, aioclient_mock
):
    aioclient_mock.get(STATION_URL, json=metadata(recent=RECENT_URL, now=CSV_URL))
    aioclient_mock.get(RECENT_URL, text=HEADER)
    aioclient_mock.get(CSV_URL, text=VALID)
    with patch(
        "custom_components.meteoswiss.precipitation.async_add_external_statistics"
    ) as queue:
        data = await coordinator(
            hass, asset_periods=("historical", "recent", "now")
        )._async_update_data()
    queue.assert_called_once()
    assert data["imported_periods"] == ["now"]
    assert data["partial_import"] is True


async def test_recorder_failure_does_not_report_success(hass, aioclient_mock):
    aioclient_mock.get(STATION_URL, json=metadata(now=CSV_URL))
    aioclient_mock.get(CSV_URL, text=VALID)
    source = coordinator(hass)
    with patch(
        "custom_components.meteoswiss.precipitation.async_add_external_statistics",
        side_effect=ValueError("invalid metadata"),
    ):
        await source.async_refresh()
    assert not source.last_update_success
    assert source.data is None


async def test_repeat_import_upserts_existing_statistic_id_in_real_recorder(
    recorder_mock, hass, aioclient_mock
):
    source = coordinator(hass)
    aioclient_mock.get(STATION_URL, json=metadata(now=CSV_URL))
    aioclient_mock.get(CSV_URL, text=VALID)
    await source._async_update_data()
    await source._async_update_data()
    await async_recorder_block_till_done(hass)
    values = await hass.async_add_executor_job(
        statistics_during_period,
        hass,
        datetime(2026, 10, 16, 0, tzinfo=UTC),
        None,
        {source.statistic_id},
        "hour",
        None,
        {"mean", "min", "max"},
    )
    rows = values[source.statistic_id]
    assert len(rows) == 2
    assert [r["mean"] for r in rows] == [0, 0.4]
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATION_URL, json=metadata(now=CSV_URL))
    aioclient_mock.get(CSV_URL, text=VALID.replace("0.4", "0.7"))
    await source._async_update_data()
    await async_recorder_block_till_done(hass)
    corrected = await hass.async_add_executor_job(
        statistics_during_period,
        hass,
        datetime(2026, 10, 16, 0, tzinfo=UTC),
        None,
        {source.statistic_id},
        "hour",
        None,
        {"mean", "min", "max"},
    )
    assert len(corrected[source.statistic_id]) == 2
    assert [r["mean"] for r in corrected[source.statistic_id]] == [0, 0.7]

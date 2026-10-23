"""Direct source privacy/ownership and Recorder boundary behaviour."""

import asyncio
import csv
import traceback
from datetime import UTC, datetime
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.meteoswiss.const import API_BASE, STAC_COLLECTION
from custom_components.meteoswiss.coordinator import (
    MeteoSwissHourlyPrecipitationCoordinator,
)
from custom_components.meteoswiss.http import MAX_ARCHIVE_BYTES, MAX_CSV_BYTES, OGD_HOST
from custom_components.meteoswiss.precipitation import (
    MeteoSwissHourlyPrecipitationClient,
    PrecipitationSourceError,
    parse_hourly_precipitation,
)
from custom_components.meteoswiss.precipitation_recorder import (
    MeteoSwissPrecipitationImporter,
)

BASE = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/klo/ogd-smn_klo_h_"
NOW_URL = BASE + "now.csv"
HISTORY_URL = BASE + "historical_2020-2029.csv"
HEADER = "station_abbr;reference_timestamp;rre150h0\n"
VALID = HEADER + "KLO;16.10.2026 06:00;0\nKLO;16.10.2026 07:00;0.4\n"


@pytest.fixture
def source(freezer):
    freezer.move_to("2026-10-16T07:50:00+00:00")
    session = Mock(spec=aiohttp.ClientSession)
    session.close = AsyncMock()
    client = MeteoSwissHourlyPrecipitationClient(
        "KLO", session, asset_periods=("historical", "now")
    )
    yield client, session
    session.close.assert_not_called()


async def test_direct_source_requests_keep_station_period_encoding_and_budgets(source):
    client, session = source
    payload = {
        "assets": {
            "ogd-smn_klo_h_historical_2010-2019.csv": {"href": "old"},
            "ogd-smn_klo_h_historical_2020-2029.csv": {"href": HISTORY_URL},
            "ogd-smn_klo_h_now.csv": {"href": NOW_URL},
        }
    }
    with patch(
        "custom_components.meteoswiss.precipitation.async_get_json",
        return_value=payload,
    ) as request:
        urls = await client.async_get_urls(2025)
    assert urls == {"historical": [HISTORY_URL], "now": [NOW_URL]}
    request.assert_awaited_once_with(
        session, f"{API_BASE}/collections/{STAC_COLLECTION}/items/klo", host=OGD_HOST
    )
    text = "Météo;" + VALID
    with patch(
        "custom_components.meteoswiss.precipitation.async_get_bytes",
        return_value=text.encode("cp1252"),
    ) as download:
        assert await client.async_get_csv(NOW_URL, "now") == text
        assert await client.async_get_csv(HISTORY_URL, "historical") == text
    assert [call.kwargs["max_bytes"] for call in download.await_args_list] == [
        MAX_CSV_BYTES,
        MAX_ARCHIVE_BYTES,
    ]
    assert all(call.kwargs["host"] == OGD_HOST for call in download.await_args_list)


@pytest.mark.parametrize("stage", ["metadata", "csv"])
@pytest.mark.parametrize(
    "error,attempts",
    [
        (aiohttp.ClientConnectionError("private_precip_marker"), 4),
        (TimeoutError("private_precip_marker"), 4),
        (ValueError("private_precip_marker"), 1),
        (TypeError("private_precip_marker"), 1),
    ],
)
async def test_direct_source_failures_are_private_and_keep_retry_budget(
    source, stage, error, attempts
):
    client, _ = source
    target = "async_get_json" if stage == "metadata" else "async_get_bytes"
    with (
        patch(
            f"custom_components.meteoswiss.precipitation.{target}", side_effect=error
        ) as request,
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ),
        pytest.raises(PrecipitationSourceError) as caught,
    ):
        if stage == "metadata":
            await client.async_get_urls()
        else:
            await client.async_get_csv(NOW_URL, "now")
    assert request.await_count == attempts
    assert str(caught.value) == ""
    assert "private_precip_marker" not in "".join(
        traceback.format_exception(caught.value)
    )


@pytest.mark.parametrize("stage", ["metadata", "csv"])
async def test_direct_source_cancellation_propagates_without_retry(source, stage):
    client, _ = source
    target = "async_get_json" if stage == "metadata" else "async_get_bytes"
    with patch(
        f"custom_components.meteoswiss.precipitation.{target}",
        side_effect=asyncio.CancelledError(),
    ) as request:
        with pytest.raises(asyncio.CancelledError):
            if stage == "metadata":
                await client.async_get_urls()
            else:
                await client.async_get_csv(NOW_URL, "now")
    assert request.await_count == 1


@pytest.mark.parametrize(
    "stage,message",
    [
        ("metadata", "Hourly precipitation metadata unavailable"),
        ("urls", "Could not find hourly precipitation URLs"),
        ("data", "No valid hourly precipitation data"),
        ("queue", "Could not queue hourly precipitation statistics"),
    ],
)
async def test_coordinator_retains_each_failure_message_and_hides_queue_errors(
    hass, source, stage, message
):
    _, session = source
    coordinator = MeteoSwissHourlyPrecipitationCoordinator(hass, "KLO", session)
    with (
        patch.object(
            coordinator.client,
            "async_get_urls",
            return_value={} if stage == "urls" else {"now": [NOW_URL]},
        ) as urls,
        patch.object(
            coordinator.client,
            "async_get_csv",
            return_value=HEADER if stage == "data" else VALID,
        ),
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics",
            side_effect=ValueError("private_queue_marker"),
        ) as queue,
        pytest.raises(UpdateFailed, match="^" + message + "$") as caught,
    ):
        if stage == "metadata":
            urls.side_effect = PrecipitationSourceError()
        await coordinator._async_update_data()
    assert "private_queue_marker" not in "".join(
        traceback.format_exception(caught.value)
    )
    assert queue.call_count == (1 if stage == "queue" else 0)


async def test_csv_parse_failure_preserves_other_files_and_later_corrections(
    hass, source
):
    client, _ = source
    importer = MeteoSwissPrecipitationImporter(
        hass, client, asset_periods=("historical", "now"), lookback_months=13
    )

    def parse(content, earliest, station):
        if content == "broken":
            raise csv.Error("private_csv_marker")
        return parse_hourly_precipitation(content, earliest, station)

    with (
        patch.object(
            client,
            "async_get_urls",
            return_value={"historical": ["broken", HISTORY_URL], "now": [NOW_URL]},
        ),
        patch.object(
            client,
            "async_get_csv",
            side_effect=["broken", VALID, VALID.replace("0.4", "0.7")],
        ),
        patch(
            "custom_components.meteoswiss.precipitation_recorder.parse_hourly_precipitation",
            side_effect=parse,
        ),
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ) as queue,
    ):
        result = await importer.async_import()
    metadata, rows = queue.call_args.args[1:]
    assert metadata["statistic_id"] == "meteoswiss:klo_precipitation_hourly"
    assert metadata["has_sum"] is False
    assert [row["mean"] for row in rows] == [0, 0.7]
    assert all(row["mean"] == row["min"] == row["max"] for row in rows)
    assert rows[0]["start"] == datetime(2026, 10, 16, 5, tzinfo=UTC)
    assert result["failed_downloads"] == 1 and result["partial_import"] is True
    assert result["imported_periods"] == ["historical", "now"]


async def test_executor_cancellation_never_queues_statistics(hass, source):
    client, _ = source
    importer = MeteoSwissPrecipitationImporter(
        hass, client, asset_periods=("now",), lookback_months=None
    )
    with (
        patch.object(client, "async_get_urls", return_value={"now": [NOW_URL]}),
        patch.object(client, "async_get_csv", return_value=VALID),
        patch.object(
            hass, "async_add_executor_job", side_effect=asyncio.CancelledError()
        ),
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ) as queue,
        pytest.raises(asyncio.CancelledError),
    ):
        await importer.async_import()
    queue.assert_not_called()

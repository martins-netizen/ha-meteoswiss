"""A bounded STAC response must not fan out into unbounded archive work."""

import asyncio
import json
import logging
import traceback
from threading import Event
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from test_provider_device_metadata import make_entry
from test_provider_device_metadata import provider_sources as provider_sources

from custom_components.meteoswiss import precipitation as p
from custom_components.meteoswiss.const import API_BASE, STAC_COLLECTION
from custom_components.meteoswiss.coordinator import (
    MeteoSwissHourlyPrecipitationCoordinator,
)
from custom_components.meteoswiss.precipitation_recorder import (
    HourlyPrecipitationDataMissing,
    HourlyPrecipitationMetadataError,
    MeteoSwissPrecipitationImporter,
)

pytestmark = pytest.mark.freeze_time("2026-10-16T07:50:00Z")

STATION_URL = f"{API_BASE}/collections/{STAC_COLLECTION}/items/klo"
BASE = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/klo/ogd-smn_klo_h_"
HISTORY_URL = BASE + "historical_2020-2029.csv"
RECENT_URL = BASE + "recent.csv"
NOW_URL = BASE + "now.csv"
VALID = "station_abbr;reference_timestamp;rre150h0\nKLO;16.10.2026 07:00;0\n"


async def blocked(*args):
    """Yield until the real timeout or caller cancellation stops this source."""
    await asyncio.Event().wait()


def importer(hass, *, periods=("historical", "recent", "now"), lookback=13):
    client = p.MeteoSwissHourlyPrecipitationClient(
        "KLO", Mock(spec=aiohttp.ClientSession), asset_periods=periods
    )
    return MeteoSwissPrecipitationImporter(
        hass, client, asset_periods=periods, lookback_months=lookback
    )


async def test_ten_thousand_metadata_assets_only_fetch_relevant_canonical_file(
    hass, aioclient_mock
):
    assets = {
        f"ogd-smn_klo_h_historical_{year:04d}-9999.csv": {"href": HISTORY_URL}
        for year in range(10000)
    }
    assets["ogd-smn_klo_h_historical_2020-2029.csv"] = {"href": HISTORY_URL}
    metadata = {"assets": assets}
    assert len(json.dumps(metadata).encode()) < 2 * 1024 * 1024
    aioclient_mock.get(STATION_URL, json=metadata)
    aioclient_mock.get(HISTORY_URL, text=VALID)
    source = importer(hass, periods=("historical",))
    source.client._session = async_get_clientsession(hass)
    with patch(
        "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
    ) as queue:
        result = await source.async_import()
    assert len(aioclient_mock.mock_calls) == 2
    assert result["imported_hours"] == 1
    assert queue.call_args.args[1]["statistic_id"] == "meteoswiss:klo_precipitation_hourly"
    assert queue.call_args.args[2][0]["mean"] == 0


@pytest.mark.parametrize("period", ["historical", "recent", "now"])
@pytest.mark.parametrize("asset", [None, {}, {"href": None}, {"href": NOW_URL + "?private"}])
async def test_present_invalid_asset_fails_mixed_two_decade_plan_before_csv_io(
    hass, aioclient_mock, freezer, period, asset
):
    freezer.move_to("2031-01-01T00:00:00Z")
    second_decade = BASE + "historical_2030-2039.csv"
    assets = {
        "ogd-smn_klo_h_historical_2020-2029.csv": {"href": HISTORY_URL},
        "ogd-smn_klo_h_historical_2030-2039.csv": {"href": second_decade},
        "ogd-smn_klo_h_recent.csv": {"href": RECENT_URL},
        "ogd-smn_klo_h_now.csv": {"href": NOW_URL},
    }
    suffix = "historical_2030-2039" if period == "historical" else period
    assets["ogd-smn_klo_h_" + suffix + ".csv"] = asset
    aioclient_mock.get(STATION_URL, json={"assets": assets})
    source = importer(hass)
    source.client._session = async_get_clientsession(hass)
    with (
        patch.object(source.client, "async_get_csv") as download,
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ) as queue,
        pytest.raises(HourlyPrecipitationMetadataError) as caught,
    ):
        await source.async_import()
    download.assert_not_called()
    queue.assert_not_called()
    assert len(aioclient_mock.mock_calls) == 1
    assert "private" not in "".join(traceback.format_exception(caught.value))


@pytest.mark.parametrize("station", [None, 1, "", "KL", "KLOO", "K/L", "KŁO", " KLO", "KLO\n"])
def test_invalid_station_is_rejected_before_request(station):
    session = Mock(spec=aiohttp.ClientSession)
    with pytest.raises(
        p.InvalidPrecipitationConfiguration, match="Invalid precipitation station"
    ):
        p.MeteoSwissHourlyPrecipitationClient(station, session)
    session.get.assert_not_called()


@pytest.mark.parametrize("periods", [None, "now", ["now"], (), ("other",), (None,), (1,), (["now"],)])
def test_invalid_periods_are_rejected_before_request(periods):
    session = Mock(spec=aiohttp.ClientSession)
    with pytest.raises(
        p.InvalidPrecipitationConfiguration, match="Invalid precipitation periods"
    ):
        p.MeteoSwissHourlyPrecipitationClient("KLO", session, asset_periods=periods)
    session.get.assert_not_called()


def test_station_case_and_repeated_known_periods_are_normalized():
    client = p.MeteoSwissHourlyPrecipitationClient(
        "kLo", Mock(spec=aiohttp.ClientSession), asset_periods=("now", "now")
    )
    assert client.station_id == "klo"
    assert client.asset_periods == ("now",)


@pytest.mark.parametrize("rejection", ["invalid_identity", "archive"])
async def test_rejected_optional_precipitation_configuration_preserves_native_entry(
    recorder_mock, hass, enable_custom_integrations, provider_sources, caplog, rejection
):
    entry = make_entry(hass, "meteoswiss")
    if rejection == "invalid_identity":
        hass.config_entries.async_update_entry(
            entry, data={**entry.data, "station_id": "../"}
        )
    built = []

    def construct(*args, **kwargs):
        if rejection == "archive" and "asset_periods" in kwargs:
            raise p.InvalidPrecipitationConfiguration("private configuration marker")
        coordinator = MeteoSwissHourlyPrecipitationCoordinator(*args, **kwargs)
        built.append(coordinator)
        return coordinator

    session = async_get_clientsession(hass)
    with (
        caplog.at_level(logging.DEBUG, logger="custom_components.meteoswiss"),
        patch("custom_components.meteoswiss.MeteoSwissHourlyPrecipitationCoordinator", new=construct),
        patch(
            "custom_components.meteoswiss.hgt_ogd_coordinator.MeteoSwissHgtCoordinator._async_update_data",
            return_value={},
        ),
        patch("custom_components.meteoswiss.precipitation.async_get_json") as metadata,
        patch("custom_components.meteoswiss.precipitation.async_get_bytes") as download,
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ) as queue,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        runtime = entry.runtime_data
        assert runtime.hourly_precipitation_coordinator is None
        assert runtime.precipitation_archive_coordinator is None
        assert runtime.coordinator.last_update_success
        assert runtime.session is session and not session.closed
        entity_id = er.async_get(hass).async_get_entity_id(
            "sensor", "meteoswiss", f"meteoswiss_{entry.entry_id}_temperature"
        )
        assert hass.states.get(entity_id).state == "12"
        assert all(not coordinator._listeners for coordinator in built)
        metadata.assert_not_called()
        download.assert_not_called()
        queue.assert_not_called()
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
        assert not session.closed
    messages = [
        record.getMessage() for record in caplog.records
        if record.name == "custom_components.meteoswiss"
        and "Official hourly precipitation" in record.getMessage()
    ]
    assert messages == [
        "Official hourly precipitation source configuration is invalid; "
        "optional imports are unavailable"
    ]
    assert "private configuration marker" not in caplog.text


async def test_unexpected_optional_constructor_value_error_remains_a_setup_failure(
    recorder_mock, hass, enable_custom_integrations, provider_sources, caplog
):
    entry = make_entry(hass, "meteoswiss")
    session = async_get_clientsession(hass)
    with (
        patch(
            "custom_components.meteoswiss.MeteoSwissHourlyPrecipitationCoordinator",
            side_effect=ValueError("unexpected constructor defect"),
        ),
        patch("custom_components.meteoswiss.precipitation.async_get_json") as metadata,
        patch("custom_components.meteoswiss.precipitation.async_get_bytes") as download,
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ) as queue,
    ):
        assert not await hass.config_entries.async_setup(entry.entry_id)
    metadata.assert_not_called()
    download.assert_not_called()
    queue.assert_not_called()
    assert not session.closed
    assert "unexpected constructor defect" in caplog.text
    assert not any(
        "Official hourly precipitation source configuration" in record.getMessage()
        for record in caplog.records
    )


@pytest.mark.parametrize(
    "url,period",
    [
        (NOW_URL, "historical"),
        (NOW_URL, "other"),
        (NOW_URL, None),
        (NOW_URL, []),
        (None, "now"),
        (NOW_URL.replace("/klo/", "/ber/"), "now"),
        (NOW_URL + "?private", "now"),
        (HISTORY_URL + "#private", "historical"),
        (BASE + "historical_2030-2039.csv", "historical"),
        ("https://data.geo.admin.ch/other.csv", "now"),
    ],
)
async def test_direct_csv_source_binds_station_and_period_before_request(url, period):
    session = Mock(spec=aiohttp.ClientSession)
    client = p.MeteoSwissHourlyPrecipitationClient("KLO", session)
    with (
        patch("custom_components.meteoswiss.precipitation.async_get_bytes") as download,
        pytest.raises(p.PrecipitationSourceError) as caught,
    ):
        await client.async_get_csv(url, period)
    download.assert_not_called()
    session.get.assert_not_called()
    assert "private" not in "".join(traceback.format_exception(caught.value))


async def test_direct_canonical_historical_read_can_precede_production_lookback():
    client = p.MeteoSwissHourlyPrecipitationClient(
        "KLO", Mock(spec=aiohttp.ClientSession), asset_periods=("historical",)
    )
    url = BASE + "historical_2010-2019.csv"
    with patch(
        "custom_components.meteoswiss.precipitation.async_get_bytes",
        return_value=VALID.encode("cp1252"),
    ) as download:
        assert await client.async_get_csv(url, "historical") == VALID
    assert download.await_args.args[1] == url
    assert download.await_args.kwargs["max_bytes"] == p.MAX_ARCHIVE_BYTES


@pytest.mark.parametrize(
    "content",
    [
        "",
        "<html>private provider failure</html>",
        '{"error": "private provider failure"}',
        "station_abbr;rre150h0\nKLO;0\n",
        "station_abbr;reference_timestamp\nKLO;16.10.2026 07:00\n",
        "reference_timestamp;rre150h0\n16.10.2026 07:00;0\n",
    ],
)
def test_runtime_csv_requires_station_time_and_hourly_amount_headers(content):
    with pytest.raises(ValueError, match="Invalid hourly precipitation CSV header") as caught:
        p.parse_hourly_precipitation(content, station_id="klo")
    assert "private" not in str(caught.value)


def test_header_only_csv_is_valid_and_pure_parser_can_omit_station_binding():
    header = VALID.splitlines()[0] + "\n"
    assert p.parse_hourly_precipitation(header, station_id="klo") == []
    values = p.parse_hourly_precipitation(
        "reference_timestamp;rre150h0\n16.10.2026 07:00;0\n"
    )
    assert len(values) == 1 and values[0]["amount"] == 0


@pytest.mark.parametrize(
    "body,failed",
    [
        ("<html>private provider failure</html>", 1),
        ('{"error": "private provider failure"}', 1),
        ("", 1),
        (VALID.splitlines()[0] + "\n", 0),
    ],
)
async def test_malformed_csv_in_two_decade_plan_retains_valid_zero_as_partial(
    hass, aioclient_mock, freezer, body, failed
):
    freezer.move_to("2031-01-01T00:00:00Z")
    second_decade = BASE + "historical_2030-2039.csv"
    good = VALID.splitlines()[0] + "\nKLO;31.12.2030 23:00;0\n"
    assets = {
        "ogd-smn_klo_h_historical_2020-2029.csv": {"href": HISTORY_URL},
        "ogd-smn_klo_h_historical_2030-2039.csv": {"href": second_decade},
        "ogd-smn_klo_h_recent.csv": {"href": RECENT_URL},
        "ogd-smn_klo_h_now.csv": {"href": NOW_URL},
    }
    aioclient_mock.get(STATION_URL, json={"assets": assets})
    aioclient_mock.get(HISTORY_URL, text=body)
    for url in (second_decade, RECENT_URL, NOW_URL):
        aioclient_mock.get(url, text=good)
    source = importer(hass)
    source.client._session = async_get_clientsession(hass)
    with patch(
        "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
    ) as queue:
        result = await source.async_import()
    assert len(aioclient_mock.mock_calls) == 5
    assert result["failed_downloads"] == failed
    assert result["partial_import"] is bool(failed)
    assert result["imported_periods"] == ["historical", "recent", "now"]
    assert queue.call_args.args[2][0]["mean"] == 0


@pytest.mark.parametrize(
    "years,selected",
    [
        ("2020-2029", True),
        ("2010-2019", False),
        ("2030-2039", False),
        ("9990-9999", False),
        ("2029-2020", False),
        ("2020-2028", False),
        ("2021-2030", False),
        ("0000-0009", False),
        ("２０２０-２０２９", False),
    ],
)
def test_only_relevant_real_decades_are_selected(years, selected):
    name = f"ogd-smn_klo_h_historical_{years}.csv"
    url = BASE + f"historical_{years}.csv"
    assets = {name: {"href": url}}
    assert p._asset_urls_for_period(assets, "klo", "historical", 2025) == (
        [url] if selected else []
    )


@pytest.mark.parametrize("period", ["now", "recent", "historical"])
@pytest.mark.parametrize(
    "change",
    [
        lambda url: url.replace("/klo/", "/ber/"),
        lambda url: url.replace("ogd-smn/", "ogd-pollen/"),
        lambda url: url.replace("/klo/", "/klo/../klo/"),
        lambda url: url + "?download=1",
        lambda url: url + "#private",
        lambda url: url.replace("https:", "http:"),
        lambda url: url.replace("data.geo.admin.ch", "evil.invalid"),
        lambda url: url.replace("_klo_h_", "_ber_h_"),
        lambda url: None,
    ],
)
def test_asset_key_must_match_exact_same_station_url(period, change):
    suffix = "historical_2020-2029" if period == "historical" else period
    name = "ogd-smn_klo_h_" + suffix + ".csv"
    assets = {name: {"href": change(BASE + suffix + ".csv")}}
    with pytest.raises(ValueError, match="Invalid precipitation asset"):
        p._asset_urls_for_period(assets, "klo", period, 2025)


def test_unknown_period_cannot_construct_a_download_plan():
    with pytest.raises(ValueError, match="Invalid precipitation period"):
        p._asset_urls_for_period({}, "klo", "other")


async def test_source_rejects_excess_plan_before_any_csv_request(hass):
    source = importer(hass, periods=("historical",), lookback=None)
    assets = {
        f"ogd-smn_klo_h_historical_{year}-{year + 9}.csv": {
            "href": BASE + f"historical_{year}-{year + 9}.csv"
        }
        for year in range(1980, 2030, 10)
    }
    with (
        patch(
            "custom_components.meteoswiss.precipitation.async_get_json",
            return_value={"assets": assets},
        ),
        patch.object(source.client, "async_get_csv") as download,
        pytest.raises(p.PrecipitationSourceError),
    ):
        await source.client.async_get_urls()
    download.assert_not_called()


@pytest.mark.parametrize(
    "plan",
    [
        {
            "historical": [
                BASE + f"historical_{year}-{year + 9}.csv"
                for year in range(1980, 2030, 10)
            ]
        },
        {"historical": [HISTORY_URL], "now": [NOW_URL + "?private"]},
        {"historical": [HISTORY_URL], "now": [NOW_URL.replace("/klo/", "/ber/")]},
        {"now": NOW_URL},
        {"now": [None]},
        {"other": [NOW_URL]},
        [],
    ],
)
async def test_importer_revalidates_whole_plan_before_download_or_queue(hass, plan):
    source = importer(hass, lookback=None)
    with (
        patch.object(source.client, "async_get_urls", return_value=plan),
        patch.object(source.client, "async_get_csv") as download,
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ) as queue,
        pytest.raises(HourlyPrecipitationMetadataError) as caught,
    ):
        await source.async_import()
    download.assert_not_called()
    queue.assert_not_called()
    assert "private" not in "".join(traceback.format_exception(caught.value))


async def test_duplicate_urls_and_periods_are_downloaded_once(hass):
    source = importer(hass, periods=("historical", "now", "now"))
    with (
        patch.object(
            source.client, "async_get_urls",
            return_value={"historical": [HISTORY_URL] * 10000, "now": [NOW_URL] * 2},
        ),
        patch.object(source.client, "async_get_csv", return_value=VALID) as download,
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ),
    ):
        result = await source.async_import()
    assert download.await_count == 2
    assert result["imported_periods"] == ["historical", "now"]
    assert result["partial_import"] is False


def test_thirteen_month_window_can_use_four_files_at_decade_boundary(freezer):
    freezer.move_to("2031-01-01T00:00:00Z")
    old = BASE + "historical_2020-2029.csv"
    current = BASE + "historical_2030-2039.csv"
    plan = {"historical": [old, current], "recent": [RECENT_URL], "now": [NOW_URL]}
    assert p.validate_precipitation_plan(
        plan, "klo", ("historical", "recent", "now"), 2029
    ) == plan


async def test_metadata_deadline_is_a_private_metadata_failure(hass, monkeypatch):
    source = importer(hass)
    monkeypatch.setattr(
        "custom_components.meteoswiss.precipitation_recorder.PRECIPITATION_IMPORT_TIMEOUT",
        0,
    )
    with (
        patch.object(source.client, "async_get_urls", side_effect=blocked),
        patch.object(source.client, "async_get_csv") as download,
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ) as queue,
        pytest.raises(HourlyPrecipitationMetadataError) as caught,
    ):
        await source.async_import()
    download.assert_not_called()
    queue.assert_not_called()
    assert str(caught.value) == ""


@pytest.mark.parametrize("stage", ["download", "parser"])
async def test_whole_import_deadline_keeps_prior_zero_and_skips_remaining_files(
    hass, monkeypatch, freezer, stage
):
    source = importer(hass)
    monkeypatch.setattr(
        "custom_components.meteoswiss.precipitation_recorder.PRECIPITATION_IMPORT_TIMEOUT",
        0.02,
    )
    parsed = p.parse_hourly_precipitation(VALID, station_id="klo")

    async def download(url, period):
        if period == "recent" and stage == "download":
            freezer.tick(1)
            await asyncio.Event().wait()
        return VALID

    calls = 0

    async def parse(*args):
        nonlocal calls
        calls += 1
        if calls == 2 and stage == "parser":
            freezer.tick(1)
            await asyncio.Event().wait()
        return parsed

    with (
        patch.object(
            source.client, "async_get_urls",
            return_value={
                "historical": [HISTORY_URL], "recent": [RECENT_URL], "now": [NOW_URL]
            },
        ),
        patch.object(source.client, "async_get_csv", side_effect=download) as request,
        patch.object(hass, "async_add_executor_job", side_effect=parse),
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ) as queue,
    ):
        result = await source.async_import()
    assert [call.args[0] for call in request.await_args_list] == [HISTORY_URL, RECENT_URL]
    assert result["failed_downloads"] == 2
    assert result["partial_import"] is True
    assert result["imported_periods"] == ["historical"]
    assert queue.call_args.args[2][0]["mean"] == 0


async def test_deadline_without_completed_files_never_queues_statistics(
    hass, monkeypatch, freezer
):
    source = importer(hass, periods=("now",))
    monkeypatch.setattr(
        "custom_components.meteoswiss.precipitation_recorder.PRECIPITATION_IMPORT_TIMEOUT",
        0.01,
    )

    async def expired(*args):
        freezer.tick(1)
        await asyncio.Event().wait()

    with (
        patch.object(source.client, "async_get_urls", return_value={"now": [NOW_URL]}),
        patch.object(source.client, "async_get_csv", side_effect=expired),
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ) as queue,
        pytest.raises(HourlyPrecipitationDataMissing),
    ):
        await source.async_import()
    queue.assert_not_called()


@pytest.mark.parametrize("stage", ["metadata", "download"])
async def test_external_cancellation_propagates_through_import_deadline(hass, stage):
    source = importer(hass, periods=("now",))
    started = asyncio.Event()

    async def blocked(*args):
        started.set()
        await asyncio.Event().wait()

    with (
        patch.object(
            source.client, "async_get_urls",
            side_effect=blocked if stage == "metadata" else None,
            return_value={"now": [NOW_URL]},
        ),
        patch.object(source.client, "async_get_csv", side_effect=blocked),
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ) as queue,
    ):
        task = asyncio.create_task(source.async_import())
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
    queue.assert_not_called()


@pytest.mark.parametrize("stop", ["cancel", "deadline"])
async def test_late_real_parser_thread_cannot_queue_after_import_stops(
    hass, freezer, stop
):
    source = importer(hass, periods=("now",))
    started, finished = asyncio.Event(), asyncio.Event()
    release = Event()

    def parse(*args):
        hass.loop.call_soon_threadsafe(started.set)
        try:
            assert release.wait(timeout=5)
            return p.parse_hourly_precipitation(*args)
        finally:
            hass.loop.call_soon_threadsafe(finished.set)

    with (
        patch.object(source.client, "async_get_urls", return_value={"now": [NOW_URL]}),
        patch.object(source.client, "async_get_csv", return_value=VALID),
        patch(
            "custom_components.meteoswiss.precipitation_recorder.parse_hourly_precipitation",
            new=parse,
        ),
        patch(
            "custom_components.meteoswiss.precipitation_recorder.async_add_external_statistics"
        ) as queue,
    ):
        task = asyncio.create_task(source.async_import())
        try:
            await started.wait()
            if stop == "cancel":
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
            else:
                freezer.tick(p.PRECIPITATION_IMPORT_TIMEOUT + 1)
                with pytest.raises(HourlyPrecipitationDataMissing):
                    await task
        finally:
            release.set()
            await finished.wait()
            if not task.done():
                task.cancel()
                with pytest.raises(asyncio.CancelledError):
                    await task
        await hass.async_block_till_done()
    queue.assert_not_called()

"""Pollen/AQ validity, visible HA states, transport and recovery contracts."""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import ExitStack
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

import aiohttp
import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.cache import (
    clear_all_caches,
    get_current_weather_cache,
)
from custom_components.meteoswiss.const import (
    DOMAIN,
    MIN_UPDATE_INTERVAL,
    POLLEN_STATIONS,
)
from custom_components.meteoswiss.pollen_coordinator_openmeteo import (
    OPENMETEO_AQ_BASE_URL,
    OPENMETEO_FORECAST_URL,
    OpenMeteoPollenCoordinator,
)
from custom_components.meteoswiss.pollen_meteoswiss import (
    POLLEN_DATA_BASE_URL,
    MeteoSwissPollenCoordinator,
)
from custom_components.meteoswiss.pollen_sensor import (
    POLLEN_SENSOR_DESCRIPTIONS,
    MeteoSwissPollenSensor,
    _pollen_level,
)
from custom_components.meteoswiss.sensor import (
    AIR_QUALITY_SENSOR_DESCRIPTIONS,
    MS_POLLEN_SENSOR_DESCRIPTIONS,
    MeteoSwissAirQualitySensor,
    MeteoSwissMeasuredPollenSensor,
)

CSV_HEADER = "station_abbr;reference_timestamp;kabetuh0;kaalnuh0;kacoryh0;kafaguh0;kafraxh0;khpoach0\n"
CSV_ZERO = CSV_HEADER + "PLZ;15.10.2026 10:00;0;0;0;0;0;0\n"
CSV_URL = f"{POLLEN_DATA_BASE_URL}/plz/ogd-pollen_plz_h_now.csv"
CURRENT_TIME = int(datetime(2026, 10, 15, 10, tzinfo=UTC).timestamp())


def _station_evidence():
    """A dated, external provider snapshot; these tests make no live requests."""
    return json.loads(
        (Path(__file__).parent / "fixtures/pollen_stations_2026-10-21.json").read_text()
    )


def test_pollen_choices_match_verified_provider_metadata_and_hourly_assets():
    evidence = _station_evidence()
    assert set(POLLEN_STATIONS) == set(evidence["hourly_now_stations"])
    assert POLLEN_STATIONS == {
        code: f"{name} ({code})" for code, name in evidence["stations"].items()
    }
    assert set(POLLEN_STATIONS).isdisjoint(evidence["items_without_assets"])


@pytest.mark.parametrize("station,expected_current", [("PZH", True), ("PLZ", False)])
def test_real_current_zurich_and_stale_luzern_samples(
    hass, freezer, station, expected_current
):
    evidence = _station_evidence()
    freezer.move_to(evidence["retrieved_at_utc"])
    coordinator = MeteoSwissPollenCoordinator(hass, station_id=station)
    data = coordinator._parse_csv(evidence["sample_hourly_csv"][station]["csv"])
    assert bool(data) is expected_current
    if expected_current:
        assert data["station_id"] == station
        assert data["birch"]["current"] == 0
        assert data["oak"]["current"] == 0


@pytest.fixture(autouse=True)
def isolated_cache_and_clock(freezer):
    """The cache is shared across entries, not across independent tests."""
    clear_all_caches()
    freezer.move_to("2026-10-15T10:20:00+00:00")
    yield
    clear_all_caches()


def aq_payload(**series):
    return {"hourly": {"time": [CURRENT_TIME], **series}}


@pytest.mark.parametrize("field", ["birch_pollen", "pm10"])
@pytest.mark.parametrize(
    "value", [None, -1, float("nan"), float("inf"), "bad", True, {}, []]
)
def test_invalid_current_values_are_not_success(hass, field, value):
    coordinator = OpenMeteoPollenCoordinator(hass, 47.45, 8.56)
    assert coordinator._parse_response(aq_payload(**{field: [value]})) == {}


@pytest.mark.parametrize(
    "payload",
    [
        None,
        [],
        {},
        {"hourly": []},
        {"hourly": {}},
        {"hourly": {"time": "broken"}},
        {"hourly": {"time": []}},
        {"hourly": {"time": ["bad"]}},
        {"hourly": {"time": [CURRENT_TIME - 3600], "pm10": [20]}},
        {"hourly": {"time": [CURRENT_TIME + 3600], "pm10": [20]}},
        aq_payload(pm10="20", birch_pollen=[]),
    ],
)
def test_malformed_or_noncurrent_feed_is_not_success(hass, payload):
    assert OpenMeteoPollenCoordinator(hass, 47.45, 8.56)._parse_response(payload) == {}


def test_partial_hour_preserves_zero_missing_and_forecast_alignment(hass):
    coordinator = OpenMeteoPollenCoordinator(hass, 47.45, 8.56)
    payload = {
        "hourly": {
            "time": [CURRENT_TIME - 3600, CURRENT_TIME, CURRENT_TIME + 3600],
            "birch_pollen": [100, None, 300],
            "alder_pollen": [100, 0, -1, float("inf")],
            "grass_pollen": [100],
            "pm2_5": [90, 0, 40],
            "pm10": [90, "12.34", 40],
            "nitrogen_dioxide": [90, "bad", 40],
            "ozone": [90, 3.25, 40],
        }
    }
    data = coordinator._parse_response(payload)
    assert data["last_update"] == "2026-10-15T10:00:00+00:00"
    assert data["birch_pollen"]["current"] is None
    assert data["birch_pollen"]["forecast"] == [None, 300]
    assert data["alder_pollen"]["current"] == 0
    assert data["alder_pollen"]["forecast"] == [0, None, None]
    assert data["grass_pollen"]["current"] is None
    assert data["pm25"] == 0
    assert data["pm10"] == 12.3
    assert data["ozone"] == 3.2
    assert data["nitrogen_dioxide"] is None
    assert data["mugwort_pollen"] is None


@pytest.mark.parametrize("hour,index", [(0, 0), (1, 1)])
def test_repeated_autumn_hour_is_unambiguous(hass, freezer, hour, index):
    freezer.move_to(f"2026-10-25T0{hour}:20:00+00:00")
    times = [int(datetime(2026, 10, 25, h, tzinfo=UTC).timestamp()) for h in (0, 1)]
    data = OpenMeteoPollenCoordinator(hass, 47.45, 8.56)._parse_response(
        {"hourly": {"time": times, "birch_pollen": [2, 8]}}
    )
    assert data["birch_pollen"]["current"] == [2, 8][index]
    assert data["last_update"] == f"2026-10-25T0{hour}:00:00+00:00"


@pytest.mark.parametrize(
    "row",
    [
        "PLZ;15.10.2026 10:00;;;;;;",
        "PLZ;bad;0;0;0;0;0;0",
        "OTHER;15.10.2026 10:00;0;0;0;0;0;0",
        ";15.10.2026 10:00;0;0;0;0;0;0",
        "PLZ;;0;0;0;0;0;0",
        "PLZ;15.10.2026 10:00;-1;nan;inf;bad;1.5;",
    ],
)
def test_invalid_measured_pollen_is_not_success(hass, row):
    assert MeteoSwissPollenCoordinator(hass, "PLZ")._parse_csv(CSV_HEADER + row) == {}


@pytest.mark.parametrize(
    "content", ["", CSV_HEADER, "<html>Service unavailable</html>"]
)
def test_empty_or_wrong_csv_is_not_success(hass, content):
    assert MeteoSwissPollenCoordinator(hass, "PLZ")._parse_csv(content) == {}


def test_measured_zero_and_partial_values_keep_provider_time_and_history(hass):
    coordinator = MeteoSwissPollenCoordinator(hass, "plz")
    rows = [f"PLZ;15.10.2026 09:00;{i};bad;;-1;0;2" for i in range(25)]
    rows.append(" plz ;15.10.2026 10:00;0; 5 ;;-1;0;2")
    data = coordinator._parse_csv(CSV_HEADER + "\n".join(rows))
    assert data["station_id"] == "PLZ"
    assert data["last_update"] == "15.10.2026 10:00"
    assert data["birch"]["current"] == 0
    assert data["birch"]["history_24h"] == list(range(2, 25)) + [0]
    assert data["alder"]["current"] == 5
    assert data["alder"]["history_24h"] == [None] * 23 + [5]
    assert data["hazel"]["current"] is None
    assert data["beech"]["current"] is None
    assert data["grass"]["current"] == 2


def test_missing_csv_columns_do_not_mask_a_valid_partial_measurement(hass):
    data = MeteoSwissPollenCoordinator(hass, "PLZ")._parse_csv(
        "station_abbr;reference_timestamp;kabetuh0\nPLZ;15.10.2026 10:00;0"
    )
    assert data["birch"]["current"] == 0
    assert data["grass"]["current"] is None


@pytest.mark.parametrize(
    "age,accepted",
    [
        (timedelta(), True),
        (timedelta(hours=1, minutes=16), True),
        (timedelta(hours=3, minutes=20), True),
        (timedelta(hours=4), True),
        (timedelta(hours=4, microseconds=1), False),
        (timedelta(days=1), False),
        (-timedelta(minutes=10), True),
        (-timedelta(minutes=10, microseconds=1), False),
    ],
)
async def test_measured_age_bounds_use_measurement_time_not_fetch_time(
    hass, aioclient_mock, age, accepted
):
    stamp = (datetime.now(UTC) - age).isoformat()
    aioclient_mock.get(CSV_URL, text=CSV_HEADER + f"PLZ;{stamp};0;0;0;0;0;0")
    coordinator = MeteoSwissPollenCoordinator(
        hass, "PLZ", session=async_get_clientsession(hass)
    )
    if accepted:
        data = await coordinator._async_update_data()
        assert data["last_update"] == stamp
        assert data["birch"]["current"] == 0
        assert data["birch"]["history_24h"] == [0]
    else:
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()
    assert len(aioclient_mock.mock_calls) == 1


@pytest.mark.parametrize(
    "now,stamp",
    [
        ("2026-10-15T19:16:00+00:00", "15.10.2026 18:00"),
        ("2026-10-25T00:20:00+00:00", "24.10.2026 21:00"),
        ("2026-10-25T01:20:00+00:00", "24.10.2026 22:00"),
        ("2026-03-29T01:20:00+00:00", "28.03.2026 22:00"),
    ],
)
def test_measured_provider_times_stay_utc_across_zurich_dst(hass, freezer, now, stamp):
    freezer.move_to(now)
    data = MeteoSwissPollenCoordinator(hass, "PLZ")._parse_csv(
        CSV_HEADER + f"PLZ;{stamp};0;;;;;"
    )
    assert data["last_update"] == stamp
    assert data["birch"]["current"] == 0
    assert data["alder"]["current"] is None


async def test_repeated_cached_measurement_cannot_extend_freshness(
    hass, aioclient_mock, freezer
):
    aioclient_mock.get(CSV_URL, text=CSV_ZERO)
    coordinator = MeteoSwissPollenCoordinator(
        hass, "PLZ", session=async_get_clientsession(hass)
    )
    freezer.move_to("2026-10-15T14:00:00+00:00")
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    saved = coordinator.data
    freezer.move_to("2026-10-15T14:00:01+00:00")
    await coordinator.async_refresh()
    assert not coordinator.last_update_success
    assert coordinator.data == saved
    assert coordinator.data["last_update"] == "15.10.2026 10:00"
    aioclient_mock.clear_requests()
    aioclient_mock.get(CSV_URL, text=CSV_ZERO.replace("10:00", "14:00"))
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.data["last_update"] == "15.10.2026 14:00"


@pytest.mark.parametrize(
    "payload,expected",
    [
        ({"current": {"uv_index": 0}}, 0),
        ({"current": {"uv_index": 3.2}}, 3.2),
        ({"current": {"uv_index": -1}}, None),
        ({"current": {"uv_index": "nan"}}, None),
        ({"current": {}}, None),
        ({"current": []}, None),
        ([], None),
    ],
)
async def test_uv_is_optional_and_request_uses_utc_seconds(
    hass, aioclient_mock, payload, expected
):
    aioclient_mock.get(OPENMETEO_AQ_BASE_URL, json=aq_payload(birch_pollen=[0]))
    aioclient_mock.get(OPENMETEO_FORECAST_URL, json=payload)
    coordinator = OpenMeteoPollenCoordinator(
        hass, 47.45, 8.56, session=async_get_clientsession(hass)
    )
    await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.data["birch_pollen"]["current"] == 0
    assert coordinator.data["uv_index"] == expected
    assert aioclient_mock.mock_calls[0][1].query["timeformat"] == "unixtime"


@pytest.mark.parametrize(
    "response",
    [
        {"status": 503},
        {"exc": TimeoutError()},
        {"text": "broken JSON"},
    ],
)
async def test_uv_failure_does_not_break_aq_or_leak_coordinates(
    hass, aioclient_mock, caplog, response
):
    aioclient_mock.get(OPENMETEO_AQ_BASE_URL, json=aq_payload(pm10=[0]))
    aioclient_mock.get(OPENMETEO_FORECAST_URL, **response)
    coordinator = OpenMeteoPollenCoordinator(
        hass, 47.451234, 8.561234, session=async_get_clientsession(hass)
    )
    with caplog.at_level(logging.DEBUG, logger=coordinator.logger.name):
        await coordinator.async_refresh()
    assert coordinator.last_update_success
    assert coordinator.data["uv_index"] is None
    assert len(aioclient_mock.mock_calls) == 2
    messages = " ".join(
        r.getMessage() for r in caplog.records if r.name == coordinator.logger.name
    )
    assert "47.451234" not in messages
    assert "8.561234" not in messages
    assert "Optional UV response unavailable" in messages


@pytest.mark.parametrize("provider", ["openmeteo", "measured"])
@pytest.mark.parametrize(
    "response,attempts",
    [
        ({"status": 404}, 1),
        ({"status": 429}, None),
        ({"status": 503}, None),
        ({"exc": TimeoutError()}, None),
        ({"exc": aiohttp.ClientConnectionError("connection failed")}, None),
    ],
)
async def test_transport_failures_are_bounded(
    hass, aioclient_mock, provider, response, attempts
):
    is_open = provider == "openmeteo"
    url = OPENMETEO_AQ_BASE_URL if is_open else CSV_URL
    aioclient_mock.get(url, **response)
    session = async_get_clientsession(hass)
    coordinator = (
        OpenMeteoPollenCoordinator(hass, 47.451234, 8.561234, session=session)
        if is_open
        else MeteoSwissPollenCoordinator(hass, "PLZ", session=session)
    )
    with (
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ),
        pytest.raises(UpdateFailed) as caught,
    ):
        await coordinator._async_update_data()
    assert len(aioclient_mock.mock_calls) == (attempts or (4 if is_open else 3))
    assert "47.451234" not in str(caught.value)
    assert "8.561234" not in str(caught.value)


@pytest.mark.parametrize("provider", ["openmeteo", "measured"])
@pytest.mark.parametrize("malformed", [False, True])
async def test_invalid_payload_is_not_retried_or_rescued_by_uv(
    hass, aioclient_mock, provider, malformed
):
    session = async_get_clientsession(hass)
    if provider == "openmeteo":
        response = (
            {"text": "broken JSON"}
            if malformed
            else {"json": aq_payload(birch_pollen=[None])}
        )
        aioclient_mock.get(OPENMETEO_AQ_BASE_URL, **response)
        coordinator = OpenMeteoPollenCoordinator(hass, 47.45, 8.56, session=session)
    else:
        aioclient_mock.get(
            CSV_URL,
            text="<html>error</html>"
            if malformed
            else CSV_HEADER + "PLZ;15.10.2026 10:00;;;;;;",
        )
        coordinator = MeteoSwissPollenCoordinator(hass, "PLZ", session=session)
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    assert len(aioclient_mock.mock_calls) == 1


@pytest.mark.parametrize("provider", ["openmeteo", "measured"])
async def test_cancellation_is_not_converted_to_failure_or_retried(
    hass, aioclient_mock, provider
):
    session = async_get_clientsession(hass)
    if provider == "openmeteo":
        aioclient_mock.get(OPENMETEO_AQ_BASE_URL, exc=asyncio.CancelledError())
        coordinator = OpenMeteoPollenCoordinator(hass, 47.45, 8.56, session=session)
    else:
        aioclient_mock.get(CSV_URL, exc=asyncio.CancelledError())
        coordinator = MeteoSwissPollenCoordinator(hass, "PLZ", session=session)
    with pytest.raises(asyncio.CancelledError):
        await coordinator._async_update_data()
    assert len(aioclient_mock.mock_calls) == 1


@pytest.mark.parametrize(
    "coordinator_class,args",
    [
        (OpenMeteoPollenCoordinator, (47.45, 8.56)),
        (MeteoSwissPollenCoordinator, ("PLZ",)),
    ],
)
async def test_missing_session_remains_a_setup_error(hass, coordinator_class, args):
    with pytest.raises(RuntimeError, match="No aiohttp session"):
        await coordinator_class(hass, *args)._async_update_data()


async def test_valid_cache_shared_but_old_hour_cannot_extend_currentness(
    hass, aioclient_mock, freezer
):
    session = async_get_clientsession(hass)
    first = OpenMeteoPollenCoordinator(hass, 47.45, 8.56, session=session)
    second = OpenMeteoPollenCoordinator(hass, 47.45, 8.56, session=session)
    freezer.move_to("2026-10-15T10:50:00+00:00")
    aioclient_mock.get(OPENMETEO_AQ_BASE_URL, json=aq_payload(pm10=[2]))
    aioclient_mock.get(OPENMETEO_FORECAST_URL, json={"current": {"uv_index": 0}})
    old = await first._async_update_data()
    assert await second._async_update_data() == old
    assert len(aioclient_mock.mock_calls) == 2
    freezer.move_to("2026-10-15T11:01:00+00:00")
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        OPENMETEO_AQ_BASE_URL,
        json={"hourly": {"time": [CURRENT_TIME + 3600], "pm10": [5]}},
    )
    aioclient_mock.get(OPENMETEO_FORECAST_URL, json={"current": {"uv_index": 0}})
    current = await second._async_update_data()
    assert current["pm10"] == 5
    assert current["last_update"] == "2026-10-15T11:00:00+00:00"
    assert len(aioclient_mock.mock_calls) == 2


async def test_empty_cache_cannot_make_failed_feed_successful(hass, aioclient_mock):
    cache = get_current_weather_cache()
    cache.set("pollen:47.45,8.56", {"last_update": "2026-10-15T10:00:00+00:00"})
    aioclient_mock.get(OPENMETEO_AQ_BASE_URL, json=aq_payload(pm10=[None]))
    coordinator = OpenMeteoPollenCoordinator(
        hass, 47.45, 8.56, session=async_get_clientsession(hass)
    )
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()
    assert cache.get("pollen:47.45,8.56") is None


def test_minimum_poll_interval_is_retained(hass):
    coordinator = OpenMeteoPollenCoordinator(hass, 47.45, 8.56, update_interval=1)
    assert coordinator.update_interval.total_seconds() == MIN_UPDATE_INTERVAL


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, "No data"),
        (0, "None"),
        (1, "Low"),
        (10, "Moderate"),
        (50, "High"),
        (200, "Very High"),
    ],
)
def test_missing_pollen_is_not_zero_risk(value, expected):
    assert _pollen_level(value, 10, 50, 200) == expected


@pytest.mark.parametrize("measured_failure", ["empty", "stale", "future"])
async def test_real_entities_start_failure_recovery_and_unload(
    hass, aioclient_mock, enable_custom_integrations, caplog, measured_failure
):
    """Exercise registered entities, rather than only the coordinator's flag."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "station_id": "KLO",
            "station_name": "Kloten",
            "postal_code": "8302",
            "data_source": "meteoswiss",
        },
    )
    entry.add_to_hass(hass)
    aioclient_mock.get(
        OPENMETEO_AQ_BASE_URL, json=aq_payload(birch_pollen=[0], pm10=[4])
    )
    aioclient_mock.get(OPENMETEO_FORECAST_URL, json={"current": {"uv_index": 0}})
    aioclient_mock.get(CSV_URL, text=CSV_ZERO)
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
                return_value={},
            )
        )
        for target, data in {
            "coordinator.MeteoSwissDataUpdateCoordinator": {
                "temperature": 12,
                "last_update": "2026-10-15T10:00:00+00:00",
            },
            "forecast_coordinator.MeteoSwissForecastCoordinator": [],
            "coordinator.MeteoSwissAlertsCoordinator": [],
        }.items():
            stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.{target}._async_update_data",
                    return_value=data,
                )
            )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        runtime = entry.runtime_data
        registry = er.async_get(hass)
        identifiers = {
            "pollen": f"{DOMAIN}_{entry.entry_id}_pollen_birch_pollen",
            "aq": f"{DOMAIN}_{entry.entry_id}_pm10",
            "measured": f"{DOMAIN}_{entry.entry_id}_ms_pollen_birch",
        }
        entity_ids = {
            key: registry.async_get_entity_id("sensor", DOMAIN, uid)
            for key, uid in identifiers.items()
        }
        assert all(entity_ids.values())

        def state(key):
            return hass.states.get(entity_ids[key])

        assert state("pollen").state == "0.0"
        assert state("aq").state == "4.0"
        assert state("measured").state == "0"
        assert state("pollen").attributes["level_name"] == "None"
        assert state("measured").attributes["last_update"] == "15.10.2026 10:00"
        hazel_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_ms_pollen_hazel"
        )
        assert hass.states.get(hazel_id).attributes["icon"] == "mdi:tree-outline"
        saved = runtime.pollen_coordinator.data
        measured_saved = runtime.meteoswiss_pollen_coordinator.data
        clear_all_caches()
        aioclient_mock.clear_requests()
        aioclient_mock.get(
            OPENMETEO_AQ_BASE_URL,
            json=aq_payload(birch_pollen=[None])
            if measured_failure == "empty"
            else aq_payload(birch_pollen=[0], pm10=[4]),
        )
        aioclient_mock.get(OPENMETEO_FORECAST_URL, json={"current": {"uv_index": 0}})
        failed_csv = {
            "empty": CSV_HEADER + "PLZ;15.10.2026 10:00;;;;;;",
            "stale": CSV_ZERO.replace("10:00", "06:00"),
            "future": CSV_ZERO.replace("10:00", "11:00"),
        }[measured_failure]
        aioclient_mock.get(CSV_URL, text=failed_csv)
        caplog.clear()
        for _ in range(2):
            await runtime.pollen_coordinator.async_refresh()
            await runtime.meteoswiss_pollen_coordinator.async_refresh()
        assert runtime.pollen_coordinator.data == saved
        assert runtime.meteoswiss_pollen_coordinator.data == measured_saved
        assert state("measured").state == "unavailable"
        assert measured_saved["last_update"] == "15.10.2026 10:00"
        if measured_failure == "empty":
            assert all(state(key).state == "unavailable" for key in entity_ids)
        else:
            assert state("pollen").state == "0.0"
            assert state("aq").state == "4.0"
        records = [
            r
            for r in caplog.records
            if r.name
            in (
                runtime.pollen_coordinator.logger.name,
                runtime.meteoswiss_pollen_coordinator.logger.name,
            )
        ]
        assert len([r for r in records if r.levelno == logging.ERROR]) == (
            2 if measured_failure == "empty" else 1
        )
        clear_all_caches()
        aioclient_mock.clear_requests()
        aioclient_mock.get(
            OPENMETEO_AQ_BASE_URL, json=aq_payload(birch_pollen=[None], pm10=[0])
        )
        aioclient_mock.get(OPENMETEO_FORECAST_URL, json={"current": {"uv_index": 0}})
        aioclient_mock.get(CSV_URL, text=CSV_ZERO)
        await runtime.pollen_coordinator.async_refresh()
        await runtime.meteoswiss_pollen_coordinator.async_refresh()
        assert state("pollen").state == "unknown"
        assert state("pollen").attributes["level_name"] == "No data"
        assert state("aq").state == "0.0"
        assert state("measured").state == "0"
        assert all(
            hass.states.get(entity_id).state != "unavailable"
            for entity_id in entity_ids.values()
        )
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert not runtime.pollen_coordinator._listeners
        assert not runtime.meteoswiss_pollen_coordinator._listeners


def test_pollen_entity_without_data_is_unknown_not_zero(hass):
    coordinator = OpenMeteoPollenCoordinator(hass, 47.45, 8.56)
    entity = MeteoSwissPollenSensor(
        coordinator,
        MockConfigEntry(domain=DOMAIN),
        POLLEN_SENSOR_DESCRIPTIONS[0],
        "Kloten",
    )
    assert entity.native_value is None
    assert entity.extra_state_attributes is None
    coordinator.data = {}
    assert entity.native_value is None
    assert entity.extra_state_attributes["level_name"] == "No data"


def test_aq_and_measured_entities_read_existing_data_on_initial_add(hass):
    entry = MockConfigEntry(domain=DOMAIN)
    aq = OpenMeteoPollenCoordinator(hass, 47.45, 8.56)
    aq.data = aq._parse_response(aq_payload(pm10=[0]))
    description = next(
        d for d in AIR_QUALITY_SENSOR_DESCRIPTIONS if d.value_key == "pm10"
    )
    aq_entity = MeteoSwissAirQualitySensor(aq, entry, description, "Kloten")
    assert aq_entity.native_value == 0
    aq.data = None
    assert aq_entity.native_value is None
    measured = MeteoSwissPollenCoordinator(hass, "PLZ")
    measured.data = measured._parse_csv(CSV_ZERO)
    measured_entity = MeteoSwissMeasuredPollenSensor(
        measured, entry, MS_POLLEN_SENSOR_DESCRIPTIONS[0], "Luzern"
    )
    assert measured_entity.native_value == 0
    assert measured_entity.extra_state_attributes["history_24h"] == [0]
    measured.data = None
    assert measured_entity.native_value is None
    assert "history_24h" not in measured_entity.extra_state_attributes


@pytest.mark.parametrize("legacy_registry", [False, True], ids=["new", "existing"])
async def test_pollen_device_grouping_preserves_existing_entities_on_reload(
    hass, aioclient_mock, enable_custom_integrations, legacy_registry
):
    """Both pollen sources belong to Sensors, including upgraded registrations."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "station_id": "KLO",
            "station_name": "Kloten",
            "postal_code": "8302",
            "data_source": "meteoswiss",
        },
    )
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    unique_ids = [
        f"{DOMAIN}_{entry.entry_id}_pollen_{description.pollen_type}"
        for description in POLLEN_SENSOR_DESCRIPTIONS
    ] + [
        f"{DOMAIN}_{entry.entry_id}_ms_pollen_{description.pollen_type}"
        for description in MS_POLLEN_SENSOR_DESCRIPTIONS
    ]

    def personal_settings(entity):
        return (
            entity.entity_id,
            entity.unique_id,
            entity.name,
            entity.icon,
            entity.aliases,
            entity.disabled_by,
            entity.hidden_by,
            entity.options,
        )

    original = {}
    if legacy_registry:
        for index, uid in enumerate(unique_ids):
            entity = registry.async_get_or_create(
                "sensor",
                DOMAIN,
                uid,
                config_entry=entry,
                suggested_object_id=f"personal_pollen_{index}",
                entity_category=EntityCategory.DIAGNOSTIC,
                disabled_by=er.RegistryEntryDisabler.USER if index == 0 else None,
                hidden_by=er.RegistryEntryHider.USER if index == 1 else None,
            )
            entity = registry.async_update_entity(
                entity.entity_id,
                name=f"My pollen {index}",
                icon="mdi:flower",
                aliases={f"Pollen {index}"},
            )
            entity = registry.async_update_entity_options(
                entity.entity_id, "sensor", {"display_precision": 1}
            )
            original[uid] = personal_settings(entity)

    aioclient_mock.get(
        OPENMETEO_AQ_BASE_URL, json=aq_payload(birch_pollen=[0], pm10=[4])
    )
    aioclient_mock.get(OPENMETEO_FORECAST_URL, json={"current": {"uv_index": 0}})
    aioclient_mock.get(CSV_URL, text=CSV_ZERO)
    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
                return_value={},
            )
        )
        for target, data in {
            "coordinator.MeteoSwissDataUpdateCoordinator": {
                "temperature": 12,
                "last_update": "2026-10-15T10:00:00+00:00",
            },
            "forecast_coordinator.MeteoSwissForecastCoordinator": [],
            "coordinator.MeteoSwissAlertsCoordinator": [],
        }.items():
            stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.{target}._async_update_data",
                    return_value=data,
                )
            )

        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        for reloaded in (False, True):
            if reloaded:
                assert await hass.config_entries.async_reload(entry.entry_id)
                await hass.async_block_till_done()
            for uid in unique_ids:
                entity_id = registry.async_get_entity_id("sensor", DOMAIN, uid)
                entity = registry.async_get(entity_id)
                assert entity is not None
                assert entity.entity_category is None
                if uid in original:
                    assert personal_settings(entity) == original[uid]
                else:
                    original[uid] = personal_settings(entity)
            for uid in (f"{DOMAIN}_stations_map", f"{DOMAIN}_cache_stats"):
                entity_id = registry.async_get_entity_id("sensor", DOMAIN, uid)
                assert (
                    registry.async_get(entity_id).entity_category
                    is EntityCategory.DIAGNOSTIC
                )

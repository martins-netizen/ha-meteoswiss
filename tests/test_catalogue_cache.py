"""Station metadata and cache validity contracts."""

from __future__ import annotations

import asyncio
import math
from dataclasses import FrozenInstanceError
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import aiohttp
import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from custom_components.meteoswiss.cache import MeteoSwissCache
from custom_components.meteoswiss.config_flow import MeteoSwissConfigFlow
from custom_components.meteoswiss.const import STATIONS_METADATA_URL
from custom_components.meteoswiss.sensor import (
    MeteoSwissCacheStatsSensor,
    MeteoSwissStationsMapSensor,
)
from custom_components.meteoswiss.stations_map import (
    MAX_CATALOGUE_BYTES,
    MeteoSwissStationsMap,
    WeatherStation,
    get_stations_map,
    parse_station_catalogue,
)

# Provider header/schema checked against the public metadata on 16 Oct 2026.
HEADER = (
    "station_abbr;station_name;station_canton;station_wigos_id;station_type_de;"
    "station_type_fr;station_type_it;station_type_en;station_dataowner;station_data_since;"
    "station_height_masl;station_height_barometer_masl;station_coordinates_lv95_east;"
    "station_coordinates_lv95_north;station_coordinates_wgs84_lat;station_coordinates_wgs84_lon"
)


def catalogue(name="Adelboden"):
    values = [
        "ABO",
        name,
        "BE",
        "0-20000-0-06735",
        "Automatische Wetterstationen",
        "Stations",
        "Stazioni",
        "Automatic stations",
        "MeteoSchweiz",
        "01.01.1901",
        "1321.0",
        "1326.0",
        "2609372.0",
        "1148939.0",
        "46.491703",
        "7.560703",
    ]
    return (HEADER + "\n" + ";".join(values) + "\n").encode("cp1252")


def test_cache_expires_at_its_exact_deadline():
    with patch(
        "custom_components.meteoswiss.cache.time.monotonic", return_value=10
    ) as clock:
        cache = MeteoSwissCache(default_ttl=600)
        cache.set("current", {"temperature": 0})
        clock.return_value = 609.999
        assert cache.get("current") == {"temperature": 0}
        clock.return_value = 610
        assert cache.get("current") is None


async def test_actual_provider_columns_and_encoding_are_used(hass, aioclient_mock):
    aioclient_mock.get(STATIONS_METADATA_URL, content=catalogue("Oberägeri"))
    loaded = await MeteoSwissStationsMap().load_stations(
        session=async_get_clientsession(hass)
    )
    assert loaded["abo"].name == "Oberägeri"
    assert loaded["abo"].altitude == 1321
    assert loaded["abo"].canton == "BE"


@pytest.fixture
def metadata_clock(monkeypatch):
    clock = Mock(return_value=10.0)
    fake_time = SimpleNamespace(monotonic=clock)
    monkeypatch.setattr("custom_components.meteoswiss.stations_map.time", fake_time)
    monkeypatch.setattr("custom_components.meteoswiss.cache.time", fake_time)
    return clock


@pytest.mark.parametrize("encoding", ["cp1252", "utf-8-sig"])
def test_named_reordered_columns_quoted_names_and_zero_coordinates(encoding):
    data = 'name;lon;station;canton;lat;altitude\n"Müller; Süd";0;ZERO;ZH;0;nan\n'
    station = parse_station_catalogue(data.encode(encoding))["zero"]
    assert station.name == "Müller; Süd"
    assert station.latitude == station.longitude == 0
    assert station.altitude is None
    assert station.to_geojson_feature()["geometry"]["coordinates"] == [0, 0]


@pytest.mark.parametrize(
    "data",
    [
        b"",
        b"wrong;header\nx;y",
        b"station;name;name\nx;y;z",
        b'station;name\nx;"unterminated',
        b"station;name\n;name\nx;\n",
        b"station;name;lat;lon\nx;X;nan;8",
        b"station;name;lat;lon\nx;X;47;181",
        b"station;name\nx;First\nx;Other",
        b"\x81",
        b"x" * (MAX_CATALOGUE_BYTES + 1),
    ],
)
def test_invalid_catalogues_do_not_form_a_valid_empty_snapshot(data):
    with pytest.raises((ValueError, UnicodeError)):
        parse_station_catalogue(data)


def test_missing_geometry_bad_rows_and_identical_duplicates():
    stations = parse_station_catalogue(
        b"station;name;lat;lon\nx;Good;0;0\nx;Good;0;0\nno;No coordinates;47;\n"
        b"bad;Bad;inf;8\n;No ID;47;8\nshort\ntoo;many;47;8;extra\n\n"
    )
    assert set(stations) == {"x", "no"}
    assert not stations["no"].has_coordinates
    assert stations["no"].to_geojson_feature()["geometry"] is None


async def test_catalogue_cache_has_original_deadline_and_copies_are_isolated(
    hass, aioclient_mock, metadata_clock
):
    aioclient_mock.get(STATIONS_METADATA_URL, content=catalogue())
    session = async_get_clientsession(hass)
    loader = MeteoSwissStationsMap()
    first = await loader.load_stations(session)
    timestamp = loader.last_successful_update
    first.clear()
    metadata_clock.return_value += 86399
    assert (await loader.load_stations(session))["abo"].name == "Adelboden"
    other = MeteoSwissStationsMap()
    assert (await other.load_stations(session))["abo"].altitude == 1321
    assert other.last_successful_update == timestamp
    assert len(aioclient_mock.mock_calls) == 1
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATIONS_METADATA_URL, content=catalogue("New name"))
    metadata_clock.return_value += 1
    assert loader.data_status == "stale"
    assert (await loader.load_stations(session))["abo"].name == "New name"
    assert loader.data_status == "current"
    assert not session.closed
    with pytest.raises(FrozenInstanceError):
        loader.get_station("ABO").name = "Cannot mutate shared metadata"


async def test_expired_catalogue_is_labelled_stale_and_user_retry_recovers(
    hass,
    aioclient_mock,
    metadata_clock,
    caplog,
    freezer,
):
    freezer.move_to("2026-10-16T13:00:00Z")
    session = async_get_clientsession(hass)
    loader = MeteoSwissStationsMap()
    aioclient_mock.get(STATIONS_METADATA_URL, content=catalogue())
    await loader.load_stations(session)
    successful = loader.last_successful_update
    metadata_clock.return_value += 86400
    freezer.tick(86400)
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATIONS_METADATA_URL, status=503)
    with patch(
        "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
    ):
        assert (await loader.load_stations(session))["abo"].name == "Adelboden"
        assert loader.last_successful_update == successful
        assert loader.data_status == "stale"
        assert not loader.last_update_success
        assert len(aioclient_mock.mock_calls) == 3
        await loader.load_stations(session)
        assert len(aioclient_mock.mock_calls) == 3
        metadata_clock.return_value += 300
        await loader.load_stations(session)
        assert len(aioclient_mock.mock_calls) == 6
    assert (
        len(
            [
                r
                for r in caplog.records
                if r.name.endswith("stations_map") and r.levelname == "WARNING"
            ]
        )
        == 1
    )
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATIONS_METADATA_URL, content=catalogue("Recovered"))
    await loader.load_stations(session, retry=True)
    assert loader.data_status == "current"
    assert loader.get_station("abo").name == "Recovered"
    assert loader.last_successful_update != successful
    assert (
        len(
            [
                r
                for r in caplog.records
                if r.name.endswith("stations_map") and "recovered" in r.getMessage()
            ]
        )
        == 1
    )


@pytest.mark.parametrize(
    "response,attempts",
    [
        ({"status": 404}, 1),
        ({"status": 429}, 3),
        ({"status": 503}, 3),
        ({"exc": TimeoutError()}, 3),
        ({"exc": aiohttp.ClientConnectionError("private 47.451234 8.561234")}, 3),
        ({"content": b"wrong;header\nx;y"}, 1),
        ({"content": b"\x81"}, 1),
    ],
)
async def test_catalogue_failures_are_bounded_and_retryable(
    hass, aioclient_mock, response, attempts, caplog
):
    aioclient_mock.get(STATIONS_METADATA_URL, **response)
    loader = MeteoSwissStationsMap()
    with patch(
        "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
    ):
        assert await loader.load_stations(async_get_clientsession(hass)) == {}
    assert loader.data_status == "unavailable"
    assert len(aioclient_mock.mock_calls) == attempts
    assert "47.451234" not in caplog.text
    assert "8.561234" not in caplog.text


async def test_concurrent_loads_share_one_inflight_fetch(hass):
    loader = MeteoSwissStationsMap()
    ready = asyncio.Event()

    async def fetch(*args):
        await ready.wait()
        return catalogue()

    with patch.object(loader, "_async_download", side_effect=fetch) as fetcher:
        tasks = [
            asyncio.create_task(loader.load_stations(async_get_clientsession(hass)))
            for _ in range(4)
        ]
        await asyncio.sleep(0)
        assert fetcher.call_count == 1
        ready.set()
        results = await asyncio.gather(*tasks)
    assert all(result["abo"].name == "Adelboden" for result in results)
    assert fetcher.call_count == 1


async def test_owned_session_closes_and_cancellation_is_not_a_source_failure(hass):
    # Test integration context ownership, not aiohttp's transport internals.
    # Replacing the constructor around aioclient_mock can bypass its patch.
    owned_session = AsyncMock()
    owned_session.__aenter__.return_value = owned_session
    loader = MeteoSwissStationsMap()
    with (
        patch(
            "custom_components.meteoswiss.stations_map.aiohttp.ClientSession",
            return_value=owned_session,
        ),
        patch.object(loader, "_async_download", return_value=catalogue()) as download,
    ):
        await loader.load_stations()
    download.assert_awaited_once_with(owned_session)
    owned_session.__aenter__.assert_awaited_once()
    owned_session.__aexit__.assert_awaited_once()
    loader = MeteoSwissStationsMap()
    # Force a network attempt rather than the valid shared cache.
    from custom_components.meteoswiss.cache import get_stations_cache

    get_stations_cache().clear()
    with (
        patch.object(loader, "_async_download", side_effect=asyncio.CancelledError),
        pytest.raises(asyncio.CancelledError),
    ):
        await loader.load_stations(async_get_clientsession(hass))
    assert loader.last_update_success is None
    assert not loader._lock.locked()


async def test_total_catalogue_wait_is_bounded(hass):
    loader = MeteoSwissStationsMap()

    async def blocked(*args):
        await asyncio.Event().wait()

    with (
        patch.object(loader, "_async_download", side_effect=blocked),
        patch(
            "custom_components.meteoswiss.stations_map.DEFAULT_API_TIMEOUT",
            aiohttp.ClientTimeout(total=0),
        ),
    ):
        assert await loader.load_stations(async_get_clientsession(hass)) == {}
    assert loader.last_exception == "TimeoutError"


async def test_global_load_false_never_fetches_and_manual_retry_is_forwarded(hass):
    first = await get_stations_map(load=False)
    assert first is await get_stations_map(load=False)
    with patch.object(first, "load_stations", return_value={}) as load:
        assert (
            await get_stations_map(async_get_clientsession(hass), retry=True) is first
        )
    assert load.call_args.kwargs["retry"] is True


def test_geographic_exports_distance_and_north_up_map():
    loader = MeteoSwissStationsMap()
    loader._stations = {
        "zero": WeatherStation("ZERO", "A zero", 0, 0, canton="ZH"),
        "north": WeatherStation("NORTH", "B north", 47.8, 10.5, canton="BE"),
        "south": WeatherStation("SOUTH", "C south", 45.8, 5.9),
        "missing": WeatherStation("MISSING", "D missing", None, None),
    }
    assert loader.get_station("zero").latitude == 0
    assert loader.get_station("absent") is None
    assert [station.station_id for station in loader.get_stations_by_canton("zh")] == [
        "ZERO"
    ]
    assert loader.get_nearby_stations(0, 0, max_distance_km=0)[0][1] == 0
    assert len(loader.get_nearby_stations(0, 0, max_distance_km=20000, limit=1)) == 1
    assert loader.get_nearby_stations(0, 0, limit=0) == []
    assert loader._calculate_distance(0, 0, 0, 180) == pytest.approx(math.pi * 6371)
    assert len(loader.to_geojson()["features"]) == 4
    assert loader.to_picture_elements_config() is None
    card = loader.to_picture_elements_config(
        image="/local/map.png", entity_id="sensor.existing_station_map"
    )
    assert card["image"] == "/local/map.png"
    assert card["elements"][1]["style"]["top"] == "0%"
    assert card["elements"][2]["style"]["top"] == "100%"
    assert all(
        element["entity"] == "sensor.existing_station_map"
        for element in card["elements"]
    )
    assert "imgur" not in repr(card)


@pytest.mark.parametrize(
    "bounds",
    [
        {"latitude": 91},
        {"longitude": -181},
        {"latitude": float("nan")},
        {"max_distance_km": -1},
        {"limit": -1},
        {"limit": True},
        {"limit": 1.5},
    ],
)
def test_invalid_nearby_search_cannot_produce_plausible_positions(bounds):
    with pytest.raises(ValueError):
        MeteoSwissStationsMap().get_nearby_stations(
            **{"latitude": 47, "longitude": 8, **bounds}
        )


async def test_config_flow_can_retry_immediately_after_catalogue_failure(
    hass, aioclient_mock
):
    flow = MeteoSwissConfigFlow()
    flow.hass = hass
    aioclient_mock.get(STATIONS_METADATA_URL, status=503)
    with patch(
        "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
    ):
        assert await flow._load_stations() == []
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATIONS_METADATA_URL, content=catalogue())
    assert (await flow._load_stations())[0]["label"] == "Adelboden (ABO)"
    assert len(aioclient_mock.mock_calls) == 1


async def test_station_sensor_reports_availability_and_last_good_catalogue(
    hass, aioclient_mock, metadata_clock
):
    loader = MeteoSwissStationsMap()
    sensor = MeteoSwissStationsMapSensor(loader)
    sensor.hass = hass
    assert not sensor.available
    aioclient_mock.get(STATIONS_METADATA_URL, content=catalogue())
    await sensor.async_update()
    assert sensor.available
    assert sensor.native_value == "1 stations"
    assert sensor.extra_state_attributes["catalogue_status"]["data_status"] == "current"
    assert sensor.extra_state_attributes["picture_elements_config"] is None
    metadata_clock.return_value += 86400
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATIONS_METADATA_URL, status=404)
    await sensor.async_update()
    assert not sensor.available
    assert sensor.extra_state_attributes["catalogue_status"]["data_status"] == "stale"
    assert sensor.extra_state_attributes["station_count"] == 1


async def test_overall_cache_hit_rate_includes_station_metadata():
    sensor = MeteoSwissCacheStatsSensor()
    stats = {
        "current_weather": {"hits": 0, "misses": 1},
        "forecast": {"hits": 1, "misses": 1},
        "stations": {"hits": 2, "misses": 0},
    }
    with patch(
        "custom_components.meteoswiss.sensor.get_all_cache_stats", return_value=stats
    ):
        await sensor.async_update()
    assert sensor.extra_state_attributes["overall_hit_rate"] == 60


@pytest.mark.parametrize(
    "response", [{"status": 404}, {"status": 503}, {"content": b"wrong;header\nx;y"}]
)
async def test_cold_catalogue_failure_never_reports_a_healthy_zero(
    hass, aioclient_mock, response
):
    sensor = MeteoSwissStationsMapSensor(MeteoSwissStationsMap())
    sensor.hass = hass
    aioclient_mock.get(STATIONS_METADATA_URL, **response)
    with patch(
        "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
    ):
        await sensor.async_update()
    assert not sensor.available
    assert sensor.native_value is None
    assert (
        sensor.extra_state_attributes["catalogue_status"]["data_status"]
        == "unavailable"
    )
    assert sensor.extra_state_attributes["station_count"] == 0


@pytest.mark.parametrize(
    "response", [{"status": 404}, {"status": 503}, {"content": b"wrong;header\nx;y"}]
)
async def test_catalogue_sensor_expires_fails_and_recovers_without_losing_metadata(
    hass, aioclient_mock, metadata_clock, freezer, response
):
    loader = MeteoSwissStationsMap()
    sensor = MeteoSwissStationsMapSensor(loader)
    sensor.hass = hass
    aioclient_mock.get(STATIONS_METADATA_URL, content=catalogue())
    await sensor.async_update()
    assert sensor.available
    snapshot = sensor.extra_state_attributes
    successful = loader.last_successful_update
    # Expiry is effective even before the next diagnostic polling callback.
    metadata_clock.return_value += 86400
    freezer.tick(86400)
    assert not sensor.available
    assert sensor.extra_state_attributes["catalogue_status"]["data_status"] == "stale"
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATIONS_METADATA_URL, **response)
    with patch(
        "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
    ):
        await sensor.async_update()
    assert not sensor.available
    assert sensor.extra_state_attributes["station_count"] == 1
    assert sensor.extra_state_attributes["stations"] == snapshot["stations"]
    assert sensor.extra_state_attributes["geojson"] == snapshot["geojson"]
    assert loader.last_successful_update == successful
    assert (
        sensor.extra_state_attributes["catalogue_status"]["last_update_success"]
        is False
    )
    metadata_clock.return_value += 300
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATIONS_METADATA_URL, content=catalogue("Recovered"))
    await sensor.async_update()
    assert sensor.available
    assert sensor.native_value == "1 stations"
    assert sensor.extra_state_attributes["catalogue_status"]["data_status"] == "current"
    assert sensor.extra_state_attributes["catalogue_status"]["last_exception"] is None
    assert loader.last_successful_update != successful


async def test_registered_catalogue_sensor_reports_unavailable_and_recovers(
    hass, aioclient_mock, metadata_clock, enable_custom_integrations
):
    from contextlib import ExitStack

    from homeassistant.components.sensor import DATA_COMPONENT
    from homeassistant.helpers import entity_registry as er
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    from custom_components.meteoswiss.const import DOMAIN
    from custom_components.meteoswiss.diagnostics import (
        async_get_config_entry_diagnostics,
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "data_source": "openmeteo",
            "latitude": 0,
            "longitude": 0,
            "postal_code": "9997",
        },
    )
    entry.add_to_hass(hass)
    aioclient_mock.get(STATIONS_METADATA_URL, content=catalogue())
    with ExitStack() as stack:
        for target, data in {
            "coordinator.OpenMeteoDataUpdateCoordinator": {"temperature": 12},
            "coordinator.MeteoSwissForecastCoordinator": [],
            "coordinator.MeteoSwissAlertsCoordinator": [],
            "pollen_coordinator_openmeteo.OpenMeteoPollenCoordinator": {},
            "coordinator.MeteoSwissPollenCoordinator": {},
        }.items():
            stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.{target}._async_update_data",
                    return_value=data,
                )
            )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        entity_id = registry.async_get_entity_id(
            "sensor", DOMAIN, f"{DOMAIN}_stations_map"
        )
        sensor = hass.data[DATA_COMPONENT].get_entity(entity_id)
        identity = (sensor.unique_id, sensor.device_info)
        await sensor.async_update_ha_state(force_refresh=True)
        assert hass.states.get(entity_id).state == "1 stations"
        metadata_clock.return_value += 86400
        aioclient_mock.clear_requests()
        aioclient_mock.get(STATIONS_METADATA_URL, status=404)
        await sensor.async_update_ha_state(force_refresh=True)
        assert hass.states.get(entity_id).state == "unavailable"
        # HA omits extra entity attributes while unavailable. Retained catalogue
        # evidence remains in the redacted integration diagnostic, without IO.
        calls = len(aioclient_mock.mock_calls)
        report = await async_get_config_entry_diagnostics(hass, entry)
        assert len(aioclient_mock.mock_calls) == calls
        assert report["station_catalogue"]["data_status"] == "stale"
        assert report["station_catalogue"]["station_count"] == 1
        metadata_clock.return_value += 300
        aioclient_mock.clear_requests()
        aioclient_mock.get(STATIONS_METADATA_URL, content=catalogue("Recovered"))
        await sensor.async_update_ha_state(force_refresh=True)
        assert hass.states.get(entity_id).state == "1 stations"
        assert sensor.entity_id == entity_id
        assert (sensor.unique_id, sensor.device_info) == identity
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()

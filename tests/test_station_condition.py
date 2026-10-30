"""Station-local model codes, measured-value isolation, time and IO boundaries."""

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
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.meteoswiss.cache import clear_all_caches
from custom_components.meteoswiss.const import CONF_FORECAST_LOCATION, DOMAIN
from custom_components.meteoswiss.coordinator import (
    MeteoSwissDataUpdateCoordinator,
    MeteoSwissForecastCoordinator,
    MeteoSwissStationConditionCoordinator,
)
from custom_components.meteoswiss.diagnostics import async_get_config_entry_diagnostics
from custom_components.meteoswiss.forecast_location_config import (
    encode_forecast_location,
)
from custom_components.meteoswiss.forecast_locations import (
    ForecastPointType,
    parse_forecast_catalogue,
)
from custom_components.meteoswiss.station_condition import (
    STATION_CONDITION_SOURCE,
    STATION_CONDITION_URL,
    StationConditionClient,
    StationConditionError,
    current_station_condition,
)
from custom_components.meteoswiss.stations_map import (
    MeteoSwissStationsMap,
    WeatherStation,
)
from custom_components.meteoswiss.weather import MeteoSwissWeather

NOW = datetime(2026, 10, 24, 13, 25, tzinfo=UTC)
HOUR = NOW.replace(minute=0)
ALT = WeatherStation("ALT", "Altdorf", 46.88, 8.62, 438)
KLO = WeatherStation("KLO", "Zürich / Kloten", 47.48, 8.53, 436)


@pytest.fixture(autouse=True)
def isolated(freezer):
    freezer.move_to(NOW)
    clear_all_caches()
    yield
    clear_all_caches()


def payload(**changes):
    return {
        "current": {
            "time": HOUR.timestamp(),
            "interval": 3600,
            "weather_code": 3,
            "is_day": 1,
            **changes,
        }
    }


def snapshot(**changes):
    return {
        "time": HOUR.isoformat(),
        "valid_until": (HOUR + timedelta(hours=1)).isoformat(),
        "fetched_at": NOW.isoformat(),
        "weather_code": 3,
        "is_day": True,
        **changes,
    }


def station_source(hass, station=ALT):
    return MeteoSwissStationConditionCoordinator(
        hass, station.station_id, async_get_clientsession(hass)
    )


@pytest.fixture
def catalogue():
    stations = MeteoSwissStationsMap()
    stations._stations = {"alt": ALT, "klo": KLO}
    with patch(
        "custom_components.meteoswiss.coordinator.get_stations_map",
        return_value=stations,
    ):
        yield stations


@pytest.mark.parametrize("elevation", [None, 0, 438])
@pytest.mark.parametrize(
    "code,day,expected",
    [(0, 0, "clear-night"), (0, 1, "sunny"), (3, 1, "cloudy"), (71, 0, "snowy")],
)
async def test_request_only_station_condition_and_daylight(
    hass, aioclient_mock, elevation, code, day, expected
):
    aioclient_mock.get(
        STATION_CONDITION_URL, json=payload(weather_code=code, is_day=day)
    )
    session = async_get_clientsession(hass)
    data = await StationConditionClient(
        ALT.latitude, ALT.longitude, session, elevation=elevation
    ).async_get_data()
    assert current_station_condition(data) == expected
    query = aioclient_mock.mock_calls[0][1].query
    assert query["latitude"] == str(ALT.latitude) and query["longitude"] == str(
        ALT.longitude
    )
    assert query["models"] == "meteoswiss_icon_seamless"
    assert query["current"] == "weather_code,is_day"
    assert not {"hourly", "daily"} & query.keys()
    assert ("elevation" in query) == (elevation is not None)
    assert not session.closed


@pytest.mark.parametrize(
    "kwargs",
    [
        {"latitude": None},
        {"latitude": True},
        {"latitude": 91},
        {"longitude": -181},
        {"longitude": "inf"},
        {"elevation": "nan"},
    ],
)
def test_invalid_coordinates_never_make_a_request(kwargs):
    with pytest.raises(ValueError, match="Invalid station condition location"):
        StationConditionClient(
            **{
                "latitude": ALT.latitude,
                "longitude": ALT.longitude,
                "session": None,
                **kwargs,
            }
        )


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {},
        {"current": None},
        {"current": []},
        *[
            payload(time=x)
            for x in (
                None,
                True,
                "bad",
                HOUR.timestamp() - 3600,
                HOUR.timestamp() + 3600,
            )
        ],
        *[payload(interval=x) for x in (None, True, 0, 3601, "nan")],
        *[payload(is_day=x) for x in (None, True, 0.5, 2)],
        *[payload(weather_code=x) for x in (None, True, 0.5, 100, {}, "nan")],
    ],
)
async def test_invalid_payload_does_not_retry_or_cache(hass, aioclient_mock, data):
    aioclient_mock.get(STATION_CONDITION_URL, text=json.dumps(data))
    with pytest.raises(StationConditionError):
        await StationConditionClient(
            ALT.latitude, ALT.longitude, async_get_clientsession(hass)
        ).async_get_data()
    assert len(aioclient_mock.mock_calls) == 1


@pytest.mark.parametrize(
    "data",
    [
        None,
        [],
        {},
        snapshot(is_day=1),
        snapshot(time=None),
        snapshot(valid_until="bad"),
        snapshot(fetched_at="bad"),
        snapshot(time=(NOW + timedelta(minutes=1)).isoformat()),
        snapshot(valid_until=NOW.isoformat()),
        snapshot(valid_until=(HOUR + timedelta(hours=2)).isoformat()),
        snapshot(fetched_at=(NOW - timedelta(minutes=21)).isoformat()),
        snapshot(fetched_at=(NOW + timedelta(minutes=6)).isoformat()),
        snapshot(weather_code=123),
    ],
)
def test_cached_condition_must_still_be_current_and_meaningful(data):
    assert current_station_condition(data) is None


@pytest.mark.parametrize(
    "response,attempts",
    [
        ({"status": 403}, 1),
        ({"status": 429}, 3),
        ({"status": 503}, 3),
        ({"exc": TimeoutError()}, 3),
        ({"exc": aiohttp.ClientConnectionError("latitude=46.88 private-url")}, 3),
        ({"text": "bad JSON"}, 1),
        ({"exc": UnicodeError("private payload")}, 1),
    ],
)
async def test_transport_failures_are_bounded_and_private(
    hass, aioclient_mock, catalogue, caplog, response, attempts
):
    aioclient_mock.get(STATION_CONDITION_URL, **response)
    source = station_source(hass)
    with (
        patch(
            "custom_components.meteoswiss.retry.asyncio.sleep", new_callable=AsyncMock
        ),
        caplog.at_level(logging.DEBUG, logger=source.logger.name),
    ):
        await source.async_refresh()
    assert not source.last_update_success
    assert source.update_interval == timedelta(minutes=10)
    assert len(aioclient_mock.mock_calls) == attempts
    formatted = "\n".join(logging.Formatter().format(r) for r in caplog.records)
    assert (
        "latitude=" not in formatted
        and "46.88" not in formatted
        and "private payload" not in formatted
    )
    assert source.last_exception.translation_key == "station_condition_unavailable"


async def test_missing_session_is_a_source_failure():
    with pytest.raises(StationConditionError):
        await StationConditionClient(ALT.latitude, ALT.longitude, None).async_get_data()


async def test_coordinate_cache_does_not_extend_lifetime(
    hass, aioclient_mock, catalogue, freezer
):
    aioclient_mock.get(STATION_CONDITION_URL, json=payload())
    first = await station_source(hass)._async_update_data()
    freezer.tick(timedelta(minutes=2))
    second = await station_source(hass)._async_update_data()
    assert second == first and len(aioclient_mock.mock_calls) == 1
    freezer.tick(timedelta(minutes=9))
    await station_source(hass)._async_update_data()
    assert len(aioclient_mock.mock_calls) == 2
    # Another station must not inherit the first location's cache or code.
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATION_CONDITION_URL, json=payload(weather_code=0))
    other = await station_source(hass, KLO)._async_update_data()
    assert current_station_condition(other) == "sunny"
    assert aioclient_mock.mock_calls[-1][1].query["latitude"] == str(KLO.latitude)


async def test_current_interval_bounds_the_poll_and_cache(
    hass, aioclient_mock, catalogue, freezer
):
    freezer.move_to(HOUR + timedelta(minutes=55))
    aioclient_mock.get(STATION_CONDITION_URL, json=payload())
    source = station_source(hass)
    await source._async_update_data()
    assert source.update_interval == timedelta(minutes=5)
    freezer.move_to(HOUR + timedelta(hours=1))
    aioclient_mock.clear_requests()
    aioclient_mock.get(
        STATION_CONDITION_URL,
        json=payload(time=(HOUR + timedelta(hours=1)).timestamp(), weather_code=61),
    )
    data = await source._async_update_data()
    assert current_station_condition(data) == "rainy"
    assert source.update_interval == timedelta(minutes=10)
    assert len(aioclient_mock.mock_calls) == 1


@pytest.mark.parametrize(
    "station", [None, WeatherStation("ALT", "Altdorf", None, None)]
)
async def test_no_station_metadata_never_borrows_home_or_poi(
    hass, catalogue, aioclient_mock, station
):
    catalogue._stations = {"alt": station} if station else {}
    with pytest.raises(UpdateFailed) as caught:
        await station_source(hass)._async_update_data()
    assert caught.value.translation_key == "station_condition_unavailable"
    assert not aioclient_mock.mock_calls


async def test_coordinator_rejects_corrupted_client_snapshot(hass, catalogue):
    with (
        patch.object(StationConditionClient, "async_get_data", return_value={}),
        pytest.raises(UpdateFailed),
    ):
        await station_source(hass)._async_update_data()


@pytest.mark.parametrize("explicit", [False, True])
async def test_model_condition_never_overwrites_measured_attributes_or_borrows_poi(
    hass, explicit, freezer
):
    data = {"station_id": "ALT"}
    if explicit:
        catalogue = parse_forecast_catalogue(
            (Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv")
            .read_text()
            .encode("latin-1"),
            NOW,
        )
        data[CONF_FORECAST_LOCATION] = encode_forecast_location(
            catalogue.select(ForecastPointType.POINT_OF_INTEREST, "711")
        )
    entry = MockConfigEntry(domain=DOMAIN, data=data)
    current = MeteoSwissDataUpdateCoordinator(hass, "ALT", 600)
    current.data = {
        "temperature": 7.8,
        "humidity": 79.2,
        "pressure": 1022.7,
        "wind_speed": 5.4,
        "precipitation": 1,
    }
    forecast = MeteoSwissForecastCoordinator(hass, latitude=47.2, longitude=9.3)
    forecast.data = [
        {"datetime": HOUR.isoformat(), "temperature": -6.8, "condition": "snowy"}
    ]
    model = station_source(hass)
    model.data = snapshot()
    entity = MeteoSwissWeather(
        current, forecast, entry, "Altdorf", station_condition_coordinator=model
    )
    assert entity.condition == "cloudy"
    assert (
        entity.native_temperature,
        entity.humidity,
        entity.native_pressure,
        entity.native_wind_speed,
    ) == (7.8, 79.2, 1022.7, 5.4)
    assert entity.extra_state_attributes["condition_value_type"] == "modelled"
    assert entity.extra_state_attributes["condition_location"] == "weather_station"
    assert entity.extra_state_attributes["condition_source"] == STATION_CONDITION_SOURCE
    assert entity.extra_state_attributes["condition_timestamp"] == HOUR.isoformat()
    assert "Open-Meteo" in entity.attribution
    model.last_update_success = False
    assert entity.condition is None and entity.available
    assert entity.extra_state_attributes["condition_available"] is False
    assert "condition_timestamp" not in entity.extra_state_attributes
    assert entity.native_temperature == 7.8
    model.last_update_success = True
    freezer.move_to(HOUR + timedelta(hours=1))
    assert entity.condition is None  # No expired sunny/snowy/rain heuristic.
    current.data["weather_condition"] = "fog"
    assert entity.condition == "fog"
    assert "condition_source" not in (entity.extra_state_attributes or {})


@pytest.fixture
async def live_entry(
    hass, enable_custom_integrations, aioclient_mock, request, freezer
):
    """Real HA setup, model transport and station metadata with distinct places."""
    points = parse_forecast_catalogue(
        (Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv")
        .read_text()
        .encode("latin-1"),
        NOW,
    )
    selected = points.select(ForecastPointType.POINT_OF_INTEREST, "711")
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "data_source": "meteoswiss",
            "station_id": "ALT",
            "station_name": "Altdorf",
            "postal_code": "8302",
            "latitude": 1.1,
            "longitude": 2.2,
            CONF_FORECAST_LOCATION: encode_forecast_location(selected),
        },
    )
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    kept = registry.async_get_or_create(
        "weather",
        DOMAIN,
        f"{DOMAIN}_{entry.entry_id}_weather",
        config_entry=entry,
        suggested_object_id="retained_station",
    )
    registry.async_update_entity(kept.entity_id, name="My station")
    station_map = MeteoSwissStationsMap()
    station_map._stations = {"alt": ALT, "klo": KLO}
    response = dict(getattr(request, "param", {"json": payload()}))
    clock = response.pop("clock", None)
    if clock is not None:
        freezer.move_to(clock)
    aioclient_mock.get(STATION_CONDITION_URL, **response)

    async def observations(source):
        return {
            "temperature": 7.8 if source.station_id == "alt" else 9.5,
            "humidity": 79.2,
            "pressure": 1022.7,
            "precipitation": 0,
            "last_update": NOW.isoformat(),
        }

    with ExitStack() as stack:
        stack.enter_context(
            patch(
                "custom_components.meteoswiss.stations_map._stations_map", station_map
            )
        )
        stack.enter_context(
            patch.object(
                station_map, "load_stations", return_value=station_map._stations
            )
        )
        stack.enter_context(
            patch.object(
                MeteoSwissDataUpdateCoordinator, "_async_update_data", observations
            )
        )
        for name, data in {
            "MeteoSwissForecastCoordinator": [
                {
                    "datetime": HOUR.isoformat(),
                    "fetched_at": NOW.isoformat(),
                    "condition": "snowy",
                    "temperature": -6.8,
                }
            ],
            "MeteoSwissAlertsCoordinator": [],
            "OpenMeteoPollenCoordinator": {},
            "MeteoSwissPollenCoordinator": {},
        }.items():
            stack.enter_context(
                patch(
                    f"custom_components.meteoswiss.coordinator.{name}._async_update_data",
                    return_value=data,
                )
            )
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        yield entry, kept.entity_id
        if getattr(entry, "runtime_data", None) is not None:
            assert await hass.config_entries.async_unload(entry.entry_id)
            await hass.async_block_till_done()


async def test_loaded_failure_recovery_and_station_reload_preserve_ids_and_places(
    hass, live_entry, aioclient_mock
):
    entry, weather_id = live_entry
    runtime = entry.runtime_data
    source = runtime.station_condition_coordinator
    predicted_id = er.async_get(hass).async_get_entity_id(
        "weather", DOMAIN, f"{DOMAIN}_{entry.entry_id}_forecast_weather"
    )
    measured = hass.states.get(weather_id)
    assert measured.state == "cloudy" and measured.name == "My station"
    assert measured.attributes["temperature"] == 7.8
    assert measured.attributes["condition_value_type"] == "modelled"
    assert hass.states.get(predicted_id).state == "snowy"
    assert aioclient_mock.mock_calls[0][1].query["latitude"] == str(ALT.latitude)
    assert len(aioclient_mock.mock_calls) == 1
    source.async_set_update_error(StationConditionError())
    await hass.async_block_till_done()
    assert hass.states.get(weather_id).state == "unknown"
    assert hass.states.get(weather_id).attributes["temperature"] == 7.8
    assert hass.states.get(weather_id).attributes["condition_available"] is False
    assert hass.states.get(predicted_id).state == "snowy"
    source.async_set_updated_data(snapshot(weather_code=45))
    await hass.async_block_till_done()
    assert hass.states.get(weather_id).state == "fog"
    diagnostics = await async_get_config_entry_diagnostics(hass, entry)
    assert diagnostics["coordinators"]["station_condition_coordinator"]["available"]
    serialized = json.dumps(diagnostics)
    assert "46.88" not in serialized and "8.62" not in serialized
    # A deliberate station change reloads the entry. Metadata, not old saved
    # coordinates or the unchanged mountain forecast, chooses the new query.
    aioclient_mock.clear_requests()
    aioclient_mock.get(STATION_CONDITION_URL, json=payload(weather_code=61))
    hass.config_entries.async_update_entry(
        entry,
        data={**entry.data, "station_id": "KLO", "station_name": "Zürich / Kloten"},
    )
    await hass.async_block_till_done()
    assert hass.states.get(weather_id).state == "rainy"
    assert hass.states.get(weather_id).attributes["temperature"] == 9.5
    assert hass.states.get(weather_id).name == "My station"
    assert hass.states.get(predicted_id).state == "snowy"
    assert aioclient_mock.mock_calls[0][1].query["latitude"] == str(KLO.latitude)
    assert len(aioclient_mock.mock_calls) == 1
    assert not source._listeners
    new_source = entry.runtime_data.station_condition_coordinator
    session = entry.runtime_data.session
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert not new_source._listeners and not session.closed


@pytest.mark.parametrize("live_entry", [{"status": 403}], indirect=True)
async def test_failed_optional_condition_does_not_block_setup_or_measurements(
    hass, live_entry
):
    entry, weather_id = live_entry
    assert entry.runtime_data.coordinator.last_update_success
    assert not entry.runtime_data.station_condition_coordinator.last_update_success
    assert hass.states.get(weather_id).state == "unknown"
    assert hass.states.get(weather_id).attributes["temperature"] == 7.8


async def test_unload_cancels_pending_condition_request_without_closing_ha_session(
    hass, live_entry
):
    entry, _ = live_entry
    source, session = (
        entry.runtime_data.station_condition_coordinator,
        entry.runtime_data.session,
    )
    started = asyncio.Event()

    async def blocked_request(_client):
        started.set()
        await asyncio.Future()

    clear_all_caches()
    with patch.object(StationConditionClient, "async_get_data", blocked_request):
        task = entry.async_create_background_task(
            hass, source.async_request_refresh(), "test station condition request"
        )
        await asyncio.wait_for(started.wait(), timeout=1)
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
        assert task.done() and not source._listeners and not session.closed


@pytest.mark.parametrize(
    "live_entry",
    [{"json": payload(), "clock": HOUR + timedelta(minutes=59)}],
    indirect=True,
)
async def test_registered_weather_refreshes_at_model_interval_end(
    hass, live_entry, aioclient_mock, freezer
):
    entry, weather_id = live_entry
    assert (
        entry.runtime_data.station_condition_coordinator.update_interval
        == timedelta(minutes=1)
    )
    assert hass.states.get(weather_id).state == "cloudy"
    aioclient_mock.clear_requests()
    end = HOUR + timedelta(hours=1)
    aioclient_mock.get(
        STATION_CONDITION_URL, json=payload(time=end.timestamp(), weather_code=61)
    )
    freezer.move_to(end + timedelta(seconds=1))
    async_fire_time_changed(hass, end + timedelta(seconds=1))
    await hass.async_block_till_done()
    assert hass.states.get(weather_id).state == "rainy"
    assert hass.states.get(weather_id).attributes["temperature"] == 7.8
    assert len(aioclient_mock.mock_calls) == 1

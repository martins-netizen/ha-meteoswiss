"""Reproduce partial KLO publication rows without hiding real data loss."""

from __future__ import annotations

import csv
from threading import get_ident
from unittest.mock import patch

import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.cache import clear_all_caches
from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.coordinator import MeteoSwissDataUpdateCoordinator
from custom_components.meteoswiss.sensor import SENSOR_DESCRIPTIONS, MeteoSwissSensor

CSV_URL = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/klo/ogd-smn_klo_t_now.csv"
HEADER = "station_abbr;reference_timestamp;tre200s0;ure200s0;fu3010z1;rre150z0;htoauts0;wcc006s0\n"


@pytest.fixture(autouse=True)
def clean_cache():
    clear_all_caches()
    yield
    clear_all_caches()


def coordinator(hass):
    return MeteoSwissDataUpdateCoordinator(
        hass, "KLO", 600, async_get_clientsession(hass)
    )


async def download(hass, aioclient_mock, content):
    aioclient_mock.get(CSV_URL, text=content)
    return await coordinator(hass)._async_download_and_parse_csv(CSV_URL)


async def test_station_csv_decoding_does_not_block_the_ha_event_loop(
    hass, aioclient_mock
):
    loop_thread = get_ident()
    parser_threads = []
    reader = csv.DictReader

    def observe_parse(*args, **kwargs):
        parser_threads.append(get_ident())
        return reader(*args, **kwargs)

    with patch(
        "custom_components.meteoswiss.coordinator.csv.DictReader",
        side_effect=observe_parse,
    ):
        data = await download(
            hass, aioclient_mock,
            HEADER + "KLO;15.10.2026 17:40;12;92;6;0;0;\n",
        )
    assert data["temperature"] == 12
    assert parser_threads and loop_thread not in parser_threads


@pytest.mark.parametrize(
    "partial", ["KLO;15.10.2026 17:40;;;;;;", "KLO;15.10.2026 17:40;;;;0;;"]
)
async def test_trailing_empty_or_rain_only_row_keeps_real_observation_time(
    hass, aioclient_mock, partial
):
    # Real failure pattern: rain is already zero while T/RH/gust are blank.
    data = await download(
        hass,
        aioclient_mock,
        HEADER + "KLO;15.10.2026 17:30;13.4;89.7;5;0;0;\n" + partial,
    )
    assert data["temperature"] == 13.4
    assert data["humidity"] == 89.7
    assert data["wind_gust"] == 5
    assert data["last_update"] == "2026-10-15T17:30:00+00:00"
    assert data["source_status"] == "partial_update"
    assert data["pending_rows"] == 1
    current = coordinator(hass)
    current.data = data
    description = next(d for d in SENSOR_DESCRIPTIONS if d.key == "wind_gust")
    entity = MeteoSwissSensor(
        current, MockConfigEntry(domain=DOMAIN), description, "Kloten"
    )
    assert entity.native_value == 5
    assert entity.extra_state_attributes["measurement_time"] == data["last_update"]
    assert entity.extra_state_attributes["source_status"] == "partial_update"


async def test_partial_update_does_not_fill_individual_missing_gust(
    hass, aioclient_mock
):
    data = await download(
        hass,
        aioclient_mock,
        HEADER
        + "KLO;15.10.2026 17:30;13;90;5;0;0;\nKLO;15.10.2026 17:40;12;92;;0;0;\n",
    )
    assert data["temperature"] == 12
    assert data["wind_gust"] is None
    assert data["last_update"] == "2026-10-15T17:40:00+00:00"
    assert data["source_status"] == "current"
    assert data["pending_rows"] == 0


async def test_zero_is_a_real_observation_and_rain_only_stations_work(
    hass, aioclient_mock
):
    data = await download(
        hass,
        aioclient_mock,
        HEADER + "KLO;15.10.2026 17:30;;;;1;;\nKLO;15.10.2026 17:40;;;;0;;\n",
    )
    assert data["precipitation"] == 0
    assert data["temperature"] is None
    assert data["last_update"] == "2026-10-15T17:40:00+00:00"
    assert data["pending_rows"] == 0


async def test_all_empty_source_is_a_failed_update(hass, aioclient_mock):
    with pytest.raises(UpdateFailed, match="no measured observations"):
        await download(hass, aioclient_mock, HEADER + "KLO;15.10.2026 17:40;;;;;;\n")


async def test_old_observation_behind_fresh_placeholder_still_fails_freshness_check(
    hass, aioclient_mock, freezer
):
    freezer.move_to("2026-10-15T18:40:00+00:00")
    aioclient_mock.get(
        CSV_URL,
        text=HEADER
        + "KLO;15.10.2026 17:30;13;90;5;0;0;\nKLO;15.10.2026 18:40;;;;0;;\n",
    )
    current = coordinator(hass)
    with patch.object(current, "_async_get_station_data_url", return_value=CSV_URL):
        await current.async_refresh()
    assert not current.last_update_success
    assert current.data is None


async def test_live_refresh_recovers_when_partial_row_is_completed(
    hass, aioclient_mock, freezer
):
    freezer.move_to("2026-10-15T17:50:00+00:00")
    current = coordinator(hass)
    aioclient_mock.get(
        CSV_URL,
        text=HEADER
        + "KLO;15.10.2026 17:30;13;90;5;0;0;\nKLO;15.10.2026 17:40;;;;0;;\n",
    )
    with patch.object(current, "_async_get_station_data_url", return_value=CSV_URL):
        await current.async_refresh()
        assert current.last_update_success
        assert current.data["source_status"] == "partial_update"
        clear_all_caches()
        aioclient_mock.clear_requests()
        aioclient_mock.get(CSV_URL, text=HEADER + "KLO;15.10.2026 17:40;12;92;6;0;0;\n")
        await current.async_refresh()
    assert current.last_update_success
    assert current.data["source_status"] == "current"
    assert current.data["wind_gust"] == 6
    assert current.data["last_update"] == "2026-10-15T17:40:00+00:00"


async def test_whole_station_outage_becomes_unavailable_and_recovers(
    hass, aioclient_mock, freezer
):
    freezer.move_to("2026-10-15T17:50:00+00:00")
    current = coordinator(hass)
    aioclient_mock.get(CSV_URL, text=HEADER + "KLO;15.10.2026 17:40;12;92;6;0;0;\n")
    entity = MeteoSwissSensor(
        current,
        MockConfigEntry(domain=DOMAIN),
        next(d for d in SENSOR_DESCRIPTIONS if d.key == "wind_gust"),
        "Kloten",
    )
    with patch.object(current, "_async_get_station_data_url", return_value=CSV_URL):
        await current.async_refresh()
        assert entity.available
        previous = current.data
        clear_all_caches()
        freezer.move_to("2026-10-15T18:50:00+00:00")
        aioclient_mock.clear_requests()
        aioclient_mock.get(CSV_URL, text=HEADER + "KLO;15.10.2026 18:40;;;;;;\n")
        await current.async_refresh()
        assert not entity.available
        assert current.data == previous
        aioclient_mock.clear_requests()
        aioclient_mock.get(CSV_URL, text=HEADER + "KLO;15.10.2026 18:50;14;91;7;0;0;\n")
        await current.async_refresh()
        assert entity.available
        assert current.data["wind_gust"] == 7

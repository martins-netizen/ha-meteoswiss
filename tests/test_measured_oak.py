"""Use the documented seventh hourly pollen column without changing old IDs."""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import patch

import pytest
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.coordinator import MeteoSwissPollenCoordinator

# Actual column names/order from the public PZH _h_now.csv on 17 October 2026.
HEADER = "station_abbr;reference_timestamp;kabetuh0;khpoach0;kaalnuh0;kacoryh0;kafaguh0;kafraxh0;kaquerh0\n"
STAMP = "17.10.2026 10:00"
URL = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-pollen/pzh/ogd-pollen_pzh_h_now.csv"


@pytest.fixture(autouse=True)
def fixed_clock(freezer):
    freezer.move_to("2026-10-17T10:20:00+00:00")


@pytest.mark.parametrize("oak", ["0", "17"])
def test_oak_only_is_a_valid_measured_source(hass, oak):
    coordinator = MeteoSwissPollenCoordinator(hass, "PZH")
    data = coordinator.client.parse_csv(HEADER + f"PZH;{STAMP};;;;;;;{oak}\n")
    assert data["oak"]["current"] == int(oak)
    assert data["oak"]["history_24h"] == [int(oak)]
    assert data["oak"]["unit"] == "No/m³"
    assert data["birch"]["current"] is None


@pytest.mark.parametrize("oak", ["", "bad", "-1", "nan"])
def test_missing_or_invalid_oak_is_not_zero(hass, oak):
    coordinator = MeteoSwissPollenCoordinator(hass, "PZH")
    data = coordinator.client.parse_csv(HEADER + f"PZH;{STAMP};0;0;0;0;0;0;{oak}\n")
    assert data["oak"]["current"] is None
    assert data["birch"]["current"] == 0


async def test_registered_oak_missing_outage_recovery_and_reload_keep_identity(
    hass, aioclient_mock, enable_custom_integrations
):
    entry = MockConfigEntry(domain=DOMAIN, data={
        "data_source": "meteoswiss", "station_id": "KLO",
        "station_name": "Kloten", "postal_code": "8302",
    }, options={"pollen_station": "PZH"})
    entry.add_to_hass(hass)
    aioclient_mock.get(URL, text=HEADER + f"PZH;{STAMP};1;2;3;4;5;6;17\n")
    with ExitStack() as stack:
        stack.enter_context(patch(
            "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations",
            return_value={},
        ))
        for target, data in {
            "coordinator.MeteoSwissDataUpdateCoordinator": {"temperature": 12},
            "coordinator.MeteoSwissForecastCoordinator": [],
            "coordinator.MeteoSwissAlertsCoordinator": [],
            "coordinator.OpenMeteoPollenCoordinator": {},
        }.items():
            stack.enter_context(patch(
                f"custom_components.meteoswiss.{target}._async_update_data",
                return_value=data,
            ))
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        registry = er.async_get(hass)
        ids = {kind: registry.async_get_entity_id(
            "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_ms_pollen_{kind}"
        ) for kind in ("birch", "grass", "alder", "hazel", "beech", "ash", "oak")}
        assert all(ids.values())
        before = {kind: registry.async_get(entity_id).unique_id
                  for kind, entity_id in ids.items()}
        assert hass.states.get(ids["oak"]).state == "17"
        # Source order must not change the six established mappings.
        assert [hass.states.get(ids[k]).state for k in ids if k != "oak"] == [
            "1", "2", "3", "4", "5", "6"]
        for language, expected in {
            "de": "Eichenpollen (gemessen)", "en": "Oak Pollen (Measured)",
            "fr": "Pollen de chêne (mesuré)", "it": "Polline di quercia (misurato)",
        }.items():
            strings = await async_get_translations(hass, language, "entity", {DOMAIN})
            assert strings["component.meteoswiss.entity.sensor.ms_pollen_oak.name"] == expected
        for oak, expected in [("0", "0"), ("", "unknown")]:
            aioclient_mock.clear_requests()
            aioclient_mock.get(URL, text=HEADER + f"PZH;{STAMP};1;2;3;4;5;6;{oak}\n")
            await entry.runtime_data.meteoswiss_pollen_coordinator.async_refresh()
            assert hass.states.get(ids["oak"]).state == expected
            assert hass.states.get(ids["birch"]).state == "1"
        aioclient_mock.clear_requests()
        aioclient_mock.get(URL, text=HEADER)
        await entry.runtime_data.meteoswiss_pollen_coordinator.async_refresh()
        assert hass.states.get(ids["oak"]).state == "unavailable"
        aioclient_mock.clear_requests()
        aioclient_mock.get(URL, text=HEADER + f"PZH;{STAMP};1;2;3;4;5;6;21\n")
        await entry.runtime_data.meteoswiss_pollen_coordinator.async_refresh()
        assert hass.states.get(ids["oak"]).state == "21"
        assert await hass.config_entries.async_reload(entry.entry_id)
        await hass.async_block_till_done()
        for kind, entity_id in ids.items():
            assert registry.async_get_entity_id("sensor", DOMAIN, before[kind]) == entity_id
        assert hass.states.get(ids["oak"]).state == "21"
        assert await hass.config_entries.async_unload(entry.entry_id)

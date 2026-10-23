"""Real entity/Recorder contracts for measured intervals and retired sums."""

from contextlib import ExitStack
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from homeassistant.components.recorder.statistics import statistics_during_period
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.translation import async_get_translations
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.components.recorder.common import (
    async_recorder_block_till_done,
)

from custom_components.meteoswiss.const import DOMAIN
from custom_components.meteoswiss.coordinator import MeteoSwissDataUpdateCoordinator
from custom_components.meteoswiss.precipitation import (
    MeteoSwissHourlyPrecipitationCoordinator,
)
from custom_components.meteoswiss.sensor import (
    _remove_legacy_current_hour_precipitation_entity,
)

NOW = datetime(2026, 10, 18, 10, 35, tzinfo=UTC)
BASE = "https://data.geo.admin.ch/ch.meteoschweiz.ogd-smn/klo/ogd-smn_klo_"


@pytest.fixture(autouse=True)
def fixed_clock(freezer):
    freezer.move_to(NOW)


@pytest.mark.parametrize("source,interval,label", [
    ("meteoswiss", 600, "precipitation"),
    ("openmeteo", 900, "precipitation_modelled"),
])
async def test_retirement_and_source_labels_preserve_surviving_entities_on_reload(
    hass, enable_custom_integrations, source, interval, label
):
    entry = MockConfigEntry(domain=DOMAIN, data={
        "data_source": source, "station_id": "KLO", "station_name": "Kloten",
        "postal_code": "8302", "latitude": 47.45, "longitude": 8.56,
    })
    entry.add_to_hass(hass)
    other = MockConfigEntry(domain=DOMAIN)
    other.add_to_hass(hass)
    utility = MockConfigEntry(domain="utility_meter")
    utility.add_to_hass(hass)
    registry = er.async_get(hass)
    retired = registry.async_get_or_create(
        "sensor", DOMAIN, f"{DOMAIN}_{entry.entry_id}_precipitation_current_hour", config_entry=entry
    )
    untouched = registry.async_get_or_create(
        "sensor", DOMAIN, f"{DOMAIN}_{other.entry_id}_precipitation_current_hour", config_entry=other
    )
    helper = registry.async_get_or_create("sensor", "utility_meter", "existing-helper", config_entry=utility)
    unique_id = f"{DOMAIN}_{entry.entry_id}_precipitation"
    previous = registry.async_get_or_create(
        "sensor", DOMAIN, unique_id, config_entry=entry, suggested_object_id="my_existing_rain",
        original_name="Previous precipitation name",
    )
    registry.async_update_entity(previous.entity_id, name="My rain")
    registry.async_update_entity_options(previous.entity_id, "sensor", {"display_precision": 1})
    with ExitStack() as stack:
        stack.enter_context(patch(
            "custom_components.meteoswiss.stations_map.MeteoSwissStationsMap.load_stations", return_value={}
        ))
        for target, data in {
            "coordinator.MeteoSwissDataUpdateCoordinator": {"temperature": 10, "precipitation": 0.3,
                "last_update": "2026-10-18T10:20:00+00:00", "precipitation_interval_seconds": interval},
            "coordinator.OpenMeteoDataUpdateCoordinator": {"temperature": 10, "precipitation": 0.3,
                "last_update": "2026-10-18T10:20:00+00:00", "precipitation_interval_seconds": interval},
            "coordinator.MeteoSwissForecastCoordinator": [],
            "coordinator.MeteoSwissAlertsCoordinator": [],
            "coordinator.OpenMeteoPollenCoordinator": {},
            "coordinator.MeteoSwissPollenCoordinator": {},
        }.items():
            stack.enter_context(patch(f"custom_components.meteoswiss.{target}._async_update_data", return_value=data))
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        for _ in range(2):
            current = registry.async_get(previous.entity_id)
            assert current.unique_id == unique_id and current.name == "My rain"
            assert current.translation_key == label
            assert current.options["sensor"]["display_precision"] == 1
            state = hass.states.get(previous.entity_id)
            assert state.state == "0.3"
            assert state.attributes["measurement_interval_seconds"] == interval
            assert state.attributes["measurement_time"] == "2026-10-18T10:20:00+00:00"
            assert registry.async_get(retired.entity_id) is None
            assert hass.states.get(retired.entity_id) is None
            assert registry.async_get(untouched.entity_id) is not None
            assert registry.async_get(helper.entity_id) is not None
            assert await hass.config_entries.async_reload(entry.entry_id)
            await hass.async_block_till_done()
        assert await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()


@pytest.mark.parametrize("language", ["de", "en", "fr", "it"])
async def test_precipitation_names_distinguish_measured_ten_minutes_and_model_interval(
    hass, enable_custom_integrations, language
):
    strings = await async_get_translations(hass, language, "entity", {DOMAIN})
    prefix = "component.meteoswiss.entity.sensor."
    assert "10" in strings[prefix + "precipitation.name"]
    assert "10" not in strings[prefix + "precipitation_modelled.name"]
    assert prefix + "precipitation_current_hour.name" not in strings


@pytest.mark.parametrize("amount,expected", [("0", 0), ("0.1", 0.1), ("", None)])
async def test_station_rain_is_the_latest_interval_not_an_unmarked_hourly_sum(
    hass, aioclient_mock, amount, expected
):
    url = BASE + "t_now.csv"
    aioclient_mock.get(url, text=(
        "station_abbr;reference_timestamp;tre200s0;rre150z0\n"
        "KLO;18.10.2026 10:10;10;0.3\n"
        "KLO;18.10.2026 10:20;10;\n"
        f"KLO;18.10.2026 10:30;10;{amount}\n"
    ))
    coordinator = MeteoSwissDataUpdateCoordinator(hass, "KLO", 600, async_get_clientsession(hass))
    data = await coordinator._async_download_and_parse_csv(url)
    assert data["precipitation"] == expected
    assert data["precipitation_interval_seconds"] == 600
    assert data["last_update"] == "2026-10-18T10:30:00+00:00"
    assert "precipitation_current_hour" not in data


async def test_retirement_leaves_official_archive_values_in_real_recorder(
    recorder_mock, hass, aioclient_mock
):
    url = BASE + "h_now.csv"
    metadata = "https://data.geo.admin.ch/api/stac/v1/collections/ch.meteoschweiz.ogd-smn/items/klo"
    aioclient_mock.get(metadata, json={"assets": {"ogd-smn_klo_h_now.csv": {"href": url}}})
    aioclient_mock.get(url, text="station_abbr;reference_timestamp;rre150h0\nKLO;18.10.2026 10:00;0.9\n")
    source = MeteoSwissHourlyPrecipitationCoordinator(hass, "KLO", async_get_clientsession(hass))
    await source._async_update_data()
    await async_recorder_block_till_done(hass)
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    registry.async_get_or_create("sensor", DOMAIN,
        f"{DOMAIN}_{entry.entry_id}_precipitation_current_hour", config_entry=entry)
    _remove_legacy_current_hour_precipitation_entity(hass, entry)
    _remove_legacy_current_hour_precipitation_entity(hass, entry)
    await async_recorder_block_till_done(hass)
    values = await hass.async_add_executor_job(statistics_during_period, hass,
        datetime(2026, 10, 18, 9, tzinfo=UTC), None, {source.statistic_id}, "hour", None, {"mean"})
    assert source.statistic_id == "meteoswiss:klo_precipitation_hourly"
    assert len(values[source.statistic_id]) == 1
    assert values[source.statistic_id][0]["mean"] == 0.9

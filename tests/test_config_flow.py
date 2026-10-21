from __future__ import annotations

from types import SimpleNamespace

# These tests exercise HA's flow manager, including retrying failed forms.
from unittest.mock import patch

import pytest
import voluptuous as vol
from homeassistant.config_entries import SOURCE_USER
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.meteoswiss.config_flow import (
    MeteoSwissConfigFlow,
    _has_matching_meteoswiss_entry,
    _has_matching_openmeteo_entry,
    _parse_stations,
)
from custom_components.meteoswiss.const import (
    CONF_DATA_SOURCE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_POLLEN_STATION,
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    CONF_UPDATE_INTERVAL,
    DATA_SOURCE_METEOSWISS,
    DATA_SOURCE_OPENMETEO,
    DEFAULT_POLLEN_STATION,
    DOMAIN,
    POLLEN_STATIONS,
    STATIONS_METADATA_URL,
)


def _entry(station_id: str, postal_code: str):
    return SimpleNamespace(
        data={
            CONF_DATA_SOURCE: DATA_SOURCE_METEOSWISS,
            CONF_STATION_ID: station_id,
            CONF_POSTAL_CODE: postal_code,
        }
    )


def test_duplicate_match_is_case_and_whitespace_tolerant() -> None:
    entries = [_entry("klo", "8302")]
    assert _has_matching_meteoswiss_entry(entries, " KLO ", " 8302 ")


def test_different_station_or_postcode_is_not_duplicate() -> None:
    entries = [_entry("klo", "8302")]
    assert not _has_matching_meteoswiss_entry(entries, "sma", "8302")
    assert not _has_matching_meteoswiss_entry(entries, "klo", "8000")


async def test_meteoswiss_flow_aborts_existing_entry(monkeypatch) -> None:
    flow = MeteoSwissConfigFlow()

    monkeypatch.setattr(
        flow,
        "_async_current_entries",
        lambda: [_entry("klo", "8302")],
    )

    result = await flow.async_step_meteoswiss(
        {
            CONF_STATION_ID: "KLO",
            CONF_POSTAL_CODE: "8302",
        }
    )

    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"


STATIONS = [
    {
        "id": "klo",
        "name": "Zürich / Kloten",
        "label": "Zürich / Kloten (KLO)",
        "lat": 47.48,
        "lon": 8.53,
    }
]
MS_INPUT = {CONF_STATION_ID: "klo", CONF_POSTAL_CODE: "8302"}
OM_INPUT = {CONF_LATITUDE: 47.05, CONF_LONGITUDE: 8.31, CONF_POSTAL_CODE: "8302"}


@pytest.fixture(autouse=True)
def mock_entry_setup():
    with patch("custom_components.meteoswiss.async_setup_entry", return_value=True):
        yield


async def start_flow(hass, source, pollen_station="PZH"):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["step_id"] == "user"
    return await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_DATA_SOURCE: source, CONF_POLLEN_STATION: pollen_station},
    )


async def test_initial_form_requires_an_explicit_measured_pollen_station(
    hass, enable_custom_integrations
):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    schema = result["data_schema"]
    with pytest.raises(vol.Invalid):
        schema({CONF_DATA_SOURCE: DATA_SOURCE_METEOSWISS})
    with pytest.raises(vol.Invalid):
        schema({CONF_DATA_SOURCE: DATA_SOURCE_METEOSWISS, CONF_POLLEN_STATION: "KLO"})
    for station in POLLEN_STATIONS:
        assert schema({CONF_POLLEN_STATION: station})[CONF_POLLEN_STATION] == station


@pytest.mark.parametrize("station", [None, "", "KLO", "missing", []])
async def test_invalid_pollen_station_can_be_corrected_before_network_access(
    hass, enable_custom_integrations, station
):
    flow = MeteoSwissConfigFlow()
    flow.hass = hass
    user_input = {CONF_DATA_SOURCE: DATA_SOURCE_METEOSWISS}
    if station is not None:
        user_input[CONF_POLLEN_STATION] = station
    with patch.object(
        flow, "_load_stations", return_value=STATIONS
    ) as load_stations:
        result = await flow.async_step_user(user_input)
        assert result["step_id"] == "user"
        assert result["errors"] == {CONF_POLLEN_STATION: "invalid_pollen_station"}
        assert not hass.config_entries.async_entries(DOMAIN)
        load_stations.assert_not_called()
        result = await flow.async_step_user(
            {CONF_DATA_SOURCE: DATA_SOURCE_METEOSWISS, CONF_POLLEN_STATION: "PBE"},
        )
        assert result["step_id"] == "meteoswiss"
        load_stations.assert_called_once()


@pytest.mark.parametrize("pollen_station", ["PBE", "PZH"])
@pytest.mark.parametrize(
    "source,inputs,unique_id",
    [
        (DATA_SOURCE_METEOSWISS, MS_INPUT, "meteoswiss:klo:8302"),
        (DATA_SOURCE_OPENMETEO, OM_INPUT, "openmeteo:47.05:8.31:8302"),
    ],
)
async def test_user_flow_success_and_connection_recovery(
    hass, enable_custom_integrations, source, inputs, unique_id, pollen_station
):
    with (
        patch.object(MeteoSwissConfigFlow, "_load_stations", return_value=STATIONS),
        patch.object(
            MeteoSwissConfigFlow, "_validate_source", side_effect=[False, True]
        ),
    ):
        result = await start_flow(hass, source, pollen_station)
        assert result["step_id"] == source
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], inputs
        )
        assert result["errors"] == {"base": "cannot_connect"}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], inputs
        )
    assert result["type"] == "create_entry"
    assert result["result"].unique_id == unique_id
    assert result["data"][CONF_DATA_SOURCE] == source
    assert result["data"][CONF_UPDATE_INTERVAL] == 600
    assert result["data"][CONF_POSTAL_CODE] == "8302"
    assert result["result"].options[CONF_POLLEN_STATION] == pollen_station
    await hass.async_block_till_done()


async def test_catalogue_failure_is_retryable(hass, enable_custom_integrations):
    with (
        patch.object(
            MeteoSwissConfigFlow, "_load_stations", side_effect=[[], STATIONS]
        ),
        patch.object(MeteoSwissConfigFlow, "_validate_source", return_value=True),
    ):
        result = await start_flow(hass, DATA_SOURCE_METEOSWISS)
        assert result["errors"] == {"base": "cannot_connect"}
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], MS_INPUT
        )
        assert result["type"] == "create_entry"
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    "source,inputs",
    [(DATA_SOURCE_METEOSWISS, MS_INPUT), (DATA_SOURCE_OPENMETEO, OM_INPUT)],
)
@pytest.mark.parametrize(
    "postcode", ["", "   ", "830", "830200", "8x02", "１２３４", "0000", "8302&x=1"]
)
async def test_invalid_warning_postcode_is_correctable_before_observation_check(
    hass, enable_custom_integrations, source, inputs, postcode
):
    """A working weather provider must not accept a mistyped warning postcode."""
    with (
        patch.object(MeteoSwissConfigFlow, "_load_stations", return_value=STATIONS),
        patch.object(
            MeteoSwissConfigFlow, "_validate_source", return_value=True
        ) as validate_source,
    ):
        result = await start_flow(hass, source)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**inputs, CONF_POSTAL_CODE: postcode}
        )
        assert result["type"] == "form"
        assert result["errors"] == {CONF_POSTAL_CODE: "invalid_postal_code"}
        validate_source.assert_not_called()
        assert not hass.config_entries.async_entries(DOMAIN)

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**inputs, CONF_POSTAL_CODE: " 8302 "}
        )
        assert result["type"] == "create_entry"
        assert result["data"][CONF_POSTAL_CODE] == "8302"
        validate_source.assert_called_once()
    await hass.async_block_till_done()


async def test_unknown_station_then_valid_station(hass, enable_custom_integrations):
    flow = MeteoSwissConfigFlow()
    flow.hass = hass
    flow.context = {"source": SOURCE_USER}
    with (
        patch.object(flow, "_load_stations", return_value=STATIONS),
        patch.object(flow, "_validate_source", return_value=True),
    ):
        result = await flow.async_step_meteoswiss(
            {**MS_INPUT, CONF_STATION_ID: "missing"}
        )
        assert result["errors"] == {"base": "station_not_found"}
        result = await flow.async_step_meteoswiss(MS_INPUT)
    assert result["type"] == "create_entry"


@pytest.mark.parametrize(
    "coordinates",
    [
        (91, 8),
        (-91, 8),
        (47, 181),
        (47, -181),
        (float("nan"), 8),
        (47, float("inf")),
    ],
)
async def test_invalid_location_can_be_corrected(
    hass, enable_custom_integrations, coordinates
):
    result = await start_flow(hass, DATA_SOURCE_OPENMETEO)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {**OM_INPUT, CONF_LATITUDE: coordinates[0], CONF_LONGITUDE: coordinates[1]},
    )
    assert result["errors"] == {"base": "invalid_location"}
    with patch.object(MeteoSwissConfigFlow, "_validate_source", return_value=True):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], OM_INPUT
        )
    assert result["type"] == "create_entry"
    await hass.async_block_till_done()


@pytest.mark.parametrize(
    "source,inputs,unique_id",
    [
        (DATA_SOURCE_METEOSWISS, MS_INPUT, "meteoswiss:klo:8302"),
        (DATA_SOURCE_OPENMETEO, OM_INPUT, "openmeteo:47.05:8.31:8302"),
    ],
)
@pytest.mark.parametrize("legacy", [False, True])
async def test_duplicate_flow_aborts_before_network(
    hass, enable_custom_integrations, source, inputs, unique_id, legacy
):
    # A unique-id match must also abort when legacy data differs.
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_DATA_SOURCE: source, **inputs} if legacy else {},
        unique_id=None if legacy else unique_id,
    )
    entry.add_to_hass(hass)
    with (
        patch.object(MeteoSwissConfigFlow, "_load_stations", return_value=STATIONS),
        patch.object(MeteoSwissConfigFlow, "_validate_source") as validate,
    ):
        result = await start_flow(hass, source)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], inputs
        )
    assert result["type"] == "abort"
    assert result["reason"] == "already_configured"
    validate.assert_not_called()


def test_legacy_matching_handles_other_sources_and_locations():
    entries = [
        SimpleNamespace(data={CONF_DATA_SOURCE: DATA_SOURCE_OPENMETEO, **OM_INPUT})
    ]
    assert not _has_matching_meteoswiss_entry(entries, "klo", "8302")
    assert not _has_matching_openmeteo_entry(
        [_entry("klo", "8302")], 47.05, 8.31, "8302"
    )
    assert not _has_matching_openmeteo_entry(entries, 46, 8.31, "8302")
    assert not _has_matching_openmeteo_entry(entries, 47.05, 7, "8302")
    assert not _has_matching_openmeteo_entry(entries, 47.05, 8.31, "8000")
    assert not _has_matching_openmeteo_entry([], 47.05, 8.31, "8302")


@pytest.mark.parametrize("source", [DATA_SOURCE_METEOSWISS, DATA_SOURCE_OPENMETEO])
@pytest.mark.parametrize("error", [None, ValueError("stale"), TimeoutError()])
async def test_validation_uses_real_coordinator_contract(hass, source, error):
    flow = MeteoSwissConfigFlow()
    flow.hass = hass
    target = (
        "MeteoSwissDataUpdateCoordinator"
        if source == DATA_SOURCE_METEOSWISS
        else "OpenMeteoDataUpdateCoordinator"
    )
    method = (
        "custom_components.meteoswiss.config_flow." + target + "._async_update_data"
    )
    payload = {"temperature": 12, "last_update": "2026-10-15T16:00:00+00:00"}
    with patch(method, side_effect=error, return_value=payload):
        kwargs = (
            {"station_id": "klo"}
            if source == DATA_SOURCE_METEOSWISS
            else {"latitude": 47, "longitude": 8}
        )
        assert await flow._validate_source(**kwargs) is (error is None)


async def test_validation_total_timeout_and_cancellation(hass):
    flow = MeteoSwissConfigFlow()
    flow.hass = hass
    with patch(
        "custom_components.meteoswiss.config_flow.MeteoSwissDataUpdateCoordinator.async_refresh",
        side_effect=TimeoutError,
    ):
        assert not await flow._validate_source(station_id="klo")
    import asyncio

    with patch(
        "custom_components.meteoswiss.config_flow.MeteoSwissDataUpdateCoordinator.async_refresh",
        side_effect=asyncio.CancelledError,
    ):
        with pytest.raises(asyncio.CancelledError):
            await flow._validate_source(station_id="klo")


def test_catalogue_encoding_rows_and_sorting():
    header = "station;name;canton;" + ";" * 11 + "lat;lon\n"
    rows = [
        ["klo", "Zürich / Kloten", "ZH"] + [""] * 11 + ["47.48", "8.53"],
        ["ber", "Bern", "BE"],
        ["empty", "", "ZH"],
        ["", "No ID", "ZH"],
        ["short"],
        ["bad", "Bad", "ZH"] + [""] * 11 + ["bad", "8"],
        ["none", "None", "ZH"] + [""] * 13,
    ]
    parsed = _parse_stations(
        (header + "\n".join(";".join(row) for row in rows)).encode("cp1252")
    )
    assert [s["id"] for s in parsed] == ["ber", "none", "klo"]
    assert parsed[-1]["lat"] == 47.48
    assert parsed[-1]["name"] == "Zürich / Kloten"
    assert parsed[0]["lon"] is None
    assert _parse_stations(b"") == []


@pytest.mark.parametrize("failure", [None, 503, "timeout", "invalid_encoding"])
async def test_catalogue_http_and_decoding(hass, aioclient_mock, failure):
    flow = MeteoSwissConfigFlow()
    flow.hass = hass
    if failure == "timeout":
        aioclient_mock.get(STATIONS_METADATA_URL, exc=TimeoutError)
    else:
        aioclient_mock.get(
            STATIONS_METADATA_URL,
            status=failure if isinstance(failure, int) else 200,
            content=b"\x81"
            if failure == "invalid_encoding"
            else b"station;name;canton\nklo;Kloten;ZH",
        )
    result = await flow._load_stations()
    assert bool(result) is (failure is None)


@pytest.mark.parametrize("pollen_station", [None, "PBE"])
async def test_options_flow_preserves_entry_identity(
    hass, enable_custom_integrations, pollen_station
):
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_UPDATE_INTERVAL: 900},
        options={
            CONF_UPDATE_INTERVAL: 1200,
            **({CONF_POLLEN_STATION: pollen_station} if pollen_station else {}),
        },
        unique_id="meteoswiss:klo:8302",
    )
    entry.add_to_hass(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == "form"
    assert result["data_schema"]({})[CONF_UPDATE_INTERVAL] == 1200
    assert result["data_schema"]({})[CONF_POLLEN_STATION] == (
        pollen_station or DEFAULT_POLLEN_STATION
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {CONF_UPDATE_INTERVAL: 1800, CONF_POLLEN_STATION: "PZH"}
    )
    assert result["type"] == "create_entry"
    assert entry.options[CONF_UPDATE_INTERVAL] == 1800
    assert entry.data[CONF_UPDATE_INTERVAL] == 900
    assert entry.options[CONF_POLLEN_STATION] == "PZH"
    assert hass.config_entries.async_get_entry(entry.entry_id) is entry
    assert entry.unique_id == "meteoswiss:klo:8302"

from __future__ import annotations

from types import SimpleNamespace

from custom_components.meteoswiss.config_flow import (
    MeteoSwissConfigFlow,
    _has_matching_meteoswiss_entry,
)
from custom_components.meteoswiss.const import (
    CONF_DATA_SOURCE,
    CONF_POSTAL_CODE,
    CONF_STATION_ID,
    DATA_SOURCE_METEOSWISS,
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
    flow._data_source = DATA_SOURCE_METEOSWISS

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

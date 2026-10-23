"""Offline selected-point persistence, invalid-selection safety and local metadata."""

import json
import traceback
from dataclasses import replace
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from custom_components.meteoswiss.const import CONF_FORECAST_LOCATION
from custom_components.meteoswiss.forecast_location_config import (
    InvalidForecastLocation,
    decode_forecast_location,
    encode_forecast_location,
    resolve_forecast_target,
)
from custom_components.meteoswiss.forecast_locations import (
    ForecastPointType,
    parse_forecast_catalogue,
)


@pytest.fixture
def location():
    raw = (
        Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv"
    ).read_text()
    catalogue = parse_forecast_catalogue(
        raw.encode("latin-1"), datetime(2026, 10, 23, tzinfo=UTC)
    )
    return catalogue.select(ForecastPointType.POINT_OF_INTEREST, "711")


@pytest.mark.parametrize(
    "point_type,station,postcode",
    [
        (ForecastPointType.STATION, "KLO", None),
        (ForecastPointType.POSTAL_CODE, None, "8302"),
        (ForecastPointType.POINT_OF_INTEREST, None, None),
    ],
)
@pytest.mark.parametrize("height", [2502, None, 0, -5.2])
def test_json_roundtrip_is_detached_and_preserves_roles_and_original_provenance(
    location, point_type, station, postcode, height
):
    location = replace(
        location,
        point=replace(
            location.point,
            point_type=point_type,
            point_id="00711",
            station_abbr=station,
            postal_code=postcode,
            altitude_masl=height,
        ),
    )
    saved = encode_forecast_location(location)
    assert decode_forecast_location(json.loads(json.dumps(saved))) == location
    assert saved["point_id"] == "00711"
    assert saved["schema_version"] == 1 and saved["crs"] == "EPSG:4326"
    saved["name"] = "Different point"
    assert location.point.name != "Different point"
    target = resolve_forecast_target(
        {CONF_FORECAST_LOCATION: encode_forecast_location(location)}, 0, 0
    )
    assert target.location == location
    assert (target.latitude, target.longitude) == (
        location.point.latitude,
        location.point.longitude,
    )
    assert target.elevation == height
    attrs = target.state_attributes()[CONF_FORECAST_LOCATION]
    assert attrs == {
        "status": "catalogue",
        "elevation_mode": "automatic_dem" if height is None else "catalogue",
        "name": location.point.name,
        "type": point_type.name.lower(),
        "altitude_masl": height,
    }
    assert "point_id" not in attrs and "catalogue_sha256" not in attrs


@pytest.mark.parametrize("raw", [None, [], {}, "private-point", 0, True])
def test_present_but_invalid_selection_never_uses_home_coordinates(raw):
    target = resolve_forecast_target({CONF_FORECAST_LOCATION: raw}, 47.45, 8.56)
    assert target.status == "invalid"
    assert (
        target.latitude is None and target.longitude is None and target.location is None
    )
    assert target.elevation_mode == "unavailable"
    assert target.state_attributes() == {
        CONF_FORECAST_LOCATION: {"status": "invalid", "elevation_mode": "unavailable"}
    }


@pytest.mark.parametrize("lat,lon", [(0, 0), (47.45, 8.56), (None, None)])
def test_absent_selection_preserves_legacy_coordinates_without_inference(lat, lon):
    target = resolve_forecast_target(
        {"postal_code": "8302", "station_id": "KLO"}, lat, lon
    )
    assert target.status == "legacy" and target.location is None
    assert (target.latitude, target.longitude, target.elevation) == (lat, lon, None)
    assert target.elevation_mode == "automatic_dem" and target.state_attributes() == {}


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema_version", True),
        ("schema_version", 2),
        ("schema_version", "1"),
        ("provider", "private-point"),
        ("source_url", "https://private-point.invalid"),
        ("crs", "EPSG:2056"),
        ("catalogue_sha256", "f" * 63),
        ("catalogue_sha256", "G" * 64),
        ("catalogue_sha256", "a" * 65),
        ("catalogue_retrieved_at", "private-point"),
        ("catalogue_retrieved_at", "2026-10-23T00:00:00"),
        ("point_type", "4"),
        ("point_type", 3),
        ("point_id", ""),
        ("point_id", " " + "private-point"),
        ("point_id", "x" * 65),
        ("name", "private-point\n"),
        ("name", "private-point\x85"),
        ("name", "x" * 257),
        ("station_abbr", "KLO"),
        ("postal_code", "8302"),
        ("latitude", True),
        ("latitude", "47.2"),
        ("latitude", None),
        ("latitude", float("nan")),
        ("latitude", float("inf")),
        ("latitude", 10**400),
        ("latitude", 91),
        ("longitude", -181),
        ("altitude_masl", "2502"),
        ("altitude_masl", float("-inf")),
    ],
)
def test_invalid_saved_fields_fail_privately_and_atomically(location, field, value):
    saved = encode_forecast_location(location)
    saved[field] = value
    with pytest.raises(InvalidForecastLocation) as error:
        decode_forecast_location(saved)
    assert str(error.value) == ""
    assert "private-point" not in "".join(traceback.format_exception(error.value))
    assert (
        resolve_forecast_target({CONF_FORECAST_LOCATION: saved}, 1, 2).status
        == "invalid"
    )


def test_role_requirements_schema_keys_and_aware_time_normalization(location):
    saved = encode_forecast_location(location)
    for changed in [
        dict(saved, point_type="1"),
        dict(saved, point_type="2"),
        dict(saved, point_type="2", postal_code="８３０２"),
        dict(saved, unexpected="private-point"),
        {k: v for k, v in saved.items() if k != "name"},
    ]:
        with pytest.raises(InvalidForecastLocation):
            decode_forecast_location(changed)
    offset = timezone(timedelta(hours=2))
    saved["catalogue_retrieved_at"] = location.catalogue_retrieved_at.astimezone(
        offset
    ).isoformat()
    assert (
        decode_forecast_location(saved).catalogue_retrieved_at
        == location.catalogue_retrieved_at
    )
    invalid = replace(location, point=replace(location.point, latitude=float("nan")))
    with pytest.raises(InvalidForecastLocation):
        encode_forecast_location(invalid)

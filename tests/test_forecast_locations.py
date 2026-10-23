"""Official point identities, whole-snapshot validation and explicit local search."""

import csv
import hashlib
import io
import traceback
from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest

from custom_components.meteoswiss.forecast_locations import (
    CATALOGUE_COLUMNS,
    FORECAST_CATALOGUE_URL,
    FORECAST_LOCATION_PROVIDER,
    ForecastPointType,
    InvalidForecastCatalogue,
    parse_forecast_catalogue,
    search_forecast_locations,
)

FIXTURE = Path(__file__).parent / "fixtures/forecast_points_2026-10-23.csv"
FETCHED = datetime(2026, 10, 23, 17, 26, 49, tzinfo=UTC)


@pytest.fixture
def rows():
    # Git fixture is UTF-8 for review; source bytes use documented Latin1.
    return list(csv.DictReader(io.StringIO(FIXTURE.read_text()), delimiter=";"))


def wire(rows, columns=CATALOGUE_COLUMNS):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=columns, delimiter=";", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue().encode("latin-1")


@pytest.fixture
def snapshot(rows):
    return parse_forecast_catalogue(wire(rows), FETCHED)


def test_public_fixture_preserves_roles_hash_and_immutable_selected_provenance(rows):
    content = wire(rows)
    snapshot = parse_forecast_catalogue(content, FETCHED)
    assert len(snapshot.points) == 7 and snapshot.duplicate_rows == 1
    assert snapshot.sha256 == hashlib.sha256(content).hexdigest()
    location = snapshot.select(ForecastPointType.POSTAL_CODE, "830200")
    assert location.point.identity == (ForecastPointType.POSTAL_CODE, "830200")
    assert location.point.postal_code == "8302"
    assert location.point.station_abbr is None
    assert (location.point.latitude, location.point.longitude) == (47.451253, 8.579761)
    assert location.point.altitude_masl == 436
    assert location.catalogue_retrieved_at == FETCHED
    assert location.catalogue_sha256 == snapshot.sha256
    assert location.source_url == FORECAST_CATALOGUE_URL
    assert location.provider == FORECAST_LOCATION_PROVIDER
    station = snapshot.select(ForecastPointType.STATION, "59").point
    assert station.station_abbr == "KLO" and station.postal_code is None
    assert station.altitude_masl == 426
    with pytest.raises(FrozenInstanceError):
        location.point.name = "changed"
    with pytest.raises(FrozenInstanceError):
        snapshot.points = ()


def test_composite_opaque_ids_and_missing_selection_never_pick_a_neighbour(rows):
    poi = dict(rows[-1], point_id="35")
    leading_zero = dict(poi, point_id="035")
    snapshot = parse_forecast_catalogue(wire([rows[0], poi, leading_zero]), FETCHED)
    assert len(snapshot.points) == 3
    assert snapshot.select(ForecastPointType.STATION, "35").point.altitude_masl == 2501
    assert (
        snapshot.select(ForecastPointType.POINT_OF_INTEREST, "35").point.altitude_masl
        == 2502
    )
    assert (
        snapshot.select(ForecastPointType.POINT_OF_INTEREST, "035").point.point_id
        == "035"
    )
    assert snapshot.select(ForecastPointType.POSTAL_CODE, "35") is None
    assert snapshot.select(ForecastPointType.POINT_OF_INTEREST, "missing") is None


@pytest.mark.parametrize("height,expected", [("", None), ("0", 0), ("-5.2", -5.2)])
def test_missing_height_stays_unknown_and_real_zero_or_negative_height_survives(
    rows, height, expected
):
    point = dict(rows[-1], point_height_masl=height)
    snapshot = parse_forecast_catalogue(wire([point]), FETCHED)
    assert snapshot.points[0].altitude_masl == expected


@pytest.mark.parametrize(
    "field,value",
    [
        ("point_id", ""),
        ("point_id", "x" * 65),
        ("point_name", " "),
        ("point_name", "x" * 257),
        ("point_name", "private_marker\x00"),
        ("point_type_en", "private_marker\x80"),
        ("point_type_fr", "private_marker\x7f"),
        ("point_name", "private_marker\n"),
        ("point_type_id", "0"),
        ("point_type_id", "4"),
        ("station_abbr", "UNEXPECTED"),
        ("postal_code", "8302"),
        ("point_coordinates_wgs84_lat", "90.01"),
        ("point_coordinates_wgs84_lat", "-90.01"),
        ("point_coordinates_wgs84_lon", "180.01"),
        ("point_coordinates_wgs84_lon", "-180.01"),
        ("point_coordinates_wgs84_lat", "NaN"),
        ("point_coordinates_wgs84_lon", "inf"),
        ("point_coordinates_lv95_east", "NaN"),
        ("point_coordinates_lv95_north", ""),
        ("point_height_masl", "nan"),
        ("point_height_masl", "inf"),
        ("point_height_masl", "private_marker"),
    ],
)
def test_invalid_record_rejects_whole_catalogue_without_raw_field_errors(
    rows, field, value
):
    bad = dict(rows[-1], **{field: value})
    with pytest.raises(InvalidForecastCatalogue) as caught:
        parse_forecast_catalogue(wire([rows[0], bad]), FETCHED)
    assert str(caught.value) == ""
    assert "private_marker" not in "".join(traceback.format_exception(caught.value))


@pytest.mark.parametrize("postal", ["", "830200", "830", "8x02", "²³°²"])
def test_postal_record_requires_its_own_four_ascii_digits(rows, postal):
    row = dict(rows[4], postal_code=postal)
    with pytest.raises(InvalidForecastCatalogue):
        parse_forecast_catalogue(wire([row]), FETCHED)


def test_station_record_requires_station_abbreviation(rows):
    with pytest.raises(InvalidForecastCatalogue):
        parse_forecast_catalogue(wire([dict(rows[0], station_abbr="")]), FETCHED)


@pytest.mark.parametrize(
    "field,value", [("point_type_fr", "changed"), ("point_name", " Säntis ")]
)
def test_duplicate_key_must_match_all_source_columns_even_ignored_or_trimmed_ones(
    rows, field, value
):
    original = rows[-1]
    changed = dict(original, **{field: value})
    with pytest.raises(InvalidForecastCatalogue):
        parse_forecast_catalogue(wire([original, changed]), FETCHED)


def test_reordered_columns_blank_lines_and_aware_time_keep_named_coordinate_contract(
    rows,
):
    local = FETCHED.astimezone(timezone(timedelta(hours=2)))
    content = wire(rows, tuple(reversed(CATALOGUE_COLUMNS))) + b"\n"
    snapshot = parse_forecast_catalogue(content, local)
    assert snapshot.retrieved_at == FETCHED
    assert snapshot.points[0].name == "Säntis"
    assert snapshot.points[0].latitude == 47.249447
    assert snapshot.points[0].longitude == 9.343469


@pytest.mark.parametrize(
    "change",
    [
        "empty",
        "header_only",
        "duplicate_header",
        "extra_header",
        "short_row",
        "long_row",
        "quote",
        "large_field",
    ],
)
def test_invalid_csv_schema_and_row_width_are_atomic_failures(rows, change):
    content = wire([rows[-1]])
    header, row = content.splitlines()
    if change == "empty":
        content = b""
    elif change == "header_only":
        content = header + b"\n"
    elif change == "duplicate_header":
        content = header.replace(b"point_id;", b"point_type_id;", 1) + b"\n" + row
    elif change == "extra_header":
        content = header + b";unexpected\n" + row + b";value"
    elif change == "short_row":
        content = header + b"\n" + row.rsplit(b";", 1)[0]
    elif change == "long_row":
        content = header + b"\n" + row + b";extra"
    elif change == "quote":
        content = header + b'\n"private_marker'
    else:
        content = wire([dict(rows[-1], point_name="x" * 140000)])
    with pytest.raises(InvalidForecastCatalogue):
        parse_forecast_catalogue(content, FETCHED)


def test_payload_limit_and_naive_retrieval_time_are_rejected(rows, monkeypatch):
    content = wire(rows)
    module = "custom_components.meteoswiss.forecast_locations.MAX_CATALOGUE_BYTES"
    monkeypatch.setattr(module, len(content))
    assert parse_forecast_catalogue(content, FETCHED).points
    with pytest.raises(InvalidForecastCatalogue):
        parse_forecast_catalogue(content + b"\n", FETCHED)
    with pytest.raises(InvalidForecastCatalogue):
        parse_forecast_catalogue(bytearray(content), FETCHED)
    with pytest.raises(InvalidForecastCatalogue):
        parse_forecast_catalogue(content, FETCHED.replace(tzinfo=None))


@pytest.mark.parametrize(
    "query,ids",
    [
        ("8302", [("2", "830200")]),
        ("Kloten", [("2", "830200"), ("1", "59")]),
        ("8302 KLOTEN", [("2", "830200")]),
        ("Säntis", [("1", "35"), ("3", "711")]),
        ("SANTIS", [("1", "35"), ("3", "711")]),
        ("Saentis", [("1", "35"), ("3", "711")]),
        ("Zuerich", [("1", "59")]),
        ("Gotthardpass", [("3", "594")]),
        ("Albert Heim Hutte", [("3", "454")]),
        ("SAE", [("1", "35"), ("3", "711")]),
        ("not-a-place", []),
    ],
)
def test_search_accent_case_postcode_station_and_poi_candidates(snapshot, query, ids):
    result = search_forecast_locations(snapshot, query)
    assert [point.identity for point in result.points] == ids
    assert result.total_matches == len(ids)
    assert not result.truncated


@pytest.mark.parametrize(
    "query", ["", " ", "z", "%", "12", "830", "83020", "830200", "711"]
)
def test_empty_short_and_internal_numeric_id_queries_do_not_select_a_place(
    snapshot, query
):
    result = search_forecast_locations(snapshot, query)
    assert result.points == () and result.total_matches == 0


@pytest.mark.parametrize("query", [None, True, "x" * 129])
def test_search_input_validation_is_bounded_and_private(snapshot, query):
    with pytest.raises(ValueError, match="^Invalid location search$"):
        search_forecast_locations(snapshot, query)


@pytest.mark.parametrize("limit", [0, -1, 51, True, "20", None])
def test_search_limit_is_a_bounded_integer(snapshot, limit):
    with pytest.raises(ValueError, match="^Invalid location search limit$"):
        search_forecast_locations(snapshot, "Kloten", limit=limit)


def test_rank_limit_total_and_order_are_stable_without_automatic_selection(rows):
    extra = [
        dict(rows[-1], point_id="900", point_name="Säntis Ost"),
        dict(rows[-1], point_id="901", point_name="Nord Säntis"),
    ]
    left = parse_forecast_catalogue(wire([*rows, *extra]), FETCHED)
    right = parse_forecast_catalogue(wire(list(reversed([*rows, *extra]))), FETCHED)
    a = search_forecast_locations(left, "Säntis")
    b = search_forecast_locations(right, "Säntis")
    assert a == b
    assert [point.point_id for point in a.points] == ["35", "711", "900", "901"]
    limited = search_forecast_locations(left, "Säntis", limit=1)
    assert limited.points == a.points[:1] and limited.total_matches == 4
    assert limited.truncated

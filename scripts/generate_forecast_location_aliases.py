"""Rebuild the postal search alias table from three local OGD files (requires GDAL)."""

import argparse
import csv
from collections import defaultdict
from io import TextIOWrapper
from pathlib import Path
from zipfile import ZipFile

from osgeo import gdal, ogr

HEADER = '''"""Search names for verified MeteoSwiss postal forecast points.

Source: MeteoSwiss. Settlement names and boundaries: ©swisstopo.
See docs/FORECAST_LOCATION_CATALOGUE.md for data terms and the offline join.
"""

POSTAL_ALIASES: dict[tuple[str, str], tuple[str, ...]] = {'''

LANGUAGES = {
    "Hochdeutsch inkl. Lokalsprachen",
    "Franzoesisch inkl. Lokalsprachen",
    "Italienisch inkl. Lokalsprachen",
    "Rumantsch Grischun inkl. Lokalsprachen",
}


def point(easting, northing):
    geometry = ogr.Geometry(ogr.wkbPoint)
    geometry.AddPoint_2D(float(easting), float(northing))
    return geometry


def settlement_names(path):
    centres = defaultdict(dict)
    aliases = defaultdict(set)
    with ZipFile(path) as archive, archive.open("swissNAMES3D_PKT.csv") as source:
        for row in csv.DictReader(TextIOWrapper(source, encoding="utf-8-sig"), delimiter=";"):
            if (row["OBJEKTKLASSE_TLM"], row["OBJEKTART"]) != ("TLM_SIEDLUNGSNAME_ZENTRUM", "Ort"):
                continue
            group = row["NAMENGRUPPE_UUID"]
            if row["NAMEN_TYP"] in {"einfacher Name", "Endonym", "Namenspaar"}:
                centres[row["NAME"]][row["UUID"]] = (group, point(row["E"], row["N"]))
            if group and row["NAMEN_TYP"] in {"Endonym", "Exonym"} and row["SPRACHCODE"] in LANGUAGES:
                aliases[group].add(row["NAME"])
    return centres, aliases


def open_locality_register(path):
    with ZipFile(path) as archive:
        gdb = next(member for member in archive.namelist() if member.endswith(".gdb/"))
    return gdal.OpenEx(f"/vsizip/{path.resolve()}/{gdb.rstrip('/')}")


def locality_name_groups(database, centres, aliases):
    locations = {}
    for locality in database.GetLayerByName("AMTOVZ_LOCALITY"):
        name = locality["LOCALITYNAME"]
        # FileGDB status code 1 denotes a current locality or postal area.
        if locality["STATUS"] != 1 or name not in centres:
            continue
        groups = [
            group for group, xy in centres[name].values() if locality.geometry().Contains(xy)
        ]
        if len(groups) == 1 and aliases.get(groups[0]):
            locations[locality["LOCALITYID"]] = (name, aliases[groups[0]])
    return locations


def postal_areas_by_code(database):
    areas = defaultdict(list)
    for area in database.GetLayerByName("AMTOVZ_ZIP"):
        if area["STATUS"] == 1:
            key = (str(area["ZIP4"]), area["ADDITIONALNUMBER"])
            areas[key].append(area)
    return areas


def postal_forecast_rows(catalogue):
    seen = {}
    with catalogue.open(encoding="latin1", newline="") as source:
        for row in csv.DictReader(source, delimiter=";"):
            if row["point_type_id"] != "2":
                continue
            point_id = row["point_id"]
            if seen.setdefault(point_id, row) != row:
                raise ValueError(f"Conflicting postal forecast rows for {point_id}")
            yield row


def aliases_for_point(row, areas, locations):
    point_id, postcode = row["point_id"], row["postal_code"]
    if len(point_id) != 6 or point_id[:4] != postcode:
        return ()
    candidates = areas.get((postcode, point_id[4:]), ())
    if len(candidates) != 1:
        return ()
    area = candidates[0]
    locality = locations.get(area["FK_LOCALITY"])
    if locality is None or locality[0] != row["point_name"]:
        return ()
    xy = point(row["point_coordinates_lv95_east"], row["point_coordinates_lv95_north"])
    if not area.geometry().Contains(xy):
        return ()
    name, group_names = locality
    return tuple(sorted(group_names - {name}))


def verified_rows(catalogue, names, localities):
    centres, aliases = settlement_names(names)
    database = open_locality_register(localities)
    locations = locality_name_groups(database, centres, aliases)
    areas = postal_areas_by_code(database)
    result = {}
    for row in postal_forecast_rows(catalogue):
        other_names = aliases_for_point(row, areas, locations)
        if other_names:
            result[row["point_id"], row["point_name"]] = other_names
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalogue", type=Path, help="MeteoSwiss point metadata CSV")
    parser.add_argument("names", type=Path, help="swissNAMES3D LV95 CSV zip")
    parser.add_argument("localities", type=Path, help="official index of localities LV95 FileGDB zip")
    args = parser.parse_args()
    gdal.UseExceptions()
    print(HEADER)
    for key, values in sorted(verified_rows(args.catalogue, args.names, args.localities).items()):
        print(f"    {key!r}: {values!r},")
    print("}")

"""Enforce >95% for every module and retain stricter source/flow contracts.

No new module or error-branch exclusions are introduced. A passing coverage
rule alone does not complete the other Bronze/Silver requirements.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def validate() -> None:
    """Read only the standard report generated in this repository."""
    path = Path(__file__).resolve().parents[1] / "coverage.json"
    if path.is_symlink():
        raise SystemExit("coverage.json must not be a symbolic link")
    report = json.loads(path.read_text(encoding="utf-8"))
    files = report["files"]
    if not report["meta"].get("branch_coverage"):
        raise SystemExit("Branch coverage must be enabled")
    print("| Module | Lines | Branches | Combined |")
    print("|---|---:|---:|---:|")
    for name, data in sorted(files.items()):
        summary = data["summary"]
        print(
            f"| `{Path(name).name}` | {summary['covered_lines']}/{summary['num_statements']} | "
            f"{summary['covered_branches']}/{summary['num_branches']} | {summary['percent_covered']:.2f}% |"
        )
        if summary["percent_covered"] <= 95.0:
            raise SystemExit(f"{name} must exceed 95% per-module coverage")
    total = report["totals"]["percent_covered"]
    print(
        f"\nCombined integration coverage: **{total:.2f}%**. All modules exceed 95%; full Silver assessment remains pending."
    )
    flow = files["custom_components/meteoswiss/config_flow.py"]
    if flow["missing_lines"] or flow["missing_branches"]:
        raise SystemExit("Config flow must have 100% line and branch coverage")
    for module in (
        "__init__.py",
        "retry.py",
        "http.py",
        "coordinator.py",
        "pollen_openmeteo.py",
        "pollen_meteoswiss.py",
        "forecast.py",
        "station_condition.py",
        "forecast_summary.py",
        "forecast_locations.py",
        "forecast_location_client.py",
        "forecast_location_config.py",
        "openmeteo.py",
        "weather.py",
        "weather_data.py",
        "cache.py",
        "diagnostics.py",
        "entity.py",
        "version.py",
        "stations_map.py",
        "alerts.py",
        "binary_sensor.py",
        "sensor.py",
        "pollen_sensor.py",
        "precipitation.py",
        "precipitation_recorder.py",
        "calc.py",
    ):
        source = files[f"custom_components/meteoswiss/{module}"]
        if source["missing_lines"] or source["missing_branches"]:
            raise SystemExit(f"{module} must retain full line and branch coverage")
    if total < 99.0:
        raise SystemExit("Integration coverage fell below the current 99.0% floor")


if __name__ == "__main__":
    if len(sys.argv) != 1:
        raise SystemExit("Usage: python scripts/check_quality_coverage.py (no arguments)")
    validate()

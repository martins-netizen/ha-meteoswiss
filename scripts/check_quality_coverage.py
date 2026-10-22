"""Report every module and enforce the first-stage coverage contract.

No integration modules or error branches are excluded. This is deliberately
not a Silver claim: Silver requires above 95% for all integration modules.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def validate(path: Path) -> None:
    report = json.loads(path.read_text())
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
    total = report["totals"]["percent_covered"]
    print(
        f"\nCombined integration coverage: **{total:.2f}%**. Silver (>95% in all modules) remains pending."
    )
    flow = files["custom_components/meteoswiss/config_flow.py"]
    if flow["missing_lines"] or flow["missing_branches"]:
        raise SystemExit("Config flow must have 100% line and branch coverage")
    for module in (
        "__init__.py",
        "retry.py",
        "http.py",
        "coordinator.py",
        "pollen_coordinator_openmeteo.py",
        "pollen_meteoswiss.py",
        "forecast_coordinator.py",
        "openmeteo_coordinator.py",
        "weather.py",
        "weather_data.py",
        "cache.py",
        "diagnostics.py",
        "stations_map.py",
        "alerts.py",
        "binary_sensor.py",
        "sensor.py",
        "pollen_sensor.py",
        "precipitation.py",
        "calc.py",
    ):
        source = files[f"custom_components/meteoswiss/{module}"]
        if source["missing_lines"] or source["missing_branches"]:
            raise SystemExit(f"{module} must retain full line and branch coverage")
    if total < 99.0:
        raise SystemExit("Integration coverage fell below the current 99.0% floor")


if __name__ == "__main__":
    validate(Path(sys.argv[1] if len(sys.argv) > 1 else "coverage.json"))

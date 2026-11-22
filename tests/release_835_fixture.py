"""Component inventory shared by the published 8.3.5b6, b7 and stable tags."""

import json
from pathlib import Path


def component_tree(blob):
    """Use the path as synthetic blob content, independent of the current checkout."""
    base_paths = Path(__file__).parent / "fixtures/release_830_component_paths.json"
    paths = json.loads(base_paths.read_text())
    # These releases retained the 38 base paths and added the same 14 files.
    additions = (
        "device_removal.py",
        "diagnostic_lifecycle.py",
        "forecast_statistics.py",
        "hgt_cleanup.py",
        "hgt_ogd.py",
        "hgt_ogd_coordinator.py",
        "hgt_ogd_manager.py",
        "hgt_ogd_recorder.py",
        "icons.json",
        "repair_issues.py",
        "repairs.py",
        "station_condition.py",
        "statistics_archive.py",
        "wind_statistics.py",
    )
    paths.extend(f"custom_components/meteoswiss/{name}" for name in additions)
    return {path: ("100644", blob(path)) for path in paths}

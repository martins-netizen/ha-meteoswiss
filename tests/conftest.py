"""Pytest configuration for the MeteoSwiss custom integration."""

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def isolated_station_metadata(monkeypatch):
    """Each test owns the global catalogue; entries still share within a test."""
    monkeypatch.setattr("custom_components.meteoswiss.cache._stations_cache", None)
    monkeypatch.setattr("custom_components.meteoswiss.stations_map._stations_map", None)

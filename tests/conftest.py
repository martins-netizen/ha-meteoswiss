"""Pytest configuration for the MeteoSwiss custom integration."""

import pytest

from ha_helpers import PYTEST_PLUGINS

pytest_plugins = PYTEST_PLUGINS


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir):
    """Keep writable HA configuration isolated from the source checkout."""
    return hass_tmp_config_dir


@pytest.fixture(autouse=True)
def isolated_station_metadata(monkeypatch):
    """Each test owns the global catalogue; entries still share within a test."""
    monkeypatch.setattr("custom_components.meteoswiss.cache._stations_cache", None)
    monkeypatch.setattr("custom_components.meteoswiss.stations_map._stations_map", None)

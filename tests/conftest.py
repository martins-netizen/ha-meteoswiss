"""Pytest configuration for the MeteoSwiss custom integration."""

from threading import Lock

import pytest

from sqlalchemy import event
from sqlalchemy.engine import Engine

from ha_helpers import PYTEST_PLUGINS, async_recorder_block_till_done

pytest_plugins = PYTEST_PLUGINS


@pytest.fixture
def recorder_connection_guard():
    """Every native test database connection needs an explicit pool close."""
    opened = 0
    closed = 0
    lock = Lock()

    def connect(connection, record):
        nonlocal opened
        with lock:
            opened += 1

    def close(connection, record):
        nonlocal closed
        with lock:
            closed += 1

    event.listen(Engine, "connect", connect)
    event.listen(Engine, "close", close)
    try:
        yield
    finally:
        event.remove(Engine, "connect", connect)
        event.remove(Engine, "close", close)
        assert opened == closed, f"Recorder left {opened - closed} database connections open"


@pytest.fixture
async def recorder_mock(recorder_connection_guard, recorder_mock, hass):
    """Drain HA work before the native fixture shuts down its database pool."""
    try:
        yield recorder_mock
    finally:
        await hass.async_block_till_done(wait_background_tasks=True)
        await async_recorder_block_till_done(hass)
        await hass.async_block_till_done(wait_background_tasks=True)


@pytest.fixture
def hass_config_dir(hass_tmp_config_dir):
    """Keep writable HA configuration isolated from the source checkout."""
    return hass_tmp_config_dir


@pytest.fixture(autouse=True)
def isolated_station_metadata(monkeypatch):
    """Each test owns the global catalogue; entries still share within a test."""
    monkeypatch.setattr("custom_components.meteoswiss.cache._stations_cache", None)
    monkeypatch.setattr("custom_components.meteoswiss.stations_map._stations_map", None)

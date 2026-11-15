"""Native test database shutdown waits for tracked background read work."""

import asyncio
from unittest.mock import patch

import pytest
from sqlalchemy.engine import Engine


@pytest.fixture
def recorder_shutdown_probe(recorder_connection_guard):
    """Observe shutdown until the original native Recorder fixture has finished."""
    observed = []
    pending = []
    original = Engine.dispose

    def dispose(engine, *args, **kwargs):
        if pending:
            observed.append(pending[0].done() and not pending[0].cancelled())
        return original(engine, *args, **kwargs)

    with patch.object(Engine, "dispose", dispose):
        yield pending
    assert observed == [True], "Recorder disposed its database before the background read completed"
    assert pending[0].result() == 1


async def test_recorder_teardown_drains_background_read_before_disposing_pool(
    recorder_shutdown_probe, recorder_mock, hass
):
    engine = recorder_mock.engine

    def read():
        with engine.connect() as connection:
            return connection.exec_driver_sql("SELECT 1").scalar_one()

    async def queued_read():
        # Model tracked work queued by a statistics-issue refresh. It intentionally
        # outlives the test body, so the fixture owns draining it before shutdown.
        await asyncio.sleep(0.05)
        return await hass.async_add_executor_job(read)

    recorder_shutdown_probe.append(
        hass.async_create_background_task(queued_read(), "Recorder teardown regression")
    )

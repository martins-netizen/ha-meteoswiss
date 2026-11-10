"""Share test imports across the current and frozen minimum HA fixtures."""

from importlib.util import find_spec

if find_spec("pytest_homeassistant") is not None:
    from pytest_homeassistant.common import MockConfigEntry, async_fire_time_changed
    from pytest_homeassistant.components.recorder.common import (
        async_recorder_block_till_done,
        async_wait_recording_done,
    )

    # The official package registers its bootstrap plugin automatically.
    PYTEST_PLUGINS = ()
else:
    from pytest_homeassistant_custom_component.common import (
        MockConfigEntry,
        async_fire_time_changed,
    )
    from pytest_homeassistant_custom_component.components.recorder.common import (
        async_recorder_block_till_done,
        async_wait_recording_done,
    )

    PYTEST_PLUGINS = ("pytest_homeassistant_custom_component",)

__all__ = [
    "MockConfigEntry",
    "PYTEST_PLUGINS",
    "async_fire_time_changed",
    "async_recorder_block_till_done",
    "async_wait_recording_done",
]

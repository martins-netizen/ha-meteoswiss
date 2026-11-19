"""Native and source evidence for HA's exact common-module placement rule."""

import ast
import logging
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest

COMPONENT = Path(__file__).resolve().parents[1] / "custom_components/meteoswiss"
EXPECTED_COORDINATORS = {
    "MeteoSwissDataUpdateCoordinator",
    "MeteoSwissAlertsCoordinator",
    "MeteoSwissPollenCoordinator",
    "OpenMeteoDataUpdateCoordinator",
    "MeteoSwissStationConditionCoordinator",
    "MeteoSwissForecastCoordinator",
    "OpenMeteoPollenCoordinator",
    "MeteoSwissHourlyPrecipitationCoordinator",
    "MeteoSwissHgtCoordinator",
}
EXPECTED_BASE_ENTITIES = {"MeteoSwissEntity", "MeteoSwissCoordinatorEntity"}


def common_definitions(sources):
    """Find actual class definitions, resolving direct and aliased HA imports."""
    result = {"coordinators": {}, "entities": {}}
    targets = {
        "homeassistant.helpers.update_coordinator.DataUpdateCoordinator": "coordinators",
        "homeassistant.helpers.update_coordinator.CoordinatorEntity": "entities",
        "homeassistant.helpers.entity.Entity": "entities",
    }
    for path, source in sources.items():
        tree = ast.parse(source, filename=path)
        imports = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and not node.level and node.module:
                imports.update({alias.asname or alias.name: node.module + "." + alias.name
                                for alias in node.names})
            elif isinstance(node, ast.Import):
                imports.update({alias.asname or alias.name.split(".")[0]:
                                alias.name if alias.asname else alias.name.split(".")[0]
                                for alias in node.names})

        def qualified(node):
            if isinstance(node, ast.Subscript):
                return qualified(node.value)
            if isinstance(node, ast.Name):
                return imports.get(node.id, node.id)
            if isinstance(node, ast.Attribute):
                prefix = qualified(node.value)
                return prefix + "." + node.attr if prefix is not None else None
            return None

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                kinds = {targets[base] for item in node.bases
                         if (base := qualified(item)) in targets}
                for kind in kinds:
                    result[kind].setdefault(node.name, []).append(path)
    return result


def placement_violations(definitions):
    """A compatibility alias is allowed; another class definition is not."""
    return {
        (kind, name, path)
        for kind, classes in definitions.items()
        for name, paths in classes.items()
        for path in paths
        if path != ("coordinator.py" if kind == "coordinators" else "entity.py")
    }


def test_all_coordinator_and_base_entity_definitions_use_common_modules():
    sources = {path.relative_to(COMPONENT).as_posix(): path.read_text()
               for path in COMPONENT.rglob("*.py") if "__pycache__" not in path.parts}
    definitions = common_definitions(sources)
    assert set(definitions["coordinators"]) == EXPECTED_COORDINATORS
    assert set(definitions["entities"]) == EXPECTED_BASE_ENTITIES
    assert not placement_violations(definitions), definitions
    assert all(len(paths) == 1 for classes in definitions.values()
               for paths in classes.values()), "A common class has duplicate definitions"


@pytest.mark.parametrize("base_import,base,kind", [
    ("from homeassistant.helpers.update_coordinator import DataUpdateCoordinator as Poller",
     "Poller[dict]", "coordinators"),
    ("from homeassistant.helpers import update_coordinator as polling",
     "polling.DataUpdateCoordinator[dict]", "coordinators"),
    ("from homeassistant.helpers.entity import Entity as Base", "Base", "entities"),
])
def test_common_module_guard_rejects_misplaced_aliased_classes(base_import, base, kind):
    definitions = common_definitions({
        "specialized.py": base_import + "\nclass Misplaced(" + base + "): pass\n"
    })
    assert placement_violations(definitions) == {(kind, "Misplaced", "specialized.py")}


async def test_hgt_compatibility_alias_preserves_logger_interval_and_entry_ownership(hass):
    from datetime import timedelta
    from typing import get_type_hints

    import aiohttp
    from ha_helpers import MockConfigEntry
    from homeassistant.core import HomeAssistant

    from custom_components.meteoswiss import coordinator, hgt_ogd_coordinator
    from custom_components.meteoswiss.const import DOMAIN
    from custom_components.meteoswiss.runtime_data import MeteoSwissConfigEntry

    canonical = getattr(coordinator, "MeteoSwissHgtCoordinator", None)
    assert canonical is not None
    assert hgt_ogd_coordinator.MeteoSwissHgtCoordinator is canonical
    assert canonical.__module__ == coordinator.__name__
    assert get_type_hints(canonical.__init__) == {
        "hass": HomeAssistant, "entry": MeteoSwissConfigEntry, "station": str,
        "session": aiohttp.ClientSession, "return": type(None),
    }
    assert get_type_hints(canonical._async_update_data) == {"return": dict}
    entry = MockConfigEntry(domain=DOMAIN)
    session = object()
    manager = SimpleNamespace(register=Mock(), release=Mock(),
                              async_refresh=AsyncMock(return_value={"statistics_status": "ready"}),
                              async_sync_issue=AsyncMock())
    with patch.object(coordinator, "get_hgt_manager", return_value=manager):
        instance = canonical(hass, entry, "KLO", session)
    manager.register.assert_called_once_with(entry.entry_id, "klo", session)
    assert instance.logger is logging.getLogger(
        "custom_components.meteoswiss.hgt_ogd_coordinator"
    )
    assert instance.update_interval == timedelta(hours=6)
    assert instance.config_entry is entry and instance._unsub_refresh is None
    assert await instance._async_update_data() == {"statistics_status": "ready"}
    manager.async_refresh.assert_awaited_once()
    manager.async_sync_issue.assert_awaited_once()
    await entry._async_process_on_unload(hass)
    manager.release.assert_called_once_with(entry.entry_id, "klo")

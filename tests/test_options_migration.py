"""Keep installed choices while removing polling from the UI contract."""

from unittest.mock import patch

import pytest
import voluptuous as vol
from homeassistant.config_entries import SOURCE_USER
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.meteoswiss as integration
from custom_components.meteoswiss.const import (
    CONF_DATA_SOURCE,
    CONF_POLLEN_STATION,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)


@pytest.mark.parametrize("source", ["meteoswiss", "openmeteo"])
@pytest.mark.parametrize(
    "data_interval,options_interval,expected",
    [
        (None, None, None),
        (600, None, 600),
        (900, None, 900),
        (900, 1200, 1200),
        (None, 1800, 1800),
    ],
)
async def test_legacy_migration_preserves_choices_and_registry(
    hass, source, data_interval, options_interval, expected
):
    data = {
        CONF_DATA_SOURCE: source,
        "station_id": "KLO",
        "postal_code": "8302",
        "latitude": 0,
        "longitude": 0,
        "unknown_data": {"keep": True},
    }
    options = {CONF_POLLEN_STATION: "PZH", "unknown_option": {"keep": True}}
    if data_interval is not None:
        data[CONF_UPDATE_INTERVAL] = data_interval
    if options_interval is not None:
        options[CONF_UPDATE_INTERVAL] = options_interval
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=data,
        options=options,
        unique_id=f"{source}:legacy",
        title="My weather",
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)
    registry = er.async_get(hass)
    entity = registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{source}_existing_temperature",
        config_entry=entry,
        suggested_object_id="my_weather_temperature",
    )
    identity = (entry.entry_id, entry.unique_id, entry.title, entity.entity_id)
    assert await integration.async_migrate_entry(hass, entry)
    assert (entry.version, entry.minor_version) == (1, 2)
    assert dict(entry.data) == {
        k: v for k, v in data.items() if k != CONF_UPDATE_INTERVAL
    }
    assert dict(entry.options) == {
        CONF_POLLEN_STATION: "PZH",
        "unknown_option": {"keep": True},
        **({CONF_UPDATE_INTERVAL: expected} if expected is not None else {}),
    }
    assert hass.config_entries.async_get_entry(entry.entry_id) is entry
    assert identity == (
        entry.entry_id,
        entry.unique_id,
        entry.title,
        registry.async_get(entity.entity_id).entity_id,
    )
    with patch.object(hass.config_entries, "async_update_entry") as update:
        assert await integration.async_migrate_entry(hass, entry)
        update.assert_not_called()


@pytest.mark.parametrize(
    "version,minor,accepted", [(2, 1, False), (0, 1, False), (1, 3, True)]
)
async def test_migration_does_not_rewrite_other_schemas(hass, version, minor, accepted):
    entry = MockConfigEntry(domain=DOMAIN, version=version, minor_version=minor)
    entry.add_to_hass(hass)
    with patch.object(hass.config_entries, "async_update_entry") as update:
        assert await integration.async_migrate_entry(hass, entry) is accepted
        update.assert_not_called()


async def test_new_setup_and_options_do_not_offer_polling(
    hass, enable_custom_integrations
):
    form = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    values = form["data_schema"](
        {CONF_DATA_SOURCE: "meteoswiss", CONF_POLLEN_STATION: "PZH"}
    )
    assert CONF_UPDATE_INTERVAL not in values
    with pytest.raises(vol.Invalid):
        form["data_schema"]({**values, CONF_UPDATE_INTERVAL: 900})
    entry = MockConfigEntry(
        domain=DOMAIN, options={CONF_UPDATE_INTERVAL: 1200, "unknown_option": "retain"}
    )
    entry.add_to_hass(hass)
    form = await hass.config_entries.options.async_init(entry.entry_id)
    assert CONF_UPDATE_INTERVAL not in form["data_schema"]({})
    with pytest.raises(vol.Invalid):
        form["data_schema"]({CONF_UPDATE_INTERVAL: 900})
    with patch("custom_components.meteoswiss.async_reload_entry"):
        await hass.config_entries.options.async_configure(
            form["flow_id"], {CONF_POLLEN_STATION: "PBE"}
        )
    assert entry.options == {
        CONF_UPDATE_INTERVAL: 1200,
        "unknown_option": "retain",
        CONF_POLLEN_STATION: "PBE",
    }

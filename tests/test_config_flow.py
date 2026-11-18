"""Home Assistant config-flow tests for the Oregon integration."""

from __future__ import annotations

import pytest

from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry
from homeassistant.helpers.selector import NumberSelector, NumberSelectorMode

from custom_components.oregon_idtw21r.const import DOMAIN, NAME, SERVICE_UUID


@pytest.fixture
def bypass_integration_dependencies(monkeypatch):
    """Keep config-flow tests independent of Bluetooth hardware and Recorder."""

    async def skip_dependencies(hass, config, integration):
        return None

    monkeypatch.setattr(
        "homeassistant.config_entries.async_process_deps_reqs",
        skip_dependencies,
    )


@pytest.mark.asyncio
async def test_manual_config_flow_creates_entry(
    hass, enable_custom_integrations, bypass_integration_dependencies
):
    """A manual setup stores a normalized Bluetooth address."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": "aa:bb:cc:dd:ee:ff"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "AA:BB:CC:DD:EE:FF"
    assert result["data"] == {
        "address": "AA:BB:CC:DD:EE:FF",
        "name": NAME,
        "service_uuid": SERVICE_UUID,
    }


@pytest.mark.asyncio
async def test_manual_config_flow_rejects_duplicate_device(
    hass, enable_custom_integrations, bypass_integration_dependencies
):
    """A device already configured cannot be added a second time."""
    address = "AA:BB:CC:DD:EE:FF"
    existing_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=address,
        data={"address": address, "name": NAME, "service_uuid": SERVICE_UUID},
    )
    existing_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"address": address.lower()},
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


@pytest.mark.asyncio
async def test_options_flow_saves_statistics_and_polling_options(
    hass, enable_custom_integrations, bypass_integration_dependencies
):
    """The options flow exposes and saves the three device settings."""
    address = "AA:BB:CC:DD:EE:FF"
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=address,
        data={"address": address, "name": NAME, "service_uuid": SERVICE_UUID},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    polling_key = next(
        key for key in result["data_schema"].schema if key == "polling_interval"
    )
    polling_selector = result["data_schema"].schema[polling_key]
    assert isinstance(polling_selector, NumberSelector)
    assert polling_selector.config["mode"] == NumberSelectorMode.BOX
    assert polling_selector.config["unit_of_measurement"] == "min"
    assert polling_selector.config["translation_key"] == "polling_interval"

    options = {
        "allow_statistics_write": True,
        "auto_sync_enabled": True,
        "polling_interval": 10,
    }
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], user_input=options
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options == options

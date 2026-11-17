"""Home Assistant config-flow tests for the Oregon integration."""

from __future__ import annotations

import pytest

from homeassistant.config_entries import SOURCE_USER
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.oregon_idtw21r.const import DOMAIN, NAME, SERVICE_UUID


@pytest.mark.asyncio
async def test_manual_config_flow_creates_entry(hass, enable_custom_integrations):
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
    hass, enable_custom_integrations
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

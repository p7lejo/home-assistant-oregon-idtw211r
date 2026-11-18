"""Device registry tests for the Oregon integration."""

from types import SimpleNamespace

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.oregon_idtw21r.const import DOMAIN
from custom_components.oregon_idtw21r.device import async_register_base_device


@pytest.mark.asyncio
async def test_base_device_is_registered_and_returns_registry_id(hass):
    """The base station is registered before child devices use its ID."""
    address = "AA:BB:CC:DD:EE:FF"
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=address,
        data={"address": address},
    )
    entry.add_to_hass(hass)
    coordinator = SimpleNamespace(
        address=address,
        device_name="IDTW213R",
    )

    device_id = async_register_base_device(hass, entry, coordinator)

    from homeassistant.helpers import device_registry as dr

    registry = dr.async_get(hass)
    device = registry.async_get_device(
        identifiers={(DOMAIN, address)},
        connections={(dr.CONNECTION_BLUETOOTH, address)},
    )
    assert device is not None
    assert device.id == device_id
    assert entry.entry_id in device.config_entries

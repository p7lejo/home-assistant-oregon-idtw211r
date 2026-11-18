"""Device-registry helpers for the Oregon integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .coordinator import OregonIDTW21RCoordinator
from .const import DOMAIN


def async_register_base_device(
    hass: HomeAssistant,
    entry: ConfigEntry,
    coordinator: OregonIDTW21RCoordinator,
) -> str:
    """Register the base station and return its Home Assistant device ID."""
    registry = dr.async_get(hass)
    device = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, coordinator.address)},
        connections={(dr.CONNECTION_BLUETOOTH, coordinator.address)},
        manufacturer="Oregon Scientific",
        model=coordinator.device_name,
        name=coordinator.device_name,
        hw_version="RAR213HG",
    )
    return device.id

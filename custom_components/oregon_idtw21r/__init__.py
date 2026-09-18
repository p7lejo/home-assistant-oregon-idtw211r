"""The Oregon Scientific IDTW21xR integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .coordinator import OregonIDTW21RCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the integration."""
    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    """Set up an Oregon Scientific device."""
    _LOGGER.info(
        "Setting up Oregon Scientific IDTW21xR '%s' (%s)",
        entry.data.get("name", "IDTW21xR"),
        entry.data["address"],
    )
    coordinator = OregonIDTW21RCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    entry.runtime_data = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.info(
        "Oregon Scientific %s (%s) setup complete; sensors are available",
        entry.data.get("name", "IDTW21xR"),
        entry.data["address"],
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an Oregon Scientific device."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        _LOGGER.info(
            "Oregon Scientific %s (%s) unloaded",
            entry.data.get("name", "IDTW21xR"),
            entry.data["address"],
        )
    return unloaded

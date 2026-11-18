"""The Oregon Scientific IDTW21xR integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_time_change

from .const import DOMAIN
from . import binary_sensor  # noqa: F401
from . import button  # noqa: F401
from . import sensor  # noqa: F401
from .coordinator import HISTORY_CHANNELS, OregonIDTW21RCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor", "button"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


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
    entry.runtime_data = coordinator

    if entry.options.get("auto_sync_enabled", False):

        async def async_daily_history_sync(now) -> None:
            """Fill missing hourly statistics once per day."""
            if not entry.options.get("allow_statistics_write", True):
                _LOGGER.warning(
                    "%s: täglicher Statistikabgleich ausgelassen, da das "
                    "Schreiben von Langzeitstatistiken deaktiviert ist",
                    coordinator.device_name,
                )
                return

            _LOGGER.info(
                "%s: täglicher Oregon-Historieabgleich gestartet",
                coordinator.device_name,
            )
            for channel, _channel_name in HISTORY_CHANNELS:
                try:
                    await coordinator.async_read_history(channel, "fill")
                except Exception:
                    _LOGGER.exception(
                        "%s: täglicher Historieabgleich für Kanal 0x%02X "
                        "fehlgeschlagen",
                        coordinator.device_name,
                        channel,
                    )

        entry.async_on_unload(
            async_track_time_change(
                hass, async_daily_history_sync, hour=3, minute=0, second=0
            )
        )
        _LOGGER.info(
            "%s: täglicher Historieabgleich aktiviert (03:00 Uhr, "
            "ausschließlich fehlende Stundenwerte)",
            coordinator.device_name,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_create_background_task(
        hass,
        coordinator.async_config_entry_first_refresh(),
        name=f"{DOMAIN} initial refresh",
    )
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

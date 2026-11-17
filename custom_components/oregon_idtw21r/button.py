"""History request buttons for Oregon Scientific IDTW21xR."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OregonIDTW21RCoordinator

HISTORY_BUTTONS = (
    (0x00, None),
    (0x10, 1),
    (0x11, 2),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up history request buttons."""
    coordinator: OregonIDTW21RCoordinator = entry.runtime_data
    async_add_entities(
        OregonHistoryButton(coordinator, entry.entry_id, channel, outdoor)
        for channel, outdoor in HISTORY_BUTTONS
    )


class OregonHistoryButton(CoordinatorEntity[OregonIDTW21RCoordinator], ButtonEntity):
    """Button that requests the hourly history for one station channel."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:history"
    _attr_name = "Historie auslesen – Drücken"

    def __init__(
        self,
        coordinator: OregonIDTW21RCoordinator,
        entry_id: str,
        channel: int,
        outdoor_channel: int | None,
    ) -> None:
        super().__init__(coordinator)
        self._channel = channel
        self._attr_unique_id = f"{entry_id}_history_{channel:02x}"
        if outdoor_channel is None:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, coordinator.address)},
                name=coordinator.device_name,
                manufacturer="Oregon Scientific",
                model=coordinator.device_name,
                hw_version="RAR213HG",
            )
        else:
            self._attr_device_info = DeviceInfo(
                identifiers={
                    (DOMAIN, f"{coordinator.address}_outdoor_{outdoor_channel}")
                },
                name=f"Kanal {outdoor_channel}",
                manufacturer="Oregon Scientific",
                via_device=(DOMAIN, coordinator.address),
            )

    async def async_press(self) -> None:
        """Request this channel's hourly history."""
        await self.coordinator.async_read_history(self._channel)

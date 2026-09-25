"""Binary sensors for Oregon Scientific IDTW21xR."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OregonIDTW21RCoordinator

LOW_BATTERY_SENSORS = (
    ("battery_low_outdoor_1", "Outdoor 1 battery", 1),
    ("battery_low_outdoor_2", "Outdoor 2 battery", 2),
    ("battery_low_outdoor_3", "Outdoor 3 battery", 3),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up Oregon Scientific binary sensors."""
    coordinator: OregonIDTW21RCoordinator = entry.runtime_data
    async_add_entities(
        OregonLowBatteryBinarySensor(coordinator, entry.entry_id, key, name, channel)
        for key, name, channel in LOW_BATTERY_SENSORS
    )


class OregonLowBatteryBinarySensor(
    CoordinatorEntity[OregonIDTW21RCoordinator], BinarySensorEntity
):
    """A low-battery status reported by the Oregon weather station."""

    def __init__(self, coordinator, entry_id, key, name, channel) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_has_entity_name = True
        self._attr_device_class = BinarySensorDeviceClass.BATTERY
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{coordinator.address}_outdoor_{channel}")},
            name=f"Kanal {channel}",
            manufacturer="Oregon Scientific",
            via_device=(DOMAIN, coordinator.address),
        )

    @property
    def is_on(self):
        """Return true when the outdoor sensor battery is low."""
        data = self.coordinator.data
        if data is None:
            return None
        return data.get(self._key)

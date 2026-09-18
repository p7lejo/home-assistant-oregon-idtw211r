"""Binary sensors for Oregon Scientific IDTW21xR."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import OregonIDTW21RCoordinator

LOW_BATTERY_SENSORS = (
    ("battery_low_outdoor_1", "Outdoor 1 low battery"),
    ("battery_low_outdoor_2", "Outdoor 2 low battery"),
    ("battery_low_outdoor_3", "Outdoor 3 low battery"),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up Oregon Scientific binary sensors."""
    coordinator: OregonIDTW21RCoordinator = entry.runtime_data
    async_add_entities(
        OregonLowBatteryBinarySensor(coordinator, entry.entry_id, key, name)
        for key, name in LOW_BATTERY_SENSORS
    )


class OregonLowBatteryBinarySensor(
    CoordinatorEntity[OregonIDTW21RCoordinator], BinarySensorEntity
):
    """A low-battery status reported by the Oregon weather station."""

    def __init__(self, coordinator, entry_id, key, name) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_has_entity_name = True
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_device_info = DeviceInfo(
            identifiers={("oregon_idtw21r", coordinator.address)},
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            name=coordinator.device_name,
            manufacturer="Oregon Scientific",
            model=coordinator.device_name,
            hw_version="RAR213HG",
        )

    @property
    def is_on(self):
        """Return the latest low-battery state."""
        data = self.coordinator.data
        if data is None:
            return None
        return bool(data.get(self._key, False))

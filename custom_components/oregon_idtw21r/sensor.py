"""Sensors for Oregon Scientific IDTW21xR."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import OregonIDTW21RCoordinator

SENSORS = (
    ("temperature_indoor", "Indoor temperature", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("temperature_outdoor", "Outdoor temperature", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("humidity_indoor", "Indoor humidity", SensorDeviceClass.HUMIDITY, PERCENTAGE),
    ("humidity_outdoor_1", "Outdoor humidity", SensorDeviceClass.HUMIDITY, PERCENTAGE),
    ("battery", "Battery", SensorDeviceClass.BATTERY, PERCENTAGE),
)


async def async_setup_entry(hass, entry, async_add_entities) -> None:
    """Set up Oregon Scientific sensors."""
    coordinator: OregonIDTW21RCoordinator = entry.runtime_data
    async_add_entities(
        OregonSensor(coordinator, entry.entry_id, key, name, device_class, unit)
        for key, name, device_class, unit in SENSORS
    )


class OregonSensor(CoordinatorEntity[OregonIDTW21RCoordinator], SensorEntity):
    """A sensor provided by the Oregon Scientific weather station."""

    def __init__(
        self, coordinator, entry_id, key, name, device_class, unit
    ) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_class = device_class
        self._attr_native_unit_of_measurement = unit
        self._attr_has_entity_name = True
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address)},
            name=coordinator.device_name,
            manufacturer="Oregon Scientific",
            model=NAME,
        )

    @property
    def native_value(self):
        """Return the latest measurement."""
        return self.coordinator.data.get(self._key)

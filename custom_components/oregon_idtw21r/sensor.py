"""Sensors for Oregon Scientific IDTW21xR."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT, UnitOfTemperature
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, NAME
from .coordinator import OregonIDTW21RCoordinator

SENSORS = (
    ("temperature_indoor", "Indoor temperature", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("temperature_outdoor", "Outdoor temperature", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("humidity_indoor", "Indoor humidity", SensorDeviceClass.HUMIDITY, PERCENTAGE),
    ("humidity_outdoor_1", "Outdoor humidity", SensorDeviceClass.HUMIDITY, PERCENTAGE),
    ("humidity_outdoor_2", "Outdoor 2 humidity", SensorDeviceClass.HUMIDITY, PERCENTAGE),
    ("humidity_outdoor_3", "Outdoor 3 humidity", SensorDeviceClass.HUMIDITY, PERCENTAGE),
    ("temperature_indoor_max", "Indoor temperature maximum", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("temperature_indoor_min", "Indoor temperature minimum", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("temperature_outdoor_max", "Outdoor temperature maximum", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("temperature_outdoor_min", "Outdoor temperature minimum", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("temperature_outdoor_2_max", "Outdoor 2 temperature maximum", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("temperature_outdoor_2_min", "Outdoor 2 temperature minimum", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("temperature_outdoor_3_max", "Outdoor 3 temperature maximum", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("temperature_outdoor_3_min", "Outdoor 3 temperature minimum", SensorDeviceClass.TEMPERATURE, UnitOfTemperature.CELSIUS),
    ("battery", "Battery", SensorDeviceClass.BATTERY, PERCENTAGE),
    ("rssi", "Bluetooth RSSI", None, SIGNAL_STRENGTH_DECIBELS_MILLIWATT),
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

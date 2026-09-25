"""Sensors for Oregon Scientific IDTW21xR."""

from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTemperature,
)
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OregonIDTW21RCoordinator

SENSORS = (
    (
        "temperature_indoor",
        "Indoor temperature",
        SensorDeviceClass.TEMPERATURE,
        UnitOfTemperature.CELSIUS,
    ),
    (
        "temperature_outdoor",
        "Outdoor temperature",
        SensorDeviceClass.TEMPERATURE,
        UnitOfTemperature.CELSIUS,
    ),
    (
        "temperature_outdoor_2",
        "Outdoor 2 temperature",
        SensorDeviceClass.TEMPERATURE,
        UnitOfTemperature.CELSIUS,
    ),
    (
        "temperature_outdoor_3",
        "Outdoor 3 temperature",
        SensorDeviceClass.TEMPERATURE,
        UnitOfTemperature.CELSIUS,
    ),
    (
        "humidity_indoor",
        "Indoor humidity",
        SensorDeviceClass.HUMIDITY,
        PERCENTAGE,
    ),
    (
        "humidity_outdoor_1",
        "Outdoor humidity",
        SensorDeviceClass.HUMIDITY,
        PERCENTAGE,
    ),
    (
        "humidity_outdoor_2",
        "Outdoor 2 humidity",
        SensorDeviceClass.HUMIDITY,
        PERCENTAGE,
    ),
    (
        "humidity_outdoor_3",
        "Outdoor 3 humidity",
        SensorDeviceClass.HUMIDITY,
        PERCENTAGE,
    ),
    ("battery", "Battery", SensorDeviceClass.BATTERY, PERCENTAGE),
    ("rssi", "Bluetooth RSSI", None, SIGNAL_STRENGTH_DECIBELS_MILLIWATT),
)

TEMPERATURE_MIN_MAX = {
    "temperature_indoor": ("temperature_indoor_min", "temperature_indoor_max"),
    "temperature_outdoor": ("temperature_outdoor_min", "temperature_outdoor_max"),
    "temperature_outdoor_2": (
        "temperature_outdoor_2_min",
        "temperature_outdoor_2_max",
    ),
    "temperature_outdoor_3": (
        "temperature_outdoor_3_min",
        "temperature_outdoor_3_max",
    ),
}

HUMIDITY_MIN_MAX = {
    "humidity_indoor": ("humidity_indoor_min", "humidity_indoor_max"),
    "humidity_outdoor_1": ("humidity_outdoor_1_min", "humidity_outdoor_1_max"),
    "humidity_outdoor_2": ("humidity_outdoor_2_min", "humidity_outdoor_2_max"),
    "humidity_outdoor_3": ("humidity_outdoor_3_min", "humidity_outdoor_3_max"),
}

OUTDOOR_SENSOR_KEYS = {
    "temperature_outdoor": 1,
    "humidity_outdoor_1": 1,
    "temperature_outdoor_2": 2,
    "humidity_outdoor_2": 2,
    "temperature_outdoor_3": 3,
    "humidity_outdoor_3": 3,
}


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

        outdoor_channel = OUTDOOR_SENSOR_KEYS.get(key)
        if outdoor_channel is None:
            self._attr_device_info = DeviceInfo(
                identifiers={(DOMAIN, coordinator.address)},
                connections={(CONNECTION_BLUETOOTH, coordinator.address)},
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

    @property
    def native_value(self):
        """Return the latest measurement."""
        data = self.coordinator.data
        if data is None:
            return None
        return data.get(self._key)

    @property
    def extra_state_attributes(self):
        """Return additional values for the sensor."""
        data = self.coordinator.data
        if data is None:
            return None

        attributes = {}

        min_max = TEMPERATURE_MIN_MAX.get(self._key)
        if min_max is not None:
            min_key, max_key = min_max
            attributes["min_temperature"] = data.get(min_key)
            attributes["max_temperature"] = data.get(max_key)

        min_max = HUMIDITY_MIN_MAX.get(self._key)
        if min_max is not None:
            min_key, max_key = min_max
            attributes["min_humidity"] = data.get(min_key)
            attributes["max_humidity"] = data.get(max_key)

        return attributes or None

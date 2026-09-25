"""Coordinator and GATT protocol handling for Oregon Scientific IDTW21xR."""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection
from homeassistant.components import bluetooth
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=5)
NOTIFICATION_CHAR_HANDLE = 0x16
# Bleak exposes the characteristic declaration handle. The ATT value handle is 0x17.
MIN_PACKET_LENGTH = 20

PROTOCOL_CCCD_HANDLES = {
    0x000C: b"\x02\x00",
    0x000F: b"\x02\x00",
    0x0012: b"\x02\x00",
    0x0015: b"\x01\x00",
    0x0018: b"\x02\x00",
    0x001B: b"\x02\x00",
    0x001E: b"\x02\x00",
    0x0021: b"\x02\x00",
    0x0032: b"\x01\x00",
}


def _signed_int16_le(data: bytes, offset: int) -> int:
    """Read a signed little-endian 16-bit value."""
    return int.from_bytes(data[offset : offset + 2], "little", signed=True)


def _temperature_value(data: bytes, offset: int) -> float | None:
    """Return temperature or None for Oregon's no-value sentinel."""
    raw = _signed_int16_le(data, offset)
    # 0x7fff (32767) is used when an outdoor channel has no current value.
    if raw == 0x7FFF:
        return None
    return raw / 10


def _humidity_value(value: int) -> int | None:
    """Return humidity or None for Oregon's no-value sentinel."""
    return None if value == 127 else value


def _decode_low_battery_flags(packet: bytes) -> dict[str, bool]:
    """Decode outdoor low-battery flags from the 0x001f status packet."""
    if len(packet) < 7 or packet[:3] != b"\\x00\\x19\\x07":
        return {}

    status_byte = packet[6]
    return {
        "battery_low_outdoor_1": bool(status_byte & 0x01),
        "battery_low_outdoor_2": bool(status_byte & 0x02),
        "battery_low_outdoor_3": bool(status_byte & 0x04),
    }


def _decode_measurements(type0: bytes, type1: bytes | None) -> dict[str, Any]:
    """Decode the packet format used by IDTW21xR."""
    if len(type0) < MIN_PACKET_LENGTH:
        raise ValueError(
            f"type-0 packet too short: {len(type0)} bytes "
            f"(expected at least {MIN_PACKET_LENGTH})"
        )

    result: dict[str, Any] = {
        "temperature_indoor": _temperature_value(type0, 1),
        "temperature_outdoor": _temperature_value(type0, 3),
        "temperature_outdoor_2": _temperature_value(type0, 5),
        "temperature_outdoor_3": _temperature_value(type0, 7),
        "humidity_indoor": _humidity_value(type0[9]),
        "humidity_outdoor_1": _humidity_value(type0[10]),
        "humidity_outdoor_2": _humidity_value(type0[11]),
        "humidity_outdoor_3": _humidity_value(type0[12]),
        "temperature_trend": type0[13],
        "humidity_trend": type0[14],
        "humidity_indoor_max": _humidity_value(type0[15]),
        "humidity_indoor_min": _humidity_value(type0[16]),
        "humidity_outdoor_1_max": _humidity_value(type0[17]),
        "humidity_outdoor_1_min": _humidity_value(type0[18]),
        "humidity_outdoor_2_max": _humidity_value(type0[19]),
    }

    if type1 is not None and len(type1) >= MIN_PACKET_LENGTH:
        result.update(
            {
                "humidity_outdoor_2_min": _humidity_value(type1[1]),
                "humidity_outdoor_3_max": _humidity_value(type1[2]),
                "humidity_outdoor_3_min": _humidity_value(type1[3]),
                "temperature_indoor_max": _temperature_value(type1, 4),
                "temperature_indoor_min": _temperature_value(type1, 6),
                "temperature_outdoor_max": _temperature_value(type1, 8),
                "temperature_outdoor_min": _temperature_value(type1, 10),
                "temperature_outdoor_2_max": _temperature_value(type1, 12),
                "temperature_outdoor_2_min": _temperature_value(type1, 14),
                "temperature_outdoor_3_max": _temperature_value(type1, 16),
                "temperature_outdoor_3_min": _temperature_value(type1, 18),
            }
        )

    result.update(_decode_low_battery_flags(type1))
    return result


def _log_gatt_services(client: BleakClient, device_name: str) -> None:
    """Log the complete GATT layout, including descriptor handles."""
    for service in client.services:
        _LOGGER.debug(
            "%s: GATT service %s",
            device_name,
            service.uuid,
        )
        for characteristic in service.characteristics:
            _LOGGER.debug(
                "%s:   characteristic handle 0x%04x uuid=%s properties=%s",
                device_name,
                characteristic.handle,
                characteristic.uuid,
                characteristic.properties,
            )
            for descriptor in characteristic.descriptors:
                _LOGGER.debug(
                    "%s:     descriptor handle 0x%04x uuid=%s",
                    device_name,
                    descriptor.handle,
                    descriptor.uuid,
                )


def _find_characteristic(client: BleakClient, handle: int) -> Any | None:
    """Find a GATT characteristic by its value handle."""
    return next(
        (
            characteristic
            for service in client.services
            for characteristic in service.characteristics
            if characteristic.handle == handle
        ),
        None,
    )


def _find_descriptor(client: BleakClient, handle: int) -> Any | None:
    """Find a GATT descriptor by its handle."""
    return next(
        (
            descriptor
            for service in client.services
            for characteristic in service.characteristics
            for descriptor in characteristic.descriptors
            if descriptor.handle == handle
        ),
        None,
    )


async def _enable_protocol_cccds(client: BleakClient, device_name: str) -> None:
    """Enable the CCCDs required by the original Oregon protocol."""
    for handle, value in PROTOCOL_CCCD_HANDLES.items():
        descriptor = _find_descriptor(client, handle)
        if descriptor is None:
            _LOGGER.warning(
                "%s: protocol CCCD descriptor 0x%04x not found",
                device_name,
                handle,
            )
            continue

        try:
            await client.write_gatt_descriptor(descriptor, value)
        except (BleakError, OSError, ValueError) as err:
            raise UpdateFailed(
                f"Failed to enable protocol CCCD 0x{handle:04x}: {err}"
            ) from err

        _LOGGER.debug(
            "%s: enabled protocol CCCD 0x%04x with %s",
            device_name,
            handle,
            value.hex(" "),
        )


class OregonIDTW21RCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Retrieve measurements by an active GATT connection."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.address = entry.data["address"]
        self.device_name = entry.data.get("name", "Oregon Scientific IDTW21xR")
        self.hass = hass
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.address}",
            update_interval=UPDATE_INTERVAL,
            update_method=self._async_update_data,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        ble_device = bluetooth.async_ble_device_from_address(
            self.hass, self.address, connectable=True
        )
        if ble_device is None:
            reason = bluetooth.async_address_reachability_diagnostics(
                self.hass, self.address
            )
            _LOGGER.warning(
                "%s: device %s is not reachable for a GATT connection: %s",
                self.device_name,
                self.address,
                reason,
            )
            raise UpdateFailed(f"Bluetooth device not reachable: {reason}")

        type0: bytes | None = None
        type1: bytes | None = None
        low_battery_flags: dict[str, bool] = {}
        notification_event = asyncio.Event()

        def notification_handler(_: Any, data: bytearray) -> None:
            nonlocal type0, type1
            packet = bytes(data)
            _LOGGER.debug(
                "%s: notification/indication received on handle 0x%02x: %s",
                self.device_name,
                NOTIFICATION_CHAR_HANDLE,
                packet.hex(" "),
            )
            if not packet:
                return

            if (packet[0] >> 4) == 0x08:
                type1 = packet
            else:
                type0 = packet

            if type0 is not None:
                notification_event.set()

        def protocol_notification_handler(handle: int):
            """Create a handler for a protocol characteristic."""
            def handler(_: Any, data: bytearray) -> None:
                packet = bytes(data)
                _LOGGER.debug(
                    "%s: protocol indication from handle 0x%04x: %s",
                    self.device_name,
                    handle,
                    packet.hex(" "),
                )
                if handle == 0x001F:
                    low_battery_flags.update(
                        _decode_low_battery_flags(packet)
                    )

            return handler

        client = None
        try:
            _LOGGER.debug(
                "%s: connecting to %s using Home Assistant Bluetooth/Bleak",
                self.device_name,
                self.address,
            )
            client = await establish_connection(
                BleakClient,
                ble_device,
                self.device_name,
                max_attempts=3,
            )
            _LOGGER.debug(
                "%s: GATT connected; services: %d",
                self.device_name,
                len(list(client.services)),
            )
            _log_gatt_services(client, self.device_name)

            target_char = _find_characteristic(client, NOTIFICATION_CHAR_HANDLE)
            if target_char is None:
                raise UpdateFailed(
                    "GATT measurement characteristic declaration handle 0x16 "
                    "(ATT value handle 0x17) not found"
                )

            if not ({"notify", "indicate"} & set(target_char.properties)):
                raise UpdateFailed(
                    "GATT measurement characteristic handle 0x17 "
                    "does not support notify/indicate"
                )

            _LOGGER.debug(
                "%s: subscribing to measurement characteristic %s "
                "(handle 0x%02x, properties=%s)",
                self.device_name,
                target_char.uuid,
                target_char.handle,
                target_char.properties,
            )

            for cccd_handle, _cccd_value in PROTOCOL_CCCD_HANDLES.items():
                descriptor = _find_descriptor(client, cccd_handle)
                if descriptor is None:
                    _LOGGER.warning(
                        "%s: protocol CCCD descriptor 0x%04x not found",
                        self.device_name,
                        cccd_handle,
                    )
                    continue

                protocol_char = next(
                    (
                        characteristic
                        for service in client.services
                        for characteristic in service.characteristics
                        if descriptor in characteristic.descriptors
                    ),
                    None,
                )
                if protocol_char is None:
                    _LOGGER.warning(
                        "%s: no characteristic found for CCCD 0x%04x",
                        self.device_name,
                        cccd_handle,
                    )
                    continue

                if not ({"notify", "indicate"} & set(protocol_char.properties)):
                    _LOGGER.warning(
                        "%s: characteristic for CCCD 0x%04x has no "
                        "notify/indicate property",
                        self.device_name,
                        cccd_handle,
                    )
                    continue

                try:
                    if protocol_char.handle == target_char.handle:
                        await client.start_notify(protocol_char, notification_handler)
                    else:
                        await client.start_notify(
                            protocol_char,
                            protocol_notification_handler(protocol_char.handle),
                        )
                except (BleakError, OSError, ValueError) as err:
                    raise UpdateFailed(
                        f"Failed to enable protocol CCCD 0x{cccd_handle:04x}: {err}"
                    ) from err

                _LOGGER.debug(
                    "%s: enabled protocol CCCD 0x%04x via start_notify() "
                    "(characteristic 0x%04x, properties=%s)",
                    self.device_name,
                    cccd_handle,
                    protocol_char.handle,
                    protocol_char.properties,
                )

            _LOGGER.debug(
                "%s: waiting for type-0 measurement notification/indication",
                self.device_name,
            )
            try:
                await asyncio.wait_for(notification_event.wait(), timeout=12)
            except TimeoutError as err:
                raise UpdateFailed(
                    "No measurement notification received within 12 seconds"
                ) from err

            await asyncio.sleep(0.5)
            result = _decode_measurements(type0, type1)
            result.update(low_battery_flags)

            service_info = bluetooth.async_last_service_info(
                self.hass, self.address, False
            )
            if service_info is not None:
                result["rssi"] = service_info.rssi
                _LOGGER.debug(
                    "%s: Bluetooth RSSI %d dBm",
                    self.device_name,
                    service_info.rssi,
                )

            battery = next(
                (
                    characteristic
                    for service in client.services
                    for characteristic in service.characteristics
                    if characteristic.uuid.lower()
                    == "00002a19-0000-1000-8000-00805f9b34fb"
                    and "read" in characteristic.properties
                ),
                None,
            )
            if battery is not None:
                raw_battery = await client.read_gatt_char(battery)
                if raw_battery:
                    result["battery"] = raw_battery[0]

            _LOGGER.info(
                "%s: received measurement packet: indoor %.1f °C / %s %%RH, "
                "outdoor %.1f °C / %s %%RH",
                self.device_name,
                result["temperature_indoor"],
                result["humidity_indoor"],
                result["temperature_outdoor"],
                result["humidity_outdoor_1"],
            )
            return result

        except UpdateFailed:
            raise
        except (BleakError, OSError, asyncio.TimeoutError, ValueError) as err:
            _LOGGER.warning(
                "%s: GATT data acquisition failed for %s: %s",
                self.device_name,
                self.address,
                err,
                exc_info=True,
            )
            raise UpdateFailed(f"GATT communication failed: {err}") from err
        finally:
            if client is not None:
                try:
                    for cccd_handle in PROTOCOL_CCCD_HANDLES:
                        descriptor = _find_descriptor(client, cccd_handle)
                        if descriptor is None:
                            continue
                        protocol_char = next(
                            (
                                characteristic
                                for service in client.services
                                for characteristic in service.characteristics
                                if descriptor in characteristic.descriptors
                            ),
                            None,
                        )
                        if protocol_char is not None:
                            await client.stop_notify(protocol_char)
                except Exception:
                    _LOGGER.debug(
                        "%s: error while stopping GATT notifications",
                        self.device_name,
                        exc_info=True,
                    )
                try:
                    await client.disconnect()
                    _LOGGER.debug("%s: GATT disconnected", self.device_name)
                except Exception:
                    _LOGGER.debug(
                        "%s: error while disconnecting GATT client",
                        self.device_name,
                        exc_info=True,
                    )

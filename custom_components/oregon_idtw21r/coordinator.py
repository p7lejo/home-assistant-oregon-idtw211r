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

from .const import DOMAIN, SERVICE_UUID

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=5)
NOTIFICATION_HANDLE = 0x17
MIN_PACKET_LENGTH = 20


def _signed_int16_le(data: bytes, offset: int) -> int:
    return int.from_bytes(data[offset : offset + 2], "little", signed=True)


def _decode_measurements(type0: bytes, type1: bytes | None) -> dict[str, Any]:
    """Decode the packet format used by IDTW21xR."""
    if len(type0) < MIN_PACKET_LENGTH:
        raise ValueError(
            "type-0 packet too short: %d bytes (expected at least %d)",
            len(type0),
            MIN_PACKET_LENGTH,
        )

    result: dict[str, Any] = {
        "temperature_indoor": _signed_int16_le(type0, 1) / 10,
        "temperature_outdoor": _signed_int16_le(type0, 3) / 10,
        "humidity_indoor": type0[9],
        "humidity_outdoor_1": type0[10],
        "humidity_outdoor_2": type0[11],
        "humidity_outdoor_3": type0[12],
        "temperature_trend": type0[13],
        "humidity_trend": type0[14],
        "humidity_indoor_max": type0[15],
        "humidity_indoor_min": type0[16],
        "humidity_outdoor_1_max": type0[17],
        "humidity_outdoor_1_min": type0[18],
        "humidity_outdoor_2_max": type0[19],
    }

    if type1 is not None and len(type1) >= 20:
        result.update(
            {
                "humidity_outdoor_2_min": type1[1],
                "humidity_outdoor_3_max": type1[2],
                "humidity_outdoor_3_min": type1[3],
                "temperature_indoor_max": _signed_int16_le(type1, 4) / 10,
                "temperature_indoor_min": _signed_int16_le(type1, 6) / 10,
                "temperature_outdoor_max": _signed_int16_le(type1, 8) / 10,
                "temperature_outdoor_min": _signed_int16_le(type1, 10) / 10,
                "temperature_outdoor_2_max": _signed_int16_le(type1, 12) / 10,
                "temperature_outdoor_2_min": _signed_int16_le(type1, 14) / 10,
                "temperature_outdoor_3_max": _signed_int16_le(type1, 16) / 10,
                "temperature_outdoor_3_min": _signed_int16_le(type1, 18) / 10,
            }
        )

    return result


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
        notification_event = asyncio.Event()

        def notification_handler(_: Any, data: bytearray) -> None:
            nonlocal type0, type1
            packet = bytes(data)
            _LOGGER.debug(
                "%s: notification received on handle 0x%02x: %s",
                self.device_name,
                NOTIFICATION_HANDLE,
                packet.hex(" "),
            )
            if not packet:
                return
            if packet[0] & 0x80:
                type1 = packet
            else:
                type0 = packet
            if type0 is not None:
                notification_event.set()

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
                len(client.services),
            )

            target_char = next(
                (
                    characteristic
                    for service in client.services
                    for characteristic in service.characteristics
                    if characteristic.handle == NOTIFICATION_HANDLE
                    and "notify" in characteristic.properties
                ),
                None,
            )
            if target_char is None:
                raise UpdateFailed(
                    "GATT notification characteristic handle 0x17 not found"
                )

            _LOGGER.debug(
                "%s: subscribing to notification characteristic %s (handle 0x%02x)",
                self.device_name,
                target_char.uuid,
                target_char.handle,
            )
            await client.start_notify(target_char, notification_handler)

            try:
                await asyncio.wait_for(notification_event.wait(), timeout=12)
            except TimeoutError as err:
                raise UpdateFailed(
                    "No measurement notification received within 12 seconds"
                ) from err

            await asyncio.sleep(0.5)
            result = _decode_measurements(type0, type1)

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
                    _LOGGER.debug(
                        "%s: battery level %d%%",
                        self.device_name,
                        raw_battery[0],
                    )

            _LOGGER.info(
                "%s: received measurement packet: indoor %.1f °C / %d %%RH, "
                "outdoor %.1f °C / %d %%RH",
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
                    await client.disconnect()
                    _LOGGER.debug("%s: GATT disconnected", self.device_name)
                except Exception:
                    _LOGGER.debug(
                        "%s: error while disconnecting GATT client",
                        self.device_name,
                        exc_info=True,
                    )

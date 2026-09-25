# Oregon Scientific IDTW21xR for Home Assistant

Custom Home Assistant integration for Oregon Scientific BLE weather stations of the IDTW21xR family.

## Current status

Version **0.2.18** provides an end-to-end local Bluetooth data path for the IDTW21xR family:

- Bluetooth discovery by the Oregon Scientific service UUID
- Configuration through the Home Assistant config flow using the Bluetooth address
- Native Home Assistant Bluetooth/Bleak GATT connection
- GATT service, characteristic and descriptor discovery
- Reproduction of the relevant CCCD activation sequence used by the original bluepy implementation
- Subscription to the measurement notification/indication characteristic
- Decoding of indoor temperature and humidity
- Decoding of up to three outdoor temperature and humidity sensors
- Base-station battery level via the standard Bluetooth Battery Service
- Separate low-battery status for outdoor sensors 1, 2 and 3
- Automatic reconnect attempts
- Explicit connection, notification, timeout, decoding and battery-status log messages

Outdoor battery status is exposed as Home Assistant binary sensors with the `battery` device class. `on` means that the corresponding outdoor sensor reports a low battery; `off` means that the battery is not reported as low.

The outdoor sensors do not provide a numeric battery percentage through the observed protocol. The base station does provide a numeric battery level through the standard Battery Service.

The implementation is based on protocol information from the original Raspberry Pi/bluepy project linked below. No bluepy, gatttool or hcitool installation is required.

## Important: IDTW211R vs IDTW213R

The original project refers to `IDTW211R` and `IDTW213R`. The observed development device identifies itself as `IDTW213R`. The integration therefore uses the common `IDTW21xR` naming while matching the shared service UUID.

## Protocol reference

- Instructables: https://www.instructables.com/Connect-Raspberry-Pi-to-Oregon-Scientific-BLE-Weat/
- Reference implementation: https://github.com/sighmon/raspberry-pi-bluetooth-temperature

The protocol decoder is a native Python/Bleak implementation of the relevant notification packet formats from that reference and from observations made with an IDTW213R.

The original reference enables nine CCCD handles before waiting for protocol data: `0x000C=02 00`, `0x000F=02 00`, `0x0012=02 00`, `0x0015=01 00`, `0x0018=02 00`, `0x001B=02 00`, `0x001E=02 00`, `0x0021=02 00`, and `0x0032=01 00`.

The native implementation uses Bleak's `start_notify()` for the measurement characteristic and writes the required CCCDs through `write_gatt_descriptor()`.

### Outdoor low-battery status

The outdoor battery state is transmitted separately from the temperature/humidity measurement packets.

The observed status packet has the following 8-byte format:

```
00 19 07 00 00 00 XX 00
```

The `XX` byte is a bit mask:

- `0x01` — outdoor sensor 1 battery low
- `0x02` — outdoor sensor 2 battery low
- `0x04` — outdoor sensor 3 battery low

The integration identifies this packet by its content rather than relying on a fixed GATT handle or CCCD. This is intentional because GATT handles can change after a device reset or rediscovery.

For example:

```
00 19 07 00 00 00 02 00
```

means that the battery of outdoor sensor 2 is reported as low.

## Entities

The integration currently provides the following data:

- Indoor temperature
- Indoor humidity
- Outdoor 1 temperature and humidity
- Outdoor 2 temperature and humidity
- Outdoor 3 temperature and humidity
- Base-station battery level
- Outdoor 1 low-battery binary sensor
- Outdoor 2 low-battery binary sensor
- Outdoor 3 low-battery binary sensor

The humidity value may be unavailable for an outdoor channel when the weather station does not provide a valid humidity value for that channel.

## Logging

For troubleshooting, enable debug logging:

```yaml
logger:
  logs:
    custom_components.oregon_idtw21r: debug
```

Useful log messages include Bluetooth reachability, GATT connection attempts, the discovered GATT layout and handles, CCCD activation, raw protocol packets, decoded measurements, outdoor battery status, base-station battery level and connection failures.

## Development

This is an independent community integration and is not affiliated with Oregon Scientific.

Additional channels, min/max values and further IDTW21xR models will be added only after validation against real devices.
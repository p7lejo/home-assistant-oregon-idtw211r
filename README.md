# Oregon Scientific IDTW21xR for Home Assistant

Custom Home Assistant integration for Oregon Scientific BLE weather stations of the IDTW21xR family.

## Current status

Version 0.2.0 implements the first end-to-end data path:
- Bluetooth discovery by the Oregon Scientific service UUID
- Manual configuration by Bluetooth address
- Native Home Assistant Bluetooth/Bleak GATT connection
- Subscription to the measurement notification characteristic
- Decoding of indoor/outdoor temperature and humidity
- Battery level via the standard Battery Service
- Automatic reconnect attempts
- Explicit connection, notification, timeout and decoding log messages

The implementation is based on the protocol information from the original Raspberry Pi/bluepy project linked below. No bluepy, gatttool or hcitool installation is required.

## Important: IDTW211R vs IDTW213R

The original project refers to `IDTW211R` and `IDTW213R`. The observed development device identifies itself as `IDTW213R`. The integration therefore uses the common `IDTW21xR` naming while matching the shared service UUID.

## Protocol reference

- Instructables: https://www.instructables.com/Connect-Raspberry-Pi-to-Oregon-Scientific-BLE-Weat/
- Reference implementation: https://github.com/sighmon/raspberry-pi-bluetooth-temperature

The protocol decoder is a native Python/Bleak implementation of the relevant notification packet format from that reference.

## Logging

For troubleshooting, enable debug logging:

```yaml
logger:
  logs:
    custom_components.oregon_idtw21r: debug
```

Useful log messages include Bluetooth reachability, GATT connection attempts, service/characteristic discovery, raw notification packets, decoded values, battery level and connection failures.

## Development

This is an independent community integration and is not affiliated with Oregon Scientific.

Additional channels, min/max values and further IDTW21xR models will be added only after validation against real devices.
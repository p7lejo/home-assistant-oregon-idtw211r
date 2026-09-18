# Oregon Scientific IDTW211R for Home Assistant

Custom Home Assistant integration for the **Oregon Scientific IDTW211R** BLE weather sensor.

## Project status

**Early development / protocol investigation**

The IDTW211R advertises via Bluetooth Low Energy (BLE), but the measurement payload is not simply available from passive advertisements. The sensor requires an active BLE GATT interaction before the relevant data is received.

The project aims to implement the complete communication sequence using Home Assistant's native Bluetooth infrastructure:

1. Discover the IDTW211R via BLE advertising.
2. Establish a GATT connection.
3. Enable the required notification characteristic and, where necessary, write the required command to the device.
4. Receive and decode the sensor payload.
5. Expose the measurements as normal Home Assistant entities.

The protocol details (GATT UUIDs, command bytes and payload format) will be derived from the existing IDTW211R implementation and validated against the actual device before the integration is considered stable.

## Goals

- Native Home Assistant integration
- No separate Raspberry Pi packages such as `bluepy`, `gatttool` or `hcitool`
- Use Home Assistant's Bluetooth/Bleak stack
- Configuration through the Home Assistant UI where practical
- Robust reconnect handling
- Proper handling of unavailable devices and failed BLE connections

## Target platform

The integration is intended for **Home Assistant OS** and should use the standard Bluetooth support provided by Home Assistant.

## Protocol reference

The initial protocol investigation is based on the publicly documented work for connecting a Raspberry Pi to Oregon Scientific BLE weather hardware:

https://www.instructables.com/Connect-Raspberry-Pi-to-Oregon-Scientific-BLE-Weat/

The original implementation uses an older Linux/Bluetooth software stack. This project adapts the relevant device communication to the current Home Assistant architecture rather than directly depending on those legacy tools.

## Disclaimer

This is an independent, community-developed Home Assistant integration and is not affiliated with or endorsed by Oregon Scientific.

## License

License to be defined during the initial development phase.

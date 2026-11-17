# Oregon Scientific IDTW21xR for Home Assistant

Custom Home Assistant integration for Oregon Scientific BLE weather stations of the IDTW21xR family.

## Current status

Version **0.2.37** provides an end-to-end local Bluetooth data path for the IDTW21xR family:

- Bluetooth discovery by the Oregon Scientific service UUID
- Configuration through the Home Assistant config flow using the Bluetooth address
- Native Home Assistant Bluetooth/Bleak GATT connection
- GATT service, characteristic and descriptor discovery
- Subscription to protocol characteristics in the original Oregon CCCD activation order, with the measurement indication at CCCD `0x0018` enabled after the preceding channels
- Best-effort subscription to auxiliary protocol characteristics for outdoor low-battery status; failures on these optional characteristics do not block measurement updates
- Decoding of indoor temperature and humidity
- Decoding of up to three outdoor temperature and humidity sensors
- Base-station battery level via the standard Bluetooth Battery Service
- Separate low-battery status for outdoor sensors 1, 2 and 3
- Outdoor sensors 1–3 are represented as separate Home Assistant devices (Kanal 1–3), linked to the IDTW213R base station
- Automatic reconnect attempts
- Explicit connection, notification, timeout, decoding and battery-status log messages

Outdoor battery status is exposed as Home Assistant binary sensors with the `battery` device class. `on` means that the corresponding outdoor sensor reports a low battery; `off` means that the battery is not reported as low.

The outdoor sensors do not provide a numeric battery percentage through the observed protocol. The base station does provide a numeric battery level through the standard Battery Service.

## Min/max values

The integration exposes the recorded minimum and maximum values as attributes of the corresponding temperature and humidity entities.

For example, a humidity entity can provide:

```
min_humidity: 49
max_humidity: 55
unit_of_measurement: %
device_class: humidity
```

Temperature entities similarly provide `min_temperature` and `max_temperature` attributes. The values are available for indoor temperature/humidity and for each available outdoor channel.

The implementation is based on protocol information from the original Raspberry Pi/bluepy project linked below. No bluepy, gatttool or hcitool installation is required.

## Experimental history diagnostics

Hourly station history is read manually from the corresponding Home Assistant device. The base station has a **Historie auslesen** button for the internal sensor; **Kanal 1**, **Kanal 2** and **Kanal 3** each have their own button. The command addresses only the selected channel, matching the Oregon mobile app's one-channel-at-a-time workflow. Channel 3 history decodes both temperature and humidity fields. The currently connected channel 3 sensor does not supply humidity, so its humidity samples are expected to be marked unavailable; the decoder retains support for a future humidity-capable sensor.

The BLE request is sent to the history command characteristic (ATT value handle `0x0011`): `81 00 FF` for the internal sensor, `81 10 FF` for outdoor channel 1, `81 11 FF` for outdoor channel 2 and `81 12 FF` for outdoor channel 3. The integration allows up to 45 seconds for the response because the mobile app's history exchange can take several tens of seconds. Live measurements continue to be updated independently.

Decoded station samples remain diagnostic data; they are not imported into Home Assistant history or statistics. The debug log contains a side-by-side comparison of station values and Home Assistant hourly **mean** statistics, including the difference for temperature and humidity. Missing station values or unavailable HA statistics are shown as `n/a`/—. HA statistics are looked up through the entity registry, not through fixed entity IDs. A comparison is possible only for hours for which HA has statistics; the measurement entities use `state_class: measurement`, so statistics are generated for new readings.

The observed history notification is 18 bytes long: a channel identifier, a start index, five hourly samples and one trailing byte of unknown meaning. The decoder validates the 18-byte packet length and channel identifier, then decodes only the first 17 bytes; the trailing byte is ignored. The latest capture uses `0x4A` (previously observed as `0x49`); no fixed terminator value is required. Each sample contains a signed little-endian 16-bit temperature in tenths of a degree Celsius and one humidity byte. Missing-value markers are `0x7FFF` for temperature and `0x7F` for humidity.

**Timestamp mapping remains provisional.** The current comparison assumes newest-first ordering and maps index 1 to the start of the current local hour; each subsequent index is one hour earlier. The arithmetic is performed in UTC to handle daylight-saving transitions. The mapping must be checked against the mobile app's displayed timestamps before interpreting differences as definitive. The comparison is read-only and never modifies HA statistics.

## Important: IDTW211R vs IDTW213R

The original project refers to `IDTW211R` and `IDTW213R`. The observed development device identifies itself as `IDTW213R`. The integration therefore uses the common `IDTW21xR` naming while matching the shared service UUID.

## Protocol reference

- Instructables: https://www.instructables.com/Connect-Raspberry-Pi-to-Oregon-Scientific-BLE-Weat/
- Reference implementation: https://github.com/sighmon/raspberry-pi-bluetooth-temperature

The protocol decoder is a native Python/Bleak implementation of the relevant notification packet formats from that reference and from observations made with an IDTW213R.

The original reference enables nine CCCD handles before waiting for protocol data: `0x000C=02 00`, `0x000F=02 00`, `0x0012=02 00`, `0x0015=01 00`, `0x0018=02 00`, `0x001B=02 00`, `0x001E=02 00`, `0x0021=02 00`, and `0x0032=01 00`.

The native implementation lets Bleak manage all CCCD activation through `start_notify()` and follows the original bluepy activation order: `0x000C`, `0x000F`, `0x0012`, `0x0015`, `0x0018` (measurement), `0x001B`, `0x001E`, `0x0021`, and `0x0032`. Auxiliary protocol subscriptions are best-effort; a failure on one of them is logged and does not prevent the remaining sequence from being attempted. Direct CCCD descriptor writes are not used.

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

Temperature and humidity entities include the corresponding min/max values as state attributes. For example, humidity entities expose `min_humidity` and `max_humidity`.

The humidity value may be unavailable for an outdoor channel when the weather station does not provide a valid humidity value for that channel.

## Planned / possible future work

Two possible extensions are especially interesting:

1. **System time synchronization** — investigate whether the station's clock can be synchronized through the BLE protocol. The Oregon Scientific mobile app can synchronize the weather station time from the phone, so the relevant BLE command or characteristic may be discoverable and reproducible locally.
2. **Weekly statistics** — investigate reading the weather station's weekly statistics through BLE. The mobile app can display/read these statistics, so the corresponding data and protocol should be investigated and, if accessible, exposed by the integration.

These are investigations rather than implemented features; the required BLE commands and data formats have not yet been established.

## Logging

For troubleshooting, enable debug logging:

```yaml
logger:
  logs:
    custom_components.oregon_idtw21r: debug
```

Useful log messages include Bluetooth reachability, GATT connection attempts, the discovered GATT layout and handles, measurement subscription, optional protocol indications, raw protocol packets, decoded live measurements and decoded hourly history (temperature and humidity by channel), outdoor battery status, base-station battery level and connection failures.

## Development

This is an independent community integration and is not affiliated with Oregon Scientific.

Further IDTW21xR models and additional channels will be added only after validation against real devices.


## Continuous integration and quality checks

The following GitHub Actions run automatically for pull requests targeting `main` and for pushes to `main`:

- **Hassfest** — validates the Home Assistant integration structure and metadata.
- **HACS Validation** — checks the repository as a HACS integration. The license, repository topics and brand-asset checks are temporarily ignored: the repository owner must choose the license, and topics/brand assets are not yet configured.
- **Ruff** — checks Python code for common lint errors.
- **Home Assistant Integration Tests** — exercises the manual config flow, address normalization and duplicate-device handling.
- **BLE Protocol Tests** — compiles the integration and runs the captured history-packet decoder regression tests.

The following workflows are intentionally disabled for now. They are retained as separate workflows and can be enabled when their test scope and acceptance criteria are ready:

- **Python and Home Assistant Compatibility** — Python-version matrix.
- **History and Recorder Tests** — history timestamp mapping and Home Assistant recorder/statistics behavior.
- **Coverage and Type Checking** — coverage reporting and Pyright.

The disabled workflows are manual-dispatch placeholders whose jobs are guarded by `if: false`; they do not run until that guard is removed. The live-device BLE exchange and comparison with the Oregon mobile app still require validation on physical hardware and are not simulated by GitHub-hosted runners.

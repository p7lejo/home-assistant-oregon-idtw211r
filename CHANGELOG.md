# Changelog

## 0.2.34

### Added
- Add separate GitHub Actions for Hassfest, HACS validation, Ruff linting, Home Assistant config-flow tests and BLE protocol regression tests.
- Add automated config-flow tests for manual setup, address normalization and duplicate-device rejection.
- Add three additional quality workflows for Python/Home Assistant compatibility, history/recorder tests and coverage/type checking; these workflows are present but explicitly disabled for now.
- Document the active and disabled CI quality checks.


## 0.2.33

### Added
- Add per-device history buttons for the internal sensor and outdoor channels 1 and 2; each press requests only that channel, matching the mobile app's channel-by-channel workflow.
- Compare decoded station history with Home Assistant hourly mean statistics in the debug log, including timestamps and temperature/humidity deltas.

### Changed
- Remove automatic multi-channel history requests during normal polling. Manual requests allow up to 45 seconds for the station response.
- Keep history diagnostic-only and comparison read-only; the provisional index-to-time mapping is clearly logged.

## 0.2.32

### Fixed
- Validate the 18-byte history packet length and channel, then decode the first 17 bytes without whitelisting the final byte. Its protocol meaning is unknown and observed values vary between captures.
- Add regression coverage for all previously observed trailing values (`0x01`, `0x26`, `0x31`, `0x3D`, `0x48`) and an arbitrary unknown value (`0x99`); malformed packet lengths remain rejected.

## 0.2.31

### Fixed
- Accept the newly captured `0x48` trailing byte on 18-byte hourly history notifications. Without it, all 56 notifications in the 2026-11-17 evening capture were rejected, so no decoded history appeared in the debug log.
- Add regression tests using captured `0x48` packets from indoor and both outdoor channels, including a packet containing missing-value markers.
- Archive the complete 2026-11-17 22:06 raw capture and document that the trailing byte's protocol meaning remains unknown.


## 0.2.30

### Fixed
- Accept the newly observed `0x3D` terminator on 18-byte hourly history notifications. This restores decoding and plaintext temperature/humidity history logging for indoor and outdoor channels 1 and 2.
- Add regression tests using captured `0x3D` packets from all three channels and verify their five decoded temperature/humidity samples.

## 0.2.29

### Fixed
- Accept the additional observed IDTW213R history notification terminator `0x31`, while retaining compatibility with `0x26` and legacy `0x01` packets. The 18-byte packet layout and five-sample decoding remain unchanged.
- Add regression coverage using all seven indoor history packets captured from a real device, including their channel, start indices and decoded sample values.

## 0.2.28

### Added
- Retain decoded hourly BLE history for indoor (`0x00`) and outdoor channels 1 (`0x10`) and 2 (`0x11`) as structured coordinator data.
- Include indexed temperature and humidity samples, independent validity flags, channel status and live sensor entity/statistic ID candidates in Home Assistant diagnostics.
- Set temperature and humidity entities to `state_class: measurement`, allowing Home Assistant to create long-term statistics for new readings.
- Include provisional local timestamps and UTC statistics start times. Hourly arithmetic is performed in UTC to remain consistent across daylight-saving transitions.

### Safety
- The index-to-time mapping is explicitly marked unverified. Index 1 is provisionally anchored to the start of the current local hour based on the synchronized station clock and newest-first ordering.
- Statistics comparison, import and overwrite remain disabled until the timestamp mapping is checked against the station/app history on the real device.

## 0.2.27

### Fixed
- Recognize the actual IDTW213R history-packet terminator `0x26` while retaining compatibility with the earlier observed `0x01` terminator. Previously, these packets were logged raw but rejected by the history decoder.

## 0.2.26

### Added
- Extend diagnostic hourly-history retrieval from the internal sensor to outdoor channels 1 and 2.
- Send the observed channel-specific requests: `81 00 FF` (indoor), `81 10 FF` (outdoor 1) and `81 11 FF` (outdoor 2).
- Decode and log each channel independently, including channels that respond only with missing-value markers.
- Keep history diagnostic-only; no historical entities or statistics are created.


## 0.2.25

### Added
- Add an initial diagnostic-only reader for the hourly history stream selected by BLE command `81 11 FF` (identified in 0.2.26 as outdoor channel 2, not the internal sensor).
- Decode five temperature/humidity samples per history notification and log the indexed series in 24-sample blocks for visual verification.
- Request the history once per coordinator lifetime; history failures do not affect live measurements.
- Keep historical values out of Home Assistant entities and statistics until timestamp, channel addressing and protocol details are validated.


## 0.2.24

### Fixed
- Cache the discovered GATT services and characteristic/CCCD mapping before starting subscriptions. Avoid re-reading `client.services` after a failed GATT operation, when Bleak may no longer expose the service-discovery cache.
- Log the connection state and full exception when a protocol subscription fails.
- Abort the update immediately when the GATT connection has been lost, preserving the original subscription error instead of raising a secondary service-discovery exception.
- Skip notification cleanup when the connection is already disconnected.
- Keep the Oregon CCCD activation order, measurement decoding, entities and five-minute polling interval unchanged.

## 0.2.23

### Fixed
- Restore the original Oregon protocol CCCD activation order using Bleak `start_notify()`: auxiliary characteristics are subscribed before the measurement characteristic at CCCD `0x0018`.
- Keep direct CCCD descriptor writes removed; Bleak remains responsible for enabling notifications and indications.
- Log each subscription attempt and its duration, and fail clearly if the measurement CCCD cannot be resolved or subscribed.
- Keep measurement decoding, entities and the five-minute polling interval unchanged.

## 0.2.22

### Fixed
- Subscribe to the measurement characteristic first and treat auxiliary protocol indications as optional. A failure to subscribe to an auxiliary characteristic no longer prevents temperature and humidity updates.
- Remove direct CCCD descriptor writes; let Bleak manage subscription state.
- Track only successfully subscribed characteristics and stop notifications without re-querying GATT services during cleanup. This avoids a secondary service-discovery exception after a failed subscription.
- Keep measurement decoding, entity definitions and the five-minute polling interval unchanged.

## 0.2.21

### Fixed
- Explicitly write the nine protocol CCCD descriptors in the original Oregon sequence after registering Bleak notification handlers. This restores deterministic device-side notification activation on Bluetooth backends where `start_notify()` alone does not reliably trigger measurements.
- Keep measurement decoding, entity definitions and the five-minute polling interval unchanged.

## 0.2.20

### Fixed
- Prevent coordinator refresh failures when an outdoor temperature is unavailable. The logger now formats missing temperatures as `n/a` instead of passing `None` to a numeric `%.1f` format.
- Keep BLE decoding and sensor values unchanged; this fix only makes diagnostic logging safe for missing temperature values.

## Release notes policy
Every integration release must have a version section above before its version is published. The GitHub Release workflow reads the matching section and uses it as the release description. If a matching section is missing, the workflow fails rather than publishing an empty or generic release note.

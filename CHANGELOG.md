# Changelog

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

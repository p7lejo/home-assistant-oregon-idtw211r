# Changelog

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

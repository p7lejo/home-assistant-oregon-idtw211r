# Changelog

## 0.2.40

### Changed
- Add complete German and English translations for the integration options; Home Assistant selects the language from its configured language.
- Replace the polling interval slider with a numeric input box and show the unit `min` explicitly.
- Keep the polling interval range at 1–60 minutes and the default at 5 minutes.

## 0.2.39

### Added
- Add device options for long-term-statistics write permission, optional daily history synchronization and live measurement polling interval.
- Add an optional daily fill-only synchronization of all four Oregon history channels at 03:00 local Home Assistant time. Existing non-empty hourly means are never overwritten.
- Log history reception, empty responses, import counts and request failures at normal log levels.

### Safety
- Long-term-statistics writing is enabled by default to preserve the existing manual actions; automatic synchronization is disabled by default.
- When statistics writing is disabled, both manual import actions and automatic synchronization are prevented. Read-only history retrieval remains available.

## 0.2.38

### Added
- Add three per-channel history actions: read-only inspection, fill missing hourly long-term-statistics `mean` values, or overwrite existing `mean` values when Oregon provides a valid sample.
- Import into the existing sensor statistic IDs using Home Assistant Recorder's internal statistics import queue. No external statistic series or short-term statistics are created.
- Preserve existing `min`, `max`, `state`, `sum` and `last_reset` values when changing an existing long-term-statistics row; only `mean` is replaced.

### Safety
- Oregon missing-value markers are skipped. Fill mode leaves existing non-null means unchanged; overwrite mode changes only the mean field.

## 0.2.37

### Fixed
- Simplify the history button label to `Historie auslesen`; Home Assistant supplies the button domain suffix automatically, so the action text is no longer duplicated.
- Archive the complete 2026-11-18 00:19 (+01:00) channel 1 raw history capture. All 34 preserved notifications carry trailing byte `0x4A`, with original per-packet timestamps; the capture confirms that `0x4A` is decoded like `0x49` without assigning protocol meaning to the trailing byte.
- Add a regression test using a packet from the `0x4A` capture.

## 0.2.36

### Fixed
- Accept the newly observed `0x4A` trailing byte in 18-byte hourly history notifications; the decoder continues to ignore the trailing byte rather than treating it as a fixed terminator.
- Decode channel 3 humidity bytes normally and include its humidity entity in the HA hourly-statistics comparison. Missing humidity remains `None` via the protocol sentinel, while a future humidity-capable channel 3 sensor will be supported without code changes.
- Add regression tests for the `0x4A` packet and for both missing and present channel 3 humidity values.

## 0.2.35

### Added
- Add a dedicated manual history button for outdoor channel 3, using the same per-channel BLE history request as the Oregon mobile app.
- Decode channel 3 hourly temperature and humidity fields and compare them with Home Assistant statistics.
- Add a protocol regression test for channel 3 history packets.

## 0.2.34

### Added
- Add separate GitHub Actions for Hassfest, HACS validation, Ruff linting, Home Assistant config-flow tests and BLE protocol regression tests.
- Add automated config-flow tests for manual setup, address normalization and duplicate-device rejection.
- Add three additional quality workflows for Python/Home Assistant compatibility, history/recorder tests and coverage/type checking; these workflows are present but explicitly disabled for now.
- Document the active and disabled CI quality checks.
- Configure HACS validation to skip only the repository metadata checks that require owner decisions or assets (license, topics and brands).

## 0.2.33

### Added
- Add per-device history buttons for the internal sensor and outdoor channels 1 and 2; each press requests only that channel, matching the mobile app's channel-by-channel workflow.
- Compare decoded station history with Home Assistant hourly mean statistics in the debug log, including timestamps and temperature/humidity deltas.

### Changed
- Remove automatic multi-channel history requests during normal polling. Manual requests allow up to 45 seconds for the station response.
- Keep history diagnostic-only and comparison read-only; the provisional index-to-time mapping is clearly logged.

## Release notes policy
Every integration release must have a version section above before its version is published. The GitHub Release workflow reads the matching section and uses it as the release description. If a matching section is missing, the workflow fails rather than publishing an empty or generic release note.

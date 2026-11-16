"""Diagnostics for Oregon Scientific IDTW21xR."""

from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import HISTORY_CHANNELS, OregonIDTW21RCoordinator

# The station clock is synchronized and the user confirms newest-first ordering.
# Index 1 is provisionally mapped to the current local hour. Verify against the
# station/app history before enabling any statistics comparison or writes.
HISTORY_ENTITY_KEYS = {
    0x00: ("temperature_indoor", "humidity_indoor"),
    0x10: ("temperature_outdoor", "humidity_outdoor_1"),
    0x11: ("temperature_outdoor_2", "humidity_outdoor_2"),
}


def _sample_timestamps(
    reference_time: datetime | None, index: int
) -> tuple[str | None, str | None]:
    """Return local display time and UTC statistics start for a history index."""
    if reference_time is None:
        return None, None

    # Do the hourly arithmetic in UTC. This keeps samples exactly one hour
    # apart across daylight-saving transitions and avoids ambiguous local hours.
    reference_utc = dt_util.as_utc(reference_time).replace(
        minute=0, second=0, microsecond=0
    )
    statistics_start = reference_utc - timedelta(hours=index - 1)
    return (
        dt_util.as_local(statistics_start).isoformat(),
        statistics_start.isoformat(),
    )


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry
) -> dict:
    """Return station history and the related sensor/statistic identifiers."""
    coordinator: OregonIDTW21RCoordinator = entry.runtime_data
    entity_registry = er.async_get(hass)

    channels = []
    for channel_id, channel_name in HISTORY_CHANNELS:
        samples = coordinator.history_samples.get(channel_id, {})
        temperature_key, humidity_key = HISTORY_ENTITY_KEYS[channel_id]
        temperature_entity_id = entity_registry.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_{temperature_key}"
        )
        humidity_entity_id = entity_registry.async_get_entity_id(
            "sensor", DOMAIN, f"{entry.entry_id}_{humidity_key}"
        )

        sample_rows = []
        for index, values in sorted(samples.items()):
            timestamp, statistics_start = _sample_timestamps(
                coordinator.history_reference_time, index
            )
            sample_rows.append(
                {
                    "index": index,
                    "timestamp": timestamp,
                    "statistics_start": statistics_start,
                    "temperature_c": values[0],
                    "temperature_valid": values[0] is not None,
                    "humidity_percent": values[1],
                    "humidity_valid": values[1] is not None,
                }
            )

        channels.append(
            {
                "channel": f"0x{channel_id:02X}",
                "name": channel_name,
                "status": coordinator.history_status.get(
                    channel_id, "not_requested"
                ),
                "temperature": {
                    "entity_id": temperature_entity_id,
                    "statistic_id_candidate": temperature_entity_id,
                },
                "humidity": {
                    "entity_id": humidity_entity_id,
                    "statistic_id_candidate": humidity_entity_id,
                },
                "samples": sample_rows,
            }
        )

    return {
        "history": {
            "captured_at": (
                coordinator.history_captured_at.isoformat()
                if coordinator.history_captured_at is not None
                else None
            ),
            "timestamp_mapping": "newest_first_index_1_is_current_hour",
            "timestamp_mapping_verified": False,
            "timestamp_mapping_note": (
                "The station clock is synchronized and history is newest first. "
                "Index 1 is provisionally anchored to the start of the current "
                "local hour; each subsequent index is one hour earlier. The "
                "first timestamps still need verification against the station/"
                "app history. Statistics comparison, import and overwrite are "
                "not enabled."
            ),
            "timestamp_reference": (
                coordinator.history_reference_time.isoformat()
                if coordinator.history_reference_time is not None
                else None
            ),
            "channels": channels,
        }
    }

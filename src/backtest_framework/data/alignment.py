"""Multi-instrument bar alignment (D45).

Pairs/multi-leg strategies use inner-join alignment: a bar missing on one leg means no
trading for ANY leg that timestamp, not just the leg that's missing it. Carry still
accrues correctly across whatever gap that creates, with no special handling needed —
carry is computed from (prev_timestamp, curr_timestamp) of two consecutive ALIGNED
bars, not from bar count, so a dropped bar just makes that gap wider. This is the same
property D33 already established for weekends and holidays; a dropped bar is just
another case of it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from ..simulator.fills import Bar
from .bars import TimestampedBar


@dataclass(frozen=True)
class AlignedBar:
    timestamp: datetime
    bars: dict[str, Bar]
    """Every instrument passed to align_bars() has an entry here — inner join means a
    timestamp only survives if every instrument had a bar at it."""


def align_bars(bars_by_instrument: Mapping[str, Sequence[TimestampedBar]]) -> list[AlignedBar]:
    if not bars_by_instrument:
        return []

    by_instrument_by_timestamp: dict[str, dict[datetime, Bar]] = {
        instrument_id: {tb.timestamp: tb.bar for tb in series}
        for instrument_id, series in bars_by_instrument.items()
    }

    common_timestamps = set.intersection(
        *(set(timestamps) for timestamps in by_instrument_by_timestamp.values())
    )

    return [
        AlignedBar(
            timestamp=timestamp,
            bars={
                instrument_id: by_instrument_by_timestamp[instrument_id][timestamp]
                for instrument_id in bars_by_instrument
            },
        )
        for timestamp in sorted(common_timestamps)
    ]

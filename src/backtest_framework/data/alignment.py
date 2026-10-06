"""Multi-instrument bar alignment.

Inner-join alignment: a bar missing on one leg means no trading for any leg at that
timestamp. Carry is computed from the timestamps of consecutive aligned bars, so a
dropped bar widens the gap the same way a weekend or holiday does.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence

from ..simulator.fills import Bar
from .bars import TimestampedBar


@dataclass(frozen=True)
class AlignedBar:
    timestamp: datetime
    bars: dict[str, Bar]
    """One entry per instrument passed to align_bars(); a timestamp is kept only if
    every instrument has a bar at it."""


def align_bars(bars_by_instrument: Mapping[str, Sequence[TimestampedBar]]) -> list[AlignedBar]:
    if not bars_by_instrument:
        return []

    by_instrument_by_timestamp: dict[str, dict[datetime, Bar]] = {
        instrument_id: {tb.timestamp: tb.bar for tb in series}
        for instrument_id, series in bars_by_instrument.items()
    }

    # The dicts above would keep only the last bar per duplicate timestamp (yfinance
    # can produce duplicates after joins or re-fetches), so raise instead.
    for instrument_id, series in bars_by_instrument.items():
        if len(by_instrument_by_timestamp[instrument_id]) != len(series):
            counts = Counter(tb.timestamp for tb in series)
            duplicates = sorted(ts for ts, n in counts.items() if n > 1)
            raise ValueError(
                f"instrument {instrument_id!r} has duplicate bar timestamps "
                f"{[ts.isoformat() for ts in duplicates[:5]]}"
                f"{' (first 5 shown)' if len(duplicates) > 5 else ''}; cannot align, "
                "because a duplicate would overwrite a bar"
            )

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

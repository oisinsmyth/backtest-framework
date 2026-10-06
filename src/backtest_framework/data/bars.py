"""TimestampedBar: a bar with the timestamp a DataSource fetched it at.

Wraps the existing `Bar` (simulator/fills.py) rather than adding a timestamp field to
Bar itself: Bar is constructed directly by the stop-fill logic and cost bricks, none of
which need a timestamp attached; only the engine loop (carry accrual) and data fetching
do.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..simulator.fills import Bar


@dataclass(frozen=True)
class TimestampedBar:
    timestamp: datetime
    bar: Bar

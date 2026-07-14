"""TimestampedBar: a bar with the timestamp a DataSource fetched it at.

Wraps the existing `Bar` (simulator/fills.py) rather than adding a timestamp field to
Bar itself — Bar is constructed directly across Steps 1-4's stop-fill logic and cost
bricks, none of which need a timestamp attached; only the engine loop (carry accrual,
D33) and data fetching do. Keeping Bar unchanged avoids rippling a schema change through
code that has no use for it (D60).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..simulator.fills import Bar


@dataclass(frozen=True)
class TimestampedBar:
    timestamp: datetime
    bar: Bar

"""TimestampedBar: a bar with the timestamp a DataSource fetched it at.

Wraps `Bar` (simulator/fills.py) rather than adding a timestamp to it, since the
stop-fill logic and cost components build Bars without one. Only the engine loop
(carry accrual) and data fetching need timestamps.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..simulator.fills import Bar


@dataclass(frozen=True)
class TimestampedBar:
    timestamp: datetime
    bar: Bar

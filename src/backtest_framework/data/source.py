"""DataSource: one interface, per-asset-class fetchers behind it (D18).

The engine should not care whether bars came from yfinance, a crypto exchange API, or
an options data vendor — every data source implements the same get_bars() shape.
"""

from __future__ import annotations

from datetime import date
from typing import Protocol

from ..instruments.base import Instrument
from .bars import TimestampedBar


class DataSource(Protocol):
    def get_bars(
        self, instrument: Instrument, start: date, end: date, timeframe: str
    ) -> list[TimestampedBar]: ...

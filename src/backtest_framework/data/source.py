"""DataSource: one interface for per-asset-class fetchers.

Every source (yfinance, a crypto exchange API, an options data vendor) implements the
same get_bars() signature.
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

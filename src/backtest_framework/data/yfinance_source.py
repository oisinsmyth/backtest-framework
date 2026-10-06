"""EquityDataSource: a yfinance-backed DataSource.

`get_bars` passes yfinance data straight through, with no snapshotting, cleaning or
validation. yfinance is a scraper and can break or serve bad prints without warning,
so treat its output as provisional. For research, fetch with `get_raw_history` and
pass the result through clean → validate → SnapshotStore.

`get_bars` carries no volume; `get_raw_history` returns volumes separately.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf

from ..instruments.equity import Equity
from ..simulator.fills import Bar
from .bars import TimestampedBar


def _bars_from_dataframe(df: pd.DataFrame) -> list[TimestampedBar]:
    """Convert a yfinance history DataFrame to bars (no network call, so testable offline).

    Timestamps become naive exchange-local wall time (tzinfo stripped). A daily bar is
    identified by its exchange-local date, and carry arithmetic stays DST-insensitive:
    a Fri→Mon weekend is 3.0 days of borrow, not 71 or 73 hours of UTC."""
    bars: list[TimestampedBar] = []
    for timestamp, row in df.iterrows():
        bar = Bar(
            open=float(row["Open"]),
            high=float(row["High"]),
            low=float(row["Low"]),
            close=float(row["Close"]),
        )
        ts = timestamp.to_pydatetime() if hasattr(timestamp, "to_pydatetime") else timestamp
        bars.append(TimestampedBar(timestamp=ts.replace(tzinfo=None), bar=bar))
    return bars


class EquityDataSource:
    """Unhardened equity DataSource over yfinance; see module docstring."""

    def get_bars(self, instrument: Equity, start: date, end: date, timeframe: str) -> list[TimestampedBar]:
        ticker = yf.Ticker(instrument.symbol)
        df = ticker.history(start=start, end=end, interval=timeframe)
        return _bars_from_dataframe(df)

    def get_raw_history(
        self, symbol: str, start: date, end: date, timeframe: str = "1d"
    ) -> tuple[list[TimestampedBar], list[float], list[tuple], list[tuple]]:
        """Fetch raw (unadjusted) bars, volumes and corporate actions.

        This is the input to clean → validate → snapshot. Returns (bars, volumes,
        dividends, splits), where dividends and splits are [(timestamp, amount or
        ratio)] with nonzero entries only."""
        ticker = yf.Ticker(symbol)
        df = ticker.history(start=start, end=end, interval=timeframe, auto_adjust=False, actions=True)
        bars = _bars_from_dataframe(df)
        volumes = [float(v) for v in df["Volume"]]
        timestamps = [tb.timestamp for tb in bars]
        dividends = [
            (ts, float(amount)) for ts, amount in zip(timestamps, df["Dividends"]) if float(amount) != 0.0
        ]
        splits = [
            (ts, float(ratio)) for ts, ratio in zip(timestamps, df["Stock Splits"]) if float(ratio) != 0.0
        ]
        return bars, volumes, dividends, splits

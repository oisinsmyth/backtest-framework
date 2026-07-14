"""EquityDataSource: a yfinance-backed DataSource (D18-lite).

UNHARDENED (D59). This is a raw passthrough over yfinance, not the hardened data layer
Step 7 builds: no immutable snapshotting (D24), no cleaning report (D25), no sanity
gate (D26). yfinance is a scraper, not an API — it breaks and serves bad prints without
warning (that's D26's own rationale). Treat anything fetched through this as
provisional, good enough to unblock Step 5/6, not good enough to trust unreviewed.

No volume/ADV field is carried through yet — D3's sqrt-impact brick will need to add it
when it actually needs it; carrying it now with nothing consuming it would be
speculative generality this codebase otherwise avoids.
"""

from __future__ import annotations

from datetime import date

import pandas as pd
import yfinance as yf

from ..instruments.equity import Equity
from ..simulator.fills import Bar
from .bars import TimestampedBar


def _bars_from_dataframe(df: pd.DataFrame) -> list[TimestampedBar]:
    """Pure conversion logic, deliberately separated from the network call so it's
    testable with a hand-built fixture DataFrame — no live fetch required.

    Timestamps are normalized to NAIVE exchange-local wall time (tzinfo stripped,
    D75): daily-bar identity is the exchange-local date, and D33's calendar-day
    carry arithmetic must not become DST-sensitive (a Fri→Mon weekend is exactly 3.0
    days of borrow in wall-clock terms, not 71/73 hours of UTC)."""
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
    """UNHARDENED equity DataSource over yfinance — see module docstring."""

    def get_bars(self, instrument: Equity, start: date, end: date, timeframe: str) -> list[TimestampedBar]:
        ticker = yf.Ticker(instrument.symbol)
        df = ticker.history(start=start, end=end, interval=timeframe)
        return _bars_from_dataframe(df)

    def get_raw_history(
        self, symbol: str, start: date, end: date, timeframe: str = "1d"
    ) -> tuple[list[TimestampedBar], list[float], list[tuple], list[tuple]]:
        """RAW (unadjusted) bars + volumes + corporate actions (D6): the input the
        hardened pipeline (clean → validate → snapshot, Step 7) starts from. Returns
        (bars, volumes, dividends, splits) where dividends/splits are
        [(timestamp, amount-or-ratio)] with nonzero entries only."""
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

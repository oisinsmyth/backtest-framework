"""Tests for the minimal (unhardened, D59) yfinance data source.

The conversion logic (_bars_from_dataframe) is tested offline against a hand-built
fixture DataFrame — no network required. One test hits real yfinance and is marked
live_fetch, excluded from the default run per pyproject.toml's addopts (matching
VERIFICATION_SCHEME.md's cross-cutting gate: "CI runs everything offline... live-fetch
tests are excluded by marker").
"""

from datetime import date, datetime

import pandas as pd
import pytest

from backtest_framework.data.yfinance_source import EquityDataSource, _bars_from_dataframe
from backtest_framework.instruments.equity import Equity


def _fixture_dataframe() -> pd.DataFrame:
    index = pd.DatetimeIndex([datetime(2026, 7, 10), datetime(2026, 7, 13), datetime(2026, 7, 14)])
    return pd.DataFrame(
        {
            "Open": [100.0, 101.0, 102.5],
            "High": [101.5, 102.0, 103.0],
            "Low": [99.5, 100.5, 101.0],
            "Close": [101.0, 101.8, 102.0],
            "Volume": [1_000_000, 900_000, 1_100_000],
        },
        index=index,
    )


def test_bars_from_dataframe_maps_ohlc_correctly():
    bars = _bars_from_dataframe(_fixture_dataframe())

    assert len(bars) == 3
    first = bars[0]
    assert first.timestamp == datetime(2026, 7, 10)
    assert first.bar.open == 100.0
    assert first.bar.high == 101.5
    assert first.bar.low == 99.5
    assert first.bar.close == 101.0


def test_bars_from_dataframe_preserves_row_order():
    bars = _bars_from_dataframe(_fixture_dataframe())
    assert [b.timestamp for b in bars] == [
        datetime(2026, 7, 10),
        datetime(2026, 7, 13),
        datetime(2026, 7, 14),
    ]


def test_bars_from_dataframe_empty_dataframe_returns_empty_list():
    empty = pd.DataFrame(columns=["Open", "High", "Low", "Close", "Volume"])
    assert _bars_from_dataframe(empty) == []


@pytest.mark.live_fetch
def test_equity_data_source_fetches_real_bars():
    source = EquityDataSource()
    bars = source.get_bars(
        Equity(symbol="AAPL"), start=date(2024, 1, 2), end=date(2024, 1, 10), timeframe="1d"
    )

    assert len(bars) > 0
    for tb in bars:
        assert tb.bar.low <= tb.bar.open <= tb.bar.high
        assert tb.bar.low <= tb.bar.close <= tb.bar.high

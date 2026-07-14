"""Step 9 X-gate (D83): Sharpe, Sortino, max drawdown vs quantstats on the same
return series — a reference implementation we didn't write.

Convention notes (why exact agreement is possible, D80/D83): our rf de-annualization
is geometric, (1+rf)^(1/N)−1, which is quantstats' convention; our Sortino downside
is the full-length RMS of negative excess, also quantstats' convention. quantstats
requires a DatetimeIndex for its rf handling (found during the smoke test — a plain
RangeIndex crashes its tz path), so the series here carries business dates.
"""

import warnings

import numpy as np
import pytest

qs = pytest.importorskip("quantstats")
import pandas as pd  # noqa: E402

from backtest_framework.analytics.metrics import max_drawdown, sharpe, sortino  # noqa: E402

TOLERANCE = 1e-9  # tighter than D47 — same formulas should agree to float precision

warnings.filterwarnings("ignore")

_rng = np.random.default_rng(7)
_returns = _rng.normal(0.0004, 0.01, 1000)
_series = pd.Series(_returns, index=pd.bdate_range("2020-01-01", periods=1000))


def test_sharpe_matches_quantstats_at_zero_rf():
    ours = sharpe(_returns, rf_annual=0.0, periods_per_year=252)
    theirs = float(qs.stats.sharpe(_series, rf=0, periods=252, annualize=True))
    assert ours == pytest.approx(theirs, rel=TOLERANCE)


def test_sharpe_matches_quantstats_at_4pct_rf():
    # The one that catches rf-convention drift: both sides de-annualize geometrically.
    ours = sharpe(_returns, rf_annual=0.04, periods_per_year=252)
    theirs = float(qs.stats.sharpe(_series, rf=0.04, periods=252, annualize=True))
    assert ours == pytest.approx(theirs, rel=1e-6)


def test_sortino_matches_quantstats():
    ours = sortino(_returns, rf_annual=0.0, periods_per_year=252)
    theirs = float(qs.stats.sortino(_series, rf=0, periods=252, annualize=True))
    assert ours == pytest.approx(theirs, rel=1e-6)


def test_max_drawdown_matches_quantstats():
    # quantstats takes returns and reports a negative fraction; ours takes an equity
    # curve and reports a positive fraction — convert, then compare.
    equity = (1 + _series).cumprod()
    curve = [(ts, float(v)) for ts, v in equity.items()]
    ours = max_drawdown(curve)
    theirs = -float(qs.stats.max_drawdown(_series))
    assert ours == pytest.approx(theirs, rel=1e-9)

"""Tests for cointegration-filtered selection (study v2, D92/D93)."""

from datetime import datetime, timedelta

import numpy as np
import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.dataview import build_data_view
from backtest_framework.research.cointegration import (
    CointegrationSelector,
    adf_stat,
    engle_granger_beta,
)
from backtest_framework.simulator.fills import Bar

RNG = np.random.default_rng(17)


def _views(log_prices_by_symbol):
    views = {}
    start = datetime(2026, 1, 5, 16)
    for symbol, logp in log_prices_by_symbol.items():
        bars = tuple(
            TimestampedBar(start + timedelta(days=i), Bar(open=p, high=p, low=p, close=p)).bar
            for i, p in enumerate(np.exp(logp).astype(float))
        )
        views[symbol] = build_data_view(bars, len(bars) - 1)
    return views


def test_engle_granger_recovers_known_beta():
    x = np.cumsum(RNG.normal(0.0005, 0.01, 400))
    noise = RNG.normal(0, 0.002, 400)  # stationary
    y = 0.3 + 1.2 * x + noise

    alpha, beta, residuals = engle_granger_beta(y, x)

    assert beta == pytest.approx(1.2, abs=0.02)
    assert alpha == pytest.approx(0.3, abs=0.02)
    assert abs(residuals.mean()) < 1e-9  # OLS residuals are mean-zero with intercept


def test_adf_separates_stationary_from_random_walk():
    n = 300
    eps = RNG.normal(0, 0.01, n)
    ar1 = np.empty(n)
    ar1[0] = 0.0
    for i in range(1, n):
        ar1[i] = 0.6 * ar1[i - 1] + eps[i]
    walk = np.cumsum(RNG.normal(0, 0.01, n))

    stat_ar1 = adf_stat(ar1)
    stat_walk = adf_stat(walk)

    assert stat_ar1 < -5.0  # strong mean reversion: decisively negative
    assert stat_walk > -2.5  # random walk: cannot reject the unit root
    assert stat_ar1 < stat_walk


def test_adf_matches_statsmodels_exactly():
    # D93's X-anchor: same regression spec (no constant, fixed lag), same statistic.
    sm = pytest.importorskip("statsmodels.tsa.stattools")

    for seed in (3, 4, 5):
        rng = np.random.default_rng(seed)
        n = 250
        s = np.empty(n)
        s[0] = 0.0
        eps = rng.normal(0, 0.01, n)
        for i in range(1, n):
            s[i] = 0.7 * s[i - 1] + eps[i]

        ours = adf_stat(s, lags=1)
        theirs = float(sm.adfuller(s, maxlag=1, autolag=None, regression="n")[0])
        assert ours == pytest.approx(theirs, rel=1e-9)


def test_selector_prefers_engineered_cointegrated_pair_and_filters_bad_beta():
    n = 260
    common = np.cumsum(RNG.normal(0.0003, 0.009, n))
    base = np.log(100.0)

    universe = {}
    # Four pure-noise walks.
    for k in range(4):
        universe[f"N{k}"] = base + np.cumsum(RNG.normal(0.0, 0.012, n))

    # GOOD pair: beta ~ 1, strongly mean-reverting spread (AR(1), rho=0.5).
    spread = np.empty(n)
    spread[0] = 0.0
    eps = RNG.normal(0, 0.004, n)
    for i in range(1, n):
        spread[i] = 0.5 * spread[i - 1] + eps[i]
    universe["GOOD_A"] = base + common
    universe["GOOD_B"] = universe["GOOD_A"] - spread

    # BAD-BETA pair: perfectly cointegrated but beta = 3 - stationarity evidence
    # about a spread the 1:1 strategy doesn't trade; must be filtered (D92).
    universe["BB_X"] = base + 0.2 * common
    universe["BB_Y"] = base + 3.0 * (universe["BB_X"] - base) + RNG.normal(0, 0.001, n)

    selector = CointegrationSelector(gatev_prefilter=20, beta_window=(0.7, 1.3))
    selection = selector(_views(universe), top_n=2)

    assert selection.n_pairs_tested == 28  # C(8,2): the FULL count, not the prefilter
    assert ("GOOD_A", "GOOD_B") in selection.ranked_pairs
    for pair in selection.ranked_pairs:
        assert set(pair) != {"BB_X", "BB_Y"}  # beta=3 pair excluded

    details = selector.last_details
    good = next(d for d in details if set(d["pair"]) == {"GOOD_A", "GOOD_B"})
    assert 0.9 < good["beta"] < 1.1
    assert good["adf_stat"] < -4.0


def test_adf_too_short_fails_loudly():
    with pytest.raises(ValueError, match="too short"):
        adf_stat(np.array([1.0, 2.0, 3.0]))

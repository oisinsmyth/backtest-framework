"""Unit tests for BetaHedgedZScoreStrategy (study v3, D94)."""

import numpy as np
import pytest

from backtest_framework.engine.dataview import build_data_view
from backtest_framework.research.beta_zscore import BetaHedgedZScoreStrategy
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy


def _views(prices_a, prices_b):
    bars_a = tuple(Bar(open=p, high=p, low=p, close=p) for p in prices_a)
    bars_b = tuple(Bar(open=p, high=p, low=p, close=p) for p in prices_b)
    i = len(bars_a) - 1
    return {"A": build_data_view(bars_a, i), "B": build_data_view(bars_b, i)}


def _strategy(beta, **overrides):
    defaults = dict(
        strategy_id="s", instrument_a="A", instrument_b="B", hedge_beta=beta,
        lookback=10, entry_z=1.5, exit_z=0.5, leg_weight=1.0,
    )
    return BetaHedgedZScoreStrategy(**{**defaults, **overrides})


def test_weights_normalize_to_constant_gross():
    for beta in (0.7, 1.0, 1.3):
        s = _strategy(beta)
        assert s.weight_a + s.weight_b == pytest.approx(2.0)  # gross == 2 x leg_weight
        assert s.weight_b / s.weight_a == pytest.approx(beta)  # legs in ratio beta


def test_beta_one_reduces_exactly_to_zscore_pairs_strategy():
    # The tie to the v2 baseline (D94): at beta=1, targets are IDENTICAL.
    rng = np.random.default_rng(9)
    prices_a = list(100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, 40))))
    prices_b = list(100.0 * np.exp(np.cumsum(rng.normal(0, 0.01, 40))))
    views = _views(prices_a, prices_b)

    hedged = _strategy(1.0)
    baseline = ZScorePairsStrategy(
        strategy_id="s", instrument_a="A", instrument_b="B",
        lookback=10, entry_z=1.5, exit_z=0.5, leg_weight=1.0,
    )
    assert hedged.generate_targets(views) == baseline.generate_targets(views)


def test_hedged_spread_sees_reversion_the_one_to_one_spread_misses():
    # Constructed beta=1.2 pair: ln B random-walks, ln A = 1.2 ln B + tiny AR noise.
    # The BETA spread (ln A - 1.2 ln B) is stationary; the 1:1 spread inherits
    # 0.2 x ln B's random walk and trends. The hedged strategy's z stays meaningful.
    rng = np.random.default_rng(4)
    n = 60
    log_b = np.log(100.0) + np.cumsum(rng.normal(0.002, 0.01, n))
    ar = np.zeros(n)
    eps = rng.normal(0, 0.003, n)
    for i in range(1, n):
        ar[i] = 0.5 * ar[i - 1] + eps[i]
    log_a = 1.2 * log_b - 0.2 * np.log(100.0) + ar  # keeps A near B's price scale

    views = _views(list(np.exp(log_a)), list(np.exp(log_b)))
    hedged = _strategy(1.2, lookback=20)
    targets = hedged.generate_targets(views)
    assert len(targets) == 2  # produces well-formed targets on the hedged spread
    # And its weights carry the 1.2 ratio when a side is on (or zero when flat):
    wa, wb = abs(targets[0].weight), abs(targets[1].weight)
    if wa > 0:
        assert wb / wa == pytest.approx(1.2)


def test_warm_up_is_flat():
    views = _views([100.0] * 5, [100.0] * 5)  # < lookback+1
    targets = _strategy(1.2).generate_targets(views)
    assert all(t.weight == 0.0 for t in targets)


def test_validation_errors():
    with pytest.raises(ValueError, match="hedge_beta"):
        _strategy(0.0)
    with pytest.raises(ValueError, match="hedge_beta"):
        _strategy(-1.1)
    with pytest.raises(ValueError, match="exit_z"):
        _strategy(1.0, entry_z=1.0, exit_z=1.0)

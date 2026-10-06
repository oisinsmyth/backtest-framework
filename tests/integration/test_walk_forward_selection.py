"""Pair selection inside walk-forward, on a synthetic universe where one pair's
relationship inverts after the training window.

Selection picks that pair by construction. The test checks that selection used only
training data, enforced by DataView (the same look-ahead guard strategies run behind),
and that the select-then-trade-OOS pipeline runs end to end.
"""

from datetime import datetime, timedelta

import numpy as np
import pytest

from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.dataview import LookAheadError
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy
from backtest_framework.validation.pair_selection import select_pairs
from backtest_framework.validation.walk_forward import walk_forward_windows

TRAIN, TEST = 120, 60
START = datetime(2026, 1, 5, 16)


def _series(log_prices) -> list[TimestampedBar]:
    return [
        TimestampedBar(START + timedelta(days=i), Bar(open=p, high=p, low=p, close=p))
        for i, p in enumerate(np.exp(log_prices).astype(float))
    ]


def _universe():
    """Six independent noise series plus the pair (P1, P2), which tracks closely in train
    and diverges sharply in test: ideal in sample, broken out of sample."""
    rng = np.random.default_rng(2026)
    universe = {}
    for k in range(6):
        universe[f"N{k}"] = _series(np.log(100.0) + np.cumsum(rng.normal(0.0002, 0.015, TRAIN + TEST)))

    p1 = np.log(100.0) + np.cumsum(rng.normal(0.0002, 0.012, TRAIN + TEST))
    spread_train = rng.normal(0.0, 0.001, TRAIN)  # tightly tracking: lowest Gatev SSD
    spread_test = 0.02 * np.arange(1, TEST + 1) + rng.normal(0.0, 0.005, TEST)  # inversion
    p2 = p1 - np.concatenate([spread_train, spread_test])
    universe["P1"], universe["P2"] = _series(p1), _series(p2)
    return universe


def test_selection_uses_training_data_only_and_pipeline_runs_oos():
    universe = _universe()
    windows = list(walk_forward_windows(universe, train_size=TRAIN, test_size=TEST))
    assert len(windows) == 1
    window = windows[0]

    # --- Structural guard: fitters get train bars only.
    for symbol, view in window.train_views.items():
        assert len(view) == TRAIN  # exactly the training window
        with pytest.raises(LookAheadError):
            view[TRAIN]  # the first test bar is not in the view at all
        # The last visible close is the last training close, not a test close.
        assert view.current_bar.close == universe[symbol][TRAIN - 1].bar.close

    # --- Selection picks the engineered pair from training data (its train score is the
    # best; its test behaviour is not visible to the selector).
    selection = select_pairs(window.train_views, top_n=1)
    assert selection.ranked_pairs[0] == ("P1", "P2")
    assert selection.n_pairs_tested == 28  # C(8,2) - the multiplicity count

    # --- The selected pair trades out of sample, end to end.
    a, b = selection.ranked_pairs[0]
    result = run_backtest(
        bars_by_instrument={s: window.test_bars_by_instrument[s] for s in (a, b)},
        instruments={a: Equity(symbol=a), b: Equity(symbol=b)},
        strategies=[
            ZScorePairsStrategy(
                strategy_id="wf", instrument_a=a, instrument_b=b, lookback=20, entry_z=1.5, exit_z=0.5
            )
        ],
        cost_stack=CostStack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )
    assert len(result.equity_curve) == TEST  # the OOS window ran in full
    # The sign of the OOS result is not checked: the inverting pair may lose, and the
    # test only requires that selection could not have known that.

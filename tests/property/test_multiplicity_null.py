"""Step 12 P-gates (D23, D29, D87), deterministic under fixed seeds:

1. Multiplicity: top-N selection on a 200-series pure-noise universe -> OOS edge
   ~ 0 within CI, and the number of pairs tested (19,900) lands in the TrialRegistry.
2. Synthetic nulls: the z-score strategy on cointegrated-LOOKING pairs whose spread
   is a random walk (zero true edge by construction) earns ~ nothing at zero cost.
   Per the gate: if this profits, stop everything.
"""

import math
from datetime import datetime, timedelta

import numpy as np

from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.instruments.equity import Equity
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy
from backtest_framework.validation.pair_selection import select_pairs
from backtest_framework.validation.synthetic import cointegrated_looking_pair
from backtest_framework.validation.walk_forward import walk_forward_windows

TRAIN, TEST = 150, 150
START = datetime(2026, 1, 5, 16)
STARTING_CASH = 100_000.0


def _noise_universe(seed: int, n_series: int = 200):
    rng = np.random.default_rng(seed)
    universe = {}
    for k in range(n_series):
        logp = np.log(100.0) + np.cumsum(rng.normal(0.0, 0.015, TRAIN + TEST))
        universe[f"S{k:03d}"] = [
            TimestampedBar(START + timedelta(days=i), Bar(open=p, high=p, low=p, close=p))
            for i, p in enumerate(np.exp(logp).astype(float))
        ]
    return universe


def _trade_pair_oos(bars_by_instrument, a: str, b: str) -> tuple[float, int]:
    # leg_weight 0.25 (not the default 1.0): at 200% gross, per-pair OOS return vol
    # on independent 1.5%/day random walks is ~20%, which would make any absolute
    # bound on the MEAN meaningless at this sample size. 50% gross scales the noise
    # down 4x so "≈ 0" is a claim with teeth. The zero-edge property itself is
    # leverage-invariant — this is test calibration, not result shopping.
    result = run_backtest(
        bars_by_instrument={a: bars_by_instrument[a], b: bars_by_instrument[b]},
        instruments={a: Equity(symbol=a), b: Equity(symbol=b)},
        strategies=[
            ZScorePairsStrategy(
                strategy_id="null",
                instrument_a=a,
                instrument_b=b,
                lookback=30,
                entry_z=1.5,
                exit_z=0.5,
                leg_weight=0.25,
            )
        ],
        cost_stack=CostStack(),  # zero cost: the claim under test is about EDGE
        allocator=ConstantSplitAllocator(),
        starting_cash=STARTING_CASH,
    )
    return (result.final_nav - STARTING_CASH) / STARTING_CASH, len(result.fills)


def test_multiplicity_top_n_on_pure_noise_has_no_oos_edge(tmp_path):
    registry = TrialRegistry(tmp_path / "trials.sqlite")
    oos_returns = []
    total_fills = 0

    for seed in (11, 23, 37):
        universe = _noise_universe(seed)
        window = next(iter(walk_forward_windows(universe, train_size=TRAIN, test_size=TEST)))
        selection = select_pairs(window.train_views, top_n=10)
        assert selection.n_pairs_tested == 19_900  # C(200, 2)

        registry.add_trial(
            trial_id=f"noise-universe-{seed}",
            config={"selector": "gatev_top_n", "top_n": 10},
            params={"n_pairs_tested": selection.n_pairs_tested},  # D29: multiplicity IS logged
            metrics={},
            snapshot_id=f"synthetic-noise-{seed}",
            seed=seed,
        )
        for a, b in selection.ranked_pairs:
            ret, fills = _trade_pair_oos(window.test_bars_by_instrument, a, b)
            oos_returns.append(ret)
            total_fills += fills

    # The gate can't pass vacuously: the selected pairs really traded OOS.
    assert total_fills > 20

    # OOS edge ~ 0 within CI: 30 pair-returns (3 seeds x top 10), mean within 2.5
    # standard errors of 0, plus an absolute sanity bound.
    mean = float(np.mean(oos_returns))
    stderr = float(np.std(oos_returns, ddof=1)) / math.sqrt(len(oos_returns))
    assert abs(mean) <= 2.5 * stderr, f"selected noise pairs 'found' OOS edge: {mean:+.4%} ± {stderr:.4%}"
    assert abs(mean) < 0.02

    # And the multiplicity count is readable back out of the registry (D20/D29).
    trial = registry.get_trial("noise-universe-11")
    assert trial.params["n_pairs_tested"] == 19_900


def test_zero_edge_synthetic_cointegrated_pairs_earn_nothing():
    # D23: if this profits, stop everything.
    returns, total_fills = [], 0
    for seed in range(40):
        pair = cointegrated_looking_pair(seed=seed, n_bars=300)
        ret, fills = _trade_pair_oos(pair, "A", "B")
        returns.append(ret)
        total_fills += fills

    assert total_fills > 100  # genuinely traded, not vacuous

    mean = float(np.mean(returns))
    stderr = float(np.std(returns, ddof=1)) / math.sqrt(len(returns))
    assert abs(mean) <= 2.5 * stderr, f"STOP EVERYTHING: zero-edge nulls 'profited' {mean:+.4%} ± {stderr:.4%}"
    assert abs(mean) < 0.02

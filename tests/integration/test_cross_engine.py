"""Cross-engine reconciliation (D41, D79): our engine vs vectorbt on identical
inputs — same close series (committed XLE fixture), same precomputed MA(10)/MA(30)
target-weight schedule, same proportional fee, fractional shares both sides.

The precomputed-weights design isolates ENGINE MECHANICS (sizing, fills, fees,
accounting) from signal code: both engines consume the identical target series, so
any divergence is a simulator disagreement, not a strategy one. Conventions matched
and the reconciliation table live in docs/verification/cross_engine_reconciliation.md.

This test runs in the normal offline suite, so D41's "re-run on every
simulator-touching change" is automatic rather than a policy anyone must remember.
"""

import importlib.util
import sys
import warnings
from pathlib import Path

import pytest

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.csv_fixture import load_fixture_csv
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.instruments.equity import Equity

TOLERANCE = 1e-6  # D47
REPO = Path(__file__).resolve().parent.parent.parent
FIXTURE = REPO / "data" / "fixtures" / "xle_xop_daily_2015_2024.csv"
RUNNER = REPO / "scripts" / "run_cross_engine_residuals.py"


def _ma_cross_weights(closes: list[float]) -> list[float]:
    """The schedule both engines consume, loaded from the extractor that writes the artifact
    `docs/figures/cross-engine-agreement.svg` is drawn from.

    It used to be defined here. Two copies of the schedule would mean that the day one drifted,
    this test and that figure would describe different reconciliations and both would still pass
    — so the definition lives in `scripts/run_cross_engine_residuals.py` and this loads it, using
    the `tests/unit/test_readme_counts_are_current.py:32` idiom (a script is not an importable
    package).
    """
    spec = importlib.util.spec_from_file_location("run_cross_engine_residuals", RUNNER)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module._ma_cross_weights(closes)


def test_equity_curves_reconcile_with_vectorbt():
    vbt = pytest.importorskip("vectorbt")
    import pandas as pd

    warnings.filterwarnings("ignore")
    bars = load_fixture_csv(FIXTURE)["XLE"]
    closes = [tb.bar.close for tb in bars]
    weights = _ma_cross_weights(closes)

    ours = run_backtest(
        bars_by_instrument={"XLE": bars},
        instruments={"XLE": Equity(symbol="XLE", quantity_precision=8)},  # fractional both sides
        strategies=[ScheduledWeightStrategy(strategy_id="ma", weights_by_instrument={"XLE": weights})],
        cost_stack=CostStack(trade_bricks=(PercentOfNotionalSpread(bps=5.0),)),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )
    our_curve = [nav for _, nav in ours.equity_curve]

    close_s = pd.Series(closes)
    pf = vbt.Portfolio.from_orders(
        close_s,
        size=pd.Series(weights),
        size_type="targetpercent",
        fees=0.0005,  # == PercentOfNotionalSpread(bps=5.0)
        init_cash=100_000,
        price=close_s,
    )
    their_curve = list(pf.value())

    assert len(our_curve) == len(their_curve)
    # Same number of trades — the engines agreed on every single re-size decision.
    assert len(ours.fills) == int(pf.orders.count())
    # Full curves tie within D47 tolerance (observed: 1.3e-12 relative — float noise).
    for ours_nav, theirs_nav in zip(our_curve, their_curve):
        assert ours_nav == pytest.approx(theirs_nav, rel=TOLERANCE)

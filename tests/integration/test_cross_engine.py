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


def _ma_cross_weights(closes: list[float], fast: int = 10, slow: int = 30, weight: float = 0.6) -> list[float]:
    """Computed ONCE; consumed by both engines. Weight 0.6 (not 1.0) deliberately:
    at ~full investment vectorbt reserves fees from the purchase while we pay fees
    from cash — below that boundary the sizing conventions are identical (D79)."""
    weights = []
    for i in range(len(closes)):
        if i + 1 < slow:
            weights.append(0.0)
        else:
            f = sum(closes[i - fast + 1 : i + 1]) / fast
            s = sum(closes[i - slow + 1 : i + 1]) / slow
            weights.append(weight if f > s else 0.0)
    return weights


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

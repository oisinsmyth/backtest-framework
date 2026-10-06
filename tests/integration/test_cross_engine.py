"""Cross-engine reconciliation: this engine against vectorbt on identical inputs.

Both engines get the same close series (the bundled XLE fixture), the same precomputed
MA(10)/MA(30) target-weight schedule, the same proportional fee, and fractional shares.

Feeding both engines one precomputed weight schedule isolates the engine mechanics (sizing,
fills, fees, accounting) from signal code: any divergence is a simulator disagreement, not a
strategy one. Conventions matched and the reconciliation table are in docs/VALIDATION.md.

The test runs in the normal offline suite, so every change that touches the simulator is
reconciled again automatically.
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

TOLERANCE = 1e-6
REPO = Path(__file__).resolve().parent.parent.parent
FIXTURE = REPO / "data" / "fixtures" / "xle_xop_daily_2015_2024.csv"


def _ma_cross_weights(
    closes: list[float], fast: int = 10, slow: int = 30, weight: float = 0.6
) -> list[float]:
    """The schedule both engines consume, computed once.

    Weight 0.6 rather than 1.0 on purpose: at close to full investment vectorbt reserves fees
    from the purchase while this engine pays fees from cash. Below that boundary the two sizing
    conventions are identical.
    """
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
    # Same number of trades: the engines agreed on every re-size decision.
    assert len(ours.fills) == int(pf.orders.count())
    # Full curves tie within tolerance (observed: 1.3e-12 relative, float noise).
    for ours_nav, theirs_nav in zip(our_curve, their_curve):
        assert ours_nav == pytest.approx(theirs_nav, rel=TOLERANCE)

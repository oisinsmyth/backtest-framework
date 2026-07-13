"""Step 3's "refactor regression" gate (VERIFICATION_SCHEME.md): a golden-master
backtest that must reproduce its equity curve through CostStack + Instrument + the
signal->target->order pipeline. Hand-worked arithmetic lives in
test_step3_refactor_regression.hand.txt, next to this file, per D39.

There is no pre-refactor engine in this project to regress against (see D53) — this
scenario is instead the *first* golden master for the new architecture: the frozen
baseline any future refactor of these three components must reproduce.

The `run_mini_backtest` helper below is a minimal, test-only harness that wires together
Sizer, CostStack, and Equity over a handful of bars. It is NOT the production engine —
there is no Portfolio/broker class in src/ yet. Building that generally is Step 4
(structural guards) and beyond; this harness exists only to prove Step 3's three
components compose correctly end to end, scoped no wider than that.
"""

from dataclasses import dataclass
from datetime import datetime

import pytest

from backtest_framework.costs.bricks import FlatCommission, FlatRateCarry, PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.instruments.equity import Equity
from backtest_framework.pipeline.sizing import Sizer, TargetWeight

TOLERANCE = 1e-6  # D47

AAPL = Equity(symbol="AAPL")
COST_STACK = CostStack(
    trade_bricks=(FlatCommission(amount=1.00), PercentOfNotionalSpread(bps=5.0)),
    carry_bricks=(FlatRateCarry(annual_rate=0.06),),
)


@dataclass
class _BarResult:
    timestamp: datetime
    quantity: float
    cash: float
    nav: float


def run_mini_backtest(bars: list[tuple[datetime, float, float]], starting_cash: float) -> list[_BarResult]:
    """bars: list of (timestamp, price, target_weight). Single strategy, single
    instrument, capital fixed at starting_cash (capital allocation is D31/Step 4's job;
    this harness just takes a number)."""
    sizer = Sizer()
    cash = starting_cash
    quantity = 0.0
    prev_timestamp: datetime | None = None
    results: list[_BarResult] = []

    for timestamp, price, target_weight in bars:
        # 1. Carry accrues on the position held coming into this bar, over the gap
        #    since the previous bar (D33) — before any trade on this bar is applied.
        if prev_timestamp is not None and quantity != 0:
            base_amount = quantity * price  # marked at the (unchanged) price
            carry = COST_STACK.carry_cost(base_amount, prev_timestamp, timestamp)
            cash -= carry

        # 2. Size this bar's target weight into a desired quantity, via the pipeline
        #    (D27) — target weight -> desired quantity -> order.
        target = TargetWeight(strategy_id="s1", instrument_id="AAPL", weight=target_weight)
        desired_qty = sizer.desired_quantity(target, capital=starting_cash, price=price, instrument=AAPL)
        delta = desired_qty - quantity

        if delta != 0:
            trade_cost = COST_STACK.trade_cost(AAPL, delta, price)
            cash -= delta * price  # buy: delta>0 spends cash; sell: delta<0 returns cash
            cash -= trade_cost
            quantity = desired_qty

        nav = cash + quantity * price
        results.append(_BarResult(timestamp=timestamp, quantity=quantity, cash=cash, nav=nav))
        prev_timestamp = timestamp

    return results


def test_step3_golden_master_equity_curve():
    bars = [
        (datetime(2026, 7, 10, 16, 0), 100.0, 0.5),  # Friday: enter, buy 500
        (datetime(2026, 7, 13, 16, 0), 100.0, 0.5),  # Monday (+3d): hold, no trade
        (datetime(2026, 7, 14, 16, 0), 100.0, 0.0),  # Tuesday (+1d): exit, sell 500
    ]
    results = run_mini_backtest(bars, starting_cash=100_000.0)

    bar0, bar1, bar2 = results

    assert bar0.quantity == 500.0
    assert bar0.cash == pytest.approx(49_974.00, rel=TOLERANCE)
    assert bar0.nav == pytest.approx(99_974.00, rel=TOLERANCE)

    assert bar1.quantity == 500.0  # unchanged: already at target, D27 no-churn
    assert bar1.nav == pytest.approx(99_949.342465753425, rel=TOLERANCE)

    assert bar2.quantity == 0.0
    assert bar2.nav == pytest.approx(99_915.123287671244, rel=TOLERANCE)

    # Cross-check independent of the step-by-step arithmetic: price never moved, so NAV
    # change must equal exactly minus the total costs incurred.
    total_costs = (
        26.00  # entry fee
        + 24.657534246575342  # carry over the 3-day gap
        + 8.219178082191781  # carry over the 1-day gap
        + 26.00  # exit fee
    )
    assert bar2.nav - 100_000.0 == pytest.approx(-total_costs, rel=TOLERANCE)

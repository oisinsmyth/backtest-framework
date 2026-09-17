"""Integration tests for the cost-multiplier sweep (D8, D68) on a synthetic
scenario — fast, exact, offline. The real-fixture half of the Step 6 gates lives in
test_first_result_e2e.py.

Scenario: one round trip (in at bar 0, out at bar 2) at constant price with a flat
$10 commission as the only cost. Two fills per run, so net P&L = −2 × 10 × multiplier
exactly — monotonicity and 0×-equals-zero-cost are checkable to the penny, not just
directionally.
"""

from datetime import datetime

import pytest

from backtest_framework.analytics.metrics import max_drawdown  # D80's home for it
from backtest_framework.costs.bricks import FlatCommission, PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.dataview import MissingVolumeError
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.engine.sweep import run_cost_sweep
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.breakout import (
    BreakoutStrategy,
    FixedWeight,
    VolumeConfirmationFilter,
)

TOLERANCE = 1e-6  # D47


def _bar(price: float) -> Bar:
    return Bar(open=price, high=price, low=price, close=price)


BARS = {
    "AAPL": [
        TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0)),
        TimestampedBar(datetime(2026, 7, 13, 16, 0), _bar(100.0)),
        TimestampedBar(datetime(2026, 7, 14, 16, 0), _bar(100.0)),
    ]
}
INSTRUMENTS = {"AAPL": Equity(symbol="AAPL")}
BASE_STACK = CostStack(trade_bricks=(FlatCommission(amount=10.0),))


def _make_strategies():
    return [ScheduledWeightStrategy(strategy_id="s1", weights_by_instrument={"AAPL": [0.5, 0.5, 0.0]})]


def _sweep(multipliers):
    return run_cost_sweep(
        bars_by_instrument=BARS,
        instruments=INSTRUMENTS,
        make_strategies=_make_strategies,
        base_cost_stack=BASE_STACK,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        multipliers=multipliers,
    )


def test_net_pnl_is_monotonically_non_increasing_in_the_multiplier():
    sweep = _sweep((0.0, 0.5, 1.0, 2.0, 4.0))
    pnls = [pnl for _, pnl in sweep.net_pnls()]

    assert all(later <= earlier + TOLERANCE for earlier, later in zip(pnls, pnls[1:]))
    # And exactly: two $10 fills per run, scaled.
    assert pnls == pytest.approx([0.0, -10.0, -20.0, -40.0, -80.0], abs=TOLERANCE)


def test_zero_multiplier_run_equals_an_empty_cost_stack_run():
    sweep = _sweep((0.0,))
    zero_cost_result = run_backtest(
        bars_by_instrument=BARS,
        instruments=INSTRUMENTS,
        strategies=_make_strategies(),
        cost_stack=CostStack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )

    sweep_navs = [nav for _, nav in sweep.runs[0].result.equity_curve]
    zero_navs = [nav for _, nav in zero_cost_result.equity_curve]
    assert sweep_navs == pytest.approx(zero_navs, rel=TOLERANCE)


def test_sweep_builds_fresh_strategies_per_run():
    calls = 0

    def counting_factory():
        nonlocal calls
        calls += 1
        return _make_strategies()

    run_cost_sweep(
        bars_by_instrument=BARS,
        instruments=INSTRUMENTS,
        make_strategies=counting_factory,
        base_cost_stack=BASE_STACK,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        multipliers=(0.0, 1.0, 2.0),
    )
    assert calls == 3  # one fresh strategy list per multiplier — no state leaks (D68)


# --------------------------------------------------------------------------------
# The strategy the sweep could NOT sweep.
#
# run_cost_sweep forwarded neither `volumes_by_instrument` nor `fill_timing`, so a
# BreakoutStrategy carrying a VolumeConfirmationFilter — which needs both — could not
# be swept at all: it raised MissingVolumeError before the first multiplier finished.
# The scenario is the volume-confirmation golden master's (tests/golden/
# test_volume_confirmation_golden.py), reused deliberately so the 1.0x run has a
# hand-computed NAV to land on rather than a number this codebase produced.
# --------------------------------------------------------------------------------

BREAKOUT_SYMBOL = "BTC-TEST"
BREAKOUT_DAYS = [datetime(2021, 1, day) for day in range(1, 12)]
BREAKOUT_OHLC = [
    (100, 102, 98, 100), (100, 102, 98, 100), (100, 102, 98, 100),
    (100, 120, 99, 125), (125, 126, 100, 100), (100, 112, 95, 94),
    (94, 96, 90, 92), (92, 94, 90, 92), (92, 94, 90, 92),
    (92, 130, 91, 120), (120, 121, 100, 115),
]
BREAKOUT_VOLUMES = [100.0, 100.0, 100.0, 500.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]
BREAKOUT_BARS = {
    BREAKOUT_SYMBOL: [
        TimestampedBar(day, Bar(open=o, high=h, low=lo, close=c))
        for day, (o, h, lo, c) in zip(BREAKOUT_DAYS, BREAKOUT_OHLC)
    ]
}
BREAKOUT_INSTRUMENTS = {BREAKOUT_SYMBOL: Equity(symbol=BREAKOUT_SYMBOL, quantity_precision=8)}


def _make_breakout_strategies():
    return [
        BreakoutStrategy(
            strategy_id="breakout",
            instrument_id=BREAKOUT_SYMBOL,
            n_entry=3,
            n_exit=2,
            weight_source=FixedWeight(1.0),
            filters=(VolumeConfirmationFilter(multiple=1.5, window=3),),
        )
    ]


def _breakout_sweep(multipliers, volumes=BREAKOUT_VOLUMES, fill_timing="next_open"):
    return run_cost_sweep(
        bars_by_instrument=BREAKOUT_BARS,
        instruments=BREAKOUT_INSTRUMENTS,
        make_strategies=_make_breakout_strategies,
        base_cost_stack=CostStack(trade_bricks=[PercentOfNotionalSpread(bps=40)]),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        multipliers=multipliers,
        fill_timing=fill_timing,
        volumes_by_instrument=None if volumes is None else {BREAKOUT_SYMBOL: volumes},
    )


def test_sweep_can_sweep_a_volume_and_next_open_strategy():
    sweep = _breakout_sweep((0.0, 1.0, 2.0))

    # The 1.0x run must reproduce the volume-confirmation golden master exactly: three
    # fills, 700.896 of cost, final NAV 74,523.104. If the sweep were quietly dropping
    # fill_timing the fills would land at closes and none of these would hold.
    base = sweep.runs[1].result
    assert len(base.fills) == 3
    assert sum(f[4] for f in base.fills) == pytest.approx(700.896, abs=TOLERANCE)
    assert base.final_nav == pytest.approx(74_523.104, abs=TOLERANCE)

    # And the volume filter is live inside the sweep: bar 9's trigger is rejected, so
    # no fill lands on bar 10 in ANY of the three runs.
    for run in sweep.runs:
        assert BREAKOUT_DAYS[10] not in [f[0] for f in run.result.fills]

    pnls = [pnl for _, pnl in sweep.net_pnls()]
    assert all(later <= earlier + TOLERANCE for earlier, later in zip(pnls, pnls[1:]))


def test_a_sweep_with_no_volumes_raises_rather_than_rejecting_every_entry():
    """D168's state 3, reached through the sweep rather than through run_backtest.

    This does NOT pin the forwarding — it goes green whether or not the sweep forwards
    `volumes_by_instrument`, because both states raise. The forwarding is pinned by
    test_sweep_can_sweep_a_volume_and_next_open_strategy above, which goes red with
    exactly this error when the forward is removed. What this pins is the other half:
    a sweep run with no volume must CRASH, not return three plausible flat books."""
    with pytest.raises(MissingVolumeError, match="require volume"):
        _breakout_sweep((1.0,), volumes=None)


def test_the_forwarded_fill_timing_argument_is_load_bearing_not_decorative():
    """Same shape for fill_timing: dropping it falls back to "close", which fills at
    the signal bar rather than the one after it.

    Read the fill TIMESTAMPS, not the NAV. This scenario has open[t+1] == close[t] on
    every bar, so both modes fill at the same PRICES and land on the same final NAV —
    an assertion on NAV here cannot fire, which is worse than no assertion at all. The
    bar each fill lands on is what actually moves: next_open shifts all three one bar
    later, and the last one (2021-01-07) does not exist in the close-timed book."""
    at_close = _breakout_sweep((1.0,), fill_timing="close").runs[0].result
    at_next_open = _breakout_sweep((1.0,), fill_timing="next_open").runs[0].result

    close_stamps = [f[0] for f in at_close.fills]
    next_open_stamps = [f[0] for f in at_next_open.fills]
    assert close_stamps == [BREAKOUT_DAYS[3], BREAKOUT_DAYS[4], BREAKOUT_DAYS[5]]
    assert next_open_stamps == [BREAKOUT_DAYS[4], BREAKOUT_DAYS[5], BREAKOUT_DAYS[6]]


def test_max_drawdown_arithmetic():
    curve = [(None, 100.0), (None, 110.0), (None, 99.0), (None, 105.0)]
    # Peak 110 -> trough 99: (110-99)/110 = 10%
    assert max_drawdown(curve) == pytest.approx(0.1, rel=TOLERANCE)
    assert max_drawdown([(None, 100.0), (None, 101.0)]) == 0.0

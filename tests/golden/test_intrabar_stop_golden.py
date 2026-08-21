"""THE INTRABAR STOP GOLDEN MASTER (D39, D170): a touched stop and a gapped stop,
side by side, asserted against hand arithmetic.

Ground truth is test_intrabar_stop_golden.hand.txt, worked out from the stated rules
without running this codebase. The two scenarios differ in exactly one thing — whether
bar 2 opens below the stop and trades through it, or opens above it — so the difference
between their final NAVs is attributable to the gap and to nothing else.

That difference is the whole point. A stop at 110 caps the loss at 10 points when the
market trades through it, and at 18 when the market opens past it. An engine that
reported the first number for the second case would be inventing risk control that never
existed, which is exactly what D169 measured happening in the short book.

The strategy here is a deliberate test double rather than BreakoutStrategy: this file
pins the ENGINE's stop semantics, and a real strategy's own entry/exit logic would only
obscure them.
"""

from datetime import datetime
from typing import Mapping

import pytest

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.dataview import DataView
from backtest_framework.instruments.equity import Equity
from backtest_framework.pipeline.sizing import TargetWeight
from backtest_framework.simulator.fills import Bar

TOLERANCE = 1e-6  # D47

SYMBOL = "BTC-TEST"
STOP = 110.0
DAYS = [datetime(2021, 1, day) for day in range(1, 5)]

SHARED = [(100, 102, 98, 100), (100, 102, 98, 100)]
TOUCHED = SHARED + [(105, 115, 104, 112), (112, 113, 111, 112)]
GAPPED = SHARED + [(118, 120, 117, 119), (119, 120, 118, 119)]


class ShortWithStop:
    """Flat on bar 0, then short 50% of capital with a stop at 110, and permanently flat
    once stopped out. The `on_stop_filled` implementation is the point: without it this
    strategy would re-open the same short on the very next bar."""

    def __init__(self) -> None:
        self.strategy_id = "short-with-stop"
        self._stopped = False
        self.stop_calls: list[str] = []

    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]:
        view = views[SYMBOL]
        flat = self._stopped or view.current_index < 1
        return [
            TargetWeight(
                strategy_id=self.strategy_id,
                instrument_id=SYMBOL,
                weight=0.0 if flat else -0.5,
                stop=None if flat else STOP,
            )
        ]

    def on_stop_filled(self, instrument_id: str) -> None:
        self.stop_calls.append(instrument_id)
        self._stopped = True


def _bars(ohlc):
    return [
        TimestampedBar(day, Bar(open=o, high=h, low=lo, close=c))
        for day, (o, h, lo, c) in zip(DAYS, ohlc)
    ]


def _run(ohlc):
    strategy = ShortWithStop()
    result = run_backtest(
        bars_by_instrument={SYMBOL: _bars(ohlc)},
        instruments={SYMBOL: Equity(symbol=SYMBOL, quantity_precision=8)},
        strategies=[strategy],
        cost_stack=CostStack(trade_bricks=[PercentOfNotionalSpread(bps=40)]),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        fill_timing="close",
    )
    return result, strategy


# ------------------------------------------------------- scenario A: touched


def test_a_touched_stop_fills_at_the_stop_price():
    result, strategy = _run(TOUCHED)
    assert len(result.fills) == 2, "expected exactly an entry and a stop, no rebalancing"

    (d_entry, _, q_entry, p_entry, c_entry), (d_stop, _, q_stop, p_stop, c_stop) = result.fills
    assert (d_entry, q_entry, p_entry) == (DAYS[1], pytest.approx(-500.0), pytest.approx(100.0))
    assert c_entry == pytest.approx(200.0, abs=TOLERANCE)

    assert d_stop == DAYS[2]
    assert q_stop == pytest.approx(500.0)
    assert p_stop == pytest.approx(STOP), "bar 2 traded through 110, so the fill IS 110"
    assert c_stop == pytest.approx(220.0, abs=TOLERANCE)

    assert strategy.stop_calls == [SYMBOL]
    assert result.equity_curve[-1][1] == pytest.approx(94_580.0, abs=TOLERANCE)


# -------------------------------------------------------- scenario B: gapped


def test_a_gapped_stop_fills_at_the_open_and_the_loss_is_worse():
    result, strategy = _run(GAPPED)
    assert len(result.fills) == 2

    (_, _, _, p_entry, _), (d_stop, _, q_stop, p_stop, c_stop) = result.fills
    assert p_entry == pytest.approx(100.0)

    assert d_stop == DAYS[2]
    assert q_stop == pytest.approx(500.0)
    assert p_stop == pytest.approx(118.0), (
        "bar 2 OPENED above the stop; the market never traded at 110, so filling there "
        "would invent risk control that did not exist (D10)"
    )
    assert p_stop > STOP
    assert c_stop == pytest.approx(236.0, abs=TOLERANCE)

    assert strategy.stop_calls == [SYMBOL]
    assert result.equity_curve[-1][1] == pytest.approx(90_564.0, abs=TOLERANCE)


def test_the_gap_costs_exactly_what_the_hand_file_says():
    """The one number this whole file exists to protect."""
    touched, _ = _run(TOUCHED)
    gapped, _ = _run(GAPPED)
    difference = touched.equity_curve[-1][1] - gapped.equity_curve[-1][1]
    assert difference == pytest.approx(4_016.0, abs=TOLERANCE)


# ------------------------------------------------- the ordering the result depends on


def test_the_stopped_strategy_issues_no_order_on_the_bar_it_was_stopped():
    """The stop is checked BEFORE the strategy is consulted, so a strategy that
    implements on_stop_filled is already flat when its turn comes. Without that
    ordering this scenario would show a third fill re-opening the short."""
    result, _ = _run(TOUCHED)
    fills_on_stop_bar = [f for f in result.fills if f[0] == DAYS[2]]
    assert len(fills_on_stop_bar) == 1


def test_a_strategy_without_the_callback_still_runs():
    """`on_stop_filled` is optional on the protocol. A strategy that omits it must not
    crash the engine — it will simply re-enter, which is its own problem, not a fault
    of the stop path."""

    class NoCallback(ShortWithStop):
        on_stop_filled = None  # type: ignore[assignment]

        def generate_targets(self, views):
            view = views[SYMBOL]
            flat = view.current_index < 1
            return [
                TargetWeight(
                    strategy_id=self.strategy_id,
                    instrument_id=SYMBOL,
                    weight=0.0 if flat else -0.5,
                    stop=None if flat else STOP,
                )
            ]

    strategy = NoCallback()
    result = run_backtest(
        bars_by_instrument={SYMBOL: _bars(TOUCHED)},
        instruments={SYMBOL: Equity(symbol=SYMBOL, quantity_precision=8)},
        strategies=[strategy],
        cost_stack=CostStack(trade_bricks=[PercentOfNotionalSpread(bps=40)]),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        fill_timing="close",
    )
    assert any(f[3] == pytest.approx(STOP) for f in result.fills)

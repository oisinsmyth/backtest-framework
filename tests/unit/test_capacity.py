"""Unit tests for the capacity study's recording cost stack (D95).

The load-bearing property is TRANSPARENCY: a recording stack must return exactly
what the unwrapped stack returns, call for call — attribution must never perturb
the run it is attributing.
"""

from datetime import datetime

import pytest

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.equity_bricks import (
    BorrowFee,
    DividendFlow,
    IBKRCommission,
    MarginInterest,
)
from backtest_framework.costs.scaling import scaled_cost_stack
from backtest_framework.costs.stack import CostStack
from backtest_framework.instruments.equity import Equity
from backtest_framework.research.capacity import recording_cost_stack

T0 = datetime(2026, 1, 5, 16)
T1 = datetime(2026, 1, 6, 16)
XLE = Equity(symbol="XLE")


def _stack() -> CostStack:
    return CostStack(
        trade_bricks=(IBKRCommission(), PercentOfNotionalSpread(bps=1.0)),
        carry_bricks=(BorrowFee(annual_rate=0.0025),),
        portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),),
        event_flow_bricks=(DividendFlow(dividends_by_symbol={"XLE": ((T1, 0.50),)}),),
    )


def test_recording_stack_is_transparent():
    plain = _stack()
    recorded, _ = recording_cost_stack(_stack())
    assert recorded.trade_cost(XLE, 500, 80.0) == plain.trade_cost(XLE, 500, 80.0)
    assert recorded.carry_cost(-40_000.0, T0, T1) == plain.carry_cost(-40_000.0, T0, T1)
    assert recorded.portfolio_carry_cost(25_000.0, T0, T1) == plain.portfolio_carry_cost(25_000.0, T0, T1)
    assert recorded.event_flow(XLE, 500, T0, T1) == plain.event_flow(XLE, 500, T0, T1)


def test_ledger_totals_match_hand_arithmetic():
    recorded, ledger = recording_cost_stack(_stack())

    # Trade: 500 sh @ $80. IBKR = max(0.005*500, 1.00) = 2.50 (cap 1%*40,000 = 400).
    # Spread = 1bp * 40,000 = 4.00.
    recorded.trade_cost(XLE, 500, 80.0)
    assert ledger.totals["IBKRCommission"] == pytest.approx(2.50)
    assert ledger.totals["PercentOfNotionalSpread"] == pytest.approx(4.00)

    # Borrow: short 40,000 for 1 day at 25bps ACT/365 = 40,000 * 0.0025 / 365.
    recorded.carry_cost(-40_000.0, T0, T1)
    assert ledger.totals["BorrowFee"] == pytest.approx(40_000 * 0.0025 / 365)

    # Margin: 25,000 borrowed for 1 day at 6% ACT/365.
    recorded.portfolio_carry_cost(25_000.0, T0, T1)
    assert ledger.totals["MarginInterest"] == pytest.approx(25_000 * 0.06 / 365)

    # Totals ACCUMULATE across calls (second trade adds on top).
    recorded.trade_cost(XLE, 500, 80.0)
    assert ledger.totals["IBKRCommission"] == pytest.approx(5.00)


def test_ledger_tracks_max_abs_quantity_per_symbol():
    recorded, ledger = recording_cost_stack(_stack())
    recorded.trade_cost(XLE, 500, 80.0)
    recorded.trade_cost(XLE, -1200, 80.0)  # a bigger SELL — abs matters
    recorded.trade_cost(XLE, 300, 80.0)
    assert ledger.max_quantity_by_symbol == {"XLE": 1200.0}


def test_event_flows_are_not_recorded():
    # Dividends are transfers, not frictions — the ledger must not count them
    # (the same boundary costs/scaling.py draws, D75).
    recorded, ledger = recording_cost_stack(_stack())
    flow = recorded.event_flow(XLE, 500, T0, T1)
    assert flow == pytest.approx(250.0)  # the flow itself still happens
    assert ledger.totals == {}


def test_recorder_composes_with_the_multiplier_sweep_at_1x():
    # run_pairs_study wraps base_stack with scaled_cost_stack(_, 1.0); the ledger
    # must still see every charge through that wrapper.
    recorded, ledger = recording_cost_stack(_stack())
    swept = scaled_cost_stack(recorded, 1.0)
    plain_total = _stack().trade_cost(XLE, 500, 80.0)
    assert swept.trade_cost(XLE, 500, 80.0) == pytest.approx(plain_total)
    assert ledger.totals["IBKRCommission"] == pytest.approx(2.50)

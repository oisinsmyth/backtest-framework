"""THE crypto-pairs golden master (D39, D77, D122-D124).

Asserts the six-bar scenario worked out line by line in the adjacent
`test_crypto_pairs_golden.hand.txt` — every fill, every fee, the single borrow charge,
the single portfolio margin charge, and the resulting NAV, all computed by hand from the
stated rules before this file was written.

The breakout golden master already pins next-open fill timing for a long-or-flat,
unlevered, fee-only book. This one pins the axes a PAIRS book adds and that one cannot
reach: two legs filling per decision, `BorrowFee` charging the short leg and only the
short leg, `MarginInterest` charging a portfolio-level base the engine computes from
gross exposure above NAV, and the constant-gross re-normalization that produces interior
fills as NAV moves.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.instruments.equity import Equity
from backtest_framework.research.breakout_study import CostTier
from backtest_framework.research.crypto_pairs_study import (
    build_pair_cost_stack,
    pair_cost_stack_config,
)
from backtest_framework.simulator.fills import Bar
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy

MONEY = 1e-6  # D47's stated reconciliation tolerance
EPOCH = datetime(2021, 1, 1)

# See the .hand.txt "BARS" block. AAA's closes are 100 x 1.25^t; its OPENS gap away
# from the prior close at t=4 and t=5 so next-open fill timing is visible.
AAA = [
    Bar(open=100.0, high=105.0, low=95.0, close=100.0),
    Bar(open=100.0, high=130.0, low=98.0, close=125.0),
    Bar(open=125.0, high=160.0, low=120.0, close=156.25),
    Bar(open=156.25, high=200.0, low=150.0, close=195.3125),
    Bar(open=200.0, high=260.0, low=195.0, close=244.140625),
    Bar(open=250.0, high=330.0, low=245.0, close=305.17578125),
]
BBB = [Bar(open=100.0, high=100.0, low=100.0, close=100.0) for _ in AAA]

GOLDEN_TIER = CostTier("golden_40bp", 40.0, "taker")
GOLDEN_RATE = 0.365
"""0.365/365 = 0.001 per calendar day exactly — chosen so the carry arithmetic is
hand-checkable, not because it is the study's rate (that is 10%/yr, D124)."""

EXPECTED_EQUITY = [
    100_000.0,
    100_000.0,
    100_000.0,
    100_000.0,
    76_590.40,
    55_621.88587840,
]
EXPECTED_FILLS = [
    (4, "AAA", -512.0, 200.0, 409.60),
    (4, "BBB", 1000.0, 100.0, 400.00),
    (5, "AAA", 198.2857216, 250.0, 198.2857216),
    (5, "BBB", -234.096, 100.0, 93.6384),
]


def _series(bars):
    return [TimestampedBar(EPOCH + timedelta(days=i), bar) for i, bar in enumerate(bars)]


@pytest.fixture(scope="module")
def golden():
    stack_config = pair_cost_stack_config(GOLDEN_TIER, GOLDEN_RATE, GOLDEN_RATE)
    return run_backtest(
        bars_by_instrument={"AAA": _series(AAA), "BBB": _series(BBB)},
        instruments={
            "AAA": Equity(symbol="AAA", quantity_precision=8),
            "BBB": Equity(symbol="BBB", quantity_precision=8),
        },
        strategies=[
            ZScorePairsStrategy(
                strategy_id="pair-AAA-BBB",
                instrument_a="AAA",
                instrument_b="BBB",
                lookback=3,
                entry_z=1.0,
                exit_z=0.5,
                leg_weight=1.0,
            )
        ],
        cost_stack=build_pair_cost_stack(stack_config),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        fill_timing="next_open",
    )


def test_equity_curve_matches_the_hand_computation(golden):
    assert len(golden.equity_curve) == len(EXPECTED_EQUITY)
    for i, ((timestamp, nav), expected) in enumerate(zip(golden.equity_curve, EXPECTED_EQUITY)):
        assert timestamp == EPOCH + timedelta(days=i)
        assert nav == pytest.approx(expected, abs=MONEY), f"bar {i}"


def test_every_fill_matches_the_hand_computation(golden):
    """Four fills, two per decision bar — the two-leg fee bill a long-only study
    cannot show. Prices are bar OPENS, never the closes the signal saw (D103)."""
    assert len(golden.fills) == len(EXPECTED_FILLS)
    for (timestamp, instrument_id, quantity, price, cost), expected in zip(
        sorted(golden.fills, key=lambda f: (f[0], f[1])), EXPECTED_FILLS
    ):
        bar_index, expected_id, expected_qty, expected_price, expected_cost = expected
        assert timestamp == EPOCH + timedelta(days=bar_index)
        assert instrument_id == expected_id
        assert quantity == pytest.approx(expected_qty, abs=1e-8)
        assert price == pytest.approx(expected_price, abs=MONEY)
        assert cost == pytest.approx(expected_cost, abs=MONEY)


def test_nothing_fills_before_the_first_decision_can_reach_an_open(golden):
    """Warm-up is lookback+1 = 4 visible bars, so the first decision is at t=3 and the
    first fill is at t=4's open. A fill at t<=3 would mean the strategy traded on a
    window it did not have."""
    first = min(timestamp for timestamp, *_ in golden.fills)
    assert first == EPOCH + timedelta(days=4)


def test_final_book_matches_the_hand_computation(golden):
    assert golden.final_cash == pytest.approx(74_769.48587840, abs=MONEY)
    assert golden.final_positions["AAA"] == pytest.approx(-313.7142784, abs=1e-8)
    assert golden.final_positions["BBB"] == pytest.approx(765.904, abs=1e-8)
    assert golden.final_nav == pytest.approx(55_621.88587840, abs=MONEY)


def test_borrow_is_charged_on_the_short_leg_and_only_the_short_leg():
    """The shape, isolated from the run: BorrowFee sees each leg's own SIGNED notional
    (D71), so the -156,250 short leg pays 156.25 and the +100,000 long leg pays nothing.
    A long-only study can never exercise this, which is why it is asserted here."""
    stack = build_pair_cost_stack(pair_cost_stack_config(GOLDEN_TIER, GOLDEN_RATE, 0.0))
    one_day = (EPOCH, EPOCH + timedelta(days=1))
    components = Equity(symbol="AAA", quantity_precision=8).carry_components()
    assert stack.carry_cost(-156_250.0, *one_day, components=components) == pytest.approx(
        156.25, abs=MONEY
    )
    assert stack.carry_cost(+100_000.0, *one_day, components=components) == pytest.approx(
        0.0, abs=MONEY
    )


def test_margin_interest_is_charged_on_gross_above_nav_only():
    """D5's base, isolated: 256,250 gross against 45,340.40 of NAV borrows 210,909.60.
    Charging on gross itself — the easy mistake for a ~200%-gross book — would bill
    256.25 instead of 210.90960."""
    stack = build_pair_cost_stack(pair_cost_stack_config(GOLDEN_TIER, 0.0, GOLDEN_RATE))
    base = max(256_250.0 - 45_340.40, 0.0)
    assert base == pytest.approx(210_909.60, abs=MONEY)
    assert stack.portfolio_carry_cost(
        base, EPOCH, EPOCH + timedelta(days=1)
    ) == pytest.approx(210.90960, abs=MONEY)


def test_the_money_reconciles_against_price_pnl_plus_frictions(golden):
    """The identity at the bottom of the hand file: NAV = starting cash + price P&L
    − trade fees − carry. Computed here from the engine's own fill stream and the
    hand file's segment arithmetic, so a change to either side shows up as a break."""
    price_pnl = -42_909.4304  # see "RECONCILIATION" in the .hand.txt
    trade_fees = sum(cost for *_, cost in golden.fills)
    carry = 156.25 + 210.90960
    assert trade_fees == pytest.approx(1_101.52412160, abs=MONEY)
    assert golden.final_nav == pytest.approx(
        100_000.0 + price_pnl - trade_fees - carry, abs=MONEY
    )


def test_the_strategy_stays_short_the_spread_throughout():
    """z is pinned at +2.0 by construction (a steadily trending spread), so the
    strategy enters short and never exits — the study's headline failure mode in six
    bars. If this ever went flat, the z arithmetic in the hand file is wrong."""
    from backtest_framework.engine.dataview import build_data_view

    strategy = ZScorePairsStrategy(
        strategy_id="s", instrument_a="AAA", instrument_b="BBB",
        lookback=3, entry_z=1.0, exit_z=0.5, leg_weight=1.0,
    )
    weights = []
    for i in range(len(AAA)):
        targets = strategy.generate_targets(
            {"AAA": build_data_view(tuple(AAA), i), "BBB": build_data_view(tuple(BBB), i)}
        )
        weights.append((targets[0].weight, targets[1].weight))
    assert weights[:3] == [(0.0, 0.0)] * 3, "warm-up must stand aside"
    assert weights[3:] == [(-1.0, 1.0)] * 3, "z = +2 on every decision bar -> short spread"

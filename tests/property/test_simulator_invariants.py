"""Property-based simulator invariants (D40, D78): across randomized price paths and
weight schedules, whole classes of bugs no example-based test anticipates.

Conventions (D78): hypothesis with derandomize=True — the suite is byte-deterministic
in CI (D34's spirit; hypothesis owns the seeding). Two gate clauses are reinterpreted
for the architecture as built, per D77/D78: "broker.reset()" has no broker to reset —
the equivalent guarantee is that identical runs are identical (fresh state per call);
"fill within [low, high]" is asserted both at the engine level (fills at close of
consistent bars) and on stop_fill_price, the one component that chooses prices.
"""

import hashlib
from datetime import datetime, timedelta

import pytest
from hypothesis import given, settings, strategies as st

from backtest_framework.costs.bricks import FlatCommission, FlatRateCarry
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar, StopSide, stop_fill_price

SETTINGS = settings(derandomize=True, max_examples=60, deadline=None)

INSTRUMENT = {"A": Equity(symbol="A")}


@st.composite
def price_paths(draw, min_bars=3, max_bars=15):
    n = draw(st.integers(min_bars, max_bars))
    moves = draw(st.lists(st.floats(-0.15, 0.15, allow_nan=False), min_size=n, max_size=n))
    prices, p = [], 100.0
    for m in moves:
        p = max(p * (1 + m), 1.0)
        prices.append(round(p, 4))
    return prices


@st.composite
def scenarios(draw, max_weight=0.9):
    prices = draw(price_paths())
    weights = draw(
        st.lists(st.floats(0.0, max_weight, allow_nan=False), min_size=len(prices), max_size=len(prices))
    )
    return prices, weights


def _run(prices, weights, cost_stack):
    start = datetime(2026, 1, 5, 16)
    bars = {
        "A": [TimestampedBar(start + timedelta(days=i), Bar(open=p, high=p, low=p, close=p)) for i, p in enumerate(prices)]
    }
    return run_backtest(
        bars_by_instrument=bars,
        instruments=INSTRUMENT,
        strategies=[ScheduledWeightStrategy(strategy_id="s", weights_by_instrument={"A": weights})],
        cost_stack=cost_stack,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )


@SETTINGS
@given(scenarios())
def test_cash_never_negative_absent_margin(scenario):
    # Long-only weights <= 0.9 leave a 10% cash buffer that dwarfs any flat commission.
    prices, weights = scenario
    result = _run(prices, weights, CostStack(trade_bricks=(FlatCommission(1.0),)))
    assert all(cash >= 0 for _, cash in result.cash_curve)


@SETTINGS
@given(scenarios())
def test_fill_prices_within_their_bars_range(scenario):
    prices, weights = scenario
    result = _run(prices, weights, CostStack())
    bars_by_ts = {}
    start = datetime(2026, 1, 5, 16)
    for i, p in enumerate(prices):
        bars_by_ts[start + timedelta(days=i)] = p
    for ts, _instrument, _qty, fill_price, _cost in result.fills:
        p = bars_by_ts[ts]
        assert p == fill_price  # engine fills at close; close is the bar here


@SETTINGS
@given(
    side=st.sampled_from([StopSide.SELL_STOP, StopSide.BUY_STOP]),
    stop=st.floats(1.0, 200.0, allow_nan=False),
    low=st.floats(1.0, 150.0, allow_nan=False),
    height=st.floats(0.0, 50.0, allow_nan=False),
    open_frac=st.floats(0.0, 1.0, allow_nan=False),
)
def test_stop_fill_price_always_within_low_high(side, stop, low, height, open_frac):
    high = low + height
    bar = Bar(open=low + open_frac * height, high=high, low=low, close=low + height / 2)
    fill = stop_fill_price(side, stop, bar)
    assert fill is None or (bar.low <= fill <= bar.high)


@SETTINGS
@given(scenarios())
def test_fills_reconcile_exactly_to_final_position(scenario):
    prices, weights = scenario
    result = _run(prices, weights, CostStack())
    net = sum(qty for _, _, qty, _, _ in result.fills)
    assert net == result.final_positions.get("A", 0.0)  # exact, not approx


@SETTINGS
@given(scenarios())
def test_no_nav_leaks_zero_cost(scenario):
    # Shadow accountant: with zero costs, NAV change per bar == position x price move,
    # exactly (positions held INTO the bar, since fills happen at this bar's close).
    prices, weights = scenario
    result = _run(prices, weights, CostStack())
    navs = [nav for _, nav in result.equity_curve]
    position = 0.0
    for i in range(1, len(prices)):
        # Holdings over the gap (i-1, i] are whatever was filled up TO AND INCLUDING
        # bar i-1 (fills happen at that bar's close). A fill at bar i itself is
        # NAV-neutral at zero cost (cash down, position up, both marked at the same
        # close), so it doesn't enter this gap's expected change.
        fills_prev = [f for f in result.fills if f[0] == result.equity_curve[i - 1][0]]
        position += sum(f[2] for f in fills_prev)
        expected_change = position * (prices[i] - prices[i - 1])
        actual_change = navs[i] - navs[i - 1]
        assert abs(actual_change - expected_change) < 1e-6


@SETTINGS
@given(scenarios())
def test_no_nav_leaks_flat_commission(scenario):
    # With a flat $10 commission as the only cost, the per-bar identity holds
    # UNCONDITIONALLY on the charged run itself (D104, audit F14 — the old version
    # compared against a zero-cost run and silently skipped whenever commissions
    # shifted the NAV-based sizing): NAV change per bar == position price P&L
    # minus $10 x fills that bar. A fill at the bar's close is NAV-neutral except
    # for its commission.
    prices, weights = scenario
    charged = _run(prices, weights, CostStack(trade_bricks=(FlatCommission(10.0),)))
    navs = [nav for _, nav in charged.equity_curve]
    timestamps = [ts for ts, _ in charged.equity_curve]

    fills_at = {}
    for ts, _, qty, _, _ in charged.fills:
        fills_at.setdefault(ts, []).append(qty)

    assert navs[0] - 100_000.0 == pytest.approx(-10.0 * len(fills_at.get(timestamps[0], [])), abs=1e-6)
    position = sum(fills_at.get(timestamps[0], []))
    for i in range(1, len(prices)):
        expected = position * (prices[i] - prices[i - 1]) - 10.0 * len(fills_at.get(timestamps[i], []))
        assert abs((navs[i] - navs[i - 1]) - expected) < 1e-6
        position += sum(fills_at.get(timestamps[i], []))


@SETTINGS
@given(scenarios())
def test_identical_runs_are_identical(scenario):
    # The "broker.reset()" guarantee, as built (D78): every run constructs fresh
    # state; nothing leaks between calls.
    prices, weights = scenario
    a = _run(prices, weights, CostStack(trade_bricks=(FlatCommission(1.0),)))
    b = _run(prices, weights, CostStack(trade_bricks=(FlatCommission(1.0),)))
    assert a.equity_curve == b.equity_curve
    assert a.fills == b.fills


@SETTINGS
@given(scenarios())
def test_equity_curve_hash_is_deterministic(scenario):
    # D34: identical inputs -> identical equity-curve hash, byte for byte.
    prices, weights = scenario

    def curve_hash(result):
        payload = ",".join(f"{ts.isoformat()}:{nav!r}" for ts, nav in result.equity_curve)
        return hashlib.sha256(payload.encode()).hexdigest()

    assert curve_hash(_run(prices, weights, CostStack())) == curve_hash(_run(prices, weights, CostStack()))


# --- D103/D104 (audit F3/F14): signed positions, real OHLC bars, next_open ------

START = datetime(2026, 1, 5, 16)


@st.composite
def ohlc_scenarios(draw, min_weight=-0.9, max_weight=0.9):
    """Price paths with genuine OHLC structure (open gaps off the previous close,
    high/low bracket both) and SIGNED weights — the audit found the original
    scenarios were long-only flat bars, leaving shorts and opens uncovered."""
    closes = draw(price_paths())
    n = len(closes)
    gaps = draw(st.lists(st.floats(-0.05, 0.05, allow_nan=False), min_size=n, max_size=n))
    weights = draw(
        st.lists(st.floats(min_weight, max_weight, allow_nan=False), min_size=n, max_size=n)
    )
    bars, prev_close = [], closes[0]
    for i, close in enumerate(closes):
        open_ = close if i == 0 else max(prev_close * (1 + gaps[i]), 0.5)
        high = max(open_, close) * 1.01
        low = min(open_, close) * 0.99
        bars.append(Bar(open=round(open_, 4), high=round(high, 4), low=round(low, 4), close=close))
        prev_close = close
    return bars, weights


def _run_bars(bars, weights, cost_stack, fill_timing="close"):
    series = {"A": [TimestampedBar(START + timedelta(days=i), b) for i, b in enumerate(bars)]}
    return run_backtest(
        bars_by_instrument=series,
        instruments=INSTRUMENT,
        strategies=[ScheduledWeightStrategy(strategy_id="s", weights_by_instrument={"A": weights})],
        cost_stack=cost_stack,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        fill_timing=fill_timing,
    )


@SETTINGS
@given(ohlc_scenarios())
def test_fills_reconcile_exactly_with_signed_positions(scenario):
    bars, weights = scenario
    result = _run_bars(bars, weights, CostStack())
    net = sum(qty for _, _, qty, _, _ in result.fills)
    assert net == result.final_positions.get("A", 0.0)  # exact, shorts included


@SETTINGS
@given(ohlc_scenarios())
def test_no_nav_leaks_zero_cost_signed(scenario):
    # The shadow accountant holds for SHORT positions too: with zero costs the only
    # legal NAV change is position x close-to-close move.
    bars, weights = scenario
    result = _run_bars(bars, weights, CostStack())
    closes = [b.close for b in bars]
    navs = [nav for _, nav in result.equity_curve]
    fills_at = {}
    for ts, _, qty, _, _ in result.fills:
        fills_at.setdefault(ts, 0.0)
        fills_at[ts] += qty
    timestamps = [ts for ts, _ in result.equity_curve]
    position = fills_at.get(timestamps[0], 0.0)
    for i in range(1, len(closes)):
        expected = position * (closes[i] - closes[i - 1])
        assert abs((navs[i] - navs[i - 1]) - expected) < 1e-6
        position += fills_at.get(timestamps[i], 0.0)


@SETTINGS
@given(ohlc_scenarios(min_weight=0.0))
def test_next_open_fills_at_the_next_bars_open_only(scenario):
    # D103: in next_open mode every fill lands at its bar's OPEN, never on the
    # first bar (nothing was pending), and the run is deterministic.
    bars, weights = scenario
    result = _run_bars(bars, weights, CostStack(), fill_timing="next_open")
    opens = {START + timedelta(days=i): b.open for i, b in enumerate(bars)}
    for ts, _, _, price, _ in result.fills:
        assert ts != START  # decisions can't fill on the bar that made them
        assert price == opens[ts]
    again = _run_bars(bars, weights, CostStack(), fill_timing="next_open")
    assert again.equity_curve == result.equity_curve and again.fills == result.fills


@SETTINGS
@given(ohlc_scenarios(min_weight=0.0))
def test_next_open_shadow_accountant(scenario):
    # Zero costs, next_open: NAV change per bar == (position held into the bar) x
    # close-to-close move + (quantity filled at this bar's open) x (close - open).
    bars, weights = scenario
    result = _run_bars(bars, weights, CostStack(), fill_timing="next_open")
    closes = [b.close for b in bars]
    opens = [b.open for b in bars]
    navs = [nav for _, nav in result.equity_curve]
    timestamps = [ts for ts, _ in result.equity_curve]
    fills_at = {}
    for ts, _, qty, _, _ in result.fills:
        fills_at.setdefault(ts, 0.0)
        fills_at[ts] += qty
    position = 0.0
    for i in range(1, len(closes)):
        filled_today = fills_at.get(timestamps[i], 0.0)
        expected = position * (closes[i] - closes[i - 1]) + filled_today * (closes[i] - opens[i])
        assert abs((navs[i] - navs[i - 1]) - expected) < 1e-6
        position += filled_today


@SETTINGS
@given(ohlc_scenarios())
def test_no_nav_leaks_with_carry(scenario):
    # FlatRateCarry as the only cost: NAV change per bar == position price P&L
    # minus carry, where carry accrues on the position held into the bar at the
    # CURRENT bar's close (the engine's stated D67 convention), over the 1-day gap.
    bars, weights = scenario
    rate = 0.06
    result = _run_bars(bars, weights, CostStack(carry_bricks=(FlatRateCarry(annual_rate=rate),)))
    closes = [b.close for b in bars]
    navs = [nav for _, nav in result.equity_curve]
    timestamps = [ts for ts, _ in result.equity_curve]
    fills_at = {}
    for ts, _, qty, _, _ in result.fills:
        fills_at.setdefault(ts, 0.0)
        fills_at[ts] += qty
    position = fills_at.get(timestamps[0], 0.0)
    for i in range(1, len(closes)):
        carry = position * closes[i] * rate * 1.0 / 365.0
        expected = position * (closes[i] - closes[i - 1]) - carry
        assert abs((navs[i] - navs[i - 1]) - expected) < 1e-6
        position += fills_at.get(timestamps[i], 0.0)

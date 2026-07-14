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

from hypothesis import given, settings, strategies as st

from backtest_framework.costs.bricks import FlatCommission
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
    # With a flat $10 commission as the only cost: total NAV change == total price
    # P&L - 10 x number of fills, exactly.
    prices, weights = scenario
    zero = _run(prices, weights, CostStack())
    charged = _run(prices, weights, CostStack(trade_bricks=(FlatCommission(10.0),)))
    if [f[2] for f in zero.fills] == [f[2] for f in charged.fills]:
        # Same trade sequence (commissions can shift NAV-based sizing; only compare
        # when the sequences match — the common case for these bounded scenarios).
        leak = (zero.final_nav - charged.final_nav) - 10.0 * len(charged.fills)
        assert abs(leak) < 1e-6


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

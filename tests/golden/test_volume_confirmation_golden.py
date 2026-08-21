"""THE VOLUME-CONFIRMATION GOLDEN MASTER (D39, D168): an 11-bar scenario in which
the price rule fires twice and the volume rule admits exactly one of them.

Ground truth is test_volume_confirmation_golden.hand.txt, worked out from the stated
rules without running this codebase. The scenario is built so that bar 3 and bar 9 are
identical in every respect the strategy cares about EXCEPT volume — both close far above
their own 3-bar high, against the same 100-unit volume baseline, one printing 500 and the
other 100. Any behavioural difference between them is therefore attributable to the
volume rule and to nothing else.

Golden by construction (D77): if the averaging window silently starts including the
trigger bar, or the filter starts being consulted on exits, or a rejected trigger starts
costing money, this test goes red and the hand file is the argument, not the code.
"""

from datetime import datetime

import pytest

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.dataview import MissingVolumeError
from backtest_framework.instruments.equity import Equity
from backtest_framework.research.trade_diagnostics import extract_episodes
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.breakout import (
    BreakoutStrategy,
    FixedWeight,
    VolumeConfirmationFilter,
)

TOLERANCE = 1e-6  # D47

SYMBOL = "BTC-TEST"
DAYS = [datetime(2021, 1, day) for day in range(1, 12)]
OHLC = [
    (100, 102, 98, 100),
    (100, 102, 98, 100),
    (100, 102, 98, 100),
    (100, 120, 99, 125),
    (125, 126, 100, 100),
    (100, 112, 95, 94),
    (94, 96, 90, 92),
    (92, 94, 90, 92),
    (92, 94, 90, 92),
    (92, 130, 91, 120),
    (120, 121, 100, 115),
]
VOLUMES = [100.0, 100.0, 100.0, 500.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0, 100.0]


@pytest.fixture(scope="module")
def bars():
    return [
        TimestampedBar(day, Bar(open=o, high=h, low=lo, close=c))
        for day, (o, h, lo, c) in zip(DAYS, OHLC)
    ]


def _strategy():
    return BreakoutStrategy(
        strategy_id="breakout",
        instrument_id=SYMBOL,
        n_entry=3,
        n_exit=2,
        weight_source=FixedWeight(1.0),
        filters=(VolumeConfirmationFilter(multiple=1.5, window=3),),
    )


def _run(bars, volumes):
    return run_backtest(
        bars_by_instrument={SYMBOL: bars},
        instruments={SYMBOL: Equity(symbol=SYMBOL, quantity_precision=8)},
        strategies=[_strategy()],
        cost_stack=CostStack(trade_bricks=[PercentOfNotionalSpread(bps=40)]),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        fill_timing="next_open",
        volumes_by_instrument=None if volumes is None else {SYMBOL: volumes},
    )


@pytest.fixture(scope="module")
def result(bars):
    return _run(bars, VOLUMES)


# --------------------------------------------------------------- the one fact


def test_the_rejected_trigger_produces_no_fill_and_costs_nothing(result):
    """Bar 9 clears the price rule (close 120 > 3-bar high 96) and fails the volume
    rule (100 is not > 1.5 x 100). The hand file says the book is unchanged across it."""
    fill_timestamps = [f[0] for f in result.fills]
    assert DAYS[10] not in fill_timestamps, (
        "the volume-rejected trigger at bar 9 produced a fill at bar 10"
    )

    curve = [nav for _, nav in result.equity_curve]
    # t=8, t=9, t=10 are all 74,523.104 — flat through the rejected trigger.
    assert curve[8] == pytest.approx(74_523.104, abs=TOLERANCE)
    assert curve[9] == pytest.approx(74_523.104, abs=TOLERANCE)
    assert curve[10] == pytest.approx(74_523.104, abs=TOLERANCE)


def test_the_price_rule_alone_would_have_taken_the_trade(bars):
    """The counterfactual that gives the test above its meaning: with no volume filter,
    the same bars DO produce a second entry. If this ever stops being true the scenario
    has lost its point, because bar 9 would no longer be a trigger at all."""
    unfiltered = BreakoutStrategy(
        strategy_id="breakout",
        instrument_id=SYMBOL,
        n_entry=3,
        n_exit=2,
        weight_source=FixedWeight(1.0),
    )
    result = run_backtest(
        bars_by_instrument={SYMBOL: bars},
        instruments={SYMBOL: Equity(symbol=SYMBOL, quantity_precision=8)},
        strategies=[unfiltered],
        cost_stack=CostStack(trade_bricks=[PercentOfNotionalSpread(bps=40)]),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        fill_timing="next_open",
    )
    assert DAYS[10] in [f[0] for f in result.fills], "bar 9 is no longer a price trigger"


# --------------------------------------------------------------- the full ladder


def test_fills_match_the_hand_arithmetic(result):
    assert len(result.fills) == 3

    (d1, _, q1, p1, c1), (d2, _, q2, p2, c2), (d3, _, q3, p3, c3) = result.fills

    # DAYS[t] is the timestamp of BAR t; bar 4 is 2021-01-05, not 2021-01-04.
    assert (d1, q1, p1) == (DAYS[4], pytest.approx(800.0), pytest.approx(125.0))
    assert c1 == pytest.approx(400.00, abs=TOLERANCE)

    assert (d2, q2, p2) == (DAYS[5], pytest.approx(-4.0), pytest.approx(100.0))
    assert c2 == pytest.approx(1.60, abs=TOLERANCE)

    assert (d3, q3, p3) == (DAYS[6], pytest.approx(-796.0), pytest.approx(94.0))
    assert c3 == pytest.approx(299.296, abs=TOLERANCE)


def test_equity_curve_matches_the_hand_arithmetic(result):
    expected = [
        100_000.0, 100_000.0, 100_000.0, 100_000.0,
        79_600.0, 74_822.40, 74_523.104, 74_523.104,
        74_523.104, 74_523.104, 74_523.104,
    ]
    actual = [nav for _, nav in result.equity_curve]
    assert len(actual) == len(expected)
    for i, (got, want) in enumerate(zip(actual, expected)):
        assert got == pytest.approx(want, abs=TOLERANCE), f"NAV at t={i}"


def test_total_fees_and_final_nav(result):
    assert sum(f[4] for f in result.fills) == pytest.approx(700.896, abs=TOLERANCE)
    assert result.equity_curve[-1][1] == pytest.approx(74_523.104, abs=TOLERANCE)


def test_the_single_episode_matches_the_hand_arithmetic(result, bars):
    episodes = extract_episodes(result, SYMBOL, bars)
    assert len(episodes) == 1
    e = episodes[0]
    assert (e.entry_index, e.exit_index, e.bars_held) == (4, 6, 2)
    assert e.entry_price == pytest.approx(125.0)
    assert e.exit_price == pytest.approx(94.0)
    assert e.n_fills == 3
    assert e.gross_pnl == pytest.approx(-24_776.00, abs=TOLERANCE)
    assert e.costs == pytest.approx(700.896, abs=TOLERANCE)
    assert e.rebalance_costs == pytest.approx(1.60, abs=TOLERANCE)
    assert e.net_pnl == pytest.approx(-25_476.896, abs=TOLERANCE)


# --------------------------------------------------------- the loud-failure state


def test_running_without_volume_fails_loudly_rather_than_rejecting_everything(bars):
    """State 3 (D168), end to end through the engine. Without this the filter would
    silently reject every entry and return a plausible, wrong, entirely flat result —
    which is precisely the failure mode the three-state design exists to prevent."""
    with pytest.raises(MissingVolumeError, match="require volume"):
        _run(bars, None)


def test_nan_volume_is_normalised_on_the_engine_path_too(bars):
    """The NaN->None conversion moved OUT of per-bar view construction and into
    `normalise_volumes`, called once by `run_backtest` (D168) — that was a measured 2x
    speedup, but it means the engine path needs its own test. A NaN that survived here
    would make the filter reject every entry silently.

    Bar 3's volume is the one that admits the only trade; NaN it and the trade must
    vanish, with no exception and no fills at all."""
    volumes = list(VOLUMES)
    volumes[3] = float("nan")
    result = _run(bars, volumes)
    assert result.fills == [], "a NaN trigger volume should reject the entry, not admit it"
    assert result.equity_curve[-1][1] == pytest.approx(100_000.0, abs=TOLERANCE)

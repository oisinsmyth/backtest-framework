"""Property-based invariants for the long-flat breakout strategy (D40, D78, D109).

The headline is the no-look-ahead property: across randomised price paths, perturbing
bars AFTER the decision bar — arbitrarily, including by orders of magnitude — must not
change a single target the strategy produced up to and including that bar. That is the
one failure that would silently invalidate every number in BREAKOUT_RESULTS.md, and an
example-based test cannot cover the shapes that would trigger it.

Conventions (D78): hypothesis with `derandomize=True`, so hypothesis owns the seeding
rather than a hand-rolled seed parameter. **It does NOT mean the same examples every run**
-- since 6.156.6 hypothesis harvests its constant pool from `sys.modules` at test time, so a
full-suite run and a single-file run draw differently from the same seed (D537). A failure
here must be reproduced with the WHOLE suite before it is called a flake.
"""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.dataview import build_data_view
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar
from backtest_framework.strategies.breakout import (
    BreakoutStrategy,
    ConsecutiveCloseFilter,
    FixedWeight,
    InverseVolatilityWeight,
    TrendGateFilter,
    VolatilityContractionFilter,
    VolumeConfirmationFilter,
)

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)
TOLERANCE = 1e-9  # D47
INSTRUMENT = {"X": Equity(symbol="X", quantity_precision=8)}
EPOCH = datetime(2020, 1, 1)

SWEEP = [(20, 5), (20, 20), (30, 10), (40, 10), (55, 5), (55, 20)]


@st.composite
def bar_paths(draw, min_bars=60, max_bars=200):
    n = draw(st.integers(min_bars, max_bars))
    moves = draw(st.lists(st.floats(-0.2, 0.2, allow_nan=False), min_size=n, max_size=n))
    ranges = draw(st.lists(st.floats(0.0, 0.1, allow_nan=False), min_size=n, max_size=n))
    bars, p = [], 100.0
    for move, span in zip(moves, ranges):
        p = max(p * (1.0 + move), 1.0)
        half = p * span / 2.0
        bars.append(Bar(open=p, high=p + half, low=max(p - half, 1e-6), close=p))
    return bars


def _replay(strategy: BreakoutStrategy, bars, up_to: int) -> list[float]:
    return [
        strategy.generate_targets({"X": build_data_view(bars, i)})[0].weight
        for i in range(up_to + 1)
    ]


def _timestamped(bars):
    return [TimestampedBar(EPOCH + timedelta(days=i), bar) for i, bar in enumerate(bars)]


def _make(n_entry: int, n_exit: int, with_filters: bool = False) -> BreakoutStrategy:
    filters = (
        (ConsecutiveCloseFilter(2), VolatilityContractionFilter(threshold=1.0, long_window=40))
        if with_filters
        else ()
    )
    return BreakoutStrategy(
        "s", "X", n_entry=n_entry, n_exit=n_exit,
        weight_source=InverseVolatilityWeight(vol_window=20, rebalance="at_entry"),
        filters=filters,
    )


# ------------------------------------------------------------------- no look-ahead


@SETTINGS
@given(bars=bar_paths(), tail=bar_paths(min_bars=1, max_bars=40), scale=st.floats(0.01, 100.0))
def test_perturbing_future_bars_cannot_change_todays_signal(bars, tail, scale):
    """The property the whole study rests on. Replay to bar i on the original series,
    then replay to bar i on a series whose bars after i have been replaced by
    arbitrary, wildly-scaled ones. The two target sequences must be identical."""
    split = len(bars) // 2
    perturbed = list(bars[: split + 1]) + [
        Bar(open=b.open * scale, high=b.high * scale, low=b.low * scale, close=b.close * scale)
        for b in tail
    ]
    original = _replay(_make(40, 10, with_filters=True), bars, split)
    replayed = _replay(_make(40, 10, with_filters=True), perturbed, split)
    assert original == replayed


def _replay_with_volume(strategy, bars, volumes, up_to: int):
    return [
        strategy.generate_targets({"X": build_data_view(bars, i, volumes=volumes)})[0].weight
        for i in range(up_to + 1)
    ]


def _volume_filtered() -> BreakoutStrategy:
    return BreakoutStrategy(
        "s", "X", n_entry=40, n_exit=10,
        weight_source=InverseVolatilityWeight(vol_window=20, rebalance="at_entry"),
        filters=(VolumeConfirmationFilter(multiple=1.5, window=20),),
    )


def _volume_series(seeds, n: int) -> list[float]:
    """A volume series of exactly `n` entries, cycled from whatever hypothesis gave us.
    The bar count varies per example, so the series is built from it rather than
    generated at a fixed length and hoped to be long enough."""
    return [seeds[i % len(seeds)] for i in range(n)]


@SETTINGS
@given(
    bars=bar_paths(min_bars=80),
    seeds=st.lists(st.floats(1.0, 1e7), min_size=1, max_size=40),
    tail_seeds=st.lists(st.floats(1.0, 1e9), min_size=1, max_size=40),
)
def test_perturbing_future_volumes_cannot_change_todays_signal(bars, seeds, tail_seeds):
    """The single most important test the volume channel adds (D168).

    Volume is a SECOND data channel reaching strategy code, and a second channel is a
    second way to leak the future. The bar channel's guarantee does not extend to it by
    argument — only by the volume tuple being constructed sliced the same way, which is
    exactly what this asserts end to end: replay to bar i, then replay to bar i again on
    a series whose volumes after i are arbitrary and wildly different. The two target
    sequences must be identical."""
    n = len(bars)
    volumes = _volume_series(seeds, n)
    split = n // 2
    tail = _volume_series(tail_seeds, n - split - 1)
    perturbed = volumes[: split + 1] + [v * 1000.0 for v in tail]
    assert len(perturbed) == len(volumes) == n

    original = _replay_with_volume(_volume_filtered(), bars, volumes, split)
    replayed = _replay_with_volume(_volume_filtered(), bars, perturbed, split)
    assert original == replayed


@SETTINGS
@given(
    bars=bar_paths(min_bars=80),
    seeds=st.lists(st.floats(1.0, 1e7), min_size=1, max_size=40),
)
def test_a_volume_filters_decision_is_a_pure_function_of_visible_volumes(bars, seeds):
    """Two views built over the same visible prefix must produce the same verdict, no
    matter what the underlying full series holds beyond it."""
    n = len(bars)
    volumes = _volume_series(seeds, n)
    brick = VolumeConfirmationFilter(multiple=1.5, window=20)
    for i in (25, n // 2, n - 1):
        if i < brick.warm_up_bars(40, 10) or i >= n:
            continue
        short_view = build_data_view(bars[: i + 1], i, volumes=volumes[: i + 1])
        long_view = build_data_view(bars, i, volumes=volumes)
        condition = lambda j: True  # noqa: E731 - the filter's verdict is what is under test
        assert brick.accepts(short_view, condition) == brick.accepts(long_view, condition)


@SETTINGS
@given(bars=bar_paths(min_bars=80), scale=st.floats(0.01, 100.0))
def test_engine_equity_curve_is_unchanged_by_future_bars(bars, scale):
    """Same property one level up: through the real engine, with real costs and
    next-open fills, the equity curve up to the decision bar cannot move when later
    bars change. Catches a leak anywhere in strategy -> sizing -> fills, not only in
    the signal."""
    split = len(bars) - 20
    perturbed = list(bars[:split]) + [
        Bar(open=b.open * scale, high=b.high * scale, low=b.low * scale, close=b.close * scale)
        for b in bars[split:]
    ]
    stack = CostStack(trade_bricks=(PercentOfNotionalSpread(bps=40.0),))

    def run(series):
        return run_backtest(
            bars_by_instrument={"X": _timestamped(series)},
            instruments=INSTRUMENT,
            strategies=[_make(40, 10)],
            cost_stack=stack,
            allocator=ConstantSplitAllocator(),
            starting_cash=100_000.0,
            fill_timing="next_open",
        )

    a, b = run(bars), run(perturbed)
    # Decisions on bar split-1 fill at bar split's OPEN, which is already perturbed —
    # so equality is asserted up to and including bar split-1's close.
    for (ts_a, nav_a), (ts_b, nav_b) in zip(a.equity_curve[:split], b.equity_curve[:split]):
        assert ts_a == ts_b
        assert nav_a == pytest.approx(nav_b, abs=TOLERANCE)


# ---------------------------------------------------------------------- hysteresis


@SETTINGS
@given(bars=bar_paths(), params=st.sampled_from(SWEEP))
def test_entry_and_exit_never_fire_on_the_same_bar(bars, params):
    n_entry, n_exit = params
    s = _make(n_entry, n_exit)
    for i in range(s.warm_up_bars(), len(bars)):
        view = build_data_view(bars, i)
        assert not (s.entry_condition(view, i) and s.exit_condition(view, i))


@SETTINGS
@given(bars=bar_paths(), params=st.sampled_from(SWEEP))
def test_the_strategy_is_long_or_flat_and_never_short(bars, params):
    n_entry, n_exit = params
    s = _make(n_entry, n_exit)
    w = _replay(s, bars, len(bars) - 1)
    assert all(0.0 <= x <= 1.0 for x in w)


@SETTINGS
@given(bars=bar_paths(), params=st.sampled_from(SWEEP))
def test_every_state_change_is_justified_by_its_own_condition(bars, params):
    """No chatter, stated exactly: a flat -> long transition happens only on a bar
    whose close cleared the trailing n_entry-bar high, and a long -> flat transition
    only on a bar whose close broke the trailing n_exit-bar low. A strategy that
    oscillated on noise would violate one of the two."""
    n_entry, n_exit = params
    s = _make(n_entry, n_exit)
    w = _replay(s, bars, len(bars) - 1)
    for i in range(1, len(w)):
        view = build_data_view(bars, i)
        if w[i] > 0 and w[i - 1] == 0:
            assert s.entry_condition(view, i)
        if w[i] == 0 and w[i - 1] > 0:
            assert s.exit_condition(view, i)


@SETTINGS
@given(bars=bar_paths(), params=st.sampled_from(SWEEP))
def test_at_entry_weight_is_constant_within_every_position_episode(bars, params):
    n_entry, n_exit = params
    s = _make(n_entry, n_exit)
    w = _replay(s, bars, len(bars) - 1)
    episode: list[float] = []
    for value in w:
        if value > 0:
            episode.append(value)
        else:
            assert len(set(episode)) <= 1
            episode = []
    assert len(set(episode)) <= 1


@SETTINGS
@given(bars=bar_paths())
def test_replay_is_deterministic(bars):
    a = _replay(_make(40, 10, with_filters=True), bars, len(bars) - 1)
    b = _replay(_make(40, 10, with_filters=True), bars, len(bars) - 1)
    assert a == b


# ------------------------------------------------------------------ cost application


@SETTINGS
@given(bars=bar_paths(min_bars=80), bps=st.sampled_from([0.0, 10.0, 25.0, 40.0]))
def test_trade_costs_are_exactly_the_fee_rate_times_traded_notional(bars, bps):
    """Cost application, asserted against arithmetic rather than against another run:
    every fill's charged cost equals bps/10,000 × |quantity × price|, and the total is
    the sum of those. This is what makes the maker/taker comparison mean anything."""
    stack = CostStack(trade_bricks=(PercentOfNotionalSpread(bps=bps),))
    result = run_backtest(
        bars_by_instrument={"X": _timestamped(bars)},
        instruments=INSTRUMENT,
        strategies=[_make(40, 10)],
        cost_stack=stack,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        fill_timing="next_open",
    )
    for _ts, _instrument, quantity, price, cost in result.fills:
        assert cost == pytest.approx(abs(quantity * price) * bps / 10_000.0, rel=1e-12)
    if bps == 0.0:
        assert all(cost == 0.0 for *_, cost in result.fills)


@SETTINGS
@given(bars=bar_paths(min_bars=80))
def test_higher_fees_never_produce_a_higher_final_nav(bars):
    """Monotonicity in the fee tier — the D8 sweep's gate, applied to this study's
    cost tiers. A violation would mean costs are not being charged where the fills
    happen."""
    navs = []
    for bps in (0.0, 10.0, 25.0, 40.0):
        result = run_backtest(
            bars_by_instrument={"X": _timestamped(bars)},
            instruments=INSTRUMENT,
            strategies=[_make(40, 10, with_filters=False)],
            cost_stack=CostStack(trade_bricks=(PercentOfNotionalSpread(bps=bps),)),
            allocator=ConstantSplitAllocator(),
            starting_cash=100_000.0,
            fill_timing="next_open",
        )
        navs.append(result.final_nav)
    for cheaper, dearer in zip(navs, navs[1:]):
        assert dearer <= cheaper + TOLERANCE


@SETTINGS
@given(bars=bar_paths(min_bars=80))
def test_the_book_is_never_short_through_the_engine(bars):
    result = run_backtest(
        bars_by_instrument={"X": _timestamped(bars)},
        instruments=INSTRUMENT,
        strategies=[_make(40, 10)],
        cost_stack=CostStack(trade_bricks=(PercentOfNotionalSpread(bps=40.0),)),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        fill_timing="next_open",
    )
    position = 0.0
    for _ts, _instrument, quantity, _price, _cost in result.fills:
        position += quantity
        assert position >= -TOLERANCE, "long-flat strategy went short"


@SETTINGS
@given(bars=bar_paths(min_bars=80))
def test_fixed_full_weight_generates_only_negligible_rebalancing_churn(bars):
    """A constant weight of 1.0 means desired quantity = NAV/price, which a fully
    invested book already holds — so the only interior (non-opening, non-closing)
    fills are the vanishing ones chasing the residual left by 8-dp quantity rounding.

    Asserted at `fill_timing="close"`, where the sizing price and the fill price are
    the same number. Under `next_open` (what the study runs) they are not: the target
    is sized on the decision bar's close and filled at the next bar's open, so a
    constant weight arrives slightly off target and is corrected on the following bar.
    That residual turnover is proportional to the close-to-open gap — ~0.06% a day on
    real crypto bars, arbitrarily large on these synthetic paths — which is exactly why
    the buy-and-hold benchmark holds a fixed QUANTITY computed directly rather than a
    fixed weight through the engine (D115)."""
    result = run_backtest(
        bars_by_instrument={"X": _timestamped(bars)},
        instruments=INSTRUMENT,
        strategies=[
            BreakoutStrategy("s", "X", n_entry=40, n_exit=10, weight_source=FixedWeight(1.0))
        ],
        cost_stack=CostStack(),
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
        fill_timing="close",
    )
    position, opening_notional, interior_notional = 0.0, 0.0, 0.0
    for _ts, _instrument, quantity, price, _cost in result.fills:
        was_flat = abs(position) < 1e-12
        position += quantity
        now_flat = abs(position) < 1e-12
        if was_flat:
            opening_notional += abs(quantity * price)
        elif not now_flat:
            interior_notional += abs(quantity * price)
    if opening_notional == 0.0:
        return  # never traded on this path — nothing to assert
    assert interior_notional <= 1e-6 * opening_notional, (
        f"interior rebalancing traded {interior_notional:.6f} of notional against "
        f"{opening_notional:.2f} opened — that is churn, not rounding residue"
    )


@settings(derandomize=True, max_examples=20, deadline=None,
          suppress_health_check=[HealthCheck.large_base_example])
@given(bars=bar_paths(min_bars=260, max_bars=340))
def test_a_filtered_strategy_never_holds_a_position_the_gate_forbids_opening(bars):
    """The trend gate is an ENTRY filter, not a position filter: it may never open a
    position below the SMA, but it is allowed to keep one that later falls below.
    Asserting the entry half is the real invariant; asserting the other half would be
    asserting a bug."""
    gate = TrendGateFilter(sma_window=200)
    s = BreakoutStrategy("s", "X", n_entry=40, n_exit=10, filters=(gate,))
    w = _replay(s, bars, len(bars) - 1)
    for i in range(1, len(w)):
        if w[i] > 0 and w[i - 1] == 0:
            view = build_data_view(bars, i)
            assert gate.accepts(view, lambda j: s.entry_condition(view, j))

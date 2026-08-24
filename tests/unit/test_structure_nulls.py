"""Unit gates for the component placebos (D204, WP3).

The harness decides four verdicts, so the tests that matter are the ones that would catch
it deciding them for the wrong reason:

- the continuation rule resolving in the wrong direction, which would invert every arm at
  once and look like a discovery;
- the band breathing after the touch, which makes the outcome depend on volatility that
  arrived later;
- a placebo that is not actually matched — a displaced gap band of a different width is
  measuring band width and reporting it as imbalance;
- an unavailable level (no gap, no RSI trigger) being touchable, which would silently put
  different populations in the two arms.

`terrain_nulls`' own false-positive check is mandatory because a *null harness* that finds
structure in noise invalidates everything downstream. That check does not transfer here:
these arms are paired, so a harness biased toward finding structure biases BOTH arms and
cancels. What has to be proved instead is that the pairing is real, which is what most of
this file does.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

import numpy as np
import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.structure import Gap, Leg
from backtest_framework.research.structure_nulls import (
    CONTINUATION,
    Reaction,
    continue_from,
    displaced_gap_levels,
    first_gap_in_leg,
    leg_span_levels,
    paired_bootstrap,
    random_window_levels,
    ratio_levels,
    reaction_at,
    touch_and_continue,
)
from backtest_framework.research.structure_setups import Setup
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2020, 1, 1)
TOUCH = 0.5


def series(closes):
    return [
        TimestampedBar(EPOCH + timedelta(minutes=15 * i), Bar(c, c, c, c))
        for i, c in enumerate(closes)
    ], [float(c) for c in closes]


def setup_over(window, direction, leg=None):
    leg = leg or Leg(0, 120.0, 5, 100.0)
    return Setup(
        choch_index=window[0] - 1,
        direction=direction,
        leg=leg,
        ready_index=window[0],
        window=tuple(window),
        holds=tuple(frozenset() for _ in window),
        closed_by="max_hold",
    )


# ------------------------------------------------------------ the continuation rule

def test_a_touch_that_runs_the_setups_way_is_a_continuation():
    # Level 100, ATR 2 -> band 1. Price touches 100 at bar 2, then runs to 104.
    _, closes = series([110, 105, 100, 102, 104, 106])
    atr = [2.0] * len(closes)
    setup = setup_over([1, 2, 3, 4, 5], direction=-1)  # a bearish setup...
    touched, continued = touch_and_continue(closes, atr, setup, 100.0, TOUCH)
    assert touched
    assert not continued, "price ran UP, and this setup is short — that is not continuation"

    long_setup = setup_over([1, 2, 3, 4, 5], direction=1, leg=Leg(0, 90.0, 5, 110.0))
    touched, continued = touch_and_continue(closes, atr, long_setup, 100.0, TOUCH)
    assert touched and continued


def test_the_direction_comes_from_the_setup_not_the_approach():
    """The one difference from `terrain_nulls`' reversal statistic, and the reason the two
    are not interchangeable. A reversal statistic is agnostic about which way price then
    goes; this one is not, because the strategy is not."""
    _, closes = series([110, 105, 100, 98, 96, 94])
    atr = [2.0] * len(closes)
    short = setup_over([1, 2, 3, 4, 5], direction=-1)
    long_ = setup_over([1, 2, 3, 4, 5], direction=1, leg=Leg(0, 90.0, 5, 110.0))
    assert touch_and_continue(closes, atr, short, 100.0, TOUCH) == (True, True)
    assert touch_and_continue(closes, atr, long_, 100.0, TOUCH) == (True, False)


def test_a_level_price_never_reaches_is_never_touched():
    _, closes = series([110, 109, 108, 107, 106, 105])
    atr = [1.0] * len(closes)
    setup = setup_over([1, 2, 3, 4, 5], direction=-1)
    assert touch_and_continue(closes, atr, setup, 50.0, TOUCH) == (False, False)


def test_an_unavailable_level_is_never_touched():
    """C4 and C5 mark a setup with no gap / no trigger as NaN. NaN must be untouchable, or
    the two arms would be running on different populations without anyone noticing."""
    _, closes = series([110, 105, 100, 102, 104, 106])
    atr = [2.0] * len(closes)
    setup = setup_over([1, 2, 3, 4, 5], direction=-1)
    assert touch_and_continue(closes, atr, setup, math.nan, TOUCH) == (False, False)


def test_only_the_first_touch_of_a_window_counts():
    """A price sitting inside the band for an hour is one touch, not four — the same rule
    `terrain_nulls` states, and the reason a level that price hugs does not dominate the
    statistic."""
    _, closes = series([110, 100, 100, 100, 100, 100, 100])
    atr = [2.0] * len(closes)
    setup = setup_over([1, 2, 3, 4, 5, 6], direction=-1)
    touched, continued = touch_and_continue(closes, atr, setup, 100.0, TOUCH)
    assert touched
    assert not continued, "it never resolved either way inside the horizon"


def test_the_band_is_fixed_at_the_touch_and_does_not_breathe():
    """A band recomputed per bar makes the outcome depend on volatility that arrived after
    the decision. Here ATR collapses right after the touch: with a fixed band price has not
    resolved, with a breathing band it would have."""
    _, closes = series([110, 100, 100.4, 100.6, 100.8, 100.9])
    atr = [2.0, 2.0, 0.01, 0.01, 0.01, 0.01]
    setup = setup_over([1, 2, 3, 4, 5], direction=1, leg=Leg(0, 90.0, 5, 110.0))
    touched, continued = touch_and_continue(closes, atr, setup, 100.0, TOUCH)
    assert touched
    assert not continued, (
        "the band is 1.0, fixed at the touch, so the upper edge is 101.0 and price only "
        "reached 100.9. A band recomputed per bar would be 0.005 wide by bar 2 and would "
        "have called this a continuation."
    )


def test_unresolved_within_the_horizon_is_not_a_continuation():
    _, closes = series([110, 100, 100.1, 100.2, 100.1, 100.0, 130.0])
    atr = [2.0] * len(closes)
    setup = setup_over([1, 2, 3, 4, 5, 6], direction=1, leg=Leg(0, 90.0, 5, 110.0))
    # The horizon is 5 bars from the touch at index 1, so the jump at index 6 is inside it.
    assert touch_and_continue(closes, atr, setup, 100.0, TOUCH, horizon=3) == (True, False)
    assert touch_and_continue(closes, atr, setup, 100.0, TOUCH, horizon=5)[1] is True


def test_continue_from_uses_the_same_resolution_rule_as_a_level_touch():
    """C5 fires at a bar rather than a price, so it takes `continue_from`. The two must
    agree when the level IS the bar's close, or C5's row is not comparable with the rest of
    the table."""
    _, closes = series([110, 100, 101, 102, 103, 104])
    atr = [2.0] * len(closes)
    setup = setup_over([1, 2, 3, 4, 5], direction=1, leg=Leg(0, 90.0, 5, 110.0))
    _, via_level = touch_and_continue(closes, atr, setup, closes[1], TOUCH)
    assert continue_from(closes, atr, 1, 1, TOUCH) == via_level


# ------------------------------------------------------------------- matched placebos

def test_leg_span_levels_land_inside_their_own_leg():
    setups = [
        setup_over([1, 2, 3], -1, Leg(0, 120.0, 3, 100.0)),
        setup_over([1, 2, 3], 1, Leg(0, 8_000.0, 3, 9_000.0)),
    ]
    rng = np.random.default_rng(0)
    for _ in range(50):
        for setup, level in zip(setups, leg_span_levels(setups, rng)):
            low = min(setup.leg.start_price, setup.leg.end_price)
            high = max(setup.leg.start_price, setup.leg.end_price)
            assert low <= level <= high


def test_leg_span_levels_are_drawn_per_setup_not_once_for_the_series():
    """The fixture runs from about $3,000 to $100,000. One range applied across it is the
    300x scalar-band error `terrain_strategies` records, in a different costume."""
    small = setup_over([1, 2, 3], -1, Leg(0, 101.0, 3, 100.0))
    large = setup_over([1, 2, 3], -1, Leg(0, 90_000.0, 3, 80_000.0))
    rng = np.random.default_rng(1)
    a, b = leg_span_levels([small, large], rng)
    assert 100.0 <= a <= 101.0
    assert 80_000.0 <= b <= 90_000.0


def test_displaced_gap_levels_preserve_width_and_stay_inside_the_leg():
    """Width matching is the whole design of C4's placebo: a wider band is touched more
    often and resolves more often for reasons that have nothing to do with imbalance."""
    setups = [setup_over([1, 2, 3], -1, Leg(0, 120.0, 3, 100.0))]
    width = 4.0
    rng = np.random.default_rng(0)
    for _ in range(50):
        level = displaced_gap_levels(setups, [110.0], [width], rng)[0]
        assert 100.0 + width / 2 <= level <= 120.0 - width / 2, (
            "the displaced band must fit inside the leg, not hang off its end"
        )


def test_a_setup_with_no_gap_gets_an_untouchable_placebo_too():
    setups = [setup_over([1, 2, 3], -1)]
    rng = np.random.default_rng(0)
    assert math.isnan(displaced_gap_levels(setups, [None], [math.nan], rng)[0])


def test_first_gap_in_leg_takes_the_earliest_matching_gap():
    """'First' rather than 'best'. Choosing among several gaps is exactly the discretion
    the course exercises by eye and exactly what this programme removes."""
    setup = setup_over([12, 13], -1, Leg(2, 120.0, 10, 100.0))
    gaps = [
        Gap(1, 90.0, 92.0, -1),      # before the leg
        Gap(5, 104.0, 108.0, 1),     # wrong direction
        Gap(6, 110.0, 114.0, -1),    # the answer
        Gap(8, 112.0, 118.0, -1),    # later
        Gap(20, 100.0, 102.0, -1),   # after the leg
    ]
    midpoint, width = first_gap_in_leg(setup, gaps)
    assert (midpoint, width) == (112.0, 4.0)


def test_no_gap_in_the_leg_reports_unavailable_rather_than_a_guess():
    setup = setup_over([12, 13], -1, Leg(2, 120.0, 10, 100.0))
    midpoint, width = first_gap_in_leg(setup, [Gap(1, 90.0, 92.0, -1)])
    assert midpoint is None and math.isnan(width)


def test_ratio_levels_walk_each_setups_own_leg():
    setups = [setup_over([1, 2], -1, Leg(0, 120.0, 2, 100.0))]
    assert ratio_levels(setups, 0.0) == [100.0]
    assert ratio_levels(setups, 1.0) == [120.0]
    assert ratio_levels(setups, 0.5) == [110.0]


def test_random_window_levels_are_closes_that_actually_occurred():
    """A price drawn from a range would compare 'a moment RSI chose' against 'a price'.
    Those are not the same kind of thing."""
    _, closes = series([10, 20, 30, 40, 50])
    setups = [setup_over([1, 2, 3], -1)]
    rng = np.random.default_rng(0)
    for _ in range(30):
        assert random_window_levels(closes, setups, rng)[0] in (20.0, 30.0, 40.0)


# --------------------------------------------------------------------- the aggregate

def test_reaction_refuses_arms_that_are_not_paired_setup_by_setup():
    _, closes = series([100] * 5)
    with pytest.raises(ValueError, match="paired"):
        reaction_at(closes, [1.0] * 5, [setup_over([1, 2], -1)], [100.0, 101.0], TOUCH)


def test_a_reaction_with_no_touches_reports_zero_rather_than_nan():
    """Zero sorts last; NaN propagates into a mean and silently poisons the comparison.
    `n_touches` is always reported beside the rate — a rate on four touches is not a rate."""
    empty = Reaction(n_setups=10, n_touches=0, n_continued=0)
    assert empty.p_continuation == 0.0
    assert empty.touch_rate == 0.0


def test_the_declared_tail_is_the_upper_one():
    """The direction IS the hypothesis. The course claims price CONTINUES off these levels,
    so a real level is notable in the upper tail. A silently-chosen tail is how a two-sided
    question gets reported as a one-sided p-value."""
    assert CONTINUATION.direction == "high"


# ---------------------------------------------------------------- the paired bootstrap

def test_identical_arms_produce_exactly_zero_difference_in_every_draw():
    """The pairing, asserted directly: one index vector applied to both arms. If the arms
    were resampled independently this would be noise around zero rather than zero."""
    outcomes = [True, False, True, True, False] * 20
    touched = [True] * len(outcomes)
    out = paired_bootstrap(outcomes, outcomes, touched, touched, n_sims=200, seed=0)
    assert out["mean_difference"] == 0.0
    assert out["p05"] == 0.0 and out["p95"] == 0.0
    assert out["share_not_better"] == 1.0


def test_a_strictly_better_arm_shows_a_positive_difference():
    better = [True] * 100
    worse = [False] * 100
    touched = [True] * 100
    out = paired_bootstrap(better, worse, touched, touched, n_sims=200, seed=0)
    assert out["mean_difference"] == pytest.approx(1.0)
    assert out["share_not_better"] == 0.0


def test_the_bootstrap_is_deterministic_under_its_seed():
    a = [True, False] * 50
    b = [False, True] * 50
    touched = [True] * 100
    first = paired_bootstrap(a, b, touched, touched, n_sims=100, seed=7)
    second = paired_bootstrap(a, b, touched, touched, n_sims=100, seed=7)
    assert first == second
    assert paired_bootstrap(a, b, touched, touched, n_sims=100, seed=8) != first

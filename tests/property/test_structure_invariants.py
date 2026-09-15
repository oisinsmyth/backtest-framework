"""Property-based invariants for the structure detectors (D204, WP1).

`tests/unit/test_structure.py` checks the look-ahead property at four hand-picked indices
on one seed. That is the right shape for a gate and the wrong shape for a guarantee: a
detector can read the future on the bars those four indices happen not to exercise. This
file quantifies over the paths and the index instead.

Conventions (D78): hypothesis with `derandomize=True`, so hypothesis owns the seeding.

**`derandomize=True` no longer implies the same examples in every run, and this file is where
that was discovered.** Hypothesis 6.156.6 injects "local constants" scraped from whatever is in
`sys.modules` when the test executes (`hypothesis/internal/conjecture/providers.py`), so a
full-suite run -- which has imported dozens more project modules by the time it reaches this
file -- draws different floats than `pytest tests/property/test_structure_invariants.py` does.
The gap-midpoint degeneracy below was found by a full run and passed in isolation, which looked
exactly like a flake and was not. **A failure here must be reproduced with the whole suite, not
with this file alone.**

Every invariant here is one a correct detector satisfies by construction. That is the
point — the value is in the ones a *nearly* correct detector does not, and the two that
earned their place by catching mutations are the causality property and the leg-endpoint
property.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from hypothesis import given, settings, strategies as st

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.structure import (
    Event,
    Gap,
    Trend,
    fair_value_gaps,
    market_structure,
    pivots,
    ratio_price,
    retracement,
    rsi,
)
from backtest_framework.research.terrain_swing import SWING_K
from backtest_framework.simulator.fills import Bar

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)
EPOCH = datetime(2020, 1, 1)


@st.composite
def bar_paths(draw, min_bars=80, max_bars=260):
    """Random OHLC paths with consistent bars — high >= max(open, close) and so on.

    Inconsistent bars would fail the detectors for reasons that say nothing about them,
    so consistency is built into the generator rather than filtered for afterwards."""
    n = draw(st.integers(min_bars, max_bars))
    moves = draw(
        st.lists(st.floats(-0.06, 0.06, allow_nan=False), min_size=n, max_size=n)
    )
    wicks = draw(
        st.lists(st.floats(0.0, 0.03, allow_nan=False), min_size=2 * n, max_size=2 * n)
    )
    out, px = [], 100.0
    for i, move in enumerate(moves):
        o = px
        px = max(px * (1.0 + move), 1.0)
        c = px
        h = max(o, c) * (1.0 + wicks[2 * i])
        lo = min(o, c) * (1.0 - wicks[2 * i + 1])
        out.append(TimestampedBar(EPOCH + timedelta(minutes=15 * i), Bar(o, h, lo, c)))
    return out


def corrupt_after(bars, index):
    """Replace everything after `index` with a violently different path.

    Deliberately not a nudge: a detector reading one bar ahead survives a nudge."""
    out = list(bars[: index + 1])
    px = bars[index].bar.close
    for i in range(index + 1, len(bars)):
        px *= 1.7 if (i % 3) else 0.55
        o, c = px, px * 1.02
        out.append(
            TimestampedBar(
                bars[i].timestamp, Bar(o, max(o, c) * 1.05, min(o, c) * 0.95, c)
            )
        )
    return out


@SETTINGS
@given(bars=bar_paths(), k=st.sampled_from(SWING_K), frac=st.floats(0.2, 0.9))
def test_structure_state_depends_only_on_the_past(bars, k, frac):
    """The load-bearing property (D173/D181), quantified over paths and index.

    D173's warning is that this leak is INVISIBLE — the equity curve it produces looks
    entirely plausible — so nothing downstream would ever surface it. This is the only
    thing that would."""
    index = int(frac * (len(bars) - 1))
    assert market_structure(bars, k)[index] == market_structure(corrupt_after(bars, index), k)[index]


@SETTINGS
@given(bars=bar_paths(), frac=st.floats(0.2, 0.9))
def test_gaps_and_rsi_depend_only_on_the_past(bars, frac):
    index = int(frac * (len(bars) - 1))
    corrupted = corrupt_after(bars, index)

    def visible(series):
        return sorted(
            (g.formed_at, g.lo, g.hi, g.direction, g.alive_at(index))
            for g in fair_value_gaps(series)
            if g.formed_at <= index
        )

    assert visible(bars) == visible(corrupted)
    a, b = rsi(bars)[index], rsi(corrupted)[index]
    assert (math.isnan(a) and math.isnan(b)) or a == b


@SETTINGS
@given(bars=bar_paths(), k=st.sampled_from(SWING_K))
def test_an_event_always_leaves_the_trend_it_declares(bars, k):
    """A change of character that does not flip the trend, or a break of structure that
    does not confirm it, is a state machine that has lost track of its own state."""
    expected = {
        Event.BOS_UP: Trend.UP,
        Event.CHOCH_UP: Trend.UP,
        Event.BOS_DOWN: Trend.DOWN,
        Event.CHOCH_DOWN: Trend.DOWN,
    }
    for state in market_structure(bars, k):
        if state.event is not Event.NONE:
            assert state.trend is expected[state.event]


@SETTINGS
@given(bars=bar_paths(), k=st.sampled_from(SWING_K))
def test_a_change_of_character_always_reverses_the_previous_trend(bars, k):
    """By definition it is a *change*. A CHoCH out of `NONE`, or one that fires in the
    direction the trend already ran, is a break of structure mislabelled."""
    states = market_structure(bars, k)
    for prev, cur in zip(states, states[1:]):
        if cur.event is Event.CHOCH_DOWN:
            assert prev.trend is Trend.UP
        elif cur.event is Event.CHOCH_UP:
            assert prev.trend is Trend.DOWN


@SETTINGS
@given(bars=bar_paths(), k=st.sampled_from(SWING_K))
def test_the_flipped_level_is_a_price_the_series_actually_reached(bars, k):
    """C2 is a broken swing, so it must be one of the pivot prices — never an average,
    an interpolation, or a stale value carried across a later change of character."""
    prices = {p.price for p in pivots(bars, k)}
    for state in market_structure(bars, k):
        if state.choch_level is not None:
            assert state.choch_level in prices


@SETTINGS
@given(bars=bar_paths(), k=st.sampled_from(SWING_K))
def test_leg_endpoints_are_confirmed_pivots_of_the_right_sign(bars, k):
    highs = {(p.index, p.price) for p in pivots(bars, k) if p.sign > 0}
    lows = {(p.index, p.price) for p in pivots(bars, k) if p.sign < 0}
    for t, state in enumerate(market_structure(bars, k)):
        leg = state.leg
        if leg is None:
            continue
        assert leg.end_index + k <= t, "a leg cannot end on a pivot that has not confirmed"
        start = (leg.start_index, leg.start_price)
        end = (leg.end_index, leg.end_price)
        if state.choch_direction > 0:
            assert start in lows and end in highs
        else:
            assert start in highs and end in lows


@SETTINGS
@given(bars=bar_paths(), k=st.sampled_from(SWING_K), ratio=st.floats(-0.5, 1.5))
def test_retracement_inverts_ratio_price_on_every_real_leg(bars, k, ratio):
    for state in market_structure(bars, k):
        if state.leg is None:
            continue
        value = retracement(state.leg, ratio_price(state.leg, ratio))
        assert value is not None
        assert math.isclose(value, ratio, rel_tol=1e-9, abs_tol=1e-9)
        break


@SETTINGS
@given(bars=bar_paths())
def test_every_gap_is_a_non_empty_band_that_price_left_behind(bars):
    for gap in fair_value_gaps(bars):
        assert gap.hi > gap.lo
        # NOT a strict inequality, and the weakening is the honest statement rather than a
        # retreat. The band above carries the non-degeneracy claim; this line only claims the
        # midpoint lies inside its own band, and `0.5 * (lo + hi)` on a band one ulp wide
        # rounds ONTO an endpoint. Hypothesis found exactly that -- lo=133.43502175545586,
        # hi=133.4350217554559, band ~4e-14 against a ulp of ~2.84e-14 at that price -- and the
        # detector was right both times. See test_a_one_ulp_band_is_still_a_gap below.
        assert gap.lo <= gap.midpoint <= gap.hi
        assert gap.formed_at >= 2
        if gap.filled_at is not None:
            assert gap.filled_at > gap.formed_at
        first, third = bars[gap.formed_at - 2].bar, bars[gap.formed_at].bar
        if gap.direction > 0:
            assert (gap.lo, gap.hi) == (first.high, third.low)
        else:
            assert (gap.lo, gap.hi) == (third.high, first.low)


def test_a_one_ulp_band_is_still_a_gap():
    """The band that falsified the invariant above, pinned as a fixed example.

    Found by hypothesis on 2026-09-15 in a full-suite run. The band is **exactly one ulp
    wide** at that price, so `0.5 * (lo + hi)` has nowhere to land but an endpoint — the
    midpoint IS the low. Two things follow, and the second is the reason this is a test and
    not a code change:

    * the strict `lo < midpoint < hi` is false, as float arithmetic and not as a defect;
    * the detector is right. `third.low > first.high` held by one ulp, so a gap is what this
      is. **Do not add a minimum-width floor to `fair_value_gaps`** — D205 and the detector's
      own docstring commit it to returning every gap "including the gaps that are obviously
      noise", and filtering by eye is the discretion this programme exists to remove.
    """
    gap = Gap(formed_at=26, lo=133.43502175545586, hi=133.4350217554559, direction=1)

    assert gap.hi > gap.lo
    assert gap.width == math.ulp(gap.lo)
    assert gap.lo <= gap.midpoint <= gap.hi
    assert gap.midpoint == gap.lo, "one ulp leaves the midpoint nowhere else to go"
    assert not (gap.lo < gap.midpoint < gap.hi), (
        "if this ever passes, the strict form above can come back"
    )


@SETTINGS
@given(bars=bar_paths())
def test_a_gap_is_alive_exactly_between_its_formation_and_its_fill(bars):
    for gap in fair_value_gaps(bars):
        assert not gap.alive_at(gap.formed_at - 1)
        assert gap.alive_at(gap.formed_at)
        if gap.filled_at is not None:
            assert gap.alive_at(gap.filled_at - 1)
            assert not gap.alive_at(gap.filled_at)


@SETTINGS
@given(bars=bar_paths())
def test_rsi_stays_inside_its_own_range(bars):
    for value in rsi(bars):
        assert math.isnan(value) or 0.0 <= value <= 100.0

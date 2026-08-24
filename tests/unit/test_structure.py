"""Unit gates for the five structure detectors (D204, WP1).

The load-bearing tests here are the first group. `DataView` (D32/D56) makes look-ahead
structurally impossible for a STRATEGY — the view arrives already sliced, so a future bar
is absent rather than merely forbidden. A detector is analytics, and D181 is the record of
what that distinction costs.

Nothing structural stops `market_structure` consuming a pivot before it confirms. This
file is what does, and D173 is why it matters: the leak would be INVISIBLE, producing an
entirely plausible equity curve.

The second group is the false-positive check. It is deliberately NOT "the detector must
find nothing in noise" — these are geometric detectors and they will find shapes in a
random walk, which is a fact about geometry rather than a bug. What they must not do is
find structure where the *geometry* forbids it: a monotone series has no change of
character, and a flat series has no pivots at all under D173's strict-and-unique rule.
Whether the shapes found in noise differ from the shapes found in real data is WP3's
question, measured against a null, not asserted here.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.structure import (
    CANONICAL_RATIOS,
    PLACEBO_RATIOS,
    RSI_WINDOW,
    Event,
    Leg,
    Trend,
    fair_value_gaps,
    market_structure,
    pivots,
    ratio_price,
    retracement,
    rsi,
)
from backtest_framework.research.terrain_swing import SWING_K, confirmed_pivots
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2020, 1, 1)


def bars_from(closes, highs=None, lows=None, opens=None):
    highs = highs if highs is not None else [c * 1.02 for c in closes]
    lows = lows if lows is not None else [c * 0.98 for c in closes]
    opens = opens if opens is not None else list(closes)
    return [
        TimestampedBar(EPOCH + timedelta(minutes=15 * i), Bar(o, h, lo, c))
        for i, (o, h, lo, c) in enumerate(zip(opens, highs, lows, closes))
    ]


def ohlc(rows):
    """Explicit OHLC rows, for the planted patterns where wicks carry the meaning."""
    return [
        TimestampedBar(EPOCH + timedelta(minutes=15 * i), Bar(o, h, lo, c))
        for i, (o, h, lo, c) in enumerate(rows)
    ]


def wandering(n: int, seed: int, start: float = 100.0) -> list[TimestampedBar]:
    rng = random.Random(seed)
    out, px = [], start
    for i in range(n):
        o = px
        px *= math.exp(rng.gauss(0.0, 0.004))
        c = px
        h = max(o, c) * (1.0 + abs(rng.gauss(0.0, 0.001)))
        lo = min(o, c) * (1.0 - abs(rng.gauss(0.0, 0.001)))
        out.append(TimestampedBar(EPOCH + timedelta(minutes=15 * i), Bar(o, h, lo, c)))
    return out


def corrupted_after(bars, index, seed=99):
    """The same series with every bar after `index` replaced by unrelated noise.

    Not a small perturbation — a detector that reads one bar ahead would survive a nudge
    and must not survive this."""
    rng = random.Random(seed)
    out = list(bars[: index + 1])
    px = bars[index].bar.close
    for i in range(index + 1, len(bars)):
        px *= math.exp(rng.gauss(0.0, 0.05))
        o, c = px * 1.01, px
        out.append(
            TimestampedBar(
                bars[i].timestamp, Bar(o, max(o, c) * 1.03, min(o, c) * 0.97, c)
            )
        )
    return out


# --------------------------------------------------- the look-ahead property (D173/D181)

PROBE_INDICES = (300, 500, 750, 900)


@pytest.mark.parametrize("k", SWING_K)
@pytest.mark.parametrize("index", PROBE_INDICES)
def test_market_structure_cannot_see_the_future(k, index):
    bars = wandering(1_000, seed=7)
    real = market_structure(bars, k)[index]
    fake = market_structure(corrupted_after(bars, index), k)[index]
    assert real == fake


@pytest.mark.parametrize("index", PROBE_INDICES)
def test_fair_value_gaps_cannot_see_the_future(index):
    bars = wandering(1_000, seed=7)

    def visible(series):
        return sorted(
            (g.formed_at, g.lo, g.hi, g.direction, g.alive_at(index))
            for g in fair_value_gaps(series)
            if g.formed_at <= index
        )

    assert visible(bars) == visible(corrupted_after(bars, index))


@pytest.mark.parametrize("index", PROBE_INDICES)
def test_rsi_cannot_see_the_future(index):
    bars = wandering(1_000, seed=7)
    assert rsi(bars)[index] == rsi(corrupted_after(bars, index))[index]


@pytest.mark.parametrize("k", SWING_K)
def test_a_pivot_is_never_consumed_before_it_confirms(k):
    """The lag itself, asserted directly rather than inferred from the states.

    Every pivot the state machine could act on at bar `t` has `confirmed_at <= t`, and
    `confirmed_at` is `index + k`. This is the arithmetic D173 identified; the test exists
    because getting it wrong produces a plausible curve rather than an exception."""
    bars = wandering(600, seed=3)
    for p in pivots(bars, k):
        assert p.confirmed_at == p.index + k
        assert p.index + k < len(bars)

    states = market_structure(bars, k)
    for t, state in enumerate(states):
        for index in (state.last_high_index, state.last_low_index):
            if index is not None:
                assert index + k <= t
        if state.leg is not None:
            assert state.leg.end_index + k <= t


# ------------------------------------------- pinned against the existing implementations

@pytest.mark.parametrize("k", SWING_K)
@pytest.mark.parametrize("sign", (1, -1))
def test_pivots_agree_with_terrain_swing(k, sign):
    """Pinned against `terrain_swing.confirmed_pivots`, not trusted to agree with it.

    Same arrangement `terrain_swing` has with `strategies.breakout._is_swing` and
    `terrain.mean_true_range` has with `breakout._mean_true_range`. Two implementations of
    one definition drift; a test is what stops them."""
    bars = wandering(400, seed=11)
    index = len(bars) - 1
    mine = sorted(p.index for p in pivots(bars, k) if p.sign == sign and p.index <= index - k)
    theirs = sorted(confirmed_pivots(bars, index, k, sign, lookback=len(bars)))
    assert mine == theirs


# ----------------------------------------------------------------- planted patterns (C1)

# A clean uptrend that flips. Closes only; wicks follow the close so the pivots land on
# the turns and nowhere else.
#          0    1    2    3    4    5    6    7    8    9   10   11   12   13   14
UPTREND = [100, 102, 105, 103, 101, 104, 108, 112, 110, 107, 109, 115, 118, 113, 99]


def test_a_planted_uptrend_produces_a_break_of_structure_then_a_change_of_character():
    bars = bars_from(UPTREND, highs=[c + 0.5 for c in UPTREND], lows=[c - 0.5 for c in UPTREND])
    states = market_structure(bars, k=2)
    events = [(t, s.event) for t, s in enumerate(states) if s.event is not Event.NONE]

    assert any(e is Event.BOS_UP for _, e in events), events
    chochs = [t for t, e in events if e is Event.CHOCH_DOWN]
    assert len(chochs) == 1, events

    at = states[chochs[0]]
    assert at.trend is Trend.DOWN
    assert at.choch_direction == -1
    assert at.choch_level is not None
    # The level broken is a higher low, so it sits above the low that preceded it.
    assert bars[chochs[0]].bar.close < at.choch_level


# A pattern built to separate `STRUCTURE_MODEL.md`'s definition of a change of character
# from the naive one. The spec requires a close below the last confirmed HIGHER LOW; the
# common shortcut is a close below the last confirmed low, full stop. Here the two differ:
# bar 13 prints a swing low at 100 that is LOWER than the higher low at 101, so it is not a
# higher low, and bar 16 closes at 100.5 — between them.
#
#   spec:  100.5 < 101  -> CHoCH_DOWN, and the flipped level is 101
#   naive: 100.5 > 100  -> nothing fires
#
# Without this pattern the shortcut passes every other test in this file. It was found by
# mutating the module and watching 43 tests stay green.
HIGHER_LOW_ROWS = [
    (100.0, 100.5, 99.5, 100.0),   # 0
    (100.0, 100.5, 99.0, 99.0),    # 1
    (99.0, 99.2, 97.0, 98.0),      # 2   swing low  L0 = 97
    (98.0, 99.5, 97.8, 99.0),      # 3
    (99.0, 100.5, 98.8, 100.0),    # 4
    (100.0, 103.5, 99.8, 103.0),   # 5
    (103.0, 106.0, 102.5, 105.0),  # 6   swing high H1 = 106
    (105.0, 105.5, 103.5, 104.0),  # 7
    (104.0, 104.5, 101.0, 102.0),  # 8   swing low  L1 = 101, higher than L0
    (102.0, 103.5, 101.5, 103.0),  # 9
    (103.0, 107.5, 102.5, 107.0),  # 10  close through H1 -> BOS_UP, higher_low := 101
    (107.0, 110.0, 106.5, 109.0),  # 11  swing high H2 = 110
    (109.0, 109.5, 104.0, 105.0),  # 12
    (105.0, 105.5, 100.0, 101.5),  # 13  swing low  L2 = 100, LOWER than L1
    (101.5, 103.0, 101.2, 102.5),  # 14
    (102.5, 103.5, 101.8, 103.0),  # 15  L2 confirms here (13 + k)
    (103.0, 103.2, 100.2, 100.5),  # 16  below the higher low, above the last low
]


def mirrored(rows, axis=200.0):
    """Reflect a pattern through a horizontal price axis, swapping high and low.

    A mirrored fixture is the cheapest test of a mirrored state machine, and a sign error
    in one branch is the most likely bug in one."""
    return [(axis - o, axis - lo, axis - h, axis - c) for o, h, lo, c in rows]


def test_a_change_of_character_needs_a_higher_low_not_merely_the_last_low():
    states = market_structure(ohlc(HIGHER_LOW_ROWS), k=2)
    assert states[15].higher_low == 101.0
    assert states[15].last_low == 100.0, "the fixture must separate the two definitions"

    fired = [t for t, s in enumerate(states) if s.event is Event.CHOCH_DOWN]
    assert fired == [16]
    assert states[16].choch_level == 101.0, "the level broken is the higher low, not the last low"
    assert states[16].trend is Trend.DOWN


def test_the_bullish_mirror_of_that_pattern_behaves_identically():
    states = market_structure(ohlc(mirrored(HIGHER_LOW_ROWS)), k=2)
    assert states[15].lower_high == 200.0 - 101.0
    assert states[15].last_high == 200.0 - 100.0

    fired = [t for t, s in enumerate(states) if s.event is Event.CHOCH_UP]
    assert fired == [16]
    assert states[16].choch_level == 200.0 - 101.0
    assert states[16].trend is Trend.UP


def test_a_monotone_series_never_changes_character():
    """The false-positive check the geometry actually licenses.

    A strictly rising series has no lower high to break and no higher low to lose, so a
    change of character is impossible — not unlikely, impossible. A detector that reports
    one here has a sign error, which is the single most likely bug in a mirrored state
    machine and the hardest to see in aggregate statistics."""
    rising = bars_from([100.0 + i for i in range(200)])
    falling = bars_from([300.0 - i for i in range(200)])
    for bars in (rising, falling):
        for k in SWING_K:
            events = {s.event for s in market_structure(bars, k)}
            assert Event.CHOCH_UP not in events
            assert Event.CHOCH_DOWN not in events


def test_a_flat_series_has_no_pivots_at_all():
    """D173's tie convention: equal extremes produce no pivot rather than an arbitrary
    tiebreak. A flat series is the degenerate case where every candidate is a tie."""
    flat = bars_from([100.0] * 200)
    for k in SWING_K:
        assert pivots(flat, k) == []
        assert {s.trend for s in market_structure(flat, k)} == {Trend.NONE}


def test_the_flipped_level_never_resurrects():
    """`level_alive` is monotone within one change of character. Broken is dead."""
    bars = wandering(1_500, seed=5)
    states = market_structure(bars, k=2)
    for prev, cur in zip(states, states[1:]):
        if cur.choch_index == prev.choch_index and not prev.level_alive:
            assert not cur.level_alive


def test_the_leg_runs_in_the_direction_of_the_change_of_character():
    """Both endpoints must be actual pivots of the right sign, in both directions.

    Asserting only that the leg's span has the right sign is not enough: a mirror bug that
    reads the wrong extreme as the leg's start is caught by the degeneracy guard, which
    silently DROPS those legs rather than producing wrong ones. So the endpoints are
    checked against the pivot set, and each direction is required to be populated — a
    branch that never produces a leg is a branch that is broken, not a branch that is
    strict. Found by mutation: without the per-direction counts this passed."""
    bars = wandering(4_000, seed=13)
    k = 2
    highs = {(p.index, p.price) for p in pivots(bars, k) if p.sign > 0}
    lows = {(p.index, p.price) for p in pivots(bars, k) if p.sign < 0}

    seen = {1: 0, -1: 0}
    for state in market_structure(bars, k):
        if state.leg is None:
            continue
        leg = state.leg
        seen[state.choch_direction] += 1
        assert leg.end_index > leg.start_index
        # A bearish CHoCH's impulse leg falls; a bullish one's rises.
        assert math.copysign(1.0, leg.span) == state.choch_direction
        if state.choch_direction > 0:  # up leg: swing low -> swing high
            assert (leg.start_index, leg.start_price) in lows
            assert (leg.end_index, leg.end_price) in highs
        else:  # down leg: swing high -> swing low
            assert (leg.start_index, leg.start_price) in highs
            assert (leg.end_index, leg.end_price) in lows
    assert seen[1] > 0 and seen[-1] > 0, seen


# ----------------------------------------------------------------- the retracement (C3)

def test_retracement_is_zero_at_the_extreme_and_one_at_the_origin():
    for leg in (Leg(0, 100.0, 10, 80.0), Leg(0, 80.0, 10, 100.0)):
        assert retracement(leg, leg.end_price) == pytest.approx(0.0)
        assert retracement(leg, leg.start_price) == pytest.approx(1.0)
        assert retracement(leg, 0.5 * (leg.start_price + leg.end_price)) == pytest.approx(0.5)


def test_retracement_and_ratio_price_are_inverses():
    for leg in (Leg(0, 100.0, 10, 80.0), Leg(0, 80.0, 10, 100.0)):
        for ratio in CANONICAL_RATIOS + PLACEBO_RATIOS:
            assert retracement(leg, ratio_price(leg, ratio)) == pytest.approx(ratio)


def test_retracement_beyond_the_origin_is_not_clipped():
    """A reading above 1.0 means price retraced past where the leg began — information
    about the structure breaking down. Clipping it would relabel a failed setup as a deep
    one, which is the kind of silent flattery this project exists to prevent."""
    leg = Leg(0, 100.0, 10, 80.0)
    assert retracement(leg, 110.0) == pytest.approx(1.5)
    assert retracement(leg, 75.0) == pytest.approx(-0.25)


def test_a_degenerate_leg_returns_none_rather_than_a_number():
    assert retracement(Leg(0, 100.0, 10, 100.0), 100.0) is None


def test_the_placebo_ratios_are_distinct_from_the_canonical_ones():
    """The whole test of C3 rests on these being genuinely non-canonical and at comparable
    depths. Asserted so that a later edit cannot quietly move one onto 0.618."""
    assert not set(PLACEBO_RATIOS) & set(CANONICAL_RATIOS)
    for placebo in PLACEBO_RATIOS:
        assert min(abs(placebo - c) for c in CANONICAL_RATIOS) >= 0.03
        assert min(CANONICAL_RATIOS) - 0.05 <= placebo <= max(CANONICAL_RATIOS) + 0.05


# ------------------------------------------------------------- the fair value gap (C4)

def test_a_planted_bullish_gap_is_found_at_the_third_bar():
    # Bar 0 high 101; bar 2 low 103 > 101, so the gap is (101, 103), midpoint 102.
    bars = ohlc([
        (100, 101, 99, 100.5),
        (101, 105, 100.5, 104),
        (104, 106, 103, 105),
    ])
    gaps = fair_value_gaps(bars)
    assert len(gaps) == 1
    gap = gaps[0]
    assert (gap.formed_at, gap.lo, gap.hi, gap.direction) == (2, 101, 103, 1)
    assert gap.midpoint == pytest.approx(102.0)
    assert gap.filled_at is None


def test_a_planted_bearish_gap_is_found_and_mirrored():
    bars = ohlc([
        (100, 101, 99, 99.5),
        (99.5, 99.5, 96, 96.5),
        (96.5, 97, 95, 95.5),
    ])
    gaps = fair_value_gaps(bars)
    assert len(gaps) == 1
    assert (gaps[0].formed_at, gaps[0].lo, gaps[0].hi, gaps[0].direction) == (2, 97, 99, -1)


def test_a_touching_wick_is_not_a_gap():
    """The definition is strict: bar 1's high and bar 3's low must not overlap. Exactly
    touching is overlap of measure zero and produces no gap — stated because a `>=` here
    would roughly double the population and nothing would look wrong."""
    bars = ohlc([
        (100, 101, 99, 100.5),
        (101, 105, 100.5, 104),
        (104, 106, 101, 105),  # low == bar 0's high
    ])
    assert fair_value_gaps(bars) == []


def test_a_gap_dies_when_price_trades_through_its_far_edge():
    bars = ohlc([
        (100, 101, 99, 100.5),
        (101, 105, 100.5, 104),
        (104, 106, 103, 105),
        (105, 105.5, 104, 104.5),
        (104.5, 104.5, 100.5, 101),  # low 100.5 < 101 -> through the far edge
    ])
    gaps = fair_value_gaps(bars)
    assert len(gaps) == 1
    assert gaps[0].filled_at == 4
    assert gaps[0].alive_at(3)
    assert not gaps[0].alive_at(4)


def test_a_gap_is_filled_by_the_bar_range_not_the_close():
    """A gap price traded through is filled whether or not the bar closed beyond it.
    Using the close would keep dead gaps alive and inflate every downstream count."""
    bars = ohlc([
        (100, 101, 99, 100.5),
        (101, 105, 100.5, 104),
        (104, 106, 103, 105),
        (105, 105.5, 100.0, 105.2),  # wicks through 101, closes well above
    ])
    assert fair_value_gaps(bars)[0].filled_at == 3


def test_gaps_are_never_reported_twice():
    bars = wandering(1_000, seed=17)
    gaps = fair_value_gaps(bars)
    keys = [(g.formed_at, g.lo, g.hi, g.direction) for g in gaps]
    assert len(keys) == len(set(keys))


# -------------------------------------------------------------------------- RSI (C5)

def test_rsi_is_nan_until_the_window_is_full_and_then_bounded():
    bars = wandering(200, seed=23)
    values = rsi(bars)
    assert all(math.isnan(v) for v in values[:RSI_WINDOW])
    assert all(0.0 <= v <= 100.0 for v in values[RSI_WINDOW:])


def test_rsi_of_a_monotone_rise_is_one_hundred():
    """The all-gains limit, returned exactly rather than dividing by zero."""
    assert rsi(bars_from([100.0 + i for i in range(60)]))[-1] == 100.0


def test_rsi_of_a_monotone_fall_is_zero():
    assert rsi(bars_from([300.0 - i for i in range(60)]))[-1] == pytest.approx(0.0)


def test_rsi_matches_a_hand_computed_wilder_seed():
    """Wilder's ORIGINAL smoothing, seeded by the simple mean of the first window — not
    the EMA variant some platforms ship under the same name. The two give different
    numbers, so the choice is pinned rather than left to the reader."""
    closes = [100.0, 101, 102, 101, 103, 104, 103, 105, 106, 105, 107, 108, 107, 109, 110]
    bars = bars_from(closes)
    gains = [max(b - a, 0.0) for a, b in zip(closes, closes[1:])][:RSI_WINDOW]
    losses = [max(a - b, 0.0) for a, b in zip(closes, closes[1:])][:RSI_WINDOW]
    avg_gain, avg_loss = sum(gains) / RSI_WINDOW, sum(losses) / RSI_WINDOW
    expected = 100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    assert rsi(bars)[RSI_WINDOW] == pytest.approx(expected)


# ------------------------------------------------------------- pre-registered parameters

def test_an_unregistered_pivot_width_is_refused():
    """A value outside D173's set is an unregistered search, and `STRUCTURE_MODEL.md`
    counts every combination tested. Refused at the door rather than in review."""
    with pytest.raises(ValueError, match="unregistered search"):
        pivots(wandering(50, seed=1), k=4)

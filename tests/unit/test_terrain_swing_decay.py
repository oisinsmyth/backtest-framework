"""Offline tests for S5b, the swing supply/demand sensor with wick-decay.

Mirrors `test_terrain_swing.py`, gates closed hardest-first, plus the ones that only exist
because S5b has a new mechanism:

- **No look-ahead.** Mutating every bar after `t` must leave the density at `t`
  byte-identical. S5b has S5's three leak sites — pivot confirmation, the impulse window,
  the invalidation walk — and the decay walk reads two MORE fields (`high`, `low`) off the
  same bars, so the property is re-tested here rather than assumed to carry over from S5's
  suite. D181: `DataView` protects strategies and does nothing for analytics built on their
  output, and a sensor is analytics. Its companion — that the poison actually reaches a
  later density — is here too, because without it the leak test can pass by mutating
  something inert.
- **Reduction to S5.** With no pierces, S5b's levels and scores must equal S5's exactly. A
  variant whose new mechanism is switched off and which still disagrees with the original
  is not a variant, and any measured difference between the two would be unattributable.
- **The kill rule survived the change.** A close beyond the far edge still removes the
  level permanently. Decay is not a soft version of the flip.
- **The arithmetic is pinned.** N pierces give exactly `(1 - decay) ** N`, not
  approximately and not after a rank-normalisation has laundered it.
"""

from __future__ import annotations

import math
import random
from dataclasses import fields
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.terrain_swing import (
    MIN_SWINGS,
    SHARPNESS_BARS,
    SWING_K,
    SwingLevel,
    SwingSupplyDemandSensor,
    confirmed_pivots,
)
from backtest_framework.research.terrain_swing import score_levels as s5_score_levels
from backtest_framework.research.terrain_swing_decay import (
    CLUSTER_ATR,
    DECAY_PER_PIERCE,
    DecayedSwingLevel,
    SwingSupplyDemandSensorV2,
    _survives_with_decay,
    score_levels,
)
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2020, 1, 1)


def bars_from(closes, highs=None, lows=None):
    highs = highs if highs is not None else [c * 1.02 for c in closes]
    lows = lows if lows is not None else [c * 0.98 for c in closes]
    return [
        TimestampedBar(EPOCH + timedelta(days=i), Bar(open=c, high=h, low=lo, close=c))
        for i, (c, h, lo) in enumerate(zip(closes, highs, lows))
    ]


def zigzag(n: int, low: float = 90.0, high: float = 110.0, period: int = 20):
    """Triangular oscillation — the fixture S5 and S5b should both love, since every peak
    is a swing high at `high` and every trough a swing low at `low`."""
    closes = []
    for i in range(n):
        phase = (i % period) / period
        closes.append(low + (high - low) * (2 * phase if phase < 0.5 else 2 * (1 - phase)))
    return bars_from(closes, highs=[c * 1.001 for c in closes], lows=[c * 0.999 for c in closes])


def wandering(n: int, seed: int, start: float = 100.0):
    rng = random.Random(seed)
    closes, px = [], start
    for _ in range(n):
        px *= math.exp(rng.gauss(0.0, 0.02))
        closes.append(px)
    return bars_from(closes)


SENSOR = SwingSupplyDemandSensorV2(2, 0.5, "quote_notional", lookback_bars=180, decay=0.25)
S5 = SwingSupplyDemandSensor(2, 0.5, "quote_notional", lookback_bars=180)
"""The same parameters as S5b's, so every comparison below varies the scoring rule alone."""


def demand_level(price=100.0, half_width=0.5, tests=2, formed_index=0):
    """A demand band centred at `price`; its far (lower) edge sits at `price - half_width`."""
    return SwingLevel(price=price, sign=-1, half_width=half_width, n_swings=2, volume=1.0,
                      sharpness=1.0, tests=tests, formed_index=formed_index)


def supply_level(price=100.0, half_width=0.5, tests=2, formed_index=0):
    """A supply band centred at `price`; its far (upper) edge sits at `price + half_width`."""
    return SwingLevel(price=price, sign=1, half_width=half_width, n_swings=2, volume=1.0,
                      sharpness=1.0, tests=tests, formed_index=formed_index)


# ---------------------------------------------------------------- no look-ahead


def test_density_does_not_read_a_single_bar_past_the_index():
    """The gate that matters, and the reason it is repeated rather than inherited: S5b's
    walk reads `high` and `low` where S5's read only `close`, so it is two new opportunities
    to index past the present on bars S5's suite never checked in those fields."""
    bars = wandering(400, seed=4)
    volumes = [1000.0 + i for i in range(400)]
    cut = 300

    before = SENSOR.density(bars, cut, volumes)
    assert before is not None

    poisoned = list(bars)
    for j in range(cut + 1, len(bars)):
        b = bars[j].bar
        poisoned[j] = TimestampedBar(
            bars[j].timestamp,
            Bar(open=b.open * 10, high=b.high * 10, low=b.low * 10, close=b.close * 10),
        )
    poisoned_volumes = list(volumes)
    for j in range(cut + 1, len(volumes)):
        poisoned_volumes[j] *= 100

    after = SENSOR.density(poisoned, cut, poisoned_volumes)
    assert after == before


def test_the_poison_actually_reaches_a_later_density():
    """Without this the look-ahead test could pass by mutating something inert."""
    bars = wandering(400, seed=4)
    volumes = [1000.0 + i for i in range(400)]
    cut = 300
    poisoned = list(bars)
    for j in range(cut + 1, len(bars)):
        b = bars[j].bar
        poisoned[j] = TimestampedBar(
            bars[j].timestamp,
            Bar(open=b.open * 10, high=b.high * 10, low=b.low * 10, close=b.close * 10),
        )
    assert SENSOR.density(poisoned, 399, volumes) != SENSOR.density(bars, 399, volumes)


def test_the_pierce_count_itself_does_not_read_past_the_index():
    """A sharper version of the same gate, aimed at the new field reads specifically.

    The density test above could in principle survive a leak that changed a pierce count
    without changing which bucket any level landed in. This asserts on the counts."""
    bars = wandering(400, seed=4)
    volumes = [1000.0 + i for i in range(400)]
    cut = 300
    before = [(lv.price, lv.pierces) for lv in SENSOR.live_levels(bars, cut, volumes)]

    poisoned = list(bars)
    for j in range(cut + 1, len(bars)):
        b = bars[j].bar
        poisoned[j] = TimestampedBar(
            bars[j].timestamp,
            Bar(open=b.open, high=b.high * 10, low=b.low / 10, close=b.close),
        )
    assert [(lv.price, lv.pierces) for lv in SENSOR.live_levels(poisoned, cut, volumes)] == before


def test_pivots_stop_short_of_the_index_by_the_confirmation_lag():
    """D173's lag, unchanged by S5b — reused from S5's `confirmed_pivots`, not restated."""
    bars = wandering(300, seed=9)
    for k in SWING_K:
        pivots = confirmed_pivots(bars, 200, k, 1, lookback=180, trailing_bars=SHARPNESS_BARS)
        assert all(t <= 200 - max(k, SHARPNESS_BARS) for t in pivots), k


# ---------------------------------------------------------------- the wick rule


def test_a_wick_through_a_demand_band_that_closes_above_it_decays_rather_than_kills():
    """The central new behaviour, in its plainest form.

    Band at 100.0 +/- 0.5, so the far (lower) edge is 99.5. Bar 1's low reaches 99.0 and it
    closes at 99.8 — above the edge. The level must still be alive, and it must have taken
    exactly one pierce."""
    bars = [
        TimestampedBar(EPOCH, Bar(open=100.0, high=100.2, low=99.8, close=100.0)),
        TimestampedBar(EPOCH + timedelta(days=1), Bar(open=99.9, high=100.0, low=99.0, close=99.8)),
    ]
    alive, _, pierces = _survives_with_decay(bars, demand_level(), 1)
    assert alive, "a wick that closes back above the edge must not kill a demand band"
    assert pierces == 1


def test_the_demand_wick_reduces_the_score_rather_than_leaving_it_untouched():
    """Surviving is only half the rule. A pierce that cost nothing would be a no-op wearing
    a mechanism's name, and the module docstring's whole claim is that it is not."""
    untouched = DecayedSwingLevel(price=100.0, sign=-1, half_width=0.5, n_swings=2, volume=1.0,
                                  sharpness=1.0, tests=2, formed_index=0, pierces=0)
    pierced = DecayedSwingLevel(price=100.0, sign=-1, half_width=0.5, n_swings=2, volume=1.0,
                                sharpness=1.0, tests=2, formed_index=0, pierces=1)
    base = s5_score_levels([untouched, pierced])
    assert base[0] == base[1], "the fixture must differ only in pierces"

    decayed = score_levels([untouched, pierced], decay=0.25)
    assert decayed[1] < decayed[0]
    assert decayed[1] == pytest.approx(decayed[0] * 0.75)


def test_a_wick_through_a_supply_band_that_closes_below_it_decays_rather_than_kills():
    """The same rule in reverse. Band at 100.0 +/- 0.5, far (upper) edge 100.5; bar 1's high
    reaches 101.0 and it closes at 100.2, below the edge."""
    bars = [
        TimestampedBar(EPOCH, Bar(open=100.0, high=100.2, low=99.8, close=100.0)),
        TimestampedBar(
            EPOCH + timedelta(days=1), Bar(open=100.1, high=101.0, low=100.0, close=100.2)
        ),
    ]
    alive, _, pierces = _survives_with_decay(bars, supply_level(), 1)
    assert alive, "a wick that closes back below the edge must not kill a supply band"
    assert pierces == 1


def test_the_supply_wick_reduces_the_score_too():
    untouched = DecayedSwingLevel(price=100.0, sign=1, half_width=0.5, n_swings=2, volume=1.0,
                                  sharpness=1.0, tests=2, formed_index=0, pierces=0)
    pierced = DecayedSwingLevel(price=100.0, sign=1, half_width=0.5, n_swings=2, volume=1.0,
                                sharpness=1.0, tests=2, formed_index=0, pierces=2)
    decayed = score_levels([untouched, pierced], decay=0.1)
    assert decayed[1] < decayed[0]
    assert decayed[1] == pytest.approx(decayed[0] * 0.9 * 0.9)


def test_a_wick_the_wrong_way_is_not_a_pierce():
    """A demand band is pierced from BELOW. A bar whose high runs away upward through the
    band's near edge is price leaving the level, which is the opposite event, and counting
    it would make `pierces` a volatility proxy rather than a rejection count."""
    bars = [
        TimestampedBar(EPOCH, Bar(open=100.0, high=100.2, low=99.8, close=100.0)),
        TimestampedBar(
            EPOCH + timedelta(days=1), Bar(open=100.1, high=105.0, low=99.9, close=104.0)
        ),
    ]
    alive, _, pierces = _survives_with_decay(bars, demand_level(), 1)
    assert alive and pierces == 0


def test_a_bar_can_be_a_test_and_a_pierce_at_once():
    """Wick through the edge, close back INSIDE the band. Both events are recorded, because
    netting them would be a hypothesis about their relationship rather than a measurement."""
    bars = [
        TimestampedBar(EPOCH, Bar(open=98.0, high=98.2, low=97.8, close=98.0)),  # outside
        TimestampedBar(EPOCH + timedelta(days=1), Bar(open=99.6, high=99.9, low=99.0, close=99.8)),
    ]
    alive, tests, pierces = _survives_with_decay(bars, demand_level(tests=2), 1)
    assert alive
    assert pierces == 1
    assert tests == 3, "2 forming pivots + 1 approach into the band on the piercing bar"


# ---------------------------------------------------------------- the kill rule survives


def test_a_close_beyond_the_far_edge_still_kills_a_demand_band():
    """S5's rule, unchanged. Decay is not a soft version of it."""
    bars = [
        TimestampedBar(EPOCH, Bar(open=100.0, high=100.2, low=99.8, close=100.0)),
        TimestampedBar(EPOCH + timedelta(days=1), Bar(open=99.6, high=99.7, low=99.0, close=99.2)),
    ]
    alive, _, pierces = _survives_with_decay(bars, demand_level(), 1)
    assert not alive
    assert pierces == 0, "a bar that closes through does not also bank a pierce"


def test_a_close_beyond_the_far_edge_still_kills_a_supply_band():
    bars = [
        TimestampedBar(EPOCH, Bar(open=100.0, high=100.2, low=99.8, close=100.0)),
        TimestampedBar(
            EPOCH + timedelta(days=1), Bar(open=100.4, high=101.0, low=100.3, close=100.9)
        ),
    ]
    alive, _, _ = _survives_with_decay(bars, supply_level(), 1)
    assert not alive


def test_a_level_closed_through_is_gone_and_does_not_come_back():
    """The whole-sensor version of the same rule — no support-becomes-resistance flip, and
    no number of prior pierces buys a level a reprieve from a close-through."""
    bars = zigzag(300, low=90.0, high=110.0, period=20)
    closes = [tb.bar.close for tb in bars] + [140.0] * 60
    broken = bars_from(closes, highs=[c * 1.001 for c in closes], lows=[c * 0.999 for c in closes])
    volumes = [1000.0] * len(broken)

    before = SENSOR.live_levels(bars, 280, volumes[: len(bars)])
    assert [lv for lv in before if lv.sign > 0 and 105.0 <= lv.price <= 115.0], (
        "expected a resistance band near 110 before the break"
    )
    after = SENSOR.live_levels(broken, len(broken) - 1, volumes)
    assert not [lv for lv in after if lv.sign > 0 and 105.0 <= lv.price <= 115.0]


def test_price_inside_the_band_neither_breaks_nor_pierces_it():
    """The band EDGE is the threshold for both rules. Noise inside the band must not kill a
    level on a tick, and it must not quietly grind the score down either."""
    closes = [100.0, 100.4, 99.6, 100.2, 99.8]
    bars = bars_from(closes, highs=[c + 0.05 for c in closes], lows=[c - 0.05 for c in closes])
    alive, _, pierces = _survives_with_decay(bars, supply_level(), len(bars) - 1)
    assert alive and pierces == 0


# ---------------------------------------------------------------- the arithmetic


@pytest.mark.parametrize("decay", DECAY_PER_PIERCE)
@pytest.mark.parametrize("n", [0, 1, 2, 3, 5, 8])
def test_n_pierces_give_exactly_one_minus_decay_to_the_n(decay: float, n: int):
    """Pinned against the closed form, not against a recomputation of the same loop."""
    level = DecayedSwingLevel(price=100.0, sign=1, half_width=0.5, n_swings=2, volume=1.0,
                              sharpness=1.0, tests=2, formed_index=0, pierces=n)
    assert level.strength_multiplier(decay) == pytest.approx((1.0 - decay) ** n)

    expected = 1.0
    for _ in range(n):
        expected *= 1.0 - decay
    assert level.strength_multiplier(decay) == pytest.approx(expected)


def test_the_multiplier_hits_the_combined_score_not_a_component():
    """`_rank_scores` reads only the ORDER of its inputs, so a multiplier applied to a
    component would do nothing at all unless it reordered two levels — and then it would
    move the score by a full 1/n step rather than by `decay`. Applied outside the ranks it
    means what it says, and here that means S5b's scores need not lie on the rank grid."""
    levels = [
        DecayedSwingLevel(price=100.0, sign=1, half_width=0.5, n_swings=2, volume=v,
                          sharpness=v, tests=int(v), formed_index=0, pierces=p)
        for v, p in ((1.0, 0), (2.0, 8), (3.0, 0))
    ]
    base = s5_score_levels(levels)
    decayed = score_levels(levels, decay=0.25)
    assert decayed == [pytest.approx(b * 0.75 ** lv.pierces) for b, lv in zip(base, levels)]
    # the mid level ranks 2nd on all three components, so its S5 score is (2/3)^3
    assert base[1] == pytest.approx((2 / 3) ** 3)
    assert decayed[1] == pytest.approx((2 / 3) ** 3 * 0.75**8)
    assert base[1] > base[0]
    assert decayed[1] < decayed[0], (
        "the middle level outranks the weakest on all three components, so nothing inside "
        "the rank grid can put it below — only a multiplier applied outside the ranks can, "
        "and here it takes 8 pierces to cross a whole rank step"
    )


def test_pierces_can_only_lower_a_score_never_raise_it():
    bars = wandering(400, seed=4)
    volumes = [1000.0 + i for i in range(400)]
    levels = SENSOR.live_levels(bars, 300, volumes)
    assert levels
    base = s5_score_levels(levels)
    for b, d in zip(base, score_levels(levels, decay=0.25)):
        assert d <= b + 1e-12


def test_scoring_an_empty_set_is_empty_rather_than_an_error():
    assert score_levels([], decay=0.1) == []


# ---------------------------------------------------------------- reduction to S5


def test_with_zero_pierces_the_levels_and_scores_are_identical_to_s5():
    """The key equivalence: the variant must reduce to the original when its new mechanism
    never fires. A `zigzag` never wicks through its own turning prices, so no pierce fires
    anywhere on it — asserted, not assumed, because an equivalence that held only because
    both sides were empty would prove nothing."""
    bars = zigzag(400, low=90.0, high=110.0, period=20)
    volumes = [1000.0 + i for i in range(400)]

    mine = SENSOR.live_levels(bars, 350, volumes)
    theirs = S5.live_levels(bars, 350, volumes)
    assert mine, "the fixture must produce levels for the comparison to mean anything"
    assert all(lv.pierces == 0 for lv in mine), "this fixture must fire no pierces"

    shared = [f.name for f in fields(SwingLevel)]
    assert [tuple(getattr(lv, f) for f in shared) for lv in mine] == [
        tuple(getattr(lv, f) for f in shared) for lv in theirs
    ]
    for decay in DECAY_PER_PIERCE:
        assert score_levels(mine, decay) == s5_score_levels(theirs)

    for decay in DECAY_PER_PIERCE:
        variant = SwingSupplyDemandSensorV2(2, 0.5, "quote_notional", 180, decay)
        assert variant.density(bars, 350, volumes) == S5.density(bars, 350, volumes)
        assert variant.levels_at(bars, 350, volumes) == S5.levels_at(bars, 350, volumes)


def test_the_level_set_is_always_identical_to_s5_pierces_or_not():
    """The claim the module docstring leads with, pinned so nobody has to take its word.

    S5 already kills on CLOSE alone, so a wick that closes back was ALREADY survivable
    there. S5b therefore rescues NOTHING — the two sensors emit the same bands at every
    index and differ only in the score. This runs on a fixture that DOES fire pierces, so
    it is the strong form of the statement and not a restatement of the zero-pierce case."""
    bars = wandering(400, seed=4)
    volumes = [1000.0 + i for i in range(400)]
    saw_a_pierce = False
    for index in range(220, 400, 7):
        mine = SENSOR.live_levels(bars, index, volumes)
        theirs = S5.live_levels(bars, index, volumes)
        saw_a_pierce = saw_a_pierce or any(lv.pierces > 0 for lv in mine)
        shared = [f.name for f in fields(SwingLevel)]
        assert [tuple(getattr(lv, f) for f in shared) for lv in mine] == [
            tuple(getattr(lv, f) for f in shared) for lv in theirs
        ], index
    assert saw_a_pierce, "a fixture with no pierces cannot test the strong form"


def test_a_pierced_map_does_differ_from_s5_in_its_density():
    """The other half of the previous test. Same levels, different mass — otherwise S5b is
    a rename and every comparison against S5 would be measuring zero by construction."""
    bars = wandering(400, seed=4)
    volumes = [1000.0 + i for i in range(400)]
    differed = False
    for index in range(220, 400, 7):
        if any(lv.pierces > 0 for lv in SENSOR.live_levels(bars, index, volumes)):
            mine = SENSOR.density(bars, index, volumes)
            theirs = S5.density(bars, index, volumes)
            if mine is not None and theirs is not None and mine.mass != theirs.mass:
                differed = True
                break
    assert differed, "a pierce must be able to move mass, or the mechanism is inert"


def test_the_null_harness_is_handed_the_same_input_for_s5b_as_for_s5():
    """The consequence of the previous two tests, and the one that has to be read before
    anyone pre-registers a comparison of the two sensors.

    `terrain_nulls.run_null` consumes `sensor_levels`, and `sensor_levels` takes the direct
    path here — it returns level PRICES. The decay lives in the score, which only
    `density()` reads, and nothing on that path calls `density()`. So the harness receives
    a byte-identical map from S5 and S5b, every rebuild date, at any decay, and would
    return a byte-identical verdict.

    This is asserted rather than left implicit because a null test of S5b run as things
    stand today would produce S5's number and look like an independent confirmation of it.
    Whatever S5b is eventually measured with, it is not this path unchanged."""
    from backtest_framework.research.terrain_nulls import sensor_levels

    bars = wandering(400, seed=4)
    volumes = [1000.0 + i for i in range(400)]
    baseline = sensor_levels(bars, volumes, S5, rebuild_every=20)
    assert baseline, "the fixture must produce a map for the comparison to mean anything"
    for decay in DECAY_PER_PIERCE:
        variant = SwingSupplyDemandSensorV2(2, 0.5, "quote_notional", 180, decay)
        assert sensor_levels(bars, volumes, variant, rebuild_every=20) == baseline, decay


# ---------------------------------------------------------------- level formation


def test_repeated_turns_at_one_price_form_a_level():
    bars = zigzag(400, low=90.0, high=110.0, period=20)
    levels = SENSOR.live_levels(bars, 350, [1000.0] * 400)
    assert levels, "a triangular oscillation must produce levels"
    assert any(lv.n_swings >= MIN_SWINGS for lv in levels)


def test_levels_from_highs_and_lows_are_kept_apart():
    bars = zigzag(400, period=20)
    for lv in SENSOR.live_levels(bars, 350, [1000.0] * 400):
        assert lv.sign in (1, -1)


def test_the_forming_pivots_count_as_tests():
    """S5's revision, inherited rather than re-litigated: a level formed by five swings has
    been tested five times."""
    bars = zigzag(400, low=90.0, high=110.0, period=20)
    levels = SENSOR.live_levels(bars, 350, [1000.0] * 400)
    assert levels
    assert all(lv.tests >= lv.n_swings for lv in levels)


# ---------------------------------------------------------------- density contract


def test_density_mass_sums_to_one():
    bars = wandering(400, seed=4)
    density = SENSOR.density(bars, 350, [1000.0] * 400)
    assert density is not None
    assert sum(density.mass) == pytest.approx(1.0)


def test_density_is_none_before_the_warm_up():
    bars = wandering(400, seed=3)
    assert SENSOR.density(bars, SENSOR.warm_up_bars() - 2, [1000.0] * 400) is None


def test_price_only_call_raises():
    bars = wandering(400, seed=5)
    with pytest.raises(ValueError, match="weights levels by volume"):
        SENSOR.density(bars, 300, None)
    with pytest.raises(ValueError, match="weights levels by volume"):
        SENSOR.levels_at(bars, 300, None)


def test_misaligned_volumes_raise():
    bars = wandering(400, seed=6)
    with pytest.raises(ValueError, match="aligned"):
        SENSOR.density(bars, 300, [1000.0] * 399)


def test_spans_is_left_empty_because_it_is_an_s1_construction():
    bars = wandering(400, seed=4)
    density = SENSOR.density(bars, 350, [1000.0] * 400)
    assert density is not None and density.spans == ()


def test_levels_at_exists_so_the_null_harness_uses_the_direct_path():
    """`terrain_nulls.sensor_levels` branches on `getattr(sensor, "levels_at", None)`. If
    S5b lost that attribute it would silently fall back to `PriceDensity.levels`, which
    keeps only local maxima at or above `HVN_QUANTILE` and discarded three of every four
    levels S5 produced. That failure is invisible — it produces a smaller map, not an
    error — so the branch is asserted directly."""
    from backtest_framework.research.terrain_nulls import sensor_levels

    bars = wandering(400, seed=4)
    volumes = [1000.0 + i for i in range(400)]
    assert getattr(SENSOR, "levels_at", None) is not None
    via_harness = sensor_levels(bars, volumes, SENSOR, rebuild_every=20)
    assert via_harness
    for t, levels in via_harness.items():
        assert levels == SENSOR.levels_at(bars, t, volumes)


# ---------------------------------------------------------------- parameter discipline


def test_the_decay_set_is_enforced():
    """S5b's only new free parameter, and therefore its only new multiplicity cost."""
    for bad in (0.0, 0.2, 0.5, 1.0, -0.1):
        with pytest.raises(ValueError, match="decay must be one of"):
            SwingSupplyDemandSensorV2(2, 0.5, "quote_notional", 180, bad)
    for good in DECAY_PER_PIERCE:
        assert SwingSupplyDemandSensorV2(2, 0.5, "quote_notional", 180, good).decay == good


def test_the_decay_set_has_exactly_two_values():
    """Three would be a wider search than was registered, and the ledger is cumulative."""
    assert DECAY_PER_PIERCE == (0.1, 0.25)


def test_the_inherited_parameter_sets_are_still_enforced():
    with pytest.raises(ValueError, match="k must be one of"):
        SwingSupplyDemandSensorV2(5, 0.5, "shares", 180, 0.1)
    with pytest.raises(ValueError, match="cluster_atr must be one of"):
        SwingSupplyDemandSensorV2(2, 0.4, "shares", 180, 0.1)
    with pytest.raises(ValueError, match="volume_units must be one of"):
        SwingSupplyDemandSensorV2(2, 0.5, "dollars", 180, 0.1)


def test_a_lookback_too_short_to_hold_two_pivots_raises():
    with pytest.raises(ValueError, match="cannot hold two confirmed pivots"):
        SwingSupplyDemandSensorV2(3, 0.5, "shares", 10, 0.1)


def test_the_sensor_satisfies_the_terrain_protocol():
    from backtest_framework.research.terrain import TerrainSensor

    sensor: TerrainSensor = SENSOR  # a type error here is the real assertion
    assert sensor.name == "S5b_swing_supply_demand_decay"
    assert all(c in CLUSTER_ATR for c in CLUSTER_ATR)


def test_the_sensor_is_frozen():
    """The protocol's stated reason: a sensor whose parameters can change after
    construction cannot be trusted to have produced the densities attributed to it."""
    from dataclasses import FrozenInstanceError

    with pytest.raises(FrozenInstanceError):
        SENSOR.decay = 0.1  # type: ignore[misc]

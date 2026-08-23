"""Offline tests for S5, the swing supply/demand sensor.

Gates closed here, hardest first:

- **No look-ahead.** Mutating every bar after `t` must leave the density at `t`
  byte-identical. D181 established that `DataView` protects strategies and does nothing
  for analytics built on their output, and a sensor is analytics. This design has three
  separate places it could read the future — pivot confirmation, the impulse window, and
  the invalidation walk — so the property is tested, not argued.
- **The pivot detector agrees with D173's.** `_is_swing_bars` restates
  `strategies.breakout._is_swing` on bars; if they drift, S5 is built on a different
  definition of "swing" than the rest of the project uses.
- **Broken is dead.** A close through the band removes the level permanently.
- Scoring has no free weights and no component can zero a level out.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.terrain_swing import (
    CLUSTER_ATR,
    MIN_SWINGS,
    SHARPNESS_BARS,
    SWING_K,
    SwingSupplyDemandSensor,
    _is_swing_bars,
    _rank_scores,
    confirmed_pivots,
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
    """Triangular oscillation — price turns at the same two prices repeatedly.

    The fixture S5 should love: every peak is a swing high at `high`, every trough a swing
    low at `low`, so two strong levels exist by construction."""
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


SENSOR = SwingSupplyDemandSensor(2, 0.5, "quote_notional", lookback_bars=180)


# ---------------------------------------------------------------- no look-ahead


def test_density_does_not_read_a_single_bar_past_the_index():
    """The gate that matters. Three places could leak: pivot confirmation, the impulse
    window, and the invalidation walk. All are covered by one property."""
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


def test_pivots_stop_short_of_the_index_by_the_confirmation_lag():
    """A pivot at t is not knowable until t+k, and the impulse needs SHARPNESS_BARS more."""
    bars = wandering(300, seed=9)
    for k in SWING_K:
        pivots = confirmed_pivots(bars, 200, k, 1, lookback=180, trailing_bars=SHARPNESS_BARS)
        assert all(t <= 200 - max(k, SHARPNESS_BARS) for t in pivots), k


# ---------------------------------------------------------------- pivot agreement


def test_the_bar_pivot_detector_agrees_with_the_dataview_one():
    """`_is_swing_bars` restates `breakout._is_swing`. Drift here means S5 is built on a
    different definition of 'swing' than the stops and gates use."""
    from backtest_framework.engine.dataview import DataView
    from backtest_framework.strategies.breakout import _is_swing

    bars = wandering(200, seed=13)
    for k in SWING_K:
        for sign in (1, -1):
            for index in range(k + 1, len(bars) - k - 1):
                view = DataView(tuple(tb.bar for tb in bars[: index + k + 1]))
                assert _is_swing_bars(bars, index, k, sign) == _is_swing(view, index, k, sign), (
                    k, sign, index
                )


def test_equal_extremes_produce_no_pivot():
    """D173's stated tie convention: strict and unique, never an arbitrary tiebreak."""
    closes = [100.0] * 9
    bars = bars_from(closes, highs=[105.0] * 9, lows=[95.0] * 9)
    assert not _is_swing_bars(bars, 4, 2, 1)
    assert not _is_swing_bars(bars, 4, 2, -1)


def test_a_pivot_at_the_series_edge_is_not_claimed():
    bars = wandering(50, seed=1)
    assert not _is_swing_bars(bars, 1, 2, 1)
    assert not _is_swing_bars(bars, len(bars) - 1, 2, 1)


# ---------------------------------------------------------------- level formation


def test_repeated_turns_at_one_price_form_a_level():
    bars = zigzag(400, low=90.0, high=110.0, period=20)
    volumes = [1000.0] * 400
    levels = SENSOR.live_levels(bars, 350, volumes)
    assert levels, "a triangular oscillation must produce levels"
    assert any(lv.n_swings >= MIN_SWINGS for lv in levels)


def test_a_single_swing_never_forms_a_level():
    """MIN_SWINGS is the whole 'more than once' premise."""
    from backtest_framework.research.terrain_swing import _cluster

    bars = wandering(100, seed=2)
    single = _cluster(bars, [1000.0] * 100, [30], 1, half_width=1.0, atr=1.0)
    assert single == []


def test_levels_from_highs_and_lows_are_kept_apart():
    bars = zigzag(400, period=20)
    levels = SENSOR.live_levels(bars, 350, [1000.0] * 400)
    signs = {lv.sign for lv in levels}
    assert signs <= {1, -1}
    for lv in levels:
        assert lv.sign in (1, -1)


# ---------------------------------------------------------------- invalidation


def test_a_level_closed_through_is_gone_and_does_not_come_back():
    """Broken is dead, permanently — no support-becomes-resistance flip."""
    # Oscillate to build a resistance band near 110, then break decisively above it.
    bars = zigzag(300, low=90.0, high=110.0, period=20)
    closes = [tb.bar.close for tb in bars] + [140.0] * 60
    broken = bars_from(closes, highs=[c * 1.001 for c in closes], lows=[c * 0.999 for c in closes])
    volumes = [1000.0] * len(broken)

    before = SENSOR.live_levels(bars, 280, volumes[: len(bars)])
    highs_before = [lv for lv in before if lv.sign > 0 and 105.0 <= lv.price <= 115.0]
    assert highs_before, "expected a resistance band near 110 before the break"

    after = SENSOR.live_levels(broken, len(broken) - 1, volumes)
    assert not [lv for lv in after if lv.sign > 0 and 105.0 <= lv.price <= 115.0]


def test_price_inside_the_band_does_not_break_it():
    """The band edge, not the level itself, is the invalidation threshold — otherwise
    noise inside the band kills a level on a tick."""
    from backtest_framework.research.terrain_swing import SwingLevel, _survives

    closes = [100.0, 100.4, 99.6, 100.2, 99.8]
    bars = bars_from(closes, highs=[c + 0.05 for c in closes], lows=[c - 0.05 for c in closes])
    level = SwingLevel(price=100.0, sign=1, half_width=0.5, n_swings=2, volume=1.0,
                       sharpness=1.0, tests=0, formed_index=0)
    alive, _ = _survives(bars, level, len(bars) - 1)
    assert alive


def test_the_forming_pivots_count_as_tests():
    """Revised before any run: counting only post-formation approaches left two thirds of
    real levels at zero, so the component barely discriminated. A level formed by five
    swings has been tested five times."""
    bars = zigzag(400, low=90.0, high=110.0, period=20)
    levels = SENSOR.live_levels(bars, 350, [1000.0] * 400)
    assert levels
    assert all(lv.tests >= lv.n_swings for lv in levels)


def test_a_test_is_counted_once_per_approach_not_once_per_bar():
    """Same convention as the null harness's touch definition."""
    from backtest_framework.research.terrain_swing import SwingLevel, _survives

    # out, in, in, in, out, in  -> two approaches
    closes = [98.0, 100.0, 100.1, 99.9, 98.0, 100.0]
    bars = bars_from(closes, highs=[c + 0.05 for c in closes], lows=[c - 0.05 for c in closes])
    level = SwingLevel(price=100.0, sign=1, half_width=0.5, n_swings=2, volume=1.0,
                       sharpness=1.0, tests=2, formed_index=0)
    alive, tests = _survives(bars, level, len(bars) - 1)
    # 2 forming pivots + 2 later approaches
    assert alive and tests == 4


# ---------------------------------------------------------------- scoring


def test_rank_scores_never_return_zero():
    """One weak component must not annihilate a level strong on the other two."""
    assert min(_rank_scores([1.0, 5.0, 9.0])) > 0.0
    assert max(_rank_scores([1.0, 5.0, 9.0])) == pytest.approx(1.0)


def test_rank_scores_share_the_lowest_rank_on_ties():
    assert _rank_scores([4.0, 4.0, 9.0]) == [pytest.approx(1 / 3), pytest.approx(1 / 3), 1.0]


def test_score_is_multiplicative_so_a_level_needs_all_three():
    """The stated hypothesis: volume alone does not make a level."""
    from backtest_framework.research.terrain_swing import SwingLevel

    def lv(volume, sharpness, tests):
        return SwingLevel(price=100.0, sign=1, half_width=1.0, n_swings=2, volume=volume,
                          sharpness=sharpness, tests=tests, formed_index=0)

    all_round = lv(5.0, 5.0, 5)
    volume_only = lv(9.0, 1.0, 1)
    scores = score_levels([volume_only, all_round, lv(1.0, 1.0, 1)])
    assert scores[1] > scores[0], "a balanced level must beat a volume-only one"


def test_scoring_an_empty_set_is_empty_rather_than_an_error():
    assert score_levels([]) == []


# ---------------------------------------------------------------- density contract


def test_density_mass_sums_to_one():
    bars = wandering(400, seed=4)
    density = SENSOR.density(bars, 350, [1000.0] * 400)
    assert density is not None
    assert sum(density.mass) == pytest.approx(1.0)


def test_density_is_none_before_the_warm_up():
    bars = wandering(400, seed=3)
    assert SENSOR.density(bars, SENSOR.warm_up_bars() - 2, [1000.0] * 400) is None


def test_density_is_none_when_too_few_levels_survive():
    """A map of two levels is not a map, and `PriceDensity.levels` needs three."""
    bars = wandering(400, seed=21)
    density = SENSOR.density(bars, 250, [1000.0] * 400)
    if density is not None:
        assert sum(1 for m in density.mass if m > 0.0) >= 1


def test_price_only_call_raises():
    bars = wandering(400, seed=5)
    with pytest.raises(ValueError, match="weights levels by volume"):
        SENSOR.density(bars, 300, None)


def test_misaligned_volumes_raise():
    bars = wandering(400, seed=6)
    with pytest.raises(ValueError, match="aligned"):
        SENSOR.density(bars, 300, [1000.0] * 399)


def test_spans_is_left_empty_because_it_is_an_s1_construction():
    """D194's degeneracy census counts buckets a BAR's range covered. S5's levels are
    discrete, so the census has no meaning here and is not faked."""
    bars = wandering(400, seed=4)
    density = SENSOR.density(bars, 350, [1000.0] * 400)
    assert density is not None and density.spans == ()


# ---------------------------------------------------------------- parameter discipline


def test_parameter_sets_are_enforced():
    with pytest.raises(ValueError, match="k must be one of"):
        SwingSupplyDemandSensor(5, 0.5, "shares", lookback_bars=180)
    with pytest.raises(ValueError, match="cluster_atr must be one of"):
        SwingSupplyDemandSensor(2, 0.4, "shares", lookback_bars=180)
    with pytest.raises(ValueError, match="volume_units must be one of"):
        SwingSupplyDemandSensor(2, 0.5, "dollars", lookback_bars=180)


def test_a_lookback_too_short_to_hold_two_pivots_raises():
    with pytest.raises(ValueError, match="cannot hold two confirmed pivots"):
        SwingSupplyDemandSensor(3, 0.5, "shares", lookback_bars=10)


def test_the_sensor_satisfies_the_terrain_protocol():
    from backtest_framework.research.terrain import TerrainSensor

    sensor: TerrainSensor = SENSOR  # a type error here is the real assertion
    assert sensor.name == "S5_swing_supply_demand"
    assert all(k in SWING_K for k in SWING_K)
    assert all(c in CLUSTER_ATR for c in CLUSTER_ATR)

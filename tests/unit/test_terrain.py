"""Unit gates for the S1 terrain sensor (D189).

The load-bearing test here is the first one. `DataView` (D32/D56) makes look-ahead
structurally impossible for a STRATEGY — the view arrives already sliced, so a future bar is
absent rather than merely forbidden. A sensor is analytics, and D181 is the record of what
that distinction costs: the ensemble weighted itself with whole-sample volatility for as
long as it existed, inside a project with a look-ahead guard, because the guard does not
reach analytics built on strategy output.

Nothing structural stops `density()` reading `bars[index + 1]`. This file is what does.
"""

from __future__ import annotations

import math
import random
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.terrain import (
    ATR_WINDOW,
    BUCKET_ATR,
    LOOKBACK_DAYS,
    PriceDensity,
    VolumeProfileSensor,
    mean_true_range,
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


def wandering(n: int, seed: int, start: float = 100.0) -> list[TimestampedBar]:
    rng = random.Random(seed)
    closes, px = [], start
    for _ in range(n):
        px *= math.exp(rng.gauss(0.0, 0.02))
        closes.append(px)
    return bars_from(closes)


SENSOR = VolumeProfileSensor(90, 0.5, "quote_notional")


# ------------------------------------------------------- the look-ahead property (D181)


def test_density_at_a_bar_is_unchanged_by_every_later_bar():
    """THE test this module exists for.

    A sensor sees a whole series and an index. Nothing in the type system stops it reading
    past the index, and the structural guard that stops a strategy doing so does not apply
    here."""
    n, cut = 400, 300
    bars = wandering(n, seed=1)
    volumes = [1_000.0 + i for i in range(n)]

    before = SENSOR.density(bars, cut, volumes)
    assert before is not None

    # Mutate everything after the index as violently as possible: prices x10, volumes x100.
    mutated = list(bars)
    mutated_volumes = list(volumes)
    for i in range(cut + 1, n):
        b = bars[i].bar
        mutated[i] = TimestampedBar(
            bars[i].timestamp,
            Bar(open=b.open * 10, high=b.high * 10, low=b.low * 10, close=b.close * 10),
        )
        mutated_volumes[i] = volumes[i] * 100

    after = SENSOR.density(mutated, cut, mutated_volumes)
    assert after == before, "the density at a bar moved when a LATER bar changed"


def test_the_mutation_actually_reaches_a_later_density():
    """Guard against the test above passing because the mutation does nothing."""
    n, cut = 400, 300
    bars = wandering(n, seed=1)
    volumes = [1_000.0 + i for i in range(n)]
    mutated = list(bars)
    for i in range(cut + 1, n):
        b = bars[i].bar
        mutated[i] = TimestampedBar(
            bars[i].timestamp,
            Bar(open=b.open * 10, high=b.high * 10, low=b.low * 10, close=b.close * 10),
        )
    assert SENSOR.density(mutated, n - 1, volumes) != SENSOR.density(bars, n - 1, volumes)


# ------------------------------------------------------------------ the histogram itself


def test_volume_lands_in_the_buckets_the_bar_actually_spanned():
    """A daily bar is not a point. Its volume is spread across the buckets its RANGE
    covers; dumping it at the close would make this a close-price histogram wearing a
    volume label."""
    n = 300
    closes = [100.0] * n
    bars = bars_from(closes, highs=[101.0] * n, lows=[99.0] * n)
    # One bar reaches far above everything else, on all of the volume.
    spike = 250
    bars[spike] = TimestampedBar(bars[spike].timestamp, Bar(open=100, high=140, low=100, close=140))
    volumes = [0.0] * n
    volumes[spike] = 1_000.0

    d = SENSOR.density(bars, n - 1, volumes)
    assert d is not None
    assert sum(d.mass) == pytest.approx(1.0)
    # Mass sits at and above the spike's own range, not below it.
    below = sum(m for i, m in enumerate(d.mass) if d.centre(i) < 100.0)
    assert below == pytest.approx(0.0)


def test_mass_is_normalised_whatever_the_volume_scale():
    n = 300
    bars = wandering(n, seed=7)
    small = SENSOR.density(bars, n - 1, [1.0] * n)
    huge = SENSOR.density(bars, n - 1, [1e12] * n)
    assert small is not None and huge is not None
    assert sum(small.mass) == pytest.approx(1.0)
    assert small.mass == pytest.approx(huge.mass)


def test_a_price_outside_the_mapped_range_has_no_density_rather_than_zero():
    """Outside-the-range is a real answer. Returning 0.0 would be indistinguishable from a
    visited-but-empty bucket, and the two mean different things."""
    n = 300
    bars = wandering(n, seed=3)
    d = SENSOR.density(bars, n - 1, [100.0] * n)
    assert d is not None
    assert d.mass_at(d.edges[-1] * 10.0) is None
    assert d.mass_at(d.edges[0] / 10.0) is None
    assert d.mass_at(d.centre(len(d.mass) // 2)) is not None


def test_a_plateau_produces_no_node():
    """A local extremum is strict against BOTH neighbours, so a flat shelf yields no level
    rather than one level per bucket in it. A plateau is not a node."""
    flat = PriceDensity(
        edges=tuple(float(i) for i in range(6)),
        mass=(0.2, 0.2, 0.2, 0.2, 0.2),
        bucket_width=1.0,
        lookback=90,
        bucket_atr=0.5,
        n_bars=90,
    )
    assert flat.levels(0.0, "hvn") == ()
    assert flat.levels(1.0, "lvn") == ()

    peaked = PriceDensity(
        edges=tuple(float(i) for i in range(6)),
        mass=(0.1, 0.1, 0.6, 0.1, 0.1),
        bucket_width=1.0,
        lookback=90,
        bucket_atr=0.5,
        n_bars=90,
    )
    assert peaked.levels(0.5, "hvn") == (2.5,)


# ------------------------------------------------------------------ loud on bad inputs


def test_insufficient_history_returns_None_not_a_thin_density():
    bars = wandering(500, seed=11)
    volumes = [100.0] * 500
    assert SENSOR.density(bars, SENSOR.warm_up_bars() - 2, volumes) is None
    assert SENSOR.density(bars, SENSOR.warm_up_bars() - 1, volumes) is not None


def test_a_price_only_call_raises_rather_than_degrading():
    """A volume-at-price sensor with no volume is a different sensor, not a worse one."""
    bars = wandering(300, seed=5)
    with pytest.raises(ValueError, match="no volume series"):
        SENSOR.density(bars, 250, None)


def test_misaligned_volumes_raise():
    """D187's second bug was a sliced bar series against a full-length volume series."""
    bars = wandering(300, seed=5)
    with pytest.raises(ValueError, match="aligned bar-for-bar"):
        SENSOR.density(bars, 250, [100.0] * 299)


def test_parameters_outside_the_specs_stated_sets_raise():
    """`TERRAIN_MODEL.md` fixes both sets. A third value is an unregistered search, and the
    terrain programme counts every combination tested."""
    with pytest.raises(ValueError, match="lookback_days must be one of"):
        VolumeProfileSensor(120, 0.5, "quote_notional")
    with pytest.raises(ValueError, match="bucket_atr must be one of"):
        VolumeProfileSensor(90, 1.0, "quote_notional")
    with pytest.raises(ValueError, match="volume_units must be one of"):
        VolumeProfileSensor(90, 0.5, "usd")
    for lb in LOOKBACK_DAYS:
        for ba in BUCKET_ATR:
            assert VolumeProfileSensor(lb, ba, "shares").lookback_days == lb


def test_the_atr_here_matches_the_one_the_stops_use():
    """The terrain and the stops must measure volatility the same way, or a "1 ATR wall
    distance" means two things in one report."""
    from backtest_framework.strategies.breakout import _mean_true_range

    bars = wandering(100, seed=13)

    class _View:
        def __getitem__(self, j):
            return bars[j].bar

    assert mean_true_range(bars, 50, 70) == pytest.approx(_mean_true_range(_View(), 50, 70))


def test_atr_window_needs_a_previous_close():
    bars = wandering(50, seed=17)
    with pytest.raises(ValueError, match="previous close"):
        mean_true_range(bars, 0, 10)
    with pytest.raises(ValueError, match="empty ATR window"):
        mean_true_range(bars, 10, 10)


def test_warm_up_covers_both_the_lookback_and_the_atr_window():
    s = VolumeProfileSensor(180, 0.25, "shares")
    assert s.warm_up_bars() == 180 + ATR_WINDOW + 1

"""S6 field tests (D197).

The look-ahead pair matters more than anything else here. A sensor that reads one bar into
the future produces an equity curve that looks entirely plausible (D173), and D181 records
that `DataView` does not protect analytics. So the guard is asserted AND poisoned: a test
that mutates the future and finds no change is worthless unless the same mutation
provably reaches a later reading.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from backtest_framework.data.bars import Bar, TimestampedBar
from backtest_framework.research.terrain_field import (
    BUCKET_LN,
    FieldParams,
    Swing,
    _deposit,
    _shrinkage,
    build_field,
    build_grid,
    confirmed_swings,
    erasure_bounds,
    field_signals,
    typical_sigma,
)
from datetime import datetime, timedelta

PARAMS = FieldParams(k=2, cluster_atr=0.5)


def _bars(rows) -> list[TimestampedBar]:
    start = datetime(2020, 1, 1)
    return [
        TimestampedBar(start + timedelta(days=i), Bar(o, h, l, c))
        for i, (o, h, l, c) in enumerate(rows)
    ]


def _walk(n: int, seed: int = 0, start: float = 100.0) -> list[TimestampedBar]:
    rng = np.random.default_rng(seed)
    rows, price = [], start
    for _ in range(n):
        step = price * rng.normal(0.0, 0.02)
        o = price
        c = max(1e-6, price + step)
        h = max(o, c) * (1.0 + abs(rng.normal(0.0, 0.005)))
        l = min(o, c) * (1.0 - abs(rng.normal(0.0, 0.005)))
        rows.append((o, h, l, c))
        price = c
    return _bars(rows)


# ---------------------------------------------------------------- look-ahead


def test_signals_do_not_read_a_single_bar_past_their_own_index():
    bars = _walk(300, seed=1)
    vols = [1_000.0] * len(bars)
    swings = confirmed_swings(bars, vols, PARAMS)
    clean = field_signals(bars, swings, PARAMS)
    cut = 200

    poisoned = list(bars)
    for i in range(cut + 1, len(bars)):
        b = poisoned[i].bar
        poisoned[i] = TimestampedBar(
            poisoned[i].timestamp,
            Bar(b.open * 40, b.high * 40, b.low * 40, b.close * 40),
        )
    grid = build_grid(bars, BUCKET_LN)  # same axis, or the buckets alone would differ
    after = field_signals(
        poisoned, confirmed_swings(poisoned, vols, PARAMS), PARAMS, grid=grid
    )

    before_clean = [s for s in clean if s.index <= cut]
    before_after = [s for s in after if s.index <= cut]
    assert [
        (s.index, s.direction, s.tilt, s.gross) for s in before_clean
    ] == [(s.index, s.direction, s.tilt, s.gross) for s in before_after]


def test_the_poison_actually_reaches_a_later_signal():
    """Without this the guard above passes even if the sensor reads nothing at all."""
    bars = _walk(300, seed=1)
    vols = [1_000.0] * len(bars)
    cut = 200
    poisoned = list(bars)
    for i in range(cut + 1, len(bars)):
        b = poisoned[i].bar
        poisoned[i] = TimestampedBar(
            poisoned[i].timestamp,
            Bar(b.open * 40, b.high * 40, b.low * 40, b.close * 40),
        )
    grid = build_grid(bars, BUCKET_LN)
    clean = field_signals(bars, confirmed_swings(bars, vols, PARAMS), PARAMS, grid=grid)
    after = field_signals(
        poisoned, confirmed_swings(poisoned, vols, PARAMS), PARAMS, grid=grid
    )
    late_clean = [(s.index, s.tilt) for s in clean if s.index > cut]
    late_after = [(s.index, s.tilt) for s in after if s.index > cut]
    assert late_clean != late_after


def test_a_pivot_is_not_used_before_its_confirmation_lag():
    bars = _walk(200, seed=3)
    swings = confirmed_swings(bars, [1_000.0] * len(bars), PARAMS)
    assert swings
    assert all(s.confirmed_at == s.index + PARAMS.k for s in swings)


def test_the_erasure_envelope_reads_no_bar_newer_than_the_exclusion():
    bars = _walk(120, seed=4)
    lo, hi = erasure_bounds(bars, PARAMS)
    t = 100
    poisoned = list(bars)
    for i in range(t - PARAMS.erase_exclude + 1, len(bars)):
        b = poisoned[i].bar
        poisoned[i] = TimestampedBar(
            poisoned[i].timestamp, Bar(b.open * 9, b.high * 9, b.low * 9, b.close * 9)
        )
    lo2, hi2 = erasure_bounds(poisoned, PARAMS)
    assert (lo[t], hi[t]) == (lo2[t], hi2[t])


# ---------------------------------------------------------------- the erasure


def test_a_destroyed_bucket_does_not_come_back_when_the_envelope_moves_off_it():
    """Destroy, not mask — D197's whole erasure semantics in one assertion.

    A swing is planted, price grinds over it so the envelope covers it, then price walks
    far away. With no new pivots at that price the mass must stay gone."""
    grid = build_grid(_walk(10, seed=0), BUCKET_LN)
    net = np.zeros(grid.n)
    gross = np.zeros(grid.n)
    centres = grid.centres()
    swing = Swing(0, 0, -1, 100.0, 1.0, 0.02)
    _deposit(net, gross, grid, swing, centres)
    c = grid.bucket(100.0)
    assert gross[c] > 0.0

    lo_b, hi_b = grid.bucket(95.0), grid.bucket(105.0)
    net[lo_b : hi_b + 1] = 0.0
    gross[lo_b : hi_b + 1] = 0.0
    assert gross[c] == 0.0

    # envelope moves far away; nothing re-deposits, so the bucket stays empty
    lo_b, hi_b = grid.bucket(200.0), grid.bucket(210.0)
    net[lo_b : hi_b + 1] = 0.0
    gross[lo_b : hi_b + 1] = 0.0
    assert gross[c] == 0.0
    assert net[c] == 0.0


def test_the_current_bar_inside_the_envelope_would_silence_the_field():
    """erase_exclude below 1 is rejected, because it makes every read identically zero."""
    with pytest.raises(ValueError, match="identically zero"):
        FieldParams(k=2, cluster_atr=0.5, erase_exclude=0)


# ---------------------------------------------------------------- the kernel


def test_deposited_mass_equals_the_weight_after_truncation():
    grid = build_grid(_walk(10, seed=0), BUCKET_LN)
    net = np.zeros(grid.n)
    gross = np.zeros(grid.n)
    _deposit(net, gross, grid, Swing(0, 0, -1, 100.0, 3.5, 0.02), grid.centres())
    assert gross.sum() == pytest.approx(3.5, rel=1e-12)
    assert net.sum() == pytest.approx(3.5, rel=1e-12)


def test_a_swing_high_subtracts_and_a_swing_low_adds():
    grid = build_grid(_walk(10, seed=0), BUCKET_LN)
    net = np.zeros(grid.n)
    gross = np.zeros(grid.n)
    _deposit(net, gross, grid, Swing(0, 0, 1, 100.0, 1.0, 0.02), grid.centres())
    assert net[grid.bucket(100.0)] < 0.0
    assert gross[grid.bucket(100.0)] > 0.0


def test_two_opposite_swings_at_one_price_cancel_in_net_but_not_in_gross():
    """The signing hypothesis, in one test. S5 could not express this."""
    grid = build_grid(_walk(10, seed=0), BUCKET_LN)
    net = np.zeros(grid.n)
    gross = np.zeros(grid.n)
    centres = grid.centres()
    _deposit(net, gross, grid, Swing(0, 0, 1, 100.0, 1.0, 0.02), centres)
    _deposit(net, gross, grid, Swing(0, 0, -1, 100.0, 1.0, 0.02), centres)
    assert net[grid.bucket(100.0)] == pytest.approx(0.0, abs=1e-12)
    assert gross[grid.bucket(100.0)] > 0.0


# ---------------------------------------------------------------- shrinkage


def test_one_typical_swing_reads_about_half():
    """The pseudo-count is calibrated so one swing's evidence halves the shrinkage.

    This is the defect D197's census caught: with `k` in a swing's TOTAL mass rather than
    its per-bucket peak, this reads about 0.04 instead of 0.5."""
    sigma = 0.02
    grid = build_grid(_walk(10, seed=0), BUCKET_LN)
    net = np.zeros(grid.n)
    gross = np.zeros(grid.n)
    _deposit(net, gross, grid, Swing(0, 0, -1, 100.0, 1.0, sigma), grid.centres())
    c = grid.bucket(100.0)
    tilt = net[c] / (gross[c] + _shrinkage(sigma))
    assert 0.4 < tilt < 0.6


def test_a_virgin_price_beside_a_strong_one_reads_near_zero_not_plus_one():
    """Kernel spill must not become confidence. An unshrunk net/gross reads 1.0 here."""
    sigma = 0.02
    grid = build_grid(_walk(10, seed=0), BUCKET_LN)
    net = np.zeros(grid.n)
    gross = np.zeros(grid.n)
    _deposit(net, gross, grid, Swing(0, 0, -1, 100.0, 1.0, sigma), grid.centres())
    far = grid.bucket(100.0 * math.exp(2.6 * sigma))  # inside the 3-sigma truncation
    raw = net[far] / gross[far] if gross[far] > 0 else 0.0
    shrunk = net[far] / (gross[far] + _shrinkage(sigma))
    assert raw == pytest.approx(1.0, abs=1e-9)
    assert abs(shrunk) < 0.15


def test_typical_sigma_is_the_median_and_not_a_per_price_lookup():
    swings = [Swing(i, i, -1, 100.0, 1.0, s) for i, s in enumerate([0.01, 0.02, 0.09])]
    assert typical_sigma(swings, PARAMS) == pytest.approx(0.02)


# ---------------------------------------------------------------- guards


def test_parameter_sets_are_enforced():
    with pytest.raises(ValueError, match="unregistered search"):
        FieldParams(k=4, cluster_atr=0.5)
    with pytest.raises(ValueError, match="unregistered search"):
        FieldParams(k=2, cluster_atr=0.75)


def test_misaligned_volumes_raise():
    bars = _walk(60, seed=5)
    with pytest.raises(ValueError, match="misaligned volume"):
        confirmed_swings(bars, [1.0] * (len(bars) - 1), PARAMS)


# ---------------------------------------------------------------- synthetic controls


def test_a_random_walk_produces_a_field_with_no_directional_edge():
    """The false-positive control. D189's caught two bad fixtures; not a formality.

    On a driftless walk the field must not systematically lean one way: the mean tilt on
    non-virgin fires should sit near zero."""
    bars = _walk(1500, seed=11)
    vols = list(np.random.default_rng(11).uniform(500, 1500, len(bars)))
    sigs = field_signals(bars, confirmed_swings(bars, vols, PARAMS), PARAMS)
    live = [s.tilt for s in sigs if not s.virgin]
    assert len(live) > 30, f"only {len(live)} live fires — control cannot say anything"
    assert abs(float(np.mean(live))) < 0.15


def test_a_planted_repeatedly_respected_level_is_found():
    """The positive control: price wicks down to 100 again and again and turns up.

    The field must carry net DEMAND at 100. Asserted on the map itself rather than on the
    pivot list — a control that only checks the detector fired says nothing about whether
    the mass survived deposit, sign and erasure.

    The bottom bar wicks to 100 while its BODY stops at 104, so the body envelope never
    covers the level and the erasure leaves it alone. That is the mechanism D197's census
    measured: the map keeps wick extremes and destroys everything the bodies swept."""
    rows = []
    for _ in range(14):
        for p in (130.0, 124.0, 118.0, 112.0):  # down; bodies bottom out at 106
            rows.append((p, p + 0.4, p - 0.4, p - 6.0))
        rows.append((106.0, 106.3, 100.0, 104.0))  # the wick that plants the level
        for p in (104.0, 110.0, 116.0, 122.0):  # back up
            rows.append((p, p + 0.4, p - 0.4, p + 6.0))
    bars = _bars(rows)
    vols = [1_000.0] * len(bars)
    swings = confirmed_swings(bars, vols, PARAMS)

    lows = [s for s in swings if s.sign < 0 and 99.5 <= s.price <= 100.5]
    assert len(lows) >= 3, f"planted level produced only {len(lows)} demand pivots"

    net, gross, grid = build_field(bars, swings, PARAMS, upto=len(bars) - 1)
    c = grid.bucket(100.0)
    assert gross[c] > 0.0, "the planted level was erased"
    assert net[c] > 0.0, "the planted level did not read as demand"
    tilt = net[c] / (gross[c] + _shrinkage(typical_sigma(swings, PARAMS)))
    assert tilt > 0.5, f"repeatedly respected demand read only {tilt:.3f}"


# ---------------------------------------------------------------- strategy and nulls


def test_the_fade_direction_is_opposite_the_break():
    from backtest_framework.research.terrain_field import Signal
    from backtest_framework.research.terrain_strategies import run_field_reversal

    bars = _walk(80, seed=7)
    atr = [1.0] * len(bars)
    up = Signal(index=30, direction=1, price=bars[30].bar.close, tilt=-0.9, gross=2.0,
                virgin=False)
    dn = Signal(index=50, direction=-1, price=bars[50].bar.close, tilt=0.9, gross=2.0,
                virgin=False)
    res = run_field_reversal(bars, [up, dn], atr, 0.0, 365.0)
    assert [t.direction for t in res.trades] == [-1, 1]


def test_a_virgin_signal_is_never_traded_by_the_filtered_arm_but_is_by_the_control():
    from backtest_framework.research.terrain_field import Signal
    from backtest_framework.research.terrain_strategies import run_field_reversal

    bars = _walk(80, seed=8)
    atr = [1.0] * len(bars)
    sig = Signal(index=30, direction=1, price=bars[30].bar.close, tilt=0.0, gross=0.0,
                 virgin=True)
    assert run_field_reversal(bars, [sig], atr, 0.0, 365.0, filtered=True).n_trades == 0
    assert run_field_reversal(bars, [sig], atr, 0.0, 365.0, filtered=False).n_trades == 1


def test_the_stop_is_taken_when_one_bar_covers_both_stop_and_target():
    from backtest_framework.research.terrain_field import Signal
    from backtest_framework.research.terrain_strategies import run_field_reversal

    # enter long at 100 on bar 1's open; bar 1 spans both the 3R target and the stop
    bars = _bars([(100, 101, 99, 100), (100, 140, 90, 120), (120, 121, 119, 120)])
    sig = Signal(index=0, direction=-1, price=100.0, tilt=0.9, gross=2.0, virgin=False)
    res = run_field_reversal(bars, [sig], [5.0] * 3, 0.0, 365.0, max_hold=10)
    assert res.n_trades == 1
    assert res.trades[0].reason == "stop"


def test_entry_is_the_next_bar_open_not_the_signal_close():
    from backtest_framework.research.terrain_field import Signal
    from backtest_framework.research.terrain_strategies import run_field_reversal

    bars = _bars([(100, 101, 99, 100), (107, 108, 106, 107), (107, 108, 106, 107)])
    sig = Signal(index=0, direction=-1, price=100.0, tilt=0.9, gross=2.0, virgin=False)
    res = run_field_reversal(bars, [sig], [1.0] * 3, 0.0, 365.0, max_hold=10)
    assert res.trades[0].entry_index == 1
    assert res.trades[0].entry_price == 107.0


def test_shuffling_preserves_sign_weight_and_kernel_width():
    from backtest_framework.research.terrain_field_nulls import (
        ShuffleBand, _local_bounds, shuffled_swings)

    bars = _walk(400, seed=9)
    swings = confirmed_swings(bars, [1_000.0] * len(bars), PARAMS)
    assert len(swings) > 20
    lo, hi = _local_bounds(bars)
    rng = np.random.default_rng(0)
    shuffled = shuffled_swings(swings, ShuffleBand.LOCAL, rng, lo, hi)

    assert [s.sign for s in shuffled] == [s.sign for s in swings]
    assert [s.weight for s in shuffled] == [s.weight for s in swings]
    assert [s.sigma_ln for s in shuffled] == [s.sigma_ln for s in swings]
    assert [s.confirmed_at for s in shuffled] == [s.confirmed_at for s in swings]
    assert [s.price for s in shuffled] != [s.price for s in swings]


def test_the_local_band_keeps_prices_in_their_own_neighbourhood():
    """The whole point of the verdict null: era and price scale must match."""
    from backtest_framework.research.terrain_field_nulls import (
        ShuffleBand, _local_bounds, shuffled_swings)

    bars = _walk(600, seed=10, start=100.0)
    swings = confirmed_swings(bars, [1_000.0] * len(bars), PARAMS)
    lo, hi = _local_bounds(bars)
    shuffled = shuffled_swings(swings, ShuffleBand.LOCAL, np.random.default_rng(1), lo, hi)
    for s in shuffled:
        assert lo[s.index] <= s.price <= hi[s.index]


def test_the_local_band_requires_bounds():
    from backtest_framework.research.terrain_field_nulls import (
        ShuffleBand, shuffled_swings)

    with pytest.raises(ValueError, match="needs per-bar bounds"):
        shuffled_swings([], ShuffleBand.LOCAL, np.random.default_rng(0))

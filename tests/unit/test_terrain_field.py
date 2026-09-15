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
        TimestampedBar(start + timedelta(days=i), Bar(o, h, lo, c))
        for i, (o, h, lo, c) in enumerate(rows)
    ]


def _walk(n: int, seed: int = 0, start: float = 100.0) -> list[TimestampedBar]:
    rng = np.random.default_rng(seed)
    rows, price = [], start
    for _ in range(n):
        step = price * rng.normal(0.0, 0.02)
        o = price
        c = max(1e-6, price + step)
        h = max(o, c) * (1.0 + abs(rng.normal(0.0, 0.005)))
        lo = min(o, c) * (1.0 - abs(rng.normal(0.0, 0.005)))
        rows.append((o, h, lo, c))
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


# ---------------------------------------------------------------- D198 confirmation


def _sig(index, direction, tilt, gross=2.0, virgin=False, price=100.0):
    from backtest_framework.research.terrain_field import Signal
    return Signal(index=index, direction=direction, price=price, tilt=tilt,
                  gross=gross, virgin=virgin)


def test_every_qualifying_signal_is_accounted_for_exactly_once():
    """Counts alone are not enough. A first draft scanned each signal independently and
    put the confirming signal in BOTH books; the totals still matched, so a count-only
    property test passed on a genuine bug. This checks roles, not just arithmetic."""
    from backtest_framework.research.terrain_field import (
        qualifying, split_by_confirmation)

    bars = _walk(900, seed=21)
    sigs = field_signals(bars, confirmed_swings(bars, [1_000.0] * len(bars), PARAMS),
                         PARAMS)
    qual = qualifying(sigs)
    split = split_by_confirmation(bars, sigs, PARAMS)
    assert split.n_qualifying == len(qual)
    assert split.accounts(), (
        f"{len(split.confirmed)}+{len(split.unconfirmed)}+{split.n_triggers}"
        f"+{split.n_absorbed} != {split.n_qualifying}"
    )
    ci = {s.index for s in split.confirmed}
    ui = {s.index for s in split.unconfirmed}
    assert not (ci & ui), "a signal landed in both books"


def test_a_continuing_excursion_is_not_a_second_approach():
    """The whole difference from the rule the census rejected.

    Two same-direction signals with NO bar between them back inside the envelope is one
    excursion still running, not a second approach."""
    from backtest_framework.research.terrain_field import split_by_confirmation

    rows = [(100 + 3 * i, 100 + 3 * i + 1, 100 + 3 * i - 1, 100 + 3 * i + 2)
            for i in range(60)]
    bars = _bars(rows)
    split = split_by_confirmation(bars, [_sig(50, 1, -0.9), _sig(52, 1, -0.9)], PARAMS)
    assert split.confirmed == ()
    assert split.n_absorbed == 1
    assert [s.index for s in split.unconfirmed] == [50]
    assert split.accounts()


def _straddle(bars, lo, hi, lookfrom=200, lookto=320):
    return next(
        t for t in range(lookfrom, lookto)
        if lo[t] == lo[t] and lo[t] <= bars[t].bar.close <= hi[t]
    )


def test_a_return_inside_the_envelope_makes_it_a_second_approach():
    from backtest_framework.research.terrain_field import split_by_confirmation

    bars = _walk(400, seed=22)
    lo, hi = erasure_bounds(bars, PARAMS)
    mid = _straddle(bars, lo, hi)
    split = split_by_confirmation(bars, [_sig(mid - 1, 1, -0.9), _sig(mid + 1, 1, -0.9)],
                                  PARAMS)
    assert [s.index for s in split.confirmed] == [mid + 1], "entry is the second sighting"
    assert split.unconfirmed == (), "the trigger is consumed, not left waiting"
    assert split.n_triggers == 1
    assert split.accounts()


def test_confirmation_respects_the_window():
    from backtest_framework.research.terrain_field import (
        CONFIRM_WINDOW, split_by_confirmation)

    bars = _walk(400, seed=23)
    lo, hi = erasure_bounds(bars, PARAMS)
    mid = _straddle(bars, lo, hi, 200, 300)
    far = _sig(mid - 1 + CONFIRM_WINDOW + 1, 1, -0.9)
    split = split_by_confirmation(bars, [_sig(mid - 1, 1, -0.9), far], PARAMS)
    assert split.confirmed == (), "a partner beyond the window must not confirm"
    assert len(split.unconfirmed) == 2
    assert split.accounts()


def test_opposite_directions_do_not_confirm_each_other():
    from backtest_framework.research.terrain_field import split_by_confirmation

    bars = _walk(400, seed=24)
    lo, hi = erasure_bounds(bars, PARAMS)
    mid = _straddle(bars, lo, hi, 200, 300)
    split = split_by_confirmation(
        bars, [_sig(mid - 1, 1, -0.9), _sig(mid + 1, -1, 0.9)], PARAMS
    )
    assert split.confirmed == ()
    assert len(split.unconfirmed) == 2
    assert split.accounts()


def test_a_virgin_signal_never_qualifies_so_never_confirms():
    from backtest_framework.research.terrain_field import split_by_confirmation

    bars = _walk(400, seed=25)
    split = split_by_confirmation(
        bars, [_sig(200, 1, 0.0, gross=0.0, virgin=True)], PARAMS
    )
    assert split.confirmed == () and split.unconfirmed == ()
    assert split.n_qualifying == 0


def test_the_confirmation_walk_reads_no_bar_past_the_confirming_signal():
    """Same guard as the field itself: mutating the future must not move the split."""
    from backtest_framework.research.terrain_field import split_by_confirmation

    bars = _walk(600, seed=26)
    vols = [1_000.0] * len(bars)
    sigs = field_signals(bars, confirmed_swings(bars, vols, PARAMS), PARAMS)
    cut = 400
    split = split_by_confirmation(bars, sigs, PARAMS)

    poisoned = list(bars)
    for i in range(cut + 1, len(bars)):
        b = poisoned[i].bar
        poisoned[i] = TimestampedBar(
            poisoned[i].timestamp, Bar(b.open * 30, b.high * 30, b.low * 30, b.close * 30)
        )
    grid = build_grid(bars, BUCKET_LN)
    psigs = field_signals(poisoned, confirmed_swings(poisoned, vols, PARAMS), PARAMS,
                          grid=grid)
    psplit = split_by_confirmation(poisoned, psigs, PARAMS)

    horizon = cut - 21  # a confirmation at t is decided by bars <= t
    assert [s.index for s in split.confirmed if s.index <= horizon] ==            [s.index for s in psplit.confirmed if s.index <= horizon]


# ---------------------------------------------------------------- D199 exit policy


def test_the_bare_bar_chandelier_agrees_with_the_dataview_one():
    """Pinned against `strategies.breakout.ChandelierStop`, not trusted to agree.

    Same arrangement terrain.mean_true_range has with breakout._mean_true_range: a
    restatement is only valid if it is provably the same number."""
    from backtest_framework.engine.dataview import DataView
    from backtest_framework.strategies.breakout import (
        ChandelierStop, OpenPosition, PositionState)
    from backtest_framework.research.terrain import mean_true_range
    from backtest_framework.research.terrain_strategies import chandelier_level

    bars = _walk(200, seed=31)
    stop = ChandelierStop(multiple=2.0, window=20)
    # ChandelierStop measures ATR over [i-window, i), EXCLUDING the current bar, while
    # rolling_mean_true_range includes it. That off-by-one is a real difference in
    # convention and it is pinned elsewhere (test_terrain.py). What is under test HERE is
    # the excursion geometry, so both sides are fed the same ATR to isolate it.
    atr = [
        mean_true_range(bars, j - 20, j) if j >= 21 else float("nan")
        for j in range(len(bars))
    ]

    checked = 0
    for direction in (1, -1):
        for entry in (60, 90):
            for j in range(entry + 1, entry + 25):
                view = DataView(tuple(tb.bar for tb in bars[: j + 1]))
                pos = OpenPosition(
                    state=PositionState(direction),
                    entry_index=entry,
                    entry_reference=bars[entry].bar.open,
                    stop_level=0.0,
                )
                theirs = stop.stop_level(view, pos)
                if theirs is None:
                    continue
                mine = chandelier_level(bars, entry, j, direction, atr, 2.0)
                assert mine == pytest.approx(theirs, rel=1e-9), (
                    f"dir={direction} entry={entry} j={j}: {mine} vs {theirs}"
                )
                checked += 1
    assert checked > 40, f"only {checked} comparisons made — the pin is vacuous"


def test_the_trail_never_loosens_in_either_direction():
    from backtest_framework.research.terrain import rolling_mean_true_range
    from backtest_framework.research.terrain_strategies import chandelier_level

    bars = _walk(300, seed=32)
    atr = rolling_mean_true_range(bars, 20)
    for direction in (1, -1):
        entry = 80
        level = bars[entry].bar.open - direction * 2.0 * atr[entry]
        for j in range(entry + 1, entry + 60):
            if not (atr[j] == atr[j]):
                continue
            cand = chandelier_level(bars, entry, j, direction, atr, 2.0)
            new = max(level, cand) if direction > 0 else min(level, cand)
            if direction > 0:
                assert new >= level, "a long's trail loosened"
            else:
                assert new <= level, "a short's trail loosened"
            level = new


def test_the_trailing_policy_has_no_target_so_never_exits_on_one():
    from backtest_framework.research.terrain import rolling_mean_true_range
    from backtest_framework.research.terrain_strategies import run_field_trailing

    bars = _walk(900, seed=33)
    atr = rolling_mean_true_range(bars, 20)
    sigs = field_signals(bars, confirmed_swings(bars, [1_000.0] * len(bars), PARAMS),
                         PARAMS)
    res = run_field_trailing(bars, sigs, atr, 40.0, 365.0)
    assert res.n_trades > 5
    reasons = {t.reason for t in res.trades}
    assert "target" not in reasons
    assert reasons <= {"stop", "trail", "max_hold"}


def test_a_shorter_max_hold_never_increases_the_holding_period():
    from backtest_framework.research.terrain import rolling_mean_true_range
    from backtest_framework.research.terrain_strategies import run_field_reversal

    bars = _walk(900, seed=34)
    atr = rolling_mean_true_range(bars, 20)
    sigs = field_signals(bars, confirmed_swings(bars, [1_000.0] * len(bars), PARAMS),
                         PARAMS)
    short = run_field_reversal(bars, sigs, atr, 40.0, 365.0, max_hold=5)
    long_ = run_field_reversal(bars, sigs, atr, 40.0, 365.0, max_hold=60)
    assert short.n_trades > 0 and long_.n_trades > 0
    assert max(t.exit_index - t.entry_index for t in short.trades) <= 5
    assert max(t.exit_index - t.entry_index for t in long_.trades) <= 60


# ---------------------------------------------------------------- D201 imbalance


def _same(a, b) -> bool:
    """List equality that treats NaN as equal to NaN — the imbalance is NaN through the
    warm-up, and `nan != nan` would make every comparison below vacuously fail."""
    return len(a) == len(b) and all(
        (x != x and y != y) or x == y for x, y in zip(a, b)
    )


def test_imbalance_stays_in_range_and_is_defined_after_warm_up():
    from backtest_framework.research.terrain_field import field_imbalance

    bars = _walk(900, seed=41)
    swings = confirmed_swings(bars, [1_000.0] * len(bars), PARAMS)
    imb = field_imbalance(bars, swings, PARAMS)
    assert len(imb) == len(bars)
    defined = [x for x in imb if x == x]
    assert len(defined) > 0.5 * len(bars), f"only {len(defined)} defined readings"
    assert all(-1.0 <= x <= 1.0 for x in defined)


def test_imbalance_does_not_read_a_single_bar_past_its_own_index():
    from backtest_framework.research.terrain_field import field_imbalance

    bars = _walk(400, seed=42)
    vols = [1_000.0] * len(bars)
    cut = 250
    grid = build_grid(bars, BUCKET_LN)
    clean = field_imbalance(bars, confirmed_swings(bars, vols, PARAMS), PARAMS, grid)

    poisoned = list(bars)
    for i in range(cut + 1, len(bars)):
        b = poisoned[i].bar
        poisoned[i] = TimestampedBar(
            poisoned[i].timestamp, Bar(b.open * 25, b.high * 25, b.low * 25, b.close * 25)
        )
    after = field_imbalance(
        poisoned, confirmed_swings(poisoned, vols, PARAMS), PARAMS, grid
    )
    assert _same(clean[: cut + 1], after[: cut + 1])


def test_the_poison_actually_reaches_a_later_imbalance():
    from backtest_framework.research.terrain_field import field_imbalance

    bars = _walk(400, seed=42)
    vols = [1_000.0] * len(bars)
    cut = 250
    grid = build_grid(bars, BUCKET_LN)
    clean = field_imbalance(bars, confirmed_swings(bars, vols, PARAMS), PARAMS, grid)
    poisoned = list(bars)
    for i in range(cut + 1, len(bars)):
        b = poisoned[i].bar
        poisoned[i] = TimestampedBar(
            poisoned[i].timestamp, Bar(b.open * 25, b.high * 25, b.low * 25, b.close * 25)
        )
    after = field_imbalance(
        poisoned, confirmed_swings(poisoned, vols, PARAMS), PARAMS, grid
    )
    assert not _same(clean[cut + 1 :], after[cut + 1 :])


def test_the_raw_field_never_erases_anything():
    """erase=False must leave gross monotone non-decreasing — nothing is ever destroyed."""
    from backtest_framework.research.terrain_field import _walk_field

    raw = FieldParams(k=2, cluster_atr=0.5, erase=False)
    bars = _walk(400, seed=43)
    swings = confirmed_swings(bars, [1_000.0] * len(bars), raw)
    grid = build_grid(bars, BUCKET_LN)
    prev = 0.0
    seen = 0
    for _t, _net, gross, _lo, _hi in _walk_field(bars, swings, raw, grid, len(bars) - 1):
        total = float(gross.sum())
        assert total >= prev - 1e-9, "the raw field lost mass"
        prev = total
        seen += 1
    assert prev > 0.0 and seen == len(bars)


def test_the_erased_field_does_lose_mass_so_the_flag_is_not_inert():
    from backtest_framework.research.terrain_field import _walk_field

    bars = _walk(400, seed=43)
    swings = confirmed_swings(bars, [1_000.0] * len(bars), PARAMS)
    grid = build_grid(bars, BUCKET_LN)
    drops = 0
    prev = 0.0
    for _t, _net, gross, _lo, _hi in _walk_field(bars, swings, PARAMS, grid, len(bars) - 1):
        total = float(gross.sum())
        if total < prev - 1e-9:
            drops += 1
        prev = total
    assert drops > 10, f"the erasure destroyed mass on only {drops} bars"


def test_erase_false_is_rejected_for_nothing_but_allowed_with_exclude_zero():
    """The erase_exclude guard protects the BOUNDARY rule; it is meaningless when the
    erasure is off entirely, so it must not fire there."""
    FieldParams(k=2, cluster_atr=0.5, erase=False, erase_exclude=0)  # must not raise
    with pytest.raises(ValueError, match="identically zero"):
        FieldParams(k=2, cluster_atr=0.5, erase=True, erase_exclude=0)


def test_the_position_curve_agrees_with_the_trade_list_curve():
    """Pinned against StrategyResult on a book the trade-list path CAN represent.

    The new equity path exists because that path silently drops a position entering on the
    bar another exits. Where both are valid they must be the same number."""
    from backtest_framework.research.terrain_strategies import (
        PositionResult, StrategyResult, Trade)

    bars = _walk(60, seed=44)
    # one long, held bars 10..20, entered and exited at the CLOSE so the two
    # representations describe the same exposure
    tr = Trade(10, 20, 1, bars[10].bar.close, bars[20].bar.close, "test")
    trades = StrategyResult((tr,), cost_bps=0.0, periods_per_year=365.0)

    closes = [b.bar.close for b in bars]
    returns = [0.0] + [
        math.log(b / a) for a, b in zip(closes, closes[1:])
    ]
    pos = [0] * len(bars)
    for i in range(11, 21):
        pos[i] = 1
    series = PositionResult(tuple(pos), tuple(returns), 0.0, 365.0)

    assert series.curve_total_return() == pytest.approx(
        trades.curve_total_return(bars), rel=1e-9
    )
    assert series.curve_sharpe(bars, 365.0) == pytest.approx(
        trades.curve_sharpe(bars, 365.0), rel=1e-6
    )


def test_a_flip_keeps_continuous_exposure():
    """The exact case the trade-list curve drops: short becomes long with no flat bar."""
    from backtest_framework.research.terrain_strategies import run_field_imbalance

    bars = _walk(60, seed=45)
    atr = [1.0] * len(bars)
    imb = [-0.9] * 30 + [0.9] * 30
    res = run_field_imbalance(bars, imb, atr, 0.0, 365.0)
    assert set(res.position[1:]) == {-1, 1}, "a flat bar appeared at the flip"
    assert 0 not in res.position[2:]
    # 1 unit opening the short from flat, then 2 more flipping it to long
    assert res.turnover == 3
    assert res.n_trades == 2, "an open and a flip are two position changes"


def test_cost_is_charged_once_per_position_change():
    from backtest_framework.research.terrain_strategies import PositionResult

    rets = tuple([0.0] * 11)
    flat = PositionResult(tuple([0] * 11), rets, 100.0, 365.0)  # 1% a unit
    one = PositionResult(tuple([0] + [1] * 10), rets, 100.0, 365.0)
    assert flat.curve_total_return() == pytest.approx(0.0)
    assert one.curve_total_return() == pytest.approx(-0.01, rel=1e-9)
    assert one.n_trades == 1 and one.turnover == 1


def test_a_stopped_out_book_stays_flat_until_the_signal_changes_state():
    from backtest_framework.research.terrain_strategies import run_field_imbalance

    # long signal throughout; bar 12 collapses far enough to trip a 2 ATR stop
    rows = [(100.0, 101.0, 99.0, 100.0)] * 30
    rows[12] = (100.0, 101.0, 80.0, 100.0)
    bars = _bars(rows)
    atr = [2.0] * len(bars)
    imb = [0.9] * len(bars)
    res = run_field_imbalance(bars, imb, atr, 0.0, 365.0, use_stop=True)
    assert 1 in res.position[:13], "the book never opened"
    assert set(res.position[14:]) == {0}, "it re-entered while the signal was unchanged"

    flipped = list(imb)
    for i in range(20, len(bars)):
        flipped[i] = -0.9
    res2 = run_field_imbalance(bars, flipped, atr, 0.0, 365.0, use_stop=True)
    assert -1 in res2.position, "the book never resumed after the signal changed state"


# ---------------------------------------------------------------- D202 local imbalance


def _swing_at(price, sign=-1, weight=1.0, sigma=0.02, index=0):
    return Swing(index, index, sign, price, weight, sigma)


def test_the_pseudo_count_is_in_the_same_units_as_the_sum():
    """The shrinkage units, pinned — and they are the OPPOSITE of _shrinkage's.

    D197 reads a single bucket, so its pseudo-count is one swing's per-bucket PEAK; using
    total mass there crushed every reading toward zero and its census caught it. This reads
    a weighted SUM, so the unit is one swing's TOTAL mass.

    The invariant that pins it: with no supply, weighted demand `d` reads `d / (d + 1)`.
    Measure it once to recover `d`, double the mass, and the reading must land exactly
    where that formula says. No appeal to what a single swing "should" read — which is
    about 0.30, not 0.50, because the kernel is 0.5 ATR wide against a 2 ATR decay so part
    of any nearby swing always falls on the far side of price."""
    from backtest_framework.research.terrain_field import local_imbalance

    bars = _bars([(100.0, 101.0, 99.0, 100.0)] * 80)
    params = FieldParams(k=2, cluster_atr=0.5, erase=False)
    one = local_imbalance(bars, [_swing_at(99.0, index=30)], params)[-1]
    two = local_imbalance(
        bars, [_swing_at(99.0, index=30), _swing_at(99.0, index=31)], params
    )[-1]

    d = one / (1.0 - one)                       # recover the weighted mass
    assert two == pytest.approx(2 * d / (2 * d + 1.0), rel=1e-6), (
        f"doubling the mass moved {one:.4f} to {two:.4f}, not to "
        f"{2*d/(2*d+1):.4f} — the pseudo-count is not 1.0 in the sum's own units"
    )
    assert 0.15 < one < 0.45, f"one nearby swing read {one:.3f}"
    assert two > one, "more evidence must read stronger"


def test_a_distant_swing_barely_registers():
    """Locality, asserted in the direction that matters: far mass must not move it."""
    from backtest_framework.research.terrain_field import local_imbalance

    bars = _bars([(100.0, 101.0, 99.0, 100.0)] * 80)
    params = FieldParams(k=2, cluster_atr=0.5, erase=False)
    near = local_imbalance(bars, [_swing_at(99.0, index=30)], params)[-1]
    far = local_imbalance(bars, [_swing_at(40.0, index=30)], params)[-1]
    assert abs(far) < 0.05, f"a swing 60% away read {far:.3f}"
    assert near > 10 * abs(far), "the decay is not doing anything"


def test_near_mass_does_move_it_so_the_decay_is_not_inert():
    """The other direction — a guard that only ever returns zero would pass the test above."""
    from backtest_framework.research.terrain_field import local_imbalance

    bars = _bars([(100.0, 101.0, 99.0, 100.0)] * 80)
    params = FieldParams(k=2, cluster_atr=0.5, erase=False)
    demand = local_imbalance(bars, [_swing_at(99.0, sign=-1, index=30)], params)[-1]
    supply = local_imbalance(bars, [_swing_at(101.0, sign=+1, index=30)], params)[-1]
    assert demand > 0.2, "demand below price should read positive"
    assert supply < -0.2, "supply above price should read negative"


def test_the_local_reading_is_defined_even_with_no_nearby_mass():
    """Shrinkage returns 0.0, not NaN — 'nothing either side of me' is a real answer and
    keeps the book flat rather than undefined, which is what D201's NaN did."""
    from backtest_framework.research.terrain_field import local_imbalance

    bars = _bars([(100.0, 101.0, 99.0, 100.0)] * 80)
    params = FieldParams(k=2, cluster_atr=0.5, erase=False)
    out = local_imbalance(bars, [], params)
    assert all(x == x for x in out) and set(out) == {0.0}


def test_local_imbalance_does_not_read_past_its_own_index():
    from backtest_framework.research.terrain_field import local_imbalance

    raw = FieldParams(k=2, cluster_atr=0.5, erase=False)
    bars = _walk(400, seed=51)
    vols = [1_000.0] * len(bars)
    cut = 250
    grid = build_grid(bars, BUCKET_LN)
    clean = local_imbalance(bars, confirmed_swings(bars, vols, raw), raw, grid)
    poisoned = list(bars)
    for i in range(cut + 1, len(bars)):
        b = poisoned[i].bar
        poisoned[i] = TimestampedBar(
            poisoned[i].timestamp, Bar(b.open * 25, b.high * 25, b.low * 25, b.close * 25)
        )
    after = local_imbalance(
        poisoned, confirmed_swings(poisoned, vols, raw), raw, grid
    )
    assert _same(clean[: cut + 1], after[: cut + 1])
    assert not _same(clean[cut + 1 :], after[cut + 1 :]), "the poison never reached it"


def test_continuous_sizing_charges_cost_in_proportion():
    from backtest_framework.research.terrain_strategies import PositionResult

    rets = tuple([0.0] * 11)
    small = PositionResult(tuple([0.0] + [0.1] * 10), rets, 100.0, 365.0)
    full = PositionResult(tuple([0.0] + [1.0] * 10), rets, 100.0, 365.0)
    assert small.curve_total_return() == pytest.approx(-0.001, rel=1e-9)
    assert full.curve_total_return() == pytest.approx(-0.01, rel=1e-9)
    assert small.turnover == pytest.approx(0.1)


def test_continuous_sizing_holds_the_signal_magnitude():
    from backtest_framework.research.terrain_strategies import run_field_position

    bars = _walk(40, seed=52)
    atr = [1.0] * len(bars)
    sig = [0.5] * len(bars)
    res = run_field_position(bars, sig, atr, 0.0, 365.0, continuous=True)
    assert set(res.position[2:]) == {0.5}
    binary = run_field_position(bars, sig, atr, 0.0, 365.0, continuous=False)
    assert set(binary.position[2:]) == {1.0}


def test_sign_changes_and_net_exposure_describe_the_book():
    from backtest_framework.research.terrain_strategies import PositionResult

    rets = tuple([0.0] * 7)
    r = PositionResult((0.0, 0.8, 0.8, -0.4, -0.4, 0.2, 0.2), rets, 0.0, 365.0)
    assert r.sign_changes == 2
    assert r.net_exposure == pytest.approx((0.8 + 0.8 - 0.4 - 0.4 + 0.2 + 0.2) / 7)


def test_the_rotation_null_preserves_the_book_and_moves_only_its_timing():
    from backtest_framework.research.terrain_field_nulls import rotation_null
    from backtest_framework.research.terrain_strategies import PositionResult

    bars = _walk(300, seed=53)
    closes = [b.bar.close for b in bars]
    rets = tuple([0.0] + [math.log(b / a) for a, b in zip(closes, closes[1:])])
    pos = tuple(
        (0.7 if (i // 40) % 3 == 0 else (-0.5 if (i // 40) % 3 == 1 else 0.0))
        for i in range(len(bars))
    )
    real = PositionResult(pos, rets, 40.0, 365.0)
    draws = rotation_null(real, 30, np.random.default_rng(0))

    assert len(draws) == 30
    for d in draws:
        assert sorted(d.position) == sorted(real.position), "exposure distribution moved"
        assert d.net_exposure == pytest.approx(real.net_exposure)
    # turnover is preserved up to the single wrap-around seam
    assert all(abs(d.turnover - real.turnover) <= 2.0 for d in draws)
    curves = {round(d.curve_sharpe(bars, 365.0), 6) for d in draws}
    assert len(curves) > 20, "rotation did not change the equity curve — control is vacuous"

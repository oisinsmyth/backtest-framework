"""Property-based invariants for the D217 MACD ladder.

`tests/unit/test_macd.py` checks the anchoring property at three hand-picked
indices on one deterministic path. That is the right shape for a gate and the
wrong shape for a guarantee. This file quantifies over the paths and the index.

The distinction that makes this file necessary is D181's: `DataView` makes
look-ahead structurally impossible for a STRATEGY, because the view arrives
already sliced. `research/macd.py` is ANALYTICS — it is handed the whole bar
sequence, and nothing structural stops `macd_series` from reading `closes[t+1]`.
D181 is the record of what that gap costs: an ensemble weighted itself with
whole-sample volatility for as long as it existed, inside a project with a
look-ahead guard, because the guard does not reach analytics.

Nothing stops it. This file is what does.

Conventions (D78): hypothesis with `derandomize=True`, so the suite is
byte-deterministic in CI and hypothesis owns the seeding.

WHY THE WINDOWS ARE QUANTIFIED OVER AND NOT PINNED AT 12/26/9
--------------------------------------------------------------
Every property here — anchoring, scale invariance, the PPO identity, the gate's
one-sidedness — is a property of the RULE, not of Appel's triple. Pinning the
windows at 12/26/9 would force a 393-bar minimum path, which hypothesis flags as
too large a base example to shrink usefully: the suite would quantify over far
fewer paths and produce unreadable counterexamples. So the windows are drawn,
with (12, 26, 9) in the set so the default is still covered, and the numerical
burn-in behaviour that IS specific to the default lives in
`tests/unit/test_macd.py` where it belongs.

The start index here is the seed span rather than the full warm-up for the same
reason: causality holds at every bar, burn-in or not, and requiring the burn-in
would be testing the study's trading policy instead of the estimator's honesty.
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta

from hypothesis import given, settings, strategies as st

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.macd import (
    MATCHED_MOMENTUM_LOOKBACK,
    crossings,
    macd_series,
    positions,
    signal_line_score,
    trailing_ma,
    trailing_return_score,
    warm_up_bars,
    zero_line_score,
)
from backtest_framework.simulator.fills import Bar

SETTINGS = settings(derandomize=True, max_examples=40, deadline=None)
EPOCH = datetime(2020, 1, 1)

MIN_BARS = 90
MAX_BARS = 220

# (12, 26, 9) included so the default configuration is still quantified over.
WINDOWS = st.sampled_from([(3, 7, 3), (4, 9, 3), (5, 12, 4), (12, 26, 9)])
GATE_WINDOW = 20


def _start(windows):
    """The ladder's common start: the seed span, shared by every arm (D217)."""
    return warm_up_bars(*windows, include_burn_in=False)


@st.composite
def bar_paths(draw, min_bars=MIN_BARS, max_bars=MAX_BARS):
    """Random OHLC paths with consistent bars — high >= max(open, close) and so on."""
    n = draw(st.integers(min_bars, max_bars))
    moves = draw(st.lists(st.floats(-0.06, 0.06, allow_nan=False), min_size=n, max_size=n))
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
        out.append(TimestampedBar(EPOCH + timedelta(days=i), Bar(o, h, lo, c)))
    return out


def corrupt_after(bars, index):
    """Replace everything after `index` with a violently different path.

    Deliberately not a nudge: an estimator reading one bar ahead survives a nudge."""
    out = list(bars[: index + 1])
    px = bars[index].bar.close
    for i in range(index + 1, len(bars)):
        px *= 1.7 if (i % 3) else 0.55
        o, c = px, px * 1.02
        out.append(
            TimestampedBar(bars[i].timestamp, Bar(o, max(o, c) * 1.05, min(o, c) * 0.95, c))
        )
    return out


def _same(a, b, upto):
    for t in range(upto + 1):
        if math.isnan(a[t]) or math.isnan(b[t]):
            assert math.isnan(a[t]) and math.isnan(b[t]), f"NaN disagreement at {t}"
        else:
            assert a[t] == b[t], f"value moved at {t}: {a[t]} != {b[t]}"


@SETTINGS
@given(bars=bar_paths(), frac=st.floats(0.35, 0.9), windows=WINDOWS)
def test_perturbing_future_bars_cannot_change_todays_indicator(bars, frac, windows):
    """The load-bearing property. Exact equality, not approx — an anchored recompute
    over an unchanged prefix does identical floating-point arithmetic, so anything
    less than `==` would be hiding a real leak behind a tolerance."""
    index = int(len(bars) * frac)
    base = macd_series(bars, *windows)
    corrupted = macd_series(corrupt_after(bars, index), *windows)
    _same(base.macd, corrupted.macd, index)
    _same(base.signal, corrupted.signal, index)
    _same(base.histogram, corrupted.histogram, index)


@SETTINGS
@given(
    bars=bar_paths(),
    frac=st.floats(0.35, 0.9),
    long_short=st.booleans(),
    windows=WINDOWS,
)
def test_perturbing_future_bars_cannot_change_todays_position(
    bars, frac, long_short, windows
):
    """The same property one layer up, over all three rungs, because a leak that
    cancels in the indicator and survives in the sign would still be a leak."""
    index = int(len(bars) * frac)
    start = _start(windows)
    other = corrupt_after(bars, index)

    for score_of in (
        lambda b: zero_line_score(macd_series(b, *windows)),
        lambda b: signal_line_score(macd_series(b, *windows)),
        lambda b: trailing_return_score(b, MATCHED_MOMENTUM_LOOKBACK),
    ):
        a = positions(score_of(bars), start=start, long_short=long_short)
        c = positions(score_of(other), start=start, long_short=long_short)
        assert a[: index + 1] == c[: index + 1]


@SETTINGS
@given(bars=bar_paths(), frac=st.floats(0.35, 0.9))
def test_the_gate_cannot_read_the_future_either(bars, frac):
    """The moving-average confluence filter is an auxiliary estimate, and D44 binds it."""
    index = int(len(bars) * frac)
    _same(
        trailing_ma(bars, GATE_WINDOW),
        trailing_ma(corrupt_after(bars, index), GATE_WINDOW),
        index,
    )


@SETTINGS
@given(bars=bar_paths(), frac=st.floats(0.4, 0.95), windows=WINDOWS)
def test_truncating_the_series_cannot_move_a_value_that_already_existed(
    bars, frac, windows
):
    """Stated separately from the corruption property because it is what an
    INCREMENTAL implementation would fail. If the anchored recompute is ever
    replaced by a stateful one for speed, this is the test that must still pass."""
    index = int(len(bars) * frac)
    full = macd_series(bars, *windows)
    truncated = macd_series(bars[: index + 1], *windows)
    _same(full.macd, truncated.macd, index)
    _same(full.signal, truncated.signal, index)


@SETTINGS
@given(bars=bar_paths(), exponent=st.integers(-12, 12), windows=WINDOWS)
def test_the_sign_rule_is_invariant_to_a_power_of_two_rescale(bars, exponent, windows):
    """Powers of two so the rescale is bit-exact and the assertion means what it says."""
    factor = 2.0**exponent
    scaled = [
        TimestampedBar(
            b.timestamp,
            Bar(
                b.bar.open * factor,
                b.bar.high * factor,
                b.bar.low * factor,
                b.bar.close * factor,
            ),
        )
        for b in bars
    ]
    start = _start(windows)
    for score_of in (zero_line_score, signal_line_score):
        assert positions(
            score_of(macd_series(bars, *windows)), start=start, long_short=True
        ) == positions(
            score_of(macd_series(scaled, *windows)), start=start, long_short=True
        )


@SETTINGS
@given(bars=bar_paths(), windows=WINDOWS)
def test_normalising_by_any_positive_series_leaves_the_zero_line_arm_alone(bars, windows):
    """The PPO identity, quantified: sign(macd/d) == sign(macd) for positive d.

    This is why D217 does not sweep normalisation for rungs 2 and 3 — it would buy
    a provable no-op and cost real trials."""
    series = macd_series(bars, *windows)
    closes = [b.bar.close for b in bars]
    start = _start(windows)
    divided = tuple(m / c for m, c in zip(series.macd, closes))
    assert positions(divided, start=start, long_short=True) == positions(
        zero_line_score(series), start=start, long_short=True
    )


@SETTINGS
@given(bars=bar_paths(), long_short=st.booleans(), windows=WINDOWS)
def test_the_book_is_flat_through_the_warm_up_and_never_exceeds_one_unit(
    bars, long_short, windows
):
    start = _start(windows)
    for score_of in (
        lambda b: zero_line_score(macd_series(b, *windows)),
        lambda b: signal_line_score(macd_series(b, *windows)),
        lambda b: trailing_return_score(b, MATCHED_MOMENTUM_LOOKBACK),
    ):
        pos = positions(score_of(bars), start=start, long_short=long_short)
        assert all(p == 0.0 for p in pos[:start])
        assert all(abs(p) <= 1.0 for p in pos)
        if not long_short:
            assert all(p >= 0.0 for p in pos)


@SETTINGS
@given(bars=bar_paths(), windows=WINDOWS)
def test_the_gate_can_only_remove_exposure_never_invert_it(bars, windows):
    series = macd_series(bars, *windows)
    closes = [b.bar.close for b in bars]
    start = _start(windows)
    gate = trailing_ma(bars, GATE_WINDOW)
    ungated = positions(zero_line_score(series), start=start, long_short=True)
    gated = positions(
        zero_line_score(series), start=start, long_short=True, gate=gate, closes=closes
    )
    for u, g in zip(ungated, gated):
        assert g == u or g == 0.0


@SETTINGS
@given(bars=bar_paths(), windows=WINDOWS)
def test_replay_is_deterministic(bars, windows):
    start = _start(windows)
    first = macd_series(bars, *windows)
    second = macd_series(bars, *windows)
    assert first == second
    assert crossings(
        positions(zero_line_score(first), start=start, long_short=True)
    ) == crossings(positions(zero_line_score(second), start=start, long_short=True))

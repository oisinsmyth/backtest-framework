"""Golden master for the D217 MACD ladder — the twin of test_macd_golden.hand.txt.

D39/D77: the hand file is ground truth produced without running the codebase, and
if the two disagree the argument happens there, not here.

Two things make this golden stronger than most:

  * MACD(3, 7, 3) has alphas 1/2, 1/4, 1/2, and the closes were chosen so both
    SMA seeds and the signal seed divide exactly. Every value in the walk is
    therefore a DYADIC RATIONAL and exactly representable, so these assertions
    are `==` rather than `approx`. Nothing is hidden behind a tolerance.
  * The scenario makes the two rungs DISAGREE, at t=9 and t=10. A golden that
    only pinned arithmetic would not notice the ladder quietly collapsing into
    one rule; this one does.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from fractions import Fraction

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.macd import (
    crossings,
    macd_series,
    positions,
    signal_line_score,
    warm_up_bars,
    zero_line_score,
)
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2021, 1, 1)

CLOSES = [100, 101, 103, 102, 104, 106, 105, 108, 112, 109, 104, 100, 98, 101, 106, 110]
FAST, SLOW, SIGNAL = 3, 7, 3
START = 8  # the ladder's common start, = (SLOW-1) + (SIGNAL-1)

# Transcribed from test_macd_golden.hand.txt as exact fractions, so a typo in the
# transcription is a different number rather than a rounded one.
HAND_MACD = {
    6: Fraction(2),
    7: Fraction(9, 4),
    8: Fraction(49, 16),
    9: Fraction(143, 64),
    10: Fraction(101, 256),
    11: Fraction(-1377, 1024),
    12: Fraction(-9539, 4096),
    13: Fraction(-27145, 16384),
    14: Fraction(3429, 65536),
    15: Fraction(442159, 262144),
}
HAND_SIGNAL = {
    8: Fraction(39, 16),
    9: Fraction(299, 128),
    10: Fraction(699, 512),
    11: Fraction(21, 2048),
    12: Fraction(-9497, 8192),
    13: Fraction(-46139, 32768),
    14: Fraction(-88849, 131072),
    15: Fraction(264461, 524288),
}
HAND_HIST = {
    8: Fraction(5, 8),
    9: Fraction(-13, 128),
    10: Fraction(-497, 512),
    11: Fraction(-2775, 2048),
    12: Fraction(-9581, 8192),
    13: Fraction(-8151, 32768),
    14: Fraction(95707, 131072),
    15: Fraction(619857, 524288),
}

HAND_ZERO_ARM = (0,) * 8 + (1, 1, 1, -1, -1, -1, 1, 1)
HAND_SIGNAL_ARM = (0,) * 8 + (1, -1, -1, -1, -1, -1, 1, 1)


@pytest.fixture(scope="module")
def series():
    bars = [
        TimestampedBar(EPOCH + timedelta(days=i), Bar(float(c), float(c), float(c), float(c)))
        for i, c in enumerate(CLOSES)
    ]
    return bars, macd_series(bars, FAST, SLOW, SIGNAL)


def test_every_dyadic_value_is_exact_not_approximate():
    """If any hand value were non-dyadic this test would be lying about `==` below."""
    for table in (HAND_MACD, HAND_SIGNAL, HAND_HIST):
        for value in table.values():
            assert Fraction(float(value)) == value, f"{value} is not exactly a float"


def test_the_seeds_are_the_hand_computed_ones(series):
    _, s = series
    assert s.first_macd_index == 6
    assert s.first_signal_index == 8
    # ema_fast[6] - ema_slow[6] = 105 - 103 = 2, both seeds dividing exactly.
    assert s.macd[6] == 2.0
    assert s.signal[8] == 2.4375


def test_the_macd_line_bar_by_bar(series):
    _, s = series
    for t, expected in HAND_MACD.items():
        assert s.macd[t] == float(expected), f"macd[{t}]"


def test_the_signal_line_bar_by_bar(series):
    _, s = series
    for t, expected in HAND_SIGNAL.items():
        assert s.signal[t] == float(expected), f"signal[{t}]"


def test_the_histogram_bar_by_bar(series):
    _, s = series
    for t, expected in HAND_HIST.items():
        assert s.histogram[t] == float(expected), f"hist[{t}]"


def test_nothing_exists_before_its_own_seed(series):
    _, s = series
    assert all(v != v for v in s.macd[:6])
    assert all(v != v for v in s.signal[:8])


def test_the_zero_line_arm_walks_the_hand_computed_path(series):
    _, s = series
    assert positions(zero_line_score(s), start=START, long_short=True) == tuple(
        float(p) for p in HAND_ZERO_ARM
    )


def test_the_signal_line_arm_walks_the_hand_computed_path(series):
    _, s = series
    assert positions(signal_line_score(s), start=START, long_short=True) == tuple(
        float(p) for p in HAND_SIGNAL_ARM
    )


def test_the_two_arms_hold_opposite_positions_at_bars_nine_and_ten(series):
    """The nesting, pinned as behaviour rather than as prose.

    The MACD is still positive at t=9 and t=10 — the trend is up — while the
    histogram has turned negative — the trend is decelerating. If a future edit
    ever makes these two arms agree everywhere, the ladder has collapsed into one
    rule and D217's central question has quietly stopped being asked."""
    _, s = series
    zero = positions(zero_line_score(s), start=START, long_short=True)
    sig = positions(signal_line_score(s), start=START, long_short=True)
    for t in (9, 10):
        assert zero[t] == 1.0
        assert sig[t] == -1.0
    assert zero != sig


def test_the_long_flat_book_holds_cash_where_the_long_short_book_is_short(series):
    _, s = series
    flat = positions(zero_line_score(s), start=START, long_short=False)
    assert flat == tuple(max(p, 0.0) for p in HAND_ZERO_ARM)


def test_position_changes_match_the_hand_count(series):
    _, s = series
    assert crossings(positions(zero_line_score(s), start=START, long_short=True)) == 3
    assert crossings(positions(signal_line_score(s), start=START, long_short=True)) == 3


def test_the_burn_in_moves_only_the_first_tradeable_bar_never_a_value(series):
    """The claim SETUP makes in the hand file, asserted rather than asserted-in-prose."""
    bars, s = series
    assert warm_up_bars(FAST, SLOW, SIGNAL, include_burn_in=False) == START
    assert warm_up_bars(FAST, SLOW, SIGNAL) > START
    again = macd_series(bars, FAST, SLOW, SIGNAL)
    assert again == s

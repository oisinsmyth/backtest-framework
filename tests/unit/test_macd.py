"""Unit gates for the D217 MACD ladder.

Most of this file is not testing "does the code compute MACD". It is pinning the
four claims the STUDY rests on, in executable form, so that a later edit cannot
quietly make the ladder non-nested and leave the write-up asserting something the
code no longer does:

  1. the MACD is a weighted moving average of past returns, kernel c_i;
  2. that kernel sums to 7.0 and centres on 18.0 bars, so the matched flat control
     is 37 and not the obvious 26;
  3. the signal line's kernel sums to ZERO — it is trend acceleration, not trend;
  4. rungs 1 and 2 read one indicator, so they cannot desynchronise.

If the ladder stops being nested, the study stops meaning anything, and these are
the tests that make that a red suite rather than a silent change of subject.
"""

from __future__ import annotations

import math
import statistics
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.macd import (
    DEFAULT_FAST,
    DEFAULT_SIGNAL,
    DEFAULT_SLOW,
    MATCHED_MOMENTUM_LOOKBACK,
    burn_in_bars,
    crossings,
    macd_series,
    positions,
    return_kernel,
    signal_line_score,
    trailing_ma,
    trailing_return_score,
    warm_up_bars,
    zero_line_score,
)
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2020, 1, 1)
TOLERANCE = 1e-9


def bars_from(closes):
    return [
        TimestampedBar(EPOCH + timedelta(days=i), Bar(c, c * 1.01, c * 0.99, c))
        for i, c in enumerate(closes)
    ]


def _independent_macd(closes, fast, slow, signal, seed):
    """A second implementation that shares no code with the module under test.

    `seed` picks the convention: "sma" is the module's, "first" seeds each EMA at
    the first close, "zero" seeds at 0.0. Used to show the module's choice differs
    from the alternatives BEFORE the burn-in and agrees with them after it."""

    def ema(series, n, start_index, seed_value):
        a = 2.0 / (n + 1.0)
        out = [math.nan] * len(series)
        e = seed_value
        out[start_index] = e
        for t in range(start_index + 1, len(series)):
            e = e + a * (series[t] - e)
            out[t] = e
        return out

    s = slow - 1
    if seed == "sma":
        slow_seed = sum(closes[0:slow]) / slow
        fast_seed = sum(closes[slow - fast : slow]) / fast
    elif seed == "first":
        slow_seed = fast_seed = closes[0]
    elif seed == "zero":
        slow_seed = fast_seed = 0.0
    else:  # pragma: no cover - guard against a typo in a parametrize list
        raise AssertionError(seed)

    es = ema(closes, slow, s, slow_seed)
    ef = ema(closes, fast, s, fast_seed)
    macd = [
        (ef[t] - es[t]) if t >= s else math.nan for t in range(len(closes))
    ]
    ss = s + signal - 1
    sig_seed = sum(macd[s : s + signal]) / signal
    sig = ema(macd, signal, ss, sig_seed)
    return macd, sig


# --------------------------------------------------------------------------
# The seed convention and the burn-in
# --------------------------------------------------------------------------


def test_the_module_agrees_with_an_independent_calculator_on_the_stated_seed():
    closes = [100.0 + 7.0 * math.sin(i / 9.0) + i * 0.05 for i in range(400)]
    series = macd_series(bars_from(closes))
    macd, sig = _independent_macd(closes, DEFAULT_FAST, DEFAULT_SLOW, DEFAULT_SIGNAL, "sma")
    for t in range(DEFAULT_SLOW - 1, len(closes)):
        assert series.macd[t] == pytest.approx(macd[t], abs=1e-12)
    for t in range(series.first_signal_index, len(closes)):
        assert series.signal[t] == pytest.approx(sig[t], abs=1e-12)


def test_the_ema_seed_choice_is_alive_before_the_burn_in_and_dead_after_it():
    """Both halves matter. The second alone would pass if the burn-in did nothing."""
    closes = [100.0 + 5.0 * math.sin(i / 11.0) for i in range(700)]
    ours = macd_series(bars_from(closes))
    zeroed, _ = _independent_macd(closes, DEFAULT_FAST, DEFAULT_SLOW, DEFAULT_SIGNAL, "zero")

    first = DEFAULT_SLOW - 1
    assert abs(ours.macd[first] - zeroed[first]) > 0.01 * closes[first]

    after = warm_up_bars()
    for t in range(after, len(closes)):
        assert abs(ours.macd[t] - zeroed[t]) <= 1e-12 * closes[t]


def test_the_burn_in_is_the_decay_arithmetic_and_the_slow_leg_binds():
    assert burn_in_bars(12) == 166
    assert burn_in_bars(9) == 124
    assert burn_in_bars(26) == 360
    # If a future parameter change inverts this, the warm-up below is wrong.
    assert burn_in_bars(DEFAULT_SLOW) > burn_in_bars(DEFAULT_FAST)
    assert burn_in_bars(DEFAULT_SLOW) > burn_in_bars(DEFAULT_SIGNAL)


def test_warm_up_is_the_seed_span_plus_the_burn_in():
    assert warm_up_bars(12, 26, 9) == 25 + 8 + 360 == 393
    assert warm_up_bars(12, 26, 9, include_burn_in=False) == 33


def test_the_sma_seed_is_exact_on_a_linear_ramp():
    """The property that justifies the seed choice, pinned rather than asserted."""
    closes = [100.0 + float(t) for t in range(60)]
    series = macd_series(bars_from(closes))
    seed = DEFAULT_SLOW - 1
    # ema_slow lags by (26-1)/2 = 12.5, ema_fast by (12-1)/2 = 5.5, exactly.
    assert series.macd[seed] == pytest.approx(12.5 - 5.5, abs=1e-12)


# --------------------------------------------------------------------------
# The thesis: MACD is a weighting of past returns
# --------------------------------------------------------------------------


@pytest.mark.parametrize("lag", [0, 1, 4, 8, 20, 50])
def test_a_permanent_price_step_enters_the_macd_at_its_closed_form_weight(lag):
    """`macd_t = sum_i c_i * r_(t-i)` — the study's thesis, in executable form."""
    step_at = 150
    closes = [100.0] * step_at + [101.0] * 120
    series = macd_series(bars_from(closes))
    kernel = return_kernel(DEFAULT_FAST, DEFAULT_SLOW, lag + 1)
    assert series.macd[step_at + lag] == pytest.approx(kernel[lag], rel=1e-11, abs=1e-13)


def test_the_kernel_weights_sum_to_seven_and_centre_on_bar_eighteen():
    kernel = return_kernel(DEFAULT_FAST, DEFAULT_SLOW, 4000)
    total = sum(kernel)
    com = sum(i * c for i, c in enumerate(kernel)) / total
    assert total == pytest.approx((DEFAULT_SLOW - 1) / 2 - (DEFAULT_FAST - 1) / 2, rel=1e-12)
    assert total == pytest.approx(7.0, rel=1e-12)
    assert com == pytest.approx(18.0, rel=1e-9)
    assert all(c > 0.0 for c in kernel[:200])


def test_the_matched_momentum_control_shares_the_kernels_centre_of_mass():
    """37, not 26. A flat N-bar kernel centres at (N-1)/2, so N = 2*18 + 1."""
    com = (DEFAULT_SLOW - 1) / 2 + (DEFAULT_FAST - 1) / 2
    assert com == 18.0
    assert MATCHED_MOMENTUM_LOOKBACK == int(2 * com + 1) == 37


def test_the_macd_reads_a_constant_drift_as_seven_times_it():
    for slope in (0.25, 1.0, 3.0):
        closes = [100.0 + slope * t for t in range(200)]
        series = macd_series(bars_from(closes))
        assert series.macd[150] == pytest.approx(7.0 * slope, abs=1e-9)


def test_the_signal_line_has_no_response_to_a_constant_drift():
    """The exact statement of what the signal line adds: it is trend ACCELERATION.

    Under constant drift the MACD sits at 7b and the signal line converges to 7b,
    so the histogram is identically zero. Rung 1 is not measuring the trend."""
    closes = [100.0 + 1.5 * t for t in range(200)]
    series = macd_series(bars_from(closes))
    for t in range(series.first_signal_index, 200):
        assert series.histogram[t] == pytest.approx(0.0, abs=1e-9)


# --------------------------------------------------------------------------
# Nestedness — structural, not prose
# --------------------------------------------------------------------------


def test_the_two_macd_arms_read_one_indicator():
    closes = [100.0 + 6.0 * math.sin(i / 8.0) for i in range(500)]
    series = macd_series(bars_from(closes))
    assert zero_line_score(series) is series.macd
    assert signal_line_score(series) is series.histogram
    for t in range(series.first_signal_index, 500):
        assert series.histogram[t] == pytest.approx(
            series.macd[t] - series.signal[t], abs=1e-12
        )


def test_the_zero_line_arm_cannot_be_moved_by_the_signal_window():
    closes = [100.0 + 6.0 * math.sin(i / 8.0) for i in range(600)]
    bars = bars_from(closes)
    start = warm_up_bars(12, 26, 50)
    nine = macd_series(bars, 12, 26, 9)
    fifty = macd_series(bars, 12, 26, 50)

    assert positions(zero_line_score(nine), start=start, long_short=True) == positions(
        zero_line_score(fifty), start=start, long_short=True
    )
    # ...while the signal-line arm plainly is moved by it, or the rung is a no-op.
    assert positions(signal_line_score(nine), start=start, long_short=True) != positions(
        signal_line_score(fifty), start=start, long_short=True
    )


# --------------------------------------------------------------------------
# Scale invariance, and the PPO identity
# --------------------------------------------------------------------------


@pytest.mark.parametrize("factor", [2.0**10, 2.0**-10])
def test_a_pure_sign_rule_is_invariant_to_rescaling_the_whole_path(factor):
    """Powers of two, so the rescale is bit-exact and the test asserts what it means."""
    closes = [100.0 + 9.0 * math.sin(i / 7.0) + 0.02 * i for i in range(600)]
    start = warm_up_bars()
    base = macd_series(bars_from(closes))
    scaled = macd_series(bars_from([c * factor for c in closes]))

    for score in (zero_line_score, signal_line_score):
        assert positions(score(base), start=start, long_short=True) == positions(
            score(scaled), start=start, long_short=True
        )


def test_normalising_by_a_positive_series_cannot_move_the_zero_line_arm():
    """PPO's zero-line cross and MACD's are the SAME STRATEGY, bar for bar."""
    closes = [100.0 * (1.0 + 0.004) ** i + 8.0 * math.sin(i / 6.0) for i in range(600)]
    bars = bars_from(closes)
    series = macd_series(bars)
    start = warm_up_bars()

    ppo = tuple(m / c for m, c in zip(series.macd, closes))
    assert positions(ppo, start=start, long_short=True) == positions(
        zero_line_score(series), start=start, long_short=True
    )


def test_normalising_does_move_the_signal_line_arm():
    """So PPO-signal and MACD-signal are two hypotheses, not one in two costumes.

    D217 parks the distinction rather than sweeping it; this test is why it is a
    real distinction and not a stylistic one."""
    closes = [100.0 * (1.0 + 0.01) ** i + 12.0 * math.sin(i / 5.0) for i in range(600)]
    bars = bars_from(closes)
    raw = macd_series(bars)
    start = warm_up_bars()

    ppo_bars = bars_from([100.0 * math.log(c) for c in closes])
    ppo = macd_series(ppo_bars)
    assert positions(signal_line_score(ppo), start=start, long_short=True) != positions(
        signal_line_score(raw), start=start, long_short=True
    )


# --------------------------------------------------------------------------
# Anchoring, ties, gates, and the loud guards
# --------------------------------------------------------------------------


def test_the_macd_at_a_bar_is_a_pure_function_of_the_bars_up_to_it():
    """Anchored recompute: truncating the future cannot move a past value."""
    closes = [100.0 + 4.0 * math.sin(i / 5.0) for i in range(500)]
    bars = bars_from(closes)
    full = macd_series(bars)
    for i in (120, 300, 460):
        truncated = macd_series(bars[: i + 1])
        assert truncated.macd[i] == full.macd[i]
        assert truncated.signal[i] == full.signal[i]


def test_a_flat_market_is_an_exact_tie_and_the_book_stays_flat():
    series = macd_series(bars_from([100.0] * 500))
    assert series.macd[400] == 0.0
    assert series.histogram[400] == 0.0
    pos = positions(zero_line_score(series), start=warm_up_bars(), long_short=True)
    assert set(pos) == {0.0}


def test_values_before_their_seed_are_nan_never_partial():
    series = macd_series(bars_from([100.0 + i for i in range(100)]))
    assert all(math.isnan(v) for v in series.macd[: series.first_macd_index])
    assert not math.isnan(series.macd[series.first_macd_index])
    assert all(math.isnan(v) for v in series.signal[: series.first_signal_index])
    assert not math.isnan(series.signal[series.first_signal_index])


def test_a_short_series_yields_all_nan_rather_than_raising():
    series = macd_series(bars_from([100.0] * 10))
    assert all(math.isnan(v) for v in series.macd)


def test_the_long_flat_book_is_never_short_and_the_long_short_book_flips():
    closes = [100.0 + 10.0 * math.sin(i / 9.0) for i in range(700)]
    series = macd_series(bars_from(closes))
    start = warm_up_bars()
    flat = positions(zero_line_score(series), start=start, long_short=False)
    both = positions(zero_line_score(series), start=start, long_short=True)
    assert min(flat) == 0.0 and max(flat) == 1.0
    assert min(both) == -1.0 and max(both) == 1.0
    assert all(p == 0.0 for p in flat[:start])


def test_the_ladder_starts_every_arm_on_the_same_bar():
    """If arms began on their own warm-ups the curves would cover different spans."""
    closes = [100.0 + 5.0 * math.sin(i / 6.0) for i in range(700)]
    bars = bars_from(closes)
    series = macd_series(bars)
    start = warm_up_bars()
    arms = (
        positions(signal_line_score(series), start=start, long_short=True),
        positions(zero_line_score(series), start=start, long_short=True),
        positions(trailing_return_score(bars), start=start, long_short=True),
    )
    for arm in arms:
        assert all(p == 0.0 for p in arm[:start])
        assert any(p != 0.0 for p in arm[start:])


def test_the_gate_stands_aside_rather_than_inverting():
    closes = [100.0 + 10.0 * math.sin(i / 9.0) for i in range(700)]
    bars = bars_from(closes)
    series = macd_series(bars)
    start = warm_up_bars()
    gate = trailing_ma(bars, 200)
    ungated = positions(zero_line_score(series), start=start, long_short=True)
    gated = positions(
        zero_line_score(series), start=start, long_short=True, gate=gate, closes=closes
    )
    for u, g in zip(ungated, gated):
        assert g == u or g == 0.0
    assert crossings(gated) <= crossings(ungated) * 3


def test_trailing_ma_is_the_mean_of_the_window_ending_at_the_bar():
    closes = [float(i) for i in range(50)]
    ma = trailing_ma(bars_from(closes), 10)
    assert math.isnan(ma[8])
    assert ma[9] == pytest.approx(statistics.fmean(closes[0:10]), abs=1e-12)
    assert ma[30] == pytest.approx(statistics.fmean(closes[21:31]), abs=1e-12)


def test_trailing_return_is_nan_until_its_lookback_exists():
    score = trailing_return_score(bars_from([100.0 + i for i in range(100)]), 37)
    assert all(math.isnan(v) for v in score[:37])
    assert score[37] == pytest.approx(137.0 / 100.0 - 1.0, abs=1e-12)


@pytest.mark.parametrize(
    "fast,slow,signal",
    [(26, 12, 9), (12, 12, 9), (1, 26, 9), (12, 26, 1), (12, 1, 9)],
)
def test_degenerate_parameters_are_refused_loudly(fast, slow, signal):
    with pytest.raises(ValueError):
        macd_series(bars_from([100.0] * 50), fast, slow, signal)


def test_crossings_counts_position_changes():
    assert crossings([0.0, 0.0, 1.0, 1.0, -1.0, -1.0, 0.0]) == 3
    assert crossings([1.0] * 10) == 0

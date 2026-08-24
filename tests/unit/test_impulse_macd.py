"""Unit gates for Impulse MACD (LazyBear) — D218.

Same shape as `test_macd.py` and for the same reason: most of this file is not
checking that the code computes the indicator, it is pinning the claims D218's
DESIGN rests on, so that an edit which quietly breaks the replication turns the
suite red rather than changing the subject.

The four load-bearing ones:

  1. `smma` is Wilder smoothing — an EMA with alpha = 1/n, NOT 2/(n+1) — and it
     lags a ramp by exactly (n-1)*b;
  2. `zlema` has centre of mass EXACTLY ZERO, so on a ramp it equals the price;
  3. therefore `md = 33b` on constant drift and the histogram is identically
     zero — the same level/acceleration split D217 found, on a construction that
     shares no arithmetic with MACD;
  4. I2 and I3 differ ONLY by the dead zone.

If (1)-(3) stop holding, D218 is no longer a replication of D217 and its
predictions no longer mean what the record says they mean.
"""

from __future__ import annotations

import math
import statistics
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.macd import (
    IMPULSE_LENGTH,
    SEED_RESIDUAL,
    IMPULSE_SIGNAL,
    burn_in_for_alpha,
    impulse_band_score,
    impulse_macd_series,
    impulse_no_deadzone_score,
    impulse_signal_score,
    impulse_warm_up_bars,
    positions,
    smma,
    zlema,
)
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2020, 1, 1)


def ohlc_bars(closes, half_range=0.0):
    return [
        TimestampedBar(
            EPOCH + timedelta(days=i),
            Bar(c, c + half_range, c - half_range, c),
        )
        for i, c in enumerate(closes)
    ]


def ramp(slope, n=1400, start=100.0):
    return [start + slope * t for t in range(n)]


# --------------------------------------------------------------------------
# 1. smma is Wilder, not the 2/(n+1) EMA
# --------------------------------------------------------------------------


def test_smma_is_an_ema_with_alpha_one_over_n():
    """Independently recursed, so a change of convention cannot slip through."""
    values = [100.0 + 5.0 * math.sin(i / 7.0) for i in range(300)]
    n = 34
    got = smma(values, n)
    expected = statistics.fmean(values[:n])
    assert got[n - 1] == pytest.approx(expected, abs=1e-12)
    for t in range(n, len(values)):
        expected += (values[t] - expected) / n
        assert got[t] == pytest.approx(expected, abs=1e-9)


def test_smma_is_not_the_same_estimator_as_the_macd_ema():
    """alpha = 1/34 against 2/35 is nearly a factor of two in lag; if these ever
    agree, one of them has silently adopted the other's convention."""
    values = ramp(1.0, n=1400)
    wilder = smma(values, 34)
    assert wilder[1300] == pytest.approx(values[1300] - 33.0, abs=1e-6)
    # The 2/(n+1) convention would lag by (n-1)/2 = 16.5, not 33.
    assert abs((values[1300] - wilder[1300]) - 16.5) > 1.0


def test_the_sma_seed_is_exact_for_the_macd_ema_and_NOT_for_wilder():
    """The asymmetry that explains the whole burn-in gap between the two studies.

    An SMA of the last n values lags a ramp by (n-1)/2. An EMA's steady-state lag
    is (1-alpha)/alpha. Those coincide ONLY at alpha = 2/(n+1) — which is why
    D217's `macd = 7b` identity held exactly with no burn-in at all, while Wilder
    smoothing (alpha = 1/n, lag n-1 = 33) is seeded 16.5b away from its own steady
    state and has to decay there over 926 bars.

    So the 926-bar burn-in is not conservatism. It is the price of a seed that does
    not fit its own recursion, and it is a real property of the published
    indicator rather than a choice this project made."""
    n, slope = 34, 1.0
    values = ramp(slope, n=1400)
    seed_index = n - 1
    seed = statistics.fmean(values[:n])

    wilder_steady = values[seed_index] - (n - 1) * slope
    macd_steady = values[seed_index] - ((n - 1) / 2) * slope

    assert seed == pytest.approx(macd_steady, abs=1e-12)  # exact for 2/(n+1)
    assert abs(seed - wilder_steady) == pytest.approx(((n - 1) / 2) * slope, abs=1e-12)
    assert abs(seed - wilder_steady) > 16.0  # 16.5b of seed error, decaying at 33/34


@pytest.mark.parametrize("slope", [0.5, 1.0, 2.5])
def test_smma_lags_a_ramp_by_exactly_n_minus_one_times_the_slope(slope):
    values = ramp(slope, n=1400)
    got = smma(values, IMPULSE_LENGTH)
    assert values[1300] - got[1300] == pytest.approx(
        (IMPULSE_LENGTH - 1) * slope, abs=1e-6
    )


# --------------------------------------------------------------------------
# 2. zlema really has zero lag
# --------------------------------------------------------------------------


@pytest.mark.parametrize("slope", [0.5, 1.0, 2.5])
def test_zlema_has_centre_of_mass_exactly_zero(slope):
    """EMA1 lags by (n-1)/2 and EMA2 by (n-1), so 2*EMA1 - EMA2 lags by zero.
    On a ramp the zero-lag EMA IS the price. The name is accurate."""
    values = ramp(slope, n=1400)
    got = zlema(values, IMPULSE_LENGTH)
    assert got[1300] == pytest.approx(values[1300], abs=1e-6)


def test_zlema_cannot_exist_until_its_second_ema_has_a_full_window():
    values = ramp(1.0, n=200)
    got = zlema(values, 34)
    first = 2 * (34 - 1)
    assert all(math.isnan(v) for v in got[:first])
    assert not math.isnan(got[first])


# --------------------------------------------------------------------------
# 3. The consequence: md = 33b, histogram = 0. THE REPLICATION CLAIM.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("slope", [0.5, 1.5, 3.0])
def test_the_impulse_reads_constant_drift_as_thirty_three_times_it(slope):
    """The counterpart of `macd = 7b`. `md` is a trend-LEVEL rule."""
    series = impulse_macd_series(ohlc_bars(ramp(slope)))
    assert series.md[1300] == pytest.approx((IMPULSE_LENGTH - 1) * slope, abs=1e-6)


def test_the_impulse_signal_line_has_no_response_to_a_constant_drift():
    """`sh` is a trend-ACCELERATION rule, exactly as D217's histogram is. This is
    the property that makes D218 a replication rather than a new question."""
    series = impulse_macd_series(ohlc_bars(ramp(1.5)))
    for t in range(1200, 1400):
        assert series.histogram[t] == pytest.approx(0.0, abs=1e-6)


def test_the_two_indicators_read_the_same_drift_at_different_scales():
    """7b against 33b: same shape, different gain. Neither is a signal; both are
    a lag times a slope, which is what a trend-LEVEL rule is."""
    from backtest_framework.research.macd import macd_series

    bars = ohlc_bars(ramp(1.0))
    assert macd_series(bars).macd[1300] == pytest.approx(7.0, abs=1e-9)
    assert impulse_macd_series(bars).md[1300] == pytest.approx(33.0, abs=1e-6)


# --------------------------------------------------------------------------
# 4. The dead zone
# --------------------------------------------------------------------------


def test_the_dead_zone_is_an_exact_zero_and_the_book_stands_aside_in_it():
    """A flat market puts mi inside the channel, and `md` is 0.0 exactly — a
    stated value, not a missing one, so the sign rule stands aside rather than
    guessing."""
    series = impulse_macd_series(ohlc_bars([100.0] * 1200, half_range=1.0))
    assert series.md[1100] == 0.0
    pos = positions(impulse_band_score(series), start=impulse_warm_up_bars(), long_short=True)
    assert set(pos) == {0.0}


def test_the_sign_of_md_is_exactly_the_band_state():
    closes = [100.0 + 9.0 * math.sin(i / 60.0) for i in range(1400)]
    series = impulse_macd_series(ohlc_bars(closes, half_range=0.6))
    checked = 0
    for t in range(series.first_md_index, len(closes)):
        if math.isnan(series.md[t]):
            continue
        checked += 1
        if series.md[t] > 0:
            assert series.mi[t] > series.hi[t]
        elif series.md[t] < 0:
            assert series.mi[t] < series.lo[t]
        else:
            assert series.lo[t] <= series.mi[t] <= series.hi[t]
    assert checked > 1000


def test_deleting_the_dead_zone_is_the_only_difference_between_i2_and_i3():
    """I3 is I2 with the channel collapsed to its midpoint. Where I2 stands aside,
    I3 must take a side — otherwise the two rungs are not isolating the dead zone
    and D218's hurdle A is measuring nothing."""
    closes = [100.0 + 9.0 * math.sin(i / 60.0) for i in range(1400)]
    series = impulse_macd_series(ohlc_bars(closes, half_range=0.8))
    i2 = impulse_band_score(series)
    i3 = impulse_no_deadzone_score(series)
    flat = [
        t
        for t in range(series.first_md_index, len(closes))
        if i2[t] == 0.0 and not math.isnan(i3[t])
    ]
    assert len(flat) > 50, "the test path never enters the dead zone"
    assert sum(1 for t in flat if i3[t] != 0.0) > 0.95 * len(flat)


def test_a_wider_channel_widens_the_dead_zone():
    closes = [100.0 + 4.0 * math.sin(i / 50.0) for i in range(1400)]
    start = impulse_warm_up_bars()
    narrow = impulse_macd_series(ohlc_bars(closes, half_range=0.1))
    wide = impulse_macd_series(ohlc_bars(closes, half_range=3.0))
    exposure = lambda s: sum(  # noqa: E731
        abs(p)
        for p in positions(impulse_band_score(s), start=start, long_short=True)
    )
    assert exposure(wide) < exposure(narrow)


# --------------------------------------------------------------------------
# 5. Warm-up, which is a finding in its own right
# --------------------------------------------------------------------------


def test_the_wilder_burn_in_is_far_longer_than_the_macd_one():
    """alpha = 1/34 decays so slowly that the seed takes 926 bars to stop
    mattering — against 360 for the 26-period EMA. Roughly four years of daily
    data before the indicator's numbers stop depending on where you started it."""
    assert burn_in_for_alpha(1.0 / 34) == 926
    assert burn_in_for_alpha(2.0 / 35) == 470
    assert impulse_warm_up_bars() == 2 * 33 + 8 + 926 == 1000
    assert impulse_warm_up_bars(include_burn_in=False) == 74


def test_the_seed_choice_is_dead_after_the_burn_in():
    values = [100.0 + 5.0 * math.sin(i / 40.0) for i in range(1600)]
    ours = smma(values, IMPULSE_LENGTH)
    zeroed = [math.nan] * len(values)
    current = 0.0
    zeroed[IMPULSE_LENGTH - 1] = current
    for t in range(IMPULSE_LENGTH, len(values)):
        current += (values[t] - current) / IMPULSE_LENGTH
        zeroed[t] = current
    seed_index = IMPULSE_LENGTH - 1
    seed_error = abs(ours[seed_index] - zeroed[seed_index])
    assert seed_error > 50.0
    # What the burn-in guarantees is a residual of SEED_RESIDUAL times the SEED
    # ERROR — not times the price at some later bar, which is a different number
    # and was the bound this test first (wrongly) asserted.
    for t in range(seed_index + burn_in_for_alpha(1.0 / IMPULSE_LENGTH), len(values)):
        assert abs(ours[t] - zeroed[t]) <= SEED_RESIDUAL * seed_error


# --------------------------------------------------------------------------
# 6. Structure, scale, causality, guards
# --------------------------------------------------------------------------


def test_the_two_rungs_read_one_series():
    series = impulse_macd_series(ohlc_bars([100.0 + 6.0 * math.sin(i / 30.0) for i in range(1400)], 0.5))
    assert impulse_band_score(series) is series.md
    assert impulse_signal_score(series) is series.histogram


def test_the_indicator_reads_hlc3_and_not_the_close():
    closes = [100.0 + 3.0 * math.sin(i / 25.0) for i in range(1400)]
    tight = impulse_macd_series(ohlc_bars(closes, half_range=0.05))
    wide = impulse_macd_series(ohlc_bars(closes, half_range=2.0))
    # hlc3 is unchanged by a symmetric range, but the CHANNEL is not, so md moves.
    assert tight.mi[1300] == pytest.approx(wide.mi[1300], abs=1e-9)
    assert tight.md[1300] != pytest.approx(wide.md[1300], abs=1e-6)


@pytest.mark.parametrize("factor", [2.0**8, 2.0**-8])
def test_the_sign_rule_is_invariant_to_rescaling_the_whole_path(factor):
    closes = [100.0 + 7.0 * math.sin(i / 33.0) + 0.01 * i for i in range(1400)]
    start = impulse_warm_up_bars()
    base = impulse_macd_series(ohlc_bars(closes, half_range=0.5))
    scaled = impulse_macd_series(ohlc_bars([c * factor for c in closes], half_range=0.5 * factor))
    for score in (impulse_band_score, impulse_signal_score):
        assert positions(score(base), start=start, long_short=True) == positions(
            score(scaled), start=start, long_short=True
        )


def test_the_value_at_a_bar_is_a_pure_function_of_the_bars_up_to_it():
    bars = ohlc_bars([100.0 + 5.0 * math.sin(i / 21.0) for i in range(1400)], 0.4)
    full = impulse_macd_series(bars)
    for i in (900, 1100, 1350):
        truncated = impulse_macd_series(bars[: i + 1])
        assert truncated.md[i] == full.md[i]
        assert truncated.signal[i] == full.signal[i]


def test_nothing_exists_before_its_own_seed():
    series = impulse_macd_series(ohlc_bars(ramp(1.0, n=200), 0.3))
    assert all(math.isnan(v) for v in series.md[: series.first_md_index])
    assert all(math.isnan(v) for v in series.signal[: series.first_signal_index])
    assert not math.isnan(series.signal[series.first_signal_index])


def test_a_short_series_yields_all_nan_rather_than_raising():
    series = impulse_macd_series(ohlc_bars([100.0] * 20, 0.2))
    assert all(math.isnan(v) for v in series.md)


@pytest.mark.parametrize("length,signal", [(1, 9), (34, 1), (0, 9)])
def test_degenerate_parameters_are_refused_loudly(length, signal):
    with pytest.raises(ValueError):
        impulse_macd_series(ohlc_bars([100.0] * 200, 0.2), length, signal)


def test_burn_in_for_alpha_refuses_a_nonsensical_alpha():
    for bad in (0.0, 1.0, -0.5, 2.0):
        with pytest.raises(ValueError):
            burn_in_for_alpha(bad)


def test_the_published_defaults_are_lazybears():
    assert (IMPULSE_LENGTH, IMPULSE_SIGNAL) == (34, 9)

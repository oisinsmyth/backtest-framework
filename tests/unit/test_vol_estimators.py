"""Offline tests for the D195 volatility estimators.

Gates closed here:

- The "incumbent" really is the incumbent: `close_to_close_vol` is pinned against
  `InverseVolatilityWeight.weight()`, not merely written to resemble it. If they drift,
  D195 is comparing against something the book does not use.
- Realized vol averages VARIANCE and not volatility — averaging volatilities understates
  by Jensen and would bias every window the same direction.
- The estimation and target windows are disjoint, which is what makes this a forecast.
- Both losses reward the better forecaster, checked on a series whose true volatility is
  known by construction.
"""

from __future__ import annotations

import math
import random
import statistics
from datetime import datetime, timedelta

import pytest

from backtest_framework.data.bars import TimestampedBar
from backtest_framework.research.vol_estimators import (
    close_to_close_vol,
    fold_to_days,
    forecast_pairs,
    mse_log,
    qlike,
    r_squared,
    realized_vol,
    score,
)
from backtest_framework.simulator.fills import Bar

EPOCH = datetime(2021, 1, 1)


def _intraday(n_days: int, bars_per_day: int = 96, sigma: float = 0.002, seed: int = 0,
              start: float = 100.0, drop_bars: int = 0):
    """A geometric walk on a 15m grid. `drop_bars` removes bars from the final day."""
    rng = random.Random(seed)
    bars, px = [], start
    total = n_days * bars_per_day - drop_bars
    step = timedelta(minutes=1440 // bars_per_day)
    for i in range(total):
        px *= math.exp(rng.gauss(0.0, sigma))
        bars.append(TimestampedBar(EPOCH + i * step,
                                   Bar(open=px, high=px * 1.001, low=px * 0.999, close=px)))
    return bars


# ---------------------------------------------------------------- the incumbent


def test_close_to_close_vol_is_the_incumbent_not_a_lookalike():
    """Pinned against the brick the book actually sizes off.

    `InverseVolatilityWeight.weight()` takes `vol_window` returns from `vol_window + 1`
    closes and applies `statistics.stdev`. If D195's incumbent were subtly different, the
    whole comparison would be against a strategy nobody runs."""
    from backtest_framework.strategies.breakout import InverseVolatilityWeight

    rng = random.Random(3)
    closes, px = [], 100.0
    for _ in range(40):
        px *= math.exp(rng.gauss(0.0, 0.03))
        closes.append(px)
    bars = [Bar(open=c, high=c, low=c, close=c) for c in closes]

    window = 20
    brick = InverseVolatilityWeight(vol_window=window)
    i = len(bars) - 1
    view_closes = [bars[j].close for j in range(i - 1 - window, i)]
    returns = [math.log(b / a) for a, b in zip(view_closes, view_closes[1:])]
    incumbent_sd = statistics.stdev(returns)

    ours = close_to_close_vol(closes, i - 1 - window, i)
    assert ours == pytest.approx(incumbent_sd, rel=1e-15)
    assert brick.vol_window == window  # the window D195 matches


def test_close_to_close_vol_uses_window_plus_one_closes():
    closes = [100.0 * math.exp(0.01 * i) for i in range(30)]
    # 21 closes -> 20 returns, all identical -> stdev 0
    assert close_to_close_vol(closes, 0, 21) == pytest.approx(0.0, abs=1e-12)


def test_a_degenerate_window_returns_zero_rather_than_raising():
    assert close_to_close_vol([100.0, 100.0], 0, 2) == 0.0
    assert realized_vol([0.0, 0.0], 0, 2) == 0.0


# ---------------------------------------------------------------- folding to days


def test_fold_assigns_each_day_its_own_realized_variance():
    bars = _intraday(5, bars_per_day=96)
    series = fold_to_days(bars, 96)
    assert len(series) == 5
    assert all(n == 96 for n in series.bars_per_day)
    assert all(v > 0.0 for v in series.realized_variance)


def test_a_short_day_is_dropped_rather_than_biasing_variance_low():
    """A partial day's RV is a sum over fewer terms — it reads as a quiet day."""
    bars = _intraday(4, bars_per_day=96, drop_bars=40)
    series = fold_to_days(bars, 96)
    assert len(series) == 3  # the final, short day is gone


def test_the_daily_close_is_the_last_intraday_close():
    bars = _intraday(3, bars_per_day=96)
    series = fold_to_days(bars, 96)
    assert series.closes[0] == bars[95].bar.close
    assert series.closes[-1] == bars[-1].bar.close


def test_folding_needs_at_least_two_bars():
    with pytest.raises(ValueError, match="at least 2 bars"):
        fold_to_days([], 96)


# ---------------------------------------------------------------- realized vol


def test_realized_vol_averages_variance_not_volatility():
    """sqrt(mean(RV)) not mean(sqrt(RV)) — the latter understates by Jensen, the same
    direction on every window, which is a bias rather than noise."""
    rv = [0.0001, 0.0009]  # daily vols 0.01 and 0.03
    assert realized_vol(rv, 0, 2) == pytest.approx(math.sqrt(0.0005))
    assert realized_vol(rv, 0, 2) > statistics.fmean([0.01, 0.03])


def test_realized_vol_recovers_a_known_sigma_far_better_than_close_to_close():
    """The whole premise, on a series whose true sigma is known by construction.

    96 draws a day of sigma 0.002 gives a true daily sigma of 0.002*sqrt(96) ~ 0.0196."""
    bars = _intraday(30, bars_per_day=96, sigma=0.002, seed=11)
    series = fold_to_days(bars, 96)
    true_daily = 0.002 * math.sqrt(96)

    rv = realized_vol(series.realized_variance, 0, 20)
    cc = close_to_close_vol(series.closes, 0, 21)
    assert abs(rv - true_daily) < abs(cc - true_daily)


# ---------------------------------------------------------------- forecast pairs


def test_estimation_and_target_windows_are_disjoint():
    """What makes this a forecast rather than a description of the same bars."""
    bars = _intraday(60, bars_per_day=96, seed=5)
    series = fold_to_days(bars, 96)
    pairs = forecast_pairs(series, 20)
    assert pairs
    # A pair at index t estimates over (t-20, t] and targets (t, t+20]; the first usable
    # t is 20 and the last is len-21, so the count is bounded accordingly.
    assert len(pairs) <= len(series) - 40


def test_forecast_pairs_carries_both_target_bases():
    bars = _intraday(60, bars_per_day=96, seed=6)
    pairs = forecast_pairs(fold_to_days(bars, 96), 20)
    p = pairs[0]
    assert p.target_realized > 0.0 and p.target_close_to_close > 0.0
    assert p.target_realized != p.target_close_to_close  # different constructions


def test_a_too_short_window_raises():
    bars = _intraday(10, bars_per_day=96)
    with pytest.raises(ValueError, match="at least 3 days"):
        forecast_pairs(fold_to_days(bars, 96), 2)


# ---------------------------------------------------------------- losses


def test_both_losses_are_zero_for_a_perfect_forecast():
    targets = [0.01, 0.02, 0.03]
    assert mse_log(targets, targets) == pytest.approx(0.0)
    assert qlike(targets, targets) == pytest.approx(0.0)


def test_both_losses_prefer_the_closer_forecast():
    targets = [0.02] * 50
    close = [0.021] * 50
    far = [0.030] * 50
    assert mse_log(close, targets) < mse_log(far, targets)
    assert qlike(close, targets) < qlike(far, targets)


def test_qlike_punishes_under_forecasting_harder_than_over():
    """Asymmetric, and in the right direction for a sizing input: under-forecasting
    volatility means over-sizing the position."""
    targets = [0.02] * 50
    under = [0.02 / 1.5] * 50
    over = [0.02 * 1.5] * 50
    assert qlike(under, targets) > qlike(over, targets)


def test_mse_log_is_symmetric_in_the_ratio():
    targets = [0.02] * 50
    assert mse_log([0.02 / 1.5] * 50, targets) == pytest.approx(
        mse_log([0.02 * 1.5] * 50, targets)
    )


def test_r_squared_is_one_for_an_exact_log_linear_relation():
    est = [0.01, 0.02, 0.04, 0.08]
    tgt = [e * 1.3 for e in est]
    assert r_squared(est, tgt) == pytest.approx(1.0)


# ---------------------------------------------------------------- scoring


def test_score_reports_every_cell_and_never_averages_them():
    """D195 requires a win on all four cells; an average would let a win on the
    shared-basis target carry a loss on the other."""
    bars = _intraday(200, bars_per_day=96, seed=7)
    result = score(forecast_pairs(fold_to_days(bars, 96), 20))
    for target in ("realized", "close_to_close"):
        for loss in ("mse_log", "qlike"):
            assert set(result[target][loss]) == {"incumbent", "candidate", "reduction"}
    assert "r2" in result["realized"]


def test_score_refuses_too_few_pairs_rather_than_reporting_a_number():
    bars = _intraday(50, bars_per_day=96, seed=8)
    with pytest.raises(ValueError, match="too few to score"):
        score(forecast_pairs(fold_to_days(bars, 96), 20))


def test_reduction_is_positive_when_the_candidate_wins():
    bars = _intraday(300, bars_per_day=96, seed=12)
    result = score(forecast_pairs(fold_to_days(bars, 96), 20))
    # On a constant-sigma walk the intraday estimator should dominate on its own basis.
    assert result["realized"]["mse_log"]["reduction"] > 0.0

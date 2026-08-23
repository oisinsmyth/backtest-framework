"""Two volatility estimators, and the losses that compare them (D195).

Pure and offline. The question is whether a realized volatility built from 15m returns
forecasts the next twenty days better than the twenty close-to-close daily returns
`InverseVolatilityWeight` currently sizes off.

## Both estimators come from ONE series

The daily series is resampled from the 15m fixture rather than loaded from the yfinance
daily one. Provider, span and calendar are then identical by construction and the
estimator is the only thing that differs — which is the entire content of the comparison.
Loading the incumbent from its original provider would have reintroduced exactly the
confound D194's span-matched control existed to remove.

## Units

Both estimators are expressed as **per-day** volatility, so they are directly comparable
and directly substitutable into a rule that expects a daily sigma.

- Close-to-close: sample stdev of daily log returns. Per-day by construction.
- Realized: for each UTC day, `RV_d = sum of squared 15m log returns in that day`; the
  window estimate is `sqrt(mean(RV_d))`. Per-day, because `RV_d` is already a day's
  variance.

## The shared-basis trap this module is built to expose

The most accurate available target is realized volatility from 15m returns. But the
candidate estimator is built the same way, so any systematic component in 15m realized
variance — microstructure noise inflating it consistently — is inherited by BOTH the
estimator and the target, flattering the candidate for a reason that has nothing to do
with forecasting skill.

So `forecast_pairs` returns both target constructions and the caller scores both. A
candidate that wins only on the target sharing its own basis has not been shown to be
better; it has been shown to be self-consistent.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Sequence

from ..data.bars import TimestampedBar

TRADING_DAYS = 365
"""Crypto's calendar (D108), used only if a caller annualises. Nothing here does."""


@dataclass(frozen=True)
class DailySeries:
    """A 15m series folded to UTC days, carrying both a close and a realized variance.

    `realized_variance[i]` is the sum of squared 15m log returns inside day `days[i]`, so
    it is a day's variance and `sqrt` of it is that day's volatility.
    """

    days: tuple[date, ...]
    closes: tuple[float, ...]
    realized_variance: tuple[float, ...]
    bars_per_day: tuple[int, ...]

    def __len__(self) -> int:
        return len(self.days)


def fold_to_days(bars: Sequence[TimestampedBar], min_bars_per_day: int) -> DailySeries:
    """Fold intraday bars into daily closes plus per-day realized variance.

    The return spanning a day boundary is assigned to the day it ENDS in, so no return is
    dropped and none is double counted — crypto trades continuously, so that bar is a real
    observation rather than an overnight gap.

    Days holding fewer than `min_bars_per_day` bars are dropped. A partial day's realized
    variance is a sum over fewer terms and is biased low, and a biased estimate that looks
    like a low-volatility day is worse than a missing one.
    """
    if len(bars) < 2:
        raise ValueError(f"need at least 2 bars to form a return, got {len(bars)}")

    variance: dict[date, float] = defaultdict(float)
    counts: dict[date, int] = defaultdict(int)
    last_close: dict[date, float] = {}
    order: list[date] = []

    for i, tb in enumerate(bars):
        day = tb.timestamp.date()
        if day not in counts:
            order.append(day)
        counts[day] += 1
        last_close[day] = tb.bar.close
        if i == 0:
            continue
        prev, cur = bars[i - 1].bar.close, tb.bar.close
        if prev > 0.0 and cur > 0.0:
            r = math.log(cur / prev)
            variance[day] += r * r

    keep = [d for d in order if counts[d] >= min_bars_per_day]
    return DailySeries(
        days=tuple(keep),
        closes=tuple(last_close[d] for d in keep),
        realized_variance=tuple(variance[d] for d in keep),
        bars_per_day=tuple(counts[d] for d in keep),
    )


def close_to_close_vol(closes: Sequence[float], start: int, end: int) -> float:
    """Sample stdev of daily close-to-close log returns over `closes[start:end]`.

    Deliberately the same arithmetic as `InverseVolatilityWeight` — this IS the incumbent,
    not a reimplementation of something like it, and the tests pin the two together.
    """
    window = closes[start:end]
    if len(window) < 3:
        return 0.0
    rets = [
        math.log(b / a) for a, b in zip(window, window[1:]) if a > 0.0 and b > 0.0
    ]
    if len(rets) < 2:
        return 0.0
    return statistics.stdev(rets)


def realized_vol(realized_variance: Sequence[float], start: int, end: int) -> float:
    """Per-day volatility from intraday realized variance over `[start, end)`.

    `sqrt(mean(RV_d))`, not `mean(sqrt(RV_d))`. Variance is what averages; averaging
    volatilities and calling the result a volatility understates it by Jensen's
    inequality, which is a small error that would run the same direction on every window.
    """
    window = [v for v in realized_variance[start:end] if v > 0.0]
    if len(window) < 2:
        return 0.0
    return math.sqrt(statistics.fmean(window))


@dataclass(frozen=True)
class ForecastPair:
    """One (estimate, outcome) observation, at one day, for both bases."""

    day: date
    incumbent: float
    """Estimator A — 20-day close-to-close stdev."""
    candidate: float
    """Estimator B — 20-day realized vol from 15m returns."""
    target_realized: float
    """Forward window measured the accurate way. Shares B's basis."""
    target_close_to_close: float
    """Forward window measured on the incumbent's own basis. Shares A's."""


def forecast_pairs(series: DailySeries, window: int) -> list[ForecastPair]:
    """Every day where a full estimation window and a full disjoint forward window exist.

    The windows share no observation: the estimate covers `(t - window, t]` and the target
    covers `(t, t + window]`. That disjointness is what makes this a forecast rather than
    a description.
    """
    if window < 3:
        raise ValueError(f"window must be at least 3 days, got {window}")
    out: list[ForecastPair] = []
    for t in range(window, len(series) - window):
        incumbent = close_to_close_vol(series.closes, t - window, t + 1)
        candidate = realized_vol(series.realized_variance, t - window + 1, t + 1)
        target_r = realized_vol(series.realized_variance, t + 1, t + window + 1)
        target_c = close_to_close_vol(series.closes, t, t + window + 1)
        if min(incumbent, candidate, target_r, target_c) <= 0.0:
            continue
        out.append(
            ForecastPair(
                day=series.days[t],
                incumbent=incumbent,
                candidate=candidate,
                target_realized=target_r,
                target_close_to_close=target_c,
            )
        )
    return out


def mse_log(estimates: Sequence[float], targets: Sequence[float]) -> float:
    """Mean squared error on LOG volatility.

    On logs rather than levels because volatility is right-skewed and a level-space MSE
    would be dominated by a handful of high-vol windows — the comparison would then be
    about who forecasts crashes, not who forecasts volatility.
    """
    return statistics.fmean(
        (math.log(e) - math.log(a)) ** 2 for e, a in zip(estimates, targets)
    )


def qlike(estimates: Sequence[float], targets: Sequence[float]) -> float:
    """QLIKE on variance: `s2/e2 - ln(s2/e2) - 1`, averaged.

    The standard loss for volatility forecasting because it is robust to noise in the
    volatility proxy — its ranking of two forecasts is unchanged by unbiased measurement
    error in the target, which matters here because neither target is the truth. Zero for
    a perfect forecast, positive otherwise, and asymmetric: it punishes under-forecasting
    harder than over-forecasting, which is the right direction for a sizing input.
    """
    total = 0.0
    for e, a in zip(estimates, targets):
        ratio = (a * a) / (e * e)
        total += ratio - math.log(ratio) - 1.0
    return total / len(estimates)


def r_squared(estimates: Sequence[float], targets: Sequence[float]) -> float:
    """Mincer-Zarnowitz R²: regress log target on log estimate, report the fit."""
    xs = [math.log(e) for e in estimates]
    ys = [math.log(a) for a in targets]
    mx, my = statistics.fmean(xs), statistics.fmean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    if sxx <= 0.0:
        return 0.0
    beta = sxy / sxx
    alpha = my - beta * mx
    ss_res = sum((y - (alpha + beta * x)) ** 2 for x, y in zip(xs, ys))
    ss_tot = sum((y - my) ** 2 for y in ys)
    return 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 0.0


def score(pairs: Sequence[ForecastPair]) -> dict:
    """Both estimators against both targets, on both losses, plus the reductions.

    A `reduction` is `1 - candidate_loss / incumbent_loss`: positive means the candidate
    is better. Reported for every (target, loss) cell rather than aggregated, because
    D195's bar requires the candidate to win on all of them and an average would let a
    win on the shared-basis target carry a loss on the other.
    """
    if len(pairs) < 30:
        raise ValueError(f"only {len(pairs)} forecast pairs — too few to score")
    inc = [p.incumbent for p in pairs]
    cand = [p.candidate for p in pairs]
    out: dict = {"n_pairs": len(pairs)}
    for target_name, targets in (
        ("realized", [p.target_realized for p in pairs]),
        ("close_to_close", [p.target_close_to_close for p in pairs]),
    ):
        cell: dict = {}
        for loss_name, loss in (("mse_log", mse_log), ("qlike", qlike)):
            a, b = loss(inc, targets), loss(cand, targets)
            cell[loss_name] = {
                "incumbent": a,
                "candidate": b,
                "reduction": 1.0 - b / a if a > 0.0 else 0.0,
            }
        cell["r2"] = {
            "incumbent": r_squared(inc, targets),
            "candidate": r_squared(cand, targets),
        }
        out[target_name] = cell
    return out

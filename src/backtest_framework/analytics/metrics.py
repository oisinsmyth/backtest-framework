"""Core performance metrics.

`rf_annual` and `periods_per_year` are required arguments with no defaults. A default
rf=0 silently flatters a market-neutral book whose natural benchmark is the risk-free
rate, and a default 252 hides a calendar assumption — the caller states its calendar.

Conventions (all tested):
- rf de-annualization is geometric: rf_period = (1+rf_annual)^(1/periods) − 1 —
  matches quantstats so the reference comparison ties exactly at nonzero rf.
- Sharpe: mean(excess) / sample-std(excess, ddof=1) × √periods. Zero variance →
  sign(mean excess) × inf (a flat series with positive rf is negative-infinitely
  bad risk-adjusted).
- Sortino: mean(excess) / √(mean(min(excess,0)²)) × √periods — full-length RMS
  downside (quantstats' convention). No downside and positive mean → +inf; no
  downside and zero mean → 0.0.
- realised_beta: cov(returns, benchmark, ddof=1) / var(benchmark, ddof=1). The ≈0
  expectation for a market-neutral book is printed by the tearsheet.
- max_drawdown operates on an equity curve and returns a positive fraction.
  max_drawdown_from_returns is the same arithmetic over the curve a return
  series implies; it is the only place that conversion is written.
- excess_sharpe charges rf on the exposed fraction, not on the whole book: a
  long-flat strategy holds cash when flat and cash earns rf, so charging rf against
  the whole book understates it. Report it beside the rf=0 number, not instead of it.

Drawdown sign is a display decision: this module returns drawdown positive, and a
caller that displays it negative should negate the result rather than keep a second
implementation.
"""

from __future__ import annotations

import math
import statistics
from typing import Sequence

import numpy as np


def _rf_period(rf_annual: float, periods_per_year: float) -> float:
    return (1.0 + rf_annual) ** (1.0 / periods_per_year) - 1.0


def sharpe(returns: Sequence[float], rf_annual: float, periods_per_year: float) -> float:
    r = np.asarray(returns, dtype=float)
    if r.size < 2:
        raise ValueError(f"sharpe needs at least 2 returns, got {r.size}")
    excess = r - _rf_period(rf_annual, periods_per_year)
    mu = float(excess.mean())
    sd = float(excess.std(ddof=1))
    if sd == 0.0:
        return math.inf * mu if mu != 0 else 0.0  # sign(mu) * inf
    return mu / sd * math.sqrt(periods_per_year)


def curve_sharpe_zero_rf(returns: Sequence[float], periods_per_year: float) -> float:
    """Annualised Sharpe at rf = 0, by exact summation.

    The rf=0 assumption is in the name on purpose: `sharpe` above makes `rf_annual`
    required, and this function exists for callers that report at rf=0 for
    comparability across studies. Report `excess_sharpe` beside it so both are visible.

    This is not `sharpe(returns, 0.0, ppy)`: same definition, different summation.
    It uses `statistics.fmean` / `statistics.stdev`, which sum exactly (`math.fsum`);
    `sharpe` uses numpy's pairwise summation. On 303 test series including tie-heavy
    ones, 200 disagree, worst 8.9e-16 absolute and 3.7e-13 relative. The two kernels are
    kept separate so that results computed with either remain bit-reproducible.

    Returns 0.0 for fewer than 3 returns or a non-positive standard deviation.
    """
    r = list(returns)
    if len(r) < 3:
        return 0.0
    sd = statistics.stdev(r)
    if sd <= 0.0:
        return 0.0
    return (statistics.fmean(r) / sd) * math.sqrt(periods_per_year)


def _rf_period_log(rf_annual: float, periods_per_year: float) -> float:
    """rf per period in log space — the right de-annualisation for a log-return series.

    `_rf_period` is the simple-return form and is pinned to quantstats by test. On a
    log-return series it is the wrong constant: at rf=4%/252 the two differ from the sixth
    significant figure. Which one applies is a property of the caller's return basis, so
    `excess_sharpe` makes the caller say which.
    """
    return math.log1p(rf_annual) / periods_per_year


def excess_sharpe(
    returns: Sequence[float],
    exposure: Sequence[float],
    rf_annual: float,
    periods_per_year: float,
    *,
    basis: str,
) -> float:
    """Sharpe with rf charged on the exposed fraction, per bar.

    `sharpe` subtracts rf from every observation, which is right for a book that is always
    in the market. A long-flat strategy is not: it holds cash when flat, and cash earns
    rf, so charging rf against the whole book understates it. The correction subtracts
    1 x rf from buy-and-hold but only ~0.5 x rf from a 50%-exposure strategy, so a
    strategy and its baseline move by different amounts and the correction cannot be
    applied by rescaling an rf=0 Sharpe.

    `exposure[t]` is the fraction of capital at risk on bar t, in [0, 1]. Report the
    result beside the rf=0 number rather than instead of it, so the convention change
    is visible.

    `basis` is required and has no default: "log" for a log-return series (rf charged as
    `log1p(rf)/ppy`), "simple" for an arithmetic one (rf charged as `(1+rf)^(1/ppy)-1`,
    as in `sharpe`). A default would silently give one kind of caller the other's
    constant.
    """
    r = np.asarray(returns, dtype=float)
    e = np.asarray(exposure, dtype=float)
    if r.size != e.size:
        raise ValueError(f"length mismatch: {r.size} returns vs {e.size} exposures")
    if r.size < 2:
        raise ValueError(f"excess_sharpe needs at least 2 returns, got {r.size}")
    if basis not in ("log", "simple"):
        raise ValueError(f"basis must be 'log' or 'simple', got {basis!r}")
    rf_period = (
        _rf_period_log(rf_annual, periods_per_year)
        if basis == "log"
        else _rf_period(rf_annual, periods_per_year)
    )
    excess = r - e * rf_period
    mu = float(excess.mean())
    sd = float(excess.std(ddof=1))
    if sd == 0.0:
        return math.inf * mu if mu != 0 else 0.0  # sign(mu) * inf, as `sharpe`
    return mu / sd * math.sqrt(periods_per_year)


def sortino(returns: Sequence[float], rf_annual: float, periods_per_year: float) -> float:
    r = np.asarray(returns, dtype=float)
    if r.size < 2:
        raise ValueError(f"sortino needs at least 2 returns, got {r.size}")
    excess = r - _rf_period(rf_annual, periods_per_year)
    mu = float(excess.mean())
    downside = float(np.sqrt(np.mean(np.minimum(excess, 0.0) ** 2)))
    if downside == 0.0:
        return math.inf if mu > 0 else 0.0
    return mu / downside * math.sqrt(periods_per_year)


def mid_rank_percentile(values: Sequence[float], observed: float) -> float:
    """Where `observed` sits inside `values`, 0–100, with ties at half weight.

    The canonical percentile of an observed statistic within a null distribution.
    Mid-rank is used because on a discrete statistic (e.g. a closed-trade count),
    counting ties as strictly-below would flatter whichever side of the comparison
    happened to be integer-equal.

    This answers `value -> rank`. Null bounds such as p05/p50/p95 answer
    `rank -> value` and should use `np.percentile` (linear) instead.
    """
    if not values:
        return 0.0
    below = sum(1 for v in values if v < observed)
    equal = sum(1 for v in values if v == observed)
    return 100.0 * (below + 0.5 * equal) / len(values)


def realised_beta(returns: Sequence[float], benchmark_returns: Sequence[float]) -> float:
    r = np.asarray(returns, dtype=float)
    b = np.asarray(benchmark_returns, dtype=float)
    if r.size != b.size:
        raise ValueError(f"length mismatch: {r.size} returns vs {b.size} benchmark returns")
    if r.size < 2:
        raise ValueError(f"realised_beta needs at least 2 observations, got {r.size}")
    benchmark_var = float(b.var(ddof=1))
    if benchmark_var == 0.0:
        raise ValueError("benchmark has zero variance — beta against a constant is undefined")
    covariance = float(np.cov(r, b, ddof=1)[0, 1])
    return covariance / benchmark_var


def max_drawdown(equity_curve: Sequence[tuple[object, float]]) -> float:
    """Largest peak-to-trough decline as a positive fraction of the peak. Plain
    arithmetic on the equity curve."""
    peak = float("-inf")
    worst = 0.0
    saw_positive_peak = False
    for _, nav in equity_curve:
        peak = max(peak, nav)
        if peak > 0:
            saw_positive_peak = True
            worst = max(worst, (peak - nav) / peak)
    if equity_curve and not saw_positive_peak:
        # The `peak > 0` gate avoids dividing by a non-positive peak. Without this check a
        # curve that is never above zero would return 0.0, which renders as `0.00%` and is
        # indistinguishable from a genuinely drawdown-free run. Unreachable through
        # `run_backtest` (every equity curve starts at a positive `starting_cash`); it
        # catches a curve of P&L rather than NAV being passed in.
        raise ValueError(
            "max_drawdown is undefined for a curve whose running peak is never positive: "
            f"{len(equity_curve)} point(s), highest {max(nav for _, nav in equity_curve)}. "
            "A drawdown is a fraction OF a peak, and there is no peak to take a fraction of."
        )
    return worst


def max_drawdown_from_returns(returns: Sequence[float]) -> float:
    """Max drawdown implied by a return series, as a positive fraction.

    This is the one place the returns-to-curve conversion happens: the implied curve is
    `[1.0, *cumprod(1+r)]` — the leading 1.0 is the book before the first return, and
    omitting it would make an opening loss invisible.

    It delegates to `max_drawdown` rather than restating the arithmetic, because forms
    that look equal are not bit-equal: `1.0 - nav/peak` and `(peak - nav)/peak` disagree
    at one ULP (worst 1.11e-16) on 322 of 605 test curves including tie-heavy ones.
    """
    curve = [1.0]
    nav = 1.0
    for r in returns:
        nav *= 1.0 + r
        curve.append(nav)
    return max_drawdown(list(enumerate(curve)))

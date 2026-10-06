"""Core performance metrics.

`rf_annual` and `periods_per_year` have no defaults: a default rf=0 would flatter a
market-neutral book whose benchmark is the risk-free rate, and a default of 252 would
hide a calendar assumption.

Conventions (all tested):
- rf de-annualization is geometric, rf_period = (1+rf_annual)^(1/periods) − 1, which
  matches the quantstats reference at nonzero rf.
- Sharpe: mean(excess) / sample-std(excess, ddof=1) × √periods. Zero variance gives
  sign(mean excess) × inf (a flat series with positive rf is -inf).
- Sortino: mean(excess) / √(mean(min(excess,0)²)) × √periods, i.e. full-length RMS
  downside (quantstats' convention). No downside gives +inf for a positive mean and
  0.0 for a zero mean.
- realised_beta: cov(returns, benchmark, ddof=1) / var(benchmark, ddof=1). The
  tearsheet prints the ≈0 expectation for a market-neutral book.
- max_drawdown takes an equity curve and returns a positive fraction;
  max_drawdown_from_returns applies it to the curve implied by a return series.
- excess_sharpe charges rf only on the exposed fraction (see its docstring).

Drawdown is returned positive. Callers that display it negative should negate the
result rather than reimplement it.
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

    For callers that report at rf=0 for comparability across studies; report
    `excess_sharpe` beside it.

    Same definition as `sharpe(returns, 0.0, ppy)` but a different summation:
    `statistics.fmean` / `statistics.stdev` sum exactly (`math.fsum`), while `sharpe`
    uses numpy's pairwise summation. On 303 test series (including tie-heavy ones), 200
    differ, worst 8.9e-16 absolute and 3.7e-13 relative. Both are kept so results from
    either stay bit-reproducible.

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
    """rf per period in log space, for a log-return series.

    `_rf_period` is the simple-return form, pinned to quantstats by test. At rf=4% and
    252 periods the two differ from the sixth significant figure.
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

    `sharpe` subtracts rf from every observation, which suits a book that is always in
    the market. A long-flat strategy holds cash (earning rf) when flat, so this charges
    rf only on the exposed fraction: 1 x rf for buy-and-hold, about 0.5 x rf at 50%
    exposure. Because the charge depends on exposure, it cannot be applied by rescaling
    an rf=0 Sharpe.

    `exposure[t]` is the fraction of capital at risk on bar t, in [0, 1]. Report the
    result beside the rf=0 number rather than instead of it.

    `basis` has no default: "log" for a log-return series (rf charged as
    `log1p(rf)/ppy`), "simple" for arithmetic returns (rf charged as
    `(1+rf)^(1/ppy)-1`, as in `sharpe`).
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
    """Percentile (0 to 100) of `observed` within `values`, counting ties at half weight.

    Used for an observed statistic within a null distribution. Mid-rank matters for
    discrete statistics (e.g. a closed-trade count), where counting ties as below
    would bias the result. Returns 0.0 for empty `values`.

    This maps value -> rank. For rank -> value (null bounds such as p05/p50/p95) use
    `np.percentile` (linear).
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
        raise ValueError("benchmark has zero variance; beta against a constant is undefined")
    covariance = float(np.cov(r, b, ddof=1)[0, 1])
    return covariance / benchmark_var


def max_drawdown(equity_curve: Sequence[tuple[object, float]]) -> float:
    """Largest peak-to-trough decline of an equity curve, as a positive fraction of the peak.

    Raises ValueError if the running peak is never positive."""
    peak = float("-inf")
    worst = 0.0
    saw_positive_peak = False
    for _, nav in equity_curve:
        peak = max(peak, nav)
        if peak > 0:
            saw_positive_peak = True
            worst = max(worst, (peak - nav) / peak)
    if equity_curve and not saw_positive_peak:
        # Otherwise a curve never above zero would return 0.0, the same as a run with
        # no drawdown. run_backtest curves start at a positive starting_cash, so this
        # catches a P&L curve passed in place of NAV.
        raise ValueError(
            "max_drawdown is undefined for a curve whose running peak is never positive: "
            f"{len(equity_curve)} point(s), highest {max(nav for _, nav in equity_curve)}. "
            "Drawdown is measured as a fraction of a positive peak."
        )
    return worst


def max_drawdown_from_returns(returns: Sequence[float]) -> float:
    """Max drawdown implied by a return series, as a positive fraction.

    The implied curve is `[1.0, *cumprod(1+r)]`; the leading 1.0 is the book before the
    first return, so an opening loss counts.

    Delegates to `max_drawdown` so the arithmetic is bit-identical: `1.0 - nav/peak` and
    `(peak - nav)/peak` differ by one ULP (worst 1.11e-16) on 322 of 605 test curves,
    including tie-heavy ones.
    """
    curve = [1.0]
    nav = 1.0
    for r in returns:
        nav *= 1.0 + r
        curve.append(nav)
    return max_drawdown(list(enumerate(curve)))

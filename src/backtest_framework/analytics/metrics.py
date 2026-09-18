"""Core performance metrics (D37, D49, D80).

Honesty by signature: `rf_annual` and `periods_per_year` are REQUIRED arguments with
no defaults. A default rf=0 is exactly the silent shortcut D49 exists to kill (it
flatters a market-neutral book whose honest hurdle IS the risk-free rate), and a
default 252 is the constant-sprinkling D17 warns about — the caller states its
calendar, or it doesn't get a number.

Conventions (D80, all stated, all tested):
- rf de-annualization is GEOMETRIC: rf_period = (1+rf_annual)^(1/periods) − 1 —
  matches the quantstats reference so the X-gate ties exactly at nonzero rf.
- Sharpe: mean(excess) / sample-std(excess, ddof=1) × √periods. Zero variance →
  sign(mean excess) × inf (a flat series with positive rf is NEGATIVE-infinitely
  bad risk-adjusted — the D49 gate's "flat series at rf=4% is negative").
- Sortino: mean(excess) / √(mean(min(excess,0)²)) × √periods — full-length RMS
  downside (quantstats' convention). No downside and positive mean → +inf; no
  downside and zero mean → 0.0.
- realised_beta: cov(returns, benchmark, ddof=1) / var(benchmark, ddof=1) (D37 —
  the ≈0 expectation for a market-neutral book is the tearsheet's job to print).
- max_drawdown operates on an EQUITY CURVE and returns a positive fraction
  (relocated here from engine/sweep.py — analytics is its natural home).
  max_drawdown_from_returns is the same arithmetic over the curve a return
  series implies; it is the only place that conversion is written (D542).
- excess_sharpe charges rf on the EXPOSED FRACTION, not on the whole book
  (D219/D228): a long-flat arm holds cash when flat and cash earns rf, so
  charging rf against the whole book understates it. Reported BESIDE the
  rf=0 number, never instead of it — D219 forbids switching silently.

SIGN IS A DISPLAY DECISION, MADE ONCE, AT THE EMIT BOUNDARY (D542). This module
returns drawdown POSITIVE. `research/terrain_strategies` publishes it negative
and negates a delegated call rather than keeping a second implementation; the
artifacts it writes carry a `max_drawdown_convention` field so a reader of the
JSON alone is told which sign the file holds.
"""

from __future__ import annotations

import math
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


def _rf_period_log(rf_annual: float, periods_per_year: float) -> float:
    """rf per period in LOG space — the right de-annualisation for a log-return series.

    `_rf_period` is the simple-return form and is pinned to quantstats by the X-gate. On a
    log-return series it is the wrong constant: at rf=4%/252 the two differ from the sixth
    significant figure, which is small but is not zero and is not a rounding choice. Which
    one applies is a property of the CALLER's return basis, so `excess_sharpe` makes the
    caller say which — the same argument D49 makes for rf itself and D17 for the calendar.
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
    """Sharpe with rf charged on the EXPOSED FRACTION, per bar (D219, D228 Part 1 fact 2).

    `sharpe` subtracts rf from every observation, which is right for a book that is always
    in the market. A long-flat arm is not: it holds CASH when flat, and cash earns rf, so
    charging rf against the whole book understates it. D219 measured the consequence —
    "the correction subtracts 1 x rf from buy-and-hold and only ~0.5 x rf from a
    50%-exposure arm. It lowers both, and it lowers buy-and-hold roughly twice as much" —
    which is why an arm and its own baseline move by different amounts and the correction
    cannot be applied by scaling a published number.

    `exposure[t]` is the fraction of capital at risk on bar t, in [0, 1]. Promoted here
    from `scripts/run_filter_search.py` and `scripts/run_jerk_rung.py`, which had the same
    body twice; it is reported BESIDE the rf=0 number and never instead of it, because
    D219 forbids switching conventions silently.

    `basis` is REQUIRED and has no default: "log" for a log-return series, "simple" for an
    arithmetic one. Both `scripts/` copies charged `log1p(rf)/ppy` against log returns and
    `metrics.sharpe` charges `(1+rf)^(1/ppy)-1` against simple ones, so a default here
    would silently hand one of the two callers the other one's constant.
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
    arithmetic on the equity curve. (Relocated from engine/sweep.py, D80.)"""
    peak = float("-inf")
    worst = 0.0
    saw_positive_peak = False
    for _, nav in equity_curve:
        peak = max(peak, nav)
        if peak > 0:
            saw_positive_peak = True
            worst = max(worst, (peak - nav) / peak)
    if equity_curve and not saw_positive_peak:
        # Refusing rather than answering. The `peak > 0` gate avoids dividing by a
        # non-positive peak, which is right, but it used to fall through to `worst = 0.0`
        # and hand back "no drawdown" for a book that was never once above water. Both
        # renderers format this as `{dd:.2%}`, so the wrong answer printed as `0.00%` --
        # indistinguishable from a genuinely drawdown-free run, which is the worst way for a
        # number to be wrong. Unreachable through `run_backtest` (every equity curve starts
        # at a positive `starting_cash`), so this costs nothing today and stops the silent
        # `0.00%` if a curve of P&L rather than NAV is ever passed in.
        raise ValueError(
            "max_drawdown is undefined for a curve whose running peak is never positive: "
            f"{len(equity_curve)} point(s), highest {max(nav for _, nav in equity_curve)}. "
            "A drawdown is a fraction OF a peak, and there is no peak to take a fraction of."
        )
    return worst


def max_drawdown_from_returns(returns: Sequence[float]) -> float:
    """Max drawdown implied by a RETURN series, as a positive fraction (D542).

    Three of the repository's drawdown implementations take returns rather than a curve,
    and each built its own curve inline. This is the one place that conversion happens:
    the implied curve is `[1.0, *cumprod(1+r)]` — the leading 1.0 is the book before the
    first return, and omitting it would make an opening loss invisible.

    It delegates to `max_drawdown` rather than restating the arithmetic, because the two
    forms that look equal are not. `breakdown_study` computed `1.0 - nav/peak` where this
    computes `(peak - nav)/peak`; measured on 605 curves including tie-heavy ones, **322
    disagree at one ULP** (worst 1.11e-16). Algebraically equal, not bit-equal — and a
    reordered float expression is exactly what D542 refuses to leave lying around in two
    places. The vectorised form in `research/breakout_nulls` already agrees with this one
    bit-exactly on 603 probed curves and keeps its own loop for speed, pinned by test.
    """
    curve = [1.0]
    nav = 1.0
    for r in returns:
        nav *= 1.0 + r
        curve.append(nav)
    return max_drawdown(list(enumerate(curve)))

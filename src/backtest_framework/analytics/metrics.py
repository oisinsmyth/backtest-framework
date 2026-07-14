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
    for _, nav in equity_curve:
        peak = max(peak, nav)
        if peak > 0:
            worst = max(worst, (peak - nav) / peak)
    return worst

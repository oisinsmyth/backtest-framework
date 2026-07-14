"""Cointegration-filtered pair selection (study v2, D92, D93).

Study v1's finding: Gatev distance selects pairs that *tracked*; nothing in the
score asks whether their spread *mean-reverts*. This module adds the classic
Engle-Granger filter, ranked — never thresholded — per D29:

  1. Gatev-score all C(n,2) pairs (n_pairs_tested stays the FULL count).
  2. Keep the `gatev_prefilter` closest as candidates.
  3. Fit the EG step-1 regression ln A = alpha + beta * ln B per candidate; DISCARD
     pairs whose beta falls outside `beta_window` — the strategy trades the 1:1
     spread ln A − ln B, so selecting on stationarity evidence about
     ln A − beta*ln B with beta far from 1 would be testing a spread we don't trade
     (D92). beta is logged for a future beta-hedged study version, not traded.
  4. Rank survivors by the ADF t-statistic of the residual spread (ascending: more
     negative = stronger mean reversion), take top-N.

The ADF here computes the STATISTIC ONLY (D93): D29's rank-don't-threshold rule
makes p-values — and the MacKinnon critical-value machinery they'd require —
unnecessary. The statistic is anchored against statsmodels' adfuller in
tests/unit/test_cointegration.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

from ..engine.dataview import DataView
from ..validation.pair_selection import PairSelection, select_pairs


def engle_granger_beta(y: np.ndarray, x: np.ndarray) -> tuple[float, float, np.ndarray]:
    """OLS y = alpha + beta*x; returns (alpha, beta, residuals). Inputs are
    log-price arrays over the training window."""
    if y.shape != x.shape or y.size < 3:
        raise ValueError(f"need equal-length series of >=3 points, got {y.size} vs {x.size}")
    design = np.column_stack([np.ones_like(x), x])
    (alpha, beta), *_ = np.linalg.lstsq(design, y, rcond=None)
    residuals = y - (alpha + beta * x)
    return float(alpha), float(beta), residuals


def adf_stat(series: np.ndarray, lags: int = 1) -> float:
    """Augmented Dickey-Fuller t-statistic, no-constant regression (the EG-residual
    convention — residuals are mean-zero by construction):

        ds_t = gamma * s_{t-1} + sum_i phi_i * ds_{t-i} + e_t

    Returns the t-statistic of gamma. More negative = stronger evidence of mean
    reversion. STATISTIC ONLY — no p-values, by design (D29/D93)."""
    s = np.asarray(series, dtype=float)
    if s.size < lags + 3:
        raise ValueError(f"series too short for ADF with {lags} lag(s): {s.size} points")
    ds = np.diff(s)
    # Rows: t = lags .. len(ds)-1. Regressors: s_{t-1}, then ds_{t-1..t-lags}.
    y = ds[lags:]
    columns = [s[lags:-1]]
    for i in range(1, lags + 1):
        columns.append(ds[lags - i : -i])
    design = np.column_stack(columns)

    coef, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    residuals = y - design @ coef
    dof = y.size - design.shape[1]
    if dof <= 0:
        raise ValueError("not enough observations for the requested lag order")
    sigma2 = float(residuals @ residuals) / dof
    covariance = sigma2 * np.linalg.inv(design.T @ design)
    return float(coef[0] / np.sqrt(covariance[0, 0]))


@dataclass
class CointegrationSelector:
    """Callable selector for run_pairs_study (D92): (views, top_n) -> PairSelection.
    Retains `.last_details` — per-selected-pair beta and ADF stat — for trial
    configs and the study artifact."""

    gatev_prefilter: int = 50
    beta_window: tuple[float, float] = (0.7, 1.3)
    adf_lags: int = 1
    name: str = "gatev_prefilter->engle_granger->adf_rank"

    last_details: list[dict] = field(default_factory=list, init=False, repr=False)

    def __call__(self, views: Mapping[str, DataView], top_n: int) -> PairSelection:
        # Step 1-2: full Gatev scoring (multiplicity = ALL pairs), prefiltered.
        gatev = select_pairs(views, top_n=self.gatev_prefilter)

        log_prices = {
            symbol: np.log([views[symbol][i].close for i in range(len(views[symbol]))])
            for symbol in views
        }

        scored: list[tuple[float, tuple[str, str], float]] = []  # (adf, pair, beta)
        for a, b in gatev.ranked_pairs:
            _, beta, residuals = engle_granger_beta(log_prices[a], log_prices[b])
            if not (self.beta_window[0] <= beta <= self.beta_window[1]):
                continue  # incoherent with the 1:1 traded spread (D92)
            scored.append((adf_stat(residuals, lags=self.adf_lags), (a, b), beta))

        scored.sort(key=lambda row: row[0])  # most negative ADF first
        chosen = scored[:top_n]
        self.last_details = [
            {"pair": list(pair), "beta": round(beta, 4), "adf_stat": round(stat, 4)}
            for stat, pair, beta in chosen
        ]
        return PairSelection(
            ranked_pairs=tuple(pair for _, pair, _ in chosen),
            n_pairs_tested=gatev.n_pairs_tested,  # the FULL C(n,2) count (D29)
        )

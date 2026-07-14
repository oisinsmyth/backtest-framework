"""Synthetic cointegrated-LOOKING pairs with zero true edge (D23, D87).

The null construction matters (D87): a genuinely cointegrated pair — an
Ornstein-Uhlenbeck (mean-reverting) spread — has REAL gross edge for a mean-reversion
strategy; using it as the null would test nothing. The correct zero-edge null keeps
the visual signature of cointegration (two series sharing a common stochastic trend,
tracking each other closely) while making the spread a RANDOM WALK: a martingale,
against which any timing rule has expected profit exactly zero. If a strategy
systematically profits on these pairs, it is reading the future or mis-accounting —
per the gate: stop everything.

Construction:
  ln A_t = common random walk (drift mu, vol sigma_common)
  ln B_t = ln A_t - s_t,  s_t = random walk with small steps (sigma_spread)

Small sigma_spread keeps the pair visually locked together (the "looks cointegrated"
part — over short windows a rebased-price plot is indistinguishable from a
cointegrated pair) while s_t's martingale property carries the zero-edge guarantee.
"""

from __future__ import annotations

import numpy as np

from ..data.bars import TimestampedBar
from ..simulator.fills import Bar
from datetime import datetime, timedelta


def cointegrated_looking_pair(
    seed: int,
    n_bars: int = 300,
    initial_price: float = 100.0,
    mu: float = 0.0002,
    sigma_common: float = 0.012,
    sigma_spread: float = 0.004,
    start: datetime = datetime(2026, 1, 5, 16),
) -> dict[str, list[TimestampedBar]]:
    rng = np.random.default_rng(seed)
    common = np.cumsum(rng.normal(mu, sigma_common, n_bars))
    spread = np.cumsum(rng.normal(0.0, sigma_spread, n_bars))  # RANDOM WALK: the null

    log_a = np.log(initial_price) + common
    log_b = log_a - spread
    prices_a, prices_b = np.exp(log_a), np.exp(log_b)

    def series(prices) -> list[TimestampedBar]:
        return [
            TimestampedBar(start + timedelta(days=i), Bar(open=p, high=p, low=p, close=p))
            for i, p in enumerate(map(float, prices))
        ]

    return {"A": series(prices_a), "B": series(prices_b)}

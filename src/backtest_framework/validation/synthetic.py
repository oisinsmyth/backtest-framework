"""Synthetic cointegrated-looking pairs with zero true edge.

A truly cointegrated pair (an Ornstein-Uhlenbeck spread) gives a mean-reversion
strategy real gross edge, so it cannot serve as a null. These pairs share a common
stochastic trend and track each other closely, but the spread is a random walk: a
martingale, against which any timing rule has zero expected profit. A strategy that
systematically profits on them is using future data or mis-accounting.

Construction:
  ln A_t = common random walk (drift mu, vol sigma_common)
  ln B_t = ln A_t - s_t,  s_t = random walk with small steps (sigma_spread)

A small sigma_spread keeps the pair close enough that, over short windows, a
rebased-price plot looks like a cointegrated pair.
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
    spread = np.cumsum(rng.normal(0.0, sigma_spread, n_bars))  # random walk: the null

    log_a = np.log(initial_price) + common
    log_b = log_a - spread
    prices_a, prices_b = np.exp(log_a), np.exp(log_b)

    def series(prices) -> list[TimestampedBar]:
        return [
            TimestampedBar(start + timedelta(days=i), Bar(open=p, high=p, low=p, close=p))
            for i, p in enumerate(map(float, prices))
        ]

    return {"A": series(prices_a), "B": series(prices_b)}

"""Sample-size-gated tail risk (D36, D81).

Reporting a number you shouldn't trust is worse than not reporting one — 95% VaR from
~500 daily points estimates the 25th-worst day (D36's own rationale). The gate here:
the tail beyond the cutoff must contain at least MIN_TAIL_OBSERVATIONS points — a
tail estimated from fewer than 30 observations is an anecdote, not an estimate. At
95% confidence that means n ≥ 600; at 99%, n ≥ 3,000. Deliberately stricter than the
verification gate's 100-bar case requires.

The result is never None and never a silently-wrong number: it's either a value or
an explicit insufficient-data marker whose message contains the minimum-n arithmetic.
Losses are reported as POSITIVE numbers (a 2.3% VaR means "you lose ≥2.3% on the
worst 5% of days").
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

import numpy as np

MIN_TAIL_OBSERVATIONS = 30


@dataclass(frozen=True)
class TailRiskResult:
    confidence: float
    n_observations: int
    var: float | None = None
    cvar: float | None = None
    insufficient_reason: str | None = None

    @property
    def sufficient(self) -> bool:
        return self.insufficient_reason is None


def minimum_observations(confidence: float) -> int:
    return math.ceil(MIN_TAIL_OBSERVATIONS / (1.0 - confidence))


def var_cvar(returns: Sequence[float], confidence: float = 0.95) -> TailRiskResult:
    r = np.asarray(returns, dtype=float)
    n = r.size
    required = minimum_observations(confidence)
    if n < required:
        return TailRiskResult(
            confidence=confidence,
            n_observations=n,
            insufficient_reason=(
                f"insufficient data (n={n}, need >={required}): a {confidence:.0%} tail from "
                f"{n} observations holds fewer than {MIN_TAIL_OBSERVATIONS} points (D36/D81)"
            ),
        )
    cutoff = float(np.quantile(r, 1.0 - confidence))
    tail = r[r <= cutoff]
    return TailRiskResult(
        confidence=confidence,
        n_observations=n,
        var=-cutoff,
        cvar=-float(tail.mean()),
    )

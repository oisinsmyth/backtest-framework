"""Sample-size-gated tail risk.

95% VaR from ~500 daily points rests on about 25 tail observations. The tail beyond
the cutoff must hold at least MIN_TAIL_OBSERVATIONS (30) points, so 95% confidence
needs n ≥ 600 and 99% needs n ≥ 3,000.

The result holds either a value or an insufficient-data reason whose message gives
the minimum-n arithmetic. Losses are positive (a 2.3% VaR means a loss of at least
2.3% on the worst 5% of days).
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
                f"{n} observations holds fewer than {MIN_TAIL_OBSERVATIONS} points"
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

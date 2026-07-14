"""Beta-hedged z-score pairs strategy (study v3, D94).

RESEARCH/STUDY STRATEGY, not a validated trading system (the D38/D82 label, honored
even though this lives outside the auto-checked strategies/ package): it exists to
measure whether trading the train-window-fitted Engle-Granger hedge ratio improves
on the 1:1 spread — study v3's single changed variable.

Signal: spread_i = ln A_i − β·ln B_i, rolling z-score over the previous `lookback`
spreads (D44's previous-bar rule), the same hysteresis state machine and guards as
strategies.zscore_pairs.ZScorePairsStrategy. β is fitted on the TRAINING window by
the CointegrationSelector (through guarded DataViews, D22/D85) and applied
out-of-sample — never re-fitted mid-window.

Weights, normalized to constant gross (D94): the factor-neutral hedge for a log-β
relationship holds dollar notionals in the ratio N_B = β·N_A; raw (±w, ∓βw) would
let gross exposure drift with β and break risk comparability with v1/v2, so:

    w_A = 2w/(1+β),   w_B = 2wβ/(1+β)      (gross = w_A + w_B = 2w, always)

At β = 1 this is exactly (w, w) — the strategy REDUCES to ZScorePairsStrategy, a
tested equivalence tying v3's machinery to the v2 baseline.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Mapping

from ..engine.dataview import DataView
from ..pipeline.sizing import TargetWeight


@dataclass
class BetaHedgedZScoreStrategy:
    strategy_id: str
    instrument_a: str
    instrument_b: str
    hedge_beta: float
    lookback: int = 30
    entry_z: float = 2.0
    exit_z: float = 0.5
    leg_weight: float = 1.0
    """`leg_weight` keeps v1/v2 semantics: gross when in a trade = 2 x leg_weight."""

    _side: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.hedge_beta <= 0:
            raise ValueError(f"hedge_beta must be positive, got {self.hedge_beta}")
        if self.lookback < 2:
            raise ValueError(f"lookback must be at least 2, got {self.lookback}")
        if self.exit_z >= self.entry_z:
            raise ValueError(
                f"exit_z ({self.exit_z}) must be below entry_z ({self.entry_z}) — "
                "the hysteresis band would be empty or inverted"
            )

    @property
    def weight_a(self) -> float:
        return 2.0 * self.leg_weight / (1.0 + self.hedge_beta)

    @property
    def weight_b(self) -> float:
        return 2.0 * self.leg_weight * self.hedge_beta / (1.0 + self.hedge_beta)

    def _spread(self, view_a: DataView, view_b: DataView, index: int) -> float:
        return math.log(view_a[index].close) - self.hedge_beta * math.log(view_b[index].close)

    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]:
        view_a, view_b = views[self.instrument_a], views[self.instrument_b]
        n = len(view_a)

        if n < self.lookback + 1:
            return self._targets_for_side(0)

        window = [self._spread(view_a, view_b, i) for i in range(n - 1 - self.lookback, n - 1)]
        mean = statistics.fmean(window)
        std = statistics.stdev(window)
        if std == 0.0:
            return self._targets_for_side(0)

        z = (self._spread(view_a, view_b, n - 1) - mean) / std

        if z > self.entry_z:
            self._side = -1
        elif z < -self.entry_z:
            self._side = 1
        elif abs(z) < self.exit_z:
            self._side = 0
        # else: hysteresis band — hold

        return self._targets_for_side(self._side)

    def _targets_for_side(self, side: int) -> list[TargetWeight]:
        return [
            TargetWeight(strategy_id=self.strategy_id, instrument_id=self.instrument_a, weight=side * self.weight_a),
            TargetWeight(strategy_id=self.strategy_id, instrument_id=self.instrument_b, weight=-side * self.weight_b),
        ]

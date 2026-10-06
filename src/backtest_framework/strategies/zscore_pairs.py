"""Minimal z-score pairs strategy.

No pair selection (the pair is an input; a well-known pair such as XLE/XOP is chosen
with hindsight, so results on it are in-sample by pair choice), no cointegration
fitting and no Kalman hedge ratio. The hedge is fixed 1:1 in log space, because an
estimated ratio would be a fitted parameter needing walk-forward machinery
(validation.walk_forward). With fixed hyperparameters there is no fitting step, and
DataView's trailing-only data covers look-ahead.

Signal: spread_t = ln(close_A) − ln(close_B); z = (spread_now − mean) / std, where
mean/std come from the `lookback` spreads ending at the previous bar, not the current
one. The strategy handles its own warm-up; the engine does not enforce one.

Rules, with hysteresis:
  z >  entry_z          → short the spread: short A, long B
  z < −entry_z          → long the spread:  long A, short B
  |z| < exit_z          → flat
  exit_z ≤ |z| ≤ entry_z → hold the current side (`_side`)

`_side` is per-run state, so use a fresh instance per backtest run (hence
engine.sweep.run_cost_sweep takes a strategy factory).
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Mapping

from ..engine.dataview import DataView
from ..pipeline.sizing import TargetWeight


@dataclass
class ZScorePairsStrategy:
    strategy_id: str
    instrument_a: str
    instrument_b: str
    lookback: int = 60
    entry_z: float = 2.0
    exit_z: float = 0.5
    leg_weight: float = 1.0
    """Per-leg weight when in a trade. 1.0 means each leg targets 100% of the
    strategy's capital, about 200% gross for a dollar-neutral pair."""

    _side: int = field(default=0, init=False, repr=False)
    """+1 = long spread (long A / short B), −1 = short spread, 0 = flat."""

    def __post_init__(self) -> None:
        if self.lookback < 2:
            raise ValueError(f"lookback must be at least 2, got {self.lookback}")
        if self.exit_z >= self.entry_z:
            raise ValueError(
                f"exit_z ({self.exit_z}) must be below entry_z ({self.entry_z}); "
                "the hysteresis band would be empty or inverted"
            )

    def _spread(self, view_a: DataView, view_b: DataView, index: int) -> float:
        return math.log(view_a[index].close) - math.log(view_b[index].close)

    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]:
        view_a, view_b = views[self.instrument_a], views[self.instrument_b]
        n = len(view_a)

        # Warm-up self-guard: need `lookback` spreads ending at the previous bar.
        if n < self.lookback + 1:
            # No bar has set `_side` yet, so it is 0.
            assert self._side == 0, "warm-up reached with a live side"
            return self._targets_for_side(0)

        window = [self._spread(view_a, view_b, i) for i in range(n - 1 - self.lookback, n - 1)]
        mean = statistics.fmean(window)
        std = statistics.stdev(window)
        if std == 0.0:
            # Clear `_side` along with the flat targets. Otherwise, if |z| next lands in
            # the hysteresis band, the stale side would re-enter without an entry signal.
            self._side = 0
            return self._targets_for_side(0)  # degenerate window: stand aside

        z = (self._spread(view_a, view_b, n - 1) - mean) / std

        if z > self.entry_z:
            self._side = -1
        elif z < -self.entry_z:
            self._side = 1
        elif abs(z) < self.exit_z:
            self._side = 0
        # else: hysteresis band, hold self._side unchanged

        return self._targets_for_side(self._side)

    def _targets_for_side(self, side: int) -> list[TargetWeight]:
        w = side * self.leg_weight
        return [
            TargetWeight(strategy_id=self.strategy_id, instrument_id=self.instrument_a, weight=w),
            TargetWeight(strategy_id=self.strategy_id, instrument_id=self.instrument_b, weight=-w),
        ]

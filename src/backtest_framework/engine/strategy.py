"""Strategy: the signal-generation side of D27's pipeline.

Strategies receive a DataView (D32) — never the raw bar series — and return the
target weights the engine should size and net (pipeline.sizing). This module doesn't
implement any real trading idea; ScheduledWeightStrategy exists only so run_backtest
is testable without one, the same role Step 3's toy cost bricks played for CostStack.
The actual pairs strategy (Gatev distance -> cointegration -> Kalman) is Phase G work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from ..engine.dataview import DataView
from ..pipeline.sizing import TargetWeight


class Strategy(Protocol):
    strategy_id: str

    def generate_targets(self, view: DataView) -> list[TargetWeight]: ...


@dataclass(frozen=True)
class ScheduledWeightStrategy:
    """Targets weights[view.current_index] on each bar (holding the last value once
    the schedule runs out). A constant weight is just a schedule of one repeated value
    — this single class covers both the "always the same weight" and "a scripted
    weight path" reference-strategy cases without needing two separate toy classes."""

    strategy_id: str
    instrument_id: str
    weights: Sequence[float]

    def generate_targets(self, view: DataView) -> list[TargetWeight]:
        index = min(view.current_index, len(self.weights) - 1)
        weight = self.weights[index]
        return [TargetWeight(strategy_id=self.strategy_id, instrument_id=self.instrument_id, weight=weight)]

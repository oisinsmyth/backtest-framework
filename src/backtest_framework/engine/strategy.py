"""Strategy: the signal-generation side of D27's pipeline.

Strategies receive one DataView per instrument they might trade (D32) — never the raw
bar series — and return the target weights the engine should size and net
(pipeline.sizing). One instrument is just the N=1 case of this interface (D64), the
same pattern D55/D58 already established for capital_by_strategy: a pairs strategy
gets {"XLE": DataView(...), "XOP": DataView(...)}; a single-instrument strategy gets a
one-entry mapping.

This module doesn't implement any real trading idea; ScheduledWeightStrategy exists
only so run_backtest is testable without one, the same role Step 3's toy cost bricks
played for CostStack. The real strategies live in strategies/ (z-score pairs, D69)
and research/ (the Phase G study strategies; the originally planned Kalman stage was
cut on study-v3 evidence, D97).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from ..engine.dataview import DataView
from ..pipeline.sizing import TargetWeight


class Strategy(Protocol):
    strategy_id: str

    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]: ...


@dataclass(frozen=True)
class ScheduledWeightStrategy:
    """Targets weights_by_instrument[instrument][view.current_index] on each bar for
    every instrument in the mapping (holding the last scheduled value once a
    particular instrument's schedule runs out). A single-instrument constant weight is
    just a one-entry mapping with a schedule of one repeated value; a pairs scenario is
    a two-entry mapping with opposite-signed schedules — this one class covers both
    without needing separate toy classes."""

    strategy_id: str
    weights_by_instrument: Mapping[str, Sequence[float]]

    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]:
        targets: list[TargetWeight] = []
        for instrument_id, weights in self.weights_by_instrument.items():
            view = views[instrument_id]
            index = min(view.current_index, len(weights) - 1)
            targets.append(
                TargetWeight(strategy_id=self.strategy_id, instrument_id=instrument_id, weight=weights[index])
            )
        return targets

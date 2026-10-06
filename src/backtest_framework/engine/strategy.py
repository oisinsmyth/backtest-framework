"""Strategy: the signal-generation side of the signal -> weight -> order pipeline.

Strategies receive one DataView per instrument (never the raw bar series) and return
target weights for the engine to size and net (pipeline.sizing). A pairs strategy gets
{"XLE": DataView(...), "XOP": DataView(...)}; a single-instrument strategy gets a
one-entry mapping.

ScheduledWeightStrategy is a test fixture for run_backtest. Real strategies live in
strategies/ (z-score pairs).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from ..engine.dataview import DataView
from ..pipeline.sizing import TargetWeight


class Strategy(Protocol):
    strategy_id: str

    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]: ...

    # Optional hook, not declared so strategies without stops still conform:
    #
    #     def on_stop_filled(self, instrument_id: str) -> None: ...
    #
    # If present, the engine calls it right after a stop closes a position. A stateful
    # strategy that declares stops should implement it; otherwise it keeps emitting the
    # same target and re-enters on the next bar. `run_backtest` looks it up with getattr,
    # so a missing hook raises nothing.


@dataclass(frozen=True)
class ScheduledWeightStrategy:
    """Targets weights_by_instrument[instrument][view.current_index] on each bar.

    Holds the last scheduled value once an instrument's schedule runs out. A constant
    single-instrument weight is a one-entry mapping; a pair is a two-entry mapping with
    opposite-signed schedules."""

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

"""Strategy: the signal-generation side of the signal -> weight -> order pipeline.

Strategies receive one DataView per instrument they might trade — never the raw
bar series — and return the target weights the engine should size and net
(pipeline.sizing). One instrument is just the N=1 case of this interface, the
same pattern used for capital_by_strategy: a pairs strategy
gets {"XLE": DataView(...), "XOP": DataView(...)}; a single-instrument strategy gets a
one-entry mapping.

This module doesn't implement any real trading idea; ScheduledWeightStrategy exists
only so run_backtest is testable without one. A real strategy lives in strategies/
(z-score pairs).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol, Sequence

from ..engine.dataview import DataView
from ..pipeline.sizing import TargetWeight


class Strategy(Protocol):
    strategy_id: str

    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]: ...

    # Optional, deliberately not declared here as a required member so that strategies
    # that never use intrabar stops still conform:
    #
    #     def on_stop_filled(self, instrument_id: str) -> None: ...
    #
    # The engine calls it, if present, immediately after a stop closes a position. A
    # stateful strategy that declares stops must implement it or it will not learn that
    # it was stopped out: it would keep emitting the same target and re-enter on the very
    # next bar, which turns a bounded loss into a repeated one. `run_backtest` looks it up
    # with getattr, so omitting it is silent.


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

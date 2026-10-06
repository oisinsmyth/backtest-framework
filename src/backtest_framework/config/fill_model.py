"""Declarative config for the stop-fill logic.

Not a full execution/fill pipeline: this wraps the gap-through-stop fill rule in
simulator/fills.py behind a factory, so it can be selected from a config dict like the
carry model.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..simulator.fills import Bar, StopSide, stop_fill_price
from .errors import ConfigError
from .factory import FactoryRegistry

_STOP_SIDE_BY_NAME = {"sell_stop": StopSide.SELL_STOP, "buy_stop": StopSide.BUY_STOP}


@dataclass(frozen=True)
class FillModel:
    stop_side: StopSide

    def fill(self, stop_price: float, bar: Bar) -> float | None:
        return stop_fill_price(self.stop_side, stop_price, bar)


def _build_stop_gap_aware_fill_model(config: dict) -> FillModel:
    if "stop_side" not in config:
        raise ConfigError("fill_model config of type 'stop_gap_aware' is missing required key 'stop_side'")
    stop_side_name = config["stop_side"]
    if stop_side_name not in _STOP_SIDE_BY_NAME:
        allowed = ", ".join(sorted(_STOP_SIDE_BY_NAME))
        raise ConfigError(
            f"fill_model config key 'stop_side' must be one of [{allowed}], got {stop_side_name!r}"
        )
    return FillModel(stop_side=_STOP_SIDE_BY_NAME[stop_side_name])


FILL_MODEL_REGISTRY = FactoryRegistry(kind="fill_model")
FILL_MODEL_REGISTRY.register("stop_gap_aware", _build_stop_gap_aware_fill_model)

"""Declarative config for D33's carry accrual (Step 2 demonstration vehicle).

Not the CostStack carry bricks from D1/D2/D5 — those are Step 3's job and will cover
margin interest, borrow fees, and funding as distinct, instrument-aware bricks. This is a
single small config-and-factory pair built to prove the declarative-config mechanism end
to end against behaviour that already exists (Step 1's accrue_carry_between_bars), without
pulling Step 3's refactor forward. Expect this module to be absorbed into the real carry
bricks once Step 3 lands.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..simulator.carry import DEFAULT_DAY_COUNT, accrue_carry_between_bars
from .errors import ConfigError
from .factory import FactoryRegistry


@dataclass(frozen=True)
class CarryModel:
    annual_rate: float
    day_count: float = DEFAULT_DAY_COUNT

    def accrue(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        return accrue_carry_between_bars(
            self.annual_rate, base_amount, prev_timestamp, curr_timestamp, day_count=self.day_count
        )


def _build_act365_carry_model(config: dict) -> CarryModel:
    if "annual_rate" not in config:
        raise ConfigError("carry_model config of type 'act365' is missing required key 'annual_rate'")
    annual_rate = config["annual_rate"]
    if not isinstance(annual_rate, (int, float)) or isinstance(annual_rate, bool):
        raise ConfigError(
            f"carry_model config key 'annual_rate' must be numeric, got {type(annual_rate).__name__}"
        )
    day_count = config.get("day_count", DEFAULT_DAY_COUNT)
    if not isinstance(day_count, (int, float)) or isinstance(day_count, bool):
        raise ConfigError(f"carry_model config key 'day_count' must be numeric, got {type(day_count).__name__}")
    return CarryModel(annual_rate=float(annual_rate), day_count=float(day_count))


CARRY_MODEL_REGISTRY = FactoryRegistry(kind="carry_model")
CARRY_MODEL_REGISTRY.register("act365", _build_act365_carry_model)

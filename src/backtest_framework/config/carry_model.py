"""Declarative config for the carry cost brick (D33, D51, D1/D2).

This is exactly the migration Step 2's original docstring here promised: the standalone
CarryModel demonstration class is retired now that Step 3's CostStack exists, and this
config-layer factory registry builds a real costs.bricks.FlatRateCarry instead. Nothing
about SimConfig's shape or the four Step 2 gates changes — only what gets constructed.
"""

from __future__ import annotations

from ..costs.bricks import FlatRateCarry
from ..simulator.carry import DEFAULT_DAY_COUNT
from .errors import ConfigError
from .factory import FactoryRegistry


def _build_act365_carry_brick(config: dict) -> FlatRateCarry:
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
    return FlatRateCarry(annual_rate=float(annual_rate), day_count=float(day_count))


CARRY_MODEL_REGISTRY = FactoryRegistry(kind="carry_model")
CARRY_MODEL_REGISTRY.register("act365", _build_act365_carry_brick)

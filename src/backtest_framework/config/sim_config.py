"""Top-level SimConfig: a plain dict validated and turned into live objects.

`seed` and `snapshot_id` are not in this dict; they are separate required fields on
TrialRegistry.add_trial. SimConfig describes only which models to build and how.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..costs.bricks import FlatRateCarry
from .carry_model import CARRY_MODEL_REGISTRY
from .errors import ConfigError
from .fill_model import FILL_MODEL_REGISTRY, FillModel

REQUIRED_KEYS = ("carry_model", "fill_model")


@dataclass(frozen=True)
class SimObjects:
    """The live objects built from a SimConfig dict; rebuilt from the config each time,
    never stored or hashed."""

    carry_model: FlatRateCarry
    fill_model: FillModel


def validate_sim_config(config: dict[str, Any]) -> None:
    """Raise ConfigError naming any missing or unknown top-level keys."""
    if not isinstance(config, dict):
        raise ConfigError(f"SimConfig must be a dict, got {type(config).__name__}")
    missing = [key for key in REQUIRED_KEYS if key not in config]
    if missing:
        raise ConfigError(f"SimConfig is missing required key(s): {', '.join(missing)}")
    unknown = [key for key in config if key not in REQUIRED_KEYS]
    if unknown:
        raise ConfigError(f"SimConfig has unknown key(s): {', '.join(unknown)}")


def build_sim_objects(config: dict[str, Any]) -> SimObjects:
    """Validate a SimConfig dict and construct the live objects it describes.

    Raises ConfigError, naming the offending key, for any invalid config: missing or
    unknown keys, unknown model types, or wrong-typed values. It raises nothing else, so
    callers can treat ConfigError as the complete contract for a bad config.
    """
    validate_sim_config(config)
    return SimObjects(
        carry_model=CARRY_MODEL_REGISTRY.build(config["carry_model"]),
        fill_model=FILL_MODEL_REGISTRY.build(config["fill_model"]),
    )

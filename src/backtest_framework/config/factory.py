"""Generic declarative-config factory registry.

Configs are plain data (dicts/strings) so they can be hashed, stored in the
TrialRegistry, diffed and reloaded; live objects (cost models, CostStacks) do not
serialise or hash stably. A FactoryRegistry maps a config dict's "type" key to the
function that builds the live object. Only the config is hashed or persisted, and the
object is rebuilt from it on every run, so config -> hash -> registry -> reload -> re-run
is reproducible.

The carry model and stop-fill model each have their own FactoryRegistry instance; the
cost-stack config (config/cost_stack.py) uses one too.
"""

from __future__ import annotations

from typing import Any, Callable

from .errors import ConfigError

FactoryFunc = Callable[[dict[str, Any]], Any]


class FactoryRegistry:
    """Map a config dict's `"type"` value to the function that builds its live object.

    `kind` is a label (e.g. "carry_model") used only in error messages.
    """

    def __init__(self, kind: str):
        self._kind = kind
        self._factories: dict[str, FactoryFunc] = {}

    def register(self, type_name: str, factory: FactoryFunc) -> None:
        self._factories[type_name] = factory

    def build(self, config: dict[str, Any]) -> Any:
        if not isinstance(config, dict):
            raise ConfigError(f"{self._kind} config must be a dict, got {type(config).__name__}")
        if "type" not in config:
            raise ConfigError(f"{self._kind} config is missing required key 'type'")
        type_name = config["type"]
        if type_name not in self._factories:
            known = ", ".join(sorted(self._factories)) or "(none registered)"
            raise ConfigError(
                f"{self._kind} config key 'type' names an unknown type {type_name!r}; known types: {known}"
            )
        # Other exceptions are not converted to ConfigError. Every factory here validates
        # its own arguments and raises ConfigError itself (via `_required_numeric` /
        # `_optional_numeric`, an enum check, or the brick-level unknown-key check), so a
        # KeyError, TypeError or ValueError from a factory is a fault inside it, not a bad
        # config. For example, `calibrate_impact_params` (called by the `sqrt_impact`
        # factory) raises ValueError on data faults: too few bars, zero return volatility, a
        # missing volume series, no usable volume, non-positive mean volume, or volumes
        # misaligned with bars.
        return self._factories[type_name](config)

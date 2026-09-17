"""Generic declarative-config factory registry (D35, D52).

D35: configs are plain data (dicts/strings) so they can be hashed, stored in the
TrialRegistry, diffed, and reloaded — live objects (cost model instances, CostStacks)
don't serialise or hash stably. A FactoryRegistry maps a config dict's "type" key to the
function that builds the corresponding live object; the config itself is the only thing
that ever gets hashed or persisted, and the live object is rebuilt fresh from it on every
run — that's what makes the reproducibility loop (config -> hash -> registry -> reload ->
re-run) actually hold.

This registry is deliberately generic and not tied to any one kind of model. Step 2 uses
it for two small, already-existing pieces of behaviour (carry accrual, stop fills) to
prove the mechanism end-to-end; Step 3's CostStack bricks are expected to register with
their own FactoryRegistry instance using the same pattern, not a new one.
"""

from __future__ import annotations

from typing import Any, Callable

from .errors import ConfigError

FactoryFunc = Callable[[dict[str, Any]], Any]


class FactoryRegistry:
    """Maps a config dict's `"type"` value to the function that builds a live object
    from that config. `kind` is a human-readable label (e.g. "carry_model") used only to
    make error messages name the right thing.
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
                f"{self._kind} config key 'type' names an unknown type {type_name!r} — known types: {known}"
            )
        # NOT wrapped in `except (KeyError, TypeError, ValueError)`. Every factory in this
        # repository validates its own arguments and raises ConfigError itself -- through
        # `_required_numeric` / `_optional_numeric`, through an inline enum check, or now
        # through the brick-level unknown-key check. So a KeyError, TypeError or ValueError
        # escaping a factory does not mean the config was bad; it means something inside the
        # factory went wrong, and relabelling it "invalid config" sends the reader to the
        # wrong file.
        #
        # The concrete case is `sqrt_impact`, whose factory calls `calibrate_impact_params`.
        # That function raises bare ValueError in seven places and SIX of them are data
        # faults, not config faults: too few bars, zero return volatility, a missing volume
        # series, no usable volume observations, non-positive mean volume, and -- the one
        # that gives the game away -- "{symbol} has N volumes against M bars", which is a
        # panel misalignment being reported as a typo in a dict. A zero close reaches
        # math.log and surfaces as "invalid cost_brick config: math domain error".
        #
        # Those now propagate as themselves. The only thing lost is a uniform exception
        # type, which nothing catches: no caller anywhere recovers from ConfigError.
        return self._factories[type_name](config)

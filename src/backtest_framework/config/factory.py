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
        try:
            return self._factories[type_name](config)
        except ConfigError:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise ConfigError(f"invalid {self._kind} config for type {type_name!r}: {exc}") from exc

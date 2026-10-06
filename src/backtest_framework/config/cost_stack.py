"""Declarative cost-stack config: the dict a study logs is the dict its stack is built from.

`build_cost_stack(config, context)` builds the stack from the same dict that is logged and
hashed by the TrialRegistry, so the record and the objects run cannot diverge.

Shape (the `{"type": ..., ...params}` convention, one list per CostStack slot):

    {
        "trade_bricks": [{"type": "ibkr_commission"},
                          {"type": "sqrt_impact", "coefficient": 1.0,
                           "calibration": "full_sample"},
                          {"type": "percent_spread", "bps": 1.0}],
        "carry_bricks": [{"type": "borrow_fee", "annual_rate": 0.0025}],
        "portfolio_carry_bricks": [{"type": "margin_interest", "annual_rate": 0.06}],
        "event_flow_bricks": [{"type": "dividend_flow", "source": "snapshot_declared"}],
    }

The futures round-trip line is one brick (commission plus crossing), declared either by
naming a contract in the cost table or by giving both numbers explicitly:

    {"type": "futures_round_trip", "root": "MES"}                              # the table's default line
    {"type": "futures_round_trip", "root": "ES", "line": "effective_es_bp"}  # a named crossing line
    {"type": "futures_round_trip", "commission_rt_usd": 3.0,
                                   "crossing_ticks_rt": 1.0}                   # explicit, no table

`root` takes a parent root ("ES", resolved to its minimum tradable size) or a traded symbol
("MES", "ZN"). `line` names the crossing measurement and requires `root`. Defaults and
errors come from `data/futures_costs.json`, so an unmeasured root fails at factory time.
Mixing the two forms raises.

The futures impact line is the size-dependent term the round trip omits. It is
table-resolved only:

    {"type": "futures_sqrt_impact", "root": "ES"}                       # the default line
    {"type": "futures_sqrt_impact", "root": "ES", "line": "trades_2025_2026",
                                    "coefficient": 0.7}                 # a named measurement

`root` is a parent root as keyed in `data/futures_impact_params.json` (36 roots); `line`
names the (ADV, σ) measurement, `day1m_2016_2023` by default. `coefficient` defaults to
Y = 0.7, where `sqrt_impact` uses Y ≈ 1. ADV and σ cannot be written into the config, since
they would lack the measurement window and provenance the table records.

Data-dependent bricks (sqrt_impact, dividend_flow) are built against a `StackDataContext`
derived from the snapshot, so config plus snapshot determine the stack. The sqrt_impact
`calibration` key records what the context holds: "full_sample" (the whole snapshot, a
documented look-ahead in cost parameters) or "train_window" (a walk-forward train slice).
The caller must supply the matching context; the key makes the two hash differently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ..costs.bricks import FlatCommission, FlatRateCarry, PercentOfNotionalSpread
from ..costs.calibration import calibrate_impact_params
from ..costs.equity_bricks import BorrowFee, DividendFlow, IBKRCommission, MarginInterest, SqrtImpact
from ..costs.futures_bricks import (
    FuturesCommission,
    FuturesCostError,
    FuturesRoundTrip,
    TickCrossing,
)
from ..costs.futures_impact import DEFAULT_IMPACT_Y, FuturesImpactError, FuturesSqrtImpact
from ..costs.stack import CostStack
from ..data.bars import TimestampedBar
from ..data.corporate_actions import CorporateActions, as_declared_dividends
from .errors import ConfigError
from .factory import FactoryRegistry

STACK_SLOTS = ("trade_bricks", "carry_bricks", "portfolio_carry_bricks", "event_flow_bricks")

IMPACT_CALIBRATIONS = ("full_sample", "train_window")


@dataclass(frozen=True)
class StackDataContext:
    """The snapshot-derived data a declarative stack config is built against."""

    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]]
    volumes_by_symbol: Mapping[str, Sequence[float]]
    actions: CorporateActions


def _required_numeric(config: dict, key: str, kind: str) -> float:
    if key not in config:
        raise ConfigError(f"{kind} config is missing required key {key!r}")
    value = config[key]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConfigError(f"{kind} config key {key!r} must be numeric, got {type(value).__name__}")
    return float(value)


def _optional_numeric(config: dict, key: str, default: float, kind: str) -> float:
    if key not in config:
        return default
    value = config[key]
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ConfigError(f"{kind} config key {key!r} must be numeric, got {type(value).__name__}")
    return float(value)


#: Every key each brick type reads, `type` included. Unknown keys raise, so a typo in an
#: optional key (e.g. `"coeficient"` for `sqrt_impact`) cannot build a brick at the default
#: while the registry records the typed value. Required keys are checked by
#: `_required_numeric`.
#:
#: Add a key here in the same change that adds it to the factory; a missing key makes a
#: valid config raise. Some rows (`flat_commission`, `flat_rate_carry`, the optional
#: `ibkr_commission` keys) have little test coverage.
BRICK_KEYS: dict[str, frozenset[str]] = {
    "flat_commission": frozenset({"type", "amount"}),
    "percent_spread": frozenset({"type", "bps"}),
    "ibkr_commission": frozenset({"type", "per_share", "min_per_order", "max_pct_of_trade_value"}),
    "borrow_fee": frozenset({"type", "annual_rate"}),
    "margin_interest": frozenset({"type", "annual_rate"}),
    "flat_rate_carry": frozenset({"type", "annual_rate"}),
    # `volume_units` must stay optional: older stored configs omit it.
    "sqrt_impact": frozenset({"type", "coefficient", "calibration", "volume_units"}),
    "dividend_flow": frozenset({"type", "source"}),
    # Both declaration forms: `root` (+ optional `line`) from data/futures_costs.json, or
    # explicit `commission_rt_usd` and `crossing_ticks_rt`. The factory rejects a mixture.
    "futures_round_trip": frozenset(
        {"type", "commission_rt_usd", "crossing_ticks_rt", "root", "line"}
    ),
    # Table-resolved only: `root` picks the instrument, optional `line` the (ADV, sigma)
    # measurement in data/futures_impact_params.json.
    "futures_sqrt_impact": frozenset({"type", "root", "coefficient", "line"}),
}


def _validate_brick_keys(brick: Any, slot: str) -> None:
    """Reject a key no factory reads, naming it and listing what the type accepts.

    Kept here rather than on `FactoryRegistry`, which the `carry_model` and `fill_model`
    registries share (for example `act365` takes an optional `day_count`).
    """
    if not isinstance(brick, dict):
        raise ConfigError(f"cost_stack slot {slot!r} contains a {type(brick).__name__}, not a dict")
    type_name = brick.get("type")
    # A missing or unknown `type` is left to FactoryRegistry.build, which lists known types.
    if not isinstance(type_name, str) or type_name not in BRICK_KEYS:
        return
    unknown = sorted(k for k in brick if k not in BRICK_KEYS[type_name])
    if unknown:
        allowed = ", ".join(sorted(BRICK_KEYS[type_name] - {"type"})) or "(no parameters)"
        raise ConfigError(
            f"cost_stack slot {slot!r}: {type_name} brick has unknown key(s): "
            f"{', '.join(unknown)}; {type_name} accepts: {allowed}. The factory would ignore "
            "an unrecognised key, so the logged config and the built object would disagree."
        )


def _brick_registry(context: StackDataContext) -> FactoryRegistry:
    """Build the cost-brick FactoryRegistry; data-dependent factories close over `context`."""
    registry = FactoryRegistry(kind="cost_brick")

    registry.register(
        "flat_commission",
        lambda c: FlatCommission(amount=_required_numeric(c, "amount", "flat_commission")),
    )
    registry.register(
        "percent_spread",
        lambda c: PercentOfNotionalSpread(bps=_required_numeric(c, "bps", "percent_spread")),
    )
    registry.register(
        "ibkr_commission",
        lambda c: IBKRCommission(
            per_share=_optional_numeric(c, "per_share", 0.005, "ibkr_commission"),
            min_per_order=_optional_numeric(c, "min_per_order", 1.00, "ibkr_commission"),
            max_pct_of_trade_value=_optional_numeric(c, "max_pct_of_trade_value", 0.01, "ibkr_commission"),
        ),
    )
    registry.register(
        "borrow_fee",
        lambda c: BorrowFee(annual_rate=_required_numeric(c, "annual_rate", "borrow_fee")),
    )
    registry.register(
        "margin_interest",
        lambda c: MarginInterest(annual_rate=_required_numeric(c, "annual_rate", "margin_interest")),
    )
    registry.register(
        "flat_rate_carry",
        lambda c: FlatRateCarry(annual_rate=_required_numeric(c, "annual_rate", "flat_rate_carry")),
    )

    def _build_sqrt_impact(c: dict) -> SqrtImpact:
        calibration = c.get("calibration", "full_sample")
        if calibration not in IMPACT_CALIBRATIONS:
            raise ConfigError(
                f"sqrt_impact config key 'calibration' must be one of {IMPACT_CALIBRATIONS}, "
                f"got {calibration!r}"
            )
        # `volume_units` defaults to "shares". A crypto fixture reports quote-currency
        # notional and must set it: SqrtImpact divides order quantity by ADV, so mismatched
        # units scale the charge by the square root of the price.
        units = c.get("volume_units", "shares")
        return SqrtImpact(
            params_by_symbol=calibrate_impact_params(
                context.bars_by_symbol, context.volumes_by_symbol, volume_units=units
            ),
            coefficient=_optional_numeric(c, "coefficient", 1.0, "sqrt_impact"),
        )

    registry.register("sqrt_impact", _build_sqrt_impact)

    def _build_dividend_flow(c: dict) -> DividendFlow:
        source = c.get("source", "snapshot_declared")
        if source != "snapshot_declared":
            raise ConfigError(
                f"dividend_flow config key 'source' must be 'snapshot_declared', got {source!r}"
            )
        declared = {
            symbol: tuple(as_declared_dividends(divs, context.actions.splits_by_symbol.get(symbol, ())))
            for symbol, divs in context.actions.dividends_by_symbol.items()
        }
        return DividendFlow(dividends_by_symbol=declared)

    registry.register("dividend_flow", _build_dividend_flow)

    def _build_futures_round_trip(c: dict) -> FuturesRoundTrip:
        """Build the futures round-trip line, table-resolved or explicit but not both.

        Ignores `context`: the line is determined by the config and
        `data/futures_costs.json`. The table's digest is not in the config hash; the table
        has its own `_provenance`, and `tests/golden/test_futures_costs_ledger.py` checks it.
        """
        by_root = "root" in c
        explicit = "commission_rt_usd" in c or "crossing_ticks_rt" in c
        if by_root and explicit:
            raise ConfigError(
                "futures_round_trip config gives both 'root' and explicit cost numbers. It "
                "must give one or the other: a logged config that carried both would say one "
                "cost and build another as soon as the table moved."
            )
        if by_root:
            if not isinstance(c["root"], str):
                raise ConfigError(
                    f"futures_round_trip config key 'root' must be a string, got "
                    f"{type(c['root']).__name__}"
                )
            line = c.get("line")
            if line is not None and not isinstance(line, str):
                raise ConfigError(
                    f"futures_round_trip config key 'line' must be a string, got "
                    f"{type(line).__name__}"
                )
            try:
                return FuturesRoundTrip.from_table(c["root"], line=line)
            except FuturesCostError as exc:
                raise ConfigError(f"futures_round_trip: {exc}") from exc
        if "line" in c:
            raise ConfigError(
                "futures_round_trip config key 'line' names a crossing measurement in "
                "data/futures_costs.json and is meaningless without 'root'. With explicit "
                "numbers, the crossing is crossing_ticks_rt."
            )
        return FuturesRoundTrip(
            commission=FuturesCommission(
                _required_numeric(c, "commission_rt_usd", "futures_round_trip")
            ),
            crossing=TickCrossing(
                _required_numeric(c, "crossing_ticks_rt", "futures_round_trip")
            ),
        )

    registry.register("futures_round_trip", _build_futures_round_trip)

    def _build_futures_sqrt_impact(c: dict) -> FuturesSqrtImpact:
        """Build the futures impact term from the table.

        Ignores `context`: the parameters are a recorded measurement in
        `data/futures_impact_params.json`, not calibrated from the snapshot as `sqrt_impact`
        is, so the line name takes the place of a `calibration` key.

        `coefficient` defaults to Y = 0.7, not `sqrt_impact`'s 1.0.
        """
        root = c.get("root")
        if not isinstance(root, str):
            raise ConfigError(
                "futures_sqrt_impact config needs a string 'root'; the impact parameters are "
                f"table-resolved and there is no explicit form, got {type(root).__name__}"
            )
        line = c.get("line")
        if line is not None and not isinstance(line, str):
            raise ConfigError(
                f"futures_sqrt_impact config key 'line' must be a string, got {type(line).__name__}"
            )
        try:
            return FuturesSqrtImpact.from_table(
                root,
                line=line,
                coefficient=_optional_numeric(c, "coefficient", DEFAULT_IMPACT_Y, "futures_sqrt_impact"),
            )
        except FuturesImpactError as exc:
            raise ConfigError(f"futures_sqrt_impact: {exc}") from exc

    registry.register("futures_sqrt_impact", _build_futures_sqrt_impact)
    return registry


def validate_stack_config(config: dict[str, Any]) -> None:
    """Validate slots and brick keys before any brick is built; raises `ConfigError`."""
    if not isinstance(config, dict):
        raise ConfigError(f"cost_stack config must be a dict, got {type(config).__name__}")
    missing = [slot for slot in STACK_SLOTS if slot not in config]
    if missing:
        raise ConfigError(f"cost_stack config is missing required slot(s): {', '.join(missing)}")
    unknown = [key for key in config if key not in STACK_SLOTS]
    if unknown:
        raise ConfigError(f"cost_stack config has unknown key(s): {', '.join(unknown)}")
    for slot in STACK_SLOTS:
        if not isinstance(config[slot], (list, tuple)):
            raise ConfigError(f"cost_stack slot {slot!r} must be a list of brick configs")
        for brick in config[slot]:
            _validate_brick_keys(brick, slot)


def build_cost_stack(config: dict[str, Any], context: StackDataContext) -> CostStack:
    """Build a CostStack from its declarative config.

    Log the same dict, unchanged, in the TrialRegistry config.
    """
    validate_stack_config(config)
    registry = _brick_registry(context)
    built = {slot: tuple(registry.build(brick) for brick in config[slot]) for slot in STACK_SLOTS}
    return CostStack(**built)

"""Declarative cost-stack config (D35, D52, D102): the dict a study LOGS is the
dict its stack is BUILT from.

The audit (F2) found the D35 mechanism had only ever been proven on two Step-2
demonstration models while every real run constructed live cost objects directly
and logged a free-hand description dict — so the TrialRegistry's config hash
covered a description nothing verified against the objects actually run. This
module closes that gap for the cost stack: `build_cost_stack(config, context)`
consumes the exact dict `StudyConfig.to_dict()` logs, so description and
construction cannot drift.

Shape (D52's `{"type": ..., ...params}` convention, one list per CostStack slot):

    {
        "trade_bricks": [{"type": "ibkr_commission"},
                          {"type": "sqrt_impact", "coefficient": 1.0,
                           "calibration": "full_sample"},
                          {"type": "percent_spread", "bps": 1.0}],
        "carry_bricks": [{"type": "borrow_fee", "annual_rate": 0.0025}],
        "portfolio_carry_bricks": [{"type": "margin_interest", "annual_rate": 0.06}],
        "event_flow_bricks": [{"type": "dividend_flow", "source": "snapshot_declared"}],
    }

Data-dependent bricks (sqrt_impact, dividend_flow) are built against a
`StackDataContext` derived from the snapshot, so config + snapshot data fully
determine the stack. The sqrt_impact `calibration` key records WHOSE data the
context slice holds — "full_sample" (the whole snapshot, D66's documented
look-ahead) or "train_window" (a walk-forward train slice, D44-compliant,
D102) — the caller is responsible for supplying the matching context; the key
exists so the two regimes hash differently and can never be confused in the
registry.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from ..costs.bricks import FlatCommission, FlatRateCarry, PercentOfNotionalSpread
from ..costs.calibration import calibrate_impact_params
from ..costs.equity_bricks import BorrowFee, DividendFlow, IBKRCommission, MarginInterest, SqrtImpact
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


def _brick_registry(context: StackDataContext) -> FactoryRegistry:
    """One type-keyed registry (D52's mechanism, not a new dialect) whose
    data-dependent factories close over the snapshot context."""
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
        # `volume_units` defaults to "shares", the equity convention every caller before
        # D187 assumed. A crypto fixture reports quote-currency notional and MUST say so:
        # SqrtImpact divides an order quantity by ADV, so mismatched units scale the whole
        # charge by the square root of the price.
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
    return registry


def validate_stack_config(config: dict[str, Any]) -> None:
    """Fail loudly, naming the bad key, at factory time — never at bar 3,000."""
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


def build_cost_stack(config: dict[str, Any], context: StackDataContext) -> CostStack:
    """Build a live CostStack from its declarative description (D102). The same
    dict belongs in the TrialRegistry config verbatim — hash what you run."""
    validate_stack_config(config)
    registry = _brick_registry(context)
    built = {slot: tuple(registry.build(brick) for brick in config[slot]) for slot in STACK_SLOTS}
    return CostStack(**built)

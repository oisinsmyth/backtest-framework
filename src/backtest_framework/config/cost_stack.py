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

The futures line (D591) is one brick with two halves, and it is declared EITHER by naming a
contract in the cost table or by writing both numbers out — never half of each:

    {"type": "futures_round_trip", "root": "MES"}                    # the table's default line
    {"type": "futures_round_trip", "root": "ES", "line": "d465"}     # a named crossing census
    {"type": "futures_round_trip", "commission_rt_usd": 3.0,
                                   "crossing_ticks_rt": 1.0}         # explicit, no table

`root` takes a parent root ("ES", which resolves to its MINIMUM TRADABLE SIZE — the size
`COMPONENTS_PROP.md` scores a component at) or a traded symbol ("MES", "ZN"). `line` names
which crossing measurement is charged and is only meaningful with `root`; both default and
every failure are `data/futures_costs.json`'s to raise, so a config naming a root nothing
measured fails at factory time rather than charging a neighbouring root's spread. Mixing the
two forms raises: a config that carried both would hash as one thing and build as another,
which is the drift this module exists to close.

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
from ..costs.futures_bricks import (
    FuturesCommission,
    FuturesCostError,
    FuturesRoundTrip,
    TickCrossing,
)
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


#: Every key each brick type reads, `type` included. The slot level has rejected unknown
#: keys since D102 and the brick level did not, so `{"type": "sqrt_impact", "coeficient": 3.0}`
#: built a brick at the DEFAULT coefficient and raised nothing -- after which the TrialRegistry
#: stored the dict verbatim, and the logged config said 3.0 while the object that produced the
#: numbers used 1.0. That is precisely the drift this module's docstring says it exists to
#: close: "the dict a study LOGS is the dict its stack is BUILT from".
#:
#: Only OPTIONAL parameters were ever exposed -- a typo on a required key already raised
#: through `_required_numeric` -- which is why this was invisible: the silent surface is
#: exactly `ibkr_commission`'s three, `sqrt_impact`'s three and `dividend_flow`'s one.
#:
#: MAINTENANCE, and it matters more than it looks. A key missing from a row here turns a
#: working config into a raise, and four of these keys are exercised by nothing anywhere in
#: the repository -- `flat_commission` and `flat_rate_carry` appear in no source literal and
#: in none of the 176,592 configs stored across the trial registries, and `ibkr_commission`
#: is stored 4,393 times always as the bare `{"type": "ibkr_commission"}`. No test and no
#: replay would catch a typo in those rows. Add a key here in the same commit that adds it
#: to the factory.
BRICK_KEYS: dict[str, frozenset[str]] = {
    "flat_commission": frozenset({"type", "amount"}),
    "percent_spread": frozenset({"type", "bps"}),
    "ibkr_commission": frozenset({"type", "per_share", "min_per_order", "max_pct_of_trade_value"}),
    "borrow_fee": frozenset({"type", "annual_rate"}),
    "margin_interest": frozenset({"type", "annual_rate"}),
    "flat_rate_carry": frozenset({"type", "annual_rate"}),
    # `volume_units` is OPTIONAL and must stay so: 2,170 trials stored before D187 carry
    # `sqrt_impact` without it, and rejecting them would retroactively invalidate a
    # published pool.
    "sqrt_impact": frozenset({"type", "coefficient", "calibration", "volume_units"}),
    "dividend_flow": frozenset({"type", "source"}),
    # D591. Two declaration forms share one row because they build one brick: `root` (+ the
    # optional `line`) resolves from data/futures_costs.json, or `commission_rt_usd` and
    # `crossing_ticks_rt` are both given outright. The factory rejects a mixture; the row
    # cannot, since an allowed-key table only knows which keys a type reads.
    "futures_round_trip": frozenset(
        {"type", "commission_rt_usd", "crossing_ticks_rt", "root", "line"}
    ),
}


def _validate_brick_keys(brick: Any, slot: str) -> None:
    """Reject a key no factory reads, naming it and listing what the type accepts.

    Deliberately here rather than on `FactoryRegistry`, which is shared with the
    `carry_model` and `fill_model` registries -- `act365` takes an optional `day_count`
    that has nothing to do with cost bricks, and a generic check would have to learn about
    it. The cost-brick dialect validates its own dialect.
    """
    if not isinstance(brick, dict):
        raise ConfigError(f"cost_stack slot {slot!r} contains a {type(brick).__name__}, not a dict")
    type_name = brick.get("type")
    # A missing or unknown `type` is FactoryRegistry.build's error to raise, with its own
    # message listing the known types. Saying nothing here leaves that message intact.
    if not isinstance(type_name, str) or type_name not in BRICK_KEYS:
        return
    unknown = sorted(k for k in brick if k not in BRICK_KEYS[type_name])
    if unknown:
        allowed = ", ".join(sorted(BRICK_KEYS[type_name] - {"type"})) or "(no parameters)"
        raise ConfigError(
            f"cost_stack slot {slot!r}: {type_name} brick has unknown key(s): "
            f"{', '.join(unknown)} — {type_name} accepts: {allowed}. An unrecognised key is "
            "silently ignored by the factory, so the logged config and the object built from "
            "it would disagree."
        )


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

    def _build_futures_round_trip(c: dict) -> FuturesRoundTrip:
        """D591's futures line. Table-resolved or explicit, never both.

        Note this factory ignores `context`: a futures cost line is declared, not calibrated
        from the snapshot, so `config + data/futures_costs.json` fully determine it. The
        table's digest is not part of the config hash — that is what the artefact's own
        `_provenance` is for, and what `tests/golden/test_futures_costs_ledger.py` gates.
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
                "numbers, the crossing IS crossing_ticks_rt."
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
        for brick in config[slot]:
            _validate_brick_keys(brick, slot)


def build_cost_stack(config: dict[str, Any], context: StackDataContext) -> CostStack:
    """Build a live CostStack from its declarative description (D102). The same
    dict belongs in the TrialRegistry config verbatim — hash what you run."""
    validate_stack_config(config)
    registry = _brick_registry(context)
    built = {slot: tuple(registry.build(brick) for brick in config[slot]) for slot in STACK_SLOTS}
    return CostStack(**built)

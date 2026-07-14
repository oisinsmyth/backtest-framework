"""Capacity analysis (D95): at what AUM does the v2 edge clear TRUE costs?

The D8 multiplier sweep scales all frictions uniformly — it cannot see account
size. The real bricks can: IBKR's $1/order minimum penalizes small accounts,
√-impact penalizes large ones (impact fraction ∝ √(Q/ADV)), and spread / borrow /
margin are scale-invariant rates. So this module runs the SAME study at log-spaced
`starting_cash` levels with the real unscaled stack and lets the bricks produce
the size dependence — a measurement, not an extrapolation.

Attribution comes from recording wrappers (the D68 scaling-wrapper pattern, with
accumulation instead of multiplication): each brick's charges land in a CostLedger
keyed by brick class name, and the trade recorder tracks per-symbol max |Q| so the
doc can report participation = max|Q|/ADV — the boundary of the √-law's calibrated
range. Recorders return the inner brick's value UNCHANGED; the transparency
identity (recorded run ≡ plain run, to the penny) is a tested property.

Ledger-validity constraint (D95): capacity runs use multipliers=(1.0,) only. A 0×
run through a recording stack would still record the unscaled costs of a
*different* trade path and poison the ledger.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Callable, Mapping, Sequence

from ..analytics.metrics import max_drawdown
from ..costs.stack import CostStack
from ..data.bars import TimestampedBar
from ..data.corporate_actions import CorporateActions
from ..instruments.base import Instrument
from ..registry.trial_registry import TrialRegistry
from .pairs_study import StudyConfig, StudyResult, build_base_cost_stack, run_pairs_study


@dataclass
class CostLedger:
    """Accumulated friction dollars by brick class name, plus per-symbol max |Q|."""

    totals: dict[str, float] = field(default_factory=dict)
    max_quantity_by_symbol: dict[str, float] = field(default_factory=dict)

    def record(self, brick_name: str, amount: float) -> None:
        self.totals[brick_name] = self.totals.get(brick_name, 0.0) + amount

    def record_quantity(self, symbol: str, quantity: float) -> None:
        q = abs(quantity)
        if q > self.max_quantity_by_symbol.get(symbol, 0.0):
            self.max_quantity_by_symbol[symbol] = q


@dataclass(frozen=True)
class _RecordingTradeBrick:
    inner: object
    ledger: CostLedger

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        amount = self.inner.cost(instrument, quantity, price)
        self.ledger.record(type(self.inner).__name__, amount)
        symbol = getattr(instrument, "symbol", None)
        if symbol is not None:
            self.ledger.record_quantity(symbol, quantity)
        return amount


@dataclass(frozen=True)
class _RecordingCarryBrick:
    inner: object
    ledger: CostLedger

    def cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        amount = self.inner.cost(base_amount, prev_timestamp, curr_timestamp)
        self.ledger.record(type(self.inner).__name__, amount)
        return amount


def recording_cost_stack(stack: CostStack) -> tuple[CostStack, CostLedger]:
    """Wrap every FRICTION brick with a recorder sharing one ledger.
    event_flow_bricks pass through unwrapped — dividends are transfers, not
    frictions (the same boundary costs/scaling.py draws, D75)."""
    ledger = CostLedger()
    recorded = CostStack(
        trade_bricks=tuple(_RecordingTradeBrick(brick, ledger) for brick in stack.trade_bricks),
        carry_bricks=tuple(_RecordingCarryBrick(brick, ledger) for brick in stack.carry_bricks),
        portfolio_carry_bricks=tuple(
            _RecordingCarryBrick(brick, ledger) for brick in stack.portfolio_carry_bricks
        ),
        event_flow_bricks=stack.event_flow_bricks,
    )
    return recorded, ledger


@dataclass
class CapacityLevel:
    aum: float
    label: str
    study: StudyResult
    ledger: CostLedger
    avg_nav: float
    years: float
    max_participation: float
    """max over symbols of (max |Q| traded) / ADV_shares — the √-law boundary."""
    participation_symbol: str

    @property
    def net_return(self) -> float:
        return self.study.curves[1.0].final_nav / self.aum - 1.0

    @property
    def net_return_annual(self) -> float:
        return (1.0 + self.net_return) ** (1.0 / self.years) - 1.0

    @property
    def max_dd(self) -> float:
        return max_drawdown(self.study.curves[1.0].equity)

    def annualized_drag(self, brick_name: str) -> float:
        """Friction dollars for one brick, as % of average NAV per year."""
        return self.ledger.totals.get(brick_name, 0.0) / self.avg_nav / self.years


@dataclass
class CapacityResult:
    levels: list[CapacityLevel]
    config: StudyConfig
    snapshot_id: str


def _format_aum(aum: float) -> str:
    if aum >= 1_000_000:
        v = aum / 1_000_000
        return f"${v:g}M"
    v = aum / 1_000
    return f"${v:g}k"


def run_capacity_study(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]],
    actions: CorporateActions,
    registry: TrialRegistry,
    snapshot_id: str,
    aum_levels: Sequence[float],
    config: StudyConfig,
    selector_factory: Callable[[], object],
    adv_by_symbol: Mapping[str, float],
    trial_prefix: str = "capacity",
) -> CapacityResult:
    """One v2-configuration study per AUM level, real unscaled costs, recorded.
    `selector_factory` builds a FRESH selector per level (same reasoning as D68's
    strategy factories); `adv_by_symbol` is the same ADV the impact brick uses, so
    reported participation is self-consistent with the cost model. `trial_prefix`
    disambiguates trial ids when several sweeps share one registry (D96 — the
    gross sweep passes one prefix per leg_weight); the default preserves the D95
    capacity artifact's ids byte-for-byte."""
    levels: list[CapacityLevel] = []
    for aum in aum_levels:
        label = _format_aum(aum)
        recorded_stack, ledger = recording_cost_stack(
            build_base_cost_stack(bars_by_symbol, volumes_by_symbol, actions)
        )
        study = run_pairs_study(
            bars_by_symbol=bars_by_symbol,
            volumes_by_symbol=volumes_by_symbol,
            actions=actions,
            registry=registry,
            snapshot_id=snapshot_id,
            config=replace(config, starting_cash=aum, multipliers=(1.0,)),
            trial_id_prefix=f"{trial_prefix}-{label}",
            selector=selector_factory(),
            base_stack=recorded_stack,
            # D98 (audit F9): levels share one registry; a per-level DSR over the
            # accumulated mixed pool would be meaningless. These runs are cost
            # diagnostics, not signal trials (D95) — no DSR is computed or reported.
            compute_dsr=False,
        )
        curve = study.curves[1.0]
        avg_nav = sum(nav for _, nav in curve.equity) / len(curve.equity)
        years = len(curve.returns) / config.periods_per_year

        max_part, part_symbol = 0.0, "-"
        for symbol, q in ledger.max_quantity_by_symbol.items():
            participation = q / adv_by_symbol[symbol]
            if participation > max_part:
                max_part, part_symbol = participation, symbol

        levels.append(
            CapacityLevel(
                aum=aum,
                label=label,
                study=study,
                ledger=ledger,
                avg_nav=avg_nav,
                years=years,
                max_participation=max_part,
                participation_symbol=part_symbol,
            )
        )
    return CapacityResult(levels=levels, config=config, snapshot_id=snapshot_id)


#: Brick class names in doc-table order (must match build_base_cost_stack's bricks).
FRICTION_BRICKS = ("IBKRCommission", "PercentOfNotionalSpread", "SqrtImpact", "BorrowFee", "MarginInterest")


def render_capacity_headline_table(result: CapacityResult) -> str:
    lines = [
        "| AUM | Net return (9yr) | Net /yr | Max drawdown | Max participation (symbol) |",
        "|---|---|---|---|---|",
    ]
    for lv in result.levels:
        lines.append(
            f"| {lv.label} | {lv.net_return:+.2%} | {lv.net_return_annual:+.2%} | "
            f"{lv.max_dd:.2%} | {lv.max_participation:.2%} ({lv.participation_symbol}) |"
        )
    return "\n".join(lines)


def render_capacity_drag_table(result: CapacityResult) -> str:
    header = " | ".join(FRICTION_BRICKS)
    lines = [f"| AUM | {header} | Total |", "|---|" + "---|" * (len(FRICTION_BRICKS) + 1)]
    for lv in result.levels:
        drags = [lv.annualized_drag(name) for name in FRICTION_BRICKS]
        cells = " | ".join(f"{d:.3%}" for d in drags)
        lines.append(f"| {lv.label} | {cells} | {sum(drags):.3%} |")
    return "\n".join(lines)

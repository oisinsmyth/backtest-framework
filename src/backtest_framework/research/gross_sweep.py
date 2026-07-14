"""Gross exposure study (D96): does lower gross clear the cost floor?

The capacity analysis (D95) found the binding constraint is the scale-invariant
cost floor of a ~200% gross book — and the floor's biggest term is not linear in
gross. Margin interest is a THRESHOLD cost, charged on max(gross − NAV, 0): at
gross ≤ 100% of NAV it vanishes entirely. Per-component scaling in leg_weight
(lw; book gross when all pairs are in trade = 2·lw·NAV):

    edge ≈ ∝ lw · spread/borrow ∝ lw · margin = rate × max(2·lw − 1, 0)
    impact drag ∝ lw^1.5 (falls faster than the edge) · commission minimums
    constant (lower gross makes SMALL accounts strictly worse)

Whether the vanished floor beats the halved edge is a sign-unknown measurement.
This module is thin composition: one D95 capacity study per leg_weight — no new
machinery, one variable per study (the variable is leg_weight).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Callable, Mapping, Sequence

from ..data.bars import TimestampedBar
from ..data.corporate_actions import CorporateActions
from ..registry.trial_registry import TrialRegistry
from .capacity import CapacityLevel, CapacityResult, run_capacity_study
from .pairs_study import StudyConfig


@dataclass
class GrossSweepResult:
    by_leg_weight: dict[float, CapacityResult]
    config: StudyConfig
    snapshot_id: str

    @property
    def leg_weights(self) -> tuple[float, ...]:
        return tuple(self.by_leg_weight)

    @property
    def aum_labels(self) -> tuple[str, ...]:
        first = next(iter(self.by_leg_weight.values()))
        return tuple(lv.label for lv in first.levels)


def run_gross_sweep(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]],
    actions: CorporateActions,
    registry: TrialRegistry,
    snapshot_id: str,
    leg_weights: Sequence[float],
    aum_levels: Sequence[float],
    config: StudyConfig,
    selector_factory: Callable[[], object],
    adv_by_symbol: Mapping[str, float],
) -> GrossSweepResult:
    by_leg_weight: dict[float, CapacityResult] = {}
    for lw in leg_weights:
        by_leg_weight[lw] = run_capacity_study(
            bars_by_symbol=bars_by_symbol,
            volumes_by_symbol=volumes_by_symbol,
            actions=actions,
            registry=registry,
            snapshot_id=snapshot_id,
            aum_levels=aum_levels,
            config=replace(config, leg_weight=lw),
            selector_factory=selector_factory,
            adv_by_symbol=adv_by_symbol,
            trial_prefix=f"gross-lw{lw:g}",
        )
    return GrossSweepResult(by_leg_weight=by_leg_weight, config=config, snapshot_id=snapshot_id)


def _matrix(result: GrossSweepResult, cell: Callable[[CapacityLevel], float], fmt: str) -> str:
    lws = result.leg_weights
    header = " | ".join(f"lw {lw:g} (gross {2 * lw:.0%})" for lw in lws)
    lines = [f"| AUM | {header} |", "|---|" + "---|" * len(lws)]
    for i, label in enumerate(result.aum_labels):
        cells = " | ".join(format(cell(result.by_leg_weight[lw].levels[i]), fmt) for lw in lws)
        lines.append(f"| {label} | {cells} |")
    return "\n".join(lines)


def render_net_return_matrix(result: GrossSweepResult) -> str:
    """The headline: annualized net return per (AUM, leg_weight) cell."""
    return _matrix(result, lambda lv: lv.net_return_annual, "+.2%")


def render_margin_drag_matrix(result: GrossSweepResult) -> str:
    """The mechanism exhibit: margin interest collapses below the gross ≤ NAV
    threshold instead of scaling down."""
    return _matrix(result, lambda lv: lv.annualized_drag("MarginInterest"), ".3%")


def render_total_drag_matrix(result: GrossSweepResult) -> str:
    from .capacity import FRICTION_BRICKS

    return _matrix(
        result, lambda lv: sum(lv.annualized_drag(b) for b in FRICTION_BRICKS), ".3%"
    )

"""RiskMonitor: per-bar portfolio-level risk checks (D30).

Positions can drift into violation purely from price movement, with no order ever
firing a check — a pair whose both legs move against the position can silently exceed
a gross exposure limit. RiskMonitor.evaluate() is meant to be called by the engine on
every bar, regardless of whether a trade happened that bar (the controls-engineering
framing D30 uses: safety interlocks run continuously, not only on operator commands).
pretrade_check() reuses the exact same limit logic to reject a proposed order before
it executes, by simulating the position it would produce and evaluating that.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..instruments.base import Instrument


@dataclass(frozen=True)
class RiskLimits:
    max_gross_exposure: float
    """Sum of absolute notional across all positions, in quote currency (e.g. 2x
    capital for a ~200%-gross-exposure pairs book, per D5's rationale)."""


@dataclass(frozen=True)
class RiskViolation:
    rule: str
    limit: float
    observed: float
    bar_index: int | None = None
    """Which bar the violation was flagged on, when evaluate() is called per-bar.
    None for pretrade_check(), which isn't tied to a specific bar index."""


def gross_exposure(
    positions: Mapping[str, float],
    prices: Mapping[str, float],
    instruments: Mapping[str, Instrument],
) -> float:
    """Sum of absolute notional across every open position — long and short exposure
    both count, since both consume buying power and both carry price risk."""
    return sum(
        abs(instruments[instrument_id].notional(quantity, prices[instrument_id]))
        for instrument_id, quantity in positions.items()
        if quantity != 0
    )


class RiskMonitor:
    def __init__(self, limits: RiskLimits):
        self.limits = limits

    def evaluate(
        self,
        positions: Mapping[str, float],
        prices: Mapping[str, float],
        instruments: Mapping[str, Instrument],
        bar_index: int | None = None,
    ) -> RiskViolation | None:
        """Called every bar by the engine, regardless of whether an order fired this
        bar (D30) — this is what catches exposure drifting over the limit from price
        movement alone, with no order to have gated in the first place."""
        exposure = gross_exposure(positions, prices, instruments)
        if exposure > self.limits.max_gross_exposure:
            return RiskViolation(
                rule="max_gross_exposure",
                limit=self.limits.max_gross_exposure,
                observed=exposure,
                bar_index=bar_index,
            )
        return None

    def pretrade_check(
        self,
        positions: Mapping[str, float],
        prices: Mapping[str, float],
        instruments: Mapping[str, Instrument],
        proposed_instrument_id: str,
        proposed_delta_qty: float,
    ) -> RiskViolation | None:
        """Simulates the position a proposed order would produce and evaluates it with
        the same limit logic as evaluate() — one set of rules, two call sites."""
        simulated_positions = dict(positions)
        simulated_positions[proposed_instrument_id] = (
            simulated_positions.get(proposed_instrument_id, 0.0) + proposed_delta_qty
        )
        exposure = gross_exposure(simulated_positions, prices, instruments)
        if exposure > self.limits.max_gross_exposure:
            return RiskViolation(
                rule="max_gross_exposure", limit=self.limits.max_gross_exposure, observed=exposure
            )
        return None

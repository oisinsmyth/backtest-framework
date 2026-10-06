"""RiskMonitor: per-bar portfolio-level risk checks.

Positions can breach a limit through price movement alone (e.g. both legs of a pair
moving against it), so the engine calls RiskMonitor.evaluate() on every bar, whether
or not a trade happened. pretrade_check() applies the same limit to the position a
proposed order would produce, to reject it before it executes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..instruments.base import Instrument


@dataclass(frozen=True)
class RiskLimits:
    max_gross_exposure: float
    """Sum of absolute notional across all positions, in quote currency (e.g. 2x
    capital for a ~200%-gross-exposure pairs book)."""


@dataclass(frozen=True)
class RiskViolation:
    rule: str
    limit: float
    observed: float
    bar_index: int | None = None
    """Bar the violation was flagged on, when evaluate() is given one. pretrade_check()
    leaves it None."""


def gross_exposure(
    positions: Mapping[str, float],
    prices: Mapping[str, float],
    instruments: Mapping[str, Instrument],
) -> float:
    """Sum of absolute notional across open positions; longs and shorts both count."""
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
        """Return a violation if current gross exposure exceeds the limit, else None.

        The engine calls this every bar, so exposure that drifts over the limit with
        price is caught even when no order fired."""
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
        """Check the position a proposed order would produce against the same limit as
        evaluate(). Returns a violation (with no bar_index) or None."""
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

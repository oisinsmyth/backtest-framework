"""PortfolioState: broker-facing cash and positions.

Tracks only the net, broker-facing book — what's actually held after netting (D27).
Per-strategy virtual books (D46) are deliberately not managed by this class; the engine
loop maintains those itself as a plain dict via the existing
`pipeline.sizing.apply_virtual_orders`, consistent with that module's stateless design
(D55) rather than duplicating bookkeeping in two places.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from ..instruments.base import Instrument


@dataclass
class PortfolioState:
    cash: float
    positions: dict[str, float] = field(default_factory=dict)

    def apply_fill(self, instrument_id: str, delta_qty: float, price: float, trade_cost: float) -> None:
        self.cash -= delta_qty * price  # buy (delta>0) spends cash; sell (delta<0) returns cash
        self.cash -= trade_cost
        self.positions[instrument_id] = self.positions.get(instrument_id, 0.0) + delta_qty

    def accrue_carry(self, carry_cost: float) -> None:
        self.cash -= carry_cost

    def nav(self, prices: Mapping[str, float], instruments: Mapping[str, Instrument]) -> float:
        # notional() is signed (quantity * price), so a short position's negative
        # quantity already contributes a negative notional here — this sum gives
        # cash + longs - |shorts| without special-casing shorts (D43).
        positions_value = sum(
            instruments[instrument_id].notional(quantity, prices[instrument_id])
            for instrument_id, quantity in self.positions.items()
            if quantity != 0
        )
        return self.cash + positions_value

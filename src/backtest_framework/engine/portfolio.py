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

    def apply_cash_flow(self, amount: float) -> None:
        """Signed event cash flow (D6/D75): positive credits (long receives a
        dividend), negative debits (short pays it)."""
        self.cash += amount

    def apply_split(self, instrument_id: str, ratio: float) -> None:
        """Scale a position for a split ex-date (D75): yfinance convention — 4.0 =
        4-for-1 forward (shares ×4), 0.25 = 1-for-4 reverse (shares ×0.25). Cash is
        untouched; NAV continuity comes from price moving by 1/ratio."""
        if instrument_id in self.positions:
            self.positions[instrument_id] *= ratio

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

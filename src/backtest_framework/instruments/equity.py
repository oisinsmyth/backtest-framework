"""Equity instrument (D12)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Equity:
    symbol: str
    quote_currency: str = "USD"
    quantity_precision: int | None = None
    """Decimal places tradeable_quantity rounds to. None means whole shares only; an
    integer (e.g. 4 for fractional shares, 8 as a crypto-precision stub) rounds to that
    many decimal places. This only proves the rounding mechanism generalizes — real
    crypto instrument semantics (funding as a carry component, 365-day calendar per
    D17) are D14/Step 10's job, not represented by this class."""

    def notional(self, quantity: float, price: float) -> float:
        return quantity * price

    def margin_requirement(self, quantity: float, price: float) -> float:
        # Full-notional stand-in; real margin schedules are Step 5+ territory.
        return abs(self.notional(quantity, price))

    def carry_components(self) -> tuple[str, ...]:
        return ("margin_interest", "borrow", "dividend")

    def tradeable_quantity(self, raw_quantity: float) -> float:
        if self.quantity_precision is None:
            return float(round(raw_quantity))
        return round(raw_quantity, self.quantity_precision)

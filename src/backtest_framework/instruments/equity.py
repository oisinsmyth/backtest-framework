"""Equity instrument."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Equity:
    symbol: str
    quote_currency: str = "USD"
    quantity_precision: int | None = None
    """Decimal places tradeable_quantity rounds to. None means whole shares; an integer
    (e.g. 4 for fractional shares, 8 for crypto precision) rounds to that many places.
    Only rounding is covered; crypto semantics (funding as a carry component, a 365-day
    trading calendar) are not represented."""

    def notional(self, quantity: float, price: float) -> float:
        return quantity * price

    def carry_components(self) -> tuple[str, ...]:
        # Matched by BorrowFee ("borrow") and DividendFlow ("dividend"). Margin interest is
        # absent: MarginInterest is in the portfolio slot, declares no `component`, and is
        # charged per book on max(gross - NAV, 0) through portfolio_carry_cost, unfiltered.
        return ("borrow", "dividend")

    def tradeable_quantity(self, raw_quantity: float) -> float:
        if self.quantity_precision is None:
            return float(round(raw_quantity))
        return round(raw_quantity, self.quantity_precision)

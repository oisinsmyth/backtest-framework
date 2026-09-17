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

    def carry_components(self) -> tuple[str, ...]:
        # "margin_interest" was the first entry here and was DELETED under D48: no
        # filter could ever match it. `costs/stack.py:_applies` is consulted only from
        # carry_cost and event_flow; MarginInterest (costs/equity_bricks.py:171) lives
        # in the PORTFOLIO slot (D5, D67), declares no `component`, and reaches the book
        # through portfolio_carry_cost, which applies no filter at all. So the entry
        # named a component that was neither honoured nor honourable — margin interest
        # is charged per BOOK, on max(gross - NAV, 0), not per leg. Removing it changes
        # no cost: _applies already admitted MarginInterest unconditionally, and still
        # does. "borrow" (BorrowFee) and "dividend" (DividendFlow) are the live pair.
        return ("borrow", "dividend")

    def tradeable_quantity(self, raw_quantity: float) -> float:
        if self.quantity_precision is None:
            return float(round(raw_quantity))
        return round(raw_quantity, self.quantity_precision)

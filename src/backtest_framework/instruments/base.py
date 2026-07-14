"""Instrument abstraction (D12).

Positions and fills reference instrument objects, not ticker strings — making the
"everything is a share of stock" assumption explicit and swappable is what enables
multi-asset support. Every instrument class supplies notional, margin_requirement,
carry_components, tradeable_quantity, and quote_currency; CostStack bricks (D1, D2) and
the sizing pipeline (D27) are written against this interface, not against any concrete
instrument type.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Instrument(Protocol):
    @property
    def quote_currency(self) -> str:
        """Read-only by declaration: every concrete instrument is a frozen
        dataclass, and a settable protocol attribute would mark them all
        non-conforming (audit F20)."""
        ...

    def notional(self, quantity: float, price: float) -> float:
        """Market value of `quantity` units at `price`, in quote_currency."""
        ...

    def margin_requirement(self, quantity: float, price: float) -> float:
        """Buying power locked up by holding `quantity` units at `price`."""
        ...

    def carry_components(self) -> tuple[str, ...]:
        """Names of the carry cost types applicable to this instrument (e.g.
        "margin_interest", "borrow", "dividend", "funding"). An empty tuple is a
        legitimate answer — "none apply" — not a missing implementation."""
        ...

    def tradeable_quantity(self, raw_quantity: float) -> float:
        """Round a raw desired quantity to whatever unit is actually tradeable (whole
        shares, fractional shares, whole option contracts, ...)."""
        ...

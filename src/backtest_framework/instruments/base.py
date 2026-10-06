"""Instrument abstraction.

Positions and fills reference instrument objects rather than ticker strings, which allows
multiple asset classes. Every instrument supplies notional, carry_components,
tradeable_quantity and quote_currency; CostStack bricks and the sizing pipeline use only
this interface.

There is no per-instrument margin requirement. `risk.gross_exposure` sizes buying-power
risk from `notional()`, and the portfolio-level margin base in `engine/backtest.py` is
computed from gross exposure and NAV. A buying-power lock (rejecting orders that breach a
hard leverage limit) is not implemented; it would need a margin member here and a
`RiskLimits` rule that reads it.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Instrument(Protocol):
    @property
    def quote_currency(self) -> str:
        """Declared read-only because every concrete instrument is a frozen dataclass;
        a settable protocol attribute would make them all non-conforming."""
        ...

    def notional(self, quantity: float, price: float) -> float:
        """Market value of `quantity` units at `price`, in quote_currency."""
        ...

    def carry_components(self) -> tuple[str, ...]:
        """Names of the carry cost types that apply to this instrument (e.g. "borrow",
        "dividend", "funding"). An empty tuple means none apply.

        A name has an effect only if some brick declares it as its `component`; the
        filter is `costs/stack.py:_applies`, called from `carry_cost` and `event_flow`.
        Margin interest is not a valid name: it is charged through
        `portfolio_carry_cost`, which has no instrument and applies no filter."""
        ...

    def tradeable_quantity(self, raw_quantity: float) -> float:
        """Round a desired quantity to the tradeable unit (whole shares, fractional
        shares, whole option contracts, ...)."""
        ...

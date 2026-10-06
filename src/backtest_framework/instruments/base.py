"""Instrument abstraction.

Positions and fills reference instrument objects, not ticker strings — making the
"everything is a share of stock" assumption explicit and swappable is what enables
multi-asset support. Every instrument class supplies notional, carry_components,
tradeable_quantity, and quote_currency; CostStack bricks and the sizing pipeline are
written against this interface, not against any concrete instrument type.

There is no per-instrument margin requirement. `risk.gross_exposure` sizes buying-power
risk off `notional()`, and the portfolio-level margin base in `engine/backtest.py` is
computed from gross exposure and NAV, never from an instrument's own margin schedule.
A buying-power lock (rejecting orders that breach a hard leverage limit) is not
implemented; adding one would mean adding a margin member here alongside the
`RiskLimits` rule that reads it.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Instrument(Protocol):
    @property
    def quote_currency(self) -> str:
        """Read-only by declaration: every concrete instrument is a frozen
        dataclass, and a settable protocol attribute would mark them all
        non-conforming."""
        ...

    def notional(self, quantity: float, price: float) -> float:
        """Market value of `quantity` units at `price`, in quote_currency."""
        ...

    def carry_components(self) -> tuple[str, ...]:
        """Names of the carry cost types applicable to this instrument (e.g.
        "borrow", "dividend", "funding"). An empty tuple is a legitimate answer —
        "none apply" — not a missing implementation.

        A name here only does something if some brick declares it as its `component`:
        the filter is `costs/stack.py:_applies`, reached from `carry_cost` and
        `event_flow` only. Margin interest is not a valid name here: it is a
        portfolio-level brick charged through `portfolio_carry_cost`, which has no
        instrument and therefore applies no filter. Keep this list to components that
        some brick actually matches."""
        ...

    def tradeable_quantity(self, raw_quantity: float) -> float:
        """Round a raw desired quantity to whatever unit is actually tradeable (whole
        shares, fractional shares, whole option contracts, ...)."""
        ...

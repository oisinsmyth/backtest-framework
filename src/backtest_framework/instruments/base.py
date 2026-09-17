"""Instrument abstraction (D12).

Positions and fills reference instrument objects, not ticker strings — making the
"everything is a share of stock" assumption explicit and swappable is what enables
multi-asset support. Every instrument class supplies notional, carry_components,
tradeable_quantity, and quote_currency; CostStack bricks (D1, D2) and the sizing
pipeline (D27) are written against this interface, not against any concrete instrument
type.

`margin_requirement` was a fifth member of this Protocol (D12, D54) and was DELETED
under D48, which forbids affordances for behaviour that does not exist. It had zero
call sites in src/: `risk.gross_exposure` sizes buying-power risk off `notional()`, and
the portfolio-level margin base in `engine/backtest.py` is computed from gross exposure
and NAV, never from an instrument's own margin schedule. What remained was a member
every new instrument was obliged to write and nothing would ever read — and
`Equity.margin_requirement` answered it with full notional, which is not a Reg T margin
requirement (50%) and was wrong by a factor of two with no test able to notice. D48's
rule is "removed or implemented"; this is the removal.

The FEATURE is still deferred, on D107 §1's terms and unchanged by this: a buying-power
lock needs a rejection policy that no validated strategy exists to inform, and the
trigger to build it is the first study whose conclusion depends on a hard leverage
constraint. That study adds the member back, next to the `RiskLimits` rule that reads
it. D107 §3 declines to build the idle FXConversionCost brick on this same D48 ground;
this is the same argument applied to the member D107 §1 left standing.
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

    def carry_components(self) -> tuple[str, ...]:
        """Names of the carry cost types applicable to this instrument (e.g.
        "borrow", "dividend", "funding"). An empty tuple is a legitimate answer —
        "none apply" — not a missing implementation.

        A name here only does something if some brick DECLARES it as its `component`:
        the filter is `costs/stack.py:_applies`, reached from `carry_cost` and
        `event_flow` only. "margin_interest" was listed here as an example and on
        `Equity` as a value, and matched nothing in either place — margin interest is a
        PORTFOLIO-level brick (D5, D67) charged through `portfolio_carry_cost`, which
        has no instrument and therefore applies no filter. Names that no filter can
        reach are D48 false affordances; keep this list to components that are actually
        matched."""
        ...

    def tradeable_quantity(self, raw_quantity: float) -> float:
        """Round a raw desired quantity to whatever unit is actually tradeable (whole
        shares, fractional shares, whole option contracts, ...)."""
        ...

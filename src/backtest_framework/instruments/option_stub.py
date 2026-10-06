"""Option instrument stub.

A well-formed stub, not a working options module: real dataclass fields and correct
contract-multiplier arithmetic, but margin, pricing, Greeks and assignment are out of
scope.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OptionStub:
    underlying_symbol: str
    strike: float
    expiry: str  # ISO date string; no calendar/settlement logic here yet
    option_type: str  # "call" or "put"
    multiplier: int = 100
    quote_currency: str = "USD"

    def notional(self, quantity: float, price: float) -> float:
        """`price` is the option premium per share; contract notional includes the
        multiplier (100 shares/contract for standard US equity options)."""
        return quantity * price * self.multiplier

    def tradeable_quantity(self, raw_quantity: float) -> float:
        return float(round(raw_quantity))  # whole contracts only

    def carry_components(self) -> tuple[str, ...]:
        # Theta decay is priced into the option's mark, not a carry cost brick in this
        # framework's model — correctly empty, not an unimplemented placeholder.
        return ()

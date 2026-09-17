"""Option instrument stub (D16, D48).

A well-formed stub, not a working options module: real dataclass fields and correct
contract-multiplier arithmetic, but margin (and everything else genuinely hard —
pricing, Greeks, assignment) is out of scope until the options wing gets built. See
docs/options_extension.md.

`margin_requirement` used to live here as a loud NotImplementedError. It went with the
Protocol member it implemented (see instruments/base.py, D48): once nothing in src/
declares or calls the method, a class-level raise is an affordance for a call that
cannot be made, not a guard against a fabricated number. The scoping claim it carried
is unchanged and still lives in docs/options_extension.md — option margin is the
hardest item in the options wing and is not attempted here.
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

"""Option instrument stub (D16, D48).

A well-formed stub, not a working options module: real dataclass fields and correct
contract-multiplier arithmetic, but margin (and everything else genuinely hard —
pricing, Greeks, assignment) is out of scope until the options wing gets built. See
docs/options_extension.md. This raises NotImplementedError rather than returning a
fabricated number (D48) — a wrong margin figure is worse than an honest crash.
"""

from __future__ import annotations

from dataclasses import dataclass

_OPTIONS_DOC = "docs/options_extension.md"


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

    def margin_requirement(self, quantity: float, price: float) -> float:
        raise NotImplementedError(
            f"OptionStub.margin_requirement is not implemented — see {_OPTIONS_DOC} (D16)."
        )

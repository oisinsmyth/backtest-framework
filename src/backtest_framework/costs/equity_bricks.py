"""Real equity cost bricks (Step 5: D3, D4, D5).

These replace the *economics* of Step 3's toy bricks (costs/bricks.py) against the
same TradeCostBrick/CarryCostBrick interfaces. The toys stay — they're honest simple
bricks the frozen D53 golden baseline uses — but everything from here on that claims
to model real trading friction should reach for these.

- IBKRCommission (D4): the actual IBKR Fixed US-equity schedule, not flat bps.
- SqrtImpact (D3): the industry-standard square-root market impact law. See D66 for
  the functional form — the *impact fraction* scales as √Q; total dollars as Q^1.5.
- MarginInterest (D5): accrues on max(gross exposure − capital, 0) — a PORTFOLIO-level
  base amount the engine computes (CostStack.portfolio_carry_bricks slot, D67), not a
  per-leg one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping

from ..instruments.base import Instrument
from ..simulator.carry import DEFAULT_DAY_COUNT, accrue_carry_between_bars


@dataclass(frozen=True)
class IBKRCommission:
    """IBKR Fixed pricing, US stocks/ETFs: $0.005/share, min $1.00/order, max 1% of
    trade value. The cap overrides the minimum — a 10-share order at $0.50 pays
    $0.05, not $1.00 (D65).

    Not modeled (deferred, D65): regulatory pass-throughs (SEC/FINRA fees on sells)
    and the Tiered schedule. Constants are dataclass fields so a schedule revision is
    a config change, not a code change.
    """

    per_share: float = 0.005
    min_per_order: float = 1.00
    max_pct_of_trade_value: float = 0.01

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        shares = abs(quantity)
        if shares == 0:
            return 0.0
        base = max(self.per_share * shares, self.min_per_order)
        cap = self.max_pct_of_trade_value * shares * price
        return min(base, cap)


@dataclass(frozen=True)
class ImpactParams:
    sigma_daily: float
    """Daily return volatility as a fraction (e.g. 0.015 for 1.5%/day)."""
    adv_shares: float
    """Average daily volume, in shares."""


@dataclass(frozen=True)
class SqrtImpact:
    """Square-root market impact (D3): impact_fraction = coefficient × σ_daily ×
    √(|Q|/ADV), charged on the trade's own notional, so total dollars scale as Q^1.5
    while the per-dollar impact fraction scales as √Q (D66).

    σ and ADV are static per-symbol parameters for now — estimating them from the
    data layer is Step 7's job once snapshots exist (D66). Validation is loud and
    early: bad params fail at construction, an unknown symbol fails at cost() time,
    and neither ever returns a silent zero (D48).
    """

    params_by_symbol: Mapping[str, ImpactParams] = field(default_factory=dict)
    coefficient: float = 1.0
    """Order-of-magnitude Y ≈ 1 convention from the empirical literature."""

    def __post_init__(self) -> None:
        for symbol, params in self.params_by_symbol.items():
            if params.adv_shares <= 0:
                raise ValueError(
                    f"SqrtImpact params for {symbol!r} have adv_shares={params.adv_shares} — "
                    "ADV must be positive; a zero/missing ADV must be a loud error, not a "
                    "silent zero cost (D48)"
                )
            if params.sigma_daily <= 0:
                raise ValueError(
                    f"SqrtImpact params for {symbol!r} have sigma_daily={params.sigma_daily} — "
                    "volatility must be positive; zero would silently zero the whole brick (D48)"
                )

    def _params_for(self, instrument: Instrument) -> ImpactParams:
        symbol = getattr(instrument, "symbol", None)
        if symbol is None:
            raise ValueError(
                f"SqrtImpact needs a 'symbol' attribute to look up impact params, but "
                f"{type(instrument).__name__} has none"
            )
        params = self.params_by_symbol.get(symbol)
        if params is None:
            known = ", ".join(sorted(self.params_by_symbol)) or "(none)"
            raise ValueError(
                f"SqrtImpact has no impact params for symbol {symbol!r} — known symbols: {known}. "
                "Missing ADV must be a loud error, not a silent zero cost (D48)."
            )
        return params

    def impact_fraction(self, instrument: Instrument, quantity: float) -> float:
        """The fractional price concession — the quantity that scales as √Q."""
        params = self._params_for(instrument)
        return self.coefficient * params.sigma_daily * math.sqrt(abs(quantity) / params.adv_shares)

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        if quantity == 0:
            return 0.0
        notional = abs(instrument.notional(quantity, price))
        return self.impact_fraction(instrument, quantity) * notional


@dataclass(frozen=True)
class MarginInterest:
    """Margin interest (D5): the caller's base_amount must be
    max(gross exposure − capital, 0) — the borrowed portion of the book. That's a
    portfolio-level quantity only the engine can compute, which is why this brick
    belongs in CostStack.portfolio_carry_bricks (D67), never in the per-leg slot.
    The accrual math itself is the shared calendar-day mechanism (D33, D51)."""

    annual_rate: float
    day_count: float = DEFAULT_DAY_COUNT

    def cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        return accrue_carry_between_bars(
            self.annual_rate, base_amount, prev_timestamp, curr_timestamp, day_count=self.day_count
        )

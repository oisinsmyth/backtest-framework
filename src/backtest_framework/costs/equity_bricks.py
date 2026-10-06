"""Equity cost bricks that model real trading friction.

They implement the same TradeCostBrick/CarryCostBrick interfaces as the simple bricks in
costs/bricks.py, which the golden baseline tests still use.

- IBKRCommission: the IBKR Fixed US-equity schedule.
- SqrtImpact: the square-root market impact law. The impact fraction scales as √Q; total
  dollars as Q^1.5.
- MarginInterest: accrues on max(gross exposure − capital, 0), a portfolio-level base the
  engine computes (CostStack.portfolio_carry_bricks slot).
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Mapping

from ..instruments.base import Instrument
from ..simulator.carry import DEFAULT_DAY_COUNT, accrue_carry_between_bars


@dataclass(frozen=True)
class IBKRCommission:
    """IBKR Fixed pricing for US stocks/ETFs: $0.005/share, min $1.00/order, max 1% of
    trade value.

    The cap overrides the minimum: a 10-share order at $0.50 pays $0.05, not $1.00. Not
    modeled: regulatory pass-throughs (SEC/FINRA fees on sells) and the Tiered schedule.
    The rates are dataclass fields, so a schedule revision is a config change.
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
    """Square-root market impact: impact_fraction = coefficient × σ_daily × √(|Q|/ADV).

    Charged on the trade's own notional, so total dollars scale as Q^1.5 while the impact
    fraction scales as √Q. σ and ADV are static per-symbol parameters, estimated from bar
    data by costs/calibration.py. Non-positive params raise at construction; an unknown
    symbol raises at cost() time.
    """

    params_by_symbol: Mapping[str, ImpactParams] = field(default_factory=dict)
    coefficient: float = 1.0
    """The order-of-magnitude Y ≈ 1 convention from the empirical literature."""

    def __post_init__(self) -> None:
        for symbol, params in self.params_by_symbol.items():
            if params.adv_shares <= 0:
                raise ValueError(
                    f"SqrtImpact params for {symbol!r} have adv_shares={params.adv_shares}; "
                    "ADV must be positive"
                )
            if params.sigma_daily <= 0:
                raise ValueError(
                    f"SqrtImpact params for {symbol!r} have sigma_daily={params.sigma_daily}; "
                    "volatility must be positive"
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
                f"SqrtImpact has no impact params for symbol {symbol!r}; known symbols: {known}."
            )
        return params

    def impact_fraction(self, instrument: Instrument, quantity: float) -> float:
        """Fractional price concession, scaling as √Q."""
        params = self._params_for(instrument)
        return self.coefficient * params.sigma_daily * math.sqrt(abs(quantity) / params.adv_shares)

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        if quantity == 0:
            return 0.0
        notional = abs(instrument.notional(quantity, price))
        return self.impact_fraction(instrument, quantity) * notional


@dataclass(frozen=True)
class DividendFlow:
    """Dividend cash flows on the ex-date at raw per-share amounts: longs credited, shorts
    debited.

    Dividends are modelled as explicit cash rather than price adjustments. The sign comes
    from the signed quantity: +500 shares × $0.87 credits $435; −500 shares debits it (a
    short owes the dividend to the lender). For a pairs book short a ~3% yielder such as
    XLE, this flow is first-order."""

    dividends_by_symbol: Mapping[str, tuple[tuple[datetime, float], ...]]
    """Per symbol: (ex-date, dividend per share), raw amounts."""

    component: ClassVar[str] = "dividend"
    """Carry component this brick models; applied only to instruments whose
    carry_components() includes it."""

    def flow(
        self, instrument: Instrument, quantity: float, prev_timestamp: datetime, curr_timestamp: datetime
    ) -> float:
        symbol = getattr(instrument, "symbol", None)
        if symbol is None:
            raise ValueError(
                f"DividendFlow needs a 'symbol' attribute to look up dividends, but "
                f"{type(instrument).__name__} has none"
            )
        total = 0.0
        for ex_date, amount in self.dividends_by_symbol.get(symbol, ()):
            if prev_timestamp < ex_date <= curr_timestamp:
                total += quantity * amount
        return total


@dataclass(frozen=True)
class BorrowFee:
    """Stock borrow fee, a per-leg carry brick: shorts pay, longs pay nothing.

    The engine passes each leg's signed notional as base_amount, so max(−base, 0) is the
    short exposure: a −100,000 short leg pays on 100,000; a long leg pays zero. The default
    rate is roughly general collateral for liquid ETFs (~0.25%/yr); hard-to-borrow rates
    are a config change."""

    annual_rate: float = 0.0025
    day_count: float = DEFAULT_DAY_COUNT

    component: ClassVar[str] = "borrow"
    """Carry component this brick models; applied only to instruments whose
    carry_components() includes it."""

    def cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        short_notional = max(-base_amount, 0.0)
        return accrue_carry_between_bars(
            self.annual_rate, short_notional, prev_timestamp, curr_timestamp, day_count=self.day_count
        )


@dataclass(frozen=True)
class MarginInterest:
    """Margin interest on the borrowed portion of the book.

    base_amount must be max(gross exposure − capital, 0), a portfolio-level quantity the
    engine computes, so this brick belongs in CostStack.portfolio_carry_bricks, not the
    per-leg slot. Accrual uses the shared calendar-day rule (ACT/365 by default)."""

    annual_rate: float
    day_count: float = DEFAULT_DAY_COUNT

    def cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        return accrue_carry_between_bars(
            self.annual_rate, base_amount, prev_timestamp, curr_timestamp, day_count=self.day_count
        )

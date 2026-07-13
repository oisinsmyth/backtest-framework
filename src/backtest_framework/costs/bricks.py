"""Cost bricks (D1, D2).

Two independent interfaces, matching two mechanically different things: TradeCostBrick
is charged once per fill (spread, impact, commission, FX conversion); CarryCostBrick is
charged per bar on open positions (margin interest, borrow, dividends, funding).

The concrete bricks below (FlatCommission, PercentOfNotionalSpread, FlatRateCarry) are
toy implementations that prove the CostStack composes and sums correctly. They are not
D3/D4/D5's real sqrt-impact / IBKR-schedule / margin-interest bricks — those are Step 5's
job and are expected to replace these. FlatRateCarry itself is the direct migration of
Step 2's CarryModel demonstration class, which always said it would end up here once
Step 3 existed (see config/carry_model.py).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from ..instruments.base import Instrument
from ..simulator.carry import DEFAULT_DAY_COUNT, accrue_carry_between_bars


class TradeCostBrick(Protocol):
    def cost(self, instrument: Instrument, quantity: float, price: float) -> float: ...


class CarryCostBrick(Protocol):
    def cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float: ...


@dataclass(frozen=True)
class FlatCommission:
    """A fixed fee per trade, regardless of size."""

    amount: float

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        return self.amount


@dataclass(frozen=True)
class PercentOfNotionalSpread:
    """A cost proportional to trade notional — a crude stand-in for D3's sqrt-impact
    brick and bid/ask spread, kept deliberately simple for Step 3's purposes."""

    bps: float

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        notional = instrument.notional(quantity, price)
        return abs(notional) * self.bps / 10_000


@dataclass(frozen=True)
class FlatRateCarry:
    """A single annualised rate applied to base_amount over the calendar-day gap
    between bars (D33). `base_amount` is whatever the caller has already determined is
    the carry-bearing quantity — this brick only knows the accrual math."""

    annual_rate: float
    day_count: float = DEFAULT_DAY_COUNT

    def cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        return accrue_carry_between_bars(
            self.annual_rate, base_amount, prev_timestamp, curr_timestamp, day_count=self.day_count
        )

"""Cost bricks.

Two independent interfaces, matching two mechanically different things: TradeCostBrick
is charged once per fill (spread, impact, commission, FX conversion); CarryCostBrick is
charged per bar on open positions (margin interest, borrow, dividends, funding).

The concrete bricks below (FlatCommission, PercentOfNotionalSpread, FlatRateCarry) are
simple implementations that exercise CostStack composition and summation. The realistic
equity bricks (square-root impact, IBKR commission schedule, margin interest) live in
costs/equity_bricks.py. FlatRateCarry is the brick that config/carry_model.py builds.
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


class EventFlowBrick(Protocol):
    """Event-driven cash flows: dividends today, other distributions later.

    Unlike carry (time-accrued, always a cost), an event flow is signed cash to the
    portfolio on specific dates: a dividend credits a long and debits a short. flow()
    returns the total for ex-dates in (prev_timestamp, curr_timestamp], given the
    signed quantity held across that gap. Not scaled by the cost-multiplier sweep, since
    flows are economic transfers rather than frictions."""

    def flow(
        self, instrument: Instrument, quantity: float, prev_timestamp: datetime, curr_timestamp: datetime
    ) -> float: ...


@dataclass(frozen=True)
class FlatCommission:
    """A fixed fee per trade, regardless of size."""

    amount: float

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        return self.amount


@dataclass(frozen=True)
class PercentOfNotionalSpread:
    """A cost proportional to trade notional: a simple stand-in for square-root
    impact and the bid/ask spread."""

    bps: float

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        notional = instrument.notional(quantity, price)
        return abs(notional) * self.bps / 10_000


@dataclass(frozen=True)
class FlatRateCarry:
    """A single annualised rate applied to base_amount over the calendar-day gap
    between bars. `base_amount` is whatever the caller has already determined is
    the carry-bearing quantity — this brick only knows the accrual math."""

    annual_rate: float
    day_count: float = DEFAULT_DAY_COUNT

    def cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        return accrue_carry_between_bars(
            self.annual_rate, base_amount, prev_timestamp, curr_timestamp, day_count=self.day_count
        )

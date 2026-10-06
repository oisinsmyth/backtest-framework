"""Cost brick interfaces and simple implementations.

TradeCostBrick is charged once per fill (spread, impact, commission, FX conversion);
CarryCostBrick is charged per bar on open positions (margin interest, borrow, dividends,
funding).

FlatCommission, PercentOfNotionalSpread and FlatRateCarry are simple bricks that exercise
CostStack composition. The realistic equity bricks are in costs/equity_bricks.py.
config/carry_model.py builds FlatRateCarry.
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
    """Event-driven cash flows, such as dividends.

    Unlike carry (time-accrued, always a cost), an event flow is signed cash on specific
    dates: a dividend credits a long and debits a short. flow() returns the total for
    ex-dates in (prev_timestamp, curr_timestamp] given the signed quantity held over that
    interval. Flows are transfers, not frictions, so the cost-multiplier sweep does not
    scale them."""

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
    """A cost proportional to trade notional; a simple stand-in for impact and spread."""

    bps: float

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        notional = instrument.notional(quantity, price)
        return abs(notional) * self.bps / 10_000


@dataclass(frozen=True)
class FlatRateCarry:
    """A single annualised rate applied to `base_amount` over the calendar days between
    bars. The caller decides what `base_amount` is."""

    annual_rate: float
    day_count: float = DEFAULT_DAY_COUNT

    def cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        return accrue_carry_between_bars(
            self.annual_rate, base_amount, prev_timestamp, curr_timestamp, day_count=self.day_count
        )

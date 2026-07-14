"""CostStack (D1): an ordered list of composable cost bricks.

An empty stack behaves exactly like a zero-cost model — there's no separate
ZeroCostModel class, because "no bricks" already is one. Every brick is purely additive
(each computes its own cost independently, from instrument/quantity/price or from
base_amount/timestamps — never from another brick's output), so brick ordering has no
effect on the total. That's asserted, not just assumed, in tests/unit/test_cost_stack.py.

Carry has two slots with different base-amount semantics (D67): `carry_bricks` are
per-leg (the engine calls carry_cost once per held instrument, base = that leg's own
notional — borrow fees, dividends, funding), while `portfolio_carry_bricks` are charged
once per bar on a portfolio-level base the engine computes (margin interest on
max(gross exposure − capital, 0), D5). Same CarryCostBrick interface, different caller
contract — the slot, not the brick class, carries the semantics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..instruments.base import Instrument
from .bricks import CarryCostBrick, TradeCostBrick


@dataclass(frozen=True)
class CostStack:
    trade_bricks: tuple[TradeCostBrick, ...] = ()
    carry_bricks: tuple[CarryCostBrick, ...] = ()
    portfolio_carry_bricks: tuple[CarryCostBrick, ...] = ()

    def trade_cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        return sum(brick.cost(instrument, quantity, price) for brick in self.trade_bricks)

    def carry_cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        return sum(
            brick.cost(base_amount, prev_timestamp, curr_timestamp) for brick in self.carry_bricks
        )

    def portfolio_carry_cost(
        self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime
    ) -> float:
        return sum(
            brick.cost(base_amount, prev_timestamp, curr_timestamp)
            for brick in self.portfolio_carry_bricks
        )

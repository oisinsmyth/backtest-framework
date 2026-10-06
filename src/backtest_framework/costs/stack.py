"""CostStack: an ordered list of composable cost bricks.

An empty stack is the zero-cost model. Each brick computes its cost independently, from
instrument/quantity/price or base_amount/timestamps and never from another brick's output,
so brick order does not affect the total (tests/unit/test_cost_stack.py asserts this).

Carry has two slots with different base amounts. `carry_bricks` are per-leg: the engine
calls carry_cost once per held instrument with that leg's notional (borrow fees,
dividends, funding). `portfolio_carry_bricks` are charged once per bar on a
portfolio-level base the engine computes (margin interest on
max(gross exposure − capital, 0)). Both use the CarryCostBrick interface; the slot
determines the base.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..instruments.base import Instrument
from .bricks import CarryCostBrick, EventFlowBrick, TradeCostBrick


@dataclass(frozen=True)
class CostStack:
    trade_bricks: tuple[TradeCostBrick, ...] = ()
    carry_bricks: tuple[CarryCostBrick, ...] = ()
    portfolio_carry_bricks: tuple[CarryCostBrick, ...] = ()
    event_flow_bricks: tuple[EventFlowBrick, ...] = ()
    """Event-driven signed cash flows (dividends: credit longs, debit shorts), applied
    per held leg. Not scaled by the cost-multiplier sweep (see costs/scaling.py)."""

    def trade_cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        return sum(brick.cost(instrument, quantity, price) for brick in self.trade_bricks)

    def carry_cost(
        self,
        base_amount: float,
        prev_timestamp: datetime,
        curr_timestamp: datetime,
        components: tuple[str, ...] | None = None,
    ) -> float:
        """Per-leg carry.

        When `components` is given (the engine passes the held instrument's
        `carry_components()`), bricks whose `component` is outside it are skipped, so an
        instrument without borrow is not charged borrow. Bricks with no `component`
        always apply."""
        return sum(
            brick.cost(base_amount, prev_timestamp, curr_timestamp)
            for brick in self.carry_bricks
            if _applies(brick, components)
        )

    def portfolio_carry_cost(
        self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime
    ) -> float:
        return sum(
            brick.cost(base_amount, prev_timestamp, curr_timestamp)
            for brick in self.portfolio_carry_bricks
        )

    def event_flow(
        self, instrument: Instrument, quantity: float, prev_timestamp: datetime, curr_timestamp: datetime
    ) -> float:
        components = instrument.carry_components()
        return sum(
            brick.flow(instrument, quantity, prev_timestamp, curr_timestamp)
            for brick in self.event_flow_bricks
            if _applies(brick, components)
        )


def _applies(brick: object, components: tuple[str, ...] | None) -> bool:
    """True if the brick's `component` is None or in `components`.

    `components=None` means no instrument context was given, so every brick applies."""
    component = getattr(brick, "component", None)
    return component is None or components is None or component in components

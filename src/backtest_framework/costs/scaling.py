"""Cost-stack scaling for the cost-multiplier sweep.

scaled_cost_stack(stack, m) returns a new CostStack in which every friction brick returns
m × the original brick's output. Each brick gets its own wrapper, so the scaled stack is
still additive and order-invariant, and a 0× stack charges zero frictions
(tests/integration/test_cost_sweep.py checks this through a full backtest).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..instruments.base import Instrument
from .bricks import CarryCostBrick, TradeCostBrick
from .stack import CostStack


@dataclass(frozen=True)
class _ScaledTradeBrick:
    inner: TradeCostBrick
    multiplier: float

    def cost(self, instrument: Instrument, quantity: float, price: float) -> float:
        return self.multiplier * self.inner.cost(instrument, quantity, price)


@dataclass(frozen=True)
class _ScaledCarryBrick:
    inner: CarryCostBrick
    multiplier: float

    @property
    def component(self) -> str | None:
        # Forward the inner brick's carry component so per-instrument filtering is
        # unchanged by scaling.
        return getattr(self.inner, "component", None)

    def cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        return self.multiplier * self.inner.cost(base_amount, prev_timestamp, curr_timestamp)


def scaled_cost_stack(stack: CostStack, multiplier: float) -> CostStack:
    """Scale the friction slots by `multiplier`.

    event_flow_bricks pass through unscaled, since a dividend is a transfer rather than a
    friction. A 0× stack therefore keeps its event flows and is not an empty CostStack."""
    if multiplier < 0:
        raise ValueError(f"cost multiplier must be non-negative, got {multiplier}")
    return CostStack(
        trade_bricks=tuple(_ScaledTradeBrick(brick, multiplier) for brick in stack.trade_bricks),
        carry_bricks=tuple(_ScaledCarryBrick(brick, multiplier) for brick in stack.carry_bricks),
        portfolio_carry_bricks=tuple(
            _ScaledCarryBrick(brick, multiplier) for brick in stack.portfolio_carry_bricks
        ),
        event_flow_bricks=stack.event_flow_bricks,
    )

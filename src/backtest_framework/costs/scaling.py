"""Cost-stack scaling for the cost-multiplier sweep.

scaled_cost_stack(stack, m) returns a new CostStack whose every friction brick produces
exactly m × the original brick's output. Structure is preserved (each brick gets its own
wrapper), so a scaled stack keeps the CostStack's additive, order-invariant guarantees,
and a 0× stack charges exactly zero frictions (tests/integration/test_cost_sweep.py checks
this through a full backtest).
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
        # Forward the inner brick's carry-component declaration so a scaled
        # stack filters per-instrument exactly like the unscaled one.
        return getattr(self.inner, "component", None)

    def cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        return self.multiplier * self.inner.cost(base_amount, prev_timestamp, curr_timestamp)


def scaled_cost_stack(stack: CostStack, multiplier: float) -> CostStack:
    """Scale the friction slots. event_flow_bricks pass through unscaled: a dividend
    is an economic transfer, not a friction, so a 4× sweep models trading at 4× the
    cost with unchanged dividends. A 0× sweep therefore equals a run whose stack has
    zero frictions but the same event flows, not an entirely empty CostStack."""
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

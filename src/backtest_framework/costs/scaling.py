"""Cost-stack scaling for the multiplier sweep (D8, D68).

scaled_cost_stack(stack, m) returns a new CostStack whose every brick — in all three
slots — produces exactly m × the original brick's output. Structure is preserved
(each brick gets its own wrapper), so a scaled stack still satisfies the additive/
order-invariant guarantees of D54, and 0× is provably equivalent to an empty
CostStack() rather than approximately so (the U-gate in VERIFICATION_SCHEME.md
Step 6 asserts this equivalence through a full backtest).
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

    def cost(self, base_amount: float, prev_timestamp: datetime, curr_timestamp: datetime) -> float:
        return self.multiplier * self.inner.cost(base_amount, prev_timestamp, curr_timestamp)


def scaled_cost_stack(stack: CostStack, multiplier: float) -> CostStack:
    """Scale the FRICTION slots. event_flow_bricks pass through unscaled (D75): a
    dividend is an economic transfer, not a friction — a 4× sweep asks "what if
    trading were 4× more expensive," not "what if XLE quadrupled its dividend."
    Consequence for the 0× gate: a 0× sweep equals a run whose stack has zero
    frictions but the SAME event flows, not an entirely empty CostStack."""
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

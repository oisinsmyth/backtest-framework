"""Allocator: a bare-bones capital-allocation stand-in behind a stable interface (D31).

Multi-strategy allocation (correlation, capacity, sleeve rebalancing) is a hard problem
with zero validated strategies to inform it yet — designing a clever interface now from
speculation would be wrong. ConstantSplitAllocator commits to nothing except a real,
swappable socket: it's the thing pipeline.sizing.Sizer's `capital_by_strategy` parameter
(D55) is meant to be sourced from, closing the loop Step 3 explicitly left open.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Allocator(Protocol):
    def allocate(self, total_capital: float, strategy_ids: list[str]) -> dict[str, float]: ...


@dataclass(frozen=True)
class ConstantSplitAllocator:
    """Splits total_capital evenly across every strategy_id given. Holds no state —
    capital changes propagate immediately on the next call, there's nothing to go
    stale."""

    def allocate(self, total_capital: float, strategy_ids: list[str]) -> dict[str, float]:
        if not strategy_ids:
            return {}
        share = total_capital / len(strategy_ids)
        return {strategy_id: share for strategy_id in strategy_ids}

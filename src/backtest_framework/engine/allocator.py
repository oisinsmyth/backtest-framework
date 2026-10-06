"""Allocator: a minimal capital-allocation component behind a stable interface.

Multi-strategy allocation (correlation, capacity, sleeve rebalancing) is left to
callers. ConstantSplitAllocator commits to nothing except a swappable interface: it is
what pipeline.sizing.Sizer's `capital_by_strategy` parameter is sourced from.
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

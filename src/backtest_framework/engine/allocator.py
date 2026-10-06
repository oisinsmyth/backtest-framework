"""Allocator: the interface that supplies capital per strategy.

The result feeds pipeline.sizing.Sizer's `capital_by_strategy`. Multi-strategy
allocation (correlation, capacity, sleeve rebalancing) is left to callers;
ConstantSplitAllocator is the minimal implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Allocator(Protocol):
    def allocate(self, total_capital: float, strategy_ids: list[str]) -> dict[str, float]: ...


@dataclass(frozen=True)
class ConstantSplitAllocator:
    """Splits total_capital evenly across the given strategy_ids.

    Stateless, so each call reflects the capital passed in."""

    def allocate(self, total_capital: float, strategy_ids: list[str]) -> dict[str, float]:
        if not strategy_ids:
            return {}
        share = total_capital / len(strategy_ids)
        return {strategy_id: share for strategy_id in strategy_ids}

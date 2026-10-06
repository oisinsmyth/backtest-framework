"""Signal -> target weight -> orders pipeline.

Strategies output target portfolio weights rather than order sizes, so sizing logic
is shared, signals can be compared independently of sizing, and orders can be netted
across strategies. One Sizer converts (target weight, current position, capital,
price) into a desired quantity for any strategy. Netting combines the strategies'
orders into the orders sent to the broker, while each strategy's virtual book updates
as if its own order filled in full.

`capital_by_strategy` is an input, supplied by an Allocator (engine.allocator).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..instruments.base import Instrument


@dataclass(frozen=True)
class TargetWeight:
    strategy_id: str
    instrument_id: str
    weight: float
    """Fraction of the strategy's allocated capital this instrument should represent."""

    stop: float | None = None
    """Price at which this position is closed intrabar if touched; None (default) for no stop.

    Re-declared with the target every bar, so a trailing stop just moves.

    Declared in the view frame and enforced against execution prices. The two match
    for instruments without splits (e.g. spot crypto); `run_backtest` raises ValueError
    for a stop on an instrument with splits."""


@dataclass(frozen=True)
class Order:
    instrument_id: str
    quantity: float
    """Signed: positive = buy, negative = sell."""


class Sizer:
    """Converts target weights into desired quantities.

    Holds no per-strategy state, so one instance serves every strategy."""

    def desired_quantity(
        self, target: TargetWeight, capital: float, price: float, instrument: Instrument
    ) -> float:
        desired_notional = target.weight * capital
        raw_quantity = desired_notional / price
        return instrument.tradeable_quantity(raw_quantity)

    def size_targets(
        self,
        targets: list[TargetWeight],
        current_positions: Mapping[tuple[str, str], float],
        capital_by_strategy: Mapping[str, float],
        prices: Mapping[str, float],
        instruments: Mapping[str, Instrument],
    ) -> dict[tuple[str, str], Order]:
        """Return per-(strategy, instrument) virtual orders, before netting.

        A position already at target produces no entry (rather than a zero-quantity
        order)."""
        virtual_orders: dict[tuple[str, str], Order] = {}
        for target in targets:
            key = (target.strategy_id, target.instrument_id)
            instrument = instruments[target.instrument_id]
            capital = capital_by_strategy[target.strategy_id]
            price = prices[target.instrument_id]
            current_qty = current_positions.get(key, 0.0)
            desired_qty = self.desired_quantity(target, capital, price, instrument)
            delta = desired_qty - current_qty
            if delta != 0:
                virtual_orders[key] = Order(target.instrument_id, delta)
        return virtual_orders


def net_orders(virtual_orders: Mapping[tuple[str, str], Order]) -> dict[str, Order]:
    """Sum the strategies' virtual orders per instrument into broker orders.

    Opposing orders cancel instead of paying trade costs twice; instruments that net
    to zero are omitted."""
    totals: dict[str, float] = {}
    for (_strategy_id, instrument_id), order in virtual_orders.items():
        totals[instrument_id] = totals.get(instrument_id, 0.0) + order.quantity
    return {
        instrument_id: Order(instrument_id, qty) for instrument_id, qty in totals.items() if qty != 0
    }


def apply_virtual_orders(
    current_positions: Mapping[tuple[str, str], float],
    virtual_orders: Mapping[tuple[str, str], Order],
) -> dict[tuple[str, str], float]:
    """Return the virtual books updated by each strategy's own order, ignoring netting."""
    updated = dict(current_positions)
    for key, order in virtual_orders.items():
        updated[key] = updated.get(key, 0.0) + order.quantity
    return updated

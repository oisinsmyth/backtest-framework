"""Signal -> target weight -> orders pipeline (D27).

Strategies output desired portfolio weights, not order sizes — welding alpha ("XLE rich
vs XOP") to implementation ("sell 43 shares") inside each strategy prevents reusing
sizing logic, prevents comparing signals independent of sizing, and prevents netting
orders across strategies. A single Sizer converts (target weight, current position,
capital, price) into a desired quantity for any strategy, unmodified; a netting step
combines every strategy's private order intent into the orders that actually reach the
broker, while each strategy's own virtual book (D46) updates as if its own order filled
in full, regardless of what happened during netting.

`capital_by_strategy` is an external input here, not something this module computes —
deciding how much capital each strategy gets is D31's Allocator's job (Step 4's
bare-bones stand-in), not Step 3's. The Sizer takes whatever capital figure it's handed.
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


@dataclass(frozen=True)
class Order:
    instrument_id: str
    quantity: float
    """Signed: positive = buy, negative = sell."""


class Sizer:
    """Converts target weights into desired quantities. Holds no per-strategy state —
    the same Sizer instance drives every strategy without modification."""

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
        """Per-(strategy, instrument) virtual orders — each strategy's private order
        intent, before netting. Already-at-target positions produce no entry at all
        (not a zero-quantity order), so "no churn" falls out of the data rather than
        needing to be filtered downstream."""
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
    """Combine every strategy's private order intent for the same instrument into the
    order that actually reaches the broker (D27) — strategy A buying what strategy B
    sells cancels internally instead of paying trade costs twice."""
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
    """Update each strategy's own virtual book (D46) by its own order, independent of
    whatever happened during netting at the broker-facing level."""
    updated = dict(current_positions)
    for key, order in virtual_orders.items():
        updated[key] = updated.get(key, 0.0) + order.quantity
    return updated

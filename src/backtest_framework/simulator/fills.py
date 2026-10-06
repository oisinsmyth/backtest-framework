"""Stop-order fill logic.

A stop the bar gaps through fills at the bar open; otherwise a touched stop fills at the
stop price. There is no rule here for a bar that touches two opposing exit orders (see
`futures_fills.resolve_exit` for that).
"""

from dataclasses import dataclass
from enum import Enum


class StopSide(Enum):
    """Which direction the stop triggers in, independent of the position it protects."""

    SELL_STOP = "sell_stop"
    """Triggers when price falls to/through the stop. The exit order for a long position."""

    BUY_STOP = "buy_stop"
    """Triggers when price rises to/through the stop. The exit order for a short position."""


@dataclass(frozen=True)
class Bar:
    open: float
    high: float
    low: float
    close: float


def stop_fill_price(side: StopSide, stop_price: float, bar: Bar) -> float | None:
    """Return the fill price for a stop order on `bar`, or None if it was not touched.

    A stop the bar gapped through fills at the bar's open, not the stop price, which
    would overstate P&L. This is not configurable.
    """
    if side is StopSide.SELL_STOP:
        if bar.open <= stop_price:
            return bar.open
        if bar.low <= stop_price:
            return stop_price
        return None

    if bar.open >= stop_price:
        return bar.open
    if bar.high >= stop_price:
        return stop_price
    return None

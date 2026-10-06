"""Stop-order fill logic.

A stop that the bar gaps through fills at the bar open, not the stop price; otherwise a
touched stop fills at the stop price. An adverse-fill-first convention for a bar that
touches two opposing exit orders is not needed for a single stop order and is not
implemented here.
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
    """Return the fill price for a stop order given the bar it's evaluated against.

    Filling at the stop price when the bar has gapped through it would overstate P&L and
    understate risk, so a gapped stop fills at the bar's open instead. This is not a
    configurable option.

    Returns None if the stop was not touched this bar.
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

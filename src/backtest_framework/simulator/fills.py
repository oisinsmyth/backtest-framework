"""Stop-order fill logic.

Implements D10 (gap-through-stop fills at the bar open, not the stop price) and the
no-gap branch of D42 (adverse-fill-first convention is not exercised by a single stop
order in isolation — it matters once a bar can touch two opposing exit orders, which is
out of scope for Step 1).
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

    D10: filling at the stop price when the bar has gapped through it is free money and
    fantasy risk numbers — a gapped stop fills at the bar's open instead. This is a bug
    fix, not a configurable sensitivity option.

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

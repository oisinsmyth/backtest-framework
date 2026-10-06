"""Calendar-day carry accrual.

Carry costs (margin interest, borrow fees, funding) accrue on the calendar time between
consecutive bar timestamps, not on bar count: a Friday-close to Monday-close hold is one
bar but three days of carry.

The day count defaults to ACT/365 for all brokers and currencies; bricks accept a
`day_count` override.
"""

from datetime import datetime

DEFAULT_DAY_COUNT = 365.0


def calendar_days_between(start: datetime, end: datetime) -> float:
    """Calendar-day gap between two timestamps, as a float (fractional for intraday bars)."""
    return (end - start).total_seconds() / 86400.0


def accrue_carry(
    annual_rate: float,
    base_amount: float,
    calendar_days: float,
    *,
    day_count: float = DEFAULT_DAY_COUNT,
) -> float:
    """Carry accrued on `base_amount` at `annual_rate` over `calendar_days` calendar days.

    The calling brick decides what `base_amount` is (e.g. gross exposure minus capital
    for margin interest, or short notional for a borrow fee).
    """
    return base_amount * annual_rate * calendar_days / day_count


def accrue_carry_between_bars(
    annual_rate: float,
    base_amount: float,
    prev_timestamp: datetime,
    curr_timestamp: datetime,
    *,
    day_count: float = DEFAULT_DAY_COUNT,
) -> float:
    """Accrue carry over the calendar time between two bar timestamps."""
    days = calendar_days_between(prev_timestamp, curr_timestamp)
    return accrue_carry(annual_rate, base_amount, days, day_count=day_count)

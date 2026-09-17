"""Engine-wiring half of the Step 5 margin interest G-gate (D5, D67): a 200%-gross
pairs position held over a weekend gets charged margin interest computed by
run_backtest itself, from a start-of-bar snapshot.

Hand arithmetic (including why the NAV assertion isolates the charge exactly) lives in
tests/golden/test_margin_interest.hand.txt under "Integration scenario".
"""

from datetime import datetime

import pytest

from backtest_framework.costs.equity_bricks import MarginInterest
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar

TOLERANCE = 1e-6  # D47


def _bar(price: float) -> Bar:
    return Bar(open=price, high=price, low=price, close=price)


BARS_BY_INSTRUMENT = {
    "A": [
        TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(100.0)),  # Friday
        TimestampedBar(datetime(2026, 7, 13, 16, 0), _bar(100.0)),  # Monday, +3 days
    ],
    "B": [
        TimestampedBar(datetime(2026, 7, 10, 16, 0), _bar(50.0)),
        TimestampedBar(datetime(2026, 7, 13, 16, 0), _bar(50.0)),
    ],
}
INSTRUMENTS = {"A": Equity(symbol="A"), "B": Equity(symbol="B")}
STRATEGY = ScheduledWeightStrategy(
    strategy_id="pairs", weights_by_instrument={"A": [1.0, 1.0], "B": [-1.0, -1.0]}
)


def _run(cost_stack: CostStack):
    return run_backtest(
        bars_by_instrument=BARS_BY_INSTRUMENT,
        instruments=INSTRUMENTS,
        strategies=[STRATEGY],
        cost_stack=cost_stack,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )


def test_margin_interest_charged_on_borrowed_portion_over_the_weekend():
    result = _run(CostStack(portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),)))

    navs = [nav for _, nav in result.equity_curve]
    assert navs[0] == pytest.approx(100_000.0, rel=TOLERANCE)  # no gap yet, no charge
    # Snapshot at Monday's open-of-bar: gross 200,000, NAV 100,000 -> base 100,000;
    # 3 calendar days at 6% -> the D33 golden number.
    assert navs[1] == pytest.approx(100_000.0 - 49.315068493150684, rel=TOLERANCE)


def test_control_run_without_portfolio_bricks_is_uncharged():
    result = _run(CostStack())

    navs = [nav for _, nav in result.equity_curve]
    assert navs[0] == pytest.approx(100_000.0, rel=TOLERANCE)
    assert navs[1] == pytest.approx(100_000.0, rel=TOLERANCE)


def test_per_leg_carry_uses_the_instruments_notional_not_quantity_times_price():
    """The carry base must come from `notional()`, like every other money in the engine.

    `run_backtest` open-coded `quantity * price` for the per-leg carry base while
    `portfolio.nav` and `gross_exposure` — the lines immediately either side of it — both
    asked the instrument. For `Equity` those agree exactly, which is why it never showed:
    `Equity.notional` IS `quantity * price`. For an instrument with a contract multiplier
    they differ by that multiplier, and nothing in the engine compares the two, so the book
    would have been charged carry on a hundredth of the exposure its own NAV reported.

    This test is the only thing in the suite that distinguishes the two, because no shipped
    instrument has a multiplier. It uses a x10 stub so the difference is arithmetic rather
    than rounding: the charge must scale with the multiplier.
    """
    from dataclasses import dataclass

    from backtest_framework.costs.equity_bricks import BorrowFee

    @dataclass(frozen=True)
    class TenXContract:
        symbol: str
        multiplier: int = 10

        @property
        def quote_currency(self) -> str:
            return "USD"

        def notional(self, quantity: float, price: float) -> float:
            return quantity * price * self.multiplier

        def carry_components(self) -> tuple[str, ...]:
            # The same pair Equity declares (D48). Returning () would make the comparison
            # vacuous: no carry brick would match, both books would be charged nothing, and
            # the ratio assertion would compare 0 with 0.
            return ("borrow", "dividend")

        def tradeable_quantity(self, raw_quantity: float) -> float:
            return raw_quantity

    def run_with(instruments):
        return run_backtest(
            bars_by_instrument=BARS_BY_INSTRUMENT,
            instruments=instruments,
            strategies=[STRATEGY],
            cost_stack=CostStack(carry_bricks=(BorrowFee(annual_rate=0.02),)),
            allocator=ConstantSplitAllocator(),
            starting_cash=100_000.0,
        )

    plain = run_with({"A": Equity(symbol="A"), "B": Equity(symbol="B")})
    tenx = run_with({"A": TenXContract(symbol="A"), "B": TenXContract(symbol="B")})

    charged_plain = 100_000.0 - plain.equity_curve[1][1]
    charged_tenx = 100_000.0 - tenx.equity_curve[1][1]

    assert charged_plain > 0, "the borrow fee must actually bite, or this proves nothing"
    assert charged_tenx == pytest.approx(10.0 * charged_plain, rel=TOLERANCE), (
        f"carry base ignored the contract multiplier: {charged_tenx} charged against "
        f"{charged_plain} on a x10 instrument — the base is not coming from notional()"
    )

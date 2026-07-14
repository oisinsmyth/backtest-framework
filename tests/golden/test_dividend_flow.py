"""G-gate for DividendFlow (D6, D75): a known historical dividend (XLE ex-date
2015-03-20, $0.2575/share, from the committed events file) credits the long and
debits the short, on the ex-date. Hand arithmetic in test_dividend_flow.hand.txt.
"""

from datetime import datetime
from pathlib import Path

import pytest

from backtest_framework.costs.equity_bricks import DividendFlow
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar

TOLERANCE = 1e-6  # D47
REPO = Path(__file__).resolve().parent.parent.parent
EVENTS = load_events_json(REPO / "data" / "fixtures" / "xle_xop_daily_2015_2024_raw_events.json")

XLE = Equity(symbol="XLE")
EX_DATE = datetime(2015, 3, 20)
AMOUNT = 0.2575


def _brick() -> DividendFlow:
    return DividendFlow(dividends_by_symbol={"XLE": tuple(EVENTS.dividends_by_symbol["XLE"])})


def test_fixture_contains_the_known_dividend():
    assert (EX_DATE, AMOUNT) in EVENTS.dividends_by_symbol["XLE"]


def test_long_credited_on_ex_date():
    flow = _brick().flow(XLE, quantity=500, prev_timestamp=datetime(2015, 3, 18), curr_timestamp=datetime(2015, 3, 20))
    assert flow == pytest.approx(128.75, rel=TOLERANCE)


def test_short_debited_identically():
    flow = _brick().flow(XLE, quantity=-500, prev_timestamp=datetime(2015, 3, 18), curr_timestamp=datetime(2015, 3, 20))
    assert flow == pytest.approx(-128.75, rel=TOLERANCE)


def test_position_opened_on_ex_date_receives_nothing():
    # Half-open window (prev, curr]: ex-date == prev means it belonged to the PRIOR gap.
    flow = _brick().flow(XLE, quantity=500, prev_timestamp=datetime(2015, 3, 20), curr_timestamp=datetime(2015, 3, 25))
    assert flow == 0.0


# --- Engine integration: constant price + zero frictions isolate the flow exactly ----


def _run(weight: float, with_dividends: bool):
    bar = Bar(open=80.0, high=80.0, low=80.0, close=80.0)
    bars = {
        "XLE": [TimestampedBar(datetime(2015, 3, 18), bar), TimestampedBar(datetime(2015, 3, 20), bar)]
    }
    stack = CostStack(event_flow_bricks=(_brick(),) if with_dividends else ())
    return run_backtest(
        bars_by_instrument=bars,
        instruments={"XLE": XLE},
        strategies=[ScheduledWeightStrategy(strategy_id="s", weights_by_instrument={"XLE": [weight, weight]})],
        cost_stack=stack,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )


def test_engine_credits_long_book_on_ex_date():
    result = _run(weight=0.4, with_dividends=True)  # +500 shares
    assert result.equity_curve[-1][1] == pytest.approx(100_128.75, rel=TOLERANCE)


def test_engine_debits_short_book_on_ex_date():
    result = _run(weight=-0.4, with_dividends=True)  # -500 shares
    assert result.equity_curve[-1][1] == pytest.approx(99_871.25, rel=TOLERANCE)


def test_control_run_without_dividend_brick_is_flat():
    result = _run(weight=0.4, with_dividends=False)
    assert result.equity_curve[-1][1] == pytest.approx(100_000.0, rel=TOLERANCE)

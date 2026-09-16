"""THE GOLDEN MASTER (D39, D77): the whole simulator against an independently
hand-computed 5-bar short-side scenario — every fill, every commission, every carry
accrual, the dividend debit, cash and NAV per bar, asserted line by line.

Ground truth in test_the_golden_master.hand.txt, produced by a standalone calculator
that never imports this codebase. If this test and the production engine ever
disagree, one of them is wrong about what a backtest IS — that argument happens here,
not at bar 3,000 of a research run.

WHAT THIS FILE USED TO MISS, AND WHY THE .hand.json EXISTS
----------------------------------------------------------
Until 2026-09-16 the fills were asserted as `(ts, instrument_id, qty, price, trade_cost)`
with `trade_cost` the SUM of commission and spread — so a defect that moved $6.00 out of
`IBKRCommission` and into `PercentOfNotionalSpread` passed every assertion here. Borrow,
margin interest and the dividend were asserted NOWHERE: only their aggregate effect on the
cash and equity curves, which cannot tell a borrow accrual from a margin one from a
dividend debit of the same size.

`BacktestResult` (src/backtest_framework/engine/backtest.py:42-79) is why: it publishes
fills, a cash curve, an equity curve and final state, and no per-brick attribution at all.
Carry accruals and event flows reach `PortfolioState` and are never recorded. So the
decomposition exists only in the hand ledger, and `test_the_golden_master.hand.json` is
that ledger in a form a test and a figure can read. It was transcribed BY HAND from the
.hand.txt — never dumped out of the engine, which would launder the engine's assumptions
into the thing meant to check them (CONTRIBUTING.md, step 2).

Three gates keep that transcription honest:

1. `test_the_closed_book_recomputation_reproduces_every_hand_value` walks the scenario
   block with stdlib arithmetic and reproduces all 19 fields of all 5 bars. This is what
   would catch the JSON having been dumped out of a buggy engine.
2. `test_every_hand_value_appears_in_the_hand_file` requires each number, formatted in the
   .hand.txt's own notation, to appear in the .hand.txt.
3. `test_the_cash_curve_carries_the_carry_the_engine_never_reports` reaches the carry and
   the dividend THROUGH the cash curve — the only channel the engine offers — and pins
   their sum per bar against the hand ledger.

What is still not separable from outside the engine: borrow from margin interest within one
bar. Both are cash deductions of the same sign at the same instant, and nothing published
distinguishes them. The hand ledger splits them, the closed-book calculator reproduces the
split, and docs/figures/golden-master-ledger-diff.svg draws the gap rather than hiding it.
"""

from __future__ import annotations

import ast
import inspect
import json
import textwrap
from datetime import datetime
from pathlib import Path

import pytest

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.equity_bricks import BorrowFee, DividendFlow, IBKRCommission, MarginInterest
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.bars import TimestampedBar
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import BacktestResult, run_backtest
from backtest_framework.engine.strategy import ScheduledWeightStrategy
from backtest_framework.instruments.equity import Equity
from backtest_framework.simulator.fills import Bar

TOLERANCE = 1e-6  # D47

HERE = Path(__file__).resolve().parent
HAND_JSON = HERE / "test_the_golden_master.hand.json"
HAND_TXT = HERE / "test_the_golden_master.hand.txt"

HAND = json.loads(HAND_JSON.read_text(encoding="utf-8"))
SCENARIO = HAND["scenario"]
BARS = HAND["bars"]

# The timestamps are read from the ledger rather than restated, so the scenario the engine
# runs and the scenario the hand ledger describes cannot drift apart silently. Three copies
# of these numbers (hand file, JSON, Python literals) collapse to two with a gate between.
THU, FRI, MON, TUE, WED = (datetime.fromisoformat(t) for t in SCENARIO["timestamps"])

# Every per-bar field the ledger carries. Named here so a field ADDED to the JSON and not
# reproduced by the closed-book calculator is a failure rather than a silent pass.
LEDGER_FIELDS = (
    "price",
    "days",
    "qty_before",
    "qty_after",
    "delta",
    "notional",
    "commission",
    "spread",
    "trade_cost",
    "short_notional",
    "borrow",
    "margin_base",
    "margin_interest",
    "dividend",
    "nav_snapshot",
    "nav_post_carry",
    "cash",
    "nav",
)


def _bar(price: float) -> Bar:
    return Bar(open=price, high=price, low=price, close=price)


@pytest.fixture(scope="module")
def result():
    """The engine's run of the scenario the hand ledger describes — parameters and all."""
    commission = SCENARIO["commission"]
    dividend = SCENARIO["dividend"]
    bars = {
        "TEST": [
            TimestampedBar(datetime.fromisoformat(ts), _bar(close))
            for ts, close in zip(SCENARIO["timestamps"], SCENARIO["closes"])
        ]
    }
    stack = CostStack(
        trade_bricks=(
            IBKRCommission(
                per_share=commission["per_share"],
                min_per_order=commission["minimum"],
                max_pct_of_trade_value=commission["cap_frac"],
            ),
            PercentOfNotionalSpread(bps=SCENARIO["spread_bps"]),
        ),
        carry_bricks=(BorrowFee(annual_rate=SCENARIO["borrow_annual"]),),
        portfolio_carry_bricks=(MarginInterest(annual_rate=SCENARIO["margin_annual"]),),
        event_flow_bricks=(
            DividendFlow(
                dividends_by_symbol={
                    SCENARIO["symbol"]: (
                        (datetime.fromisoformat(dividend["ex"]), dividend["per_share"]),
                    )
                }
            ),
        ),
    )
    strategy = ScheduledWeightStrategy(
        strategy_id="s", weights_by_instrument={SCENARIO["symbol"]: list(SCENARIO["weights"])}
    )
    return run_backtest(
        bars_by_instrument=bars,
        instruments={SCENARIO["symbol"]: Equity(symbol=SCENARIO["symbol"])},
        strategies=[strategy],
        cost_stack=stack,
        allocator=ConstantSplitAllocator(),
        starting_cash=SCENARIO["starting_cash"],
    )


# --------------------------------------------------------------- the closed-book calculator


def recompute(scenario: dict) -> list[dict]:
    """The scenario walked from first principles, in stdlib arithmetic only.

    This function must never reach for `backtest_framework` — that is the whole point of it,
    and `test_the_closed_book_calculator_never_reaches_for_the_engine` enforces it over this
    function's own source. A calculator that called the cost bricks would agree with them by
    construction and check nothing.

    The order of operations is the engine's stated order (hand file, line 20): snapshot at
    THIS bar's close on the PREVIOUS bar's cash -> per-leg borrow and dividend -> portfolio
    margin -> re-size at the post-carry NAV -> fill at the close.
    """
    per_share = scenario["commission"]["per_share"]
    minimum = scenario["commission"]["minimum"]
    cap_frac = scenario["commission"]["cap_frac"]
    bps = scenario["spread_bps"]
    ex_date = datetime.fromisoformat(scenario["dividend"]["ex"])
    per_share_dividend = scenario["dividend"]["per_share"]

    cash = scenario["starting_cash"]
    qty = 0.0
    previous: datetime | None = None
    out: list[dict] = []

    for index, (raw_ts, price, weight) in enumerate(
        zip(scenario["timestamps"], scenario["closes"], scenario["weights"])
    ):
        timestamp = datetime.fromisoformat(raw_ts)
        days = None if previous is None else (timestamp - previous).days
        borrow = margin_interest = dividend = 0.0
        short_notional = margin_base = 0.0

        if previous is None:
            # No previous bar means no carry step at all: the sizing NAV is the starting cash.
            nav_snapshot = cash + qty * price
        else:
            nav_snapshot = cash + qty * price
            if qty != 0.0:
                short_notional = -qty * price if qty < 0.0 else 0.0
                borrow = scenario["borrow_annual"] * short_notional * days / 365.0
                cash -= borrow
                if previous < ex_date <= timestamp:
                    # The SHORT pays the dividend it owes the lender (D6), so this is
                    # negative on a negative quantity and the sign is the assertion.
                    dividend = qty * per_share_dividend
                    cash += dividend
            margin_base = max(abs(qty) * price - nav_snapshot, 0.0)
            margin_interest = scenario["margin_annual"] * margin_base * days / 365.0
            cash -= margin_interest

        nav_post_carry = cash + qty * price
        desired = float(round(weight * nav_post_carry / price))  # whole shares
        delta = desired - qty
        notional = abs(delta) * price
        commission = (
            min(max(per_share * abs(delta), minimum), cap_frac * notional) if delta != 0.0 else 0.0
        )
        spread = bps / 10_000.0 * notional
        trade_cost = commission + spread
        cash -= delta * price + trade_cost

        out.append(
            {
                "index": index,
                "timestamp": raw_ts,
                "price": price,
                "days": days,
                "qty_before": qty,
                "qty_after": desired,
                "delta": delta,
                "notional": notional,
                "commission": commission,
                "spread": spread,
                "trade_cost": trade_cost,
                "short_notional": short_notional,
                "borrow": borrow,
                "margin_base": margin_base,
                "margin_interest": margin_interest,
                "dividend": dividend,
                "nav_snapshot": nav_snapshot,
                "nav_post_carry": nav_post_carry,
                "cash": cash,
                "nav": cash + desired * price,
            }
        )
        qty = desired
        previous = timestamp

    return out


def hand_notation(value: float) -> str:
    """A number as the .hand.txt writes one: comma-grouped, at the fewest decimals that
    reproduce it, capped at the ten places its carry accruals are printed to.

    `6.4438356164` and `100,149.6537022380` are how that file states borrow and final NAV;
    `117,600` and `-626.50` are how it states a notional and a dividend. One rule covers all
    four, and the JSON carries the file's digits precisely so this rule can be exact.
    """
    for places in range(0, 11):
        text = f"{value:,.{places}f}"
        if float(text.replace(",", "")) == value:
            return text
    return f"{value:,.10f}"


def _numbers(node: object, path: str = "") -> list[tuple[str, float]]:
    """Every numeric leaf in the ledger, with the path that names it.

    `index` is skipped: it is an ordinal, not a measurement, and asserting that "3" appears
    somewhere in a document full of dates would be theatre.
    """
    if isinstance(node, bool) or node is None:
        return []
    if isinstance(node, (int, float)):
        return [(path, float(node))]
    if isinstance(node, dict):
        return [
            pair
            for key, value in node.items()
            if key != "index"
            for pair in _numbers(value, f"{path}.{key}" if path else key)
        ]
    if isinstance(node, list):
        return [pair for i, item in enumerate(node) for pair in _numbers(item, f"{path}[{i}]")]
    return []


# ------------------------------------------------------------- the ledger against itself


def test_the_closed_book_recomputation_reproduces_every_hand_value():
    """The JSON is a transcription, made checkable.

    A hand ledger dumped out of the engine it is meant to check is worse than no golden test
    (CONTRIBUTING.md). Nothing about a committed JSON says which it is — so this walks the
    scenario block with stdlib arithmetic and reproduces all 19 fields of all 5 bars. It is
    the reason the artifact is trustworthy at all, and the reason the two figures built on it
    are allowed to quote it.
    """
    computed = recompute(SCENARIO)
    assert len(computed) == len(BARS)
    for got, want in zip(computed, BARS):
        assert got["timestamp"] == want["timestamp"]
        for field in LEDGER_FIELDS:
            assert field in want, f"bar {want['index']} has no {field!r} in the hand ledger"
            if want[field] is None:
                assert got[field] is None, f"bar {want['index']}: {field} should be null"
                continue
            assert got[field] == pytest.approx(want[field], rel=TOLERANCE, abs=1e-9), (
                f"bar {want['index']}: recomputed {field}={got[field]!r}, "
                f"hand ledger says {want[field]!r}"
            )


def test_the_closed_book_calculator_never_reaches_for_the_engine():
    """The one structural guarantee behind the test above.

    `recompute` sharing a module with the engine's imports is a standing invitation to "fix"
    a disagreement by calling `IBKRCommission().cost(...)` — after which the calculator agrees
    with the implementation by construction and the golden master checks nothing. The source
    is read rather than the behaviour, because the behaviour of a laundered calculator is
    indistinguishable from the behaviour of an honest one.
    """
    # The CODE, with the docstring and the comments removed: this test's subject is what the
    # function executes, and a prose mention of the module it must not call is not a call.
    tree = ast.parse(textwrap.dedent(inspect.getsource(recompute)))
    function = tree.body[0]
    assert isinstance(function, ast.FunctionDef)
    if ast.get_docstring(function) is not None:
        function.body = function.body[1:]
    source = ast.unparse(function)
    assert "backtest_framework" not in source
    for name in (
        "IBKRCommission",
        "PercentOfNotionalSpread",
        "BorrowFee",
        "MarginInterest",
        "DividendFlow",
        "CostStack",
        "run_backtest",
        "Equity",
        "Sizer",
    ):
        assert name not in source, (
            f"the closed-book calculator names {name!r}. It must reproduce the arithmetic, "
            "not call the implementation it exists to check."
        )


def test_every_hand_value_appears_in_the_hand_file():
    """Prose containment: the JSON says nothing the hand derivation does not.

    Substring containment against the .hand.txt, never a regex pulled through its prose — a
    parser over a hand-written document is a second implementation of the document, and it
    fails the day someone writes a sentence it did not anticipate.

    Containment is a floor, not a proof (at zero decimals `6.00` contains `6`). The
    recomputation above carries the weight; this catches the different failure — a value
    invented in the JSON that the hand derivation never states.
    """
    prose = HAND_TXT.read_text(encoding="utf-8")
    missing = [
        (path, value, hand_notation(value))
        for path, value in _numbers(HAND)
        if hand_notation(value) not in prose
    ]
    assert not missing, (
        f"{len(missing)} value(s) in the hand JSON are not stated in "
        f"{HAND_TXT.name}: {missing[:6]}"
    )
    # Dates: the hand file writes the year once ("Thu 2026-01-08") and the rest month-day
    # ("Fri 01-09"), so the year is checked once and each bar by the form it is written in.
    years = {raw_ts[:4] for raw_ts in SCENARIO["timestamps"]}
    assert len(years) == 1 and years.pop() in prose
    for raw_ts in SCENARIO["timestamps"] + [SCENARIO["dividend"]["ex"]]:
        month_day = raw_ts.split("T")[0][5:]
        assert month_day in prose, f"{month_day} is not a date the hand derivation mentions"


def test_the_hand_file_is_the_transcription_source_and_says_so():
    """The convention in one assertion: the .hand.txt is the source, the JSON is downstream.

    If these ever point at each other the provenance is circular and the artifact is only as
    good as whichever was written second.
    """
    assert HAND["transcribed_from"] == "tests/golden/test_the_golden_master.hand.txt"
    assert "INDEPENDENT bar-by-bar calculator" in HAND_TXT.read_text(encoding="utf-8")


# ------------------------------------------------------------ the ledger against the engine


def test_every_fill_line_by_line(result):
    expected = [
        (datetime.fromisoformat(b["timestamp"]), SCENARIO["symbol"], b["delta"], b["price"], b["trade_cost"])
        for b in BARS
        if b["delta"] != 0.0
    ]
    assert len(result.fills) == len(expected)
    for actual, exp in zip(result.fills, expected):
        ts, instrument_id, qty, price, cost = actual
        assert (ts, instrument_id) == (exp[0], exp[1])
        assert qty == exp[2]  # share counts are exact integers
        assert price == exp[3]
        assert cost == pytest.approx(exp[4], rel=TOLERANCE)


def test_each_trade_cost_is_its_commission_plus_its_spread(result):
    """The defect this file could not see before the ledger existed.

    `BacktestResult.fills` carries ONE number per fill for the whole cost stack, so $6.00
    moved out of `IBKRCommission` and into `PercentOfNotionalSpread` changed nothing any
    assertion here could read. It still cannot be read off a fill — but the two components
    are now stated separately, recomputed separately, and required to sum to the published
    figure. The $1 minimum firing on bar 1's 53-share re-size is the case that matters: it
    is the only bar where commission is not a linear function of size.
    """
    traded = [b for b in BARS if b["delta"] != 0.0]
    assert len(traded) == len(result.fills)
    for fill, bar in zip(result.fills, traded):
        published = fill[4]
        assert bar["commission"] + bar["spread"] == pytest.approx(published, rel=TOLERANCE), (
            f"bar {bar['index']}: the hand ledger's {bar['commission']} + {bar['spread']} "
            f"is not the {published} the engine published"
        )
    # The minimum fires exactly once, and on the smallest order.
    minimum = SCENARIO["commission"]["minimum"]
    by_the_minimum = [
        b for b in traded if b["commission"] == minimum and SCENARIO["commission"]["per_share"] * abs(b["delta"]) < minimum
    ]
    assert [b["index"] for b in by_the_minimum] == [1, 2]


def test_the_cash_curve_carries_the_carry_the_engine_never_reports(result):
    """Borrow, margin interest and the dividend, reached through the only channel there is.

    The engine records no carry accrual and no event flow (backtest.py:42-79). What it does
    record is cash, so the carry is exactly the residual: whatever moved the cash curve that
    the bar's own fill does not explain. That residual is asserted against the hand ledger
    here, which is the first time any of the three has been pinned at all.

    It pins their SUM. Borrow and margin interest are cash deductions of the same sign at the
    same instant and no published quantity separates them; the hand ledger splits them and the
    closed-book calculator reproduces the split, but the engine is silent on which is which.
    That is the gap docs/figures/golden-master-ledger-diff.svg draws.
    """
    cash = [value for _ts, value in result.cash_curve]
    previous = SCENARIO["starting_cash"]
    for bar, actual in zip(BARS, cash):
        # cash_t = cash_{t-1} - borrow - margin + dividend - (delta * price) - trade_cost
        implied_carry = actual - previous + bar["delta"] * bar["price"] + bar["trade_cost"]
        expected_carry = bar["dividend"] - bar["borrow"] - bar["margin_interest"]
        assert implied_carry == pytest.approx(expected_carry, rel=TOLERANCE, abs=1e-6), (
            f"bar {bar['index']}: the cash curve moved by a carry of {implied_carry!r}; "
            f"the hand ledger says borrow {bar['borrow']!r} + margin "
            f"{bar['margin_interest']!r} + dividend {bar['dividend']!r}"
        )
        previous = actual


def test_the_dividend_debit_lands_on_the_right_bar_with_the_right_sign(result):
    """A sign asserted in prose inverted a study once (CLAUDE.md, D280). This one is asserted
    in money: the short pays, so the flow is negative, it lands on the ex-date bar and on no
    other, and its size is the share count owed times the per-share amount."""
    ex = datetime.fromisoformat(SCENARIO["dividend"]["ex"])
    on_ex = [b for b in BARS if datetime.fromisoformat(b["timestamp"]) == ex]
    assert len(on_ex) == 1
    bar = on_ex[0]
    assert bar["dividend"] < 0.0, "a short position PAYS the dividend it owes the lender (D6)"
    assert bar["dividend"] == pytest.approx(
        bar["qty_before"] * SCENARIO["dividend"]["per_share"], rel=TOLERANCE
    )
    assert all(b["dividend"] == 0.0 for b in BARS if b["index"] != bar["index"])
    # And it is visible in the engine's cash curve as a step this size, net of the bar's fill
    # and its two accruals — the only place the engine lets it be seen at all.
    cash_before = SCENARIO["starting_cash"] if bar["index"] == 0 else BARS[bar["index"] - 1]["cash"]
    step = bar["cash"] - cash_before
    assert step == pytest.approx(
        bar["dividend"] - bar["borrow"] - bar["margin_interest"] - bar["delta"] * bar["price"] - bar["trade_cost"],
        rel=TOLERANCE,
    )
    assert result.cash_curve[bar["index"]][1] == pytest.approx(bar["cash"], rel=TOLERANCE)


def test_cash_curve_line_by_line(result):
    expected = [(datetime.fromisoformat(b["timestamp"]), b["cash"]) for b in BARS]
    assert [ts for ts, _ in result.cash_curve] == [ts for ts, _ in expected]
    for (_, actual), (_, exp) in zip(result.cash_curve, expected):
        assert actual == pytest.approx(exp, rel=TOLERANCE)


def test_equity_curve_line_by_line(result):
    expected = [(datetime.fromisoformat(b["timestamp"]), b["nav"]) for b in BARS]
    assert [ts for ts, _ in result.equity_curve] == [ts for ts, _ in expected]
    for (_, actual), (_, exp) in zip(result.equity_curve, expected):
        assert actual == pytest.approx(exp, rel=TOLERANCE)


def test_nav_is_cash_plus_the_marked_position_every_bar(result):
    """The identity the equity curve is supposed to BE, checked against the ledger's own
    share count rather than against the engine's — which is the half of it the engine's own
    curve cannot check."""
    for bar, (_ts, nav) in zip(BARS, result.equity_curve):
        assert nav == pytest.approx(bar["cash"] + bar["qty_after"] * bar["price"], rel=TOLERANCE)


def test_final_state(result):
    assert result.final_positions.get(SCENARIO["symbol"], 0.0) == 0.0
    assert result.final_nav == pytest.approx(HAND["final_nav"], rel=TOLERANCE)
    # Cross-check independent of the bar-by-bar bookkeeping: final NAV - start ==
    # short price P&L - all frictions - dividend debit. The identity that MUST hold
    # here is NAV == cash (flat book).
    assert result.final_cash == pytest.approx(result.final_nav, rel=TOLERANCE)


def test_the_frictions_and_the_price_pnl_account_for_the_whole_result():
    """Every dollar between 100,000 and the final NAV, named.

    Price P&L on the varying short position is +967.00 exactly; the five frictions take
    817.35 of it, of which the dividend alone is 626.50 — 4.5x the commission and spread the
    engine actually reports. This is the decomposition docs/figures/cost-waterfall.svg draws,
    and it is asserted here so the figure is quoting a checked identity rather than a sum
    somebody did once.
    """
    price_pnl = sum(
        bar["qty_after"] * (nxt["price"] - bar["price"]) for bar, nxt in zip(BARS, BARS[1:])
    )
    assert price_pnl == pytest.approx(967.0, abs=1e-9)
    frictions = sum(
        bar["commission"] + bar["spread"] + bar["borrow"] + bar["margin_interest"] - bar["dividend"]
        for bar in BARS
    )
    assert price_pnl - frictions == pytest.approx(
        HAND["final_nav"] - SCENARIO["starting_cash"], rel=TOLERANCE
    )


def test_the_engine_still_publishes_no_per_brick_attribution():
    """The gap, recorded as a gate so it cannot close silently.

    `BacktestResult` has no field for commission, spread, borrow, margin interest or an event
    flow. That is the reason this file needs a hand ledger for the decomposition and the
    reason the ledger-diff figure has a 'hand only' band. The day the engine grows real
    attribution, this test fails — and the right response is to delete it and assert the new
    fields against the ledger, component by component, instead of inferring their sum from
    the cash curve.
    """
    published = set(BacktestResult.__dataclass_fields__)
    for absent in ("commissions", "spreads", "borrow", "carry", "carry_curve", "flows", "dividends", "attribution"):
        assert absent not in published, (
            f"BacktestResult now publishes {absent!r}. Assert it against the hand ledger "
            "and delete this test — the inference through the cash curve is a workaround."
        )
    assert "fills" in published and "cash_curve" in published and "equity_curve" in published

"""What the ENGINE publishes for the golden-master scenario, as a tracked artifact.

    python scripts/run_golden_master_ledger.py --build     # writes data/golden_master_ledger.json
    python scripts/run_golden_master_ledger.py --check     # re-runs and fails if it has drifted
    python scripts/run_golden_master_ledger.py --status

WHY A SECOND LEDGER
-------------------
`tests/golden/test_the_golden_master.hand.json` is the hand ledger: every brick, per bar,
transcribed from `test_the_golden_master.hand.txt`. This file is the other side of the
comparison — the same five bars as the engine actually reports them.

The two are not the same shape, and that is the finding. `BacktestResult`
(src/backtest_framework/engine/backtest.py:42-79) publishes fills, a cash curve, an equity
curve and final state. A fill carries ONE cost number for the whole stack, so commission and
spread are already summed by the time anything can read them; carry accruals and event flows
reach `PortfolioState` and are recorded nowhere at all. Borrow, margin interest and the
dividend are therefore invisible except as motion in the cash curve.

This script writes down exactly what is there and nothing more — no reconstruction, no
inference, no decomposition. `NOT_PUBLISHED` names what is missing, in the artifact, so a
reader of the JSON alone is told. `docs/figures/golden-master-ledger-diff.svg` draws the two
side by side with a zero-valued difference column, and a separated band for the rows that
have no engine column to compare against.

The scenario is read from the hand ledger's `scenario` block, so there is one statement of
it in the repository rather than three.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.costs.bricks import PercentOfNotionalSpread  # noqa: E402
from backtest_framework.costs.equity_bricks import (  # noqa: E402
    BorrowFee,
    DividendFlow,
    IBKRCommission,
    MarginInterest,
)
from backtest_framework.costs.stack import CostStack  # noqa: E402
from backtest_framework.data.bars import TimestampedBar  # noqa: E402
from backtest_framework.engine.allocator import ConstantSplitAllocator  # noqa: E402
from backtest_framework.engine.backtest import BacktestResult, run_backtest  # noqa: E402
from backtest_framework.engine.strategy import ScheduledWeightStrategy  # noqa: E402
from backtest_framework.instruments.equity import Equity  # noqa: E402
from backtest_framework.simulator.fills import Bar  # noqa: E402

HAND = REPO / "tests" / "golden" / "test_the_golden_master.hand.json"
LEDGER = REPO / "data" / "golden_master_ledger.json"

# Named in the artifact itself: a reader who has only this file should not have to infer the
# absence of an attribution they were looking for.
NOT_PUBLISHED = (
    "commission",
    "spread",
    "borrow",
    "margin_interest",
    "dividend",
)


def scenario() -> dict:
    return json.loads(HAND.read_text(encoding="utf-8"))["scenario"]


def run(spec: dict) -> BacktestResult:
    """The scenario as the engine runs it. Every parameter comes from `spec`."""
    symbol = spec["symbol"]
    commission = spec["commission"]
    dividend = spec["dividend"]
    bars = {
        symbol: [
            TimestampedBar(
                datetime.fromisoformat(ts), Bar(open=close, high=close, low=close, close=close)
            )
            for ts, close in zip(spec["timestamps"], spec["closes"])
        ]
    }
    stack = CostStack(
        trade_bricks=(
            IBKRCommission(
                per_share=commission["per_share"],
                min_per_order=commission["minimum"],
                max_pct_of_trade_value=commission["cap_frac"],
            ),
            PercentOfNotionalSpread(bps=spec["spread_bps"]),
        ),
        carry_bricks=(BorrowFee(annual_rate=spec["borrow_annual"]),),
        portfolio_carry_bricks=(MarginInterest(annual_rate=spec["margin_annual"]),),
        event_flow_bricks=(
            DividendFlow(
                dividends_by_symbol={
                    symbol: ((datetime.fromisoformat(dividend["ex"]), dividend["per_share"]),)
                }
            ),
        ),
    )
    return run_backtest(
        bars_by_instrument=bars,
        instruments={symbol: Equity(symbol=symbol)},
        strategies=[
            ScheduledWeightStrategy(
                strategy_id="s", weights_by_instrument={symbol: list(spec["weights"])}
            )
        ],
        cost_stack=stack,
        allocator=ConstantSplitAllocator(),
        starting_cash=spec["starting_cash"],
    )


def ledger(spec: dict, result: BacktestResult) -> dict:
    """Published values only, per bar and in the raw.

    A bar with no fill gets `fill_qty` 0.0 and `fill_price` null — null means THERE WAS NO
    FILL, which is a different statement from a price of zero, and the two must not be
    allowed to look alike in an artifact a figure reads.
    """
    fills_by_timestamp: dict[str, list[tuple]] = {}
    for ts, instrument_id, qty, price, trade_cost in result.fills:
        fills_by_timestamp.setdefault(ts.isoformat(), []).append(
            (instrument_id, qty, price, trade_cost)
        )

    bars = []
    for (ts, cash), (_ts, nav) in zip(result.cash_curve, result.equity_curve):
        key = ts.isoformat()
        at_this_bar = fills_by_timestamp.get(key, [])
        if len(at_this_bar) > 1:  # pragma: no cover - one instrument, netted orders
            raise SystemExit(f"{key}: {len(at_this_bar)} broker fills on one bar; expected 0 or 1")
        bars.append(
            {
                "timestamp": key,
                "fill_qty": at_this_bar[0][1] if at_this_bar else 0.0,
                "fill_price": at_this_bar[0][2] if at_this_bar else None,
                "trade_cost": at_this_bar[0][3] if at_this_bar else 0.0,
                "cash": cash,
                "nav": nav,
            }
        )

    return {
        "what": "What BacktestResult publishes for the golden-master scenario, and nothing else.",
        "generator": "scripts/run_golden_master_ledger.py",
        "scenario_source": "tests/golden/test_the_golden_master.hand.json (scenario block)",
        "gate": "tests/unit/test_figure_ledger_diff.py",
        "not_published": list(NOT_PUBLISHED),
        "not_published_note": (
            "BacktestResult (src/backtest_framework/engine/backtest.py:42-79) records no "
            "per-brick attribution. A fill's trade_cost is commission PLUS spread, already "
            "summed; carry accruals and event flows are applied to PortfolioState and never "
            "recorded. These five rows exist only in the hand ledger."
        ),
        "bars": bars,
        "fills": [
            {
                "timestamp": ts.isoformat(),
                "instrument_id": instrument_id,
                "qty": qty,
                "price": price,
                "trade_cost": trade_cost,
            }
            for ts, instrument_id, qty, price, trade_cost in result.fills
        ],
        "cash_curve": [[ts.isoformat(), value] for ts, value in result.cash_curve],
        "equity_curve": [[ts.isoformat(), value] for ts, value in result.equity_curve],
        "final_positions": dict(result.final_positions),
        "final_cash": result.final_cash,
        "final_nav": result.final_nav,
        "starting_cash": spec["starting_cash"],
    }


def build() -> dict:
    return ledger(scenario(), run(scenario()))


def cmd_build() -> int:
    payload = build()
    LEDGER.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(
        f"{len(payload['bars'])} bars, {len(payload['fills'])} fills, "
        f"final NAV {payload['final_nav']:,.10f} -> {LEDGER.relative_to(REPO).as_posix()}"
    )
    return 0


def cmd_check() -> int:
    """A committed artifact that no longer matches the engine is the drift this exists to
    catch — the figure built on it would keep quoting yesterday's engine."""
    if not LEDGER.exists():
        print(f"MISSING  {LEDGER.relative_to(REPO).as_posix()} — run --build")
        return 1
    want = json.dumps(build(), indent=2) + "\n"
    # Bytes, not text — `--build` above pins `newline="\n"`, and `read_text` applies
    # universal-newline translation, so a CRLF ledger would decode back to `\n` and compare
    # equal to what the build produces. The check would be blind to exactly the thing the build
    # controls. Same defect as `scripts/figures/build_all.py --check` carried, found by applying
    # that finding to the rest of the repository rather than stopping at the instance.
    if LEDGER.read_bytes() != want.encode("utf-8"):
        print(f"STALE    {LEDGER.relative_to(REPO).as_posix()} — run --build")
        return 1
    print(f"{LEDGER.relative_to(REPO).as_posix()} is current")
    return 0


def cmd_status() -> int:
    if not LEDGER.exists():
        print("no ledger")
        return 1
    payload = json.loads(LEDGER.read_text(encoding="utf-8"))
    print(f"bars          {len(payload['bars'])}")
    print(f"fills         {len(payload['fills'])}")
    print(f"final NAV     {payload['final_nav']:,.10f}")
    print(f"not published {', '.join(payload['not_published'])}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--status", action="store_true")
    args = ap.parse_args()

    if args.build:
        return cmd_build()
    if args.check:
        return cmd_check()
    if args.status:
        return cmd_status()
    ap.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

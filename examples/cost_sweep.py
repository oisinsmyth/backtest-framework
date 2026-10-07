"""Run one backtest at 0x, 0.5x, 1x, 2x and 4x its cost stack.

Net P&L must not rise as costs are scaled up. How fast it falls shows how much of the
gross edge the costs consume.

Run: uv run python examples/cost_sweep.py
"""

from pathlib import Path

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.equity_bricks import IBKRCommission
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.csv_fixture import load_fixture_csv
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.sweep import render_sweep_table, run_cost_sweep
from backtest_framework.instruments.equity import Equity
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy

FIXTURE = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "synthetic_pair_daily.csv"


def make_strategies():
    # A factory, not an instance: each run gets a fresh strategy with no carried-over state.
    return [ZScorePairsStrategy(strategy_id="aaa_bbb", instrument_a="AAA", instrument_b="BBB")]


sweep = run_cost_sweep(
    bars_by_instrument=load_fixture_csv(FIXTURE),
    instruments={"AAA": Equity(symbol="AAA"), "BBB": Equity(symbol="BBB")},
    make_strategies=make_strategies,
    base_cost_stack=CostStack(trade_bricks=(IBKRCommission(), PercentOfNotionalSpread(bps=1.0))),
    allocator=ConstantSplitAllocator(),
    starting_cash=100_000.0,
    multipliers=(0.0, 0.5, 1.0, 2.0, 4.0),
)

print(render_sweep_table(sweep))

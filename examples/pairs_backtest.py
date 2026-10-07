"""End-to-end backtest: a z-score pairs strategy on the bundled synthetic AAA/BBB daily fixture.

Run: uv run python examples/pairs_backtest.py
"""

from pathlib import Path

from backtest_framework.analytics.metrics import max_drawdown, sharpe, sortino
from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.equity_bricks import BorrowFee, IBKRCommission, MarginInterest
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.csv_fixture import load_fixture_csv
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.instruments.equity import Equity
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy

FIXTURE = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "synthetic_pair_daily.csv"
STARTING_CASH = 100_000.0

bars = load_fixture_csv(FIXTURE)  # {"AAA": [...], "BBB": [...]}, daily OHLC bars

costs = CostStack(
    trade_bricks=(IBKRCommission(), PercentOfNotionalSpread(bps=1.0)),  # per fill
    carry_bricks=(BorrowFee(annual_rate=0.0025),),  # per short leg held overnight
    portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),),  # on the book's borrowing
)

strategy = ZScorePairsStrategy(
    strategy_id="aaa_bbb", instrument_a="AAA", instrument_b="BBB",
    lookback=60, entry_z=2.0, exit_z=0.5, leg_weight=1.0,
)

result = run_backtest(
    bars_by_instrument=bars,
    instruments={"AAA": Equity(symbol="AAA"), "BBB": Equity(symbol="BBB")},
    strategies=[strategy],
    cost_stack=costs,
    allocator=ConstantSplitAllocator(),
    starting_cash=STARTING_CASH,
)

navs = [nav for _, nav in result.equity_curve]
returns = [b / a - 1.0 for a, b in zip(navs, navs[1:])]
total_cost = sum(fill[4] for fill in result.fills)

print(f"bars            {len(navs)}")
print(f"fills           {len(result.fills)}")
print(f"trading costs   ${total_cost:,.2f}")
print(f"final NAV       ${result.final_nav:,.2f}")
print(f"net P&L         ${result.final_nav - STARTING_CASH:,.2f}")
print(f"Sharpe (rf 0)   {sharpe(returns, rf_annual=0.0, periods_per_year=252):.3f}")
print(f"Sortino (rf 0)  {sortino(returns, rf_annual=0.0, periods_per_year=252):.3f}")
print(f"max drawdown    {max_drawdown(result.equity_curve):.2%}")

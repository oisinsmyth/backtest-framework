"""Log every cell of a parameter grid, then deflate the best cell's Sharpe by the grid size.

The best of many trials looks good partly by luck. The deflated Sharpe ratio (Bailey and
Lopez de Prado, 2014) is the probability that the selected Sharpe beats the best Sharpe
expected from the same number of zero-edge trials. Its inputs, the trial count and the
variance of Sharpe across trials, come from the registry rather than from memory.

Run: uv run python examples/deflated_sharpe.py
"""

import statistics
import tempfile
from itertools import product
from pathlib import Path

from backtest_framework.costs.bricks import PercentOfNotionalSpread
from backtest_framework.costs.equity_bricks import IBKRCommission
from backtest_framework.costs.stack import CostStack
from backtest_framework.data.csv_fixture import load_fixture_csv
from backtest_framework.engine.allocator import ConstantSplitAllocator
from backtest_framework.engine.backtest import run_backtest
from backtest_framework.instruments.equity import Equity
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.strategies.zscore_pairs import ZScorePairsStrategy
from backtest_framework.validation.dsr import deflated_sharpe_from_trials, expected_max_sharpe

FIXTURE = Path(__file__).resolve().parent.parent / "data" / "fixtures" / "synthetic_pair_daily.csv"
bars = load_fixture_csv(FIXTURE)
instruments = {"AAA": Equity(symbol="AAA"), "BBB": Equity(symbol="BBB")}
costs = CostStack(trade_bricks=(IBKRCommission(), PercentOfNotionalSpread(bps=1.0)))

workdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
registry = TrialRegistry(Path(workdir.name) / "trials.sqlite")
returns_by_trial = {}
for lookback, entry_z in product((20, 40, 60, 90), (1.5, 2.0, 2.5)):
    trial_id = f"lb{lookback}-z{entry_z}"
    result = run_backtest(
        bars_by_instrument=bars,
        instruments=instruments,
        strategies=[ZScorePairsStrategy("aaa_bbb", "AAA", "BBB", lookback=lookback, entry_z=entry_z)],
        cost_stack=costs,
        allocator=ConstantSplitAllocator(),
        starting_cash=100_000.0,
    )
    navs = [nav for _, nav in result.equity_curve]
    returns = [b / a - 1.0 for a, b in zip(navs, navs[1:])]
    sr = statistics.mean(returns) / statistics.stdev(returns)  # per period, not annualised
    registry.add_trial(trial_id, config={"lookback": lookback, "entry_z": entry_z}, params={},
                       metrics={"sharpe_per_period": sr}, snapshot_id=FIXTURE.name, seed=0)
    returns_by_trial[trial_id] = returns
    print(f"{trial_id:<12} Sharpe/period {sr:+.4f}   annualised {sr * 252 ** 0.5:+.3f}")

best = max(registry.all_trials(), key=lambda t: t.metrics["sharpe_per_period"])
r = returns_by_trial[best.trial_id]
mu, sd, n = statistics.mean(r), statistics.pstdev(r), len(r)
skew = sum((x - mu) ** 3 for x in r) / n / sd**3
kurt = sum((x - mu) ** 4 for x in r) / n / sd**4  # raw kurtosis, 3.0 for Normal returns

sharpes = [t.metrics["sharpe_per_period"] for t in registry.all_trials()]
floor = expected_max_sharpe(len(sharpes), statistics.variance(sharpes))
dsr = deflated_sharpe_from_trials(registry, "sharpe_per_period", best.metrics["sharpe_per_period"], n, skew, kurt)
print(f"\nbest cell       {best.trial_id}")
print(f"noise floor     {floor:+.4f} per period, the expected best of {len(sharpes)} zero-edge trials")
print(f"deflated Sharpe {dsr:.3f}  (probability the best cell's Sharpe beats that floor)")

registry.close()
workdir.cleanup()

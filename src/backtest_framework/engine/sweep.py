"""Cost-multiplier sweep (D8, D68): run the same backtest at scaled cost levels.

"Does it survive 2× costs" is the single most informative output for edges this thin
— more valuable than any refinement to cost functional forms (D8's own rationale).
run_cost_sweep runs an identical scenario once per multiplier through the existing
run_backtest, scaling the CostStack via costs.scaling.scaled_cost_stack.

Strategies are supplied as a FACTORY (a zero-arg callable returning fresh instances),
not as instances — strategies may hold per-run state (e.g. ZScorePairsStrategy's
current side), and reusing an instance across multiplier runs would leak state from
one run into the next (D68). The sweep cannot be handed something it could silently
misuse.

render_sweep_table produces the minimal markdown table the Step 6 gate calls a
"tearsheet" — multiplier, final NAV, net P&L, return, max drawdown. The real
tearsheet (Sharpe with explicit rf per D49, beta per D37, sample-size-gated tails per
D36) is Step 9's job and is deliberately not imitated here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Mapping, Sequence

from ..costs.scaling import scaled_cost_stack
from ..costs.stack import CostStack
from ..data.bars import TimestampedBar
from ..instruments.base import Instrument
from ..registry.trial_registry import TrialRegistry
from .allocator import Allocator
from .backtest import BacktestResult, run_backtest
from .strategy import Strategy

DEFAULT_MULTIPLIERS = (0.0, 0.5, 1.0, 2.0, 4.0)


@dataclass(frozen=True)
class SweepRun:
    multiplier: float
    result: BacktestResult

    def net_pnl(self, starting_cash: float) -> float:
        return self.result.final_nav - starting_cash


@dataclass(frozen=True)
class SweepResult:
    starting_cash: float
    runs: tuple[SweepRun, ...]

    def net_pnls(self) -> list[tuple[float, float]]:
        """[(multiplier, net P&L)], in the order the sweep ran (ascending multiplier
        if the caller passed them sorted — the default is)."""
        return [(run.multiplier, run.net_pnl(self.starting_cash)) for run in self.runs]


def max_drawdown(equity_curve: Sequence[tuple[object, float]]) -> float:
    """Largest peak-to-trough decline as a positive fraction of the peak. Plain
    arithmetic on the equity curve — not a Step 9 statistic."""
    peak = float("-inf")
    worst = 0.0
    for _, nav in equity_curve:
        peak = max(peak, nav)
        if peak > 0:
            worst = max(worst, (peak - nav) / peak)
    return worst


def run_cost_sweep(
    bars_by_instrument: Mapping[str, Sequence[TimestampedBar]],
    instruments: Mapping[str, Instrument],
    make_strategies: Callable[[], list[Strategy]],
    base_cost_stack: CostStack,
    allocator: Allocator,
    starting_cash: float,
    multipliers: Sequence[float] = DEFAULT_MULTIPLIERS,
    trial_registry: TrialRegistry | None = None,
    trial_id_prefix: str | None = None,
    config: dict | None = None,
    snapshot_id: str = "unspecified",
    seed: int = 0,
    splits_by_instrument=None,
    view_bars_by_instrument=None,
) -> SweepResult:
    runs: list[SweepRun] = []
    for multiplier in multipliers:
        result = run_backtest(
            bars_by_instrument=bars_by_instrument,
            instruments=instruments,
            strategies=make_strategies(),  # fresh instances — no state leaks across runs
            cost_stack=scaled_cost_stack(base_cost_stack, multiplier),
            allocator=allocator,
            starting_cash=starting_cash,
            trial_registry=trial_registry,
            trial_id=f"{trial_id_prefix}-{multiplier}x" if trial_id_prefix is not None else None,
            config={**config, "cost_multiplier": multiplier} if config is not None else None,
            snapshot_id=snapshot_id,
            seed=seed,
            splits_by_instrument=splits_by_instrument,
            view_bars_by_instrument=view_bars_by_instrument,
        )
        runs.append(SweepRun(multiplier=multiplier, result=result))
    return SweepResult(starting_cash=starting_cash, runs=tuple(runs))


def render_sweep_table(sweep: SweepResult) -> str:
    lines = [
        "| Cost multiplier | Final NAV | Net P&L | Return | Max drawdown |",
        "|---|---|---|---|---|",
    ]
    for run in sweep.runs:
        nav = run.result.final_nav
        pnl = run.net_pnl(sweep.starting_cash)
        ret = pnl / sweep.starting_cash
        dd = max_drawdown(run.result.equity_curve)
        lines.append(
            f"| {run.multiplier:g}× | {nav:,.2f} | {pnl:+,.2f} | {ret:+.2%} | {dd:.2%} |"
        )
    return "\n".join(lines)

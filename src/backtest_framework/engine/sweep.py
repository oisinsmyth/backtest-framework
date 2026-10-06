"""Cost-multiplier sweep: run the same backtest at scaled cost levels.

For a thin edge, whether it survives 2× costs is usually more informative than any
refinement of the cost model. run_cost_sweep runs the same scenario through
run_backtest once per multiplier, scaling the CostStack with
costs.scaling.scaled_cost_stack.

Strategies are passed as a zero-argument factory so each run gets fresh instances;
strategies can hold per-run state (e.g. ZScorePairsStrategy's current side).

render_sweep_table produces a markdown table of multiplier, final NAV, net P&L,
return and max drawdown. The full tearsheet (Sharpe with explicit rf, beta,
sample-size-gated tails) is in analytics.tearsheet.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Mapping, Sequence

from ..analytics.metrics import max_drawdown
from ..costs.scaling import scaled_cost_stack
from ..costs.stack import CostStack
from ..data.bars import TimestampedBar
from ..instruments.base import Instrument
from ..registry.trial_registry import TrialRegistry
from .allocator import Allocator
from .backtest import BacktestResult, run_backtest
from .risk import RiskLimits
from .strategy import Strategy

# `max_drawdown` is used by render_sweep_table but exported from analytics/metrics.py.
__all__ = ["run_cost_sweep", "render_sweep_table", "SweepResult", "SweepRun"]

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
        """[(multiplier, net P&L)] in the order the sweep ran (the default multipliers
        are ascending)."""
        return [(run.multiplier, run.net_pnl(self.starting_cash)) for run in self.runs]


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
    splits_by_instrument: Mapping[str, Sequence[tuple[datetime, float]]] | None = None,
    view_bars_by_instrument: Mapping[str, Sequence[TimestampedBar]] | None = None,
    volumes_by_instrument: Mapping[str, Sequence[float | None]] | None = None,
    fill_timing: str = "close",
    risk_limits: RiskLimits | None = None,
    enforce_pretrade: bool = False,
) -> SweepResult:
    """Run the backtest once per cost multiplier and collect the results.

    Apart from `multipliers` and `make_strategies`, every argument is forwarded to
    run_backtest with the same meaning and default. Each run's trial_id gets a
    `-{multiplier}x` suffix and its config a `cost_multiplier` key."""
    runs: list[SweepRun] = []
    for multiplier in multipliers:
        result = run_backtest(
            bars_by_instrument=bars_by_instrument,
            instruments=instruments,
            strategies=make_strategies(),  # fresh instances so no state carries over
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
            volumes_by_instrument=volumes_by_instrument,
            fill_timing=fill_timing,
            risk_limits=risk_limits,
            enforce_pretrade=enforce_pretrade,
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

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

`run_cost_sweep` forwards EVERY run_backtest keyword that shapes the run. It used to
forward only nine of thirteen, silently dropping `volumes_by_instrument`,
`fill_timing`, `risk_limits` and `enforce_pretrade` — which meant a caller could hand
it a BreakoutStrategy carrying a VolumeConfirmationFilter and get MissingVolumeError,
or hand it fill_timing="next_open" and get close fills with no complaint. A sweep
argument that a caller sets and the sweep discards is worse than one that does not
exist (D48). `test_cost_sweep.py` now sweeps exactly that strategy, and asserts the
sweep raises when the volumes are withheld, so the forwarding cannot rot back.

NOT superseded by research/gross_sweep.py, which sweeps LEG WEIGHT through the D95
capacity study, not the cost multiplier, and answers a different question (D96).
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

# `max_drawdown` is imported for render_sweep_table's own use and is deliberately NOT
# re-exported: D80 moved it to analytics/metrics.py, and a second public name for it
# here is the kind of duplicate import path that keeps a moved function half-moved.
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
        """[(multiplier, net P&L)], in the order the sweep ran (ascending multiplier
        if the caller passed them sorted — the default is)."""
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
    """Every keyword here except `multipliers` and `make_strategies` has the same
    meaning and default as the run_backtest parameter it forwards to; the sweep adds
    no semantics of its own. Keep it that way — the defect this signature fixes was
    four run_backtest parameters with no way to reach them from a sweep."""
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

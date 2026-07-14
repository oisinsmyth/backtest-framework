"""Pairs study v1 (Phase G, D89, D90): walk-forward Gatev selection + z-score
trading over a broad ETF universe, through the full real cost stack, swept, logged,
and DSR-adjusted.

Study glue only — every load-bearing component is the gate-tested framework piece:
walk_forward_windows (D85), select_pairs (D29), run_backtest's multi-strategy
netting engine (D27/D64), scaled_cost_stack (D68), TrialRegistry (D20),
deflated_sharpe_from_trials (D86), the tearsheet (D80/D81).

Design (D89):
- One multi-strategy run per (window, multiplier): N ZScorePairsStrategy instances
  (one per selected pair) share a single portfolio; ConstantSplitAllocator splits
  capital; shared legs across pairs net internally instead of paying costs twice.
- Warm-up prefix: each run receives the last `lookback` TRAIN bars prepended to its
  test bars. The strategy's own warm-up guard keeps it flat through the prefix, so
  the first possible trade is the first true test bar; stitching takes equity from
  the first test bar on. Backward-looking data only — no leak.
- Window chaining: window i's starting cash = window i−1's final NAV at the same
  multiplier, so the stitched curve compounds like a real account.
- Signal/execution frames per D75: selection and strategy views use the provider
  (split-adjusted) frame; fills, costs, carry and NAV use reconstructed as-traded
  prices, with splits scaling positions and declared-frame dividends flowing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Mapping, Sequence

import numpy as np

from ..analytics.metrics import max_drawdown, sharpe
from ..analytics.tearsheet import render_metrics_table
from ..costs.calibration import calibrate_impact_params
from ..costs.bricks import PercentOfNotionalSpread
from ..costs.equity_bricks import BorrowFee, DividendFlow, IBKRCommission, MarginInterest, SqrtImpact
from ..costs.scaling import scaled_cost_stack
from ..costs.stack import CostStack
from ..data.bars import TimestampedBar
from ..data.corporate_actions import CorporateActions, as_declared_dividends, as_traded_from_adjusted
from ..engine.allocator import ConstantSplitAllocator
from ..engine.backtest import run_backtest
from ..instruments.equity import Equity
from ..registry.trial_registry import TrialRegistry
from ..strategies.zscore_pairs import ZScorePairsStrategy
from ..validation.dsr import deflated_sharpe_from_trials
from ..validation.pair_selection import select_pairs
from ..validation.walk_forward import walk_forward_windows


@dataclass(frozen=True)
class StudyConfig:
    train_size: int = 252
    test_size: int = 63
    step: int = 63
    top_n: int = 5
    lookback: int = 30
    entry_z: float = 2.0
    exit_z: float = 0.5
    leg_weight: float = 1.0
    multipliers: tuple[float, ...] = (0.0, 0.5, 1.0, 2.0, 4.0)
    starting_cash: float = 100_000.0
    rf_annual: float = 0.04
    periods_per_year: float = 252.0
    mc_seed: int = 0
    benchmark_symbol: str = "SPY"

    def to_dict(self) -> dict:
        return {
            "study": "pairs_study_v1",
            "signal": "zscore_pairs (fixed 1:1 log-hedge - study v1; cointegration/Kalman are future versions)",
            "train_size": self.train_size,
            "test_size": self.test_size,
            "step": self.step,
            "top_n": self.top_n,
            "lookback": self.lookback,
            "entry_z": self.entry_z,
            "exit_z": self.exit_z,
            "leg_weight": self.leg_weight,
            "rf_annual": self.rf_annual,
        }


@dataclass
class StitchedCurve:
    multiplier: float
    equity: list[tuple[datetime, float]] = field(default_factory=list)
    returns: list[float] = field(default_factory=list)

    @property
    def final_nav(self) -> float:
        return self.equity[-1][1]


@dataclass
class StudyResult:
    config: StudyConfig
    snapshot_id: str
    n_windows: int
    n_pairs_tested_per_window: int
    curves: dict[float, StitchedCurve]
    selected_by_window: list[tuple[int, tuple[tuple[str, str], ...]]]
    dsr: float
    dsr_inputs: dict


def _skewness(returns: Sequence[float]) -> float:
    r = np.asarray(returns, dtype=float)
    mu, sd = r.mean(), r.std(ddof=0)
    return float(np.mean((r - mu) ** 3) / sd**3) if sd > 0 else 0.0


def _kurtosis(returns: Sequence[float]) -> float:
    """Raw (non-excess) kurtosis — the PSR formula's convention (D86)."""
    r = np.asarray(returns, dtype=float)
    mu, sd = r.mean(), r.std(ddof=0)
    return float(np.mean((r - mu) ** 4) / sd**4) if sd > 0 else 3.0


def build_base_cost_stack(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]],
    actions: CorporateActions,
) -> CostStack:
    declared = {
        symbol: tuple(as_declared_dividends(divs, actions.splits_by_symbol.get(symbol, ())))
        for symbol, divs in actions.dividends_by_symbol.items()
    }
    return CostStack(
        trade_bricks=(
            IBKRCommission(),
            SqrtImpact(params_by_symbol=calibrate_impact_params(bars_by_symbol, volumes_by_symbol)),
            PercentOfNotionalSpread(bps=1.0),
        ),
        carry_bricks=(BorrowFee(annual_rate=0.0025),),
        portfolio_carry_bricks=(MarginInterest(annual_rate=0.06),),
        event_flow_bricks=(DividendFlow(dividends_by_symbol=declared),),
    )


def run_pairs_study(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]],
    actions: CorporateActions,
    registry: TrialRegistry,
    snapshot_id: str,
    config: StudyConfig = StudyConfig(),
    trial_id_prefix: str = "pairs-study-v1",
) -> StudyResult:
    if 1.0 not in config.multipliers:
        raise ValueError("multipliers must include 1.0 — the tearsheet and DSR are computed at real costs")

    execution_frame = {
        symbol: as_traded_from_adjusted(series, actions.splits_by_symbol.get(symbol, ()))
        for symbol, series in bars_by_symbol.items()
    }
    view_index = {
        symbol: {tb.timestamp: i for i, tb in enumerate(series)} for symbol, series in bars_by_symbol.items()
    }
    base_stack = build_base_cost_stack(bars_by_symbol, volumes_by_symbol, actions)
    splits = {s: list(v) for s, v in actions.splits_by_symbol.items() if v}
    instruments = {symbol: Equity(symbol=symbol) for symbol in bars_by_symbol}

    windows = list(
        walk_forward_windows(bars_by_symbol, config.train_size, config.test_size, config.step)
    )
    if not windows:
        raise ValueError("no walk-forward windows fit the data — check sizes vs series length")

    selected_by_window: list[tuple[int, tuple[tuple[str, str], ...]]] = []
    n_tested = 0
    curves = {m: StitchedCurve(multiplier=m) for m in config.multipliers}
    capital = {m: config.starting_cash for m in config.multipliers}

    for window in windows:
        selection = select_pairs(window.train_views, top_n=config.top_n)
        n_tested = selection.n_pairs_tested
        selected_by_window.append((window.index, selection.ranked_pairs))
        legs = sorted({s for pair in selection.ranked_pairs for s in pair})

        # Warm-up prefix (D89): last `lookback` TRAIN bars prepended, both frames.
        test_ts = [tb.timestamp for tb in next(iter(window.test_bars_by_instrument.values()))]
        run_bars, run_views = {}, {}
        for symbol in legs:
            first_test_i = view_index[symbol][test_ts[0]]
            lo = first_test_i - config.lookback
            hi = first_test_i + len(test_ts)
            run_views[symbol] = list(bars_by_symbol[symbol][lo:hi])
            run_bars[symbol] = list(execution_frame[symbol][lo:hi])

        for m in config.multipliers:
            strategies = [
                ZScorePairsStrategy(
                    strategy_id=f"pair-{a}-{b}",
                    instrument_a=a,
                    instrument_b=b,
                    lookback=config.lookback,
                    entry_z=config.entry_z,
                    exit_z=config.exit_z,
                    leg_weight=config.leg_weight,
                )
                for a, b in selection.ranked_pairs
            ]
            result = run_backtest(
                bars_by_instrument=run_bars,
                instruments=instruments,
                strategies=strategies,
                cost_stack=scaled_cost_stack(base_stack, m),
                allocator=ConstantSplitAllocator(),
                starting_cash=capital[m],
                splits_by_instrument=splits,
                view_bars_by_instrument=run_views,
            )

            # Stitch: equity from the last prefix bar onward (flat through the
            # prefix by the strategy's warm-up guard), returns over test bars only.
            test_curve = result.equity_curve[config.lookback - 1 :]
            navs = [nav for _, nav in test_curve]
            window_returns = [b / a - 1.0 for a, b in zip(navs, navs[1:])]
            curves[m].equity.extend(test_curve[1:])
            curves[m].returns.extend(window_returns)
            capital[m] = result.final_nav

            window_sharpe = (
                sharpe(window_returns, config.rf_annual, config.periods_per_year)
                if len(set(window_returns)) > 1
                else 0.0
            )
            registry.add_trial(
                trial_id=f"{trial_id_prefix}-{m}x-w{window.index:02d}",
                config={**config.to_dict(), "cost_multiplier": m, "window": window.index,
                        "pairs": [list(p) for p in selection.ranked_pairs]},
                params={"n_pairs_tested": selection.n_pairs_tested},
                metrics={
                    "final_nav": result.final_nav,
                    "window_sharpe_daily": window_sharpe if np.isfinite(window_sharpe) else 0.0,
                    "num_fills": len(result.fills),
                },
                snapshot_id=snapshot_id,
                seed=config.mc_seed,
            )

    stitched_1x = curves[1.0]
    dsr_inputs = {
        "observed_sr_daily": sharpe(stitched_1x.returns, config.rf_annual, config.periods_per_year)
        / np.sqrt(config.periods_per_year),
        "t": len(stitched_1x.returns),
        "skew": _skewness(stitched_1x.returns),
        "kurt": _kurtosis(stitched_1x.returns),
    }
    dsr = deflated_sharpe_from_trials(
        registry,
        "window_sharpe_daily",
        sr=dsr_inputs["observed_sr_daily"],
        t=dsr_inputs["t"],
        skew=dsr_inputs["skew"],
        kurt=dsr_inputs["kurt"],
    )

    return StudyResult(
        config=config,
        snapshot_id=snapshot_id,
        n_windows=len(windows),
        n_pairs_tested_per_window=n_tested,
        curves=curves,
        selected_by_window=selected_by_window,
        dsr=dsr,
        dsr_inputs=dsr_inputs,
    )


def render_study_sweep_table(result: StudyResult) -> str:
    lines = ["| Cost multiplier | Final NAV | Net P&L | Return | Max drawdown |", "|---|---|---|---|---|"]
    start = result.config.starting_cash
    for m in result.config.multipliers:
        curve = result.curves[m]
        pnl = curve.final_nav - start
        lines.append(
            f"| {m:g}× | {curve.final_nav:,.2f} | {pnl:+,.2f} | {pnl / start:+.2%} | "
            f"{max_drawdown(curve.equity):.2%} |"
        )
    return "\n".join(lines)


def render_study_tearsheet(
    result: StudyResult, benchmark_returns_by_date: Mapping[datetime, float]
) -> str:
    curve = result.curves[1.0]
    benchmark = [benchmark_returns_by_date[ts] for ts, _ in curve.equity if ts in benchmark_returns_by_date]
    returns = [r for (ts, _), r in zip(curve.equity, curve.returns) if ts in benchmark_returns_by_date]
    return render_metrics_table(
        returns,
        rf_annual=result.config.rf_annual,
        periods_per_year=result.config.periods_per_year,
        equity_curve=curve.equity,
        benchmark_returns=benchmark,
        mc_seed=result.config.mc_seed,
    )

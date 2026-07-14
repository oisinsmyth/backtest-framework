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
from ..config.cost_stack import StackDataContext, build_cost_stack
from ..costs.scaling import scaled_cost_stack
from ..costs.stack import CostStack
from ..data.bars import TimestampedBar
from ..data.corporate_actions import CorporateActions, as_traded_from_adjusted
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
    impact_calibration: str = "full_sample"
    """How SqrtImpact's σ/ADV are estimated (D102): "full_sample" is the original,
    documented look-ahead in cost parameters (D66/D70); "train_window" recalibrates
    per walk-forward window from that window's TRAIN slice only (D44-compliant)."""

    def cost_stack_config(self) -> dict:
        """The declarative description of the study's real cost stack (D102) — the
        SAME dict `build_cost_stack` consumes, so what the registry hashes is what
        ran, not a free-hand description."""
        return {
            "trade_bricks": [
                {"type": "ibkr_commission"},
                {"type": "sqrt_impact", "coefficient": 1.0, "calibration": self.impact_calibration},
                {"type": "percent_spread", "bps": 1.0},
            ],
            "carry_bricks": [{"type": "borrow_fee", "annual_rate": 0.0025}],
            "portfolio_carry_bricks": [{"type": "margin_interest", "annual_rate": 0.06}],
            "event_flow_bricks": [{"type": "dividend_flow", "source": "snapshot_declared"}],
        }

    def to_dict(self) -> dict:
        """EVERY field that determines the result (D102 — the audit found
        starting_cash and multipliers missing, so two different experiments could
        hash identically), plus the declarative stack description."""
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
            "multipliers": list(self.multipliers),
            "starting_cash": self.starting_cash,
            "rf_annual": self.rf_annual,
            "periods_per_year": self.periods_per_year,
            "mc_seed": self.mc_seed,
            "benchmark_symbol": self.benchmark_symbol,
            "impact_calibration": self.impact_calibration,
            "cost_stack": self.cost_stack_config(),
        }

    @classmethod
    def from_dict(cls, config: dict) -> "StudyConfig":
        """Rebuild a StudyConfig from a logged trial's config dict — the study-level
        reproducibility loop (D35/D102): config → registry → reload → re-run.
        Extra keys the study logs per trial (cost_multiplier, window, selector,
        pairs, ...) are ignored; a logged cost_stack that does not match what this
        config would rebuild is a loud error, never silently overridden."""
        field_names = (
            "train_size", "test_size", "step", "top_n", "lookback", "entry_z", "exit_z",
            "leg_weight", "starting_cash", "rf_annual", "periods_per_year", "mc_seed",
            "benchmark_symbol", "impact_calibration",
        )
        kwargs = {name: config[name] for name in field_names if name in config}
        if "multipliers" in config:
            kwargs["multipliers"] = tuple(config["multipliers"])
        rebuilt = cls(**kwargs)
        if "cost_stack" in config and config["cost_stack"] != rebuilt.cost_stack_config():
            raise ValueError(
                "logged cost_stack config does not match what this StudyConfig rebuilds — "
                "the trial was run with a non-default stack this loader cannot reproduce (D102)"
            )
        return rebuilt


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
    dsr: float | None
    """None when the run was executed with compute_dsr=False (D98) — e.g. capacity
    levels sharing a registry, where a per-level DSR over the mixed pool would be
    meaningless (audit F9)."""
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
    """The study's real cost stack, built from its own declarative description
    (D102) — construction and the logged config dict share one source of truth."""
    return build_cost_stack(
        StudyConfig().cost_stack_config(),
        StackDataContext(bars_by_symbol=bars_by_symbol, volumes_by_symbol=volumes_by_symbol, actions=actions),
    )


def run_pairs_study(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]],
    actions: CorporateActions,
    registry: TrialRegistry,
    snapshot_id: str,
    config: StudyConfig = StudyConfig(),
    trial_id_prefix: str = "pairs-study-v1",
    selector=None,
    strategy_factory=None,
    base_stack: CostStack | None = None,
    compute_dsr: bool = True,
) -> StudyResult:
    """`selector`, when given, replaces the default Gatev top-N selection (D92): any
    callable `(views, top_n) -> PairSelection`. None preserves study v1's behavior
    exactly — v1 stays byte-reproducible. If the selector exposes `.name` /
    `.last_details`, they're logged into each trial's config.

    `strategy_factory`, when given, replaces the default ZScorePairsStrategy
    construction (D94): any callable `(pair, strategy_id, config, details) ->
    Strategy`, called once per (window, multiplier, pair) so each run gets fresh
    instances (D68 — strategies hold mutable state). `details` is the pair's entry
    from the selector's `last_details` (e.g. its fitted β), or None when the
    selector publishes none. None preserves v1/v2 behavior exactly.

    `base_stack`, when given, replaces the internally built real cost stack (D95 —
    the capacity study injects a recording wrapper here). None builds
    `build_base_cost_stack` exactly as before; v1/v2/v3 stay byte-reproducible.

    `compute_dsr=False` skips the registry-fed DSR and returns `dsr=None` (D98):
    capacity/gross-sweep levels share one registry, so a per-level DSR over the
    accumulated pool would be meaningless. `dsr_inputs` (the observed stitched SR,
    T, skew, kurtosis) is still populated — it's pure arithmetic on this run.

    DSR trial pool and units (D98, fixing audit F1/F8): every trial logs
    `window_sharpe_daily` in per-period (DAILY, non-annualized) units — the same
    units as the observed SR handed to the PSR — and the DSR pool is this study's
    1× trials only: the same window re-run at a scaled cost multiplier is a
    sensitivity point, not an additional independent trial. A 1× window with no
    return variation has no defined Sharpe estimate; rather than impute one (the
    old code logged 0.0), the study fails loudly."""
    if 1.0 not in config.multipliers:
        raise ValueError("multipliers must include 1.0 — the tearsheet and DSR are computed at real costs")

    execution_frame = {
        symbol: as_traded_from_adjusted(series, actions.splits_by_symbol.get(symbol, ()))
        for symbol, series in bars_by_symbol.items()
    }
    view_index = {
        symbol: {tb.timestamp: i for i, tb in enumerate(series)} for symbol, series in bars_by_symbol.items()
    }
    per_window_stack = config.impact_calibration == "train_window"
    if per_window_stack and base_stack is not None:
        raise ValueError(
            "impact_calibration='train_window' cannot be combined with an injected "
            "base_stack — recorder/scaling wrappers wrap one stack instance, and the "
            "per-window rebuild would bypass them (D102)"
        )
    if base_stack is None and not per_window_stack:
        base_stack = build_cost_stack(
            config.cost_stack_config(),
            StackDataContext(
                bars_by_symbol=bars_by_symbol, volumes_by_symbol=volumes_by_symbol, actions=actions
            ),
        )
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

    select = selector if selector is not None else select_pairs
    selector_name = getattr(selector, "name", "gatev_top_n")

    for window in windows:
        selection = select(window.train_views, config.top_n)
        selection_details = list(getattr(selector, "last_details", []) or [])
        details_by_pair = {tuple(d["pair"]): d for d in selection_details if "pair" in d}
        n_tested = selection.n_pairs_tested
        selected_by_window.append((window.index, selection.ranked_pairs))
        legs = sorted({s for pair in selection.ranked_pairs for s in pair})

        # Warm-up prefix (D89): last `lookback` TRAIN bars prepended, both frames.
        # The slicing below indexes each symbol's OWN series and assumes it carries
        # the same bar grid as the aligned universe inside the window's span — a
        # symbol with extra or missing bars there would silently shorten the run
        # through the engine's inner join. Assert the assumption loudly (D99).
        test_ts = [tb.timestamp for tb in next(iter(window.test_bars_by_instrument.values()))]
        run_bars, run_views = {}, {}
        reference_ts: list | None = None
        for symbol in legs:
            first_test_i = view_index[symbol][test_ts[0]]
            lo = first_test_i - config.lookback
            if lo < 0:
                raise ValueError(
                    f"warm-up prefix needs {config.lookback} bars before window "
                    f"{window.index}'s first test bar, but {symbol} has only {first_test_i}"
                )
            hi = first_test_i + len(test_ts)
            run_views[symbol] = list(bars_by_symbol[symbol][lo:hi])
            run_bars[symbol] = list(execution_frame[symbol][lo:hi])
            sliced_ts = [tb.timestamp for tb in run_views[symbol]]
            if sliced_ts[config.lookback :] != test_ts:
                raise ValueError(
                    f"{symbol} carries a different bar grid inside window {window.index}'s "
                    "test span than the aligned universe — clean/align the fixture first (D99)"
                )
            if reference_ts is None:
                reference_ts = sliced_ts
            elif sliced_ts != reference_ts:
                raise ValueError(
                    f"{symbol}'s warm-up prefix timestamps differ from {legs[0]}'s in window "
                    f"{window.index} — the legs would inner-join to a shorter warm-up (D99)"
                )

        if per_window_stack:
            # D102: rebuild the stack from THIS window's train slice only, through
            # the same declarative config path — sqrt-impact σ/ADV estimation obeys
            # D44's no-test-window-data rule instead of D66's full-sample look-ahead.
            train_slice_bars, train_slice_volumes = {}, {}
            for symbol in legs:
                first_test_i = view_index[symbol][test_ts[0]]
                train_lo = first_test_i - config.train_size
                train_slice_bars[symbol] = list(bars_by_symbol[symbol][train_lo:first_test_i])
                train_slice_volumes[symbol] = list(volumes_by_symbol[symbol][train_lo:first_test_i])
            window_stack = build_cost_stack(
                config.cost_stack_config(),
                StackDataContext(
                    bars_by_symbol=train_slice_bars,
                    volumes_by_symbol=train_slice_volumes,
                    actions=actions,
                ),
            )
        else:
            window_stack = base_stack

        for m in config.multipliers:
            if strategy_factory is not None:
                strategies = [
                    strategy_factory((a, b), f"pair-{a}-{b}", config, details_by_pair.get((a, b)))
                    for a, b in selection.ranked_pairs
                ]
            else:
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
                cost_stack=scaled_cost_stack(window_stack, m),
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

            # D98 (audit F1/F8): the logged Sharpe is DAILY (per-period), the same
            # units as the observed SR the PSR consumes — sharpe() annualizes, so
            # divide the √periods factor back out. A window with no return
            # variation has no defined Sharpe estimate; imputing 0.0 (the old
            # behaviour) silently distorted V[{SRn}], so the metric is omitted —
            # and if that happens on a 1× trial the DSR pool would be quietly
            # short, which is a loud error instead.
            metrics = {
                "final_nav": result.final_nav,
                "num_fills": len(result.fills),
                "window_traded": bool(result.fills),
            }
            if len(set(window_returns)) > 1:
                metrics["window_sharpe_daily"] = sharpe(
                    window_returns, config.rf_annual, config.periods_per_year
                ) / np.sqrt(config.periods_per_year)
            elif m == 1.0 and compute_dsr:
                raise ValueError(
                    f"window {window.index} produced no return variation at 1× costs — "
                    "its Sharpe estimate is undefined, so the DSR pool cannot be built "
                    "honestly. Re-run with compute_dsr=False or adjust the config (D98)."
                )
            registry.add_trial(
                trial_id=f"{trial_id_prefix}-{m}x-w{window.index:02d}",
                config={**config.to_dict(), "cost_multiplier": m, "window": window.index,
                        "selector": selector_name,
                        "selection_details": selection_details,
                        "pairs": [list(p) for p in selection.ranked_pairs]},
                params={"n_pairs_tested": selection.n_pairs_tested},
                metrics=metrics,
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
    if compute_dsr:
        # D98: the DSR pool is THIS study's 1× trials — identity/config-based
        # selection, never presence-of-metric (that would silently shrink N).
        def _in_pool(trial) -> bool:
            return (
                trial.trial_id.startswith(f"{trial_id_prefix}-")
                and trial.config.get("cost_multiplier") == 1.0
            )

        pool = [t.metrics["window_sharpe_daily"] for t in registry.all_trials() if _in_pool(t)]
        dsr_inputs["n_trials"] = len(pool)
        dsr_inputs["var_trials_daily"] = float(np.var(pool, ddof=1)) if len(pool) > 1 else float("nan")
        dsr = deflated_sharpe_from_trials(
            registry,
            "window_sharpe_daily",
            sr=dsr_inputs["observed_sr_daily"],
            t=dsr_inputs["t"],
            skew=dsr_inputs["skew"],
            kurt=dsr_inputs["kurt"],
            include=_in_pool,
        )
    else:
        dsr = None

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

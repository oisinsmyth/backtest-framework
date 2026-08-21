"""Breakout study harness (D109–D114): walk-forward, cost-tiered, plateau-swept,
logged and DSR-adjusted.

Study glue only — every load-bearing piece is a gate-tested framework component:
`walk_forward_windows` (D85), `run_backtest` with `fill_timing="next_open"` (D103),
`build_cost_stack` from a declarative config (D102), `TrialRegistry` (D20),
`deflated_sharpe_from_trials` (D86), `analytics.metrics` (D80).

## Why one CONTINUOUS out-of-sample run instead of chained windows (D113)

The pairs study runs each walk-forward window as its own backtest and chains capital
window to window. For a mean-reverting strategy whose trades last days, the seam is
cheap. For a trend follower whose trades last weeks-to-months it is not: every window
boundary would force the book flat, hand back a free liquidation with no exit cost, and
require a brand-new breakout before the trend could be re-entered — an artifact worth
several percent a year, in an unknown direction, on a study whose whole question is
whether a few tens of basis points of fees matter.

So each (symbol, variant, cost tier) is ONE continuous backtest over the union of the
walk-forward test windows. The walk-forward structure is still what defines the study:

- the out-of-sample span starts exactly where window 0's TRAINING slice ends, so no OOS
  bar is ever inside any training slice;
- per-window returns are sliced out of the continuous stream for per-window trial rows
  and per-window Sharpes;
- anything FITTED is fitted on a training slice only, and applied to that window's test
  bars via a parameter SCHEDULE keyed on absolute bar index (`ScheduledBreakout`), so
  parameters change at window boundaries exactly as walk-forward requires while the
  POSITION carries across the boundary the way a real book would.

The warm-up prefix is exactly `strategy.warm_up_bars()` bars, taken from inside window
0's training slice. That length is chosen so the strategy's own warm-up guard keeps it
flat for the entire prefix — it cannot trade before the first OOS bar, so no in-sample
P&L can leak into the reported curve. That is checked at runtime, not assumed.

## Costs (D114)

The tiers model an EXCHANGE FEE and nothing else: one `percent_spread` brick per tier,
no commission, no bid/ask spread, no market impact, no funding. That makes every number
here optimistic, and the report says so. It is the right scope for the question asked
("does the maker/taker difference decide viability?") and the wrong scope for "what
would this have actually earned".
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from ..analytics.metrics import max_drawdown, sharpe
from ..config.cost_stack import StackDataContext, build_cost_stack
from ..costs.stack import CostStack
from ..data.bars import TimestampedBar
from ..data.corporate_actions import CorporateActions
from ..engine.allocator import ConstantSplitAllocator
from ..engine.backtest import BacktestResult, run_backtest
from ..engine.dataview import DataView
from ..engine.strategy import ScheduledWeightStrategy
from ..instruments.base import Instrument
from ..instruments.equity import Equity
from ..pipeline.sizing import TargetWeight
from ..registry.trial_registry import TrialRegistry
from ..strategies.breakout import BreakoutStrategy, build_breakout_strategy
from ..validation.dsr import deflated_sharpe_from_trials
from ..validation.walk_forward import walk_forward_windows
from .trade_diagnostics import (
    DiagnosticsSummary,
    TradeEpisode,
    breadth_series,
    extract_episodes,
    summarise,
    trigger_features,
)

CRYPTO_QUANTITY_PRECISION = 8
"""BTC/ETH are traded as `Equity(quantity_precision=8)` (D108): spot crypto, long only,
never levered, so the equity instrument's semantics (signed notional, full-notional
margin) are exactly right and its 8-dp rounding is the crypto lot size. A dedicated
CryptoInstrument with a funding-rate carry brick is Step 10's deferred job (D14) and
would buy this study nothing — a long-only spot book pays no funding."""


# ---------------------------------------------------------------------- cost tiers


@dataclass(frozen=True)
class CostTier:
    """A crypto exchange fee tier. `role` is a label, not a mechanism: whether a
    breakout entry can realistically be a MAKER fill is a question about order
    placement the bar-level simulator cannot answer, and the report treats the maker
    tiers as a lower bound rather than an achievable execution (D114)."""

    name: str
    fee_bps: float
    role: str
    borrow_annual_rate: float = 0.0
    """Cost of borrowing the coin to sell it short, per year (D169).

    Zero for the long book, where it is not merely negligible but structurally absent —
    a long spot position borrows nothing, and `BorrowFee` charges only the short side of
    a signed notional anyway. Non-zero for the short book, where assuming free shorts is
    the single most result-corrupting choice available: the borrow accrues on ~100% of
    NAV for the entire life of every trade, and D124 made exactly this point for the
    pairs book's short leg."""

    def cost_stack_config(self) -> dict[str, Any]:
        # The borrow brick is emitted ONLY when the rate is non-zero, so every long-side
        # tier hashes exactly as it did before the short book existed (D166's rule).
        carry_bricks: list[dict[str, Any]] = []
        if self.borrow_annual_rate:
            carry_bricks.append(
                {"type": "borrow_fee", "annual_rate": self.borrow_annual_rate}
            )
        return {
            "trade_bricks": [{"type": "percent_spread", "bps": self.fee_bps}],
            "carry_bricks": carry_bricks,
            "portfolio_carry_bricks": [],
            "event_flow_bricks": [],
        }

    def build(self) -> CostStack:
        return build_cost_stack(
            self.cost_stack_config(),
            StackDataContext(bars_by_symbol={}, volumes_by_symbol={}, actions=CorporateActions()),
        )


DEFAULT_TIERS: tuple[CostTier, ...] = (
    CostTier("maker_0bp", 0.0, "maker"),
    CostTier("maker_10bp", 10.0, "maker"),
    CostTier("maker_25bp", 25.0, "maker"),
    CostTier("taker_40bp", 40.0, "taker"),
)

SHORT_BORROW_ANNUAL_RATE = 0.10
"""10%/yr, the same rate D124 pinned for the crypto pairs book's short leg: mid-range
for BTC/ETH spot margin borrow on the major venues over the sample. Not a free parameter
and not swept — it is a stated cost, and the short book is not run without it."""

SHORT_TIERS: tuple[CostTier, ...] = tuple(
    CostTier(t.name, t.fee_bps, t.role, borrow_annual_rate=SHORT_BORROW_ANNUAL_RATE)
    for t in DEFAULT_TIERS
)
"""The same four fee tiers as the long book, so the fee dimension is directly
comparable, plus the borrow every short position actually pays."""
REFERENCE_TIER = "taker_40bp"
"""The tier the headline verdict is read at: a market order into a breakout is a taker
fill, so this is the honest default and the maker tiers are the sensitivity."""


# -------------------------------------------------------------------------- config


@dataclass(frozen=True)
class BreakoutStudyConfig:
    train_size: int = 252
    test_size: int = 63
    step: int = 63
    starting_cash: float = 100_000.0
    rf_annual: float = 0.04
    periods_per_year: float = 365.0
    """365, not 252 — crypto trades every calendar day (D17's rule, applied via the
    caller since the Instrument protocol carries no calendar method)."""
    fill_timing: str = "next_open"
    whipsaw_bars: int = 3
    seed: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "study": "breakout_long_flat_v1",
            "train_size": self.train_size,
            "test_size": self.test_size,
            "step": self.step,
            "starting_cash": self.starting_cash,
            "rf_annual": self.rf_annual,
            "periods_per_year": self.periods_per_year,
            "fill_timing": self.fill_timing,
            "whipsaw_bars": self.whipsaw_bars,
            "seed": self.seed,
        }


# ------------------------------------------------------------- scheduled parameters


@dataclass
class ScheduledBreakout:
    """A BreakoutStrategy whose configuration swaps at pre-computed bar indices, with
    position state carried across the swap (D113).

    This is how walk-forward parameter selection reaches a continuous run: the schedule
    is `[(start_index, strategy_config), ...]` in absolute run-series indices, every
    entry fitted on that window's TRAINING slice only, and the strategy simply looks up
    which configuration is active on the current bar. A fixed-parameter variant is the
    one-entry case.

    Warm-up is the MAXIMUM across every scheduled configuration, so a later window with
    a longer lookback can never find itself short of history mid-run."""

    strategy_id: str
    instrument_id: str
    schedule: tuple[tuple[int, dict[str, Any]], ...]

    _active_from: int = field(default=-1, init=False, repr=False)
    _inner: BreakoutStrategy | None = field(default=None, init=False, repr=False)
    _warm_up: int = field(default=0, init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.schedule:
            raise ValueError("schedule must contain at least one (start_index, config) entry")
        starts = [start for start, _ in self.schedule]
        if starts != sorted(starts) or len(set(starts)) != len(starts):
            raise ValueError(f"schedule start indices must be strictly increasing, got {starts}")
        if starts[0] != 0:
            raise ValueError(f"schedule must begin at index 0, got {starts[0]}")
        self._warm_up = max(
            build_breakout_strategy(config, self.strategy_id, self.instrument_id).warm_up_bars()
            for _, config in self.schedule
        )

    def warm_up_bars(self) -> int:
        return self._warm_up

    def _config_for(self, index: int) -> tuple[int, dict[str, Any]]:
        active = self.schedule[0]
        for start, config in self.schedule:
            if start <= index:
                active = (start, config)
            else:
                break
        return active

    def generate_targets(self, views: Mapping[str, DataView]) -> list[TargetWeight]:
        view = views[self.instrument_id]
        start, config = self._config_for(view.current_index)
        if self._inner is None or start != self._active_from:
            rebuilt = build_breakout_strategy(config, self.strategy_id, self.instrument_id)
            if self._inner is not None:
                # Carry the open position across the parameter swap — the whole point
                # of running continuously (D113). A rebuilt strategy that forgot it was
                # long would silently flatten the book at every window boundary.
                rebuilt._state = self._inner._state
                rebuilt._held_weight = self._inner._held_weight
            self._inner, self._active_from = rebuilt, start
        # The inner strategy's own warm-up guard is keyed on its own requirement; this
        # wrapper's is the max across the schedule, so enforce the stricter one here.
        if view.current_index < self._warm_up:
            return [
                TargetWeight(strategy_id=self.strategy_id, instrument_id=self.instrument_id, weight=0.0)
            ]
        return self._inner.generate_targets(views)


# ------------------------------------------------------------------------ variants

StrategyConfigFor = Callable[[Sequence[TimestampedBar], CostTier, "BreakoutStudyConfig"], dict]


@dataclass(frozen=True)
class Variant:
    """One evaluated strategy configuration.

    `fixed_config` is a strategy config used unchanged in every window. `fit` is the
    alternative: a callable handed ONLY that window's training bars, returning the
    config to use for that window's test bars. Exactly one of the two must be set —
    a variant that is both fitted and fixed is a contradiction, not a default."""

    name: str
    group: str
    """Which table the variant belongs to in the report: "plateau", "filter",
    "sizing", or "selection"."""
    fixed_config: dict[str, Any] | None = None
    fit: StrategyConfigFor | None = None
    fit_description: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if (self.fixed_config is None) == (self.fit is None):
            raise ValueError(f"variant {self.name!r}: set exactly one of fixed_config or fit")

    def describe(self) -> dict[str, Any]:
        return {
            "variant": self.name,
            "group": self.group,
            "fixed_config": self.fixed_config,
            "fit": self.fit_description,
        }


INVERSE_VOL_AT_ENTRY = {
    "type": "inverse_vol_weight",
    "target_annual_vol": 0.40,
    "vol_window": 20,
    "periods_per_year": 365.0,
    "max_weight": 1.0,
    "rebalance": "at_entry",
}
"""The study's default sizing (D110). 40% target against BTC's ~68% / ETH's ~87%
realized annual vol means the cap binds rarely and the typical weight is ~0.5, i.e. the
strategy is usually HALF invested when long — that is what inverse-vol sizing does to a
high-vol instrument, and it is a first-order driver of every return below."""


def breakout_config(
    n_entry: int = 40,
    n_exit: int = 10,
    weight_source: dict[str, Any] | None = None,
    filters: Sequence[dict[str, Any]] = (),
    direction: str = "long",
    exit_rules: Sequence[dict[str, Any]] = (),
) -> dict[str, Any]:
    """`direction` and `exit_rules` are emitted only when they differ from the long-flat
    defaults, so every config this produced before the short side existed still hashes
    exactly as it did (D166/D169)."""
    config: dict[str, Any] = {
        "type": "breakout_long_flat",
        "n_entry": n_entry,
        "n_exit": n_exit,
        "weight_source": dict(weight_source or INVERSE_VOL_AT_ENTRY),
        "filters": [dict(f) for f in filters],
    }
    if direction != "long":
        config["direction"] = direction
    if exit_rules:
        config["exit_rules"] = [dict(r) for r in exit_rules]
    return config


PLATEAU_N_ENTRY: tuple[int, ...] = (20, 30, 40, 55)
PLATEAU_N_EXIT: tuple[int, ...] = (5, 10, 20)
BASELINE_N_ENTRY, BASELINE_N_EXIT = 40, 10


def plateau_variants() -> list[Variant]:
    """The full sweep surface. `n_exit > n_entry` combinations are not evaluated — the
    strategy refuses to construct them (the hysteresis band would be empty), so they
    are absent from the grid rather than silently skipped inside it."""
    variants = []
    for n_entry in PLATEAU_N_ENTRY:
        for n_exit in PLATEAU_N_EXIT:
            if n_exit > n_entry:
                continue
            variants.append(
                Variant(
                    name=f"plateau_{n_entry}_{n_exit}",
                    group="plateau",
                    fixed_config=breakout_config(n_entry=n_entry, n_exit=n_exit),
                )
            )
    return variants


def filter_variants() -> list[Variant]:
    """Each filter added ONE AT A TIME on top of the baseline — never stacked, so every
    row's delta against the baseline prices exactly one component."""
    def baseline_plus(*filters: dict[str, Any]) -> dict[str, Any]:
        return breakout_config(
            n_entry=BASELINE_N_ENTRY, n_exit=BASELINE_N_EXIT, filters=list(filters)
        )

    return [
        Variant("filter_debounce_m2", "filter",
                fixed_config=baseline_plus({"type": "consecutive_close", "m": 2})),
        Variant("filter_volcontract_0.8", "filter",
                fixed_config=baseline_plus(
                    {"type": "volatility_contraction", "threshold": 0.8,
                     "short_window": 20, "long_window": 100})),
        Variant("filter_volcontract_1.0", "filter",
                fixed_config=baseline_plus(
                    {"type": "volatility_contraction", "threshold": 1.0,
                     "short_window": 20, "long_window": 100})),
        Variant("filter_trend_gate_200", "filter",
                fixed_config=baseline_plus({"type": "trend_gate", "sma_window": 200})),
        # The filter the original brief specified and D111 recorded as BLOCKED. D168
        # closed the blocker, so it now faces exactly the same keep/drop rule as the
        # other four rather than being reported as an absence.
        Variant("filter_volume_1.5x", "filter",
                fixed_config=baseline_plus(
                    {"type": "volume_confirmation", "multiple": 1.5, "window": 20})),
    ]


def sizing_variants() -> list[Variant]:
    def baseline_sized(weight_source: dict[str, Any]) -> dict[str, Any]:
        return breakout_config(
            n_entry=BASELINE_N_ENTRY, n_exit=BASELINE_N_EXIT, weight_source=weight_source
        )

    return [
        Variant("sizing_fixed_1.0", "sizing",
                fixed_config=baseline_sized({"type": "fixed_weight", "fraction": 1.0})),
        Variant("sizing_invvol_daily", "sizing",
                fixed_config=baseline_sized({**INVERSE_VOL_AT_ENTRY, "rebalance": "every_bar"})),
    ]


@dataclass
class InTrainGridSelector:
    """Picks (n_entry, n_exit) by backtesting the grid on the TRAINING slice only.

    Selection runs the same engine, the same cost stack, and the same strategy code
    that the test window will use — a training-window backtest, not a proxy score. The
    objective is the training slice's daily Sharpe; ties break on the lower n_entry
    then the lower n_exit, so the choice is deterministic and does not depend on dict
    ordering.

    `evaluations` counts every (window, combination) backtest run for selection. Those
    are in-sample fits, not out-of-sample trials — they belong in the multiplicity
    story (this many parameter settings were looked at) but NOT in the DSR trial pool,
    which is out-of-sample results only (D98)."""

    instruments: Mapping[str, Instrument]
    symbol: str
    study: BreakoutStudyConfig
    grid: tuple[tuple[int, int], ...]
    weight_source: dict[str, Any]
    evaluations: int = 0

    def __call__(
        self, train_bars: Sequence[TimestampedBar], tier: CostTier, study: BreakoutStudyConfig
    ) -> dict[str, Any]:
        stack = tier.build()
        best_score, best_key, best_config = -math.inf, None, None
        for n_entry, n_exit in self.grid:
            config = breakout_config(n_entry=n_entry, n_exit=n_exit, weight_source=self.weight_source)
            strategy = build_breakout_strategy(config, f"select-{self.symbol}", self.symbol)
            if len(train_bars) <= strategy.warm_up_bars() + 2:
                continue
            result = run_backtest(
                bars_by_instrument={self.symbol: list(train_bars)},
                instruments=self.instruments,
                strategies=[strategy],
                cost_stack=stack,
                allocator=ConstantSplitAllocator(),
                starting_cash=study.starting_cash,
                fill_timing=study.fill_timing,
            )
            self.evaluations += 1
            navs = [nav for _, nav in result.equity_curve[strategy.warm_up_bars() :]]
            returns = [b / a - 1.0 for a, b in zip(navs, navs[1:])]
            score = (
                sharpe(returns, study.rf_annual, study.periods_per_year)
                if len(set(returns)) > 1
                else -math.inf
            )
            key = (-score, n_entry, n_exit)
            if best_key is None or key < best_key:
                best_score, best_key, best_config = score, key, config
        if best_config is None:
            # No combination produced a scoreable training window (e.g. never traded).
            # Fall back to the a-priori baseline and say so, rather than picking the
            # first grid entry as if it had won something.
            return breakout_config(
                n_entry=BASELINE_N_ENTRY, n_exit=BASELINE_N_EXIT, weight_source=self.weight_source
            )
        return best_config


# ------------------------------------------------------------------------- results


@dataclass
class VariantResult:
    symbol: str
    variant: Variant
    tier: CostTier
    schedule: tuple[tuple[int, dict[str, Any]], ...]
    oos_equity: list[tuple[datetime, float]]
    oos_returns: list[float]
    window_sharpes_daily: dict[int, float]
    window_final_nav: dict[int, float]
    episodes: list[TradeEpisode]
    diagnostics: DiagnosticsSummary
    n_oos_bars: int

    @property
    def final_nav(self) -> float:
        return self.oos_equity[-1][1]

    @property
    def total_return(self) -> float:
        return self.final_nav / self.oos_equity[0][1] - 1.0

    def sharpe_annual(self, study: BreakoutStudyConfig) -> float:
        return sharpe(self.oos_returns, study.rf_annual, study.periods_per_year)

    def sharpe_daily(self, study: BreakoutStudyConfig) -> float:
        return self.sharpe_annual(study) / math.sqrt(study.periods_per_year)

    @property
    def max_drawdown(self) -> float:
        return max_drawdown(self.oos_equity)


@dataclass
class BenchmarkResult:
    symbol: str
    tier: CostTier
    oos_equity: list[tuple[datetime, float]]
    oos_returns: list[float]

    @property
    def total_return(self) -> float:
        return self.oos_equity[-1][1] / self.oos_equity[0][1] - 1.0

    @property
    def max_drawdown(self) -> float:
        return max_drawdown(self.oos_equity)

    def sharpe_annual(self, study: BreakoutStudyConfig) -> float:
        return sharpe(self.oos_returns, study.rf_annual, study.periods_per_year)


@dataclass
class SymbolResult:
    symbol: str
    n_windows: int
    oos_start: datetime
    oos_end: datetime
    n_oos_bars: int
    variants: dict[tuple[str, str], VariantResult]
    """(variant name, tier name) -> result."""
    benchmarks: dict[str, BenchmarkResult]
    """tier name -> buy-and-hold."""
    n_train_evaluations: int
    dsr_by_tier: dict[str, float]
    dsr_inputs_by_tier: dict[str, dict[str, float]]


@dataclass
class StudyResult:
    config: BreakoutStudyConfig
    snapshot_id: str
    tiers: tuple[CostTier, ...]
    variant_names: tuple[str, ...]
    by_symbol: dict[str, SymbolResult]

    @property
    def n_oos_trials(self) -> int:
        return sum(len(s.variants) for s in self.by_symbol.values())

    @property
    def n_train_evaluations(self) -> int:
        return sum(s.n_train_evaluations for s in self.by_symbol.values())


# ---------------------------------------------------------------------- the harness


def _instruments(symbol: str) -> dict[str, Instrument]:
    return {symbol: Equity(symbol=symbol, quantity_precision=CRYPTO_QUANTITY_PRECISION)}


def _window_spans(
    bars: Sequence[TimestampedBar], study: BreakoutStudyConfig
) -> list[tuple[int, int, int, int]]:
    """(window index, train start, test start, test end-exclusive) in absolute indices
    of `bars`. Derived from `walk_forward_windows` (never re-derived by hand) so the
    study and the framework's walk-forward machinery cannot drift apart."""
    symbol = "series"
    index_by_timestamp = {tb.timestamp: i for i, tb in enumerate(bars)}
    spans = []
    for window in walk_forward_windows(
        {symbol: bars}, study.train_size, study.test_size, study.step
    ):
        test_bars = window.test_bars_by_instrument[symbol]
        test_start = index_by_timestamp[test_bars[0].timestamp]
        test_end = index_by_timestamp[test_bars[-1].timestamp] + 1
        spans.append((window.index, test_start - study.train_size, test_start, test_end))
    return spans


def run_variant(
    bars: Sequence[TimestampedBar],
    symbol: str,
    variant: Variant,
    tier: CostTier,
    study: BreakoutStudyConfig,
    breadth: Mapping[datetime, float] | None = None,
    volumes: Sequence[float] | None = None,
) -> VariantResult:
    """`breadth` is F4's cross-sectional input, built once across the whole universe by
    `run_breakout_study`. None simply leaves F4 unavailable — features are diagnostics
    and never gate a run.

    `volumes` must align 1:1 with `bars` and is sliced to the run window alongside them
    (D168). A variant carrying a filter that requires volume will fail loudly if this is
    None, which is the intended behaviour — better than silently rejecting every entry."""
    spans = _window_spans(bars, study)
    if not spans:
        raise ValueError("no walk-forward windows fit the series — check sizes vs series length")
    oos_start, oos_end = spans[0][2], spans[-1][3]

    schedule: list[tuple[int, dict[str, Any]]] = []
    if variant.fixed_config is not None:
        schedule.append((0, variant.fixed_config))
    else:
        assert variant.fit is not None
        for _, train_start, test_start, _ in spans:
            train_bars = bars[train_start:test_start]
            config = variant.fit(train_bars, tier, study)
            if not schedule or schedule[-1][1] != config:
                # Schedule indices are relative to the RUN series, which starts at
                # oos_start - warm_up; the offset is applied after warm-up is known.
                schedule.append((test_start, config))
        if schedule[0][0] != oos_start:
            raise ValueError("fitted schedule must start at the first OOS window")

    warm_up = max(
        ScheduledBreakout(f"breakout-{symbol}", symbol, ((0, config),)).warm_up_bars()
        for _, config in schedule
    )
    run_start = oos_start - warm_up
    if run_start < 0:
        raise ValueError(
            f"variant {variant.name!r} needs {warm_up} warm-up bars before the first OOS bar at "
            f"index {oos_start}, but only {oos_start} are available — widen train_size or shorten "
            "the longest lookback"
        )
    run_bars = list(bars[run_start:oos_end])
    run_schedule = [(max(start - run_start, 0), config) for start, config in schedule]
    # A fitted schedule's first entry starts at oos_start, i.e. `warm_up` bars into the
    # run — but the wrapper requires an entry at index 0 so the warm-up bars have some
    # configuration to stand aside under. The first fitted config serves that role; it
    # governs only bars the strategy is provably flat through (asserted below).
    if run_schedule[0][0] != 0:
        run_schedule.insert(0, (0, run_schedule[0][1]))

    strategy = ScheduledBreakout(f"breakout-{symbol}", symbol, tuple(run_schedule))
    if strategy.warm_up_bars() != warm_up:
        raise ValueError("warm-up disagreement between probe and run strategy — refusing to run")

    # Sliced with exactly the same bounds as run_bars, so the two cannot drift apart.
    run_volumes = None if volumes is None else list(volumes[run_start:oos_end])
    result = run_backtest(
        bars_by_instrument={symbol: run_bars},
        instruments=_instruments(symbol),
        strategies=[strategy],
        cost_stack=tier.build(),
        allocator=ConstantSplitAllocator(),
        starting_cash=study.starting_cash,
        fill_timing=study.fill_timing,
        volumes_by_instrument=None if run_volumes is None else {symbol: run_volumes},
    )

    # The prefix is exactly warm_up bars long, so the strategy's own guard keeps it
    # flat throughout it. Assert rather than trust: an off-by-one here would leak
    # in-sample P&L into the reported OOS curve (D113).
    prefix_timestamps = {tb.timestamp for tb in run_bars[:warm_up]}
    leaked = [f for f in result.fills if f[0] in prefix_timestamps]
    if leaked:
        raise ValueError(
            f"variant {variant.name!r} traded {len(leaked)} time(s) during the warm-up prefix "
            f"(first at {leaked[0][0].isoformat()}) — in-sample P&L would leak into the OOS "
            "curve; the prefix length must equal the strategy's warm-up requirement (D113)"
        )

    oos_curve = result.equity_curve[warm_up:]
    if [ts for ts, _ in oos_curve] != [tb.timestamp for tb in bars[oos_start:oos_end]]:
        raise ValueError("OOS equity curve timestamps do not match the walk-forward test span")
    oos_returns = [b / a - 1.0 for (_, a), (_, b) in zip(oos_curve, oos_curve[1:])]

    index_in_oos = {ts: i for i, (ts, _) in enumerate(oos_curve)}
    window_sharpes: dict[int, float] = {}
    window_final_nav: dict[int, float] = {}
    for window_index, _, test_start, test_end in spans:
        lo = index_in_oos[bars[test_start].timestamp]
        hi = index_in_oos[bars[test_end - 1].timestamp]
        navs = [nav for _, nav in oos_curve[lo : hi + 1]]
        window_final_nav[window_index] = navs[-1]
        segment = [b / a - 1.0 for a, b in zip(navs, navs[1:])]
        if len(set(segment)) > 1:
            window_sharpes[window_index] = sharpe(
                segment, study.rf_annual, study.periods_per_year
            ) / math.sqrt(study.periods_per_year)

    episodes = extract_episodes(
        result,
        symbol,
        run_bars,
        features_at=lambda i: trigger_features(
            run_bars, i, breadth=breadth, volumes=run_volumes
        ),
    )
    oos_episodes = [e for e in episodes if e.entry_index >= warm_up]
    if len(oos_episodes) != len(episodes):
        raise ValueError("an episode opened inside the warm-up prefix — see the leak check above")
    diagnostics = summarise(
        oos_episodes,
        equity_curve=oos_curve,
        instrument_bars=list(bars[oos_start:oos_end]),
        n_oos_bars=len(oos_curve),
        whipsaw_bars=study.whipsaw_bars,
        periods_per_year=study.periods_per_year,
    )

    return VariantResult(
        symbol=symbol,
        variant=variant,
        tier=tier,
        schedule=tuple(schedule),
        oos_equity=list(oos_curve),
        oos_returns=oos_returns,
        window_sharpes_daily=window_sharpes,
        window_final_nav=window_final_nav,
        episodes=oos_episodes,
        diagnostics=diagnostics,
        n_oos_bars=len(oos_curve),
    )


def run_benchmark(
    bars: Sequence[TimestampedBar], symbol: str, tier: CostTier, study: BreakoutStudyConfig
) -> BenchmarkResult:
    """True buy-and-hold over the OOS span, on the SAME cost tier and the SAME fill
    timing as every strategy variant (D115).

    Computed directly rather than through the engine, and the reason is worth stating
    because it is the same effect that shows up in the strategy's own turnover: the
    sizing pipeline targets a WEIGHT, sized on the decision bar's close but filled at
    the next bar's open (D103). Whenever those two prices differ — a ~0.06% mean gap on
    daily crypto bars — a constant 100% weight is slightly off target on arrival and
    gets corrected on the following bar. That is correct behaviour for a weight-targeting
    strategy and wrong behaviour for a benchmark: buy-and-hold buys once and does
    nothing else. So the benchmark holds a fixed QUANTITY:

      buy at the second OOS bar's open (the earliest any decision made on the first OOS
      bar could fill), paying the tier's fee on the entry notional; hold to the end;
      mark at the final close with no forced liquidation — exactly as a strategy variant
      that ends long is marked.

    `tests/integration/test_breakout_study.py` cross-checks this against the engine-run
    constant-weight version so the two never drift silently apart."""
    spans = _window_spans(bars, study)
    oos_start, oos_end = spans[0][2], spans[-1][3]
    series = list(bars[oos_start:oos_end])
    if len(series) < 2:
        raise ValueError("buy-and-hold needs at least two OOS bars")

    instrument = _instruments(symbol)[symbol]
    stack = tier.build()
    entry_price = series[1].bar.open
    # Solve for the quantity whose notional plus its own fee exhausts starting cash.
    # The fee bricks in this study are proportional, so one Newton step is exact; the
    # loop keeps it correct if a non-proportional brick is ever added to a tier.
    quantity = instrument.tradeable_quantity(study.starting_cash / entry_price)
    for _ in range(8):
        cost = stack.trade_cost(instrument, quantity, entry_price)
        quantity = instrument.tradeable_quantity((study.starting_cash - cost) / entry_price)
    cost = stack.trade_cost(instrument, quantity, entry_price)
    cash = study.starting_cash - quantity * entry_price - cost

    equity = [(series[0].timestamp, study.starting_cash)]
    equity += [(tb.timestamp, cash + quantity * tb.bar.close) for tb in series[1:]]
    return BenchmarkResult(
        symbol=symbol,
        tier=tier,
        oos_equity=equity,
        oos_returns=[b / a - 1.0 for (_, a), (_, b) in zip(equity, equity[1:])],
    )


def run_benchmark_via_engine(
    bars: Sequence[TimestampedBar], symbol: str, tier: CostTier, study: BreakoutStudyConfig
) -> BenchmarkResult:
    """The engine-run constant-100%-weight version of buy-and-hold — kept as the
    cross-check on `run_benchmark`, not as the reported benchmark (see its docstring)."""
    spans = _window_spans(bars, study)
    oos_start, oos_end = spans[0][2], spans[-1][3]
    run_bars = list(bars[oos_start:oos_end])
    result = run_backtest(
        bars_by_instrument={symbol: run_bars},
        instruments=_instruments(symbol),
        # ScheduledWeightStrategy is a FROZEN dataclass, so its strategy_id is a
        # read-only attribute while the Strategy protocol declares a settable one —
        # the same protocol-variance trap audit F20 fixed on Instrument. Left as a
        # narrow ignore rather than edited: engine/strategy.py is an existing
        # interface and this study does not get to change one (flagged in
        # BREAKOUT_RESULTS.md's interface notes).
        strategies=[
            ScheduledWeightStrategy(  # type: ignore[list-item]
                strategy_id=f"buyhold-{symbol}", weights_by_instrument={symbol: [1.0]}
            )
        ],
        cost_stack=tier.build(),
        allocator=ConstantSplitAllocator(),
        starting_cash=study.starting_cash,
        fill_timing=study.fill_timing,
    )
    curve = result.equity_curve
    return BenchmarkResult(
        symbol=symbol,
        tier=tier,
        oos_equity=list(curve),
        oos_returns=[b / a - 1.0 for (_, a), (_, b) in zip(curve, curve[1:])],
    )


def default_variants(symbol: str, study: BreakoutStudyConfig) -> tuple[list[Variant], InTrainGridSelector]:
    grid = tuple(
        (n_entry, n_exit)
        for n_entry in PLATEAU_N_ENTRY
        for n_exit in PLATEAU_N_EXIT
        if n_exit <= n_entry
    )
    selector = InTrainGridSelector(
        instruments=_instruments(symbol),
        symbol=symbol,
        study=study,
        grid=grid,
        weight_source=dict(INVERSE_VOL_AT_ENTRY),
    )
    selected = Variant(
        name="selected_in_train",
        group="selection",
        fit=selector,
        fit_description={
            "selection": "in_train_grid",
            "objective": "training-window daily Sharpe",
            "grid": [list(pair) for pair in grid],
            "tie_break": "lower n_entry, then lower n_exit",
        },
    )
    return (
        plateau_variants() + filter_variants() + sizing_variants() + vol_target_variants() + [selected]
    ), selector


def run_breakout_study(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    registry: TrialRegistry,
    snapshot_id: str,
    volumes_by_symbol: Mapping[str, Sequence[float]] | None = None,
    study: BreakoutStudyConfig = BreakoutStudyConfig(),
    tiers: Sequence[CostTier] = DEFAULT_TIERS,
    trial_id_prefix: str = "breakout-v1",
    progress: Callable[[str], None] | None = None,
) -> StudyResult:
    """Runs every (symbol, variant, tier) combination, logs a variant-level trial row
    and one row per walk-forward window, and computes a DSR per (symbol, tier) whose
    trial pool is the variants evaluated at that tier.

    DSR pool choice (D116): Bailey & López de Prado's N is the number of CONFIGURATIONS
    tried, and that is what this study has a lot of — the pairs study's one-row-per-
    window pool answered a different question (it varied no parameters). So the pool
    here is every variant's out-of-sample daily Sharpe at one (symbol, tier), selected
    on identity fields in the config, never on presence of a metric (D98). Per-window
    rows carry `row_kind="window"` and are excluded by the same predicate."""
    by_symbol: dict[str, SymbolResult] = {}
    variant_names: tuple[str, ...] = ()

    # F4 is the one feature that needs more than the instrument's own bars, so it is
    # built once over the whole universe before any variant runs. Two instruments is
    # thin and known to be thin — BREAKOUT_REVERSAL_FEATURES.md predicts F4 is
    # underpowered until the universe grows, and the report says so.
    breadth = breadth_series(bars_by_symbol)

    for symbol, bars in bars_by_symbol.items():
        variants, selector = default_variants(symbol, study)
        variant_names = tuple(v.name for v in variants)
        spans = _window_spans(bars, study)
        oos_start, oos_end = spans[0][2], spans[-1][3]

        results: dict[tuple[str, str], VariantResult] = {}
        benchmarks: dict[str, BenchmarkResult] = {}
        for tier in tiers:
            benchmarks[tier.name] = run_benchmark(bars, symbol, tier, study)
            for variant in variants:
                if progress:
                    progress(f"{symbol} {tier.name} {variant.name}")
                result = run_variant(
                    bars, symbol, variant, tier, study, breadth=breadth,
                    volumes=None if volumes_by_symbol is None else volumes_by_symbol.get(symbol),
                )
                results[(variant.name, tier.name)] = result
                _log_trials(registry, result, study, snapshot_id, trial_id_prefix, spans, bars)

        dsr_by_tier, dsr_inputs_by_tier = {}, {}
        for tier in tiers:
            dsr, inputs = _dsr_for(registry, symbol, tier, study, results, trial_id_prefix)
            dsr_by_tier[tier.name] = dsr
            dsr_inputs_by_tier[tier.name] = inputs

        by_symbol[symbol] = SymbolResult(
            symbol=symbol,
            n_windows=len(spans),
            oos_start=bars[oos_start].timestamp,
            oos_end=bars[oos_end - 1].timestamp,
            n_oos_bars=oos_end - oos_start,
            variants=results,
            benchmarks=benchmarks,
            n_train_evaluations=selector.evaluations,
            dsr_by_tier=dsr_by_tier,
            dsr_inputs_by_tier=dsr_inputs_by_tier,
        )

    return StudyResult(
        config=study,
        snapshot_id=snapshot_id,
        tiers=tuple(tiers),
        variant_names=variant_names,
        by_symbol=by_symbol,
    )


def _log_trials(
    registry: TrialRegistry,
    result: VariantResult,
    study: BreakoutStudyConfig,
    snapshot_id: str,
    prefix: str,
    spans: Sequence[tuple[int, int, int, int]],
    bars: Sequence[TimestampedBar],
) -> None:
    base_config = {
        **study.to_dict(),
        "symbol": result.symbol,
        "tier": result.tier.name,
        "fee_bps": result.tier.fee_bps,
        "venue_role": result.tier.role,
        "cost_stack": result.tier.cost_stack_config(),
        **result.variant.describe(),
        "resolved_schedule": [[start, config] for start, config in result.schedule],
    }
    metrics = {
        "final_nav": result.final_nav,
        "total_return": result.total_return,
        "oos_sharpe_daily": result.sharpe_daily(study),
        "oos_sharpe_annual": result.sharpe_annual(study),
        "max_drawdown": result.max_drawdown,
        "num_fills": sum(e.n_fills for e in result.episodes),
        **result.diagnostics.to_metrics(),
    }
    registry.add_trial(
        trial_id=f"{prefix}-{result.symbol}-{result.tier.name}-{result.variant.name}",
        config={**base_config, "row_kind": "variant"},
        params={"n_oos_bars": result.n_oos_bars, "n_windows": len(spans)},
        metrics=metrics,
        snapshot_id=snapshot_id,
        seed=study.seed,
    )
    for window_index, _, test_start, test_end in spans:
        window_metrics: dict[str, Any] = {"window_final_nav": result.window_final_nav[window_index]}
        if window_index in result.window_sharpes_daily:
            window_metrics["window_sharpe_daily"] = result.window_sharpes_daily[window_index]
        registry.add_trial(
            trial_id=f"{prefix}-{result.symbol}-{result.tier.name}-{result.variant.name}-w{window_index:02d}",
            config={**base_config, "row_kind": "window", "window": window_index},
            params={
                "window_start": bars[test_start].timestamp.date().isoformat(),
                "window_end": bars[test_end - 1].timestamp.date().isoformat(),
            },
            metrics=window_metrics,
            snapshot_id=snapshot_id,
            seed=study.seed,
        )


def _dsr_for(
    registry: TrialRegistry,
    symbol: str,
    tier: CostTier,
    study: BreakoutStudyConfig,
    results: Mapping[tuple[str, str], VariantResult],
    prefix: str,
) -> tuple[float, dict[str, Any]]:
    at_tier = [r for (_, tier_name), r in results.items() if tier_name == tier.name]
    best = max(at_tier, key=lambda r: r.sharpe_daily(study))
    returns = np.asarray(best.oos_returns, dtype=float)
    mu, sd = returns.mean(), returns.std(ddof=0)
    inputs: dict[str, Any] = {
        "observed_sr_daily": best.sharpe_daily(study),
        "best_variant": best.variant.name,
        "t": len(returns),
        "skew": float(np.mean((returns - mu) ** 3) / sd**3) if sd > 0 else 0.0,
        "kurt": float(np.mean((returns - mu) ** 4) / sd**4) if sd > 0 else 3.0,
        "n_trials": len(at_tier),
    }

    def _in_pool(trial) -> bool:
        return (
            trial.config.get("row_kind") == "variant"
            and trial.config.get("symbol") == symbol
            and trial.config.get("tier") == tier.name
            and trial.trial_id.startswith(f"{prefix}-")
        )

    dsr = deflated_sharpe_from_trials(
        registry,
        "oos_sharpe_daily",
        sr=float(inputs["observed_sr_daily"]),
        t=int(inputs["t"]),
        skew=float(inputs["skew"]),
        kurt=float(inputs["kurt"]),
        include=_in_pool,
    )
    pool = [
        t.metrics["oos_sharpe_daily"] for t in registry.all_trials() if _in_pool(t)
    ]
    inputs["var_trials_daily"] = float(np.var(pool, ddof=1)) if len(pool) > 1 else float("nan")
    inputs["n_trials"] = len(pool)
    return dsr, inputs


# ------------------------------------------------------------------------ rendering


def _pct(x: float) -> str:
    return "n/a" if x != x else f"{x:+.2%}"


def _num(x: float, places: int = 2) -> str:
    return "n/a" if x != x else f"{x:.{places}f}"


def cagr(total_return: float, n_bars: int, periods_per_year: float) -> float:
    """Compound annual growth rate from a total return over `n_bars` bars. Stated as a
    function rather than inlined because several tables quote it, and a second inlined
    copy is how two tables in one report end up disagreeing."""
    if n_bars <= 0 or total_return <= -1.0:
        return float("nan")
    return (1.0 + total_return) ** (periods_per_year / n_bars) - 1.0


def render_variant_table(
    result: StudyResult, symbol: str, tier_name: str, variant_names: Sequence[str]
) -> str:
    symbol_result = result.by_symbol[symbol]
    study = result.config
    lines = [
        "| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure | Costs / gross P&L |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name in variant_names:
        r = symbol_result.variants[(name, tier_name)]
        d = r.diagnostics
        open_note = " +1 open" if d.n_open_at_end else ""
        lines.append(
            f"| `{name}` | {_pct(r.total_return)} | "
            f"{_pct(cagr(r.total_return, r.n_oos_bars, study.periods_per_year))} | "
            f"{_num(r.sharpe_annual(study))} | {_num(r.max_drawdown * 100, 1)}% | "
            f"{d.n_closed_trades}{open_note} | "
            f"{_num(d.exposure * 100, 1)}% | {_num(d.cost_share_of_gross * 100, 1)}% |"
        )
    benchmark = symbol_result.benchmarks[tier_name]
    lines.append(
        f"| **buy & hold** | {_pct(benchmark.total_return)} | "
        f"{_pct(cagr(benchmark.total_return, len(benchmark.oos_equity), study.periods_per_year))} | "
        f"{_num(benchmark.sharpe_annual(study))} | {_num(benchmark.max_drawdown * 100, 1)}% | "
        "1 | 100.0% | — |"
    )
    return "\n".join(lines)


def render_plateau_surface(
    result: StudyResult, symbol: str, tier_name: str, metric: str = "sharpe"
) -> str:
    """The full N_entry x N_exit surface. Printed as a grid rather than a ranked list on
    purpose: a ranked list hides whether the best cell has good neighbours, which is the
    entire question a plateau analysis exists to answer."""
    symbol_result = result.by_symbol[symbol]
    study = result.config
    lines = [
        "| N_entry \\ N_exit | " + " | ".join(str(n) for n in PLATEAU_N_EXIT) + " |",
        "|---" * (len(PLATEAU_N_EXIT) + 1) + "|",
    ]
    for n_entry in PLATEAU_N_ENTRY:
        cells = []
        for n_exit in PLATEAU_N_EXIT:
            key = (f"plateau_{n_entry}_{n_exit}", tier_name)
            if key not in symbol_result.variants:
                cells.append("—")  # n_exit > n_entry is never constructed (D109)
                continue
            r = symbol_result.variants[key]
            if metric == "sharpe":
                cells.append(_num(r.sharpe_annual(study)))
            elif metric == "cagr":
                cells.append(_pct(cagr(r.total_return, r.n_oos_bars, study.periods_per_year)))
            elif metric == "trades":
                cells.append(str(r.diagnostics.n_closed_trades))
            else:
                raise ValueError(f"unknown plateau metric {metric!r}")
        lines.append(f"| **{n_entry}** | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def plateau_spread(result: StudyResult, symbol: str, tier_name: str) -> dict[str, float]:
    """The numbers that decide "plateau or spike?" without eyeballing the grid: the best
    cell, the mean of its immediate neighbours, and the gap between them expressed in
    units of the surface's own spread. A spike is a large positive gap; a plateau is a
    gap near zero."""
    symbol_result = result.by_symbol[symbol]
    study = result.config
    sharpes = {
        (n_entry, n_exit): symbol_result.variants[
            (f"plateau_{n_entry}_{n_exit}", tier_name)
        ].sharpe_annual(study)
        for n_entry in PLATEAU_N_ENTRY
        for n_exit in PLATEAU_N_EXIT
        if (f"plateau_{n_entry}_{n_exit}", tier_name) in symbol_result.variants
    }
    best_key = max(sharpes, key=lambda k: sharpes[k])
    entries, exits = list(PLATEAU_N_ENTRY), list(PLATEAU_N_EXIT)
    ei, xi = entries.index(best_key[0]), exits.index(best_key[1])
    neighbours = [
        sharpes[(entries[e], exits[x])]
        for e in (ei - 1, ei, ei + 1)
        for x in (xi - 1, xi, xi + 1)
        if 0 <= e < len(entries)
        and 0 <= x < len(exits)
        and (e, x) != (ei, xi)
        and (entries[e], exits[x]) in sharpes
    ]
    values = list(sharpes.values())
    spread = max(values) - min(values)
    best, neighbour_mean = sharpes[best_key], sum(neighbours) / len(neighbours)
    return {
        "best_n_entry": float(best_key[0]),
        "best_n_exit": float(best_key[1]),
        "best_sharpe": best,
        "neighbour_mean_sharpe": neighbour_mean,
        "worst_sharpe": min(values),
        "surface_spread": spread,
        "best_minus_neighbours_over_spread": (best - neighbour_mean) / spread if spread else 0.0,
        "n_cells": float(len(sharpes)),
    }


def render_diagnostics_table(
    result: StudyResult, symbol: str, tier_name: str, variant_names: Sequence[str]
) -> str:
    symbol_result = result.by_symbol[symbol]
    lines = [
        "| Variant | Win rate | Mean MFE | Mean MAE | Median bars held | p90 bars held | "
        "Median bars to stop-out (losers) | Whipsaw rate | Rebalance share of costs | Ann. turnover |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for name in variant_names:
        d = symbol_result.variants[(name, tier_name)].diagnostics
        lines.append(
            f"| `{name}` | {_num(d.win_rate * 100, 1)}% | {_pct(d.mean_mfe)} | {_pct(d.mean_mae)} | "
            f"{_num(d.median_bars_held, 0)} | {_num(d.p90_bars_held, 0)} | "
            f"{_num(d.median_bars_to_stop_out_losers, 0)} | {_num(d.whipsaw_rate * 100, 1)}% | "
            f"{_num(d.rebalance_cost_share * 100, 1)}% | {_num(d.annual_turnover, 2)}x |"
        )
    return "\n".join(lines)


def render_capture_table(
    result: StudyResult, symbol: str, tier_name: str, variant_names: Sequence[str]
) -> str:
    symbol_result = result.by_symbol[symbol]
    lines = [
        "| Variant | Upside captured | Downside participated | Downside avoided | Drawdown avoided |",
        "|---|---|---|---|---|",
    ]
    for name in variant_names:
        d = symbol_result.variants[(name, tier_name)].diagnostics
        lines.append(
            f"| `{name}` | {_num(d.upside_capture * 100, 1)}% | "
            f"{_num(d.downside_participation * 100, 1)}% | {_num(d.downside_avoided * 100, 1)}% | "
            f"{_num(d.drawdown_avoided * 100, 1)}% |"
        )
    return "\n".join(lines)


def render_tier_table(result: StudyResult, symbol: str, variant_name: str) -> str:
    """One variant across every cost tier — the maker-versus-taker question, isolated."""
    symbol_result = result.by_symbol[symbol]
    study = result.config
    lines = [
        "| Tier | Fee | Role | Total return | CAGR | Sharpe (ann.) | Costs paid | "
        "Costs / gross P&L | Buy & hold (same tier) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for tier in result.tiers:
        r = symbol_result.variants[(variant_name, tier.name)]
        b = symbol_result.benchmarks[tier.name]
        lines.append(
            f"| `{tier.name}` | {tier.fee_bps / 100:.2f}% | {tier.role} | {_pct(r.total_return)} | "
            f"{_pct(cagr(r.total_return, r.n_oos_bars, study.periods_per_year))} | "
            f"{_num(r.sharpe_annual(study))} | {r.diagnostics.total_costs:,.0f} | "
            f"{_num(r.diagnostics.cost_share_of_gross * 100, 1)}% | {_pct(b.total_return)} |"
        )
    return "\n".join(lines)


# ------------------------------------------------------- era / regime decomposition


VOL_TARGET_SWEEP: tuple[float, ...] = (0.20, 0.30, 0.60, 0.80)
"""Target annual vols swept alongside the 0.40 baseline (D118). The target was the one
free parameter of the original study that was chosen and never tested — and since the
Sharpe differences it buys turn out to be inside the noise band, sweeping it is how that
becomes visible rather than assumed."""

START_YEAR_CUTS: tuple[int, ...] = (2015, 2018, 2020, 2021, 2022)
"""Fixture start years for the start-date sensitivity. Each one shifts the OOS span by
`train_size` bars, so "OOS from 2021" means a fixture beginning 2021-01-01."""


def vol_target_variants() -> list["Variant"]:
    return [
        Variant(
            f"voltarget_{target:.2f}".replace(".", ""),
            "sizing",
            fixed_config=breakout_config(
                n_entry=BASELINE_N_ENTRY,
                n_exit=BASELINE_N_EXIT,
                weight_source={**INVERSE_VOL_AT_ENTRY, "target_annual_vol": target},
            ),
        )
        for target in VOL_TARGET_SWEEP
    ]


def run_constant_fraction_benchmark(
    bars: Sequence[TimestampedBar],
    symbol: str,
    tier: CostTier,
    study: BreakoutStudyConfig,
    fraction: float,
) -> BenchmarkResult:
    """Hold a CONSTANT FRACTION of capital in the instrument, rest in cash, through the
    same engine, tier and fill timing as every strategy variant (D119).

    This is the risk-equalised benchmark. Comparing a strategy that is in the market a
    third of the time against a 100%-invested buy-and-hold answers "would you have been
    better off just holding it", which is worth knowing but is not a like-for-like risk
    comparison. Setting `fraction` to the strategy's own average exposure asks the
    sharper question: **given that much average exposure, did choosing WHEN to take it
    beat spreading it evenly?**

    Run through the engine rather than computed, deliberately — unlike fixed-quantity
    buy-and-hold (D115), a constant fraction genuinely does rebalance, and that
    rebalancing costs real money at these fee tiers. Charging it is the point."""
    if not 0.0 < fraction <= 1.0:
        raise ValueError(f"fraction must be in (0, 1], got {fraction}")
    spans = _window_spans(bars, study)
    oos_start, oos_end = spans[0][2], spans[-1][3]
    result = run_backtest(
        bars_by_instrument={symbol: list(bars[oos_start:oos_end])},
        instruments=_instruments(symbol),
        strategies=[
            ScheduledWeightStrategy(  # type: ignore[list-item]  # see run_benchmark_via_engine
                strategy_id=f"constfrac-{symbol}", weights_by_instrument={symbol: [fraction]}
            )
        ],
        cost_stack=tier.build(),
        allocator=ConstantSplitAllocator(),
        starting_cash=study.starting_cash,
        fill_timing=study.fill_timing,
    )
    curve = result.equity_curve
    return BenchmarkResult(
        symbol=symbol,
        tier=tier,
        oos_equity=list(curve),
        oos_returns=[b / a - 1.0 for (_, a), (_, b) in zip(curve, curve[1:])],
    )


def sharpe_difference_bootstrap(
    strategy_returns: Sequence[float],
    benchmark_returns: Sequence[float],
    study: BreakoutStudyConfig,
    seed: int,
    n_sims: int = 4000,
    block_size: int = 20,
) -> dict[str, float]:
    """PAIRED block bootstrap of (strategy Sharpe − benchmark Sharpe), D120.

    Paired is the load-bearing word: the same resampled BAR INDICES are applied to both
    return series, so the strong correlation between a long-flat strategy and the
    instrument it trades is preserved. Bootstrapping the two independently would inflate
    the variance of the difference and make everything look insignificant for the wrong
    reason.

    Blocks rather than single bars, for the reason D23 gives: resampling contiguous
    stretches preserves the local dependence a trend follower lives on. `seed` is
    required (D34).

    Returns the observed difference, a 90% interval, and P(difference > 0) — which is
    the number that matters, because an interval spanning zero on a 0.04 Sharpe gap is
    the honest description of "this is not measurable at this sample size"."""
    s = np.asarray(strategy_returns, dtype=float)
    b = np.asarray(benchmark_returns, dtype=float)
    if s.size != b.size:
        raise ValueError(f"paired bootstrap needs equal lengths, got {s.size} and {b.size}")
    if s.size <= block_size:
        raise ValueError(f"need more than {block_size} observations, got {s.size}")

    rng = np.random.default_rng(seed)
    n = s.size
    n_blocks = n // block_size + 1
    diffs = np.empty(n_sims, dtype=float)
    for i in range(n_sims):
        starts = rng.integers(0, n - block_size, size=n_blocks)
        index = np.concatenate([np.arange(start, start + block_size) for start in starts])[:n]
        diffs[i] = sharpe(s[index], study.rf_annual, study.periods_per_year) - sharpe(
            b[index], study.rf_annual, study.periods_per_year
        )
    observed = sharpe(list(s), study.rf_annual, study.periods_per_year) - sharpe(
        list(b), study.rf_annual, study.periods_per_year
    )
    return {
        "observed": observed,
        "p05": float(np.percentile(diffs, 5)),
        "p95": float(np.percentile(diffs, 95)),
        "prob_positive": float((diffs > 0).mean()),
        "n_sims": float(n_sims),
        "block_size": float(block_size),
        "seed": float(seed),
    }


def exposure_by_year(result: VariantResult) -> dict[int, float]:
    """Fraction of each calendar year's OOS bars spent holding a position. Computed from
    episode TIMESTAMPS against the OOS calendar, not from episode bar indices — those are
    relative to the run series, which begins one warm-up prefix earlier."""
    timestamps = [ts for ts, _ in result.oos_equity]
    bars_in_year: dict[int, int] = {}
    for ts in timestamps:
        bars_in_year[ts.year] = bars_in_year.get(ts.year, 0) + 1
    held_in_year: dict[int, int] = {}
    for episode in result.episodes:
        end = episode.exit_timestamp or timestamps[-1]
        for ts in timestamps:
            if episode.entry_timestamp <= ts < end:
                held_in_year[ts.year] = held_in_year.get(ts.year, 0) + 1
    return {year: held_in_year.get(year, 0) / count for year, count in sorted(bars_in_year.items())}


def annual_breakdown(result: VariantResult, benchmark: BenchmarkResult) -> list[dict[str, float]]:
    """Per calendar year: the strategy's compounded return, the benchmark's, the number
    of trades opened, and time in market. The single most clarifying table in the study —
    a decade-long total return hides which years produced it."""
    if len(result.oos_returns) != len(benchmark.oos_returns):
        raise ValueError("strategy and benchmark cover different spans")
    strategy_year: dict[int, float] = {}
    benchmark_year: dict[int, float] = {}
    for (ts, _), s_ret, b_ret in zip(result.oos_equity[1:], result.oos_returns, benchmark.oos_returns):
        strategy_year[ts.year] = strategy_year.get(ts.year, 1.0) * (1.0 + s_ret)
        benchmark_year[ts.year] = benchmark_year.get(ts.year, 1.0) * (1.0 + b_ret)
    trades: dict[int, int] = {}
    for episode in result.episodes:
        trades[episode.entry_timestamp.year] = trades.get(episode.entry_timestamp.year, 0) + 1
    exposure = exposure_by_year(result)
    return [
        {
            "year": float(year),
            "strategy": strategy_year[year] - 1.0,
            "benchmark": benchmark_year[year] - 1.0,
            "trades": float(trades.get(year, 0)),
            "exposure": exposure.get(year, 0.0),
        }
        for year in sorted(strategy_year)
    ]


def start_date_sensitivity(
    bars: Sequence[TimestampedBar],
    symbol: str,
    variant: Variant,
    tier: CostTier,
    study: BreakoutStudyConfig,
    cut_years: Sequence[int] = START_YEAR_CUTS,
) -> list[dict]:
    """Re-run the identical configuration on fixtures truncated to begin at each cut
    year. Nothing about the strategy changes — only when the investor started.

    This is the study's answer to "are these numbers just the era?". A result whose CAGR
    depends heavily on the start date is telling you the sample, not the rule."""
    rows = []
    for cut in cut_years:
        sliced = [tb for tb in bars if tb.timestamp.year >= cut]
        # Need a full window plus the longest warm-up prefix the variant can require.
        if len(sliced) < study.train_size + study.test_size + 210:
            continue
        result = run_variant(sliced, symbol, variant, tier, study)
        benchmark = run_benchmark(sliced, symbol, tier, study)
        rows.append(
            {
                "cut_year": cut,
                "oos_start": result.oos_equity[0][0],
                "n_oos_bars": result.n_oos_bars,
                "strategy_return": result.total_return,
                "benchmark_return": benchmark.total_return,
                "strategy_cagr": cagr(result.total_return, result.n_oos_bars, study.periods_per_year),
                "benchmark_cagr": cagr(
                    benchmark.total_return, len(benchmark.oos_equity), study.periods_per_year
                ),
                "strategy_sharpe": result.sharpe_annual(study),
                "benchmark_sharpe": benchmark.sharpe_annual(study),
                "strategy_maxdd": result.max_drawdown,
                "benchmark_maxdd": benchmark.max_drawdown,
            }
        )
    return rows


def render_annual_table(rows: Sequence[dict[str, float]]) -> str:
    lines = [
        "| Year | Strategy | Buy & hold | Trades opened | Time in market |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {int(row['year'])} | {row['strategy']:+.1%} | {row['benchmark']:+.1%} | "
            f"{int(row['trades'])} | {row['exposure']:.0%} |"
        )
    return "\n".join(lines)


def render_start_date_table(rows: Sequence[dict]) -> str:
    lines = [
        "| OOS begins | Bars | Strategy | Buy & hold | Strategy CAGR | B&H CAGR | "
        "Strategy Sharpe | B&H Sharpe | Strategy max DD | B&H max DD |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['oos_start'].date()} | {row['n_oos_bars']:,} | "
            f"{row['strategy_return']:+.1%} | {row['benchmark_return']:+.1%} | "
            f"{row['strategy_cagr']:+.1%} | {row['benchmark_cagr']:+.1%} | "
            f"{row['strategy_sharpe']:.2f} | {row['benchmark_sharpe']:.2f} | "
            f"{row['strategy_maxdd']:.0%} | {row['benchmark_maxdd']:.0%} |"
        )
    return "\n".join(lines)

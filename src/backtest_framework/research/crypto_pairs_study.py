"""BTC/ETH z-score pairs study (D122-D127): walk-forward, cost-tiered, swept,
logged, DSR-adjusted, and benchmarked against the risk-free rate first.

Study glue only — every load-bearing piece is a gate-tested framework component:
`ZScorePairsStrategy` UNMODIFIED (D69), `walk_forward_windows` (D85), `run_backtest`
with `fill_timing="next_open"` (D103), `build_cost_stack` from a declarative config
(D102), `TrialRegistry` (D20), `deflated_sharpe_from_trials` (D86),
`analytics.metrics` (D80), `research.cointegration`'s Engle-Granger/ADF machinery
(D92/D93), `research.capacity.recording_cost_stack` for per-brick attribution (D95),
and `research.breakout_study`'s `CostTier` / `run_benchmark` so the two crypto studies
price fees and buy-and-hold identically (D114/D115).

## What this study is NOT

It is not a pair *selection* study. The pair is given a priori, and BTC/ETH is famous.
D22's rule — selection belongs inside the training window, over a broad universe —
cannot be satisfied by a study with no selection step, so D70's meta-in-sample caveat
applies in full and is stated in the artifact rather than mitigated. The one thing that
CAN be done honestly is to test the premise instead of assuming it: `cointegration_report`
runs the ADF machinery on each TRAINING window only and reports how often the log spread
is stationary at conventional levels. On this pair it usually is not (D125).

## One continuous out-of-sample run, not chained windows (D123)

The pairs studies (v1-v3, D89) run each walk-forward window as its own backtest and chain
capital window to window. This study follows the breakout study's continuous pattern
(D113) instead, and both are measured: `stitch="chained"` is run as a sensitivity so the
size of the difference is a number in the artifact rather than an argument in a docstring.

Two seams, not one, motivate the choice for a *pairs* book specifically:

1. **A free liquidation at every boundary.** A chained window ends with the book marked
   at the close and the next window starts in cash — the position teleports to cash with
   no exit fee, no borrow, and no margin. D113 called this cheap for mean reversion; with
   43 boundaries and the book in a position about half the time, that is roughly twenty
   free round-trip exits — priced by the `stitch_chained` row rather than estimated.
2. **A silent reset of the strategy's own hysteresis.** `ZScorePairsStrategy._side` is
   per-run mutable state (D69). A fresh instance per window starts at `_side = 0`, so the
   band between `exit_z` and `entry_z` — the whole point of the hysteresis — is discarded
   at every boundary and the strategy re-enters only on a fresh |z| > entry_z crossing.
   That is a SIGNAL artifact, not merely a cost artifact, and it has no analogue in the
   breakout study (whose `ScheduledBreakout` explicitly carries position state across).

Nothing in this study is fitted, so the continuous run needs no parameter schedule: every
variant is one fixed configuration over the whole OOS span. The walk-forward structure
still defines the study — the OOS span starts exactly where window 0's TRAINING slice
ends, per-window returns are sliced out for per-window trial rows, and the training slices
are what the cointegration diagnostic is computed on.

**Comparability consequence.** These curves are methodologically identical to
BREAKOUT_RESULTS.md's and NOT identical to `docs/results/pairs_study_v*.md`'s. The
`stitch_chained` sensitivity row prices exactly that difference.

## Costs (D124)

A pairs trade is not a long-only trade, and the cost model says so in three places:

- **Two legs.** Every round trip pays the tier fee four times (in and out, twice), against
  the breakout study's two. The tiers themselves are `breakout_study.DEFAULT_TIERS`
  unchanged so the fee dimension is identical between the studies.
- **A short leg that must be borrowed.** `BorrowFee` (D71) is in every stack at a stated,
  non-zero rate. Silently assuming free shorts is the single most result-corrupting choice
  available to a spot-crypto pairs study, because the short leg is ~100% of NAV for the
  entire life of every trade.
- **~200% gross fires margin interest.** At `leg_weight=1.0` gross exposure is twice NAV,
  so `MarginInterest` (D5) accrues on ~100% of NAV continuously while in a trade. D96
  found this threshold to be the dominant lever, so `leg_weight` is swept.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from ..analytics.metrics import max_drawdown, realised_beta, sharpe, sortino
from ..config.cost_stack import StackDataContext, build_cost_stack
from ..costs.stack import CostStack
from ..data.alignment import align_bars
from ..data.bars import TimestampedBar
from ..data.corporate_actions import CorporateActions
from ..engine.allocator import ConstantSplitAllocator
from ..engine.backtest import run_backtest
from ..instruments.base import Instrument
from ..instruments.equity import Equity
from ..registry.trial_registry import TrialRegistry
from ..strategies.zscore_pairs import ZScorePairsStrategy
from ..validation.dsr import deflated_sharpe_from_trials
from ..validation.walk_forward import walk_forward_windows
from .breakout_study import CRYPTO_QUANTITY_PRECISION, DEFAULT_TIERS, CostTier
from .breakout_study import BenchmarkResult, BreakoutStudyConfig, cagr, run_benchmark
from .capacity import CostLedger, recording_cost_stack
from .cointegration import adf_stat, engle_granger_beta

REFERENCE_TIER = "taker_40bp"
"""The tier the headline verdict is read at — identical to the breakout study's choice
(D114), for the same reason: a z-score entry is a market order, so it is a taker fill,
and the maker rows answer "how much of the outcome is fees?" and nothing else."""


# ------------------------------------------------------------- cointegration constants

DF_TAU_MU_CRITICAL: dict[str, float] = {"1%": -3.4568, "5%": -2.8732, "10%": -2.5730}
"""Dickey-Fuller tau_mu critical values (constant, no trend) at T = 252, as tabulated by
MacKinnon and returned by `statsmodels.tsa.stattools.adfuller(..., regression="c")` —
anchored against that library in `tests/unit/test_crypto_pairs.py` rather than
typed in from memory (Pillar 3).

Why thresholds exist here at all, when D29/D93 deliberately refused them: those decisions
govern *selection*, where ranking N candidates is the honest operation and a p-value adds
nothing. This study selects nothing — the pair is given — so the only question the ADF
can answer is the binary one, "is this spread stationary at a conventional level?", and
that question needs a critical value (D125)."""

ENGLE_GRANGER_CRITICAL: dict[str, float] = {"1%": -3.90, "5%": -3.34, "10%": -3.04}
"""Engle-Granger residual-ADF critical values, one estimated cointegrating regressor plus
constant (MacKinnon). Stricter than the Dickey-Fuller table because beta was estimated
from the same sample — the reason the two tests below are reported side by side and never
against each other's thresholds."""


@dataclass(frozen=True)
class WindowCointegration:
    """One training window's answer to "is this pair actually cointegrated?"."""

    window: int
    train_start: datetime
    train_end: datetime
    adf_traded_spread: float
    """ADF t-statistic of the DEMEANED 1:1 log spread — the spread the strategy actually
    trades (D69's fixed hedge). Compared against `DF_TAU_MU_CRITICAL`: the hedge ratio is
    known rather than estimated, so only the mean is removed."""
    engle_granger_beta: float
    engle_granger_adf: float
    """beta and the residual ADF from `ln A = alpha + beta * ln B` — the textbook test,
    compared against `ENGLE_GRANGER_CRITICAL`. beta is reported and NOT traded (D92's
    coherence argument): evidence about `ln A - 0.4 * ln B` is evidence about a spread
    this strategy does not hold."""

    def traded_spread_cointegrated_at(self, level: str) -> bool:
        return self.adf_traded_spread < DF_TAU_MU_CRITICAL[level]

    def engle_granger_cointegrated_at(self, level: str) -> bool:
        return self.engle_granger_adf < ENGLE_GRANGER_CRITICAL[level]


@dataclass(frozen=True)
class CointegrationReport:
    windows: tuple[WindowCointegration, ...]

    def rate(self, level: str, test: str = "traded") -> float:
        if not self.windows:
            return float("nan")
        if test == "traded":
            hits = sum(1 for w in self.windows if w.traded_spread_cointegrated_at(level))
        elif test == "engle_granger":
            hits = sum(1 for w in self.windows if w.engle_granger_cointegrated_at(level))
        else:
            raise ValueError(f"unknown cointegration test {test!r}")
        return hits / len(self.windows)

    def count(self, level: str, test: str = "traded") -> int:
        return round(self.rate(level, test) * len(self.windows))

    @property
    def betas(self) -> list[float]:
        return [w.engle_granger_beta for w in self.windows]

    def beta_coherent_rate(self, window: tuple[float, float] = (0.7, 1.3)) -> float:
        """Fraction of windows whose fitted beta sits inside D92's coherence band. The
        1:1 hedge is only a defensible description of the relationship where it does."""
        if not self.windows:
            return float("nan")
        return sum(1 for b in self.betas if window[0] <= b <= window[1]) / len(self.windows)

    def to_metrics(self) -> dict[str, float]:
        return {
            "coint_windows": float(len(self.windows)),
            "coint_rate_traded_5pct": self.rate("5%"),
            "coint_rate_traded_10pct": self.rate("10%"),
            "coint_rate_eg_5pct": self.rate("5%", "engle_granger"),
            "coint_rate_eg_10pct": self.rate("10%", "engle_granger"),
            "beta_median": float(np.median(self.betas)) if self.windows else float("nan"),
            "beta_coherent_rate": self.beta_coherent_rate(),
        }


# -------------------------------------------------------------------------- config


@dataclass(frozen=True)
class CryptoPairsConfig:
    symbol_a: str = "BTC-USD"
    symbol_b: str = "ETH-USD"
    train_size: int = 252
    test_size: int = 63
    step: int = 63
    starting_cash: float = 100_000.0
    rf_annual: float = 0.04
    periods_per_year: float = 365.0
    """365, not 252 — crypto trades every calendar day. Supplied by the caller because
    the `Instrument` protocol carries no calendar method (D17 as designed vs
    `instruments/base.py` as built; the same reading D108 took)."""
    fill_timing: str = "next_open"
    borrow_annual_rate: float = 0.10
    """Cost of borrowing the SHORT leg's coin, per year (D124). Not a free parameter and
    not zero: 10%/yr is mid-range for BTC/ETH spot margin borrow on the major venues over
    this sample. Swept, because the honest range is wide."""
    margin_annual_rate: float = 0.10
    """USD margin financing on the borrowed portion of the book, per year (D5's base:
    max(gross - NAV, 0)). Set equal to the coin borrow rate deliberately, so the two
    carry channels are legible against each other rather than confounded."""
    stitch: str = "continuous"
    """"continuous" (D123, the headline) or "chained" (the pairs-study v1-v3 pattern,
    D89) — run as a sensitivity so the seam is priced, not argued about."""
    adf_lags: int = 1
    seed: int = 0

    def __post_init__(self) -> None:
        if self.stitch not in ("continuous", "chained"):
            raise ValueError(f"stitch must be 'continuous' or 'chained', got {self.stitch!r}")
        if self.fill_timing not in ("close", "next_open"):
            raise ValueError(f"fill_timing must be 'close' or 'next_open', got {self.fill_timing!r}")

    @property
    def symbols(self) -> tuple[str, str]:
        return (self.symbol_a, self.symbol_b)

    def to_dict(self) -> dict[str, Any]:
        """EVERY field that determines the result (D102's rule: two experiments that
        differ must not hash identically)."""
        return {
            "study": "crypto_pairs_btc_eth_v1",
            "signal": "zscore_pairs (D69, unmodified: fixed 1:1 log hedge, trailing z ending at t-1)",
            "symbol_a": self.symbol_a,
            "symbol_b": self.symbol_b,
            "train_size": self.train_size,
            "test_size": self.test_size,
            "step": self.step,
            "starting_cash": self.starting_cash,
            "rf_annual": self.rf_annual,
            "periods_per_year": self.periods_per_year,
            "fill_timing": self.fill_timing,
            "borrow_annual_rate": self.borrow_annual_rate,
            "margin_annual_rate": self.margin_annual_rate,
            "stitch": self.stitch,
            "adf_lags": self.adf_lags,
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, config: Mapping[str, Any]) -> "CryptoPairsConfig":
        """Rebuild from a logged trial's config dict — the study-level reproducibility
        loop (D35/D102): config -> registry -> reload -> rebuild -> re-run."""
        names = (
            "symbol_a", "symbol_b", "train_size", "test_size", "step", "starting_cash",
            "rf_annual", "periods_per_year", "fill_timing", "borrow_annual_rate",
            "margin_annual_rate", "stitch", "adf_lags", "seed",
        )
        return cls(**{name: config[name] for name in names if name in config})

    def benchmark_config(self) -> BreakoutStudyConfig:
        """The breakout study's config shape, carrying this study's window geometry — so
        `breakout_study.run_benchmark` (D115) computes buy-and-hold over exactly this
        study's OOS span, at exactly this study's fill timing, with no reimplementation."""
        return BreakoutStudyConfig(
            train_size=self.train_size,
            test_size=self.test_size,
            step=self.step,
            starting_cash=self.starting_cash,
            rf_annual=self.rf_annual,
            periods_per_year=self.periods_per_year,
            fill_timing=self.fill_timing,
        )


# ------------------------------------------------------------------------- costs


def pair_cost_stack_config(
    tier: CostTier, borrow_annual_rate: float, margin_annual_rate: float
) -> dict[str, Any]:
    """The declarative description of one (tier, borrow, margin) stack (D102) — the SAME
    dict `build_cost_stack` consumes and the TrialRegistry hashes.

    The trade slot is byte-identical to `CostTier.cost_stack_config()` so the fee
    dimension is shared with the breakout study; the two carry slots are what a pairs
    book adds and a long-flat book does not (D124)."""
    return {
        "trade_bricks": [{"type": "percent_spread", "bps": tier.fee_bps}],
        "carry_bricks": [{"type": "borrow_fee", "annual_rate": borrow_annual_rate}],
        "portfolio_carry_bricks": [{"type": "margin_interest", "annual_rate": margin_annual_rate}],
        "event_flow_bricks": [],
    }


def build_pair_cost_stack(config: Mapping[str, Any]) -> CostStack:
    """Spot crypto carries no dividends or splits (D108), so the stack needs no snapshot
    context — an empty one is the honest input, not a placeholder."""
    return build_cost_stack(
        dict(config),
        StackDataContext(bars_by_symbol={}, volumes_by_symbol={}, actions=CorporateActions()),
    )


# ------------------------------------------------------------------------ variants


BASELINE_LOOKBACK, BASELINE_ENTRY_Z, BASELINE_EXIT_Z = 60, 2.0, 0.5
"""D69's a-priori first-number parameters, carried over unchanged as this study's
baseline so the grid is a sensitivity around a pre-existing choice rather than around
its own best cell."""

GRID_LOOKBACKS: tuple[int, ...] = (20, 30, 60, 90)
GRID_ENTRY_Z: tuple[float, ...] = (1.5, 2.0, 2.5)
GRID_EXIT_Z = BASELINE_EXIT_Z
"""12 cells. `exit_z` is HELD at D69's 0.5 rather than swept: adding it as a third axis
would triple the grid, and the brief's own precedent (the breakout study's 12 cells) says
that is enough. The un-swept axis is named in the artifact's caveats rather than left to
be discovered."""

GROSS_LEG_WEIGHTS: tuple[float, ...] = (0.25, 0.5)
"""Sweep around the baseline's 1.0. At 0.5 gross exposure equals NAV exactly, so D5's
margin base max(gross - NAV, 0) collapses to zero — D96 found that threshold to be the
dominant lever, and it costs one extra run per tier to check whether it still is."""

DSR_POOL_GROUPS = ("grid", "gross")
"""Which variant groups constitute the DSR trial pool (D116): genuine strategy
CONFIGURATIONS. Convention sensitivities (fill timing, stitching) and cost-assumption
sensitivities (borrow rate) are the same configuration re-priced, which D98 established
is a sensitivity point and not an additional independent trial."""


@dataclass(frozen=True)
class PairsVariant:
    """One evaluated configuration. Everything that can differ between runs is a field,
    and every field is logged — a variant that differed by something not on this record
    could not be rebuilt from its trial row."""

    name: str
    group: str
    """"grid" | "gross" | "convention" | "cost" — decides which table it appears in and,
    via DSR_POOL_GROUPS, whether it counts as a trial."""
    lookback: int = BASELINE_LOOKBACK
    entry_z: float = BASELINE_ENTRY_Z
    exit_z: float = BASELINE_EXIT_Z
    leg_weight: float = 1.0
    fill_timing: str | None = None
    stitch: str | None = None
    borrow_annual_rate: float | None = None
    margin_annual_rate: float | None = None

    def resolve(self, config: CryptoPairsConfig) -> CryptoPairsConfig:
        """The effective study config for this variant — overrides applied, everything
        else inherited, so a sensitivity differs from the baseline in exactly one place."""
        overrides: dict[str, Any] = {
            name: value
            for name, value in (
                ("fill_timing", self.fill_timing),
                ("stitch", self.stitch),
                ("borrow_annual_rate", self.borrow_annual_rate),
                ("margin_annual_rate", self.margin_annual_rate),
            )
            if value is not None
        }
        return replace(config, **overrides) if overrides else config

    def strategy_config(self) -> dict[str, Any]:
        return {
            "type": "zscore_pairs",
            "lookback": self.lookback,
            "entry_z": self.entry_z,
            "exit_z": self.exit_z,
            "leg_weight": self.leg_weight,
        }

    def build_strategy(self, config: CryptoPairsConfig) -> ZScorePairsStrategy:
        """A FRESH instance every call — `_side` is per-run mutable state (D69)."""
        return ZScorePairsStrategy(
            strategy_id=f"pair-{config.symbol_a}-{config.symbol_b}",
            instrument_a=config.symbol_a,
            instrument_b=config.symbol_b,
            lookback=self.lookback,
            entry_z=self.entry_z,
            exit_z=self.exit_z,
            leg_weight=self.leg_weight,
        )

    def describe(self) -> dict[str, Any]:
        return {
            "variant": self.name,
            "group": self.group,
            "strategy_config": self.strategy_config(),
            "in_dsr_pool": self.group in DSR_POOL_GROUPS,
        }

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "PairsVariant":
        """Rebuild a variant from a logged trial row — the other half of the
        reproducibility loop (D35/D102): `CryptoPairsConfig.from_dict` recovers the
        study config and this recovers the strategy.

        No overrides are set, and that is correct rather than lossy: a trial logs its
        RESOLVED config, so a sensitivity variant's fill timing / stitching / borrow rate
        are already in the config dict `from_dict` reads. Re-applying them here would
        double-apply nothing but would let the two paths disagree, which is exactly the
        drift D102 exists to close."""
        strategy = config["strategy_config"]
        if strategy.get("type") != "zscore_pairs":
            raise ValueError(
                f"logged strategy_config is not a zscore_pairs config: {strategy.get('type')!r}"
            )
        return cls(
            name=config["variant"],
            group=config["group"],
            lookback=int(strategy["lookback"]),
            entry_z=float(strategy["entry_z"]),
            exit_z=float(strategy["exit_z"]),
            leg_weight=float(strategy["leg_weight"]),
        )


def grid_variants() -> list[PairsVariant]:
    return [
        PairsVariant(
            name=f"grid_lb{lookback}_z{entry_z:g}",
            group="grid",
            lookback=lookback,
            entry_z=entry_z,
            exit_z=GRID_EXIT_Z,
        )
        for lookback in GRID_LOOKBACKS
        for entry_z in GRID_ENTRY_Z
    ]


def baseline_name() -> str:
    return f"grid_lb{BASELINE_LOOKBACK}_z{BASELINE_ENTRY_Z:g}"


def gross_variants() -> list[PairsVariant]:
    return [
        PairsVariant(name=f"gross_lw{lw:g}", group="gross", leg_weight=lw)
        for lw in GROSS_LEG_WEIGHTS
    ]


def convention_variants() -> list[PairsVariant]:
    return [
        PairsVariant(name="fill_close", group="convention", fill_timing="close"),
        PairsVariant(name="stitch_chained", group="convention", stitch="chained"),
    ]


def cost_variants() -> list[PairsVariant]:
    return [
        PairsVariant(
            name="carry_free", group="cost", borrow_annual_rate=0.0, margin_annual_rate=0.0
        ),
        PairsVariant(name="borrow_0pct", group="cost", borrow_annual_rate=0.0),
        PairsVariant(name="borrow_25pct", group="cost", borrow_annual_rate=0.25),
    ]


def default_variants() -> list[PairsVariant]:
    return grid_variants() + gross_variants() + convention_variants() + cost_variants()


# ------------------------------------------------------------------------- results


@dataclass
class VariantResult:
    variant: PairsVariant
    tier: CostTier
    resolved: CryptoPairsConfig
    oos_equity: list[tuple[datetime, float]]
    oos_returns: list[float]
    window_sharpes_daily: dict[int, float]
    window_final_nav: dict[int, float]
    ledger: CostLedger
    oos_fills: list[tuple[datetime, str, float, float, float]]
    """The engine's own fill stream, restricted to the OOS span (D77: a fill is what the
    simulator produces; a "trade" is an interpretation). Kept on the result so tests can
    assert WHEN the book first traded without re-running the backtest."""
    n_round_trips: int
    n_fills: int
    exposure: float
    """Fraction of OOS bars on which the book held a non-zero position."""
    traded_notional: float
    avg_nav: float
    n_oos_bars: int

    @property
    def final_nav(self) -> float:
        return self.oos_equity[-1][1]

    @property
    def total_return(self) -> float:
        return self.final_nav / self.oos_equity[0][1] - 1.0

    @property
    def years(self) -> float:
        return self.n_oos_bars / 365.0

    def sharpe_annual(self, config: CryptoPairsConfig) -> float:
        return sharpe(self.oos_returns, config.rf_annual, config.periods_per_year)

    def sortino_annual(self, config: CryptoPairsConfig) -> float:
        """R17 (2026-09-19): a Sortino beside every Sharpe, same rf and periods."""
        return sortino(self.oos_returns, config.rf_annual, config.periods_per_year)

    def sharpe_daily(self, config: CryptoPairsConfig) -> float:
        return self.sharpe_annual(config) / math.sqrt(config.periods_per_year)

    @property
    def max_drawdown(self) -> float:
        return max_drawdown(self.oos_equity)

    @property
    def annual_turnover(self) -> float:
        return self.traded_notional / self.avg_nav / self.years if self.avg_nav else float("nan")

    def cost_totals(self) -> dict[str, float]:
        """Friction dollars by brick, from the recording stack (D95's mechanism reused).
        Named by role rather than by class so the artifact's table is readable."""
        totals = self.ledger.totals
        return {
            "fees": totals.get("PercentOfNotionalSpread", 0.0),
            "borrow": totals.get("BorrowFee", 0.0),
            "margin": totals.get("MarginInterest", 0.0),
        }

    @property
    def total_costs(self) -> float:
        return sum(self.cost_totals().values())

    def annualised_drag(self, brick: str) -> float:
        return self.cost_totals()[brick] / self.avg_nav / self.years if self.avg_nav else float("nan")


@dataclass
class StudyResult:
    config: CryptoPairsConfig
    snapshot_id: str
    tiers: tuple[CostTier, ...]
    variants: tuple[PairsVariant, ...]
    results: dict[tuple[str, str], VariantResult]
    """(variant name, tier name) -> result."""
    benchmarks: dict[tuple[str, str], BenchmarkResult]
    """(benchmark name, tier name) -> buy-and-hold. Names: symbol_a, symbol_b, "basket_5050"."""
    cointegration: CointegrationReport
    n_windows: int
    oos_start: datetime
    oos_end: datetime
    n_oos_bars: int
    window_test_spans: tuple[tuple[int, datetime, datetime], ...]
    """(window index, first test bar, last test bar) — so a report can name a window's
    dates without re-deriving them from the fixture and getting them subtly wrong."""
    dsr_by_tier: dict[str, float]
    dsr_inputs_by_tier: dict[str, dict[str, Any]]
    betas_by_tier: dict[str, dict[str, float]]
    """tier -> {"vs_BTC-USD": beta, "vs_ETH-USD": beta, "vs_basket_5050": beta} for the
    baseline variant. D37 makes this first-class for a market-neutral claim."""

    @property
    def n_oos_trials(self) -> int:
        return len(self.results)


# ------------------------------------------------------------------------ harness


def aligned_series(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]], config: CryptoPairsConfig
) -> dict[str, list[TimestampedBar]]:
    """Inner-join the two legs on exact timestamps (D45/D63) and return the surviving
    per-symbol series.

    On this fixture that TRUNCATES the study to ETH's inception (2017-11-09), discarding
    nearly three years of BTC history. That is correct for a pairs trade — there is no
    spread on a day one leg does not exist — and it is stated in the artifact rather than
    worked around. Every downstream span, benchmark and window is computed from these
    series, so the strategy and its benchmarks cannot disagree about what "the sample" is.
    """
    missing = [s for s in config.symbols if s not in bars_by_symbol]
    if missing:
        raise ValueError(f"fixture is missing required symbol(s): {', '.join(missing)}")
    selected = {symbol: list(bars_by_symbol[symbol]) for symbol in config.symbols}
    aligned = align_bars(selected)
    if not aligned:
        raise ValueError(
            f"{config.symbol_a} and {config.symbol_b} share no timestamps after inner-join "
            "alignment — there is no spread to trade (D45/D63/D99)"
        )
    return {
        symbol: [TimestampedBar(ab.timestamp, ab.bars[symbol]) for ab in aligned]
        for symbol in config.symbols
    }


def window_spans(
    series: Mapping[str, Sequence[TimestampedBar]], config: CryptoPairsConfig
) -> list[tuple[int, int, int, int]]:
    """(window index, train start, test start, test end-exclusive) in absolute indices of
    the aligned series. Derived from `walk_forward_windows` (never re-derived by hand) so
    the study and the framework's walk-forward machinery cannot drift apart."""
    reference = series[config.symbol_a]
    index_by_timestamp = {tb.timestamp: i for i, tb in enumerate(reference)}
    spans = []
    for window in walk_forward_windows(series, config.train_size, config.test_size, config.step):
        test_bars = window.test_bars_by_instrument[config.symbol_a]
        test_start = index_by_timestamp[test_bars[0].timestamp]
        test_end = index_by_timestamp[test_bars[-1].timestamp] + 1
        spans.append((window.index, test_start - config.train_size, test_start, test_end))
    if not spans:
        raise ValueError("no walk-forward windows fit the series — check sizes vs series length")
    return spans


def cointegration_report(
    series: Mapping[str, Sequence[TimestampedBar]], config: CryptoPairsConfig
) -> CointegrationReport:
    """Test the premise, per TRAINING window only (D22's structural rule applied to a
    diagnostic: `walk_forward_windows` hands out train views that physically contain no
    test bar, so this cannot peek even by accident).

    Two tests, reported side by side and never against each other's thresholds:
    the demeaned 1:1 log spread the strategy actually trades, and the textbook
    Engle-Granger residual with beta estimated from the same window."""
    windows = []
    for window in walk_forward_windows(series, config.train_size, config.test_size, config.step):
        view_a = window.train_views[config.symbol_a]
        view_b = window.train_views[config.symbol_b]
        log_a = np.log([view_a[i].close for i in range(len(view_a))])
        log_b = np.log([view_b[i].close for i in range(len(view_b))])
        spread = log_a - log_b
        _alpha, beta, residuals = engle_granger_beta(log_a, log_b)
        windows.append(
            WindowCointegration(
                window=window.index,
                train_start=_view_timestamp(series, config, window.index, config.train_size, first=True),
                train_end=_view_timestamp(series, config, window.index, config.train_size, first=False),
                adf_traded_spread=adf_stat(spread - spread.mean(), lags=config.adf_lags),
                engle_granger_beta=beta,
                engle_granger_adf=adf_stat(residuals, lags=config.adf_lags),
            )
        )
    return CointegrationReport(windows=tuple(windows))


def _view_timestamp(
    series: Mapping[str, Sequence[TimestampedBar]],
    config: CryptoPairsConfig,
    window_index: int,
    train_size: int,
    first: bool,
) -> datetime:
    reference = series[config.symbol_a]
    start = window_index * config.step
    return reference[start].timestamp if first else reference[start + train_size - 1].timestamp


def _instruments(config: CryptoPairsConfig) -> dict[str, Instrument]:
    """BTC/ETH as `Equity(quantity_precision=8)` (D108). Unlike the breakout study this
    book DOES go short and DOES run above 100% gross, so the equity semantics are load
    bearing here rather than incidental: signed notional feeds `BorrowFee`'s
    shorts-only base, full-notional margin feeds D5's gross-exposure base, and
    `carry_components()` is what lets both bricks apply at all (D100)."""
    return {
        symbol: Equity(symbol=symbol, quantity_precision=CRYPTO_QUANTITY_PRECISION)
        for symbol in config.symbols
    }


def _position_walk(
    timestamps: Sequence[datetime],
    fills: Sequence[tuple[datetime, str, float, float, float]],
    symbol: str,
) -> list[float]:
    """Position in `symbol` at each bar's close, reconstructed from the fill stream.

    The engine reports fills, not a position curve (D77 — a fill is what the simulator
    produces). Cumulative signed quantity is the exact reconstruction here because spot
    crypto has no splits to scale positions (D108)."""
    by_timestamp: dict[datetime, float] = {}
    for timestamp, instrument_id, quantity, _price, _cost in fills:
        if instrument_id == symbol:
            by_timestamp[timestamp] = by_timestamp.get(timestamp, 0.0) + quantity
    position, walk = 0.0, []
    for timestamp in timestamps:
        position += by_timestamp.get(timestamp, 0.0)
        walk.append(position)
    return walk


def _episode_stats(
    segments: Sequence[tuple[Sequence[datetime], Sequence[tuple[datetime, str, float, float, float]]]],
    config: CryptoPairsConfig,
) -> tuple[int, float]:
    """(round trips, exposure) across one or more independently-run segments.

    A round trip is a flat -> in-position transition of the PAIR, read off leg A: the two
    legs are opened and closed together by construction (`_targets_for_side` emits +w and
    -w in one call), so leg A's position is a faithful state variable for the pair. A side
    FLIP (long spread straight to short spread) is one close and one open on the same bar
    and counts as one new round trip, which is what it costs.

    Segments matter for chained stitching (D123): each window is its own `run_backtest`
    with its own portfolio, so a position open at a window's end simply CEASES — there is
    no closing fill. Reconstructing across the seam from one cumulative fill stream would
    carry a phantom position into the next window and undercount round trips; per-segment
    reconstruction is what makes the free-liquidation artifact visible instead of hidden."""
    round_trips, held_bars, total_bars = 0, 0, 0
    for timestamps, fills in segments:
        walk = _position_walk(timestamps, fills, config.symbol_a)
        in_position = [abs(q) > 0 for q in walk]
        round_trips += sum(
            1 for i, held in enumerate(in_position) if held and (i == 0 or not in_position[i - 1])
        )
        round_trips += sum(
            1 for a, b in zip(walk, walk[1:]) if a != 0 and b != 0 and (a > 0) != (b > 0)
        )
        held_bars += sum(in_position)
        total_bars += len(in_position)
    return round_trips, (held_bars / total_bars if total_bars else float("nan"))


def run_variant(
    series: Mapping[str, Sequence[TimestampedBar]],
    variant: PairsVariant,
    tier: CostTier,
    config: CryptoPairsConfig,
) -> VariantResult:
    """One (variant, tier) out-of-sample result, in whichever stitching mode the variant
    resolves to. Both modes produce the same OOS timestamps and the same number of
    returns, so every downstream metric compares like with like."""
    resolved = variant.resolve(config)
    spans = window_spans(series, resolved)
    oos_start, oos_end = spans[0][2], spans[-1][3]
    stack_config = pair_cost_stack_config(
        tier, resolved.borrow_annual_rate, resolved.margin_annual_rate
    )
    stack, ledger = recording_cost_stack(build_pair_cost_stack(stack_config))
    instruments = _instruments(resolved)
    warm_up = variant.lookback
    """The strategy stands aside while it has fewer than lookback+1 visible bars (D69),
    so a prefix of exactly `lookback` bars is provably flat and the first decision bar is
    the first true OOS bar — the same rule D113 states for the breakout study, and it is
    asserted below rather than trusted."""

    if oos_start - warm_up < 0:
        raise ValueError(
            f"variant {variant.name!r} needs {warm_up} warm-up bars before the first OOS bar at "
            f"index {oos_start}, but only {oos_start} are available — widen train_size or "
            "shorten the lookback"
        )

    equity: list[tuple[datetime, float]] = []
    fills: list[tuple[datetime, str, float, float, float]] = []
    segments: list[tuple[list[datetime], list[tuple[datetime, str, float, float, float]]]] = []

    if resolved.stitch == "continuous":
        run_start = oos_start - warm_up
        run_bars = {s: list(series[s][run_start:oos_end]) for s in resolved.symbols}
        result = run_backtest(
            bars_by_instrument=run_bars,
            instruments=instruments,
            strategies=[variant.build_strategy(resolved)],
            cost_stack=stack,
            allocator=ConstantSplitAllocator(),
            starting_cash=resolved.starting_cash,
            fill_timing=resolved.fill_timing,
        )
        prefix_timestamps = {tb.timestamp for tb in run_bars[resolved.symbol_a][:warm_up]}
        leaked = [f for f in result.fills if f[0] in prefix_timestamps]
        if leaked:
            raise ValueError(
                f"variant {variant.name!r} traded {len(leaked)} time(s) during the warm-up prefix "
                f"(first at {leaked[0][0].isoformat()}) — in-sample P&L would leak into the OOS "
                "curve; the prefix must equal the strategy's warm-up requirement (D123)"
            )
        equity = list(result.equity_curve[warm_up:])
        fills = [f for f in result.fills if f[0] not in prefix_timestamps]
        segments.append(([ts for ts, _ in equity], fills))
    else:
        capital = resolved.starting_cash
        for _index, _train_start, test_start, test_end in spans:
            lo = test_start - warm_up
            run_bars = {s: list(series[s][lo:test_end]) for s in resolved.symbols}
            result = run_backtest(
                bars_by_instrument=run_bars,
                instruments=instruments,
                strategies=[variant.build_strategy(resolved)],
                cost_stack=stack,
                allocator=ConstantSplitAllocator(),
                starting_cash=capital,
                fill_timing=resolved.fill_timing,
            )
            prefix_timestamps = {tb.timestamp for tb in run_bars[resolved.symbol_a][:warm_up]}
            leaked = [f for f in result.fills if f[0] in prefix_timestamps]
            if leaked:
                raise ValueError(
                    f"variant {variant.name!r} traded during a chained window's warm-up prefix "
                    f"(first at {leaked[0][0].isoformat()}) — in-sample P&L would leak (D123)"
                )
            window_equity = list(result.equity_curve[warm_up:])
            window_fills = [f for f in result.fills if f[0] not in prefix_timestamps]
            equity.extend(window_equity)
            fills.extend(window_fills)
            segments.append(([ts for ts, _ in window_equity], window_fills))
            capital = result.final_nav

    expected = [tb.timestamp for tb in series[resolved.symbol_a][oos_start:oos_end]]
    if [ts for ts, _ in equity] != expected:
        raise ValueError("OOS equity curve timestamps do not match the walk-forward test span")

    returns = [b / a - 1.0 for (_, a), (_, b) in zip(equity, equity[1:])]
    index_in_oos = {ts: i for i, (ts, _) in enumerate(equity)}
    window_sharpes: dict[int, float] = {}
    window_final_nav: dict[int, float] = {}
    for window_index, _train_start, test_start, test_end in spans:
        lo = index_in_oos[series[resolved.symbol_a][test_start].timestamp]
        hi = index_in_oos[series[resolved.symbol_a][test_end - 1].timestamp]
        navs = [nav for _, nav in equity[lo : hi + 1]]
        window_final_nav[window_index] = navs[-1]
        segment = [b / a - 1.0 for a, b in zip(navs, navs[1:])]
        if len(set(segment)) > 1:
            window_sharpes[window_index] = sharpe(
                segment, resolved.rf_annual, resolved.periods_per_year
            ) / math.sqrt(resolved.periods_per_year)

    round_trips, exposure = _episode_stats(segments, resolved)
    return VariantResult(
        variant=variant,
        tier=tier,
        resolved=resolved,
        oos_equity=equity,
        oos_returns=returns,
        window_sharpes_daily=window_sharpes,
        window_final_nav=window_final_nav,
        ledger=ledger,
        oos_fills=fills,
        n_round_trips=round_trips,
        n_fills=len(fills),
        exposure=exposure,
        traded_notional=sum(abs(q * p) for _ts, _s, q, p, _c in fills),
        avg_nav=float(np.mean([nav for _, nav in equity])),
        n_oos_bars=len(equity),
    )


def run_benchmarks(
    series: Mapping[str, Sequence[TimestampedBar]], tier: CostTier, config: CryptoPairsConfig
) -> dict[str, BenchmarkResult]:
    """Buy-and-hold each leg and a 50/50 basket, over the same OOS span at the same tier.

    The single-leg benchmarks are `breakout_study.run_benchmark` verbatim (D115: fixed
    QUANTITY, bought at the second OOS bar's open, fee paid on entry notional, marked at
    the final close). The basket is the arithmetic mean of the two curves, which is
    exactly a fixed-quantity 50/50 buy-and-hold with half the capital in each leg —
    `run_benchmark` is linear in `starting_cash` because both the quantity solved for and
    the proportional entry fee are, so averaging two full-capital curves and halving the
    capital are the same portfolio. Reused rather than reimplemented, per the brief.

    **This is a long-only benchmark for a market-neutral strategy.** Per D37 the honest
    primary hurdle is the risk-free rate (which every Sharpe here already carries); these
    columns answer "what did the beta you did not take do over the same span?"."""
    benchmark_config = config.benchmark_config()
    single = {
        symbol: run_benchmark(list(series[symbol]), symbol, tier, benchmark_config)
        for symbol in config.symbols
    }
    a, b = single[config.symbol_a], single[config.symbol_b]
    if [ts for ts, _ in a.oos_equity] != [ts for ts, _ in b.oos_equity]:
        raise ValueError("benchmark legs cover different spans — alignment was bypassed")
    basket_equity = [
        (ts, 0.5 * nav_a + 0.5 * nav_b)
        for (ts, nav_a), (_, nav_b) in zip(a.oos_equity, b.oos_equity)
    ]
    single["basket_5050"] = BenchmarkResult(
        symbol="basket_5050",
        tier=tier,
        oos_equity=basket_equity,
        oos_returns=[x / y - 1.0 for (_, y), (_, x) in zip(basket_equity, basket_equity[1:])],
    )
    return single


def realised_betas(
    result: VariantResult, benchmarks: Mapping[str, BenchmarkResult]
) -> dict[str, float]:
    """Realised beta of the strategy against each benchmark's returns (D37).

    For a market-neutral book the expectation is ~0, and the artifact says so next to the
    number. If it is not ~0, the market-neutral claim is falsified and that is the
    headline — which is why this is computed for every tier rather than mentioned once."""
    return {
        f"vs_{name}": realised_beta(result.oos_returns, benchmark.oos_returns)
        for name, benchmark in benchmarks.items()
    }


def _log_trials(
    registry: TrialRegistry,
    result: VariantResult,
    config: CryptoPairsConfig,
    snapshot_id: str,
    prefix: str,
    spans: Sequence[tuple[int, int, int, int]],
    series: Mapping[str, Sequence[TimestampedBar]],
    cointegration: CointegrationReport,
) -> None:
    resolved = result.resolved
    base_config = {
        **resolved.to_dict(),
        "tier": result.tier.name,
        "fee_bps": result.tier.fee_bps,
        "venue_role": result.tier.role,
        "cost_stack": pair_cost_stack_config(
            result.tier, resolved.borrow_annual_rate, resolved.margin_annual_rate
        ),
        **result.variant.describe(),
    }
    costs = result.cost_totals()
    registry.add_trial(
        trial_id=f"{prefix}-{result.tier.name}-{result.variant.name}",
        config={**base_config, "row_kind": "variant"},
        params={
            "n_oos_bars": result.n_oos_bars,
            "n_windows": len(spans),
            "n_pairs_tested": 1,
        },
        metrics={
            "final_nav": result.final_nav,
            "total_return": result.total_return,
            "oos_sharpe_daily": result.sharpe_daily(resolved),
            "oos_sharpe_annual": result.sharpe_annual(resolved),
            "max_drawdown": result.max_drawdown,
            "num_fills": result.n_fills,
            "round_trips": result.n_round_trips,
            "exposure": result.exposure,
            "annual_turnover": result.annual_turnover,
            "cost_fees": costs["fees"],
            "cost_borrow": costs["borrow"],
            "cost_margin": costs["margin"],
            **cointegration.to_metrics(),
        },
        snapshot_id=snapshot_id,
        seed=resolved.seed,
    )
    for window_index, _train_start, test_start, test_end in spans:
        metrics: dict[str, Any] = {"window_final_nav": result.window_final_nav[window_index]}
        if window_index in result.window_sharpes_daily:
            metrics["window_sharpe_daily"] = result.window_sharpes_daily[window_index]
        coint = cointegration.windows[window_index]
        metrics["train_adf_traded_spread"] = coint.adf_traded_spread
        metrics["train_engle_granger_beta"] = coint.engle_granger_beta
        registry.add_trial(
            trial_id=f"{prefix}-{result.tier.name}-{result.variant.name}-w{window_index:02d}",
            config={**base_config, "row_kind": "window", "window": window_index},
            params={
                "window_start": series[resolved.symbol_a][test_start].timestamp.date().isoformat(),
                "window_end": series[resolved.symbol_a][test_end - 1].timestamp.date().isoformat(),
            },
            metrics=metrics,
            snapshot_id=snapshot_id,
            seed=resolved.seed,
        )


def _dsr_for(
    registry: TrialRegistry,
    tier: CostTier,
    config: CryptoPairsConfig,
    results: Mapping[tuple[str, str], VariantResult],
    prefix: str,
) -> tuple[float, dict[str, Any]]:
    """DSR at one tier, pool = the strategy CONFIGURATIONS evaluated there (D116).

    Pool membership is decided on identity fields in the logged config (`row_kind`,
    `group`, `tier`) and never on the presence of a metric (D98's rule)."""
    pooled = [
        r
        for (_name, tier_name), r in results.items()
        if tier_name == tier.name and r.variant.group in DSR_POOL_GROUPS
    ]
    best = max(pooled, key=lambda r: r.sharpe_daily(r.resolved))
    returns = np.asarray(best.oos_returns, dtype=float)
    mu, sd = returns.mean(), returns.std(ddof=0)
    inputs: dict[str, Any] = {
        "observed_sr_daily": best.sharpe_daily(best.resolved),
        "best_variant": best.variant.name,
        "t": len(returns),
        "skew": float(np.mean((returns - mu) ** 3) / sd**3) if sd > 0 else 0.0,
        "kurt": float(np.mean((returns - mu) ** 4) / sd**4) if sd > 0 else 3.0,
    }

    def _in_pool(trial) -> bool:
        return (
            trial.config.get("row_kind") == "variant"
            and trial.config.get("tier") == tier.name
            and trial.config.get("group") in DSR_POOL_GROUPS
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
    pool = [t.metrics["oos_sharpe_daily"] for t in registry.all_trials() if _in_pool(t)]
    inputs["n_trials"] = len(pool)
    inputs["var_trials_daily"] = float(np.var(pool, ddof=1)) if len(pool) > 1 else float("nan")
    return dsr, inputs


def run_crypto_pairs_study(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    registry: TrialRegistry,
    snapshot_id: str,
    config: CryptoPairsConfig = CryptoPairsConfig(),
    tiers: Sequence[CostTier] = DEFAULT_TIERS,
    variants: Sequence[PairsVariant] | None = None,
    trial_id_prefix: str = "crypto-pairs-v1",
    progress: Callable[[str], None] | None = None,
) -> StudyResult:
    """Run every (variant, tier), log a variant row and one row per walk-forward window,
    and compute a per-tier DSR whose pool is the strategy configurations (D116)."""
    series = aligned_series(bars_by_symbol, config)
    spans = window_spans(series, config)
    oos_start, oos_end = spans[0][2], spans[-1][3]
    coint = cointegration_report(series, config)
    chosen = list(variants) if variants is not None else default_variants()

    results: dict[tuple[str, str], VariantResult] = {}
    benchmarks: dict[tuple[str, str], BenchmarkResult] = {}
    for tier in tiers:
        for name, benchmark in run_benchmarks(series, tier, config).items():
            benchmarks[(name, tier.name)] = benchmark
        for variant in chosen:
            if progress:
                progress(f"{tier.name} {variant.name}")
            result = run_variant(series, variant, tier, config)
            results[(variant.name, tier.name)] = result
            _log_trials(registry, result, config, snapshot_id, trial_id_prefix, spans, series, coint)

    dsr_by_tier, dsr_inputs_by_tier, betas_by_tier = {}, {}, {}
    baseline = baseline_name()
    for tier in tiers:
        dsr, inputs = _dsr_for(registry, tier, config, results, trial_id_prefix)
        dsr_by_tier[tier.name] = dsr
        dsr_inputs_by_tier[tier.name] = inputs
        betas_by_tier[tier.name] = realised_betas(
            results[(baseline, tier.name)],
            {name: benchmarks[(name, tier.name)] for name in (*config.symbols, "basket_5050")},
        )

    return StudyResult(
        config=config,
        snapshot_id=snapshot_id,
        tiers=tuple(tiers),
        variants=tuple(chosen),
        results=results,
        benchmarks=benchmarks,
        cointegration=coint,
        n_windows=len(spans),
        oos_start=series[config.symbol_a][oos_start].timestamp,
        oos_end=series[config.symbol_a][oos_end - 1].timestamp,
        n_oos_bars=oos_end - oos_start,
        window_test_spans=tuple(
            (
                index,
                series[config.symbol_a][test_start].timestamp,
                series[config.symbol_a][test_end - 1].timestamp,
            )
            for index, _train_start, test_start, test_end in spans
        ),
        dsr_by_tier=dsr_by_tier,
        dsr_inputs_by_tier=dsr_inputs_by_tier,
        betas_by_tier=betas_by_tier,
    )


# ------------------------------------------------------------------------ rendering


def _pct(x: float) -> str:
    return "n/a" if x != x else f"{x:+.2%}"


def _num(x: float, places: int = 2) -> str:
    return "n/a" if x != x else f"{x:.{places}f}"


def render_variant_table(
    result: StudyResult, tier_name: str, variant_names: Sequence[str]
) -> str:
    lines = [
        "| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Round trips | "
        "Exposure | Costs (fees / borrow / margin) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for name in variant_names:
        r = result.results[(name, tier_name)]
        costs = r.cost_totals()
        lines.append(
            f"| `{name}` | {_pct(r.total_return)} | "
            f"{_pct(cagr(r.total_return, r.n_oos_bars, result.config.periods_per_year))} | "
            f"{_num(r.sharpe_annual(r.resolved))} | {_num(r.max_drawdown * 100, 1)}% | "
            f"{r.n_round_trips} | {_num(r.exposure * 100, 1)}% | "
            f"{costs['fees']:,.0f} / {costs['borrow']:,.0f} / {costs['margin']:,.0f} |"
        )
    return "\n".join(lines)


def render_grid_surface(result: StudyResult, tier_name: str, metric: str = "sharpe") -> str:
    """The full lookback x entry_z surface, printed as a grid rather than a ranked list:
    a ranked list hides whether the best cell has good neighbours, which is the entire
    question a sensitivity surface exists to answer."""
    lines = [
        "| lookback \\ entry_z | " + " | ".join(f"{z:g}" for z in GRID_ENTRY_Z) + " |",
        "|---" * (len(GRID_ENTRY_Z) + 1) + "|",
    ]
    for lookback in GRID_LOOKBACKS:
        cells = []
        for entry_z in GRID_ENTRY_Z:
            r = result.results[(f"grid_lb{lookback}_z{entry_z:g}", tier_name)]
            if metric == "sharpe":
                cells.append(_num(r.sharpe_annual(r.resolved)))
            elif metric == "cagr":
                cells.append(_pct(cagr(r.total_return, r.n_oos_bars, result.config.periods_per_year)))
            elif metric == "round_trips":
                cells.append(str(r.n_round_trips))
            else:
                raise ValueError(f"unknown grid metric {metric!r}")
        lines.append(f"| **{lookback}** | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def grid_spread(result: StudyResult, tier_name: str) -> dict[str, float]:
    """"Plateau or spike?", without eyeballing the grid: the best cell, the mean of its
    immediate neighbours, and the gap between them in units of the surface's own spread."""
    sharpes = {
        (lookback, entry_z): result.results[
            (f"grid_lb{lookback}_z{entry_z:g}", tier_name)
        ].sharpe_annual(result.config)
        for lookback in GRID_LOOKBACKS
        for entry_z in GRID_ENTRY_Z
    }
    best_key = max(sharpes, key=lambda k: sharpes[k])
    lookbacks, zs = list(GRID_LOOKBACKS), list(GRID_ENTRY_Z)
    li, zi = lookbacks.index(best_key[0]), zs.index(best_key[1])
    neighbours = [
        sharpes[(lookbacks[i], zs[j])]
        for i in (li - 1, li, li + 1)
        for j in (zi - 1, zi, zi + 1)
        if 0 <= i < len(lookbacks) and 0 <= j < len(zs) and (i, j) != (li, zi)
    ]
    values = list(sharpes.values())
    spread = max(values) - min(values)
    best, neighbour_mean = sharpes[best_key], sum(neighbours) / len(neighbours)
    return {
        "best_lookback": float(best_key[0]),
        "best_entry_z": float(best_key[1]),
        "best_sharpe": best,
        "neighbour_mean_sharpe": neighbour_mean,
        "worst_sharpe": min(values),
        "surface_spread": spread,
        "best_minus_neighbours_over_spread": (best - neighbour_mean) / spread if spread else 0.0,
        "n_cells": float(len(sharpes)),
    }


def render_tier_table(result: StudyResult, variant_name: str) -> str:
    """One variant across every cost tier — the maker-versus-taker question, isolated."""
    lines = [
        "| Tier | Fee | Role | Total return | CAGR | Sharpe (ann.) | Max DD | "
        "Fees paid | Borrow paid | Margin paid |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for tier in result.tiers:
        r = result.results[(variant_name, tier.name)]
        costs = r.cost_totals()
        lines.append(
            f"| `{tier.name}` | {tier.fee_bps / 100:.2f}% | {tier.role} | {_pct(r.total_return)} | "
            f"{_pct(cagr(r.total_return, r.n_oos_bars, result.config.periods_per_year))} | "
            f"{_num(r.sharpe_annual(r.resolved))} | {_num(r.max_drawdown * 100, 1)}% | "
            f"{costs['fees']:,.0f} | {costs['borrow']:,.0f} | {costs['margin']:,.0f} |"
        )
    return "\n".join(lines)


def render_benchmark_table(result: StudyResult, tier_name: str, variant_name: str) -> str:
    config = result.config
    r = result.results[(variant_name, tier_name)]
    lines = [
        "| Series | Total return | CAGR | Sharpe (ann., rf=4%) | Max DD | Realised beta of strategy |",
        "|---|---|---|---|---|---|",
        f"| **strategy `{variant_name}`** | {_pct(r.total_return)} | "
        f"{_pct(cagr(r.total_return, r.n_oos_bars, config.periods_per_year))} | "
        f"{_num(r.sharpe_annual(r.resolved))} | {_num(r.max_drawdown * 100, 1)}% | — |",
    ]
    betas = result.betas_by_tier[tier_name]
    # BenchmarkResult is the breakout study's type, so its Sharpe takes that study's
    # config object (D115). `benchmark_config()` is this study's rf/calendar/window
    # geometry in that shape — the same numbers, not a second set.
    benchmark_config = config.benchmark_config()
    for name in (*config.symbols, "basket_5050"):
        b = result.benchmarks[(name, tier_name)]
        lines.append(
            f"| buy & hold {name} | {_pct(b.total_return)} | "
            f"{_pct(cagr(b.total_return, len(b.oos_equity), config.periods_per_year))} | "
            f"{_num(b.sharpe_annual(benchmark_config))} | {_num(b.max_drawdown * 100, 1)}% | "
            f"{betas[f'vs_{name}']:+.4f} |"
        )
    return "\n".join(lines)


def render_cointegration_table(result: StudyResult) -> str:
    coint = result.cointegration
    n = len(coint.windows)
    lines = [
        "| Test | Threshold | Windows cointegrated | Rate |",
        "|---|---|---|---|",
    ]
    for level in ("1%", "5%", "10%"):
        lines.append(
            f"| traded 1:1 log spread (DF tau_mu) | {DF_TAU_MU_CRITICAL[level]:.4f} ({level}) | "
            f"{coint.count(level)} / {n} | {coint.rate(level):.1%} |"
        )
    for level in ("1%", "5%", "10%"):
        lines.append(
            f"| Engle-Granger residual | {ENGLE_GRANGER_CRITICAL[level]:.2f} ({level}) | "
            f"{coint.count(level, 'engle_granger')} / {n} | "
            f"{coint.rate(level, 'engle_granger'):.1%} |"
        )
    return "\n".join(lines)


def render_window_cointegration_table(result: StudyResult) -> str:
    lines = [
        "| Window | Train span | ADF (traded 1:1 spread) | EG beta | ADF (EG residual) | Cointegrated @5%? |",
        "|---|---|---|---|---|---|",
    ]
    for w in result.cointegration.windows:
        verdict = []
        if w.traded_spread_cointegrated_at("5%"):
            verdict.append("1:1")
        if w.engle_granger_cointegrated_at("5%"):
            verdict.append("EG")
        lines.append(
            f"| {w.window} | {w.train_start.date()} → {w.train_end.date()} | "
            f"{w.adf_traded_spread:+.3f} | {w.engle_granger_beta:+.3f} | "
            f"{w.engle_granger_adf:+.3f} | {', '.join(verdict) if verdict else '—'} |"
        )
    return "\n".join(lines)

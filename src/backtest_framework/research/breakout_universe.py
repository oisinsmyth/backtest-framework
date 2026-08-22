"""Cross-sectional breakout study over a broad crypto universe (D140–D144).

This module is **study glue only**. Every load-bearing computation is imported
unchanged from `research.breakout_study` — `run_variant`, `run_benchmark`,
`run_constant_fraction_benchmark`, `breakout_config`, `CostTier`, `DEFAULT_TIERS`,
`annual_breakdown`, `start_date_sensitivity`, `sharpe_difference_bootstrap`. Nothing
about the engine, the walk-forward geometry, the cost tiers or the diagnostics is
re-implemented or forked here; if a number in this study disagrees with the BTC/ETH
study it is because the data disagreed, not because the machinery did.

## What this study exists to do (D140)

`BREAKOUT_RESULTS.md` names its own largest bias in its caveats: "BTC and ETH are the
two crypto assets that survived to be worth studying ... the single largest
un-deflatable bias in this document." Adding twenty more of *today's* largest coins
would restate that bias at greater scale. So the universe is built to contain the
assets that **failed** — tokens that fell 90%+ from their own peak and never came back,
tokens whose provider stopped serving bars at all — and every statistic is reported
twice: once across the whole cross-section, and once split **survived vs
collapsed/delisted**. That split is the study's headline, and it is the only way the
bias becomes a measurement rather than a disclaimer.

## The selection policy is mechanical, and it is applied twice

`UniversePolicy` is a pre-stated, mechanical screen: all-positive prices, a peg screen,
minimum history, a liquidity floor. `apply_policy` is the single implementation of it. The
fetch script (`scripts/fetch_crypto_universe.py`) runs it to decide what goes in the
fixture and records every exclusion with its reason in the fixture meta; the study
runs it *again* on the committed fixture and refuses to hand the engine any symbol
that fails. A symbol cannot reach `run_variant` by being quietly present in a CSV.

Both applications screen the **cleaned** series (D25's `clean`), not the raw one, for
the obvious reason: the engine trades cleaned bars, so the screen must describe cleaned
bars. Dropping a symbol for a single bad print the cleaner already removes would be a
data-quality accident dressed up as a universe rule.

## Alignment (D45/D64)

Each symbol is its own single-instrument backtest — the N=1 case of D64 — so no
symbol is truncated to another's inception. D45's inner-join rule never binds here,
which is exactly why the fixture is deliberately NOT inner-joined.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from ..data.bars import TimestampedBar
from ..registry.trial_registry import TrialRegistry
from ..validation.dsr import deflated_sharpe_from_trials
from . import breakout_study as bs

# ------------------------------------------------------------------ status labels

SURVIVED = "survived"
COLLAPSED = "collapsed"
DELISTED = "delisted"
COLLAPSED_BUCKET: tuple[str, ...] = (COLLAPSED, DELISTED)
"""`collapsed` and `delisted` are reported as one bucket against `survived`. They are
kept as separate labels because they are different failures — one is an asset that is
still quoted at 0.1% of its peak, the other is an asset the data provider stopped
serving — and a reader should be able to see which is which."""


# ------------------------------------------------------------------------- policy


@dataclass(frozen=True)
class UniversePolicy:
    """The pre-stated inclusion screen (D140). Every field is a threshold with a
    stated derivation, not a tuned knob — and every symbol it rejects is reported by
    name with the statistic that rejected it.

    **This policy screens for tradability and for data adequacy. It does NOT screen on
    anything the strategy produced.** No return, Sharpe, drawdown or trade count enters
    it. That is the difference between a universe rule and a survivorship filter."""

    min_bars: int = 520
    """Minimum daily bars a symbol must carry to enter the study.

    The mechanical floor is lower: the harness takes its warm-up prefix from *inside*
    window 0's training slice, so `train_size + test_size` = 315 bars already produce
    one walk-forward window even for the longest lookback the study family uses (a
    200-day SMA gate, 201 bars, which fits inside the 252-bar training slice). 315
    bars would therefore be the honest mechanical minimum — and it would also be a
    useless one: a single 63-bar test window is ten weeks of out-of-sample data for a
    strategy whose median holding period is roughly four weeks, i.e. one or two trades.

    520 bars is the shortest history that yields **four windows and a full year (252
    bars) of out-of-sample data** (252 + 4x63 = 504, and 520 is the first round number
    above it). It is stated in bars, not in dates, so it applies identically to a coin
    that launched in 2017 and one that launched in 2021."""

    min_median_abs_daily_return: float = 0.005
    """Peg screen: the median absolute daily log return must be at least 0.5%.

    A trend-following universe cannot contain an instrument whose design pins its price
    to a constant. A pegged stablecoin never prints a 40-bar high, so the strategy never
    trades it, its return series is identically zero, and its Sharpe is not merely bad
    but **undefined** — which would poison the DSR pool's variance if it were imputed
    (exactly the failure D98 fixed one layer up).

    **This rule was added after the policy's first run, and that is stated rather than
    hidden.** The first run of the study raised loudly on `UST-USD` — TerraUSD, a
    stablecoin that reached the roster through the `sought_failures` cohort — because
    its Sharpe was -inf. The policy as first written had no clause for "is this
    instrument a candidate for trend following at all", which is a definitional gap, not
    a performance filter. It was amended once, before any performance number in this
    study had been read, and the threshold is set where nothing could plausibly turn on
    it: the pegged series sits at 0.14%/day and the *least* volatile real asset in the
    universe (BTC) at 1.42%/day, a factor of ten apart, with 0.5% in between. USTC — the
    same token after it depegged and started floating — sits at 1.52% and stays in, in
    the collapsed bucket, which is where it belongs."""

    min_median_daily_volume_usd: float = 5_000_000.0
    """Liquidity floor on the **median** daily volume over the symbol's own history,
    in the fixture's volume column. For `X-USD` crypto pairs the provider reports
    volume in the quote currency, i.e. USD notional.

    Median rather than mean, deliberately: crypto volume is spiked hard by launch
    weeks and collapse weeks, and a mean is a statistic about those few days rather
    than about a typical trading day.

    Derivation of the level: the study starts with 100,000 USD and the sizing brick
    caps a position at 1.0x capital, so the largest opening order at the start of a run
    is ~100,000 USD. A 5,000,000 USD median day puts that order at 2% of a typical
    day's volume — the region where this framework's own capacity study (D95) treats
    unmodelled market impact as second-order. It is a floor on *tradability*, and it
    binds hardest on exactly the small tokens whose backtest numbers would otherwise be
    the most flattering and the least real.

    It has a second, unplanned effect worth stating: it also rejects provider garbage.
    Several yfinance crypto tickers are ticker-symbol collisions serving a stale or
    near-zero series with a handful of dollars of daily volume, and this screen removes
    them without anyone having to eyeball a chart."""

    collapse_terminal_drawdown: float = 0.90
    """Classification threshold, NOT an inclusion threshold. A symbol whose final close
    sits at or below 10% of its own highest close inside the fixture range is labelled
    `collapsed`. 90% is the conventional "this asset failed" line for crypto, and it is
    applied to the symbol's own peak so it is scale-free.

    This is computed **with hindsight, on purpose** — see `SymbolCoverage`. It is a
    conditioning variable used to split results after the fact, never a selection
    variable used to decide what gets traded."""

    delisted_gap_days: int = 90
    """A symbol whose last bar is more than this many days before the fixture's end
    date is labelled `delisted`: the provider stopped serving it. Checked before the
    drawdown rule, so a token that was delisted *and* down 99% is reported as the
    former — losing the quote is the more specific fact."""

    def to_dict(self) -> dict[str, Any]:
        return {
            "min_bars": self.min_bars,
            "min_median_abs_daily_return": self.min_median_abs_daily_return,
            "min_median_daily_volume_usd": self.min_median_daily_volume_usd,
            "collapse_terminal_drawdown": self.collapse_terminal_drawdown,
            "delisted_gap_days": self.delisted_gap_days,
        }


DEFAULT_POLICY = UniversePolicy()


@dataclass(frozen=True)
class SymbolCoverage:
    """Everything the policy needs to know about one symbol, computed from bars and
    volumes alone. Deliberately separated from the screen itself so the numbers behind
    an exclusion can be reported next to it."""

    symbol: str
    n_bars: int
    first_bar: datetime
    last_bar: datetime
    median_daily_volume: float
    mean_daily_volume: float
    median_abs_daily_return: float
    peak_close: float
    final_close: float
    terminal_drawdown: float
    """1 - final close / highest close, over the symbol's whole fixture history. The
    label this feeds is hindsight by construction and is used only to SPLIT results."""
    n_nonpositive_bars: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "n_bars": self.n_bars,
            "first_bar": self.first_bar.date().isoformat(),
            "last_bar": self.last_bar.date().isoformat(),
            "median_daily_volume": self.median_daily_volume,
            "mean_daily_volume": self.mean_daily_volume,
            "median_abs_daily_return": self.median_abs_daily_return,
            "peak_close": self.peak_close,
            "final_close": self.final_close,
            "terminal_drawdown": self.terminal_drawdown,
            "n_nonpositive_bars": self.n_nonpositive_bars,
        }


def coverage_for(
    symbol: str, bars: Sequence[TimestampedBar], volumes: Sequence[float]
) -> SymbolCoverage:
    if not bars:
        raise ValueError(f"{symbol}: no bars — an empty series must be reported as a fetch failure")
    if len(volumes) != len(bars):
        raise ValueError(
            f"{symbol}: {len(bars)} bars but {len(volumes)} volumes — the fixture rows are misaligned"
        )
    closes = [tb.bar.close for tb in bars]
    clean_volumes = [v for v in volumes if v == v]  # NaN means "no volume column"
    peak = max(closes)
    final = closes[-1]
    moves = [
        abs(math.log(b / a)) for a, b in zip(closes, closes[1:]) if a > 0 and b > 0
    ]
    nonpositive = sum(
        1
        for tb in bars
        if min(tb.bar.open, tb.bar.high, tb.bar.low, tb.bar.close) <= 0.0
    )
    return SymbolCoverage(
        symbol=symbol,
        n_bars=len(bars),
        first_bar=bars[0].timestamp,
        last_bar=bars[-1].timestamp,
        median_daily_volume=statistics.median(clean_volumes) if clean_volumes else float("nan"),
        mean_daily_volume=statistics.fmean(clean_volumes) if clean_volumes else float("nan"),
        median_abs_daily_return=statistics.median(moves) if moves else float("nan"),
        peak_close=peak,
        final_close=final,
        terminal_drawdown=1.0 - final / peak if peak > 0 else float("nan"),
        n_nonpositive_bars=nonpositive,
    )


def align_volumes(
    bars: Sequence[TimestampedBar],
    raw_bars: Sequence[TimestampedBar],
    raw_volumes: Sequence[float],
) -> list[float]:
    """Re-index a raw volume series onto a CLEANED bar series, by timestamp.

    `clean()` (D25) returns bars only — it drops bad prints and reports them, but the
    volume list it was handed is not re-indexed, so after any drop the two are
    misaligned by construction. That is an existing interface and this study does not
    get to change it (D111's precedent), so the re-indexing happens here instead:
    cleaning only ever removes bars, never adds or reorders them, so a timestamp lookup
    is exact. Raises if a cleaned timestamp is absent from the raw series, because that
    would mean the two series are not the same data."""
    if len(raw_bars) != len(raw_volumes):
        raise ValueError(
            f"raw series has {len(raw_bars)} bars but {len(raw_volumes)} volumes — misaligned input"
        )
    by_timestamp = {tb.timestamp: v for tb, v in zip(raw_bars, raw_volumes)}
    missing = [tb.timestamp for tb in bars if tb.timestamp not in by_timestamp]
    if missing:
        raise ValueError(
            f"{len(missing)} cleaned bar(s) have no raw volume (first {missing[0].isoformat()}) — "
            "the cleaned and raw series are not the same data"
        )
    return [by_timestamp[tb.timestamp] for tb in bars]


def classify(coverage: SymbolCoverage, policy: UniversePolicy, end_date: date) -> str:
    """`survived` / `collapsed` / `delisted`, from the coverage statistics alone.

    Hindsight, stated plainly: every one of these labels uses information from the end
    of the sample. That is legitimate here and only here — the label is not used to
    decide what is traded, it is used to split results that were produced identically
    for every symbol."""
    if coverage.last_bar.date() < end_date - timedelta(days=policy.delisted_gap_days):
        return DELISTED
    if coverage.terminal_drawdown >= policy.collapse_terminal_drawdown:
        return COLLAPSED
    return SURVIVED


def screen(coverage: SymbolCoverage, policy: UniversePolicy) -> str | None:
    """The exclusion reason, or None if the symbol is included. Rules are applied in a
    fixed order and the FIRST failure is reported, so an exclusion reason is
    deterministic; the full statistics travel alongside it so a reader can see whether
    a symbol also failed a later rule."""
    if coverage.n_nonpositive_bars:
        return (
            f"{coverage.n_nonpositive_bars} bar(s) with a non-positive price — log returns and "
            "inverse-vol sizing are undefined on them"
        )
    if not (coverage.median_abs_daily_return >= policy.min_median_abs_daily_return):
        # No pipe characters in any reason string: these land verbatim in markdown
        # tables in the report, and a stray "|" silently breaks the row.
        return (
            f"median absolute daily return {coverage.median_abs_daily_return:.3%} < required "
            f"{policy.min_median_abs_daily_return:.3%} — a pegged instrument is not a "
            "trend-following candidate (peg screen)"
        )
    if coverage.n_bars < policy.min_bars:
        return f"{coverage.n_bars} bars < required {policy.min_bars} (min-history rule)"
    if not (coverage.median_daily_volume >= policy.min_median_daily_volume_usd):
        return (
            f"median daily volume {coverage.median_daily_volume:,.0f} USD < required "
            f"{policy.min_median_daily_volume_usd:,.0f} (liquidity floor)"
        )
    return None


@dataclass(frozen=True)
class UniverseSelection:
    policy: UniversePolicy
    end_date: date
    included: tuple[str, ...]
    excluded: dict[str, str]
    """symbol -> exclusion reason, for every symbol that had bars but failed the screen."""
    coverage: dict[str, SymbolCoverage]
    status: dict[str, str]
    """symbol -> survived / collapsed / delisted, for INCLUDED symbols only."""

    def in_bucket(self, bucket: Sequence[str]) -> tuple[str, ...]:
        return tuple(s for s in self.included if self.status[s] in bucket)

    @property
    def survived(self) -> tuple[str, ...]:
        return self.in_bucket((SURVIVED,))

    @property
    def collapsed(self) -> tuple[str, ...]:
        return self.in_bucket(COLLAPSED_BUCKET)

    def to_dict(self) -> dict[str, Any]:
        return {
            "policy": self.policy.to_dict(),
            "end_date": self.end_date.isoformat(),
            "included": list(self.included),
            "excluded": dict(self.excluded),
            "status": dict(self.status),
            "coverage": {s: c.to_dict() for s, c in self.coverage.items()},
        }


def apply_policy(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]],
    policy: UniversePolicy = DEFAULT_POLICY,
    end_date: date = date(2025, 12, 31),
) -> UniverseSelection:
    """The one implementation of the universe policy. Run at fetch time to decide the
    fixture's contents, and run again at study time on the committed fixture so a
    symbol that fails the screen can never reach the engine by being present in a CSV.

    Both callers hand it CLEANED bars (D25) with volumes re-indexed by `align_volumes`,
    so the screen describes the series the engine will actually trade."""
    coverage: dict[str, SymbolCoverage] = {}
    included: list[str] = []
    excluded: dict[str, str] = {}
    status: dict[str, str] = {}
    for symbol in sorted(bars_by_symbol):
        cov = coverage_for(symbol, bars_by_symbol[symbol], volumes_by_symbol.get(symbol, []))
        coverage[symbol] = cov
        reason = screen(cov, policy)
        if reason is None:
            included.append(symbol)
            status[symbol] = classify(cov, policy, end_date)
        else:
            excluded[symbol] = reason
    return UniverseSelection(
        policy=policy,
        end_date=end_date,
        included=tuple(included),
        excluded=excluded,
        coverage=coverage,
        status=status,
    )


# -------------------------------------------------------------------------- study

BASELINE_VARIANT = f"plateau_{bs.BASELINE_N_ENTRY}_{bs.BASELINE_N_EXIT}"
"""The ONLY configuration this study runs, at every symbol and every tier (D141).

No per-coin parameter sweep. The BTC/ETH study already established that the plateau is
flat and that in-training selection did not pay; re-sweeping 12 grid cells per coin
would multiply the multiplicity by twelve to answer a question that has been asked and
answered. The variable here is the cross-section, and holding the rule fixed is what
makes it the only variable."""


def baseline_variant() -> bs.Variant:
    return bs.Variant(
        BASELINE_VARIANT,
        "plateau",
        fixed_config=bs.breakout_config(bs.BASELINE_N_ENTRY, bs.BASELINE_N_EXIT),
    )


PUBLISHED_PRECISION: dict[str, float] = {
    "total_return": 0.00005,      # printed as +5657.04% — four decimals of a ratio
    "sharpe_annual": 0.005,       # printed as 1.20
    "max_drawdown": 0.0005,       # printed as 43.0%
    "exposure": 0.0005,           # printed as 36.7%
    "n_closed_trades": 0.0,       # printed as an integer, so exact
    "hold_return": 0.00005,       # printed as +42386.71%
    "matched_return": 0.0005,     # printed as +1357.6% — one decimal of a percentage
}
"""Half a unit of the last digit `BREAKOUT_RESULTS.md` actually prints for each metric.

The comparison below is stated as an ABSOLUTE tolerance per metric rather than one blanket
relative tolerance, because the published document reports each number at a different
precision — a Sharpe to two decimals and a total return to four. A single relative
tolerance would either be too loose for the returns or would fail on the Sharpe purely
because the source rounds it, which is a transcription artifact and not a data event."""

PUBLISHED_BTC_ETH_REFERENCE: dict[str, dict[str, float]] = {
    "BTC-USD": {
        "total_return": 56.5704,
        "sharpe_annual": 1.20,
        "max_drawdown": 0.4301,
        "exposure": 0.367,
        "n_closed_trades": 38.0,
        "hold_return": 423.8671,
        "matched_return": 13.576,
    },
    "ETH-USD": {
        "total_return": 5.5221,
        "sharpe_annual": 0.78,
        "max_drawdown": 0.3518,
        "exposure": 0.328,
        "n_closed_trades": 28.0,
        "hold_return": 5.0091,
        "matched_return": 1.980,
    },
}
"""The `plateau_40_10` @ `taker_40bp` rows published in `BREAKOUT_RESULTS.md`, transcribed
here as the reconciliation target for this study's own BTC and ETH runs.

This is an independence check with real teeth. The two studies share the strategy code and
the harness, but **not the data**: the BTC/ETH study reads
`crypto_daily_2015_2025_raw.csv.gz` and this one reads
`crypto_universe_2015_2025_raw.csv.gz`, fetched separately, months apart in wall-clock
terms, from a provider that restates history (D24's whole rationale). If the overlapping
rows agree to the printed precision, the universe fixture is the same underlying data and
the cross-section's numbers can be read against the published ones directly. If they ever
diverge, that is a *data* event worth knowing about — the provider restated, or one of the
two fixtures is stale — and the test that pins this fails loudly rather than leaving two
documents quietly quoting different BTC histories."""


def reconcile_against_published(
    result: UniverseResult, tier_name: str = bs.REFERENCE_TIER
) -> dict[str, dict[str, float]]:
    """Per symbol and metric, the **absolute difference in units of the published
    precision**: 1.0 means "off by exactly the last digit the source prints", so anything
    below 1.0 is agreement to the precision `BREAKOUT_RESULTS.md` actually states.
    Returns {} for symbols absent from the cross-section."""
    study = result.config
    out: dict[str, dict[str, float]] = {}
    for symbol, reference in PUBLISHED_BTC_ETH_REFERENCE.items():
        if symbol not in result.runs:
            continue
        t = result.runs[symbol].by_tier[tier_name]
        actual = {
            "total_return": t.variant.total_return,
            "sharpe_annual": t.variant.sharpe_annual(study),
            "max_drawdown": t.variant.max_drawdown,
            "exposure": t.variant.diagnostics.exposure,
            "n_closed_trades": float(t.variant.diagnostics.n_closed_trades),
            "hold_return": t.hold.total_return,
            "matched_return": float("nan") if t.matched is None else t.matched.total_return,
        }
        out[symbol] = {
            key: (
                abs(actual[key] - expected) / PUBLISHED_PRECISION[key]
                if PUBLISHED_PRECISION[key]
                else abs(actual[key] - expected)
            )
            for key, expected in reference.items()
        }
    return out


def risk_free_return(n_bars: int, study: bs.BreakoutStudyConfig) -> float:
    """The third benchmark: cash at the study's own risk-free rate over the same span.
    Trivial arithmetic, stated as a function so the report and the registry cannot
    disagree about it."""
    return (1.0 + study.rf_annual) ** (n_bars / study.periods_per_year) - 1.0


@dataclass
class TierRun:
    """One (symbol, tier): the strategy and all three benchmarks over the same span."""

    tier: bs.CostTier
    variant: bs.VariantResult
    hold: bs.BenchmarkResult
    matched: bs.BenchmarkResult | None
    """Constant-fraction at the strategy's own average exposure (D119). None when the
    strategy never took a position at all — a constant fraction of zero is not a
    benchmark, it is cash, and the risk-free row already says that."""
    rf_return: float

    @property
    def beats_hold(self) -> bool:
        return self.variant.total_return > self.hold.total_return

    @property
    def beats_matched(self) -> bool | None:
        return None if self.matched is None else self.variant.total_return > self.matched.total_return

    @property
    def beats_rf(self) -> bool:
        return self.variant.total_return > self.rf_return

    @property
    def reduces_drawdown(self) -> bool:
        return self.variant.max_drawdown < self.hold.max_drawdown


@dataclass
class SymbolRun:
    symbol: str
    cohort: str
    status: str
    coverage: SymbolCoverage
    n_windows: int
    oos_start: datetime
    oos_end: datetime
    n_oos_bars: int
    by_tier: dict[str, TierRun]


@dataclass
class UniverseResult:
    config: bs.BreakoutStudyConfig
    snapshot_id: str
    selection: UniverseSelection
    cohorts: dict[str, str]
    tiers: tuple[bs.CostTier, ...]
    runs: dict[str, SymbolRun]
    dsr_by_tier: dict[str, float]
    dsr_inputs_by_tier: dict[str, dict[str, Any]]

    @property
    def symbols(self) -> tuple[str, ...]:
        return tuple(self.runs)

    def bucket(self, bucket: Sequence[str]) -> tuple[str, ...]:
        return tuple(s for s in self.runs if self.runs[s].status in bucket)

    @property
    def n_oos_trials(self) -> int:
        return sum(len(r.by_tier) for r in self.runs.values())


def run_universe_study(
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    volumes_by_symbol: Mapping[str, Sequence[float]],
    registry: TrialRegistry,
    snapshot_id: str,
    cohorts: Mapping[str, str],
    study: bs.BreakoutStudyConfig = bs.BreakoutStudyConfig(),
    tiers: Sequence[bs.CostTier] = bs.DEFAULT_TIERS,
    policy: UniversePolicy = DEFAULT_POLICY,
    end_date: date = date(2025, 12, 31),
    trial_id_prefix: str = "breakout-universe-v1",
    progress: Callable[[str], None] | None = None,
    variant: bs.Variant | None = None,
    compute_dsr: bool = True,
) -> UniverseResult:
    """Run ONE fixed configuration on every symbol the policy admits, at every cost tier,
    and log every run.

    The policy is applied HERE, on the data handed in — not trusted from the fixture
    meta. A symbol that fails the screen never reaches `run_variant`.

    `compute_dsr=False` skips the cross-sectional deflated Sharpe. Only the capacity sweep
    (D186) passes it: that study deflates against the LONG BOOK's published trial pool —
    the search that actually selected the configuration — rather than against a pool of
    62 symbols running the same configuration, which is a cross-section and not a search.
    It also has to, because at large AUM impact makes some coins untradeable, their return
    series go flat, and their Sharpe is undefined. `_dsr_for` refuses that pool and is
    right to; a study whose FINDING is "coins go inert at size" must not be blocked by a
    guard against inert coins, so it counts them and reports them instead.

    `variant` defaults to the long book's published baseline, which is what this study
    was built for. It is a parameter so the SHORT book's stop comparison (D174) can reuse
    this machinery unchanged rather than fork it — the whole point of D141's
    one-configuration-across-the-cross-section rule is that the configuration is fixed
    BEFORE it meets the universe, and that holds whichever configuration it is."""
    selection = apply_policy(bars_by_symbol, volumes_by_symbol, policy, end_date)
    variant = variant if variant is not None else baseline_variant()
    runs: dict[str, SymbolRun] = {}

    for symbol in selection.included:
        bars = bars_by_symbol[symbol]
        spans = bs._window_spans(bars, study)
        if not spans:
            raise ValueError(
                f"{symbol} passed the {policy.min_bars}-bar min-history rule with "
                f"{len(bars)} bars but produced no walk-forward window — the policy and the "
                "harness disagree, which must never be papered over"
            )
        by_tier: dict[str, TierRun] = {}
        for tier in tiers:
            if progress:
                progress(f"{symbol} {tier.name}")
            # Volumes were accepted by this function, used for the policy screen, and
            # then never handed to the run (D186). Harmless while nothing downstream
            # wanted them; the moment a cost tier charged square-root impact it became a
            # loud failure, which is the only reason it was found. Passed unconditionally
            # rather than "when needed" — a conditional is what hid it in the first place.
            result = bs.run_variant(
                bars, symbol, variant, tier, study, volumes=volumes_by_symbol.get(symbol)
            )
            vols = volumes_by_symbol.get(symbol)
            hold = bs.run_benchmark(bars, symbol, tier, study, volumes=vols)
            fraction = result.diagnostics.exposure
            matched = (
                bs.run_constant_fraction_benchmark(
                    bars, symbol, tier, study, fraction, volumes=vols
                )
                if fraction > 1e-9
                else None
            )
            by_tier[tier.name] = TierRun(
                tier=tier,
                variant=result,
                hold=hold,
                matched=matched,
                rf_return=risk_free_return(result.n_oos_bars, study),
            )
        runs[symbol] = SymbolRun(
            symbol=symbol,
            cohort=cohorts.get(symbol, "unknown"),
            status=selection.status[symbol],
            coverage=selection.coverage[symbol],
            n_windows=len(spans),
            oos_start=bars[spans[0][2]].timestamp,
            oos_end=bars[spans[-1][3] - 1].timestamp,
            n_oos_bars=spans[-1][3] - spans[0][2],
            by_tier=by_tier,
        )
        _log_symbol(registry, runs[symbol], study, snapshot_id, trial_id_prefix, selection, spans, bars)

    dsr_by_tier: dict[str, float] = {}
    dsr_inputs_by_tier: dict[str, dict[str, Any]] = {}
    if compute_dsr:
        for tier in tiers:
            dsr, inputs = _dsr_for(registry, tier, study, runs, trial_id_prefix)
            dsr_by_tier[tier.name] = dsr
            dsr_inputs_by_tier[tier.name] = inputs

    return UniverseResult(
        config=study,
        snapshot_id=snapshot_id,
        selection=selection,
        cohorts=dict(cohorts),
        tiers=tuple(tiers),
        runs=runs,
        dsr_by_tier=dsr_by_tier,
        dsr_inputs_by_tier=dsr_inputs_by_tier,
    )


def _log_symbol(
    registry: TrialRegistry,
    run: SymbolRun,
    study: bs.BreakoutStudyConfig,
    snapshot_id: str,
    prefix: str,
    selection: UniverseSelection,
    spans: Sequence[tuple[int, int, int, int]],
    bars: Sequence[TimestampedBar],
) -> None:
    """One `row_kind="symbol"` row per (symbol, tier) — that is the DSR pool — plus a
    `row_kind="benchmark"` row per benchmark and a `row_kind="window"` row per
    walk-forward window, which are the program-level multiplicity record (D90) and are
    excluded from the pool by the same identity predicate (D98)."""
    variant = baseline_variant()
    for tier_name, tier_run in run.by_tier.items():
        base_config = {
            **study.to_dict(),
            "study": "breakout_universe_v1",
            "symbol": run.symbol,
            "cohort": run.cohort,
            "status": run.status,
            "tier": tier_name,
            "fee_bps": tier_run.tier.fee_bps,
            "venue_role": tier_run.tier.role,
            "cost_stack": tier_run.tier.cost_stack_config(),
            "universe_policy": selection.policy.to_dict(),
            **variant.describe(),
        }
        r = tier_run.variant
        registry.add_trial(
            trial_id=f"{prefix}-{run.symbol}-{tier_name}",
            config={**base_config, "row_kind": "symbol"},
            params={
                "n_oos_bars": r.n_oos_bars,
                "n_windows": len(spans),
                "oos_start": run.oos_start.date().isoformat(),
                "oos_end": run.oos_end.date().isoformat(),
                **run.coverage.to_dict(),
            },
            metrics={
                "final_nav": r.final_nav,
                "total_return": r.total_return,
                "oos_sharpe_daily": r.sharpe_daily(study),
                "oos_sharpe_annual": r.sharpe_annual(study),
                "max_drawdown": r.max_drawdown,
                "num_fills": sum(e.n_fills for e in r.episodes),
                **r.diagnostics.to_metrics(),
            },
            snapshot_id=snapshot_id,
            seed=study.seed,
        )
        benchmarks: list[tuple[str, float, float, float]] = [
            ("buy_and_hold", tier_run.hold.total_return, tier_run.hold.max_drawdown,
             tier_run.hold.sharpe_annual(study)),
            ("risk_free", tier_run.rf_return, 0.0, float("nan")),
        ]
        if tier_run.matched is not None:
            benchmarks.append(
                ("constant_fraction", tier_run.matched.total_return, tier_run.matched.max_drawdown,
                 tier_run.matched.sharpe_annual(study))
            )
        for kind, total_return, maxdd, sharpe_annual in benchmarks:
            registry.add_trial(
                trial_id=f"{prefix}-{run.symbol}-{tier_name}-bench-{kind}",
                config={**base_config, "row_kind": "benchmark", "benchmark": kind},
                params={"n_oos_bars": r.n_oos_bars,
                        "fraction": r.diagnostics.exposure if kind == "constant_fraction" else None},
                metrics={"total_return": total_return, "max_drawdown": maxdd,
                         "sharpe_annual": sharpe_annual},
                snapshot_id=snapshot_id,
                seed=study.seed,
            )
        for window_index, _, test_start, test_end in spans:
            window_metrics: dict[str, Any] = {"window_final_nav": r.window_final_nav[window_index]}
            if window_index in r.window_sharpes_daily:
                window_metrics["window_sharpe_daily"] = r.window_sharpes_daily[window_index]
            registry.add_trial(
                trial_id=f"{prefix}-{run.symbol}-{tier_name}-w{window_index:03d}",
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
    tier: bs.CostTier,
    study: bs.BreakoutStudyConfig,
    runs: Mapping[str, SymbolRun],
    prefix: str,
) -> tuple[float, dict[str, Any]]:
    """DSR at one cost tier, with the trial pool = **every symbol's out-of-sample daily
    Sharpe at that tier** (D142).

    D116 set the pool to configurations because that study swept configurations. This
    study sweeps none — it runs one fixed rule — so its multiplicity lives entirely in
    the cross-section: N coins were tried and the best one will inevitably look good.
    That is precisely the selection DSR was built to deflate.

    Pool membership is selected on identity fields in the logged config (`row_kind`,
    `tier`, prefix), never on the presence of a metric (D98's rule). Units are daily
    throughout, matching D98's contract."""
    at_tier = [run.by_tier[tier.name] for run in runs.values()]
    best = max(at_tier, key=lambda t: t.variant.sharpe_daily(study))
    returns = np.asarray(best.variant.oos_returns, dtype=float)
    mu, sd = returns.mean(), returns.std(ddof=0)
    inputs: dict[str, Any] = {
        "observed_sr_daily": best.variant.sharpe_daily(study),
        "best_symbol": best.variant.symbol,
        "t": len(returns),
        "skew": float(np.mean((returns - mu) ** 3) / sd**3) if sd > 0 else 0.0,
        "kurt": float(np.mean((returns - mu) ** 4) / sd**4) if sd > 0 else 3.0,
    }

    def _in_pool(trial) -> bool:
        return (
            trial.config.get("row_kind") == "symbol"
            and trial.config.get("tier") == tier.name
            and trial.trial_id.startswith(f"{prefix}-")
        )

    pool = [t.metrics["oos_sharpe_daily"] for t in registry.all_trials() if _in_pool(t)]
    if any(not math.isfinite(v) for v in pool):
        raise ValueError(
            f"tier {tier.name}: the DSR pool contains a non-finite Sharpe — a symbol whose "
            "returns never varied. Imputing or dropping it would distort N and V (D98); fix "
            "the universe policy instead."
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
    inputs["n_trials"] = len(pool)
    inputs["var_trials_daily"] = float(np.var(pool, ddof=1)) if len(pool) > 1 else float("nan")
    return dsr, inputs


# ------------------------------------------------------------- cross-section stats


def distribution(values: Sequence[float]) -> dict[str, float]:
    """Min / p10 / p25 / median / p75 / p90 / max / mean. The whole distribution is
    reported rather than a mean because a cross-section dominated by one or two coins
    is exactly the failure mode this study exists to expose, and a mean hides it."""
    clean = sorted(v for v in values if v == v)
    if not clean:
        return {k: float("nan") for k in
                ("n", "min", "p10", "p25", "median", "p75", "p90", "max", "mean")}

    def q(p: float) -> float:
        rank = max(1, math.ceil(p * len(clean)))
        return float(clean[rank - 1])

    return {
        "n": float(len(clean)),
        "min": clean[0],
        "p10": q(0.10),
        "p25": q(0.25),
        "median": float(statistics.median(clean)),
        "p75": q(0.75),
        "p90": q(0.90),
        "max": clean[-1],
        "mean": float(statistics.fmean(clean)),
    }


def _rate(hits: Sequence[bool | None]) -> tuple[int, int, float]:
    """(wins, comparisons, fraction) — `None` entries are comparisons that do not
    exist and are excluded from BOTH numerator and denominator rather than counted as
    losses."""
    defined = [h for h in hits if h is not None]
    wins = sum(1 for h in defined if h)
    return wins, len(defined), (wins / len(defined) if defined else float("nan"))


def cross_section(
    result: UniverseResult, tier_name: str, symbols: Sequence[str] | None = None
) -> dict[str, Any]:
    """The study's actual result: how often, across the cross-section, did a fixed
    breakout rule beat each benchmark?"""
    names = tuple(symbols) if symbols is not None else result.symbols
    tier_runs = [result.runs[s].by_tier[tier_name] for s in names]
    study = result.config
    beat_hold = _rate([t.beats_hold for t in tier_runs])
    beat_matched = _rate([t.beats_matched for t in tier_runs])
    beat_rf = _rate([t.beats_rf for t in tier_runs])
    lower_dd = _rate([t.reduces_drawdown for t in tier_runs])
    positive = _rate([t.variant.total_return > 0.0 for t in tier_runs])
    return {
        "tier": tier_name,
        "symbols": list(names),
        "n_symbols": len(names),
        "beat_buy_and_hold": beat_hold,
        "beat_matched_exposure": beat_matched,
        "beat_risk_free": beat_rf,
        "reduced_max_drawdown": lower_dd,
        "positive_total_return": positive,
        "strategy_return": distribution([t.variant.total_return for t in tier_runs]),
        "hold_return": distribution([t.hold.total_return for t in tier_runs]),
        "matched_return": distribution(
            [t.matched.total_return for t in tier_runs if t.matched is not None]
        ),
        "strategy_cagr": distribution(
            [bs.cagr(t.variant.total_return, t.variant.n_oos_bars, study.periods_per_year)
             for t in tier_runs]
        ),
        "hold_cagr": distribution(
            [bs.cagr(t.hold.total_return, len(t.hold.oos_equity), study.periods_per_year)
             for t in tier_runs]
        ),
        "strategy_sharpe": distribution([t.variant.sharpe_annual(study) for t in tier_runs]),
        "hold_sharpe": distribution([t.hold.sharpe_annual(study) for t in tier_runs]),
        "strategy_maxdd": distribution([t.variant.max_drawdown for t in tier_runs]),
        "hold_maxdd": distribution([t.hold.max_drawdown for t in tier_runs]),
        "exposure": distribution([t.variant.diagnostics.exposure for t in tier_runs]),
        "trades": distribution([float(t.variant.diagnostics.n_closed_trades) for t in tier_runs]),
        "whipsaw_rate": distribution([t.variant.diagnostics.whipsaw_rate for t in tier_runs]),
        "cost_share_of_gross": distribution(
            [t.variant.diagnostics.cost_share_of_gross for t in tier_runs]
        ),
    }


def split_by_status(result: UniverseResult, tier_name: str) -> dict[str, dict[str, Any]]:
    """The headline: every cross-sectional statistic, computed separately over the
    symbols that survived and the symbols that collapsed or were delisted."""
    return {
        "all": cross_section(result, tier_name),
        SURVIVED: cross_section(result, tier_name, result.bucket((SURVIVED,))),
        "collapsed_or_delisted": cross_section(result, tier_name, result.bucket(COLLAPSED_BUCKET)),
    }


def cross_sectional_year_table(result: UniverseResult, tier_name: str) -> list[dict[str, float]]:
    """D121's annual breakdown, lifted to the cross-section: per calendar year, the
    median coin's strategy return, the median coin's buy-and-hold return, the fraction
    of live coins where the strategy beat holding, and mean time in market.

    Built from `bs.annual_breakdown` per symbol — the same function the BTC/ETH report
    uses, unmodified."""
    per_year: dict[int, list[tuple[float, float, float]]] = {}
    for run in result.runs.values():
        tier_run = run.by_tier[tier_name]
        for row in bs.annual_breakdown(tier_run.variant, tier_run.hold):
            per_year.setdefault(int(row["year"]), []).append(
                (row["strategy"], row["benchmark"], row["exposure"])
            )
    rows = []
    for year in sorted(per_year):
        entries = per_year[year]
        rows.append(
            {
                "year": float(year),
                "n_live": float(len(entries)),
                "median_strategy": float(statistics.median(s for s, _b, _e in entries)),
                "median_benchmark": float(statistics.median(b for _s, b, _e in entries)),
                "share_beating_hold": sum(1 for s, b, _e in entries if s > b) / len(entries),
                "mean_exposure": float(statistics.fmean(e for _s, _b, e in entries)),
            }
        )
    return rows


def start_date_cross_section(
    result: UniverseResult,
    bars_by_symbol: Mapping[str, Sequence[TimestampedBar]],
    tier_name: str,
    cut_years: Sequence[int] = bs.START_YEAR_CUTS,
) -> list[dict[str, float]]:
    """D121's start-date sensitivity, lifted to the cross-section: for each start year,
    the share of coins where the strategy beat buy-and-hold and the median CAGR of each,
    using `bs.start_date_sensitivity` per symbol, unmodified."""
    tier = [t for t in result.tiers if t.name == tier_name][0]
    variant = baseline_variant()
    per_cut: dict[int, list[dict]] = {}
    for symbol, run in result.runs.items():
        rows = bs.start_date_sensitivity(
            bars_by_symbol[symbol], symbol, variant, tier, result.config, cut_years
        )
        for row in rows:
            per_cut.setdefault(int(row["cut_year"]), []).append(row)
    out = []
    for cut in sorted(per_cut):
        rows = per_cut[cut]
        out.append(
            {
                "cut_year": float(cut),
                "n_symbols": float(len(rows)),
                "share_beating_hold": sum(
                    1 for r in rows if r["strategy_return"] > r["benchmark_return"]
                ) / len(rows),
                "share_lower_maxdd": sum(
                    1 for r in rows if r["strategy_maxdd"] < r["benchmark_maxdd"]
                ) / len(rows),
                "median_strategy_cagr": float(statistics.median(r["strategy_cagr"] for r in rows)),
                "median_benchmark_cagr": float(statistics.median(r["benchmark_cagr"] for r in rows)),
                "median_strategy_maxdd": float(statistics.median(r["strategy_maxdd"] for r in rows)),
                "median_benchmark_maxdd": float(statistics.median(r["benchmark_maxdd"] for r in rows)),
            }
        )
    return out


def bootstrap_cross_section(
    result: UniverseResult, tier_name: str, seed: int | None = None
) -> dict[str, Any]:
    """Per-coin paired block bootstrap of (strategy Sharpe - benchmark Sharpe), D120,
    run against BOTH benchmarks and aggregated across the cross-section.

    `bs.sharpe_difference_bootstrap` is imported unmodified; what is new is only the
    question. The BTC/ETH study found the Sharpe difference indistinguishable from zero
    on two symbols and concluded that a decade of daily data buys roughly +/-0.4 of
    standard error on an annualised Sharpe. A cross-section can ask the sharper version:
    **on how many of the coins is the difference distinguishable at all?** If the answer
    is "a handful out of sixty", then every Sharpe comparison in this document is
    arithmetic rather than evidence, and the report should say so with a count."""
    study = result.config
    use_seed = study.seed if seed is None else seed
    hold_probs: list[float] = []
    matched_probs: list[float] = []
    hold_significant = matched_significant = matched_n = 0
    for run in result.runs.values():
        t = run.by_tier[tier_name]
        boot_hold = bs.sharpe_difference_bootstrap(
            t.variant.oos_returns, t.hold.oos_returns, study, seed=use_seed
        )
        hold_probs.append(boot_hold["prob_positive"])
        hold_significant += int(boot_hold["p05"] > 0 or boot_hold["p95"] < 0)
        if t.matched is not None:
            boot_matched = bs.sharpe_difference_bootstrap(
                t.variant.oos_returns, t.matched.oos_returns, study, seed=use_seed
            )
            matched_probs.append(boot_matched["prob_positive"])
            matched_significant += int(boot_matched["p05"] > 0 or boot_matched["p95"] < 0)
            matched_n += 1
    return {
        "tier": tier_name,
        "seed": use_seed,
        "n_symbols": len(result.runs),
        "vs_hold_prob_positive": distribution(hold_probs),
        "vs_hold_n_significant": hold_significant,
        "vs_matched_prob_positive": distribution(matched_probs),
        "vs_matched_n_significant": matched_significant,
        "vs_matched_n": matched_n,
    }


# ------------------------------------------------------------------------ rendering


def _pct(x: float, places: int = 1) -> str:
    return "n/a" if x != x else f"{x:+.{places}%}"


def _num(x: float, places: int = 2) -> str:
    return "n/a" if x != x else f"{x:.{places}f}"


def render_symbol_table(result: UniverseResult, tier_name: str) -> str:
    """One row per symbol, sorted by status then symbol, with all three benchmarks."""
    study = result.config
    lines = [
        "| Symbol | Status | Cohort | OOS span | Bars | Total return | CAGR | Sharpe | Max DD | "
        "Exposure | Trades | Whipsaw | Costs/gross | B&H return | B&H max DD | Matched-exposure | "
        "Risk-free |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    order = sorted(
        result.runs.values(),
        key=lambda r: (0 if r.status == SURVIVED else 1, r.symbol),
    )
    for run in order:
        t = run.by_tier[tier_name]
        r = t.variant
        d = r.diagnostics
        open_note = " +1 open" if d.n_open_at_end else ""
        matched = "n/a" if t.matched is None else _pct(t.matched.total_return)
        lines.append(
            f"| `{run.symbol}` | {run.status} | {run.cohort} | "
            f"{run.oos_start.date()} → {run.oos_end.date()} | {run.n_oos_bars:,} | "
            f"{_pct(r.total_return)} | "
            f"{_pct(bs.cagr(r.total_return, r.n_oos_bars, study.periods_per_year))} | "
            f"{_num(r.sharpe_annual(study))} | {_num(r.max_drawdown * 100, 1)}% | "
            f"{_num(d.exposure * 100, 1)}% | {d.n_closed_trades}{open_note} | "
            f"{_num(d.whipsaw_rate * 100, 1)}% | {_num(d.cost_share_of_gross * 100, 1)}% | "
            f"{_pct(t.hold.total_return)} | {_num(t.hold.max_drawdown * 100, 1)}% | "
            f"{matched} | {_pct(t.rf_return)} |"
        )
    return "\n".join(lines)


def _rate_cell(rate: tuple[int, int, float]) -> str:
    wins, total, fraction = rate
    return "n/a" if total == 0 else f"{wins}/{total} ({fraction:.0%})"


def render_hit_rate_table(result: UniverseResult, tier_name: str) -> str:
    split = split_by_status(result, tier_name)
    labels = [("All", "all"), ("Survived", SURVIVED), ("Collapsed / delisted", "collapsed_or_delisted")]
    lines = [
        "| Bucket | Coins | Beat 100% buy & hold | Beat matched-exposure (D119) | "
        "Beat risk-free | Reduced max drawdown | Positive total return |",
        "|---|---|---|---|---|---|---|",
    ]
    for label, key in labels:
        c = split[key]
        lines.append(
            f"| {label} | {c['n_symbols']} | {_rate_cell(c['beat_buy_and_hold'])} | "
            f"{_rate_cell(c['beat_matched_exposure'])} | {_rate_cell(c['beat_risk_free'])} | "
            f"{_rate_cell(c['reduced_max_drawdown'])} | {_rate_cell(c['positive_total_return'])} |"
        )
    return "\n".join(lines)


def render_distribution_table(result: UniverseResult, tier_name: str, key: str, as_pct: bool) -> str:
    """One statistic's full cross-sectional distribution, per bucket."""
    split = split_by_status(result, tier_name)
    fmt = (lambda v: _pct(v)) if as_pct else (lambda v: _num(v))
    lines = [
        "| Bucket | n | min | p10 | p25 | median | p75 | p90 | max | mean |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for label, bucket_key in (("All", "all"), ("Survived", SURVIVED),
                              ("Collapsed / delisted", "collapsed_or_delisted")):
        d = split[bucket_key][key]
        lines.append(
            f"| {label} | {int(d['n'])} | " + " | ".join(
                fmt(d[q]) for q in ("min", "p10", "p25", "median", "p75", "p90", "max", "mean")
            ) + " |"
        )
    return "\n".join(lines)


def render_tier_table(result: UniverseResult) -> str:
    """Cost monotonicity across the cross-section: median return and the hit rates at
    each tier."""
    lines = [
        "| Tier | Fee | Role | Median total return | Median Sharpe | Beat B&H | "
        "Beat matched-exposure | Median costs / gross P&L |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for tier in result.tiers:
        c = cross_section(result, tier.name)
        lines.append(
            f"| `{tier.name}` | {tier.fee_bps / 100:.2f}% | {tier.role} | "
            f"{_pct(c['strategy_return']['median'])} | {_num(c['strategy_sharpe']['median'])} | "
            f"{_rate_cell(c['beat_buy_and_hold'])} | {_rate_cell(c['beat_matched_exposure'])} | "
            f"{_num(c['cost_share_of_gross']['median'] * 100, 1)}% |"
        )
    return "\n".join(lines)


def render_exclusion_table(
    excluded: Mapping[str, str],
    fetch_failures: Mapping[str, str],
    coverage: Mapping[str, Mapping[str, Any]],
    cohorts: Mapping[str, str],
) -> str:
    """Every symbol that was attempted and did not make it, with the statistic that
    rejected it.

    Fed from the FIXTURE META rather than from the study's own re-application of the
    policy: the committed fixture holds admitted symbols only (D88's shape), so by the
    time the study runs, the evidence about the rejected ones lives in the meta. That is
    the whole reason the meta records coverage for every fetched symbol and not just the
    survivors of the screen."""
    def cell(text: str) -> str:
        """Reason strings are written by the policy and by the provider's exception
        messages, and they land verbatim in a markdown table. A stray `|` silently
        breaks the row and the reader never learns why a symbol was excluded — so the
        renderer escapes rather than trusting its input."""
        return str(text).replace("|", "\\|").replace("\n", " ")

    lines = [
        "| Symbol | Cohort | Outcome | Reason | Bars | Median daily volume (USD) | "
        "Median abs. daily return |",
        "|---|---|---|---|---|---|---|",
    ]
    for symbol in sorted(set(excluded) | set(fetch_failures)):
        cohort = cohorts.get(symbol, "unknown")
        if symbol in fetch_failures:
            lines.append(
                f"| `{symbol}` | {cohort} | **fetch failed** | {cell(fetch_failures[symbol])} | "
                "— | — | — |"
            )
            continue
        cov = coverage.get(symbol, {})
        bars = f"{cov['n_bars']:,}" if "n_bars" in cov else "—"
        volume = f"{cov['median_daily_volume']:,.0f}" if "median_daily_volume" in cov else "—"
        move = f"{cov['median_abs_daily_return']:.2%}" if "median_abs_daily_return" in cov else "—"
        lines.append(
            f"| `{symbol}` | {cohort} | excluded | {cell(excluded[symbol])} | {bars} | {volume} | "
            f"{move} |"
        )
    return "\n".join(lines)


def render_year_table(rows: Sequence[dict[str, float]]) -> str:
    lines = [
        "| Year | Coins live | Median strategy | Median buy & hold | Share beating B&H | "
        "Mean time in market |",
        "|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {int(row['year'])} | {int(row['n_live'])} | {row['median_strategy']:+.1%} | "
            f"{row['median_benchmark']:+.1%} | {row['share_beating_hold']:.0%} | "
            f"{row['mean_exposure']:.0%} |"
        )
    return "\n".join(lines)


def render_start_date_table(rows: Sequence[dict[str, float]]) -> str:
    lines = [
        "| OOS begins in | Coins with enough history | Share beating B&H | Share with lower max DD | "
        "Median strategy CAGR | Median B&H CAGR | Median strategy max DD | Median B&H max DD |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {int(row['cut_year'])} | {int(row['n_symbols'])} | {row['share_beating_hold']:.0%} | "
            f"{row['share_lower_maxdd']:.0%} | {row['median_strategy_cagr']:+.1%} | "
            f"{row['median_benchmark_cagr']:+.1%} | {row['median_strategy_maxdd']:.0%} | "
            f"{row['median_benchmark_maxdd']:.0%} |"
        )
    return "\n".join(lines)


def render_dsr_table(result: UniverseResult) -> str:
    lines = [
        "| Tier | Best symbol | Its daily SR | T (bars) | N (symbols in pool) | V[{SRn}] | **DSR** |",
        "|---|---|---|---|---|---|---|",
    ]
    for tier in result.tiers:
        i = result.dsr_inputs_by_tier[tier.name]
        lines.append(
            f"| `{tier.name}` | `{i['best_symbol']}` | {i['observed_sr_daily']:.4f} | "
            f"{i['t']:,} | {i['n_trials']} | {i['var_trials_daily']:.6f} | "
            f"**{result.dsr_by_tier[tier.name]:.4f}** |"
        )
    return "\n".join(lines)

"""Cost-frequency frontier for the long-flat breakout (D160-D165).

`BREAKOUT_RESULTS.md` concludes that exchange fees are "not the binding constraint" for
this strategy. That conclusion rests entirely on DAILY bars, where annualised turnover is
~6-7x and the median trade is held 26-29 days. Run the identical rule on finer bars and
turnover rises roughly with the frequency ratio while the gross edge does not. This
module is where that conclusion gets TESTED rather than assumed.

The output is a **frontier**, not a horse race: as frequency rises, what does the gross
edge do, what does the cost do, and at what frequency do the two curves cross? "The edge
does not survive above daily frequency" is a perfectly good answer to that question.

Study glue only — every load-bearing piece is imported unmodified from
`research.breakout_study` (`run_variant`, `run_benchmark`,
`run_constant_fraction_benchmark`, `breakout_config`, `CostTier`, `DEFAULT_TIERS`) and
from the framework beneath it. Nothing in this module edits an existing interface.

## The resampling contract (D161)

yfinance serves 730 days of 1h bars, 60 days of 15m/30m, no 4h for `period='max'`, and
has no 6h interval at all. So the study fetches **1h over 730 days** and resamples
upward. Resampling is exact because 60 minutes divides every target and every target
divides 1440, so buckets align to 00:00 UTC:

    open  = first constituent open      high = max constituent high
    low   = min constituent low         close = last constituent close
    volume = sum of constituent volumes

**Incomplete buckets are never silently short.** The provider drops occasional hours
(6 UTC days out of 729 in the committed fixture). A bucket built from fewer than its
full complement of source bars would be a bar of the wrong duration wearing the right
timestamp. Dropping only that bucket is not enough either: it would give each frequency
a DIFFERENT calendar, and frequency is the one thing this study varies. So the policy is
day-level and shared:

> **A UTC day that the provider does not serve in full is dropped at EVERY frequency.**

Every frequency then holds exactly `complete_days x 1440/minutes` bars, and — since the
walk-forward sizes are scaled by the same `bars_per_day` — the window count
`floor((days - train_days - test_days)/step_days) + 1` is *identical across frequencies
by construction*, not by luck. `frequency_series` asserts it anyway.

## Two designs, which answer different questions and must not be conflated (D162)

- **Design A — constant calendar horizon.** 40-day entry / 10-day exit at every
  frequency (960/240 bars at 1h, 40/10 at 1d). The economic signal is identical; only
  the sampling rate changes. Isolates: *does finer sampling of the same signal help, or
  just add cost?*
- **Design B — constant bar count.** 40 bars / 10 bars at every frequency, so the
  economic horizon shortens with the bar. Asks: *does the trend effect exist at shorter
  horizons at all?* — and it is the design that generates the turnover explosion.

The inverse-vol sizing window scales with the design for the same reason the breakout
windows do: under Design A a 20-BAR vol estimate at 1h would measure 20 hours of
volatility while the signal measures 40 days, so "the economic signal is identical"
would be false. Under Design B everything is
counted in bars, including the vol window.

At 1d the two designs are the same configuration. That is not waste — it is the anchor
that ties this study to `BREAKOUT_RESULTS.md`, and the multiplicity count says so.

## periods_per_year appears in TWO places and both must move (D17)

`analytics.metrics` requires it as an argument (D17's rule), and `InverseVolatilityWeight`
carries its own copy for annualising the realized-vol estimate. A study that scaled one
and not the other would report a 1h Sharpe annualised on 8,760 periods while sizing every
position as though a bar were a day. `assert_periods_per_year_agree` refuses to run such
a configuration.
"""

from __future__ import annotations

import math
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from ..analytics.metrics import sharpe
from ..data.bars import TimestampedBar
from ..registry.trial_registry import TrialRegistry
from ..simulator.fills import Bar
from ..validation.dsr import deflated_sharpe_from_trials
from .breakout_study import (
    BreakoutStudyConfig,
    CostTier,
    DEFAULT_TIERS,
    REFERENCE_TIER,
    Variant,
    VariantResult,
    breakout_config,
    cagr,
    run_benchmark,
    run_constant_fraction_benchmark,
    run_variant,
)
from .trade_diagnostics import TradeEpisode

MINUTES_PER_DAY = 1440
SOURCE_MINUTES = 60
"""The fixture's own bar size. Everything coarser is resampled from it; nothing finer
can be (D160: yfinance serves 60 days of 15m/30m and no 4h/6h at all)."""


# ------------------------------------------------------------------- frequency ladder


@dataclass(frozen=True)
class Frequency:
    """One rung of the ladder. `minutes` must divide 1440 so buckets align to 00:00 UTC."""

    name: str
    minutes: int

    def __post_init__(self) -> None:
        if MINUTES_PER_DAY % self.minutes:
            raise ValueError(
                f"frequency {self.name!r}: {self.minutes} minutes does not divide a UTC day, so "
                "its buckets cannot align to 00:00 and the resampling contract (D161) does not hold"
            )

    @property
    def bars_per_day(self) -> int:
        return MINUTES_PER_DAY // self.minutes

    @property
    def periods_per_year(self) -> float:
        """365 calendar days x bars per day — D17's rule, crypto's 365-day calendar
        (D108) carried down to the bar. 8,760 (1h) / 4,380 (2h) / 2,190 (4h) /
        1,460 (6h) / 730 (12h) / 365 (1d)."""
        return 365.0 * self.bars_per_day


FREQ_1H = Frequency("1h", 60)
STUDY_FREQUENCIES: tuple[Frequency, ...] = (
    FREQ_1H,
    Frequency("2h", 120),
    Frequency("4h", 240),
    Frequency("6h", 360),
    Frequency("12h", 720),
    Frequency("1d", 1440),
)
SUB_HOURLY_FREQUENCIES: tuple[Frequency, ...] = (Frequency("15m", 15), Frequency("30m", 30))


# ------------------------------------------------------- the resampling contract (D161)


@dataclass(frozen=True)
class DayCensus:
    """Which UTC days the provider served in full, and which it did not.

    The dropped days are the study's shared calendar hole: a partial day is excluded at
    EVERY frequency, because a frequency-dependent calendar would make frequency stop
    being the only variable (D161)."""

    source_minutes: int
    complete: tuple[date, ...]
    incomplete: tuple[tuple[date, int], ...]
    """(day, bars actually served) for every day short of a full complement."""

    @property
    def expected_bars_per_day(self) -> int:
        return MINUTES_PER_DAY // self.source_minutes

    def to_meta(self) -> dict[str, Any]:
        return {
            "source_minutes": self.source_minutes,
            "expected_bars_per_day": self.expected_bars_per_day,
            "complete_days": len(self.complete),
            "first_complete_day": self.complete[0].isoformat() if self.complete else None,
            "last_complete_day": self.complete[-1].isoformat() if self.complete else None,
            "dropped_days": [[day.isoformat(), served] for day, served in self.incomplete],
        }


def census_days(bars: Sequence[TimestampedBar], source_minutes: int = SOURCE_MINUTES) -> DayCensus:
    """Count served bars per UTC day. Loud by construction: the incomplete days are
    returned as data, not logged and forgotten."""
    expected = MINUTES_PER_DAY // source_minutes
    counts: dict[date, int] = defaultdict(int)
    for tb in bars:
        counts[tb.timestamp.date()] += 1
    complete = tuple(sorted(day for day, n in counts.items() if n == expected))
    incomplete = tuple(sorted((day, n) for day, n in counts.items() if n != expected))
    return DayCensus(source_minutes=source_minutes, complete=complete, incomplete=incomplete)


@dataclass(frozen=True)
class ResampleReport:
    source_minutes: int
    target_minutes: int
    n_source_bars_used: int
    n_target_bars: int
    n_days: int

    def check(self) -> None:
        """The arithmetic that must hold if the contract held. Raises rather than
        warns: a series that is one bar short is a series whose walk-forward windows no
        longer line up with every other frequency's."""
        factor = self.target_minutes // self.source_minutes
        bars_per_day = MINUTES_PER_DAY // self.target_minutes
        if self.n_target_bars != self.n_days * bars_per_day:
            raise ValueError(
                f"resample to {self.target_minutes}m produced {self.n_target_bars} bars from "
                f"{self.n_days} complete days, expected {self.n_days * bars_per_day} (D161)"
            )
        if self.n_source_bars_used != self.n_target_bars * factor:
            raise ValueError(
                f"resample to {self.target_minutes}m consumed {self.n_source_bars_used} source "
                f"bars for {self.n_target_bars} target bars, expected "
                f"{self.n_target_bars * factor} (D161)"
            )


def resample(
    bars: Sequence[TimestampedBar],
    volumes: Sequence[float],
    target_minutes: int,
    keep_days: Sequence[date],
    source_minutes: int = SOURCE_MINUTES,
) -> tuple[list[TimestampedBar], list[float], ResampleReport]:
    """Exact OHLCV aggregation of `bars` into `target_minutes` buckets anchored at
    00:00 UTC, restricted to `keep_days`.

    open = first open, high = max high, low = min low, close = last close,
    volume = sum. Buckets are keyed on (UTC date, minute-of-day // target_minutes), so
    they align to midnight whenever `target_minutes` divides 1440 — which the Frequency
    constructor enforces.

    A bucket that does not receive exactly `target_minutes / source_minutes` source bars
    raises. It cannot happen for a day in `keep_days` (a complete day has every source
    bar), and that is precisely why the drop policy is day-level: the assertion is how a
    silent short bar is made impossible rather than merely unlikely (Pillar 1)."""
    if target_minutes % source_minutes:
        raise ValueError(
            f"target {target_minutes}m is not a whole multiple of source {source_minutes}m"
        )
    if MINUTES_PER_DAY % target_minutes:
        raise ValueError(f"target {target_minutes}m does not divide a UTC day (D161)")
    if len(bars) != len(volumes):
        raise ValueError(f"{len(bars)} bars but {len(volumes)} volumes")
    factor = target_minutes // source_minutes
    kept = set(keep_days)

    buckets: dict[tuple[date, int], list[tuple[TimestampedBar, float]]] = defaultdict(list)
    used = 0
    for tb, volume in zip(bars, volumes):
        day = tb.timestamp.date()
        if day not in kept:
            continue
        slot = (tb.timestamp.hour * 60 + tb.timestamp.minute) // target_minutes
        buckets[(day, slot)].append((tb, volume))
        used += 1

    out_bars: list[TimestampedBar] = []
    out_volumes: list[float] = []
    for (day, slot), members in sorted(buckets.items()):
        if len(members) != factor:
            raise ValueError(
                f"incomplete {target_minutes}m bucket at {day} slot {slot}: {len(members)} of "
                f"{factor} source bars — refusing to emit a bar of the wrong duration (D161)"
            )
        members.sort(key=lambda pair: pair[0].timestamp)
        first = members[0][0]
        expected_start = datetime.combine(day, datetime.min.time()) + timedelta(
            minutes=slot * target_minutes
        )
        if first.timestamp != expected_start:
            raise ValueError(
                f"{target_minutes}m bucket at {day} slot {slot} starts at {first.timestamp}, "
                f"expected {expected_start} — buckets are not aligned to 00:00 UTC (D161)"
            )
        out_bars.append(
            TimestampedBar(
                timestamp=expected_start,
                bar=Bar(
                    open=members[0][0].bar.open,
                    high=max(m[0].bar.high for m in members),
                    low=min(m[0].bar.low for m in members),
                    close=members[-1][0].bar.close,
                ),
            )
        )
        out_volumes.append(float(sum(m[1] for m in members)))

    report = ResampleReport(
        source_minutes=source_minutes,
        target_minutes=target_minutes,
        n_source_bars_used=used,
        n_target_bars=len(out_bars),
        n_days=len(kept & {d for d, _ in buckets}),
    )
    report.check()
    return out_bars, out_volumes, report


def frequency_series(
    bars: Sequence[TimestampedBar],
    volumes: Sequence[float],
    frequencies: Sequence[Frequency] = STUDY_FREQUENCIES,
    source_minutes: int = SOURCE_MINUTES,
) -> tuple[dict[str, tuple[list[TimestampedBar], list[float]]], DayCensus, dict[str, ResampleReport]]:
    """Build every frequency's series off ONE shared calendar of complete UTC days.

    This is the function that makes "frequency is the only variable" true rather than
    aspirational: all frequencies are cut from the same day set, so all of them span the
    same calendar and — because the walk-forward sizes scale by `bars_per_day` — produce
    the same number of windows."""
    census = census_days(bars, source_minutes)
    if not census.complete:
        raise ValueError("no complete UTC day in the source series — nothing to resample")
    series: dict[str, tuple[list[TimestampedBar], list[float]]] = {}
    reports: dict[str, ResampleReport] = {}
    for freq in frequencies:
        out_bars, out_volumes, report = resample(
            bars, volumes, freq.minutes, census.complete, source_minutes
        )
        if len(out_bars) != len(census.complete) * freq.bars_per_day:
            raise ValueError(
                f"{freq.name}: {len(out_bars)} bars from {len(census.complete)} complete days"
            )
        series[freq.name] = (out_bars, out_volumes)
        reports[freq.name] = report
    return series, census, reports


# ---------------------------------------------------------------------- designs (D162)

BASE_N_ENTRY, BASE_N_EXIT, BASE_VOL_WINDOW = 40, 10, 20
"""The daily baseline this study inherits: `plateau_40_10` with a 20-bar inverse-vol
window (BREAKOUT_RESULTS.md). Both designs are defined relative to it, and both reduce
to it exactly at 1d."""


@dataclass(frozen=True)
class Design:
    key: str
    label: str
    scale_with_frequency: bool

    def windows(self, freq: Frequency) -> tuple[int, int, int]:
        """(n_entry, n_exit, vol_window) in BARS at this frequency."""
        multiple = freq.bars_per_day if self.scale_with_frequency else 1
        return (
            BASE_N_ENTRY * multiple,
            BASE_N_EXIT * multiple,
            BASE_VOL_WINDOW * multiple,
        )

    def describe(self, freq: Frequency) -> dict[str, Any]:
        n_entry, n_exit, vol_window = self.windows(freq)
        return {
            "design": self.key,
            "design_label": self.label,
            "n_entry_bars": n_entry,
            "n_exit_bars": n_exit,
            "vol_window_bars": vol_window,
            "n_entry_days": n_entry / freq.bars_per_day,
            "n_exit_days": n_exit / freq.bars_per_day,
        }


DESIGN_A = Design("A", "constant calendar horizon (40-day entry / 10-day exit)", True)
DESIGN_B = Design("B", "constant bar count (40-bar entry / 10-bar exit)", False)
DESIGNS: tuple[Design, ...] = (DESIGN_A, DESIGN_B)

TRAIN_DAYS, TEST_DAYS, STEP_DAYS = 252, 63, 63
"""Walk-forward sizes in CALENDAR DAYS, scaled to bars per frequency. Equal calendar
duration at every frequency is what makes the window counts equal (and the comparison
meaningful); the day numbers themselves are inherited unchanged from
BREAKOUT_RESULTS.md so the 1d rung reproduces that study's structure."""

WHIPSAW_DAYS = 3
"""A whipsaw is a trade closed within 3 CALENDAR days of opening, at every frequency.
The daily study's `whipsaw_bars=3` meant three days; keeping the bar count fixed instead
would make "whipsaw" mean three hours at 1h and three days at 1d, and the resulting
column would compare nothing."""

VOL_TARGET = 0.40
TARGET_MAX_WEIGHT = 1.0


def weight_source_config(freq: Frequency, vol_window: int) -> dict[str, Any]:
    """Baseline sizing (D110), with BOTH frequency-dependent knobs set: the vol window
    in bars and `periods_per_year` for annualising the estimate."""
    return {
        "type": "inverse_vol_weight",
        "target_annual_vol": VOL_TARGET,
        "vol_window": vol_window,
        "periods_per_year": freq.periods_per_year,
        "max_weight": TARGET_MAX_WEIGHT,
        "rebalance": "at_entry",
    }


def study_config(freq: Frequency, seed: int = 0) -> BreakoutStudyConfig:
    return BreakoutStudyConfig(
        train_size=TRAIN_DAYS * freq.bars_per_day,
        test_size=TEST_DAYS * freq.bars_per_day,
        step=STEP_DAYS * freq.bars_per_day,
        periods_per_year=freq.periods_per_year,
        fill_timing="next_open",
        whipsaw_bars=WHIPSAW_DAYS * freq.bars_per_day,
        seed=seed,
    )


def variant_for(design: Design, freq: Frequency) -> Variant:
    n_entry, n_exit, vol_window = design.windows(freq)
    return Variant(
        name=f"freq_{freq.name}_design_{design.key}",
        group="frequency",
        fixed_config=breakout_config(
            n_entry=n_entry,
            n_exit=n_exit,
            weight_source=weight_source_config(freq, vol_window),
        ),
    )


def assert_periods_per_year_agree(variant: Variant, study: BreakoutStudyConfig) -> None:
    """The metrics layer and the sizing brick each carry their own `periods_per_year`
    (D17 as designed vs `InverseVolatilityWeight` as built). They must agree, or the
    study annualises on one calendar and sizes on another — silently, since neither
    layer can see the other's copy."""
    config = variant.fixed_config
    if config is None:
        raise ValueError(
            "a frequency variant must be fixed-config: this one has no fixed_config, so "
            "there is no periods_per_year to agree with the study's"
        )
    sizing = config["weight_source"].get("periods_per_year")
    if sizing != study.periods_per_year:
        raise ValueError(
            f"variant {variant.name!r}: sizing periods_per_year={sizing} but study "
            f"periods_per_year={study.periods_per_year} — the Sharpe would be annualised on one "
            "calendar and every position sized on another (D17)"
        )


def window_count(n_days: int) -> int:
    """Windows a `n_days`-day span yields under the calendar-scaled walk-forward. Note
    what is NOT in the signature: the frequency. That independence is the point (D161)."""
    if n_days < TRAIN_DAYS + TEST_DAYS:
        return 0
    return (n_days - TRAIN_DAYS - TEST_DAYS) // STEP_DAYS + 1


# ------------------------------------------------------- calendar-unit diagnostics (D163)


def holding_periods_days(episodes: Sequence[TradeEpisode]) -> list[float]:
    """Closed-trade holding periods in CALENDAR DAYS, from episode timestamps.

    `DiagnosticsSummary.median_bars_held` is in bars, and bars mean different amounts of
    time at each frequency — a table comparing "26 bars" at 1d with "180 bars" at 1h
    tells the reader nothing about the strategy's economic character. This does."""
    return [
        (e.exit_timestamp - e.entry_timestamp).total_seconds() / 86400.0
        for e in episodes
        if e.exit_timestamp is not None
    ]


def calendar_trade_stats(result: VariantResult) -> dict[str, float]:
    held = holding_periods_days(result.episodes)
    closed = len(held)
    span_days = (result.oos_equity[-1][0] - result.oos_equity[0][0]).total_seconds() / 86400.0
    return {
        "n_closed_trades": float(closed),
        "median_hold_days": float(statistics.median(held)) if held else float("nan"),
        "mean_hold_days": float(statistics.fmean(held)) if held else float("nan"),
        "p90_hold_days": float(sorted(held)[max(0, math.ceil(0.9 * closed) - 1)])
        if held
        else float("nan"),
        "whipsaw_rate_3d": (sum(1 for h in held if h <= WHIPSAW_DAYS) / closed)
        if closed
        else float("nan"),
        "trades_per_year": (closed / (span_days / 365.0)) if span_days > 0 else float("nan"),
        "oos_span_days": span_days,
    }


def daily_equity(equity: Sequence[tuple[datetime, float]]) -> list[tuple[datetime, float]]:
    """End-of-UTC-day NAV. Collapsing every frequency's curve onto the same calendar is
    what makes cross-frequency Sharpe comparison unit-consistent (D164): the same T, the
    same period, whatever the bar size was underneath."""
    by_day: dict[date, tuple[datetime, float]] = {}
    for ts, nav in equity:
        by_day[ts.date()] = (ts, nav)
    return [by_day[day] for day in sorted(by_day)]


def daily_returns(equity: Sequence[tuple[datetime, float]]) -> list[float]:
    curve = daily_equity(equity)
    return [b / a - 1.0 for (_, a), (_, b) in zip(curve, curve[1:])]


# ------------------------------------------------------------------------- the frontier


@dataclass
class FrontierRow:
    """One (symbol, design, frequency, tier) cell of the frontier."""

    symbol: str
    design: Design
    frequency: Frequency
    tier: CostTier
    result: VariantResult
    study: BreakoutStudyConfig
    n_windows: int
    calendar: dict[str, float]
    daily_returns: list[float]

    @property
    def total_return(self) -> float:
        return self.result.total_return

    @property
    def cagr(self) -> float:
        return cagr(self.result.total_return, self.result.n_oos_bars, self.study.periods_per_year)

    @property
    def sharpe_annual(self) -> float:
        return self.result.sharpe_annual(self.study)

    @property
    def sharpe_daily(self) -> float:
        """Per-CALENDAR-DAY Sharpe, computed from the day-collapsed curve — the unit the
        cross-frequency DSR pool lives in (D164)."""
        return sharpe(self.daily_returns, self.study.rf_annual, 365.0) / math.sqrt(365.0)

    @property
    def max_drawdown(self) -> float:
        return self.result.max_drawdown

    @property
    def annual_vol(self) -> float:
        """Annualised volatility of the strategy's CALENDAR-DAILY returns — one unit for
        every frequency, so the cost-drag conversion below is comparable up the ladder."""
        if len(self.daily_returns) < 2:
            return float("nan")
        return float(statistics.stdev(self.daily_returns) * math.sqrt(365.0))

    @property
    def fee_drag_annual(self) -> float:
        """Fees paid per year as a fraction of average equity ≈ annual turnover × fee
        rate. **This is the sample-robust half of the frontier.** Unlike
        `cost_share_of_gross` it has no P&L in its denominator, so it does not blow up or
        change sign when the sample's gross P&L happens to be near zero — which it is
        over this 2024–2026 window."""
        years = self.result.n_oos_bars / self.study.periods_per_year
        mean_equity = statistics.fmean([nav for _, nav in self.result.oos_equity])
        if not (years and mean_equity):
            return float("nan")
        return self.result.diagnostics.total_costs / mean_equity / years

    @property
    def cost_drag_sharpe_units(self) -> float:
        """The cost curve expressed in Sharpe units: annual fee drag ÷ annual volatility.

        Sharpe ≈ (μ − rf)/σ, so charging `c` per year of fees costs `c/σ` of Sharpe, to
        first order. That conversion is what lets a cost curve measured on a two-year
        window with no edge in it be compared against a gross edge measured somewhere
        else — which is the only way this study can answer its own question (D165)."""
        vol = self.annual_vol
        return self.fee_drag_annual / vol if vol and vol == vol else float("nan")

    def metrics(self) -> dict[str, float]:
        d = self.result.diagnostics
        return {
            "total_return": self.total_return,
            "cagr": self.cagr,
            "sharpe_annual": self.sharpe_annual,
            "sharpe_daily": self.sharpe_daily,
            "annual_vol": self.annual_vol,
            "max_drawdown": self.max_drawdown,
            "exposure": d.exposure,
            "n_closed_trades": float(d.n_closed_trades),
            "annual_turnover": d.annual_turnover,
            "cost_share_of_gross": d.cost_share_of_gross,
            "fee_drag_annual": self.fee_drag_annual,
            "cost_drag_sharpe_units": self.cost_drag_sharpe_units,
            "total_costs": d.total_costs,
            "gross_pnl": d.gross_pnl,
            "net_pnl": d.net_pnl,
            "rebalance_cost_share": d.rebalance_cost_share,
            **self.calendar,
        }


@dataclass
class FrontierResult:
    snapshot_id: str
    census: DayCensus
    tiers: tuple[CostTier, ...]
    frequencies: tuple[Frequency, ...]
    designs: tuple[Design, ...]
    symbols: tuple[str, ...]
    rows: dict[tuple[str, str, str, str], FrontierRow]
    """(symbol, design key, frequency name, tier name) -> row."""
    benchmarks: dict[tuple[str, str, str], Any]
    """(symbol, frequency name, tier name) -> buy-and-hold BenchmarkResult."""
    matched: dict[tuple[str, str, str, str], Any]
    """(symbol, design key, frequency name, tier name) -> constant-fraction benchmark."""
    n_windows: int
    dsr_by_symbol_tier: dict[tuple[str, str], float]
    dsr_inputs: dict[tuple[str, str], dict[str, Any]]

    def row(self, symbol: str, design: str, freq: str, tier: str) -> FrontierRow:
        return self.rows[(symbol, design, freq, tier)]


def run_frontier(
    series_by_symbol: Mapping[str, Mapping[str, tuple[Sequence[TimestampedBar], Sequence[float]]]],
    census: DayCensus,
    registry: TrialRegistry,
    snapshot_id: str,
    frequencies: Sequence[Frequency] = STUDY_FREQUENCIES,
    designs: Sequence[Design] = DESIGNS,
    tiers: Sequence[CostTier] = DEFAULT_TIERS,
    trial_id_prefix: str = "breakout-intraday-v1",
    progress: Callable[[str], None] | None = None,
) -> FrontierResult:
    """Every (symbol, design, frequency, tier) cell, logged as its own trial.

    The window count is computed once from the shared day calendar and asserted against
    every single run. An unequal count anywhere means some frequency saw a different
    amount of out-of-sample data, which would make the entire frontier a comparison of
    spans rather than of frequencies."""
    expected_windows = window_count(len(census.complete))
    if expected_windows < 1:
        raise ValueError(
            f"{len(census.complete)} complete days is not enough for one walk-forward window "
            f"({TRAIN_DAYS} train + {TEST_DAYS} test)"
        )

    rows: dict[tuple[str, str, str, str], FrontierRow] = {}
    benchmarks: dict[tuple[str, str, str], Any] = {}
    matched: dict[tuple[str, str, str, str], Any] = {}

    for symbol, by_freq in series_by_symbol.items():
        for freq in frequencies:
            bars, _volumes = by_freq[freq.name]
            study = study_config(freq)
            for tier in tiers:
                benchmarks[(symbol, freq.name, tier.name)] = run_benchmark(
                    bars, symbol, tier, study
                )
            for design in designs:
                variant = variant_for(design, freq)
                assert_periods_per_year_agree(variant, study)
                for tier in tiers:
                    if progress:
                        progress(f"{symbol} {design.key} {freq.name} {tier.name}")
                    result = run_variant(bars, symbol, variant, tier, study)
                    n_windows = len(result.window_final_nav)
                    if n_windows != expected_windows:
                        raise ValueError(
                            f"{symbol}/{design.key}/{freq.name}/{tier.name} produced {n_windows} "
                            f"walk-forward windows, expected {expected_windows} — frequencies "
                            "would not be comparable (D161)"
                        )
                    row = FrontierRow(
                        symbol=symbol,
                        design=design,
                        frequency=freq,
                        tier=tier,
                        result=result,
                        study=study,
                        n_windows=n_windows,
                        calendar=calendar_trade_stats(result),
                        daily_returns=daily_returns(result.oos_equity),
                    )
                    rows[(symbol, design.key, freq.name, tier.name)] = row
                    matched[(symbol, design.key, freq.name, tier.name)] = (
                        run_constant_fraction_benchmark(
                            bars, symbol, tier, study, max(result.diagnostics.exposure, 1e-6)
                        )
                    )
                    _log_row(registry, row, snapshot_id, trial_id_prefix, census)

    dsr_by_symbol_tier: dict[tuple[str, str], float] = {}
    dsr_inputs: dict[tuple[str, str], dict[str, Any]] = {}
    for symbol in series_by_symbol:
        for tier in tiers:
            value, inputs = _dsr_for(registry, symbol, tier, rows, trial_id_prefix)
            dsr_by_symbol_tier[(symbol, tier.name)] = value
            dsr_inputs[(symbol, tier.name)] = inputs

    return FrontierResult(
        snapshot_id=snapshot_id,
        census=census,
        tiers=tuple(tiers),
        frequencies=tuple(frequencies),
        designs=tuple(designs),
        symbols=tuple(series_by_symbol),
        rows=rows,
        benchmarks=benchmarks,
        matched=matched,
        n_windows=expected_windows,
        dsr_by_symbol_tier=dsr_by_symbol_tier,
        dsr_inputs=dsr_inputs,
    )


def trial_config(row: FrontierRow, census: DayCensus) -> dict[str, Any]:
    variant = variant_for(row.design, row.frequency)
    return {
        "study": "breakout_cost_frequency_frontier_v1",
        "row_kind": "variant",
        "symbol": row.symbol,
        "frequency": row.frequency.name,
        "minutes_per_bar": row.frequency.minutes,
        "bars_per_day": row.frequency.bars_per_day,
        "tier": row.tier.name,
        "fee_bps": row.tier.fee_bps,
        "venue_role": row.tier.role,
        "cost_stack": row.tier.cost_stack_config(),
        "calendar_days": len(census.complete),
        "dropped_days": [day.isoformat() for day, _ in census.incomplete],
        **row.design.describe(row.frequency),
        **row.study.to_dict(),
        "strategy": variant.fixed_config,
    }


def _log_row(
    registry: TrialRegistry,
    row: FrontierRow,
    snapshot_id: str,
    prefix: str,
    census: DayCensus,
) -> None:
    registry.add_trial(
        trial_id=f"{prefix}-{row.symbol}-{row.design.key}-{row.frequency.name}-{row.tier.name}",
        config=trial_config(row, census),
        params={
            "n_oos_bars": row.result.n_oos_bars,
            "n_windows": row.n_windows,
            "oos_start": row.result.oos_equity[0][0].isoformat(),
            "oos_end": row.result.oos_equity[-1][0].isoformat(),
        },
        metrics=row.metrics(),
        snapshot_id=snapshot_id,
        seed=row.study.seed,
    )


def _dsr_for(
    registry: TrialRegistry,
    symbol: str,
    tier: CostTier,
    rows: Mapping[tuple[str, str, str, str], FrontierRow],
    prefix: str,
) -> tuple[float, dict[str, Any]]:
    """DSR per (symbol, tier), pool = every (design x frequency) configuration at that
    cell, in PER-CALENDAR-DAY units (D164).

    D98's units contract says the logged metric, `sr` and `T` must share one period. The
    obvious per-bar choice does not survive a multi-frequency pool: a 1h bar and a 1d bar
    are not the same period, so pooling per-bar Sharpes would be exactly the units bug
    D98 exists to prevent. Collapsing every equity curve to end-of-day NAV gives one
    period (the calendar day) and one T (the shared OOS day count) for the whole pool."""
    at_cell = [r for key, r in rows.items() if key[0] == symbol and key[3] == tier.name]
    degenerate = [
        f"{r.design.key}/{r.frequency.name}" for r in at_cell if not math.isfinite(r.sharpe_daily)
    ]
    if degenerate:
        # A cell that never traded has a flat NAV, so `sharpe` returns -inf (a flat
        # series against a positive risk-free rate is infinitely bad, D49) and the
        # pool's variance becomes meaningless. Loud rather than silently dropped:
        # dropping it would shrink N, which is precisely what D98's pool rule forbids.
        raise ValueError(
            f"{symbol} @ {tier.name}: configuration(s) {', '.join(degenerate)} produced a "
            "non-finite daily Sharpe (a flat equity curve — the rule never traded over the "
            "out-of-sample span). The DSR pool cannot include them and must not silently "
            "exclude them; widen the span or drop the frequency from the ladder."
        )
    best = max(at_cell, key=lambda r: r.sharpe_daily)
    returns = np.asarray(best.daily_returns, dtype=float)
    mu, sd = returns.mean(), returns.std(ddof=0)
    inputs: dict[str, Any] = {
        "observed_sr_daily": best.sharpe_daily,
        "best_config": f"{best.design.key}/{best.frequency.name}",
        "t": len(returns),
        "skew": float(np.mean((returns - mu) ** 3) / sd**3) if sd > 0 else 0.0,
        "kurt": float(np.mean((returns - mu) ** 4) / sd**4) if sd > 0 else 3.0,
        "units": "per calendar day (D164)",
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
        "sharpe_daily",
        sr=float(inputs["observed_sr_daily"]),
        t=int(inputs["t"]),
        skew=float(inputs["skew"]),
        kurt=float(inputs["kurt"]),
        include=_in_pool,
    )
    pool = [t.metrics["sharpe_daily"] for t in registry.all_trials() if _in_pool(t)]
    inputs["n_trials"] = len(pool)
    inputs["var_trials_daily"] = float(np.var(pool, ddof=1)) if len(pool) > 1 else float("nan")
    return dsr, inputs


# ----------------------------------------------------------- the crossover rule (D165)

CROSSOVER_RULE = (
    "The crossover frequency is the COARSEST (slowest) bar at which the cost curve has "
    "risen above the trend edge, read three ways because the three fail differently. "
    "(1) IN-SAMPLE SHARPE: net annualised Sharpe at `taker_40bp` <= 0. (2) IN-SAMPLE "
    "COST SHARE: costs >= 100% of gross P&L. (3) SPLICED: cost drag in Sharpe units "
    "(annual fee drag / annual volatility, measured HERE) >= the gross annualised Sharpe "
    "measured over 2015-2025 daily data in BREAKOUT_RESULTS.md at `maker_0bp`. Readings "
    "(1) and (2) are contaminated whenever the window's own gross edge is near zero or "
    "negative; reading (3) is not, because neither of its terms has this window's P&L in "
    "it. All three are read off the ladder ordered slow -> fast, and 'no rung on the "
    "ladder' is a legitimate answer. Fixed before the numbers were looked at."
)

REFERENCE_GROSS_SHARPE: dict[str, float] = {"BTC-USD": 1.27, "ETH-USD": 0.84}
"""The `plateau_40_10` gross (zero-fee, `maker_0bp`) annualised Sharpe measured over
2015-2025 DAILY bars in `BREAKOUT_RESULTS.md`. Imported as a number, not re-measured:
this study's own 730-day window is far too short to estimate a gross edge (its Sharpe
standard error is roughly +/-1), and splicing a well-measured edge onto a well-measured
cost curve is the only honest way to locate a crossover from data this short. The splice
is labelled everywhere it is used, and it is the reason reading (3) is reported ALONGSIDE
the in-sample readings rather than instead of them."""


def crossover(
    result: FrontierResult, symbol: str, design_key: str, tier_name: str = REFERENCE_TIER
) -> dict[str, Any]:
    """Apply D165's three readings to one (symbol, design) ladder. Frequencies are walked
    from the coarsest bar to the finest, which is the direction turnover increases."""
    ladder = sorted(result.frequencies, key=lambda f: -f.minutes)
    reference = REFERENCE_GROSS_SHARPE.get(symbol, float("nan"))
    sharpe_cross: str | None = None
    cost_cross: str | None = None
    spliced_cross: str | None = None
    ladder_rows = []
    for freq in ladder:
        row = result.row(symbol, design_key, freq.name, tier_name)
        net_sharpe = row.sharpe_annual
        cost_share = row.result.diagnostics.cost_share_of_gross
        drag = row.cost_drag_sharpe_units
        ladder_rows.append(
            {
                "frequency": freq.name,
                "sharpe_annual": net_sharpe,
                "cost_share_of_gross": cost_share,
                "annual_turnover": row.result.diagnostics.annual_turnover,
                "fee_drag_annual": row.fee_drag_annual,
                "cost_drag_sharpe_units": drag,
                "reference_gross_sharpe": reference,
            }
        )
        if sharpe_cross is None and net_sharpe <= 0.0:
            sharpe_cross = freq.name
        if cost_cross is None and cost_share == cost_share and cost_share >= 1.0:
            cost_cross = freq.name
        if spliced_cross is None and drag == drag and reference == reference and drag >= reference:
            spliced_cross = freq.name
    return {
        "symbol": symbol,
        "design": design_key,
        "tier": tier_name,
        "sharpe_crossover": sharpe_cross,
        "cost_share_crossover": cost_cross,
        "spliced_crossover": spliced_cross,
        "reference_gross_sharpe": reference,
        "ladder": ladder_rows,
    }


def cost_wedge(result: FrontierResult, symbol: str, design_key: str, freq_name: str,
               tier_name: str = REFERENCE_TIER, free_tier: str = "maker_0bp") -> float:
    """Gross-minus-net Sharpe: the annualised Sharpe at the zero-fee tier minus the
    Sharpe at `tier_name`. This is the cost half of the frontier, in Sharpe units."""
    gross = result.row(symbol, design_key, freq_name, free_tier).sharpe_annual
    net = result.row(symbol, design_key, freq_name, tier_name).sharpe_annual
    return gross - net


# --------------------------------------------- 15m / 30m turnover measurement (D163)


@dataclass
class TurnoverMeasurement:
    """NOT a performance result. A trade-count-and-fee measurement over a span too short
    to contain a single walk-forward training window."""

    symbol: str
    frequency: Frequency
    tier: CostTier
    n_bars: int
    n_days: float
    n_closed_trades: int
    n_open_at_end: int
    traded_notional: float
    total_costs: float
    annual_turnover: float
    fee_drag_annual: float
    """Costs paid, annualised, as a fraction of starting capital: what fees ALONE would
    consume per year at this trading rate. Deliberately not netted against any return."""
    median_hold_days: float
    whipsaw_rate_3d: float
    gross_pnl: float

    def to_metrics(self) -> dict[str, float]:
        return {
            "n_bars": float(self.n_bars),
            "n_days": self.n_days,
            "n_closed_trades": float(self.n_closed_trades),
            "n_open_at_end": float(self.n_open_at_end),
            "traded_notional": self.traded_notional,
            "total_costs": self.total_costs,
            "annual_turnover": self.annual_turnover,
            "fee_drag_annual": self.fee_drag_annual,
            "median_hold_days": self.median_hold_days,
            "whipsaw_rate_3d": self.whipsaw_rate_3d,
            "gross_pnl": self.gross_pnl,
        }


def measure_turnover(
    bars: Sequence[TimestampedBar],
    volumes: Sequence[float],
    symbol: str,
    freq: Frequency,
    tier: CostTier,
    design: Design = DESIGN_B,
    starting_cash: float = 100_000.0,
) -> TurnoverMeasurement:
    """Run the rule straight through the engine over whatever span is available, with NO
    walk-forward and NO return claim (D163).

    60 days of 15m data does not contain one 252-day training window, and shrinking the
    window to 252 *bars* would make the training slice 2.6 days — economically
    meaningless, and exactly the kind of number this project exists not to print. What
    IS measurable on 60 days is how often the rule trades and what that costs, because
    turnover is a property of the rule and the bar size, not of the sample's returns."""
    from ..engine.allocator import ConstantSplitAllocator
    from ..engine.backtest import run_backtest
    from ..instruments.equity import Equity
    from ..strategies.breakout import build_breakout_strategy
    from .breakout_study import CRYPTO_QUANTITY_PRECISION
    from .trade_diagnostics import extract_episodes

    n_entry, n_exit, vol_window = design.windows(freq)
    config = breakout_config(
        n_entry=n_entry, n_exit=n_exit, weight_source=weight_source_config(freq, vol_window)
    )
    strategy = build_breakout_strategy(config, f"measure-{symbol}", symbol)
    if len(bars) <= strategy.warm_up_bars() + 2:
        raise ValueError(
            f"{symbol} @ {freq.name}: {len(bars)} bars is not enough for a "
            f"{strategy.warm_up_bars()}-bar warm-up"
        )
    result = run_backtest(
        bars_by_instrument={symbol: list(bars)},
        instruments={symbol: Equity(symbol=symbol, quantity_precision=CRYPTO_QUANTITY_PRECISION)},
        strategies=[strategy],
        cost_stack=tier.build(),
        allocator=ConstantSplitAllocator(),
        starting_cash=starting_cash,
        fill_timing="next_open",
    )
    episodes = extract_episodes(result, symbol, list(bars))
    closed = [e for e in episodes if not e.is_open]
    held = holding_periods_days(episodes)
    span_days = (bars[-1].timestamp - bars[0].timestamp).total_seconds() / 86400.0
    years = span_days / 365.0
    mean_equity = statistics.fmean([nav for _, nav in result.equity_curve])
    traded = sum(e.traded_notional for e in episodes)
    costs = sum(e.costs for e in episodes)
    return TurnoverMeasurement(
        symbol=symbol,
        frequency=freq,
        tier=tier,
        n_bars=len(bars),
        n_days=span_days,
        n_closed_trades=len(closed),
        n_open_at_end=len(episodes) - len(closed),
        traded_notional=traded,
        total_costs=costs,
        annual_turnover=traded / mean_equity / years if mean_equity and years else float("nan"),
        fee_drag_annual=costs / mean_equity / years if mean_equity and years else float("nan"),
        median_hold_days=float(statistics.median(held)) if held else float("nan"),
        whipsaw_rate_3d=(sum(1 for h in held if h <= WHIPSAW_DAYS) / len(held))
        if held
        else float("nan"),
        gross_pnl=sum(e.gross_pnl for e in episodes),
    )


# ------------------------------------------------------------------------- rendering


def _pct(x: float) -> str:
    return "n/a" if x != x else f"{x:+.2%}"


def _num(x: float, places: int = 2) -> str:
    return "n/a" if x != x else f"{x:.{places}f}"


FRONTIER_HEADER = (
    "| Frequency | Total return | CAGR | Sharpe (ann.) | Max DD | Exposure | Trades | "
    "Ann. turnover | Costs / gross P&L | Gross−net Sharpe |"
)


def render_frontier_table(
    result: FrontierResult, symbol: str, design_key: str, tier_name: str
) -> str:
    lines = [FRONTIER_HEADER, "|---" * 10 + "|"]
    for freq in sorted(result.frequencies, key=lambda f: -f.minutes):
        row = result.row(symbol, design_key, freq.name, tier_name)
        d = row.result.diagnostics
        wedge = cost_wedge(result, symbol, design_key, freq.name, tier_name)
        open_note = f" +{d.n_open_at_end} open" if d.n_open_at_end else ""
        lines.append(
            f"| `{freq.name}` | {_pct(row.total_return)} | {_pct(row.cagr)} | "
            f"{_num(row.sharpe_annual)} | {_num(row.max_drawdown * 100, 1)}% | "
            f"{_num(d.exposure * 100, 1)}% | {d.n_closed_trades}{open_note} | "
            f"{_num(d.annual_turnover, 1)}x | {_num(d.cost_share_of_gross * 100, 1)}% | "
            f"{_num(wedge)} |"
        )
    return "\n".join(lines)


def render_cost_curve(
    result: FrontierResult, symbol: str, design_key: str, tier_name: str = REFERENCE_TIER
) -> str:
    """The cost half of the frontier, in units that do not depend on this window's P&L,
    against the gross edge measured over ten years of daily data (D165 reading 3)."""
    reference = REFERENCE_GROSS_SHARPE.get(symbol, float("nan"))
    lines = [
        "| Frequency | Ann. turnover | Fee drag / yr | Strategy ann. vol | "
        "Cost drag (Sharpe units) | vs. 2015–2025 gross Sharpe | Verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    for freq in sorted(result.frequencies, key=lambda f: -f.minutes):
        row = result.row(symbol, design_key, freq.name, tier_name)
        drag = row.cost_drag_sharpe_units
        verdict = "—" if drag != drag else ("**costs win**" if drag >= reference else "edge survives")
        lines.append(
            f"| `{freq.name}` | {_num(row.result.diagnostics.annual_turnover, 1)}x | "
            f"{_num(row.fee_drag_annual * 100, 2)}% | {_num(row.annual_vol * 100, 1)}% | "
            f"{_num(drag)} | {_num(reference)} | {verdict} |"
        )
    return "\n".join(lines)


def render_character_table(result: FrontierResult, symbol: str, design_key: str,
                           tier_name: str = REFERENCE_TIER) -> str:
    """The strategy's economic character, in calendar units — so the reader can see it
    stop being a trend follower rather than just watch a Sharpe fall."""
    lines = [
        "| Frequency | Entry / exit window | Trades / yr | Median hold | p90 hold | "
        "Whipsaw rate (≤3 days) | Exposure |",
        "|---|---|---|---|---|---|---|",
    ]
    for freq in sorted(result.frequencies, key=lambda f: -f.minutes):
        row = result.row(symbol, design_key, freq.name, tier_name)
        c, d = row.calendar, row.result.diagnostics
        n_entry, n_exit, _ = row.design.windows(freq)
        window = (
            f"{n_entry}/{n_exit} bars = "
            f"{n_entry / freq.bars_per_day:.4g}d / {n_exit / freq.bars_per_day:.4g}d"
        )
        lines.append(
            f"| `{freq.name}` | {window} | {_num(c['trades_per_year'], 1)} | "
            f"{_num(c['median_hold_days'], 2)} d | {_num(c['p90_hold_days'], 2)} d | "
            f"{_num(c['whipsaw_rate_3d'] * 100, 1)}% | {_num(d.exposure * 100, 1)}% |"
        )
    return "\n".join(lines)


def render_tier_ladder(result: FrontierResult, symbol: str, design_key: str) -> str:
    """Sharpe at every frequency x every tier — the frontier's two curves in one grid."""
    tiers = result.tiers
    lines = [
        "| Frequency | " + " | ".join(f"`{t.name}`" for t in tiers) + " | Cost wedge (0bp→40bp) |",
        "|---" * (len(tiers) + 2) + "|",
    ]
    for freq in sorted(result.frequencies, key=lambda f: -f.minutes):
        cells = [
            _num(result.row(symbol, design_key, freq.name, t.name).sharpe_annual) for t in tiers
        ]
        lines.append(
            f"| `{freq.name}` | " + " | ".join(cells) + " | "
            f"{_num(cost_wedge(result, symbol, design_key, freq.name))} |"
        )
    return "\n".join(lines)


def render_benchmark_table(result: FrontierResult, symbol: str, design_key: str,
                           tier_name: str = REFERENCE_TIER) -> str:
    lines = [
        "| Frequency | Strategy return | Strategy Sharpe | Buy & hold return | B&H Sharpe | "
        "Constant-fraction return | CF Sharpe | CF fraction |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for freq in sorted(result.frequencies, key=lambda f: -f.minutes):
        row = result.row(symbol, design_key, freq.name, tier_name)
        hold = result.benchmarks[(symbol, freq.name, tier_name)]
        cf = result.matched[(symbol, design_key, freq.name, tier_name)]
        lines.append(
            f"| `{freq.name}` | {_pct(row.total_return)} | {_num(row.sharpe_annual)} | "
            f"{_pct(hold.total_return)} | {_num(hold.sharpe_annual(row.study))} | "
            f"{_pct(cf.total_return)} | {_num(cf.sharpe_annual(row.study))} | "
            f"{row.result.diagnostics.exposure:.0%} |"
        )
    return "\n".join(lines)


def render_measurement_table(measurements: Sequence[TurnoverMeasurement]) -> str:
    lines = [
        "| Frequency | Bars | Closed trades | Median hold | Whipsaw (≤3 d) | Ann. turnover | "
        "Fees alone, annualised |",
        "|---|---|---|---|---|---|---|",
    ]
    for m in sorted(measurements, key=lambda m: m.frequency.minutes):
        hold = "n/a" if m.median_hold_days != m.median_hold_days else f"{m.median_hold_days:.2f} d"
        whip = "n/a" if m.whipsaw_rate_3d != m.whipsaw_rate_3d else f"{m.whipsaw_rate_3d * 100:.1f}%"
        lines.append(
            f"| `{m.frequency.name}` | {m.n_bars:,} | {m.n_closed_trades}"
            f"{f' +{m.n_open_at_end} open' if m.n_open_at_end else ''} | "
            f"{hold} | {whip} | "
            f"{_num(m.annual_turnover, 1)}x | {_num(m.fee_drag_annual * 100, 1)}% |"
        )
    return "\n".join(lines)

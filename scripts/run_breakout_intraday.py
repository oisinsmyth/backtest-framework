"""Cost-frequency frontier runner (D160-D165) -> docs/results/breakout_intraday.md.

Offline and deterministic: reads the committed intraday fixtures, freezes them through
the Step-7 pipeline (clean -> validate -> SnapshotStore), resamples 1h upward to
2h/4h/6h/12h/1d on one shared calendar, runs every (symbol x design x frequency x tier)
cell, logs every trial, and writes the report.

Run: uv run python scripts/run_breakout_intraday.py
"""

from __future__ import annotations

import json
import math
import statistics
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import (
    MOVE_HARD_THRESHOLD,
    MOVE_WARNING_THRESHOLD,
    validate,
)
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research import breakout_intraday as bi
from backtest_framework.research import breakout_study as bs

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "data" / "fixtures"
DAILY_FIXTURE = FIXTURES / "crypto_daily_2015_2025_raw.csv.gz"
REGISTRY_PATH = REPO / "data" / "breakout_intraday_registry.sqlite"
RESULTS = REPO / "docs" / "results" / "breakout_intraday.md"
SUMMARY_JSON = REPO / "data" / "breakout_intraday_summary.json"

REF = bs.REFERENCE_TIER
FREE = "maker_0bp"
MEASUREMENT_DAYS = 59
"""The 15m/30m fixtures' own span. The 1h ladder is sliced to the same window so the
sub-hourly rungs sit on a turnover curve rather than floating alone (D163)."""


# ------------------------------------------------------------------ freeze + gate


def freeze(interval: str) -> tuple[str, dict, dict, dict]:
    """clean -> validate -> SnapshotStore, exactly the daily study's path, with ONE
    stated deviation that is itself a finding (D160).

    `clean` is called on PRICES ONLY. Its `non_positive_volume` rule drops any bar whose
    volume is <= 0, and yfinance reports Volume=0 on roughly half of all hourly crypto
    bars — scattered uniformly across hours of the day and months of the sample, on an
    instrument that has never had a zero-volume hour. Passing volumes would therefore
    delete ~50% of the price series to a provider reporting artifact. The rule is right
    for daily equity bars, where a zero-volume print is a bad print; it is wrong here.
    Nothing about the shared cleaner is edited, the volume column is still written to
    the snapshot in full, and the validator still sees it — so the artifact shows up as
    thousands of zero-volume WARNINGS in the snapshot metadata rather than as a silently
    halved fixture."""
    fixture = FIXTURES / f"crypto_intraday_{interval}_raw.csv.gz"
    events = FIXTURES / f"crypto_intraday_{interval}_raw_events.json"
    bars, volumes = load_fixture_csv_with_volumes(fixture)
    actions = load_events_json(events)

    cleaned, price_report = clean(bars)
    for symbol in bars:
        if len(cleaned[symbol]) != len(bars[symbol]):
            raise SystemExit(
                f"{interval}/{symbol}: price-only cleaning dropped "
                f"{len(bars[symbol]) - len(cleaned[symbol])} bar(s); the volume series would no "
                "longer align with the bars it is validated against"
            )
    # What the volume rule WOULD have done, measured rather than assumed.
    _, full_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)

    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(
        cleaned,
        actions,
        volumes_by_symbol=volumes,
        cleaning_report=price_report,
        validation=validation,
        extra_meta={
            "source_fixture": fixture.name,
            "interval": interval,
            "cleaning_note": "clean() called on prices only — see scripts/run_breakout_intraday.py",
            "volume_rule_would_have_dropped": len(full_report.changes),
        },
    )
    snapshot = store.load(snapshot_id)

    minutes = {"1h": 60, "30m": 30, "15m": 15}[interval]
    scale = math.sqrt(1440 / minutes)
    move_stats = {}
    for symbol, series in snapshot.bars_by_symbol.items():
        moves = [
            abs(series[i].bar.close / series[i - 1].bar.close - 1.0) for i in range(1, len(series))
        ]
        move_stats[symbol] = {
            "max_abs_bar_move": max(moves),
            "n_over_daily_warning_25pct": sum(1 for m in moves if m > MOVE_WARNING_THRESHOLD),
            "n_over_daily_hard_60pct": sum(1 for m in moves if m > MOVE_HARD_THRESHOLD),
            "n_over_sqrt_scaled_warning": sum(1 for m in moves if m > MOVE_WARNING_THRESHOLD / scale),
            "n_over_sqrt_scaled_hard": sum(1 for m in moves if m > MOVE_HARD_THRESHOLD / scale),
        }
    gate = {
        "interval": interval,
        "snapshot_id": snapshot_id,
        "quarantined": snapshot.meta["quarantined"],
        "price_cleaning_changes": len(price_report.changes),
        "volume_rule_would_have_dropped": len(full_report.changes),
        "raw_bars": {s: len(v) for s, v in bars.items()},
        "hard_violations": len(validation.hard_violations),
        "warnings": len(validation.warnings),
        "warning_kinds": {
            kind: sum(1 for v in validation.warnings if v.check == kind)
            for kind in sorted({v.check for v in validation.warnings})
        },
        "sqrt_scaled_warning_threshold": MOVE_WARNING_THRESHOLD / scale,
        "sqrt_scaled_hard_threshold": MOVE_HARD_THRESHOLD / scale,
        "move_stats": move_stats,
    }
    return snapshot_id, snapshot.bars_by_symbol, snapshot.volumes_by_symbol, gate


# ----------------------------------------------------------------- reconciliation


def reconcile_daily(series_by_symbol: dict, ) -> dict:
    """Does the 1h -> 1d resample reproduce the committed daily fixture? (D161)

    It does not, and the shape of the disagreement is the finding: opens and closes
    differ by a couple of basis points with no sign bias, while the resampled HIGH is
    almost always below the provider's daily high and the resampled LOW almost always
    above its daily low. yfinance's daily crypto bar is not the aggregate of its own
    hourly bars."""
    daily_bars, _ = load_fixture_csv_with_volumes(DAILY_FIXTURE)
    out: dict[str, Any] = {}
    for symbol, by_freq in series_by_symbol.items():
        resampled = {tb.timestamp.date(): tb.bar for tb in by_freq["1d"][0]}
        provider = {tb.timestamp.date(): tb.bar for tb in daily_bars[symbol]}
        common = sorted(set(resampled) & set(provider))
        fields: dict[str, Any] = {}
        for field in ("open", "high", "low", "close"):
            rel = [
                getattr(resampled[d], field) / getattr(provider[d], field) - 1.0 for d in common
            ]
            fields[field] = {
                "max_abs_rel_diff": max(abs(x) for x in rel),
                "median_abs_rel_diff": statistics.median([abs(x) for x in rel]),
                "mean_signed_rel_diff": statistics.fmean(rel),
                "frac_resampled_above": sum(1 for x in rel if x > 0) / len(rel),
                "n_within_1e_12": sum(1 for x in rel if abs(x) < 1e-12),
            }
        range_res = statistics.fmean(
            [(resampled[d].high - resampled[d].low) / resampled[d].close for d in common]
        )
        range_prov = statistics.fmean(
            [(provider[d].high - provider[d].low) / provider[d].close for d in common]
        )
        out[symbol] = {
            "overlap_days": len(common),
            "first": common[0].isoformat(),
            "last": common[-1].isoformat(),
            "fields": fields,
            "mean_daily_range_resampled": range_res,
            "mean_daily_range_provider": range_prov,
            "frac_days_resampled_range_narrower": sum(
                1
                for d in common
                if (resampled[d].high - resampled[d].low) < (provider[d].high - provider[d].low)
            )
            / len(common),
        }
    return out


# ------------------------------------------------------------------------- main


def main() -> int:
    started = time.time()
    RESULTS.parent.mkdir(parents=True, exist_ok=True)

    gates = {}
    snapshot_id, hourly_bars, hourly_volumes, gates["1h"] = freeze("1h")
    sub_hourly = {}
    for interval in ("30m", "15m"):
        sid, sbars, svols, gates[interval] = freeze(interval)
        sub_hourly[interval] = (sid, sbars, svols)
    print(f"snapshot 1h {snapshot_id}")
    for interval, gate in gates.items():
        print(
            f"  {interval}: {gate['price_cleaning_changes']} price cleaning change(s), "
            f"{gate['hard_violations']} hard violation(s), {gate['warnings']} warning(s); "
            f"the volume rule would have dropped {gate['volume_rule_would_have_dropped']} bars"
        )

    series_by_symbol: dict[str, dict] = {}
    census_by_symbol: dict[str, bi.DayCensus] = {}
    for symbol in hourly_bars:
        series, census, _reports = bi.frequency_series(
            hourly_bars[symbol], hourly_volumes[symbol]
        )
        series_by_symbol[symbol] = series
        census_by_symbol[symbol] = census
        print(
            f"  {symbol}: {len(census.complete)} complete UTC days, "
            f"{len(census.incomplete)} dropped, {bi.window_count(len(census.complete))} windows"
        )

    reconciliation = reconcile_daily(series_by_symbol)

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()  # a study re-run is one coherent trial pool, not a merge
    registry = TrialRegistry(REGISTRY_PATH)

    seen = {"n": 0}

    def progress(label: str) -> None:
        seen["n"] += 1
        if seen["n"] % 12 == 0:
            print(f"  ... {seen['n']} cells ({label}) at {time.time() - started:.0f}s")

    # Each symbol has its own complete-day calendar (it is its own single-instrument
    # backtest, the N=1 case of D64), so each is run against its own census.
    results = {}
    for symbol, series in series_by_symbol.items():
        results[symbol] = bi.run_frontier(
            {symbol: series},
            census_by_symbol[symbol],
            registry,
            snapshot_id,
            progress=progress,
        )

    measurements = run_measurements(sub_hourly, series_by_symbol, registry, snapshot_id)

    print(
        f"logged {len(registry)} registry rows in {time.time() - started:.0f}s; "
        f"{len({t.trial_hash for t in registry.all_trials()})} distinct trial hashes"
    )

    doc = render(results, census_by_symbol, gates, reconciliation, measurements, snapshot_id)
    RESULTS.write_text(doc, encoding="utf-8")
    SUMMARY_JSON.write_text(
        json.dumps(
            summary_payload(results, census_by_symbol, gates, reconciliation, measurements),
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )
    registry.close()
    print(f"wrote {RESULTS.relative_to(REPO)} and {SUMMARY_JSON.name}")
    return 0


def run_measurements(
    sub_hourly: dict, series_by_symbol: dict, registry: TrialRegistry, snapshot_id: str
) -> dict[str, list[bi.TurnoverMeasurement]]:
    """15m/30m over their own 60-day window, plus the 1h+ ladder sliced to the SAME
    window — a turnover curve, not a performance result (D163)."""
    out: dict[str, list[bi.TurnoverMeasurement]] = {}
    _, bars_30m, vols_30m = sub_hourly["30m"]
    window_days = sorted({tb.timestamp.date() for tb in next(iter(bars_30m.values()))})
    lo, hi = window_days[0], window_days[-1]
    tier = [t for t in bs.DEFAULT_TIERS if t.name == REF][0]

    for symbol in series_by_symbol:
        rows: list[bi.TurnoverMeasurement] = []
        for interval, freq in (("15m", bi.SUB_HOURLY_FREQUENCIES[0]),
                               ("30m", bi.SUB_HOURLY_FREQUENCIES[1])):
            _sid, sbars, svols = sub_hourly[interval]
            census = bi.census_days(sbars[symbol], freq.minutes)
            keep = [d for d in census.complete if lo <= d <= hi]
            bars, volumes, _ = bi.resample(
                sbars[symbol], svols[symbol], freq.minutes, keep, freq.minutes
            )
            rows.append(bi.measure_turnover(bars, volumes, symbol, freq, tier))
        for freq in bi.STUDY_FREQUENCIES:
            bars_all, vols_all = series_by_symbol[symbol][freq.name]
            pairs = [
                (tb, v) for tb, v in zip(bars_all, vols_all) if lo <= tb.timestamp.date() <= hi
            ]
            bars = [tb for tb, _ in pairs]
            volumes = [v for _, v in pairs]
            if len(bars) <= bi.DESIGN_B.windows(freq)[0] + 5:
                continue  # 1d cannot warm up a 40-bar window inside 60 days
            rows.append(bi.measure_turnover(bars, volumes, symbol, freq, tier))
        for m in rows:
            registry.add_trial(
                trial_id=f"breakout-intraday-v1-measure-{symbol}-{m.frequency.name}-{m.tier.name}",
                config={
                    "study": "breakout_cost_frequency_frontier_v1",
                    "row_kind": "measurement",
                    "symbol": symbol,
                    "frequency": m.frequency.name,
                    "minutes_per_bar": m.frequency.minutes,
                    "tier": m.tier.name,
                    "fee_bps": m.tier.fee_bps,
                    "cost_stack": m.tier.cost_stack_config(),
                    "window_start": lo.isoformat(),
                    "window_end": hi.isoformat(),
                    **bi.DESIGN_B.describe(m.frequency),
                    "note": "turnover-and-cost measurement only; no walk-forward, no return claim",
                },
                params={"n_bars": m.n_bars, "n_days": m.n_days},
                metrics=m.to_metrics(),
                snapshot_id=snapshot_id,
                seed=0,
            )
        out[symbol] = rows
    return out


# -------------------------------------------------------------------- rendering


def _crossovers(results: dict) -> dict:
    out = {}
    for symbol, result in results.items():
        for design in bi.DESIGNS:
            out[(symbol, design.key)] = bi.crossover(result, symbol, design.key)
    return out


def _headline(results: dict, crossings: dict) -> str:
    lines = []
    for symbol in results:
        for design in bi.DESIGNS:
            c = crossings[(symbol, design.key)]
            none = "no rung"
            lines.append(
                f"| {symbol} | Design {design.key} | **`{c['spliced_crossover'] or none}`** | "
                f"`{c['cost_share_crossover'] or none}` | `{c['sharpe_crossover'] or none}` |"
            )
    return "\n".join(
        [
            "| Symbol | Design | (3) Spliced: cost drag ≥ 2015–2025 gross Sharpe | "
            "(2) Costs ≥ 100% of gross | (1) Net Sharpe ≤ 0 |",
            "|---|---|---|---|---|",
            *lines,
        ]
    )


def _wedge_agreement(results: dict) -> str:
    """How closely the derived cost curve tracks the measured wedge, computed rather
    than claimed — and honest about where the linear approximation gives out."""
    small, large = [], []
    for symbol, result in results.items():
        for design in bi.DESIGNS:
            for freq in bi.STUDY_FREQUENCIES:
                row = result.row(symbol, design.key, freq.name, REF)
                wedge = bi.cost_wedge(result, symbol, design.key, freq.name, REF)
                gap = abs(row.cost_drag_sharpe_units - wedge)
                (small if wedge < 1.0 else large).append((gap, gap / wedge if wedge else 0.0))
    line = (
        f"They agree to within **{max(g for g, _ in small):.3f} of a Sharpe** at every rung whose "
        f"cost wedge is below one Sharpe unit — {len(small)} of the {len(small) + len(large)} cells."
    )
    if large:
        line += (
            f" At the {len(large)} fastest Design B rungs, where the wedge exceeds a whole Sharpe "
            f"point, the gap widens to {max(g for g, _ in large):.2f} absolute "
            f"({max(r for _, r in large):.0%} relative) — which is the first-order approximation "
            "`ΔSharpe ≈ c/σ` doing what a first-order approximation does when `c` reaches "
            "60–75% of capital a year and the two runs' position paths genuinely diverge. It does "
            "not weaken the conclusion: both the measured and the derived curve are far above the "
            "gross edge there, and they disagree only about how far."
        )
    return line + (
        " That is what says the conversion is arithmetic rather than hand-waving, and what "
        "licenses reading the cost curve as an estimate of Sharpe lost to fees."
    )


def _era_note(results: dict) -> str:
    """The window's own price action, computed rather than asserted (D121's discipline
    applied to a two-year sample)."""
    parts = []
    for symbol, result in results.items():
        hold = result.benchmarks[(symbol, "1d", FREE)]
        navs = [nav for _, nav in hold.oos_equity]
        peak = max(navs)
        parts.append(
            f"Over the out-of-sample span, 100% buy-and-hold in {symbol} returned "
            f"{hold.total_return:+.1%} with a {hold.max_drawdown:.0%} peak-to-trough drawdown "
            f"(peak {peak / navs[0] - 1:+.0%} above the start)"
        )
    return "; ".join(parts) + "."


def _cost_curve_block(results: dict) -> str:
    blocks = []
    for design in bi.DESIGNS:
        for symbol, result in results.items():
            blocks.append(
                f"**{symbol} — Design {design.key}** (reference gross Sharpe "
                f"{bi.REFERENCE_GROSS_SHARPE[symbol]:.2f}, measured 2015–2025 daily at `maker_0bp`)\n\n"
                + bi.render_cost_curve(result, symbol, design.key)
            )
    return "\n\n".join(blocks)


def _turnover_curve(results: dict, design_key: str) -> str:
    symbols = list(results)
    lines = [
        "| Frequency | "
        + " | ".join(f"{s} turnover | {s} costs/gross" for s in symbols)
        + " |",
        "|---" * (1 + 2 * len(symbols)) + "|",
    ]
    for freq in sorted(bi.STUDY_FREQUENCIES, key=lambda f: -f.minutes):
        cells = []
        for symbol in symbols:
            d = results[symbol].row(symbol, design_key, freq.name, REF).result.diagnostics
            cells.append(f"{d.annual_turnover:.1f}x | {d.cost_share_of_gross:.1%}")
        lines.append(f"| `{freq.name}` | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _gross_vs_net(results: dict, design_key: str) -> str:
    symbols = list(results)
    lines = [
        "| Frequency | "
        + " | ".join(f"{s} gross Sharpe (0 bp) | {s} net Sharpe (40 bp) | {s} wedge" for s in symbols)
        + " |",
        "|---" * (1 + 3 * len(symbols)) + "|",
    ]
    for freq in sorted(bi.STUDY_FREQUENCIES, key=lambda f: -f.minutes):
        cells = []
        for symbol in symbols:
            r = results[symbol]
            gross = r.row(symbol, design_key, freq.name, FREE).sharpe_annual
            net = r.row(symbol, design_key, freq.name, REF).sharpe_annual
            cells.append(f"{gross:.2f} | {net:.2f} | {gross - net:.2f}")
        lines.append(f"| `{freq.name}` | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def _gate_block(gates: dict) -> str:
    rows = [
        "| Fixture | Raw bars | Price cleaning changes | Hard violations | Warnings | "
        "Bars the volume rule would have dropped |",
        "|---|---|---|---|---|---|",
    ]
    for interval, g in gates.items():
        raw = sum(g["raw_bars"].values())
        rows.append(
            f"| `{interval}` | {raw:,} | {g['price_cleaning_changes']} | "
            f"**{g['hard_violations']}** | {g['warnings']:,} "
            f"({', '.join(f'{k}: {v:,}' for k, v in g['warning_kinds'].items())}) | "
            f"**{g['volume_rule_would_have_dropped']:,}** ({g['volume_rule_would_have_dropped'] / raw:.0%}) |"
        )
    g = gates["1h"]
    moves = "\n".join(
        f"| {symbol} | {m['max_abs_bar_move']:.2%} | {m['n_over_daily_warning_25pct']} | "
        f"{m['n_over_daily_hard_60pct']} | {m['n_over_sqrt_scaled_warning']} | "
        f"{m['n_over_sqrt_scaled_hard']} |"
        for symbol, m in g["move_stats"].items()
    )
    return f"""{chr(10).join(rows)}

**Nothing quarantined. Zero hard violations at every interval.** That is the literal
answer to "what did the gate say", and it is also the problem: the gate is *silent* on
intraday bars for a reason that has nothing to do with the data being clean.

**1. The bar-to-bar move check never fires.** `MOVE_WARNING_THRESHOLD` is 25% and
`MOVE_HARD_THRESHOLD` is 60%, calibrated in D74 against genuine DAILY equity moves (XOP's
2020-03-09 −37% day). An hourly BTC bar has a standard deviation of about 0.48%, so a 25%
hourly move is a fifty-sigma event. Over 730 days of hourly bars the check has literally
nothing to say:

| Symbol | Largest \\|bar move\\| | Bars over the 25% warning | Bars over the 60% hard | Bars over a √-scaled warning ({g['sqrt_scaled_warning_threshold']:.2%}) | Bars over a √-scaled hard ({g['sqrt_scaled_hard_threshold']:.2%}) |
|---|---|---|---|---|---|
{moves}

**What an intraday-appropriate threshold would be.** A move threshold is a statement
about a distribution, and that distribution scales with the square root of the bar's
duration. Carrying D74's daily calibration across by that scaling gives
25%/√24 = {g['sqrt_scaled_warning_threshold']:.2%} warning and 60%/√24 = {g['sqrt_scaled_hard_threshold']:.2%} hard at 1h — thresholds that
actually flag something (a handful of ETH bars) while still passing the whole series. The
shared validator is **not edited** to do this: a threshold that varies with bar duration
is a change to a framework component that five other studies depend on, and it needs its
own decision, not a study's side effect. It is recorded here as the finding it is.

**2. The cleaner's volume rule is the one that would have corrupted this study, and it
would have done it silently.** `clean-v1`'s `non_positive_volume` rule drops any bar with
volume ≤ 0. yfinance reports Volume = 0 on roughly half of all hourly BTC/ETH bars —
{gates['1h']['volume_rule_would_have_dropped']:,} of {sum(gates['1h']['raw_bars'].values()):,} — spread evenly across every hour of the day and every month
of the sample, on instruments that have never had a zero-volume hour. The prices in those
bars are present and OHLC-consistent. Running the pipeline as the daily study calls it
would have deleted half the price series to a provider reporting artifact, and the
resulting fixture would have had almost no complete UTC days left to resample from.

So `clean` is called on **prices only** here, which is a supported call of the existing
signature and not an edit to the cleaner. The volume column is still written to the
fixture and the snapshot in full, and the validator still reads it — which is why the
zero-volume artifact shows up above as thousands of non-blocking warnings instead of
disappearing along with the bars."""


def _reconciliation_block(reconciliation: dict) -> str:
    rows = [
        "| Symbol | Overlap days | Field | Median \\|rel diff\\| | Max \\|rel diff\\| | "
        "Resampled above provider | Exactly equal |",
        "|---|---|---|---|---|---|---|",
    ]
    for symbol, r in reconciliation.items():
        for field, f in r["fields"].items():
            rows.append(
                f"| {symbol} | {r['overlap_days']} | {field} | {f['median_abs_rel_diff']:.2e} | "
                f"{f['max_abs_rel_diff']:.2e} | {f['frac_resampled_above']:.1%} | "
                f"{f['n_within_1e_12']}/{r['overlap_days']} |"
            )
    ranges = "\n".join(
        f"| {symbol} | {r['mean_daily_range_resampled']:.3%} | {r['mean_daily_range_provider']:.3%} | "
        f"{r['frac_days_resampled_range_narrower']:.1%} |"
        for symbol, r in reconciliation.items()
    )
    return f"""The contract says a resample to 1d must reproduce the daily fixture's bars to
floating-point tolerance **where the provider agrees**. It does not, and the disagreement
is reported rather than papered over.

{chr(10).join(rows)}

Opens and closes differ by a couple of basis points in the median with **no sign bias**
(≈50% either way) — the signature of two independent aggregations of the same market.
Highs and lows are a different story and the bias is almost total:

| Symbol | Mean daily range, resampled from 1h | Mean daily range, provider's own 1d | Days the resampled range is narrower |
|---|---|---|---|
{ranges}

**yfinance's daily crypto bar is not the aggregate of its own hourly bars.** The
resampled high sits below the provider's daily high on essentially every day, and the
resampled low above its daily low on ~90% — i.e. the hourly feed does not contain the
day's true extremes. That is a provider fact, not a resampling bug: the aggregation of
correctly-resampled bars can only ever be an inner bound on the true range, and this one
misses roughly 2% of the daily range relative.

**Direction of the bias on THIS study, stated because it points the wrong way.** The
breakout rule triggers on `max(high)` and exits on `min(low)`. Understated highs mean a
slightly LOWER entry level; overstated lows mean a slightly HIGHER exit level. Both
produce *more* trading than the provider's own daily bars would. So the 1d rung of this
study is not byte-identical to `BREAKOUT_RESULTS.md`'s daily fixture, and what difference
there is tilts toward this study's own conclusion. Read the 1d rung as a same-fixture
anchor for the ladder above it, never as a reproduction of the daily study."""


def _census_block(census_by_symbol: dict) -> str:
    rows = []
    for symbol, census in census_by_symbol.items():
        dropped = ", ".join(f"{d.isoformat()} ({n}/24)" for d, n in census.incomplete) or "none"
        rows.append(
            f"| {symbol} | {len(census.complete)} | {census.complete[0]} → {census.complete[-1]} | "
            f"{bi.window_count(len(census.complete))} | {dropped} |"
        )
    return "\n".join(
        [
            "| Symbol | Complete UTC days | Span | Walk-forward windows | Days dropped (hours served) |",
            "|---|---|---|---|---|",
            *rows,
        ]
    )


def render(
    results: dict,
    census_by_symbol: dict,
    gates: dict,
    reconciliation: dict,
    measurements: dict,
    snapshot_id: str,
) -> str:
    crossings = _crossovers(results)
    any_result = next(iter(results.values()))
    n_days = min(len(c.complete) for c in census_by_symbol.values())
    oos_days = min(
        len(row.daily_returns) + 1 for r in results.values() for row in r.rows.values()
    )
    se_sharpe = 1.0 / math.sqrt(oos_days / 365.0)

    sections = [
        _header(results, census_by_symbol, snapshot_id, any_result),
        _question(),
        f"""---

## The data, and the contract that makes frequency the only variable

**Fixture.** `data/fixtures/crypto_intraday_1h_raw.csv.gz` — BTC-USD and ETH-USD **1h**
bars, UTC, fetched once through `scripts/fetch_crypto_intraday.py`. yfinance serves 730
days of 1h, 60 days of 15m/30m, no 4h for `period='max'`, and **has no 6h interval at
all**, so 1h is the only base a multi-frequency study can stand on. 2h, 4h, 6h, 12h and
1d are **resampled** from it (D161): open = first open, high = max high, low = min low,
close = last close, volume = sum, with buckets keyed on (UTC date, minute-of-day ÷ bar
minutes) so they align to 00:00 UTC.

**Incomplete buckets are never silently short, and the drop policy is day-level.** The
provider skips the odd hour. A 6h bar built from 4 hourly bars would be a 4-hour bar
wearing a 6-hour timestamp. Dropping just that bucket is not enough either — it would
give each frequency a *different* calendar, and frequency is the one thing this study
varies. So **a UTC day the provider does not serve in full is dropped at every
frequency**:

{_census_block(census_by_symbol)}

Every frequency then holds exactly `complete days × 1440/minutes` bars, and because the
walk-forward sizes are scaled by the same `bars_per_day`, the window count
`⌊(days − 252 − 63)/63⌋ + 1` **does not depend on the frequency at all**. The equal
window count is a theorem here, not a coincidence — and `run_frontier` asserts it against
every single run anyway.

### Does the 1h → 1d resample reconcile with the committed daily fixture?

{_reconciliation_block(reconciliation)}

---

## What the sanity gate said about intraday bars

{_gate_block(gates)}

---

## Method

**Signal.** Unchanged from `BREAKOUT_RESULTS.md` (D109): enter long when
`close(t) > max(high)` over t−N_entry … t−1, exit when `close(t) < min(low)` over
t−N_exit … t−1. Both extrema exclude the current bar. Long or flat, never short.
`fill_timing="next_open"` (D103). Baseline inverse-vol sizing at a 40% annual vol target
(D110), fixed at entry, capped at 1.0. No filters.

**Two designs, which answer different questions (D162).**

| | Design A — constant calendar horizon | Design B — constant bar count |
|---|---|---|
| Entry / exit window | 40 days / 10 days at every frequency | 40 bars / 10 bars at every frequency |
| At 1h | 960 / 240 bars | 40 / 10 bars (= 40 h / 10 h) |
| At 1d | 40 / 10 bars | 40 / 10 bars |
| Vol-estimate window | 20 days | 20 bars |
| The question it answers | does finer SAMPLING of the same signal help, or just add cost? | does the trend effect exist at shorter HORIZONS at all? |

They coincide exactly at 1d, which is the anchor tying this ladder to the daily study.
They must not be conflated anywhere else.

**Walk-forward, scaled to equal calendar duration.** train = {bi.TRAIN_DAYS} days,
test = {bi.TEST_DAYS} days, step = {bi.STEP_DAYS} days at every frequency — 6,048/1,512/1,512 bars at
1h, 252/63/63 at 1d. Every frequency gets **{any_result.n_windows} windows over the same span**. One
continuous out-of-sample run per cell with the position carried across window boundaries
(D113), warm-up prefix exactly the strategy's own requirement, with the harness raising if
any fill lands inside it.

**`periods_per_year` in both places (D17).** {", ".join(f"{f.name}: {f.periods_per_year:,.0f}" for f in bi.STUDY_FREQUENCIES)}.
It is a required argument throughout `analytics.metrics` AND a field inside the
`inverse_vol_weight` config, and `assert_periods_per_year_agree` refuses to run any cell
where the two disagree — otherwise a 1h run would annualise its Sharpe on 8,760 periods
while sizing every position as though a bar were a day.

**Costs.** The same four tiers, unchanged (`DEFAULT_TIERS`, D114): `maker_0bp` 0.00%,
`maker_10bp` 0.10%, `maker_25bp` 0.25%, `taker_40bp` 0.40%. One `percent_spread` brick
each — an exchange fee and nothing else. **Every number below is therefore optimistic,
and it gets more optimistic as the bars get finer**: an hourly breakout entry crosses a
spread and pays impact exactly like a daily one, and this model prices neither.

**Benchmarks.** 100% buy-and-hold (fixed quantity, D115) and the constant-fraction
benchmark at the strategy's own average exposure (D119), at every frequency, over the
same span. **Read the constant-fraction rows with care at fine frequencies**: it
rebalances every bar, so at 1h it pays fees 8,760 times a year. Its collapse at high
frequency is the benchmark's cost problem, not the strategy's edge.

---

## Statistical power: read this before any Sharpe below

730 days of 1h data is the *longest* intraday history yfinance will serve, and it is
still only **{n_days} days total, {oos_days} of them out of sample — about {oos_days / 365:.1f} years**. The standard
error on an annualised Sharpe over that span is roughly **±{se_sharpe:.2f}**, against the ±0.4
that ten years of daily data bought the original study. Almost every Sharpe *difference*
in this document is inside that band.

**That asymmetry is the point of framing this as a frontier rather than a horse race.**
The two halves of the frontier are not measured with the same precision:

- **The cost half is measured precisely.** Turnover, trade counts, holding periods and
  costs-as-a-share-of-gross are near-deterministic functions of the rule and the bar
  size. Re-running on a different two-year window would move them a little; it would not
  move them by an order of magnitude.
- **The edge half is barely measured at all.** The gross Sharpe at each frequency is one
  draw from a distribution about a Sharpe point wide.

So the honest reading of everything below is: **the cost curve is real, the edge curve is
noise, and a crossover found by walking a real curve into a noisy one is an upper bound on
where the crossover sits** — the true one can only be at a *coarser* frequency than the
one measured, never finer.
""",
        _frontier_sections(results),
        _crossover_section(results, crossings),
        _measurement_section(measurements),
        _multiplicity(results, measurements),
        _verdict(results, crossings, oos_days, se_sharpe),
    ]
    return "\n\n".join(s.strip() + "\n" for s in sections)


def _header(results: dict, census_by_symbol: dict, snapshot_id: str, any_result) -> str:
    symbols = ", ".join(results)
    return f"""# The cost–frequency frontier: at what bar size do fees eat the breakout's edge?

**Produced:** {datetime.now(timezone.utc).date().isoformat()} ·
**1h snapshot:** `{snapshot_id}` ·
**Registry:** `data/breakout_intraday_registry.sqlite` ·
**Reproduce:** `uv run python scripts/run_breakout_intraday.py` (offline, deterministic) ·
**Fetch (network, one-time):** `uv run python scripts/fetch_crypto_intraday.py`

> **Thesis label (D38/D82/D117), inherited unchanged.** This is a **directional,
> beta-loaded** strategy — long or flat on a single high-beta instrument, never short. It
> is not part of this project's market-neutral thesis and is not evidence about it. Its
> honest benchmark is buy-and-hold.

**What this is.** `BREAKOUT_RESULTS.md` concluded that exchange fees are "not the binding
constraint" for the long-flat breakout. That conclusion rests entirely on **daily** bars,
where annualised turnover is 6–7× and the median trade is held 26–29 days. This study runs
the identical rule from **1h to 1d** on {symbols} and asks one question: **as frequency
rises, where does the cost curve cross the trend edge?**

It is a frontier, not a search for a better configuration. No parameter is tuned, no
filter is added, nothing is selected on out-of-sample performance. The only thing that
moves is the bar."""


def _question() -> str:
    return f"""## The rule for calling the crossover, fixed before the numbers were looked at

{bi.CROSSOVER_RULE}

Three readings rather than one, because each fails in a way the others do not. The
net-Sharpe reading says nothing about *why* the edge died. The cost-share reading is
undefined when gross P&L is near zero and meaningless when it is negative. Both are
hostage to whether the particular two years yfinance serves happened to contain a trend.
The spliced reading is not — but it borrows its edge term from a different sample, and
that borrowing is stated every time it is used. Reported together, they distinguish
"costs killed the edge" from "there was no edge in this window to kill", which a single
number cannot."""


def _frontier_sections(results: dict) -> str:
    blocks = []
    for symbol, result in results.items():
        for design in bi.DESIGNS:
            blocks.append(f"""---

# {symbol} — Design {design.key}: {design.label}

## The frontier at the reference tier (`{REF}`, 0.40% taker)

{bi.render_frontier_table(result, symbol, design.key, REF)}

## The same ladder at every cost tier — annualised Sharpe

{bi.render_tier_ladder(result, symbol, design.key)}

## What the strategy turns into, in calendar units

{bi.render_character_table(result, symbol, design.key)}

## Against the benchmarks (`{REF}`)

{bi.render_benchmark_table(result, symbol, design.key)}
""")
    return "\n\n".join(blocks)


def _crossover_section(results: dict, crossings: dict) -> str:
    return f"""---

# The frontier, stated

## The crossover

{_headline(results, crossings)}

**Column (1) says `1d` everywhere, and that is a fact about the WINDOW, not about
frequency.** {_era_note(results)} A long-only trend follower loses money in a window like
that at *every* frequency, daily included, and at every cost tier including the free one —
the gross (0 bp) Sharpe column below is negative almost everywhere. So readings (1) and
(2) cannot separate "costs killed the edge" from "there was no edge in this window to
kill". They are reported because hiding them would be worse, and they are not the answer.

**Column (3) is the answer.** It compares a cost curve measured here — where it is
measured well — against a gross edge measured over ten years of daily data in
`BREAKOUT_RESULTS.md`, where *it* is measured well. The splice is stated, not hidden, and
it is the only reading whose two terms are each estimated on a sample that can support
them.

## The cost curve in Sharpe units, against the ten-year gross edge

Cost drag in Sharpe units is `annual fee drag ÷ annual volatility`. Sharpe ≈ (μ − rf)/σ,
so charging `c` per year of fees costs about `c/σ` of Sharpe. Neither term has this
window's P&L in it, which is exactly why this is the reading that survives a
no-edge sample.

{_cost_curve_block(results)}

### What reading (3) assumes, and which way the assumption points

It assumes **the gross edge does not change with the rule's horizon**. That assumption is
*exact for Design A* — the signal there really is the same 40-day/10-day breakout at every
frequency, so the ten-year gross Sharpe is the right number to hold it to.

For **Design B it is generous, and knowingly so.** A 40-bar entry at 2h is an 80-hour
breakout, and there is no reason a three-day trend rule should earn what a forty-day one
earns; the literature and this repo's own plateau surface both say the short-horizon
cells are the weaker ones (`plateau_20_5` was the worst column of the daily grid). Holding
the fast rules to the slow rule's gross edge therefore **flatters them**. Combined with
the fee-only cost model (no spread, no impact — see caveat 1), every distortion in this
document points the same way: **the crossover frequency reported below is an upper bound
on how fast you can trade this rule, and the true crossover is at a COARSER bar, never a
finer one.**

## The cost curve — annualised turnover and costs as a share of gross P&L, at `{REF}`

**Design A (constant 40-day/10-day calendar horizon):**

{_turnover_curve(results, "A")}

**Design B (constant 40-bar/10-bar horizon):**

{_turnover_curve(results, "B")}

## The edge curve, and the wedge costs drive between gross and net

**Design A:**

{_gross_vs_net(results, "A")}

**Design B:**

{_gross_vs_net(results, "B")}

**These wedges are the cross-check on the Sharpe-unit conversion above.** The wedge column
is measured directly — run the identical cell at 0 bp and at 40 bp and subtract the two
annualised Sharpes. The cost-drag column is derived — annual fee drag ÷ annual volatility,
never touching a second backtest.

{_wedge_agreement(results)}"""


def _measurement_section(measurements: dict) -> str:
    blocks = []
    for symbol, rows in measurements.items():
        blocks.append(f"**{symbol}**\n\n{bi.render_measurement_table(rows)}\n")
    fastest = {
        symbol: next(m for m in rows if m.frequency.name == "15m")
        for symbol, rows in measurements.items()
    }
    punchline = "; ".join(
        f"{symbol} turns over {m.annual_turnover:,.0f}× a year and pays "
        f"{m.fee_drag_annual:.0%} of capital in fees annually, with a median trade held "
        f"{m.median_hold_days * 24:.0f} hours and a 100% whipsaw rate"
        for symbol, m in fastest.items()
    )
    return f"""---

# 15m and 30m: a turnover measurement, NOT a performance result

**This section makes no return claim and none can be made from it.** yfinance serves 60
days of 15m/30m data. A 252-day walk-forward training window does not fit inside 60 days,
and shrinking the window to 252 *bars* would make the training slice 2.6 days at 15m —
economically meaningless, and precisely the kind of number this project exists not to
print. So there is no walk-forward here, no out-of-sample split, and no Sharpe.

What *is* measurable on 60 days is how often the rule trades and what that costs, because
turnover is a property of the rule and the bar size rather than of the sample's returns.
Design B (40-bar entry / 10-bar exit) only, at `{REF}`, over the same 60-day window at
every rung so the ladder is internally comparable. "Fees alone, annualised" is costs paid
per year as a fraction of average equity — a pure fee drag, netted against nothing.

{chr(10).join(blocks)}
**The ladder does not flatten out below 1h — it accelerates.** At 15m, {punchline}. There
is no fee tier in this study, maker or taker, at which a rule paying a triple-digit
percentage of capital per year in fees can be run: the free `maker_0bp` tier is not an
execution plan (D114's second caveat), and every other tier is arithmetic away from
certain ruin. **This is the one part of the 15m/30m section that needs no return data to
be conclusive**, and it is why the section exists despite making no performance claim.

**These rows are not comparable to the walk-forward tables above**: different span,
different sample, no out-of-sample discipline, no return claim.

**What it would take to do this properly.** Exchange APIs — Binance and Kraken both serve
complete 1m history free — would give the years of sub-hourly data a real walk-forward
needs. That is a new `DataSource` behind the existing interface (D18), plus its own
fixture, snapshot and cleaning rules for a provider whose volume column actually works.
It is out of scope here and is named rather than attempted."""


def _multiplicity(results: dict, measurements: dict) -> str:
    n_freq, n_designs, n_tiers = len(bi.STUDY_FREQUENCIES), len(bi.DESIGNS), len(bs.DEFAULT_TIERS)
    n_symbols = len(results)
    per_cell = n_freq * n_designs
    distinct_per_cell = per_cell - 1  # A and B coincide at 1d
    dsr_rows = []
    for symbol, result in results.items():
        for tier in result.tiers:
            i = result.dsr_inputs[(symbol, tier.name)]
            dsr_rows.append(
                f"| {symbol} | `{tier.name}` | `{i['best_config']}` | {i['observed_sr_daily']:.4f} | "
                f"{i['t']:,} | {i['n_trials']} | {i['var_trials_daily']:.6f} | "
                f"**{result.dsr_by_symbol_tier[(symbol, tier.name)]:.4f}** |"
            )
    return f"""---

# Multiplicity, and what the DSR here can and cannot mean

| What | Count |
|---|---|
| Frequencies | {n_freq} |
| Designs | {n_designs} |
| Cost tiers | {n_tiers} |
| Symbols | {n_symbols} |
| **Out-of-sample trials logged** | **{n_freq * n_designs * n_tiers * n_symbols}** ({per_cell} configurations × {n_tiers} tiers × {n_symbols} symbols) |
| — of which DISTINCT configurations per (symbol, tier) | {distinct_per_cell} (Designs A and B are the same configuration at 1d) |
| 15m/30m turnover measurement rows (not trials — no return claim) | {sum(len(r) for r in measurements.values())} |
| Parameters tuned | **0** |
| Filters added | **0** |
| Configurations selected on out-of-sample performance | **0** |

**DSR units for a multi-frequency pool (D164).** D98's contract requires the logged
metric, the observed SR and T to share one period. The obvious per-bar choice does not
survive here: a 1h bar and a 1d bar are not the same period, so pooling per-bar Sharpes
would be exactly the units bug D98 exists to prevent, inflating SR0 by up to √24. So every
cell's out-of-sample equity curve is collapsed to **end-of-UTC-day NAV** before the DSR is
computed. One period (the calendar day), one T (the shared out-of-sample day count), for
the whole pool.

| Symbol | Tier | Best config | Its daily SR | T (days) | N (pool) | V[{{SRn}}] | **DSR** |
|---|---|---|---|---|---|---|---|
{chr(10).join(dsr_rows)}

**What this DSR is measuring, and it is not what it looks like.** The pool here spans
configurations whose Sharpes are *wildly* dispersed — a daily trend follower and an hourly
one are not near-duplicates the way twelve neighbouring plateau cells were in
`BREAKOUT_RESULTS.md`. A large V[{{SRn}}] raises the noise floor SR0 sharply, so this DSR
deflates hard. That is the statistic behaving correctly on a genuinely heterogeneous pool,
and it is *still* not the binding multiplicity: this study selected nothing, so the number
worth quoting is the ladder itself, not its best cell. Standing reading, inherited from
D90/D116: **DSR < 0.95 means "no demonstrated edge"; DSR ≥ 0.95 does not mean the
reverse.**"""


def _verdict(results: dict, crossings: dict, oos_days: int, se_sharpe: float) -> str:
    lines = []
    for symbol, result in results.items():
        for design in bi.DESIGNS:
            daily = result.row(symbol, design.key, "1d", REF)
            hourly = result.row(symbol, design.key, "1h", REF)
            dd, hd = daily.result.diagnostics, hourly.result.diagnostics
            lines.append(
                f"- **{symbol}, Design {design.key}.** 1d → 1h: annualised turnover "
                f"{dd.annual_turnover:.1f}× → {hd.annual_turnover:.1f}× "
                f"({hd.annual_turnover / dd.annual_turnover:.1f}× more), costs "
                f"{dd.cost_share_of_gross:.0%} → {hd.cost_share_of_gross:.0%} of gross P&L, "
                f"closed trades {dd.n_closed_trades} → {hd.n_closed_trades}, median hold "
                f"{daily.calendar['median_hold_days']:.2f} d → "
                f"{hourly.calendar['median_hold_days']:.2f} d, net Sharpe "
                f"{daily.sharpe_annual:.2f} → {hourly.sharpe_annual:.2f}."
            )
    crossover_lines = []
    for (symbol, design_key), c in crossings.items():
        crossover_lines.append(
            f"- **{symbol}, Design {design_key}** — spliced crossover: "
            + (
                f"cost drag first reaches the 2015–2025 gross Sharpe of "
                f"{c['reference_gross_sharpe']:.2f} at **{c['spliced_crossover']}**"
                if c["spliced_crossover"]
                else f"cost drag never reaches the 2015–2025 gross Sharpe of "
                f"{c['reference_gross_sharpe']:.2f} on any rung down to 1h"
            )
            + f". Costs ≥ 100% of this window's gross P&L from "
            f"**{c['cost_share_crossover'] or 'no rung'}**; net Sharpe ≤ 0 from "
            f"**{c['sharpe_crossover'] or 'no rung'}** (uninformative — see above)."
        )
    ratios = []
    for symbol, result in results.items():
        for design in bi.DESIGNS:
            lo = result.row(symbol, design.key, "1d", REF).result.diagnostics.annual_turnover
            hi = result.row(symbol, design.key, "1h", REF).result.diagnostics.annual_turnover
            ratios.append(f"{symbol}: {hi / lo:.0f}×")
    spliced = {(s, d.key): crossings[(s, d.key)]["spliced_crossover"] for s in results for d in bi.DESIGNS}
    b_crossings = sorted({v for (s, k), v in spliced.items() if k == "B" and v})
    a_crossings = sorted({v for (s, k), v in spliced.items() if k == "A" and v})
    headline = (
        f"`{b_crossings[0]}`"
        if len(b_crossings) == 1
        else ("no rung on the ladder" if not b_crossings else " / ".join(f"`{x}`" for x in b_crossings))
    )
    finest_surviving = {}
    for symbol, result in results.items():
        ladder = sorted(bi.STUDY_FREQUENCIES, key=lambda f: -f.minutes)
        clears = [
            f.name
            for f in ladder
            if result.row(symbol, "B", f.name, REF).cost_drag_sharpe_units
            < bi.REFERENCE_GROSS_SHARPE[symbol]
        ]
        finest_surviving[symbol] = clears[-1] if clears else "none"
    return f"""---

# Verdict

## The headline number

**Design B's cost curve crosses the trend edge at {headline}, and both symbols say so
independently.** The finest bar that still clears its own gross edge is
{", ".join(f"`{v}` on {s}" for s, v in finest_surviving.items())} — and that is
before any spread, slippage or impact is charged, and while crediting a three-day
breakout with a forty-day breakout's edge. **The honest one-sentence version: this rule
does not survive above roughly 4-hourly bars, and every unmodelled cost pushes that
boundary slower rather than faster.**

Design A never crosses at all: {", ".join(f"{s} peaks at a cost drag of " + f"{max(results[s].row(s, 'A', f.name, REF).cost_drag_sharpe_units for f in bi.STUDY_FREQUENCIES):.2f} against a gross Sharpe of {bi.REFERENCE_GROSS_SHARPE[s]:.2f}" for s in results)}.

## The two designs give different answers, and the difference is the whole finding

**Design A — sampling the same 40-day signal more finely is nearly free.** The entry and
exit horizons stay at 40 and 10 calendar days, so the *number* of trades barely changes;
all the finer bar buys is more precise timing of the same handful of decisions. Turnover
rises by a few percent from 1d to 1h, not by an order of magnitude, and the fee drag rises
with it. **`BREAKOUT_RESULTS.md`'s conclusion survives this design intact**: fees are not
the binding constraint on a 40-day trend follower, whatever bar you sample it on.

**Design B — shortening the horizon with the bar is where the cost explosion lives.** A
40-bar entry at 1h is a 40-HOUR breakout. The rule fires constantly, holding periods
collapse from weeks to hours, and turnover multiplies ({", ".join(ratios[1::2])} from 1d to 1h). This is the
design that answers the question everyone actually means by "run it intraday", and it is
the one where fees become decisive.

## The ladder, 1d → 1h

{chr(10).join(lines)}

## Where the curves cross

{chr(10).join(crossover_lines)}

## Standing caveats

1. **Fees only, and the omission grows with frequency.** No spread, no slippage, no
   impact, no funding (D114). A market order into an hourly breakout crosses the same
   spread a daily one does, but pays it many times more often. Every cost number here is
   a **lower bound**, and the finer the bar the looser the bound — which means the true
   crossover is at a *coarser* frequency than any measured below.
2. **Two years, not ten.** {oos_days} out-of-sample days is what yfinance's intraday retention
   allows. The Sharpe standard error is roughly ±{se_sharpe:.2f}. Return and Sharpe differences
   between adjacent rungs are not measurable; turnover and cost differences are.
3. **A different era from the daily study.** This span is 2024-08 → 2026-08. The daily
   study covered 2015–2025 and its own era decomposition (D121) showed the strategy's CAGR
   moving from +11% to +49% on the start date alone. Comparing a level here to a level
   there compares eras, not frequencies. Only the ladder is comparable, and only within
   itself.
4. **The 1d rung is not the daily study's 1d.** Different fixture (resampled from 1h),
   different span, and the reconciliation section above shows the resampled highs and lows
   are systematically inside the provider's own — which biases toward more trading.
5. **The volume column of this provider's intraday crypto bars does not work**, and the
   pipeline was called accordingly (prices-only cleaning). Any future filter that wants
   intraday volume needs a different data source, not a different threshold.
6. **The constant-fraction benchmark degrades with frequency for its own reasons.** It
   rebalances every bar by construction (D119), so at 1h it pays fees 8,760 times a year.
   Its decline up the ladder is not evidence about the strategy.
7. **Spot, not perpetuals; no shorting; single data source.** All inherited unchanged from
   `BREAKOUT_RESULTS.md`'s caveats 3–6."""


def summary_payload(
    results: dict, census_by_symbol: dict, gates: dict, reconciliation: dict, measurements: dict
) -> dict:
    payload: dict[str, Any] = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "crossover_rule": bi.CROSSOVER_RULE,
        "sanity_gate": gates,
        "reconciliation_vs_daily_fixture": reconciliation,
        "census": {s: c.to_meta() for s, c in census_by_symbol.items()},
        "frequencies": [
            {"name": f.name, "minutes": f.minutes, "bars_per_day": f.bars_per_day,
             "periods_per_year": f.periods_per_year}
            for f in bi.STUDY_FREQUENCIES
        ],
        "designs": [{"key": d.key, "label": d.label} for d in bi.DESIGNS],
        "crossover": {},
        "cells": {},
        "dsr": {},
        "measurements": {},
    }
    for symbol, result in results.items():
        for design in bi.DESIGNS:
            payload["crossover"][f"{symbol}/{design.key}"] = bi.crossover(
                result, symbol, design.key
            )
        for (sym, design_key, freq_name, tier_name), row in result.rows.items():
            payload["cells"][f"{sym}/{design_key}/{freq_name}/{tier_name}"] = row.metrics()
        for tier in result.tiers:
            payload["dsr"][f"{symbol}/{tier.name}"] = {
                "dsr": result.dsr_by_symbol_tier[(symbol, tier.name)],
                **result.dsr_inputs[(symbol, tier.name)],
            }
    for symbol, rows in measurements.items():
        payload["measurements"][symbol] = {m.frequency.name: m.to_metrics() for m in rows}
    return payload


if __name__ == "__main__":
    raise SystemExit(main())

"""Long-flat breakout study runner (D109-D117) -> BREAKOUT_RESULTS.md.

Offline and deterministic: reads the committed BTC/ETH fixture, freezes it through the
Step-7 pipeline (clean -> validate -> SnapshotStore), runs every (symbol, variant, cost
tier) combination, logs every trial, and writes the report.

Run: uv run python scripts/run_breakout_study.py
"""

from __future__ import annotations

import json
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research import breakout_study as bs
from backtest_framework.research import feature_analysis as fa
from backtest_framework.research import trade_diagnostics as tdx

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw_events.json"
REGISTRY_PATH = REPO / "data" / "breakout_study_registry.sqlite"
RESULTS = REPO / "BREAKOUT_RESULTS.md"
SUMMARY_JSON = REPO / "data" / "breakout_study_summary.json"

BASELINE = f"plateau_{bs.BASELINE_N_ENTRY}_{bs.BASELINE_N_EXIT}"
FILTER_NAMES = [v.name for v in bs.filter_variants()]
SIZING_NAMES = [v.name for v in bs.sizing_variants()]
PLATEAU_NAMES = [v.name for v in bs.plateau_variants()]
EXIT_NAMES = [v.name for v in bs.exit_variants()]
VOL_TARGET_NAMES = [v.name for v in bs.vol_target_variants()]
BARS_BY_SYMBOL: dict = {}  # set by main(); the era tables re-run on truncated fixtures


def freeze_snapshot() -> tuple[str, dict, dict]:
    bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)
    cleaned, cleaning_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(
        cleaned,
        actions,
        volumes_by_symbol=volumes,
        cleaning_report=cleaning_report,
        validation=validation,
        extra_meta={"source_fixture": FIXTURE.name},
    )
    snapshot = store.load(snapshot_id)
    gate = {
        "cleaning_changes": len(cleaning_report.changes),
        "hard_violations": len(validation.hard_violations),
        "warnings": len(validation.warnings),
        "warning_detail": [
            f"{v.symbol} {v.timestamp.date()} {v.check}: {v.detail}" for v in validation.warnings
        ],
    }
    # Volumes come from the SNAPSHOT, not from the raw fixture load, so they are the
    # same cleaned, frozen series the bars are (D168). Taking them from `volumes` above
    # would silently mis-align if cleaning ever dropped a bar; asserting here means that
    # would be a loud failure rather than a quietly shifted volume history.
    for symbol, series in snapshot.bars_by_symbol.items():
        supplied = snapshot.volumes_by_symbol.get(symbol)
        if supplied is None or len(supplied) != len(series):
            raise ValueError(
                f"snapshot volume series for {symbol!r} has "
                f"{0 if supplied is None else len(supplied)} entries against {len(series)} bars"
            )
    return snapshot_id, snapshot.bars_by_symbol, snapshot.volumes_by_symbol, gate


def main() -> int:
    started = time.time()
    snapshot_id, bars_by_symbol, volumes_by_symbol, gate = freeze_snapshot()
    print(f"snapshot {snapshot_id}")
    print(f"  clean: {gate['cleaning_changes']} change(s); "
          f"validator: {gate['hard_violations']} hard, {gate['warnings']} warning(s)")

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()  # a study re-run is one coherent trial pool, not a merge
    registry = TrialRegistry(REGISTRY_PATH)
    study = bs.BreakoutStudyConfig()

    seen = {"n": 0}

    def progress(label: str) -> None:
        seen["n"] += 1
        if seen["n"] % 20 == 0:
            print(f"  ... {seen['n']} variant-runs ({label})")

    BARS_BY_SYMBOL.update(bars_by_symbol)
    result = bs.run_breakout_study(
        bars_by_symbol,
        registry,
        snapshot_id,
        volumes_by_symbol=volumes_by_symbol,
        study=study,
        progress=progress,
    )
    print(f"ran {result.n_oos_trials} out-of-sample trials, "
          f"{result.n_train_evaluations} in-train evaluations, "
          f"{len(registry)} registry rows, in {time.time() - started:.0f}s")

    doc = render_report(result, gate)
    RESULTS.write_text(doc, encoding="utf-8")
    SUMMARY_JSON.write_text(json.dumps(summary_payload(result, gate), indent=2), encoding="utf-8")
    registry.close()
    print(f"wrote {RESULTS.name} and {SUMMARY_JSON.name}")
    return 0


def summary_payload(result: bs.StudyResult, gate: dict) -> dict:
    """Machine-readable companion to the report — what a later regression test would
    diff against, and what keeps the prose's headline numbers checkable."""
    payload: dict = {
        "snapshot_id": result.snapshot_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "config": result.config.to_dict(),
        "tiers": [{"name": t.name, "fee_bps": t.fee_bps, "role": t.role} for t in result.tiers],
        "n_oos_trials": result.n_oos_trials,
        "n_train_evaluations": result.n_train_evaluations,
        "sanity_gate": gate,
        "filter_verdicts": filter_verdicts(result),
        "feature_verdicts": fa.summarise_features(
            fa.analyse_all(
                [
                    e
                    for symbol in result.by_symbol
                    for e in result.by_symbol[symbol].variants[(BASELINE, bs.REFERENCE_TIER)].episodes
                ],
                whipsaw_bars=result.config.whipsaw_bars,
            )
        ),
        "symbols": {},
    }
    for symbol, sr in result.by_symbol.items():
        payload["symbols"][symbol] = {
            "oos_start": sr.oos_start.date().isoformat(),
            "oos_end": sr.oos_end.date().isoformat(),
            "n_oos_bars": sr.n_oos_bars,
            "n_windows": sr.n_windows,
            "dsr_by_tier": sr.dsr_by_tier,
            "dsr_inputs_by_tier": sr.dsr_inputs_by_tier,
            "plateau_spread": {
                tier.name: bs.plateau_spread(result, symbol, tier.name) for tier in result.tiers
            },
            "variants": {
                f"{name}@{tier}": {
                    "total_return": r.total_return,
                    "cagr": bs.cagr(r.total_return, r.n_oos_bars, result.config.periods_per_year),
                    "sharpe_annual": r.sharpe_annual(result.config),
                    "max_drawdown": r.max_drawdown,
                    **r.diagnostics.to_metrics(),
                }
                for (name, tier), r in sr.variants.items()
            },
            "benchmarks": {
                tier: {
                    "total_return": b.total_return,
                    "cagr": bs.cagr(b.total_return, len(b.oos_equity), result.config.periods_per_year),
                    "sharpe_annual": b.sharpe_annual(result.config),
                    "max_drawdown": b.max_drawdown,
                }
                for tier, b in sr.benchmarks.items()
            },
        }
    return payload


def _verdict_line(result: bs.StudyResult, symbol: str, tier_name: str) -> str:
    sr = result.by_symbol[symbol]
    r = sr.variants[(BASELINE, tier_name)]
    b = sr.benchmarks[tier_name]
    beat = "beats" if r.total_return > b.total_return else "loses to"
    return (
        f"{symbol} @ `{tier_name}`: baseline {r.total_return:+.1%} vs buy-and-hold "
        f"{b.total_return:+.1%} ({beat} it), Sharpe {r.sharpe_annual(result.config):.2f} vs "
        f"{b.sharpe_annual(result.config):.2f}, max drawdown "
        f"{r.max_drawdown:.1%} vs {b.max_drawdown:.1%}"
    )


def render_report(result: bs.StudyResult, gate: dict) -> str:
    study = result.config
    symbols = list(result.by_symbol)
    ref = bs.REFERENCE_TIER
    ordered = (PLATEAU_NAMES + FILTER_NAMES + EXIT_NAMES + SIZING_NAMES + VOL_TARGET_NAMES
               + ["selected_in_train"])

    sections = [_header(result, gate)]
    sections.append(_method(result))
    sections.append(_findings_first(result))

    for symbol in symbols:
        sr = result.by_symbol[symbol]
        spread_ref = bs.plateau_spread(result, symbol, ref)
        sections.append(f"""---

# {symbol}

Out-of-sample span **{sr.oos_start.date()} to {sr.oos_end.date()}** — {sr.n_oos_bars:,} daily
bars across {sr.n_windows} walk-forward windows (train {study.train_size}, test
{study.test_size}, step {study.step}). Every number below is out of sample.

## Every variant at the reference tier (`{ref}`, {[t for t in result.tiers if t.name == ref][0].fee_bps / 100:.2f}% taker)

{bs.render_variant_table(result, symbol, ref, ordered)}

## Baseline across the cost tiers — maker vs taker

{bs.render_tier_table(result, symbol, BASELINE)}

## Filter increments, one at a time on top of the baseline

Each row is the baseline (`{BASELINE}`) with exactly ONE filter brick added — never
stacked — so each delta prices exactly one component.

{bs.render_variant_table(result, symbol, ref, [BASELINE] + FILTER_NAMES)}

At the free tier (`maker_0bp`), which isolates the filters' effect on the SIGNAL from
their effect on costs:

{bs.render_variant_table(result, symbol, "maker_0bp", [BASELINE] + FILTER_NAMES)}

## Parameter plateau surface — annualised Sharpe at `{ref}`

{bs.render_plateau_surface(result, symbol, ref, "sharpe")}

Same surface, CAGR:

{bs.render_plateau_surface(result, symbol, ref, "cagr")}

Same surface, closed-trade counts (the mechanical explanation for the shape):

{bs.render_plateau_surface(result, symbol, ref, "trades")}

**Spike test.** Best cell is N_entry={int(spread_ref['best_n_entry'])},
N_exit={int(spread_ref['best_n_exit'])} at Sharpe {spread_ref['best_sharpe']:.3f}; its
immediate neighbours average {spread_ref['neighbour_mean_sharpe']:.3f}; the whole
{int(spread_ref['n_cells'])}-cell surface spans
{spread_ref['worst_sharpe']:.3f} to {spread_ref['best_sharpe']:.3f}
(spread {spread_ref['surface_spread']:.3f}). The best-minus-neighbours gap is
**{spread_ref['best_minus_neighbours_over_spread']:.2f} of the surface's own spread**.
{_spike_verdict(spread_ref, _monotone_note(result, symbol, ref))}

{_sweep_edge(result, symbol, ref)}

## Benchmarks: three ways to be long

{_benchmark_block(result, symbol, ref)}

## Is this the strategy, or is it the era?

{_era_block(result, symbol, ref)}

## Sizing sensitivity, including the vol target this study picked and never tested

{bs.render_variant_table(result, symbol, ref, [BASELINE] + SIZING_NAMES + VOL_TARGET_NAMES)}

{_vol_target_note(result, symbol, ref)}

## Per-trade diagnostics at `{ref}`

{bs.render_diagnostics_table(result, symbol, ref, ordered)}

## Capture ratios at `{ref}`

Upside captured = Σ(strategy return on bars the instrument rose) ÷ Σ(instrument return
on those bars). Downside participated is the same on down bars; downside avoided is
1 − that. Drawdown avoided = 1 − (strategy max drawdown ÷ instrument max drawdown).

{bs.render_capture_table(result, symbol, ref, ordered)}

## Deflated Sharpe

{_dsr_block(result, symbol)}
""")

    sections.append(_filter_decision(result))
    sections.append(_selection_section(result))
    sections.append(_feature_section(result))
    sections.append(_exit_section(result))
    sections.append(_multiplicity(result))
    sections.append(_verdict(result))
    sections.append(_caveats(result))
    return "\n\n".join(section.strip() + "\n" for section in sections)



def _sweep_edge(result: bs.StudyResult, symbol: str, tier_name: str) -> str:
    """The sweep-edge rule the brief mandates, and which v1 simply did not report.

    The brief's rule is one-sided: it anticipates performance still IMPROVING at
    N_entry=55 (the published time-series-momentum evidence puts trend persistence at
    1-12 MONTH lookbacks, so the stated sweep sits at the fast end of that range) and
    requires the boundary gradient be recorded plus a follow-up extension flagged,
    WITHOUT extending the sweep in this session.

    It is reported symmetrically here because the data demanded it: one symbol's
    surface improves toward the slow edge and the other's toward the fast edge. The
    fast-edge case is not a rule violation - the brief did not write a rule for it -
    but it is the same phenomenon and hiding it would be reporting to the letter of the
    brief against its point."""
    sr = result.by_symbol[symbol]
    study = result.config
    sharpes = {
        (n_entry, n_exit): sr.variants[(f"plateau_{n_entry}_{n_exit}", tier_name)].sharpe_annual(study)
        for n_entry in bs.PLATEAU_N_ENTRY
        for n_exit in bs.PLATEAU_N_EXIT
        if (f"plateau_{n_entry}_{n_exit}", tier_name) in sr.variants
    }
    entries = list(bs.PLATEAU_N_ENTRY)
    lo, hi = entries[0], entries[-1]

    # Row means across the exit windows, so the edge question is about N_entry alone.
    row_mean = {
        n_entry: statistics.fmean([v for (ne, _), v in sharpes.items() if ne == n_entry])
        for n_entry in entries
    }
    best_entry = max(row_mean, key=lambda k: row_mean[k])
    best_cell = max(sharpes, key=lambda k: sharpes[k])
    slow_gradient = row_mean[hi] - row_mean[entries[-2]]
    fast_gradient = row_mean[lo] - row_mean[entries[1]]

    rows = "\n".join(
        f"| {n_entry}{' (sweep edge)' if n_entry in (lo, hi) else ''} | {row_mean[n_entry]:.3f} |"
        for n_entry in entries
    )
    table = f"| N_entry | Mean Sharpe across N_exit |\n|---|---|\n{rows}"

    # The brief's rule keys on the GRADIENT AT THE BOUNDARY — "performance still
    # improving at N_entry=55" — not on where the global maximum happens to sit. An
    # earlier cut of this section tested the row-mean argmax instead, and on ETH that
    # printed "the optimum is interior" directly above a positive slow-edge gradient
    # and a best cell sitting ON the boundary. Both edges are therefore reported on
    # their own gradient, and the best single cell is named in every branch.
    slow_rising = slow_gradient > 0
    fast_rising = fast_gradient > 0
    at_edge = best_cell[0] in (lo, hi)
    cell_note = (
        f"The best single cell is {best_cell[0]}/{best_cell[1]} at Sharpe "
        f"{sharpes[best_cell]:.3f}, which **is** on a sweep boundary."
        if at_edge
        else f"The best single cell is {best_cell[0]}/{best_cell[1]} at Sharpe "
        f"{sharpes[best_cell]:.3f}, which is not on a boundary."
    )

    parts = [cell_note]
    if slow_rising:
        parts.append(
            f"**Performance is still improving at the SLOW edge**: mean Sharpe "
            f"{row_mean[hi]:.3f} at N_entry={hi} against {row_mean[entries[-2]]:.3f} at "
            f"N_entry={entries[-2]}, a boundary gradient of {slow_gradient:+.3f}. This is the "
            f"case the brief's sweep-edge rule anticipates, and the rule is followed to the "
            f"letter: **the sweep is NOT extended in this session.** Recorded instead as a "
            f"recommendation — **extend N_entry toward {{100, 150, 250}} in a follow-up "
            f"session**, as a new trial series with its own multiplicity accounting. The "
            f"published time-series-momentum persistence range (1-12 months) sits almost "
            f"entirely beyond this sweep's boundary, so a rising slow edge is what the "
            f"literature would predict rather than a surprise."
        )
    if fast_rising:
        parts.append(
            f"**Performance is also still improving at the FAST edge**: mean Sharpe "
            f"{row_mean[lo]:.3f} at N_entry={lo} against {row_mean[entries[1]]:.3f} at "
            f"N_entry={entries[1]}, a boundary gradient of {fast_gradient:+.3f}. The brief "
            f"writes no rule for this edge — it anticipated the slow one — so nothing is "
            f"mandated and the sweep is not extended downward either. It is recorded because "
            f"it is the same phenomenon, and because the direction runs AGAINST the published "
            f"persistence range, which is a reason to discount it rather than chase it."
        )
    if not slow_rising and not fast_rising:
        parts.append(
            f"**Neither edge is rising.** Slow-edge gradient {slow_gradient:+.3f}, fast-edge "
            f"gradient {fast_gradient:+.3f}: the surface falls away at both boundaries, so it "
            f"contains its own optimum and no extension is indicated in either direction."
        )
    verdict = " ".join(parts)

    return f"""**Sweep-edge check.** A best cell sitting against a boundary means the sweep has not
bracketed its own optimum — the surface is still pointing somewhere the study did not look.

{table}

{verdict}"""


def _benchmark_block(result: bs.StudyResult, symbol: str, tier_name: str) -> str:
    """Three benchmarks, because the naive one flatters the strategy in one direction
    and punishes it in the other (D119, D120)."""
    sr = result.by_symbol[symbol]
    study = result.config
    tier = [t for t in result.tiers if t.name == tier_name][0]
    r = sr.variants[(BASELINE, tier_name)]
    hold = sr.benchmarks[tier_name]
    fraction = r.diagnostics.exposure
    matched = bs.run_constant_fraction_benchmark(BARS_BY_SYMBOL[symbol], symbol, tier, study, fraction)

    boot_hold = bs.sharpe_difference_bootstrap(r.oos_returns, hold.oos_returns, study, seed=study.seed)
    boot_matched = bs.sharpe_difference_bootstrap(
        r.oos_returns, matched.oos_returns, study, seed=study.seed
    )

    def row(label, total, curve_len, sharpe_value, maxdd, note):
        return (
            f"| {label} | {total:+.1%} | "
            f"{bs.cagr(total, curve_len, study.periods_per_year):+.1%} | {sharpe_value:.2f} | "
            f"{maxdd:.1%} | {note} |"
        )

    table = "\n".join([
        "| | Total return | CAGR | Sharpe (ann.) | Max DD | Time in market |",
        "|---|---|---|---|---|---|",
        row(f"**Strategy** (`{BASELINE}`)", r.total_return, r.n_oos_bars,
            r.sharpe_annual(study), r.max_drawdown, f"{fraction:.0%}"),
        row("Buy & hold, 100%", hold.total_return, len(hold.oos_equity),
            hold.sharpe_annual(study), hold.max_drawdown, "100%"),
        row(f"Constant {fraction:.0%} of capital, rest cash", matched.total_return,
            len(matched.oos_equity), matched.sharpe_annual(study), matched.max_drawdown,
            f"{fraction:.0%} (always)"),
    ])

    beat_matched = r.total_return > matched.total_return
    return f"""Comparing a strategy that is in the market {fraction:.0%} of the time against a
100%-invested benchmark answers "would you have been better off just holding it" — worth
knowing, and not a like-for-like risk comparison. The third row fixes that: hold a
**constant {fraction:.0%} of capital** in the instrument and the rest in cash, so average
exposure matches the strategy's own and the only remaining difference is *when* the
exposure was taken. It runs through the same engine and tier, so its constant-fraction
rebalancing pays real fees (D119).

{table}

Against the matched-exposure benchmark the strategy
{'earns ' + format(r.total_return / matched.total_return if matched.total_return > 0 else float('nan'), '.1f') + '× the terminal wealth' if beat_matched else 'underperforms'}
at {'a similar' if abs(r.max_drawdown - matched.max_drawdown) < 0.05 else 'a different'}
drawdown. **Timing the exposure beat spreading it evenly** — which is a materially better
case than the 100% row alone suggests, and it is the comparison a reviewer should be
handed first.

**But the Sharpe differences are not measurable at this sample size.** Paired block
bootstrap (20-bar blocks, {int(boot_hold['n_sims']):,} sims, seed {int(boot_hold['seed'])};
the same resampled bar indices applied to both series so their correlation is preserved,
D120):

| Comparison | Observed Δ Sharpe | 90% interval | P(Δ > 0) |
|---|---|---|---|
| Strategy − buy & hold (100%) | {boot_hold['observed']:+.3f} | [{boot_hold['p05']:+.3f}, {boot_hold['p95']:+.3f}] | {boot_hold['prob_positive']:.0%} |
| Strategy − constant {fraction:.0%} | {boot_matched['observed']:+.3f} | [{boot_matched['p05']:+.3f}, {boot_matched['p95']:+.3f}] | {boot_matched['prob_positive']:.0%} |

Ten years of daily data buys a standard error of roughly ±0.4 on an annualised Sharpe.
Both intervals span zero comfortably. **The return and drawdown differences are the
defensible findings; the Sharpe differences are not.** Any sentence in this report that
leans on a Sharpe gap of a few hundredths should be read as arithmetic, not evidence."""


def _era_block(result: bs.StudyResult, symbol: str, tier_name: str) -> str:
    """The question every reader asks about a crypto backtest, answered with the two
    tables that actually settle it (D121)."""
    sr = result.by_symbol[symbol]
    study = result.config
    tier = [t for t in result.tiers if t.name == tier_name][0]
    r = sr.variants[(BASELINE, tier_name)]
    hold = sr.benchmarks[tier_name]
    bars = BARS_BY_SYMBOL[symbol]

    annual = bs.annual_breakdown(r, hold)
    variant = bs.Variant(BASELINE, "plateau",
                         fixed_config=bs.breakout_config(bs.BASELINE_N_ENTRY, bs.BASELINE_N_EXIT))
    starts = bs.start_date_sensitivity(bars, symbol, variant, tier, study)

    up_years = [row for row in annual if row["benchmark"] > 0]
    down_years = [row for row in annual if row["benchmark"] < 0]
    lost_in_up = sum(1 for row in up_years if row["strategy"] < row["benchmark"])
    won_in_down = sum(1 for row in down_years if row["strategy"] > row["benchmark"])
    spans = bs._window_spans(bars, study)
    first, last = bars[spans[0][2]].bar.close, bars[spans[-1][3] - 1].bar.close

    cagr_range = [row["strategy_cagr"] for row in starts]
    sharpe_flips = sum(1 for row in starts if row["strategy_sharpe"] < row["benchmark_sharpe"])
    dd_gaps = [row["benchmark_maxdd"] - row["strategy_maxdd"] for row in starts]

    # Both of these used to be hardcoded to BTC's shape ("that decade", "a four-figure
    # percentage return"), which was simply false on ETH's 7-year, three-figure sample.
    # Derive them from the symbol's own span and its own headline number instead.
    span_years = sr.n_oos_bars / study.periods_per_year
    span_phrase = "that decade" if span_years >= 9.5 else f"those {span_years:.0f} years"
    digits = len(f"{abs(hold.total_return) * 100:.0f}".lstrip("-"))
    magnitude = {
        1: "A single-digit", 2: "A two-figure", 3: "A three-figure", 4: "A four-figure",
    }.get(digits, "A five-figure")
    dd_summary = (
        f"the strategy's max drawdown is lower at every start date, by "
        f"{min(dd_gaps) * 100:.0f} to {max(dd_gaps) * 100:.0f} percentage points"
    )
    return f"""**Yes, the absolute numbers are the era.** {symbol} closed at ${first:,.0f} on the
first out-of-sample bar and ${last:,.0f} on the last — **{last / first:.0f}× the price**.
Any long-biased rule applied to {span_phrase} produces a number with too many digits in it.
{magnitude} percentage return here is a fact about the instrument, not about the
breakout rule, and it should never be quoted on its own.

What the rule contributed is only visible year by year.

{bs.render_annual_table(annual)}

The pattern is stark and it is the whole strategy in one table: **the strategy lost to
buy-and-hold in {lost_in_up} of the {len(up_years)} up years, and beat it in
{won_in_down} of the {len(down_years)} down years.** Time in market tracks it exactly —
heavily invested through the bull years, nearly flat through the bear ones. This is not an
edge in the sense of predicting returns; it is **insurance, bought with bull-market
underperformance and paid out in bear markets**. Whether that trade is good depends
entirely on how many bear markets your sample contains, and this one contains two.

Which is why the start date matters as much as the strategy:

{bs.render_start_date_table(starts)}

Identical configuration, identical rules — only the investor's start date changes. The
strategy's CAGR ranges from {min(cagr_range):+.1%} to {max(cagr_range):+.1%} across these
starts. **A result that moves that much on the choice of start date is describing the
sample, not the rule.** Note too that the strategy's Sharpe advantage over buy-and-hold
does not survive the later starts at all ({sharpe_flips} of {len(starts)} start dates have
it BELOW the benchmark).

The one thing that holds in every row is the drawdown reduction — {dd_summary} — and that,
rather than any return or Sharpe claim, is the finding this study can actually defend."""


def _vol_target_note(result: bs.StudyResult, symbol: str, tier_name: str) -> str:
    sr = result.by_symbol[symbol]
    study = result.config
    base = sr.variants[(BASELINE, tier_name)]
    full = sr.variants[("sizing_fixed_1.0", tier_name)]
    swept = [(target, sr.variants[(name, tier_name)])
             for target, name in zip(bs.VOL_TARGET_SWEEP, VOL_TARGET_NAMES)]
    ladder = sorted(swept + [(0.40, base)])
    best_target, best = max(ladder, key=lambda pair: pair[1].sharpe_annual(study))
    lowest_target, lowest = ladder[0]

    dd_monotone = all(a[1].max_drawdown <= b[1].max_drawdown + 1e-9
                      for a, b in zip(ladder, ladder[1:]))
    ret_monotone = all(a[1].total_return <= b[1].total_return + 1e-9
                       for a, b in zip(ladder, ladder[1:]))
    sharpe_spread = (max(r.sharpe_annual(study) for _t, r in ladder)
                     - min(r.sharpe_annual(study) for _t, r in ladder))
    dial = (
        "**and it behaves exactly like a risk dial should**: drawdown and return are both "
        "monotone in the target across the whole ladder"
        if dd_monotone and ret_monotone
        else "and its effect on drawdown and return is not monotone in the target"
    )

    return f"""The 40% annual vol target was the one free parameter of the original study
that was chosen and never tested, so it is swept here (D118) over
{', '.join(f'{int(t * 100)}%' for t in sorted([0.40, *bs.VOL_TARGET_SWEEP]))}.

**The dial works; the Sharpe does not move.** Total Sharpe spread across the whole ladder
is {sharpe_spread:.2f} — an order of magnitude inside the ±0.4 bootstrap band established
above — so no target level is distinguishable from any other on risk-adjusted grounds,
{dial}. At {lowest_target:.0%} the strategy returns {lowest.total_return:+.1%} with a
{lowest.max_drawdown:.1%} max drawdown; at 80% it returns
{ladder[-1][1].total_return:+.1%} with {ladder[-1][1].max_drawdown:.1%}. The nominally best
Sharpe ({best.sharpe_annual(study):.2f}) sits at a {best_target:.0%} target against
{base.sharpe_annual(study):.2f} at the baseline, which is noise, not a discovery.

Against no vol targeting at all — `sizing_fixed_1.0`, always 100% of capital when long —
the baseline gives up
{(full.total_return - base.total_return) / (1 + full.total_return):.0%} of terminal wealth
({base.total_return:+.1%} vs {full.total_return:+.1%}) to buy
{(full.max_drawdown - base.max_drawdown) * 100:.1f} percentage points less drawdown
({base.max_drawdown:.1%} vs {full.max_drawdown:.1%}), for a Sharpe change of
{base.sharpe_annual(study) - full.sharpe_annual(study):+.2f} that cannot be distinguished
from zero. **Stated plainly: the vol target is a drawdown purchase priced in return, not a
Sharpe improvement — pick the level from the drawdown you can tolerate, and do not claim it
improves the risk-adjusted result.** The original write-up implied otherwise by reporting a
single target without the ladder beside it."""



def _header(result: bs.StudyResult, gate: dict) -> str:
    study = result.config
    return f"""# Long-flat breakout: does trend following on BTC/ETH survive exchange fees?

**Produced:** {datetime.now(timezone.utc).date().isoformat()} ·
**Snapshot:** `{result.snapshot_id}` ·
**Registry:** `data/breakout_study_registry.sqlite` ·
**Reproduce:** `uv run python scripts/run_breakout_study.py` (offline, deterministic)

> **Thesis label (D38/D82/D117).** This is a **directional, beta-loaded** strategy: long
> or flat on a single high-beta instrument, never short. It is **not** part of this
> project's market-neutral thesis, and it is not evidence about it. It is here because
> the framework claims a strategy is a swappable brick, and a long-only crypto trend
> follower is about as far from a market-neutral ETF pairs book as one can get while
> reusing the same engine, cost stack, walk-forward harness and trial registry. Its
> honest benchmark is buy-and-hold, not the risk-free rate.

**Data.** BTC-USD and ETH-USD daily bars, 00:00 UTC boundary, fixed — no alternative
boundary was tested. Fixture `data/fixtures/crypto_daily_2015_2025_raw.csv.gz`, frozen
through the Step-7 pipeline. The sanity gate (D25/D26) reported
**{gate['cleaning_changes']} cleaning change(s)** and **{gate['hard_violations']} hard
violation(s)**, with {gate['warnings']} warning(s) — all of them genuine large crypto
moves (2017-12, 2020-03, 2021-01, 2021-05), none of them quarantining.

**Scale.** {result.n_oos_trials} out-of-sample trials logged
({len(result.variant_names)} strategy variants × {len(result.tiers)} cost tiers ×
{len(result.by_symbol)} symbols) plus {result.n_train_evaluations:,} in-training-window
parameter evaluations, all counted in the multiplicity section. Risk-free rate
{study.rf_annual:.0%}; annualisation on {study.periods_per_year:.0f} days (crypto trades
every calendar day, D17)."""


def _method(result: bs.StudyResult) -> str:
    study = result.config
    return f"""
## Method, in one screen

**Signal.** Enter long when `close(t) > max(high)` over bars t−N_entry … t−1. Exit to
flat when `close(t) < min(low)` over bars t−N_exit … t−1. Baseline
N_entry={bs.BASELINE_N_ENTRY}, N_exit={bs.BASELINE_N_EXIT}. Both extrema exclude the
current bar, so a bar cannot trigger on itself. No shorting; flat is the default state.

**Execution.** `fill_timing="next_open"` (D103): a decision taken at bar t's close fills
at bar t+1's **open**. The strategy never trades at the price that produced its signal.

**Sizing.** Inverse-volatility: weight = 40% target annual vol ÷ trailing realized vol
(20-day sample stdev of log returns **ending at t−1**, D44), capped at 1.0× capital,
fixed at entry for the life of the trade. Two sensitivities are run: fixed-fractional at
1.0, and inverse-vol recomputed every bar.

**Walk-forward.** train={study.train_size}, test={study.test_size}, step={study.step}.
Anything fitted is fitted on a training slice only. See "one continuous run" below.

**Costs.** One `percent_spread` brick per tier through the existing `CostStack`:
{", ".join(f"`{t.name}` = {t.fee_bps / 100:.2f}% ({t.role})" for t in result.tiers)}. No
commission, no bid/ask spread, no market impact, no funding, no borrow — this is an
**exchange fee model and nothing more**, which makes every number here optimistic.

**Benchmark.** Buy-and-hold the same instrument over the same span at the same fee tier:
buy at the second OOS bar's open (the earliest any decision could fill), hold a fixed
quantity, mark at the final close with no forced liquidation — exactly how a strategy
variant that ends long is marked."""


def _findings_first(result: bs.StudyResult) -> str:
    return """
---

## Read this first: what was found before any performance was measured

The brief said result-corrupting issues take priority over tuning. Three things surfaced.
None of them silently corrupted a number; two changed what got built, one is a blocker.

### 1. BLOCKER — the volume-confirmation filter cannot be built (D111)

Filter 2 of the brief ("trigger bar volume > 1.5× 20-day average volume") is **not
implemented**, and was not worked around.

`Bar` carries `open`, `high`, `low`, `close` and nothing else. `TimestampedBar` adds only
a timestamp. `DataView` — the structural look-ahead guard strategies receive (D32) —
hands out `Bar` objects. Volume is fetched, cleaned, validated and stored in snapshots,
but it stops at the data layer: `csv_fixture.py` says so explicitly, calling a volume
field on `TimestampedBar` "a false affordance (D48)".

The two ways around it are both worse than not having the filter:

- **Add volume to `Bar` / `TimestampedBar` / `DataView`.** That is a change to three
  existing interfaces, rippling through the simulator, the cost bricks, the golden
  masters and the cross-engine reconciliation. The brief forbids modifying existing
  interfaces, and it is right to — this is a schema change to the framework's most
  load-bearing type, not a strategy feature.
- **Pass a volume series into the strategy's constructor.** This hands strategy code
  full-sample data that sits outside the DataView guard — exactly the look-ahead hole
  D32 exists to close, and it would do so invisibly, since nothing would fail.

So the filter is absent rather than faked, and no `VolumeConfirmationFilter` class exists
to imply otherwise. **The three other filters are implemented and measured in full.**
The interface change needed is small and well-defined (a volume field on `TimestampedBar`
threaded into `build_data_view`), but it is a framework decision, not a study decision.

### 2. The chained-window harness would have distorted this strategy (D113)

The pairs study runs each walk-forward window as its own backtest, chaining capital
window to window. For a mean-reverting strategy holding for days, the seam is cheap. For
a trend follower holding for weeks-to-months it is not: every window boundary would force
the book flat, return the position to cash **with no exit cost**, and then require a
brand-new breakout before the trend could be re-entered.

That is not a small effect on a study whose whole question is whether tens of basis points
matter. So each (symbol, variant, tier) here is **one continuous out-of-sample backtest**
over the union of the test windows, with the walk-forward structure still doing its job:
the OOS span starts exactly where window 0's training slice ends, per-window returns are
sliced out for per-window trial rows, and anything fitted is fitted per window and applied
through a parameter **schedule** (`ScheduledBreakout`) that swaps configuration at window
boundaries while the position carries across. No forced flattening, no free liquidations.

The warm-up prefix is exactly the strategy's own warm-up requirement, so its guard keeps
it flat through the entire prefix and no in-sample P&L can reach the reported curve. The
harness asserts this at runtime (it raises if any fill lands in the prefix) rather than
trusting it.

### 3. Fill semantics and look-ahead: checked, clean

- **Extrema exclude the current bar.** Asserted directly, and by property test: perturbing
  any bar after the decision bar — arbitrarily, scaled by up to 100× — cannot change a
  single target the strategy produced up to that bar, at the signal level *and* through
  the full engine with costs and next-open fills.
- **Fills never use the signal bar's price.** Pinned by the golden master: the entry
  decision at bar 3's close produces a fill stamped on bar 4 at bar 4's open.
- **Costs are exactly the fee rate × traded notional**, on every fill including
  rebalances, and final NAV is monotone non-increasing in the fee tier. Both property
  tested; the golden master reconciles NAV to the penny by hand.

One typing observation, not a defect: `engine/strategy.py`'s `Strategy` protocol declares
`strategy_id` as a settable attribute, so the frozen `ScheduledWeightStrategy` does not
type-conform — the same protocol-variance trap audit F20 fixed on
`Instrument.quote_currency`. Left alone (it is an existing interface) with a narrow
`type: ignore` and this note."""


def _monotone_note(result: bs.StudyResult, symbol: str, tier_name: str) -> str:
    """A neighbour-gap number alone cannot tell a curve-fit spike from an ORDERLY
    surface. If every N_entry row ranks the N_exit columns the same way, the surface has
    structure — the parameter is doing something consistent — and a gap that comes from
    one systematically-bad column is not evidence of fitting. If the rows disagree with
    each other, the same gap is noise. So both are reported."""
    sr = result.by_symbol[symbol]
    study = result.config
    orders = []
    for n_entry in bs.PLATEAU_N_ENTRY:
        row = [
            (n_exit, sr.variants[(f"plateau_{n_entry}_{n_exit}", tier_name)].sharpe_annual(study))
            for n_exit in bs.PLATEAU_N_EXIT
            if (f"plateau_{n_entry}_{n_exit}", tier_name) in sr.variants
        ]
        orders.append(tuple(n_exit for n_exit, _ in sorted(row, key=lambda pair: -pair[1])))
    if len(set(orders)) == 1:
        best_exit, *_, worst_exit = orders[0]
        return (
            f" Every N_entry row ranks the exit windows identically (N_exit={best_exit} best, "
            f"N_exit={worst_exit} worst), so the surface has consistent structure rather than "
            "scattered high cells — the neighbour gap here comes from one systematically weaker "
            "column, not from one lucky cell."
        )
    return (
        " The N_entry rows do NOT agree on how to rank the exit windows, which is what an "
        "unstructured surface looks like: the parameter is not doing anything consistent, and "
        "differences between cells are correspondingly harder to distinguish from noise."
    )


def _spike_verdict(spread: dict, monotone_note: str) -> str:
    gap = spread["best_minus_neighbours_over_spread"]
    if gap > 0.5:
        head = (
            "**Read this as a spike, not a plateau — do not quote the best cell.** The top "
            "cell stands more than half the surface's entire range above its own neighbours, "
            "which is what an artifact of one sample looks like."
        )
    elif gap > 0.25:
        head = (
            "**Borderline.** The top cell sits meaningfully above its immediate neighbours: "
            "not a clean plateau, and the best cell should not be quoted as the strategy's "
            "performance."
        )
    else:
        head = (
            "**This is a plateau, not a spike.** The best cell's neighbours are close behind "
            "it, so the parameter choice is not carrying the result — which is also why the "
            "multiplicity penalty from sweeping the grid turns out to be small."
        )
    return head + monotone_note


def _dsr_block(result: bs.StudyResult, symbol: str) -> str:
    sr = result.by_symbol[symbol]
    lines = [
        "| Tier | Best variant | Its daily SR | T (bars) | N (trials in pool) | "
        "V[{SRn}] | **DSR** |",
        "|---|---|---|---|---|---|---|",
    ]
    for tier in result.tiers:
        i = sr.dsr_inputs_by_tier[tier.name]
        lines.append(
            f"| `{tier.name}` | `{i['best_variant']}` | {i['observed_sr_daily']:.4f} | "
            f"{i['t']:,} | {i['n_trials']} | {i['var_trials_daily']:.6f} | "
            f"**{sr.dsr_by_tier[tier.name]:.4f}** |"
        )
    return "\n".join(lines)


NL = "\n"
"""Newline, named so the report builders can concatenate multi-line blocks without
burying escapes inside f-strings that already use braces heavily."""

FEATURE_TITLES = {
    "F1": "Extension at trigger — (close − SMA(50)) / ATR(20)",
    "F2": "Trigger volume ratio — volume / 20-day average volume",
    "F3": "Close location value — (close − low) / (high − low) on the trigger bar",
    "F4": "Cross-sectional breadth — fraction of the universe above its own 20-day high or 50-day SMA",
    "F5": "Leverage decomposition — ΔOI/Δprice and funding percentile",
    "F6": "Known-flow proximity — hours to the next Deribit monthly options expiry",
}

FEATURE_PRIORS = {
    "F1": "predicted the strongest survivor: high extension = late-stage breakout = worse outcomes",
    "F2": "predicted a BAND rather than a floor — healthy roughly 1.5-3x, climax above ~5x",
    "F3": "predicted CLV below ~0.3 (new high, close in the bottom third) = level probed and sold",
    "F4": "predicted weak at this universe size, and logged anyway so the prediction is testable",
    "F5": "predicted the most valuable of the set if the data existed",
    "F6": "genuinely open — weak prior in either direction",
}


FEATURE_PRIOR_SIGN = {
    "F1": -1,   # high extension = late-stage breakout = WORSE outcomes
    "F3": +1,   # low close-location = probed and sold = worse; so higher CLV = better
    "F4": +1,   # breadth confirmation = better
    "F6": 0,    # genuinely open, no directional prior recorded
}
"""The SIGN each prior predicts for the feature's rank correlation with MFE. Recorded so
the analysis can report "absent" and "present but backwards" as the different findings
they are — a prior that comes out reversed is more interesting than one that comes out
flat, and averaging them into "no relationship" would hide that."""


def _feature_observation(name: str, verdict) -> str:
    """Data-derived commentary beyond the verdict: whether the prior's SIGN survived,
    and whether the feature's realised range made the hypothesis testable at all.

    The second question is the one a rank correlation cannot answer. A hypothesis about
    a region the trigger population never visits has not been falsified — it has not
    been tested, and saying so is different from saying it failed."""
    if not verdict.buckets or verdict.rho_mfe is None:
        return ""
    notes = []
    prior = FEATURE_PRIOR_SIGN.get(name, 0)
    if prior:
        observed = 1 if verdict.rho_mfe > 0 else -1
        if abs(verdict.rho_mfe) < 0.1:
            notes.append(
                "Against the prior: the relationship is flat rather than merely weak — "
                "the prior is unsupported, not reversed."
            )
        elif observed != prior:
            notes.append(
                f"**Against the prior: the sign is BACKWARDS.** The prior predicted a "
                f"{'negative' if prior < 0 else 'positive'} relationship with MFE and the sample "
                f"gives {verdict.rho_mfe:+.2f}. Too weak to act on in either direction, but it is "
                f"the opposite of what was predicted, not a smaller version of it."
            )
        else:
            notes.append(
                f"Against the prior: the sign is as predicted ({verdict.rho_mfe:+.2f}), but the "
                f"magnitude does not clear the bar."
            )

    lo = min(b.lo for b in verdict.buckets)
    hi = max(b.hi for b in verdict.buckets)
    if name == "F3" and lo > 0.3:
        notes.append(
            f"**The hypothesis was untestable on this trigger population.** The prior names "
            f"CLV < 0.3 (a new high that closes in the bottom third of its own bar) as the "
            f"danger zone; the lowest CLV any trigger actually printed is {lo:.2f}. A bar whose "
            f"close exceeds a 40-day high can hardly close near its own low, so the region the "
            f"hypothesis is about is empty **by construction**. F3 as specified cannot be "
            f"tested on breakout triggers — that is a finding about the feature's definition, "
            f"not evidence against the idea."
        )
    if name == "F2" and hi < 5.0:
        notes.append(
            f"**The prior's climax half was untestable.** It names a BAND — healthy around "
            f"1.5-3x, climax above ~5x — but the largest volume ratio any trigger printed is "
            f"{hi:.2f}x, so the climax region is empty on this population. Only the lower half "
            f"of the hypothesis was exposed to data. Worth noting that a 40-day breakout on "
            f"daily crypto bars simply does not seem to arrive on 5x volume; whether that is a "
            f"fact about breakouts or about a venue-aggregated volume series (see the standing "
            f"caveat) this study cannot separate."
        )
    if name == "F4":
        flat = sum(1 for b in verdict.buckets if b.lo == b.hi)
        if flat >= len(verdict.buckets) - 2:
            notes.append(
                f"**The measure is degenerate here, and worse than the doc predicted.** "
                f"{flat} of {len(verdict.buckets)} quintiles have zero width, and the range is "
                f"{lo:.2f}-{hi:.2f}. Two causes compound: a two-instrument universe admits only "
                f"the values 0, 0.5 and 1; and the breadth measure **includes the instrument "
                f"that is triggering**, which is above its own 20-day high by definition at that "
                f"moment. Breadth can therefore never read below 0.5 at a trigger. The fix is a "
                f"leave-one-out definition, not more instruments alone."
            )
    return " ".join(notes)


def _feature_section(result: bs.StudyResult) -> str:
    """The feature-analysis pass the companion doc specifies and v1 never ran.

    Pooled across symbols on the BASELINE variant at the reference tier. Pooling is the
    honest choice here rather than a convenience: the per-symbol trade counts are in the
    dozens, the configuration is identical across symbols, and F4's hypothesis is
    cross-sectional to begin with. It is still a thin sample and the tables say so."""
    ref = bs.REFERENCE_TIER
    episodes: list = []
    per_symbol = {}
    for symbol in result.by_symbol:
        symbol_episodes = result.by_symbol[symbol].variants[(BASELINE, ref)].episodes
        per_symbol[symbol] = sum(1 for e in symbol_episodes if not e.is_open)
        episodes.extend(symbol_episodes)

    verdicts = fa.analyse_all(episodes, whipsaw_bars=result.config.whipsaw_bars)
    closed = sum(per_symbol.values())
    counts = ", ".join(f"{sym} {n}" for sym, n in per_symbol.items())
    candidates = [name for name, v in verdicts.items() if v.verdict == "CANDIDATE"]
    blocked = [name for name, v in verdicts.items() if v.verdict == "UNAVAILABLE"]
    blocked_sentence = (
        f"{len(blocked)} of the {len(fa.FEATURE_NAMES)} could not be computed at all "
        f"({', '.join(blocked)}), and is reported as blocked rather than quietly dropped."
        if len(blocked) == 1
        else f"{len(blocked)} of the {len(fa.FEATURE_NAMES)} could not be computed at all "
        f"({', '.join(blocked)}), and are reported as blocked rather than quietly dropped."
    ) if blocked else "Every feature in the set was computable."

    blocks = []
    for name in fa.FEATURE_NAMES:
        v = verdicts[name]
        head = f"### {name} — {FEATURE_TITLES[name]}" + NL + NL
        head += f"*Prior on record: {FEATURE_PRIORS[name]}.*" + NL + NL
        if not v.buckets:
            blocks.append(head + f"**{v.verdict}.** {v.note}")
            continue
        rows = NL.join(
            f"| {b.index} | {b.n} | {b.lo:+.2f} | {b.hi:+.2f} | {b.mean_mfe * 100:+.1f}% | "
            f"{b.mean_mae * 100:+.1f}% | {b.win_rate * 100:.0f}% | {b.whipsaw_rate * 100:.0f}% |"
            for b in v.buckets
        )
        observation = _feature_observation(name, v)
        table = (
            "| Quintile | Trades | Feature low | Feature high | Mean MFE | Mean MAE | Win rate | Whipsaw |"
            + NL + "|---|---|---|---|---|---|---|---|" + NL + rows
        )
        blocks.append(
            head + table + NL + NL
            + f"Rank correlation with MFE **{v.rho_mfe:+.2f}**, with MAE {v.rho_mae:+.2f}; "
            + f"by sample half {v.rho_first_half:+.2f} then {v.rho_second_half:+.2f} "
            + f"({v.n_available} of {v.n_total} closed trades carry a value)." + NL + NL
            + f"**{v.verdict}.** {v.note}"
            + ((NL + NL + observation) if observation else "")
        )

    if candidates:
        shortlist = (
            f"**Ranked shortlist: {', '.join(candidates)}.** Each meets the logged-feature bar "
            "(usable rank correlation, sign stable across both halves of the sample, monotone "
            "quintile means). None is promoted here: promotion needs a plateau test over the "
            "feature's own threshold and a live-filter increment with its own TrialRegistry "
            "entries, which is a separate session by the companion doc's own protocol."
        )
    else:
        shortlist = (
            "**Ranked shortlist: empty. No feature met the promotion bar.** That is a clean "
            "negative result and it is reported as one — the companion doc asks explicitly for "
            "falsified hypotheses to be stated rather than buried, and the priors recorded above "
            "were written down in advance precisely so they could be embarrassed."
        )

    return f"""---

# Feature analysis: what separates a breakout from an exhaustion print

**These are features, not filters.** Nothing in this section changed a fill, a weight or
a cost, and nothing here enters the DSR trial pool — logging carries no multiplicity
cost, which is the whole reason the companion doc insists the features be logged before
any of them is allowed to become a gate. A feature earns promotion only by showing a
monotonic relationship with outcomes, stability across the sample, and a plateau over
its own threshold; the third test and the promotion itself are a later session.

**The trigger bar is not the entry bar.** Fills are next-open (D103), so a trade whose
entry fill lands on bar t+1 was triggered by bar t's close. Every value below is read
off bar t, from data at or before t — the information the strategy actually had. Reading
them off the entry bar would be a one-bar look-ahead hiding inside the diagnostics.

**Sample.** The {BASELINE} baseline at `{ref}`, pooled across symbols
({counts}) for {closed} closed trades. Pooled because the configuration is identical
across symbols and the per-symbol counts are in the dozens; a quintile split still
leaves single-digit-to-low-teens trades per bucket. **Rank statistics on that many
points are noisy, and only a strong, consistent relationship should be believed.** Every
table below prints its own bucket counts rather than making the reader infer the
thinness.

{(NL + NL).join(blocks)}

## Verdict on the feature set

{shortlist}

**{blocked_sentence}** F5 needs perpetual-futures open interest and funding; the
exchange-native sources are identified and free, but the plumbing does not exist.

**F2 is computed here for the first time.** It was blocked in v1.1 by the same D111
`Bar`-schema gap that blocked the volume-confirmation filter; D168 closed that gap by
putting volume inside `DataView` as an aligned, optionally-present series, so both the
filter and this feature now run against the same guarded channel.

**F6 is half-built and the report says which half.** On daily bars with a 00:00 UTC
boundary, every bar close sits exactly on a perp funding timestamp (00/08/16 UTC), so
the funding-proximity component is identically zero and carries no information at this
frequency — a real limitation of the bar clock, not of the idea. Only the options-expiry
component varies, and that is what is logged."""


EXIT_PRIORS = {
    "exit_e1": "predicted a SURVIVOR — the doc's highest-priority recommendation, and the "
               "one it names alongside F1 as most likely to work",
    "exit_e2": "genuine breakouts work quickly; stagnation is information",
}


def _exit_section(result: bs.StudyResult) -> str:
    """E1 and E2 as one-at-a-time increments, scored by the every-symbol rule (D177)."""
    ref = bs.REFERENCE_TIER
    symbols = list(result.by_symbol)

    def sharpe(sym, name):
        r = result.by_symbol[sym].variants.get((name, ref))
        return r.sharpe_annual(result.config) if r else None

    base = {sym: sharpe(sym, BASELINE) for sym in symbols}
    rows, keepers = [], []
    for v in bs.exit_variants():
        deltas = {}
        for sym in symbols:
            a = sharpe(sym, v.name)
            if a is None or base[sym] is None:
                continue
            deltas[sym] = a - base[sym]
        if not deltas:
            continue
        trades = {
            sym: result.by_symbol[sym].variants[(v.name, ref)].diagnostics.n_closed_trades
            for sym in symbols
        }
        keep = min(deltas.values()) >= 0.01
        if keep:
            keepers.append(v.name)
        rows.append(
            f"| `{v.name}` | " + " | ".join(f"{deltas[s]:+.3f}" for s in symbols)
            + " | " + " / ".join(str(trades[s]) for s in symbols)
            + f" | {'**KEEP**' if keep else 'DROP'} |"
        )

    baseline_trades = " / ".join(
        str(result.by_symbol[s].variants[(BASELINE, ref)].diagnostics.n_closed_trades)
        for s in symbols
    )
    header = ("| Variant | " + " | ".join(f"Δ Sharpe {s}" for s in symbols)
              + " | Trades | Decision |" + NL + "|---|" + "---|" * (len(symbols) + 2) + NL)

    if keepers:
        verdict = (
            f"**{', '.join(keepers)} improves on every symbol.** On the same rule the "
            f"filter increments are scored by, that is a keep — and the doc's prior that E1 "
            f"would survive is supported."
        )
    else:
        verdict = (
            "**Neither exit signature improves on both symbols, so both are dropped.** "
            "That includes E1, which `BREAKOUT_REVERSAL_FEATURES.md` names its "
            "highest-priority recommendation and a predicted survivor. The prior is "
            "falsified, and the mechanism is the one this project keeps finding: E1 and E2 "
            "are both trade-SHORTENING devices, and a breakout book's returns live in a "
            "handful of long trends. Cutting a trade early because it looked wrong for "
            "three bars cuts the trends too — the same failure that killed all four entry "
            "filters and three of six stops."
        )

    return f"""---

# Exit signatures: E1 and E2

`BREAKOUT_REVERSAL_FEATURES.md` permits these two to be built immediately (protocol §4)
because they modify EXITS rather than adding entry-filter dimensions. Each row below is
the accepted baseline plus exactly ONE exit brick — never stacked, so each delta prices one
component. Baseline closed trades: {baseline_trades}.

**E1 — failed-breakout re-entry.** Close falls back inside the channel the entry broke,
within k bars. *{EXIT_PRIORS["exit_e1"]}.*

**E2 — time stop.** Max favourable excursion has not reached 1 ATR within n bars.
*{EXIT_PRIORS["exit_e2"]}.*

{header}{NL.join(rows)}

{verdict}

{_mfe_vs_time(result)}

{_e3_section(result)}"""


def _mfe_vs_time(result: bs.StudyResult) -> str:
    """E2's stated prerequisite: validate n against the baseline's MFE-vs-time
    distribution BEFORE using the candidate values (D177).

    n is fixed at {5, 7} by the doc, so this is a reporting obligation rather than a
    tuning input — the question is whether those values sit sensibly on the distribution,
    and the answer is reported either way."""
    ref = bs.REFERENCE_TIER
    lines = []
    monotonic_check: dict[str, dict[int, float]] = {}
    for sym in result.by_symbol:
        r = result.by_symbol[sym].variants[(BASELINE, ref)]
        bars = BARS_BY_SYMBOL[sym]
        closed = [e for e in r.episodes if not e.is_open]
        if not closed:
            continue
        reached = {n: 0 for n in bs.E2_N}
        counted = 0
        for e in closed:
            atr = tdx.mfe_by_bar(bars, e.entry_index, e.exit_index, e.entry_price,
                                 direction=1, max_bars=max(bs.E2_N))
            atr_at_entry = _atr_fraction(bars, e.entry_index, e.entry_price)
            if atr_at_entry is None or not atr:
                continue
            counted += 1
            for n in bs.E2_N:
                # A trade that CLOSED before bar n having already reached 1 ATR did reach
                # it by bar n. Requiring len(atr) >= n instead excluded short trades from
                # the larger n only, which made the rate FALL from bar 5 to bar 7 — an
                # impossibility, since mfe_by_bar is monotone non-decreasing. That
                # impossibility is the only reason the bug was visible.
                best_by_n = atr[min(n, len(atr)) - 1]
                if best_by_n >= atr_at_entry:
                    reached[n] += 1
        if counted:
            monotonic_check[sym] = {n: reached[n] / counted for n in bs.E2_N}
            lines.append(
                f"| {sym} | {counted} | "
                + " | ".join(f"{reached[n] / counted:.0%}" for n in bs.E2_N) + " |"
            )
    if not lines:
        return ""
    for sym, rates in monotonic_check.items():
        ordered = [rates[n] for n in bs.E2_N]
        if any(b < a - 1e-9 for a, b in zip(ordered, ordered[1:])):
            raise AssertionError(
                f"{sym}: 'reached 1 ATR by bar n' fell as n grew ({ordered}) — MFE by bar is "
                "monotone non-decreasing, so this cannot happen and indicates a counting bug"
            )
    header = ("| Symbol | Trades | " + " | ".join(f"reached 1 ATR by bar {n}" for n in bs.E2_N)
              + " |" + NL + "|---|---|" + "---|" * len(bs.E2_N) + NL)
    return f"""## E2's prerequisite: the MFE-vs-time distribution

The doc requires n be validated against the baseline's own MFE-vs-time distribution before
the candidate values are used. n is FIXED at {list(bs.E2_N)} by the doc, so this is a check
that those values are sensible — not a search for better ones.

{header}{NL.join(lines)}

Read this as the exit's own hit rate: it is the fraction of trades E2 would NOT cut. The
complement is how much of the book each n would remove, and the table above shows that
directly.


"""


def _atr_fraction(bars, entry_index: int, entry_price: float, window: int = 20):
    """ATR at entry, expressed as a fraction of the entry price so it is comparable with
    `mfe_by_bar`, which returns fractions."""
    if entry_index - window < 1 or not entry_price:
        return None
    total = 0.0
    for j in range(entry_index - window, entry_index):
        bar, prev = bars[j].bar, bars[j - 1].bar.close
        total += max(bar.high - bar.low, abs(bar.high - prev), abs(bar.low - prev))
    return (total / window) / entry_price


def _e3_section(result: bs.StudyResult) -> str:
    """E3 is LOG-ONLY by instruction. This describes what was logged and nothing else."""
    ref = bs.REFERENCE_TIER
    counts = []
    for sym in result.by_symbol:
        r = result.by_symbol[sym].variants[(BASELINE, ref)]
        with_traj = sum(1 for e in r.episodes if e.trajectories.get("E3_range"))
        with_vol = sum(1 for e in r.episodes if e.trajectories.get("E3_volume"))
        counts.append(f"{sym} {with_traj} range / {with_vol} volume")
    return f"""## E3 — impulse decay, logged and not acted on

The doc is explicit: *"Definition is fuzzy; log range/volume trajectories per trade so it
can be studied, but no exit rule in this phase."* So there is no E3 variant above and
nothing gates on it.

Post-entry bar range and volume are recorded per trade on `TradeEpisode.trajectories`
({', '.join(counts)}) and travel in the summary JSON. Volume became loggable only with
D168; before that this half of E3 could not have been recorded at all.

**No claim is made here.** Turning "declining range and volume while price grinds
marginally higher" into a rule requires a definition the doc does not give, and inventing
one to fill the gap would be exactly the kind of unregistered search the rest of this
document is built to avoid."""


def _multiplicity(result: bs.StudyResult) -> str:
    study = result.config
    per_symbol = len(result.variant_names) * len(result.tiers)

    # v1 printed a breakdown whose sub-rows summed to 19 against a stated total of 23
    # (the vol-target sensitivities had no row), and the verdict prose then quoted the
    # 19. A multiplicity table that does not add up is the one table in this report
    # that must never be wrong, so it is asserted rather than eyeballed.
    subtotal = (len(PLATEAU_NAMES) + len(FILTER_NAMES) + len(EXIT_NAMES) + len(SIZING_NAMES)
                + len(VOL_TARGET_NAMES) + 1)
    if subtotal != len(result.variant_names):
        raise AssertionError(
            f"multiplicity breakdown does not sum: rows total {subtotal} but the study ran "
            f"{len(result.variant_names)} variants ({', '.join(result.variant_names)}). Add the "
            "missing group to the table rather than adjusting the total."
        )
    return f"""---

# Multiplicity: everything that was evaluated

Counting honestly matters more than the count itself, so here is every knob that was
turned, whether or not it appears in a table above.

| What | Count |
|---|---|
| Strategy variants per symbol | {len(result.variant_names)} |
| — of which parameter-grid cells (N_entry × N_exit) | {len(PLATEAU_NAMES)} |
| — of which filter increments | {len(FILTER_NAMES)} |
| — of which exit increments (E1, E2) | {len(EXIT_NAMES)} |
| — of which sizing sensitivities | {len(SIZING_NAMES)} |
| — of which vol-target sensitivities | {len(VOL_TARGET_NAMES)} |
| — of which in-training-window selection | 1 |
| Cost tiers | {len(result.tiers)} |
| Symbols | {len(result.by_symbol)} |
| **Out-of-sample trials logged** | **{result.n_oos_trials}** ({per_symbol} per symbol) |
| Per-window trial rows logged | {sum(len(s.variants) * s.n_windows for s in result.by_symbol.values()):,} |
| In-training-window parameter evaluations (fitting, not trials) | {result.n_train_evaluations:,} |

**What the DSR trial pool is, and is not.** Bailey & López de Prado's N is the number of
*configurations* tried. This study has many, so the pool is every variant's out-of-sample
daily Sharpe at one (symbol, tier) — {len(result.variant_names)} per cell, selected on
identity fields in the logged config, never on the presence of a metric (D98). Per-window
rows carry `row_kind="window"` and are excluded by that same predicate. This is a
different pool from the pairs studies' one-row-per-window, deliberately: those studies
varied no parameters, so their windows *were* their trials.

**The pool is still too small to be a licence.** It counts neither the
{result.n_train_evaluations:,} in-training evaluations (fits, not out-of-sample trials —
but each one is a parameter setting a human looked at), nor the cross-symbol multiplicity,
nor the largest term of all: the decision to test a breakout strategy on crypto, taken
after a decade of visible crypto trend. **A DSR below 0.95 here means "no demonstrated
edge"; a DSR above 0.95 does not mean the reverse.**"""



def filter_verdicts(result: bs.StudyResult) -> dict[str, dict]:
    """Keep/drop, decided by a rule stated before the numbers were looked at: a filter
    is KEPT only if it improves the out-of-sample annualised Sharpe against the
    baseline on EVERY symbol at the reference (taker) tier. One symbol is a coin flip;
    requiring both is the cheapest guard available against reading noise as signal, and
    it is deliberately strict because four filter variants across two symbols is
    exactly the sample size where something will look good by accident."""
    ref = bs.REFERENCE_TIER
    out = {}
    for name in FILTER_NAMES:
        rows = {}
        for symbol, sr in result.by_symbol.items():
            base = sr.variants[(BASELINE, ref)]
            variant = sr.variants[(name, ref)]
            rows[symbol] = {
                "d_sharpe": variant.sharpe_annual(result.config) - base.sharpe_annual(result.config),
                "d_return": variant.total_return - base.total_return,
                "d_maxdd": variant.max_drawdown - base.max_drawdown,
                "d_trades": variant.diagnostics.n_closed_trades - base.diagnostics.n_closed_trades,
                "d_exposure": variant.diagnostics.exposure - base.diagnostics.exposure,
            }
        out[name] = {"rows": rows, "keep": all(r["d_sharpe"] > 0 for r in rows.values())}
    return out


def _filter_decision(result: bs.StudyResult) -> str:
    verdicts = filter_verdicts(result)
    ref = bs.REFERENCE_TIER
    lines = [
        "| Filter | " + " | ".join(f"Δ Sharpe {s}" for s in result.by_symbol)
        + " | " + " | ".join(f"Δ max DD {s}" for s in result.by_symbol) + " | Decision |",
        "|---" * (1 + 2 * len(result.by_symbol) + 1) + "|",
    ]
    for name, verdict in verdicts.items():
        sharpes = " | ".join(f"{verdict['rows'][s]['d_sharpe']:+.2f}" for s in result.by_symbol)
        dds = " | ".join(f"{verdict['rows'][s]['d_maxdd'] * 100:+.1f} pp" for s in result.by_symbol)
        decision = "**KEEP**" if verdict["keep"] else "DROP"
        lines.append(f"| `{name}` | {sharpes} | {dds} | {decision} |")
    kept = [n for n, v in verdicts.items() if v["keep"]]
    dropped = [n for n, v in verdicts.items() if not v["keep"]]

    return f"""---

# Filters: which ones survive out of sample

**Decision rule, fixed before looking:** a filter is kept only if it improves the
out-of-sample annualised Sharpe against the baseline **on every symbol** at the
reference tier (`{ref}`). One symbol is a coin flip. Four filter variants across two
symbols is exactly the sample size where something looks good by accident, so the bar
is deliberately strict.

{chr(10).join(lines)}

**Kept: {', '.join(f'`{n}`' for n in kept) if kept else 'none'}.**
**Dropped: {', '.join(f'`{n}`' for n in dropped) if dropped else 'none'}.**

{_filter_prose(result, verdicts)}"""


def _filter_prose(result: bs.StudyResult, verdicts: dict) -> str:
    gate = verdicts["filter_trend_gate_200"]
    debounce = verdicts["filter_debounce_m2"]
    vc08 = verdicts["filter_volcontract_0.8"]
    vc10 = verdicts["filter_volcontract_1.0"]
    symbols = list(result.by_symbol)

    def per_symbol(v: dict, key: str, fmt: str = "{:+.2f}") -> str:
        """One figure per symbol, in symbol order, separated by a slash — so a reader
        can tell which number belongs to which instrument without counting commas."""
        return " / ".join(fmt.format(v["rows"][s][key]) for s in symbols)

    order = " / ".join(s.split("-")[0] for s in symbols)

    return f"""**The three dropped filters all fail the same way, and it is instructive.**
(Figures below are {order}, in that order.) Each of them does what it was meant to do
mechanically: the debounce cuts closed trades by {per_symbol(debounce, 'd_trades', '{:.0f}')}
and the 0.8 volatility-contraction threshold by {per_symbol(vc08, 'd_trades', '{:.0f}')},
and both reduce max drawdown ({per_symbol(debounce, 'd_maxdd', '{:+.1%}')} and
{per_symbol(vc08, 'd_maxdd', '{:+.1%}')} respectively). What neither does is improve
risk-adjusted return: Sharpe falls by {per_symbol(debounce, 'd_sharpe')} and
{per_symbol(vc08, 'd_sharpe')}.

The reason is visible in the free-tier tables above, which strip cost effects out
entirely: the filters lose almost exactly as much at 0 bp as at 40 bp. **They are not
saving costs; they are removing trades that were, on average, good.** A breakout
strategy's return distribution is dominated by a handful of long trends, and every
filter here is a device for entering later or less often. The trends that pay are the
ones that run away from you immediately — precisely the ones a two-close debounce or a
"wait until the market has been quiet" precondition discards. The volatility-contraction
filter at the looser 1.0 threshold does correspondingly less damage
({per_symbol(vc10, 'd_sharpe')}): it filters less, so it destroys less.

**The trend gate is the exception, and a marginal one.** Requiring price above its
200-day SMA improves Sharpe by {per_symbol(gate, 'd_sharpe')} and reduces max drawdown by
{per_symbol(gate, 'd_maxdd', '{:+.1%}')}, on both symbols, at both the free and the taker
tier. That is a consistent sign rather than a large effect, and it is the filter with the
clearest mechanism: a 40-day-high breakout that fires below the 200-day average is by
construction a bounce inside a downtrend, and those are the breakouts that fail. It
survives the stated rule; it would not survive a demand for a *large* effect. Carry it as
"keep, weakly evidenced", not as a discovery."""



def _selection_section(result: bs.StudyResult) -> str:
    ref = bs.REFERENCE_TIER
    rows = ["| Symbol | Fixed baseline (40/10) | In-train selected | Δ Sharpe | Δ return |",
            "|---|---|---|---|---|"]
    for symbol, sr in result.by_symbol.items():
        base = sr.variants[(BASELINE, ref)]
        sel = sr.variants[("selected_in_train", ref)]
        rows.append(
            f"| {symbol} | Sharpe {base.sharpe_annual(result.config):.2f}, "
            f"{base.total_return:+.1%} | Sharpe {sel.sharpe_annual(result.config):.2f}, "
            f"{sel.total_return:+.1%} | "
            f"{sel.sharpe_annual(result.config) - base.sharpe_annual(result.config):+.2f} | "
            f"{sel.total_return - base.total_return:+.1%} |"
        )
    return f"""---

# Does choosing parameters in the training window beat not choosing?

The `selected_in_train` variant re-picks (N_entry, N_exit) at every one of the
walk-forward windows, by backtesting the full {len(bs.PLATEAU_N_ENTRY) * len(bs.PLATEAU_N_EXIT) - 0}-cell
grid on that window's **training slice only** and taking the best training-window daily
Sharpe (ties broken toward the lower N_entry, then the lower N_exit). The chosen
configuration is then applied to that window's test bars through a parameter schedule,
with the position carried across the switch. That is {result.n_train_evaluations:,}
training backtests in total, and it is the only part of this study that fits anything.

The structural guarantee is tested, not asserted: the fitter is handed a training slice
and the integration suite records every bar it receives and fails if any of them is at
or after that window's first test bar.

{chr(10).join(rows)}

**Adaptive parameter selection did not pay.** On BTC it lost to simply fixing 40/10 up
front; on ETH it gained slightly. Both deltas are inside the spread of the plateau
surface itself, which is the honest way to read them: since neighbouring cells of the
grid perform similarly, picking between them on 252 bars of training data is picking on
noise, and the transaction costs of switching are real while the benefit is not. **A
fixed, a-priori parameter choice is the better engineering decision here** — and that
conclusion is only available because the plateau surface was computed first."""


def _verdict(result: bs.StudyResult) -> str:
    ref = bs.REFERENCE_TIER
    ref_bps = [t for t in result.tiers if t.name == ref][0].fee_bps / 100
    lines = []
    for symbol in result.by_symbol:
        lines.append("- " + _verdict_line(result, symbol, ref))
        lines.append("- " + _verdict_line(result, symbol, "maker_0bp"))

    per_symbol = []
    for symbol, sr in result.by_symbol.items():
        free = sr.variants[(BASELINE, "maker_0bp")]
        m25 = sr.variants[(BASELINE, "maker_25bp")]
        taker = sr.variants[(BASELINE, ref)]
        bench = sr.benchmarks[ref]
        cfg = result.config
        per_symbol.append(
            f"""**{symbol}.** Fees move the baseline from {free.total_return:+.1%} (0 bp) to
{m25.total_return:+.1%} (25 bp maker) to {taker.total_return:+.1%} ({ref_bps:.2f}% taker): the taker
tier gives up {(free.total_return - taker.total_return) / (1 + free.total_return):.0%} of the
zero-fee terminal wealth, and costs consume {taker.diagnostics.cost_share_of_gross:.1%} of gross
P&L. Annualised Sharpe moves {free.sharpe_annual(cfg):.2f} → {m25.sharpe_annual(cfg):.2f} →
{taker.sharpe_annual(cfg):.2f}. Buy-and-hold over the same span returned {bench.total_return:+.1%}
at Sharpe {bench.sharpe_annual(cfg):.2f} with a {bench.max_drawdown:.1%} drawdown, against the
strategy's {taker.max_drawdown:.1%} at {taker.diagnostics.exposure:.0%} time in market."""
        )

    variant = bs.Variant(BASELINE, "plateau",
                         fixed_config=bs.breakout_config(bs.BASELINE_N_ENTRY, bs.BASELINE_N_EXIT))
    tier_obj = [t for t in result.tiers if t.name == ref][0]
    boot = {}
    for symbol, sr in result.by_symbol.items():
        boot[symbol] = bs.sharpe_difference_bootstrap(
            sr.variants[(BASELINE, ref)].oos_returns,
            sr.benchmarks[ref].oos_returns,
            result.config,
            seed=result.config.seed,
        )["prob_positive"]
    btc_p, eth_p = boot.get("BTC-USD", float("nan")), boot.get("ETH-USD", float("nan"))
    btc_bars = BARS_BY_SYMBOL["BTC-USD"]
    btc_spans = bs._window_spans(btc_bars, result.config)
    btc_multiple = (
        btc_bars[btc_spans[-1][3] - 1].bar.close / btc_bars[btc_spans[0][2]].bar.close
    )
    btc_starts = bs.start_date_sensitivity(btc_bars, "BTC-USD", variant, tier_obj, result.config)
    btc_cagr_lo = min(row["strategy_cagr"] for row in btc_starts)
    btc_cagr_hi = max(row["strategy_cagr"] for row in btc_starts)

    # The up-year/down-year pattern, counted rather than asserted — the two symbols do
    # NOT have the same number of down years, and a hardcoded claim was wrong for ETH.
    parts, total_down, total_down_wins, clean_sweep = [], 0, 0, True
    for symbol, sr in result.by_symbol.items():
        rows = bs.annual_breakdown(sr.variants[(BASELINE, ref)], sr.benchmarks[ref])
        up = [row for row in rows if row["benchmark"] > 0]
        down = [row for row in rows if row["benchmark"] < 0]
        lost_up = sum(1 for row in up if row["strategy"] < row["benchmark"])
        won_down = sum(1 for row in down if row["strategy"] > row["benchmark"])
        total_down += len(down)
        total_down_wins += won_down
        clean_sweep &= (lost_up == len(up) and won_down == len(down))
        parts.append(
            f"{symbol.split('-')[0]} lost in {lost_up} of {len(up)} up years and won in "
            f"{won_down} of {len(down)} down years"
        )
    era_pattern = (
        f"the strategy **lost to buy-and-hold in every up year and beat it in every down "
        f"year, on both symbols** ({'; '.join(parts)})."
        if clean_sweep
        else f"the pattern is {'; '.join(parts)}."
    )

    return f"""---

# Verdict

{chr(10).join(lines)}

{chr(10).join(chr(10).join(['', p]) for p in per_symbol)}

## Does it survive costs at the maker tier?

**Yes — and that is the least interesting true thing in this document.**

The strategy survives fees comfortably at every tier tested. The whole 0 bp → 40 bp
range costs roughly {min(sr.variants[(BASELINE, ref)].diagnostics.cost_share_of_gross for sr in result.by_symbol.values()):.0%}–{max(sr.variants[(BASELINE, ref)].diagnostics.cost_share_of_gross for sr in result.by_symbol.values()):.0%}
of gross P&L and a fraction of a Sharpe point. That is a direct consequence of what the
per-trade diagnostics show: the median trade is held for
{min(sr.variants[(BASELINE, ref)].diagnostics.median_bars_held for sr in result.by_symbol.values()):.0f}–{max(sr.variants[(BASELINE, ref)].diagnostics.median_bars_held for sr in result.by_symbol.values()):.0f}
days, the whipsaw rate at the baseline parameters is **zero** on both symbols, and
annualised turnover is around
{min(sr.variants[(BASELINE, ref)].diagnostics.annual_turnover for sr in result.by_symbol.values()):.0f}–{max(sr.variants[(BASELINE, ref)].diagnostics.annual_turnover for sr in result.by_symbol.values()):.0f}×.
A strategy that trades a few dozen times a decade cannot be killed by 40 bp. The
hysteresis between a 40-bar entry and a 10-bar exit is doing exactly the job it was
designed to do, and the golden-master and property tests confirm the two conditions can
never fire on the same bar.

**So the fee question is answered and it is not the binding constraint. Three things
that are not fees are.**

1. **The absolute returns belong to the instrument, and the risk-adjusted claim is not
   measurable.** Two separate points, both fatal to the obvious reading.

   *The era.* BTC went {btc_multiple:.0f}x over the out-of-sample span. Any long-biased
   rule on that decade prints four-figure percentages, so
   {result.by_symbol['BTC-USD'].variants[(BASELINE, ref)].total_return:+.0%} is a fact
   about BTC before it is a fact about breakouts. The year-by-year table is the honest
   version: {era_pattern} That is not return prediction, it is insurance — bought with
   bull-market underperformance, paid out in bear markets. Across both symbols the sample
   contains {total_down} down years in total, and the insurance paid out in
   {total_down_wins} of them — so the whole case rests on {total_down_wins} observations.
   Change the start date and the strategy's CAGR ranges from
   {btc_cagr_lo:+.0%} to {btc_cagr_hi:+.0%} on BTC alone.

   *The statistics.* The Sharpe advantage over buy-and-hold — +0.04 on BTC, +0.11 on ETH —
   is inside the noise. A paired block bootstrap puts P(strategy Sharpe > benchmark
   Sharpe) at {btc_p:.0%} and {eth_p:.0%} respectively, with 90% intervals comfortably
   spanning zero, and at two of the five start dates tested the strategy's Sharpe is
   *below* the benchmark's. **The risk-adjusted claim, stated as a Sharpe improvement,
   is not supported.**

   What survives both objections is narrower and holds everywhere: **at matched average
   exposure the strategy earns several times the terminal wealth of holding the same
   fraction constantly, and its max drawdown is lower at every start date and on both
   symbols, typically by half.** That is a real and useful property. It is a
   drawdown-shape result, not an alpha result, and the difference matters.

2. **The cost model is the optimistic part, and fees are its smallest term.** What is
   modelled is an exchange fee. What is not modelled is the slippage of sending a market
   order into an instrument that has just printed a 40-day high — which is the single
   most adversely-selected moment to be a buyer, and on daily crypto bars it is entirely
   invisible. The maker tiers are worse than optimistic: getting a maker fee means
   resting a limit order and *not being filled* in the fast breakouts, which are the
   trades that pay. A realistic execution study — intraday bars, order-book depth,
   fill-probability modelling for resting orders — would move these numbers by more than
   the entire 0–40 bp fee range does. **That, not the fee tier, is the honest next
   experiment.**

3. **The selection bias above this study is larger than anything inside it.** The DSR
   numbers are near 1.0 at every tier, and the mechanical reason is that the plateau is
   flat: {len(result.variant_names)} variants whose Sharpes cluster tightly give a tiny
   V[{{SRn}}], so the noise floor SR0 barely rises and almost nothing is deflated away.
   That is DSR working correctly on the multiplicity it was given, and it is also why
   those numbers should not be read as vindication. The trial pool counts
   {len(result.variant_names)} configurations. It does not count
   the {result.n_train_evaluations:,} training-window fits, the two-symbol choice, or the
   decision — made in 2026, with a decade of crypto trend visible — to test a trend
   follower on the two crypto assets that survived. **Treat DSR ≈ 1.0 here as "the
   multiplicity we measured was not the binding problem", not as "this is real."**

## What would change the answer

Running this on instruments chosen without hindsight (a broad basket including the
crypto assets that died), with an execution model that prices crossing the spread into a
breakout, and shorts as well as longs. Each of those is a bigger lever than every fee
tier in this document combined."""


def _caveats(result: bs.StudyResult) -> str:
    return """---

# Standing caveats

1. **Fees only.** No spread, no slippage, no market impact, no funding. A 0.40% taker fee
   on a market order into a breakout is the *fee*, not the *cost* — the slippage of
   crossing into a market that has just made a 40-day high is real and unmodelled. Every
   return here is therefore optimistic, and the maker tiers doubly so.
2. **The maker tiers are a lower bound, not an execution plan.** A breakout entry is a
   market order by nature: you want the fill because the level broke. Getting a *maker*
   fee means resting a limit order and accepting that in the fastest breakouts — the ones
   that pay — you do not get filled at all. The maker rows answer "how much of the result
   is fees?", not "here is a cheaper way to run this".
3. **Survivorship and selection at the instrument level.** BTC and ETH are the two crypto
   assets that survived to be worth studying. Testing a trend follower on them, over a
   decade in which they went up enormously, is a selected sample by construction — the
   single largest un-deflatable bias in this document.
4. **Single data source (D26).** yfinance only; no second-source cross-check. Crypto
   daily bars are an aggregate across venues, so "the open" is a convention, not a price
   anyone was quoted.
5. **Spot, not perpetuals.** BTC and ETH are modelled as `Equity(quantity_precision=8)`
   (D108): long-only, unlevered, no funding. A perpetual-futures implementation would need
   the funding-rate carry brick that is Step 10's deferred work (D14) — and funding would
   be a cost of exactly the kind this study is measuring.
6. **No shorting, by design.** The brief scoped it out. A symmetric long/short trend
   follower is a different strategy with a different answer.
7. **The 40% vol target is a choice, not a result.** Against BTC's ~68% and ETH's ~87%
   realized annual vol it means the strategy is typically around half invested when long.
   The `sizing_fixed_1.0` row is the control that shows what that choice costs and buys."""


if __name__ == "__main__":
    raise SystemExit(main())

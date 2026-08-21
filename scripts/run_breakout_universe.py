"""Cross-sectional breakout universe runner (D140-D144) -> docs/results/breakout_universe.md.

Offline and deterministic: reads the committed crypto-universe fixture, freezes it
through the Step-7 pipeline (clean -> validate -> SnapshotStore), re-applies the
universe policy to the CLEANED bars, runs the single baseline configuration on every
admitted symbol at every cost tier, logs every run to its own registry, and writes the
report.

Run: uv run python scripts/run_breakout_universe.py
"""

from __future__ import annotations

import json
import statistics
import time
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.data.validator import validate
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research import breakout_study as bs
from backtest_framework.research import breakout_universe as bu

REPO = Path(__file__).resolve().parent.parent
FIXTURE = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw_events.json"
META = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.meta.json"
REGISTRY_PATH = REPO / "data" / "breakout_universe_registry.sqlite"
RESULTS = REPO / "docs" / "results" / "breakout_universe.md"
SUMMARY_JSON = REPO / "data" / "breakout_universe_summary.json"
END_DATE = date(2025, 12, 31)
REF = bs.REFERENCE_TIER


# ------------------------------------------------------------------------ pipeline


def freeze_snapshot() -> tuple[str, dict, dict, dict]:
    """clean -> align volumes -> validate -> snapshot. Returns (snapshot_id, cleaned
    bars, cleaned volumes, gate summary).

    **The snapshot is quarantined, and it is loaded anyway — deliberately (D143).** The
    validator's hard threshold (>60% unexplained single-bar move) was calibrated on
    ETFs, where it exists to catch a scraper serving a bad print. On a broad crypto
    cross-section it fires on genuine moves, and it fires hardest on precisely the
    tokens that collapsed. Respecting it mechanically would delete the failed assets
    and hand back the survivorship bias this study exists to remove. So the gate's
    verdict is reported in full — every hard violation counted, by symbol and by
    bucket — and then overridden explicitly rather than silently."""
    raw_bars, raw_volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)
    cleaned, cleaning_report = clean(raw_bars, raw_volumes)
    volumes = {s: bu.align_volumes(cleaned[s], raw_bars[s], raw_volumes[s]) for s in cleaned}
    validation = validate(cleaned, actions, volumes)

    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(
        cleaned,
        actions,
        volumes_by_symbol=volumes,
        cleaning_report=cleaning_report,
        validation=validation,
        extra_meta={"source_fixture": FIXTURE.name, "study": "breakout_universe_v1"},
    )
    snapshot = store.load(snapshot_id, allow_quarantined=True)

    hard_by_symbol = Counter(v.symbol for v in validation.hard_violations)
    gate = {
        "cleaning_changes": len(cleaning_report.changes),
        "cleaning_detail": [
            f"{c.symbol} {c.timestamp.date()} {c.rule}: {c.detail}" for c in cleaning_report.changes
        ],
        "hard_violations": len(validation.hard_violations),
        "warnings": len(validation.warnings),
        "quarantined": not validation.passed,
        "hard_by_symbol": dict(hard_by_symbol),
        "hard_symbols": len(hard_by_symbol),
        "hard_by_check": dict(Counter(v.check for v in validation.hard_violations)),
        "warning_by_check": dict(Counter(v.check for v in validation.warnings)),
        "worst_hard": [
            f"{v.symbol} {v.timestamp.date()}: {v.detail}"
            for v in sorted(validation.hard_violations, key=lambda v: v.timestamp)[:8]
        ],
    }
    return snapshot_id, snapshot.bars_by_symbol, volumes, gate


def main() -> int:
    started = time.time()
    meta = json.loads(META.read_text(encoding="utf-8"))
    cohorts = meta["cohort_by_symbol"]
    fetch_failures = meta["fetch_failures"]

    snapshot_id, bars_by_symbol, volumes_by_symbol, gate = freeze_snapshot()
    print(f"snapshot {snapshot_id} (quarantined={gate['quarantined']})")
    print(f"  clean: {gate['cleaning_changes']} change(s); validator: "
          f"{gate['hard_violations']} hard across {gate['hard_symbols']} symbols, "
          f"{gate['warnings']} warning(s)")

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()  # a study re-run is one coherent trial pool, not a merge
    registry = TrialRegistry(REGISTRY_PATH)
    study = bs.BreakoutStudyConfig()

    seen = {"n": 0}

    def progress(label: str) -> None:
        seen["n"] += 1
        if seen["n"] % 40 == 0:
            print(f"  ... {seen['n']} symbol-tier runs ({label})")

    result = bu.run_universe_study(
        bars_by_symbol,
        volumes_by_symbol,
        registry,
        snapshot_id,
        cohorts=cohorts,
        study=study,
        progress=progress,
        end_date=END_DATE,
    )

    # The fixture's committed membership and the study's own re-application of the
    # policy must agree. If they ever do not, the fixture has drifted from the rule
    # that produced it and the study must stop rather than quietly trade a different
    # universe from the one it documents.
    committed = set(meta["symbols_included"])
    if set(result.selection.included) != committed:
        raise SystemExit(
            "universe policy disagreement between the fixture meta and this run: "
            f"meta-only={sorted(committed - set(result.selection.included))}, "
            f"run-only={sorted(set(result.selection.included) - committed)}"
        )

    print(f"ran {result.n_oos_trials} out-of-sample trials over "
          f"{len(result.runs)} symbols, {len(registry)} registry rows, "
          f"in {time.time() - started:.0f}s")

    year_rows = bu.cross_sectional_year_table(result, REF)
    start_rows = bu.start_date_cross_section(result, bars_by_symbol, REF)
    boot = bu.bootstrap_cross_section(result, REF)
    doc = render_report(result, gate, meta, fetch_failures, year_rows, start_rows, boot)
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(doc, encoding="utf-8")
    SUMMARY_JSON.write_text(
        json.dumps(
            summary_payload(result, gate, year_rows, start_rows, boot), indent=2, default=str
        ),
        encoding="utf-8",
    )
    registry.close()
    print(f"wrote {RESULTS.relative_to(REPO)} and {SUMMARY_JSON.name} "
          f"in {time.time() - started:.0f}s total")
    return 0


def summary_payload(result: bu.UniverseResult, gate: dict, year_rows, start_rows, boot) -> dict:
    """Machine-readable companion — what a regression test would diff against, and what
    keeps the prose's headline numbers checkable."""
    study = result.config
    return {
        "snapshot_id": result.snapshot_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "config": study.to_dict(),
        "policy": result.selection.policy.to_dict(),
        "tiers": [{"name": t.name, "fee_bps": t.fee_bps, "role": t.role} for t in result.tiers],
        "sanity_gate": gate,
        "selection": result.selection.to_dict(),
        "n_oos_trials": result.n_oos_trials,
        "dsr_by_tier": result.dsr_by_tier,
        "dsr_inputs_by_tier": result.dsr_inputs_by_tier,
        "cross_section_by_tier": {
            tier.name: bu.split_by_status(result, tier.name) for tier in result.tiers
        },
        "annual_cross_section": year_rows,
        "start_date_cross_section": start_rows,
        "sharpe_bootstrap_cross_section": boot,
        "symbols": {
            symbol: {
                "cohort": run.cohort,
                "status": run.status,
                "oos_start": run.oos_start.date().isoformat(),
                "oos_end": run.oos_end.date().isoformat(),
                "n_oos_bars": run.n_oos_bars,
                "n_windows": run.n_windows,
                "coverage": run.coverage.to_dict(),
                "by_tier": {
                    tier_name: {
                        "total_return": t.variant.total_return,
                        "cagr": bs.cagr(t.variant.total_return, t.variant.n_oos_bars,
                                        study.periods_per_year),
                        "sharpe_annual": t.variant.sharpe_annual(study),
                        "max_drawdown": t.variant.max_drawdown,
                        "hold_return": t.hold.total_return,
                        "hold_sharpe": t.hold.sharpe_annual(study),
                        "hold_maxdd": t.hold.max_drawdown,
                        "matched_return": None if t.matched is None else t.matched.total_return,
                        "matched_maxdd": None if t.matched is None else t.matched.max_drawdown,
                        "rf_return": t.rf_return,
                        **t.variant.diagnostics.to_metrics(),
                    }
                    for tier_name, t in run.by_tier.items()
                },
            }
            for symbol, run in result.runs.items()
        },
    }


# ------------------------------------------------------------------------ rendering


def _bucket_counts(result: bu.UniverseResult) -> dict[str, int]:
    counts = Counter(run.status for run in result.runs.values())
    return {
        "survived": counts.get(bu.SURVIVED, 0),
        "collapsed": counts.get(bu.COLLAPSED, 0),
        "delisted": counts.get(bu.DELISTED, 0),
    }


def render_report(result, gate, meta, fetch_failures, year_rows, start_rows, boot) -> str:
    sections = [
        _header(result, gate, meta, fetch_failures),
        _method(result),
        _policy_section(result, meta, fetch_failures),
        _gate_section(result, gate),
        _per_symbol_section(result),
        _cross_section(result),
        _split_section(result),
        _bootstrap_section(result, boot),
        _tier_section(result),
        _era_section(result, year_rows, start_rows),
        _dsr_section(result),
        _verdict(result),
        _caveats(result),
    ]
    return "\n\n".join(section.strip() + "\n" for section in sections)


def _bootstrap_section(result, boot) -> str:
    """D120's paired block bootstrap, run per coin and counted across the cross-section.
    The BTC/ETH study could only say "not measurable on two symbols"; sixty-odd symbols
    turn that into a count."""
    n = boot["n_symbols"]
    hold_sig, matched_sig = boot["vs_hold_n_significant"], boot["vs_matched_n_significant"]
    hold_p, matched_p = boot["vs_hold_prob_positive"], boot["vs_matched_prob_positive"]
    verdict = (
        "**On this evidence, no Sharpe comparison in this document should be read as a "
        "measurement.**"
        if max(hold_sig, matched_sig) <= n * 0.2
        else "**A minority of coins do show a distinguishable Sharpe difference**, and "
        "they are the only ones about which a risk-adjusted claim can be made at all."
    )
    return f"""---

# Are any of these Sharpe differences measurable? (D120)

`BREAKOUT_RESULTS.md` retracted its risk-adjusted claim because the paired block
bootstrap put the 90% interval on the Sharpe difference comfortably across zero on both
of its symbols, concluding that ten years of daily data buys roughly ±0.4 of standard
error. With {n} coins the same test can be *counted* instead of described. Each coin gets
its own paired block bootstrap (20-bar blocks, 4,000 sims, seed {int(boot['seed'])}, the
same resampled bar indices applied to both series so their correlation is preserved).

| Comparison | Coins | Median P(Δ Sharpe > 0) | p10 | p90 | Coins whose 90% interval excludes zero |
|---|---|---|---|---|---|
| Strategy − buy & hold (100%) | {n} | {hold_p['median']:.0%} | {hold_p['p10']:.0%} | {hold_p['p90']:.0%} | **{hold_sig} of {n}** |
| Strategy − constant fraction (D119) | {boot['vs_matched_n']} | {matched_p['median']:.0%} | {matched_p['p10']:.0%} | {matched_p['p90']:.0%} | **{matched_sig} of {boot['vs_matched_n']}** |

{verdict} The return and drawdown differences are the defensible findings, exactly as the
two-symbol study concluded — and the cross-section says so with a count rather than an
anecdote. Note also that these are {n} separate 90% intervals: at that confidence level
roughly {int(round(n * 0.1))} would be expected to exclude zero by chance alone, and no
multiplicity correction is applied to them."""


def _header(result, gate, meta, fetch_failures) -> str:
    counts = _bucket_counts(result)
    study = result.config
    return f"""# Does the crypto breakout result generalise? A {len(result.runs)}-coin cross-section including the ones that died

**Date produced:** {datetime.now(timezone.utc).date().isoformat()} ·
**Snapshot:** `{result.snapshot_id}` ·
**Registry:** `data/breakout_universe_registry.sqlite` ·
**Reproduce:** `uv run python scripts/run_breakout_universe.py` (offline, deterministic) ·
**Fixture:** `data/fixtures/crypto_universe_2015_2025_raw.csv.gz`
(fetched once by `scripts/fetch_crypto_universe.py`, the only step that touches the network)

> **Thesis label (D38/D82/D117).** Same label as
> [`BREAKOUT_RESULTS.md`](../../BREAKOUT_RESULTS.md): this is a **directional,
> beta-loaded** strategy, long or flat on one high-beta instrument, never short. It is
> **not** part of this project's market-neutral thesis and is not evidence about it. Its
> honest benchmark is buy-and-hold, not the risk-free rate.

## Why this exists

`BREAKOUT_RESULTS.md` names its own worst problem in its own caveats:

> "BTC and ETH are the two crypto assets that survived to be worth studying. Testing a
> trend follower on them, over a decade in which they went up enormously, is a selected
> sample by construction — the single largest un-deflatable bias in this document."

Adding twenty more of today's largest coins would restate that bias at greater scale.
This study instead runs the **identical, unmodified machinery** — `run_variant`,
`run_benchmark`, `run_constant_fraction_benchmark`, the same cost tiers, the same
walk-forward geometry — over a universe deliberately built to contain assets that
**failed**, and reports every statistic split **survived vs collapsed/delisted**. That
split is the point. It converts the bias from a disclaimer into a measurement.

**Universe:** {len(result.runs)} coins admitted of
{len(meta["symbols_requested"])} attempted —
{counts['survived']} survived, {counts['collapsed']} collapsed,
{counts['delisted']} delisted;
{len(meta["symbols_excluded"])} excluded by the pre-stated policy and
{len(fetch_failures)} that the provider would not serve at all. Every one of them is
named below with its reason.

**Scale.** One configuration (`{bu.BASELINE_VARIANT}`, the BTC/ETH study's baseline),
{len(result.tiers)} cost tiers, {len(result.runs)} symbols =
**{result.n_oos_trials} out-of-sample trials**, each its own continuous walk-forward run
(D113). Risk-free rate {study.rf_annual:.0%}; annualisation on
{study.periods_per_year:.0f} days (crypto trades every calendar day, D17)."""


def _method(result) -> str:
    study = result.config
    return f"""## Method, in one screen

**Nothing here is new machinery.** Every number is produced by
`research.breakout_study`, imported unmodified: `run_variant`, `run_benchmark`,
`run_constant_fraction_benchmark`, `breakout_config`, `CostTier`, `DEFAULT_TIERS`,
`annual_breakdown`, `start_date_sensitivity`, `sharpe_difference_bootstrap`. If a
number here disagrees with `BREAKOUT_RESULTS.md`, the data disagreed, not the code.

**Signal.** The BTC/ETH baseline, unchanged: enter long when `close(t)` exceeds the
{bs.BASELINE_N_ENTRY}-bar high over t−{bs.BASELINE_N_ENTRY} … t−1, exit to flat when it
falls below the {bs.BASELINE_N_EXIT}-bar low. Both extrema exclude the current bar.
Inverse-volatility sizing at a 40% annual vol target, fixed at entry. No filters.

**One configuration, deliberately (D141).** No per-coin parameter sweep. The BTC/ETH
study already showed the plateau is flat and that in-training selection did not pay;
sweeping 12 grid cells per coin would multiply the multiplicity by twelve to re-answer a
settled question. Holding the rule fixed is what makes the cross-section the only
variable.

**Walk-forward.** train={study.train_size}, test={study.test_size}, step={study.step};
one continuous out-of-sample run per (symbol, tier) with the warm-up prefix taken from
inside window 0's training slice, and a runtime assertion that nothing fills inside it
(D113).

**Alignment (D45/D64).** Each symbol is its own single-instrument backtest — the N=1
case — so **no coin is truncated to another's inception**. The fixture is deliberately
not inner-joined; if it were, D45 would cut all {len(result.runs)} coins back to the
youngest one's start and delete most of the sample.

**Costs.** The same four tiers:
{", ".join(f"`{t.name}` = {t.fee_bps / 100:.2f}% ({t.role})" for t in result.tiers)}. One
`percent_spread` brick each — an exchange fee model and nothing more (D114), which makes
every number here optimistic.

**Three benchmarks per coin, all over the identical span.**

1. **100% buy-and-hold** at the same fee tier, fixed quantity (D115).
2. **Constant-fraction at the strategy's own average exposure** (D119) — the fairer
   test, run through the engine so its rebalancing pays real fees.
3. **The risk-free hurdle** — cash at {study.rf_annual:.0%}/yr over the same number of
   bars."""


def _policy_section(result, meta, fetch_failures) -> str:
    policy = result.selection.policy
    counts = _bucket_counts(result)
    survived = ", ".join(f"`{s}`" for s in result.bucket((bu.SURVIVED,)))
    collapsed = ", ".join(f"`{s}`" for s in result.bucket((bu.COLLAPSED,)))
    delisted = ", ".join(f"`{s}`" for s in result.bucket((bu.DELISTED,)))
    cohort_counts = Counter(run.cohort for run in result.runs.values())
    cohort_lines = "\n".join(
        f"| `{cohort}` | {len(meta['cohorts'][cohort])} | {cohort_counts.get(cohort, 0)} |"
        for cohort in meta["cohorts"]
    )
    return f"""---

# The universe: policy first, then the list

## The candidate roster, and exactly how honest it is

Three cohorts, chosen for **point-in-time prominence** rather than present size:

| Cohort | Tickers attempted | Admitted |
|---|---|---|
{cohort_lines}

**Selection-time honesty, stated plainly because it is the study's own weak point.**
The roster was assembled **by hand, in 2026, with hindsight**. It is not a
reconstruction from an archived point-in-time index — no such archive is wired into this
repo, and pretending otherwise would be exactly the self-deception this framework exists
to prevent. What can be said for it is narrower and still worth something:

- two of the three cohorts were chosen for what an asset was worth at a **past** date
  (the 2017/18 peak and the 2021 peak), not for what it is worth now;
- the third cohort was chosen **because those assets failed** — Terra/LUNA, TerraUSD,
  FTX's FTT, Celsius, Serum — which biases the universe *against* the strategy's
  flattering case, not toward it;
- {counts['collapsed'] + counts['delisted']} of the {len(result.runs)} admitted coins
  ended the sample down 90% or more from their own peak, or with the provider no longer
  quoting them at all. A universe of today's top names would contain almost none of them.

What is left un-removed: survivorship inside the *data provider*. A 2017 token that
yfinance never listed, or has since dropped entirely, cannot appear here at any price —
and those are, by construction, the worst outcomes of all. **This universe is less
biased than BTC/ETH. It is not unbiased.**

## The screen, pre-stated and mechanical

Applied by `research.breakout_universe.apply_policy` — one implementation, run at fetch
time to decide the fixture's contents and run **again** by the study on the committed
fixture, so a symbol that fails cannot reach the engine by being quietly present in a
CSV. It screens the **cleaned** series (D25), because the engine trades cleaned bars.

1. **All prices strictly positive.** Log returns and inverse-vol sizing are undefined
   otherwise. Applied after cleaning, so a symbol is not lost to a single bad print the
   cleaner already drops — only to a series that is genuinely part-zero.
2. **Minimum history: {policy.min_bars} bars.** The mechanical floor is lower: the
   harness takes its warm-up prefix from *inside* window 0's training slice, so
   {result.config.train_size} + {result.config.test_size} = {result.config.train_size + result.config.test_size}
   bars already produce one walk-forward window even for the longest lookback in this
   strategy family (a 200-day SMA gate needs 201 bars, which fits inside the 252-bar
   training slice). That floor would also be useless: one 63-bar test window is ten weeks
   of out-of-sample data for a strategy whose median trade lasts about four weeks.
   {policy.min_bars} bars is the shortest history yielding **four windows and a full year
   (252 bars) out of sample**.
3. **Liquidity floor: median daily volume ≥ {policy.min_median_daily_volume_usd:,.0f} USD**
   over the symbol's own history. **Median**, not mean — crypto volume is spiked hard by
   launch weeks and collapse weeks, and a mean describes those days rather than a typical
   one. The level is derived from this study's own capital: 100,000 USD starting cash
   with a 1.0× position cap means the largest opening order is ~100,000 USD, which is 2%
   of a 5,000,000 USD median day — the region D95's capacity work treats unmodelled
   impact as second-order in. It binds hardest on exactly the small tokens whose
   backtests would otherwise be the most flattering and the least real.

**Nothing in the screen touches a return, a Sharpe, a drawdown or a trade count.** That
is the difference between a universe rule and a survivorship filter, and it is why the
screen can be stated in full before any performance is computed.

## Classification: survived, collapsed, delisted

Mechanical, and **hindsight by construction** — which is legitimate here and only here,
because the label decides nothing about what is traded. Every coin is run identically;
the label only splits the results afterwards.

- **delisted** — last bar more than {policy.delisted_gap_days} days before the fixture's
  end date: the provider stopped quoting it. Checked first, because losing the quote is
  the more specific fact.
- **collapsed** — final close at or below {(1 - policy.collapse_terminal_drawdown):.0%}
  of the symbol's own highest close in the fixture (i.e. down
  {policy.collapse_terminal_drawdown:.0%} or worse, terminally). Scale-free by
  construction.
- **survived** — neither.

**Survived ({counts['survived']}):** {survived}

**Collapsed ({counts['collapsed']}):** {collapsed}

**Delisted ({counts['delisted']}):** {delisted}

## Every exclusion and every fetch failure, with its reason

A documented "could not obtain" is evidence. A silent omission is the bias itself.

{bu.render_exclusion_table(meta["symbols_excluded"], fetch_failures, meta["coverage"], meta["cohort_by_symbol"])}

Four of these are worth a sentence, and none of them flatters the study.

- **`MIOTA-USD`** is IOTA, a genuine 2018 top-ten asset. yfinance no longer serves it
  under any ticker this study could find, so it is **missing, not omitted** — and it is a
  token that fell ~99% from its peak, so its absence biases the cross-section toward the
  strategy looking *worse*, not better.
- **`CEL-USD`** (Celsius) and **`LEO-USD`** are real tokens removed by the liquidity
  floor, not by any judgement about them. CEL is a genuine bankruptcy and its loss from
  the collapsed cohort is a real cost of having a mechanical rule; the rule is kept
  because a rule that bends for an interesting name is not a rule.
- **`UNI-USD`** and **`LUNA-USD`** are provider ticker collisions: yfinance serves a
  stale or near-zero series under both, at 17 and 183 USD of median daily volume. The
  liquidity floor removed them mechanically, without anyone eyeballing a chart — an
  unplanned benefit of writing the screen in terms of tradability.
- **`SHIB-USD`**, **`COMP-USD`** and **`ICP-USD`** are excluded on data quality: their
  series contain bars the provider prints at zero. SHIB is a large asset and its
  exclusion is a real loss; ICP loses its whole history to a single zero bar the
  cleaner's spike-and-revert rule cannot reach (that rule needs a bar on each side).
  Both are the honest cost of refusing to hand the engine a price of zero."""


def _gate_section(result, gate) -> str:
    hard_by_bucket = Counter()
    for symbol, count in gate["hard_by_symbol"].items():
        if symbol in result.runs:
            hard_by_bucket[result.runs[symbol].status] += count
    top = sorted(gate["hard_by_symbol"].items(), key=lambda kv: -kv[1])[:10]
    top_line = ", ".join(f"`{s}` ({n})" for s, n in top)
    survived_hits = hard_by_bucket.get(bu.SURVIVED, 0)
    collapsed_hits = hard_by_bucket.get(bu.COLLAPSED, 0) + hard_by_bucket.get(bu.DELISTED, 0)
    return f"""---

# The sanity gate fired, and this study overrode it — on purpose (D143)

The Step-7 pipeline ran normally: cleaning made **{gate['cleaning_changes']} change(s)**
(dropped bars, never rewritten prices — D25's ruleset is drop-and-report). The validator
then recorded **{gate['hard_violations']} hard violation(s)** across
{gate['hard_symbols']} symbols and {gate['warnings']:,} warning(s), so the snapshot is
**quarantined** — `SnapshotStore.load` refuses it unless the caller says
`allow_quarantined=True`, which this runner does, explicitly, and says so here.

Every hard violation is the same check: `unexplained_move`, a >60% single-bar move with
no split to explain it. That threshold was calibrated on ETFs (D74), where a 60% day
means the scraper served a bad print. **On a broad crypto cross-section it means
Tuesday.** ADA rose 137% on 2017-11-28; BNB rose 62% on 2018-01-05; these are real.

The distribution is the argument:

| | Hard violations |
|---|---|
| Symbols that survived | {survived_hits} |
| Symbols that collapsed or were delisted | {collapsed_hits} |

Concentrated in: {top_line}.

**Respecting the gate mechanically would have deleted the collapsed cohort and handed
back the exact survivorship bias this study exists to remove.** So the gate's verdict is
reported in full rather than suppressed, and overridden in one visible place rather than
worked around. The honest reading is that D74's threshold is an *equity* threshold and a
crypto-calibrated one does not exist yet — recorded as a deferral in D143, not fixed
here, because recalibrating a cross-cutting data gate from inside a study is how gates
stop meaning anything."""


def _per_symbol_section(result) -> str:
    diffs = bu.reconcile_against_published(result)
    worst = max((d for symbol in diffs for d in diffs[symbol].values()), default=float("nan"))
    reconciled = worst == worst and worst < 1.0
    reconciliation = (
        "**Reconciliation against `BREAKOUT_RESULTS.md`, and why it matters.** BTC-USD and "
        "ETH-USD appear in both studies. The two share the strategy code and the harness "
        "but **not the data**: the BTC/ETH study reads `crypto_daily_2015_2025_raw.csv.gz` "
        "and this one reads `crypto_universe_2015_2025_raw.csv.gz`, fetched separately from "
        "a provider that restates history (D24's whole rationale). Their `plateau_40_10` @ "
        f"`{REF}` rows nevertheless **agree to the precision that document prints** — the "
        f"largest disagreement across every reported statistic is {worst:.2f}x the last "
        "digit it states, on total return, Sharpe, max drawdown, exposure, trade count, "
        "buy-and-hold and matched-exposure alike. So the "
        "cross-section's numbers can be read directly against the published ones, and a "
        "test pins the agreement so a future provider restatement shows up as a failure "
        "rather than as two documents quietly quoting different BTC histories."
        if reconciled
        else "**Reconciliation against `BREAKOUT_RESULTS.md` FAILED.** The overlapping "
        f"BTC/ETH rows differ by up to {worst:.2f}x the precision that document prints, "
        "which means the two fixtures are not the same underlying data. Treat every "
        "cross-study comparison in this document as suspect until that is explained."
    )
    return f"""---

# Every coin at the reference tier (`{REF}`)

Sorted survivors first, then collapsed/delisted. `Matched-exposure` is the D119
constant-fraction benchmark at that coin's own average exposure; `Risk-free` is cash at
{result.config.rf_annual:.0%}/yr over the same span. Every row is out of sample.

{reconciliation}

**One column needs a warning.** `Costs/gross` is round-trip costs over |gross P&L|, so it
explodes toward meaninglessness on any coin whose gross P&L is near zero — a strategy that
made and lost almost exactly the same amount can show a four-figure percentage there. Read
it on the coins that made money and ignore it on the ones that did not; the tier table
further down reports the cross-sectional median, which is the number that means something.

{bu.render_symbol_table(result, REF)}"""


def _cross_section(result) -> str:
    c = bu.cross_section(result, REF)
    hold = c["hold_return"]
    strat = c["strategy_return"]
    return f"""---

# The cross-section: the actual result

The question is not "what did the strategy return" — with {len(result.runs)} coins over a
decade, some number will be large. The question is **in what fraction of the
cross-section did a fixed breakout rule beat each benchmark.**

{bu.render_hit_rate_table(result, REF)}

Read the second column against the third. Beating 100% buy-and-hold is a low bar on a
cross-section this full of assets that fell 90%+ — you clear it by being in cash. Beating
the **matched-exposure** benchmark is the real test (D119): it holds the same average
fraction of capital in the same coin over the same span, so the only difference left is
*when* the exposure was taken. That is the only column that isolates the timing claim.

## Distributions, not means

A cross-section dominated by one or two coins is exactly the failure this study exists to
expose, so the whole distribution is reported.

**Total return (out of sample, `{REF}`):**

{bu.render_distribution_table(result, REF, "strategy_return", as_pct=True)}

**Buy-and-hold total return over the same spans:**

{bu.render_distribution_table(result, REF, "hold_return", as_pct=True)}

**Annualised Sharpe:**

{bu.render_distribution_table(result, REF, "strategy_sharpe", as_pct=False)}

**Max drawdown:**

{bu.render_distribution_table(result, REF, "strategy_maxdd", as_pct=True)}

**Buy-and-hold max drawdown:**

{bu.render_distribution_table(result, REF, "hold_maxdd", as_pct=True)}

**Time in market:**

{bu.render_distribution_table(result, REF, "exposure", as_pct=True)}

**Closed trades per coin:**

{bu.render_distribution_table(result, REF, "trades", as_pct=False)}

**Costs as a share of gross P&L:**

{bu.render_distribution_table(result, REF, "cost_share_of_gross", as_pct=True)}

The median coin's strategy return is {strat['median']:+.1%} against a median
buy-and-hold of {hold['median']:+.1%}; the mean strategy return is
{strat['mean']:+.1%} against a mean buy-and-hold of {hold['mean']:+.1%}.
**The gap between the median and the mean is the whole story of a crypto
cross-section** — a handful of coins carry the average, and neither the strategy nor the
benchmark is described by its own mean."""


def _split_section(result) -> str:
    split = bu.split_by_status(result, REF)
    s, c = split[bu.SURVIVED], split["collapsed_or_delisted"]
    study = result.config

    def rate(block, key):
        wins, total, fraction = block[key]
        return f"{wins}/{total} ({fraction:.0%})" if total else "n/a"

    prior_holds = c["beat_buy_and_hold"][2] > s["beat_buy_and_hold"][2]
    matched_holds = (
        c["beat_matched_exposure"][2] > s["beat_matched_exposure"][2]
        if c["beat_matched_exposure"][1] and s["beat_matched_exposure"][1]
        else False
    )
    verdict = (
        "**The prior is confirmed on the buy-and-hold comparison.**"
        if prior_holds
        else "**The prior is NOT confirmed on the buy-and-hold comparison.**"
    )
    matched_verdict = (
        "and it survives the matched-exposure test too, which is the harder one"
        if matched_holds
        else "but it does NOT survive the matched-exposure test, which is the harder one"
    )
    return f"""---

# Survived vs collapsed: the headline

The standing prior for a trend follower is that its value is concentrated in the assets
that fell apart — it is insurance, and insurance pays out on the wreck. `BREAKOUT_RESULTS`
could not test that: it had two survivors and five down years. This universe has
{len(result.bucket(bu.COLLAPSED_BUCKET))} wrecks.

{bu.render_hit_rate_table(result, REF)}

{verdict} Against 100% buy-and-hold the strategy wins
{rate(c, 'beat_buy_and_hold')} of the collapsed/delisted coins versus
{rate(s, 'beat_buy_and_hold')} of the survivors — {matched_verdict}:
{rate(c, 'beat_matched_exposure')} versus {rate(s, 'beat_matched_exposure')} at matched
exposure.

**Why the two columns disagree, mechanically.** Against a 100%-invested benchmark on an
asset that fell 99%, being flat most of the time is enough to win; the strategy does not
have to be right about anything except *not holding*. The matched-exposure benchmark
removes that advantage by construction — it holds the same average fraction — so what it
measures is whether the exposure was taken at better moments than average. Those are two
different claims, and a cross-section is the first place in this project where they can
be separated cleanly.

## The same split on the underlying statistics

| Statistic (median) | Survived | Collapsed / delisted |
|---|---|---|
| Strategy total return | {s['strategy_return']['median']:+.1%} | {c['strategy_return']['median']:+.1%} |
| Buy & hold total return | {s['hold_return']['median']:+.1%} | {c['hold_return']['median']:+.1%} |
| Strategy CAGR | {s['strategy_cagr']['median']:+.1%} | {c['strategy_cagr']['median']:+.1%} |
| Buy & hold CAGR | {s['hold_cagr']['median']:+.1%} | {c['hold_cagr']['median']:+.1%} |
| Strategy Sharpe (ann.) | {s['strategy_sharpe']['median']:.2f} | {c['strategy_sharpe']['median']:.2f} |
| Buy & hold Sharpe (ann.) | {s['hold_sharpe']['median']:.2f} | {c['hold_sharpe']['median']:.2f} |
| Strategy max drawdown | {s['strategy_maxdd']['median']:.1%} | {c['strategy_maxdd']['median']:.1%} |
| Buy & hold max drawdown | {s['hold_maxdd']['median']:.1%} | {c['hold_maxdd']['median']:.1%} |
| Time in market | {s['exposure']['median']:.1%} | {c['exposure']['median']:.1%} |
| Closed trades | {s['trades']['median']:.0f} | {c['trades']['median']:.0f} |
| Costs / gross P&L | {s['cost_share_of_gross']['median']:.1%} | {c['cost_share_of_gross']['median']:.1%} |

Note the drawdown rows, which are the finding `BREAKOUT_RESULTS` said was the one it
could defend. Median strategy drawdown is {s['strategy_maxdd']['median']:.1%} on
survivors and {c['strategy_maxdd']['median']:.1%} on the wrecks, against buy-and-hold
drawdowns of {s['hold_maxdd']['median']:.1%} and {c['hold_maxdd']['median']:.1%}. Whether
that is worth its cost is the return rows above, and a reader should decide from both.

## Where BTC and ETH sit in their own cross-section

{_rank_block(result)}"""


def _rank_block(result) -> str:
    study = result.config
    lines = [
        "| Coin | Total return | Rank of "
        f"{len(result.runs)} | Sharpe | Rank | Beat B&H? | Beat matched-exposure? |",
        "|---|---|---|---|---|---|---|",
    ]
    returns = sorted(
        (r.by_tier[REF].variant.total_return for r in result.runs.values()), reverse=True
    )
    sharpes = sorted(
        (r.by_tier[REF].variant.sharpe_annual(study) for r in result.runs.values()), reverse=True
    )
    for symbol in ("BTC-USD", "ETH-USD"):
        if symbol not in result.runs:
            continue
        t = result.runs[symbol].by_tier[REF]
        ret = t.variant.total_return
        shp = t.variant.sharpe_annual(study)
        matched = "n/a" if t.beats_matched is None else ("yes" if t.beats_matched else "no")
        lines.append(
            f"| `{symbol}` | {ret:+.1%} | {returns.index(ret) + 1} | {shp:.2f} | "
            f"{sharpes.index(shp) + 1} | {'yes' if t.beats_hold else 'no'} | {matched} |"
        )
    n = len(returns)
    ranks = []
    for symbol in ("BTC-USD", "ETH-USD"):
        if symbol in result.runs:
            t = result.runs[symbol].by_tier[REF]
            ranks.append((symbol,
                          returns.index(t.variant.total_return) + 1,
                          sharpes.index(t.variant.sharpe_annual(study)) + 1))
    if not ranks:
        return "\n".join(lines)
    worst_rank = max(max(r, s) for _sym, r, s in ranks)
    top_decile = worst_rank <= max(1, n // 10)
    top_quartile = worst_rank <= max(1, n // 4)
    if top_decile:
        note = (
            f"**Both of the original study's coins sit in the top decile of this "
            f"cross-section on both statistics** (worst rank {worst_rank} of {n}). That is "
            "the direct, numerical answer to that study's own caveat 3: its headline "
            "numbers were, to a substantial degree, a measurement of which two instruments "
            "were chosen. It is not a claim that the rule does nothing — the hit-rate "
            "tables above are that test — but no reader should carry BTC's "
            "four-figure return away as a property of the rule."
        )
    elif top_quartile:
        note = (
            f"Both of the original study's coins sit in the top quartile of this "
            f"cross-section (worst rank {worst_rank} of {n}) — flattering, but not the "
            "extreme outlier case. The hit-rate tables above are the test that matters."
        )
    else:
        note = (
            f"The original study's coins are NOT near the top of this cross-section "
            f"(worst rank {worst_rank} of {n}), which is a genuine point in that study's "
            "favour: its instrument choice was not doing the work its own caveat feared."
        )
    return "\n".join(lines) + "\n\n" + note


def _tier_section(result) -> str:
    return f"""---

# Costs across the cross-section

{bu.render_tier_table(result)}

Median return is monotone non-increasing in the fee tier by construction — the same
property the BTC/ETH study property-tested at the NAV level. What the cross-section adds
is the median cost share: the fee question is answered the same way on 60-odd coins as it
was on two, because the mechanism (a few dozen trades per decade, hysteresis between a
{bs.BASELINE_N_ENTRY}-bar entry and a {bs.BASELINE_N_EXIT}-bar exit) is a property of the
rule, not of the instrument."""


def _era_section(result, year_rows, start_rows) -> str:
    return f"""---

# Is this the strategy, or is it the era? (D121, lifted to the cross-section)

D121 makes these two tables mandatory for any crypto backtest. Here they are computed
across the whole universe rather than per coin, using `bs.annual_breakdown` and
`bs.start_date_sensitivity` unmodified.

## Year by year, across the cross-section

{bu.render_year_table(year_rows)}

The `share beating B&H` column is the one to read: it is a per-year cross-sectional hit
rate, and its swing between bull and bear years is the insurance mechanism showing up in
60-odd instruments at once instead of two.

## Start date, across the cross-section

Identical configuration, identical universe; only the investor's start date changes.

{bu.render_start_date_table(start_rows)}"""


def _dsr_section(result) -> str:
    n = len(result.runs)
    inputs = result.dsr_inputs_by_tier[REF]
    best = inputs["best_symbol"]
    best_run = result.runs[best]
    dsr = result.dsr_by_tier[REF]
    reading = (
        "clears the standing 0.95 line"
        if dsr >= 0.95
        else "does NOT clear the standing 0.95 line, i.e. no demonstrated edge"
    )
    return f"""---

# Deflated Sharpe and multiplicity

{bu.render_dsr_table(result)}

**Read the "best symbol" column before the DSR column.** At the reference tier the best
cross-sectional daily Sharpe belongs to `{best}` — a coin this study labels
**{best_run.status}** — over {inputs['t']:,} out-of-sample bars, which is
{inputs['t'] / result.config.periods_per_year:.1f} years, the short end of this universe.
Its DSR of {dsr:.4f} {reading}. A selected best-of-{n} result on a short span, from a
token that no longer trades, is the single least robust number in this document, and it
is printed here rather than in a headline for that reason.

**What the pool is.** One row per **symbol** at that tier — N = {n} — selected on
identity fields in the logged config (`row_kind == "symbol"`, matching tier, matching
trial-id prefix), never on the presence of a metric (D98's rule). Units are daily
throughout, matching D98's contract. Per-benchmark rows (`row_kind="benchmark"`) and
per-window rows (`row_kind="window"`) are in the registry as the program-level
multiplicity record and are excluded by that same predicate.

**Why symbols and not configurations.** D116 set the pool to configurations *for a study
that swept configurations*. This study sweeps none — one fixed rule everywhere — so its
multiplicity lives entirely in the cross-section: {n} coins were run and the best one
will inevitably look good. That is precisely the selection DSR was built to deflate, and
it is the honest pool here.

**What the pool is NOT.** It does not count:

- the **roster construction** — a hand-assembled list, in 2026, of coins someone
  remembered. That is the largest uncounted term and it cannot be deflated away by any
  statistic computed inside this document;
- the **{len(result.tiers)} cost tiers** (the same run at a different fee is a
  sensitivity point, not an independent trial — D98's rule);
- the **23 configurations** the BTC/ETH study already evaluated before this one fixed the
  baseline. That study's multiplicity is upstream of this study's rule, and this study
  inherits it;
- the multiplicity of having asked the crypto question at all, in 2026, with a decade of
  crypto trend visible.

**The standing reading, inherited from D90/D116:** a DSR below 0.95 means "no
demonstrated edge"; a DSR above 0.95 does **not** mean the reverse.

| What | Count |
|---|---|
| Symbols admitted | {n} |
| Strategy configurations per symbol | 1 |
| Cost tiers | {len(result.tiers)} |
| **Out-of-sample trials logged** | **{result.n_oos_trials}** |
| Benchmark rows logged | {sum(len(r.by_tier) for r in result.runs.values()) * 2 + sum(1 for r in result.runs.values() for t in r.by_tier.values() if t.matched is not None)} |
| Per-window rows logged | {sum(r.n_windows * len(r.by_tier) for r in result.runs.values()):,} |
| In-training-window parameter evaluations | 0 (nothing is fitted — the rule is fixed a priori) |"""


def _verdict(result) -> str:
    study = result.config
    split = bu.split_by_status(result, REF)
    a, s, c = split["all"], split[bu.SURVIVED], split["collapsed_or_delisted"]
    hold_w, hold_n, hold_r = a["beat_buy_and_hold"]
    m_w, m_n, m_r = a["beat_matched_exposure"]
    dd_w, dd_n, dd_r = a["reduced_max_drawdown"]

    btc = result.runs.get("BTC-USD")
    eth = result.runs.get("ETH-USD")
    returns = sorted((r.by_tier[REF].variant.total_return for r in result.runs.values()), reverse=True)
    sharpes = sorted((r.by_tier[REF].variant.sharpe_annual(study) for r in result.runs.values()), reverse=True)

    def rank_line(run) -> str:
        t = run.by_tier[REF]
        return (
            f"`{run.symbol}` ranks {returns.index(t.variant.total_return) + 1} of "
            f"{len(returns)} on total return and "
            f"{sharpes.index(t.variant.sharpe_annual(study)) + 1} of {len(sharpes)} on Sharpe"
        )

    s_matched, c_matched = s["beat_matched_exposure"][2], c["beat_matched_exposure"][2]
    # Three-way, computed rather than asserted: does the timing claim hold everywhere,
    # nowhere, or only on the assets that fell apart? The last is the standing prior for
    # a trend follower, and it is the answer with the most consequences.
    if s_matched > 0.5 and c_matched > 0.5:
        headline = (
            "**Partly — and the part that survives is narrower than the original report "
            "implied.** The timing claim holds in both halves of the cross-section."
        )
    elif s_matched <= 0.5 < c_matched:
        headline = (
            "**Only where the asset fell apart.** The timing claim holds on the coins "
            "that collapsed and fails on the coins that survived — which is the standing "
            "prior for a trend follower, confirmed here for the first time in this "
            "project on a sample large enough to see it."
        )
    elif c_matched <= 0.5 < s_matched:
        headline = (
            "**Only on the survivors** — which is the opposite of the standing prior and "
            "should be treated as a warning about the sample, not a discovery."
        )
    else:
        headline = "**No.** The timing claim fails in both halves of the cross-section."
    dd_claim = (
        f"The drawdown claim, by contrast, holds everywhere: **{dd_w} of {dd_n} "
        f"({dd_r:.0%})**."
        if dd_r > 0.9
        else f"The drawdown claim holds in **{dd_w} of {dd_n} ({dd_r:.0%})**."
    )
    return f"""---

# Verdict: does the BTC/ETH result generalise?

{headline}

Across {a['n_symbols']} coins at the reference tier, the fixed baseline beat the
matched-exposure benchmark (D119 — the fair test) in **{m_w} of {m_n} ({m_r:.0%})** and
beat 100% buy-and-hold in **{hold_w} of {hold_n} ({hold_r:.0%})**. {dd_claim}

The median coin returned {a['strategy_return']['median']:+.1%} out of sample against a
median buy-and-hold of {a['hold_return']['median']:+.1%}, at a median Sharpe of
{a['strategy_sharpe']['median']:.2f} against {a['hold_sharpe']['median']:.2f}, with a
median max drawdown of {a['strategy_maxdd']['median']:.1%} against
{a['hold_maxdd']['median']:.1%}.

**The survived/collapsed split.** Beat-buy-and-hold: {s['beat_buy_and_hold'][2]:.0%} of
survivors versus {c['beat_buy_and_hold'][2]:.0%} of the wrecks. Beat-matched-exposure:
{s['beat_matched_exposure'][2]:.0%} versus {c['beat_matched_exposure'][2]:.0%}. Lower
drawdown: {s['reduced_max_drawdown'][2]:.0%} versus {c['reduced_max_drawdown'][2]:.0%}.

**Where the original two coins sit.** {rank_line(btc) if btc else "BTC-USD is absent"};
{rank_line(eth) if eth else "ETH-USD is absent"}. That is the number
`BREAKOUT_RESULTS.md` could not compute about itself, and it is the direct answer to its
own caveat 3.

## What this study does and does not settle

- It **does** settle whether the BTC/ETH numbers were an instrument-selection artifact:
  the ranks above answer that with a number rather than a disclaimer.
- It **does** separate two claims the two-symbol study could not: "better than holding"
  (easy on a dying asset — you win by being in cash) and "better than holding the same
  average exposure" (hard, and the only version that is about timing).
- It **does not** remove selection bias. The roster is hand-assembled with hindsight, and
  the provider's own coverage removes the worst failures before this study ever sees
  them. It removes the *specific* bias of studying only two survivors, and it measures
  what removing it costs.
- It **does not** change the execution story. Every number is still fees-only (D114): no
  spread, no slippage, no market impact. On the small and dying end of this universe that
  understatement is far worse than on BTC — an exit signal on a token that has fallen 95%
  is a market order into a book that is not there. **That, not the fee tier, is what
  would move these numbers most.**"""


def _caveats(result) -> str:
    return f"""---

# Standing caveats (R3)

1. **The roster is hindsight-assembled.** Stated at length above. This universe is less
   biased than BTC/ETH; it is not unbiased, and no statistic in this document can fix
   that.
2. **Provider survivorship.** A token yfinance never listed, or has dropped entirely,
   cannot appear here — and those are the worst outcomes by construction. `MIOTA-USD` is
   the visible case; the invisible ones are the problem.
3. **Fees only (D114).** No spread, no slippage, no market impact, no funding. On
   collapsed and illiquid names this is a much larger understatement than it was on
   BTC/ETH, and it biases every collapsed-cohort number optimistically — which is
   precisely the cohort this study leans on.
4. **The liquidity floor is a full-history median.** A token that was liquid for three
   years and then died is judged on both eras at once. The floor is stated, mechanical
   and reported per exclusion, but it is not a point-in-time tradability test, and a
   point-in-time one would be better.
5. **The sanity gate was overridden (D143).** {result.selection.policy.min_bars}-bar
   coverage and the liquidity floor are respected; the validator's ETF-calibrated 60%
   move threshold is not. Every hard violation is counted and reported above.
6. **Capital is unmodelled at scale.** The liquidity floor is derived from 100,000 USD of
   starting capital. Several coins compound to many multiples of that inside the
   backtest, at which point the same order is no longer 2% of a day's volume. D95's
   capacity machinery exists and was not run here.
7. **Spot, not perpetuals; no shorting (D108).** Unchanged from `BREAKOUT_RESULTS.md`. A
   long-flat rule on a universe of assets that mostly went to zero is leaving the obvious
   trade on the table, and saying so is not the same as having tested it.
8. **One configuration, inherited.** The baseline was chosen by the BTC/ETH study, on
   BTC/ETH. Fixing it here is the right call for multiplicity (D141) and it also means
   this cross-section is evaluating a rule that was, in a small way, already fitted to
   two of its members."""


if __name__ == "__main__":
    raise SystemExit(main())

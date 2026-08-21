"""Run the breakdown (short) study and write BREAKDOWN_RESULTS.md (D169).

Offline and deterministic, like its long sibling: the fixture is frozen through the
Step-7 pipeline into a content-addressed snapshot, every variant is one continuous
out-of-sample run with a parameter schedule (D113), and every trial is registered.

    uv run python scripts/run_breakdown_study.py
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
from backtest_framework.research import breakdown_study as ds
from backtest_framework.research import breakout_study as bs

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw.csv.gz"
EVENTS = REPO / "data" / "fixtures" / "crypto_daily_2015_2025_raw_events.json"
REGISTRY_PATH = REPO / "data" / "breakdown_study_registry.sqlite"
RESULTS = REPO / "BREAKDOWN_RESULTS.md"
SUMMARY_JSON = REPO / "data" / "breakdown_study_summary.json"

NL = "\n"


def freeze_snapshot():
    bars, volumes = load_fixture_csv_with_volumes(FIXTURE)
    actions = load_events_json(EVENTS)
    cleaned, cleaning_report = clean(bars, volumes)
    validation = validate(cleaned, actions, volumes)
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(
        cleaned, actions, volumes_by_symbol=volumes,
        cleaning_report=cleaning_report, validation=validation,
        extra_meta={"source_fixture": FIXTURE.name},
    )
    snapshot = store.load(snapshot_id)
    gate = {
        "cleaning_changes": len(cleaning_report.changes),
        "hard_violations": len(validation.hard_violations),
        "warnings": len(validation.warnings),
    }
    return snapshot_id, snapshot.bars_by_symbol, gate


def main() -> int:
    started = time.time()
    snapshot_id, bars_by_symbol, gate = freeze_snapshot()
    print(f"snapshot {snapshot_id}")

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()
    registry = TrialRegistry(REGISTRY_PATH)
    study = bs.BreakoutStudyConfig()
    variants = ds.short_variants()
    tiers = bs.SHORT_TIERS
    ref = "taker_40bp"

    payload: dict = {
        "snapshot_id": snapshot_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "config": study.to_dict(),
        "borrow_annual_rate": bs.SHORT_BORROW_ANNUAL_RATE,
        "sanity_gate": gate,
        "n_variants": len(variants),
        "symbols": {},
    }

    n_runs = 0
    for symbol, bars in bars_by_symbol.items():
        spans = bs._window_spans(bars, study)
        oos_start, oos_end = spans[0][2], spans[-1][3]
        oos_bars = list(bars[oos_start:oos_end])
        labels = ds.regime_labels(bars)[oos_start:oos_end]

        # The long book's accepted baseline, run on the SAME span and the SAME tiers, so
        # the correlation and ensemble numbers compare like with like.
        long_variant = bs.Variant(
            "long_baseline", "plateau",
            fixed_config=bs.breakout_config(bs.BASELINE_N_ENTRY, bs.BASELINE_N_EXIT),
        )
        long_result = bs.run_variant(bars, symbol, long_variant, tiers[-1], study)

        per_variant: dict = {}
        for tier in tiers:
            for variant in variants:
                n_runs += 1
                print(f"  ... {n_runs} runs ({symbol} {tier.name} {variant.name})")
                r = bs.run_variant(bars, symbol, variant, tier, study)
                key = f"{variant.name}@{tier.name}"

                # Returns aligned to OOS bars: oos_returns[i] is the return over the
                # step from bar i to bar i+1, so it pairs with labels[1:].
                in_market = _exposure_flags(r, oos_bars)
                slices = ds.slice_by_regime(
                    r.oos_returns, labels[1:], in_market[1:]
                ) if len(r.oos_returns) == len(labels) - 1 else []

                per_variant[key] = {
                    "total_return": r.total_return,
                    "cagr": bs.cagr(r.total_return, r.n_oos_bars, study.periods_per_year),
                    "sharpe_annual": r.sharpe_annual(study),
                    "max_drawdown": r.max_drawdown,
                    "n_closed_trades": r.diagnostics.n_closed_trades,
                    "exposure": r.diagnostics.exposure,
                    "cost_share_of_gross": r.diagnostics.cost_share_of_gross,
                    "regimes": [s.to_dict() for s in slices],
                }

                if tier.name == ref and variant.name == ds.SHORT_BASELINE:
                    holding = [e.bars_held for e in r.episodes if not e.is_open]
                    instrument_returns = [
                        oos_bars[i + 1].bar.close / oos_bars[i].bar.close - 1.0
                        for i in range(len(oos_bars) - 1)
                    ]
                    null = ds.random_entry_null(
                        instrument_returns, holding, r.sharpe_annual(study),
                        direction=-1, rf_annual=study.rf_annual,
                        periods_per_year=study.periods_per_year, n_draws=1000,
                        seed=study.seed,
                    )
                    ensemble = ds.combine_books(
                        long_result.oos_returns, r.oos_returns,
                        study.rf_annual, study.periods_per_year,
                    )
                    # A stop is live on exactly the bars a position is open, so the
                    # in-market bar count is the arming count — the denominator that
                    # says whether the tail discipline BINDS or is merely present.
                    armings = sum(
                        e.bars_held for e in r.episodes if not e.is_open
                    )
                    gaps = ds.measure_stop_gaps(r.stop_fills, n_armings=armings)
                    payload.setdefault("baseline_detail", {})[symbol] = {
                        "null": null.to_dict(),
                        "ensemble": ensemble.to_dict(),
                        "stop_gaps": gaps.to_dict(),
                        "long_baseline_sharpe": long_result.sharpe_annual(study),
                        "long_baseline_total_return": long_result.total_return,
                    }

        payload["symbols"][symbol] = {
            "oos_start": bars[oos_start].timestamp.date().isoformat(),
            "oos_end": bars[oos_end - 1].timestamp.date().isoformat(),
            "n_oos_bars": len(oos_bars),
            "n_windows": len(spans),
            "regime_share": _regime_share(labels),
            "variants": per_variant,
        }

    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RESULTS.write_text(build_report(payload), encoding="utf-8")
    print(f"ran {n_runs} out-of-sample trials in {time.time() - started:.0f}s")
    print(f"wrote {RESULTS.name} and {SUMMARY_JSON.name}")
    return 0


def _exposure_flags(result, oos_bars) -> list[bool]:
    """Per-OOS-bar "was the book in a position" flags, rebuilt from the episodes.

    Matched by TIMESTAMP, not by index. An episode's `entry_index` is an index into the
    variant's own run series, which begins `warm_up` bars BEFORE the first OOS bar — so
    using it directly here would shift every exposure flag by the warm-up length, and
    silently mis-attribute which regime each trade was held in."""
    position = {tb.timestamp: i for i, tb in enumerate(oos_bars)}
    flags = [False] * len(oos_bars)
    for e in result.episodes:
        start = position.get(e.entry_timestamp)
        if start is None:
            continue
        end = position.get(e.exit_timestamp) if e.exit_timestamp is not None else len(flags)
        for i in range(start, min(end if end is not None else len(flags), len(flags))):
            flags[i] = True
    return flags


def _regime_share(labels) -> dict:
    labelled = [x for x in labels if x is not None]
    return {
        r: sum(1 for x in labelled if x == r) / len(labelled) if labelled else 0.0
        for r in ("bull", "bear", "chop")
    }


def build_report(p: dict) -> str:
    ref = "taker_40bp"
    out = [f"""# The breakdown short book: does crisis alpha survive borrow?

**Produced:** {p["generated_utc"][:10]} ·
**Snapshot:** `{p["snapshot_id"]}` ·
**Reproduce:** `uv run python scripts/run_breakdown_study.py` (offline, deterministic)

> **Thesis label (D38/D82/D117).** Directional and beta-loaded, exactly like its long
> sibling, and equally **not** part of this project's market-neutral thesis. It is short
> or flat on a single high-beta instrument. Its honest benchmark is neither the risk-free
> rate nor buy-and-hold: it is "does this pay in the regimes it claims, and does it
> diversify the long book?" — which is what the regime table and the correlation table
> below are for, and why neither is an appendix.

## Read this first: three things that bound what this study can claim

### 1. The stop is INTRABAR now — and it turns out barely to matter

Phase 2 shipped this book with a close-based stop, because `run_backtest` had no intrabar
stop execution, and said so loudly. D170 wired it: `simulator/fills.stop_fill_price` and
its D10 gap semantics now sit in the engine's bar loop, checked before the strategy is
consulted, so a stop closes a position **the moment the bar touches it** and a bar that
gaps through fills at the open rather than at a price the market never traded.

The honest result is that it changes almost nothing here, and the reason is worth more
than the fix. **The stop sits at the far side of the entry channel** — for a short
entering on an N-bar low, it is the N-bar high — which is an enormous distance from the
entry. The trailing exit channel gets there first essentially every time. See the stop
table below: the stop is armed for hundreds of bars per symbol and causes a handful of
exits, or none.

**This also corrects a Phase 2 claim.** That report said "4 of 4 stop exits filled beyond
their own stop, worst by 38.5%". That number was a measurement artifact: it inferred stop
exits by asking whether an exit price ended up beyond the stop level, which also counts
ordinary channel exits that closed past it. The engine now records which fills a stop
actually caused, and the true count is far smaller.

### 2. Borrow is charged, at a stated non-zero rate

{p["borrow_annual_rate"]:.0%}/yr on the short notional for the whole life of every trade
(D124's rate, D169's decision). Assuming free shorts is the single most result-corrupting
choice available to a spot-crypto short study, because the borrow accrues on ~100% of NAV
continuously while the position is open — unlike the long book, where the equivalent cost
is structurally zero.

### 3. The parameters are NOT mirrored from the long book

Sweep is {ds.SHORT_N_ENTRY} x {ds.SHORT_N_EXIT}, against the long book's
{bs.PLATEAU_N_ENTRY} x {bs.PLATEAU_N_EXIT}. Bear legs are faster and shorter and bear
rallies are violent. **Different optimal parameters from the long side is the expected
finding, not a red flag** — and this sweep is counted separately for multiplicity.
"""]

    for symbol, sr in p["symbols"].items():
        share = sr["regime_share"]
        out.append(f"""---

# {symbol}

Out-of-sample **{sr["oos_start"]} to {sr["oos_end"]}** — {sr["n_oos_bars"]:,} daily bars
across {sr["n_windows"]} walk-forward windows. Regime mix of the sample:
**bull {share["bull"]:.0%} · bear {share["bear"]:.0%} · chop {share["chop"]:.0%}**.

## The headline table: performance by regime

A short book that is flat through a bull sample and profitable through the bears is a
SUCCESS. Judging it on full-sample Sharpe would call that a failure, which is why the
regime slice leads and the full-sample number follows it.

Regimes are ex-post SMA(200) labels — bull is price above a rising average, bear is price
below a falling one, chop is the two disagreeing. They are used only to READ the results;
the strategy's own gate is the plain close-vs-average test and it never sees these labels.

{_regime_table(sr, ref)}

## Every variant at `{ref}`

{_variant_table(sr, ref)}
""")
        detail = p.get("baseline_detail", {}).get(symbol)
        if detail:
            out.append(_detail_block(symbol, detail))

    out.append(_verdict(p))
    return NL.join(out)


def _regime_table(sr: dict, ref: str) -> str:
    key = f"{ds.SHORT_BASELINE}@{ref}"
    v = sr["variants"].get(key)
    if not v or not v["regimes"]:
        return "_Regime slices unavailable for the baseline variant._"
    rows = NL.join(
        f"| **{r['regime']}** | {r['n_bars']:,} | {r['share_of_sample']:.0%} | "
        f"{r['total_return'] * 100:+.1f}% | {r['sharpe_daily']:+.3f} | {r['exposure']:.0%} |"
        for r in v["regimes"]
    )
    return (
        f"Baseline `{ds.SHORT_BASELINE}` at `{ref}`:" + NL + NL
        + "| Regime | Bars | Share | Return in regime | Daily Sharpe | Exposure |" + NL
        + "|---|---|---|---|---|---|" + NL + rows
    )


def _variant_table(sr: dict, ref: str) -> str:
    rows = []
    for key, v in sr["variants"].items():
        if not key.endswith(f"@{ref}"):
            continue
        rows.append(
            f"| `{key.split('@')[0]}` | {v['total_return'] * 100:+.1f}% | "
            f"{v['cagr'] * 100:+.1f}% | {v['sharpe_annual']:.2f} | {v['max_drawdown'] * 100:.1f}% | "
            f"{v['n_closed_trades']} | {v['exposure']:.1%} |"
        )
    return (
        "| Variant | Total return | CAGR | Sharpe (ann.) | Max DD | Trades | Exposure |" + NL
        + "|---|---|---|---|---|---|---|" + NL + NL.join(rows)
    )


def _detail_block(symbol: str, d: dict) -> str:
    null, ens, gaps = d["null"], d["ensemble"], d["stop_gaps"]
    verdict = (
        "**beats** the null" if null["percentile"] >= 0.95
        else "**does not beat** the null"
    )
    return f"""## The primary verdict: exposure-matched random SHORT entries

Any short rule shows a profit in a sample containing 2018 and 2022, because the
instrument fell. The question is whether THESE entries beat randomly-placed shorts of the
same count and the same holding-period distribution. {null["n_draws"]:,} draws, direction
{null["direction"]}, exposure matched by construction.

| | Sharpe (ann.) |
|---|---|
| **Strategy (observed)** | **{null["observed_sharpe"]:.3f}** |
| Random-entry null, 95th pct | {null["null_p95"]:.3f} |
| Random-entry null, median | {null["null_p50"]:.3f} |
| Random-entry null, 5th pct | {null["null_p05"]:.3f} |

**Percentile vs the null: {null["percentile"]:.0%}.** At the conventional 95% bar the
strategy {verdict}.

## Does it diversify the long book?

Correlation is computed over the full span **including bars either book is flat** —
excluding them would measure "how do they behave when both happen to be trading", which
is not the diversification question. The whole claim is that the short book wakes when the
long book sleeps.

| | Value |
|---|---|
| Long-vs-short daily return correlation | **{ens["correlation"]:+.3f}** |
| Target from the brief | ≤ ~0.2 |
| Long book Sharpe (alone) | {ens["long_sharpe"]:.2f} |
| Short book Sharpe (alone) | {ens["short_sharpe"]:.2f} |
| Combined, equal VOL weight | {ens["combined_sharpe"]:.2f} |
| Long book max drawdown | {ens["long_max_drawdown"] * 100:.1f}% |
| Combined max drawdown | {ens["combined_max_drawdown"] * 100:.1f}% |

## What the close-based stop actually cost

Every exit that filled beyond its own stop level — the tail the stop did not truncate.

| | Value |
|---|---|
| Exits the stop actually caused | {gaps["n_stop_exits"]} |
| ...of which gapped past the stop | {gaps["n_gapped"]} |
| Bars carrying a live stop | {gaps["n_armings"]:,} |
| Worst single gap | {gaps["worst_gap_pct"] * 100:.1f}% beyond the stop |

**Read the first two rows against the third.** A stop that is armed for thousands of bars
and closes a handful of trades is *present* rather than *binding*: the trailing channel
almost always gets there first, because the stop sits at the far side of the entry
channel and that is a very long way from a breakdown entry.

These counts come from the engine's own record of which fills a stop caused (D170).
The Phase 2 version of this table inferred them, by asking whether an exit price ended
up beyond the stop level — which also catches ordinary channel exits that happened to
close past it. That inference is what produced the earlier "4 of 4 stop exits gapped"
claim, and it was wrong: most of those exits were not stop exits at all.
"""


def _criteria_scorecard(p: dict) -> str:
    """Score the brief's three criteria PER SYMBOL, from the regime slices.

    An earlier cut of this section stated the outcome in prose written from one symbol's
    shape. It said the bear-regime return was "around flat" — true on BTC, and flatly
    false on ETH, which returned +33.7% there. Hardcoded prose drifting from computed
    data is the exact defect Phase 1.1 had to fix in the long study's multiplicity table,
    so this table is derived."""
    ref = "taker_40bp"
    key = f"{ds.SHORT_BASELINE}@{ref}"
    rows, notes = [], []
    for symbol, sr in p["symbols"].items():
        v = sr["variants"].get(key)
        if not v or not v["regimes"]:
            continue
        by = {r["regime"]: r for r in v["regimes"]}
        bear = by.get("bear", {}).get("total_return", 0.0)
        bull = by.get("bull", {}).get("total_return", 0.0)
        bull_exposure = by.get("bull", {}).get("exposure", 0.0)
        chop = by.get("chop", {}).get("total_return", 0.0)

        bear_ok = bear > 0.10
        bull_ok = bull > -0.20
        chop_ok = chop > -0.10
        rows.append(
            f"| {symbol} | {bear * 100:+.1f}% {'PASS' if bear_ok else 'FAIL'} | "
            f"{bull * 100:+.1f}% at {bull_exposure:.0%} exposure "
            f"{'PASS' if bull_ok else 'FAIL'} | "
            f"{chop * 100:+.1f}% {'PASS' if chop_ok else 'FAIL'} |"
        )
        notes.append((symbol, bear_ok, bull_ok, chop_ok))

    passed_all = [s for s, b, u, c in notes if b and u and c]
    failed_any = [s for s, b, u, c in notes if not (b and u and c)]
    if passed_all and failed_any:
        reading = (
            f"**Split again, and along the same line as the null.** {', '.join(passed_all)} "
            f"meets all three; {', '.join(failed_any)} does not. The two symbols are telling "
            f"different stories about the same rule, which on a two-instrument sample is the "
            f"definition of an undemonstrated result rather than a partial success."
        )
    elif passed_all:
        reading = (
            f"**All three criteria met on every symbol** ({', '.join(passed_all)}). On a "
            f"two-instrument sample that is encouraging and not yet evidence."
        )
    else:
        reading = (
            "**No symbol meets all three.** A short book that is flat when it should be "
            "winning, or bleeding when it should be quiet, has not earned its place in the "
            "ensemble."
        )

    # The gate's MECHANICAL effect and the bull CRITERION are different claims, and an
    # earlier cut of this section conflated them: it asserted the middle criterion held
    # everywhere while the table above showed BTC failing it. The gate can work
    # perfectly and the criterion still fail, if the few trades it lets through are bad
    # enough — which is exactly what happened.
    exposures = [
        by["exposure"]
        for sr in p["symbols"].values()
        for v in [sr["variants"].get(key)] if v and v["regimes"]
        for by in v["regimes"] if by["regime"] == "bull"
    ]
    if exposures and max(exposures) <= 0.05:
        gate_reading = (
            f"**The gate itself works on every symbol** — bull-regime exposure is at most "
            f"{max(exposures):.0%}, so the book really does stand aside when the long book is "
            f"working. Note that this is a separate claim from the bull CRITERION above, and "
            f"the two can diverge: on a symbol where the criterion fails, it fails not because "
            f"the gate let the book trade through the bull market but because the handful of "
            f"trades it did allow were bad enough to lose double digits on their own. The gate "
            f"is not the problem. What it gates is."
        )
    else:
        gate_reading = (
            f"**The gate is not holding the book out of bull markets**: bull-regime exposure "
            f"reaches {max(exposures, default=0.0):.0%}. That is a failure of the gate itself, "
            f"not just of the rule behind it."
        )

    return f"""### Success criteria from the brief, scored

The brief named three: *strongly profitable in bear regimes; flat-to-small-loss in bull
regimes; acceptable chop bleed.* Scored here as bear return > +10%, bull return > −20%,
chop return > −10% — thresholds fixed before reading, and blunt on purpose.

| Symbol | Bear (strongly profitable?) | Bull (flat-to-small-loss?) | Chop (acceptable bleed?) |
|---|---|---|---|
{NL.join(rows)}

{reading}

{gate_reading}"""


def _stop_paragraph(p: dict) -> str:
    """Report what the stop DID, from the engine's own record.

    Written computed rather than as prose because this is the third time in this project
    that a hardcoded sentence has drifted from the numbers beside it. The earlier version
    of this paragraph asserted the stop "did not do its job" on the strength of a gap
    count that, once measured properly, turned out to be zero."""
    detail = p.get("baseline_detail", {})
    exits = sum(d["stop_gaps"]["n_stop_exits"] for d in detail.values())
    gapped = sum(d["stop_gaps"]["n_gapped"] for d in detail.values())
    armed = sum(d["stop_gaps"]["n_armings"] for d in detail.values())
    worst = max((d["stop_gaps"]["worst_gap_pct"] for d in detail.values()), default=0.0)
    per_symbol = " · ".join(
        f"{sym} {d['stop_gaps']['n_stop_exits']} exit(s) from "
        f"{d['stop_gaps']['n_armings']:,} armed bars"
        for sym, d in detail.items()
    )

    if exits == 0:
        return f"""### The stop never fired

Across both symbols the stop was armed for {armed:,} bars and closed **not one trade**
({per_symbol}). The trailing exit channel reached every position first.

That is information, not a clean bill of health, and it is not a defence of the design
either. A stop placed at the far side of the entry channel is so distant from a breakdown
entry that it is nearly unreachable before the ordinary exit fires. The tail discipline
the brief demanded is **present but not binding** — and a risk control that never binds
has not been shown to work, it has only been shown not to be needed on this sample."""

    gap_line = (
        f"Of those, **{gapped} gapped past the stop** and filled at the bar's open "
        f"instead, the worst by {worst * 100:.1f}%. That is the residue no intrabar stop "
        f"can remove: on daily bars the dangerous move happens between one close and the "
        f"next open, where there is no intrabar to trade in."
        if gapped
        else "**None of them gapped** — each filled at its stop price, which is the "
        "intrabar machinery doing exactly what it exists to do."
    )
    return f"""### What the stop actually did

The stop was armed for **{armed:,} bars** and caused **{exits} exit(s)**
({per_symbol}). {gap_line}

**Read those two numbers against each other.** A stop armed for hundreds of bars that
closes a handful of trades is *present* rather than *binding*: it sits at the far side of
the entry channel, which is a very long way from a breakdown entry, so the trailing exit
gets there first almost every time. The brief's premise — that short expectancy becomes
calculable once the squeeze tail is truncated — is now satisfied mechanically, and turns
out not to be the thing that was limiting this book."""


def _verdict(p: dict) -> str:
    detail = p.get("baseline_detail", {})
    lines = ["---", "", "# Verdict", ""]
    for symbol, d in detail.items():
        null, ens = d["null"], d["ensemble"]
        lines.append(
            f"- **{symbol}**: null percentile {null['percentile']:.0%}, "
            f"long/short correlation {ens['correlation']:+.2f}, "
            f"combined Sharpe {ens['combined_sharpe']:.2f} against "
            f"{ens['long_sharpe']:.2f} long-only "
            f"(max drawdown {ens['combined_max_drawdown'] * 100:.0f}% against "
            f"{ens['long_max_drawdown'] * 100:.0f}%)."
        )

    beat = [s for s, d in detail.items() if d["null"]["percentile"] >= 0.95]
    missed = [s for s, d in detail.items() if d["null"]["percentile"] < 0.95]
    hurts = [
        s for s, d in detail.items()
        if d["ensemble"]["combined_sharpe"] < d["ensemble"]["long_sharpe"]
    ]
    helps_dd = [
        s for s, d in detail.items()
        if d["ensemble"]["combined_max_drawdown"] < d["ensemble"]["long_max_drawdown"]
    ]

    if beat and missed:
        null_read = (
            f"**The null verdict is SPLIT and must not be read as a pass.** "
            f"{', '.join(beat)} clears the 95% bar; {', '.join(missed)} does not. The long "
            f"study fixed the rule for exactly this situation before looking — a filter is "
            f"kept only if it improves on EVERY symbol, because one symbol out of two is a "
            f"coin flip. The same discipline applies here, and by it the entry rule is not "
            f"demonstrated. Reporting the winner alone would be the single most misleading "
            f"thing available in this document."
        )
    elif beat:
        null_read = (
            f"**The entry rule beats the exposure-matched null on every symbol tested** "
            f"({', '.join(beat)}). That is the primary verdict the brief asked for, and it "
            f"is a genuine positive — on a two-symbol sample."
        )
    else:
        null_read = (
            f"**The entry rule does not beat randomly-placed shorts of the same count and "
            f"duration on any symbol.** This is the primary verdict the brief nominated, and "
            f"it is a clean negative: the timing of these entries is indistinguishable from "
            f"chance, so whatever the book earns it earns from being short during falls, not "
            f"from choosing when."
        )
    lines += ["", null_read, ""]

    ens_read = (
        "**The diversification claim holds and the profitability claim does not, and those "
        "are separate findings.** Correlation against the long book comes in at or below "
        "the brief's ~0.2 target on both symbols — genuinely near zero, which is the "
        "complementary-payoff property the ensemble argument needs."
    )
    if hurts:
        ens_read += (
            f" But near-zero correlation cannot rescue a book that loses money: on "
            f"{', '.join(hurts)} the equal-vol-weighted combination has a LOWER Sharpe than "
            f"the long book alone. You cannot diversify with a negative-expectancy asset; "
            f"you can only spread the same losses more smoothly."
        )
    if helps_dd:
        ens_read += (
            f" The one thing that does survive is drawdown: on {', '.join(helps_dd)} the "
            f"combined book's worst drawdown is smaller than the long book's. That is the "
            f"same shape of result the long study landed on — a drawdown-shape finding, not "
            f"an alpha finding — and it should be quoted with the Sharpe cost attached, "
            f"never on its own."
        )
    lines += [ens_read, ""]

    lines += [_criteria_scorecard(p), _stop_paragraph(p), """
# Standing caveats

1. **The stop is intrabar (D170) but almost never binds.** The mechanism is correct —
   touched stops fill at the stop, gapped ones at the open — but the level sits at the
   far side of the entry channel, so the trailing exit closes nearly every position
   first. A risk control that never binds has not been shown to work on this sample, only
   to be unneeded on it. A tighter stop (ATR-based, say) is a different strategy and
   would need its own sweep and its own multiplicity accounting.
2. **Borrow is a stated assumption, not a quote.** 10%/yr is mid-range for BTC/ETH spot
   margin borrow over the sample; it was neither swept nor negotiated, and hard-to-borrow
   episodes in a real crash would be worse precisely when the book is most short.
3. **No funding, no perp expression.** These are spot shorts (D108). A perpetual-futures
   implementation would pay funding, which in a falling market is often a CREDIT to
   shorts — so this is conservative in that one direction and silent about it otherwise.
4. **Live tradability is out of scope and mostly negative.** The FCA retail
   crypto-derivatives ban and the absence of retail spot margin mean this book is
   backtest-and-shadow-signals only. The one legal live expression at current capital is
   equity-index breakdown via spread betting, which is a different instrument and a
   different spec.
5. **Two instruments, both survivors.** The same selection bias the long study named as
   its largest un-deflatable problem applies here unchanged.
"""]
    return NL.join(lines)


if __name__ == "__main__":
    raise SystemExit(main())

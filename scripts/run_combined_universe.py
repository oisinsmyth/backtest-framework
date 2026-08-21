"""The long+short combined book on the D140 universe — the baseline nobody has measured.
(D182)

D172 combined the two books on BTC/ETH and found the combination has a **lower** Sharpe
than the long book alone but a **smaller** drawdown. That is a two-instrument finding, and
D180 has just shown what two-instrument findings are worth here: E1 passed five times on
BTC/ETH and failed on sixty-two coins, because those two sit at the 97th and 85th
percentile of the variable that decided the outcome.

So this measures the combined book across the whole cross-section, with no rule attached.
It is the prerequisite for reading any rule-level combined result — testing an improvement
against an unmeasured baseline is the mistake D179 made by landing as a headline before the
universe test that undercut it.

    uv run python scripts/run_combined_universe.py

Per-symbol construction: each coin's own long and short series are combined into one book,
which is the direct analogue of D179 and reuses `ds.combine_books` unchanged. This is NOT a
portfolio — there is no cross-sectional capital allocation here, and the two legs remain
entirely separate backtests that are blended after the fact.

Weights are EXPANDING-window inverse-vol (D181). The whole-sample weighting this replaced
would have been inherited sixty-two times over.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research import breakdown_study as ds
from backtest_framework.research import breakout_study as bs
from backtest_framework.research import breakout_universe as bu

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.csv.gz"
META = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.meta.json"
EVENTS = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw_events.json"
REGISTRY_PATH = REPO / "data" / "combined_universe_registry.sqlite"
RESULTS = REPO / "docs" / "results" / "combined_universe.md"
SUMMARY_JSON = REPO / "data" / "combined_universe_summary.json"

REF_TIER = bs.REFERENCE_TIER
NL = "\n"


def long_variant() -> bs.Variant:
    """The published long baseline, reused rather than re-derived (D141)."""
    return bu.baseline_variant()


def short_variant() -> bs.Variant:
    """The published short baseline: 20/5, SMA200 regime gate, inverse-vol sizing, and the
    `channel_stop` that `BreakoutStrategy` refuses to build a short without."""
    return bs.Variant(
        "short_baseline",
        "plateau",
        fixed_config=ds.short_config(ds.SHORT_BASELINE_N_ENTRY, ds.SHORT_BASELINE_N_EXIT),
    )


ARMS = {"long": long_variant, "short": short_variant}


def main() -> int:
    # Re-render from the payload on disk rather than re-running two walk-forwards over 62
    # symbols. A report that can only be produced by a full recompute is a report nobody
    # checks.
    if "--report-only" in sys.argv:
        payload = json.loads(SUMMARY_JSON.read_text(encoding="utf-8"))
        RESULTS.write_text(build_report(payload), encoding="utf-8")
        print(f"re-rendered {RESULTS.name} from {SUMMARY_JSON.name}")
        return 0

    started = time.time()
    raw_bars, raw_volumes = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, cleaning_report = clean(raw_bars)
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(
        cleaned,
        # The events file, rather than an empty corporate-actions object (D184). The file
        # is empty today, so this moves no number — it closes the silent failure for
        # the day it is not.
        load_events_json(EVENTS),
        volumes_by_symbol=raw_volumes,
        cleaning_report=cleaning_report,
        validation=None,
        extra_meta={"source_fixture": FIXTURE.name, "study": "combined_universe_v1"},
    )
    snapshot = store.load(snapshot_id)
    cohorts = json.loads(META.read_text(encoding="utf-8"))["cohort_by_symbol"]

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()
    registry = TrialRegistry(REGISTRY_PATH)
    study = bs.BreakoutStudyConfig()

    results: dict[str, Any] = {}
    for arm, make in ARMS.items():
        print(f"running {arm} baseline across the universe ...", flush=True)
        results[arm] = bu.run_universe_study(
            snapshot.bars_by_symbol,
            snapshot.volumes_by_symbol,
            registry,
            snapshot_id,
            cohorts=cohorts,
            study=study,
            tiers=bs.SHORT_TIERS if arm == "short" else bs.DEFAULT_TIERS,
            trial_id_prefix=f"combined-universe-{arm}",
            variant=make(),
            progress=lambda m: None,
        )

    payload = build_payload(results, cohorts, snapshot_id, study)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RESULTS.write_text(build_report(payload), encoding="utf-8")
    print(
        f"combined {len(payload['per_symbol'])} symbols in {time.time() - started:.0f}s"
    )
    print(f"wrote {RESULTS.name} and {SUMMARY_JSON.name}")
    return 0


def _total_return(returns: list[float]) -> float:
    nav = 1.0
    for r in returns:
        nav *= 1.0 + r
    return nav - 1.0


def build_payload(results, cohorts, snapshot_id, study) -> dict:
    per_symbol = {}
    skipped: dict[str, str] = {}
    for symbol, run in results["long"].runs.items():
        other = results["short"].runs.get(symbol)
        if other is None:
            skipped[symbol] = "no short-book run"
            continue
        lv = run.by_tier[REF_TIER].variant
        sv = other.by_tier[REF_TIER].variant
        try:
            ens = ds.combine_books(
                lv.oos_returns, sv.oos_returns, study.rf_annual, study.periods_per_year
            )
            series = ds.combined_series(lv.oos_returns, sv.oos_returns)
        except ValueError as exc:
            # A symbol with too little out-of-sample history to clear the warm-up is
            # EXCLUDED and named, not silently dropped and not back-filled with
            # whole-sample weights, which is the bug D181 removed.
            skipped[symbol] = str(exc).split(" — ")[0]
            continue
        w = ds.ENSEMBLE_MIN_BARS
        per_symbol[symbol] = {
            "status": run.status,
            "source_cohort": cohorts.get(symbol, "unknown"),
            "n_bars": ens.n_bars,
            "n_fallback_bars": ens.n_fallback_bars,
            "mean_long_weight": ens.mean_long_weight,
            "correlation": ens.correlation,
            "long_sharpe": ens.long_sharpe,
            "short_sharpe": ens.short_sharpe,
            "combined_sharpe": ens.combined_sharpe,
            "long_maxdd": ens.long_max_drawdown,
            "short_maxdd": ens.short_max_drawdown,
            "combined_maxdd": ens.combined_max_drawdown,
            # Total returns are recomputed over the SAME post-warm-up span the Sharpes use.
            # `VariantResult.total_return` covers the full series and would be quietly
            # measuring a different period than everything beside it.
            "long_return": _total_return(list(lv.oos_returns[w:])),
            "short_return": _total_return(list(sv.oos_returns[w:])),
            "combined_return": _total_return(series),
            "long_trades": lv.diagnostics.n_closed_trades,
            "short_trades": sv.diagnostics.n_closed_trades,
            "d_sharpe_vs_long": ens.combined_sharpe - ens.long_sharpe,
            "d_maxdd_vs_long": ens.combined_max_drawdown - ens.long_max_drawdown,
        }
    return {
        "snapshot_id": snapshot_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "reference_tier": REF_TIER,
        "min_bars": ds.ENSEMBLE_MIN_BARS,
        "borrow_annual_rate": bs.SHORT_BORROW_ANNUAL_RATE,
        "skipped": skipped,
        "per_symbol": per_symbol,
        "cohort_summary": cohort_summary(per_symbol),
    }


def cohort_summary(per_symbol: dict) -> dict:
    out = {}
    groups: dict[str, list] = {"ALL": list(per_symbol.values())}
    for row in per_symbol.values():
        groups.setdefault(row["status"], []).append(row)
    for name, rows in groups.items():
        if not rows:
            continue
        sh = [r["d_sharpe_vs_long"] for r in rows]
        dd = [r["d_maxdd_vs_long"] for r in rows]
        out[name] = {
            "n": len(rows),
            # "Beats the long book alone" is the question; a tie is not a win.
            "sharpe_wins": sum(1 for d in sh if d > 0),
            "sharpe_win_rate": sum(1 for d in sh if d > 0) / len(sh),
            "mean_d_sharpe": statistics.fmean(sh),
            "median_d_sharpe": statistics.median(sh),
            "dd_wins": sum(1 for d in dd if d < 0),  # a SMALLER drawdown is the win
            "dd_win_rate": sum(1 for d in dd if d < 0) / len(dd),
            "mean_d_maxdd": statistics.fmean(dd),
            "median_d_maxdd": statistics.median(dd),
            "mean_correlation": statistics.fmean([r["correlation"] for r in rows]),
            "median_correlation": statistics.median([r["correlation"] for r in rows]),
        }
    return out


def build_report(p: dict) -> str:
    cs = p["cohort_summary"]
    rows = NL.join(
        f"| {name} | {v['n']} | {v['sharpe_win_rate']:.0%} | {v['mean_d_sharpe']:+.3f} | "
        f"{v['median_d_sharpe']:+.3f} | {v['dd_win_rate']:.0%} | "
        f"{v['mean_d_maxdd'] * 100:+.1f} pp | {v['median_d_maxdd'] * 100:+.1f} pp |"
        for name, v in sorted(cs.items(), key=lambda kv: (kv[0] != "ALL", kv[0]))
    )
    return f"""# The combined long+short book on 62 coins

**Produced:** {p["generated_utc"][:10]} ·
**Snapshot:** `{p["snapshot_id"]}` ·
**Reproduce:** `uv run python scripts/run_combined_universe.py` (offline, deterministic)

## What this is

D172 combined the two books on BTC/ETH and found the combination has a **lower Sharpe than
the long book alone** but a **smaller drawdown**. That is a two-instrument finding, and
D180 has just shown what those are worth here: E1 cleared its bar five times on BTC/ETH and
failed on sixty-two coins.

This measures the combined book across the whole D140 cross-section with **no rule
attached** — the baseline that has to exist before any rule-level combined result can be
read. Both baselines already exist and are already in their pools, so **no multiplicity is
added**; the long arm reuses `breakout_universe.baseline_variant()` directly.

**Per-symbol, not portfolio.** Each coin's own long and short series are combined into one
book. There is no cross-sectional capital allocation here and the two legs remain separate
backtests blended after the fact.

**Weights are expanding-window inverse-vol** — every return from the start of the
out-of-sample period up to the previous bar (D181/D44). The first {p["min_bars"]} bars of
every symbol are warm-up and are excluded from every figure below, legs included, so all
three arms are quoted over the same span. A fixed window was tried first and abandoned:
the short book is flat on ~85% of bars, so a 63-bar window was entirely flat 75% of the
time and fell back to equal weight.

Reference tier `{p["reference_tier"]}`; the short leg pays borrow at
{p["borrow_annual_rate"]:.0%}/yr.

## Does combining beat the long book alone?

A win in the Sharpe columns means the combination scored higher. A win in the drawdown
columns means it drew down **less**. D172's BTC/ETH finding was that these two disagree.

| Cohort | Symbols | Sharpe win rate | Mean Δ Sharpe | Median Δ | DD win rate | Mean Δ max DD | Median Δ |
|---|---|---|---|---|---|---|---|
{rows}

{_verdict(p)}

{_absolute_table(p)}

{_correlation_block(p)}

{_samples(p)}

{_skipped_block(p)}

<details><summary>Every symbol</summary>

| Symbol | Status | Long Sharpe | Short Sharpe | Combined | Δ vs long | Long DD | Combined DD | Corr |
|---|---|---|---|---|---|---|---|---|
{_symbol_rows(p)}

</details>

## Standing caveats

1. **This is not a portfolio result.** Per-symbol combination answers "does pairing this
   coin's two books help?", not "does a long/short book across 62 coins work?". The second
   needs cross-sectional capital allocation that does not exist in this framework yet.
2. **Neither leg has a demonstrated edge.** The long book's DSR sits near 1.0 only because
   its plateau is flat; the short book's is 0.04-0.538. Combining two books does not create
   an edge that neither has.
3. **No margin call, no liquidation, no borrow recall (D175).** Short accounts in this
   universe have passed -100% and kept trading.
4. **The cross-section is not independent.** These coins move together, so 62 symbols is
   far fewer than 62 independent tests.
5. **Borrow at a flat {p["borrow_annual_rate"]:.0%}/yr is generous** for small-cap alts,
   and the optimism is largest exactly where the short leg looks most attractive.
"""


def _verdict(p: dict) -> str:
    v = p["cohort_summary"]["ALL"]
    cohorts = {k: x for k, x in p["cohort_summary"].items() if k != "ALL"}
    sh_up = v["sharpe_win_rate"] > 0.5
    dd_up = v["dd_win_rate"] > 0.5
    split = [k for k, x in cohorts.items() if (x["sharpe_win_rate"] > 0.5) != sh_up]
    if not sh_up and dd_up:
        head = (
            f"**D172's finding holds on the cross-section.** The combination scores a LOWER "
            f"Sharpe than the long book alone on {100 - v['sharpe_win_rate'] * 100:.0f}% of "
            f"coins (mean Δ {v['mean_d_sharpe']:+.3f}) while drawing down LESS on "
            f"{v['dd_win_rate']:.0%} (mean Δ {v['mean_d_maxdd'] * 100:+.1f} pp). You cannot "
            f"diversify with a negative-expectancy asset; you can only spread the same "
            f"losses more smoothly. The drawdown gain is real and it is bought with return."
        )
    elif sh_up and dd_up:
        head = (
            f"**The combination beats the long book on both counts**, on "
            f"{v['sharpe_win_rate']:.0%} of coins by Sharpe (mean {v['mean_d_sharpe']:+.3f}) "
            f"and {v['dd_win_rate']:.0%} by drawdown. That is a stronger result than D172 "
            f"found on BTC/ETH, so the first question is what the short leg is contributing "
            f"here that it did not there — not whether to adopt it."
        )
    elif sh_up:
        head = (
            f"**Sharpe improves and drawdown does not**, which is the reverse of D172's "
            f"BTC/ETH finding: {v['sharpe_win_rate']:.0%} of coins score higher combined "
            f"while only {v['dd_win_rate']:.0%} draw down less."
        )
    else:
        head = (
            f"**Combining loses on both counts.** Lower Sharpe on "
            f"{100 - v['sharpe_win_rate'] * 100:.0f}% of coins and no drawdown compensation "
            f"({v['dd_win_rate']:.0%} improve). D172's drawdown consolation does not survive "
            f"the cross-section, and the combined book has nothing left to recommend it."
        )
    if split:
        head += (
            f" The Sharpe direction flips in {', '.join(sorted(split))}, so the cohort "
            f"split is doing work here and the ALL row should not be quoted alone."
        )
    return head


def _absolute_table(p: dict) -> str:
    rows = p["per_symbol"]
    blown = {
        s: r
        for s, r in rows.items()
        if min(r["long_return"], r["short_return"], r["combined_return"]) <= -1.0
    }
    kept = {s: r for s, r in rows.items() if s not in blown}
    lines = []
    for arm in ("long", "short", "combined"):
        allr = [r[f"{arm}_return"] for r in rows.values()]
        exr = [r[f"{arm}_return"] for r in kept.values()]
        sh = [r[f"{arm}_sharpe"] for r in rows.values()]
        dd = [r[f"{arm}_maxdd"] for r in rows.values()]
        lines.append(
            f"| `{arm}` | {statistics.median(allr) * 100:+.1f}% | "
            f"{statistics.fmean(exr) * 100:+.1f}% | {statistics.fmean(sh):+.3f} | "
            f"{statistics.fmean(dd) * 100:.1f}% | "
            f"{sum(1 for x in allr if x > 0)} / {len(allr)} |"
        )
    note = (
        f"{len(blown)} symbol(s) lost more than the entire account in some arm "
        f"(`{'`, `'.join(sorted(blown))}`), so the mean column excludes them."
        if blown
        else "No symbol drove total return past -100% in any arm."
    )
    return f"""## Is any arm worth running?

The win rates above are RELATIVE — they say whether combining helps, not whether the result
is worth having. This says the second thing, over the same post-warm-up span.

| Arm | Median total return | Mean, ex blow-ups | Mean Sharpe | Mean max DD | Profitable symbols |
|---|---|---|---|---|---|
{NL.join(lines)}

**The median is the headline and the mean is not** — a cross-section of alts has a return
distribution with a tail that eats any average. {note}"""


def _correlation_block(p: dict) -> str:
    """D172's near-zero long/short correlation is a two-symbol claim. On a cross-section it
    is a distribution, and the spread is the part that decides whether the diversification
    argument generalises."""
    cs = p["cohort_summary"]["ALL"]
    cors = sorted(r["correlation"] for r in p["per_symbol"].values())
    n = len(cors)
    pct = lambda q: cors[min(int(q * n), n - 1)]
    near_zero = sum(1 for c in cors if abs(c) <= 0.2)
    fallback = sum(r["n_fallback_bars"] for r in p["per_symbol"].values())
    total = sum(r["n_bars"] for r in p["per_symbol"].values())
    return f"""## The diversification claim, as a distribution

`BREAKDOWN_SHORT_STRATEGY.md` sets a ~0.2 correlation target and D172 reported the two
books clearing it on BTC and ETH. Across 62 coins it is a distribution, not a number:

| p05 | p25 | median | p75 | p95 | mean | within ±0.2 |
|---|---|---|---|---|---|---|
| {pct(0.05):+.3f} | {pct(0.25):+.3f} | {cs["median_correlation"]:+.3f} | {pct(0.75):+.3f} | {pct(0.95):+.3f} | {cs["mean_correlation"]:+.3f} | {near_zero}/{n} |

Low correlation is the precondition for the diversification argument, not the argument
itself — two books can be uncorrelated and still combine into something worse than the
better one, which is what the Sharpe column above measures.

## How the risk budget actually splits

{_weight_note(p)}

**Degenerate weighting:** {fallback:,} of {total:,} scored bars ({fallback / total:.1%})
fell back to 50/50 because one leg was flat for its entire history to that point."""


def _weight_note(p: dict) -> str:
    """The known flaw in equal-vol weighting, surfaced so it cannot be read past (D181).

    Inverse-vol reads a flat book as low-risk when what it actually is, is absent. The
    short book is regime-gated and sits out most bars, so the construction hands it a
    LARGER share of the risk budget the less it trades."""
    ws = sorted(r["mean_long_weight"] for r in p["per_symbol"].values())
    n = len(ws)
    minority = sum(1 for w in ws if w < 0.5)
    return (
        f"Average share of the combined book carried by the LONG leg: median "
        f"**{statistics.median(ws):.3f}**, range {ws[0]:.3f}-{ws[-1]:.3f}. The long leg "
        f"holds a MINORITY of the risk budget on **{minority} of {n}** symbols."
        + NL + NL
        + f"That is a known flaw in the equal-vol construction, not a property of these "
        f"coins (D181). Inverse-vol weighting reads a flat book as low-risk, when what it "
        f"actually is, is absent — and the short book is regime-gated, so the less it "
        f"trades the more of the risk budget it is handed. Every combined figure in this "
        f"document inherits that, and it is reported here rather than left to be "
        f"discovered."
    )


def _samples(p: dict, k: int = 5) -> str:
    ranked = sorted(p["per_symbol"].items(), key=lambda kv: -kv[1]["d_sharpe_vs_long"])
    picks = ranked[:k] + ([("...", None)] if len(ranked) > 2 * k else []) + ranked[-k:]
    lines = []
    for sym, r in picks:
        if r is None:
            lines.append("| … | | | | | |")
            continue
        lines.append(
            f"| `{sym}` | {r['status']} | {r['long_return'] * 100:+,.1f}% | "
            f"{r['combined_return'] * 100:+,.1f}% | {r['d_sharpe_vs_long']:+.3f} | "
            f"{r['d_maxdd_vs_long'] * 100:+.1f} pp |"
        )
    return f"""## Sample symbols — the {k} best and {k} worst

Ranked by Δ Sharpe against the long book alone, shown in total return so the size is
legible.

| Symbol | Status | Long return | Combined return | Δ Sharpe | Δ max DD |
|---|---|---|---|---|---|
{NL.join(lines)}"""


def _skipped_block(p: dict) -> str:
    skipped = p.get("skipped") or {}
    if not skipped:
        return (
            "**Every admitted symbol was combined.** None had too little out-of-sample "
            "history to weight on the trailing window."
        )
    rows = NL.join(f"| `{s}` | {why} |" for s, why in sorted(skipped.items()))
    return f"""## {len(skipped)} symbol(s) excluded

Named rather than silently dropped, and excluded rather than back-filled with whole-sample
weights — the back-fill is the bug D181 removed.

| Symbol | Reason |
|---|---|
{rows}"""


def _symbol_rows(p: dict) -> str:
    return NL.join(
        f"| `{sym}` | {r['status']} | {r['long_sharpe']:+.2f} | {r['short_sharpe']:+.2f} | "
        f"{r['combined_sharpe']:+.2f} | **{r['d_sharpe_vs_long']:+.3f}** | "
        f"{r['long_maxdd'] * 100:.0f}% | {r['combined_maxdd'] * 100:.0f}% | "
        f"{r['correlation']:+.2f} |"
        for sym, r in sorted(
            p["per_symbol"].items(), key=lambda kv: -kv[1]["d_sharpe_vs_long"]
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())

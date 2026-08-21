"""Out-of-sample test of ONE rule on coins it was not fitted on: does E1 improve the book?
(D180)

`FailedBreakoutExit(k)` — E1 — has now cleared the every-symbol bar five times: the long
book at k=2 and k=3 (D177), the short book at k=2 and k=3 (D178), and the combined
long+short ensemble at k=3 with both bootstrap intervals excluding zero (D179). That is
the strongest record any rule in this project has.

Every one of those passes is on **BTC-USD and ETH-USD**. Five correlated passes on two
instruments are not five independent tests, and D178/D179 both named the same next step:
E1 versus no-E1 on the D140 universe, one configuration each, on a cross-section that was
mechanically screened to CONTAIN the coins that failed.

    uv run python scripts/run_e1_universe.py

**Both books are run**, because E1's distinctive claim is that it is direction-agnostic by
construction, and testing one side would leave exactly that claim untested. Two fixed
configurations per book, k=3 throughout (D179's choice, made before this run and not
revisited here). Nothing is tuned. This is not a sweep.
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
from backtest_framework.data.corporate_actions import CorporateActions
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research import breakdown_study as ds
from backtest_framework.research import breakout_study as bs
from backtest_framework.research import breakout_universe as bu

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.csv.gz"
META = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.meta.json"
REGISTRY_PATH = REPO / "data" / "e1_universe_registry.sqlite"
RESULTS = REPO / "docs" / "results" / "e1_universe.md"
SUMMARY_JSON = REPO / "data" / "e1_universe_summary.json"

REF_TIER = bs.REFERENCE_TIER
NL = "\n"

E1_K = 3
"""Fixed at k=3 before this run, on D179's stated grounds: it was the stronger k on BOTH
books in D178, so it is the consistent choice rather than one picked per side. Running
both k here would turn a single out-of-sample test into a two-configuration search on the
universe, which is the specific thing D141 exists to prevent."""


def _long_config(with_e1: bool) -> dict[str, Any]:
    """The long book's published baseline, plus E1 and nothing else."""
    rules: list[dict[str, Any]] = (
        [{"type": "failed_breakout", "k": E1_K}] if with_e1 else []
    )
    return bs.breakout_config(
        n_entry=bs.BASELINE_N_ENTRY, n_exit=bs.BASELINE_N_EXIT, exit_rules=rules
    )


def _short_config(with_e1: bool) -> dict[str, Any]:
    """The short book's baseline, plus E1 and nothing else.

    E1 is NOT a stop — it bounds duration inside a k-bar window, it does not bound loss —
    so on a short it rides alongside the incumbent `channel_stop` that the baseline also
    carries and that `BreakoutStrategy` refuses to construct a short without. The delta
    therefore prices E1 alone, exactly as it did in D178."""
    rules: list[dict[str, Any]] = [{"type": "channel_stop"}]
    if with_e1:
        rules.append({"type": "failed_breakout", "k": E1_K})
    return bs.breakout_config(
        n_entry=ds.SHORT_BASELINE_N_ENTRY,
        n_exit=ds.SHORT_BASELINE_N_EXIT,
        weight_source=ds.SHORT_INVERSE_VOL,
        filters=[
            {"type": "trend_gate", "sma_window": ds.SMA_GATE_WINDOW, "direction": "short"}
        ],
        direction="short",
        exit_rules=rules,
    )


BOOKS: dict[str, dict[str, Any]] = {
    "long": {"config": _long_config, "tiers": bs.DEFAULT_TIERS},
    "short": {"config": _short_config, "tiers": bs.SHORT_TIERS},
}
"""Both books, because E1's claim is that it is direction-agnostic. Two configurations
each — baseline and baseline+E1 — fixed before they meet this universe (D141)."""


def variant_for(book: str, with_e1: bool) -> bs.Variant:
    label = "e1" if with_e1 else "base"
    return bs.Variant(
        f"{book}_{label}", "exit", fixed_config=BOOKS[book]["config"](with_e1)
    )


def main() -> int:
    # Re-render the report from the payload already on disk, without re-running four
    # walk-forwards over 62 symbols. The payload is the study's whole output, so a
    # reporting change never needs a recompute — and a report that can only be produced
    # by a 40-minute run is a report nobody checks.
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
        CorporateActions(),
        volumes_by_symbol=raw_volumes,
        cleaning_report=cleaning_report,
        validation=None,
        extra_meta={"source_fixture": FIXTURE.name, "study": "e1_universe_v1"},
    )
    snapshot = store.load(snapshot_id)
    cohorts = json.loads(META.read_text(encoding="utf-8"))["cohort_by_symbol"]

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()
    registry = TrialRegistry(REGISTRY_PATH)
    study = bs.BreakoutStudyConfig()

    results: dict[str, dict[str, Any]] = {}
    for book, spec in BOOKS.items():
        results[book] = {}
        for with_e1 in (False, True):
            label = "e1" if with_e1 else "base"
            print(f"running {book}/{label} across the universe ...", flush=True)
            results[book][label] = bu.run_universe_study(
                snapshot.bars_by_symbol,
                snapshot.volumes_by_symbol,
                registry,
                snapshot_id,
                cohorts=cohorts,
                study=study,
                tiers=spec["tiers"],
                trial_id_prefix=f"e1-universe-{book}-{label}",
                variant=variant_for(book, with_e1),
                progress=lambda m: None,
            )

    payload = build_payload(results, cohorts, snapshot_id, study)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RESULTS.write_text(build_report(payload), encoding="utf-8")
    n = len(payload["books"]["long"]["per_symbol"])
    print(
        f"compared 2 configurations on 2 books across {n} symbols in "
        f"{time.time() - started:.0f}s"
    )
    print(f"wrote {RESULTS.name} and {SUMMARY_JSON.name}")
    return 0


def build_payload(results, cohorts, snapshot_id, study) -> dict:
    books = {}
    for book in BOOKS:
        per_symbol = {}
        for symbol, run in results[book]["e1"].runs.items():
            base = results[book]["base"].runs.get(symbol)
            if base is None:
                continue
            b, e = base.by_tier[REF_TIER].variant, run.by_tier[REF_TIER].variant
            per_symbol[symbol] = {
                "status": run.status,
                "source_cohort": cohorts.get(symbol, "unknown"),
                "base_sharpe": b.sharpe_annual(study),
                "e1_sharpe": e.sharpe_annual(study),
                "delta": e.sharpe_annual(study) - b.sharpe_annual(study),
                "base_return": b.total_return,
                "e1_return": e.total_return,
                "base_maxdd": b.max_drawdown,
                "e1_maxdd": e.max_drawdown,
                "base_trades": b.diagnostics.n_closed_trades,
                "e1_trades": e.diagnostics.n_closed_trades,
                # E1 is an ADDED brick, not a swapped one, so on a symbol where it never
                # fires the two runs are the same run and the delta is exactly zero. That
                # is a tie, not a loss: counting it as a loss would understate the rule
                # and counting it as a win would inflate it. D174's comparison never faced
                # this, because two different stops always differ.
                "fired": e.total_return != b.total_return,
                # CAGR is undefined past -100%: (1+r) is negative and a fractional power
                # of a negative number is not a real rate. A short book CAN pass -100%
                # here because the engine models no margin call (D175). None, never nan.
                "base_cagr": _safe_cagr(b, study),
                "e1_cagr": _safe_cagr(e, study),
            }
        books[book] = {
            "per_symbol": per_symbol,
            "cohort_summary": cohort_summary(per_symbol),
        }
    return {
        "snapshot_id": snapshot_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "reference_tier": REF_TIER,
        "e1_k": E1_K,
        "borrow_annual_rate": bs.SHORT_BORROW_ANNUAL_RATE,
        "books": books,
    }


def _safe_cagr(variant, study):
    if variant.total_return <= -1.0:
        return None
    return bs.cagr(variant.total_return, variant.n_oos_bars, study.periods_per_year)


def cohort_summary(per_symbol: dict) -> dict:
    """Win rates computed over the symbols where E1 ACTUALLY FIRED.

    Both denominators are reported. A rule that never fires on half the cross-section is
    telling you something real about its reach, and a win rate that silently counts those
    symbols as losses is telling you something false about its quality."""
    out = {}
    groups: dict[str, list] = {"ALL": list(per_symbol.values())}
    for row in per_symbol.values():
        groups.setdefault(row["status"], []).append(row)
    for name, rows in groups.items():
        active = [r for r in rows if r["fired"]]
        deltas = [r["delta"] for r in active]
        wins = sum(1 for d in deltas if d > 0)
        losses = sum(1 for d in deltas if d < 0)
        out[name] = {
            "n": len(rows),
            "n_fired": len(active),
            "wins": wins,
            "losses": losses,
            "win_rate": wins / len(active) if active else 0.0,
            "mean_delta": statistics.fmean(deltas) if deltas else 0.0,
            "median_delta": statistics.median(deltas) if deltas else 0.0,
        }
    return out


def build_report(p: dict) -> str:
    sections = NL.join(_book_section(p, book) for book in BOOKS)
    return f"""# E1 on 62 coins it was never fitted on

**Produced:** {p["generated_utc"][:10]} ·
**Snapshot:** `{p["snapshot_id"]}` ·
**Reproduce:** `uv run python scripts/run_e1_universe.py` (offline, deterministic)

## What this is

`FailedBreakoutExit(k)` — E1 — exits when the close falls back INSIDE the channel the
entry broke, within k bars. It has cleared the every-symbol bar five times: the long book
at both k (D177), the short book at both k (D178), and the combined ensemble with both
bootstrap intervals excluding zero (D179).

**All five are BTC-USD and ETH-USD.** Correlated passes on two instruments are not
independent evidence, which is why D178 and D179 both named this test rather than another
sweep.

Two configurations per book — baseline, and baseline plus E1 at **k={p["e1_k"]}** — fixed
before they met this universe (D141), run unchanged across the D140 cross-section: a
mechanically-screened universe built to contain the coins that **failed**, not the ones
that survived to be worth studying. Reference tier `{p["reference_tier"]}`; the short book
pays borrow at {p["borrow_annual_rate"]:.0%}/yr.

**Ties are counted as ties.** E1 is an added brick rather than a swapped one, so on a
symbol where it never fires the two runs are identical and the delta is exactly zero. Win
rates below are over the symbols where E1 actually fired, and both denominators are shown.

{sections}
{_joint_verdict(p)}

## Standing caveats

1. **This tests one rule, not a strategy.** Neither book has a demonstrated edge — the
   long book's DSR sits near 1.0 only because its plateau is flat, and the short book's is
   0.04-0.54. A rule that improves a losing book makes it lose less.
2. **The universe is screened, not curated.** `UniversePolicy` admits on tradability and
   data adequacy only — no return, Sharpe, drawdown or trade count enters it (D140).
3. **The cross-section is not independent.** These coins move together, so 62 symbols is
   far fewer than 62 independent tests and every win rate's effective sample is smaller
   than it looks.
4. **No margin call, no liquidation, no borrow recall (D175).** Short accounts in this
   universe have gone past -100% and kept trading. Until that is modelled, no short number
   here describes a loss a trader could actually have taken.
5. **One configuration each, no per-symbol tuning, one k** (D141). That is what makes this
   an out-of-sample test rather than a second search.
"""


def _book_section(p: dict, book: str) -> str:
    d = p["books"][book]
    cs = d["cohort_summary"]
    rows = NL.join(
        f"| {name} | {v['n']} | {v['n_fired']} | {v['wins']} | {v['losses']} | "
        f"{v['win_rate']:.0%} | {v['mean_delta']:+.3f} | {v['median_delta']:+.3f} |"
        for name, v in sorted(cs.items(), key=lambda kv: (kv[0] != "ALL", kv[0]))
    )
    symbol_rows = NL.join(
        f"| `{sym}` | {r['status']} | {r['base_sharpe']:+.2f} | {r['e1_sharpe']:+.2f} | "
        f"**{r['delta']:+.3f}** | {r['base_trades']} -> {r['e1_trades']} |"
        for sym, r in sorted(d["per_symbol"].items(), key=lambda kv: -kv[1]["delta"])
    )
    return f"""---

## The {book.upper()} book

| Status | Symbols | E1 fired | Wins | Losses | Win rate | Mean Δ Sharpe | Median Δ Sharpe |
|---|---|---|---|---|---|---|---|
{rows}

{_verdict(cs, book)}

{_trade_count_note(d, book)}

{_pnl_table(d, book)}

{_samples(d, book)}

<details><summary>Every symbol ({book})</summary>

| Symbol | Status | Baseline Sharpe | +E1 Sharpe | Δ | Trades |
|---|---|---|---|---|---|
{symbol_rows}

</details>
"""


def blown_accounts(per_symbol: dict) -> dict:
    """Symbols where EITHER arm lost more than the entire account.

    Not a curiosity. This engine has no margin call, no liquidation and no borrow recall
    (D175), so NAV goes negative and the book keeps trading. A mean that quietly contains
    a -1100% row is not a mean of anything, so these are excluded from the mean column
    and named separately (D174)."""
    return {
        sym: r
        for sym, r in per_symbol.items()
        if min(r["base_return"], r["e1_return"]) <= -1.0
    }


def _pnl_table(d: dict, book: str) -> str:
    """The ABSOLUTE result, which the Sharpe deltas above deliberately do not show.

    A win rate is a RELATIVE statistic: it says whether E1 is the better of two
    configurations, and says nothing about whether either is worth running. This says the
    second thing."""
    rows = d["per_symbol"]
    if not rows:
        return ""
    blown = blown_accounts(rows)
    kept = {s: r for s, r in rows.items() if s not in blown}
    lines = []
    for label, name in (("base", "baseline"), ("e1", "+ E1")):
        allr = [r[f"{label}_return"] for r in rows.values()]
        exr = [r[f"{label}_return"] for r in kept.values()]
        sh = [r[f"{label}_sharpe"] for r in rows.values()]
        dd = [r[f"{label}_maxdd"] for r in rows.values()]
        pos = sum(1 for x in allr if x > 0)
        lines.append(
            f"| `{name}` | {statistics.median(allr) * 100:+.1f}% | "
            f"{statistics.fmean(exr) * 100:+.1f}% | {statistics.fmean(sh):+.3f} | "
            f"{statistics.fmean(dd) * 100:.1f}% | {pos} / {len(allr)} |"
        )
    blowup = (
        f"{len(blown)} symbol(s) lost more than the entire account "
        f"(`{'`, `'.join(sorted(blown))}`), so the mean column excludes them. The engine "
        f"models no margin call, liquidation or borrow recall (D175) — a real venue would "
        f"have closed those positions."
        if blown
        else "No symbol drove total return past -100% in this book."
    )
    return f"""**Absolute P&L — is either arm worth running?**

The win rate above is a RELATIVE statistic. It says whether E1 is the better of two
configurations; it says nothing about whether either makes money. This says that.

| Arm | Median total return | Mean, ex blow-ups | Mean Sharpe | Mean max DD | Profitable symbols |
|---|---|---|---|---|---|
{NL.join(lines)}

**The median is the headline and the mean is not** — a cross-section of alts has a return
distribution with a tail that eats any average. {blowup}"""


def _samples(d: dict, book: str, k: int = 5) -> str:
    """Named symbols at both ends, with actual P&L rather than Sharpe.

    A mean delta of +0.05 can be one coin moving a lot or sixty moving a little, and those
    are different findings. These rows say which."""
    fired = [(s, r) for s, r in d["per_symbol"].items() if r["fired"]]
    if not fired:
        return ""
    ranked = sorted(fired, key=lambda kv: -kv[1]["delta"])
    picks = ranked[:k] + ([("...", None)] if len(ranked) > 2 * k else []) + ranked[-k:]
    lines = []
    for sym, r in picks:
        if r is None:
            lines.append(f"| … | | | | | |")
            continue
        lines.append(
            f"| `{sym}` | {r['status']} | {r['base_return'] * 100:+,.1f}% | "
            f"{r['e1_return'] * 100:+,.1f}% | "
            f"{(r['e1_return'] - r['base_return']) * 100:+,.1f} pp | "
            f"{r['delta']:+.3f} |"
        )
    return f"""**Sample symbols — the {k} largest gains and {k} largest losses**, by Sharpe
delta, shown in total return so the size of the effect is legible:

| Symbol | Status | Baseline return | + E1 return | Δ return | Δ Sharpe |
|---|---|---|---|---|---|
{NL.join(lines)}"""


def _trade_count_note(d: dict, book: str) -> str:
    """D177 found E1 RAISES the long book's trade count on BTC/ETH (38->44) and read that
    as re-entry. D178 then falsified the re-entry attribution on the short book. Whether
    the count rises here, and on which book, is the cross-section's read on that
    disagreement."""
    rows = [r for r in d["per_symbol"].values() if r["fired"]]
    if not rows:
        return ""
    base = sum(r["base_trades"] for r in rows)
    e1 = sum(r["e1_trades"] for r in rows)
    up = sum(1 for r in rows if r["e1_trades"] > r["base_trades"])
    down = sum(1 for r in rows if r["e1_trades"] < r["base_trades"])
    direction = "raises" if e1 > base else ("lowers" if e1 < base else "leaves unchanged")
    return (
        f"**Trade count:** E1 {direction} the total across the {len(rows)} symbols it "
        f"fires on ({base:,} -> {e1:,}), up on {up} symbols and down on {down}. D177 read "
        f"the long book's rise on BTC/ETH as re-entry; D178 falsified that attribution on "
        f"the short book, concluding E1's benefit is not sitting in a failed trade. This "
        f"is the cross-section's read on the same question."
    )


def _verdict(cs: dict, book: str) -> str:
    all_row = cs["ALL"]
    cohorts = {k: v for k, v in cs.items() if k != "ALL"}
    weak = [k for k, v in cohorts.items() if v["win_rate"] <= 0.5]
    if all_row["n_fired"] == 0:
        return (
            f"**E1 never fired on the {book} book anywhere in this universe.** That is a "
            f"result about the rule's reach, not its quality: a condition that never "
            f"triggers cannot be evidence for or against itself."
        )
    if all_row["win_rate"] > 0.5 and not weak:
        return (
            f"**The rule survives contact with coins it was not fitted on.** E1 beats the "
            f"bare baseline on {all_row['wins']} of the {all_row['n_fired']} symbols it "
            f"fires on ({all_row['win_rate']:.0%}), mean Δ Sharpe "
            f"{all_row['mean_delta']:+.3f}, and the win rate clears half in **every** "
            f"cohort — including the coins that collapsed or delisted, which a BTC/ETH "
            f"study never sees. That is evidence the effect belongs to the RULE rather "
            f"than to the two instruments it was found on."
        )
    if all_row["win_rate"] > 0.5:
        return (
            f"**Mixed, and the split is the finding.** E1 wins on {all_row['wins']} of "
            f"{all_row['n_fired']} firing symbols overall ({all_row['win_rate']:.0%}, mean "
            f"Δ {all_row['mean_delta']:+.3f}), but the win rate is at or below half in "
            f"{', '.join(sorted(weak))}. An effect that holds among survivors and not "
            f"among the coins that died is the classic shape of a survivorship artifact, "
            f"and it is the specific thing this universe exists to expose."
        )
    return (
        f"**The claim does not survive on the {book} book.** E1 wins on only "
        f"{all_row['wins']} of {all_row['n_fired']} firing symbols "
        f"({all_row['win_rate']:.0%}), mean Δ Sharpe {all_row['mean_delta']:+.3f}. Five "
        f"passes on two instruments is then most simply explained as two instruments."
    )


def _joint_verdict(p: dict) -> str:
    rates = {b: p["books"][b]["cohort_summary"]["ALL"] for b in BOOKS}
    passing = [b for b, v in rates.items() if v["n_fired"] and v["win_rate"] > 0.5]
    detail = ", ".join(
        f"{b} {v['win_rate']:.0%} of {v['n_fired']}" for b, v in rates.items()
    )
    if len(passing) == len(BOOKS):
        head = (
            "**E1 transfers on both books.** That is the direction-agnostic claim D178 "
            "made, now tested on instruments neither book chose."
        )
    elif passing:
        head = (
            f"**E1 transfers on the {passing[0]} book and not the other.** The rule is "
            f"then a property of that book's trade cadence rather than of breakouts as "
            f"such — the same shape D178 found for the swing stop's k, one level up."
        )
    else:
        head = (
            "**E1 does not transfer on either book.** Five every-symbol passes on BTC and "
            "ETH, and neither survives a cross-section that includes the coins that died."
        )
    return f"""---

## Both books together

{head}

Win rates among firing symbols: {detail}.

Whatever the sign, this does not make either book worth running. It answers one question
— whether E1's effect is a property of the rule or of two instruments — and nothing about
whether a breakout book has an edge. The long book's deflated Sharpe is near 1.0 on a flat
plateau and the short book's is 0.04-0.54; neither number moves because of anything here.
"""


if __name__ == "__main__":
    raise SystemExit(main())

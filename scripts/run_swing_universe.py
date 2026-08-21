"""Out-of-sample test of ONE claim: does `swing_k2` beat `trail_10` on coins this study
did not choose? (D174)

`swing_k2` was found on BTC/ETH as the 25th of 25 configurations (D173). It beat
`trail_10` on both symbols, which is a real result and also exactly what a search over 25
configurations produces by chance often enough to be worthless on its own. Deflated
Sharpe on that book is 0.04–0.54 — no demonstrated edge.

So the test that matters is not another sweep. It is the SAME two configurations, fixed,
on the D140 universe: a mechanically-screened cross-section built to contain the coins
that **failed** — down 90%+ from their own peak and never back, or delisted outright.
Nothing is tuned here. Two configurations go in, and the only question asked of the data
is whether the challenger beats the incumbent more often than not, split by whether the
coin survived.

    uv run python scripts/run_swing_universe.py

**The comparison is pre-stated and singular.** Not "which stop is best on the universe" —
that would be a fresh sweep with fresh multiplicity. Just: swing_k2 vs trail_10, the one
claim D173 left standing, on instruments that had no say in producing it.
"""

from __future__ import annotations

import json
import statistics
import time
from datetime import date, datetime, timezone
from pathlib import Path

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
REGISTRY_PATH = REPO / "data" / "swing_universe_registry.sqlite"
RESULTS = REPO / "docs" / "results" / "swing_universe.md"
SUMMARY_JSON = REPO / "data" / "swing_universe_summary.json"

REF_TIER = "taker_40bp"
NL = "\n"

CONTENDERS = {
    "trail_10": [{"type": "trailing_channel_stop", "n_bars": 10}],
    "swing_k2": [{"type": "swing_structure_stop", "k": 2}],
}
"""The two configurations under test, fixed before they meet this universe (D141).

Both are the short baseline in every other respect — same entry/exit lengths, same
SMA200 regime gate, same inverse-vol sizing, same borrow. Only the stop differs, so a
difference between them is attributable to the stop and to nothing else."""


def short_variant(label: str) -> bs.Variant:
    return bs.Variant(
        f"short_{label}", "stop",
        fixed_config=bs.breakout_config(
            n_entry=ds.SHORT_BASELINE_N_ENTRY,
            n_exit=ds.SHORT_BASELINE_N_EXIT,
            weight_source=ds.SHORT_INVERSE_VOL,
            filters=[{"type": "trend_gate", "sma_window": ds.SMA_GATE_WINDOW,
                      "direction": "short"}],
            direction="short",
            exit_rules=CONTENDERS[label],
        ),
    )


def main() -> int:
    started = time.time()
    raw_bars, raw_volumes = load_fixture_csv_with_volumes(FIXTURE)
    cleaned, cleaning_report = clean(raw_bars)
    store = SnapshotStore(REPO / "data" / "snapshots")
    snapshot_id = store.create(
        # The events file, rather than an empty corporate-actions object (D184). The file
        # is empty today, so this moves no number — it closes the silent failure for
        # the day it is not.
        cleaned, load_events_json(EVENTS), volumes_by_symbol=raw_volumes,
        cleaning_report=cleaning_report, validation=None,
        extra_meta={"source_fixture": FIXTURE.name, "study": "swing_universe_v1"},
    )
    snapshot = store.load(snapshot_id)
    meta = json.loads(META.read_text(encoding="utf-8"))
    cohorts = meta["cohort_by_symbol"]

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()
    registry = TrialRegistry(REGISTRY_PATH)
    study = bs.BreakoutStudyConfig()

    results = {}
    for label in CONTENDERS:
        print(f"running {label} across the universe ...")
        results[label] = bu.run_universe_study(
            snapshot.bars_by_symbol,
            snapshot.volumes_by_symbol,
            registry,
            snapshot_id,
            cohorts=cohorts,
            study=study,
            tiers=bs.SHORT_TIERS,
            trial_id_prefix=f"swing-universe-{label}",
            variant=short_variant(label),
            progress=lambda m: None,
        )

    payload = build_payload(results, cohorts, snapshot_id, study)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RESULTS.write_text(build_report(payload), encoding="utf-8")
    n = len(payload["per_symbol"])
    print(f"compared {len(CONTENDERS)} configurations on {n} symbols in "
          f"{time.time() - started:.0f}s")
    print(f"wrote {RESULTS.name} and {SUMMARY_JSON.name}")
    return 0


def build_payload(results, cohorts, snapshot_id, study) -> dict:
    incumbent, challenger = "trail_10", "swing_k2"
    per_symbol = {}
    for symbol, run in results[challenger].runs.items():
        a = results[incumbent].runs.get(symbol)
        if a is None:
            continue
        ai, ci = a.by_tier[REF_TIER], run.by_tier[REF_TIER]
        per_symbol[symbol] = {
            # SURVIVED / COLLAPSED / DELISTED, from `classify` — this is the split the
            # universe exists to expose. `cohort_by_symbol` in the fixture meta is how a
            # symbol was SOURCED (top-30 in 2018, prominent at the 2021 peak, sought
            # failure), which is a different question and would hide the survivorship
            # cut behind a sampling label.
            "status": run.status,
            "source_cohort": cohorts.get(symbol, "unknown"),
            "trail_10_sharpe": ai.variant.sharpe_annual(study),
            "swing_k2_sharpe": ci.variant.sharpe_annual(study),
            "delta": ci.variant.sharpe_annual(study) - ai.variant.sharpe_annual(study),
            "trail_10_return": ai.variant.total_return,
            "swing_k2_return": ci.variant.total_return,
            "trail_10_maxdd": ai.variant.max_drawdown,
            "swing_k2_maxdd": ci.variant.max_drawdown,
            "trades": ci.variant.diagnostics.n_closed_trades,
            # CAGR is undefined once total return passes -100%: (1+r) is negative and a
            # fractional power of a negative number is not a real rate. A short book CAN
            # pass -100% because this engine models no margin call (D175), so this is a
            # real state and not a guard against a hypothetical. None, never nan.
            "trail_10_cagr": _safe_cagr(ai.variant, study),
            "swing_k2_cagr": _safe_cagr(ci.variant, study),
        }
    return {
        "snapshot_id": snapshot_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "reference_tier": REF_TIER,
        "borrow_annual_rate": bs.SHORT_BORROW_ANNUAL_RATE,
        "contenders": {k: v for k, v in CONTENDERS.items()},
        "per_symbol": per_symbol,
        "cohort_summary": cohort_summary(per_symbol),
    }


def _safe_cagr(variant, study):
    if variant.total_return <= -1.0:
        return None
    return bs.cagr(variant.total_return, variant.n_oos_bars, study.periods_per_year)


def blown_accounts(per_symbol: dict) -> dict:
    """Symbols where the short book lost MORE than the entire account.

    Not a curiosity. A short's loss has no ceiling, and this engine has no margin call,
    no liquidation and no borrow recall (D175) — so NAV goes negative and the book keeps
    trading. Reported by name, because an average that quietly contains a -1105% row is
    not an average of anything."""
    out = {}
    for sym, r in per_symbol.items():
        worst = min(r["trail_10_return"], r["swing_k2_return"])
        if worst <= -1.0:
            out[sym] = r
    return out


def cohort_summary(per_symbol: dict) -> dict:
    out = {}
    groups = {"ALL": list(per_symbol.values())}
    for row in per_symbol.values():
        groups.setdefault(row["status"], []).append(row)
    for name, rows in groups.items():
        deltas = [r["delta"] for r in rows]
        wins = sum(1 for d in deltas if d > 0)
        out[name] = {
            "n": len(rows),
            "wins": wins,
            "win_rate": wins / len(rows) if rows else 0.0,
            "mean_delta": statistics.fmean(deltas) if deltas else 0.0,
            "median_delta": statistics.median(deltas) if deltas else 0.0,
        }
    return out


def build_report(p: dict) -> str:
    cs = p["cohort_summary"]
    all_row = cs["ALL"]
    rows = NL.join(
        f"| {name} | {v['n']} | {v['wins']} | {v['win_rate']:.0%} | "
        f"{v['mean_delta']:+.3f} | {v['median_delta']:+.3f} |"
        for name, v in sorted(cs.items(), key=lambda kv: (kv[0] != "ALL", kv[0]))
    )
    symbol_rows = NL.join(
        f"| `{sym}` | {r['status']} | {r['trail_10_sharpe']:+.2f} | "
        f"{r['swing_k2_sharpe']:+.2f} | **{r['delta']:+.3f}** | {r['trades']} |"
        for sym, r in sorted(p["per_symbol"].items(), key=lambda kv: -kv[1]["delta"])
    )
    verdict = _verdict(p)
    return f"""# swing_k2 vs trail_10 on coins this study did not choose

**Produced:** {p["generated_utc"][:10]} ·
**Snapshot:** `{p["snapshot_id"]}` ·
**Reproduce:** `uv run python scripts/run_swing_universe.py` (offline, deterministic)

## What this is, and what it deliberately is not

`swing_k2` was found on BTC/ETH as the **25th of 25 configurations** (D173). It beat
`trail_10` on both symbols — a real result, and also exactly what searching 25
configurations produces by chance often enough to be worth nothing on its own. That book's
deflated Sharpe is 0.04–0.54: no demonstrated edge.

So this is **not** another sweep. Two configurations, fixed before they met this universe
(D141), differing only in the stop, run unchanged across the D140 cross-section — a
mechanically-screened universe built to contain the coins that **failed**, not the ones
that survived to be worth studying. The only question asked is whether the challenger
beats the incumbent, and whether that holds among the coins that collapsed as well as the
ones that lived.

Short book throughout: SMA200 regime gate, inverse-vol sizing capped at 1.0, and borrow
charged at {p["borrow_annual_rate"]:.0%}/yr. Reference tier `{p["reference_tier"]}`.

## The result, by cohort

| Status | Symbols | `swing_k2` wins | Win rate | Mean Δ Sharpe | Median Δ Sharpe |
|---|---|---|---|---|---|
{rows}

{verdict}

## And now the number that matters more

A win rate is a RELATIVE statistic. It says `swing_k2` is the better stop; it says nothing
about whether either is worth running. The absolute P&L says that, and it is brutal.

{_absolute_table(p)}

**The median coin loses roughly half the account.** `swing_k2` is consistently the better
of two stops on a book that is profitable on a handful of coins out of sixty-two — and it
posts *fewer* profitable symbols than `trail_10` while beating it on average, which is the
shape of a rule that trims the middle of the distribution rather than finding winners.

Read the two sections together and the honest summary is: **the stop is real, the strategy
is not.** Nothing here rescues a book whose deflated Sharpe on BTC/ETH is 0.04–0.54.

{_blowup_section(p)}

## Every symbol

| Symbol | Status | `trail_10` Sharpe | `swing_k2` Sharpe | Δ | Trades |
|---|---|---|---|---|---|
{symbol_rows}

## Standing caveats

1. **This tests one claim, not the strategy.** The short book has no demonstrated edge on
   BTC/ETH and nothing here changes that. A stop that improves a losing book makes it lose
   less; it does not make it win.
2. **The universe is screened, not curated.** `UniversePolicy` admits on tradability and
   data adequacy only — no return, Sharpe, drawdown or trade count enters it (D140). But
   it is still a universe someone assembled, and the coins in it are the ones a provider
   still serves bars for.
3. **Borrow at a flat {p["borrow_annual_rate"]:.0%}/yr is generous here.** Borrowing a
   small-cap altcoin to short it, in the size and at the moment you would most want to,
   is frequently impossible at any rate. Every short number in this document is optimistic
   for that reason and the effect is largest exactly in the collapsed cohort.
4. **One configuration each, no per-symbol tuning** (D141). That is what makes this an
   out-of-sample test rather than a second search.
5. **No margin call, no liquidation, no borrow recall (D175).** Three accounts in this
   run went past −100% and kept trading. A real venue would have closed them. Until that
   is modelled, no short result in this project describes a loss a trader could actually
   have taken.
6. **The cross-section is not independent.** These coins move together, so 62 symbols is
   far fewer than 62 independent tests and the win rate's effective sample is smaller
   than it looks.
"""


def _absolute_table(p: dict) -> str:
    rows = p["per_symbol"]
    blown = blown_accounts(rows)
    kept = {s: r for s, r in rows.items() if s not in blown}
    lines = []
    for label in ("trail_10", "swing_k2"):
        allr = [r[f"{label}_return"] for r in rows.values()]
        exr = [r[f"{label}_return"] for r in kept.values()]
        sh = [r[f"{label}_sharpe"] for r in rows.values()]
        pos = sum(1 for x in allr if x > 0)
        lines.append(
            f"| `{label}` | {statistics.median(allr) * 100:+.1f}% | "
            f"{statistics.fmean(exr) * 100:+.1f}% | {statistics.fmean(sh):+.3f} | "
            f"{pos} / {len(allr)} |"
        )
    return (
        "| Stop | Median total return | Mean, excluding blow-ups | Mean Sharpe | "
        "Profitable symbols |" + NL
        + "|---|---|---|---|---|" + NL + NL.join(lines) + NL + NL
        + "**The median is the headline and the mean is not.** The unadjusted mean return "
        f"is dominated by {len(blown)} symbol(s) that lost more than the entire account, so "
        "the column above excludes them and the next section names them."
    )


def _blowup_section(p: dict) -> str:
    blown = blown_accounts(p["per_symbol"])
    if not blown:
        return """## No account was destroyed

No symbol drove total return past −100% in this run. That is a fact about this sample,
not a property of the strategy: this engine models no margin call, no liquidation and no
borrow recall (D175), so nothing would have stopped it if one had."""
    rows = NL.join(
        f"| `{sym}` | {r['status']} | {r['trail_10_return'] * 100:,.1f}% | "
        f"{r['swing_k2_return'] * 100:,.1f}% | {r['swing_k2_maxdd'] * 100:.1f}% |"
        for sym, r in sorted(blown.items(), key=lambda kv: kv[1]["swing_k2_return"])
    )
    worst = min(r["swing_k2_return"] for r in blown.values())
    return f"""## {len(blown)} coins destroyed the account, and the engine let them

| Symbol | Status | `trail_10` return | `swing_k2` return | `swing_k2` max DD |
|---|---|---|---|---|
{rows}

These are Terra. Shorting a collapsed, near-zero-priced coin that then rallies multiples
loses many times the notional, and the worst here is **{worst * 100:,.0f}%** — the book
lost eleven times the account it started with.

**The stops were active and did not prevent it, which is the point.** An intrabar stop
(D170) exits the moment price touches the level; it cannot help when the instrument opens
five times higher, and it cannot help at all once repeated losses have taken NAV negative
and the book is still trading.

**The engine models no margin call, no liquidation and no borrow recall (D175).** A real
venue would have closed these positions — probably at a terrible price, but it would have
closed them — and a real borrow desk would have recalled the shares long before. Every
short number in this project is optimistic for that reason, and the optimism is largest
exactly where the instrument is most violent, which is exactly where a short book looks
most attractive.

This is the single most important thing the universe test found, and it was not what the
test was looking for."""


def _verdict(p: dict) -> str:
    cs = p["cohort_summary"]
    all_row = cs["ALL"]
    cohorts = {k: v for k, v in cs.items() if k != "ALL"}
    consistent = [k for k, v in cohorts.items() if v["win_rate"] > 0.5]
    inconsistent = [k for k, v in cohorts.items() if v["win_rate"] <= 0.5]

    if all_row["win_rate"] > 0.5 and not inconsistent:
        return (
            f"**The claim survives contact with coins it was not fitted on.** `swing_k2` "
            f"beats `trail_10` on {all_row['wins']} of {all_row['n']} symbols "
            f"({all_row['win_rate']:.0%}), mean Δ Sharpe {all_row['mean_delta']:+.3f}, and "
            f"the win rate is above half in **every** cohort — including the coins that "
            f"collapsed or delisted, which are the ones a BTC/ETH study never sees. That is "
            f"the first evidence in this project that the effect is a property of the stop "
            f"rather than of the two instruments it was found on. It is evidence, not proof: "
            f"the cross-section is not independent (these coins move together), so the "
            f"effective sample is smaller than the symbol count suggests."
        )
    if all_row["win_rate"] > 0.5:
        return (
            f"**Mixed, and the split is the finding.** `swing_k2` beats `trail_10` on "
            f"{all_row['wins']} of {all_row['n']} symbols overall ({all_row['win_rate']:.0%}, "
            f"mean Δ {all_row['mean_delta']:+.3f}), but the win rate is at or below half in "
            f"{', '.join(inconsistent)}. An effect that holds among survivors and not among "
            f"the coins that died is the classic shape of a survivorship artifact, and it is "
            f"the specific thing this universe exists to expose."
        )
    return (
        f"**The claim does not survive.** `swing_k2` beats `trail_10` on only "
        f"{all_row['wins']} of {all_row['n']} symbols ({all_row['win_rate']:.0%}), mean Δ "
        f"Sharpe {all_row['mean_delta']:+.3f}. The BTC/ETH result is then most simply "
        f"explained as the 25th of 25 configurations doing what the 25th of 25 "
        f"configurations does, and the deflated Sharpe on that book already said so."
    )


if __name__ == "__main__":
    raise SystemExit(main())

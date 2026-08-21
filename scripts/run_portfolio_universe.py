"""A CROSS-SECTIONAL long/short portfolio across the D140 universe. (D183)

D182 combined each coin's own long and short books and found the pairing costs 118
percentage points of median return to buy 4.7 of drawdown. That answered "does pairing one
coin's two books help?" — and explicitly did **not** answer the question underneath it:
does a long/short book run ACROSS the cross-section work?

The difference is diversification between coins, which no study in this project has ever
had. Every result so far — the long study, the short study, D174, D180, D182 — is a
single-instrument book, or a cross-section of single-instrument books averaged after the
fact. Averaging Sharpes is not the same as earning the Sharpe of an average.

    uv run python scripts/run_portfolio_universe.py

**What this is.** Each coin's long and short books are run exactly as published. Their
DATED return series are then aggregated: on each date, the long portfolio earns the equal-
weighted mean of every long book with a position open, and likewise the short. The two
portfolio series are then combined at D181's expanding inverse-vol weights.

**What this is not.** It is a return-aggregation portfolio, not a portfolio backtest. There
is no shared capital constraint, no cross-sectional position limit, and — the one that
matters most — **no cost for rebalancing between coins.** Each coin's own trading costs are
charged inside its book; moving capital between coins to hold equal weights is free here
and would not be free anywhere else. Every number in this study is optimistic by that
amount, and the amount is not measured.
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
REGISTRY_PATH = REPO / "data" / "portfolio_universe_registry.sqlite"
RESULTS = REPO / "docs" / "results" / "portfolio_universe.md"
SUMMARY_JSON = REPO / "data" / "portfolio_universe_summary.json"

REF_TIER = bs.REFERENCE_TIER
NL = "\n"

ARMS = ("long", "short")


def variant_for(arm: str) -> bs.Variant:
    """Both published baselines, reused rather than re-derived (D141). The long arm IS
    `breakout_universe.baseline_variant()` — the same object the D140 study runs."""
    if arm == "long":
        return bu.baseline_variant()
    return bs.Variant(
        "short_baseline",
        "plateau",
        fixed_config=ds.short_config(ds.SHORT_BASELINE_N_ENTRY, ds.SHORT_BASELINE_N_EXIT),
    )


def dated_returns(equity: list[tuple[datetime, float]]) -> tuple[list[tuple[str, float]], bool]:
    """Per-bar returns keyed by date, TRUNCATED the moment the account is gone.

    Two of the short books drive NAV past -100% (`LUNA1-USD` -154%, `LUNC-USD` -175%),
    which this engine permits because it models no margin call, liquidation or borrow
    recall (D175). Once NAV is negative the per-bar return `b/a - 1` is not a return at
    all — the sign of the denominator has flipped — and feeding it into a portfolio mean
    would propagate nonsense across every other coin.

    So a book whose NAV reaches zero is treated as dead from that bar: the position is
    gone, the capital is gone, and it contributes nothing further. That is STRICTER than
    the per-symbol studies, which let the book keep trading a negative account, and it is
    the more realistic of the two. It is not a fix for D175 — a real venue would have
    closed the position earlier and at a worse price."""
    out: list[tuple[str, float]] = []
    died = False
    for (_, a), (ts, b) in zip(equity, equity[1:]):
        if a <= 0.0:
            died = True
            break
        r = b / a - 1.0
        if b <= 0.0:
            # The bar that wipes the account out: book the full loss, then stop.
            out.append((ts.date().isoformat(), -1.0))
            died = True
            break
        out.append((ts.date().isoformat(), r))
    return out, died


def main() -> int:
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
        extra_meta={"source_fixture": FIXTURE.name, "study": "portfolio_universe_v1"},
    )
    snapshot = store.load(snapshot_id)
    cohorts = json.loads(META.read_text(encoding="utf-8"))["cohort_by_symbol"]

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()
    registry = TrialRegistry(REGISTRY_PATH)
    study = bs.BreakoutStudyConfig()

    runs: dict[str, Any] = {}
    for arm in ARMS:
        print(f"running {arm} baseline across the universe ...", flush=True)
        runs[arm] = bu.run_universe_study(
            snapshot.bars_by_symbol,
            snapshot.volumes_by_symbol,
            registry,
            snapshot_id,
            cohorts=cohorts,
            study=study,
            tiers=bs.SHORT_TIERS if arm == "short" else bs.DEFAULT_TIERS,
            trial_id_prefix=f"portfolio-universe-{arm}",
            variant=variant_for(arm),
            progress=lambda m: None,
        )

    payload = build_payload(runs, cohorts, snapshot_id, study)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RESULTS.write_text(build_report(payload), encoding="utf-8")
    print(f"built the portfolio over {payload['n_dates']:,} dates in {time.time() - started:.0f}s")
    print(f"wrote {RESULTS.name} and {SUMMARY_JSON.name}")
    return 0


def _stats(returns: list[float], study: bs.BreakoutStudyConfig) -> dict[str, float]:
    nav, peak, worst = 1.0, 1.0, 0.0
    for r in returns:
        nav *= 1.0 + r
        peak = max(peak, nav)
        worst = max(worst, 1.0 - nav / peak) if peak > 0 else worst
    return {
        "sharpe": bs.sharpe(returns, study.rf_annual, study.periods_per_year),
        "total_return": nav - 1.0,
        "max_drawdown": worst,
        "n_bars": len(returns),
    }


def build_payload(runs, cohorts, snapshot_id, study) -> dict:
    # ---- per-symbol dated series, per arm -----------------------------------------
    series: dict[str, dict[str, dict[str, float]]] = {arm: {} for arm in ARMS}
    per_symbol: dict[str, dict[str, Any]] = {}
    deaths: dict[str, str] = {}
    for arm in ARMS:
        for symbol, run in runs[arm].runs.items():
            v = run.by_tier[REF_TIER].variant
            dated, died = dated_returns(v.oos_equity)
            series[arm][symbol] = dict(dated)
            if died:
                deaths[f"{symbol}/{arm}"] = dated[-1][0] if dated else "immediately"
            row = per_symbol.setdefault(
                symbol, {"status": run.status, "source_cohort": cohorts.get(symbol, "unknown")}
            )
            row[f"{arm}_sharpe"] = v.sharpe_annual(study)
            row[f"{arm}_return"] = v.total_return
            row[f"{arm}_first_date"] = dated[0][0] if dated else None
            row[f"{arm}_n_bars"] = len(dated)

    # ---- the portfolio timeline ----------------------------------------------------
    # Every date any book is live. A coin contributes only from ITS OWN out-of-sample
    # start, so nothing is held before the walk-forward would have admitted it.
    dates = sorted({d for arm in ARMS for s in series[arm].values() for d in s})
    breadth: list[tuple[str, int, int]] = []
    arm_series: dict[str, list[float]] = {arm: [] for arm in ARMS}
    for d in dates:
        counts = {}
        for arm in ARMS:
            live = [s[d] for s in series[arm].values() if d in s]
            counts[arm] = len(live)
            # Equal weight across every coin live on the date; a date with nothing live
            # earns zero rather than being dropped, so the two arms stay aligned and the
            # flat periods are counted honestly.
            arm_series[arm].append(statistics.fmean(live) if live else 0.0)
        breadth.append((d, counts["long"], counts["short"]))

    ens = ds.combine_books(
        arm_series["long"], arm_series["short"], study.rf_annual, study.periods_per_year
    )
    combined = ds.combined_series(arm_series["long"], arm_series["short"])
    w = ds.ENSEMBLE_MIN_BARS

    portfolio = {
        # Scored on the same post-warm-up span as the combination, so all three are
        # comparable (D181).
        "long": _stats(arm_series["long"][w:], study),
        "short": _stats(arm_series["short"][w:], study),
        "combined": _stats(combined, study),
        "correlation": ens.correlation,
        "mean_long_weight": ens.mean_long_weight,
        "n_fallback_bars": ens.n_fallback_bars,
    }
    single = {
        arm: {
            "median_sharpe": statistics.median(
                [r[f"{arm}_sharpe"] for r in per_symbol.values()]
            ),
            "mean_sharpe": statistics.fmean(
                [r[f"{arm}_sharpe"] for r in per_symbol.values()]
            ),
            "median_return": statistics.median(
                [r[f"{arm}_return"] for r in per_symbol.values()]
            ),
        }
        for arm in ARMS
    }
    return {
        "snapshot_id": snapshot_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "reference_tier": REF_TIER,
        "min_bars": ds.ENSEMBLE_MIN_BARS,
        "borrow_annual_rate": bs.SHORT_BORROW_ANNUAL_RATE,
        "n_symbols": len(per_symbol),
        "n_dates": len(dates),
        "first_date": dates[0],
        "last_date": dates[-1],
        "portfolio": portfolio,
        "single_symbol": single,
        "breadth": breadth,
        "deaths": deaths,
        "per_symbol": per_symbol,
    }


def build_report(p: dict) -> str:
    pf, ss = p["portfolio"], p["single_symbol"]
    rows = NL.join(
        f"| {arm} portfolio | {pf[arm]['sharpe']:+.3f} | "
        f"{pf[arm]['total_return'] * 100:+,.1f}% | {pf[arm]['max_drawdown'] * 100:.1f}% | "
        f"{ss[arm]['median_sharpe']:+.3f} | {ss[arm]['median_return'] * 100:+,.1f}% |"
        for arm in ARMS
    )
    return f"""# A cross-sectional long/short portfolio across 62 coins

**Produced:** {p["generated_utc"][:10]} ·
**Snapshot:** `{p["snapshot_id"]}` ·
**Reproduce:** `uv run python scripts/run_portfolio_universe.py` (offline, deterministic)

## What this is

D182 combined each coin's own two books and found the pairing costs 118 percentage points
of median return to buy 4.7 of drawdown. That answered *"does pairing one coin's two books
help?"* and deliberately did not answer the question underneath: **does a long/short book
run ACROSS the cross-section work?**

The difference is diversification between coins — the one thing no study in this project
has ever had. Every prior result is a single-instrument book, or a cross-section of
single-instrument books averaged afterwards. **Averaging Sharpes is not the same as
earning the Sharpe of an average**, and that gap is the whole subject here.

Both baselines are the published ones, unchanged (D141); the long arm is
`breakout_universe.baseline_variant()` itself. On each date the long portfolio earns the
equal-weighted mean of every long book with a position open, likewise the short, and the
two are combined at D181's expanding inverse-vol weights.

{p["n_symbols"]} symbols, {p["n_dates"]:,} dates, {p["first_date"]} to {p["last_date"]}.
Reference tier `{p["reference_tier"]}`; the short leg pays borrow at
{p["borrow_annual_rate"]:.0%}/yr. The first {p["min_bars"]} bars are weighting warm-up and
are excluded from every figure, all three arms alike.

## Does diversifying across coins do what diversifying within a coin could not?

| | Sharpe | Total return | Max DD | Median SINGLE coin Sharpe | Median single coin return |
|---|---|---|---|---|---|
{rows}
| **combined portfolio** | **{pf["combined"]["sharpe"]:+.3f}** | {pf["combined"]["total_return"] * 100:+,.1f}% | {pf["combined"]["max_drawdown"] * 100:.1f}% | — | — |

{_verdict(p)}

{_breadth_block(p)}

{_weight_block(p)}

{_deaths_block(p)}

## Standing caveats

1. **No rebalancing cost between coins.** Each coin's own trading costs are charged inside
   its book. Moving capital between coins to hold equal weights is free here and is free
   nowhere else. Every number above is optimistic by an amount this study does not measure,
   and the daily-rebalanced equal weight is the most turnover-hungry construction there is.
2. **Return aggregation, not a portfolio backtest.** No shared capital constraint, no
   cross-sectional position limit, no netting of a long and a short in the same coin beyond
   what the arithmetic does on its own.
3. **Universe membership is fixed in advance.** `UniversePolicy` admits on tradability and
   data adequacy only, with no return, Sharpe or drawdown input (D140) — but a coin is
   admitted because of how much history it *turns out* to have, which is not knowable on
   the first day it is held. The same limitation D140/D141 carries.
4. **Early breadth is thin.** The portfolio starts with whatever had cleared its
   walk-forward by {p["first_date"]}, and a one-coin "portfolio" is a single coin.
5. **The short book is what it is.** It loses on 57 of 62 coins (D182), and no allocation
   scheme creates an edge from a leg that does not have one.
6. **No margin call, no liquidation, no borrow recall (D175).** Books that wipe out are
   truncated here rather than allowed to trade a negative account, which is stricter than
   the per-symbol studies and still not a model of what a venue would have done.
"""


def _verdict(p: dict) -> str:
    pf, ss = p["portfolio"], p["single_symbol"]
    lp, lm = pf["long"]["sharpe"], ss["long"]["median_sharpe"]
    lift = lp - lm
    cost = pf["combined"]["sharpe"] - lp
    dd = pf["combined"]["max_drawdown"] - pf["long"]["max_drawdown"]
    head = (
        f"**Diversifying across coins lifts the long book from {lm:+.3f} on the median "
        f"single coin to {lp:+.3f} as a portfolio — {lift:+.3f}.** "
        if lift > 0
        else (
            f"**Diversifying across coins does NOT lift the long book**: {lp:+.3f} as a "
            f"portfolio against {lm:+.3f} on the median single coin ({lift:+.3f}). "
        )
    )
    head += (
        "That is the one form of diversification this project had never tested, and it is "
        "the only one that operates on the return distribution rather than on a losing "
        "book's timing."
    )
    tail = (
        f"{NL}{NL}**Adding the short portfolio costs {cost:+.3f} Sharpe** and moves max "
        f"drawdown by {dd * 100:+.1f} pp. "
    )
    tail += (
        "The D182 finding survives at portfolio level: the short book subtracts."
        if cost < 0
        else "This reverses D182's per-symbol finding and is the first thing in this "
        "project to make the short book look useful — which is reason to check it "
        "hard, not to adopt it."
    )
    return head + tail


def _breadth_block(p: dict) -> str:
    b = p["breadth"]
    marks = [b[0], b[len(b) // 4], b[len(b) // 2], b[3 * len(b) // 4], b[-1]]
    rows = NL.join(f"| {d} | {nl} | {ns} |" for d, nl, ns in marks)
    longs = [x[1] for x in b]
    thin = sum(1 for x in longs if x <= 3)
    return f"""## Breadth — how many coins the portfolio actually held

A portfolio of one coin is a coin. This is the number of books with a position open, which
is not the number of coins admitted: the long book is in the market roughly half the time
and the short book ~15% of it.

| Date | Long books open | Short books open |
|---|---|---|
{rows}

Median long breadth **{statistics.median(longs):.0f}**, maximum {max(longs)}. On
**{thin:,} of {len(b):,}** dates ({thin / len(b):.0%}) the long side held three coins or
fewer, and those dates are concentrated at the start of the sample where only the oldest
coins had cleared their walk-forward."""


def _weight_block(p: dict) -> str:
    pf = p["portfolio"]
    return f"""## How the risk budget splits, and the flaw it carries

Mean weight on the LONG portfolio: **{pf["mean_long_weight"]:.3f}**. Long/short correlation
**{pf["correlation"]:+.4f}**; the weighting fell back to 50/50 on {pf["n_fallback_bars"]:,}
bars.

Inverse-vol weighting reads a book that is flat most of the time as low-risk, when what it
actually is, is absent (D181). Aggregating across 62 coins raises the short arm's
in-the-market share well above any single coin's, so this bites less here than it does per
symbol — but it is the same construction and it is not fixed."""


def _deaths_block(p: dict) -> str:
    deaths = p.get("deaths") or {}
    if not deaths:
        return (
            "**No book wiped out its account.** Nothing was truncated, so the portfolio "
            "series contains every bar every book produced."
        )
    rows = NL.join(f"| `{k}` | {v} |" for k, v in sorted(deaths.items()))
    return f"""## {len(deaths)} book(s) wiped out and were truncated

Once NAV reaches zero the per-bar return is not a return — the denominator's sign has
flipped — and averaging it into a portfolio would propagate nonsense across every other
coin. These books are dead from the date shown and contribute nothing after it.

| Book | Dead from |
|---|---|
{rows}

This is **stricter** than the per-symbol studies, which let a book keep trading a negative
account (D175), and it is the more realistic of the two. It is still not a liquidation
model: a real venue would have closed the position earlier, and at a worse price."""


if __name__ == "__main__":
    raise SystemExit(main())

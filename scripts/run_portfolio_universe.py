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
REGISTRY_PATH = REPO / "data" / "portfolio_universe_registry.sqlite"
RESULTS = REPO / "docs" / "results" / "portfolio_universe.md"
SUMMARY_JSON = REPO / "data" / "portfolio_universe_summary.json"

REF_TIER = bs.REFERENCE_TIER
NL = "\n"

ARMS = ("long", "short")

COST_BPS = (0.0, 10.0, 25.0, 40.0)
"""One-way cost charged on portfolio turnover, in basis points.

The same four levels as `bs.DEFAULT_TIERS` — maker 0/10/25 and taker 40 — so the
rebalancing charge is read on the ladder the rest of the project already uses, rather than
on a number invented for this study. `taker_40bp` is the reference tier and the honest
default: moving capital between small-cap alts on a daily schedule is a taker fill."""

D184_ARTIFACTS = {("HT-USD", "2025-03-12"), ("AAVE-USD", "2020-10-03")}
"""Two unrecorded corporate actions (D184), neutralised in the BENCHMARK only.

HT-USD printed +3,398,300% on a price-scale defect; AAVE-USD +10,189% on the LEND->AAVE
100:1 migration. Left in, the equal-weight benchmark reads +102,682,123%. The strategy is
untouched by both — next-open fills (D103) mean a one-bar gap cannot be entered."""


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
        # The events file, rather than an empty corporate-actions object (D184). The file
        # is empty today, so this moves no number — it closes the silent failure for
        # the day it is not.
        load_events_json(EVENTS),
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

    payload = build_payload(runs, cohorts, snapshot_id, study, snapshot.bars_by_symbol)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RESULTS.write_text(build_report(payload), encoding="utf-8")
    print(f"built the portfolio over {payload['n_dates']:,} dates in {time.time() - started:.0f}s")
    print(f"wrote {RESULTS.name} and {SUMMARY_JSON.name}")
    return 0


def _equal_weight_arm(
    dates: list[str], per_symbol: dict[str, dict[str, float]]
) -> tuple[list[float], list[float]]:
    """Equal-weight the live books each date, and measure the TURNOVER that requires.

    Returns (gross return series, one-way turnover series). This is the cost D183 did not
    charge and named as the test of its own result.

    Where the turnover comes from. Each date opens with capital split equally across the
    live books. Over the day each book's slice grows by its own return, so the slices
    drift apart; restoring equal weight means selling the winners and buying the losers.
    Books entering or leaving the live set are a full slice traded either way.

    One-way turnover is `0.5 * sum |drifted weight - target weight|` — the standard
    convention, counting the value that changes hands once rather than double-counting
    each sale against its matching purchase.

    **A book that is flat holds cash, and moving cash between books is free.** A flat book
    reports exactly 0.0, so its slice does not drift and it contributes turnover only
    through the denominator — which is the correct treatment and not an approximation.
    What IS approximate: when a flat book joins or leaves the live set its whole slice is
    counted as traded, though it was cash. That over-charges, and over-charging is the
    right direction for a test built to threaten a result."""
    gross: list[float] = []
    turn: list[float] = []
    prev_weights: dict[str, float] = {}
    for d in dates:
        live = {s: r[d] for s, r in per_symbol.items() if d in r}
        if not live:
            gross.append(0.0)
            # Capital that was deployed is now in nothing: unwinding is a real trade.
            turn.append(0.5 * sum(abs(w) for w in prev_weights.values()))
            prev_weights = {}
            continue
        target = 1.0 / len(live)
        # Value each slice carries into the date. A book that was not held yesterday
        # starts from zero and has to be bought.
        value = {s: prev_weights.get(s, 0.0) * (1.0 + r) for s, r in live.items()}
        for s, w in prev_weights.items():
            if s not in live:
                value[s] = w  # dropped out; the slice is still there and must be sold
        total = sum(value.values())
        invested = sum(prev_weights.values())
        gross.append(total / invested - 1.0 if invested > 0 else 0.0)
        drifted = (
            {s: v / total for s, v in value.items()} if total > 0
            else {s: 0.0 for s in value}
        )
        turn.append(
            0.5 * sum(abs(drifted.get(s, 0.0) - (target if s in live else 0.0))
                      for s in set(drifted) | set(live))
        )
        prev_weights = {s: target for s in live}
    return gross, turn


def _charge(gross: list[float], turnover: list[float], bps: float) -> list[float]:
    """Net returns after a one-way cost of `bps` on each unit of turnover."""
    rate = bps / 10_000.0
    return [g - t * rate for g, t in zip(gross, turnover)]


def _breakeven(
    s_gross: list[float], s_turn: list[float],
    b_gross: list[float], b_turn: list[float],
    w: int, study: bs.BreakoutStudyConfig,
) -> float | None:
    """The cost at which the strategy's Sharpe EDGE over the benchmark reaches zero.

    Both sides are charged the same rate. The benchmark holds every coin every day and so
    turns over more, which means a rising cost hurts it faster — the edge can therefore
    WIDEN with cost rather than narrow, and the honest answer is then "there isn't one".

    Bisection on a monotone-in-practice function, not a solve: if the edge is already
    negative at zero cost, or still positive at 1000bp, that is reported rather than
    interpolated into a number that does not exist."""
    def edge(bps: float) -> float:
        a = bs.sharpe(_charge(s_gross, s_turn, bps)[w:], study.rf_annual, study.periods_per_year)
        b = bs.sharpe(_charge(b_gross, b_turn, bps)[w:], study.rf_annual, study.periods_per_year)
        return a - b

    lo, hi = 0.0, 1000.0
    if edge(lo) <= 0.0 or edge(hi) > 0.0:
        return None
    for _ in range(60):
        mid = (lo + hi) / 2.0
        if edge(mid) > 0.0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


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


def build_payload(runs, cohorts, snapshot_id, study, bars_by_symbol) -> dict:
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
    turnover: dict[str, list[float]] = {arm: [] for arm in ARMS}
    for arm in ARMS:
        arm_series[arm], turnover[arm] = _equal_weight_arm(dates, series[arm])
    for d in dates:
        breadth.append(
            (d, sum(1 for s in series["long"].values() if d in s),
             sum(1 for s in series["short"].values() if d in s))
        )

    ens = ds.combine_books(
        arm_series["long"], arm_series["short"], study.rf_annual, study.periods_per_year
    )
    combined = ds.combined_series(arm_series["long"], arm_series["short"])
    w = ds.ENSEMBLE_MIN_BARS

    # ---- benchmarks, charged the SAME way -----------------------------------------
    # Charging the strategy and not the benchmark would rig the comparison: the
    # equal-weight universe rebalances daily too, holds every coin all the time, and
    # therefore turns over far more.
    bench_raw = {}
    for symbol, bars in bars_by_symbol.items():
        r = {}
        for a, b in zip(bars, bars[1:]):
            d = b.timestamp.date().isoformat()
            if a.bar.close > 0 and (symbol, d) not in D184_ARTIFACTS:
                r[d] = b.bar.close / a.bar.close - 1.0
        bench_raw[symbol] = r
    ew_gross, ew_turn = _equal_weight_arm(dates, bench_raw)
    btc_gross = [bench_raw.get("BTC-USD", {}).get(d, 0.0) for d in dates]

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
    # ---- the rebalancing cost D183 named as the test of its own result -------------
    costed: dict[str, Any] = {"tiers": list(COST_BPS), "rows": {}}
    for label, gross, turn in (
        ("strategy_long", arm_series["long"], turnover["long"]),
        ("benchmark_ew", ew_gross, ew_turn),
        # Buy and hold turns over once at the start and never again; charging it the same
        # daily rate would invent a cost it does not pay.
        ("benchmark_btc", btc_gross, [0.0] * len(btc_gross)),
    ):
        costed["rows"][label] = {
            "mean_daily_turnover": statistics.fmean(turn[w:]) if len(turn) > w else 0.0,
            "annual_turnover": (statistics.fmean(turn[w:]) * 365.0) if len(turn) > w else 0.0,
            "net": {
                str(bps): _stats(_charge(gross, turn, bps)[w:], study) for bps in COST_BPS
            },
        }
    costed["breakeven_bps"] = _breakeven(
        arm_series["long"], turnover["long"], ew_gross, ew_turn, w, study
    )
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
        "costed": costed,
        "single_symbol": single,
        "breadth": breadth,
        # The study's actual output. Without it, every follow-up question needs a full
        # recompute and `--report-only` is a promise the payload cannot keep.
        "series": {
            "dates": dates,
            "long": arm_series["long"],
            "short": arm_series["short"],
            "combined": combined,
        },
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

{_breadth_conditional(p)}

{_cost_block(p)}

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
    return f"""## Breadth — how many coins the portfolio could hold

A portfolio of one coin is a coin. This counts the books **live in the sample** on each
date — coins whose own walk-forward has started and which have not wiped out. It is an
upper bound on positions, not a position count: a book that is flat still contributes a
0.0 return and is counted here.

| Date | Long books live | Short books live |
|---|---|---|
{rows}

Median **{statistics.median(longs):.0f}** live, maximum {max(longs)}. On **{thin:,} of
{len(b):,}** dates ({thin / len(b):.0%}) fewer than four coins were live at all, and those
dates sit at the start of the sample where only the oldest coins had cleared their
walk-forward.

**Position-level breadth is not measured here.** The long book is in the market roughly
half the time and the short book far less, so the number of positions actually held is
materially below these counts. That matters for whether daily equal-weighting across coins
is a realistic construction, and this study does not answer it."""


def _cost_block(p: dict) -> str:
    """The rebalancing cost D183 named as the test of its own result."""
    c = p.get("costed")
    if not c:
        return ""
    labels = {
        "strategy_long": "**LONG portfolio (strategy)**",
        "benchmark_ew": "Equal-weight universe",
        "benchmark_btc": "BTC buy & hold",
    }
    header = ("| Book | Annual turnover | " + " | ".join(f"{int(b)} bp" for b in c["tiers"])
              + " |" + NL + "|---|---|" + "---|" * len(c["tiers"]))
    rows = []
    for key, lab in labels.items():
        r = c["rows"][key]
        cells = " | ".join(f"{r['net'][str(b)]['sharpe']:+.3f}" for b in c["tiers"])
        rows.append(f"| {lab} | {r['annual_turnover']:.1f}x | {cells} |")
    be = c.get("breakeven_bps")
    strat = c["rows"]["strategy_long"]["net"]
    bench = c["rows"]["benchmark_ew"]["net"]
    edges = " · ".join(
        f"{int(b)}bp **{strat[str(b)]['sharpe'] - bench[str(b)]['sharpe']:+.3f}**"
        for b in c["tiers"]
    )
    if be is None:
        e0 = strat["0.0"]["sharpe"] - bench["0.0"]["sharpe"]
        verdict = (
            "**There is no break-even cost.** "
            + (
                "The edge is already negative before any cost is charged, so the "
                "strategy never beat the benchmark on a like-for-like basis."
                if e0 <= 0
                else "The edge is still positive at 1000bp, because the benchmark holds "
                "every coin every day and turns over far more — so a rising cost hurts "
                "the benchmark faster than it hurts the strategy, and the gap WIDENS. "
                "That is a real property of a book that sits in cash half the time, and "
                "it is not a licence to ignore the cost: the strategy's own absolute "
                "return still falls at every tier."
            )
        )
    else:
        verdict = (
            f"**The edge breaks even at {be:.0f} bp** of one-way cost per unit of "
            f"turnover. Below that the strategy beats the equal-weight universe on a "
            f"like-for-like basis; above it, it does not."
        )
    return f"""## Charging the rebalancing cost

D183 charged nothing for moving capital between coins and named that as the test of its own
result. This charges it — **on the benchmark too**, because the equal-weight universe
rebalances daily as well and charging only the strategy would rig the comparison.

Turnover is one-way, `0.5 * sum |drifted weight - target weight|`, and buy-and-hold is
charged nothing after its initial purchase because it does not trade again.

Net Sharpe at each cost level:

{header}
{NL.join(rows)}

Strategy edge over the equal-weight universe: {edges}.

{verdict}

**A flat book holds cash and moving cash is free**, which the turnover measure gets right
on its own: a flat book reports exactly 0.0, so its slice does not drift. What is still
over-charged is a flat book joining or leaving the live set, counted as a full slice
traded when it was cash — and over-charging is the right direction for a test built to
threaten a result."""


def _weight_block(p: dict) -> str:
    pf = p["portfolio"]
    return f"""## How the risk budget splits, and the flaw it carries

Mean weight on the LONG portfolio: **{pf["mean_long_weight"]:.3f}**. Long/short correlation
**{pf["correlation"]:+.4f}**; the weighting fell back to 50/50 on {pf["n_fallback_bars"]:,}
bars.

{_weight_reading(pf)}"""


def _weight_reading(pf: dict) -> str:
    """Read the weight off the run rather than asserting it.

    I wrote the opposite of this into the report before running it — that aggregation
    would make the D181 weighting flaw bite LESS at portfolio level, because the short arm
    is in the market far more often once 62 coins are pooled. Hardcoded prose drifting
    from computed data is the single most repeated defect in this project, so the claim is
    now derived."""
    w = pf["mean_long_weight"]
    if w < 0.389:  # the worst single-coin figure, BTC, from D181
        return (
            f"Inverse-vol weighting reads a book that is flat most of the time as low-risk, "
            f"when what it actually is, is absent (D181). **Aggregation makes this WORSE, "
            f"not better.** Pooling 62 coins diversifies the short arm's own returns, which "
            f"lowers its measured volatility, which inverse-vol rewards with MORE weight — "
            f"so the losing leg carries {1 - w:.0%} of the risk budget here against 61% on "
            f"BTC alone (D181). The construction pays a book for being diversified and for "
            f"being absent, and neither is a reason to give it capital."
        )
    return (
        f"Inverse-vol weighting reads a book that is flat most of the time as low-risk, when "
        f"what it actually is, is absent (D181). Pooling 62 coins raises the short arm's "
        f"in-the-market share above any single coin's, and the long leg ends up with "
        f"{w:.1%} of the risk budget against 38.9% on BTC alone — so aggregation bites less "
        f"here than per symbol. It is the same construction and it is not fixed."
    )


def _breadth_conditional(p: dict) -> str:
    """Does H1 survive dropping the thin early sample?

    The pre-registration named this as the way H1 could hold for the wrong reason: a
    one-coin portfolio is a coin, and the earliest dates have almost nothing admitted."""
    ser, breadth = p["series"], p["breadth"]
    w = p["min_bars"]
    rows = []
    for k in (1, 5, 10, 20, 30):
        idx = [i for i, (_, nl, _) in enumerate(breadth) if nl >= k and i >= w]
        if len(idx) < 60:
            continue
        lr = [ser["long"][i] for i in idx]
        cr = [ser["combined"][i - w] for i in idx if i - w < len(ser["combined"])]
        rows.append(
            f"| >= {k} | {len(idx):,} | {_sharpe_of(lr):+.3f} | {_sharpe_of(cr):+.3f} |"
        )
    return f"""## Does the long portfolio's Sharpe survive dropping the thin early sample?

The pre-registration named this as the way H1 could hold for the wrong reason. Each row
keeps only the dates on which at least that many long books were open, and rescores.

| Long books live | Dates kept | Long portfolio Sharpe | Combined Sharpe |
|---|---|---|---|
{NL.join(rows)}

The rows above 5 are identical because the universe fills in quickly: there is essentially
no period with between five and thirty coins live, so every threshold past five selects the
same 2,708 dates.

A Sharpe that climbed as the thin dates were dropped would mean the early, near-single-coin
period was dragging the headline down; one that collapsed would mean the headline was that
period's luck. Conditioning on breadth is not a free lunch either — it is a filter applied
after the fact, and the rows are a robustness reading rather than a tradable variant."""


def _sharpe_of(returns: list[float]) -> float:
    import math

    if len(returns) < 2 or len(set(returns)) < 2:
        return 0.0
    mean = statistics.fmean(returns)
    sd = statistics.stdev(returns)
    rf_per_bar = 0.04 / 365.0
    return (mean - rf_per_bar) / sd * math.sqrt(365.0) if sd else 0.0


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

"""Capacity: does the cross-sectional portfolio edge exist at size? (D186)

D183 found a long portfolio at +1.277 Sharpe against +1.196 for a daily-rebalanced
equal-weight universe — a like-for-like edge of +0.081. D185 charged the rebalancing cost
D183 had named as the test of itself, and the edge barely moved: +0.078, break-even at
972bp. Both records closed by naming the same next question:

    A turnover charge is not a liquidity model. Nothing here says the required size could
    be traded in these coins at all.

Every number in this project so far assumes a fill at the quoted price regardless of size,
on 62 small-cap alts, rebalanced daily. This charges square-root market impact (D66) and
sweeps total AUM to find where the edge dies.

    uv run python scripts/run_capacity_portfolio.py

**The benchmark is charged impact too**, on the principle D185 established for the
rebalancing cost: charging only the strategy rigs the comparison. A passive basket is more
capacity-tolerant and the study should show that rather than assume it.

**The coefficient is 1.0 and is not swept** — D66's Y ≈ 1 convention, the same value
`pairs_study.py` uses. Tuning it would be a search for whichever capacity number flattered
the book.
"""

from __future__ import annotations

import dataclasses
import json
import math
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backtest_framework.costs.calibration import calibrate_impact_params
from backtest_framework.data.cleaner import clean
from backtest_framework.data.corporate_actions import load_events_json
from backtest_framework.data.csv_fixture import load_fixture_csv_with_volumes
from backtest_framework.data.snapshot_store import SnapshotStore
from backtest_framework.registry.trial_registry import TrialRegistry
from backtest_framework.research import breakout_study as bs
from backtest_framework.research import breakout_universe as bu
from backtest_framework.validation.dsr import deflated_sharpe_ratio

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_portfolio_universe import (  # noqa: E402
    D184_ARTIFACTS,
    _charge,
    _equal_weight_arm,
    dated_returns,
)

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.csv.gz"
META = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw.meta.json"
EVENTS = REPO / "data" / "fixtures" / "crypto_universe_2015_2025_raw_events.json"
REGISTRY_PATH = REPO / "data" / "capacity_portfolio_registry.sqlite"
LONG_SUMMARY = REPO / "data" / "breakout_study_summary.json"
RESULTS = REPO / "docs" / "results" / "capacity_portfolio.md"
SUMMARY_JSON = REPO / "data" / "capacity_portfolio_summary.json"

NL = "\n"

AUM_LEVELS = (100e3, 300e3, 1e6, 3e6, 10e6, 30e6, 100e6)
"""Total book size. Per-coin slice is AUM / 62 — the steady-state share of an equal-weight
book, not the instantaneous one, since breadth varies. Stated rather than hidden: early in
the sample far fewer coins are live and the real slice is larger."""

IMPACT_COEFFICIENT = 1.0
"""D66's Y ~ 1 convention, and `pairs_study.py:82` uses the same. Not swept."""

REBALANCE_BPS = 40.0
"""The between-coin rebalancing charge from D185, held at the reference tier throughout so
this study varies ONE thing: size."""

DSR_POOL_TIER = bs.REFERENCE_TIER
"""The trial pool for the portfolio's deflated Sharpe is READ from the long study's own
published DSR inputs (D183's second debt), not asserted here.

`data/breakout_study_summary.json` records `n_trials` and `var_trials_daily` per symbol per
tier — the actual search that produced the baseline. Hardcoding "30" would be a
self-reported trial count, which is the specific thing D20/D21 built the registry to
prevent.

The portfolio runs ONE configuration — but that configuration is the survivor of that
search, so the pool is the search. Not 1, and not 62: **holding a selected rule on more
instruments does not undo the selection that produced it.**"""


def _impact_tier(coefficient: float) -> bs.CostTier:
    """The reference tier, plus impact. Capacity is a reference-tier question, and running
    all four tiers would quadruple the runtime for a sensitivity nobody reads here."""
    ref = next(t for t in bs.DEFAULT_TIERS if t.name == bs.REFERENCE_TIER)
    return dataclasses.replace(ref, impact_coefficient=coefficient)


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
        load_events_json(EVENTS),
        volumes_by_symbol=raw_volumes,
        cleaning_report=cleaning_report,
        validation=None,
        extra_meta={"source_fixture": FIXTURE.name, "study": "capacity_portfolio_v1"},
    )
    snapshot = store.load(snapshot_id)
    # Re-index volumes onto the CLEANED bars. `clean()` drops bad prints and does not
    # re-index the volume list it was handed, so the two are misaligned by construction
    # after any drop (D111's precedent, handled by `align_volumes`). Impact calibrates ADV
    # from this series, so a misalignment here would quietly mis-price every fill.
    volumes = {
        s: bu.align_volumes(cleaned[s], raw_bars[s], raw_volumes[s]) for s in cleaned
    }
    cohorts = json.loads(META.read_text(encoding="utf-8"))["cohort_by_symbol"]

    if REGISTRY_PATH.exists():
        REGISTRY_PATH.unlink()
    registry = TrialRegistry(REGISTRY_PATH)
    base_study = bs.BreakoutStudyConfig()
    tier = _impact_tier(IMPACT_COEFFICIENT)

    levels: dict[str, Any] = {}
    dates_ref: list[str] = []
    for aum in AUM_LEVELS:
        per_coin = aum / 62.0
        study = dataclasses.replace(base_study, starting_cash=per_coin)
        print(f"AUM ${aum:,.0f}  (${per_coin:,.0f} per coin) ...", flush=True)
        run = bu.run_universe_study(
            snapshot.bars_by_symbol,
            volumes,
            registry,
            snapshot_id,
            cohorts=cohorts,
            study=study,
            tiers=(tier,),
            trial_id_prefix=f"capacity-{int(aum)}",
            variant=bu.baseline_variant(),
            progress=lambda m: None,
            # This study deflates against the LONG BOOK's published trial pool, not a
            # cross-section of 62 symbols running one configuration. It also must skip
            # the built-in DSR because at large AUM impact makes coins untradeable, their
            # returns go flat, and `_dsr_for` rightly refuses a pool with an undefined
            # Sharpe in it. A study whose FINDING is "coins go inert at size" cannot be
            # stopped by a guard against inert coins — so they are counted below instead.
            compute_dsr=False,
        )
        per_symbol = {}
        killed = []
        for symbol, srun in run.runs.items():
            dated, died = dated_returns(srun.by_tier[tier.name].variant.oos_equity)
            per_symbol[symbol] = dict(dated)
            # A book whose NAV reaches zero has been DESTROYED by its own trading costs:
            # at this size the impact of entering a thin coin exceeds what the position
            # can bear. No long book dies at zero impact, so every name here is impact
            # doing it. That is the capacity limit arriving coin by coin rather than as a
            # smooth Sharpe decay, and it is the most concrete thing this study finds.
            if died:
                killed.append(symbol)
        dates = sorted({d for s in per_symbol.values() for d in s})
        dates_ref = dates_ref or dates
        gross, turn = _equal_weight_arm(dates, per_symbol)
        net = _charge(gross, turn, REBALANCE_BPS)
        w = 252
        levels[str(int(aum))] = {
            "aum": aum,
            "per_coin": per_coin,
            **_stats(net[w:], base_study),
            "mean_daily_turnover": statistics.fmean(turn[w:]) if len(turn) > w else 0.0,
            "n_killed": len(killed),
            "killed": sorted(killed),
            # Popped in build_payload once the DSR's skew/kurt are computed from it; it
            # would otherwise bloat the summary with seven copies of a 3,500-point series.
            "_net": net[w:],
        }

    payload = build_payload(levels, snapshot, volumes, dates_ref, base_study, snapshot_id)
    SUMMARY_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    RESULTS.write_text(build_report(payload), encoding="utf-8")
    print(f"swept {len(AUM_LEVELS)} AUM levels in {time.time() - started:.0f}s")
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


def build_payload(levels, snapshot, volumes, dates, study, snapshot_id) -> dict:
    # ---- the benchmark, charged impact on the SAME terms ----------------------------
    # A passive equal-weight basket also has to trade to hold its weights, and it holds
    # every coin every day. Charging only the strategy would rig the comparison — the
    # principle D185 established for the rebalancing cost, applied to impact.
    # Crypto fixtures report quote-currency notional, not units (D187). Saying so is
    # mandatory: the default is the equity convention and guessing wrong scales every
    # impact charge by the square root of the price.
    params = calibrate_impact_params(
        snapshot.bars_by_symbol, volumes, volume_units="quote_notional"
    )
    raw: dict[str, dict[str, float]] = {}
    prices: dict[str, dict[str, float]] = {}
    for symbol, bars in snapshot.bars_by_symbol.items():
        r, px = {}, {}
        for a, b in zip(bars, bars[1:]):
            d = b.timestamp.date().isoformat()
            if a.bar.close > 0 and (symbol, d) not in D184_ARTIFACTS:
                r[d] = b.bar.close / a.bar.close - 1.0
                px[d] = b.bar.close
        raw[symbol], prices[symbol] = r, px
    bench_gross, bench_turn = _equal_weight_arm(dates, raw)

    w = 252
    bench_levels = {}
    for aum in AUM_LEVELS:
        # Impact on the benchmark's own rebalancing: each date it trades `turnover * AUM`
        # of notional, spread across the live coins, and pays sqrt-impact on its share.
        drag = []
        for i, d in enumerate(dates):
            live = [s for s in raw if d in raw[s]]
            if not live or bench_turn[i] <= 0:
                drag.append(0.0)
                continue
            notional = bench_turn[i] * aum / len(live)
            frac = 0.0
            for s in live:
                p = prices[s].get(d, 0.0)
                if p <= 0 or s not in params:
                    continue
                q = notional / p
                frac += (
                    IMPACT_COEFFICIENT
                    * params[s].sigma_daily
                    * math.sqrt(q / params[s].adv_shares)
                )
            drag.append(bench_turn[i] * (frac / len(live)))
        net = [
            g - t * REBALANCE_BPS / 10_000.0 - dr
            for g, t, dr in zip(bench_gross, bench_turn, drag)
        ]
        bench_levels[str(int(aum))] = {"aum": aum, **_stats(net[w:], study)}

    edges = {
        k: levels[k]["sharpe"] - bench_levels[k]["sharpe"] for k in levels
    }
    # ---- D183's second debt: deflate the portfolio against the pool that selected it --
    # UNITS (D98, where an earlier bug in this project lived): sr, t and var_trials must
    # all be per-period. `var_trials_daily` is daily, so the portfolio's annual Sharpe is
    # divided down rather than the pool variance scaled up.
    pool = json.loads(LONG_SUMMARY.read_text(encoding="utf-8"))["symbols"]
    inputs = [v["dsr_inputs_by_tier"][DSR_POOL_TIER] for v in pool.values()]
    n_trials = max(int(i["n_trials"]) for i in inputs)
    var_trials = max(float(i["var_trials_daily"]) for i in inputs)
    smallest = levels[str(int(AUM_LEVELS[0]))]
    net = smallest.pop("_net")
    sr_daily = smallest["sharpe"] / math.sqrt(study.periods_per_year)
    mu = statistics.fmean(net)
    sd = statistics.pstdev(net)
    skew = statistics.fmean([((x - mu) / sd) ** 3 for x in net]) if sd > 0 else 0.0
    kurt = statistics.fmean([((x - mu) / sd) ** 4 for x in net]) if sd > 0 else 3.0
    dsr = deflated_sharpe_ratio(
        sr=sr_daily, t=smallest["n_bars"], skew=skew, kurt=kurt,
        n_trials=n_trials, var_trials=var_trials,
    )
    for lvl in levels.values():
        lvl.pop("_net", None)
    return {
        "snapshot_id": snapshot_id,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "reference_tier": bs.REFERENCE_TIER,
        "impact_coefficient": IMPACT_COEFFICIENT,
        "rebalance_bps": REBALANCE_BPS,
        "aum_levels": list(AUM_LEVELS),
        "strategy": levels,
        "benchmark": bench_levels,
        "edges": edges,
        "deflated_sharpe": {
            "at_aum": AUM_LEVELS[0],
            "n_trials": n_trials,
            "var_trials_daily": var_trials,
            "observed_sharpe_annual": smallest["sharpe"],
            "observed_sr_daily": sr_daily,
            "t": smallest["n_bars"],
            "skew": skew,
            "kurt": kurt,
            "dsr": dsr,
        },
    }


def build_report(p: dict) -> str:
    rows = []
    for aum in p["aum_levels"]:
        k = str(int(aum))
        s, b = p["strategy"][k], p["benchmark"][k]
        rows.append(
            f"| ${aum / 1e6:,.1f}M | ${aum / 62 / 1e3:,.0f}k | {s['sharpe']:+.3f} | "
            f"{s['total_return'] * 100:+,.0f}% | {s['max_drawdown'] * 100:.1f}% | "
            f"{s.get('n_killed', 0)} | {b['sharpe']:+.3f} | **{p['edges'][k]:+.3f}** |"
        )
    d = p["deflated_sharpe"]
    return f"""# Capacity: does the portfolio edge exist at size?

**Produced:** {p["generated_utc"][:10]} ·
**Snapshot:** `{p["snapshot_id"]}` ·
**Reproduce:** `uv run python scripts/run_capacity_portfolio.py` (offline, deterministic)

## What this charges

Every number in this project before D186 assumed a fill at the quoted price **regardless of
size** — on 62 small-cap alts, rebalanced daily. This charges square-root market impact
(D66):

    impact_fraction = {p["impact_coefficient"]} x sigma_daily x sqrt(|Q| / ADV)

so total impact dollars scale as Q^1.5. The coefficient is D66's Y ~ 1 convention and is
**not swept**. Sigma and ADV are calibrated per coin from the snapshot's own bars and
volumes, and a coin with missing or zero volume **raises** rather than defaulting (D48).

The between-coin rebalancing charge from D185 stays fixed at {p["rebalance_bps"]:.0f} bp
throughout, so this study varies exactly one thing: **size**.

**The benchmark is charged impact too.** A passive equal-weight basket also trades to hold
its weights, and it holds every coin every day. Charging only the strategy would rig the
comparison — the principle D185 established, applied to impact.

Reference tier `{p["reference_tier"]}` only: capacity is a reference-tier question and four
tiers would quadruple the runtime for a sensitivity nobody reads here.

## The sweep

| Total AUM | Per coin | Strategy Sharpe | Return | Max DD | Books destroyed | Benchmark Sharpe | Edge |
|---|---|---|---|---|---|---|---|
{NL.join(rows)}

{_verdict(p)}

{_killed_block(p)}

## The deflated Sharpe — D183's second debt

At ${d["at_aum"] / 1e6:,.1f}M the portfolio scores **{d["observed_sharpe_annual"]:+.3f}**
annualised. Deflated against **{d["n_trials"]} trials** (V[SRn] = {d["var_trials_daily"]:.2e} daily,
both read from the long study's own published DSR inputs rather than asserted here), DSR =
**{d["dsr"]:.4f}**.

The portfolio runs **one** configuration — but that configuration is the survivor of a
{d["n_trials"]}-configuration search on the long book, so the pool is {d["n_trials"]}. Not
1, and not 62: **holding a selected rule on more instruments does not undo the selection
that produced it.**

Units are per-period throughout (D98): observed SR {d["observed_sr_daily"]:.5f} daily over
{d["t"]:,} bars, skew {d["skew"]:+.3f}, kurtosis {d["kurt"]:.2f}. Feeding an annualised
Sharpe against a daily pool variance would inflate the noise floor ~19x and force the DSR
to zero regardless of the strategy — the exact bug D98 was written to close.

## Standing caveats

1. **Impact is calibrated FULL-SAMPLE** (D66's stated caveat, carried forward verbatim):
   sigma and ADV come from the whole series. A mild look-ahead in cost parameters, never in
   the signal. Per-window calibration remains deferred.
2. **A square-root impact model is not a liquidity model.** It says what a fill costs, not
   whether a counterparty exists. On a delisted coin the honest answer is that the trade
   does not happen at any price, and no coefficient expresses that.
3. **The per-coin slice is AUM / 62**, the steady-state share. Early in the sample far
   fewer coins are live and the real slice is larger, so early-period impact is understated.
4. **ADV is the whole-period mean.** A coin's volume in 2016 and in 2025 differ by orders of
   magnitude, and one average across both flatters the thin years.
5. Everything D183 and D185 carry still applies: one crypto cross-section, one
   bull-dominated decade, no out-of-sample test on a cross-section this one does not contain.
"""


def _killed_block(p: dict) -> str:
    """Books destroyed by their own trading costs as size rises.

    This is the capacity limit in its most concrete form. A Sharpe drifting down is an
    average; this is an account reaching zero."""
    rows = []
    for aum in p["aum_levels"]:
        lvl = p["strategy"][str(int(aum))]
        n = lvl.get("n_killed", 0)
        if n:
            names = ", ".join(f"`{s}`" for s in lvl.get("killed", [])[:8])
            more = "" if n <= 8 else f" and {n - 8} more"
            rows.append(f"| ${aum / 1e6:,.1f}M | {n} | {names}{more} |")
    if not rows:
        return (
            "**No book was destroyed at any size tested.** Impact made the fills worse "
            f"all the way to ${p['aum_levels'][-1] / 1e6:,.0f}M; it did not wipe an "
            "account out."
        )
    return f"""### Books destroyed by their own trading costs

**No long book dies at zero impact** (D183), so every name below is impact doing it: at
this size the cost of entering a thin coin exceeds what the position can bear, and the
account reaches zero.

| Total AUM | Books destroyed | Which |
|---|---|---|
{NL.join(rows)}

**Read this as the model's own edge, not only as a result.** A square-root impact charge
large enough to destroy an account is a charge outside the range the functional form was
calibrated for — D66 fits a cost, not a bankruptcy. The honest reading is that the trade
does not exist at this size, which is the same answer, arrived at less gracefully."""


def _verdict(p: dict) -> str:
    levels = p["aum_levels"]
    edges = [p["edges"][str(int(a))] for a in levels]
    sharpes = [p["strategy"][str(int(a))]["sharpe"] for a in levels]
    dead = [a for a, e in zip(levels, edges) if e <= 0]
    drop = sharpes[0] - sharpes[-1]
    head = (
        f"**The edge dies at ${dead[0] / 1e6:,.1f}M.** Below it the strategy beats the "
        f"equal-weight universe; at and above it, it does not."
        if dead
        else f"**The edge survives every level tested, to ${levels[-1] / 1e6:,.0f}M.** "
        f"It runs {edges[0]:+.3f} at the smallest size and {edges[-1]:+.3f} at the "
        f"largest."
    )
    return (
        f"{head}{NL}{NL}The strategy's own Sharpe falls {sharpes[0]:+.3f} → "
        f"{sharpes[-1]:+.3f} across the sweep, a loss of **{drop:.3f}**. Impact is the only "
        f"thing that changes between rows — same signal, same rebalancing charge, same "
        f"span."
    )


if __name__ == "__main__":
    raise SystemExit(main())

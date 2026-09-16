"""D242 — the uptrend arm and the combined book on withheld data.

    A0   uptrend onset + 63-bar age cap
    A2   A0 plus a fixed -8% stop
    C0   S1 + A2 on one shared pool at TOTAL = 100% (the allocator is inert there)

THE RULES ARE FROZEN. Every constant is asserted equal to `run_uptrend_onset`'s
at import. If one differs between the mined run and this one, the test is void
and the runner says so rather than quietly measuring a different rule.

WHAT THIS FIXTURE CAN AND CANNOT SHOW. 60 ETFs sharing ZERO tickers with the
mined 57, same 1,515-bar span, so it has the same power -- unlike D237's T3. But
the two universes correlate +0.978 and both sit inside the 2018-2024 market. This
is an INSTRUMENT holdout, not a time holdout.

H4 IS KEPT SEPARATE FROM H1-H3 ON PURPOSE. "The entry replicated" and "the stop
replicated" are different claims, and D242 predicts they will differ.

WRITTEN FRESH: NOTHING. Every component already exists and is tested -- a holdout
test that needed new code would be a holdout test whose code had never been
checked.

Offline, deterministic, seed 0. `--report-only` re-renders from the artifact.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import macd as M  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


B = _load("d241_combined", "run_combined_book.py")
U, X, L, S, J = B.U, B.X, B.L, B.S, B.J

SUMMARY = REPO / "data" / "uptrend_withheld_summary.json"
RESULTS = REPO / "docs" / "results" / "UPTREND_WITHHELD_RESULTS.md"
FIX = REPO / "data" / "fixtures"

SEED, PPY = X.SEED, X.PPY
RF_ANNUAL = X.RF_ANNUAL
N_SIMS = X.N_SIMS

# D242's frozen constants, asserted against the mined runner. This is the whole
# integrity of a holdout test: the rule may not drift.
FROZEN = {"K": 3, "WINDOW": 252, "AGE_CAP": 63, "ATR_WINDOW": 21,
          "STOP_ATR": 1.0, "FLOOR_ATR": 2.0, "FIXED_STOP": 0.08, "TARGET_R": 2.0}
for _k, _v in FROZEN.items():
    assert getattr(U, _k) == _v, f"{_k} drifted: {getattr(U, _k)} != {_v}"

# D237's anti-triviality floor, set the same way: 25% of the mined delta.
MINED = {"A0": 0.610, "A2": 0.822, "S1": 0.746, "BH_MINED": 0.235}
H3_FLOOR = 0.25 * (MINED["A2"] - MINED["BH_MINED"])      # +0.147

FIXTURES = {
    "mined": (FIX / "universe_daily_2015_2024_raw.csv.gz",
              FIX / "universe_daily_2015_2024_raw_events.json"),
    "holdout": (FIX / "universe_holdout_daily_raw.csv.gz",
                FIX / "universe_holdout_daily_raw_events.json"),
}
CELL_ORDER = ("S1", "A0", "A2", "C0")


def books_on(which: str):
    """Every book on one fixture. `L.FIXTURE`/`L.EVENTS` are repointed exactly as
    `run_withheld_test.run_test` does it -- the loader, cleaning, per-symbol costs
    and dividend frame are D217's and unchanged."""
    L.FIXTURE, L.EVENTS = FIXTURES[which]
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    md, hs, ok = S.base_masks(panel, cleaned, start)
    s1 = S.hold_book((hs > 0) & (md <= 0) & ok, start)
    up, g_lo, i_lo, atr = U.signals(panel, cleaned, start)
    a0, _, _ = U.walk(panel, up, g_lo, i_lo, atr, start)
    a2, base_trades, cuts = U.walk(panel, up, g_lo, i_lo, atr, start, stop_mode="fixed")
    granted, _ = B.allocate({"S1": s1, "A2": a2}, start, 1.0, {"S1": 0.0, "A2": 0.0})
    c0 = granted["S1"] + granted["A2"]
    assert np.array_equal(c0, np.maximum(s1, a2)), "the allocator rationed at full capital"

    ones = np.ones_like(s1)
    ones[:, :start] = 0.0
    return panel, start, {"S1": s1, "A0": a0, "A2": a2, "C0": c0}, ones, base_trades, cuts


def build() -> dict:
    t0 = time.time()

    # The mined fixture first: a holdout runner that cannot reproduce the training
    # result is measuring something else.
    _, _, mb, _, _, _ = books_on("mined")
    _p, _s = None, None
    L.FIXTURE, L.EVENTS = FIXTURES["mined"]
    _p, _c = L.load_panel()
    _s = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    repro = {k: X.score(_p, mb[k], _s)["excess_sharpe"] for k in ("S1", "A0", "A2")}
    for k in ("S1", "A0", "A2"):
        assert abs(repro[k] - MINED[k]) < 5e-4, f"{k} did not reproduce: {repro[k]}"

    panel, start, books, ones, base_trades, cuts = books_on("holdout")
    cells = {k: X.score(panel, books[k], start) for k in CELL_ORDER}
    bh = X.score(panel, ones, start)

    def excess(pos):
        tot = X.signed_log_returns(panel, pos, total_return=True)[start:]
        return X.excess_of(tot, pos, start)

    r = {k: excess(books[k]) for k in CELL_ORDER}

    # H2 -- the matched-count rotation null, on the entry rules
    nl = X.rotation_nulls(panel, {"A0": books["A0"], "A2": books["A2"]}, start)
    nulls = {}
    for k, draws in nl["draws"].items():
        actual = cells[k]["excess_sharpe"]
        nulls[k] = {
            "p50": float(np.percentile(draws, 50)), "p95": float(np.percentile(draws, 95)),
            "percentile_of_actual": float((draws < actual).mean() * 100.0),
            "money_percentile_of_actual": float(
                (nl["money"][k] < cells[k]["total_return"]).mean() * 100.0),
            "vol_ratio": float(cells[k]["vol"] / np.percentile(nl["vol"][k], 50)),
            "clears_H2": bool(actual > float(np.percentile(draws, 95))),
        }

    # H4 -- R7's matched-exit-count overlay null on the -8% stop
    rng = np.random.default_rng(SEED)
    pool = np.array([f for _, f in cuts]) if cuts else np.array([1.0])
    draws = np.empty(N_SIMS)
    for s in range(N_SIMS):
        draws[s] = X._excess_sharpe(
            panel, U.null_book(panel, base_trades, len(cuts), pool, rng, start), start)
    a2_sh = cells["A2"]["excess_sharpe"]
    h4 = {"n_cut": len(cuts), "n_trades": len(base_trades),
          "p50": float(np.percentile(draws, 50)), "p95": float(np.percentile(draws, 95)),
          "percentile_of_actual": float((draws < a2_sh).mean() * 100.0),
          "clears_H4": bool(a2_sh > float(np.percentile(draws, 95)))}

    # H1 / H3 on the two entry rules
    verdict = {}
    for k in ("A0", "A2"):
        d = cells[k]["excess_sharpe"] - bh["excess_sharpe"]
        verdict[k] = {
            "delta_vs_bh": d,
            "clears_H1": bool(cells[k]["excess_sharpe"] > 0 and d > 0),
            "clears_H3": bool(d >= H3_FLOOR),
            "clears_H2": nulls[k]["clears_H2"],
            "clears_all": bool(cells[k]["excess_sharpe"] > 0 and d > 0
                               and nulls[k]["clears_H2"] and d >= H3_FLOOR),
            "mined": MINED[k],
            "shrinkage": (cells[k]["excess_sharpe"] / MINED[k] - 1.0) if MINED[k] else None,
        }

    # H5 / H6 -- the combined book
    boot = J.paired_block_bootstrap(r["C0"], r["S1"])
    h56 = {"delta_vs_S1": cells["C0"]["excess_sharpe"] - cells["S1"]["excess_sharpe"],
           "p05": boot["p05"], "p95": boot["p95"],
           "clears_H5": bool(cells["C0"]["excess_sharpe"] > cells["S1"]["excess_sharpe"]),
           "clears_H6": bool(cells["C0"]["excess_sharpe"] > cells["S1"]["excess_sharpe"]
                             and boot["p05"] > 0.0)}

    rho = float(np.corrcoef(r["S1"], r["A2"])[0, 1])
    reading = {
        (True, True): "THE STRONGEST RESULT THE PROGRAMME HAS PRODUCED. Still one era and a "
                      "+0.978-correlated universe -- the next step is more forward time, not "
                      "capital.",
        (True, False): "THE ENTRY GENERALISES; THE STOP WAS FITTED. A0 is the candidate, A2 is "
                       "retired, and D240's headline is corrected in writing.",
        (False, True): "INCOHERENT -- a stop cannot rescue an entry that does not generalise. "
                       "Treat as failure and investigate the overlay null.",
        (False, False): "THE ARM DOES NOT GENERALISE. CLOSED, with no variant and no third "
                        "fixture.",
    }[(verdict["A0"]["clears_all"], verdict["A2"]["clears_all"])]

    return {
        "produced": "D242", "stage": "VERDICT -- withheld 60-ETF fixture",
        "seed": SEED, "n_sims": N_SIMS, "frozen": FROZEN, "h3_floor": H3_FLOOR,
        "mined_reproduction": repro,
        "n_symbols": len(panel.symbols), "live_bars": len(panel.dates) - start,
        "first_live_date": panel.dates[start], "last_date": panel.dates[-1],
        "cells": cells, "buy_and_hold": bh, "nulls": nulls, "overlay_null": h4,
        "verdict": verdict, "combined": h56, "rho_S1_A2": rho,
        "deployable_return": {
            k: float(np.expm1(np.log1p(cells[k]["cagr"])
                              + math.log1p(RF_ANNUAL) * (1 - cells[k]["exposure_gross"])))
            for k in CELL_ORDER},
        "reading": reading,
        "arm_closed": not verdict["A0"]["clears_all"],
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    c, n, v, dep = p["cells"], p["nulls"], p["verdict"], p["deployable_return"]
    bh, h4, cm = p["buy_and_hold"], p["overlay_null"], p["combined"]
    o = ["# D242 — the uptrend arm and the combined book on withheld data\n"]
    o.append("**STAGE 2 — THE VERDICT.** 60 ETFs sharing zero tickers with the mined 57.\n")
    o.append(
        f"*seed {p['seed']}, {p['n_sims']:,} sims, {p['elapsed_seconds']}s. "
        f"{p['n_symbols']} ETFs x {p['live_bars']:,} live bars, "
        f"{p['first_live_date'][:10]} .. {p['last_date'][:10]}. "
        f"Every constant frozen and asserted against the mined runner.*\n"
    )
    o.append(
        "**What this cannot show, stated before the run:** the two universes correlate "
        "**+0.978** and both sit inside the 2018–2024 market. This is an **instrument** "
        "holdout, not a time holdout.\n"
    )
    o.append("## The books on withheld data\n")
    o.append("| | exposure | excess Sharpe | *mined* | shrinkage | CAGR | deployable | "
             "max DD | Calmar | E |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        x = c[k]
        cal = x["cagr"] / abs(x["max_drawdown"]) if x["max_drawdown"] else float("nan")
        mn = v.get(k, {}).get("mined")
        sh = v.get(k, {}).get("shrinkage")
        o.append(
            f"| **{k}** | {x['exposure_gross']:.1%} | **{x['excess_sharpe']:+.3f}** | "
            f"{f'*{mn:+.3f}*' if mn else '—'} | {f'{sh * 100:+.1f}%' if sh is not None else '—'} | "
            f"{x['cagr'] * 100:.2f}% | {dep[k] * 100:.2f}% | "
            f"{x['max_drawdown'] * 100:+.2f}% | {cal:.3f} | "
            f"{'✓' if x['clears_E'] else '✗'} |"
        )
    o.append(
        f"| *B&H* | *100.0%* | *{bh['excess_sharpe']:+.3f}* | — | — | "
        f"*{bh['cagr'] * 100:.2f}%* | *{bh['cagr'] * 100:.2f}%* | "
        f"*{bh['max_drawdown'] * 100:+.2f}%* | "
        f"*{bh['cagr'] / abs(bh['max_drawdown']):.3f}* | — |"
    )
    o.append("")

    o.append("## H1–H3 — the entry rules\n")
    o.append(f"*H3's floor is **{p['h3_floor']:+.3f}** — 25% of the mined delta, set the way "
             "D237 set its own.*\n")
    o.append("| | excess Sharpe | Δ vs B&H | rot null p95 | percentile | money pct | "
             "H1 | H2 | H3 | **all** |")
    o.append("|---|---:|---:|---:|---:|---:|:--:|:--:|:--:|:--:|")
    for k in ("A0", "A2"):
        q, nn = v[k], n[k]
        o.append(
            f"| **{k}** | {c[k]['excess_sharpe']:+.3f} | **{q['delta_vs_bh']:+.3f}** | "
            f"{nn['p95']:+.3f} | **{nn['percentile_of_actual']:.1f}th** | "
            f"{nn['money_percentile_of_actual']:.1f}th | "
            f"{'✓' if q['clears_H1'] else '✗'} | {'✓' if q['clears_H2'] else '✗'} | "
            f"{'✓' if q['clears_H3'] else '✗'} | "
            f"**{'✓' if q['clears_all'] else '✗'}** |"
        )
    o.append("")

    o.append("## H4 — did the −8% stop's edge replicate?\n")
    o.append(
        "*R7's matched-exit-count overlay null: keep A0's book, cut the same number of trades "
        "short at random trades and random points inside their own spans. Kept separate from "
        "H1–H3 so that \"the entry replicated\" and \"the stop replicated\" cannot be "
        "conflated.*\n"
    )
    o.append(
        f"| trades cut | actual | null p50 | null p95 | **percentile** | H4 |\n"
        f"|---:|---:|---:|---:|---:|:--:|\n"
        f"| {h4['n_cut']} of {h4['n_trades']} | **{c['A2']['excess_sharpe']:+.3f}** | "
        f"{h4['p50']:+.3f} | {h4['p95']:+.3f} | **{h4['percentile_of_actual']:.1f}th** | "
        f"{'✓' if h4['clears_H4'] else '✗'} |\n"
    )

    o.append("## H5 / H6 — the combined book\n")
    o.append(
        f"| | excess Sharpe |\n|---|---:|\n"
        f"| S1 alone | {c['S1']['excess_sharpe']:+.3f} |\n"
        f"| **C0 combined** | **{c['C0']['excess_sharpe']:+.3f}** |\n"
        f"| **delta** | **{cm['delta_vs_S1']:+.3f}** |\n"
        f"| bootstrap p05 | {cm['p05']:+.3f} |\n"
        f"| bootstrap p95 | {cm['p95']:+.3f} |\n"
        f"| **H5** (point estimate) | **{'✓' if cm['clears_H5'] else '✗'}** |\n"
        f"| **H6** (interval) | **{'✓' if cm['clears_H6'] else '✗'}** |\n"
    )
    o.append(f"**ρ between S1 and A2 on this fixture: `{p['rho_S1_A2']:+.4f}`** "
             f"(mined: +0.1586).\n")

    o.append("## The reading, as declared in advance\n")
    o.append(f"> **{p['reading']}**\n")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    if args.report_only:
        payload = json.loads(SUMMARY.read_text(encoding="utf-8"))
    else:
        payload = build()
        SUMMARY.write_text(json.dumps(payload, indent=1, sort_keys=True), encoding="utf-8")
    RESULTS.write_text(render(payload), encoding="utf-8")

    c, v, n = payload["cells"], payload["verdict"], payload["nulls"]
    print()
    print(f"{'cell':5s} {'expo':>7s} {'exSh':>8s} {'mined':>8s} {'dBH':>8s} {'pctile':>8s} "
          f"{'maxDD':>8s}  H1 H2 H3")
    for k in CELL_ORDER:
        x = c[k]
        q = v.get(k)
        line = (f"{k:5s} {x['exposure_gross']:7.1%} {x['excess_sharpe']:+8.3f} "
                f"{q['mined']:+8.3f} {q['delta_vs_bh']:+8.3f} "
                f"{n[k]['percentile_of_actual']:7.1f}th {x['max_drawdown']:+8.2%}  "
                f"{'Y' if q['clears_H1'] else 'N'}  {'Y' if q['clears_H2'] else 'N'}  "
                f"{'Y' if q['clears_H3'] else 'N'}" if q else
                f"{k:5s} {x['exposure_gross']:7.1%} {x['excess_sharpe']:+8.3f} "
                f"{'—':>8s} {'—':>8s} {'—':>8s} {x['max_drawdown']:+8.2%}")
        print(line)
    b = payload["buy_and_hold"]
    print(f"{'B&H':5s} {100.0:6.1f}% {b['excess_sharpe']:+8.3f} {'—':>8s} {'—':>8s} "
          f"{'—':>8s} {b['max_drawdown']:+8.2%}")
    h4, cm = payload["overlay_null"], payload["combined"]
    print(f"\nH4 stop overlay: {h4['percentile_of_actual']:.1f}th percentile -> "
          f"{'CLEARS' if h4['clears_H4'] else 'FAILS'}")
    print(f"H5/H6 combined : C0 - S1 = {cm['delta_vs_S1']:+.3f} "
          f"[p05 {cm['p05']:+.3f}, p95 {cm['p95']:+.3f}] -> "
          f"H5 {'CLEARS' if cm['clears_H5'] else 'FAILS'}, "
          f"H6 {'CLEARS' if cm['clears_H6'] else 'FAILS'}")
    print(f"rho(S1, A2) = {payload['rho_S1_A2']:+.4f}  (mined +0.1586)")
    print()
    print(payload["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

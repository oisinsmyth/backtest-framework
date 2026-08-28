"""D243 — the book on extended history.

    S1  position = +1 if hist_L > 0 AND md_L <= 0
    S2  UPTREND := g_lo > 0 AND g_hi > 0; enter at onset, exit at age 63 or state end
    C   S1 + S2 on one shared pool at 100% capital

ONLY THE BOOK. No variants, no cells, no stop -- D242 retired the -8% stop after
it failed its overlay null out of sample. Zero fresh looks.

THE EXTENDED LIVE WINDOW CONTAINS THE TRAINING WINDOW, so it is NOT a clean
holdout and is not reported as one. It splits into:

    NEW      ~2013-11 .. 2018-12   never seen -- THE FIRST TIME-INDEPENDENT TEST
    TRAIN     2018-12 .. 2024-12   the window S1 and S2 were built on
    FORWARD   2024-12 .. 2026-08   spent by D237 for S1, unspent for S2

Every previous holdout was an INSTRUMENT holdout: the 60-ETF universe correlates
+0.978 with the 57, so D237 and D242 showed the rules are not fitted to particular
tickers and showed nothing about the era. The verdict here lives in NEW.

The split is applied to SCORED RETURNS, never to the signal, so the pre-2018
window is scored with exactly the warm-up it would have had.

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


W = _load("d242_withheld", "run_uptrend_withheld.py")
B, U, X, L, S, J = W.B, W.U, W.X, W.L, W.S, W.J

SUMMARY = REPO / "data" / "book_extended_summary.json"
RESULTS = REPO / "BOOK_EXTENDED_RESULTS.md"
FIX = REPO / "data" / "fixtures"

SEED, PPY, N_SIMS = X.SEED, X.PPY, X.N_SIMS
RF_ANNUAL = X.RF_ANNUAL

TRAIN_START = "2018-12-21"        # the mined fixture's first live bar
FORWARD_START = "2025-01-02"

# D237's construction, reused: 25% of the mined delta over buy-and-hold.
V3_FLOOR = {"S1": 0.25 * 0.511, "S2": 0.25 * 0.375}
ARMS = ("S1", "S2")
CELL_ORDER = ("S1", "S2", "C")

FIXTURES = {
    "extended": (FIX / "universe_daily_extended_raw.csv.gz",
                 FIX / "universe_daily_extended_raw_events.json"),
    "holdout_extended": (FIX / "universe_holdout_extended_raw.csv.gz",
                         FIX / "universe_holdout_extended_raw_events.json"),
}


def books_on(fixture, events):
    """S1, S2 and their union on one fixture. `run_uptrend_withheld.books_on` is
    the precedent; this one drops A2 because the stop is retired."""
    L.FIXTURE, L.EVENTS = fixture, events
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    md, hs, ok = S.base_masks(panel, cleaned, start)
    s1 = S.hold_book((hs > 0) & (md <= 0) & ok, start)
    up, g_lo, i_lo, atr = U.signals(panel, cleaned, start)
    s2, _, _ = U.walk(panel, up, g_lo, i_lo, atr, start)
    granted, _ = B.allocate({"S1": s1, "A2": s2}, start, 1.0, {"S1": 0.0, "A2": 0.0})
    c = granted["S1"] + granted["A2"]
    assert np.array_equal(c, np.maximum(s1, s2)), "the allocator rationed at full capital"

    ones = np.ones_like(s1)
    ones[:, :start] = 0.0
    return panel, start, {"S1": s1, "S2": s2, "C": c}, ones


def _sh(v):
    sd = float(np.std(v, ddof=1))
    return float(np.mean(v) / sd * math.sqrt(PPY)) if sd > 0 else 0.0


def sub_score(panel, pos, start, mask):
    """Score a sub-period. The MASK selects scored bars; the SIGNAL is untouched,
    so the window carries exactly the warm-up it would have had."""
    tot = X.signed_log_returns(panel, pos, total_return=True)[start:]
    ex = X.excess_of(tot, pos, start)
    live = pos[:, start:]
    return {
        "excess_sharpe": _sh(ex[mask]),
        "cagr": float(np.expm1(np.sum(tot[mask]) / (mask.sum() / PPY))),
        "exposure": float(live[:, mask].mean()),
        "max_drawdown": L.max_drawdown_of(tot[mask]),
        "bars": int(mask.sum()),
    }


def build() -> dict:
    t0 = time.time()

    panel, start, books, ones = books_on(*FIXTURES["extended"])
    dates = [d[:10] for d in panel.dates[start:]]
    assert len(panel.symbols) == 57, "the extended universe is not the 57"
    assert panel.dates[0][:10] == "2009-11-11", "the extended fixture does not start where it should"

    d = np.array(dates)
    periods = {
        "NEW": d < TRAIN_START,
        "TRAIN": (d >= TRAIN_START) & (d < FORWARD_START),
        "FORWARD": d >= FORWARD_START,
        "FULL": np.ones(len(d), dtype=bool),
    }
    assert periods["NEW"].sum() > 500, "the never-seen window is too short to test on"

    full = {k: X.score(panel, books[k], start) for k in CELL_ORDER}
    bh_full = X.score(panel, ones, start)
    per = {k: {p: sub_score(panel, books[k], start, m) for p, m in periods.items()}
           for k in CELL_ORDER}
    per["BH"] = {p: sub_score(panel, ones, start, m) for p, m in periods.items()}

    # V1 / V3 on the never-seen window
    verdict = {}
    for k in ARMS:
        new, tr = per[k]["NEW"], per[k]["TRAIN"]
        delta = new["excess_sharpe"] - per["BH"]["NEW"]["excess_sharpe"]
        verdict[k] = {
            "new_sharpe": new["excess_sharpe"], "train_sharpe": tr["excess_sharpe"],
            "bh_new": per["BH"]["NEW"]["excess_sharpe"], "delta_vs_bh": delta,
            "floor": V3_FLOOR[k],
            "clears_V1": bool(new["excess_sharpe"] > 0 and delta > 0),
            "clears_V3": bool(delta >= V3_FLOOR[k]),
            "weaker_on_new": bool(new["excess_sharpe"] < tr["excess_sharpe"]),
        }

    # V2 -- rotation nulls scored on the NEW window only
    rng = np.random.default_rng(SEED)
    n, T = books["S1"].shape
    span = T - start
    nl = {k: np.empty(N_SIMS) for k in ARMS}
    mask_new = periods["NEW"]
    for s in range(N_SIMS):
        off = rng.integers(1, span, size=n)
        for k in ARMS:
            src = books[k][:, start:]
            rot = np.zeros_like(books[k])
            for i in range(n):
                rot[i, start:] = np.roll(src[i], int(off[i]))
            tot = X.signed_log_returns(panel, rot, total_return=True)[start:]
            nl[k][s] = _sh(X.excess_of(tot, rot, start)[mask_new])
    nulls = {}
    for k in ARMS:
        a = per[k]["NEW"]["excess_sharpe"]
        nulls[k] = {"p50": float(np.percentile(nl[k], 50)),
                    "p95": float(np.percentile(nl[k], 95)),
                    "percentile_of_actual": float((nl[k] < a).mean() * 100.0),
                    "clears_V2": bool(a > float(np.percentile(nl[k], 95)))}
        verdict[k]["clears_V2"] = nulls[k]["clears_V2"]
        verdict[k]["clears_all"] = bool(verdict[k]["clears_V1"] and verdict[k]["clears_V2"]
                                        and verdict[k]["clears_V3"])

    # V4 -- the intervals, on the FULL extended span. The point of doubling the data.
    def ex_of(pos):
        tot = X.signed_log_returns(panel, pos, total_return=True)[start:]
        return X.excess_of(tot, pos, start)

    r = {k: ex_of(books[k]) for k in CELL_ORDER}
    r["BH"] = ex_of(ones)
    nlen = len(r["S1"])
    nblk = math.ceil(nlen / J.BLOCK)
    rb = np.random.default_rng(SEED)
    idxs = [(rb.integers(0, nlen - J.BLOCK + 1, size=nblk)[:, None]
             + np.arange(J.BLOCK)[None, :]).ravel()[:nlen] for _ in range(J.N_BOOT)]
    boot = {}
    for k in CELL_ORDER:
        own = np.array([_sh(r[k][i]) for i in idxs])
        dbh = np.array([_sh(r[k][i]) - _sh(r["BH"][i]) for i in idxs])
        boot[k] = {"sharpe": _sh(r[k]),
                   "sharpe_p05": float(np.percentile(own, 5)),
                   "sharpe_p95": float(np.percentile(own, 95)),
                   "sharpe_excludes_zero": bool(np.percentile(own, 5) > 0.0),
                   "delta_bh": _sh(r[k]) - _sh(r["BH"]),
                   "delta_bh_p05": float(np.percentile(dbh, 5)),
                   "delta_bh_excludes_zero": bool(np.percentile(dbh, 5) > 0.0)}
    dc = np.array([_sh(r["C"][i]) - _sh(r["S1"][i]) for i in idxs])
    boot["C_vs_S1"] = {"delta": _sh(r["C"]) - _sh(r["S1"]),
                       "p05": float(np.percentile(dc, 5)),
                       "p95": float(np.percentile(dc, 95)),
                       "excludes_zero": bool(np.percentile(dc, 5) > 0.0)}

    rho = float(np.corrcoef(r["S1"], r["S2"])[0, 1])
    both = (verdict["S1"]["clears_all"], verdict["S2"]["clears_all"])
    reading = {
        (True, True): "BOTH ENTRIES SURVIVE THE FIRST TIME-INDEPENDENT TEST THE PROGRAMME HAS "
                      "HAD. The era question, open since D237, is answered for these bars.",
        (True, False): "S1 SURVIVES A NEW ERA; S2 DOES NOT. S2 is amended in BOOK.md in "
                       "writing with the sub-period recorded as a demonstrated weakness.",
        (False, True): "S2 SURVIVES A NEW ERA; S1 DOES NOT. S1 is amended in BOOK.md in "
                       "writing -- and D239's mechanism predicted exactly this.",
        (False, False): "NEITHER ENTRY SURVIVES A CHANGE OF ERA. Both are amended in writing "
                        "and the book's evidence base is much weaker than it looked.",
    }[both]

    return {
        "produced": "D243", "stage": "VERDICT -- extended history, never-seen sub-period",
        "seed": SEED, "n_sims": N_SIMS,
        "n_symbols": len(panel.symbols), "raw_bars": len(panel.dates),
        "first_bar": panel.dates[0][:10], "last_bar": panel.dates[-1][:10],
        "live_bars": len(dates), "first_live": dates[0], "last_live": dates[-1],
        "period_bars": {p: int(m.sum()) for p, m in periods.items()},
        "full": full, "buy_and_hold_full": bh_full, "by_period": per,
        "verdict": verdict, "nulls": nulls, "bootstrap": boot, "rho_S1_S2": rho,
        "deployable_return": {
            k: float(np.expm1(np.log1p(full[k]["cagr"])
                              + math.log1p(RF_ANNUAL) * (1 - full[k]["exposure_gross"])))
            for k in CELL_ORDER},
        "reading": reading,
        "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    f, per, v, n, bt = (p["full"], p["by_period"], p["verdict"], p["nulls"], p["bootstrap"])
    bh, dep, pb = p["buy_and_hold_full"], p["deployable_return"], p["period_bars"]
    o = ["# D243 — the book on extended history\n"]
    o.append("**THE FIRST TIME-INDEPENDENT TEST THIS PROGRAMME HAS HAD.**\n")
    o.append(
        f"*seed {p['seed']}, {p['n_sims']:,} rotations, {p['elapsed_seconds']}s. "
        f"{p['n_symbols']} ETFs x {p['raw_bars']:,} bars, {p['first_bar']} .. {p['last_bar']}; "
        f"{p['live_bars']:,} live from {p['first_live']}. Only the book — no variants, no stop, "
        f"zero fresh looks.*\n"
    )
    o.append(
        f"**The extended live window CONTAINS the training window**, so it is not a clean "
        f"holdout. It splits into **NEW** ({pb['NEW']:,} bars, never seen), **TRAIN** "
        f"({pb['TRAIN']:,}) and **FORWARD** ({pb['FORWARD']:,}). Every previous holdout was an "
        f"*instrument* holdout at ρ = +0.978 between universes. **The verdict lives in NEW.**\n"
    )

    o.append("## The verdict — the never-seen window\n")
    o.append("| | NEW | *TRAIN* | B&H on NEW | Δ vs B&H | floor | rot p95 | pctile | "
             "V1 | V2 | V3 | **all** |")
    o.append("|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|:--:|")
    for k in ARMS:
        q, nn = v[k], n[k]
        o.append(
            f"| **{k}** | **{q['new_sharpe']:+.3f}** | *{q['train_sharpe']:+.3f}* | "
            f"{q['bh_new']:+.3f} | **{q['delta_vs_bh']:+.3f}** | {q['floor']:+.3f} | "
            f"{nn['p95']:+.3f} | **{nn['percentile_of_actual']:.1f}th** | "
            f"{'✓' if q['clears_V1'] else '✗'} | {'✓' if q['clears_V2'] else '✗'} | "
            f"{'✓' if q['clears_V3'] else '✗'} | "
            f"**{'✓' if q['clears_all'] else '✗'}** |"
        )
    o.append("")

    o.append("## Every period, side by side\n")
    o.append("| | NEW | TRAIN | FORWARD | FULL |")
    o.append("|---|---:|---:|---:|---:|")
    for k in list(CELL_ORDER) + ["BH"]:
        row = f"| **{k}** | " + " | ".join(
            f"{per[k][x]['excess_sharpe']:+.3f}" for x in ("NEW", "TRAIN", "FORWARD", "FULL"))
        o.append(row + " |")
    o.append("")
    o.append("*Exposure and drawdown by period:*\n")
    o.append("| | NEW expo | NEW maxDD | TRAIN maxDD | FULL maxDD |")
    o.append("|---|---:|---:|---:|---:|")
    for k in CELL_ORDER:
        o.append(f"| **{k}** | {per[k]['NEW']['exposure']:.1%} | "
                 f"{per[k]['NEW']['max_drawdown'] * 100:+.2f}% | "
                 f"{per[k]['TRAIN']['max_drawdown'] * 100:+.2f}% | "
                 f"{per[k]['FULL']['max_drawdown'] * 100:+.2f}% |")
    o.append("")

    o.append("## V4 — the intervals, on 12.8 years instead of 6\n")
    o.append("*The whole point of doubling the data. Contaminated by containing TRAIN, so "
             "reported for **width**, not as a verdict.*\n")
    o.append("| | excess Sharpe | p05 | p95 | **excludes 0** | Δ vs B&H | p05 | excludes 0 |")
    o.append("|---|---:|---:|---:|:--:|---:|---:|:--:|")
    for k in CELL_ORDER:
        q = bt[k]
        o.append(
            f"| **{k}** | {q['sharpe']:+.3f} | {q['sharpe_p05']:+.3f} | {q['sharpe_p95']:+.3f} | "
            f"**{'✓' if q['sharpe_excludes_zero'] else '✗'}** | {q['delta_bh']:+.3f} | "
            f"{q['delta_bh_p05']:+.3f} | {'✓' if q['delta_bh_excludes_zero'] else '✗'} |")
    c = bt["C_vs_S1"]
    o.append("")
    o.append(
        f"**The combination against S1 alone:** {c['delta']:+.3f}, "
        f"p05 {c['p05']:+.3f}, p95 {c['p95']:+.3f} — "
        f"**{'excludes' if c['excludes_zero'] else 'contains'} zero**.\n"
    )
    o.append("## The book, in full\n")
    o.append("| | exposure | excess Sharpe | CAGR | deployable | max DD | Calmar | E |")
    o.append("|---|---:|---:|---:|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        x = f[k]
        o.append(f"| **{k}** | {x['exposure_gross']:.1%} | {x['excess_sharpe']:+.3f} | "
                 f"{x['cagr'] * 100:.2f}% | **{dep[k] * 100:.2f}%** | "
                 f"{x['max_drawdown'] * 100:+.2f}% | "
                 f"{x['cagr'] / abs(x['max_drawdown']):.3f} | "
                 f"{'✓' if x['clears_E'] else '✗'} ({x['min_entries_per_symbol']}) |")
    o.append(f"| *B&H* | *100.0%* | *{bh['excess_sharpe']:+.3f}* | *{bh['cagr'] * 100:.2f}%* | "
             f"*{bh['cagr'] * 100:.2f}%* | *{bh['max_drawdown'] * 100:+.2f}%* | "
             f"*{bh['cagr'] / abs(bh['max_drawdown']):.3f}* | — |")
    o.append("")
    o.append(f"**ρ between S1 and S2 over 12.8 years: `{p['rho_S1_S2']:+.4f}`** "
             f"(mined +0.159, holdout +0.175).\n")
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

    per, v, bt = payload["by_period"], payload["verdict"], payload["bootstrap"]
    print()
    print(f"live {payload['live_bars']:,} bars from {payload['first_live']}   "
          f"NEW {payload['period_bars']['NEW']:,} | TRAIN {payload['period_bars']['TRAIN']:,} | "
          f"FWD {payload['period_bars']['FORWARD']:,}")
    print()
    print(f"{'':5s} {'NEW':>8s} {'TRAIN':>8s} {'FWD':>8s} {'FULL':>8s} {'p05':>8s} {'excl0':>6s}")
    for k in list(CELL_ORDER) + ["BH"]:
        b = bt.get(k)
        print(f"{k:5s} " + " ".join(f"{per[k][x]['excess_sharpe']:+8.3f}"
                                   for x in ("NEW", "TRAIN", "FORWARD", "FULL"))
              + (f" {b['sharpe_p05']:+8.3f} {'YES' if b['sharpe_excludes_zero'] else 'no':>6s}"
                 if b else ""))
    print()
    for k in ARMS:
        q = v[k]
        print(f"V1/V2/V3 {k}: dBH {q['delta_vs_bh']:+.3f} (floor {q['floor']:+.3f})  "
              f"null {payload['nulls'][k]['percentile_of_actual']:.1f}th  -> "
              f"{'CLEARS' if q['clears_all'] else 'FAILS'}")
    c = bt["C_vs_S1"]
    print(f"C vs S1: {c['delta']:+.3f} [p05 {c['p05']:+.3f}] -> "
          f"{'excludes 0' if c['excludes_zero'] else 'contains 0'}")
    print(f"rho(S1,S2) = {payload['rho_S1_S2']:+.4f}")
    print()
    print(payload["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

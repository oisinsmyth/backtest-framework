"""D255 — stops and targets on the book and on each arm.

21 cells: 3 arms (S1, S2, C) x 7 overlays (SL 5/10/20, TP 10/20/30, and the
declared TP20+SL20 pair). Counted in full; no level added after the run.

HURDLE H IS R7's MATCHED-EXIT-COUNT NULL, NOT A ROTATION NULL. D235 failed by
using a rotation null, whose p95 of -0.284 anything not actively harmful clears.
The right control keeps the base book and cuts THE SAME NUMBER of trades short at
random points inside their own spans, with cut fractions drawn from the real
overlay's own pool. `run_uptrend_onset.null_book`, reused unmodified.

REACHABILITY IS REPORTED BEFORE ANY CELL IS SCORED. An overlay that never fires
trivially matches its base, so a cell whose level is unreachable is reported as
VACUOUS rather than as a pass. The pre-screen predicts this is the binding
constraint: the ETF universe's >= +20% bucket holds 121 instances in 16.8 years.

ONE SIMPLIFICATION, STATED. For the combined book C the overlay exits a name and
the freed capital is NOT reallocated by the FCFS allocator. Re-running allocation
inside an overlay would change which arm owns which name and make the cell a
different construction rather than an overlay on C. The simplification is
conservative -- it can only reduce C's exposure.

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


E = _load("d243_extended", "run_book_extended.py")
B, U, X, L, S = E.B, E.U, E.X, E.L, E.S
F = _load("d228_filter", "run_filter_search.py")

SUMMARY = REPO / "data" / "stops_book_summary.json"
RESULTS = REPO / "docs" / "results" / "STOPS_BOOK_RESULTS.md"

SEED = X.SEED
N_SIMS = 1000
ARMS = ("S1", "S2", "C")
STOPS = (0.05, 0.10, 0.20)
TARGETS = (0.10, 0.20, 0.30)
COMBO = (0.20, 0.20)          # (tp, sl) -- declared in D255 before the run
LEVELS = ([("SL%02d" % int(100 * s), None, s) for s in STOPS]
          + [("TP%02d" % int(100 * t), t, None) for t in TARGETS]
          + [("TP20SL20", COMBO[0], COMBO[1])])


def spans_of(pos):
    """(symbol, first held bar, last held bar INCLUSIVE)."""
    sym, s0, e0 = F.trade_spans(pos)
    return [(int(i), int(a), int(b) - 1) for i, a, b in zip(sym, s0, e0)]


def apply_overlay(base_pos, closes, start, *, tp, sl):
    """Exit fully at the first close where the trade's gain touches +tp or -sl.

    Decided at the close of `t`, effective from `t+1` -- D235's convention, and
    close-to-close because daily OHLC cannot tell a touch from a gap through."""
    out = base_pos.copy()
    cuts = []
    for i, a, b in spans_of(base_pos):
        if a < start or a == 0 or b <= a:
            continue
        entry = closes[i, a - 1]
        for t in range(a, b + 1):
            g = closes[i, t] / entry - 1.0
            if (tp is not None and g >= tp) or (sl is not None and g <= -sl):
                if t < b:
                    out[i, t + 1: b + 1] = 0.0
                    cuts.append((t - a) / max(b - a, 1))
                break
    out[:, :start] = 0.0
    return out, cuts


def reachability(base_pos, closes, start):
    """What fraction of trades ever touch each level while held. Descriptive."""
    hi, lo, n = [], [], 0
    for i, a, b in spans_of(base_pos):
        if a < start or a == 0 or b < a:
            continue
        entry = closes[i, a - 1]
        g = closes[i, a: b + 1] / entry - 1.0
        hi.append(float(g.max()))
        lo.append(float(g.min()))
        n += 1
    hi, lo = np.array(hi), np.array(lo)
    out = {"trades": n, "median_max_gain": float(np.median(hi)) if n else float("nan"),
           "median_max_loss": float(np.median(lo)) if n else float("nan")}
    for t in TARGETS:
        out["reach_TP%02d" % int(100 * t)] = float(np.mean(hi >= t)) if n else float("nan")
    for s in STOPS:
        out["reach_SL%02d" % int(100 * s)] = float(np.mean(lo <= -s)) if n else float("nan")
    return out


def r7_null(panel, base_pos, n_cut, frac_pool, start, rng):
    """R7's matched-exit-count control, via D240's null_book."""
    trades = [(i, a, b, 0.0) for i, a, b in spans_of(base_pos) if a >= start and a > 0 and b >= a]
    sh = np.empty(N_SIMS)
    mn = np.empty(N_SIMS)
    pool = np.asarray(frac_pool) if len(frac_pool) else np.array([0.5])
    for s in range(N_SIMS):
        pos = U.null_book(panel, trades, n_cut, pool, rng, start)
        total = X.signed_log_returns(panel, pos, total_return=True)[start:]
        ex = X.excess_of(total, pos, start)
        sd = float(np.std(ex, ddof=1))
        sh[s] = (float(np.mean(ex)) / sd * math.sqrt(X.PPY)) if sd > 0 else 0.0
        mn[s] = X.L.total_return_of(total)
    return sh, mn


def build() -> dict:
    t0 = time.time()
    panel, start, books, ones = E.books_on(*E.FIXTURES["extended"])
    closes = panel.closes
    base = {"S1": books["S1"], "S2": books["S2"], "C": books["C"]}

    reach = {k: reachability(v, closes, start) for k, v in base.items()}
    base_scores = {k: X.score(panel, v, start) for k, v in base.items()}
    bh = X.score(panel, ones, start)

    rng = np.random.default_rng(SEED)
    cells, verdict, nulls = {}, {}, {}
    all_sh = []
    for arm in ARMS:
        for name, tp, sl in LEVELS:
            key = f"{arm}:{name}"
            pos, cuts = apply_overlay(base[arm], closes, start, tp=tp, sl=sl)
            sc = X.score(panel, pos, start)
            sc["n_cut"] = len(cuts)
            sc["cut_rate"] = len(cuts) / max(reach[arm]["trades"], 1)
            sh, mn = r7_null(panel, base[arm], len(cuts), cuts, start, rng)
            all_sh.append(sh)
            sp = float((sh < sc["excess_sharpe"]).mean() * 100.0)
            mp = float((mn < sc["total_return"]).mean() * 100.0)
            cells[key] = sc
            nulls[key] = {"sharpe_p95": float(np.percentile(sh, 95)),
                          "money_p95": float(np.percentile(mn, 95))}
            verdict[key] = {
                "sharpe_pct": sp, "money_pct": mp,
                "clears_H": bool(sp >= 95.0 and mp >= 95.0),
                "clears_B": bool(sc["excess_sharpe"] > base_scores[arm]["excess_sharpe"]),
                "vacuous": bool(len(cuts) == 0),
            }
    floor = float(np.percentile(np.max(np.vstack(all_sh), axis=0), 95))
    for k, v in verdict.items():
        v["clears_F"] = bool(cells[k]["excess_sharpe"] > floor)
        v["success"] = bool(v["clears_H"] and v["clears_B"] and v["clears_F"]
                            and not v["vacuous"])

    payload = {
        "study": "D255", "seed": SEED, "n_sims": N_SIMS,
        "fixture": "universe_daily_extended_raw.csv.gz",
        "n_symbols": int(panel.closes.shape[0]), "bars": int(panel.closes.shape[1]),
        "start": start, "ppy": X.PPY,
        "stops": list(STOPS), "targets": list(TARGETS), "combo": list(COMBO),
        "reachability": reach, "base": base_scores, "buy_and_hold": bh,
        "cells": cells, "verdict": verdict, "nulls": nulls,
        "best_of_floor_p95": floor,
        "any_success": bool(any(v["success"] for v in verdict.values())),
        "seconds": time.time() - t0,
    }
    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def render(p: dict) -> str:
    o = []
    a = o.append
    a("# D255 — stops and targets on the book and on each arm\n")
    a(f"**Produced by** `scripts/run_stops_book.py` · seed {p['seed']} · "
      f"{p['n_sims']:,} R7 null draws per cell · {p['seconds']:.0f}s\n")
    a(f"`{p['fixture']}` — {p['n_symbols']} ETFs x {p['bars']:,} bars, "
      f"live from bar {p['start']:,}.\n")

    a("\n## Reachability — reported BEFORE any cell is scored\n")
    a("| arm | trades | median max gain | median max loss | reach +10% | +20% | +30% | "
      "−5% | −10% | −20% |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for k in ARMS:
        r = p["reachability"][k]
        a(f"| **{k}** | {r['trades']:,} | {r['median_max_gain']:+.2%} | "
          f"{r['median_max_loss']:+.2%} | "
          + " | ".join(f"{r['reach_TP%02d' % int(100*t)]:.1%}" for t in TARGETS) + " | "
          + " | ".join(f"{r['reach_SL%02d' % int(100*s)]:.1%}" for s in STOPS) + " |")
    a("\n**A level reached by few trades cannot move a book, whatever its conditional edge.**\n")

    a("\n## The 21 cells\n")
    a(f"Base arms: " + ", ".join(
        f"**{k}** {p['base'][k]['excess_sharpe']:+.3f} ({p['base'][k]['cagr']:+.2%})"
        for k in ARMS) + f" · buy-and-hold {p['buy_and_hold']['excess_sharpe']:+.3f}\n")
    a(f"\nBest-of-21 floor (D228), p95: **{p['best_of_floor_p95']:+.3f}**\n")
    a("\n| cell | cuts | cut rate | excess Sharpe | vs base | CAGR | max DD | "
      "H (Sharpe/money) | B | F | **success** |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|")
    for arm in ARMS:
        for name, _tp, _sl in LEVELS:
            k = f"{arm}:{name}"
            c, v = p["cells"][k], p["verdict"][k]
            d = c["excess_sharpe"] - p["base"][arm]["excess_sharpe"]
            tag = " *(vacuous)*" if v["vacuous"] else ""
            a(f"| {k}{tag} | {c['n_cut']:,} | {c['cut_rate']:.1%} | {c['excess_sharpe']:+.3f} | "
              f"{d:+.3f} | {c['cagr']:+.2%} | {c['max_drawdown']:.2%} | "
              f"{v['sharpe_pct']:.1f}th / {v['money_pct']:.1f}th | "
              f"{'y' if v['clears_B'] else 'n'} | {'y' if v['clears_F'] else 'n'} | "
              f"{'**YES**' if v['success'] else 'no'} |")

    a("\n## Verdict\n")
    a("**" + ("At least one cell clears H, B and F." if p["any_success"] else
             "NO CELL CLEARS H, B AND F. Per D255's stop, stops and targets are CLOSED for this "
             "book — no further levels, no trailing variants, no per-symbol calibration, no "
             "ATR-scaled version. What is NOT closed is the same overlay on a single-name "
             "universe, where the pre-screen predicts the +20% bucket is populated.") + "**\n")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    p = json.loads(SUMMARY.read_text(encoding="utf-8")) if args.report_only else build()
    RESULTS.write_text(render(p), encoding="utf-8")
    for k in ARMS:
        r = p["reachability"][k]
        print(f"{k}: {r['trades']:,} trades, median max gain {r['median_max_gain']:+.2%}, "
              f"reach +20% {r['reach_TP20']:.1%}, reach -10% {r['reach_SL10']:.1%}")
    print(f"floor {p['best_of_floor_p95']:+.3f}")
    for arm in ARMS:
        for name, _t, _s in LEVELS:
            k = f"{arm}:{name}"
            c, v = p["cells"][k], p["verdict"][k]
            print(f"  {k:14} cuts {c['n_cut']:5,} exS {c['excess_sharpe']:+6.3f} "
                  f"(base {p['base'][arm]['excess_sharpe']:+6.3f}) "
                  f"null {v['sharpe_pct']:5.1f}/{v['money_pct']:5.1f} "
                  f"H={int(v['clears_H'])} B={int(v['clears_B'])} F={int(v['clears_F'])}")
    print("ANY SUCCESS:", p["any_success"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""D245 — the book on the wide universe.

Two cells, W5 (>= $5M/day) and W1 (>= $1M/day), on the extended fixture's exact
span so the comparison against D243 is clean.

THE WIDE UNIVERSE CONTAINS THE 57 AND THE 60, so it is not a clean holdout and is
not reported as one. Every cell decomposes into three cohorts:

    MINED     the 57   S1 and S2 were built here
    HOLDOUT   the 60   spent by D237 and D242
    NEW       the rest NEVER SEEN by any rule in this programme

HURDLES ARE EVALUATED ON THE NEW COHORT. Full-universe numbers are reported for
BREADTH and INTERVAL WIDTH only, and are contaminated by construction.

Only the book -- S1, S2 and their union at full capital. No variants, no search.

Offline, deterministic, seed 0. `--report-only` re-renders from the artifact.
"""

from __future__ import annotations

import argparse
import csv
import gzip
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
B, U, X, L, S, J = E.B, E.U, E.X, E.L, E.S, E.J

SUMMARY = REPO / "data" / "book_wide_summary.json"
RESULTS = REPO / "BOOK_WIDE_RESULTS.md"
FIX = REPO / "data" / "fixtures"

SEED, PPY, N_SIMS = X.SEED, X.PPY, X.N_SIMS
RF_ANNUAL = X.RF_ANNUAL

CELLS = ("W5", "W1")
ARMS = ("S1", "S2")
BOOKS = ("S1", "S2", "C")
COHORTS = ("NEW", "MINED", "HOLDOUT", "ALL")

# D237's construction, reused: 25% of the 12.8-year delta over buy-and-hold.
Z3_FLOOR = {"S1": 0.25 * (0.478 - 0.242), "S2": 0.25 * (0.511 - 0.242)}
D243 = {"S1": 0.478, "S2": 0.511, "C": 0.620}      # for the narrowing comparison


def universe_of(path):
    syms = set()
    with gzip.open(path, "rt") as f:
        for r in csv.DictReader(f):
            syms.add(r["symbol"])
    return syms


def effective_instruments(rets):
    """`1 / (w'Rw)` at equal weights = `n^2 / sum(R)`. The 57 score 2.23, which is
    why every interval in this programme has been wide."""
    if rets.shape[0] < 2:
        return 1.0
    R = np.corrcoef(rets)
    R = np.nan_to_num(R, nan=0.0)
    n = R.shape[0]
    return float(n * n / R.sum())


def books_on(cell):
    L.FIXTURE = FIX / f"universe_wide_{cell.lower()}_raw.csv.gz"
    L.EVENTS = FIX / f"universe_wide_{cell.lower()}_raw_events.json"
    panel, cleaned = L.load_panel()
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)
    live = panel.closes.shape[1] - start
    if live < 500:
        raise SystemExit(
            f"{cell}: only {live} live bars after a {start}-bar warm-up -- the date "
            "intersection collapsed, which means a symbol with truncated history "
            "survived the completeness screen")
    md, hs, ok = S.base_masks(panel, cleaned, start)
    s1 = S.hold_book((hs > 0) & (md <= 0) & ok, start)
    up, g_lo, i_lo, atr = U.signals(panel, cleaned, start)
    s2, _, _ = U.walk(panel, up, g_lo, i_lo, atr, start)
    granted, _ = B.allocate({"S1": s1, "A2": s2}, start, 1.0, {"S1": 0.0, "A2": 0.0})
    c = granted["S1"] + granted["A2"]
    assert np.array_equal(c, np.maximum(s1, s2)), "the allocator rationed at full capital"
    return panel, start, {"S1": s1, "S2": s2, "C": c}


def sub_panel(panel, rows):
    """An N-name book must be equal-weighted over N. Zeroing rows leaves
    `portfolio_log_returns` dividing by the full count -- D239's `subset_panel`."""
    r = list(rows)
    return type(panel)(
        symbols=tuple(panel.symbols[i] for i in r), closes=panel.closes[r],
        log_returns=panel.log_returns[r], cost_fraction=panel.cost_fraction[r],
        dates=panel.dates, total_log_returns=panel.total_log_returns[r],
    )


def _sh(v):
    sd = float(np.std(v, ddof=1))
    return float(np.mean(v) / sd * math.sqrt(PPY)) if sd > 0 else 0.0


def build() -> dict:
    t0 = time.time()
    mined = universe_of(FIX / "universe_daily_2015_2024_raw.csv.gz")
    holdout = universe_of(FIX / "universe_holdout_daily_raw.csv.gz")
    assert not (mined & holdout), "the two spent universes overlap"

    out = {}
    for cell in CELLS:
        panel, start, books = books_on(cell)
        syms = list(panel.symbols)
        idx = {
            "MINED": [i for i, s in enumerate(syms) if s in mined],
            "HOLDOUT": [i for i, s in enumerate(syms) if s in holdout],
            "NEW": [i for i, s in enumerate(syms) if s not in mined and s not in holdout],
        }
        idx["ALL"] = list(range(len(syms)))
        assert len(idx["MINED"]) + len(idx["HOLDOUT"]) + len(idx["NEW"]) == len(syms), \
            "the cohort split does not cover the universe"
        assert len(idx["NEW"]) > 50, f"{cell}: the never-seen cohort is too small to test on"

        per_cohort, nulls, boot, breadth = {}, {}, {}, {}
        for coh in COHORTS:
            rows = idx[coh]
            if not rows:
                continue
            p = sub_panel(panel, rows)
            ones = np.zeros_like(p.closes)
            ones[:, start:] = 1.0
            sub = {k: books[k][rows] for k in BOOKS}
            per_cohort[coh] = {k: X.score(p, sub[k], start) for k in BOOKS}
            per_cohort[coh]["BH"] = X.score(p, ones, start)
            breadth[coh] = effective_instruments(p.total_log_returns[:, start:])

            # nulls and intervals only where a verdict or a width claim is made
            if coh in ("NEW", "ALL"):
                nl = X.rotation_nulls(p, {k: sub[k] for k in ARMS}, start)
                nulls[coh] = {}
                for k, draws in nl["draws"].items():
                    a = per_cohort[coh][k]["excess_sharpe"]
                    nulls[coh][k] = {
                        "p95": float(np.percentile(draws, 95)),
                        "percentile_of_actual": float((draws < a).mean() * 100.0),
                        "money_percentile_of_actual": float(
                            (nl["money"][k] < per_cohort[coh][k]["total_return"]).mean() * 100.0),
                        "clears_Z2": bool(a > float(np.percentile(draws, 95))),
                    }
                def ex_of(pos, pp=p):
                    tot = X.signed_log_returns(pp, pos, total_return=True)[start:]
                    return X.excess_of(tot, pos, start)
                nlen = panel.closes.shape[1] - start
                nblk = math.ceil(nlen / J.BLOCK)
                rb = np.random.default_rng(SEED)
                ids = [(rb.integers(0, nlen - J.BLOCK + 1, size=nblk)[:, None]
                        + np.arange(J.BLOCK)[None, :]).ravel()[:nlen] for _ in range(J.N_BOOT)]
                boot[coh] = {}
                for k in BOOKS:
                    v = ex_of(sub[k])
                    d = np.array([_sh(v[i]) for i in ids])
                    boot[coh][k] = {"p05": float(np.percentile(d, 5)),
                                    "p95": float(np.percentile(d, 95)),
                                    "excludes_zero": bool(np.percentile(d, 5) > 0.0)}

        verdict = {}
        for k in ARMS:
            new, bh = per_cohort["NEW"][k], per_cohort["NEW"]["BH"]
            delta = new["excess_sharpe"] - bh["excess_sharpe"]
            verdict[k] = {
                "sharpe": new["excess_sharpe"], "bh": bh["excess_sharpe"],
                "delta_vs_bh": delta, "floor": Z3_FLOOR[k],
                "clears_Z1": bool(new["excess_sharpe"] > 0 and delta > 0),
                "clears_Z2": nulls["NEW"][k]["clears_Z2"],
                "clears_Z3": bool(delta >= Z3_FLOOR[k]),
            }
            verdict[k]["clears_all"] = all(
                verdict[k][x] for x in ("clears_Z1", "clears_Z2", "clears_Z3"))

        out[cell] = {
            "n_symbols": len(syms), "bars": int(panel.closes.shape[1]),
            "live_bars": int(panel.closes.shape[1] - start),
            "first": panel.dates[0][:10], "last": panel.dates[-1][:10],
            "cohort_sizes": {c: len(idx[c]) for c in COHORTS},
            "by_cohort": per_cohort, "nulls": nulls, "bootstrap": boot,
            "effective_instruments": breadth, "verdict": verdict,
            "deployable_return": {
                k: float(np.expm1(np.log1p(per_cohort["ALL"][k]["cagr"])
                                  + math.log1p(RF_ANNUAL)
                                  * (1 - per_cohort["ALL"][k]["exposure_gross"])))
                for k in BOOKS},
        }
        print(f"{cell}: {len(syms)} symbols, NEW cohort {len(idx['NEW'])}, "
              f"S2 on NEW {verdict['S2']['sharpe']:+.3f}", flush=True)

    reading = {
        (True, True): "S2 GENERALISES ACROSS THE BROAD ETF UNIVERSE at both liquidity floors.",
        (True, False): "S2 generalises at the $5M floor but not at $1M -- consistent with the "
                       "thinner names being where the cost model stops being credible.",
        (False, True): "S2 clears only at the $1M floor. Treat with suspicion: the weaker cost "
                       "assumption is the likelier explanation.",
        (False, False): "S2 DOES NOT GENERALISE beyond the 57 it was found on.",
    }[(out["W5"]["verdict"]["S2"]["clears_all"], out["W1"]["verdict"]["S2"]["clears_all"])]

    return {"produced": "D245", "stage": "instrument cohort split -- NEW carries the verdict",
            "seed": SEED, "n_sims": N_SIMS, "z3_floor": Z3_FLOOR, "d243_reference": D243,
            "cells": out, "reading": reading,
            "elapsed_seconds": round(time.time() - t0, 1)}


def render(p: dict) -> str:
    o = ["# D245 — the book on the wide universe\n"]
    o.append("**The wide universe CONTAINS the 57 and the 60**, so it is not a clean holdout. "
             "Hurdles are evaluated on the **NEW** cohort; full-universe numbers are reported "
             "for breadth and interval width only.\n")
    o.append(f"*seed {p['seed']}, {p['n_sims']:,} rotations, {p['elapsed_seconds']}s. "
             f"Only the book — no variants, no search.*\n")
    for cell in CELLS:
        d = p["cells"][cell]
        cs, bc, nl, bt = d["cohort_sizes"], d["by_cohort"], d["nulls"], d["bootstrap"]
        o.append(f"## {cell} — {d['n_symbols']} symbols, {d['live_bars']:,} live bars "
                 f"({d['first']} .. {d['last']})\n")
        o.append(f"*cohorts: **NEW {cs['NEW']}**, mined {cs['MINED']}, holdout "
                 f"{cs['HOLDOUT']}*\n")
        o.append("| | NEW | *MINED* | *HOLDOUT* | ALL |")
        o.append("|---|---:|---:|---:|---:|")
        for k in list(BOOKS) + ["BH"]:
            o.append(f"| **{k}** | " + " | ".join(
                f"{bc[c][k]['excess_sharpe']:+.3f}" for c in COHORTS) + " |")
        o.append("")
        o.append("**Effective independent instruments** "
                 + " · ".join(f"{c} **{d['effective_instruments'][c]:.2f}**" for c in COHORTS)
                 + "  *(the 57 score 2.23)*\n")
        o.append("| | NEW Δ vs B&H | floor | rot null pctile | money pct | Z1 | Z2 | Z3 | "
                 "**all** |")
        o.append("|---|---:|---:|---:|---:|:--:|:--:|:--:|:--:|")
        for k in ARMS:
            q, n = d["verdict"][k], nl["NEW"][k]
            o.append(f"| **{k}** | **{q['delta_vs_bh']:+.3f}** | {q['floor']:+.3f} | "
                     f"**{n['percentile_of_actual']:.1f}th** | "
                     f"{n['money_percentile_of_actual']:.1f}th | "
                     f"{'✓' if q['clears_Z1'] else '✗'} | {'✓' if q['clears_Z2'] else '✗'} | "
                     f"{'✓' if q['clears_Z3'] else '✗'} | "
                     f"**{'✓' if q['clears_all'] else '✗'}** |")
        o.append("")
        o.append("**Intervals on ALL, against D243's 57-name figures:**\n")
        o.append("| | D243 (57) | wide | p05 | excludes 0 | deployable |")
        o.append("|---|---:|---:|---:|:--:|---:|")
        for k in BOOKS:
            o.append(f"| **{k}** | {p['d243_reference'][k]:+.3f} | "
                     f"{bc['ALL'][k]['excess_sharpe']:+.3f} | {bt['ALL'][k]['p05']:+.3f} | "
                     f"{'✓' if bt['ALL'][k]['excludes_zero'] else '✗'} | "
                     f"{d['deployable_return'][k] * 100:.2f}% |")
        o.append("")
    o.append("## The reading\n")
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
    for cell in CELLS:
        d = payload["cells"][cell]
        print(f"\n{cell}: {d['n_symbols']} symbols  NEW={d['cohort_sizes']['NEW']}  "
              f"breadth NEW {d['effective_instruments']['NEW']:.2f} / "
              f"ALL {d['effective_instruments']['ALL']:.2f}")
        for k in ARMS:
            q = d["verdict"][k]
            print(f"  {k}: NEW {q['sharpe']:+.3f} vs BH {q['bh']:+.3f}  "
                  f"delta {q['delta_vs_bh']:+.3f} (floor {q['floor']:+.3f})  "
                  f"null {d['nulls']['NEW'][k]['percentile_of_actual']:.1f}th -> "
                  f"{'CLEARS' if q['clears_all'] else 'FAILS'}")
        for k in BOOKS:
            b = d["bootstrap"]["ALL"][k]
            print(f"  ALL {k}: {d['by_cohort']['ALL'][k]['excess_sharpe']:+.3f} "
                  f"[p05 {b['p05']:+.3f}] {'excl 0' if b['excludes_zero'] else 'contains 0'}"
                  f"   (D243 57-name: {payload['d243_reference'][k]:+.3f})")
    print()
    print(payload["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

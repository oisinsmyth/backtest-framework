"""D261 — the index spread, as a prop-track candidate.

Six pairs from SPY/QQQ/IWM/DIA — the whole venue-liquid equity index universe, so
THERE IS NO SELECTION STEP AND NOTHING TO OVERFIT. `|z| > 2.0` is the textbook
default and is not swept.

Motivated by a shape measurement, not a hope: a SPY-QQQ spread runs 6.4% vol
against SPY's 16.7% and breaches a 4% floor on 0.15% of holds against 0.92% --
roughly 4x the sizing headroom C1 had. The drift vanishes with the volatility, so
this tests ONE thing: does the spread itself mean-revert enough to pay.

NEUTRALITY IS A HURDLE, NOT AN ASSUMPTION. SPY-IWM (+4.33%) and QQQ-IWM (+8.03%)
earned in the shape measurement by carrying a tech/small-cap tilt. D251 caught the
same failure at -1.27 net beta. A cell failing neutrality is reported as a
DIRECTIONAL BET, never as a spread, whatever it earned.

Execution is venue-compliant by construction: the position is held over the
18:00 -> 16:10 window and FLAT at 16:10, re-entered at 18:00 while the signal
persists, so a multi-day trade is a SEQUENCE of compliant overnight holds.

Offline, deterministic. `--report-only` re-renders from the artifact.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import itertools
import json
import math
import sys
import time
from collections import defaultdict
from datetime import date
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures" / "index_extended_15m_raw.csv.gz"
SUMMARY = REPO / "data" / "index_spread_summary.json"
RESULTS = REPO / "docs" / "results" / "INDEX_SPREAD_RESULTS.md"

SYMBOLS = ("SPY", "QQQ", "IWM", "DIA")
LOOKBACK = 60          # prior holds, for beta and for the z-score
Z_ENTRY, Z_EXIT = 2.0, 0.5
MAX_HOLDS = 20
LEG_RT = 0.2e-4        # futures round turn PER LEG
FLOOR = 0.04
P3_LIMIT = 0.02
SCREEN_END = "2018-12-31"
PPY = 252.0
N_SIMS, SEED = 400, 0
LADDER = 0.26
BETA_LIMIT = 0.10


def load_paths():
    """Per symbol, per session: the 18:00 -> 16:10 close path and its endpoints."""
    bars = defaultdict(lambda: defaultdict(dict))
    with gzip.open(FIX, "rt") as f:
        for r in csv.DictReader(f):
            if r["symbol"] in SYMBOLS:
                bars[r["symbol"]][r["timestamp"][:10]][r["timestamp"][11:16]] = float(r["close"])
    days = sorted(set.intersection(*[set(bars[s]) for s in SYMBOLS]))
    paths = {s: {} for s in SYMBOLS}
    for a, b in zip(days, days[1:]):
        if (date.fromisoformat(b) - date.fromisoformat(a)).days != 1:
            continue           # D259: Friday->Monday is not a placeable hold
        ok = True
        seq = {}
        for s in SYMBOLS:
            ev = {k: v for k, v in bars[s].get(a, {}).items() if k >= "18:00"}
            nx = {k: v for k, v in bars[s].get(b, {}).items() if k <= "16:10"}
            if not ev or len(nx) < 10:
                ok = False
                break
            seq[s] = np.array([ev[k] for k in sorted(ev)] + [nx[k] for k in sorted(nx)])
        if ok:
            n = min(len(v) for v in seq.values())
            for s in SYMBOLS:
                paths[s][b] = seq[s][:n]
    common = sorted(set.intersection(*[set(paths[s]) for s in SYMBOLS]))
    return paths, common


def signals(paths, common, x, y):
    """z-score of the beta-hedged spread, everything from PRIOR holds only (R9)."""
    close_x = np.array([paths[x][d][-1] for d in common])
    close_y = np.array([paths[y][d][-1] for d in common])
    lx, ly = np.log(close_x), np.log(close_y)
    n = len(common)
    beta = np.full(n, np.nan)
    z = np.full(n, np.nan)
    for i in range(LOOKBACK, n):
        wx, wy = lx[i - LOOKBACK:i], ly[i - LOOKBACK:i]      # STRICTLY prior
        v = np.var(wy)
        b = float(np.clip(np.cov(wx, wy)[0, 1] / v, 0.2, 3.0)) if v > 0 else 1.0
        beta[i] = b
        sp = wx - b * wy
        sd = sp.std(ddof=1)
        z[i] = ((lx[i] - b * ly[i]) - sp.mean()) / sd if sd > 0 else 0.0
    return beta, z


def walk(paths, common, x, y, beta, z):
    """State machine over holds. Signal at day i decides the NEXT hold."""
    pos = np.zeros(len(common))          # +1 long spread, -1 short spread
    age = 0
    state = 0
    for i in range(LOOKBACK, len(common) - 1):
        if state == 0:
            if z[i] < -Z_ENTRY:
                state, age = +1, 0
            elif z[i] > Z_ENTRY:
                state, age = -1, 0
        else:
            age += 1
            if abs(z[i]) < Z_EXIT or age >= MAX_HOLDS:
                state = 0
        pos[i + 1] = state
    return pos


def hold_returns(paths, common, x, y, beta, pos):
    """Per-hold spread return, MAE on the sized path, and the leg exposures."""
    rets, maes, betas = [], [], []
    for i, d in enumerate(common):
        if pos[i] == 0:
            rets.append(0.0); maes.append(0.0); betas.append(0.0)
            continue
        px, py = paths[x][d], paths[y][d]
        n = min(len(px), len(py))
        b = beta[i - 1] if i > 0 and np.isfinite(beta[i - 1]) else 1.0
        rx = px[:n] / px[0] - 1.0
        ry = py[:n] / py[0] - 1.0
        eq = 1.0 + pos[i] * (rx - b * ry)
        peak = np.maximum.accumulate(eq)
        maes.append(float((1.0 - eq / peak).max()))
        rets.append(float(eq[-1] - 1.0))
        betas.append(float(pos[i] * (1.0 - b)))      # net beta of the sized book
    turn = np.abs(np.diff(pos, prepend=0.0))
    cost = turn * 2.0 * LEG_RT                       # two legs
    return np.array(rets) - cost, np.array(maes), np.array(betas)


def score(rets, maes, mkt, mask, label):
    r, m = rets[mask], maes[mask]
    live = r[np.asarray(mask)] if False else r
    n_trades = int((np.abs(np.diff(np.sign(r) != 0, prepend=False))).sum()) if False else None
    held = m > 0
    breach = float((m > FLOOR).mean()) if len(m) else 0.0
    mean = float(r.mean()) if len(r) else 0.0
    life = (1.0 / breach / PPY) if breach > 0 else float("inf")
    profit = (mean / breach) if breach > 0 else float("inf")
    # net beta of the realised book, regressed on the equal-weighted index
    mm = mkt[mask]
    beta_book = float(np.polyfit(mm, r, 1)[0]) if len(r) > 30 and mm.std() > 0 else float("nan")
    worst = float(r.min()) if len(r) else 0.0
    return {
        "label": label, "n_holds": int(len(r)), "exposure": float(held.mean()),
        "ann_return": mean * PPY, "ann_vol": float(r.std(ddof=1) * math.sqrt(PPY)),
        "sharpe": float(mean / r.std(ddof=1) * math.sqrt(PPY)) if r.std(ddof=1) > 0 else 0.0,
        "breach_rate": breach, "expected_life_years": life,
        "profit_before_breach": profit,
        "mae_p99": float(np.percentile(m[held], 99)) if held.any() else 0.0,
        "worst_hold": worst, "net_beta": beta_book,
        "clears_P4": bool(life > 3.0), "clears_P3": bool(abs(worst) <= P3_LIMIT),
        "clears_V": bool(mean > 0.0), "clears_LADDER": bool(profit > LADDER),
        "clears_NEUTRALITY": bool(np.isfinite(beta_book) and abs(beta_book) < BETA_LIMIT),
    }


def rotation_null(rets, pos, mask, n_sims, seed):
    """Same entry count, same holding lengths, WRONG BARS."""
    rng = np.random.default_rng(seed)
    r = rets[mask]
    n = len(r)
    sh = np.empty(n_sims); mn = np.empty(n_sims)
    for k in range(n_sims):
        rot = np.roll(r, int(rng.integers(1, n)))
        s = rot.std(ddof=1)
        sh[k] = (rot.mean() / s * math.sqrt(PPY)) if s > 0 else 0.0
        mn[k] = float(np.expm1(np.log1p(rot).sum()))
    return sh, mn


def build() -> dict:
    t0 = time.time()
    paths, common = load_paths()
    print(f"{len(common):,} common holds, {common[0]} to {common[-1]}")
    mkt = np.array([np.mean([paths[s][d][-1] / paths[s][d][0] - 1.0 for s in SYMBOLS])
                    for d in common])
    days = np.array(common)
    scr = days <= SCREEN_END
    hld = days > SCREEN_END
    y2020 = np.array([d[:4] == "2020" for d in common])

    cells = {}
    for x, y in itertools.combinations(SYMBOLS, 2):
        beta, z = signals(paths, common, x, y)
        pos = walk(paths, common, x, y, beta, z)
        rets, maes, betas = hold_returns(paths, common, x, y, beta, pos)
        key = f"{x}-{y}"
        c = {"screen": score(rets, maes, mkt, scr, "screen"),
             "holdout": score(rets, maes, mkt, hld, "holdout"),
             "y2020": score(rets, maes, mkt, hld & y2020, "2020"),
             "trades": int((np.diff(pos, prepend=0.0) != 0).sum() // 2),
             "mean_abs_beta_tilt": float(np.mean(np.abs(betas[betas != 0]))) if (betas != 0).any() else 0.0}
        sh, mn = rotation_null(rets, pos, hld, N_SIMS, SEED)
        h = c["holdout"]
        c["null"] = {
            "sharpe_pct": float((sh < h["sharpe"]).mean() * 100.0),
            "money_pct": float((mn < np.expm1(np.log1p(rets[hld]).sum())).mean() * 100.0),
        }
        c["clears_NULL"] = bool(c["null"]["sharpe_pct"] >= 95.0 and c["null"]["money_pct"] >= 95.0)
        c["success"] = bool(h["clears_V"] and c["clears_NULL"] and h["clears_NEUTRALITY"]
                            and h["clears_P3"] and h["clears_P4"])
        cells[key] = c
        print(f"  {key:9} trades {c['trades']:4d}  holdout ann {h['ann_return']:+7.2%} "
              f"breach {h['breach_rate']:.3%} beta {h['net_beta']:+.3f} "
              f"null {c['null']['sharpe_pct']:5.1f}/{c['null']['money_pct']:5.1f}  "
              f"[{time.time()-t0:.0f}s]")

    payload = {
        "study": "D261", "z_entry": Z_ENTRY, "z_exit": Z_EXIT, "lookback": LOOKBACK,
        "max_holds": MAX_HOLDS, "leg_rt_bps": LEG_RT * 1e4, "floor": FLOOR,
        "screen_end": SCREEN_END, "n_common": len(common),
        "span": [common[0], common[-1]], "cells": cells,
        "any_success": bool(any(c["success"] for c in cells.values())),
        "seconds": time.time() - t0,
    }
    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def render(p: dict) -> str:
    o = []
    a = o.append
    a("# D261 — the index spread, as a prop-track candidate\n")
    a(f"**Produced by** `scripts/run_index_spread.py` · {p['seconds']:.0f}s · "
      f"{p['n_common']:,} holds, {p['span'][0]} → {p['span'][1]}\n")
    a(f"\n`|z| > {p['z_entry']}` entry, `|z| < {p['z_exit']}` exit, {p['lookback']}-hold lookback, "
      f"{p['max_holds']}-hold cap, {p['leg_rt_bps']:.1f} bp per leg. "
      f"**All six pairs, no selection step.**\n")
    a("\n| pair | trades | ann return | vol | Sharpe | breach | life | worst | **net beta** | "
      "null (S/M) | V | NEUT | P3 | P4 | NULL | **success** |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|:--:|:--:|:--:|")
    for k, c in p["cells"].items():
        h = c["holdout"]
        life = "∞" if not np.isfinite(h["expected_life_years"]) else f"{h['expected_life_years']:.1f}y"
        a(f"| **{k}** | {c['trades']} | {h['ann_return']:+.2%} | {h['ann_vol']:.1%} | "
          f"{h['sharpe']:+.3f} | {h['breach_rate']:.3%} | {life} | {h['worst_hold']:.2%} | "
          f"**{h['net_beta']:+.3f}** | {c['null']['sharpe_pct']:.0f}/{c['null']['money_pct']:.0f} | "
          + " | ".join('y' if h[f"clears_{f}"] else 'n' for f in ("V", "NEUTRALITY", "P3", "P4"))
          + f" | {'y' if c['clears_NULL'] else 'n'} | "
          f"{'**YES**' if c['success'] else 'no'} |")
    a("\n## Verdict\n\n**" + ("At least one pair clears every hurdle." if p["any_success"] else
      "NO PAIR CLEARS V, NULL AND NEUTRALITY TOGETHER. Per D261's stop the spread category is "
      "CLOSED for the prop track — no threshold sweep, no second lookback, no cointegration screen "
      "added afterwards.") + "**\n")
    a("\n*Equity proxies, not futures. A pass would be a feasibility bound.*\n")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    p = json.loads(SUMMARY.read_text(encoding="utf-8")) if args.report_only else build()
    RESULTS.write_text(render(p), encoding="utf-8")
    for k, c in p["cells"].items():
        h = c["holdout"]
        print(f"{k:9} V={int(h['clears_V'])} NEUT={int(h['clears_NEUTRALITY'])} "
              f"P3={int(h['clears_P3'])} P4={int(h['clears_P4'])} "
              f"NULL={int(c['clears_NULL'])} -> {c['success']}")
    print("ANY SUCCESS:", p["any_success"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

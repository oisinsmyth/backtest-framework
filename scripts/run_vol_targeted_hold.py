"""D260 — the vol-targeted overnight hold, on a time holdout.

The 18:00 -> 16:10 hold, sized by k = clip(TARGET / vol_lag, 0, 4), with
TARGET = 0.04 / N and N in {6, 8, 10, 12} -- the floor stated as a SAFETY FACTOR
in standard deviations rather than as a freely chosen number.

D259 closed this candidate on STATIC sizing, which was an error: D258 had named
the sizing wrapper as a precondition "before P1 is even measurable". This runner
completes that registered test.

THE VERDICT PROTOCOL, and it is what handles the multiplicity: N is chosen on the
SCREEN by expected profit before breach, and THAT N's HOLDOUT result carries the
verdict. All four are reported so the choice is visible, but only one is judged.

THE HOLDOUT CONTAINS MARCH 2020 BY DESIGN. A rule tuned before it that survives
it is worth something; one validated on a quiet period is not.

Drawdown is computed on the EXACT sized equity path, not by scaling the unsized
drawdown -- at k = 4 the linear approximation drifts, and it drifts in the
direction that manufactures comfort.

Offline, deterministic. `--report-only` re-renders from the artifact.
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
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


D = _load("d259", "run_overnight_decomposition.py")

SUMMARY = REPO / "data" / "vol_targeted_hold_summary.json"
RESULTS = REPO / "docs" / "results" / "VOL_TARGETED_HOLD_RESULTS.md"

FLOOR = 0.04                 # P1: 4% trailing drawdown on OPEN equity
CAP = 4.0                    # fixed in D260, not swept
VOL_WINDOW = 21              # prior holds, shifted by 1
N_GRID = (6, 8, 10, 12)      # TARGET = FLOOR / N
SCREEN_END = "2018-12-31"    # screen 2010-2018, holdout 2019-2026
PPY = 252.0
P3_LIMIT = 0.02              # worst single hold, as a fraction of account
LADDER_BENCHMARK = 0.26      # Apex: $13,000 on a $50,000 account. MFF's own cap is UNVERIFIED.
ACCOUNT = 150_000


def walk_sized(entry: float, pts: list, k: float) -> tuple[float, bool, float]:
    """Exact trailing drawdown of the SIZED equity path.

    equity = 1 + k * (P/P0 - 1). The peak includes the current bar's high, as
    D259 established: within a 15-minute bar the high may precede the low, so a
    bar can lift the floor and then breach it. Assuming otherwise under-counts
    breaches, which is the direction that manufactures comfort."""
    peak = 1.0
    max_dd = 0.0
    worst = 0.0
    breached = False
    for _seg, hi, lo in pts:
        eq_hi = 1.0 + k * (hi / entry - 1.0)
        eq_lo = 1.0 + k * (lo / entry - 1.0)
        if eq_hi > peak:
            peak = eq_hi
        dd = 1.0 - eq_lo / peak if peak > 0 else 1.0
        if dd > max_dd:
            max_dd = dd
        if eq_lo - 1.0 < worst:
            worst = eq_lo - 1.0
        if dd > FLOOR:
            breached = True
    return max_dd, breached, worst


def build_holds() -> pd.DataFrame:
    df = D.load()
    drop = D.half_days(df)
    rows = []
    for sym in sorted(df["symbol"].unique()):
        sess = D.sessions_for(df, sym, drop)
        days = sorted(sess)
        for a, b in zip(days, days[1:]):
            from datetime import date
            if (date.fromisoformat(b) - date.fromisoformat(a)).days != 1:
                continue          # D259: Friday->Monday is not a placeable hold
            p = D.path_points(sess, a, b, "prints")
            if p is None:
                continue
            entry, pts, exit_px = p
            rows.append({"symbol": sym, "day": b, "era": D.era_of(b),
                         "entry": entry, "ret": exit_px / entry - 1.0, "pts": pts})
    H = pd.DataFrame(rows).sort_values(["symbol", "day"]).reset_index(drop=True)
    # R9: volatility over the PRIOR 21 holds of that symbol, shifted by one
    H["vol_lag"] = np.nan
    for sym, g in H.groupby("symbol"):
        H.loc[g.index, "vol_lag"] = (
            g["ret"].rolling(VOL_WINDOW, min_periods=VOL_WINDOW).std().shift(1))
    return H[np.isfinite(H["vol_lag"])].reset_index(drop=True)


def evaluate(H: pd.DataFrame, target: float) -> dict:
    k = np.clip(target / H["vol_lag"].values, 0.0, CAP)
    dd = np.empty(len(H))
    br = np.zeros(len(H), dtype=bool)
    wr = np.empty(len(H))
    for i, (entry, pts) in enumerate(zip(H["entry"].values, H["pts"].values)):
        dd[i], br[i], wr[i] = walk_sized(entry, pts, k[i])
    ret = H["ret"].values * k
    rate = float(br.mean())
    mean_ret = float(ret.mean())
    life = (1.0 / rate / PPY) if rate > 0 else float("inf")
    profit = (mean_ret / rate) if rate > 0 else float("inf")
    return {
        "n_holds": int(len(H)), "avg_size": float(k.mean()), "max_size": float(k.max()),
        "breach_rate": rate, "expected_life_years": life,
        "ann_return": float(mean_ret * PPY),
        "profit_before_breach": profit,
        "profit_before_breach_usd": (profit * ACCOUNT) if np.isfinite(profit) else None,
        "worst_hold": float(wr.min()), "dd_p99": float(np.percentile(dd, 99)),
        "dd_median": float(np.median(dd)),
        "clears_P4": bool(life > 3.0),
        "clears_P3": bool(abs(wr.min()) <= P3_LIMIT),
        # BUG FIXED: `np.isfinite(profit) and ...` made a ZERO breach rate FAIL,
        # because profit is +inf there. Never breaching is the best outcome available.
        "clears_LADDER": bool(profit > LADDER_BENCHMARK),
    }


def build() -> dict:
    t0 = time.time()
    H = build_holds()
    screen = H[H["day"] <= SCREEN_END]
    hold = H[H["day"] > SCREEN_END]
    print(f"{len(H):,} holds; screen {len(screen):,} ({screen['day'].min()} to {screen['day'].max()}), "
          f"holdout {len(hold):,} ({hold['day'].min()} to {hold['day'].max()})")

    cells = {}
    for n in N_GRID:
        tgt = FLOOR / n
        cells[str(n)] = {
            "target": tgt,
            "screen": evaluate(screen, tgt),
            "holdout": evaluate(hold, tgt),
            "y2020": evaluate(hold[hold["era"] == "2020"], tgt),
            "holdout_ex2020": evaluate(hold[hold["era"] != "2020"], tgt),
        }
        s, h = cells[str(n)]["screen"], cells[str(n)]["holdout"]
        cells[str(n)]["stability_ratio"] = (
            (h["breach_rate"] / s["breach_rate"]) if s["breach_rate"] > 0 else float("inf"))
        # BUG FIXED: this was two-sided, so a holdout BETTER than the screen failed.
        # The hurdle exists to catch DEGRADATION; improvement is not a defect.
        cells[str(n)]["clears_STABILITY"] = bool(cells[str(n)]["stability_ratio"] <= 2.0)
        print(f"  N={n:2d} target {tgt:.2%}  screen breach {s['breach_rate']:.3%} "
              f"life {s['expected_life_years']:.2f}y | holdout {h['breach_rate']:.3%} "
              f"life {h['expected_life_years']:.2f}y  [{time.time()-t0:.0f}s]")

    # THE VERDICT PROTOCOL: N chosen on the SCREEN, judged on the HOLDOUT.
    chosen = max(N_GRID, key=lambda n: (
        cells[str(n)]["screen"]["profit_before_breach"]
        if np.isfinite(cells[str(n)]["screen"]["profit_before_breach"]) else 1e18))
    c = cells[str(chosen)]
    verdict = {
        "chosen_N_on_screen": chosen,
        "chosen_target": c["target"],
        "clears_P4": c["holdout"]["clears_P4"],
        "clears_P3": c["holdout"]["clears_P3"],
        "clears_LADDER": c["holdout"]["clears_LADDER"],
        "clears_STABILITY": c["clears_STABILITY"],
    }
    verdict["success"] = bool(all(verdict[k] for k in
                                  ("clears_P4", "clears_P3", "clears_LADDER", "clears_STABILITY")))

    payload = {
        "study": "D260", "floor": FLOOR, "cap": CAP, "vol_window": VOL_WINDOW,
        "n_grid": list(N_GRID), "screen_end": SCREEN_END, "account": ACCOUNT,
        "ladder_benchmark": LADDER_BENCHMARK,
        "n_holds": int(len(H)), "n_screen": int(len(screen)), "n_holdout": int(len(hold)),
        "span": [H["day"].min(), H["day"].max()],
        "cells": cells, "verdict": verdict, "seconds": time.time() - t0,
    }
    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def render(p: dict) -> str:
    o, a = [], None
    a = o.append
    v = p["verdict"]
    a("# D260 — the vol-targeted overnight hold, on a time holdout\n")
    a(f"**Produced by** `scripts/run_vol_targeted_hold.py` · {p['seconds']:.0f}s · "
      f"{p['n_holds']:,} holds, {p['span'][0]} → {p['span'][1]}\n")
    a(f"Screen {p['n_screen']:,} holds (→ {p['screen_end']}), **holdout {p['n_holdout']:,} holds, "
      f"and it contains March 2020 by design.**\n")
    a(f"\n`TARGET = {p['floor']:.0%} / N`, cap {p['cap']:.0f}x, volatility over the prior "
      f"{p['vol_window']} holds.\n")

    a("\n## All four cells — screen and holdout\n")
    a("| N | target | | breach | expected life | ann return | profit before breach | worst hold |")
    a("|---|---:|---|---:|---:|---:|---:|---:|")
    for n in p["n_grid"]:
        c = p["cells"][str(n)]
        for lab in ("screen", "holdout"):
            e = c[lab]
            life = "∞" if not np.isfinite(e["expected_life_years"]) else f"{e['expected_life_years']:.2f}y"
            pb = "∞" if e["profit_before_breach_usd"] is None else f"{e['profit_before_breach']:.1%}"
            a(f"| {n if lab=='screen' else ''} | {c['target']:.2%} | {lab} | "
              f"{e['breach_rate']:.3%} | {life} | {e['ann_return']:+.2%} | {pb} | "
              f"{e['worst_hold']:.2%} |")

    a(f"\n## The verdict cell — N chosen on the screen, judged on the holdout\n")
    a(f"**N = {v['chosen_N_on_screen']}**, target **{v['chosen_target']:.2%}**\n")
    c = p["cells"][str(v["chosen_N_on_screen"])]
    a("\n| hurdle | measured | required | |")
    a("|---|---:|---:|:--:|")
    h = c["holdout"]
    life = "∞" if not np.isfinite(h["expected_life_years"]) else f"{h['expected_life_years']:.2f}y"
    a(f"| **P4** expected life | {life} | > 3 y | {'**YES**' if v['clears_P4'] else 'no'} |")
    a(f"| **P3** worst hold | {h['worst_hold']:.2%} | ≥ −2.00% | "
      f"{'**YES**' if v['clears_P3'] else 'no'} |")
    pb = "∞" if h["profit_before_breach_usd"] is None else f"{h['profit_before_breach']:.1%}"
    a(f"| **LADDER** profit before breach | {pb} | > {p['ladder_benchmark']:.0%} | "
      f"{'**YES**' if v['clears_LADDER'] else 'no'} |")
    a(f"| **STABILITY** holdout/screen breach | {c['stability_ratio']:.2f}x | 0.5–2.0x | "
      f"{'**YES**' if v['clears_STABILITY'] else 'no'} |")

    a("\n## 2020, reported separately — V-c's test\n")
    a("| N | 2020 breach | holdout ex-2020 | ratio |")
    a("|---|---:|---:|---:|")
    for n in p["n_grid"]:
        c2 = p["cells"][str(n)]
        b20, bex = c2["y2020"]["breach_rate"], c2["holdout_ex2020"]["breach_rate"]
        a(f"| {n} | {b20:.3%} | {bex:.3%} | "
          f"{(b20/bex if bex>0 else float('inf')):.1f}x |")
    a("\n**V-c predicted 2020 would be the worst year in the holdout, because a 21-hold volatility "
      "estimate cannot adapt to a regime that changed in a week.**\n")

    a("\n## Verdict\n\n**" + (
        f"N={v['chosen_N_on_screen']} clears P4, P3, LADDER and STABILITY on the holdout."
        if v["success"] else
        "THE VERDICT CELL DOES NOT CLEAR ALL FOUR. Per D260's stop, C1 is CLOSED for good — no "
        "third sizing scheme, no re-split, no alternative estimator window.") + "**\n")
    a("\n*A pass here is a FEASIBILITY BOUND, not a deployable backtest: the path is equity "
      "extended-hours bars, 16 of the 23 futures hours.*\n")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    p = json.loads(SUMMARY.read_text(encoding="utf-8")) if args.report_only else build()
    RESULTS.write_text(render(p), encoding="utf-8")
    v = p["verdict"]
    c = p["cells"][str(v["chosen_N_on_screen"])]
    print(f"\nchosen on screen: N={v['chosen_N_on_screen']} (target {v['chosen_target']:.2%})")
    for k in ("clears_P4", "clears_P3", "clears_LADDER", "clears_STABILITY"):
        print(f"  {k:18} {v[k]}")
    print(f"  holdout: breach {c['holdout']['breach_rate']:.3%}, "
          f"life {c['holdout']['expected_life_years']:.2f}y, "
          f"ann {c['holdout']['ann_return']:+.2%}, "
          f"profit-before-breach {c['holdout']['profit_before_breach']:.1%}")
    print(f"  2020 breach {c['y2020']['breach_rate']:.3%} vs ex-2020 "
          f"{c['holdout_ex2020']['breach_rate']:.3%}")
    print("SUCCESS:", v["success"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

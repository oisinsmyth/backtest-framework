"""D254 — the wedge breakout on crypto.

D249's construction, frozen, on D244's 34-coin fixture. A MECHANISM TEST before
it is a strategy test: the principal's hypothesis says a weighted average cancels
the asset-specific information a breakout needs, so the ETF wedge should fail and
the crypto wedge should not.

THE LOAD-BEARING NUMBER IS THE ANATOMY'S SIGN, NOT ANY CELL. On 57 ETFs the
up-minus-down spread is NEGATIVE at every horizon (-8.08 / -6.96 / -8.84 /
-10.05). If the mechanism holds, crypto's is positive. That is X-2.

Scoring is D253's pooled model B, because model A ruins on this universe. It
FLATTERS the arms and the model-A ruin is reported beside it.

Hurdle V is new and forced by D253's recorded defect: H without a positive-CAGR
bar is a skill measurement, not a result.

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


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


W = _load("d249_wedge", "run_wedge_inverse.py")       # wedge_signals, ARM_ATR, K
D = _load("d253_shorts", "run_book_shorts_crypto.py")  # pooled scoring, ruin, nulls
C, L = D.C, D.L

SUMMARY = REPO / "data" / "wedge_crypto_summary.json"
RESULTS = REPO / "docs" / "results" / "WEDGE_CRYPTO_RESULTS.md"

SEED, N_SIMS = D.SEED, D.N_SIMS
PPY = D.PPY_CRYPTO
TRIG_ATR = 2.0
HOLD = 21
HORIZONS = (5, 10, 21, 42, 63)
CELL_ORDER = ("U_long", "D_long", "D_short")

# D249's measured ETF anatomy, for the side-by-side the whole study turns on
ETF_ANATOMY = {5: (6.47, 14.55), 10: (6.89, 9.05), 21: (8.33, 15.29),
               42: (9.47, 18.31), 63: (8.00, 18.04)}


def load_crypto():
    """D253's fixture and overrides, reused rather than restated."""
    panel, start, _, ones = D.books_on_crypto()
    return panel, start, ones


def wedge_on(panel, cleaned, start):
    saved_k = W.K
    return W.wedge_signals(panel, cleaned, start)


def triggers(panel, sig, start: int):
    """UP and DOWN break masks. R9 BY CONSTRUCTION: `armed`, `centre` and `atr` are
    all read at t-1; the comparison close is at t; exposure begins at t+1."""
    logC = np.log(panel.closes)
    n, T = logC.shape
    armed_l = np.zeros((n, T), dtype=bool)
    armed_l[:, 1:] = sig["armed"][:, :-1]
    up_lvl = np.full((n, T), np.nan)
    dn_lvl = np.full((n, T), np.nan)
    up_lvl[:, 1:] = (sig["centre"] + TRIG_ATR * sig["atr"])[:, :-1]
    dn_lvl[:, 1:] = (sig["centre"] - TRIG_ATR * sig["atr"])[:, :-1]
    with np.errstate(invalid="ignore"):
        up = armed_l & (logC > up_lvl)
        dn = armed_l & (logC < dn_lvl)
    up[:, :start] = False
    dn[:, :start] = False
    return up, dn


def walk(panel, fire, start: int, hold: int, side: float):
    """One trade per firing, no overlapping trades on one symbol.

    D249's convention: the break is detected at the close of `t`, so exposure
    begins at `t+1` and the entry price is `C[t]`."""
    n, T = panel.closes.shape
    pos = np.zeros((n, T))
    entries, suppressed = 0, 0
    for i in range(n):
        held_to = -1
        for t in np.flatnonzero(fire[i]):
            if t <= held_to:
                suppressed += 1
                continue
            a = t + 1
            b = min(t + hold, T - 1)
            if a > b:
                continue
            pos[i, a:b + 1] = side
            held_to = b
            entries += 1
    pos[:, :start] = 0.0
    return pos, entries, suppressed


def anatomy(panel, up, dn, start: int):
    """Forward returns after each break, annualised, set beside D249's ETF table."""
    lr = panel.total_log_returns
    n, T = lr.shape
    cs = np.concatenate([np.zeros((n, 1)), np.cumsum(lr, axis=1)], axis=1)
    out = {}
    for h in HORIZONS:
        row = {}
        for lab, mask in (("up", up), ("down", dn)):
            ii, tt = np.where(mask)
            keep = tt + 1 + h <= T
            ii, tt = ii[keep], tt[keep]
            if len(ii) == 0:
                row[lab] = (None, 0)
                continue
            fwd = cs[ii, tt + 1 + h] - cs[ii, tt + 1]
            row[lab] = (float(np.expm1(fwd.mean() * PPY / h)), int(len(ii)))
        u, d = row["up"][0], row["down"][0]
        row["spread"] = (u - d) if (u is not None and d is not None) else None
        out[h] = row
    return out


def build() -> dict:
    t0 = time.time()
    saved = (D.X.PPY, D.X.RF_PER_BAR, D.X.BORROW_PER_BAR)
    panel, start, ones = load_crypto()

    # rebuild `cleaned` inside the override block, the way D253 does
    sf, se, sp = L.FIXTURE, L.EVENTS, L.PPY
    try:
        L.FIXTURE, L.EVENTS, L.PPY = C.FIXTURE, C.EVENTS, PPY
        _, cleaned = L.load_panel()
    finally:
        L.FIXTURE, L.EVENTS, L.PPY = sf, se, sp

    D.X.PPY = PPY
    D.X.RF_PER_BAR = math.log1p(D.RF_ANNUAL) / PPY
    D.X.BORROW_PER_BAR = math.log1p(D.BORROW_CRYPTO) / PPY
    try:
        sig = wedge_on(panel, cleaned, start)
        up, dn = triggers(panel, sig, start)
        anat = anatomy(panel, up, dn, start)

        books, meta = {}, {}
        for k, fire, side in (("U_long", up, 1.0), ("D_long", dn, 1.0), ("D_short", dn, -1.0)):
            pos, e, s = walk(panel, fire, start, HOLD, side)
            books[k] = pos
            meta[k] = {"entries": e, "suppressed": s}

        cells = {k: D.pooled_score(panel, v, start) for k, v in books.items()}
        ruin = {k: D.model_a_ruin(panel, v, start) for k, v in books.items()}
        nulls = D.pooled_rotation_nulls(panel, books, start)
        rng = np.random.default_rng(SEED)
        conc = {k: D.concurrency(v, start, rng) for k, v in books.items()}
        eff = D.effective_instruments(panel, start)
        drift = D.universe_drift(panel, start)
        armed_frac = float(sig["armed"][:, start:].mean())
    finally:
        D.X.PPY, D.X.RF_PER_BAR, D.X.BORROW_PER_BAR = saved

    assert D.X.PPY == saved[0] and L.FIXTURE == sf, "overrides leaked"

    draws, money = nulls["draws"], nulls["money"]
    verdict = {}
    for k in CELL_ORDER:
        sp_ = float((np.asarray(draws[k]) < cells[k]["excess_sharpe"]).mean() * 100.0)
        mp = float((np.asarray(money[k]) < cells[k]["total_return"]).mean() * 100.0)
        verdict[k] = {
            "sharpe_pct": sp_, "money_pct": mp,
            "clears_H": bool(sp_ >= 95.0 and mp >= 95.0),
            "clears_V": bool(cells[k]["cagr"] > 0.0),
            "clears_E": cells[k]["clears_E"],
        }
        verdict[k]["success"] = bool(verdict[k]["clears_H"] and verdict[k]["clears_V"])
    best = np.max(np.vstack([np.asarray(draws[k]) for k in CELL_ORDER]), axis=0)

    n, T = panel.closes.shape
    payload = {
        "study": "D254", "seed": SEED, "n_sims": N_SIMS,
        "fixture": C.FIXTURE.name, "n_symbols": n, "bars": T, "start": start,
        "years": (T - start) / PPY, "ppy": PPY,
        "arm_atr": W.ARM_ATR, "trig_atr": TRIG_ATR, "hold": HOLD, "k": W.K,
        "armed_fraction": armed_frac,
        "universe_drift": drift, "effective_instruments": eff,
        "anatomy": {str(h): v for h, v in anat.items()},
        "etf_anatomy": {str(h): v for h, v in ETF_ANATOMY.items()},
        "cells": cells, "verdict": verdict, "concurrency": conc,
        "model_a_ruin": ruin, "walk_meta": meta,
        "best_of_floor_p95": float(np.percentile(best, 95)),
        "any_success": bool(any(verdict[k]["success"] for k in CELL_ORDER)),
        "seconds": time.time() - t0,
    }
    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def render(p: dict) -> str:
    o = []
    a = o.append
    a("# D254 — the wedge breakout on crypto\n")
    a(f"**Produced by** `scripts/run_wedge_crypto.py` · seed {p['seed']} · "
      f"{p['n_sims']:,} null draws · {p['seconds']:.1f}s\n")
    a(f"`{p['fixture']}` — {p['n_symbols']} coins x {p['bars']:,} bars, {p['years']:.2f} live "
      f"years. k={p['k']}, arm ≤ {p['arm_atr']} ATR, trigger ±{p['trig_atr']} ATR, hold "
      f"{p['hold']}. Armed on **{p['armed_fraction']:.2%}** of live cells.\n")
    a(f"\nUniverse CAGR {p['universe_drift']['equal_weighted_cagr']:+.2%}, "
      f"{p['universe_drift']['symbols_that_fell']} of {p['universe_drift']['n_symbols']} coins "
      f"fell. Effective instruments **{p['effective_instruments']:.2f}**.\n")

    a("\n## X-2 — the anatomy, beside D249's ETF table. This is the load-bearing number.\n")
    a("| horizon | **crypto up** | **crypto down** | **crypto spread** | *ETF up* | *ETF down* | "
      "*ETF spread* |")
    a("|---:|---:|---:|---:|---:|---:|---:|")
    for h in HORIZONS:
        r = p["anatomy"][str(h)]
        eu, ed = p["etf_anatomy"][str(h)]
        u = f"{r['up'][0]:+.2%} ({r['up'][1]:,})" if r["up"][0] is not None else "—"
        d = f"{r['down'][0]:+.2%} ({r['down'][1]:,})" if r["down"][0] is not None else "—"
        s = f"**{r['spread']:+.2%}**" if r["spread"] is not None else "—"
        a(f"| {h} | {u} | {d} | {s} | *{eu:+.2f}%* | *{ed:+.2f}%* | *{eu-ed:+.2f}%* |")
    signs = [p["anatomy"][str(h)]["spread"] for h in HORIZONS]
    pos = sum(1 for s in signs if s is not None and s > 0)
    a(f"\n**Crypto spread positive at {pos} of {len(HORIZONS)} horizons.** "
      f"ETF spread is negative at all five. "
      f"**X-2 {'CONFIRMED' if pos >= 4 else ('PARTIAL' if pos >= 3 else 'FALSIFIED')}.**\n")

    a("\n## Cells\n")
    a("| cell | exposure | CAGR | excess Sharpe | max DD | entries | min/sym | "
      "H (Sharpe/money) | V | E | **success** |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|")
    for k in CELL_ORDER:
        c, v = p["cells"][k], p["verdict"][k]
        a(f"| **{k}** | {c['exposure_gross']:.1%} | {c['cagr']:+.2%} | {c['excess_sharpe']:+.3f} | "
          f"{c['max_drawdown']:.2%} | {c['entries']:,} | {c['min_entries_per_symbol']} | "
          f"{v['sharpe_pct']:.1f}th / {v['money_pct']:.1f}th | "
          f"{'yes' if v['clears_V'] else 'no'} | {'yes' if v['clears_E'] else 'no'} | "
          f"{'**YES**' if v['success'] else 'no'} |")

    a("\n## R10 — concurrency\n")
    a("| cell | mean | max | *rotated max* | sd ratio |")
    a("|---|---:|---:|---:|---:|")
    for k in CELL_ORDER:
        c = p["concurrency"][k]
        a(f"| {k} | {c['mean']:.1f} | **{c['max']}** of {c['names']} | *{c['rot_max']}* | "
          f"{c['sd_ratio']:.2f}x |")

    a("\n## Model-A ruin — full per-name notional\n")
    a("| cell | worst adverse bar | | max survivable notional |")
    a("|---|---:|---|---:|")
    for k in CELL_ORDER:
        r = p["model_a_ruin"][k]
        ms = f"{r['max_survivable_notional']:.2f}x" if r["max_survivable_notional"] else "—"
        a(f"| {k} | {r['worst_adverse_bar']:+.1%} | {r['symbol']} {r['date']} | "
          f"{'**RUINED**' if r['ruined_at_1x'] else ms} |")

    a("\n## Verdict\n")
    a("**" + ("At least one cell clears H and V." if p["any_success"] else
             "NO CELL CLEARS BOTH H AND V. Per D254's stop this is CLOSED — no parameter sweep, "
             "no second arming threshold, no move to the 63-name universe. The anatomy's sign "
             "stands as a mechanism finding regardless.") + "**\n")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    args = ap.parse_args()
    p = json.loads(SUMMARY.read_text(encoding="utf-8")) if args.report_only else build()
    RESULTS.write_text(render(p), encoding="utf-8")
    print(f"armed {p['armed_fraction']:.2%} of cells")
    for h in HORIZONS:
        r = p["anatomy"][str(h)]
        u = r["up"][0]; d = r["down"][0]
        print(f"  h={h:2d}  up {u:+8.2%} ({r['up'][1]:4,})  down {d:+8.2%} ({r['down'][1]:4,})  "
              f"spread {r['spread']:+8.2%}")
    for k in CELL_ORDER:
        c, v = p["cells"][k], p["verdict"][k]
        print(f"  {k:8} expo {c['exposure_gross']:5.1%} CAGR {c['cagr']:+7.2%} "
              f"exS {c['excess_sharpe']:+6.3f} null {v['sharpe_pct']:5.1f}/{v['money_pct']:5.1f} "
              f"H={v['clears_H']} V={v['clears_V']} E={v['clears_E']}")
    print("ANY SUCCESS:", p["any_success"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

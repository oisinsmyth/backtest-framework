"""D256 — the short arms and the take-profit overlay, on single names.

Part A: S1_short, S2_short, C_short, frozen from D253.
Part B: take-profit at +10/20/30 on S1, S2, C, frozen from D255. Stops are NOT
        re-tested -- D255 established the asymmetry on two independent controls.

RAGGED BY NECESSITY. `load_panel` refuses unequal bar counts, and that requirement
is exactly what deletes the 564 dead names this study exists to measure. The
contract is in `scripts/ragged_panel.py` and was fixed in D256 before either file
was written: per-symbol live windows, EQUAL WEIGHT OVER LIVE NAMES rather than
over `n`, delisting as an exit with no foreknowledge, no forward-filled prices.

INDICATORS ARE COMPUTED ON EACH SYMBOL'S OWN SERIES AND SCATTERED into the global
grid, so a 252-bar window always means 252 of that symbol's bars.

Offline, deterministic, seed 0. `--report-only` re-renders. `--smoke` runs a
reduced null count for timing.
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
from backtest_framework.research.structure import pivots  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


RP = _load("ragged", "ragged_panel.py")
A = _load("d234_activation", "run_activation_threshold.py")
U = _load("d240_uptrend", "run_uptrend_onset.py")

FIX = REPO / "data" / "fixtures"
FIXTURE = FIX / "us_shorts_daily_raw.csv.gz"
EVENTS = FIX / "us_shorts_daily_raw_events.json"
SUMMARY = REPO / "data" / "book_single_names_summary.json"
RESULTS = REPO / "BOOK_SINGLE_NAMES_RESULTS.md"

SEED = 0
PPY = 252.0
RF_ANNUAL = 0.04
BORROW_ANNUAL = 0.03          # US single-name general collateral; breakeven reported regardless
FEE_BPS = 5.0                 # single names are dearer than the ETF book's ~1.9bp
TARGETS = (0.10, 0.20, 0.30)
SHORT_CELLS = ("S1_short", "S2_short", "C_short")
LONG_ARMS = ("S1", "S2", "C")


def signals_ragged(panel, cleaned, start):
    """S1's and S2's parts, computed per symbol and scattered into the grid."""
    n, T = panel.closes.shape
    md = np.full((n, T), np.nan)
    hs = np.full((n, T), np.nan)
    g_lo = np.full((n, T), np.nan)
    g_hi = np.full((n, T), np.nan)
    i_lo = np.full((n, T), np.nan)
    atr = np.full((n, T), np.nan)
    warm = np.zeros((n, T), dtype=bool)
    need = max(M.impulse_warm_up_bars(), M.warm_up_bars(), U.WINDOW)
    holed = 0
    for i, sym in enumerate(panel.symbols):
        bars = cleaned[sym]
        # SCATTER TO ACTUAL BAR INDICES, NOT A CONTIGUOUS SLICE. Some symbols carry
        # internal gaps (halts, provider holes), so `index_of`'s span is longer than
        # the bar count and a slice would misalign every indicator by the gap width.
        # Caught by an assertion on the first run -- AAV: window 2254 != bars 2252.
        at = np.flatnonzero(panel.live[i])
        assert at.size == len(bars), f"{sym}: live {at.size} != bars {len(bars)}"
        a, b = panel.index_of[sym]
        if (b - a + 1) != at.size:
            holed += 1
        m = at.size
        if m <= need + 5:
            continue
        mdv, hsv = A.log_parts(bars)
        md[i, at] = mdv
        hs[i, at] = hsv
        ps = pivots(bars, U.K)
        li = np.array([p.index for p in ps if p.sign < 0], dtype=int)
        hj = np.array([p.index for p in ps if p.sign > 0], dtype=int)
        lp = np.log([p.price for p in ps if p.sign < 0]) if len(li) else np.array([])
        hp = np.log([p.price for p in ps if p.sign > 0]) if len(hj) else np.array([])
        gl, il = U.rolling_fit(m, li, lp, U.K)
        gh, _ = U.rolling_fit(m, hj, hp, U.K)
        g_lo[i, at], i_lo[i, at], g_hi[i, at] = gl, il, gh
        atr[i, at] = U.atr_log(bars, U.ATR_WINDOW)
        # each symbol warms up on ITS OWN clock, counted in its own bars
        warm[i, at[need:]] = True
    print(f"  symbols with internal gaps: {holed} of {len(panel.symbols)}")
    return md, hs, g_lo, g_hi, i_lo, atr, warm


def hold_book(mask, warm):
    p = np.zeros(mask.shape, dtype=float)
    p[:, 1:] = mask[:, :-1]
    return p * warm


def walk_state(panel, state, warm, age_cap):
    """Enter at the first bar of an episode, exit at age cap or when the state ends.
    Per symbol, on that symbol's own bars. Reuses D240's semantics, not its code,
    because the grid is ragged."""
    n, T = state.shape
    pos = np.zeros((n, T))
    for i in range(n):
        idx = np.flatnonzero(warm[i])
        if idx.size == 0:
            continue
        st = state[i]
        t = idx[0]
        end = idx[-1]
        while t <= end:
            if st[t] and not (t > 0 and st[t - 1]):
                a = t + 1
                b = min(t + age_cap, end)
                while b > a and not st[b - 1]:
                    b -= 1
                if b >= a:
                    pos[i, a:b + 1] = 1.0
                    t = b
            t += 1
    return pos * warm


def take_profit(panel, base_pos, start, level):
    """D255's overlay: exit at the first close where the gain touches +level.
    Decided at the close of t, effective t+1. Stay flat until the base cycles."""
    out = base_pos.copy()
    closes = panel.closes
    on = base_pos > 0.0
    n, T = base_pos.shape
    cuts = 0
    for i in range(n):
        idx = np.flatnonzero(on[i])
        if idx.size == 0:
            continue
        brk = np.flatnonzero(np.diff(idx) != 1)
        starts = np.concatenate(([idx[0]], idx[brk + 1]))
        ends = np.concatenate((idx[brk], [idx[-1]]))
        for a, b in zip(starts, ends):
            if a <= start or a == 0 or np.isnan(closes[i, a - 1]):
                continue
            entry = closes[i, a - 1]
            seg = closes[i, a:b + 1] / entry - 1.0
            hit = np.flatnonzero(np.isfinite(seg) & (seg >= level))
            if hit.size:
                t = a + int(hit[0])
                if t < b:
                    out[i, t + 1:b + 1] = 0.0
                    cuts += 1
    return out, cuts


def reachability(panel, base_pos, start):
    closes = panel.closes
    on = base_pos > 0.0
    hi = []
    for i in range(base_pos.shape[0]):
        idx = np.flatnonzero(on[i])
        if idx.size == 0:
            continue
        brk = np.flatnonzero(np.diff(idx) != 1)
        starts = np.concatenate(([idx[0]], idx[brk + 1]))
        ends = np.concatenate((idx[brk], [idx[-1]]))
        for a, b in zip(starts, ends):
            if a <= start or a == 0 or np.isnan(closes[i, a - 1]):
                continue
            g = closes[i, a:b + 1] / closes[i, a - 1] - 1.0
            g = g[np.isfinite(g)]
            if g.size:
                hi.append(float(g.max()))
    hi = np.array(hi)
    out = {"trades": int(hi.size),
           "median_max_gain": float(np.median(hi)) if hi.size else float("nan")}
    for t in TARGETS:
        out["reach_TP%02d" % int(100 * t)] = float(np.mean(hi >= t)) if hi.size else float("nan")
    return out


def build(n_sims: int) -> dict:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(FIXTURE, EVENTS, fee_bps=FEE_BPS)
    n, T = panel.closes.shape
    md, hs, g_lo, g_hi, i_lo, atr, warm = signals_ragged(panel, cleaned, 0)
    print(f"loaded+signals {time.time()-t0:.0f}s  {n} names x {T:,} bars")

    ok = ~(np.isnan(md) | np.isnan(hs)) & warm
    s1 = hold_book((hs > 0) & (md <= 0) & ok, warm)
    sok = ~(np.isnan(g_lo) | np.isnan(g_hi) | np.isnan(atr)) & warm
    s2 = walk_state(panel, (g_lo > 0) & (g_hi > 0) & sok, warm, U.AGE_CAP)
    dn = walk_state(panel, (g_lo < 0) & (g_hi < 0) & sok, warm, U.AGE_CAP)
    c = np.maximum(s1, s2)
    start = 0

    books = {"S1": s1, "S2": s2, "C": c}
    shorts = {"S1_short": -s1, "S2_short": -dn, "C_short": -np.maximum(s1, dn)}

    sc = lambda p: RP.score(panel, p, start, ppy=PPY, rf_annual=RF_ANNUAL,
                            borrow_annual=BORROW_ANNUAL)
    base = {k: sc(v) for k, v in books.items()}
    cells = {k: sc(v) for k, v in shorts.items()}
    reach = {k: reachability(panel, v, start) for k, v in books.items()}
    print(f"scored bases {time.time()-t0:.0f}s")

    tp_cells, tp_cuts = {}, {}
    for arm in LONG_ARMS:
        for lv in TARGETS:
            key = f"{arm}:TP%02d" % int(100 * lv)
            pos, cuts = take_profit(panel, books[arm], start, lv)
            tp_cells[key] = sc(pos)
            tp_cuts[key] = cuts

    verdict, nulls = {}, {}
    for k, v in shorts.items():
        sh, mn = RP.rotation_null(panel, v, start, n_sims=n_sims, seed=SEED, ppy=PPY,
                                  rf_annual=RF_ANNUAL, borrow_annual=BORROW_ANNUAL)
        sp = float((sh < cells[k]["excess_sharpe"]).mean() * 100.0)
        mp = float((mn < cells[k]["total_return"]).mean() * 100.0)
        verdict[k] = {"sharpe_pct": sp, "money_pct": mp,
                      "clears_H": bool(sp >= 95.0 and mp >= 95.0),
                      "clears_V": bool(cells[k]["cagr"] > 0.0),
                      "clears_E": cells[k]["clears_E"]}
        verdict[k]["success"] = bool(verdict[k]["clears_H"] and verdict[k]["clears_V"])
        nulls[k] = {"sharpe_p95": float(np.percentile(sh, 95)),
                    "money_p95": float(np.percentile(mn, 95))}
        print(f"  null {k} {time.time()-t0:.0f}s -> {sp:.1f}/{mp:.1f}")

    conc = {k: RP.concurrency(panel, v, start, SEED) for k, v in
            list(books.items()) + list(shorts.items())}
    payload = {
        "study": "D256", "seed": SEED, "n_sims": n_sims, "fixture": FIXTURE.name,
        "n_symbols": n, "bars": T, "ppy": PPY, "fee_bps": FEE_BPS,
        "borrow_annual_assumed": BORROW_ANNUAL,
        "span": [str(panel.dates[0]), str(panel.dates[-1])],
        "base": base, "cells": cells, "verdict": verdict, "nulls": nulls,
        "reachability": reach, "tp_cells": tp_cells, "tp_cuts": tp_cuts,
        "concurrency": conc,
        "any_short_success": bool(any(v["success"] for v in verdict.values())),
        "seconds": time.time() - t0,
    }
    SUMMARY.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return payload


def render(p: dict) -> str:
    o = []
    a = o.append
    a("# D256 — the short arms and the take-profit overlay, on single names\n")
    a(f"**Produced by** `scripts/run_book_single_names.py` · seed {p['seed']} · "
      f"{p['n_sims']:,} null draws · {p['seconds']:.0f}s\n")
    a(f"`{p['fixture']}` — **{p['n_symbols']:,} names x {p['bars']:,} bars**, "
      f"{p['span'][0]} → {p['span'][1]}. Fees {p['fee_bps']:.0f} bp/side, "
      f"borrow {p['borrow_annual_assumed']:.0%}/yr assumed.\n")
    a("\n**Ragged panel**: equal weight over LIVE names, per-symbol warm-up, no forward fill.\n")

    a("\n## Part B first — reachability, the quantity D255 said should differ\n")
    a("| arm | trades | median max gain | reach +10% | **+20%** | +30% | *ETF +20% (D255)* |")
    a("|---|---:|---:|---:|---:|---:|---:|")
    etf = {"S1": "2.8%", "S2": "9.7%", "C": "4.2%"}
    for k in LONG_ARMS:
        r = p["reachability"][k]
        a(f"| **{k}** | {r['trades']:,} | {r['median_max_gain']:+.2%} | "
          + " | ".join(f"{r['reach_TP%02d' % int(100*t)]:.1%}" for t in TARGETS)
          + f" | *{etf[k]}* |")

    a("\n### Take-profit cells\n")
    a("| cell | cuts | exposure | CAGR | excess Sharpe | vs base |")
    a("|---|---:|---:|---:|---:|---:|")
    for arm in LONG_ARMS:
        for lv in TARGETS:
            k = f"{arm}:TP%02d" % int(100 * lv)
            c = p["tp_cells"][k]
            a(f"| {k} | {p['tp_cuts'][k]:,} | {c['exposure_gross']:.1%} | {c['cagr']:+.2%} | "
              f"{c['excess_sharpe']:+.3f} | "
              f"{c['excess_sharpe']-p['base'][arm]['excess_sharpe']:+.3f} |")

    a("\n## Part A — the short arms\n")
    a("| cell | exposure | CAGR | **exposure x edge** | excess Sharpe | max DD | "
      "min entries/sym | H (Sharpe/money) | V | E | **success** |")
    a("|---|---:|---:|---:|---:|---:|---:|---:|:--:|:--:|:--:|")
    for k in SHORT_CELLS:
        c, v = p["cells"][k], p["verdict"][k]
        a(f"| **{k}** | {c['exposure_gross']:.1%} | {c['cagr']:+.2%} | "
          f"{c['gross_edge_annual']:+.2%} | {c['excess_sharpe']:+.3f} | "
          f"{c['max_drawdown']:.2%} | {c['min_entries_per_traded_symbol']} | "
          f"{v['sharpe_pct']:.1f}th / {v['money_pct']:.1f}th | "
          f"{'y' if v['clears_V'] else 'n'} | {'y' if v['clears_E'] else 'n'} | "
          f"{'**YES**' if v['success'] else 'no'} |")
    a("\n### Long arms, for reference\n")
    a("| arm | exposure | CAGR | excess Sharpe | max DD |")
    a("|---|---:|---:|---:|---:|")
    for k in LONG_ARMS:
        b = p["base"][k]
        a(f"| {k} | {b['exposure_gross']:.1%} | {b['cagr']:+.2%} | "
          f"{b['excess_sharpe']:+.3f} | {b['max_drawdown']:.2%} |")

    a("\n## Z-e — R10 concurrency, the mechanism test\n")
    a("| book | mean held | max | share of live (mean/max) | *rotated max* | **sd ratio** |")
    a("|---|---:|---:|---:|---:|---:|")
    for k, c in p["concurrency"].items():
        a(f"| {k} | {c['mean_held']:.1f} | {c['max_held']:,} | "
          f"{c['mean_share_of_live']:.1%} / {c['max_share_of_live']:.1%} | "
          f"*{c['rot_max_held']:,}* | **{c['sd_ratio']:.2f}x** |")
    a("\n*Prior clustering ratios: ETF wedge 3.02x, crypto S1_short 4.37x, gap screen 4.08x. "
      "Z-e predicted under 2.5x here.*\n")
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--sims", type=int, default=200)
    args = ap.parse_args()
    p = (json.loads(SUMMARY.read_text(encoding="utf-8")) if args.report_only
         else build(args.sims))
    RESULTS.write_text(render(p), encoding="utf-8")
    for k in LONG_ARMS:
        r = p["reachability"][k]
        print(f"{k}: {r['trades']:,} trades, med max gain {r['median_max_gain']:+.2%}, "
              f"reach+20 {r['reach_TP20']:.1%} (ETF was {['2.8%','9.7%','4.2%'][LONG_ARMS.index(k)]})")
    for k in SHORT_CELLS:
        c, v = p["cells"][k], p["verdict"][k]
        print(f"{k:10} expo {c['exposure_gross']:5.1%} CAGR {c['cagr']:+7.2%} "
              f"exS {c['excess_sharpe']:+6.3f} null {v['sharpe_pct']:5.1f}/{v['money_pct']:5.1f} "
              f"H={int(v['clears_H'])} V={int(v['clears_V'])} E={int(v['clears_E'])}")
    for k in ("S1", "C_short"):
        if k in p["concurrency"]:
            print(f"conc {k}: sd ratio {p['concurrency'][k]['sd_ratio']:.2f}x")
    print("ANY SHORT SUCCESS:", p["any_short_success"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

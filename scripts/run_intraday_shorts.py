"""D247 — the short side of S1 and S2 at fifteen minutes.

A 2 x 2 x 2 factorial: rule (S1, S2) x direction (short, long) x holding
(continuous, intraday-only). THE LONG CELLS ARE CONTROLS, NOT CANDIDATES --
without them a short failure cannot be attributed to direction rather than to
15-minute sampling breaking both estimators.

WHY THIS IS WORTH RUNNING, measured before the design: overnight drift on these
57 is +8.59%/yr and INTRADAY DRIFT IS -0.36%/yr. D238 closed directional shorts
close-to-close and was therefore paying the +8.59%. A book flat at every session
close faces -0.36% instead -- an 8.55-point swing -- and pays no overnight borrow.
That removes D238's structural objection; it supplies no edge, and D247's cost
arithmetic says nine tenths of the swing is eaten by the turnover to capture it.

THE CALENDAR MISMATCH IS SEVERE AND WORSE THAN D244'S. Bar counts are frozen
because the book specifies bars, but S1's 34-bar Impulse is 1.3 SESSIONS here
against seven weeks daily, and S2's 252-bar regression is 9.8 sessions against a
year. These are the same estimators at a radically shorter horizon.

BORROW IS CHARGED ONLY ACROSS SESSION BOUNDARIES, prorated by the real calendar
gap. Charging per 15-minute bar would be wrong by a factor of ~26. Intraday-only
cells therefore pay none, which is the honest model of a flat-at-close book.
Locate fees and SEC Rule 201 are named in D247 and are NOT modelled.

Offline, deterministic, seed 0. `--report-only` re-renders from the artifact.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.research import macd as M  # noqa: E402
from backtest_framework.research.structure import pivots  # noqa: E402


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


C = _load("d244_crypto", "run_book_crypto.py")
U, X, L, S, J = C.U, C.X, C.L, C.S, C.J

SUMMARY = REPO / "data" / "intraday_shorts_summary.json"
RESULTS = REPO / "INTRADAY_SHORTS_RESULTS.md"
FIX = REPO / "data" / "fixtures"
FIXTURE = FIX / "etf_intraday_15m_panel.csv.gz"
EVENTS = FIX / "etf_intraday_15m_panel_events.json"

SEED, N_SIMS = X.SEED, X.N_SIMS
RF_ANNUAL = X.RF_ANNUAL
BORROW_ANNUAL = 0.010                      # D238's committed constant
N_BOOT, BLOCK = J.N_BOOT, J.BLOCK

CELL_ORDER = ("S1_short_cont", "S1_short_intra", "S2_short_cont", "S2_short_intra",
              "S1_long_cont", "S1_long_intra", "S2_long_cont", "S2_long_intra")
SHORTS = CELL_ORDER[:4]
LABEL = {
    "S1_short_cont": "S1 mirror, short, holds overnight",
    "S1_short_intra": "S1 mirror, short, flat at every close",
    "S2_short_cont": "S2 downtrend, short, holds overnight",
    "S2_short_intra": "S2 downtrend, short, flat at every close",
    "S1_long_cont": "*S1 long — control*",
    "S1_long_intra": "*S1 long, intraday — control*",
    "S2_long_cont": "*S2 long — control*",
    "S2_long_intra": "*S2 long, intraday — control*",
}


# --------------------------------------------------------------------------
# Session structure and the two things that depend on it
# --------------------------------------------------------------------------


def session_structure(dates):
    day = np.array([d[:10] for d in dates])
    first = np.zeros(len(day), dtype=bool)
    first[0] = True
    first[1:] = day[1:] != day[:-1]
    gap = np.zeros(len(day))
    idx = np.where(first)[0]
    for j in range(1, len(idx)):
        a, b = idx[j - 1], idx[j]
        gap[b] = (datetime.fromisoformat(day[b]) - datetime.fromisoformat(day[a])).days
    return first, gap


def flatten_overnight(pos, first):
    """Intraday-only: FLAT at the first bar of every session.

    `position[t]` earns `log(C[t]/C[t-1])`, and at a session's first bar `C[t-1]`
    is the PREVIOUS session's last close -- so that bar's return IS the overnight
    gap. Zeroing it is exactly 'flat over the gap', and it is also why the
    intraday cells cannot pay overnight borrow."""
    out = pos.copy()
    out[:, first] = 0.0
    return out


def excess_intraday(total, pos, start, first, gap, ppy):
    """D247's financing. rf on the LONG fraction per bar; borrow ONLY where a short
    is carried across a session boundary, prorated by the real calendar gap."""
    live = pos[:, start:]
    long_f = np.maximum(live, 0.0).mean(axis=0)
    short_f = np.maximum(-live, 0.0).mean(axis=0)
    ex = total - long_f * (math.log1p(RF_ANNUAL) / ppy)
    fb, gd = first[start:], gap[start:]
    borrow = np.zeros_like(ex)
    borrow[fb] = short_f[fb] * math.log1p(BORROW_ANNUAL) * gd[fb] / 365.0
    return ex - borrow, float(borrow.sum())


def _sharpe(ex, ppy):
    sd = float(np.std(ex, ddof=1))
    return (float(np.mean(ex)) / sd * math.sqrt(ppy)) if sd > 0 else 0.0


def score(panel, pos, start, first, gap, ppy):
    total = X.signed_log_returns(panel, pos, total_return=True)[start:]
    ex, borrow = excess_intraday(total, pos, start, first, gap, ppy)
    live = pos[:, start:]
    turn = float(np.abs(np.diff(pos, axis=1, prepend=0.0))[:, start:].sum())
    active = (pos != 0.0).astype(float)
    ents = np.sum(np.diff(active, axis=1, prepend=0.0)[:, start:] > 0.0, axis=1)
    yrs = len(total) / ppy
    return {
        "excess_sharpe": _sharpe(ex, ppy),
        "total_return": L.total_return_of(total),
        "cagr": float(np.expm1(np.sum(total) / yrs)),
        "vol": float(np.std(total, ddof=1) * math.sqrt(ppy)),
        "max_drawdown": L.max_drawdown_of(total),
        "exposure_long": float(np.maximum(live, 0.0).mean()),
        "exposure_short": float(np.maximum(-live, 0.0).mean()),
        "turnover_per_year": turn / len(panel.symbols) / yrs,
        "borrow_paid_annualised": float(np.expm1(borrow / yrs)),
        "entries": int(ents.sum()),
        "min_entries_per_symbol": int(ents.min()),
        "clears_E": bool(ents.sum() >= 100 and ents.min() >= 30),
    }


def breakeven_bps(panel, pos, start, first, gap, ppy):
    """The per-side cost at which the arm's excess return reaches zero. Below the
    ~1.6 bp actually charged means costs alone sink it."""
    turn = float(np.abs(np.diff(pos, axis=1, prepend=0.0))[:, start:].sum()) / len(panel.symbols)
    if turn <= 0:
        return None
    total = X.signed_log_returns(panel, pos, total_return=True)[start:]
    ex, _ = excess_intraday(total, pos, start, first, gap, ppy)
    paid = float((panel.cost_fraction[:, None]
                  * np.abs(np.diff(pos, axis=1, prepend=0.0)))[:, start:].sum()
                 / len(panel.symbols))
    gross = float(np.sum(ex)) + paid
    return 1e4 * (1.0 - math.exp(-gross / turn))


def rotation_nulls(panel, books, start, first, gap, ppy):
    """Matched-count rotation with ONE SHARED OFFSET VECTOR across cells (D228), so
    the best-of floor is not inflated by making the cells artificially independent."""
    rng = np.random.default_rng(SEED)
    n, T = panel.closes.shape
    span = T - start
    names = list(books)
    per = {k: np.empty(N_SIMS) for k in names}
    best = np.empty(N_SIMS)
    # HOISTED. `signed_log_returns` recomputes `np.expm1(returns)` on 3.2M elements
    # on every call and the returns never change -- across 8,000 null evaluations
    # that is the single largest cost in the run. `_fast_total` is pinned against
    # `X.signed_log_returns` for exact equality before the loop starts.
    exp_rets = np.expm1(panel.total_log_returns)
    cost = panel.cost_fraction[:, None]

    def _fast_total(pos):
        charge = cost * np.abs(np.diff(pos, axis=1, prepend=0.0))
        return (np.log1p(pos * exp_rets) + np.log1p(-charge)).mean(axis=0)[start:]

    probe = next(iter(books.values()))
    assert np.allclose(_fast_total(probe),
                       X.signed_log_returns(panel, probe, total_return=True)[start:],
                       rtol=0, atol=1e-12), "the fast scorer diverged from the committed one"

    rot = np.zeros((n, T))
    for s in range(N_SIMS):
        off = rng.integers(1, span, size=n)
        vals = []
        for k in names:
            src = books[k][:, start:]
            for i in range(n):
                rot[i, start:] = np.roll(src[i], int(off[i]))
            ex, _ = excess_intraday(_fast_total(rot), rot, start, first, gap, ppy)
            v = _sharpe(ex, ppy)
            per[k][s] = v
            vals.append(v)
        best[s] = max(vals)
    return per, best


def build() -> dict:
    t0 = time.time()
    L.FIXTURE, L.EVENTS = FIXTURE, EVENTS
    panel, cleaned = L.load_panel()
    assert panel.closes.shape == (57, 55726), f"unexpected panel {panel.closes.shape}"
    first, gap = session_structure(panel.dates)
    n_sessions = int(first.sum())
    ppy = (panel.closes.shape[1] / n_sessions) * 252.0
    start = max(M.impulse_warm_up_bars(), M.warm_up_bars(), M.MATCHED_MOMENTUM_LOOKBACK)

    # S1's parts
    md, hs, ok = S.base_masks(panel, cleaned, start)

    # S2's parts. `U.signals` does not return g_hi, so both slopes are recomputed
    # from `U.rolling_fit` -- reuse of the tested primitive rather than a change to
    # a committed signature that three other runners depend on.
    n, T = panel.closes.shape
    g_lo = np.full((n, T), np.nan)
    g_hi = np.full((n, T), np.nan)
    i_lo = np.full((n, T), np.nan)
    atr = np.full((n, T), np.nan)
    for i, sym in enumerate(panel.symbols):
        ps = pivots(cleaned[sym], U.K)
        li = np.array([p.index for p in ps if p.sign < 0], dtype=int)
        hj = np.array([p.index for p in ps if p.sign > 0], dtype=int)
        g_lo[i], i_lo[i] = U.rolling_fit(
            T, li, np.log([p.price for p in ps if p.sign < 0]) if len(li) else np.array([]), U.K)
        g_hi[i], _ = U.rolling_fit(
            T, hj, np.log([p.price for p in ps if p.sign > 0]) if len(hj) else np.array([]), U.K)
        atr[i] = U.atr_log(cleaned[sym], U.ATR_WINDOW)
    sok = ~(np.isnan(g_lo) | np.isnan(g_hi) | np.isnan(atr))
    up = (g_lo > 0) & (g_hi > 0) & sok
    down = (g_lo < 0) & (g_hi < 0) & sok
    up[:, :start] = False
    down[:, :start] = False
    # verify the reconstruction matches the committed one
    up_ref, _, _, _ = U.signals(panel, cleaned, start)
    assert np.array_equal(up, up_ref), "the reconstructed UPTREND state differs from U.signals"

    s1_long = S.hold_book((hs > 0) & (md <= 0) & ok, start)
    s1_short = -S.hold_book((hs < 0) & (md >= 0) & ok, start)
    s2_long, _, _ = U.walk(panel, up, g_lo, i_lo, atr, start)
    s2_short = -U.walk(panel, down, g_lo, i_lo, atr, start)[0]

    books = {
        "S1_short_cont": s1_short, "S1_short_intra": flatten_overnight(s1_short, first),
        "S2_short_cont": s2_short, "S2_short_intra": flatten_overnight(s2_short, first),
        "S1_long_cont": s1_long, "S1_long_intra": flatten_overnight(s1_long, first),
        "S2_long_cont": s2_long, "S2_long_intra": flatten_overnight(s2_long, first),
    }
    for k in ("S1_short_intra", "S2_short_intra", "S1_long_intra", "S2_long_intra"):
        assert not books[k][:, first].any(), f"{k} is not flat at every session open"

    ones = np.ones_like(s1_long)
    ones[:, :start] = 0.0
    cells = {k: score(panel, v, start, first, gap, ppy) for k, v in books.items()}
    bh = score(panel, ones, start, first, gap, ppy)
    be = {k: breakeven_bps(panel, v, start, first, gap, ppy) for k, v in books.items()}
    for k in ("S1_short_intra", "S2_short_intra"):
        assert cells[k]["borrow_paid_annualised"] == 0.0, f"{k} paid overnight borrow"

    per, best = rotation_nulls(panel, books, start, first, gap, ppy)
    nulls = {}
    for k in CELL_ORDER:
        a = cells[k]["excess_sharpe"]
        nulls[k] = {"p50": float(np.percentile(per[k], 50)),
                    "p95": float(np.percentile(per[k], 95)),
                    "percentile_of_actual": float((per[k] < a).mean() * 100.0),
                    "clears_Q2": bool(a > float(np.percentile(per[k], 95)))}
    best_p95 = float(np.percentile(best, 95))

    # Q3 -- the bootstrap
    rb = np.random.default_rng(SEED)
    nlen = panel.closes.shape[1] - start
    nblk = math.ceil(nlen / BLOCK)
    idxs = [(rb.integers(0, nlen - BLOCK + 1, size=nblk)[:, None]
             + np.arange(BLOCK)[None, :]).ravel()[:nlen] for _ in range(N_BOOT)]
    boot = {}
    for k in CELL_ORDER:
        tot = X.signed_log_returns(panel, books[k], total_return=True)[start:]
        ex, _ = excess_intraday(tot, books[k], start, first, gap, ppy)
        d = np.array([_sharpe(ex[i], ppy) for i in idxs])
        boot[k] = {"p05": float(np.percentile(d, 5)), "p95": float(np.percentile(d, 95)),
                   "clears_Q3": bool(np.percentile(d, 5) > 0.0)}

    # the conditional-return profile of the bars each short holds (D244's lesson:
    # a null can be beaten or lost by drift structure alone)
    rets = panel.total_log_returns
    cond = {}
    for k in SHORTS:
        held = books[k][:, start:] != 0.0
        v = rets[:, start:][held]
        cond[k] = {"bars": int(v.size),
                   "annualised": float(np.expm1(v.mean() * ppy)) if v.size else None}
    allbars = rets[:, start:]
    cond["ALL BARS"] = {"bars": int(allbars.size),
                        "annualised": float(np.expm1(allbars.mean() * ppy))}

    verdict = {}
    for k in SHORTS:
        verdict[k] = {
            "clears_Q1": bool(cells[k]["excess_sharpe"] > 0.0),
            "clears_Q2": nulls[k]["clears_Q2"],
            "clears_Q3": boot[k]["clears_Q3"],
            "clears_best_of": bool(cells[k]["excess_sharpe"] > best_p95),
        }
        verdict[k]["clears_all"] = all(verdict[k][x] for x in
                                       ("clears_Q1", "clears_Q2", "clears_Q3"))
    longs_ok = sum(nulls[k]["clears_Q2"] for k in CELL_ORDER[4:])
    reading = (
        "NEITHER DIRECTION SURVIVES 15-MINUTE SAMPLING. The long controls fail their nulls too, "
        "so this says the estimators break at this horizon and says nothing about the short "
        "side." if longs_ok == 0 else
        "THE LONG CONTROLS HOLD AND THE SHORTS DO NOT -- a direction result, and informative."
        if not any(verdict[k]["clears_all"] for k in SHORTS) else
        "A SHORT CELL CLEARED. Check it against the best-of-four floor before believing it.")

    return {
        "produced": "D247", "stage": "baseline, expected negative",
        "seed": SEED, "n_sims": N_SIMS, "ppy": ppy, "borrow_annual": BORROW_ANNUAL,
        "n_symbols": len(panel.symbols), "bars": int(panel.closes.shape[1]),
        "sessions": n_sessions, "bars_per_session": panel.closes.shape[1] / n_sessions,
        "warmup_bars": start, "live_bars": int(panel.closes.shape[1] - start),
        "live_years": (panel.closes.shape[1] - start) / ppy,
        "first_bar": panel.dates[0], "last_bar": panel.dates[-1],
        "cells": cells, "buy_and_hold": bh, "nulls": nulls, "bootstrap": boot,
        "breakeven_bps": be, "best_of_p95": best_p95, "verdict": verdict,
        "conditional_returns": cond,
        "reading": reading, "elapsed_seconds": round(time.time() - t0, 1),
    }


def render(p: dict) -> str:
    c, n, bt, v, be = p["cells"], p["nulls"], p["bootstrap"], p["verdict"], p["breakeven_bps"]
    bh = p["buy_and_hold"]
    o = ["# D247 — the short side of S1 and S2 at fifteen minutes\n"]
    o.append("**A BASELINE, EXPECTED NEGATIVE.** The long cells are controls, not candidates.\n")
    o.append(
        f"*seed {p['seed']}, {p['n_sims']:,} rotations, {p['elapsed_seconds']}s. "
        f"{p['n_symbols']} ETFs x {p['bars']:,} bars over {p['sessions']:,} sessions "
        f"({p['bars_per_session']:.2f}/session, PPY {p['ppy']:.0f}); warm-up "
        f"{p['warmup_bars']:,} bars = {p['warmup_bars'] / p['bars_per_session']:.0f} sessions, "
        f"live {p['live_years']:.2f} years. {p['first_bar'][:10]} .. {p['last_bar'][:10]}.*\n"
    )
    o.append(
        "**Calendar mismatch, declared before the run:** S1's 34-bar Impulse is **1.3 sessions** "
        "here against seven weeks daily; S2's 252-bar regression is **9.8 sessions** against a "
        "year. These are the same estimators at a radically shorter horizon.\n"
    )
    o.append("## The eight cells\n")
    o.append("| | | long | short | excess Sharpe | CAGR | max DD | turnover/yr | "
             "borrow/yr | E |")
    o.append("|---|---|---:|---:|---:|---:|---:|---:|---:|:--:|")
    for k in CELL_ORDER:
        x = c[k]
        o.append(
            f"| **{k}** | {LABEL[k]} | {x['exposure_long']:.1%} | {x['exposure_short']:.1%} | "
            f"**{x['excess_sharpe']:+.3f}** | {x['cagr'] * 100:+.2f}% | "
            f"{x['max_drawdown'] * 100:+.2f}% | {x['turnover_per_year']:.0f} | "
            f"{x['borrow_paid_annualised'] * 100:.2f}% | "
            f"{'✓' if x['clears_E'] else '✗'} |")
    o.append(f"| *B&H* | *always long* | *100.0%* | *0.0%* | *{bh['excess_sharpe']:+.3f}* | "
             f"*{bh['cagr'] * 100:+.2f}%* | *{bh['max_drawdown'] * 100:+.2f}%* | *0* | *0.00%* | — |")
    o.append("")

    o.append("## Hurdles — the four short cells\n")
    o.append("| | Q1 >0 | Q2 rotation null | pctile | Q3 boot p05 | best-of-4 | **all** |")
    o.append("|---|:--:|:--:|---:|---:|:--:|:--:|")
    for k in SHORTS:
        q = v[k]
        o.append(
            f"| **{k}** | {'✓' if q['clears_Q1'] else '✗'} | "
            f"{'✓' if q['clears_Q2'] else '✗'} | **{n[k]['percentile_of_actual']:.1f}th** | "
            f"{bt[k]['p05']:+.3f} {'✓' if q['clears_Q3'] else '✗'} | "
            f"{'✓' if q['clears_best_of'] else '✗'} | "
            f"**{'✓' if q['clears_all'] else '✗'}** |")
    o.append("")
    o.append(f"*Best-of-four floor (D228, one shared offset vector): "
             f"**{p['best_of_p95']:+.3f}**.*\n")

    o.append("## The long controls — do the estimators survive this horizon at all?\n")
    o.append("| | excess Sharpe | rotation null pctile | clears Q2 |")
    o.append("|---|---:|---:|:--:|")
    for k in CELL_ORDER[4:]:
        o.append(f"| **{k}** | {c[k]['excess_sharpe']:+.3f} | "
                 f"{n[k]['percentile_of_actual']:.1f}th | "
                 f"{'✓' if n[k]['clears_Q2'] else '✗'} |")
    o.append("")

    o.append("## Costs — the predicted verdict\n")
    o.append("| | turnover/yr | **breakeven bp/side** | charged | headroom |")
    o.append("|---|---:|---:|---:|---:|")
    for k in CELL_ORDER:
        b = be[k]
        o.append(f"| **{k}** | {c[k]['turnover_per_year']:.0f} | "
                 f"**{f'{b:.2f}' if b is not None else '—'}** | ~1.6 | "
                 f"{f'{b / 1.6:.2f}x' if b is not None else '—'} |")
    o.append("")
    o.append("*Breakeven below ~1.6 bp means costs alone sink the cell, before any signal "
             "question arises.*\n")

    o.append("## What the shorted bars actually returned\n")
    o.append("*D244's lesson: a null can be beaten or lost by drift structure alone, so this is "
             "measured before any null result is interpreted.*\n")
    o.append("| bars held by | count | annualised return of those bars |")
    o.append("|---|---:|---:|")
    for k, d in p["conditional_returns"].items():
        val = f"**{d['annualised'] * 100:+.2f}%**" if d["annualised"] is not None else "—"
        o.append(f"| {k} | {d['bars']:,} | {val} |")
    o.append("")
    o.append(
        "**This is the finding.** The intraday-only S1 short holds bars returning "
        "**−4.27%/yr** against the continuous version's **+4.72%** — an **8.99-point swing**, "
        "close to the +8.55 predicted from the overnight/intraday decomposition. **It is the "
        "first construction in this programme to isolate bars that actually fall.** It still "
        "loses, because turnover costs five times the gross edge.\n"
    )
    o.append("## The reading\n")
    o.append(f"> **{p['reading']}**\n")
    o.append(
        "\n*The auto-generated line above is too crude and is corrected in "
        "[D247](docs/decisions/D247-the-short-side-at-fifteen-minutes.md): it counts a long "
        "control as \"holding\" if it merely beats its rotation null, and S1's longs do that at "
        "**−0.279** and **−0.586** excess Sharpe. **Seven of eight cells lose money.** The "
        "honest reading is that 15-minute sampling breaks both estimators in both directions.*\n"
    )
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

    c, n, bt, be = (payload["cells"], payload["nulls"], payload["bootstrap"],
                    payload["breakeven_bps"])
    print()
    print(f"{payload['n_symbols']} ETFs x {payload['bars']:,} bars, PPY {payload['ppy']:.0f}, "
          f"live {payload['live_years']:.2f}y")
    print()
    print(f"{'cell':16s} {'long':>6s} {'short':>6s} {'exSh':>8s} {'CAGR':>8s} {'turn':>6s} "
          f"{'brw%':>6s} {'pctile':>8s} {'p05':>8s} {'be bp':>7s}")
    for k in CELL_ORDER:
        x, b = c[k], be[k]
        print(f"{k:16s} {x['exposure_long']:6.1%} {x['exposure_short']:6.1%} "
              f"{x['excess_sharpe']:+8.3f} {x['cagr']:+8.2%} {x['turnover_per_year']:6.0f} "
              f"{x['borrow_paid_annualised']:6.2%} {n[k]['percentile_of_actual']:7.1f}th "
              f"{bt[k]['p05']:+8.3f} {(f'{b:.2f}' if b is not None else '-'):>7s}")
    bh = payload["buy_and_hold"]
    print(f"{'B&H':16s} {1.0:6.1%} {0.0:6.1%} {bh['excess_sharpe']:+8.3f} {bh['cagr']:+8.2%}")
    print(f"\nbest-of-4 floor: {payload['best_of_p95']:+.3f}")
    print("\nbars held, annualised return:")
    for k, d in payload["conditional_returns"].items():
        if d["annualised"] is not None:
            print(f"  {k:16s} {d['annualised']:+8.2%}  ({d['bars']:,} bars)")
    print()
    print(payload["reading"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""D285 -- the factor-neutral book. Pre-registered in `41d29c3`, BEFORE this file.

    uv run python scripts/run_factor_neutral.py --selftest   # synthetic, no cell
    uv run python scripts/run_factor_neutral.py              # the study

Record: `docs/decisions/D285-the-factor-neutral-book.md`.

LONG the N LOWEST lagged `hist_L`, SHORT the N HIGHEST, equal dollars per leg.
Daily bars, close to close, re-ranked each bar. N in {10, 25, 50} per leg.

WHY THE POSITIONS ARE DOLLAR-NEUTRAL BY CONSTRUCTION AND NOT BY NORMALISATION.
Each held name carries +1 or -1, and `RP.pooled_returns` divides the book by the
LIVE NAME COUNT. N names at +1 and N at -1 therefore contribute equal and
opposite dollars with no rescaling step, so there is no place for a sizing bug
to hide. Neutrality is then MEASURED rather than assumed -- hurdle NEU.

THREE THINGS THIS FILE COMPUTES THAT NO PRIOR RUNNER NEEDED
============================================================

1. MOVE PER TRADE IS PER EPISODE, NOT PER BAR. D282 scored an OVERNIGHT book
   where a trade IS a bar, so held name-nights were the right count. This book
   holds a name for a RUN of bars -- D279 measured a mean run of ~9 under these
   exact semantics -- and D265's bar compares the move of a WHOLE TRADE against
   ONE round trip. Counting bars would divide the move by ~9 and compare it to
   the cost of a single round trip, understating the ratio ninefold. Episodes
   are walked per symbol, split on entry, exit AND sign change.

2. THE BREAKEVEN HALF-SPREAD, the statistic that killed D284. Costs enter the
   excess return linearly through a uniform `cost_fraction`, so the fee at which
   net reaches zero is exact rather than a first-order reading.

3. NEUTRALITY AS A MEASUREMENT. The correlation of the book's daily return to
   the EQUAL-WEIGHT UNIVERSE return. A book that claims to have removed `-mu`
   and has not is not testing this hypothesis, and D285 makes that VOID rather
   than negative.

Every constant is D279's and none is varied: 5 bp/side, borrow 3%/yr, rf 4%,
PPY 252, seed 0, 300 null draws, Impulse 34/9.
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


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


B = _load("d256", "run_book_single_names.py")
C = _load("d279", "run_concentrated_short.py")
EP = _load("d279e", "d279_fix_eprime.py")
P1 = _load("d280p1", "d280_forecast_precheck.py")
RP = B.RP

OUT = REPO / "data" / "d285_factor_neutral_summary.json"
N_LEVELS = C.N_LEVELS
N_SIMS, SEED = C.N_SIMS, C.SEED
PPY, RF, BORROW, FEE = C.PPY, C.RF, C.BORROW, C.FEE
TWO_C_BP = 2.0 * FEE                 # 10 bp per name round trip
BREAKEVEN_FLOOR_BPS = 15.0           # hurdle B
NEU_MAX_ABS_CORR = 0.20              # hurdle NEU
PRICE_FLOOR = 5.0                    # universe variant B
HORIZONS = (1, 2, 5, 10, 15)         # the declared persistence diagnostic


def neutral_book(base, score, n, rng=None, tail=False):
    """LONG the N lowest lagged score, SHORT the N highest. +1 / -1 per name.

    `rng` without `tail` is the whole-universe random control: N long and N short
    drawn at random from every qualifying name.

    `tail=True` is THE BINDING CONTROL. The pool is the 2N most extreme names --
    N from each end of the LAGGED score -- and N of them are assigned long and N
    short AT RANDOM. Same count, same volatility tail, random on WHICH tail,
    which is exactly the directional component hurdle C is meant to isolate.
    D283 measured the tail tax at -14.68/-9.80/-6.58 bp against a directional
    +4.75/+4.66/+3.60, so a control drawn from the whole universe is beaten by
    the tax alone -- that is why this one exists."""
    out = np.zeros_like(base)
    s = C.lag1(score)
    for t in range(base.shape[1]):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size == 0:
            continue
        v = s[q, t]
        fin = np.isfinite(v)
        q, v = q[fin], v[fin]
        if q.size < 2 * n:
            continue                       # cannot form two disjoint legs
        order = np.argsort(v, kind="stable")
        if tail:
            pool = q[np.concatenate([order[:n], order[-n:]])]
            perm = rng.permutation(pool)
            lo, hi = perm[:n], perm[n:2 * n]
        elif rng is not None:
            perm = rng.permutation(q)
            lo, hi = perm[:n], perm[n:2 * n]
        else:
            lo, hi = q[order[:n]], q[order[-n:]]
        out[lo, t] = +1.0
        out[hi, t] = -1.0
    return out


def episode_moves(panel, pos, start=0):
    """Signed move of each TRADE, where a trade is a RUN of bars at one sign.

    D265's condition compares the move of a whole trade against ONE round-trip
    cost. This book holds a name for many bars, so counting bars would divide the
    move by the holding run and understate the ratio. Runs are split on entry,
    on exit, and on a SIGN CHANGE -- a name flipping from the long tail to the
    short tail is two trades, not one."""
    p = RP.enforce_live(pos, panel, start)
    simple = np.expm1(panel.total_log_returns)
    moves, runs = [], []
    n, T = p.shape
    for i in range(n):
        row = p[i]
        t = start
        while t < T:
            if row[t] == 0.0:
                t += 1
                continue
            sgn = row[t]
            acc, k = 0.0, 0
            while t < T and row[t] == sgn:
                r = simple[i, t]
                if np.isfinite(r):
                    acc += sgn * r
                k += 1
                t += 1
            moves.append(acc)
            runs.append(k)
    if not moves:
        return None
    m = np.array(moves)
    return {"mean_move_bp": float(m.mean() * 1e4),
            "median_move_bp": float(np.median(m) * 1e4),
            "n_trades": int(m.size),
            "mean_run_bars": float(np.mean(runs)),
            "win_rate": float((m > 0).mean()),
            "share_of_pnl_top_1pct": float(
                np.sort(m)[::-1][:max(1, m.size // 100)].sum() / m.sum())
            if m.sum() != 0 else None}


def breakeven_bps(panel, pos, start=0):
    """The uniform half-spread at which net return reaches zero.

    Exact, not first-order: `cost_fraction` is uniform and enters the excess
    return linearly, so the zero is a ratio rather than a derivative. Same form
    D264 used for `breakeven_bps` and D282 for its overnight book."""
    p = RP.enforce_live(pos, panel, start)
    simple = np.expm1(panel.total_log_returns)
    nlive = np.maximum(panel.live.sum(axis=0), 1).astype(float)
    gross_bar = (p * simple).sum(axis=0) / nlive
    turn_bar = np.abs(np.diff(p, axis=1, prepend=0.0)).sum(axis=0) / nlive
    lf = float((np.maximum(p, 0.0).sum(axis=0) / nlive)[start:].mean())
    sf = float((np.maximum(-p, 0.0).sum(axis=0) / nlive)[start:].mean())
    rf_p = math.expm1(math.log1p(RF) / PPY)
    bor_p = math.expm1(math.log1p(BORROW) / PPY)
    ex_gross = (gross_bar - lf * rf_p - sf * bor_p)[start:]
    turn = float(turn_bar[start:].sum())
    return (1e4 * float(ex_gross.sum()) / turn) if turn > 0 else None


def neutrality(panel, pos, start=0):
    """Correlation of the book's daily return to the EQUAL-WEIGHT universe.

    Hurdle NEU. A book that claims to have removed the market term and has not
    is not testing this hypothesis, which is why D285 makes a failure here VOID
    rather than negative."""
    p = RP.enforce_live(pos, panel, start)
    simple = np.expm1(panel.total_log_returns) * panel.live
    nlive = np.maximum(panel.live.sum(axis=0), 1).astype(float)
    book = ((p * simple).sum(axis=0) / nlive)[start:]
    mkt = (simple.sum(axis=0) / nlive)[start:]
    m = np.isfinite(book) & np.isfinite(mkt)
    if m.sum() < 100 or book[m].std() == 0 or mkt[m].std() == 0:
        return None
    return float(np.corrcoef(book[m], mkt[m])[0, 1])


def persistence(panel, base, score, n, horizons=HORIZONS):
    """The declared diagnostic: does `d` accrue on every bar of a hold?

    For each horizon k, the cross-sectional spread -- mean forward k-bar return
    of the LOW tail minus that of the HIGH tail -- reported PER BAR so the
    horizons are directly comparable. D283 and D284 measured only k = 1."""
    s = C.lag1(score)
    simple = np.expm1(panel.total_log_returns)
    cum = {}
    for k in horizons:
        fwd = np.full_like(simple, np.nan)
        # forward k-bar simple return, within a symbol's own live window
        logs = panel.total_log_returns
        ok = panel.live.copy()
        for j in range(1, k + 1):
            ok[:, :-j] &= panel.live[:, j:]
        acc = np.zeros_like(logs)
        for j in range(1, k + 1):
            acc[:, :-j] += logs[:, j:]
        fwd = np.where(ok, np.expm1(acc), np.nan)
        per_bar = []
        for t in range(base.shape[1]):
            q = np.flatnonzero(base[:, t] != 0.0)
            if q.size < 2 * n:
                continue
            v, f = s[q, t], fwd[q, t]
            good = np.isfinite(v) & np.isfinite(f)
            q2, v2, f2 = q[good], v[good], f[good]
            if q2.size < 2 * n:
                continue
            o = np.argsort(v2, kind="stable")
            per_bar.append(f2[o[:n]].mean() - f2[o[-n:]].mean())
        if len(per_bar) < 30:
            continue
        a = np.array(per_bar)
        cum[k] = {"spread_bp_total": float(a.mean() * 1e4),
                  "spread_bp_per_bar": float(a.mean() * 1e4 / k),
                  "t": float(a.mean() / (a.std(ddof=1) / np.sqrt(a.size))),
                  "bars": int(a.size)}
    return cum


def selftest() -> int:
    print("D285 SELF-TEST -- synthetic, no fixture, no cell scored\n")
    panel, cleaned, amt, _px = _load("d282", "run_overnight_short.py")._synth()
    n, T = panel.closes.shape
    base = np.where(panel.live, 1.0, 0.0)
    base[:, 0] = 0.0
    sc = ((np.arange(n, dtype=float)[:, None] + np.arange(T)[None, :]) % n)

    p = neutral_book(base, sc, 1)
    if not (p.sum(axis=0) == 0).all():
        raise AssertionError("book is not dollar-neutral bar by bar")
    print("  [1] every bar sums to zero: the book is dollar-neutral by construction")
    if not ((p > 0).sum(axis=0) == (p < 0).sum(axis=0)).all():
        raise AssertionError("legs are not count-matched")
    print("  [2] long and short legs are count-matched at every bar")

    # the long leg must be the LOWEST lagged score, the short leg the HIGHEST
    s = C.lag1(sc)
    for t in range(1, T):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size < 2:
            continue
        lo = np.flatnonzero(p[:, t] > 0)
        hi = np.flatnonzero(p[:, t] < 0)
        if lo.size and hi.size and not s[lo, t].max() <= s[hi, t].min():
            raise AssertionError(f"bar {t}: long leg is not below the short leg")
    print("  [3] the long leg sits strictly below the short leg on score[:, t-1]")

    em = episode_moves(panel, p)
    if em is None or em["mean_run_bars"] < 1.0:
        raise AssertionError("episode walker produced no trades")
    print(f"  [4] episode walker: {em['n_trades']} trades, mean run "
          f"{em['mean_run_bars']:.2f} bars -- runs, not bars")

    flat = np.zeros_like(base)
    if breakeven_bps(panel, flat) is not None:
        raise AssertionError("breakeven on a flat book should be undefined")
    print("  [5] breakeven is undefined on a book that never trades")

    rng = np.random.default_rng(0)
    tl = neutral_book(base, sc, 1, rng=rng, tail=True)
    if not (tl.sum(axis=0) == 0).all():
        raise AssertionError("tail control is not dollar-neutral")
    print("  [6] the tail control is dollar-neutral and count-matched too")
    print("\n  ALL SELF-TESTS PASSED. No fixture read, no cell scored.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--sims", type=int, default=N_SIMS)
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=FEE)
    g = P1.build_grids(panel, cleaned)
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    print(f"loaded + signals {time.time() - t0:.0f}s   {len(panel.symbols)} names "
          f"x {len(panel.dates):,} bars", flush=True)

    ok = ~(np.isnan(md) | np.isnan(hs)) & warm & panel.live
    uni = {"A_nofloor": np.where(ok, 1.0, 0.0),
           "B_floor5": np.where(ok & (g["close"] >= PRICE_FLOOR), 1.0, 0.0)}
    for k in uni:
        uni[k][:, 0] = 0.0          # no score[t-1] exists at t=0
        print(f"  universe {k}: {int(uni[k].sum()):,} qualifying name-bars")
    print(flush=True)

    free = type(panel)(**{**vars(panel),
                          "cost_fraction": np.zeros_like(panel.cost_fraction)})
    rng = np.random.default_rng(SEED)
    books = {}
    for uname, bse in uni.items():
        for N in N_LEVELS:
            books[f"{uname}|book{N}"] = neutral_book(bse, hs, N)
            books[f"{uname}|rnd{N}"] = neutral_book(bse, hs, N, rng=rng)
            books[f"{uname}|tal{N}"] = neutral_book(bse, hs, N, rng=rng, tail=True)
    print(f"  built {len(books)} books {time.time() - t0:.0f}s\n", flush=True)

    sc = lambda p, pn: RP.score(pn, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
    cells = {}
    print(f"  HURDLE M -- mean move PER TRADE (an episode, not a bar) against "
          f"2c = {TWO_C_BP:.1f} bp,\n  HURDLE B -- breakeven half-spread against "
          f"{BREAKEVEN_FLOOR_BPS:.0f} bp/side, and HURDLE NEU -- |corr to the "
          f"universe| <= {NEU_MAX_ABS_CORR:.2f}.\n")
    print(f"  {'cell':20s} {'move bp':>9s} {'x2c':>6s} {'run':>6s} {'be bp':>8s} "
          f"{'NEU':>7s} {'trades':>9s} {'win':>6s} {'top1%':>7s}")
    for k, p in books.items():
        s = sc(p, panel)
        em = episode_moves(panel, p) or {}
        s.update({f"episode_{kk}": vv for kk, vv in em.items()})
        s["breakeven_bps"] = breakeven_bps(panel, p)
        s["neutrality_corr"] = neutrality(panel, p)
        s["clears_M"] = bool(em.get("mean_move_bp", -1) >= TWO_C_BP)
        s["clears_B"] = bool(s["breakeven_bps"] is not None
                             and s["breakeven_bps"] >= BREAKEVEN_FLOOR_BPS)
        s["clears_NEU"] = bool(s["neutrality_corr"] is not None
                               and abs(s["neutrality_corr"]) <= NEU_MAX_ABS_CORR)
        cells[k] = s
        print(f"  {k:20s} {em.get('mean_move_bp', float('nan')):+9.2f} "
              f"{em.get('mean_move_bp', float('nan')) / TWO_C_BP:+6.2f} "
              f"{em.get('mean_run_bars', float('nan')):6.2f} "
              f"{(s['breakeven_bps'] if s['breakeven_bps'] is not None else float('nan')):8.2f} "
              f"{(s['neutrality_corr'] if s['neutrality_corr'] is not None else float('nan')):+7.3f} "
              f"{em.get('n_trades', 0):9,d} {em.get('win_rate', float('nan')):6.1%} "
              f"{(em.get('share_of_pnl_top_1pct') or float('nan')):7.1%}", flush=True)

    print(f"\n  {'cell':20s} {'expo':>7s} {'net CAGR':>9s} {'net SR':>8s} "
          f"{'GROSS CAGR':>11s} {'GROSS SR':>9s} {'maxDD':>8s}")
    for k, p in books.items():
        gs = RP.score(free, p, 0, ppy=PPY, rf_annual=0.0, borrow_annual=0.0)
        cells[k]["gross_sharpe"] = gs["excess_sharpe"]
        cells[k]["gross_cagr"] = gs["cagr"]
        cells[k]["gross_total_return"] = gs["total_return"]
        s = cells[k]
        print(f"  {k:20s} {s['exposure_gross']:6.2%} {s['cagr']:+9.2%} "
              f"{s['excess_sharpe']:+8.3f} {gs['cagr']:+10.2%} "
              f"{gs['excess_sharpe']:+9.3f} {s['max_drawdown']:8.2%}", flush=True)

    print(f"\n  THE DECLARED DIAGNOSTIC -- does `d` accrue on every bar of a hold?")
    print(f"  Spread = mean forward return of the LOW tail minus the HIGH tail.\n")
    print(f"  {'universe':>10s} {'N':>4s} {'k':>4s} {'total bp':>10s} "
          f"{'per bar':>9s} {'t':>7s}")
    persist = {}
    for uname, bse in uni.items():
        for N in N_LEVELS:
            pr = persistence(panel, bse, hs, N)
            persist[f"{uname}|N{N}"] = pr
            for kk, v in pr.items():
                print(f"  {uname:>10s} {N:4d} {kk:4d} {v['spread_bp_total']:+10.2f} "
                      f"{v['spread_bp_per_bar']:+9.2f} {v['t']:+7.2f}", flush=True)
            print()

    print(f"  E-prime over the HELD BOOK ...")
    for k, p in books.items():
        e, nk = EP.eff_over_book(panel, p)
        cells[k]["effective_instruments_book"] = e
        cells[k]["names_held_over_min_overlap"] = nk
        cells[k]["Eprime"] = bool(e >= 3.0 and cells[k].get("episode_n_trades", 0) >= 500)
        flag = "  <-- ~= N: identity matrix, E-prime has stopped measuring" \
               if nk and abs(e - nk) < 0.5 else ""
        print(f"    {k:20s} names>=250 held {nk:6d}   E-prime {e:8.2f}{flag}", flush=True)

    print(f"\n  rotation nulls, {a.sims} draws -- REPORTED, NOT DECISIVE "
          f"(R7 corollary, four demonstrations) ...", flush=True)
    draws = []
    for k, p in books.items():
        sh, mn = RP.rotation_null(panel, p, 0, n_sims=a.sims, seed=SEED, ppy=PPY,
                                  rf_annual=RF, borrow_annual=BORROW)
        c = cells[k]
        c["sharpe_pct"] = float((sh < c["excess_sharpe"]).mean() * 100)
        c["money_pct"] = float((mn < c["total_return"]).mean() * 100)
        c["H"] = bool(c["sharpe_pct"] >= 95 and c["money_pct"] >= 95)
        draws.append(sh)
        print(f"    {k:20s} {c['sharpe_pct']:5.1f}th / {c['money_pct']:5.1f}th   "
              f"{time.time() - t0:.0f}s", flush=True)
    floor = float(np.percentile(np.max(np.vstack(draws), axis=0), 95))

    print(f"\n  best-of-{len(books)} floor: {floor:+.3f}")
    print(f"  {'cell':20s} {'move bp':>9s} {'GROSS SR':>9s} {'vs tail':>8s} "
          f"{'M':>3s} {'B':>3s} {'NEU':>4s} {'V':>3s} {'C':>3s} {'F':>3s} {'E':>3s}  ALL")
    surv = []
    for k in books:
        uname, mode = k.split("|")
        c = cells[k]
        if mode.startswith("book"):
            N = mode[4:]
            r, tl = cells[f"{uname}|rnd{N}"], cells[f"{uname}|tal{N}"]
            c["C"] = bool(all(c["excess_sharpe"] > x["excess_sharpe"]
                              and c["total_return"] > x["total_return"]
                              and c["gross_sharpe"] > x["gross_sharpe"]
                              for x in (r, tl)))
            c["vs_tail_gross"] = c["gross_sharpe"] - tl["gross_sharpe"]
            vs = f"{c['vs_tail_gross']:+.3f}"
        else:
            c["C"], vs = False, "—"
        c["V"] = bool(c["cagr"] > 0)
        c["F"] = bool(c["excess_sharpe"] > floor)
        c["clears_all"] = bool(c["clears_M"] and c["clears_B"] and c["clears_NEU"]
                               and c["V"] and c["C"] and c["F"] and c["Eprime"])
        if c["clears_all"]:
            surv.append(k)
        y = lambda b: "YES" if b else "no"  # noqa: E731
        print(f"  {k:20s} {c.get('episode_mean_move_bp', float('nan')):+9.2f} "
              f"{c['gross_sharpe']:+9.3f} {vs:>8s} {y(c['clears_M']):>3s} "
              f"{y(c['clears_B']):>3s} {y(c['clears_NEU']):>4s} {y(c['V']):>3s} "
              f"{y(c['C']):>3s} {y(c['F']):>3s} {y(c['Eprime']):>3s}  "
              f"{'** SURVIVES **' if c['clears_all'] else 'no'}")

    print(f"\n  SURVIVORS: {surv or 'NONE'}")
    json.dump({"study": "D285 the factor-neutral book",
               "preregistration": "docs/decisions/D285-the-factor-neutral-book.md, 41d29c3",
               "two_c_bp": TWO_C_BP, "breakeven_floor_bps": BREAKEVEN_FLOOR_BPS,
               "neu_max_abs_corr": NEU_MAX_ABS_CORR, "price_floor": PRICE_FLOOR,
               "floor": floor, "cells": cells, "persistence": persist,
               "survivors": surv, "elapsed_s": round(time.time() - t0, 1)},
              open(OUT, "w"), indent=1)
    print(f"  wrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

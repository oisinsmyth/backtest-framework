"""D281 -- the unfiltered ranking.
Pre-registered in `docs/decisions/D281-the-unfiltered-ranking.md`, commit
2450af1, BEFORE this file was written.

    uv run python scripts/run_unfiltered_ranking.py

ONE CHANGE FROM D279: rank the WHOLE universe, not the qualifying set.

D256 and D279 both filtered on `hist_L < 0 & md_L >= 0` and then ranked the
survivors by `hist_L` again. **The filter and the ranking are the same
variable**, so the signal is spent by the time the ranking runs.
`data/d280_score_extrapolation.json` measured what that costs -- cross-sectional
Spearman IC, within bar, lagged score against the NEXT bar's return, out of
sample from 2018-01-01:

    hist_L over ALL live names      mean IC -0.00524   t -1.79   2,173 bars
    hist_L over the QUALIFYING set  mean IC +0.00462   t +1.43   2,147 bars

Correctly signed for a short over the whole universe -- the book ranks ASCENDING
so a negative IC is tradeable -- and the WRONG SIGN inside the qualifying set.
This runner removes the collision and changes nothing else. Every constant is
D256's and D279's, unvaried: 5 bp/side, borrow 3%/yr, rf 4%, PPY 252, seed 0,
300 null draws.

THE LAG, AND WHY THIS FILE ASSERTS RATHER THAN TRUSTS
-----------------------------------------------------
D279's first result did not exist. `top_n` ranked with `score[q, t]` -- hist_L
from the close of the very bar the position was about to earn -- and `top25`
scored +2.250 Sharpe unlagged against -0.638 lagged. The fix now lives inside
`top_n`, which calls `lag1` unconditionally. **A fix in a dependency is not a
guarantee in a caller**, so `audit_lag` below re-derives the held set from
`score[:, t-1]` in a second, independent implementation and raises on the first
disagreement. The run aborts rather than reporting a number nobody checked.

TWO CONTROLS, because D279 learned that matched COUNT is not matched TURNOVER
----------------------------------------------------------------------------
  rnd-N  N names redrawn AT RANDOM every bar. Matched count. It churns 5-6x
         harder than a ranked book and pays 5-6x the fees, so on its own it is
         a WEAK control -- it differs from the treatment in two ways.
  per-N  PERSISTENT random: draw at random, then HOLD the draw while the name
         is live, refilling only vacancies. Matched turnover. This is the
         control hurdle C should always have carried. Copied unchanged from
         `scripts/d279_turnover_decomposition.py`.

Every cell is scored NET and GROSS, gross being zero fees, zero borrow, zero rf
on a rebuilt panel. D279 established that this book loses GROSS on this fixture,
so costs are not the binding constraint and **the gross number is the
informative one**.

HURDLE H IS COMPUTED AND CARRIES NO VERDICT. Under R7's corollary D279 showed it
is broken here: `S1_short|all` scored the 100th percentile on both legs with
-0.757 Sharpe and -2.45% CAGR. D281's unfiltered base holds nearly every live
name every bar, where rolling a position inside its own window is close to the
identity. The verdicts rest on V, C and F, with E-prime -- measured OVER THE
HELD BOOK via `d279_fix_eprime.eff_over_book`, never over the panel -- as a
disclosed and near-vacuous side condition.
"""

from __future__ import annotations

import importlib.util
import json
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
TD = _load("d279_turnover", "d279_turnover_decomposition.py")
EP = _load("d279_eprime", "d279_fix_eprime.py")
RP, U = B.RP, B.U

OUT = REPO / "data" / "d281_unfiltered_summary.json"
N_LEVELS = C.N_LEVELS                      # (10, 25, 50), frozen from D279
N_SIMS, SEED = C.N_SIMS, C.SEED            # 300 draws, seed 0
PPY, RF, BORROW, FEE = C.PPY, C.RF, C.BORROW, C.FEE


def audit_lag(base, score, n, pos):
    """R9 correctness gate -- re-derive the held set from `score[:, t-1]`.

    Deliberately a SECOND implementation rather than a call into `top_n`: the
    point is to disagree with it if it is wrong, and a check that shares the
    code it checks cannot. Returns the number of bars verified; raises on the
    first mismatch."""
    if np.any(base[:, 0] != 0.0):
        raise AssertionError("base column 0 is non-zero; hold_book did not lag")
    T = base.shape[1]
    checked = 0
    for t in range(1, T):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size == 0:
            continue
        if q.size <= n:
            want = q
        else:
            s = score[q, t - 1]                      # EXPLICITLY the prior bar
            s = np.where(np.isfinite(s), s, np.inf)
            want = q[np.argsort(s, kind="stable")[:n]]
        got = np.flatnonzero(pos[:, t] != 0.0)
        if got.size != want.size or not np.array_equal(np.sort(got), np.sort(want)):
            raise AssertionError(f"top{n} bar {t}: held set does not match "
                                 f"the rank of score[:, t-1]")
        checked += 1
    return checked


def held_rank_pctile(base, score, pos, shift):
    """Mean cross-sectional percentile of the HELD names in the bar's score.

    `shift=1` scores them on `score[:, t-1]` (what the book may see), `shift=0`
    on `score[:, t]` (the bar it earns). A correctly lagged book sits near the
    bottom of the LAGGED distribution and near the middle of the contemporaneous
    one; the D279 defect inverted exactly that."""
    T = base.shape[1]
    acc = []
    for t in range(1, T):
        q = np.flatnonzero(base[:, t] != 0.0)
        if q.size < 2:
            continue
        h = np.flatnonzero(pos[:, t] != 0.0)
        if h.size == 0:
            continue
        s = score[q, t - shift]
        s = np.where(np.isfinite(s), s, np.inf)
        rank = np.empty(q.size, dtype=float)
        rank[np.argsort(s, kind="stable")] = np.arange(q.size)
        # `q` is sorted, and every held name is in it, so searchsorted maps
        # symbol index -> position in `q` without a per-bar dict.
        acc.append(rank[np.searchsorted(q, h)] / max(q.size - 1, 1))
    return float(np.concatenate(acc).mean()) if acc else float("nan")


def main() -> int:
    t0 = time.time()
    panel, cleaned = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=FEE)
    n, T = panel.closes.shape
    md, hs, g_lo, g_hi, i_lo, atr, warm = B.signals_ragged(panel, cleaned, 0)
    print(f"loaded + signals {time.time() - t0:.0f}s   {n} names x {T:,} bars", flush=True)

    # THE UNFILTERED UNIVERSE. `ok` is D279's mask with BOTH VALUE CONDITIONS
    # REMOVED -- what survives is finiteness and warm-up, so this universe is
    # exactly D279's superset and the only change is that nothing is filtered.
    ok = ~(np.isnan(md) | np.isnan(hs)) & warm
    base = -B.hold_book(ok, warm)
    qual = -B.hold_book((hs < 0) & (md >= 0) & ok, warm)
    print(f"  universe: {int((base != 0).sum()):,} name-bars unfiltered vs "
          f"{int((qual != 0).sum()):,} qualifying "
          f"({(qual != 0).sum() / max((base != 0).sum(), 1):.1%} of it)\n", flush=True)

    rng = np.random.default_rng(SEED)
    books = {"hist_L|all": base}
    for N in N_LEVELS:
        books[f"hist_L|top{N}"] = C.top_n(base, hs, N)
        books[f"hist_L|rnd{N}"] = C.top_n(base, hs, N, rng=rng)
        books[f"hist_L|per{N}"] = TD.persistent_rnd(base, N, rng)
    print(f"built {len(books)} books {time.time() - t0:.0f}s", flush=True)

    # ---- R9 GATE. Nothing downstream runs until the lag is verified. ----
    print("\n  LAG AUDIT -- the check D279 failed:", flush=True)
    r = np.expm1(panel.total_log_returns)
    live = panel.live & np.isfinite(hs) & np.isfinite(C.lag1(hs)) & np.isfinite(r)
    c_now = float(np.corrcoef(hs[live], r[live])[0, 1])
    c_lag = float(np.corrcoef(C.lag1(hs)[live], r[live])[0, 1])
    print(f"    corr(hist_L at t,   return at t) : {c_now:+.4f}   ranking on this is peeking")
    print(f"    corr(hist_L at t-1, return at t) : {c_lag:+.4f}   the tradeable version",
          flush=True)
    audit = {"corr_score_t_return_t": c_now, "corr_score_lag1_return_t": c_lag}
    for N in N_LEVELS:
        p = books[f"hist_L|top{N}"]
        bars = audit_lag(base, hs, N, p)
        pl = held_rank_pctile(base, hs, p, 1)
        pn = held_rank_pctile(base, hs, p, 0)
        audit[f"top{N}"] = {"bars_verified": bars, "mean_pctile_lagged": pl,
                            "mean_pctile_contemporaneous": pn}
        print(f"    top{N:<3d} {bars:,} bars re-derived from score[:, t-1] and MATCHED; "
              f"held names sit at pctile {pl:.4f} of the LAGGED score, "
              f"{pn:.4f} of the contemporaneous one", flush=True)
    print(f"  lag audit passed {time.time() - t0:.0f}s\n", flush=True)

    # ---- NET and GROSS. GROSS zeroes fees, borrow and rf. ----
    free = type(panel)(**{**vars(panel),
                          "cost_fraction": np.zeros_like(panel.cost_fraction)})
    net = {k: RP.score(panel, p, 0, ppy=PPY, rf_annual=RF, borrow_annual=BORROW)
           for k, p in books.items()}
    gro = {k: RP.score(free, p, 0, ppy=PPY, rf_annual=0.0, borrow_annual=0.0)
           for k, p in books.items()}
    print(f"scored {time.time() - t0:.0f}s\n", flush=True)

    print(f"  {'cell':16s} {'expo':>7s} {'turnover':>10s} {'net CAGR':>9s} {'net SR':>8s} "
          f"{'GROSS CAGR':>11s} {'GROSS SR':>9s} {'maxDD':>8s} {'trades':>8s}")
    for k in books:
        a, g = net[k], gro[k]
        print(f"  {k:16s} {a['exposure_gross']:6.2%} {a['turnover_units']:10,.0f} "
              f"{a['cagr']:+8.2%} {a['excess_sharpe']:+8.3f} {g['cagr']:+10.2%} "
              f"{g['excess_sharpe']:+9.3f} {a['max_drawdown']:7.2%} {a['entries']:8,d}",
              flush=True)

    # ---- E-prime OVER THE HELD BOOK, and per-symbol P&L concentration ----
    print(f"\n  E-prime over the HELD BOOK (never the panel) {time.time() - t0:.0f}s ...",
          flush=True)
    eff = {}
    for k, p in books.items():
        e, kept = EP.eff_over_book(panel, p)
        eff[k] = {"eff_book": e, "names_over_min_overlap": kept}
        print(f"    {k:16s} names>=250 held {kept:5d}   E-prime {e:8.2f}   "
              f"{time.time() - t0:.0f}s", flush=True)

    # ---- Rotation nulls. ONE SHARED OFFSET VECTOR: rotation_null reseeds from
    # SEED and walks symbols in panel order, so draw k uses identical offsets in
    # every book and the per-draw max across books is a valid best-of-K. ----
    print(f"\n  rotation nulls, {N_SIMS} draws each -- REPORTED, NOT DECISIVE "
          f"(R7 corollary; see the record) ...", flush=True)
    cells, draws = {}, []
    for k, p in books.items():
        sh, mn = RP.rotation_null(panel, p, 0, n_sims=N_SIMS, seed=SEED, ppy=PPY,
                                  rf_annual=RF, borrow_annual=BORROW)
        c = dict(net[k])
        c["gross"] = gro[k]
        c["sharpe_pct"] = float((sh < net[k]["excess_sharpe"]).mean() * 100)
        c["money_pct"] = float((mn < net[k]["total_return"]).mean() * 100)
        c["null_sharpe_p50"] = float(np.percentile(sh, 50))
        c["null_sharpe_p95"] = float(np.percentile(sh, 95))
        c["H"] = bool(c["sharpe_pct"] >= 95 and c["money_pct"] >= 95)
        c["V"] = bool(c["cagr"] > 0)
        c.update(eff[k])
        c["top_name_share"] = C.per_symbol_concentration(panel, p, 0)
        c["breakeven_borrow"] = C.breakeven_borrow(panel, p, 0, net[k])
        cells[k] = c
        draws.append(sh)
        print(f"    {k:16s} {c['sharpe_pct']:5.1f}th / {c['money_pct']:5.1f}th   "
              f"null p50 {c['null_sharpe_p50']:+.3f} p95 {c['null_sharpe_p95']:+.3f}   "
              f"{time.time() - t0:.0f}s", flush=True)
    floor = float(np.percentile(np.max(np.vstack(draws), axis=0), 95))
    print(f"\n  best-of-{len(books)} floor: {floor:+.3f}\n", flush=True)

    # ---- THE DECOMPOSITION. This is what the study is for. ----
    print("  RANKING CONTRIBUTION -- top-N minus each control, gross and net.")
    print("  D279's FILTERED ranking added +0.203 GROSS over per25. Zero gross "
          "needs +0.635.\n")
    print(f"  {'N':>4s}  {'vs rnd net':>11s} {'vs rnd GROSS':>13s} "
          f"{'vs per net':>11s} {'vs per GROSS':>13s}   turnover ratio")
    decomp = {}
    for N in N_LEVELS:
        t, rd, pe = (net[f"hist_L|{m}{N}"] for m in ("top", "rnd", "per"))
        tg, rg, pg = (gro[f"hist_L|{m}{N}"] for m in ("top", "rnd", "per"))
        d = {"vs_rnd_net": t["excess_sharpe"] - rd["excess_sharpe"],
             "vs_rnd_gross": tg["excess_sharpe"] - rg["excess_sharpe"],
             "vs_per_net": t["excess_sharpe"] - pe["excess_sharpe"],
             "vs_per_gross": tg["excess_sharpe"] - pg["excess_sharpe"],
             "vs_rnd_money_net": t["total_return"] - rd["total_return"],
             "vs_rnd_money_gross": tg["total_return"] - rg["total_return"],
             "vs_per_money_net": t["total_return"] - pe["total_return"],
             "vs_per_money_gross": tg["total_return"] - pg["total_return"],
             "turnover_ratio_rnd": rd["turnover_units"] / t["turnover_units"],
             "turnover_ratio_per": pe["turnover_units"] / t["turnover_units"]}
        decomp[str(N)] = d
        print(f"  {N:4d}  {d['vs_rnd_net']:+11.3f} {d['vs_rnd_gross']:+13.3f} "
              f"{d['vs_per_net']:+11.3f} {d['vs_per_gross']:+13.3f}   "
              f"rnd {d['turnover_ratio_rnd']:.1f}x per {d['turnover_ratio_per']:.1f}x")

    # ---- Hurdles. C requires BOTH controls, on Sharpe AND money, GROSS AND NET. ----
    print(f"\n  {'cell':16s} {'net CAGR':>9s} {'net SR':>8s} {'GROSS SR':>9s} "
          f"{'V':>3s} {'C':>3s} {'F':>3s} {'E-prime':>8s} {'(H)':>5s}  ALL")
    surv = []
    for k in books:
        c = cells[k]
        mode = k.split("|")[1]
        if mode.startswith("top"):
            N = mode[3:]
            legs = []
            for m in ("rnd", "per"):
                o, og = cells[f"hist_L|{m}{N}"], gro[f"hist_L|{m}{N}"]
                legs += [c["excess_sharpe"] > o["excess_sharpe"],
                         c["total_return"] > o["total_return"],
                         gro[k]["excess_sharpe"] > og["excess_sharpe"],
                         gro[k]["total_return"] > og["total_return"]]
            c["C"] = bool(all(legs))
            c["C_legs"] = [bool(x) for x in legs]
        else:
            c["C"] = False
            c["C_legs"] = []
        c["F"] = bool(c["excess_sharpe"] > floor)
        c["Eprime"] = bool(c["eff_book"] >= 3.0 and c["entries"] >= 500)
        # H IS EXCLUDED FROM `clears_all` BY PRE-REGISTRATION. It is computed and
        # printed; it carries no verdict. R7's corollary, established by D279.
        c["clears_all"] = bool(c["V"] and c["C"] and c["F"] and c["Eprime"])
        if c["clears_all"]:
            surv.append(k)
        y = lambda b: "YES" if b else "no"  # noqa: E731
        print(f"  {k:16s} {c['cagr']:+8.2%} {c['excess_sharpe']:+8.3f} "
              f"{gro[k]['excess_sharpe']:+9.3f} {y(c['V']):>3s} {y(c['C']):>3s} "
              f"{y(c['F']):>3s} {y(c['Eprime']):>8s} {y(c['H']):>5s}  "
              f"{'** YES **' if c['clears_all'] else 'no'}")

    print(f"\n  SURVIVORS: {surv or 'NONE'}")
    json.dump({"study": "D281", "seed": SEED, "n_sims": N_SIMS, "fee_bps": FEE,
               "borrow_charged": BORROW, "rf": RF, "ppy": PPY,
               "n_levels": list(N_LEVELS), "floor": floor, "K": len(books),
               "hurdle_H": "computed, reported, EXCLUDED from every verdict (R7 corollary)",
               "lag_audit": audit, "decomposition": decomp,
               "cells": cells, "survivors": surv,
               "elapsed_s": round(time.time() - t0, 1)},
              open(OUT, "w"), indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}   {time.time() - t0:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

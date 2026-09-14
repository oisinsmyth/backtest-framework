"""D528 -- the MEAN-REVERSION ORACLE. Does a rare excursion return to its level more reliably
than the same moves in random order?

    python scripts/d528_mean_reversion_oracle.py --self-test
    python scripts/d528_mean_reversion_oracle.py --profile
    python scripts/d528_mean_reversion_oracle.py --run

Spec: docs/decisions/D528-the-mean-reversion-oracle-...md, committed 98bf297 BEFORE this file.

A LABEL, NOT A TRADE. No P&L, no cost, no position (R15).

PRIMARY (R14, one): P(return to level within N s-bars | excursion >= 2.0 sigma) MINUS the same
under the window's own sign shuffle, at s=5, x=2.0 sigma, tau=N, phase 0, pooled over roots.

TWO ARITHMETIC CORRECTIONS TO THE SPEC'S LADDER, found while building and recorded rather than
quietly applied:

  1. s=21 IS INFEASIBLE. N bar-returns need N+1 PRICE POINTS, and 420/21 = 20 points gives only
     19 returns -- one short. s_max = 420 // (N+1) = 20, so the ladder's top step becomes 20
     minutes, where 420/20 = 21 points is exactly N+1.
  2. SS11's SPLIT TEST IS REALISED BY THE x LADDER, NOT THE k LADDER. The conditional return
     probability depends on the EXCURSION threshold x, not on the envelope radius k -- k sets the
     range W and the traverse measures only. So "is the envelope the entry, or is the entry
     deeper?" is answered by the SHAPE of the primary across x, which is also SS10's P3. Both
     ladders are still computed; the claim is just attached to the right one.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
FIX = REPO / "data" / "fixtures" / "fut_day1m_mid.parquet"
BMETA = REPO / "data" / "fixtures" / "fut_breadth_hourly.meta.json"
OUT = REPO / "data" / "d528_mean_reversion_oracle.json"

N = 20                                  # s-bars per window
SCALES = (1, 2, 3, 5, 8, 13, 20)        # minutes per bar; 21 infeasible (see docstring)
N_PHASES = 4
K_ENV = (1.5, 2.0, 2.5, 3.0)            # envelope radii, in residual sigma
X_EXC = (1.0, 1.5, 2.0, 2.5, 3.0)       # excursion thresholds, in residual sigma
TAUS = (5, 10, 20, 40)                  # 0.25N, 0.5N, N, 2N
EXT_MULT = 1.5                          # an excursion "extends" at (1 + 0.5) * x
N_SHUF = 200
MIN_TICKS = 4                           # A2: lattice filter, per window
DAY_LO, DAY_HI = 540, 959
IS_END = "2026-04-10"                   # 2026-04-11 onward is RESERVED and NOT READ
SEED = 528
PRIMARY = {"s": 5, "x": 2.0, "tau": 20, "phase": 0}
BIG = 1 << 30


class GateError(RuntimeError):
    pass


def P(*a):
    print(*a, flush=True)


# ---------------------------------------------------------------------------------------------
# the level, the envelope, and the outcomes
# ---------------------------------------------------------------------------------------------
def detrend_ext(Pm: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Linear detrend fitted on the FIRST N+1 rows and EXTRAPOLATED over all T.

    Pm is (T, M) prices. The line continues past the window because the return is measured past
    the window's end -- an excursion at bar N-2 is not a failure because the window stopped, and
    the oracle is entitled to look there. Returns (residual, slope, sigma)."""
    T = Pm.shape[0]
    t = np.arange(T, dtype=np.float64)
    tw = t[:N + 1]
    twc = tw - tw.mean()
    den = (twc * twc).sum()
    W = Pm[:N + 1]
    mu = W.mean(0)
    b = (twc[:, None] * (W - mu)).sum(0) / den
    a = mu - b * tw.mean()
    y = Pm - (a[None, :] + b[None, :] * t[:, None])
    sig = y[:N + 1].std(0, ddof=1)
    return y, b, sig


def _next_true(C: np.ndarray) -> np.ndarray:
    """nxt[j, m] = smallest j' >= j with C[j', m], else BIG. One reverse accumulate."""
    T = C.shape[0]
    idx = np.arange(T, dtype=np.int64)[:, None]
    w = np.where(C, idx, BIG)
    return np.minimum.accumulate(w[::-1], axis=0)[::-1]


def outcomes(y: np.ndarray, sig: np.ndarray, valid: np.ndarray, x: float,
             tol: np.ndarray) -> dict:
    """Three-way outcome for every EXCURSION RUN, at every tau. y is (T, M).

    An excursion is the FIRST bar of a run beyond +/- x*sigma inside the window. It RETURNS when
    the residual reaches the level within one tick (`tol`), EXTENDS when it reaches
    EXT_MULT * x * sigma further out on the same side, and is NEITHER if it does not do either by
    tau. No stop is defined -- a stop is a trading choice, not part of a label."""
    T, M = y.shape
    thr = (x * sig)[None, :]
    up = (y >= thr) & valid
    dn = (y <= -thr) & valid
    inwin = np.zeros((T, 1), bool)
    inwin[:N + 1] = True
    up_w, dn_w = up & inwin, dn & inwin
    # first bar of each run
    up_start = up_w & ~np.vstack([np.zeros((1, M), bool), up_w[:-1]])
    dn_start = dn_w & ~np.vstack([np.zeros((1, M), bool), dn_w[:-1]])

    # returning to the level: cross or touch within one tick, on the opposite side of the entry
    ret_from_up = _next_true((y <= tol[None, :]) & valid)
    ret_from_dn = _next_true((y >= -tol[None, :]) & valid)
    ext_from_up = _next_true((y >= EXT_MULT * thr) & valid)
    ext_from_dn = _next_true((y <= -EXT_MULT * thr) & valid)

    res = {}
    for side, start, ret, ext in (("up", up_start, ret_from_up, ext_from_up),
                                  ("dn", dn_start, ret_from_dn, ext_from_dn)):
        ii, mm = np.nonzero(start)
        if len(ii) == 0:
            res[side] = (np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros(0, np.int64))
            continue
        nx = np.minimum(ii + 1, T - 1)
        res[side] = (mm, ret[nx, mm] - ii, ext[nx, mm] - ii)
    cols = np.concatenate([res["up"][0], res["dn"][0]])
    dret = np.concatenate([res["up"][1], res["dn"][1]])
    dext = np.concatenate([res["up"][2], res["dn"][2]])
    return {"col": cols, "d_ret": dret, "d_ext": dext}


def tally(o: dict, M: int) -> np.ndarray:
    """(len(TAUS), 3) counts of returned / extended / neither, pooled over excursions."""
    out = np.zeros((len(TAUS), 3), np.int64)
    dr, de = o["d_ret"], o["d_ext"]
    for i, tau in enumerate(TAUS):
        r = dr <= tau
        e = (~r) & (de <= tau)
        out[i, 0] = int(r.sum())
        out[i, 1] = int(e.sum())
        out[i, 2] = int(len(dr) - r.sum() - e.sum())
    return out


def crossings(y: np.ndarray) -> np.ndarray:
    """Level crossings inside the window, per column. Sign-sensitive, unlike any variance."""
    s = np.sign(y[:N + 1])
    s = np.where(s == 0, np.nan, s)
    d = np.diff(s, axis=0)
    return np.nansum(np.abs(d) > 1.5, axis=0).astype(np.int64)


def traverses(y: np.ndarray, sig: np.ndarray, k: float, tol: np.ndarray) -> np.ndarray:
    """(edge->level, level->edge, edge->edge) completions inside the window, per column."""
    T, M = y.shape
    thr = (k * sig)[None, :]
    inw = np.zeros((T, 1), bool)
    inw[:N + 1] = True
    at_up = (y >= thr) & inw
    at_dn = (y <= -thr) & inw
    at_lv = (np.abs(y) <= tol[None, :]) & inw
    nx_up, nx_dn, nx_lv = _next_true(at_up), _next_true(at_dn), _next_true(at_lv)
    # VECTORISED over windows. The first version looped over M, which is ~2,900 per root at
    # s=1 and would have been ~8M interpreter iterations across the full grid.
    cols = np.arange(M)
    e_up, e_dn, l0 = nx_up[0], nx_dn[0], nx_lv[0]
    e = np.minimum(e_up, e_dn)
    has_e, has_l = e < BIG, l0 < BIG
    ie = np.minimum(e + 1, T - 1)
    il = np.minimum(l0 + 1, T - 1)
    edge_to_level = (nx_lv[ie, cols] < BIG) & has_e
    opp = np.where(e_up <= e_dn, nx_dn[ie, cols], nx_up[ie, cols])
    edge_to_edge = (opp < BIG) & has_e
    level_to_edge = (np.minimum(nx_up[il, cols], nx_dn[il, cols]) < BIG) & has_l
    return np.vstack([edge_to_level, level_to_edge, edge_to_edge]).astype(np.int64)


# ---------------------------------------------------------------------------------------------
# window admission
# ---------------------------------------------------------------------------------------------
def admit(Pm: np.ndarray, tick: float) -> tuple[np.ndarray, dict]:
    """A1 stability (split-half level and range agreement) and A2 lattice, both PER WINDOW."""
    W = Pm[:N + 1]
    h = (N + 1) // 2
    out = {}
    stab = np.ones(Pm.shape[1], bool)
    sl, sg = [], []
    for part in (W[:h], W[h:]):
        n = part.shape[0]
        t = np.arange(n, dtype=np.float64)
        tc = t - t.mean()
        b = (tc[:, None] * (part - part.mean(0))).sum(0) / (tc * tc).sum()
        r = part - (part.mean(0) + b[None, :] * tc[:, None])
        sl.append(b)
        sg.append(r.std(0, ddof=1))
    sig_pool = np.sqrt(0.5 * (sg[0] ** 2 + sg[1] ** 2))
    with np.errstate(invalid="ignore", divide="ignore"):
        slope_ok = np.abs(sl[0] - sl[1]) * (N / 2) <= 0.5 * sig_pool
        ratio = np.where(sg[1] > 0, sg[0] / sg[1], np.inf)
        sig_ok = (ratio >= 0.5) & (ratio <= 2.0)
    stab = slope_ok & sig_ok & (sig_pool > 0)
    med_ticks = np.median(np.abs(np.diff(W, axis=0)), axis=0) / tick
    latt = med_ticks >= MIN_TICKS
    out["n"] = int(Pm.shape[1])
    out["stable"] = int(stab.sum())
    out["lattice"] = int(latt.sum())
    out["admitted"] = int((stab & latt).sum())
    out["median_ticks"] = float(np.median(med_ticks))
    return stab & latt, out


# ---------------------------------------------------------------------------------------------
def session_bars(g: pd.DataFrame, s: int) -> list:
    """Per session, the s-minute PRICE PATH (price sampled every s minutes), contiguous only."""
    bar = g["bar"].to_numpy()
    mid = g["mid"].to_numpy(np.float64)
    day = g["day"].to_numpy()
    cut = np.flatnonzero(day[1:] != day[:-1]) + 1
    segs = list(zip(np.concatenate(([0], cut)), np.concatenate((cut, [len(g)]))))
    out = []
    npts = (DAY_HI - DAY_LO + 1) // s
    want = np.arange(npts, dtype=np.int64) * s
    for a, b in segs:
        bb, mm = bar[a:b], mid[a:b]
        full = np.full(DAY_HI - DAY_LO + 1, np.nan)
        full[bb] = mm
        pth = full[want]
        if np.isfinite(pth).sum() < npts:      # a gap anywhere disqualifies the session
            continue
        out.append((day[a], pth))
    return out


def windows_of(paths: list, phase: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Tiled windows at the given phase, EXTENDED to 2N past the window, capped at session end.

    Returns (Pm of shape (T, M), valid mask, session index per window)."""
    T = N + 1 + max(TAUS)
    off = (phase * N) // N_PHASES
    cols, vals, sid = [], [], []
    for si, (day, pth) in enumerate(paths):
        npts = len(pth)
        j0 = off
        while j0 + N < npts:
            hi = min(j0 + T, npts)
            c = np.full(T, np.nan)
            c[:hi - j0] = pth[j0:hi]
            cols.append(c)
            v = np.zeros(T, bool)
            v[:hi - j0] = True
            vals.append(v)
            sid.append(si)
            j0 += N
    if not cols:
        return np.zeros((T, 0)), np.zeros((T, 0), bool), np.zeros(0, np.int64)
    return (np.column_stack(cols), np.column_stack(vals), np.array(sid, np.int64))


def specs() -> dict:
    m = json.loads(BMETA.read_text(encoding="utf-8"))
    return m["specs"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--profile", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--roots", type=str, default=None)
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if a.profile:
        return profile()
    if a.run:
        return run(a.roots.split(",") if a.roots else None)
    ap.print_help()
    return 1


# ---------------------------------------------------------------------------------------------
def load() -> pd.DataFrame:
    if not FIX.exists():
        raise GateError(f"[FIX] {FIX.name} absent -- run build_fut_day1m_mid.py")
    d = pd.read_parquet(FIX, columns=["root", "day", "bar", "mid", "present", "same_front"])
    d = d[d["present"]]
    d = d[d["same_front"]]
    d = d[d["day"] <= IS_END]
    if len(d) and str(d["day"].max()) > IS_END:
        raise GateError("[HOLDOUT] the reserved slice was loaded")
    return d.sort_values(["root", "day", "bar"], kind="stable").reset_index(drop=True)


def one_cell(Pm, valid, tick, rng, n_shuf):
    """Observed and null tallies for one (root, scale, phase) window batch."""
    keep, adm = admit(Pm, tick)
    Pm, valid = Pm[:, keep], valid[:, keep]
    M = Pm.shape[1]
    if M == 0:
        return None, adm
    y, b, sig = detrend_ext(Pm)
    tol = np.full(M, tick)
    obs = {"cross": crossings(y), "sigma": sig, "slope": b,
           "W": {}, "trav": {}, "cond": {}}
    for k in K_ENV:
        obs["W"][k] = 2.0 * k * sig / tick                 # range width in TICKS
        obs["trav"][k] = traverses(y, sig, k, tol)
    for x in X_EXC:
        obs["cond"][x] = tally(outcomes(y, sig, valid, x, tol), M)

    # ---- the null: sign shuffle of the window's own returns, EXTENDED segment included -------
    r = np.diff(Pm, axis=0)
    nullc = np.zeros(n_shuf, np.int64)
    ncond = {x: np.zeros((len(TAUS), 3), np.int64) for x in X_EXC}
    step = max(1, 4_000_000 // (Pm.shape[0] * max(M, 1)))
    done = 0
    while done < n_shuf:
        B = min(step, n_shuf - done)
        sgn = np.where(rng.integers(0, 2, (r.shape[0], M, B)) == 1, 1.0, -1.0)
        rr = (np.abs(r)[:, :, None] * sgn)
        Pn = np.concatenate([np.zeros((1, M, B)), np.nancumsum(rr, axis=0)], axis=0) \
            + Pm[0][None, :, None]
        Pn = Pn.reshape(Pm.shape[0], M * B)
        vv = np.repeat(valid, B, axis=1)
        yn, bn, sgn2 = detrend_ext(Pn)
        nullc[done:done + B] = crossings(yn).reshape(M, B).sum(0)
        tn = np.repeat(tol, B)
        for x in X_EXC:
            ncond[x] += tally(outcomes(yn, sgn2, vv, x, tn), M * B) // 1
        done += B
    return {"obs": obs, "null_cross": nullc, "null_cond": ncond,
            "M": M, "n_shuf": n_shuf}, adm


def profile() -> int:
    d = load()
    sp = specs()
    rng = np.random.default_rng(SEED)
    P("  profiling ONE root before the fan-out (measure the worker, then decide)")
    g = d[d["root"] == "NQ"]
    tick = sp["NQ"]["tick_price_units"]
    for s in (5, 1):
        t0 = time.time()
        paths = session_bars(g, s)
        Pm, valid, sid = windows_of(paths, 0)
        t1 = time.time()
        res, adm = one_cell(Pm, valid, tick, rng, 20)
        t2 = time.time()
        full = (t2 - t1) * (N_SHUF / 20)
        P(f"    NQ s={s:<3} {len(paths):>4} sessions, {Pm.shape[1]:>6,} windows, "
          f"{adm['admitted']:>6,} admitted ({adm['admitted']/max(adm['n'],1):.0%})  "
          f"build {t1-t0:4.1f}s  20 shuf {t2-t1:5.1f}s  -> {N_SHUF} shuf {full:6.1f}s")
    P("\n    full grid is 26 roots x 7 scales x 4 phases; s=1 dominates.")
    return 0


def run(only=None) -> int:
    t_start = time.time()
    rng = np.random.default_rng(SEED)
    d = load()
    sp = specs()
    roots = sorted(set(d["root"]) & set(sp)) if only is None else only
    P("D528 -- the mean-reversion oracle")
    P(f"  fixture {FIX.name}, {len(d):,} rows, {d['day'].min()} .. {d['day'].max()}")
    P(f"  {len(roots)} roots, scales {SCALES}, N={N}, {N_PHASES} phases, {N_SHUF} shuffles")
    P(f"  RESERVED AND NOT READ: after {IS_END}")
    res = {"spec": "D528 pre-reg 98bf297", "primary_cell": PRIMARY,
           "scales": list(SCALES), "N": N, "phases": N_PHASES, "n_shuf": N_SHUF,
           "k_env": list(K_ENV), "x_exc": list(X_EXC), "taus": list(TAUS),
           "window": [str(d["day"].min()), str(d["day"].max())],
           "ladder_note": "s=21 is infeasible: N bar-returns need N+1 price points and "
                          "420/21 = 20 points gives 19. Top step is 20 minutes.",
           "cells": {}}
    for s in SCALES:
        for ph in range(N_PHASES):
            key = f"s{s}_p{ph}"
            agg = {"admitted": 0, "n_windows": 0, "cross_obs": 0, "cross_null": 0.0,
                   "cond": {str(x): np.zeros((len(TAUS), 3), np.int64) for x in X_EXC},
                   "cond_null": {str(x): np.zeros((len(TAUS), 3), np.int64) for x in X_EXC},
                   "per_root": {}}
            for r in roots:
                g = d[d["root"] == r]
                if len(g) == 0:
                    continue
                tick = sp[r]["tick_price_units"]
                paths = session_bars(g, s)
                if not paths:
                    continue
                Pm, valid, sid = windows_of(paths, ph)
                if Pm.shape[1] == 0:
                    continue
                cell, adm = one_cell(Pm, valid, tick, rng, N_SHUF)
                if cell is None:
                    continue
                agg["admitted"] += adm["admitted"]
                agg["n_windows"] += adm["n"]
                agg["cross_obs"] += int(cell["obs"]["cross"].sum())
                agg["cross_null"] += float(cell["null_cross"].mean())
                pr = {"admitted": adm["admitted"], "n": adm["n"],
                      "median_ticks": adm["median_ticks"]}
                for x in X_EXC:
                    agg["cond"][str(x)] += cell["obs"]["cond"][x]
                    agg["cond_null"][str(x)] += cell["null_cond"][x]
                    tot = cell["obs"]["cond"][x][2, :].sum()
                    if x == PRIMARY["x"]:
                        o = cell["obs"]["cond"][x]
                        nn = cell["null_cond"][x]
                        i = TAUS.index(PRIMARY["tau"])
                        po = o[i, 0] / max(o[i].sum(), 1)
                        pn = nn[i, 0] / max(nn[i].sum(), 1)
                        pr["p_obs"], pr["p_null"] = float(po), float(pn)
                        pr["excess"] = float(po - pn)
                        pr["n_exc"] = int(o[i].sum())
                agg["per_root"][r] = pr
            for x in X_EXC:
                agg["cond"][str(x)] = agg["cond"][str(x)].tolist()
                agg["cond_null"][str(x)] = agg["cond_null"][str(x)].tolist()
            res["cells"][key] = agg
            i = TAUS.index(PRIMARY["tau"])
            o = np.array(agg["cond"][str(PRIMARY["x"])])[i]
            nn = np.array(agg["cond_null"][str(PRIMARY["x"])])[i]
            po = o[0] / max(o.sum(), 1)
            pn = nn[0] / max(nn.sum(), 1)
            P(f"  s={s:<3} phase {ph}  admitted {agg['admitted']:>7,}/{agg['n_windows']:>7,}"
              f"  exc {o.sum():>7,}  P(ret) obs {po:.4f} null {pn:.4f}"
              f"  EXCESS {po-pn:+.4f}   [{time.time()-t_start:.0f}s]")
    OUT.write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    P(f"\n  wrote {OUT.relative_to(REPO)} in {(time.time()-t_start)/60:.1f} min")
    return 0


def self_test() -> int:
    fails = []
    rng = np.random.default_rng(1)

    def chk(name, ok, note=""):
        P(f"    [{'PASS' if ok else 'FAIL'}] {name:<68} {note}")
        if not ok:
            fails.append(name)

    T = N + 1 + max(TAUS)
    # 1 -- detrend: a straight line leaves zero residual
    t = np.arange(T, dtype=np.float64)
    Pm = (3.0 + 0.7 * t)[:, None]
    y, b, sig = detrend_ext(Pm)
    chk("detrend: a straight line leaves a zero residual and recovers the slope",
        abs(b[0] - 0.7) < 1e-10 and np.abs(y).max() < 1e-9 and sig[0] < 1e-9)
    # and it EXTRAPOLATES: the residual past the window is also zero
    chk("[X] the line is EXTRAPOLATED past the window, so the tail residual is zero too",
        np.abs(y[N + 1:]).max() < 1e-9)

    # 2 -- envelope in sigma can sit OUTSIDE the sample, a quantile cannot
    r = rng.normal(size=(N, 400))
    Pq = np.vstack([np.zeros((1, 400)), r.cumsum(0)])
    yq, _, sq = detrend_ext(np.vstack([Pq, np.zeros((T - N - 1, 400))]))
    out3 = (3.0 * sq > np.abs(yq[:N + 1]).max(0))
    chk("a +/-3sigma envelope lies OUTSIDE the observed residual range on some windows",
        out3.mean() > 0.2, f"{out3.mean():.0%} of windows")
    q98 = np.percentile(np.abs(yq[:N + 1]), 98, axis=0)
    chk("[X] a q98 envelope NEVER exceeds the observed range -- why quantiles were rejected",
        bool((q98 <= np.abs(yq[:N + 1]).max(0) + 1e-12).all()))

    # 3 -- the return is measured PAST the window end
    p = np.zeros(T)
    p[:N + 1] = np.linspace(0, 0, N + 1)
    p[N - 1] = 3.0
    p[N] = 3.0
    p[N + 1:N + 6] = 0.0
    Pm = p[:, None]
    valid = np.ones((T, 1), bool)
    y, b, sig = detrend_ext(Pm)
    o = outcomes(y, sig, valid, 1.0, np.full(1, 1e-9))
    past = (len(o["d_ret"]) > 0) and (o["d_ret"].min() > 0)
    chk("an excursion near the window end can still RETURN, using bars past the window",
        past, f"d_ret {o['d_ret'][:3] if len(o['d_ret']) else 'none'}")
    vtrunc = np.zeros((T, 1), bool)
    vtrunc[:N + 1] = True
    o2 = outcomes(y, sig, vtrunc, 1.0, np.full(1, 1e-9))
    t_i = TAUS.index(20)
    chk("[X] truncating at the window boundary LOWERS the short-horizon return count",
        tally(o2, 1)[t_i, 0] <= tally(o, 1)[t_i, 0],
        f"truncated {tally(o2,1)[t_i,0]} vs extended {tally(o,1)[t_i,0]}")

    # 4 -- the three-way outcome is exhaustive and exclusive
    rr = rng.normal(size=(T - 1, 60))
    PP = np.vstack([np.zeros((1, 60)), rr.cumsum(0)])
    yy, _, ss = detrend_ext(PP)
    vv = np.ones((T, 60), bool)
    oo = outcomes(yy, ss, vv, 1.5, np.full(60, 1e-9))
    tt = tally(oo, 60)
    chk("the three-way outcome is exhaustive and exclusive at every tau",
        bool((tt.sum(1) == len(oo["d_ret"])).all()), f"{len(oo['d_ret'])} excursions")

    # 5 -- crossings are sign-sensitive where a variance ratio is not
    lam = np.concatenate([np.full(N // 2, 1.0), np.full(N - N // 2, -1.0)])
    Pl = np.concatenate([[0.0], lam.cumsum()])
    Pl = np.concatenate([Pl, np.full(T - len(Pl), Pl[-1])])[:, None]
    chop = np.tile(np.array([1.0, -1.0]), N // 2)
    Pc = np.concatenate([[0.0], chop.cumsum()])
    Pc = np.concatenate([Pc, np.full(T - len(Pc), Pc[-1])])[:, None]
    yl, _, _ = detrend_ext(Pl)
    yc, _, _ = detrend_ext(Pc)
    chk("crossings separate a Lambda (few) from fast chop (many)",
        crossings(yl)[0] < crossings(yc)[0],
        f"Lambda {crossings(yl)[0]} vs chop {crossings(yc)[0]}")

    # 5b -- [OPT] the vectorised traverses equal a reference loop EXACTLY
    rt = rng.normal(size=(T - 1, 120))
    Pt = np.vstack([np.zeros((1, 120)), rt.cumsum(0)])
    yt, _, st = detrend_ext(Pt)
    tolt = np.full(120, 1e-9)
    fast = traverses(yt, st, 2.0, tolt)
    ref = np.zeros((3, 120), np.int64)
    thr = (2.0 * st)[None, :]
    inw = np.zeros((T, 1), bool)
    inw[:N + 1] = True
    nu, nd, nl = (_next_true((yt >= thr) & inw), _next_true((yt <= -thr) & inw),
                  _next_true((np.abs(yt) <= tolt[None, :]) & inw))
    for m in range(120):
        e = min(nu[0, m], nd[0, m])
        if e < BIG:
            ref[0, m] = int(nl[min(e + 1, T - 1), m] < BIG)
            opp = nd if nu[0, m] <= nd[0, m] else nu
            ref[2, m] = int(opp[min(e + 1, T - 1), m] < BIG)
        if nl[0, m] < BIG:
            j = min(nl[0, m] + 1, T - 1)
            ref[1, m] = int(min(nu[j, m], nd[j, m]) < BIG)
    chk("[OPT] vectorised traverses equal the reference loop EXACTLY",
        np.array_equal(fast, ref), f"{ref.sum()} completions over 120 windows")

    # 6 -- A1 stability fires on a vol regime change, admits a constant one
    base = rng.normal(size=(N, 2000))
    Pst = np.vstack([np.zeros((1, 2000)), base.cumsum(0)])
    Pst = np.vstack([Pst, np.zeros((T - N - 1, 2000))])
    kk, ad = admit(Pst, 1e-6)
    half = N // 2
    b2 = base.copy()
    b2[half:] *= 8.0
    Pch = np.vstack([np.zeros((1, 2000)), b2.cumsum(0)])
    Pch = np.vstack([Pch, np.zeros((T - N - 1, 2000))])
    kk2, ad2 = admit(Pch, 1e-6)
    chk("[X] A1 rejects far more windows when the volatility regime changes mid-window",
        ad2["stable"] < ad["stable"] * 0.7,
        f"constant {ad['stable']/2000:.0%} vs regime-change {ad2['stable']/2000:.0%}")

    # 7 -- A2 is per window
    scale = np.repeat(np.array([0.5, 8.0]), 1000)
    Pa = np.vstack([np.zeros((1, 2000)), (base * scale).cumsum(0)])
    Pa = np.vstack([Pa, np.zeros((T - N - 1, 2000))])
    _, ada = admit(Pa, 1.0)
    chk("A2 is PER WINDOW: a mixed population keeps the coarse half and drops the fine half",
        0.2 < ada["lattice"] / 2000 < 0.8, f"{ada['lattice']/2000:.0%} pass the lattice filter")

    # 8 -- the sign shuffle preserves prefix sum|r| exactly, so admission is identical
    rx = rng.normal(size=(N, 50))
    sg = np.where(rng.integers(0, 2, (N, 50)) == 1, 1.0, -1.0)
    chk("the sign shuffle preserves prefix sum|r| EXACTLY, so A2 is identical under the null",
        np.array_equal(np.abs(rx).cumsum(0), np.abs(np.abs(rx) * sg).cumsum(0)))

    # 9 -- the ladder arithmetic that corrected the spec
    chk("s=21 is INFEASIBLE at N=20 and the top step is 20 minutes",
        (420 // 21) - 1 < N and (420 // 20) - 1 == N and 21 not in SCALES and 20 in SCALES,
        f"420//21={420//21} points -> {420//21-1} returns")

    # 10 -- the primary is the pre-registered one
    chk("the runner's PRIMARY is s=5, x=2.0 sigma, tau=N=20, phase 0",
        PRIMARY == {"s": 5, "x": 2.0, "tau": 20, "phase": 0} and 20 in TAUS)
    chk("the reserved slice boundary is the pre-registered one",
        IS_END == "2026-04-10")

    # 11 -- known answer: a random walk has excess ~0
    nR = 3000
    rw = rng.normal(size=(T - 1, nR))
    Pw = np.vstack([np.zeros((1, nR)), rw.cumsum(0)])
    yw, _, sw = detrend_ext(Pw)
    vw = np.ones((T, nR), bool)
    ow = tally(outcomes(yw, sw, vw, 2.0, np.full(nR, 1e-9)), nR)
    i = TAUS.index(20)
    po = ow[i, 0] / max(ow[i].sum(), 1)
    # its own sign-shuffle null
    sg2 = np.where(rng.integers(0, 2, rw.shape) == 1, 1.0, -1.0)
    Pn = np.vstack([np.zeros((1, nR)), (np.abs(rw) * sg2).cumsum(0)])
    yn, _, sn = detrend_ext(Pn)
    on = tally(outcomes(yn, sn, vw, 2.0, np.full(nR, 1e-9)), nR)
    pn = on[i, 0] / max(on[i].sum(), 1)
    chk("known answer: a random walk's excess over its own sign shuffle is ~0",
        abs(po - pn) < 0.05, f"obs {po:.4f} null {pn:.4f} excess {po-pn:+.4f}")

    P(f"\n  {len(fails)} failed: {fails}" if fails else "\n  all checks pass")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())

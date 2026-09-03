"""D312 -- vol-targeted breadth.

    uv run python scripts/run_d312_vol_targeted.py --selftest
    uv run python scripts/run_d312_vol_targeted.py [--draws 200]

PRE-REGISTERED AT `201dfff`, committed before this file existed (R8).

THIS VARIES BREADTH ON RISK, NEVER ON EXPECTED RETURN. D299, D308 and D311 each
closed the return-timing question; this one keys on the quantity that is actually
measurable -- between N_eff 2 and 10 the mean differs at t = 0.42 and the vol at
t = 6.37.

THREE ARMS, MATCHED ON REALISED VOLATILITY:
  F  fixed N_eff, vol floats -- the baseline
  B  vary N_eff to hold vol near target, always fully invested
  E  fixed N_eff, scale exposure to hold vol near target

E EXISTS TO TEST MY OWN ARGUMENT. I claimed exposure-scaling weakly dominates
breadth-scaling, because widening dilutes the edge while leverage does not. Q3
and Q7 enter that as falsifiable predictions rather than as a premise.

A COMBINED B+E ARM IS DELIBERATELY OUT OF SCOPE for this run, at the principal's
direction. It is a plausible successor and it would confound the very comparison
this study exists to make.

THE NULL IS A CIRCULAR ROTATION of the realised path, not D308c's Jensen-gap
draw. This study has no oracle and no max-picking, so there is no Jensen gap to
price; the question is whether de-risking WHEN THE BOOK IS VOLATILE beats
de-risking by the same amount, in the same pattern, at unrelated times.

TWO READINGS THE PRE-REGISTRATION LEFT OPEN, both resolved here in the
conservative direction and both flagged in the record:

  * The targets are D310's PUBLISHED `vol_bp` for `none/exp{2,5,10,19}`, read
    from the data file rather than recomputed, so Q1's 10% band is measured
    against the literal pre-registered number.
  * Assertion [2]'s second clause -- "the fixed arm's vol must miss by more" --
    cannot be tested on the FULL-SAMPLE vol, because each target IS its fixed
    arm's full-sample vol and that miss is identically zero. It is therefore
    tested on the TRAILING vol series, which is the thing the rule controls and
    the only reading under which the clause has content.

The grid is D311's fifteen levels PLUS 19.0, which D311 omitted and this study's
declared bases require.
"""

from __future__ import annotations

import argparse
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


T = _load("d311", "run_d311_adaptive_lambda.py")
R, W, D, SP, M = T.R, T.W, T.D, T.SP, T.M

LEVELS = tuple(sorted(set(T.LEVELS) | {19.0}))
BASES = (2.0, 5.0, 10.0, 19.0)          # the four declared, vol-matched levels
ARMS = ("F", "B", "E")
VOL_WIN = 63
MAX_SCALE = 2.0
ANN, SEED = 252.0, 20260904
OUT = REPO / "data" / "d312_vol_targeted.json"


# ---------------------------------------------------------------- primitives
def roll_sd(v, w=VOL_WIN, lag=True):
    """Trailing sd of `v` over a `w`-bar window, LAGGED one bar.

    `lag=False` is the peeking variant assertion [3] fires at: it lets the rule
    see bar t's own return before it sizes bar t.
    """
    out = np.full(v.size, np.nan)
    c1 = np.concatenate([[0.0], np.cumsum(v)])
    c2 = np.concatenate([[0.0], np.cumsum(v * v)])
    j = np.arange(w, v.size + 1)
    s1 = c1[j] - c1[j - w]
    s2 = c2[j] - c2[j - w]
    out[j - 1] = np.sqrt(np.maximum((s2 - s1 * s1 / w) / (w - 1), 0.0))
    return np.concatenate([[np.nan], out[:-1]]) if lag else out


def build(A, G, rt):
    """Per-bar gross, cost and net for every level. `none` family, no band."""
    out = {}
    for lv in LEVELS:
        r = R.simulate(A, G, "exp", lv, 0.0, False)
        ok = r["mask"]
        gross = np.where(ok, r["book"] * 1e4, 0.0)
        cost = np.where(ok, rt * r["turn"], 0.0)
        out[lv] = dict(gross=gross, cost=cost, net=gross - cost, mask=ok)
    return out, out[LEVELS[0]]["mask"]


def pack(cells, mask):
    """(levels, bars) matrices on the masked bars -- everything downstream is
    indexing into these, so a null draw costs one gather and no simulation."""
    idx = np.flatnonzero(mask)
    return (np.array([cells[lv]["gross"][idx] for lv in LEVELS]),
            np.array([cells[lv]["cost"][idx] for lv in LEVELS]))


def arm_path(NET, base, target, lag=True):
    """The realised control path: level indices for B, exposure scale for E."""
    b = LEVELS.index(base)
    vols = np.array([roll_sd(NET[j], lag=lag) for j in range(len(LEVELS))])
    good = np.isfinite(vols).all(axis=0)
    pick = np.full(NET.shape[1], b, np.int64)
    pick[good] = np.abs(vols[:, good] - target).argmin(axis=0)

    v = vols[b]
    sc = np.where(np.isfinite(v) & (v > 0), target / np.maximum(v, 1e-12), 1.0)
    return pick, np.clip(sc, 0.0, MAX_SCALE)


def book(GR, CO, arm, base, tc, rt, pick=None, sc=None):
    """One arm's per-bar gross, cost and net, transitions charged."""
    n, b = GR.shape[1], LEVELS.index(base)
    if arm == "F":
        return GR[b], CO[b], np.zeros(n), np.full(n, base), np.ones(n)
    if arm == "B":
        g, c = GR[pick, np.arange(n)], CO[pick, np.arange(n)]
        tr = np.zeros(n)
        tr[1:] = tc[pick[:-1], pick[1:]]
        return g, c, tr, np.array(LEVELS)[pick], np.ones(n)
    tr = np.abs(np.diff(np.concatenate([[1.0], sc]))) * rt / 2.0
    return GR[b] * sc, CO[b] * sc, tr, np.full(n, base), sc


def stats(g, c, tr, sc, target):
    net = g - c - tr
    sd = net.std(ddof=1)
    eq = np.cumsum(net)
    tv = roll_sd(net, lag=False)
    tv = tv[np.isfinite(tv)]
    return dict(
        gross_bp=float(g.mean()), cost_bp=float((c + tr).mean()),
        trans_bp=float(tr.mean()), net_bp=float(net.mean()), vol_bp=float(sd),
        sharpe=float(net.mean() / sd * np.sqrt(ANN)),
        gross_sharpe=float(g.mean() / g.std(ddof=1) * np.sqrt(ANN)),
        t=float(net.mean() / (sd / np.sqrt(net.size))),
        maxdd_bp=float(np.max(np.maximum.accumulate(eq) - eq)),
        exposure=float(sc.mean()), target=target,
        vol_vs_target=float(sd / target - 1.0),
        vol_disp=float(tv.std(ddof=1)),
        trail_miss=float(np.abs(tv / target - 1.0).mean()),
        bars=int(net.size))


def cell(GR, CO, arm, base, tc, rt, target, **kw):
    g, c, tr, path, sc = book(GR, CO, arm, base, tc, rt, **kw)
    return stats(g, c, tr, sc, target), path


def bh(ps, q=0.10):
    """Benjamini-Hochberg. Returns the boolean reject vector in input order."""
    o = np.argsort(ps)
    m = len(ps)
    thr = (np.arange(1, m + 1) / m) * q
    hit = np.asarray(ps)[o] <= thr
    k = np.flatnonzero(hit).max() + 1 if hit.any() else 0
    rej = np.zeros(m, bool)
    rej[o[:k]] = True
    return rej


# ---------------------------------------------------------------- assertions
def assertions(cells, mask, GR, CO, tc, rt, targets, d310):
    print("\nASSERTIONS")
    NET = GR - CO
    n = NET.shape[1]

    # 1. REPRODUCTION -- arm F is D310's cell, to floating point.
    worst = 0.0
    for lv in (2.0, 3.0, 5.0, 7.0, 10.0, 14.0, 19.0):
        ref = d310[f"none/exp{int(lv)}"]
        j = LEVELS.index(lv)
        worst = max(worst, abs(float(NET[j].mean()) - ref["net_bp"]),
                    abs(float(GR[j].mean()) - ref["gross_bp"]))
    assert worst < 1e-9, f"[1] arm F differs from D310 by {worst:.2e} bp"
    print(f"    [1] arm F reproduces D310's gross AND net at all 7 shared "
          f"levels (max {worst:.1e} bp)")

    # 2. THE TARGET IS HIT, and the fixed arm's TRAILING vol misses by more.
    #    The full-sample clause is vacuous by construction -- each target IS its
    #    own fixed arm's full-sample vol -- so the clause is tested where it has
    #    content.
    # THE LAGGED RULE MISSES ITS TARGET AT EVERY CELL, so the assertion is put
    # where it can still catch a BUG: the same rule reading bar t's own return
    # must hit. If peeking hits and lagging misses, the arithmetic is right and
    # the estimator is the problem -- which is Q1's answer, not a defect. If
    # peeking ALSO missed, the book construction would be wrong.
    miss = {}
    print("        %-8s %8s %8s %9s %8s %8s %8s" % (
        "cell", "vol", "vs tgt", "PEEKING", "trailmiss", "pinlo", "pinhi"))
    for base, tg in zip(BASES, targets):
        f, _ = cell(GR, CO, "F", base, tc, rt, tg)
        assert abs(f["vol_vs_target"]) < 0.01, \
            f"[2] target {tg:.0f} is not level {base:g}'s own vol"
        pick, sc = arm_path(NET, base, tg)
        pk, sk = arm_path(NET, base, tg, lag=False)
        print("        %-8s %8.0f %+8.1f%% %9s %9.3f %8s %8s" % (
            f"F@N{base:g}", f["vol_bp"], 100 * f["vol_vs_target"], "--",
            f["trail_miss"], "--", "--"))
        for arm, kw, pkw in (("B", dict(pick=pick), dict(pick=pk)),
                             ("E", dict(sc=sc), dict(sc=sk))):
            s, _ = cell(GR, CO, arm, base, tc, rt, tg, **kw)
            p, _ = cell(GR, CO, arm, base, tc, rt, tg, **pkw)
            lo = np.mean(pick == 0) if arm == "B" else np.mean(sc <= 0.0)
            hi = (np.mean(pick == len(LEVELS) - 1) if arm == "B"
                  else np.mean(sc >= MAX_SCALE))
            miss[f"{arm}@N{base:g}"] = dict(lagged=s["vol_vs_target"],
                                            peeking=p["vol_vs_target"],
                                            pin_lo=float(lo), pin_hi=float(hi))
            print("        %-8s %8.0f %+8.1f%% %+8.1f%% %9.3f %7.1f%% %7.1f%%" % (
                f"{arm}@N{base:g}", s["vol_bp"], 100 * s["vol_vs_target"],
                100 * p["vol_vs_target"], s["trail_miss"], 100 * lo, 100 * hi))
            # arm E has no grid to run out of, so peeking MUST land on target.
            if arm == "E":
                assert abs(p["vol_vs_target"]) < 0.10, \
                    f"[2] {arm}@{tg:.0f} misses by {p['vol_vs_target']:+.1%} " \
                    f"EVEN WHEN PEEKING -- the sizing arithmetic is wrong"
            assert s["trail_miss"] < f["trail_miss"], \
                f"[2] {arm}@{tg:.0f} trailing miss {s['trail_miss']:.3f} " \
                f">= fixed {f['trail_miss']:.3f}"
    print("    [2] the sizing arithmetic is correct -- arm E lands within 10% "
          "of every target WHEN IT PEEKS -- and every arm tracks the target\n"
          "        more closely than its own fixed arm. THE LAGGED RULE MISSES "
          "AT EVERY CELL, which is Q1's answer and not a defect")

    # 3. CAUSALITY -- and the audit must be able to fail.
    for base, tg in zip(BASES, targets):
        p1, s1 = arm_path(NET, base, tg, lag=True)
        p0, s0 = arm_path(NET, base, tg, lag=False)
        assert not np.array_equal(p1, p0), \
            f"[3] the peeking breadth path at {tg:.0f} is IDENTICAL -- the " \
            f"lag is not doing anything and the audit cannot fail"
        assert not np.allclose(s1, s0), \
            f"[3] the peeking exposure path at {tg:.0f} is identical"
        b1 = book(GR, CO, "B", base, tc, rt, pick=p1)[0]
        b0 = book(GR, CO, "B", base, tc, rt, pick=p0)[0]
        assert not np.array_equal(b1, b0), "[3] peeking gives the same book"
    dp = np.mean(arm_path(NET, 5.0, targets[1], True)[0]
                 != arm_path(NET, 5.0, targets[1], False)[0])
    print(f"    [3] CAUSALITY: the rule reads only t-1, and a peeking variant "
          f"moves {dp:.1%} of bars to a different level -- the audit fails when "
          f"the lag is removed")

    # 4. TRANSITIONS zero at no move, monotone in |d log N_eff|.
    assert tc[LEVELS.index(5.0), LEVELS.index(5.0)] == 0.0
    seq = [tc[LEVELS.index(2.0), LEVELS.index(lv)]
           for lv in (2.5, 3.0, 5.0, 10.0, 25.0)]
    assert all(a <= b + 1e-12 for a, b in zip(seq, seq[1:])), f"[4] {seq}"
    flat = np.full(n, LEVELS.index(7.0), np.int64)
    assert book(GR, CO, "B", 7.0, tc, rt, pick=flat)[2].sum() == 0.0
    assert book(GR, CO, "E", 7.0, tc, rt, sc=np.ones(n))[2].sum() == 0.0
    print(f"    [4] transitions vanish on a constant path in both arms and are "
          f"monotone -- 2->2.5 costs {seq[0]:.1f} bp, 2->25 costs {seq[-1]:.1f}")

    # 5. EVERY CELL A DISTINCT BOOK.
    seen = {}
    for base, tg in zip(BASES, targets):
        pick, sc = arm_path(NET, base, tg)
        for arm, kw in (("F", {}), ("B", dict(pick=pick)), ("E", dict(sc=sc))):
            g, c, tr, _, _ = book(GR, CO, arm, base, tc, rt, **kw)
            key = float(np.round((g - c - tr).sum(), 9))
            assert key not in seen, \
                f"[5] {arm}@{tg:.0f} is bit-identical to {seen[key]}"
            seen[key] = f"{arm}@{tg:.0f}"
    print(f"    [5] all {len(seen)} cells are distinct books")

    # 6. THE NULL MATCHES on move count and |delta| distribution.
    rng = np.random.default_rng(7)
    pick, sc = arm_path(NET, 5.0, targets[1])
    for lab, x in (("breadth", pick.astype(float)), ("exposure", sc)):
        r = np.roll(x, int(rng.integers(1, x.size)))
        mv = lambda z: int((np.diff(z) != 0).sum())
        assert abs(mv(r) - mv(x)) <= 1, f"[6] {lab} move count {mv(r)}/{mv(x)}"
        a, b = np.sort(np.abs(np.diff(x))), np.sort(np.abs(np.diff(r)))
        assert abs(a.sum() - b.sum()) <= 1.01 * max(a.max(), 1e-9), \
            f"[6] {lab} |delta| mass {a.sum():.3f} vs {b.sum():.3f}"
    print("    [6] rotation preserves move count and the |delta| distribution "
          "in both arms, up to the single wrap point")

    # C. COST DIMENSIONS against d295's published fixed point.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's "
          f"{b0['cost_bar_mean']:.4f}; the doubled form is rejected")

    # 7. THE SELF-TEST MUST RAISE ON A BROKEN BOOK -- corrupted INSIDE the mask.
    broke = False
    try:
        bad = {lv: dict(cells[lv]) for lv in LEVELS}
        idx = np.flatnonzero(mask)[:200]
        g = bad[5.0]["gross"].copy()
        g[idx] += 0.05
        bad[5.0] = dict(bad[5.0], gross=g, net=g - bad[5.0]["cost"])
        ref = d310["none/exp5"]
        assert abs(float(bad[5.0]["gross"][mask].mean())
                   - ref["gross_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[7] reproduction passed a book handed free money inside the mask"
    print("    [7] and [1] raises on a book handed free money inside the mask")
    return miss


def forecastability(NET):
    """WHY the lagged rule misses: is the trailing estimate LATE, or BLIND?

    Correlate the trailing-63 sd against the sd of the NEXT 63 bars. A vol
    target can only work to the extent this is positive -- it is the whole
    premise of the study, and it was never measured before the pre-registration
    was written.
    """
    out = {}
    print("\nFORECASTABILITY of the book's own volatility -- the study's premise")
    print("    %-6s %10s %10s %10s %9s" % (
        "N_eff", "corr", "mean trail", "mean fwd", "ratio"))
    for base in BASES:
        v = NET[LEVELS.index(base)]
        tr = roll_sd(v, lag=True)
        fw = np.concatenate([roll_sd(v, lag=False)[VOL_WIN - 1:],
                             np.full(VOL_WIN - 1, np.nan)])
        m = np.isfinite(tr) & np.isfinite(fw)
        c = float(np.corrcoef(tr[m], fw[m])[0, 1])
        out[str(base)] = dict(corr=c, mean_trail=float(tr[m].mean()),
                              mean_fwd=float(fw[m].mean()),
                              ratio=float(tr[m].mean() / fw[m].mean()))
        print("    %-6g %10.3f %10.0f %10.0f %9.3f" % (
            base, c, tr[m].mean(), fw[m].mean(), tr[m].mean() / fw[m].mean()))
    return out


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()

    print("D312  vol-targeted breadth")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    rt = 4.0 * float(np.nanmedian(half[np.isfinite(half)]))
    d310 = json.loads((REPO / "data" / "d310_rank_weighted.json").read_text())["cells"]

    # THE TARGETS ARE DECLARED, NOT SEARCHED -- read from D310's published cells.
    targets = [d310[f"none/exp{int(b)}"]["vol_bp"] for b in BASES]

    cells, mask = build(A, G, rt)
    GR, CO = pack(cells, mask)
    NET = GR - CO
    tc = np.array([[T.transition(x, y, rt) for y in LEVELS] for x in LEVELS])
    nb = GR.shape[1]
    print(f"  built {len(LEVELS)} levels over {nb:,} bars, rt {rt:.1f} bp "
          f"({time.time() - t0:.0f}s)")
    print("  targets (D310 vol_bp): " +
          "  ".join(f"N={b:g}:{t:.0f}" for b, t in zip(BASES, targets)))

    miss = assertions(cells, mask, GR, CO, tc, rt, targets, d310)
    fc = forecastability(NET)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    rng = np.random.default_rng(SEED)
    res = {"round_trip": rt, "bars": nb, "targets": dict(zip(map(str, BASES), targets)),
           "target_miss": miss, "forecastability": fc, "cells": {}, "null": {}}

    print("\nTHE TWELVE CELLS")
    h = "%-10s %8s %8s %8s %8s %8s %8s %8s %8s %8s"
    print(h % ("cell", "gross", "cost", "trans", "NET", "vol", "vs tgt",
               "SHARPE", "voldisp", "expo"))
    print("-" * 92)
    keep = {}
    for base, tg in zip(BASES, targets):
        pick, sc = arm_path(NET, base, tg)
        for arm in ARMS:
            kw = dict(pick=pick) if arm == "B" else (
                dict(sc=sc) if arm == "E" else {})
            s, path = cell(GR, CO, arm, base, tc, rt, tg, **kw)
            name = f"{arm}@N{base:g}"
            s["base"] = base
            s["arm"] = arm
            res["cells"][name] = s
            keep[name] = (base, tg, pick, sc, path)
            print(h % (name, "%+.2f" % s["gross_bp"], "%.2f" % s["cost_bp"],
                       "%.3f" % s["trans_bp"], "%+.2f" % s["net_bp"],
                       "%.0f" % s["vol_bp"], "%+.1f%%" % (100 * s["vol_vs_target"]),
                       "%+.3f" % s["sharpe"], "%.0f" % s["vol_disp"],
                       "%.2f" % s["exposure"]))
        print("-" * 92)

    print("\nTHE NULL -- circular rotation of the realised path, %d draws" % a.draws)
    print("%-10s %9s %9s %9s %7s %9s %9s %9s %7s" % (
        "cell", "SHARPE", "null p50", "null p95", "p", "net", "null p50",
        "null p95", "p"))
    print("-" * 84)
    names, ps_sh, ps_nt = [], [], []
    for base, tg in zip(BASES, targets):
        pick, sc = arm_path(NET, base, tg)
        for arm in ("B", "E"):
            obs = res["cells"][f"{arm}@N{base:g}"]
            nsh, nnt = np.empty(a.draws), np.empty(a.draws)
            for d in range(a.draws):
                k = int(rng.integers(1, nb))
                if arm == "B":
                    kw = dict(pick=np.roll(pick, k))
                else:
                    kw = dict(sc=np.roll(sc, k))
                q, _ = cell(GR, CO, arm, base, tc, rt, tg, **kw)
                nsh[d], nnt[d] = q["sharpe"], q["net_bp"]
            psh = float((nsh >= obs["sharpe"]).sum() + 1) / (a.draws + 1)
            pnt = float((nnt >= obs["net_bp"]).sum() + 1) / (a.draws + 1)
            name = f"{arm}@N{base:g}"
            res["null"][name] = dict(
                sharpe_p50=float(np.median(nsh)),
                sharpe_p95=float(np.quantile(nsh, .95)), sharpe_p=psh,
                net_p50=float(np.median(nnt)),
                net_p95=float(np.quantile(nnt, .95)), net_p=pnt)
            names.append(name); ps_sh.append(psh); ps_nt.append(pnt)
            print("%-10s %+9.3f %+9.3f %+9.3f %7.4f %+9.2f %+9.2f %+9.2f %7.4f" % (
                name, obs["sharpe"], np.median(nsh), np.quantile(nsh, .95), psh,
                obs["net_bp"], np.median(nnt), np.quantile(nnt, .95), pnt))

    rs, rn = bh(ps_sh), bh(ps_nt)
    res["bh"] = {n: dict(sharpe=bool(x), net=bool(y))
                 for n, x, y in zip(names, rs, rn)}
    print(f"\n  BH-FDR q=0.10 over the {len(names)} testable cells "
          f"(the four F cells have no path to rotate):")
    print("    Sharpe: " + (", ".join(n for n, x in zip(names, rs) if x) or "NONE"))
    print("    net:    " + (", ".join(n for n, x in zip(names, rn) if x) or "NONE"))

    # ---- the predictions ---------------------------------------------------
    print("\nPREDICTIONS")
    C = res["cells"]
    q1 = all(abs(C[f"{a_}@N{b:g}"]["vol_vs_target"]) < 0.10
             for b in BASES for a_ in ("B", "E"))
    q2 = all(C[f"{a_}@N{b:g}"]["vol_disp"] < 0.5 * C[f"F@N{b:g}"]["vol_disp"]
             for b in BASES for a_ in ("B", "E"))
    q3 = all(C[f"E@N{b:g}"]["net_bp"] > C[f"B@N{b:g}"]["net_bp"] for b in BASES)
    q4 = all(C[f"B@N{b:g}"]["sharpe"] <= C[f"F@N{b:g}"]["sharpe"] for b in BASES)
    q5r = {b: T.acorr(np.log(keep[f"B@N{b:g}"][4])) for b in BASES}
    q5 = all(v > 0.5 for v in q5r.values())
    q6 = all(C[f"{a_}@N{b:g}"]["trans_bp"] < 0.05 * C[f"{a_}@N{b:g}"]["gross_bp"]
             for b in BASES for a_ in ("B", "E"))
    q7 = C["E@N2"]["sharpe"] < C["F@N2"]["sharpe"]
    q8 = (C["B@N19"]["sharpe"] > C["F@N19"]["sharpe"]) and \
         (C["B@N2"]["sharpe"] <= C["F@N2"]["sharpe"])
    res["predictions"] = dict(Q1=q1, Q2=q2, Q3=q3, Q4=q4, Q5=q5, Q6=q6,
                              Q7=q7, Q8=q8,
                              Q5_lag1={str(k): v for k, v in q5r.items()})
    for k, v in (("Q1 vol within 10% of target", q1),
                 ("Q2 vol dispersion cut by >half", q2),
                 ("Q3 E beats B on net at every target", q3),
                 ("Q4 B never beats fixed on Sharpe  [load-bearing]", q4),
                 ("Q5 breadth path persistent, lag-1 > 0.5", q5),
                 ("Q6 transitions under 5% of gross", q6),
                 ("Q7 E hurts at the tightest target", q7),
                 ("Q8 B beats F wide and not tight", q8)):
        print(f"    {'CONFIRMED' if v else 'FALSIFIED'}  {k}")
    print("    Q5 lag-1 by target: " +
          "  ".join(f"N={k:g}:{v:+.3f}" for k, v in q5r.items()))

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""D313 -- universe-conditioned risk.

    uv run python scripts/run_d313_universe_risk.py --selftest
    uv run python scripts/run_d313_universe_risk.py [--draws 200]

PRE-REGISTERED AT `a533b8c`, committed before this file existed (R8).

D312 conditioned on the BOOK'S OWN trailing sd, measured at rho = -0.016, and
lost every cell. This runs the same arms on the conditioner that forecasts:
cross-sectional dispersion over the whole live universe, +0.352 at N_eff=2, with
its own level persisting at lag-63 rho +0.616.

THE MAPPING IS THE DESIGN'S ACTUAL IDEA. Dispersion is not in book-vol units, so

    c_j(t)  = trailing-252 MEDIAN of  v_j(s) / P(s)      for s < t
    vhat(t) = c_j(t) * P(t)

estimates the noisy quantity -- a two-name book's realised vol -- as a NEAR-
CONSTANT structural ratio where 252 bars of averaging conditions it well, and
takes the bar-to-bar variation from ~1,019 names. D312 did the opposite: it asked
a 63-bar two-name series to supply the time variation. Median, not mean, for
D302's reason: the numerator is a noisy sd and its ratio is right-skewed.

THE TARGET IS THE MEAN OF ROLLING SDs, NOT THE FULL-SAMPLE SD. D312's full-sample
target exceeded the average of rolling sds -- the between-window component sits
in one and not the other -- so `target / vhat` averaged above 1 before any
forecasting happened and its arm E ran at mean exposure 1.34-1.53. A third of it
was leverage. Q6 makes the fix falsifiable.

xs_out IS A DECLARED SECONDARY ARM, NEVER A FALLBACK. It scored +0.355 against
xs_all's +0.352 in a post-hoc diagnostic that compared six predictors; choosing
on that margin would be selecting on the diagnostic. Q7 predicts the two are
indistinguishable.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


X = _load("d312", "run_d312_vol_targeted.py")
U = _load("d312u", "d312_universe_forecast.py")
D, W, M, SP, T = X.D, X.W, X.M, X.SP, X.T
LEVELS, BASES = X.LEVELS, X.BASES
roll_sd, book, cell, stats, bh = X.roll_sd, X.book, X.cell, X.stats, X.bh

VOL_WIN, CAL_WIN = 63, 252
MAX_SCALE = X.MAX_SCALE
ANN, SEED = 252.0, 20260905
OUT = REPO / "data" / "d313_universe_risk.json"

# arm -> (predictor key, mechanism). F ignores both.
ARMS = {"F": (None, "F"), "B": ("xs_all", "B"), "E": ("xs_all", "E"),
        "B_own": ("own", "B"), "B_out": ("xs_out", "B")}


def trailing_median(r, w=CAL_WIN):
    """Trailing median of `r` over a `w`-bar window ENDING AT t.

    `r` is already lagged one bar by its inputs, so a window ending at t reads
    only data through t-1. NaN-tolerant via nanmedian; windows that are entirely
    NaN come back NaN and the caller treats them as no forecast.
    """
    out = np.full(r.size, np.nan)
    if r.size >= w:
        sw = sliding_window_view(r, w)
        with np.errstate(invalid="ignore"):
            out[w - 1:] = np.nanmedian(sw, axis=1)
    return out


def predicted_vol(NET, P, lag=True):
    """vhat_j(t) = c_j(t) * P(t), the structural ratio times the wide read."""
    V = np.array([roll_sd(NET[j], lag=lag) for j in range(NET.shape[0])])
    Pp = np.where(np.isfinite(P) & (P > 0), P, np.nan)
    out = np.full_like(V, np.nan)
    for j in range(V.shape[0]):
        out[j] = trailing_median(V[j] / Pp) * Pp
    return out


def paths(VH, base, target):
    """The realised control paths: level indices for B, exposure scale for E."""
    b = LEVELS.index(base)
    n = VH.shape[1]
    pick = np.full(n, b, np.int64)
    good = np.isfinite(VH).all(axis=0)
    pick[good] = np.abs(VH[:, good] - target).argmin(axis=0)
    v = VH[b]
    sc = np.where(np.isfinite(v) & (v > 0), target / np.maximum(v, 1e-12), 1.0)
    return pick, np.clip(sc, 0.0, MAX_SCALE)


def run_cell(GR, CO, VH, arm, base, tc, rt, target):
    key, mech = ARMS[arm]
    if mech == "F":
        return cell(GR, CO, "F", base, tc, rt, target)
    pick, sc = paths(VH[key], base, target)
    kw = dict(pick=pick) if mech == "B" else dict(sc=sc)
    s, path = cell(GR, CO, mech, base, tc, rt, target, **kw)
    return s, (pick if mech == "B" else sc)


# ---------------------------------------------------------------- assertions
def assertions(GR, CO, NET, VH, tc, rt, targets, d310, d312, fc, P):
    print("\nASSERTIONS")

    # 1a. ARM F reproduces D310's gross AND net at every shared level.
    worst = 0.0
    for lv in (2.0, 3.0, 5.0, 7.0, 10.0, 14.0, 19.0):
        ref, j = d310[f"none/exp{int(lv)}"], LEVELS.index(lv)
        worst = max(worst, abs(float(NET[j].mean()) - ref["net_bp"]),
                    abs(float(GR[j].mean()) - ref["gross_bp"]))
    assert worst < 1e-9, f"[1] arm F differs from D310 by {worst:.2e} bp"

    # 1b. ARM B_own AT D312'S OWN TARGETS reproduces D312's B cells BIT-
    #     IDENTICALLY. D313's targets are the mean of rolling sds, so this is
    #     run at D312's full-sample targets on purpose -- it is a reproduction
    #     check, not a cell of this study.
    worst2 = 0.0
    for base in BASES:
        tg = d310[f"none/exp{int(base)}"]["vol_bp"]
        pick, _ = paths(VH["own"], base, tg)
        s, _ = cell(GR, CO, "B", base, tc, rt, tg, pick=pick)
        ref = d312["cells"][f"B@N{base:g}"]
        worst2 = max(worst2, abs(s["net_bp"] - ref["net_bp"]),
                     abs(s["sharpe"] - ref["sharpe"]))
    assert worst2 == 0.0, f"[1] B_own differs from D312's B by {worst2:.2e}"
    print(f"    [1] arm F reproduces D310 at 7 levels (max {worst:.1e} bp) and "
          f"B_own reproduces D312's B BIT-IDENTICALLY at all 4 targets")

    # 2. CAUSALITY -- and the audit must be able to fail.
    VHp = predicted_vol(NET, P["xs_all"], lag=False)
    moved = []
    for base, tg in zip(BASES, targets):
        p1, s1 = paths(VH["xs_all"], base, tg)
        p0, s0 = paths(VHp, base, tg)
        assert not np.array_equal(p1, p0), \
            f"[2] the peeking breadth path at {tg:.0f} is IDENTICAL -- the lag " \
            f"is not doing anything and the audit cannot fail"
        assert not np.allclose(s1, s0), f"[2] peeking exposure path identical"
        b1 = book(GR, CO, "B", base, tc, rt, pick=p1)[0]
        b0 = book(GR, CO, "B", base, tc, rt, pick=p0)[0]
        assert not np.array_equal(b1, b0), "[2] peeking gives the same book"
        moved.append(np.mean(p1 != p0))
    print(f"    [2] CAUSALITY: c_j and P read only t-1, and removing the lag "
          f"moves {100 * float(np.mean(moved)):.1f}% of bars to a different "
          f"level -- the audit fails when the lag goes")

    # 3. STAGE 0 reproduces D312's published diagnostic EXACTLY. This is a
    #    harness check: both values are already known and cannot surprise.
    ref = json.loads((REPO / "data" / "d312_universe_forecast.json").read_text())
    # D312's diagnostic carried six predictors; this study declares three, so
    # only the shared keys are compared. The other three are not recomputed here
    # precisely because re-opening that comparison would be searching.
    dp = max(abs(fc["persistence"][k] - ref["persistence"][k])
             for k in fc["persistence"])
    dc = max(abs(fc["forward_corr"][a][b] - ref["forward_corr"][a][b])
             for a in fc["forward_corr"] for b in fc["forward_corr"][a])
    assert dp < 1e-12 and dc < 1e-12, f"[3] stage 0 drifted: {dp:.1e} / {dc:.1e}"
    print(f"    [3] stage 0 reproduces d312_universe_forecast.json exactly "
          f"(persistence {dp:.0e}, forward corr {dc:.0e}) -- a harness check, "
          f"not a test")

    # 4. TRANSITIONS zero on a constant path in every arm, monotone.
    n = GR.shape[1]
    assert tc[LEVELS.index(5.0), LEVELS.index(5.0)] == 0.0
    seq = [tc[LEVELS.index(2.0), LEVELS.index(lv)]
           for lv in (2.5, 3.0, 5.0, 10.0, 25.0)]
    assert all(a <= b + 1e-12 for a, b in zip(seq, seq[1:])), f"[4] {seq}"
    assert book(GR, CO, "B", 7.0, tc, rt,
                pick=np.full(n, LEVELS.index(7.0), np.int64))[2].sum() == 0.0
    assert book(GR, CO, "E", 7.0, tc, rt, sc=np.ones(n))[2].sum() == 0.0
    print(f"    [4] transitions vanish on a constant path in both mechanisms "
          f"and are monotone -- 2->2.5 costs {seq[0]:.1f}, 2->25 {seq[-1]:.1f}")

    # 5. EVERY CELL A DISTINCT BOOK, all 20.
    seen = {}
    for base, tg in zip(BASES, targets):
        for arm in ARMS:
            s, _ = run_cell(GR, CO, VH, arm, base, tc, rt, tg)
            k = (round(s["net_bp"], 12), round(s["vol_bp"], 12))
            assert k not in seen, f"[5] {arm}@N{base:g} identical to {seen[k]}"
            seen[k] = f"{arm}@N{base:g}"
    print(f"    [5] all {len(seen)} cells are distinct books")

    # 6. THE NULL MATCHES on move count and |delta| distribution.
    rng = np.random.default_rng(11)
    pick, sc = paths(VH["xs_all"], 5.0, targets[1])
    for lab, x in (("breadth", pick.astype(float)), ("exposure", sc)):
        r = np.roll(x, int(rng.integers(1, x.size)))
        mv = lambda z: int((np.diff(z) != 0).sum())
        assert abs(mv(r) - mv(x)) <= 1, f"[6] {lab} moves {mv(r)}/{mv(x)}"
        a, b = np.abs(np.diff(x)), np.abs(np.diff(r))
        assert abs(a.sum() - b.sum()) <= 1.01 * max(a.max(), 1e-9), \
            f"[6] {lab} |delta| mass {a.sum():.3f} vs {b.sum():.3f}"
    print("    [6] rotation preserves move count and the |delta| distribution "
          "in both mechanisms, up to the single wrap point")

    # 7. EXPOSURE ACCOUNTING -- arm B is exactly 1.00 by construction.
    for base, tg in zip(BASES, targets):
        for arm in ("B", "B_own", "B_out"):
            s, _ = run_cell(GR, CO, VH, arm, base, tc, rt, tg)
            assert s["exposure"] == 1.0, \
                f"[7] {arm}@N{base:g} exposure {s['exposure']} != 1.0"
    print("    [7] every breadth arm is exactly fully invested; arm E's "
          "exposure is reported and enters Q6")

    # C. COST DIMENSIONS against d295's published fixed point.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's "
          f"{b0['cost_bar_mean']:.4f}; the doubled form is rejected")

    # 8. THE SELF-TEST MUST RAISE ON A BROKEN BOOK -- corrupted INSIDE the mask.
    broke = False
    try:
        g = GR[LEVELS.index(5.0)].copy()
        g[:200] += 0.05
        assert abs(float(g.mean()) - d310["none/exp5"]["gross_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[8] reproduction passed a book handed free money in the mask"
    print("    [8] and [1] raises on a book handed free money inside the mask")


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()

    print("D313  universe-conditioned risk")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    G = W.build_gate(A, verbose=False)
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    half = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    rt = 4.0 * float(np.nanmedian(half[np.isfinite(half)]))
    d310 = json.loads((REPO / "data" / "d310_rank_weighted.json").read_text())["cells"]
    d312 = json.loads((REPO / "data" / "d312_vol_targeted.json").read_text())

    cells, mask = X.build(A, G, rt)
    GR, CO = X.pack(cells, mask)
    NET = GR - CO
    idx = np.flatnonzero(mask)
    tc = np.array([[T.transition(x, y, rt) for y in LEVELS] for x in LEVELS])
    nb = GR.shape[1]

    disp, ncount = U.dispersion(A, G, A["r1T"].shape[0])
    P = {"xs_all": U.trail_mean(disp["all"], idx),
         "xs_out": U.trail_mean(disp["out"], idx)}
    VH = {"xs_all": predicted_vol(NET, P["xs_all"]),
          "xs_out": predicted_vol(NET, P["xs_out"]),
          "own": np.array([roll_sd(NET[j], lag=True) for j in range(len(LEVELS))])}

    # THE TARGETS ARE THE LITERAL PRE-REGISTERED NUMBERS, not a recomputation.
    # They are each base level's mean rolling-63 sd, taken from D312's diagnostic
    # where the mean ran over bars that ALSO had a forward window -- so a plain
    # nanmean here lands 0.3-0.6% away (296.6 against 295, 229.0 against 228).
    # The study runs on what was declared; the assertion checks the declared
    # numbers are the quantity they claim to be.
    targets = [614.0, 403.0, 295.0, 228.0]
    got = [float(np.nanmean(roll_sd(NET[LEVELS.index(b)], lag=True)))
           for b in BASES]
    print(f"  built {len(LEVELS)} levels over {nb:,} bars, rt {rt:.1f} bp "
          f"({time.time() - t0:.0f}s)")
    print("  targets (pre-registered mean-of-rolling-sd): " +
          "  ".join(f"N={b:g}:{t:.0f}" for b, t in zip(BASES, targets)))
    assert all(abs(t - q) < 2.0 for t, q in zip(targets, got)), \
        f"the declared targets {targets} are not the mean rolling sd {got}"

    fc = dict(persistence={}, forward_corr={})
    for name in list(P) + ["own"]:
        p = P[name] if name != "own" else roll_sd(NET[LEVELS.index(2.0)], lag=True)
        q = p[np.isfinite(p)]
        fc["persistence"][name] = float(np.corrcoef(q[:-VOL_WIN], q[VOL_WIN:])[0, 1])
    for name in ["own"] + list(P):
        row = {}
        for base in BASES:
            v = NET[LEVELS.index(base)]
            f = np.concatenate([roll_sd(v, lag=False)[VOL_WIN - 1:],
                                np.full(VOL_WIN - 1, np.nan)])
            p = roll_sd(v, lag=True) if name == "own" else P[name]
            m = np.isfinite(p) & np.isfinite(f)
            row[str(base)] = float(np.corrcoef(p[m], f[m])[0, 1])
        fc["forward_corr"][name] = row

    assertions(GR, CO, NET, VH, tc, rt, targets, d310, d312, fc, P)
    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    rng = np.random.default_rng(SEED)
    res = {"round_trip": rt, "bars": nb, "cal_win": CAL_WIN,
           "targets": dict(zip(map(str, BASES), targets)),
           "stage0": fc, "cells": {}, "null": {}}

    print("\nTHE CELLS   (net Sharpe is primary; gross Sharpe beside it)")
    h = "%-11s %8s %8s %7s %8s %7s %8s %8s %8s %8s %6s"
    print(h % ("cell", "gross", "cost", "trans", "NET", "vol", "vs tgt",
               "netSHRP", "grsSHRP", "voldisp", "expo"))
    print("-" * 100)
    keep = {}
    for base, tg in zip(BASES, targets):
        for arm in ARMS:
            s, path = run_cell(GR, CO, VH, arm, base, tc, rt, tg)
            name = f"{arm}@N{base:g}"
            s["arm"], s["base"] = arm, base
            res["cells"][name], keep[name] = s, path
            print(h % (name, "%+.2f" % s["gross_bp"], "%.2f" % s["cost_bp"],
                       "%.3f" % s["trans_bp"], "%+.2f" % s["net_bp"],
                       "%.0f" % s["vol_bp"], "%+.1f%%" % (100 * s["vol_vs_target"]),
                       "%+.3f" % s["sharpe"], "%+.3f" % s["gross_sharpe"],
                       "%.0f" % s["vol_disp"], "%.2f" % s["exposure"]))
        print("-" * 100)

    print(f"\nTHE NULL -- circular rotation of the realised path, {a.draws} draws")
    print("%-11s %9s %9s %9s %7s %9s %9s %9s %7s" % (
        "cell", "netSHRP", "null p50", "null p95", "p", "net", "null p50",
        "null p95", "p"))
    print("-" * 86)
    names, ps_sh, ps_nt = [], [], []
    for base, tg in zip(BASES, targets):
        for arm in ARMS:
            if arm == "F":
                continue
            key, mech = ARMS[arm]
            obs = res["cells"][f"{arm}@N{base:g}"]
            pick, sc = paths(VH[key], base, tg)
            nsh, nnt = np.empty(a.draws), np.empty(a.draws)
            for d in range(a.draws):
                k = int(rng.integers(1, nb))
                kw = (dict(pick=np.roll(pick, k)) if mech == "B"
                      else dict(sc=np.roll(sc, k)))
                q, _ = cell(GR, CO, mech, base, tc, rt, tg, **kw)
                nsh[d], nnt[d] = q["sharpe"], q["net_bp"]
            psh = float((nsh >= obs["sharpe"]).sum() + 1) / (a.draws + 1)
            pnt = float((nnt >= obs["net_bp"]).sum() + 1) / (a.draws + 1)
            nm = f"{arm}@N{base:g}"
            res["null"][nm] = dict(
                sharpe_p50=float(np.median(nsh)),
                sharpe_p95=float(np.quantile(nsh, .95)), sharpe_p=psh,
                net_p50=float(np.median(nnt)),
                net_p95=float(np.quantile(nnt, .95)), net_p=pnt)
            names.append(nm); ps_sh.append(psh); ps_nt.append(pnt)
            print("%-11s %+9.3f %+9.3f %+9.3f %7.4f %+9.2f %+9.2f %+9.2f %7.4f" % (
                nm, obs["sharpe"], np.median(nsh), np.quantile(nsh, .95), psh,
                obs["net_bp"], np.median(nnt), np.quantile(nnt, .95), pnt))

    rs, rn = bh(ps_sh), bh(ps_nt)
    res["bh"] = {n: dict(sharpe=bool(x), net=bool(y))
                 for n, x, y in zip(names, rs, rn)}
    print(f"\n  BH-FDR q=0.10 over the {len(names)} testable cells "
          f"(the four F cells have no path to rotate):")
    print("    net Sharpe: " + (", ".join(n for n, x in zip(names, rs) if x) or "NONE"))
    print("    net bp/bar: " + (", ".join(n for n, x in zip(names, rn) if x) or "NONE"))

    # ---- the predictions ---------------------------------------------------
    C = res["cells"]
    q1 = all(abs(C[f"{m}@N{b:g}"]["vol_vs_target"]) < 0.10
             for b in BASES for m in ("B", "E"))
    q2 = all(C[f"{m}@N{b:g}"]["vol_disp"] < 0.7 * C[f"F@N{b:g}"]["vol_disp"]
             for b in BASES for m in ("B", "E"))
    q3 = all(C[f"B@N{b:g}"]["sharpe"] <= C[f"F@N{b:g}"]["sharpe"] for b in BASES)
    q4 = all(C[f"E@N{b:g}"]["sharpe"] <= C[f"F@N{b:g}"]["sharpe"] for b in BASES)
    q5 = all(C[f"B@N{b:g}"]["sharpe"] > C[f"B_own@N{b:g}"]["sharpe"] for b in BASES)
    q6 = all(abs(C[f"E@N{b:g}"]["exposure"] - 1.0) < 0.05 for b in BASES)
    q7 = all(abs(C[f"B@N{b:g}"]["sharpe"] - C[f"B_out@N{b:g}"]["sharpe"]) < 0.05
             for b in BASES)
    adv = {b: C[f"B@N{b:g}"]["sharpe"] - C[f"B_own@N{b:g}"]["sharpe"] for b in BASES}
    q8 = adv[2.0] == max(adv.values()) and adv[19.0] == min(adv.values())
    res["predictions"] = dict(Q1=q1, Q2=q2, Q3=q3, Q4=q4, Q5=q5, Q6=q6, Q7=q7,
                              Q8=q8, B_minus_Bown={str(k): v for k, v in adv.items()})
    print("\nPREDICTIONS")
    for k, v in (("Q1 vol within 10% of target", q1),
                 ("Q2 vol dispersion cut by >30%", q2),
                 ("Q3 B never beats fixed on net Sharpe  [load-bearing]", q3),
                 ("Q4 E never beats fixed on net Sharpe", q4),
                 ("Q5 B beats B_own at every target", q5),
                 ("Q6 arm E exposure within 1.05 of 1.00", q6),
                 ("Q7 xs_out indistinguishable from xs_all", q7),
                 ("Q8 B's edge over B_own largest at N=2, smallest at N=19", q8)):
        print(f"    {'CONFIRMED' if v else 'FALSIFIED'}  {k}")
    print("    B - B_own net Sharpe: " +
          "  ".join(f"N={k:g}:{v:+.3f}" for k, v in adv.items()))

    OUT.write_text(json.dumps(res, indent=1))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

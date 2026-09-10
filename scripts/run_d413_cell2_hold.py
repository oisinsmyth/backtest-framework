"""D413 CELL 2 -- the holding-period sweep on `deep . clean . hi`.

    uv run python scripts/run_d413_cell2_hold.py --run

EXPLORATORY, on data D413 has already spent. Clears nothing, admits nothing.

THE CELL, fixed exactly as ADDENDUM 2 reported it and NOT re-tuned here:
  REV  signed trailing 5-day return at the touch  <= its median  (-2.47%)   "deep"
  EFF  10-bar path efficiency |net|/sum|steps|     >  its median  (0.2367)   "clean"
  LIQ  trailing average dollar volume              >  its median  ($44.4M)   "hi"

WHAT DECAY SHOULD LOOK LIKE, stated before reading it, because "monotone" means different things
for the three curves and only one of them is the real test:

  CUMULATIVE bp   RISES then falls. More holding time accrues more move, until the effect is spent
                  and drift takes over. A monotone-decreasing cumulative curve would be strange.
  PER-BAR bp      THIS is the one that should decay monotonically. It is the signal's own decay
                  profile with the accrual divided out.
  THE LEVEL'S GAP (real - LVL)  the sharpest test of all. Cell 2's entire justification is a
                  +15.15 bp gap over a width-and-distance-matched band. If THAT decays smoothly the
                  level is releasing information over a horizon; if it is jagged, it is noise that
                  happened to land at h=5.

ONE POPULATION, MEASURED AT SUCCESSIVE HORIZONS. The cell membership is fixed at the touch bar and
does not depend on h, so every horizon reuses the same events and the errors are heavily correlated
ACROSS h. A monotone profile here is ONE draw behaving smoothly, not 20 independent confirmations,
and it is not evidence of the same weight as 20 separate tests would be.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d413c", REPO / "scripts" / "run_d413_combine.py")
C = importlib.util.module_from_spec(_s)
sys.modules["d413c"] = C
_s.loader.exec_module(C)
M, Z4, D = C.M, C.Z4, C.D
CS = C.CS

OUT = REPO / "data" / "d413_cell2_hold.json"
HS = (1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 21, 25, 30)
N_LVL = 40
IBKR = 0.0035


def run():
    t0 = time.time()
    print("D413 CELL 2 -- holding-period sweep on deep . clean . hi\n")
    P = D.load_panel()
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z = A["Z"]
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    tr5 = D.trailing_ret(lg, 5)
    eff = C.path_efficiency(lg)
    DV = D.X.roll_mean_T(P["CL"] * P["VOL"])
    spread = CS.corwin_schultz(P["HI"].T, P["LO"].T, P["live"].T).T
    neutral = np.full_like(spread, np.nan)
    for t in range(62, spread.shape[0]):
        with np.errstate(invalid="ignore"):
            neutral[t] = np.nanmedian(spread[t - 62:t - 2], axis=0)

    # ---- the cuts are the ones ADDENDUM 2 used: medians over the FULL event population.
    r0, g0, t0e = Z4.response(P, Z, A["rows"], A["idx"], A["has"], Z["side"], M.H)
    ii0, te0 = Z["i"][g0], t0e[g0]
    rev0, ef0, dv0 = tr5[te0, ii0] * Z["side"][g0], eff[te0, ii0], DV[te0, ii0]
    f0 = np.isfinite(rev0) & np.isfinite(ef0) & np.isfinite(dv0)
    cuts = dict(rev=float(np.median(rev0[f0])), eff=float(np.median(ef0[f0])),
                dv=float(np.median(dv0[f0])))
    print(f"  cuts (unchanged from ADDENDUM 2): REV {1e4*cuts['rev']:+.0f} bp   "
          f"EFF {cuts['eff']:.4f}   DV ${cuts['dv']/1e6:.1f}M\n")

    def cell_mask(te, ii, side_sel):
        rv = tr5[te, ii] * side_sel
        ef = eff[te, ii]
        dv = DV[te, ii]
        ok = np.isfinite(rv) & np.isfinite(ef) & np.isfinite(dv)
        return ok & (rv <= cuts["rev"]) & (ef > cuts["eff"]) & (dv > cuts["dv"])

    # ---- LVL: touches computed ONCE per draw (they do not depend on h), responses per h.
    rng = np.random.default_rng(5)
    side = Z["side"]
    grp = {s: np.where(side == s)[0] for s in (1, -1)}
    lvl_by_h = {h: [] for h in HS}
    for _ in range(N_LVL):
        w2, d2 = np.empty_like(Z["wid"]), np.empty_like(Z["dist"])
        for s, gg in grp.items():
            p = rng.permutation(gg)
            w2[gg], d2[gg] = Z["wid"][p], Z["dist"][p]
        hi_b = np.where(side > 0, Z["Ca"] - d2, Z["Ca"] + d2 + w2)
        lo_b = np.where(side > 0, Z["Ca"] - d2 - w2, Z["Ca"] + d2)
        idx, has = Z4.touches(A["HIw"], A["LOw"], A["ok"], lo_b, hi_b)
        for h in HS:
            rr, gg2, t2 = Z4.response(P, Z, A["rows"], idx, has, side, h)
            m = cell_mask(t2[gg2], Z["i"][gg2], side[gg2])
            lvl_by_h[h].append(rr[gg2][m])

    print(f"  {'h':>3} {'n':>7} {'gross':>8} {'+-':>5} {'SE':>6} {'median':>8} {'win%':>6} "
          f"{'bp/bar':>7} {'LVL':>8} {'gap':>8} {'+-':>5} {'cost':>6} {'cov':>6} {'net':>7}")
    rows = []
    for h in HS:
        rr, gg2, t2 = Z4.response(P, Z, A["rows"], A["idx"], A["has"], Z["side"], h)
        te, ii = t2[gg2], Z["i"][gg2]
        m = cell_mask(te, ii, Z["side"][gg2])
        x = rr[gg2][m]
        if x.size < 2000:
            continue
        se = x.std(ddof=1) / np.sqrt(x.size)
        lv = np.concatenate(lvl_by_h[h])
        lse = lv.std(ddof=1) / np.sqrt(lv.size)
        gap = x.mean() - lv.mean()
        gse = float(np.hypot(se, lse))
        tee, iie = te[m], ii[m]
        txe = np.minimum(tee + h, P["CL"].shape[0] - 1)
        cst = np.nanmedian(0.5 * neutral[tee, iie] + 0.5 * neutral[txe, iie]
                           + IBKR / P["CL"][tee, iie] + IBKR / np.maximum(P["CL"][txe, iie], 1e-9))
        row = dict(h=h, n=int(x.size), gross=float(1e4 * x.mean()), se=float(1e4 * se),
                   t=float(x.mean() / se), median=float(1e4 * np.median(x)),
                   win=float(100 * (x > 0).mean()), per_bar=float(1e4 * x.mean() / h),
                   lvl=float(1e4 * lv.mean()), gap=float(1e4 * gap), gap_se=float(1e4 * gse),
                   cost=float(1e4 * cst), cov=float(x.mean() / cst),
                   net=float(1e4 * (x.mean() - cst)))
        rows.append(row)
        print(f"  {h:3d} {row['n']:7,} {row['gross']:+8.2f} {row['se']:5.2f} {row['t']:+6.1f} "
              f"{row['median']:+8.2f} {row['win']:6.2f} {row['per_bar']:+7.2f} "
              f"{row['lvl']:+8.2f} {row['gap']:+8.2f} {row['gap_se']:5.2f} "
              f"{row['cost']:6.1f} {row['cov']:6.2f} {row['net']:+7.2f}")

    def longest_run(key):
        """The longest run of consecutive NON-INCREASING steps, and where it starts and ends.

        A binary "is it monotone from h=1" is the wrong question and the first version of this
        asked it: past the point where the signal is dead, the series is noise around zero and a
        single upward wobble of a tenth of a basis point -- far inside one SE -- reports the whole
        profile as non-monotone. What matters is whether it decays cleanly WHILE IT IS ALIVE."""
        v = [r[key] for r in rows]
        best = (0, 0, 0)
        i = 0
        while i < len(v) - 1:
            j = i
            while j < len(v) - 1 and v[j] >= v[j + 1]:
                j += 1
            if j - i > best[0]:
                best = (j - i, i, j)
            i = max(j, i + 1)
        return best

    pk = max(rows, key=lambda r: r["gross"])
    pkc = max(rows, key=lambda r: r["cov"])
    print(f"\n  cumulative peaks at h={pk['h']} ({pk['gross']:+.2f} bp); "
          f"coverage peaks at h={pkc['h']} ({pkc['cov']:.2f}x, net {pkc['net']:+.2f} bp)")
    print()
    for key, label in (("per_bar", "per-bar edge"), ("win", "win rate"),
                       ("gap", "the LEVEL's own gap")):
        L, i, j = longest_run(key)
        print(f"  {label:20s} longest monotone DECREASING run: h={rows[i]['h']} -> "
              f"h={rows[j]['h']}  ({L} consecutive steps, {rows[i][key]:+.2f} -> "
              f"{rows[j][key]:+.2f})")
        print(f"  {'':20s} full profile: " + " ".join(f"{r[key]:+.2f}" for r in rows))

    OUT.write_text(json.dumps(dict(exploratory=True, cell="deep.clean.hi", cuts=cuts,
                                   lvl_draws=N_LVL, rows=rows), indent=1, default=float),
                   encoding="utf-8")
    print(f"\n  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()

"""D413 COMBINE -- does the zone carry information the reversal indicators do not?

    uv run python scripts/run_d413_combine.py --run

EXPLORATORY, on data D413 has already spent. Clears nothing, admits nothing. Anything found here
is SELECTED ON SPENT DATA and would need its own pre-registration and an out-of-sample test.

THE PRINCIPAL'S POINT, WHICH IS CORRECT AND WHICH THIS PROGRAMME HAS GOT WRONG BEFORE: two
indicators correlating at 0.8 still leave a quarter of the variance unshared, so "correlated with a
known effect" is not the same as "adds nothing to it". D411 and D413 both treated an overlapping
effect as a CONFOUND TO BE STRIPPED -- residualise it away, standardise it out -- and never asked
the complementary question: does the pair beat either alone?

The counterweight, also from this repo: D268 found NINE price scores collapse to 2.87 effective
independent inputs, with RSI correlating +0.85 with a MACD level. So "there is extra information in
the other indicator" is a hypothesis to measure, not a principle to assume. This file measures it.

THREE INDICATORS, deliberately few, because a grid is a multiplicity machine:
  REV   signed trailing 5-day return at the touch     -- the reversal D413's extras found
  EFF   path efficiency over 10 bars, |net| / sum|steps|  -- direction of travel, NOT its size,
        so it is a genuinely different statistic from REV rather than a rescaling of it
  LIQ   trailing dollar volume                        -- the floor the principal asked about

Each split at its median: eight cells, declared here, and every cell reported whatever it says.
The zone's own contribution in each cell is `real - LVL`, with LVL the width-and-distance-matched
band from D412 -- so this asks whether the LEVEL adds to the pair, not whether the pair works.
"""
import argparse
import importlib.util
import json
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d413", REPO / "scripts" / "run_d413_distance_armed_zones.py")
M = importlib.util.module_from_spec(_s)
sys.modules["d413"] = M
_s.loader.exec_module(M)
Z4, D = M.Z4, M.D
_c = importlib.util.spec_from_file_location("d285cs", REPO / "scripts" / "d285_spread_estimate.py")
CS = importlib.util.module_from_spec(_c)
sys.modules["d285cs"] = CS
_c.loader.exec_module(CS)

OUT = REPO / "data" / "d413_combine.json"
IBKR = 0.0035
EFF_W = 10
N_LVL = 40


def path_efficiency(lg, w=EFF_W):
    """|log P_t - log P_{t-w}| / sum of |daily log steps| over the same window, in [0, 1].

    1.0 is a straight line; near 0 is chop. It carries the SHAPE of the path and not its size,
    which is what makes it a different question from the trailing return."""
    T, n = lg.shape
    step = np.full((T, n), np.nan)
    step[1:] = np.abs(lg[1:] - lg[:-1])
    cs = np.nancumsum(np.nan_to_num(step), axis=0)
    tot = np.full((T, n), np.nan)
    tot[w:] = cs[w:] - cs[:-w]
    net = np.full((T, n), np.nan)
    net[w:] = np.abs(lg[w:] - lg[:-w])
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(tot > 0, net / tot, np.nan)


def run():
    t0 = time.time()
    print("D413 COMBINE -- does the LEVEL add to reversal and path efficiency?\n")
    P = D.load_panel()
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g, tt = A["Z"], A["good"], A["tt"]
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    tr5 = D.trailing_ret(lg, 5)
    eff = path_efficiency(lg)
    DV = D.X.roll_mean_T(P["CL"] * P["VOL"])
    spread = CS.corwin_schultz(P["HI"].T, P["LO"].T, P["live"].T).T

    def feats(idx_arr, has_arr, side_arr, tag):
        rr, gg, t2 = Z4.response(P, Z, A["rows"], idx_arr, has_arr, side_arr, M.H)
        ii = Z["i"][gg]
        te = t2[gg]
        return dict(r=rr[gg], ii=ii, te=te,
                    rev=tr5[te, ii] * side_arr[gg],
                    eff=eff[te, ii], dv=DV[te, ii], px=P["CL"][te, ii])

    R = feats(A["idx"], A["has"], Z["side"], "real")
    fin = np.isfinite(R["rev"]) & np.isfinite(R["eff"]) & np.isfinite(R["dv"])
    R = {k: v[fin] for k, v in R.items()}
    print(f"  real events with all three features: {R['r'].size:,}")
    print(f"  corr(REV, EFF) = {np.corrcoef(R['rev'], R['eff'])[0,1]:+.4f}   "
          f"-- if this were near 1 the pair would be one indicator")

    cuts = dict(rev=float(np.median(R["rev"])), eff=float(np.median(R["eff"])),
                dv=float(np.median(R["dv"])))
    print(f"  medians: REV {1e4*cuts['rev']:+.0f} bp   EFF {cuts['eff']:.3f}   "
          f"DV ${cuts['dv']/1e6:.1f}M")

    # ---- LVL, pooled over draws, with the same features
    rng = np.random.default_rng(5)
    side = Z["side"]
    grp = {s: np.where(side == s)[0] for s in (1, -1)}
    parts = []
    for _ in range(N_LVL):
        w2, d2 = np.empty_like(Z["wid"]), np.empty_like(Z["dist"])
        for s, gg2 in grp.items():
            p = rng.permutation(gg2)
            w2[gg2], d2[gg2] = Z["wid"][p], Z["dist"][p]
        hi_b = np.where(side > 0, Z["Ca"] - d2, Z["Ca"] + d2 + w2)
        lo_b = np.where(side > 0, Z["Ca"] - d2 - w2, Z["Ca"] + d2)
        i2, h2 = Z4.touches(A["HIw"], A["LOw"], A["ok"], lo_b, hi_b)
        parts.append(feats(i2, h2, side, "lvl"))
    L = {k: np.concatenate([p[k] for p in parts]) for k in parts[0]}
    finl = np.isfinite(L["rev"]) & np.isfinite(L["eff"]) & np.isfinite(L["dv"])
    L = {k: v[finl] for k, v in L.items()}

    # The NEUTRAL spread, per take-two: the name's median Corwin-Schultz over the 60 bars ending
    # 2 before entry. Estimating it AT the entry bar reads the event's own volatility -- 2.2x too
    # high, uniformly across price. Both are carried so neither can be chosen after the fact.
    print(f"  building the neutral spread ...", flush=True)
    neutral = np.full_like(spread, np.nan)
    for t in range(62, spread.shape[0]):
        with np.errstate(invalid="ignore"):
            neutral[t] = np.nanmedian(spread[t - 62:t - 2], axis=0)

    def cost_of(d, which):
        s = (spread if which == "event" else neutral)[d["te"], d["ii"]]
        return s + 2 * IBKR / np.maximum(d["px"], 1e-9)

    print(f"\n  --- eight declared cells. gross, the LEVEL's own contribution, and coverage ---")
    print(f"  {'REV':>5} {'EFF':>5} {'LIQ':>5} {'n':>8} {'gross':>8} {'LVL':>8} {'gap':>8} "
          f"{'+-':>6} {'cost':>7} {'cov':>6}")
    rows = []
    for rl in (0, 1):
        for el in (0, 1):
            for ll in (0, 1):
                def sel(d):
                    a = (d["rev"] <= cuts["rev"]) if rl == 0 else (d["rev"] > cuts["rev"])
                    b = (d["eff"] <= cuts["eff"]) if el == 0 else (d["eff"] > cuts["eff"])
                    c = (d["dv"] <= cuts["dv"]) if ll == 0 else (d["dv"] > cuts["dv"])
                    return a & b & c
                mr, ml = sel(R), sel(L)
                if mr.sum() < 1000 or ml.sum() < 1000:
                    continue
                gr = 1e4 * R["r"][mr].mean()
                gl = 1e4 * L["r"][ml].mean()
                se = 1e4 * float(np.hypot(R["r"][mr].std(ddof=1) / np.sqrt(mr.sum()),
                                          L["r"][ml].std(ddof=1) / np.sqrt(ml.sum())))
                sub = {k: v[mr] for k, v in R.items()}
                cev = 1e4 * float(np.nanmedian(cost_of(sub, "event")))
                cnt = 1e4 * float(np.nanmedian(cost_of(sub, "neutral")))
                row = dict(rev="deep" if rl == 0 else "shal", eff="chop" if el == 0 else "clean",
                           liq="lo" if ll == 0 else "hi", n=int(mr.sum()), gross=float(gr),
                           lvl=float(gl), gap=float(gr - gl), se=se,
                           cost_event=cev, cost_neutral=cnt,
                           cov_event=float(gr / cev) if cev > 0 else float("nan"),
                           cov_neutral=float(gr / cnt) if cnt > 0 else float("nan"))
                rows.append(row)
                print(f"  {row['rev']:>5} {row['eff']:>5} {row['liq']:>5} {row['n']:8,} "
                      f"{gr:+8.2f} {gl:+8.2f} {gr-gl:+8.2f} {se:6.2f} {cnt:7.1f} "
                      f"{row['cov_neutral']:6.2f}x")

    best_g = max(rows, key=lambda x: x["gross"])
    best_c = max(rows, key=lambda x: x["cov_neutral"])
    print(f"\n  largest GROSS  : REV={best_g['rev']} EFF={best_g['eff']} LIQ={best_g['liq']}  "
          f"{best_g['gross']:+.2f} bp on {best_g['n']:,}   level's own share {best_g['gap']:+.2f} "
          f"+-{best_g['se']:.2f}")
    print(f"  best COVERAGE  : REV={best_c['rev']} EFF={best_c['eff']} LIQ={best_c['liq']}  "
          f"{best_c['cov_neutral']:.2f}x on the neutral spread "
          f"({best_c['cov_event']:.2f}x on the event-bar one)   "
          f"gross {best_c['gross']:+.2f}  cost {best_c['cost_neutral']:.1f}")

    OUT.write_text(json.dumps(dict(exploratory=True, cuts=cuts, cells=rows,
                                   corr_rev_eff=float(np.corrcoef(R["rev"], R["eff"])[0, 1]),
                                   n_real=int(R["r"].size), n_lvl=int(L["r"].size),
                                   lvl_draws=N_LVL), indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()

"""D413 DIAGNOSTICS -- the trade distribution CLAUDE.md requires, and the two confounds D413 named.

    uv run python scripts/run_d413_diagnostics.py --run

EXPLORATORY. Clears nothing, admits nothing, and does not change D413's verdict (1587f66).
Everything here is measured on data D413 has already spent.

WHY THIS RUNS BEFORE ANY OPTIMISATION. D413 reported a mean and a win rate and nothing else, which
is half of CLAUDE.md's reporting standard: "a number without what makes it interpretable is not a
result." And it named two confounds it did not resolve. Tuning an edge whose controls are unresolved
is tuning noise, so both are settled here first.

  GROUP 2  trade distribution -- count, mean, MEDIAN, win rate, payoff, skew, kurtosis, and the
           mean trimmed 1% from BOTH tails, reported ex-top, ex-bottom and trimmed. Dropping only
           winners is a flag, not a verdict (D307).
  GROUP 3  what the winners depend on -- names to half the P&L, top-name share, per-year, and the
           split on PRICE, which killed D284.

  CONFOUND 1  AGE-MATCHED LVL. D413's control was touched at median age 4 against the real 6, and
              the youngest ages pay -10.63 bp, so LVL's margin is partly an age-mix artefact.
              Fixed by DIRECT STANDARDISATION: LVL's per-age-bin means reweighted to the REAL
              population's age weights.
  CONFOUND 2  REVERSAL. The pooled effect is three-quarters carried by the most-reverted quintile
              of trailing 5-day return. Fixed by standardising LVL JOINTLY on (age x trailing-5d)
              and by asking, WITHIN each reversal bin, whether the real level still beats it.

A double-sort is the honest form of "does the level add anything beyond the move that reached it".
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

OUT = REPO / "data" / "d413_diagnostics.json"
NB = 5
N_LVL = 60


def dist_stats(x):
    x = np.asarray(x, float)
    n = x.size
    lo, hi = np.quantile(x, [0.01, 0.99])
    w, l = x[x > 0], x[x < 0]
    return dict(
        n=int(n), mean=float(x.mean()), median=float(np.median(x)),
        se=float(x.std(ddof=1) / np.sqrt(n)), win=float((x > 0).mean()),
        avg_win=float(w.mean()) if w.size else 0.0,
        avg_loss=float(l.mean()) if l.size else 0.0,
        payoff=float(abs(w.mean() / l.mean())) if l.size and w.size else float("nan"),
        skew=float(((x - x.mean()) ** 3).mean() / x.std() ** 3),
        kurt=float(((x - x.mean()) ** 4).mean() / x.std() ** 4),
        mean_ex_top=float(x[x <= hi].mean()), mean_ex_bottom=float(x[x >= lo].mean()),
        mean_trimmed=float(x[(x >= lo) & (x <= hi)].mean()),
        top1pct_share=float(x[x >= np.quantile(x, .99)].sum() / x.sum()) if x.sum() != 0 else float("nan"))


def binned(v, nb=NB):
    """Quantile bins, with NON-FINITE VALUES EXCLUDED (bin -1) rather than swept into bin 0.

    The first version of this took np.quantile over an array carrying NaNs from the early bars.
    Every edge came back NaN, searchsorted then returned 0 for everything, and the clip turned
    that into "all 180,050 events are in bin 1" -- which printed as a one-row table and would
    have been reported as a reversal control that controlled for nothing."""
    fin = np.isfinite(v)
    q = np.quantile(v[fin], np.linspace(0, 1, nb + 1))
    q[-1] += 1e-12
    b = np.full(v.shape, -1, int)
    b[fin] = np.clip(np.searchsorted(q, v[fin], side="right") - 1, 0, nb - 1)
    return b, q


def apply_bins(v, q, nb=NB):
    fin = np.isfinite(v)
    b = np.full(v.shape, -1, int)
    b[fin] = np.clip(np.searchsorted(q, v[fin], side="right") - 1, 0, nb - 1)
    return b


def standardise(ctrl_vals, ctrl_bins, real_w, nb):
    """Direct standardisation: the control's per-bin mean, reweighted to the REAL population's bin
    weights. This is the fix for a control whose event population differs from the treatment's."""
    out, tot = 0.0, 0.0
    for j in range(nb):
        m = ctrl_bins == j
        if m.sum() < 50 or real_w[j] <= 0:
            continue
        out += real_w[j] * ctrl_vals[m].mean()
        tot += real_w[j]
    return out / tot if tot > 0 else float("nan")


def run():
    t0 = time.time()
    print("D413 DIAGNOSTICS -- exploratory, clears nothing, changes no verdict\n")
    P = D.load_panel()
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g, tt = A["Z"], A["good"], A["tt"]
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    tr5 = D.trailing_ret(lg, 5)

    r = A["r"][g]
    age = (A["idx"] + 1)[g].astype(float)
    ii = Z["i"][g]
    tg = tt[g]
    rev = tr5[tg, ii] * Z["side"][g]
    px = P["CL"][tg, ii]
    yr = np.array([int(P["dates"][t][:4]) for t in tg])
    res = {}

    # ---------------- GROUP 2
    st = dist_stats(r)
    res["distribution"] = st
    print("  --- GROUP 2: the trade distribution ---")
    print(f"  n {st['n']:,}   mean {1e4*st['mean']:+7.2f} bp +-{1e4*st['se']:.2f}   "
          f"MEDIAN {1e4*st['median']:+7.2f} bp   win {100*st['win']:.2f}%")
    print(f"  avg win {1e4*st['avg_win']:+7.2f}   avg loss {1e4*st['avg_loss']:+7.2f}   "
          f"payoff {st['payoff']:.3f}")
    print(f"  skew {st['skew']:+.2f}   kurtosis {st['kurt']:.1f}   "
          f"top 1% share of P&L {100*st['top1pct_share']:.1f}%")
    print(f"  mean ex-top1% {1e4*st['mean_ex_top']:+7.2f}   ex-bottom1% "
          f"{1e4*st['mean_ex_bottom']:+7.2f}   BOTH trimmed {1e4*st['mean_trimmed']:+7.2f} bp")
    print(f"  -> a mean {'ABOVE' if st['mean'] > st['median'] else 'BELOW'} its median: "
          f"{'the right tail is doing the work' if st['mean'] > st['median'] else 'the LEFT tail is doing the work (D285 tell)'}")

    # ---------------- GROUP 3
    print("\n  --- GROUP 3: what the winners depend on ---")
    syms = np.array(P["symbols"])[ii]
    tot = r.sum()
    bysym = {}
    for s, v in zip(syms, r):
        bysym[s] = bysym.get(s, 0.0) + v
    vals = np.sort(np.array(list(bysym.values())))[::-1]
    csum = np.cumsum(vals)
    half = int(np.searchsorted(csum, 0.5 * tot) + 1) if tot > 0 else -1
    res["concentration"] = dict(names=len(bysym), names_to_half=half,
                                top1=float(vals[0] / tot), top5=float(vals[:5].sum() / tot),
                                top10=float(vals[:10].sum() / tot))
    print(f"  {len(bysym)} names; {half} names reach half the P&L; "
          f"top1 {100*vals[0]/tot:.1f}%  top5 {100*vals[:5].sum()/tot:.1f}%  "
          f"top10 {100*vals[:10].sum()/tot:.1f}%")
    years = sorted(set(yr.tolist()))
    ym = {int(y): float(r[yr == y].mean()) for y in years}
    res["by_year"] = ym
    print("  by year (bp): " + "  ".join(f"{y}:{1e4*v:+.0f}" for y, v in ym.items()))
    print(f"  profitable years: {sum(1 for v in ym.values() if v > 0)} of {len(ym)}")
    pb, _ = binned(px, 5)
    res["by_price"] = [dict(n=int((pb == j).sum()), px=float(np.median(px[pb == j])),
                            mean=float(r[pb == j].mean())) for j in range(5)]
    print("  by PRICE quintile (killed D284): " +
          "  ".join(f"${x['px']:.0f}:{1e4*x['mean']:+.1f}" for x in res["by_price"]))

    # ---------------- horizon scan
    print("\n  --- where the edge lives in HOLDING TIME (exploratory) ---")
    hs = {}
    for h in (1, 2, 3, 4, 5, 8, 10, 15, 21):
        rr, gg, _ = Z4.response(P, Z, A["rows"], A["idx"], A["has"], Z["side"], h)
        x = rr[gg]
        hs[h] = dict(n=int(x.size), mean=float(x.mean()),
                     se=float(x.std(ddof=1) / np.sqrt(x.size)), win=float((x > 0).mean()))
        print(f"  h={h:2d}   mean {1e4*hs[h]['mean']:+7.2f} +-{1e4*hs[h]['se']:.2f} bp   "
              f"{hs[h]['mean']/hs[h]['se']:+5.1f} SE   win {100*hs[h]['win']:.2f}%")
    res["by_horizon"] = hs

    # ---------------- the two confounds
    print("\n  --- CONFOUND 1 and 2: LVL standardised on AGE, and on AGE x REVERSAL ---")
    ab, _ = binned(age)
    rb, _ = binned(rev)
    wa = np.array([(ab == j).mean() for j in range(NB)])
    joint_w = np.zeros((NB, NB))
    for j in range(NB):
        for k in range(NB):
            joint_w[j, k] = ((ab == j) & (rb == k)).mean()

    rng = np.random.default_rng(5)
    side = Z["side"]
    grp = {s: np.where(side == s)[0] for s in (1, -1)}
    cr, ca, cv = [], [], []
    for _ in range(N_LVL):
        w2, d2 = np.empty_like(Z["wid"]), np.empty_like(Z["dist"])
        for s, gg in grp.items():
            p = rng.permutation(gg)
            w2[gg], d2[gg] = Z["wid"][p], Z["dist"][p]
        hi_b = np.where(side > 0, Z["Ca"] - d2, Z["Ca"] + d2 + w2)
        lo_b = np.where(side > 0, Z["Ca"] - d2 - w2, Z["Ca"] + d2)
        idx, has = Z4.touches(A["HIw"], A["LOw"], A["ok"], lo_b, hi_b)
        rr, gg2, tt2 = Z4.response(P, Z, A["rows"], idx, has, side, M.H)
        cr.append(rr[gg2])
        ca.append((idx + 1)[gg2].astype(float))
        cv.append(tr5[tt2[gg2], Z["i"][gg2]] * side[gg2])
    cr, ca, cv = np.concatenate(cr), np.concatenate(ca), np.concatenate(cv)
    _, qa = binned(age)
    _, qv = binned(rev)
    cab = apply_bins(ca, qa)
    cvb = apply_bins(cv, qv)
    print(f"  control bin occupancy, reversal: "
          + " ".join(f"{100*np.mean(cvb == k):.1f}%" for k in range(NB))
          + f"   (excluded {100*np.mean(cvb < 0):.1f}%)")
    print(f"  real    bin occupancy, reversal: "
          + " ".join(f"{100*np.mean(rb == k):.1f}%" for k in range(NB))
          + f"   (excluded {100*np.mean(rb < 0):.1f}%)")

    raw = float(cr.mean())
    std_age = standardise(cr, cab, wa, NB)
    num = den = 0.0
    for j in range(NB):
        for k in range(NB):
            m = (cab == j) & (cvb == k)
            if m.sum() >= 50 and joint_w[j, k] > 0:
                num += joint_w[j, k] * cr[m].mean()
                den += joint_w[j, k]
    std_joint = num / den if den > 0 else float("nan")
    res["lvl"] = dict(raw=raw, standardised_age=std_age, standardised_joint=std_joint,
                      observed=float(r.mean()), draws=N_LVL)
    print(f"  real                                   {1e4*r.mean():+7.2f} bp")
    print(f"  LVL raw (D413's T2 comparison)         {1e4*raw:+7.2f} bp   "
          f"gap {1e4*(r.mean()-raw):+7.2f}")
    print(f"  LVL standardised on AGE                {1e4*std_age:+7.2f} bp   "
          f"gap {1e4*(r.mean()-std_age):+7.2f}")
    print(f"  LVL standardised on AGE x REVERSAL     {1e4*std_joint:+7.2f} bp   "
          f"gap {1e4*(r.mean()-std_joint):+7.2f}")

    print("\n  --- does the LEVEL beat a matched band WITHIN each reversal bin? ---")
    within = []
    for k in range(NB):
        mr = rb == k
        mc = cvb == k
        if mr.sum() < 200 or mc.sum() < 200:
            continue
        a_, b_ = r[mr], cr[mc]
        se = float(np.hypot(a_.std(ddof=1) / np.sqrt(a_.size), b_.std(ddof=1) / np.sqrt(b_.size)))
        within.append(dict(bin=k + 1, n_real=int(mr.sum()), real=float(a_.mean()),
                           lvl=float(b_.mean()), gap=float(a_.mean() - b_.mean()), se=se))
        w = within[-1]
        print(f"   rev bin {k+1}  real {1e4*w['real']:+7.2f}   LVL {1e4*w['lvl']:+7.2f}   "
              f"gap {1e4*w['gap']:+7.2f} +-{1e4*w['se']:.2f}  ({w['gap']/w['se']:+.1f} SE)")
    res["within_reversal"] = within
    nsig = sum(1 for w in within if w["gap"] > 2 * w["se"])
    print(f"  bins where the level beats its matched band by more than 2 SE: {nsig} of "
          f"{len(within)}")

    OUT.write_text(json.dumps(dict(exploratory=True, **res), indent=1, default=float),
                   encoding="utf-8")
    print(f"\n  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run()

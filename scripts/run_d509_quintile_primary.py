"""D509 -- the stretch ranker re-scored on an ECONOMIC primary: top-minus-bottom quintile in dollars per session.
Primary: Delta = mean net $/session in the top quintile of |log(P/SMA200)| minus the bottom. Null: the exact enumerated rotation of the
conditioner, which SUBSUMES D508's hand-built run-length-matched gate (a rotated conditioner is a persistent gate of identical duty cycle
and identical run-length distribution). Plus a four-cell family maximum, the within-year decomposition, and a tie control.
The arm and the conditioner are imported from D508/D504/D491 -- nothing is re-implemented. Spec committed in 4a138f4 BEFORE this file.

    uv run python -u scripts/run_d509_quintile_primary.py --run
    uv run python -u scripts/run_d509_quintile_primary.py --selftest
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
OUT = REPO / "data" / "d509_quintile_primary.json"; SPEC = "4a138f4"


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m


D508 = _load("d508c", "run_d508_stretch_ranker.py")
LO, HI, N_Q = D508.LO, D508.HI, D508.N_Q


# ------------------------------------------------------------------------------------------ the primary
def qdiff(cond, net, n_q=N_Q):
    """Top-minus-bottom quintile of net $ per session. Returns (delta, top_mean, bot_mean, n_top, n_bot)."""
    m = np.isfinite(cond) & np.isfinite(net)
    if m.sum() < 5 * n_q:
        return (np.nan,) * 5
    c = cond[m]; y = net[m]
    q = pd.qcut(c, n_q, labels=False, duplicates="drop")
    if q.max() != n_q - 1:
        return (np.nan,) * 5
    top = y[q == n_q - 1]; bot = y[q == 0]
    return float(top.mean() - bot.mean()), float(top.mean()), float(bot.mean()), int(top.size), int(bot.size)


def rotation_qdiff(cond, net, n_q=N_Q, d_max=None):
    """Exact enumerated rotation of the CONDITIONER against the arm's P&L, recomputing the quintile difference at every offset.
    A rotated conditioner keeps its run-length distribution and its duty cycle exactly, so this null already contains the
    persistent-gate control D508 had to build by hand."""
    m = np.isfinite(cond) & np.isfinite(net); c = cond[m]; y = net[m]; T = len(c)
    D = T - 1 if d_max is None else min(d_max, T - 1); out = np.full(D, np.nan)
    for k in range(1, D + 1):
        ck = np.roll(c, k); q = pd.qcut(ck, n_q, labels=False, duplicates="drop")
        if q.max() != n_q - 1:
            continue
        out[k - 1] = float(y[q == n_q - 1].mean() - y[q == 0].mean())
    return out


def rotation_slow(cond, net, k, n_q=N_Q):
    m = np.isfinite(cond) & np.isfinite(net); c = cond[m]; y = net[m]; T = len(c)
    ck = np.array([c[(i - k) % T] for i in range(T)])
    q = pd.qcut(ck, n_q, labels=False, duplicates="drop")
    return float(y[q == n_q - 1].mean() - y[q == 0].mean())


def rank_corr_small(x, y):
    """Spearman on a handful of points. D508's version guards for n >= 30 because it scores session series; a quintile table has five rows,
    so that guard returns NaN and the monotonicity check silently reports nothing. D508's version also divides the covariance by n while
    dividing the standard deviations by n-1, so it is short by a factor (n-1)/n -- 0.05% at n = 1,876 and therefore invisible in D508's
    numbers, but 20% at the five points of a quintile table. This uses ddof=0 throughout."""
    a = pd.Series(np.asarray(x, float)).rank().to_numpy(); b = pd.Series(np.asarray(y, float)).rank().to_numpy()
    sa, sb = a.std(ddof=0), b.std(ddof=0)
    return float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb)) if sa > 0 and sb > 0 else float("nan")


def runlengths(mask):
    """The multiset of run lengths of a boolean mask -- used to prove rotation preserves persistence."""
    out = []; i = 0
    while i < len(mask):
        j = i
        while j < len(mask) and mask[j] == mask[i]:
            j += 1
        out.append((bool(mask[i]), j - i)); i = j
    return out


# ------------------------------------------------------------------------------------------ run
def run():
    t0 = time.time(); print(f"D509 -- the stretch ranker on an economic primary\n      spec committed in {SPEC} BEFORE this ran; {LO}..{HI}; the arm's 2024+ slice is SPENT and is not scored")
    a = D508.load_arm(); days, net, gross, trips = a["days"], a["net"], a["gross"], a["trips"]
    pub = json.loads((REPO / "data" / "d504_arm_full_history.json").read_text())["per_year"]
    want_n = sum(pub[y]["n_sessions"] for y in pub if LO[:4] <= y <= HI[:4])
    want_tot = sum(pub[y]["total_usd"] for y in pub if LO[:4] <= y <= HI[:4])
    assert len(days) == want_n and abs(float(net.sum()) - want_tot) < 1.0, "the imported arm does not reproduce D504"
    print(f"  arm reproduced: {len(days):,} sessions, ${net.sum():,.0f} (D504 publishes {want_n:,}, ${want_tot:,.0f})")
    cond = {}
    for kind in ("sma", "ema"):
        ab, sg = D508.stretch(a["level_all"], kind)
        cond[f"{kind}_abs"] = ab[a["mask"]]; cond[f"{kind}_signed"] = sg[a["mask"]]
    res = dict(spec="D509", commit=SPEC, lo=LO, hi=HI, sessions=int(len(days)), cells={})
    print(f"\n  {'cell':12s} {'Delta $':>8s} {'top $':>7s} {'bot $':>7s} {'N1 p05':>7s} {'N1 p50':>7s} {'N1 p95':>7s} {'pct':>6s} {'clears':>7s}")
    paths = {}
    for k in ("sma_abs", "ema_abs", "sma_signed", "ema_signed"):
        d, tm, bm, nt, nb = qdiff(cond[k], net); path = rotation_qdiff(cond[k], net); path = path[np.isfinite(path)]; paths[k] = path
        p05, p50, p95 = (float(np.quantile(path, q)) for q in (.05, .50, .95)); pct = float((path <= d).mean())
        res["cells"][k] = dict(delta=d, top_mean=tm, bot_mean=bm, n_top=nt, n_bot=nb, p05=p05, p50=p50, p95=p95,
                               percentile=pct, share_ge=float((path >= d).mean()), clears=bool(d > p95), n_offsets=int(path.size))
        print(f"  {k:12s} {d:+8.2f} {tm:+7.2f} {bm:+7.2f} {p05:+7.2f} {p50:+7.2f} {p95:+7.2f} {100*pct:5.1f}% {str(bool(d > p95)):>7s}")
    D = min(len(v) for v in paths.values()); fam = np.nanmax(np.column_stack([v[:D] for v in paths.values()]), axis=1)
    obs = {k: res["cells"][k]["delta"] for k in paths}; best = max(obs, key=obs.get)
    res["family"] = dict(n_cells=4, n_offsets=int(D), p50=float(np.median(fam)), p95=float(np.quantile(fam, .95)),
                         observed_max=obs[best], observed_argmax=best, share_ge=float((fam >= obs[best]).mean()))
    f = res["family"]; print(f"\n  N2 FAMILY MAXIMUM over 4 cells, {f['n_offsets']:,} common offsets (exact): p50 {f['p50']:+.2f}  p95 {f['p95']:+.2f}   observed max {f['observed_max']:+.2f} ({f['observed_argmax']}); share of offsets >= observed {100*f['share_ge']:.1f}%")
    print(f"  single-cell p95 {res['cells']['sma_abs']['p95']:+.2f} -> family p95 {f['p95']:+.2f}  (ratio {f['p95']/res['cells']['sma_abs']['p95']:.2f}x)")
    # the quintile shape, and whether it is monotone
    Q = D508.quintiles(cond["sma_abs"], net, gross, trips, days); res["quintiles"] = Q.to_dict("records")
    mono = rank_corr_small(Q.quintile.to_numpy(float), Q.net_mean.to_numpy())
    res["monotonicity"] = dict(spearman_index_vs_mean=mono, q1_beats_q2=bool(Q.iloc[0].net_mean > Q.iloc[1].net_mean),
                               q1_beats_q3=bool(Q.iloc[0].net_mean > Q.iloc[2].net_mean))
    print(f"\n  QUINTILE SHAPE (net $/session): " + "  ".join(f"q{int(r.quintile)} {r.net_mean:+.2f}" for r in Q.itertuples()) +
          f"   monotonicity (index vs mean) {mono:+.2f}; q1 beats q2 {res['monotonicity']['q1_beats_q2']}, q1 beats q3 {res['monotonicity']['q1_beats_q3']}")
    # N3 within-year
    yrs = np.array([t[:4] for t in days]); wy = {}
    for y in sorted(set(yrs)):
        s = yrs == y
        if s.sum() > 100:
            wy[y] = qdiff(cond["sma_abs"][s], net[s])[0]
    vals = [v for v in wy.values() if np.isfinite(v)]
    res["n3_within_year"] = dict(by_year=wy, mean=float(np.mean(vals)), n_negative=int(sum(v < 0 for v in vals)), n_years=len(vals))
    print(f"\n  N3 WITHIN-YEAR Delta ($/session): " + "  ".join(f"{y}:{v:+.1f}" for y, v in wy.items()) +
          f"\n     mean {res['n3_within_year']['mean']:+.2f}  negative in {res['n3_within_year']['n_negative']} of {res['n3_within_year']['n_years']} years  vs pooled {res['cells']['sma_abs']['delta']:+.2f}")
    # N4 tie control: traded sessions only
    traded = trips > 0
    dt, tt, bt, _, _ = qdiff(cond["sma_abs"][traded], net[traded])
    pt = rotation_qdiff(cond["sma_abs"][traded], net[traded]); pt = pt[np.isfinite(pt)]
    res["n4_traded_only"] = dict(n=int(traded.sum()), n_untraded=int((~traded).sum()), delta=dt, top_mean=tt, bot_mean=bt,
                                 p95=float(np.quantile(pt, .95)), percentile=float((pt <= dt).mean()), clears=bool(dt > float(np.quantile(pt, .95))))
    r4 = res["n4_traded_only"]
    print(f"\n  N4 TIE CONTROL -- traded sessions only ({r4['n']:,} of {len(days):,}; {r4['n_untraded']} untraded at exactly $0):")
    print(f"     Delta {dt:+.2f} (top {tt:+.2f}, bottom {bt:+.2f}) against its own rotation p95 {r4['p95']:+.2f} -- {100*r4['percentile']:.1f}th percentile, clears {r4['clears']}")
    print(f"     all-sessions Delta {res['cells']['sma_abs']['delta']:+.2f}; the tie block moves it by {100*abs(dt - res['cells']['sma_abs']['delta'])/abs(res['cells']['sma_abs']['delta']):.0f}%")
    # [PROOF] rotation preserves the persistence structure D508 had to match by hand
    thr = float(Q.iloc[-1].cond_lo); m = np.isfinite(cond["sma_abs"])
    on = cond["sma_abs"][m] >= thr; on_rot = np.roll(cond["sma_abs"][m], 137) >= thr
    rl_a = sorted(L for v, L in runlengths(on) if v); rl_b = sorted(L for v, L in runlengths(on_rot) if v)
    res["rotation_preserves_persistence"] = dict(duty_observed=float(on.mean()), duty_rotated=float(on_rot.mean()),
                                                 runs_observed=len(rl_a), runs_rotated=len(rl_b), identical_multiset=bool(rl_a == rl_b))
    rp = res["rotation_preserves_persistence"]
    print(f"\n  [PROOF] a rotated conditioner IS a matched persistent gate: duty {100*rp['duty_observed']:.1f}% -> {100*rp['duty_rotated']:.1f}%, "
          f"{rp['runs_observed']} runs -> {rp['runs_rotated']}, run-length multiset identical {rp['identical_multiset']} (a wrap can split one run)")
    p = res["cells"]["sma_abs"]
    verdict = "PROCEED" if (p["clears"] and p["delta"] > f["p95"] and res["n3_within_year"]["mean"] > 0 and r4["clears"]) else ("PICK" if p["clears"] else "CLOSE")
    res["verdict"] = verdict
    res["decision_terms"] = dict(n1=p["clears"], family=bool(p["delta"] > f["p95"]), within_year=bool(res["n3_within_year"]["mean"] > 0), tie_control=r4["clears"])
    print(f"\n  VERDICT (pre-registered rule): {verdict}   terms {res['decision_terms']}")
    print("\nPREDICTIONS")
    print(f"  X-a observed Delta +13.82 +- 0.05, reproducing D508's table                          : {p['delta']:+.2f}")
    print(f"  X-b N1 p50 within +-$3 and p95 in [+12, +28]; Delta at the 70th-92nd pct, not clearing: p50 {p['p50']:+.2f} p95 {p['p95']:+.2f}; {100*p['percentile']:.1f}th pct; clears {p['clears']}")
    print(f"  X-c family p95 at least 1.3x the single-cell p95, observed max does not clear        : {f['p95']/p['p95']:.2f}x; max {f['observed_max']:+.2f} vs p95 {f['p95']:+.2f}")
    print(f"  X-d within-year mean below +$6 and negative in >= 4 of 8 years                        : mean {res['n3_within_year']['mean']:+.2f}; negative in {res['n3_within_year']['n_negative']} of {res['n3_within_year']['n_years']}")
    print(f"  X-e traded-only Delta within 25% of the all-sessions Delta                            : {100*abs(dt - p['delta'])/abs(p['delta']):.0f}%")
    print(f"  X-f the quintile means are NOT monotone (index-vs-mean Spearman < +0.8; q1 > q2, q3)  : {mono:+.2f}; q1>q2 {res['monotonicity']['q1_beats_q2']}, q1>q3 {res['monotonicity']['q1_beats_q3']}")
    print(f"  X-g the verdict is CLOSE                                                              : {verdict}")
    OUT.write_text(json.dumps(res, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    print("D509 selftest")
    rng = np.random.default_rng(12); n = 1500
    c = np.abs(np.cumsum(rng.normal(0, .02, n)))                       # a persistent, right-skewed conditioner
    noise = rng.normal(0, 100, n)
    # [A] the primary is exactly the difference of the two extreme quintile means
    d, tm, bm, nt, nb = qdiff(c, noise); assert abs(d - (tm - bm)) < 1e-12 and nt > 250 and nb > 250
    # [B] a planted step shows up at the declared size, and flipping the conditioner flips the sign
    planted = noise + np.where(c >= np.quantile(c, 0.8), 300.0, 0.0)
    dp = qdiff(c, planted)[0]; assert 250 < dp < 350, dp
    dn = qdiff(-c, planted)[0]; assert dn < -100, dn
    # [C] the rotation is exact against an explicit loop
    path = rotation_qdiff(c, planted, d_max=30)
    for k in (1, 7, 23):
        assert abs(rotation_slow(c, planted, k) - path[k - 1]) < 1e-9, (k, rotation_slow(c, planted, k), path[k - 1])
    # [D] the null is centred near zero on an unrelated outcome, and the planted case clears it
    pn = rotation_qdiff(c, noise); pn = pn[np.isfinite(pn)]
    assert abs(np.median(pn)) < 25, float(np.median(pn))
    pp = rotation_qdiff(c, planted); pp = pp[np.isfinite(pp)]
    assert (pp >= dp).mean() < 0.02, float((pp >= dp).mean())
    # and it can FAIL: an unplanted observation does not clear its own null in the typical case
    shares = []
    for sd in (1, 2, 3, 4, 5):
        r2 = np.random.default_rng(sd); cc = np.abs(np.cumsum(r2.normal(0, .02, n))); yy = r2.normal(0, 100, n)
        pth = rotation_qdiff(cc, yy); pth = pth[np.isfinite(pth)]; shares.append(float((pth >= qdiff(cc, yy)[0]).mean()))
    assert np.median(shares) > 0.15 and sum(s < 0.05 for s in shares) <= 1, shares
    # [E] THE CLAIM THIS RECORD RESTS ON: a rotated conditioner keeps duty cycle and run lengths
    thr = float(np.quantile(c, 0.8)); on = c >= thr
    for k in (1, 50, 613):
        rot = np.roll(c, k) >= thr
        assert abs(on.mean() - rot.mean()) < 1e-12, (k, on.mean(), rot.mean())
        a_runs = sorted(L for v, L in runlengths(on) if v); b_runs = sorted(L for v, L in runlengths(rot) if v)
        assert abs(sum(a_runs) - sum(b_runs)) < 1e-9 and abs(len(a_runs) - len(b_runs)) <= 1, (k, len(a_runs), len(b_runs))
    # [F2] the small-sample rank correlation works where D508 s guard returns NaN
    assert abs(rank_corr_small([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]) - 1.0) < 1e-12
    assert abs(rank_corr_small([1, 2, 3, 4, 5], [5, 4, 3, 2, 1]) + 1.0) < 1e-12
    assert not np.isfinite(D508.spearman(np.arange(5.0), np.arange(5.0))), "D508 s guard should refuse 5 points"
    # [F] the tie block dilutes a rank statistic but not this one
    tied = planted.copy(); tied[rng.random(n) < 0.3] = 0.0
    assert abs(qdiff(c, tied)[0]) > 0.5 * abs(dp), (qdiff(c, tied)[0], dp)
    print(f"  A primary is the quintile difference  B planted step recovered ({dp:+.0f}) and flips ({dn:+.0f})  C exact rotation"
          f"  D null centred at {np.median(pn):+.1f}, planted clears, unplanted typically does not (shares {[round(s,2) for s in shares]})"
          f"  E rotation preserves duty and run lengths  F tie block does not break the statistic  F2 small-sample rank correlation\n  all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.run:
        run()
    if not (a.run or a.selftest):
        ap.print_help()

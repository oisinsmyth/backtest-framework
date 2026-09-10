"""D432 -- three mechanisms on the union, both lenses. Bar committed in f84bf33 BEFORE this file.
M1 breadth gate on the long arm (cut 58, frozen); M2 DV terciles inside cell 2; M3 the gap by half.
All data spent; no fixture opened (both panels from caches); holdout2 untouched.

usage:  uv run python -u scripts/run_d432_mechanisms.py --run
"""
import argparse, importlib.util, json, pathlib, sys, time
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
R31 = _load("d431r", "run_d431_shorts_union.py"); R30 = R31.R30; R28 = R31.R28
sim4, dist, show, concentration, with_borrow, union = R28.sim4, R28.dist, R28.show, R28.concentration, R28.with_borrow, R31.union

OUT = REPO / "data" / "d432_mechanisms.json"
HOLD, SEEDS, N3, N10 = 5, (419, 4190, 41900), 3, 10
BREADTH_CUT = 58            # the union's trailing-5 cell-2 long-breadth p90, frozen (pre-registration §1)
B1 = 0.01


def breadth5(t, mask, T):
    """Trailing 5-day sum (days d-4..d) of cell-2 long touches; the value on day d is known at d's close."""
    bl = np.bincount(t[mask], minlength=T).astype(float)
    return np.convolve(bl, np.ones(5), "full")[:T]


def paired_gate(r, kept, excl):
    a, b = r[kept], r[excl]; a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    d = a.mean() - b.mean(); se = float(np.hypot(a.std(ddof=1) / np.sqrt(a.size), b.std(ddof=1) / np.sqrt(max(b.size, 2))))
    return dict(kept_n=int(a.size), excl_n=int(b.size), kept_bp=float(1e4 * a.mean()), excl_bp=float(1e4 * b.mean()), diff_bp=float(1e4 * d), se_bp=float(1e4 * se), t=float(d / se) if se > 0 else float("nan"))


def rotation_null(b5, t, r, pool, T, cut):
    """Enumerated: every circular offset of the breadth series; statistic = kept - excluded mean on the pool. Exact p95."""
    m = pool & np.isfinite(r); td = t[m]; rr = r[m]
    S = np.bincount(td, weights=rr, minlength=T); C = np.bincount(td, minlength=T).astype(float)
    high = b5 > cut; draws = np.empty(T)
    for k in range(T):
        h = np.roll(high, k)
        sh, ch = S[h].sum(), C[h].sum(); sl, cl = S[~h].sum(), C[~h].sum()
        draws[k] = (sl / cl if cl > 0 else np.nan) - (sh / ch if ch > 0 else np.nan)
    return draws


def run():
    t0 = time.time()
    print("D432  three mechanisms on the union -- breadth gate, DV lever, gap by half\n      the bar was committed in f84bf33 BEFORE this ran; all data spent; nothing opened\n")
    Bw = _load("d419w", "run_d419_book.py"); FL = _load("d422f", "d422_stack_flags.py"); RF = _load("d426f", "d426_rung_flags.py")
    D = Bw.D
    Pa = D.load_panel(verbose=False); Pb = R30.load_panel_from(D, R30.HOLDOUT_FIX, R30.HOLDOUT_EVJ, R30.HOLDOUT_CACHE, verbose=False)
    Ia, fla, Fa, Xa, _ = R30.pipeline(Bw, FL, RF, Pa); Ib, flb, Fb, Xb, _ = R30.pipeline(Bw, FL, RF, Pb)
    DVa = D.X.roll_mean_T(Pa["CL"] * Pa["VOL"])[Ia["t"], Ia["i"]]; DVb = D.X.roll_mean_T(Pb["CL"] * Pb["VOL"])[Ib["t"], Ib["i"]]
    I, is_b = union(Ia, Ib); dv = np.concatenate([DVa, DVb])
    N = len(I["t"]); T = int(I["T"][0]); t, i, side, E, c2, rb, cost = I["t"], I["i"], I["side"], I["E"], I["c2"], I["r_base"], I["cost"]
    SYM = I["symbols"]; dates = I["dates"]; yr = np.array([int(str(x)[:4]) for x in dates[t]])
    cat = lambda k: np.concatenate([Xa[k], Xb[k]])
    R2, L1 = cat("R2"), cat("L1"); full = L1 & (E < R30.PRICE_CUT); long_ = full & (side > 0); short = full & (side < 0)
    gap = np.concatenate([Fa["prev_gap"], Fb["prev_gap"]])
    b5 = breadth5(t, c2 & (side > 0), T); high = b5[t] > BREADTH_CUT
    assert (int(long_.sum()), int(short.sum())) == (2083, 1783) and abs(100 * high[long_].mean() - 26.6) < 0.2 and abs(100 * high[short].mean() - 3.4) < 0.2, "[STAGE0]"
    # [GATE] causal: recomputing the breadth with touches shifted one day later must change the gate on some events
    b5s = np.convolve(np.bincount(np.minimum(t[c2 & (side > 0)] + 1, T - 1), minlength=T).astype(float), np.ones(5), "full")[:T]
    assert np.any((b5s[t] > BREADTH_CUT) != high), "[GATE] the breadth series is insensitive to the touch dates"
    assert np.all(b5[5:] == np.array([np.bincount(t[c2 & (side > 0)], minlength=T)[d - 4:d + 1].sum() for d in range(5, T)])), "[GATE] trailing window is not d-4..d"
    print(f"  [STAGE0] 2,083 / 1,783; gate share long {100*high[long_].mean():.1f}% short {100*high[short].mean():.1f}%;  [GATE] causal trailing-5 window, shifted dates move it")
    I1 = with_borrow(I, B1); nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan)
    d31 = json.loads((REPO / "data" / "d431_shorts_union.json").read_text(encoding="utf-8"))
    prio_s = short & np.concatenate([Fa["opp_prior"], Fb["opp_prior"]]) & (gap >= 3) & (gap <= 10)
    for seed in SEEDS:
        S = Bw.score(I1, sim4(I1, N3, seed, nan1, nan2, short, prio=prio_s), N3); r = d31["books"][f"PRIO_N3_s{seed}"]
        assert abs(S["net_bp"] - r["net_bp"]) < 1e-12 and S["trades"] == r["trades"], f"[P2] D431 seed {seed}"
    print("  [P2]   the union pipeline reproduces D431's short N=3 book on every seed")
    res = dict(m1={}, m2={}, m3={}, books={}, se={}, rot=None, bar={})
    halves = [("union", np.ones(N, bool)), ("in-sample half", ~is_b), ("holdout half", is_b)]
    wins = [("pooled", np.ones(N, bool)), ("2018+", yr >= 2018), ("2021-2026", yr >= 2021)]

    print("\n1. M1 -- the breadth gate on the long arm (kept = breadth <= 58; excluded = above)")
    for hl, hm in halves:
        for wl, wm in wins:
            g = paired_gate(rb, long_ & ~high & hm & wm, long_ & high & hm & wm); res["m1"][f"long|{hl}|{wl}"] = g
            if wl == "pooled" or hl == "holdout half":
                print(f"  LONG  {hl:15s} {wl:10s} kept n {g['kept_n']:5,} {g['kept_bp']:+8.2f}   excluded n {g['excl_n']:4,} {g['excl_bp']:+8.2f}   kept - excluded {g['diff_bp']:+8.2f} ± {g['se_bp']:.2f}  ({g['t']:+.1f} SE)")
        print()
    for hl, hm in halves:
        g = paired_gate(rb, short & ~high & hm, short & high & hm); res["m1"][f"short|{hl}|pooled"] = g
        print(f"  SHORT {hl:15s} pooled     kept n {g['kept_n']:5,} {g['kept_bp']:+8.2f}   excluded n {g['excl_n']:4,} {g['excl_bp']:+8.2f}   kept - excluded {g['diff_bp']:+8.2f} ± {g['se_bp']:.2f}")
    print("\n  the gated long pool, per trade (D422's table):")
    for hl, hm in halves:
        for wl, wm in wins:
            d = dist(rb, cost, long_ & ~high & hm & wm, f"gated long  {hl}  {wl}"); res["m1"][f"table|{hl}|{wl}"] = d
            if wl == "pooled" or hl == "holdout half": show(d)
    dh = dist(rb, cost, long_ & ~high & is_b, "gated long  holdout half  pooled")
    print("  the excluded long trades by year on the holdout half: " + "  ".join(f"{y}:{1e4*np.nanmean(rb[long_ & high & is_b & (yr == y)]):+.0f}({int((long_ & high & is_b & (yr == y)).sum())})" for y in range(2010, 2027) if (long_ & high & is_b & (yr == y)).any()))
    qh = concentration(rb, i, yr, long_ & ~high & is_b, SYM); res["m1"]["conc_holdout_gated"] = qh
    print(f"  gated long, holdout half: names {qh['names']}  to half P&L {qh['to_half']}  top1 {qh['top1']:.1f}%  years + {qh['years_pos']}/{qh['years']}  top name {qh['top_name']}")

    print("\n2. THE ROTATION NULL for the gate on the holdout half -- every circular offset of the breadth series (enumerated)")
    draws = rotation_null(b5, t, rb, long_ & is_b, T, BREADTH_CUT); obs = res["m1"]["long|holdout half|pooled"]["diff_bp"] / 1e4
    assert abs(draws[0] - obs) < 1e-12, "[ROT] offset 0 != observed"
    fin = draws[np.isfinite(draws)]; p95 = float(np.quantile(fin, .95)); rank = float((fin < obs).mean())
    res["rot"] = dict(observed_bp=1e4 * obs, p50=float(1e4 * np.median(fin)), p95=1e4 * p95, n_offsets=int(fin.size), percentile=rank, passes=bool(obs > p95))
    print(f"  [ROT] offset 0 == observed;  observed {1e4*obs:+.2f}   null p50 {1e4*np.median(fin):+.2f}  p95 {1e4*p95:+.2f}  (exact, {fin.size:,} offsets)   percentile {100*rank:.1f}   {'PASS' if obs > p95 else 'FAIL'}")

    print("\n3. M2 -- dollar-volume terciles inside cell 2 (cuts fixed on the union's cell 2)")
    cuts = np.quantile(dv[c2 & np.isfinite(dv)], [1 / 3, 2 / 3]); res["m2"]["cuts"] = [float(c) for c in cuts]
    print(f"  cuts ${cuts[0]/1e6:.1f}M / ${cuts[1]/1e6:.1f}M")
    ter = [("bottom", c2 & (dv < cuts[0])), ("middle", c2 & (dv >= cuts[0]) & (dv < cuts[1])), ("top", c2 & (dv >= cuts[1]))]
    for tl, tm in ter:
        for hl, hm in halves:
            d = dist(rb, cost, tm & hm, f"cell 2 DV {tl:6s} {hl}"); res["m2"][f"{tl}|{hl}"] = d; show(d)
        print()
    for wl, wm in wins[1:]:
        d = dist(rb, cost, ter[2][1] & is_b & wm, f"cell 2 DV top  holdout half  {wl}"); res["m2"][f"top|holdout half|{wl}"] = d; show(d)

    print("\n4. M3 -- the second touch's gap, by half (second touch & cell 2)")
    for lo, hi in ((3, 5), (6, 10), (11, 20)):
        for hl, hm in halves:
            d = dist(rb, cost, R2 & (gap >= lo) & (gap <= hi) & hm, f"gap {lo:2d}-{hi:2d}  {hl}"); res["m3"][f"{lo}-{hi}|{hl}"] = d; show(d)
        print()

    print("5. THE BOOKS -- gated long N=3, ungated long N=3, top-DV cell 2 N=10; three seeds")
    series = {}
    for name, pool, n_slots, Ix in (("GATED-LONG", long_ & ~high, N3, I), ("UNGATED-LONG", long_, N3, I), ("DV-TOP-C2", ter[2][1], N10, I1)):
        for seed in SEEDS:
            R = sim4(Ix, n_slots, seed, nan1, nan2, pool); S = Bw.score(Ix, R, n_slots); assert S["recon_rel"] < 1e-9, "[RECON]"
            series[(name, seed)] = S["net_series"]; d0 = R["d0"]
            res["books"][f"{name}_s{seed}"] = {k: v for k, v in S.items() if not k.endswith("_series") and k != "run_dist"}
    ds = dates[d0:]; ys = np.array([str(x)[:4] for x in ds]).astype(int); w18 = ys >= 2018
    print(f"  [RECON] all\n  {'book':14s} {'N':>2s} {'gross':>7s} {'net':>7s} {'cost':>6s} {'util':>6s} {'trades':>6s} {'per trade':>9s}   net by seed            pooled ± SE      2018+ ± SE")
    for name, n_slots in (("GATED-LONG", N3), ("UNGATED-LONG", N3), ("DV-TOP-C2", N10)):
        S = res["books"][f"{name}_s{SEEDS[0]}"]; nets = [res["books"][f"{name}_s{s}"]["net_bp"] for s in SEEDS]
        ser = np.mean([series[(name, s)] for s in SEEDS], axis=0); se_, mean = Bw.block_boot(ser, ds); se18, m18 = Bw.block_boot(ser[w18], ds[w18])
        res["se"][name] = dict(mean=float(1e4 * mean), se=float(1e4 * se_), mean18=float(1e4 * m18), se18=float(1e4 * se18), nets=nets)
        print(f"  {name:14s} {n_slots:2d} {S['gross_bp']:+7.3f} {S['net_bp']:+7.3f} {S['cost_bp']:6.3f} {100*S['utilisation']:5.1f}% {S['trades']:6,} {S['trade_mean_bp']:+9.2f}   "
              + " ".join(f"{x:+.3f}" for x in nets) + f"   {1e4*mean:+6.3f} ± {1e4*se_:.3f}   {1e4*m18:+6.3f} ± {1e4*se18:.3f}")
    dgu = np.mean([series[("GATED-LONG", s)] - series[("UNGATED-LONG", s)] for s in SEEDS], axis=0); seg, mg = Bw.block_boot(dgu, ds)
    res["se"]["gated_minus_ungated"] = dict(mean=float(1e4 * mg), se=float(1e4 * seg))
    print(f"  gated - ungated long book: {1e4*mg:+.3f} ± {1e4*seg:.3f}")

    gh = res["m1"]["long|holdout half|pooled"]; sg = res["se"]["GATED-LONG"]
    T1 = bool(dh["gross"] > 0 and dh["gross"] / dh["se"] >= 2); T1b = bool(dh["net"] > 0); T2 = bool(gh["diff_bp"] > 0 and gh["t"] >= 2); T3 = bool(res["rot"]["passes"]); T4 = bool(sg["mean"] > 0 and sg["mean"] / sg["se"] >= 2)
    res["bar"] = dict(T1=T1, T1b=T1b, T2=T2, T3=T3, T4=T4, all=bool(T1 and T1b and T2 and T3 and T4))
    print("\n6. THE BAR -- M1 on the holdout half (in-sample evidence; not a candidate)")
    print(f"    T1  gated long gross > 0 by 2 SE, holdout half : {T1}   ({dh['gross']:+.2f} ± {dh['se']:.2f}, {dh['gross']/dh['se']:+.1f} SE, n {dh['n']})")
    print(f"    T1b gated long net > 0                         : {T1b}  ({dh['net']:+.2f})")
    print(f"    T2  kept - excluded > 0 by 2 SE, holdout half  : {T2}   ({gh['diff_bp']:+.2f} ± {gh['se_bp']:.2f}, {gh['t']:+.1f} SE)")
    print(f"    T3  beats the enumerated rotation p95          : {T3}   (percentile {100*res['rot']['percentile']:.1f})")
    print(f"    T4  gated long book N=3 net > 0 by 2 SE, union : {T4}   ({sg['mean']:+.3f} ± {sg['se']:.3f})")
    print(f"    all four: {res['bar']['all']}")
    gu = res["m1"]["long|union|pooled"]; gs = res["m1"]["short|union|pooled"]
    print("\n7. PREDICTIONS")
    print(f"    X-a union excl -20..+10, kept +55..+75; holdout excl -150..-300, kept 0..+40; T2, T3 pass : union excl {gu['excl_bp']:+.1f} kept {gu['kept_bp']:+.1f}; holdout excl {gh['excl_bp']:+.1f} kept {gh['kept_bp']:+.1f}; T2 {T2} T3 {T3}")
    print(f"    X-b T1 fails, T1b a coin                          : T1 {T1}, T1b {T1b}")
    print(f"    X-c short kept - excluded inside ±30              : {gs['diff_bp']:+.1f} ± {gs['se_bp']:.1f}")
    print(f"    X-d gated long book +2..+4.5, above ungated by 0.5..2 : {sg['mean']:+.3f}; delta {1e4*mg:+.3f} ± {1e4*seg:.3f}")
    m2 = res["m2"]; print(f"    X-e cost falls with DV; top tercile net -5..+10 union, ±15 holdout; book inside ±1 : cost {m2['bottom|union']['cost']:.1f}/{m2['middle|union']['cost']:.1f}/{m2['top|union']['cost']:.1f}; top net union {m2['top|union']['net']:+.1f}, holdout {m2['top|holdout half']['net']:+.1f}; book {res['se']['DV-TOP-C2']['mean']:+.3f}")
    m3 = res["m3"]; print(f"    X-f holdout 6-10 gross +15..+40, > 3-5, 11-20 lowest : holdout 3-5 {m3['3-5|holdout half']['gross']:+.1f}, 6-10 {m3['6-10|holdout half']['gross']:+.1f}, 11-20 {m3['11-20|holdout half']['gross']:+.1f}  (in-sample {m3['3-5|in-sample half']['gross']:+.1f} / {m3['6-10|in-sample half']['gross']:+.1f} / {m3['11-20|in-sample half']['gross']:+.1f})")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT}   total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    if a.run:
        run()

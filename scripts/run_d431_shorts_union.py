"""D431 -- the short arm on the union of the universe and holdout 1, both lenses. Bar committed in 7f2dd15 BEFORE this file.

Both fixtures are spent for this line. Each is run through D430's parametrised pipeline from its own cached
panel (no fixture is opened); events are pooled on a union calendar with name indices offset.

usage:  uv run python -u scripts/run_d431_shorts_union.py --run [--workers 8]
"""
import argparse, importlib.util, json, multiprocessing as mp, os, pathlib, sys, time
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
R30 = _load("d430r", "run_d430_holdout.py")           # light at import; pipeline, masks, load_panel_from, PRICE_CUT
R28 = _load("d428r", "run_d428_combined_book.py")      # light: sim4, dist, show, concentration, with_borrow
sim4, dist, show, concentration, with_borrow = R28.sim4, R28.dist, R28.show, R28.concentration, R28.with_borrow

OUT = REPO / "data" / "d431_shorts_union.json"
UNION_INPUTS = REPO / "temp" / "d431_union_inputs.npz"
HOLD, SEEDS, NS, N_PRIMARY, N_DRAW, N_PERM = 5, (419, 4190, 41900), (2, 3, 4, 5), 3, 100, 200
B1, B10 = 0.01, 0.10
EXPECT = dict(short=1783, long=2083, full=3866)


def union(Ia, Ib):
    """Pool two fixtures' event tables on a union calendar; holdout names offset past the in-sample names."""
    da, db = [str(x) for x in Ia["dates"]], [str(x) for x in Ib["dates"]]
    ud = sorted(set(da) | set(db)); pos = {d: k for k, d in enumerate(ud)}
    ta = np.array([pos[da[k]] for k in Ia["t"]]); tb = np.array([pos[db[k]] for k in Ib["t"]])
    na = len(Ia["symbols"])
    I = {}
    for k in ("side", "r_base", "c2", "OP", "HI", "LO", "CL", "E", "ATR", "cost"):
        I[k] = np.concatenate([Ia[k], Ib[k]])
    I["t"] = np.concatenate([ta, tb]); I["i"] = np.concatenate([Ia["i"], Ib["i"] + na])
    I["T"] = np.array([len(ud)]); I["dates"] = np.array(ud); I["symbols"] = np.concatenate([Ia["symbols"], Ib["symbols"]])
    return I, np.concatenate([np.zeros(len(Ia["t"]), bool), np.ones(len(Ib["t"]), bool)])


def top1_share(r, m):
    x = r[m]; x = x[np.isfinite(x)]; k = max(1, int(round(0.01 * x.size))); s = np.sort(x)
    return float(100 * s[-k:].sum() / x.sum()) if x.sum() > 0 else float("nan")


def perm_within_day(vals, t, mask, rng):
    idx = np.flatnonzero(mask); base = idx[np.lexsort((np.arange(idx.size), t[idx]))]; perm = idx[np.lexsort((rng.random(idx.size), t[idx]))]
    out = vals.copy(); out[perm] = vals[base]; return out


def _ctrl_worker(args):
    n_slots, count, draws, npz = args
    import psutil
    Bw = _load("d419w", "run_d419_book.py")
    z = np.load(npz, allow_pickle=False); I = {k: z[k] for k in z.files}; N = len(I["t"])
    nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan); base = np.flatnonzero(I["c2"] & (I["side"] < 0)); out = []
    for dr in draws:
        rng = np.random.default_rng(300000 + dr)
        pool = np.zeros(N, bool); pool[rng.choice(base, size=count, replace=False)] = True
        R = sim4(I, n_slots, SEEDS[0], nan1, nan2, pool); S = Bw.score(I, R, n_slots); assert S["recon_rel"] < 1e-9, "[RECON] control"
        out.append((dr, S["net_bp"], S["utilisation"]))
    return out, psutil.Process(os.getpid()).memory_info().rss / 1e6


def run(workers):
    t0 = time.time()
    print("D431  the short arm on the union of the universe and holdout 1 -- both lenses\n      the bar was committed in 7f2dd15 BEFORE this ran; both fixtures are spent for this line\n")
    Bw = _load("d419w", "run_d419_book.py"); FL = _load("d422f", "d422_stack_flags.py"); RF = _load("d426f", "d426_rung_flags.py")
    D = Bw.D
    Pa = D.load_panel(verbose=False)
    assert R30.HOLDOUT_CACHE.exists(), "[DOOR] the holdout panel cache is absent; nothing is opened here"
    Pb = R30.load_panel_from(D, R30.HOLDOUT_FIX, R30.HOLDOUT_EVJ, R30.HOLDOUT_CACHE, verbose=False)     # cache hit: no fixture is opened
    Ia, fla, Fa, Xa, _ = R30.pipeline(Bw, FL, RF, Pa); Ib, flb, Fb, Xb, _ = R30.pipeline(Bw, FL, RF, Pb)
    assert len(Ia["t"]) == 180050 and int(Xa["pool"].sum()) == 1416 and len(Ib["t"]) == 92183 and int(Xb["pool"].sum()) == 667, "[STAGE0] halves"
    # [P2] the in-sample half reproduces D428's full-pool N=3 book; the holdout half reproduces D430's N=2 long book
    d28 = json.loads((REPO / "data" / "d428_combined_book.json").read_text(encoding="utf-8")); d30 = json.loads((REPO / "data" / "d430_oos.json").read_text(encoding="utf-8"))
    Na = len(Ia["t"]); nan1a = np.full(Na, np.nan); nan2a = np.full((Na, HOLD), np.nan)
    full_a = Xa["L1"] & (Ia["E"] < R30.PRICE_CUT); prio_a = full_a & Fa["opp_prior"] & (Fa["prev_gap"] >= 3) & (Fa["prev_gap"] <= 10)
    for seed in SEEDS:
        S = Bw.score(with_borrow(Ia, B1), sim4(with_borrow(Ia, B1), 3, seed, nan1a, nan2a, full_a, prio=prio_a), 3); r = d28["books"][f"PRIO_N3_s{seed}"]
        assert abs(S["net_bp"] - r["net_bp"]) < 1e-12 and S["trades"] == r["trades"], f"[P2] D428 PRIO_N3 seed {seed}"
    Nb = len(Ib["t"]); nan1b = np.full(Nb, np.nan); nan2b = np.full((Nb, HOLD), np.nan)
    for seed in SEEDS:
        S = Bw.score(Ib, sim4(Ib, 2, seed, nan1b, nan2b, Xb["pool"], prio=Xb["prio"]), 2); r = d30["books"][f"PRIO_N2_s{seed}"]
        assert abs(S["net_bp"] - r["net_bp"]) < 1e-12 and S["trades"] == r["trades"], f"[P2] D430 PRIO_N2 seed {seed}"
    print("  [STAGE0] halves reproduce D413/D428/D430's counts;  [P2] D428's full-pool N=3 book and D430's N=2 long book reproduce on every seed")

    I0, is_b = union(Ia, Ib)
    N = len(I0["t"]); T = int(I0["T"][0]); t, i, side, E, c2, rb = I0["t"], I0["i"], I0["side"], I0["E"], I0["c2"], I0["r_base"]
    SYM = I0["symbols"]; dates = I0["dates"]; yr = np.array([int(str(x)[:4]) for x in dates[t]])
    cat = lambda k: np.concatenate([Xa[k], Xb[k]])
    R2, L1 = cat("R2"), cat("L1"); cheap = E < R30.PRICE_CUT; full = L1 & cheap
    short = full & (side < 0); long_ = full & (side > 0)
    gap = np.concatenate([Fa["prev_gap"], Fb["prev_gap"]]); opp = np.concatenate([Fa["opp_prior"], Fb["opp_prior"]])
    prio = short & opp & (gap >= 3) & (gap <= 10)
    assert (int(short.sum()), int(long_.sum()), int(full.sum())) == (EXPECT["short"], EXPECT["long"], EXPECT["full"]), f"[STAGE0] union {(int(short.sum()), int(long_.sum()), int(full.sum()))}"
    print(f"  [UNION] {len(SYM):,} names, {T:,} dates, {N:,} touches;  short pool {int(short.sum()):,}  long {int(long_.sum()):,}  priority {int(prio.sum())}")
    I1, I10 = with_borrow(I0, B1), with_borrow(I0, B10)
    res = dict(per_trade={}, ladder={}, conc={}, null=None, books={}, se={}, by_year={}, control=None, bar={})

    print("\n1. PER TRADE -- the union short pool")
    wins = [("pooled", np.ones(N, bool)), ("2018+", yr >= 2018), ("2021-2026", yr >= 2021)]
    for lab, m in (("short pool", short), ("  in-sample half", short & ~is_b), ("  holdout half", short & is_b), ("priority sub-cell", prio), ("short |r|<=50%", short & (np.abs(rb) <= .5)), ("LONG pool (symmetry)", long_)):
        for wl, wm in wins:
            d = dist(rb, I1["cost"], m & wm, f"{lab}  {wl}"); d["net_b10"] = dist(rb, I10["cost"], m & wm, "")["net"] if "gross" in d else None
            d["top1_share"] = top1_share(rb, m & wm); res["per_trade"][f"{lab.strip()}|{wl}"] = d
            if wl == "pooled" or lab == "short pool":
                show(d)
                if "gross" in d: print(f"  {'':30s} net at 10% borrow {d['net_b10']:+7.2f}   top 1% of trades = {d['top1_share']:.1f}% of P&L")
        print()
    print("  THE LADDER on the union (pooled):")
    for lab, m in (("all touches", np.ones(N, bool)), ("cell 2", c2), ("second touch & cell 2", R2), ("+ cheap", R2 & cheap), ("+ gap 3-20", full), ("short", short), ("long", long_)):
        d = dist(rb, I1["cost"], m, f"ladder {lab}"); res["ladder"][lab] = d; show(d)
    for lab, m in (("short pool", short), ("short 2018+", short & (yr >= 2018)), ("short 2021-2026", short & (yr >= 2021))):
        q = concentration(rb, i, yr, m, SYM); res["conc"][lab] = q
        print(f"  {lab:16s} names {q['names']:4,}  to half P&L {q['to_half']:3d}  top1 {q['top1']:4.1f}%  top5 {q['top5']:4.1f}%  top10 {q['top10']:4.1f}%  years + {q['years_pos']}/{q['years']}  top name {q['top_name']}  top year {q['top_year']} {q['top_year_share']:.1f}%")
    kk = np.flatnonzero(short); top = kk[np.nanargmax(rb[kk])]; nm = int(i[top]); src = Pb if is_b[top] else Pa; nm_local = nm - len(Ia["symbols"]) if is_b[top] else nm
    dloc = int(Ib["t"][top - Na]) if is_b[top] else int(Ia["t"][top]); Tl = src["CL"].shape[0]
    print(f"  top trade: {SYM[nm]} {dates[t[top]]} ({'holdout' if is_b[top] else 'in-sample'}) entry {E[top]:.2f} -> {src['CL'][min(dloc + HOLD, Tl - 1), nm_local]:.2f}  r {1e4*rb[top]:+.0f} bp = {100*rb[top]/np.nansum(rb[short]):.1f}% of P&L;  closes " +
          " ".join(f"{src['CL'][dloc + j, nm_local]:.2f}" for j in range(0, min(HOLD + 1, Tl - dloc))) + ";  volume " + " ".join(f"{src['VOL'][dloc + j, nm_local]/1e6:.1f}M" for j in range(0, min(HOLD + 1, Tl - dloc))))
    print("  short pool by year: " + "  ".join(f"{y}:{1e4*np.nanmean(rb[short & (yr == y)]):+.0f}({int((short & (yr == y)).sum())})" for y in range(2010, 2027) if (short & (yr == y)).any()))

    print("\n2. THE PER-TRADE NULL -- the short pool's premium over the union's other cell-2 short events, within-day permutation")
    base = c2 & (side < 0); lab_ = short.astype(float)
    obs = float(rb[short].mean() - rb[base & ~short].mean()); rng = np.random.default_rng(431); draws = np.empty(N_PERM)
    for b in range(N_PERM):
        lp = perm_within_day(lab_, t, base, rng) > 0.5; draws[b] = rb[lp & base].mean() - rb[base & ~lp].mean()
    p95 = float(np.quantile(draws, .95)); se = float(draws.std(ddof=1) / np.sqrt(N_PERM)); edge = obs - p95
    res["null"] = dict(observed_bp=1e4 * obs, p50=float(1e4 * np.median(draws)), p95=1e4 * p95, se=1e4 * se, margin_se=float(edge / se), passes=bool(edge > 0 and abs(edge) >= 2 * se), unresolved=bool(abs(edge) < 2 * se))
    q = res["null"]; print(f"  premium {q['observed_bp']:+7.2f}   null p50 {q['p50']:+6.2f}  p95 {q['p95']:+6.2f} (±{q['se']:.2f})   margin {q['margin_se']:+.1f} SE   {'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}")

    print("\n3. THE BOOK -- short pool on the union, three seeds")
    nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan); series = {}
    arms = [("PRIO", I1, short, prio), ("NOPRIO", I1, short, None), ("PRIO-b10", I10, short, prio), ("HOLDOUT-HALF", I1, short & is_b, prio & is_b)]
    for n_slots in NS:
        for arm, Ix, pl, pr in arms:
            if arm == "HOLDOUT-HALF" and n_slots != 2:
                continue
            for seed in SEEDS:
                R = sim4(Ix, n_slots, seed, nan1, nan2, pl, prio=pr); S = Bw.score(Ix, R, n_slots); assert S["recon_rel"] < 1e-9, "[RECON]"
                series[(arm, n_slots, seed)] = S["net_series"]; d0 = R["d0"]
                res["books"][f"{arm}_N{n_slots}_s{seed}"] = {k: v for k, v in S.items() if not k.endswith("_series") and k != "run_dist"}
    ds = dates[d0:]; ys = np.array([str(x)[:4] for x in ds]).astype(int); w18 = ys >= 2018; w21 = ys >= 2021
    print(f"  [RECON] all\n  {'N':>3s} {'arm':13s} {'gross':>7s} {'net':>7s} {'cost':>6s} {'util':>6s} {'trades':>6s} {'per trade':>9s}   net by seed            pooled ± SE      2018+ ± SE       2021-26 ± SE")
    for n_slots in NS:
        for arm, _, _, _ in arms:
            if (arm, n_slots, SEEDS[0]) not in series:
                continue
            S = res["books"][f"{arm}_N{n_slots}_s{SEEDS[0]}"]; nets = [res["books"][f"{arm}_N{n_slots}_s{s}"]["net_bp"] for s in SEEDS]
            ser = np.mean([series[(arm, n_slots, s)] for s in SEEDS], axis=0)
            se_, mean = Bw.block_boot(ser, ds); se18, m18 = Bw.block_boot(ser[w18], ds[w18]); se21, m21 = Bw.block_boot(ser[w21], ds[w21])
            res["se"][f"{arm}_N{n_slots}"] = dict(mean=float(1e4 * mean), se=float(1e4 * se_), mean18=float(1e4 * m18), se18=float(1e4 * se18), mean21=float(1e4 * m21), se21=float(1e4 * se21), nets=nets)
            print(f"  {n_slots:3d} {arm:13s} {S['gross_bp']:+7.3f} {S['net_bp']:+7.3f} {S['cost_bp']:6.3f} {100*S['utilisation']:5.1f}% {S['trades']:6,} {S['trade_mean_bp']:+9.2f}   "
                  + " ".join(f"{x:+.3f}" for x in nets) + f"   {1e4*mean:+6.3f} ± {1e4*se_:.3f}   {1e4*m18:+6.3f} ± {1e4*se18:.3f}   {1e4*m21:+6.3f} ± {1e4*se21:.3f}")
        print()
    ser3 = np.mean([series[("PRIO", N_PRIMARY, s)] for s in SEEDS], axis=0)
    for y in range(2010, 2027):
        m = ys == y
        if m.any(): res["by_year"][str(y)] = float(1e4 * ser3[m].mean())
    print("  the N=3 short book by year: " + "  ".join(f"{y}:{v:+.1f}" for y, v in res["by_year"].items()))

    print(f"\n4. CONTROL at N={N_PRIMARY} -- random pools of {int(short.sum()):,} of the union's cell-2 SHORT events at 1% borrow; one worker measured first")
    np.savez_compressed(UNION_INPUTS, **{k: v for k, v in I1.items()})
    with mp.Pool(1) as pl:
        out1, rss = pl.map(_ctrl_worker, [(N_PRIMARY, int(short.sum()), [0], str(UNION_INPUTS))])[0]
    print(f"  one worker: RSS {rss:.0f} MB  ->  {workers} workers ~ {workers*rss/1e3:.1f} GB")
    rng = np.random.default_rng(300000); p0 = np.zeros(N, bool); p0[rng.choice(np.flatnonzero(base), size=int(short.sum()), replace=False)] = True
    S0 = Bw.score(I1, sim4(I1, N_PRIMARY, SEEDS[0], nan1, nan2, p0), N_PRIMARY); assert abs(out1[0][1] - S0["net_bp"]) < 1e-12, "[CHUNK]"
    with mp.Pool(workers) as pl:
        results = pl.map(_ctrl_worker, [(N_PRIMARY, int(short.sum()), list(range(w, N_DRAW, workers)), str(UNION_INPUTS)) for w in range(workers)])
    out = sorted(o for oo, _ in results for o in oo); net = np.array([o[1] for o in out])
    obs = res["se"][f"PRIO_N{N_PRIMARY}"]["mean"]; p95 = float(np.quantile(net, .95)); se_ = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs - p95
    res["control"] = dict(observed=obs, p5=float(np.quantile(net, .05)), p50=float(np.median(net)), p95=p95, se=se_, margin_se=float(edge / se_),
                          passes=bool(edge > 0 and abs(edge) >= 2 * se_), unresolved=bool(abs(edge) < 2 * se_), util=float(np.mean([o[2] for o in out])))
    q = res["control"]; print(f"  book {obs:+.3f}   random short pools p5 {q['p5']:+.3f}  p50 {q['p50']:+.3f}  p95 {p95:+.3f} (±{se_:.3f})   margin {q['margin_se']:+.1f} SE   "
                              f"{'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}   util ctrl {100*q['util']:.1f}%\n  [CHUNK] worker draw 0 == in-process")

    dp = res["per_trade"]["short pool|pooled"]; s3 = res["se"][f"PRIO_N{N_PRIMARY}"]
    T1 = bool(dp["gross"] > 0 and dp["gross"] / dp["se"] >= 2); T1b = bool(dp["net"] > 0 and dp["net_b10"] > 0); T2 = bool(s3["mean"] > 0 and s3["mean"] / s3["se"] >= 2); T3 = bool(q["passes"])
    res["bar"] = dict(T1=T1, T1b=T1b, T2=T2, T3=T3, passes=bool(T1 and T1b and T2 and T3))
    print(f"\n5. THE BAR -- N={N_PRIMARY}, short, priority, 1% borrow  (an IN-SAMPLE bar on 2,376 spent names; not a candidate)")
    print(f"    T1  gross > 0 by 2 SE           : {T1}   ({dp['gross']:+.2f} ± {dp['se']:.2f}, {dp['gross']/dp['se']:+.1f} SE, n {dp['n']:,})")
    print(f"    T1b net > 0 at 1% AND 10%       : {T1b}  ({dp['net']:+.2f} / {dp['net_b10']:+.2f})")
    print(f"    T2  book net > 0 by 2 SE        : {T2}   ({s3['mean']:+.3f} ± {s3['se']:.3f}, {s3['mean']/s3['se']:+.1f} SE)")
    print(f"    T3  book > random short p95     : {T3}   (margin {q['margin_se']:+.1f} SE)")
    print(f"    in-sample bar {'PASSED' if res['bar']['passes'] else 'FAILED'}")
    lad = res["ladder"]; hh = res["per_trade"]["holdout half|pooled"]; sh = res["se"]["HOLDOUT-HALF_N2"]
    print("\n6. PREDICTIONS")
    print(f"    X-a n 1,783; gross +75..+85; median +10..+20; win 50-53; payoff > 1.3; net 1% +40..+50, 10% +20..+32; top1% > 45% : n {dp['n']:,}; {dp['gross']:+.2f}; med {dp['median']:+.2f}; win {dp['win']:.1f}%; payoff {dp['payoff']:.2f}; net {dp['net']:+.2f} / {dp['net_b10']:+.2f}; top1% {dp['top1_share']:.1f}%")
    print(f"    X-b null passes                                       : margin {res['null']['margin_se']:+.1f} SE")
    print(f"    X-c ladder: touches +9..+11, cell 2 +24..+28, second touch +25..+35, long pool +40..+50 : {lad['all touches']['gross']:+.1f}, {lad['cell 2']['gross']:+.1f}, {lad['second touch & cell 2']['gross']:+.1f}, long {lad['long']['gross']:+.1f}")
    print(f"    X-d N=3 book +3..+5 at 1%, +1.5..+3.5 at 10%, all seeds +, util 45-60, T3 pass, prio inside noise : {s3['mean']:+.3f} / {res['se']['PRIO-b10_N3']['mean']:+.3f}; seeds {' '.join(f'{x:+.2f}' for x in s3['nets'])}; util {100*res['books']['PRIO_N3_s419']['utilisation']:.0f}%; T3 {T3}; prio delta {s3['mean'] - res['se']['NOPRIO_N3']['mean']:+.3f}")
    print(f"    X-e 2018+, 2021+ below pooled; one negative on the holdout half : {dp['gross']:+.1f} vs 2018+ {res['per_trade']['short pool|2018+']['gross']:+.1f}, 2021+ {res['per_trade']['short pool|2021-2026']['gross']:+.1f}; holdout half 2018+ {res['per_trade']['holdout half|2018+'].get('gross', float('nan')):+.1f}, 2021+ {res['per_trade']['holdout half|2021-2026'].get('gross', float('nan')):+.1f}")
    print(f"    X-f holdout half alone: gross +58.4; N=2 book inside ±2 : {hh['gross']:+.2f}; {sh['mean']:+.3f} ± {sh['se']:.3f}")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT}   total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.run:
        run(a.workers)

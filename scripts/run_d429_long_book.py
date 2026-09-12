"""D429 -- the long-only combined book at three slots, 2018+ window. Bar committed in 477df47 BEFORE this file.

usage:  uv run python -u scripts/run_d429_long_book.py --run [--workers 8]
"""
import argparse, importlib.util, json, multiprocessing as mp, os, pathlib, sys, time
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
R28 = _load("d428r", "run_d428_combined_book.py")     # light at import; brings sim4, dist, show, concentration
sim4, dist, show, concentration = R28.sim4, R28.dist, R28.show, R28.concentration

OUT = REPO / "data" / "d429_long_book.json"
HOLD, SEEDS, NS, N_PRIMARY, N_DRAW = 5, (419, 4190, 41900), (2, 3, 4, 5), 3, 100
LONG_COUNT, PRIO_COUNT = 1416, 165


def _ctrl_worker(args):
    n_slots, count, draws = args
    import psutil
    Bw = _load("d419w", "run_d419_book.py")
    I = dict(Bw.build_inputs()); N = len(I["t"])
    nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan)
    base = np.flatnonzero(I["c2"] & (I["side"] > 0)); out = []           # random pools of cell-2 LONG events
    for dr in draws:
        rng = np.random.default_rng(300000 + dr)
        pool = np.zeros(N, bool); pool[rng.choice(base, size=count, replace=False)] = True
        R = sim4(I, n_slots, SEEDS[0], nan1, nan2, pool); S = Bw.score(I, R, n_slots)
        assert S["recon_rel"] < 1e-9, "[RECON] control"
        out.append((dr, S["net_bp"], S["utilisation"]))
    return out, psutil.Process(os.getpid()).memory_info().rss / 1e6


def run(workers):
    t0 = time.time()
    print("D429  the long-only combined book at three slots, 2018+ window\n      the bar was committed in 477df47 BEFORE this ran\n")
    PL = _load("d428p", "d428_pool.py")
    I, P, B, fl, M, F, L, X = PL.load(); Q = PL.pool(I, X)
    t, i, side, E, c2, rb, cost = I["t"], I["i"], I["side"], I["E"], I["c2"], I["r_base"], I["cost"]
    N = len(t); T = int(I["T"][0]); SYM = I["symbols"]; dates = I["dates"]; yr = np.array([int(str(x)[:4]) for x in dates[t]])
    pool, prio = Q["long"], Q["prio"] & Q["long"]
    assert int(pool.sum()) == LONG_COUNT and int(prio.sum()) == PRIO_COUNT, "[STAGE0]"
    assert np.all((R28.with_borrow(I, 0.10)["cost"] - cost)[pool] == 0), "[COST] the borrow term is identically zero on the long pool"
    print(f"  [STAGE0] {LONG_COUNT:,} / {PRIO_COUNT} reproduce;  [COST] borrow term identically zero on the pool")
    nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan)
    res = dict(per_trade={}, conc={}, books={}, se={}, control=None, by_year={}, bar={})

    print("\n1. PER TRADE")
    wins = [("pooled", np.ones(N, bool)), ("2018+", yr >= 2018), ("2021-2026", yr >= 2021)]
    for lab, m in (("long pool", pool), ("priority sub-cell", prio), ("long pool |r|<=50%", pool & (np.abs(rb) <= .5))):
        for wl, wm in wins:
            d = dist(rb, cost, m & wm, f"{lab}  {wl}"); res["per_trade"][f"{lab}|{wl}"] = d; show(d)
        print()
    for lab, m in (("long pool", pool), ("long pool 2018+", pool & (yr >= 2018)), ("long pool 2021-2026", pool & (yr >= 2021))):
        cc = concentration(rb, i, yr, m, SYM); res["conc"][lab] = cc
        print(f"  {lab:20s} names {cc['names']:4,}  to half P&L {cc['to_half']:3d}  top1 {cc['top1']:4.1f}%  top5 {cc['top5']:4.1f}%  top10 {cc['top10']:4.1f}%  years + {cc['years_pos']}/{cc['years']}  "
              f"top name {cc['top_name']}  top year {cc['top_year']} {cc['top_year_share']:.1f}%")
    for lab, m in (("pooled", pool), ("2018+", pool & (yr >= 2018))):
        kk = np.flatnonzero(m); top = kk[np.nanargmax(rb[kk])]; nm = int(i[top]); d_ = int(t[top])
        print(f"  top trade {lab:7s}: {SYM[nm]} {dates[d_]} entry {E[top]:.2f} -> {P['CL'][min(d_ + HOLD, T - 1), nm]:.2f}  r {1e4*rb[top]:+.0f} bp = {100*rb[top]/np.nansum(rb[m]):.1f}% of P&L;  "
              f"closes: " + " ".join(f"{P['CL'][d_ + j, nm]:.2f}" for j in range(0, min(HOLD + 1, T - d_))) + f";  volume t..t+5: " + " ".join(f"{P['VOL'][d_ + j, nm]/1e6:.1f}M" for j in range(0, min(HOLD + 1, T - d_))))

    print("\n2. THE BOOK -- long pool, three seeds")
    R28j = json.loads((REPO / "data" / "d428_combined_book.json").read_text(encoding="utf-8"))
    series = {}; t1 = time.time()
    for n_slots in NS:
        for arm, pr in (("PRIO", prio), ("NOPRIO", None)):
            for seed in SEEDS:
                R = sim4(I, n_slots, seed, nan1, nan2, pool, prio=pr); S = B.score(I, R, n_slots); assert S["recon_rel"] < 1e-9, "[RECON]"
                series[(arm, n_slots, seed)] = S["net_series"]
                res["books"][f"{arm}_N{n_slots}_s{seed}"] = {k: v for k, v in S.items() if not k.endswith("_series") and k != "run_dist"}
                if arm == "PRIO" and n_slots == N_PRIMARY:
                    ref = R28j["books"][f"LONG_N3_s{seed}"]
                    assert abs(S["net_bp"] - ref["net_bp"]) < 1e-12 and S["trades"] == ref["trades"] and abs(S["gross_bp"] - ref["gross_bp"]) < 1e-12, f"[P2] LONG_N3_s{seed}"
    d0 = R["d0"]; print(f"  [P2]   the N=3 priority book == D428's LONG_N3 on every seed (net, gross, trade count to 1e-12)\n  {len(res['books'])} books in {time.time()-t1:.0f}s   [RECON] all\n")
    ds = dates[d0:]; ys = np.array([str(x)[:4] for x in ds]).astype(int); w18 = ys >= 2018; w21 = ys >= 2021
    print(f"  {'N':>3s} {'arm':7s} {'gross':>7s} {'net':>7s} {'cost':>6s} {'util':>6s} {'trades':>6s} {'per trade':>9s}   net by seed            pooled ± SE      2018+ ± SE       2021-26 ± SE")
    for n_slots in NS:
        for arm in ("PRIO", "NOPRIO"):
            S = res["books"][f"{arm}_N{n_slots}_s{SEEDS[0]}"]; nets = [res["books"][f"{arm}_N{n_slots}_s{s}"]["net_bp"] for s in SEEDS]
            ser = np.mean([series[(arm, n_slots, s)] for s in SEEDS], axis=0)
            se, mean = B.block_boot(ser, ds); se18, m18 = B.block_boot(ser[w18], ds[w18]); se21, m21 = B.block_boot(ser[w21], ds[w21])
            res["se"][f"{arm}_N{n_slots}"] = dict(mean=float(1e4 * mean), se=float(1e4 * se), mean18=float(1e4 * m18), se18=float(1e4 * se18), mean21=float(1e4 * m21), se21=float(1e4 * se21))
            print(f"  {n_slots:3d} {arm:7s} {S['gross_bp']:+7.3f} {S['net_bp']:+7.3f} {S['cost_bp']:6.3f} {100*S['utilisation']:5.1f}% {S['trades']:6,} {S['trade_mean_bp']:+9.2f}   "
                  + " ".join(f"{x:+.3f}" for x in nets) + f"   {1e4*mean:+6.3f} ± {1e4*se:.3f}   {1e4*m18:+6.3f} ± {1e4*se18:.3f}   {1e4*m21:+6.3f} ± {1e4*se21:.3f}")
        print()
    ser3 = np.mean([series[("PRIO", N_PRIMARY, s)] for s in SEEDS], axis=0)
    print("  the N=3 book by year (net bp/bar, mean over seeds)")
    line = []
    for y in range(2010, 2027):
        m = ys == y
        if m.any():
            res["by_year"][str(y)] = float(1e4 * ser3[m].mean()); line.append(f"{y}:{1e4*ser3[m].mean():+.1f}")
    print("  " + "  ".join(line))

    print(f"\n3. CONTROL at N={N_PRIMARY} -- random cell-2 LONG pools of {LONG_COUNT:,}: one worker measured, then {workers} x {N_DRAW//workers}")
    with mp.Pool(1) as pl:
        out1, rss = pl.map(_ctrl_worker, [(N_PRIMARY, LONG_COUNT, [0])])[0]
    print(f"  one worker: RSS {rss:.0f} MB  ->  {workers} workers ~ {workers*rss/1e3:.1f} GB")
    rng = np.random.default_rng(300000); p0 = np.zeros(N, bool); p0[rng.choice(np.flatnonzero(c2 & (side > 0)), size=LONG_COUNT, replace=False)] = True
    S0 = B.score(I, sim4(I, N_PRIMARY, SEEDS[0], nan1, nan2, p0), N_PRIMARY); assert abs(out1[0][1] - S0["net_bp"]) < 1e-12, "[CHUNK]"
    with mp.Pool(workers) as pl:
        results = pl.map(_ctrl_worker, [(N_PRIMARY, LONG_COUNT, list(range(w, N_DRAW, workers))) for w in range(workers)])
    out = sorted(o for oo, _ in results for o in oo); net = np.array([o[1] for o in out])
    obs = res["se"][f"PRIO_N{N_PRIMARY}"]["mean"]; p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs - p95
    res["control"] = dict(observed=obs, p5=float(np.quantile(net, .05)), p50=float(np.median(net)), p95=p95, se=se, margin_se=float(edge / se),
                          passes=bool(edge > 0 and abs(edge) >= 2 * se), unresolved=bool(abs(edge) < 2 * se), util=float(np.mean([o[2] for o in out])))
    q = res["control"]
    print(f"  book {obs:+.3f}   random long pools p5 {q['p5']:+.3f}  p50 {q['p50']:+.3f}  p95 {p95:+.3f} (±{se:.3f})   margin {edge/se:+.1f} SE   "
          f"{'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}   util ctrl {100*q['util']:.1f}%\n  [CHUNK] worker draw 0 == in-process")

    s3 = res["se"][f"PRIO_N{N_PRIMARY}"]
    T1 = bool(s3["mean"] > 0 and s3["mean"] / s3["se"] >= 2); T2 = bool(q["passes"]); T3 = bool(s3["mean18"] > 0 and s3["mean18"] / s3["se18"] >= 2)
    res["bar"] = dict(T1=T1, T2=T2, T3=T3, candidate=bool(T1 and T2 and T3))
    print(f"\n4. THE BAR -- N={N_PRIMARY}, long, priority")
    print(f"    T1 pooled net > 0 by 2 SE (a reproduction) : {T1}   ({s3['mean']:+.3f} ± {s3['se']:.3f}, {s3['mean']/s3['se']:+.1f} SE)")
    print(f"    T2 > random long-pool p95                  : {T2}   (margin {q['margin_se']:+.1f} SE)")
    print(f"    T3 2018-2026 net > 0 by 2 SE               : {T3}   ({s3['mean18']:+.3f} ± {s3['se18']:.3f}, {s3['mean18']/s3['se18']:+.1f} SE)")
    print(f"    CANDIDATE under the principal's rule: {res['bar']['candidate']}   (post-hoc arm, slots and window -- see the pre-registration §1; no holdout is read)")
    cc18 = res["conc"]["long pool 2018+"]; pd = res["se"][f"PRIO_N{N_PRIMARY}"]["mean"] - res["se"][f"NOPRIO_N{N_PRIMARY}"]["mean"]
    ypos = sum(v > 0 for v in res["by_year"].values())
    print("\n5. PREDICTIONS")
    print(f"    X-a pooled reproduces +4.40 ± 1.99            : {s3['mean']:+.2f} ± {s3['se']:.2f}")
    print(f"    X-b 2018+ +5.5..+8, SE 2.5..3.5               : {s3['mean18']:+.2f} ± {s3['se18']:.2f}")
    print(f"    X-c 2018+ 8-12 names to half, top year <= 30% : {cc18['to_half']} of {cc18['names']}, top year {cc18['top_year']} {cc18['top_year_share']:.1f}%")
    print(f"    X-d control p95 +0.5..+2.0, beaten by > 2 SE   : p95 {q['p95']:+.2f}, margin {q['margin_se']:+.1f} SE")
    print(f"    X-e priority inside ±0.4; peak at N=3          : delta {pd:+.3f}; " + "  ".join(f"N{n_}:{res['se'][f'PRIO_N{n_}']['mean']:+.2f}" for n_ in NS))
    print(f"    X-f >= 11 of 17 years positive; 2022 or 2023 < 0 : {ypos}/{len(res['by_year'])}; 2022 {res['by_year'].get('2022', float('nan')):+.1f}, 2023 {res['by_year'].get('2023', float('nan')):+.1f}")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT}   total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.run:
        run(a.workers)

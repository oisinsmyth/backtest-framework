"""D428 -- the combined book with a slot sweep, both lenses. Bar committed in 99b2b8d BEFORE this file.

Pool  STACK2-ANY & cell 2 & price < $38.51 & gap 3-20 (2,649); priority = opposite-side prior 3-10 (303);
      LONG arm 1,416. No exit. Borrow on the short half: 1%/yr primary, 10%/yr reported.
Books D427's sim4 (D421's priority ordering) at N in {2,3,4,5,7,10}, three seeds, with/without priority,
      LONG arm, 10% borrow. Controls at N=4: matched-count random cell-2 pools; random priorities.
Bar   N=4, priority, 1% borrow: T1 net > 0 by 2 SE; T2 > random-pool p95; T3 2021-2026 net > 0 by 2 SE.

usage:  uv run python -u scripts/run_d428_combined_book.py --run [--workers 8]
"""
import argparse, importlib.util, json, multiprocessing as mp, os, pathlib, sys, time
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
R27 = _load("d427r", "run_d427_layers.py")          # light at import: its heavy loads live inside its run()
sim4 = R27.sim4

OUT = REPO / "data" / "d428_combined_book.json"
HOLD, SEEDS, NS, N_PRIMARY, N_DRAW = 5, (419, 4190, 41900), (2, 3, 4, 5, 7, 10), 4, 100
BORROW = dict(b1=0.01, b10=0.10)                     # per year, on the short half, charged pro rata for the hold
POOL_COUNT, PRIO_COUNT, LONG_COUNT = 2649, 303, 1416


def with_borrow(I, rate):
    J = dict(I); J["cost"] = I["cost"] + np.where(I["side"] < 0, rate * HOLD / 252.0, 0.0)
    return J


# ------------------------------------------------------------------ per trade
def dist(r, c, m, label):
    r, c = r[m], c[m]; f = np.isfinite(r) & np.isfinite(c); r, c = r[f], c[f]; n = r.size
    if n < 30:
        return dict(label=label, n=int(n))
    lo, hi = np.quantile(r, [.01, .99]); w = r > 0; s = np.argsort(r); k = max(1, int(round(0.01 * n)))
    return dict(label=label, n=int(n), gross=float(1e4 * r.mean()), median=float(1e4 * np.median(r)), se=float(1e4 * r.std(ddof=1) / np.sqrt(n)),
                cost=float(1e4 * c.mean()), net=float(1e4 * (r - c).mean()), win=float(100 * w.mean()),
                payoff=float(r[w].mean() / -r[~w].mean()) if (~w).any() else float("nan"),
                trim=float(1e4 * r[(r >= lo) & (r <= hi)].mean()), ex_top=float(1e4 * r[s[:-k]].mean()), ex_bot=float(1e4 * r[s[k:]].mean()))


def show(d):
    if "gross" not in d:
        print(f"  {d['label']:30s} n {d['n']:5,} (too few)"); return
    print(f"  {d['label']:30s} n {d['n']:5,}  gross {d['gross']:+7.2f}  med {d['median']:+7.2f}  se {d['se']:5.2f}  cost {d['cost']:5.2f}  NET {d['net']:+7.2f}  "
          f"win {d['win']:4.1f}%  payoff {d['payoff']:4.2f}  trim {d['trim']:+7.2f}  ex-top {d['ex_top']:+7.2f}  ex-bot {d['ex_bot']:+7.2f}")


def concentration(r, i, yr, m, SYM):
    x = r[m]; nm = i[m]; y = yr[m]; f = np.isfinite(x); x, nm, y = x[f], nm[f], y[f]; tot = x.sum()
    by = {}
    for a, b in zip(nm, x): by[int(a)] = by.get(int(a), 0.0) + float(b)
    v = np.sort(np.array(list(by.values())))[::-1]; cs = np.cumsum(v)
    byy = {}
    for a, b in zip(y, x): byy[int(a)] = byy.get(int(a), 0.0) + float(b)
    top = max(by, key=by.get); ty = max(byy, key=byy.get)
    return dict(names=len(by), to_half=int(np.searchsorted(cs, 0.5 * tot) + 1), top1=float(100 * v[0] / tot), top5=float(100 * cs[min(4, v.size - 1)] / tot),
                top10=float(100 * cs[min(9, v.size - 1)] / tot), years_pos=int(sum(b > 0 for b in byy.values())), years=len(byy),
                top_name=str(SYM[top]), top_year=int(ty), top_year_share=float(100 * byy[ty] / tot))


# ------------------------------------------------------------------ controls
def _ctrl_worker(args):
    """Light: run_d419 for inputs and scorer, sim4 from run_d427 (light import). kind 'pool' draws random
    cell-2 pools of `count` (no priority); kind 'prio' draws random priorities of `count` inside the pool."""
    kind, n_slots, count, draws, pool_list = args
    import psutil
    Bw = _load("d419w", "run_d419_book.py")
    I = with_borrow(dict(Bw.build_inputs()), BORROW["b1"]); N = len(I["t"])
    nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan); base = np.flatnonzero(I["c2"]); out = []
    pool_fixed = None
    if kind == "prio":
        pool_fixed = np.zeros(N, bool); pool_fixed[np.array(pool_list)] = True
    for dr in draws:
        rng = np.random.default_rng(300000 + dr)
        if kind == "pool":
            pool = np.zeros(N, bool); pool[rng.choice(base, size=count, replace=False)] = True; prio = None
        else:
            pool = pool_fixed; prio = np.zeros(N, bool); prio[rng.choice(np.flatnonzero(pool), size=count, replace=False)] = True
        R = sim4(I, n_slots, SEEDS[0], nan1, nan2, pool, prio=prio); S = Bw.score(I, R, n_slots)
        assert S["recon_rel"] < 1e-9, "[RECON] control"
        out.append((dr, S["net_bp"], S["utilisation"]))
    return kind, out, psutil.Process(os.getpid()).memory_info().rss / 1e6


def run(workers):
    t0 = time.time()
    print("D428  the combined book with a slot sweep -- both lenses\n      the bar was committed in 99b2b8d BEFORE this ran\n")
    PL = _load("d428p", "d428_pool.py")
    I0, P, B, fl, M, F, L, X = PL.load(); Q = PL.pool(I0, X)
    t, i, side, E, c2, rb = I0["t"], I0["i"], I0["side"], I0["E"], I0["c2"], I0["r_base"]
    N = len(t); T = int(I0["T"][0]); SYM = I0["symbols"]; dates = I0["dates"]; yr = np.array([int(str(x)[:4]) for x in dates[t]])
    pool, prio, long_ = Q["pool"], Q["prio"], Q["long"]
    assert int(pool.sum()) == POOL_COUNT and int(prio.sum()) == PRIO_COUNT and int(long_.sum()) == LONG_COUNT, "[STAGE0]"
    print(f"  [STAGE0] {POOL_COUNT:,} / {PRIO_COUNT} / {LONG_COUNT:,} reproduce")
    I1, I10 = with_borrow(I0, BORROW["b1"]), with_borrow(I0, BORROW["b10"])
    bt = I1["cost"] - I0["cost"]
    assert np.all(bt[side > 0] == 0) and np.all(bt[side < 0] > 0), "[COST] borrow term must be zero on longs and positive on shorts"
    nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan)
    res = dict(per_trade={}, conc={}, books={}, se={}, control={}, bar={})

    print("\n1. PER TRADE -- the pool")
    wins = [("pooled", np.ones(N, bool)), ("2018+", yr >= 2018), ("2021-2026", yr >= 2021)]
    for lab, m in (("pool", pool), ("pool long", long_), ("pool short", pool & (side < 0)), ("priority sub-cell", prio), ("pool |r|<=50%", pool & (np.abs(rb) <= .5))):
        for wl, wm in wins:
            d = dist(rb, I1["cost"], m & wm, f"{lab}  {wl}"); d["net_b10"] = dist(rb, I10["cost"], m & wm, "")["net"] if "gross" in d else None
            res["per_trade"][f"{lab}|{wl}"] = d; show(d)
        print()
    for lab, m in (("pool", pool), ("pool 2021-2026", pool & (yr >= 2021)), ("pool long", long_)):
        cc = concentration(rb, i, yr, m, SYM); res["conc"][lab] = cc
        print(f"  {lab:16s} names {cc['names']:4,}  to half P&L {cc['to_half']:3d}  top1 {cc['top1']:4.1f}%  top5 {cc['top5']:4.1f}%  top10 {cc['top10']:4.1f}%  years + {cc['years_pos']}/{cc['years']}  "
              f"top name {cc['top_name']}  top year {cc['top_year']} {cc['top_year_share']:.1f}%")
    kk = np.flatnonzero(pool); top = kk[np.nanargmax(rb[kk])]; nm = int(i[top]); d_ = int(t[top])
    print(f"  top trade: {SYM[nm]} {dates[d_]} side {int(side[top]):+d} entry {E[top]:.2f} -> close t+5 {P['CL'][min(d_ + HOLD, T - 1), nm]:.2f}  r {1e4*rb[top]:+.0f} bp  "
          f"= {100*rb[top]/np.nansum(rb[pool]):.1f}% of P&L;  bars: " + " ".join(f"{P['CL'][d_ + j, nm]:.2f}" for j in range(0, min(HOLD + 1, T - d_))))
    res["top_trade"] = dict(sym=str(SYM[nm]), date=str(dates[d_]), side=int(side[top]), entry=float(E[top]), r_bp=float(1e4 * rb[top]))

    print("\n2. THE BOOK -- the slot sweep, three seeds; net at 1% borrow unless marked")
    R21 = M.simulate(I1, N_PRIMARY, SEEDS[0], pool_mask=pool); R0 = sim4(I1, N_PRIMARY, SEEDS[0], nan1, nan2, pool)
    assert [x[:3] for x in R0["trades"]] == [x[:3] for x in R21["trades"]] and np.array_equal(R0["gross"], R21["gross"]) and np.array_equal(R0["costs"], R21["costs"]), "[P2] no priority"
    R21p = M.simulate(I1, N_PRIMARY, SEEDS[0], prio=prio, pool_mask=pool); R0p = sim4(I1, N_PRIMARY, SEEDS[0], nan1, nan2, pool, prio=prio)
    assert [x[:3] for x in R0p["trades"]] == [x[:3] for x in R21p["trades"]] and np.array_equal(R0p["gross"], R21p["gross"]), "[P2] priority"
    print("  [P2]   sim4 on this pool == D421's simulate, with and without the priority, bit-identical (gross and cost series)")
    arms = [("PRIO", I1, pool, prio), ("NOPRIO", I1, pool, None), ("LONG", I1, long_, prio & long_), ("LONG-b0", I0, long_, prio & long_), ("PRIO-b10", I10, pool, prio)]
    series = {}; t1 = time.time(); d0 = R0["d0"]
    for n_slots in NS:
        for arm, Ix, pl, pr in arms:
            for seed in SEEDS:
                R = sim4(Ix, n_slots, seed, nan1, nan2, pl, prio=pr); S = B.score(Ix, R, n_slots); assert S["recon_rel"] < 1e-9, f"[RECON] {arm} N{n_slots}"
                series[(arm, n_slots, seed)] = S["net_series"]
                res["books"][f"{arm}_N{n_slots}_s{seed}"] = {k: v for k, v in S.items() if not k.endswith("_series") and k != "run_dist"}
    for n_slots in NS:
        for seed in SEEDS:
            assert np.array_equal(series[("LONG", n_slots, seed)], series[("LONG-b0", n_slots, seed)]), "[COST] the 1%-borrow LONG book must equal the no-borrow LONG book"
    print(f"  [COST] borrow term zero on longs, positive on shorts; the LONG book is identical with and without borrow\n  {len(res['books'])} books in {time.time()-t1:.0f}s   [RECON] all\n")
    mon = np.array([str(x)[:7] for x in dates[d0:]]); w21 = np.array([str(x)[:4] for x in dates[d0:]]).astype(int) >= 2021
    print(f"  {'N':>3s} {'arm':9s} {'gross':>7s} {'net':>7s} {'cost':>6s} {'util':>6s} {'trades':>6s} {'per trade':>9s}   net by seed             mean ± SE(block)   2021-26 net ± SE")
    for n_slots in NS:
        for arm in ("PRIO", "NOPRIO", "LONG", "PRIO-b10"):
            S = res["books"][f"{arm}_N{n_slots}_s{SEEDS[0]}"]; nets = [res["books"][f"{arm}_N{n_slots}_s{s}"]["net_bp"] for s in SEEDS]
            ser = np.mean([series[(arm, n_slots, s)] for s in SEEDS], axis=0)
            se, mean = B.block_boot(ser, dates[d0:]); se21, mean21 = B.block_boot(ser[w21], dates[d0:][w21])
            res["se"][f"{arm}_N{n_slots}"] = dict(mean=float(1e4 * mean), se=float(1e4 * se), t=float(mean / se), mean21=float(1e4 * mean21), se21=float(1e4 * se21), t21=float(mean21 / se21))
            print(f"  {n_slots:3d} {arm:9s} {S['gross_bp']:+7.3f} {S['net_bp']:+7.3f} {S['cost_bp']:6.3f} {100*S['utilisation']:5.1f}% {S['trades']:6,} {S['trade_mean_bp']:+9.2f}   "
                  + " ".join(f"{x:+.3f}" for x in nets) + f"   {1e4*mean:+7.3f} ± {1e4*se:.3f}   {1e4*mean21:+7.3f} ± {1e4*se21:.3f}")
        print()
    print("  the priority's delta (PRIO - NOPRIO), mean over seeds, block-bootstrap SE")
    for n_slots in NS:
        diff = np.mean([series[("PRIO", n_slots, s)] - series[("NOPRIO", n_slots, s)] for s in SEEDS], axis=0); se, mean = B.block_boot(diff, dates[d0:])
        res["se"][f"PRIO_delta_N{n_slots}"] = dict(mean=float(1e4 * mean), se=float(1e4 * se))
        print(f"  N={n_slots:2d}  {1e4*mean:+6.3f} ± {1e4*se:.3f}")

    print(f"\n3. CONTROLS at N={N_PRIMARY} -- one worker measured first, then {workers} workers x {N_DRAW} draws each kind")
    pool_list = np.flatnonzero(pool).tolist()
    with mp.Pool(1) as pl:
        kind, out1, rss = pl.map(_ctrl_worker, [("pool", N_PRIMARY, POOL_COUNT, [0], pool_list)])[0]
    print(f"  one worker: RSS {rss:.0f} MB after one draw  ->  {workers} workers ~ {workers*rss/1e3:.1f} GB")
    S_in = B.score(I1, sim4(I1, N_PRIMARY, SEEDS[0], nan1, nan2, (lambda p: p)(np.isin(np.arange(N), np.random.default_rng(300000).choice(np.flatnonzero(c2), size=POOL_COUNT, replace=False))), prio=None), N_PRIMARY)
    assert abs(out1[0][1] - S_in["net_bp"]) < 1e-12, "[CHUNK]"
    jobs = [("pool", N_PRIMARY, POOL_COUNT, list(range(w, N_DRAW, workers)), pool_list) for w in range(workers)] + \
           [("prio", N_PRIMARY, PRIO_COUNT, list(range(w, N_DRAW, workers)), pool_list) for w in range(workers)]
    with mp.Pool(workers) as pl:
        results = pl.map(_ctrl_worker, jobs)
    agg = {}
    for kind, out, _ in results:
        agg.setdefault(kind, []).extend(out)
    obs = res["se"][f"PRIO_N{N_PRIMARY}"]["mean"]
    for kind, label, ref in (("pool", "random cell-2 pools of 2,649", obs), ("prio", "random priorities of 303", res["se"][f"PRIO_N{N_PRIMARY}"]["mean"])):
        out = sorted(agg[kind]); net = np.array([o[1] for o in out]); p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size))
        if kind == "prio":
            ref_ = res["se"][f"NOPRIO_N{N_PRIMARY}"]["mean"]; delta_obs = obs - ref_; deltas = net - ref_
            p95 = float(np.quantile(deltas, .95)); se = float(deltas.std(ddof=1) / np.sqrt(deltas.size)); edge = delta_obs - p95
            res["control"][kind] = dict(observed_delta=float(delta_obs), p50=float(np.median(deltas)), p95=p95, se=se, margin_se=float(edge / se), inside=bool(delta_obs <= p95))
            print(f"  {label:32s} priority delta {delta_obs:+.3f}   random-priority deltas p50 {np.median(deltas):+.3f}  p95 {p95:+.3f} (±{se:.3f})   margin {edge/se:+.1f} SE   "
                  f"{'inside the null' if delta_obs <= p95 else 'beats the null'}")
        else:
            edge = obs - p95
            res["control"][kind] = dict(observed=float(obs), p5=float(np.quantile(net, .05)), p50=float(np.median(net)), p95=p95, se=se, margin_se=float(edge / se),
                                        passes=bool(edge > 0 and abs(edge) >= 2 * se), unresolved=bool(abs(edge) < 2 * se), util=float(np.mean([o[2] for o in out])))
            q = res["control"][kind]
            print(f"  {label:32s} book {obs:+.3f}   random p5 {q['p5']:+.3f}  p50 {q['p50']:+.3f}  p95 {p95:+.3f} (±{se:.3f})   margin {edge/se:+.1f} SE   "
                  f"{'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}   util ctrl {100*q['util']:.1f}%")
    print("  [CHUNK] worker draw 0 == in-process")

    s4 = res["se"][f"PRIO_N{N_PRIMARY}"]; cp = res["control"]["pool"]
    T1 = bool(s4["mean"] > 0 and s4["t"] >= 2); T2 = bool(cp["passes"]); T3 = bool(s4["mean21"] > 0 and s4["t21"] >= 2)
    res["bar"] = dict(T1=T1, T2=T2, T3=T3, candidate=bool(T1 and T2 and T3))
    print(f"\n4. THE BAR -- N={N_PRIMARY}, priority, 1% borrow")
    print(f"    T1 net > 0 by 2 SE               : {T1}   ({s4['mean']:+.3f} ± {s4['se']:.3f}, {s4['t']:+.1f} SE)")
    print(f"    T2 > random-pool p95             : {T2}   (margin {cp['margin_se']:+.1f} SE)")
    print(f"    T3 2021-2026 net > 0 by 2 SE     : {T3}   ({s4['mean21']:+.3f} ± {s4['se21']:.3f}, {s4['t21']:+.1f} SE)")
    print(f"    CANDIDATE under the principal's rule: {res['bar']['candidate']}   (no holdout is read by this runner)")
    pt = res["per_trade"]; b = lambda arm, n_: res["se"][f"{arm}_N{n_}"]["mean"]
    print("\n5. PREDICTIONS")
    print(f"    X-a pool +88..+96 gross, net +52..+62; 2021+ above; prio sub-cell above mean : {pt['pool|pooled']['gross']:+.2f}, {pt['pool|pooled']['net']:+.2f}; 2021+ {pt['pool|2021-2026']['gross']:+.2f}; prio {pt['priority sub-cell|pooled']['gross']:+.2f} ± {pt['priority sub-cell|pooled']['se']:.1f}")
    print(f"    X-b monotone in N; N10 +2.7..+3.4, N4 +5..+7, N2 +6..+9 : " + "  ".join(f"N{n_}:{b('PRIO', n_):+.2f}" for n_ in NS) + f";  util N10/N4/N2 {100*res['books']['PRIO_N10_s419']['utilisation']:.0f}/{100*res['books']['PRIO_N4_s419']['utilisation']:.0f}/{100*res['books']['PRIO_N2_s419']['utilisation']:.0f}%")
    print(f"    X-c priority +0.2..+0.8 at N4, <= +0.1 at N10, inside random-priority null : N4 {res['se']['PRIO_delta_N4']['mean']:+.3f}, N10 {res['se']['PRIO_delta_N10']['mean']:+.3f}, {'inside' if res['control']['prio']['inside'] else 'beats'}")
    print(f"    X-d N4 beats random pools by > 2 SE : margin {cp['margin_se']:+.1f} SE")
    print(f"    X-e 10% borrow costs 0.3..0.7 at N4; LONG N4 +3..+5 at ~40% : borrow {b('PRIO', 4) - b('PRIO-b10', 4):+.3f}; LONG {b('LONG', 4):+.3f} util {100*res['books']['LONG_N4_s419']['utilisation']:.0f}%")
    print(f"    X-f |r|>50% variant moves the mean < 5 bp : {pt['pool |r|<=50%|pooled']['gross'] - pt['pool|pooled']['gross']:+.2f}")
    print(f"    X-g T1, T2, T3 all hold : {T1}, {T2}, {T3}")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT}   total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.run:
        run(a.workers)

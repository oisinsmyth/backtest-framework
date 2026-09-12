"""D433 -- cell 2 & top-DV tercile, both sides, t+5, 10-slot book, with Sharpe, on holdout2. Bar committed in 8d27f03.
Reads the opener's cache only (temp/d433_oos2_panel.npz); references from the two spent caches; nothing is opened.

usage:  uv run python -u scripts/run_d433_holdout2.py --run [--workers 8]
"""
import argparse, importlib.util, json, multiprocessing as mp, os, pathlib, sys, time
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
R31 = _load("d431r", "run_d431_shorts_union.py"); R30 = R31.R30; R28 = R31.R28
sim4, dist, show, concentration, with_borrow, union = R28.sim4, R28.dist, R28.show, R28.concentration, R28.with_borrow, R31.union

OOS2_CACHE = REPO / "temp" / "d433_oos2_panel.npz"
OOS2_FIX = REPO / "data/fixtures/us_shorts_daily_holdout2.csv.gz"; OOS2_EVJ = REPO / "data/fixtures/us_shorts_daily_holdout2_events.json"
INPUTS = REPO / "temp" / "d433_oos2_inputs.npz"
OUT = REPO / "data" / "d433_oos2.json"
HOLD, SEEDS, NS, N_PRIMARY, N_DRAW, N_PERM, N_BOOT = 5, (419, 4190, 41900), (5, 10, 20), 10, 100, 200, 1000
DV_CUT = 186623861.92063487        # D432 m2.cuts[1], frozen
B1, B10 = 0.01, 0.10


def sharpe(ser):
    s = ser.std(ddof=1); return float(ser.mean() / s * np.sqrt(252)) if s > 0 else float("nan")


def sharpe_boot(ser, dates, n_boot=N_BOOT, seed=7):
    mon = np.array([str(x)[:7] for x in dates]); keys, inv = np.unique(mon, return_inverse=True)
    groups = [np.flatnonzero(inv == k) for k in range(keys.size)]
    rng = np.random.default_rng(seed); vals = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, keys.size, keys.size); x = np.concatenate([ser[groups[p]] for p in pick]); vals[b] = sharpe(x)
    return float(np.nanstd(vals, ddof=1))


def perm_within_day(vals, t, mask, rng):
    idx = np.flatnonzero(mask); base = idx[np.lexsort((np.arange(idx.size), t[idx]))]; perm = idx[np.lexsort((rng.random(idx.size), t[idx]))]
    out = vals.copy(); out[perm] = vals[base]; return out


def _ctrl_worker(args):
    n_slots, count, draws, npz = args
    import psutil
    Bw = _load("d419w", "run_d419_book.py")
    z = np.load(npz, allow_pickle=False); I = {k: z[k] for k in z.files}; N = len(I["t"])
    nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan); base = np.flatnonzero(I["c2"]); out = []
    for dr in draws:
        rng = np.random.default_rng(300000 + dr)
        pool = np.zeros(N, bool); pool[rng.choice(base, size=count, replace=False)] = True
        R = sim4(I, n_slots, SEEDS[0], nan1, nan2, pool); S = Bw.score(I, R, n_slots); assert S["recon_rel"] < 1e-9, "[RECON] control"
        out.append((dr, S["net_bp"], S["utilisation"]))
    return out, psutil.Process(os.getpid()).memory_info().rss / 1e6


def book_stats(Bw, I, pool, n_slots, seeds, label, res):
    series = []
    for seed in seeds:
        R = sim4(I, n_slots, seed, np.full(len(I["t"]), np.nan), np.full((len(I["t"]), HOLD), np.nan), pool); S = Bw.score(I, R, n_slots); assert S["recon_rel"] < 1e-9, f"[RECON] {label}"
        series.append((S["net_series"], S["gross_series"], R["d0"], S))
    d0 = series[0][2]; ds = I["dates"][d0:]
    net = np.mean([s[0] for s in series], axis=0); gross = np.mean([s[1] for s in series], axis=0)
    se_, mean = Bw.block_boot(net, ds); S0 = series[0][3]
    out = dict(net_bp=float(1e4 * mean), se=float(1e4 * se_), nets=[float(s[3]["net_bp"]) for s in series], gross_bp=float(1e4 * gross.mean()),
               sharpe_net=sharpe(net), sharpe_net_se=sharpe_boot(net, ds), sharpe_gross=sharpe(gross), daily_sd_bp=float(1e4 * net.std(ddof=1)),
               util=float(S0["utilisation"]), trades=int(S0["trades"]), per_trade=float(S0["trade_mean_bp"]), cost_bp=float(S0["cost_bp"]))
    res["books"][label] = out
    print(f"  {label:34s} N {n_slots:2d}  gross {out['gross_bp']:+6.3f}  net {out['net_bp']:+6.3f} ± {out['se']:.3f}  util {100*out['util']:4.1f}%  trades {out['trades']:5,}  per trade {out['per_trade']:+6.2f}   "
          f"seeds {' '.join(f'{x:+.2f}' for x in out['nets'])}   SHARPE net {out['sharpe_net']:+.2f} ± {out['sharpe_net_se']:.2f}  gross {out['sharpe_gross']:+.2f}   daily sd {out['daily_sd_bp']:.0f} bp")
    return out, net


def run(workers):
    t0 = time.time()
    assert OOS2_CACHE.exists(), "[DOOR] run scripts/d433_oos2_loader.py --spend-the-holdout first (the only opener)"
    assert not OUT.exists(), "[ONE-READ] data/d433_oos2.json exists; not re-run"
    print("D433  cell 2 & top-DV tercile, both sides, t+5, 10 slots, with Sharpe -- on holdout2, from the opener's cache\n      the bar was committed in 8d27f03 BEFORE this ran\n")
    Bw = _load("d419w", "run_d419_book.py"); FL = _load("d422f", "d422_stack_flags.py"); RF = _load("d426f", "d426_rung_flags.py"); D = Bw.D
    d32 = json.loads((REPO / "data" / "d432_mechanisms.json").read_text(encoding="utf-8")); assert abs(d32["m2"]["cuts"][1] - DV_CUT) < 1e-6, "[CUT] frozen cut != D432's artefact"
    # references from the two spent caches, and [P2]: D432's DV-TOP-C2 book on the union
    Pa = D.load_panel(verbose=False); Pb = R30.load_panel_from(D, R30.HOLDOUT_FIX, R30.HOLDOUT_EVJ, R30.HOLDOUT_CACHE, verbose=False)
    Ia, fla, Fa, Xa, _ = R30.pipeline(Bw, FL, RF, Pa); Ib, flb, Fb, Xb, _ = R30.pipeline(Bw, FL, RF, Pb)
    dva = D.X.roll_mean_T(Pa["CL"] * Pa["VOL"])[Ia["t"], Ia["i"]]; dvb = D.X.roll_mean_T(Pb["CL"] * Pb["VOL"])[Ib["t"], Ib["i"]]
    Iu, is_b = union(Ia, Ib); dvu = np.concatenate([dva, dvb]); top_u = Iu["c2"] & (dvu >= DV_CUT)
    res = dict(books={}, ladder={}, obj={}, conc={}, null=None, control=None, by_year={}, bar={}, counts={})
    print("REFERENCES (spent data, from caches)")
    ref, _ = book_stats(Bw, with_borrow(Iu, B1), top_u, 10, SEEDS, "union  top-DV cell 2 (D432's book)", res)
    for seed in SEEDS:
        assert abs(res["books"]["union  top-DV cell 2 (D432's book)"]["nets"][SEEDS.index(seed)] - d32["books"][f"DV-TOP-C2_s{seed}"]["net_bp"]) < 1e-12, f"[P2] D432 seed {seed}"
    print("  [P2]   D432's top-DV cell-2 book reproduces on every seed")
    book_stats(Bw, with_borrow(Ia, B1), Ia["c2"] & (dva >= DV_CUT), 10, SEEDS, "in-sample  top-DV cell 2", res)
    book_stats(Bw, with_borrow(Ib, B1), Ib["c2"] & (dvb >= DV_CUT), 10, SEEDS, "holdout 1  top-DV cell 2", res)

    print("\nHOLDOUT2 -- the one read, from the cache")
    P = R30.load_panel_from(D, OOS2_FIX, OOS2_EVJ, OOS2_CACHE, verbose=False)
    I, fl, F, X, info = R30.pipeline(Bw, FL, RF, P)
    dv = D.X.roll_mean_T(P["CL"] * P["VOL"])[I["t"], I["i"]]
    t, i, side, E, c2, rb = I["t"], I["i"], I["side"], I["E"], I["c2"], I["r_base"]; N = len(t); T = int(I["T"][0]); SYM = I["symbols"]; dates = I["dates"]
    yr = np.array([int(str(x)[:4]) for x in dates[t]]); top = c2 & (dv >= DV_CUT)
    I1, I10 = with_borrow(I, B1), with_borrow(I, B10)
    cheap = E < R30.PRICE_CUT; R2, L1 = X["R2"], X["L1"]; full = L1 & cheap
    res["counts"] = dict(names=len(SYM), touches=N, cell2=int(c2.sum()), top=int(top.sum()), r2=int(R2.sum()), long_pool=int(X["pool"].sum()), short_pool=int((full & (side < 0)).sum()),
                         holdout_medians=info["medians"], top_2018=int((top & (yr >= 2018)).sum()), top_2021=int((top & (yr >= 2021)).sum()))
    cc = res["counts"]
    print(f"  [COUNTS] {cc['names']} names; touches {N:,}  cell 2 {cc['cell2']:,}  TOP-DV cell 2 {cc['top']:,}  (expected ~66,000 / ~9,400 / ~3,100)   second touch & cell 2 {cc['r2']:,}  long pool {cc['long_pool']}  short pool {cc['short_pool']}")
    print(f"  holdout2's own cell-2 medians (NOT used): REV {info['medians'][0]:+.5f}  EFF {info['medians'][1]:.4f}  DV {info['medians'][2]/1e6:.1f}M")

    print("\n1. THE LADDER on holdout2 (pooled), with the dead layers for the record")
    for lab, m in (("all touches", np.ones(N, bool)), ("cell 2", c2), ("TOP-DV cell 2 = THE OBJECT", top), ("second touch & cell 2", R2), ("+ cheap", R2 & cheap), ("+ gap 3-20", full),
                   ("long pool (dead)", X["pool"]), ("short pool", full & (side < 0))):
        d = dist(rb, I1["cost"], m, f"{lab}"); res["ladder"][lab] = d; show(d)
    print("\n2. THE OBJECT, by window and side")
    wins = [("pooled", np.ones(N, bool)), ("2018+", yr >= 2018), ("2021-2026", yr >= 2021)]
    for lab, m in (("object", top), ("object long", top & (side > 0)), ("object short", top & (side < 0)), ("object |r|<=50%", top & (np.abs(rb) <= .5))):
        for wl, wm in wins:
            d = dist(rb, I1["cost"], m & wm, f"{lab}  {wl}"); d["net_b10"] = dist(rb, I10["cost"], m & wm, "")["net"] if "gross" in d else None; res["obj"][f"{lab}|{wl}"] = d
            if wl == "pooled" or lab == "object": show(d)
        print()
    for lab, m in (("object", top), ("object 2018+", top & (yr >= 2018))):
        q = concentration(rb, i, yr, m, SYM); res["conc"][lab] = q
        print(f"  {lab:14s} names {q['names']:4,}  to half P&L {q['to_half']:3d}  top1 {q['top1']:4.1f}%  top5 {q['top5']:4.1f}%  top10 {q['top10']:4.1f}%  years + {q['years_pos']}/{q['years']}  top name {q['top_name']}  top year {q['top_year']} {q['top_year_share']:.1f}%")
    kk = np.flatnonzero(top); tp = kk[np.nanargmax(rb[kk])]; nm = int(i[tp]); d_ = int(t[tp])
    print(f"  top trade: {SYM[nm]} {dates[d_]} side {int(side[tp]):+d} entry {E[tp]:.2f} -> {P['CL'][min(d_ + HOLD, T - 1), nm]:.2f}  r {1e4*rb[tp]:+.0f} bp = {100*rb[tp]/np.nansum(rb[top]):.1f}% of P&L;  closes " +
          " ".join(f"{P['CL'][d_ + j, nm]:.2f}" for j in range(0, min(HOLD + 1, T - d_))) + ";  volume " + " ".join(f"{P['VOL'][d_ + j, nm]/1e6:.1f}M" for j in range(0, min(HOLD + 1, T - d_))))
    print("  object by year: " + "  ".join(f"{y}:{1e4*np.nanmean(rb[top & (yr == y)]):+.0f}({int((top & (yr == y)).sum())})" for y in range(2010, 2027) if (top & (yr == y)).any()))

    print("\n3. THE PER-TRADE NULL -- the tercile's premium over the rest of holdout2's cell 2, within-day permutation")
    lab_ = top.astype(float); obs = float(rb[top].mean() - rb[c2 & ~top].mean()); rng = np.random.default_rng(433); draws = np.empty(N_PERM)
    for b in range(N_PERM):
        lp = perm_within_day(lab_, t, c2, rng) > 0.5; draws[b] = rb[lp & c2].mean() - rb[c2 & ~lp].mean()
    p95 = float(np.quantile(draws, .95)); se = float(draws.std(ddof=1) / np.sqrt(N_PERM)); edge = obs - p95
    res["null"] = dict(observed_bp=1e4 * obs, p50=float(1e4 * np.median(draws)), p95=1e4 * p95, se=1e4 * se, margin_se=float(edge / se), passes=bool(edge > 0 and abs(edge) >= 2 * se), unresolved=bool(abs(edge) < 2 * se))
    q = res["null"]; print(f"  premium {q['observed_bp']:+7.2f}   null p50 {q['p50']:+6.2f}  p95 {q['p95']:+6.2f} (±{q['se']:.2f})   margin {q['margin_se']:+.1f} SE   {'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}")

    print("\n4. THE BOOK on holdout2, with Sharpe")
    net10 = None
    for n_slots in NS:
        out, net = book_stats(Bw, I1, top, n_slots, SEEDS, f"holdout2  top-DV cell 2", res) if n_slots != N_PRIMARY else book_stats(Bw, I1, top, n_slots, SEEDS, "holdout2  top-DV cell 2  PRIMARY", res)
        if n_slots == N_PRIMARY: net10 = net; d0 = len(dates) - net.size
        res["books"][f"holdout2_N{n_slots}"] = out
    book_stats(Bw, I10, top, N_PRIMARY, SEEDS, "holdout2  top-DV cell 2  10% borrow", res)
    ys = np.array([str(x)[:4] for x in dates[d0:]]).astype(int)
    for y in range(2010, 2027):
        m = ys == y
        if m.any(): res["by_year"][str(y)] = float(1e4 * net10[m].mean())
    print("  the 10-slot book by year (net bp/bar): " + "  ".join(f"{y}:{v:+.1f}" for y, v in res["by_year"].items()))
    w21 = ys >= 2021; res["books"]["holdout2_N10_2021"] = dict(net_bp=float(1e4 * net10[w21].mean()), sharpe_net=sharpe(net10[w21]))
    print(f"  2021-2026: net {1e4*net10[w21].mean():+.3f}  Sharpe net {sharpe(net10[w21]):+.2f}")

    print(f"\n5. CONTROL at N={N_PRIMARY} -- random pools of {cc['top']:,} of holdout2's cell-2 events; one worker measured first")
    np.savez_compressed(INPUTS, **{k: v for k, v in I1.items()})
    with mp.Pool(1) as pl:
        out1, rss = pl.map(_ctrl_worker, [(N_PRIMARY, cc["top"], [0], str(INPUTS))])[0]
    print(f"  one worker: RSS {rss:.0f} MB  ->  {workers} workers ~ {workers*rss/1e3:.1f} GB")
    rng = np.random.default_rng(300000); p0 = np.zeros(N, bool); p0[rng.choice(np.flatnonzero(c2), size=cc["top"], replace=False)] = True
    S0 = Bw.score(I1, sim4(I1, N_PRIMARY, SEEDS[0], np.full(N, np.nan), np.full((N, HOLD), np.nan), p0), N_PRIMARY); assert abs(out1[0][1] - S0["net_bp"]) < 1e-12, "[CHUNK]"
    with mp.Pool(workers) as pl:
        results = pl.map(_ctrl_worker, [(N_PRIMARY, cc["top"], list(range(w, N_DRAW, workers)), str(INPUTS)) for w in range(workers)])
    out = sorted(o for oo, _ in results for o in oo); netc = np.array([o[1] for o in out])
    obs = res["books"]["holdout2  top-DV cell 2  PRIMARY"]["net_bp"]; p95 = float(np.quantile(netc, .95)); se_ = float(netc.std(ddof=1) / np.sqrt(netc.size)); edge = obs - p95
    res["control"] = dict(observed=obs, p5=float(np.quantile(netc, .05)), p50=float(np.median(netc)), p95=p95, se=se_, margin_se=float(edge / se_), passes=bool(edge > 0 and abs(edge) >= 2 * se_), unresolved=bool(abs(edge) < 2 * se_))
    q = res["control"]; print(f"  book {obs:+.3f}   random cell-2 pools p5 {q['p5']:+.3f}  p50 {q['p50']:+.3f}  p95 {p95:+.3f} (±{se_:.3f})   margin {q['margin_se']:+.1f} SE   {'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}\n  [CHUNK] worker draw 0 == in-process")

    ob = res["obj"]["object|pooled"]; bk = res["books"]["holdout2  top-DV cell 2  PRIMARY"]
    T1 = bool(ob["gross"] > 0 and ob["gross"] / ob["se"] >= 2); T1b = bool(ob["net"] > 0); T2 = bool(bk["net_bp"] > 0 and bk["net_bp"] / bk["se"] >= 2)
    T3 = bool(bk["sharpe_net"] > 0 and bk["sharpe_net"] / bk["sharpe_net_se"] >= 2); T4 = bool(q["passes"])
    res["bar"] = dict(T1=T1, T1b=T1b, T2=T2, T3=T3, T4=T4, candidate=bool(T1 and T1b and T2 and T3 and T4))
    print("\n6. THE BAR -- the object on holdout2")
    print(f"    T1  gross > 0 by 2 SE          : {T1}   ({ob['gross']:+.2f} ± {ob['se']:.2f}, {ob['gross']/ob['se']:+.1f} SE, n {ob['n']:,})")
    print(f"    T1b net > 0 at 1% borrow       : {T1b}  ({ob['net']:+.2f}; at 10% {ob['net_b10']:+.2f})")
    print(f"    T2  book net > 0 by 2 SE       : {T2}   ({bk['net_bp']:+.3f} ± {bk['se']:.3f})")
    print(f"    T3  book net Sharpe > 0 by 2 SE: {T3}   ({bk['sharpe_net']:+.2f} ± {bk['sharpe_net_se']:.2f}; gross Sharpe {bk['sharpe_gross']:+.2f})")
    print(f"    T4  book > random-pool p95     : {T4}   (margin {q['margin_se']:+.1f} SE)")
    print(f"    CANDIDATE: {res['bar']['candidate']}")
    L = res["ladder"]; ra, rb_ = res["books"]["in-sample  top-DV cell 2"], res["books"]["holdout 1  top-DV cell 2"]
    print("\n7. PREDICTIONS")
    print(f"    X-a tercile events 2,500-3,700                        : {cc['top']:,}")
    print(f"    X-b gross +18..+32, net -8..+6 (1%), -15..0 (10%), median +10..+25, win 51-53 : {ob['gross']:+.2f}, {ob['net']:+.2f}, {ob['net_b10']:+.2f}, med {ob['median']:+.2f}, win {ob['win']:.1f}%")
    print(f"    X-c dead layers stay dead: second touch within ±15 of cell 2; long pool <= 0 or inside 2 SE; short median << mean : second touch {L['second touch & cell 2'].get('gross', float('nan')):+.1f} vs cell 2 {L['cell 2']['gross']:+.1f}; long {L['long pool (dead)'].get('gross', float('nan')):+.1f} ± {L['long pool (dead)'].get('se', float('nan')):.1f}; short {L['short pool'].get('gross', float('nan')):+.1f} med {L['short pool'].get('median', float('nan')):+.1f}")
    print(f"    X-d book net -1.5..+1.0; Sharpe net -0.4..+0.4, gross +0.6..+1.6; above ctrl p50, below p95 : {bk['net_bp']:+.3f}; {bk['sharpe_net']:+.2f} / {bk['sharpe_gross']:+.2f}; vs p50 {obs - q['p50']:+.3f}, vs p95 {edge:+.3f}")
    print(f"    X-e references: in-sample Sharpe net 0..+0.5; holdout 1 -0.5..+0.2 : {ra['sharpe_net']:+.2f} ± {ra['sharpe_net_se']:.2f}; {rb_['sharpe_net']:+.2f} ± {rb_['sharpe_net_se']:.2f}")
    print(f"    X-f 2021-2026 gross above pooled                      : {res['obj']['object|2021-2026']['gross']:+.2f} vs {ob['gross']:+.2f}")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT}   total {time.time()-t0:.0f}s   HOLDOUT2 IS SPENT FOR THIS LINE.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.run:
        run(a.workers)

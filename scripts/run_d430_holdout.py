"""D430 -- the long book out of sample on us_shorts_daily_holdout, ONE read. Bar committed in 7dd4ff8 BEFORE this file.

--proof     in-sample fixture through the SAME parametrised path; must reproduce D413/D422/D429 bit-identically.
            Reads no holdout. If it fails, the holdout is not opened.
--holdout   reads data/fixtures/us_shorts_daily_holdout.csv.gz (+ _events.json) once, computes everything the
            pre-registration lists, writes data/d430_holdout.json, stops. holdout2 is never touched.

usage:  uv run python -u scripts/run_d430_holdout.py --proof
        uv run python -u scripts/run_d430_holdout.py --holdout [--workers 8]
"""
import argparse, importlib.util, json, multiprocessing as mp, os, pathlib, sys, time
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
R28 = _load("d428r", "run_d428_combined_book.py")        # light: sim4, dist, show, concentration
sim4, dist, show, concentration = R28.sim4, R28.dist, R28.show, R28.concentration

HOLDOUT_FIX = REPO / "data/fixtures/us_shorts_daily_holdout.csv.gz"
HOLDOUT_EVJ = REPO / "data/fixtures/us_shorts_daily_holdout_events.json"
# ADDENDUM: the fixture is opened ONLY by scripts/d430_oos_loader.py (a process without run_d411's [SPLIT] audit
# hook); this runner reads the cache it writes. Names carry no "holdout" so the hook, active here, has nothing to
# refuse -- and every other holdout path in this process stays refused.
HOLDOUT_CACHE = REPO / "temp" / "d430_oos_panel.npz"
HOLDOUT_INPUTS = REPO / "temp" / "d430_oos_inputs.npz"
OUT = REPO / "data" / "d430_oos.json"
D429 = REPO / "data" / "d429_long_book.json"

# ---- frozen from in-sample, to the digit (pre-registration §2)
CUTS = (-0.02473244344202641, 0.23669449533835638, 44370158.19015902)      # REV <=, EFF >, DV >
PRICE_CUT = 38.50639133333333
GAP_LO, GAP_HI, PRIO_LO, PRIO_HI = 3, 20, 3, 10
HOLD, SEEDS, NS, N_PRIMARY, N_DRAW, N_PERM = 5, (419, 4190, 41900), (1, 2, 3), 2, 100, 200
IBKR = 0.0035


# ------------------------------------------------------------------ the parametrised pipeline
def load_panel_from(D, fix, evj, cache, verbose=True):
    """D411's load_panel, verbatim, with the fixture, events file and cache as parameters."""
    if cache.exists():
        z = np.load(cache, allow_pickle=True)
        return {k: z[k] for k in ("OP", "HI", "LO", "CL", "VOL", "live", "elig")} | dict(dates=list(z["dates"]), symbols=list(z["symbols"]))
    t0 = time.time()
    panel, cleaned = D.RP.load_ragged(fix, evj, fee_bps=0.0)
    CL = np.ascontiguousarray(panel.closes.T); live = np.ascontiguousarray(panel.live.T)
    T, n = CL.shape
    OP, HI, LO, VOL = (np.full((T, n), np.nan) for _ in range(4))
    pos = {d: i for i, d in enumerate(panel.dates)}; sym = {s: i for i, s in enumerate(panel.symbols)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                b = st.bar; OP[t, i], HI[t, i], LO[t, i], VOL[t, i] = b.open, b.high, b.low, b.volume
    ev = json.loads(evj.read_text(encoding="utf-8"))
    RAWF = D.UF.raw_price_factor(panel, ev)
    DV = D.X.roll_mean_T(CL * VOL)
    elig = live & D.UF.floor_mask_v2(CL * RAWF, DV, live)
    if verbose:
        print(f"  panel {T} dates x {n} names in {time.time()-t0:.0f}s   elig {100*elig.mean():.1f}% of cells")
    cache.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, OP=OP, HI=HI, LO=LO, CL=CL, VOL=VOL, live=live, elig=elig, dates=np.array(panel.dates), symbols=np.array(panel.symbols))
    return dict(OP=OP, HI=HI, LO=LO, CL=CL, VOL=VOL, live=live, elig=elig, dates=list(panel.dates), symbols=list(panel.symbols))


def build_inputs_from(Bw, P):
    """D419's build_inputs with the cell-2 cuts FROZEN (not medians), plus the zone fields D421 attaches."""
    D, C, M, Z4, CS = Bw.D, Bw.C, Bw.M, Bw.Z4, Bw.CS
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g = A["Z"], A["good"]
    t = A["tt"][g]; i = Z["i"][g]; side = Z["side"][g]; r_base = A["r"][g]
    lg = np.log(np.where(P["CL"] > 0, P["CL"], np.nan))
    tr5 = D.trailing_ret(lg, 5); eff = C.path_efficiency(lg); DV = D.X.roll_mean_T(P["CL"] * P["VOL"])
    rev = tr5[t, i] * side; ef = eff[t, i]; dv = DV[t, i]
    fin = np.isfinite(rev) & np.isfinite(ef) & np.isfinite(dv)
    c2 = fin & (rev <= CUTS[0]) & (ef > CUTS[1]) & (dv > CUTS[2])
    T = P["CL"].shape[0]
    off = np.arange(1, HOLD + 1); rows = t[:, None] + off[None, :]; cols = np.repeat(i[:, None], HOLD, axis=1)
    gth = lambda A_: Z4.gather(A_, rows, cols, T)[0]
    OP, HI, LO, CL = gth(P["OP"]), gth(P["HI"]), gth(P["LO"]), gth(P["CL"])
    E = P["CL"][t, i]; ATR = atr[t, i]
    spread = CS.corwin_schultz(P["HI"].T, P["LO"].T, P["live"].T).T
    neutral = np.full_like(spread, np.nan)
    for tt in range(62, T):
        with np.errstate(invalid="ignore"):
            neutral[tt] = np.nanmedian(spread[tt - 62:tt - 2], axis=0)
    cost = neutral[t, i] + 2 * IBKR / E
    cost = np.where(np.isfinite(cost), cost, np.nanmedian(cost))
    I = dict(t=t, i=i, side=side, r_base=r_base, c2=c2, OP=OP, HI=HI, LO=LO, CL=CL, E=E, ATR=ATR, cost=cost, T=np.array([T]),
             dates=np.array(P["dates"]), symbols=np.array(P["symbols"]), a=Z["a"][g], lo=Z["lo"][g], hi=Z["hi"][g])
    assert np.all(I["a"] <= I["t"]) and np.all(I["lo"] < I["hi"]), "[ALIGN] zone table malformed"
    return I, dict(medians=(float(np.median(rev[fin])), float(np.median(ef[fin])), float(np.median(dv[fin]))))


def masks(I, fl, F):
    t, side, E, c2 = I["t"], I["side"], I["E"], I["c2"]
    g = F["prev_gap"]
    R2 = fl["s2any"] & c2
    L1 = R2 & (g >= GAP_LO) & (g <= GAP_HI)
    cheap = E < PRICE_CUT
    pool = L1 & cheap & (side > 0)
    prio = pool & F["opp_prior"] & (g >= PRIO_LO) & (g <= PRIO_HI)
    ladder = [("all touches", np.ones(len(t), bool)), ("cell 2", c2), ("second touch & cell 2", R2), ("+ cheap", R2 & cheap),
              ("+ gap 3-20", L1 & cheap), ("long = THE POOL", pool), ("the short half", L1 & cheap & (side < 0)), ("priority sub-cell", prio)]
    return dict(R2=R2, L1=L1, pool=pool, prio=prio, ladder=ladder, base_long=c2 & (side > 0))


def pipeline(Bw, FL, RF, P):
    I, info = build_inputs_from(Bw, P)
    fl = FL.flags(I, P); F = RF.flags(I, fl); X = masks(I, fl, F)
    return I, fl, F, X, info


def perm_within_day(vals, t, mask, rng):
    idx = np.flatnonzero(mask); base = idx[np.lexsort((np.arange(idx.size), t[idx]))]; perm = idx[np.lexsort((rng.random(idx.size), t[idx]))]
    out = vals.copy(); out[perm] = vals[base]; return out


def _ctrl_worker(args):
    n_slots, count, draws, npz = args
    import psutil
    Bw = _load("d419w", "run_d419_book.py")
    z = np.load(npz, allow_pickle=False); I = {k: z[k] for k in z.files}; N = len(I["t"])
    nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan); base = np.flatnonzero(I["c2"] & (I["side"] > 0)); out = []
    for dr in draws:
        rng = np.random.default_rng(300000 + dr)
        pool = np.zeros(N, bool); pool[rng.choice(base, size=count, replace=False)] = True
        R = sim4(I, n_slots, SEEDS[0], nan1, nan2, pool); S = Bw.score(I, R, n_slots); assert S["recon_rel"] < 1e-9, "[RECON] control"
        out.append((dr, S["net_bp"], S["utilisation"]))
    return out, psutil.Process(os.getpid()).memory_info().rss / 1e6


# ------------------------------------------------------------------ proof
def proof():
    t0 = time.time()
    print("D430 --proof: the parametrised pipeline on the IN-SAMPLE fixture must reproduce D413 / D422 / D429. No holdout is read.\n")
    Bw = _load("d419w", "run_d419_book.py"); FL = _load("d422f", "d422_stack_flags.py"); RF = _load("d426f", "d426_rung_flags.py")
    D = Bw.D
    P0 = D.load_panel(verbose=False)
    P1 = load_panel_from(D, D.FIX, D.EVJ, REPO / "temp" / "d430_proof_panel.npz", verbose=True)
    for k in ("OP", "HI", "LO", "CL", "VOL", "live", "elig"):
        assert np.array_equal(P0[k], P1[k], equal_nan=True), f"[LOADER] {k} differs between D411's loader and the parametrised one"
    assert list(P0["dates"]) == list(P1["dates"]) and list(P0["symbols"]) == list(P1["symbols"]), "[LOADER] grid"
    print("  [LOADER] parametrised loader == D411's on the in-sample fixture, every array, every cell")
    I, fl, F, X, info = pipeline(Bw, FL, RF, P1)
    n = len(I["t"]); c2 = int(I["c2"].sum()); r2 = int(X["R2"].sum()); pl = int(X["pool"].sum()); pr = int(X["prio"].sum())
    assert (n, c2, r2, pl, pr) == (180050, 26024, 9411, 1416, 165), f"[P2] counts {(n, c2, r2, pl, pr)}"
    assert all(abs(a - b) < 1e-9 for a, b in zip(info["medians"], CUTS)), f"[P2] in-sample medians {info['medians']} != frozen cuts"
    d29 = json.loads(D429.read_text(encoding="utf-8"))
    d = dist(I["r_base"], I["cost"], X["pool"], "long pool")
    ref = d29["per_trade"]["long pool|pooled"]
    assert d["n"] == ref["n"] and abs(d["gross"] - ref["gross"]) < 1e-9 and abs(d["net"] - ref["net"]) < 1e-9, "[P2] D429 trade table"
    N = n; nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan)
    for seed in SEEDS:
        S = Bw.score(I, sim4(I, 3, seed, nan1, nan2, X["pool"], prio=X["prio"]), 3); r = d29["books"][f"PRIO_N3_s{seed}"]
        assert abs(S["net_bp"] - r["net_bp"]) < 1e-12 and abs(S["gross_bp"] - r["gross_bp"]) < 1e-12 and S["trades"] == r["trades"], f"[P2] D429 book seed {seed}"
    print(f"  [P2]   180,050 / 26,024 / 9,411 / 1,416 / 165; the frozen cuts are the in-sample medians to 1e-9; D429's trade table and its N=3 books reproduce on every seed")
    print(f"\nPROOF PASSED in {time.time()-t0:.0f}s. The holdout may be opened, once, with --holdout.")


# ------------------------------------------------------------------ the read
def holdout(workers):
    t0 = time.time()
    assert HOLDOUT_FIX.name == "us_shorts_daily_holdout.csv.gz" and "holdout2" not in HOLDOUT_FIX.name, "[FILE] wrong fixture"
    assert not OUT.exists(), "[ONE-READ] data/d430_oos.json exists: this file has been read for this line already. Not re-run."
    assert HOLDOUT_CACHE.exists(), "[DOOR] no panel cache: run scripts/d430_oos_loader.py --spend-the-holdout first (the only opener)"
    print("D430 --holdout: the one read, from the opener's cache.  The bar was committed in 7dd4ff8 BEFORE this ran; the door in the ADDENDUM.\n")
    Bw = _load("d419w", "run_d419_book.py"); FL = _load("d422f", "d422_stack_flags.py"); RF = _load("d426f", "d426_rung_flags.py")
    P = load_panel_from(Bw.D, HOLDOUT_FIX, HOLDOUT_EVJ, HOLDOUT_CACHE, verbose=True)
    I, fl, F, X, info = pipeline(Bw, FL, RF, P)
    t, i, side, E, c2, rb, cost = I["t"], I["i"], I["side"], I["E"], I["c2"], I["r_base"], I["cost"]
    N = len(t); T = int(I["T"][0]); SYM = I["symbols"]; dates = I["dates"]; yr = np.array([int(str(x)[:4]) for x in dates[t]])
    pool, prio = X["pool"], X["prio"]
    res = dict(counts={}, holdout_medians=info["medians"], ladder={}, null=None, conc={}, books={}, se={}, by_year={}, control=None, bar={})
    res["counts"] = dict(names=len(SYM), touches=N, cell2=int(c2.sum()), r2=int(X["R2"].sum()), pool=int(pool.sum()), prio=int(prio.sum()),
                         pool_2018=int((pool & (yr >= 2018)).sum()), pool_2021=int((pool & (yr >= 2021)).sum()), per_day=float(pool.sum() / T))
    cc = res["counts"]
    print(f"  [COUNTS] {cc['names']} names; touches {N:,}  cell 2 {cc['cell2']:,}  second touch & cell 2 {cc['r2']:,}  POOL {cc['pool']:,} ({cc['per_day']:.3f}/day)  priority {cc['prio']}   "
          f"(scaled expectation: ~92,000 / ~13,300 / ~4,800 / ~720 / ~85)")
    print(f"  holdout's own cell-2 medians (NOT used): REV {info['medians'][0]:+.5f}  EFF {info['medians'][1]:.4f}  DV {info['medians'][2]/1e6:.1f}M   vs frozen {CUTS[0]:+.5f} / {CUTS[1]:.4f} / {CUTS[2]/1e6:.1f}M")

    print("\n1. THE LADDER, per trade")
    wins = [("pooled", np.ones(N, bool)), ("2018+", yr >= 2018), ("2021-2026", yr >= 2021)]
    for lab, m in X["ladder"]:
        for wl, wm in wins:
            d = dist(rb, cost, m & wm, f"{lab}  {wl}"); res["ladder"][f"{lab}|{wl}"] = d
            if wl == "pooled" or lab == "long = THE POOL":
                show(d)
        print()
    d = dist(rb, cost, pool & (np.abs(rb) <= .5), "THE POOL |r|<=50%"); res["ladder"]["pool |r|<=50%|pooled"] = d; show(d)
    for lab, m in (("pool", pool), ("pool 2018+", pool & (yr >= 2018)), ("pool 2021-2026", pool & (yr >= 2021))):
        if m.sum() >= 30:
            q = concentration(rb, i, yr, m, SYM); res["conc"][lab] = q
            print(f"  {lab:16s} names {q['names']:4,}  to half P&L {q['to_half']:3d}  top1 {q['top1']:4.1f}%  top5 {q['top5']:4.1f}%  top10 {q['top10']:4.1f}%  years + {q['years_pos']}/{q['years']}  top name {q['top_name']}  top year {q['top_year']} {q['top_year_share']:.1f}%")
    kk = np.flatnonzero(pool); top = kk[np.nanargmax(rb[kk])]; nm = int(i[top]); d_ = int(t[top])
    print(f"  top trade: {SYM[nm]} {dates[d_]} entry {E[top]:.2f} -> {P['CL'][min(d_ + HOLD, T - 1), nm]:.2f}  r {1e4*rb[top]:+.0f} bp = {100*rb[top]/np.nansum(rb[pool]):.1f}% of P&L;  closes " +
          " ".join(f"{P['CL'][d_ + j, nm]:.2f}" for j in range(0, min(HOLD + 1, T - d_))) + ";  volume " + " ".join(f"{P['VOL'][d_ + j, nm]/1e6:.1f}M" for j in range(0, min(HOLD + 1, T - d_))))
    res["top_trade"] = dict(sym=str(SYM[nm]), date=str(dates[d_]), entry=float(E[top]), r_bp=float(1e4 * rb[top]))
    print("  the pool by year: mean bp (n)  " + "  ".join(f"{y}:{1e4*np.nanmean(rb[pool & (yr == y)]):+.0f}({int((pool & (yr == y)).sum())})" for y in range(2010, 2027) if (pool & (yr == y)).any()))

    print("\n2. THE PER-TRADE NULL -- the pool's premium over the holdout's other cell-2 long events, within-day permutation")
    base = X["base_long"]; lab_ = pool.astype(float)
    obs = float(rb[pool].mean() - rb[base & ~pool].mean()); rng = np.random.default_rng(430); draws = np.empty(N_PERM)
    for b in range(N_PERM):
        lp = perm_within_day(lab_, t, base, rng) > 0.5; draws[b] = rb[lp & base].mean() - rb[base & ~lp].mean()
    p95 = float(np.quantile(draws, .95)); se = float(draws.std(ddof=1) / np.sqrt(N_PERM)); edge = obs - p95
    res["null"] = dict(observed_bp=1e4 * obs, p50=float(1e4 * np.median(draws)), p95=1e4 * p95, se=1e4 * se, margin_se=float(edge / se), passes=bool(edge > 0 and abs(edge) >= 2 * se), unresolved=bool(abs(edge) < 2 * se))
    q = res["null"]; print(f"  premium {q['observed_bp']:+7.2f}   null p50 {q['p50']:+6.2f}  p95 {q['p95']:+6.2f} (±{q['se']:.2f})   margin {q['margin_se']:+.1f} SE   {'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}")

    print("\n3. THE BOOK -- N in {1,2,3}, three seeds, with and without the priority")
    nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan); series = {}
    for n_slots in NS:
        for arm, pr in (("PRIO", prio), ("NOPRIO", None)):
            for seed in SEEDS:
                R = sim4(I, n_slots, seed, nan1, nan2, pool, prio=pr); S = Bw.score(I, R, n_slots); assert S["recon_rel"] < 1e-9, "[RECON]"
                series[(arm, n_slots, seed)] = S["net_series"]; d0 = R["d0"]
                res["books"][f"{arm}_N{n_slots}_s{seed}"] = {k: v for k, v in S.items() if not k.endswith("_series") and k != "run_dist"}
    ds = dates[d0:]; ys = np.array([str(x)[:4] for x in ds]).astype(int); w18 = ys >= 2018; w21 = ys >= 2021
    print(f"  [RECON] all\n  {'N':>3s} {'arm':7s} {'gross':>7s} {'net':>7s} {'cost':>6s} {'util':>6s} {'trades':>6s} {'per trade':>9s}   net by seed            pooled ± SE      2018+ ± SE       2021-26 ± SE")
    for n_slots in NS:
        for arm in ("PRIO", "NOPRIO"):
            S = res["books"][f"{arm}_N{n_slots}_s{SEEDS[0]}"]; nets = [res["books"][f"{arm}_N{n_slots}_s{s}"]["net_bp"] for s in SEEDS]
            ser = np.mean([series[(arm, n_slots, s)] for s in SEEDS], axis=0)
            se_, mean = Bw.block_boot(ser, ds); se18, m18 = Bw.block_boot(ser[w18], ds[w18]); se21, m21 = Bw.block_boot(ser[w21], ds[w21])
            res["se"][f"{arm}_N{n_slots}"] = dict(mean=float(1e4 * mean), se=float(1e4 * se_), mean18=float(1e4 * m18), se18=float(1e4 * se18), mean21=float(1e4 * m21), se21=float(1e4 * se21), nets=nets)
            print(f"  {n_slots:3d} {arm:7s} {S['gross_bp']:+7.3f} {S['net_bp']:+7.3f} {S['cost_bp']:6.3f} {100*S['utilisation']:5.1f}% {S['trades']:6,} {S['trade_mean_bp']:+9.2f}   "
                  + " ".join(f"{x:+.3f}" for x in nets) + f"   {1e4*mean:+6.3f} ± {1e4*se_:.3f}   {1e4*m18:+6.3f} ± {1e4*se18:.3f}   {1e4*m21:+6.3f} ± {1e4*se21:.3f}")
        print()
    ser2 = np.mean([series[("PRIO", N_PRIMARY, s)] for s in SEEDS], axis=0)
    for y in range(2010, 2027):
        m = ys == y
        if m.any(): res["by_year"][str(y)] = float(1e4 * ser2[m].mean())
    print("  the N=2 book by year: " + "  ".join(f"{y}:{v:+.1f}" for y, v in res["by_year"].items()))

    print(f"\n4. CONTROL at N={N_PRIMARY} -- random pools of {cc['pool']} of the holdout's cell-2 LONG events; one worker measured first")
    np.savez_compressed(HOLDOUT_INPUTS, **{k: v for k, v in I.items()})
    with mp.Pool(1) as pl:
        out1, rss = pl.map(_ctrl_worker, [(N_PRIMARY, cc["pool"], [0], str(HOLDOUT_INPUTS))])[0]
    print(f"  one worker: RSS {rss:.0f} MB  ->  {workers} workers ~ {workers*rss/1e3:.1f} GB")
    rng = np.random.default_rng(300000); p0 = np.zeros(N, bool); p0[rng.choice(np.flatnonzero(base), size=cc["pool"], replace=False)] = True
    S0 = Bw.score(I, sim4(I, N_PRIMARY, SEEDS[0], nan1, nan2, p0), N_PRIMARY); assert abs(out1[0][1] - S0["net_bp"]) < 1e-12, "[CHUNK]"
    with mp.Pool(workers) as pl:
        results = pl.map(_ctrl_worker, [(N_PRIMARY, cc["pool"], list(range(w, N_DRAW, workers)), str(HOLDOUT_INPUTS)) for w in range(workers)])
    out = sorted(o for oo, _ in results for o in oo); net = np.array([o[1] for o in out])
    obs = res["se"][f"PRIO_N{N_PRIMARY}"]["mean"]; p95 = float(np.quantile(net, .95)); se_ = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs - p95
    res["control"] = dict(observed=obs, p5=float(np.quantile(net, .05)), p50=float(np.median(net)), p95=p95, se=se_, margin_se=float(edge / se_),
                          passes=bool(edge > 0 and abs(edge) >= 2 * se_), unresolved=bool(abs(edge) < 2 * se_), util=float(np.mean([o[2] for o in out])))
    q = res["control"]; print(f"  book {obs:+.3f}   random long pools p5 {q['p5']:+.3f}  p50 {q['p50']:+.3f}  p95 {p95:+.3f} (±{se_:.3f})   margin {q['margin_se']:+.1f} SE   "
                              f"{'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}   util ctrl {100*q['util']:.1f}%\n  [CHUNK] worker draw 0 == in-process")

    dp = res["ladder"]["long = THE POOL|pooled"]; s2 = res["se"][f"PRIO_N{N_PRIMARY}"]
    T1 = bool(dp["gross"] > 0 and dp["gross"] / dp["se"] >= 2); T1b = bool(dp["net"] > 0); T2 = bool(s2["mean"] > 0 and s2["mean"] / s2["se"] >= 2); T3 = bool(q["passes"])
    res["bar"] = dict(T1=T1, T1b=T1b, T2=T2, T3=T3, candidate=bool(T1 and T1b and T2 and T3),
                      reading=("CANDIDATE: all four hold" if (T1 and T1b and T2 and T3) else ("signal generalises across names; the book's capacity is too thin to prove at 803 names" if (T1 and T1b and T3 and not T2)
                               else ("the construction does not generalise across names" if not T1 else "partial -- see the record"))))
    print("\n5. THE BAR")
    print(f"    T1  pool gross > 0 by 2 SE        : {T1}   ({dp['gross']:+.2f} ± {dp['se']:.2f}, {dp['gross']/dp['se']:+.1f} SE, n {dp['n']:,})")
    print(f"    T1b pool net > 0                   : {T1b}  ({dp['net']:+.2f}, {dp['net']/dp['se']:+.1f} SE)")
    print(f"    T2  N=2 book net > 0 by 2 SE       : {T2}   ({s2['mean']:+.3f} ± {s2['se']:.3f}, {s2['mean']/s2['se']:+.1f} SE)")
    print(f"    T3  N=2 book > random-pool p95     : {T3}   (margin {q['margin_se']:+.1f} SE)")
    print(f"    READING: {res['bar']['reading']}")
    print("\n6. PREDICTIONS")
    print(f"    X-a pool 580-870                            : {cc['pool']}")
    lad = {k.split('|')[0]: v for k, v in res['ladder'].items() if k.endswith('|pooled')}
    print(f"    X-b ladder keeps shape, rungs 50-80% of in-sample : " + "  ".join(f"{k}:{v.get('gross', float('nan')):+.1f}" for k, v in lad.items() if k in ('all touches', 'cell 2', 'second touch & cell 2', '+ cheap', '+ gap 3-20', 'long = THE POOL')))
    print(f"    X-c pool gross +35..+65, net 0..+30, median > mean, win 54-60 : {dp['gross']:+.2f}, {dp['net']:+.2f}, med {dp['median']:+.2f}, win {dp['win']:.1f}%")
    print(f"    X-d permutation null passes                  : margin {res['null']['margin_se']:+.1f} SE")
    print(f"    X-e N=2 book +1..+3.5, T2 fails, >= 2 seeds positive, T3 passes : {s2['mean']:+.3f} ± {s2['se']:.3f}; seeds {' '.join(f'{x:+.2f}' for x in s2['nets'])}; T3 {T3}")
    print(f"    X-f 2018+, 2021+ above pooled; 6-10 names to half : 2018+ {res['ladder']['long = THE POOL|2018+'].get('gross', float('nan')):+.1f}, 2021+ {res['ladder']['long = THE POOL|2021-2026'].get('gross', float('nan')):+.1f}; to half {res['conc'].get('pool', {}).get('to_half')}")
    print(f"    X-g priority inside noise; N=1 >= N=2       : delta {res['se']['PRIO_N2']['mean'] - res['se']['NOPRIO_N2']['mean']:+.3f}; N1 {res['se']['PRIO_N1']['mean']:+.2f} vs N2 {res['se']['PRIO_N2']['mean']:+.2f}")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT}   total {time.time()-t0:.0f}s   THE FILE IS NOW SPENT FOR THIS LINE.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--proof", action="store_true"); ap.add_argument("--holdout", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.proof:
        proof()
    elif a.holdout:
        holdout(a.workers)

"""D427 -- the five layers on rung 2, each alone and stacked, both lenses. Measurement; gated on nothing.
Declared in 44038ea BEFORE this file.

usage:  uv run python -u scripts/run_d427_layers.py --run [--workers 8]
"""
import argparse, importlib.util, json, multiprocessing as mp, pathlib, sys, time
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
# The heavy modules are loaded inside run(), not here: Windows spawn re-executes this file's top level
# in every worker, and D423 + D425 + D419 cost 2.7 GB per process -- eight of them swapped the machine.
LY = R23 = R25 = M22 = None

OUT = REPO / "data" / "d427_layers.json"
HOLD, N10, SEEDS, N_DRAW, N_PERM = 5, 10, (419, 4190, 41900), 100, 200
ATLAS_CHEAP_LONG_P50 = 19.22            # D392 RESULT §0: random long, cheap price third, hedged, n=30,000 -- quoted, not re-run


# ------------------------------------------------------------------ the book: sim2 + a priority
def sim4(I, n_slots, seed, target, stop2, pool_mask, prio=None, run_targets=None):
    """D425's sim2 with D421's refill priority (prio first, then cell 2, then random). Everything else verbatim."""
    t, side, E, cost = I["t"], I["side"], I["E"], I["cost"]
    OP, HI, LO, CL, c2 = I["OP"], I["HI"], I["LO"], I["CL"], I["c2"]
    T = int(I["T"][0]); N = len(t)
    rng = np.random.default_rng(seed)
    order = np.lexsort((rng.random(N), ~c2)) if prio is None else np.lexsort((rng.random(N), ~c2, ~prio))
    by_day = {}
    for k in order:
        if pool_mask is None or pool_mask[k]:
            by_day.setdefault(int(t[k]), []).append(int(k))
    lgE = np.log(E); lgCL = np.log(CL)
    held = {}; held_names = set()
    gross = np.zeros(T); costs = np.zeros(T); occ = np.zeros(T, np.int32)
    ent = np.zeros(T, np.int32); frees = np.zeros(T, np.int32); refilled = np.zeros(T, np.int32); early_frees = np.zeros(T, np.int32)
    trades = []; swaps = []
    d0 = int(t.min()) + 1
    for d in range(d0, T):
        freed = []
        for k in list(held):
            st = held[k]; a = st[0]
            o, h, l, c = OP[k, a], HI[k, a], LO[k, a], CL[k, a]
            if not (np.isfinite(o) and np.isfinite(h) and np.isfinite(l) and np.isfinite(c)):
                held.pop(k); held_names.discard(int(I["i"][k]))
                trades.append((k, st[1], a, False, d, np.nan)); frees[d] += 1; freed.append((k, np.nan, a, False))
                continue
            s = float(side[k]); prev = lgE[k] if a == 0 else lgCL[k, a - 1]
            os_, hs = s * o, (s * h if s > 0 else s * l)
            if run_targets is None and np.isfinite(target[k]) and hs >= s * target[k]:
                fill = s * max(s * target[k], os_); mark = s * (np.log(fill) - prev)
                gross[d] += mark; occ[d] += 1
                held.pop(k); held_names.discard(int(I["i"][k]))
                trades.append((k, st[1] + mark, a + 1, True, d, fill)); frees[d] += 1; freed.append((k, fill, a + 1, True))
                continue
            mark = s * (lgCL[k, a] - prev)
            gross[d] += mark; occ[d] += 1
            st[0] += 1; st[1] += mark; st[2] = max(st[2], hs)
            breached = run_targets is None and np.isfinite(stop2[k, a]) and (s * c < s * stop2[k, a])
            close_now = (st[0] >= HOLD) or (run_targets is not None and st[0] >= run_targets[k]) or breached
            if close_now:
                early = (run_targets is not None) or (breached and st[0] < HOLD)
                held.pop(k); held_names.discard(int(I["i"][k]))
                trades.append((k, st[1], st[0], early, d, c)); frees[d] += 1
                if early:
                    freed.append((k, c, st[0], True))
        free = n_slots - len(held); arrivals = []
        if free > 0:
            for k in by_day.get(d, []):
                if free == 0:
                    break
                nm = int(I["i"][k])
                if nm in held_names or k in held or not np.isfinite(E[k]) or E[k] <= 0:
                    continue
                held[k] = [0, 0.0, side[k] * E[k]]; held_names.add(nm)
                costs[d] += cost[k]; ent[d] += 1; free -= 1; arrivals.append(k)
        for j, (kd, fill, age, early) in enumerate(freed):
            if early:
                swaps.append((kd, fill, d, age, arrivals[j] if j < len(arrivals) else -1))
        refilled[d] += min(len(freed), len(arrivals)); early_frees[d] += len(freed)
    resid = sum(st[1] for st in held.values())
    return dict(gross=gross, costs=costs, occ=occ, ent=ent, frees=frees, refilled=refilled, early_frees=early_frees,
                trades=trades, swaps=swaps, resid=resid, d0=d0)


# ------------------------------------------------------------------ per-trade
def table(r, cost, m, label):
    x = r[m]; c = cost[m]; f = np.isfinite(x) & np.isfinite(c); x, c = x[f], c[f]; n = x.size
    if n < 30:
        return dict(label=label, n=int(n))
    lo, hi = np.quantile(x, [.01, .99]); w = x > 0
    return dict(label=label, n=int(n), gross=float(1e4 * x.mean()), median=float(1e4 * np.median(x)), se=float(1e4 * x.std(ddof=1) / np.sqrt(n)),
                net=float(1e4 * (x - c).mean()), cost=float(1e4 * c.mean()), win=float(100 * w.mean()),
                payoff=float(x[w].mean() / -x[~w].mean()) if (~w).any() else float("nan"), trim=float(1e4 * x[(x >= lo) & (x <= hi)].mean()))


def show_t(d):
    if "gross" not in d:
        print(f"  {d['label']:34s} n {d['n']:6,}  (too few)"); return
    print(f"  {d['label']:34s} n {d['n']:6,}  gross {d['gross']:+7.2f}  med {d['median']:+7.2f}  se {d['se']:5.2f}  cost {d['cost']:5.2f}  NET {d['net']:+7.2f}  "
          f"win {d['win']:4.1f}%  payoff {d['payoff']:4.2f}  trim {d['trim']:+7.2f}")


def filter_null(lab, base, t, r, n, seed):
    """Premium of the layer over the base's complement, against a within-day permutation of the layer
    label among the BASE events (D423/D425's permutation; the base's per-day counts are held)."""
    lab = lab & base
    obs = float(r[lab].mean() - r[base & ~lab].mean())
    rng = np.random.default_rng(seed); draws = np.empty(n)
    for b in range(n):
        lp = R23.perm_within_day(lab.astype(float), t, base, rng) > 0.5
        draws[b] = r[lp & base].mean() - r[base & ~lp].mean()
    p95 = float(np.quantile(draws, .95)); se = float(draws.std(ddof=1) / np.sqrt(n)); edge = obs - p95
    return dict(observed_bp=1e4 * obs, p50=float(1e4 * np.median(draws)), p95=1e4 * p95, se=1e4 * se,
                margin_se=float(edge / se) if se > 0 else float("inf"), passes=bool(edge > 0 and abs(edge) >= 2 * se), unresolved=bool(abs(edge) < 2 * se))


# ------------------------------------------------------------------ control
def _ctrl_worker(args):
    """Loads ONLY run_d419 (0.9 GB): its cached inputs, its scorer, and its own FIXED simulate, which
    D421 P2 asserted bit-identical to the D421/D422 simulator; [CHUNK] re-checks that against the parent."""
    n_slots, count, draws = args
    Bw = _load("d419w", "run_d419_book.py")
    I = dict(Bw.build_inputs()); base = np.flatnonzero(I["c2"]); out = []
    for dr in draws:
        rng = np.random.default_rng(300000 + dr)
        pool = np.zeros(len(I["t"]), bool); pool[rng.choice(base, size=count, replace=False)] = True
        R = Bw.simulate(I, "FIXED", n_slots, SEEDS[0], pool_mask=pool); S = Bw.score(I, R, n_slots)
        assert S["recon_rel"] < 1e-9, "[RECON] control"
        out.append((dr, S["net_bp"], S["utilisation"]))
    return out


def run(workers):
    global LY, R23, R25, M22
    t0 = time.time()
    print("D427  the five layers on the second zone -- each alone, then stacked; both lenses\n      declared in 44038ea BEFORE this ran\n")
    LY = _load("d427l", "d427_layers.py"); R23 = _load("d423r", "run_d423_structure_exits.py")
    R25 = _load("d425r", "run_d425_zone_exits.py"); M22 = _load("d422r", "run_d422_second_zone.py")
    I, P, B, fl, M, F, L = LY.load()
    X = LY.layers(I, fl, F)
    t, i, side, E, ATR, c2, rb, cost = I["t"], I["i"], I["side"], I["E"], I["ATR"], I["c2"], I["r_base"], I["cost"]
    N = len(t); T = int(I["T"][0]); yr = np.array([int(str(x)[:4]) for x in I["dates"][t]])
    R2, L1, L2, L3, L5, cum = X["R2"], X["L1"], X["L2"], X["L3"], X["L5"], X["cum"]
    assert int(R2.sum()) == 9411 and int(L1.sum()) == 7856 and int(L2.sum()) == 5137 and int(L3.sum()) == 921 and int(L5.sum()) == 3137 and int(cum["L1..L5"].sum()) == 1416, "[STAGE0]"
    print(f"  [STAGE0] 9,411 / 7,856 / 5,137 / 921 / 3,137 / 1,416 reproduce;  L5 cut ${X['cut']:.2f}")
    res = dict(per_trade={}, null={}, l4={}, books={}, deltas={}, control={})
    wins = [("pooled", np.ones(N, bool)), ("2018+", yr >= 2018), ("2021-2026", yr >= 2021)]

    print("\n1. PER TRADE -- each layer alone, then the stack")
    pops = [("base R2", R2), ("L1 alone", L1), ("L2 alone", L2), ("L3 sub-cell", L3), ("L5 alone", L5), ("dropped by L1 (gap 1-2)", R2 & ~L1),
            ("L1+L2", cum["L1+L2"]), ("L1..L5", cum["L1..L5"]), ("L1..L5 & L3", cum["L1..L5"] & L3)]
    for lab, m in pops:
        for wl, wm in wins:
            d = table(rb, cost, m & wm, f"{lab}  {wl}"); res["per_trade"][f"{lab}|{wl}"] = d; show_t(d)
        print()
    print("2. THE WITHIN-DAY PERMUTATION NULL on each filter's premium over the base's complement (200 draws)")
    for lab, m in (("L1", L1), ("L2", L2), ("L5", L5), ("L1+L2", cum["L1+L2"]), ("L1..L5", cum["L1..L5"]), ("L3 sub-cell", L3)):
        q = filter_null(m, R2, t, rb, N_PERM, 427); res["null"][lab] = q
        print(f"  {lab:12s} premium {q['observed_bp']:+7.2f}   null p50 {q['p50']:+6.2f}  p95 {q['p95']:+6.2f} (+-{q['se']:.2f})   margin {q['margin_se']:+6.1f} SE   "
              f"{'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}")
    l5l = table(rb, cost, L5 & (side > 0), "L5 long"); res["per_trade"]["L5 long|pooled"] = l5l
    print(f"  L5 long half: gross {l5l['gross']:+.2f} on {l5l['n']:,}  vs the D392 atlas's random cheap long p50 {ATLAS_CHEAP_LONG_P50:+.2f}  ->  excess {l5l['gross'] - ATLAS_CHEAP_LONG_P50:+.2f}")

    print("\n3. L4 -- ZTP as the exit, paired against t+5, on each population")
    last = P["CL"][np.clip(t + HOLD, 0, T - 1), i]; nan1 = np.full(N, np.nan)
    W = R23.walk_levels(I["OP"], I["HI"], I["LO"], I["CL"], E, ATR, side, last, L["ztp"], nan1); rr = R23.ret_of(W, E, side)
    for lab, m in (("base R2", R2), ("L1", L1), ("L1+L2", cum["L1+L2"]), ("L1..L5", cum["L1..L5"])):
        p = R23.paired(rr, rb, W, m, E, side, f"ZTP on {lab}"); res["l4"][lab] = p; R23.show(p)

    print("\n4. THE BOOK -- cell 2, 10 slots, three seeds")
    nan2 = np.full((N, HOLD), np.nan)
    R22 = M.simulate(I, N10, SEEDS[0], pool_mask=R2); R0 = sim4(I, N10, SEEDS[0], nan1, nan2, R2)
    assert [x[:3] for x in R0["trades"]] == [x[:3] for x in R22["trades"]] and np.array_equal(R0["gross"], R22["gross"]), "[P2] base"
    Rp = M.simulate(I, N10, SEEDS[0], prio=L3, pool_mask=R2); Rq = sim4(I, N10, SEEDS[0], nan1, nan2, R2, prio=L3)
    assert [x[:3] for x in Rq["trades"]] == [x[:3] for x in Rp["trades"]] and np.array_equal(Rq["gross"], Rp["gross"]), "[P2] priority"
    Rz = R25.sim2(I, N10, SEEDS[0], L["ztp"], nan2, pool_mask=R2); Ry = sim4(I, N10, SEEDS[0], L["ztp"], nan2, R2)
    assert [x[:3] for x in Ry["trades"]] == [x[:3] for x in Rz["trades"]] and np.array_equal(Ry["gross"], Rz["gross"]), "[P2] levels"
    print("  [P2]   sim4 == D422's ANY-REQ book; == D421's simulate with the L3 priority; == D425's sim2 with ZTP -- all bit-identical")
    specs = [("base", R2, None, False), ("L1-REQ", L1, None, False), ("L2-REQ", L2, None, False), ("L3-PRIO", R2, L3, False), ("L4-ZTP", R2, None, True), ("L5-REQ", L5, None, False),
             ("C1 L1", L1, None, False), ("C2 L1+L2", cum["L1+L2"], None, False), ("C3 +L3prio", cum["L1+L2"], L3, False), ("C4 +L4", cum["L1+L2"], L3, True), ("C5 +L5", cum["L1..L5"], L3, True)]
    series = {}; t1 = time.time(); dates = I["dates"]; d0 = R0["d0"]
    for name, pool, prio, ztp in specs:
        for seed in SEEDS:
            R = sim4(I, N10, seed, L["ztp"] if ztp else nan1, nan2, pool, prio=prio); S = B.score(I, R, N10); assert S["recon_rel"] < 1e-9, f"[RECON] {name}"
            series[(name, seed)] = S["net_series"]
            res["books"][f"{name}_s{seed}"] = {k: v for k, v in S.items() if not k.endswith("_series") and k != "run_dist"}
    print(f"  {len(res['books'])} books in {time.time()-t1:.0f}s   [RECON] all\n")
    print(f"  {'book':12s} {'gross':>7s} {'net':>7s} {'cost':>6s} {'util':>6s} {'trades':>7s} {'per trade':>9s}   net by seed          delta vs base (block boot)")
    for name, pool, prio, ztp in specs:
        S = res["books"][f"{name}_s{SEEDS[0]}"]; nets = [res["books"][f"{name}_s{s}"]["net_bp"] for s in SEEDS]
        line = f"  {name:12s} {S['gross_bp']:+7.3f} {S['net_bp']:+7.3f} {S['cost_bp']:6.3f} {100*S['utilisation']:5.1f}% {S['trades']:7,} {S['trade_mean_bp']:+9.2f}   " + " ".join(f"{x:+.3f}" for x in nets)
        if name != "base":
            diff = np.mean([series[(name, s)] - series[("base", s)] for s in SEEDS], axis=0); se, mean = B.block_boot(diff, dates[d0:])
            res["deltas"][name] = dict(net_delta=float(1e4 * mean), se=float(1e4 * se), t=float(mean / se), net_abs=float(np.mean(nets)))
            line += f"   {1e4*mean:+6.3f} +- {1e4*se:.3f} ({mean/se:+4.1f} SE)"
        print(line)

    print(f"\n5. MATCHED-COUNT RANDOM-POOL CONTROLS ({N_DRAW} draws each, {workers} workers): base, L1-REQ, C5")
    jobs = []; specs_c = [("base", int(R2.sum())), ("L1-REQ", int(L1.sum())), ("C5 +L5", int(cum["L1..L5"].sum()))]
    for name, count in specs_c:
        for w in range(workers):
            jobs.append((N10, count, list(range(w, N_DRAW, workers))))
    with mp.Pool(workers) as pl:
        results = pl.map(_ctrl_worker, jobs)
    rng = np.random.default_rng(300000); p0 = np.zeros(N, bool); p0[rng.choice(np.flatnonzero(c2), size=int(R2.sum()), replace=False)] = True
    S0 = B.score(I, M.simulate(I, N10, SEEDS[0], pool_mask=p0), N10)
    for j, (name, count) in enumerate(specs_c):
        out = sorted(o for oo in results[j * workers:(j + 1) * workers] for o in oo); net = np.array([o[1] for o in out])
        if j == 0:
            assert abs(out[0][1] - S0["net_bp"]) < 1e-12, "[CHUNK]"
        obs = float(np.mean([res["books"][f"{name}_s{s}"]["net_bp"] for s in SEEDS]))
        p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs - p95
        res["control"][name] = dict(count=count, p50=float(np.median(net)), p95=p95, se=se, observed=obs, margin_se=float(edge / se),
                                    passes=bool(edge > 0 and abs(edge) >= 2 * se), unresolved=bool(abs(edge) < 2 * se), util=float(np.mean([o[2] for o in out])))
        q = res["control"][name]
        print(f"  {name:12s} n {count:6,}  book {obs:+.3f}   random p50 {q['p50']:+.3f}  p95 {p95:+.3f} (+-{se:.3f})   margin {q['margin_se']:+6.1f} SE   "
              f"{'BEATS p95' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'below p95')}   util ctrl {100*q['util']:.1f}%")
    print("  [CHUNK] worker draw 0 == in-process")

    pt = res["per_trade"]; bk = lambda n_: np.mean([res["books"][f"{n_}_s{s}"]["net_bp"] for s in SEEDS])
    print("\n6. PREDICTIONS")
    print(f"    X-a L1 +47..+49, null passes, book +1.3..+1.7        : {pt['L1 alone|pooled']['gross']:+.2f}, null {res['null']['L1']['margin_se']:+.1f} SE, book {bk('L1-REQ'):+.3f} util {100*res['books']['L1-REQ_s419']['utilisation']:.0f}%")
    print(f"    X-b L2 +44..+46, median>55 win>55, null fails       : {pt['L2 alone|pooled']['gross']:+.2f}, med {pt['L2 alone|pooled']['median']:+.1f}, win {pt['L2 alone|pooled']['win']:.1f}%, null {res['null']['L2']['margin_se']:+.1f} SE, book {bk('L2-REQ'):+.3f}")
    print(f"    X-c L3 +100..+130; priority adds 0..+0.3            : {pt['L3 sub-cell|pooled']['gross']:+.2f} +- {pt['L3 sub-cell|pooled']['se']:.1f}; C3-C2 {bk('C3 +L3prio') - bk('C2 L1+L2'):+.3f}")
    print(f"    X-d L4 on L1+L2 +1..+4; book +0.1..+0.4             : {res['l4']['L1+L2']['delta_bp']:+.2f} +- {res['l4']['L1+L2']['se_bp']:.2f}; C4-C3 {bk('C4 +L4') - bk('C3 +L3prio'):+.3f}")
    print(f"    X-e L5 +80..+90, excess over atlas +30..+40, book +0.4..+0.9 : {pt['L5 alone|pooled']['gross']:+.2f}, excess {l5l['gross'] - ATLAS_CHEAP_LONG_P50:+.2f}, book {bk('L5-REQ'):+.3f}")
    print(f"    X-f stack +85..+100 gross, net +50..+65, book +0.3..+0.8 at ~17% : {pt['L1..L5|pooled']['gross']:+.2f}, net {pt['L1..L5|pooled']['net']:+.2f}, book {bk('C5 +L5'):+.3f} util {100*res['books']['C5 +L5_s419']['utilisation']:.0f}%")
    print(f"    X-g base, L1, stack beat their random p95            : " + ", ".join(f"{k} {v['margin_se']:+.1f}" for k, v in res["control"].items()))
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT}   total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.run:
        run(a.workers)

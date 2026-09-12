"""D426 -- double down on the second zone, both lenses. Bar committed in 49997c9 BEFORE this file.

PER EPISODE  every cell-2 rung-1 trade; four rules (BASE, RESTART, STOPS, DD) in unit-returns.
THE BOOK     D419's simulator rewritten over the PANEL (a restarted rung-1 unit is held past the
             5-bar cache window) with two-slot names. With adds disabled and no levels it must
             reproduce D422's ANY-REQ book; with ZTP+FAR levels, D425's sim2 -- both bit-identical.
Books: ANY-REQ, UNION-1PN, UNION-STOPS, DD-A, DD-B.  Bar: DD-A (T1 episodes, T2 vs ANY-REQ, T3 vs random pools).

usage:  uv run python -u scripts/run_d426_double_down.py --run [--workers 8]
"""
import argparse, importlib.util, json, multiprocessing as mp, pathlib, sys, time
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
RF = _load("d426f", "d426_rung_flags.py")
R23 = _load("d423r", "run_d423_structure_exits.py")
R25 = _load("d425r", "run_d425_zone_exits.py")

OUT = REPO / "data" / "d426_double_down.json"
HOLD, N10, SEEDS, N_DRAW = 5, 10, (419, 4190, 41900), 100
BOOKS = ("ANY-REQ", "UNION-1PN", "UNION-STOPS", "DD-A", "DD-B")


# ------------------------------------------------------------------ the episode lens
def add_map(F, version, N):
    """add_of[k1] = the FIRST qualifying rung-2 event that doubles rung-1 event k1, else -1."""
    flag = F["add_A"] if version == "A" else F["add_B"]
    add_of = np.full(N, -1, np.int64)
    js = np.flatnonzero(flag)
    return add_of, js


def episodes(I, P, L, F, version, r1_pool):
    """Unit-return sums per rung-1 episode under BASE / RESTART / STOPS / DD, plus unit-days."""
    t, i, side, E, ATR = I["t"], I["i"], I["side"], I["E"], I["ATR"]
    N = len(t); T = int(I["T"][0]); rb = I["r_base"]
    last = P["CL"][np.clip(t + HOLD, 0, T - 1), i]
    flag = F["add_A"] if version == "A" else F["add_B"]
    add_of = np.full(N, -1, np.int64)
    for j in np.flatnonzero(flag)[np.argsort(t[np.flatnonzero(flag)], kind="stable")]:
        k1 = F["prev_k"][j]
        if add_of[k1] < 0:
            add_of[k1] = j
    K = np.flatnonzero(r1_pool); J = add_of[K]; dbl = J >= 0
    # unit 2 walks its own window with the rung-2 zone's levels
    W = R23.walk_levels(I["OP"], I["HI"], I["LO"], I["CL"], E, ATR, side, last, L["ztp"], L["far"])
    r_walk = R23.ret_of(W, E, side)                      # unit 2 under ZTP+FAR, exit price W["price"]
    s = side[K].astype(float); lgE1 = np.log(E[K])
    Jc = np.where(dbl, J, 0)
    X = W["price"][Jc]; lastj = last[Jc]
    u1_restart = s * (np.log(lastj) - lgE1)              # unit 1 held to t2+5
    u1_dd = s * (np.log(X) - lgE1)                       # unit 1 exits with unit 2
    base = np.where(dbl, rb[K] + rb[Jc], rb[K])
    restart = np.where(dbl, u1_restart + rb[Jc], rb[K])
    stops = np.where(dbl, rb[K] + r_walk[Jc], rb[K])
    dd = np.where(dbl, u1_dd + r_walk[Jc], rb[K])
    gap = np.where(dbl, t[Jc] - t[K], 0); b2 = np.where(W["early"][Jc], W["bar"][Jc] + 1, HOLD)
    days = dict(BASE=np.where(dbl, 2 * HOLD, HOLD), RESTART=np.where(dbl, gap + 2 * HOLD, HOLD),
                STOPS=np.where(dbl, HOLD + b2, HOLD), DD=np.where(dbl, gap + 2 * b2, HOLD))
    return dict(K=K, J=J, dbl=dbl, BASE=base, RESTART=restart, STOPS=stops, DD=dd, days=days,
                u1_dd=u1_dd, u2_dd=r_walk[Jc], u1_base=rb[K], u2_base=rb[Jc], fired=W["early"][Jc], gap=gap)


def ep_stats(ep, mask, label):
    out = dict(label=label, n=int(mask.sum()))
    for rule in ("BASE", "RESTART", "STOPS", "DD"):
        x = ep[rule][mask]; f = np.isfinite(x)
        out[rule] = float(1e4 * x[f].mean()); out[f"{rule}_per_unit_day"] = float(1e4 * x[f].sum() / ep["days"][rule][mask][f].sum())
        if rule != "BASE":
            d = (ep[rule] - ep["BASE"])[mask]; d = d[np.isfinite(d)]
            out[f"{rule}_delta"] = float(1e4 * d.mean()); out[f"{rule}_se"] = float(1e4 * d.std(ddof=1) / np.sqrt(d.size)) if d.size > 1 else float("nan")
    return out


def show_ep(o):
    print(f"  {o['label']:26s} n {o['n']:6,}   BASE {o['BASE']:+7.2f}   RESTART {o['RESTART']:+7.2f} ({o['RESTART_delta']:+6.2f} ± {o['RESTART_se']:.2f})   "
          f"STOPS {o['STOPS']:+7.2f} ({o['STOPS_delta']:+6.2f} ± {o['STOPS_se']:.2f})   DD {o['DD']:+7.2f} ({o['DD_delta']:+6.2f} ± {o['DD_se']:.2f})   "
          f"per unit-day  BASE {o['BASE_per_unit_day']:+5.2f}  DD {o['DD_per_unit_day']:+5.2f}")


def assert_SIGN():
    """A synthetic doubled episode, long and its short log mirror; the check fires when broken."""
    # rung 1 at day 0 close 100; rung 2 at day 2 close 98 (the second zone is lower); no level fires;
    # exit at day 7 close 101. BASE: rung 1 at day-5 close 99, rung 2 at day-7 close 101.
    r1_5, x = 99.0, 101.0
    E1, E2 = 100.0, 98.0
    for s in (1.0, -1.0):
        f = (lambda p: p) if s > 0 else (lambda p: 100.0 * 100.0 / p)       # log mirror about 100
        lg = np.log
        u1_dd = s * (lg(f(x)) - lg(f(E1))); u2 = s * (lg(f(x)) - lg(f(E2)))
        base = s * (lg(f(r1_5)) - lg(f(E1))) + u2
        dd = u1_dd + u2
        assert abs(dd - base - s * (lg(f(x)) - lg(f(r1_5)))) < 1e-12, "[SIGN] restart delta is unit 1's move from its old exit to the joint exit"
        assert (dd - base) > 0 and abs((dd - base) - lg(101 / 99)) < 1e-12, "[SIGN] held past t1+5 into a rise: restart pays, long and short alike"
    # the walker: a FAR above the path exits on bar 0 at the close; the episode must then NOT reach day 7
    OP = np.array([[98.5, 99, 100, 100.5, 101]]); HI = np.array([[99.5, 100, 101, 101, 101.5]]); LO = np.array([[97.5, 98.5, 99.5, 100, 100.5]]); CL = np.array([[99, 99.5, 100.5, 100.5, 101]], float)
    W = R23.walk_levels(OP, HI, LO, CL, np.array([98.0]), np.array([2.0]), np.array([1]), np.array([101.0]), np.array([np.nan]), np.array([97.0]))
    assert not W["early"][0] and W["price"][0] == 101.0, "[SIGN] no level in the path: joint exit at the clock"
    Wb = R23.walk_levels(OP, HI, LO, CL, np.array([98.0]), np.array([2.0]), np.array([1]), np.array([101.0]), np.array([np.nan]), np.array([99.5]))
    assert Wb["early"][0] and Wb["bar"][0] == 0 and Wb["price"][0] == 99.0, "[SIGN] a close through FAR on bar 0 exits both units there"
    fired = False
    try:
        assert not Wb["early"][0], "x"
    except AssertionError:
        fired = True
    assert fired, "[SIGN] the self-test cannot fail"


# ------------------------------------------------------------------ the book, over the panel
def sim3(I, P, n_slots, seed, pool_mask, levels_on, add_flag, L):
    """Two-slot names over the panel. pool_mask: events that may open a position. levels_on[k]: this
    event's ZTP/FAR apply when it opens or adds. add_flag[k]: this rung-2 event may ADD to a held
    same-side rung-1 position on its name (second unit, both units re-clocked and re-levelled).
    Everything else is D419's bar order: mark and exit on day d, then refill from day d's touches."""
    t, i, side, E, cost, c2 = I["t"], I["i"], I["side"], I["E"], I["cost"], I["c2"]
    OPp, HIp, LOp, CLp = P["OP"], P["HI"], P["LO"], P["CL"]
    lgCLp = np.log(np.where(CLp > 0, CLp, np.nan))
    T = int(I["T"][0]); N = len(t)
    rng = np.random.default_rng(seed)
    order = np.lexsort((rng.random(N), ~c2))
    by_day = {}
    for k in order:
        if pool_mask[k]:
            by_day.setdefault(int(t[k]), []).append(int(k))
    ztp, far = L["ztp"], L["far"]
    held = {}                       # k -> dict(nm, s, lgE, age, cum, D (exit day), tgt, stp, first (rung-1 not yet doubled), t0)
    by_name = {}                    # nm -> list of held k
    gross = np.zeros(T); costs = np.zeros(T); occ = np.zeros(T, np.int32)
    ent = np.zeros(T, np.int32); frees = np.zeros(T, np.int32); refilled = np.zeros(T, np.int32); early_frees = np.zeros(T, np.int32)
    trades = []; adds = 0; adds_blocked = 0; opp_skipped = 0
    d0 = int(t.min()) + 1
    for d in range(d0, T):
        freed = 0
        for k in list(held):
            st = held[k]; nm = st["nm"]; s = st["s"]
            o, h, l, c = OPp[d, nm], HIp[d, nm], LOp[d, nm], CLp[d, nm]
            if not (np.isfinite(o) and np.isfinite(h) and np.isfinite(l) and np.isfinite(c)):
                held.pop(k); by_name[nm].remove(k)
                trades.append((k, st["cum"], st["age"], False, d, np.nan)); frees[d] += 1
                continue
            prev = st["lgE"] if st["age"] == 0 else lgCLp[d - 1, nm]
            os_, hs = s * o, (s * h if s > 0 else s * l)
            if np.isfinite(st["tgt"]) and hs >= s * st["tgt"]:
                fill = s * max(s * st["tgt"], os_); mark = s * (np.log(fill) - prev)
                gross[d] += mark; occ[d] += 1
                held.pop(k); by_name[nm].remove(k)
                trades.append((k, st["cum"] + mark, st["age"] + 1, True, d, fill)); frees[d] += 1; freed += 1
                continue
            mark = s * (lgCLp[d, nm] - prev)
            gross[d] += mark; occ[d] += 1
            st["age"] += 1; st["cum"] += mark
            breached = np.isfinite(st["stp"]) and (s * c < s * st["stp"])
            if d >= st["D"] or breached:
                early = breached and d < st["D"]
                held.pop(k); by_name[nm].remove(k)
                trades.append((k, st["cum"], st["age"], early, d, c)); frees[d] += 1
                if early:
                    freed += 1
        free = n_slots - len(held); arrivals = 0
        for k in by_day.get(d, []):
            nm = int(i[k]); s = float(side[k])
            hk = by_name.get(nm, [])
            if hk:
                if add_flag[k] and len(hk) == 1 and held[hk[0]]["first"] and held[hk[0]]["s"] == s:
                    if free == 0:
                        adds_blocked += 1; continue
                    if not (np.isfinite(E[k]) and E[k] > 0):
                        continue
                    p1 = held[hk[0]]; p1["first"] = False; p1["D"] = d + HOLD; p1["tgt"] = ztp[k]; p1["stp"] = far[k]
                    held[k] = dict(nm=nm, s=s, lgE=np.log(E[k]), age=0, cum=0.0, D=d + HOLD, tgt=ztp[k], stp=far[k], first=False, t0=d)
                    hk.append(k); costs[d] += cost[k]; ent[d] += 1; free -= 1; arrivals += 1; adds += 1
                elif add_flag[k] and hk and held[hk[0]]["s"] != s:
                    opp_skipped += 1
                continue
            if free == 0:
                continue
            if not pool_open[k]:
                continue
            if not (np.isfinite(E[k]) and E[k] > 0):
                continue
            lv = levels_on[k]
            held[k] = dict(nm=nm, s=s, lgE=np.log(E[k]), age=0, cum=0.0, D=d + HOLD, tgt=ztp[k] if lv else np.nan, stp=far[k] if lv else np.nan,
                           first=bool(rung1[k]), t0=d)
            by_name.setdefault(nm, []).append(k)
            costs[d] += cost[k]; ent[d] += 1; free -= 1; arrivals += 1
        refilled[d] += min(freed, arrivals); early_frees[d] += freed
    resid = sum(st["cum"] for st in held.values())
    return dict(gross=gross, costs=costs, occ=occ, ent=ent, frees=frees, refilled=refilled, early_frees=early_frees,
                trades=trades, swaps=[], resid=resid, d0=d0, adds=adds, adds_blocked=adds_blocked, opp_skipped=opp_skipped)


pool_open = None; rung1 = None      # set per book before sim3 (module globals keep the signature small)


def book_spec(name, I, F, L, prim, r1c2):
    N = len(I["t"]); no = np.zeros(N, bool)
    if name == "ANY-REQ":
        return dict(pool=prim, open_=prim, levels=no, add=no)
    if name == "UNION-1PN":
        return dict(pool=prim | r1c2, open_=prim | r1c2, levels=no, add=no)
    if name == "UNION-STOPS":
        return dict(pool=prim | r1c2, open_=prim | r1c2, levels=prim, add=no)
    if name == "DD-A":
        return dict(pool=prim | r1c2, open_=prim | r1c2, levels=prim | F["add_A"], add=F["add_A"])
    if name == "DD-B":
        return dict(pool=prim | r1c2 | F["add_B"], open_=prim | r1c2, levels=prim | F["add_B"], add=F["add_B"])
    raise KeyError(name)


def run_book(name, I, P, F, L, prim, r1c2, seed):
    global pool_open, rung1
    sp = book_spec(name, I, F, L, prim, r1c2); pool_open = sp["open_"]; rung1 = F["r1"]
    return sim3(I, P, N10, seed, sp["pool"], sp["levels"], sp["add"], L)


def _ctrl_worker(args):
    n_slots, count, draws = args
    M = _load("d422r", "run_d422_second_zone.py")      # the D422 runner: its simulate, and D419's scorer via load_all
    I, P, B, fl = M.load_all()
    base = np.flatnonzero(I["c2"]); out = []
    for dr in draws:
        rng = np.random.default_rng(300000 + dr)
        pool = np.zeros(len(I["t"]), bool); pool[rng.choice(base, size=count, replace=False)] = True
        R = M.simulate(I, n_slots, SEEDS[0], pool_mask=pool); S = B.score(I, R, n_slots)
        assert S["recon_rel"] < 1e-9, "[RECON] control"
        out.append((dr, S["net_bp"], S["utilisation"]))
    return out


def run(workers):
    t0 = time.time()
    print("D426  double down on the second zone -- both lenses\n      the bar was committed in 49997c9 BEFORE this ran\n")
    assert_SIGN(); print("  [SIGN] restart delta = unit 1's move from its old exit to the joint exit, long and short; FAR on bar 0 exits both; the check fires when broken")
    I, P, B, fl, M, zones = RF.load()
    F = RF.flags(I, fl); L = R25.ZL.levels(I, zones)
    t, i, side, E, c2 = I["t"], I["i"], I["side"], I["E"], I["c2"]
    N = len(t); T = int(I["T"][0]); yr = np.array([int(str(x)[:4]) for x in I["dates"][t]])
    prim = fl["s2any"] & c2; r1c2 = F["r1"] & c2
    assert N == 180050 and int(prim.sum()) == 9411 and int(r1c2.sum()) == 7974 and int(F["add_A"].sum()) == 1022 and int(F["add_B"].sum()) == 1249, "[STAGE0]"
    print(f"  [STAGE0] 180,050 / 9,411 / 7,974 / adds A 1,022 / B 1,249 reproduce")
    res = dict(episodes={}, books={}, deltas={}, control=None)

    print("\n1. THE EPISODE LENS -- every cell-2 rung-1 trade, unit-return sums")
    for ver in ("A", "B"):
        ep = episodes(I, P, L, F, ver, r1c2)
        if ver == "A":
            nanx = ~np.isfinite(ep["DD"]) | ~np.isfinite(ep["BASE"])
            assert np.allclose(ep["DD"][~ep["dbl"] & ~nanx], I["r_base"][ep["K"]][~ep["dbl"] & ~nanx], atol=0, rtol=0), "[X] undoubled episode != r_base"
            print("  [X]    undoubled episodes return r_base exactly")
        K = ep["K"]; dbl = ep["dbl"]
        masks = [(f"{ver}  doubled", dbl), (f"{ver}  doubled long", dbl & (side[K] > 0)), (f"{ver}  doubled short", dbl & (side[K] < 0)),
                 (f"{ver}  doubled 2018+", dbl & (yr[K] >= 2018)), (f"{ver}  all rung-1 episodes", np.ones(K.size, bool))]
        for lab, m in masks:
            o = ep_stats(ep, m, lab); res["episodes"][lab] = o; show_ep(o)
        if ver == "A":
            fd = ep["fired"][dbl]; g = ep["gap"][dbl]
            print(f"     doubled A: levels fire on {100*fd.mean():.1f}% of episodes;  unit 1 alone BASE {1e4*np.nanmean(ep['u1_base'][dbl]):+.2f} -> DD {1e4*np.nanmean(ep['u1_dd'][dbl]):+.2f};  "
                  f"unit 2 alone BASE {1e4*np.nanmean(ep['u2_base'][dbl]):+.2f} -> DD {1e4*np.nanmean(ep['u2_dd'][dbl]):+.2f};  gap p50 {np.median(g):.0f}")
            res["episodes"]["A_decomp"] = dict(fire=float(fd.mean()), u1_base=float(1e4*np.nanmean(ep['u1_base'][dbl])), u1_dd=float(1e4*np.nanmean(ep['u1_dd'][dbl])),
                                               u2_base=float(1e4*np.nanmean(ep['u2_base'][dbl])), u2_dd=float(1e4*np.nanmean(ep['u2_dd'][dbl])))
        print()
    # standalone rung 2 with the exits, against t+5
    last = P["CL"][np.clip(t + HOLD, 0, T - 1), i]
    W = R23.walk_levels(I["OP"], I["HI"], I["LO"], I["CL"], E, I["ATR"], side, last, L["ztp"], L["far"])
    rr = R23.ret_of(W, E, side); sa = prim & ~F["add_A"]
    p = R23.paired(rr, I["r_base"], W, sa, E, side, "rung 2 standalone, ZTP+FAR"); res["episodes"]["standalone_r2"] = p; R23.show(p)

    print("\n2. THE BOOK -- cell 2, 10 slots, two-slot names")
    R22 = M.simulate(I, N10, SEEDS[0], pool_mask=prim)
    R0 = run_book("ANY-REQ", I, P, F, L, prim, r1c2, SEEDS[0])
    assert [x[:3] for x in R0["trades"]] == [x[:3] for x in R22["trades"]] and np.array_equal(R0["gross"], R22["gross"]), "[P2] ANY-REQ"
    global pool_open, rung1
    pool_open = prim; rung1 = F["r1"]
    Rl = sim3(I, P, N10, SEEDS[0], prim, prim, np.zeros(N, bool), L)
    far2 = np.repeat(L["far"][:, None], HOLD, axis=1)
    R25b = R25.sim2(I, N10, SEEDS[0], L["ztp"], far2, pool_mask=prim)
    assert [x[:3] for x in Rl["trades"]] == [x[:3] for x in R25b["trades"]] and np.array_equal(Rl["gross"], R25b["gross"]), "[P2] ZTP+FAR"
    print("  [P2]   sim3 == D422's ANY-REQ book (no adds, no levels) and == D425's sim2 with ZTP+FAR, bit for bit")
    series = {}; t1 = time.time()
    for name in BOOKS:
        for seed in SEEDS:
            R = run_book(name, I, P, F, L, prim, r1c2, seed); S = B.score(I, R, N10); assert S["recon_rel"] < 1e-9, f"[RECON] {name}"
            series[(name, seed)] = S["net_series"]
            res["books"][f"{name}_s{seed}"] = {k: v for k, v in S.items() if not k.endswith("_series") and k != "run_dist"} | dict(adds=R["adds"], adds_blocked=R["adds_blocked"], opp_skipped=R["opp_skipped"])
    print(f"  {len(res['books'])} books in {time.time()-t1:.0f}s   [RECON] all\n")
    print(f"  {'book':12s} {'gross':>7s} {'net':>7s} {'cost':>6s} {'util':>6s} {'trades':>7s} {'run':>5s} {'early':>6s} {'per trade':>9s} {'adds':>6s} {'blocked':>7s}   net by seed")
    d0 = R0["d0"]; dates = I["dates"]
    for name in BOOKS:
        S = res["books"][f"{name}_s{SEEDS[0]}"]; nets = [res["books"][f"{name}_s{s}"]["net_bp"] for s in SEEDS]
        print(f"  {name:12s} {S['gross_bp']:+7.3f} {S['net_bp']:+7.3f} {S['cost_bp']:6.3f} {100*S['utilisation']:5.1f}% {S['trades']:7,} {S['run']:5.2f} {100*S['early_share']:5.1f}% {S['trade_mean_bp']:+9.2f} {S['adds']:6,} {S['adds_blocked']:7,}   "
              + " ".join(f"{x:+.3f}" for x in nets))
        if name != "ANY-REQ":
            diff = np.mean([series[(name, s)] - series[("ANY-REQ", s)] for s in SEEDS], axis=0); se, mean = B.block_boot(diff, dates[d0:])
            res["deltas"][name] = dict(net_delta=float(1e4 * mean), se=float(1e4 * se), t=float(mean / se), net_abs=float(np.mean(nets)),
                                       gross_delta=float(np.mean([res["books"][f"{name}_s{s}"]["gross_bp"] - res["books"][f"ANY-REQ_s{s}"]["gross_bp"] for s in SEEDS])))
    print("\n  deltas vs ANY-REQ, mean over seeds, monthly block-bootstrap SE")
    for name, dd in res["deltas"].items():
        print(f"  {name:12s} gross delta {dd['gross_delta']:+6.3f}   NET delta {dd['net_delta']:+6.3f} +- {dd['se']:.3f}   {dd['t']:+4.1f} SE")

    count = int((prim | r1c2).sum())
    print(f"\n3. T3's CONTROL -- random cell-2 pools of {count:,} events, one per name, no stops ({N_DRAW} draws, {workers} workers)")
    with mp.Pool(workers) as pl:
        results = pl.map(_ctrl_worker, [(N10, count, list(range(w, N_DRAW, workers))) for w in range(workers)])
    out = sorted(o for oo in results for o in oo); net = np.array([o[1] for o in out])
    rng = np.random.default_rng(300000); pool0 = np.zeros(N, bool); pool0[rng.choice(np.flatnonzero(c2), size=count, replace=False)] = True
    S0 = B.score(I, M.simulate(I, N10, SEEDS[0], pool_mask=pool0), N10); assert abs(out[0][1] - S0["net_bp"]) < 1e-12, "[CHUNK]"
    obs = res["deltas"]["DD-A"]["net_abs"]; p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs - p95
    res["control"] = dict(count=count, p5=float(np.quantile(net, .05)), p50=float(np.median(net)), p95=p95, se=se, observed=obs, margin_se=float(edge / se),
                          beats=bool(edge > 0), unresolved=bool(abs(edge) < 2 * se), passes=bool(edge > 0 and abs(edge) >= 2 * se),
                          util=float(np.mean([o[2] for o in out])))
    print(f"  [CHUNK] worker draw 0 == in-process")
    print(f"  DD-A net {obs:+.3f}   random pools p5 {res['control']['p5']:+.3f}  p50 {res['control']['p50']:+.3f}  p95 {p95:+.3f} (+-{se:.3f})   margin {edge/se:+.1f} SE   "
          f"{'PASS' if res['control']['passes'] else ('UNRESOLVED' if res['control']['unresolved'] else 'FAIL')}   util ctrl {100*res['control']['util']:.1f}%")

    eA = res["episodes"]["A  doubled"]; dd = res["deltas"]["DD-A"]; ct = res["control"]
    T1 = bool(eA["DD_delta"] > 0 and eA["DD_delta"] / eA["DD_se"] >= 2); T2 = bool(dd["net_delta"] > 0 and dd["t"] >= 2); T3 = bool(ct["passes"])
    res["bar"] = dict(T1=T1, T2=T2, T3=T3, clears=bool(T1 and T2 and T3))
    print("\n4. THE BAR -- version A")
    print(f"    T1 DD - BASE on doubled episodes > 0 by 2 SE : {T1}   ({eA['DD_delta']:+.2f} +- {eA['DD_se']:.2f}, {eA['DD_delta']/eA['DD_se']:+.1f} SE)")
    print(f"    T2 DD-A net - ANY-REQ net > 0 by 2 SE        : {T2}   ({dd['net_delta']:+.3f} +- {dd['se']:.3f}, {dd['t']:+.1f} SE)")
    print(f"    T3 DD-A net > random-pool p95                : {T3}   (margin {ct['margin_se']:+.1f} SE)")
    print(f"    version A {'CLEARS' if res['bar']['clears'] else 'FAILS'} the bar")
    u = res["deltas"]["UNION-1PN"]; bB = res["deltas"]["DD-B"]
    print("\n5. PREDICTIONS")
    print(f"    X-a RESTART - BASE -5..-15            : {eA['RESTART_delta']:+.2f} +- {eA['RESTART_se']:.2f}")
    print(f"    X-b STOPS - BASE -3..-10              : {eA['STOPS_delta']:+.2f} +- {eA['STOPS_se']:.2f}")
    print(f"    X-c DD - BASE -15..-30, < -2 SE       : {eA['DD_delta']:+.2f} +- {eA['DD_se']:.2f}   ({eA['DD_delta']/eA['DD_se']:+.1f} SE);  per rung-1 trade {res['episodes']['A  all rung-1 episodes']['DD_delta']:+.2f}")
    print(f"    X-d UNION-1PN below ANY-REQ by 0.3-1.0 : {u['net_delta']:+.3f} +- {u['se']:.3f}")
    print(f"    X-e DD-A net +0.2..+0.9, util 85-92%, T2 fail, T3 pass; DD-B within 0.2 : net {dd['net_abs']:+.3f}, util {100*res['books'][f'DD-A_s{SEEDS[0]}']['utilisation']:.1f}%, "
          f"T2 {T2}, T3 {T3}; DD-B {bB['net_abs']:+.3f}")
    order = sorted(("BASE", "STOPS", "RESTART", "DD"), key=lambda r: -eA[r])
    print(f"    X-f ladder BASE > STOPS > RESTART > DD : {' > '.join(order)}")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT}   total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.run:
        run(a.workers)

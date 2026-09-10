"""D425 -- exits read off the detected zones, both lenses. Bar committed in e98b3ee BEFORE this file.

The walker and the book are D423's with the stop-on-close level allowed to vary by hold bar (shape
(N, HOLD)) -- a trail. With a constant stop broadcast they must reproduce D423 bit-identically.
Rules: FIXED, ZTP, ZTRAIL, FAR->ZTRAIL, ZTP+ZTRAIL, ZTP+FAR->ZTRAIL. Only ZTP is gated.

usage:  uv run python -u scripts/run_d425_zone_exits.py --run [--workers 8]
"""
import argparse, importlib.util, json, multiprocessing as mp, pathlib, sys, time
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
ZL = _load("d425l", "d425_zone_levels.py")
R23 = _load("d423r", "run_d423_structure_exits.py")

OUT = REPO / "data" / "d425_zone_exits.json"
FLAGS = REPO / "temp" / "d422_flags.npz"
HOLD, N10, SEEDS, N_DRAW = 5, 10, (419, 4190, 41900), 200
RULES = ("FIXED", "ZTP", "ZTRAIL", "FAR->ZTRAIL", "ZTP+ZTRAIL", "ZTP+FAR->ZTRAIL")


def walk2(OP, HI, LO, CL, E, ATR, side, last_close, target, stop2):
    """D423's walk_levels with stop2 of shape (n, B): the stop active on each bar."""
    s = side[:, None].astype(float)
    o, h, l, c = s * OP, s * HI, s * LO, s * CL
    hi_s = np.where(s > 0, h, l); sd = side.astype(float)
    tgt = np.where(np.isfinite(target), sd * np.where(np.isfinite(target), target, 0.0), np.inf)
    stp = np.where(np.isfinite(stop2), s * np.where(np.isfinite(stop2), stop2, 0.0), -np.inf)
    n, B = o.shape
    exit_bar = np.full(n, -1); fill = np.full(n, np.nan); done = np.zeros(n, bool)
    for j in range(B):
        ok = ~done & np.isfinite(o[:, j]) & np.isfinite(hi_s[:, j]) & np.isfinite(c[:, j])
        hit_tp = ok & (hi_s[:, j] >= tgt)
        hit_st = ok & ~hit_tp & (c[:, j] < stp[:, j])
        fill = np.where(hit_tp, np.maximum(tgt, o[:, j]), fill)
        fill = np.where(hit_st, c[:, j], fill)
        newly = hit_tp | hit_st
        exit_bar = np.where(newly, j, exit_bar); done |= newly
    fill = np.where(done, fill, sd * last_close)
    return dict(bar=exit_bar, price=sd * fill, early=done)


def sim2(I, n_slots, seed, target, stop2, pool_mask=None, run_targets=None):
    """D423's simulate_levels with a per-bar stop. Every other line is D419's."""
    t, side, E, cost = I["t"], I["side"], I["E"], I["cost"]
    OP, HI, LO, CL, c2 = I["OP"], I["HI"], I["LO"], I["CL"], I["c2"]
    T = int(I["T"][0]); N = len(t)
    rng = np.random.default_rng(seed)
    order = np.lexsort((rng.random(N), ~c2))
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


def levels_for(rule, L, I):
    N = len(I["t"]); nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan)
    tgt = L["ztp"] if rule.startswith("ZTP") else nan1
    far2 = np.repeat(L["far"][:, None], HOLD, axis=1)
    if "FAR->ZTRAIL" in rule:
        stp = np.where(I["side"][:, None] > 0, np.fmax(far2, L["trail"]), np.fmin(far2, L["trail"]))
    elif "ZTRAIL" in rule:
        stp = L["trail"]
    else:
        stp = nan2
    return tgt, stp


def assert_SIGN():
    E = np.full(3, 100.0); ATR = np.full(3, 2.0); side = np.array([1, -1, 1])
    OP = np.array([[100, 101, 100, 98.5, 99], [100, 99, 100, 101.5, 101], [100, 101, 98, 99, 100]], float)
    HI = np.array([[102, 103, 101, 99, 101], [101, 100, 102, 103, 102], [102, 105, 99, 100, 101]], float)
    LO = np.array([[99, 100, 97, 97, 98], [98, 97, 99, 99, 99], [99, 97, 98, 99, 100]], float)
    CL = np.array([[101, 102, 99, 97.5, 100], [99, 98, 101, 100 * 100 / 97.5, 100], [101, 97.5, 99, 100, 101]], float)
    last = CL[:, -1]; nan = np.nan
    trail = np.array([[nan, nan, 98, 98, 98], [nan, nan, 100 * 100 / 98, 100 * 100 / 98, 100 * 100 / 98], [nan, 98, 98, 98, 98]])
    tgt = np.array([nan, nan, 104.0])

    def check(trail):
        W = walk2(OP, HI, LO, CL, E, ATR, side, last, tgt, trail); r = R23.ret_of(W, E, side)
        assert W["bar"][0] == 3 and W["price"][0] == 97.5, "[SIGN] trail ratchets on bar 2; wick on bar 2 must not exit; close on bar 3 must"
        assert W["bar"][1] == 3 and abs(r[1] - r[0]) < 1e-12, "[SIGN] short log mirror"
        assert W["bar"][2] == 1 and W["price"][2] == 104.0, "[SIGN] limit before the close on the same bar"
    check(trail)
    fired = False
    try:
        check(np.where(np.isfinite(trail), trail - 3.0, trail))       # trail 3 below: ev0 never closes under it
    except AssertionError:
        fired = True
    assert fired, "[SIGN] the self-test cannot fail"


def _ctrl_worker(args):
    n_slots, draws, run_dist = args
    Bw = _load("d419w", "run_d419_book.py")
    I = dict(Bw.build_inputs()); z = np.load(FLAGS); pool = I["c2"] & z["s2any"]
    N = len(I["t"]); nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan); rd = np.array(run_dist); out = []
    for dr in draws:
        rng = np.random.default_rng(100000 + dr)
        R = sim2(I, n_slots, SEEDS[0], nan1, nan2, pool_mask=pool, run_targets=rng.choice(rd, size=N))
        S = Bw.score(I, R, n_slots); assert S["recon_rel"] < 1e-9, "[RECON] control"
        out.append((dr, S["net_bp"], S["gross_bp"], S["run"], S["turnover"]))
    return out


def run(workers):
    t0 = time.time()
    print("D425  exits read off the detected zones -- ZTP, ZTRAIL, both lenses\n      the bar was committed in e98b3ee BEFORE this ran\n")
    assert_SIGN(); print("  [SIGN] ratcheting trail, wick vs close, short log mirror, limit-before-close; the check fires when broken")
    I, P, B, fl, M, zones = ZL.load()
    L = ZL.levels(I, zones)
    t, i, side, E, ATR, c2 = I["t"], I["i"], I["side"], I["E"], I["ATR"], I["c2"]
    A = fl["s2any"]; prim = A & c2; N = len(t); T = int(I["T"][0])
    yr = np.array([int(str(x)[:4]) for x in I["dates"][t]])
    last = P["CL"][np.clip(t + HOLD, 0, T - 1), i]
    OP, HI, LO, CL = I["OP"], I["HI"], I["LO"], I["CL"]
    nan1 = np.full(N, np.nan); nan2 = np.full((N, HOLD), np.nan)
    assert N == 180050 and int(prim.sum()) == 9411, "[STAGE0]"
    # [X] constant-stop broadcast == D423 on all events
    L23 = R23.LV.levels(I, P)
    far2 = np.repeat(L23["far"][:, None], HOLD, axis=1)
    W23 = R23.walk_levels(OP, HI, LO, CL, E, ATR, side, last, L23["swing"], L23["far"])
    Wx = walk2(OP, HI, LO, CL, E, ATR, side, last, L23["swing"], far2)
    assert all(np.array_equal(W23[k], Wx[k]) for k in ("bar", "early", "price")), "[X] walk2 != D423 SWING+BREACH"
    print("  [X]    walk2 with a constant stop == D423's SWING+BREACH walker, bit for bit, all 180,050")
    r_fixed = I["r_base"]

    res = dict(stage0={}, per_trade={}, null={}, books={}, deltas={}, premium={}, control=None)
    eng = np.isfinite(L["trail"]).any(axis=1); first = np.where(eng, np.argmax(np.isfinite(L["trail"]), axis=1) + 1, -1)
    for lab, m in (("ANY & cell 2", prim), ("ANY pooled", A), ("cell 2 all", c2), ("pooled", np.ones(N, bool))):
        res["stage0"][lab] = dict(ztp_coverage=float(np.isfinite(L["ztp"][m]).mean()), trail_engaged=float(eng[m].mean()),
                                  engage_bar_p50=float(np.median(first[m & eng])) if (m & eng).any() else None,
                                  n_new_p50=float(np.median(L["n_new"][m])))
        s0 = res["stage0"][lab]
        print(f"  {lab:13s} ZTP coverage {100*s0['ztp_coverage']:5.1f}%   ZTRAIL engages on {100*s0['trail_engaged']:5.1f}% of trades, first at bar {s0['engage_bar_p50']}")

    print("\n1. PER TRADE, paired against the fixed exit")
    masks = [("ANY & cell 2", prim), ("ANY & cell 2  long", prim & (side > 0)), ("ANY & cell 2  short", prim & (side < 0)),
             ("ANY & cell 2  2018+", prim & (yr >= 2018)), ("ANY pooled", A), ("cell 2 all", c2)]
    walks = {}
    for rule in RULES[1:]:
        tgt, stp = levels_for(rule, L, I)
        W = walk2(OP, HI, LO, CL, E, ATR, side, last, tgt, stp); walks[rule] = W; rr = R23.ret_of(W, E, side)
        for lab, m in masks:
            p = R23.paired(rr, r_fixed, W, m, E, side, f"{rule:16s} {lab}"); res["per_trade"][f"{rule}|{lab}"] = p; R23.show(p)
        print()
    print("2. THE DISTANCE-PERMUTATION NULL for ZTP (within day, ANY & cell 2, 200 draws)")
    q = R23.distance_null(L["ztp"], I, walks["ZTP"], r_fixed, prim, last, N_DRAW, 425); res["null"]["ZTP"] = q
    print(f"  ZTP observed {q['observed_bp']:+6.2f}   null p5 {q['p5']:+6.2f}  p50 {q['p50']:+6.2f}  p95 {q['p95']:+6.2f} (+-{q['se']:.2f})   margin {q['margin_se']:+5.1f} SE   "
          f"{'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}")

    print("\n3. THE BOOK -- cell-2 ANY-REQUIRED, 10 slots")
    pool = prim
    R22 = M.simulate(I, N10, SEEDS[0], pool_mask=pool); R0 = sim2(I, N10, SEEDS[0], nan1, nan2, pool_mask=pool)
    assert [x[:3] for x in R0["trades"]] == [x[:3] for x in R22["trades"]] and np.array_equal(R0["gross"], R22["gross"]), "[P2] FIXED"
    R23b = R23.simulate_levels(I, N10, SEEDS[0], L23["swing"], L23["far"], pool_mask=pool)
    Rx = sim2(I, N10, SEEDS[0], L23["swing"], far2, pool_mask=pool)
    assert [x[:3] for x in Rx["trades"]] == [x[:3] for x in R23b["trades"]] and np.array_equal(Rx["gross"], R23b["gross"]), "[P2] SWING+BREACH"
    print("  [P2]   sim2 == D422's ANY-REQ FIXED book and == D423's SWING+BREACH book, bit for bit")
    series = {}; t1 = time.time()
    for rule in RULES:
        tgt, stp = levels_for(rule, L, I)
        for seed in SEEDS:
            R = sim2(I, N10, seed, tgt, stp, pool_mask=pool); S = B.score(I, R, N10); assert S["recon_rel"] < 1e-9, "[RECON]"
            series[(rule, seed)] = S["net_series"]
            if rule != "FIXED":
                res["premium"][f"{rule}_s{seed}"] = B.premium(I, R, T)
            if rule == "ZTP" and seed == SEEDS[0]:
                res["run_dist_ztp"] = S["run_dist"].tolist()
            res["books"][f"{rule}_s{seed}"] = {k: v for k, v in S.items() if not k.endswith("_series") and k != "run_dist"}
    print(f"  {len(res['books'])} books in {time.time()-t1:.0f}s   [RECON] all\n")
    print(f"  {'rule':16s} {'gross':>7s} {'net':>7s} {'cost':>6s} {'util':>6s} {'trades':>7s} {'run':>5s} {'early':>6s} {'per trade':>9s}   net by seed")
    dates = I["dates"]; d0 = R0["d0"]
    for rule in RULES:
        S = res["books"][f"{rule}_s{SEEDS[0]}"]; nets = [res["books"][f"{rule}_s{s}"]["net_bp"] for s in SEEDS]
        print(f"  {rule:16s} {S['gross_bp']:+7.3f} {S['net_bp']:+7.3f} {S['cost_bp']:6.3f} {100*S['utilisation']:5.1f}% {S['trades']:7,} {S['run']:5.2f} {100*S['early_share']:5.1f}% {S['trade_mean_bp']:+9.2f}   "
              + " ".join(f"{x:+.3f}" for x in nets))
        if rule != "FIXED":
            diff = np.mean([series[(rule, s)] - series[("FIXED", s)] for s in SEEDS], axis=0); se, mean = B.block_boot(diff, dates[d0:])
            g = np.mean([res["books"][f"{rule}_s{s}"]["gross_bp"] - res["books"][f"FIXED_s{s}"]["gross_bp"] for s in SEEDS])
            res["deltas"][rule] = dict(gross_delta=float(g), net_delta=float(1e4 * mean), se=float(1e4 * se), t=float(mean / se), net_abs=float(np.mean(nets)))
    print("\n  deltas vs FIXED, mean over seeds, monthly block-bootstrap SE")
    for rule, dd in res["deltas"].items():
        print(f"  {rule:16s} gross delta {dd['gross_delta']:+6.3f}   NET delta {dd['net_delta']:+6.3f} +- {dd['se']:.3f}   {dd['t']:+4.1f} SE")
    print("\n  the replacement premium (D304), seed 419")
    for rule in RULES[1:]:
        pr = res["premium"][f"{rule}_s{SEEDS[0]}"].get("avail", {})
        print(f"  {rule:16s} n {pr.get('n', 0):6,}" + (f"  premium {pr['premium_bp']:+7.2f} +- {pr['se_bp']:.2f}   arriving {pr['arriving_bp']:+7.2f}   forfeited {pr['forfeited_bp']:+7.2f}" if "premium_bp" in pr else ""))

    print(f"\n4. THE SAMPLED-RUNS CONTROL for ZTP ({N_DRAW} draws, {workers} workers)")
    rd = res["run_dist_ztp"]; rng = np.random.default_rng(100000); tg0 = rng.choice(np.array(rd), size=N)
    S_in = B.score(I, sim2(I, N10, SEEDS[0], nan1, nan2, pool_mask=pool, run_targets=tg0), N10)
    with mp.Pool(workers) as pl:
        results = pl.map(_ctrl_worker, [(N10, list(range(w, N_DRAW, workers)), rd) for w in range(workers)])
    out = sorted(o for oo in results for o in oo)
    assert abs(out[0][1] - S_in["net_bp"]) < 1e-12, "[CHUNK]"
    net = np.array([o[1] for o in out]); run = np.array([o[3] for o in out]); obs = res["deltas"]["ZTP"]["net_abs"]
    p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs - p95
    bk_run = res["books"][f"ZTP_s{SEEDS[0]}"]["run"]; assert abs(run.mean() - bk_run) < 0.05, "[NUISANCE]"
    res["control"] = dict(p5=float(np.quantile(net, .05)), p50=float(np.median(net)), p95=p95, se=se, observed=obs, margin_se=float(edge / se),
                          beats=bool(edge > 0), unresolved=bool(abs(edge) < 2 * se), passes=bool(edge > 0 and abs(edge) >= 2 * se), run=float(run.mean()))
    print(f"  [CHUNK] worker draw 0 == in-process;  [NUISANCE] control run {run.mean():.3f} vs ZTP {bk_run:.3f}")
    print(f"  ZTP net {obs:+.3f}   control p5 {res['control']['p5']:+.3f}  p50 {res['control']['p50']:+.3f}  p95 {p95:+.3f} (+-{se:.3f})   margin {edge/se:+.1f} SE   "
          f"{'PASS' if res['control']['passes'] else ('UNRESOLVED' if res['control']['unresolved'] else 'FAIL')}")

    p1 = res["per_trade"]["ZTP|ANY & cell 2"]; dd = res["deltas"]["ZTP"]; ct = res["control"]
    T1 = bool(p1["delta_bp"] > 0 and p1["t"] >= 2); T2 = bool(res["null"]["ZTP"]["passes"]); T3 = bool(dd["net_delta"] > 0 and dd["t"] >= 2 and ct["passes"])
    res["bar"] = dict(T1=T1, T2=T2, T3=T3, clears=bool(T1 and T2 and T3))
    print("\n5. THE BAR -- ZTP on ANY & cell 2")
    print(f"    T1 paired delta > 0 by 2 SE           : {T1}   ({p1['delta_bp']:+.2f} +- {p1['se_bp']:.2f}, {p1['t']:+.1f} SE)")
    print(f"    T2 beats the distance-permutation p95 : {T2}   (margin {res['null']['ZTP']['margin_se']:+.1f} SE)")
    print(f"    T3 book net delta > 0 by 2 SE, > ctrl : {T3}   (delta {dd['net_delta']:+.3f} +- {dd['se']:.3f}; ctrl margin {ct['margin_se']:+.1f} SE)")
    print(f"    ZTP {'CLEARS' if res['bar']['clears'] else 'FAILS'} the bar")
    ptr = res["per_trade"]["ZTRAIL|ANY & cell 2"]; pft = res["per_trade"]["FAR->ZTRAIL|ANY & cell 2"]; pall = res["per_trade"]["ZTP+FAR->ZTRAIL|ANY & cell 2"]
    s0 = res["stage0"]["ANY & cell 2"]
    print("\n6. PREDICTIONS")
    print(f"    X-a ZTP -4..+1 inside 2 SE, fires 12-20%, forfeit -5..-20 : {p1['delta_bp']:+.2f} ({p1['t']:+.1f} SE), {100*p1['early']:.1f}%, forfeit {p1.get('forfeit_bp', float('nan')):+.2f}")
    print(f"    X-b ZTP at its null's median, inside 2 SE of p95         : p50 {res['null']['ZTP']['p50']:+.2f}, margin {res['null']['ZTP']['margin_se']:+.1f} SE")
    print(f"    X-c ZTRAIL engages 10-25%, fires 3-8%, delta -1..-4       : engages {100*s0['trail_engaged']:.1f}%, fires {100*ptr['early']:.1f}%, {ptr['delta_bp']:+.2f} ({ptr['t']:+.1f} SE)")
    print(f"    X-d FAR->ZTRAIL within 2 of -6.61; ZTP+FAR->ZTRAIL -8..-14 : {pft['delta_bp']:+.2f};  {pall['delta_bp']:+.2f}")
    print(f"    X-e ZTP book gross -0.4..+0.3, util<68.2, net inside 2 SE, above ctrl p50 below p95; trail books negative : gross {dd['gross_delta']:+.3f}, "
          f"util {100*res['books'][f'ZTP_s{SEEDS[0]}']['utilisation']:.1f}%, net {dd['t']:+.1f} SE, vs p50 {obs-ct['p50']:+.3f}, vs p95 {edge:+.3f};  "
          f"trails {res['deltas']['ZTRAIL']['t']:+.1f} / {res['deltas']['FAR->ZTRAIL']['t']:+.1f} SE")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT}   total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.run:
        run(a.workers)

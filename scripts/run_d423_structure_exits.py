"""D423 -- structure exits on the second zone, both lenses. The bar was committed in cb0d0a8 BEFORE
this file existed.

PER TRADE   a level walker in long space (D417's construction) with per-event TARGET (limit, fills at
            the level or better) and STOP-ON-CLOSE (a close beyond the level, fills at the close)
            prices. Given E +- 2 ATR it must reproduce D417's TP 2.0 bit-identically ([X]).
            T1  SWING paired delta over FIXED on ANY & cell 2 > 0 by 2 SE
            T2  ... beats the p95 of a WITHIN-DAY PERMUTATION OF THE SWING DISTANCE (200 draws)
THE BOOK    D419's simulator with the same level triggers. No levels == D422's ANY-REQ FIXED book;
            E +- 2 ATR == D419's TP book; both bit-identical ([P2]).
            T3  cell-2 ANY-REQUIRED 10-slot, SWING net - FIXED net > 0 by 2 SE over three seeds
                (monthly block bootstrap) AND SWING net > p95 of the sampled-runs control
Rules: FIXED, SWING, OPP, BREACH, SWING+BREACH. Only SWING is gated.

usage:  uv run python -u scripts/run_d423_structure_exits.py --run [--workers 8]
"""
import argparse
import importlib.util
import json
import multiprocessing as mp
import pathlib
import sys
import time

import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d423l", REPO / "scripts" / "d423_exit_levels.py")
LV = importlib.util.module_from_spec(_s); sys.modules["d423l"] = LV; _s.loader.exec_module(LV)
_s17 = importlib.util.spec_from_file_location("d417r", REPO / "scripts" / "run_d417_exits.py")
R17 = importlib.util.module_from_spec(_s17); sys.modules["d417r"] = R17; _s17.loader.exec_module(R17)

OUT = REPO / "data" / "d423_structure_exits.json"
FLAGS = REPO / "temp" / "d422_flags.npz"
HOLD = 5
N10 = 10
SEEDS = (419, 4190, 41900)
N_DRAW = 200
RULES = ("FIXED", "SWING", "OPP", "BREACH", "SWING+BREACH")


# ------------------------------------------------------------------ the per-trade walker
def walk_levels(OP, HI, LO, CL, E, ATR, side, last_close, target, stop_close):
    """Exit bar, fill and early flag for one rule over (n, B) bar arrays, in LONG space.
    target / stop_close are per-event PRICES (NaN = none). A resting limit fills the moment the bar
    trades through it (at the level or the open, whichever is better); the stop is evaluated on the
    close only, after the limit. NaN bars are skipped, as D417's are."""
    s = side[:, None].astype(float)
    o, h, l, c = s * OP, s * HI, s * LO, s * CL
    hi_s = np.where(s > 0, h, l)
    sd = side.astype(float)
    tgt = np.where(np.isfinite(target), sd * np.where(np.isfinite(target), target, 0.0), np.inf)
    stp = np.where(np.isfinite(stop_close), sd * np.where(np.isfinite(stop_close), stop_close, 0.0), -np.inf)
    n, B = o.shape
    exit_bar = np.full(n, -1); fill = np.full(n, np.nan); done = np.zeros(n, bool)
    for j in range(B):
        ok = ~done & np.isfinite(o[:, j]) & np.isfinite(hi_s[:, j]) & np.isfinite(c[:, j])
        hit_tp = ok & (hi_s[:, j] >= tgt)
        hit_st = ok & ~hit_tp & (c[:, j] < stp)
        fill = np.where(hit_tp, np.maximum(tgt, o[:, j]), fill)
        fill = np.where(hit_st, c[:, j], fill)
        newly = hit_tp | hit_st
        exit_bar = np.where(newly, j, exit_bar); done |= newly
    fill = np.where(done, fill, sd * last_close)
    return dict(bar=exit_bar, price=sd * fill, early=done)


def ret_of(W, E, side):
    return side.astype(float) * (np.log(W["price"]) - np.log(E))


def assert_SIGN():
    """[SIGN] the walker does what the words say, in money, long and short -- and the check can fail."""
    E = np.array([100.0, 100.0, 100.0, 100.0]); ATR = np.full(4, 2.0); side = np.array([1, -1, 1, 1])
    OP = np.array([[100, 101, 103, 103, 103], [100, 99, 97, 97, 97], [100, 99, 98, 99, 100], [100, 101, 98, 99, 100]], float)
    HI = np.array([[102, 105, 103, 103, 103], [101, 100, 98, 98, 98], [100, 99, 99, 100, 101], [102, 105, 99, 100, 101]], float)
    LO = np.array([[99, 101, 102, 102, 102], [98, 95, 97, 97, 97], [97, 97, 98, 99, 100], [99, 97, 98, 99, 100]], float)
    CL = np.array([[101, 103, 103, 103, 103], [99, 97, 97, 97, 97], [99, 97.5, 99, 100, 101], [101, 97.5, 99, 100, 101]], float)
    last = CL[:, -1]
    # the short's swing is the LOG mirror of the long's (+4% is 100/1.04 on the way down, not 96)
    swing = np.array([104.0, 100.0 / 1.04, np.nan, 104.0]); far = np.array([np.nan, np.nan, 98.0, 98.0])

    def check(swing, far):
        W = walk_levels(OP, HI, LO, CL, E, ATR, side, last, swing, far)
        F = walk_levels(OP, HI, LO, CL, E, ATR, side, last, np.full(4, np.nan), np.full(4, np.nan))
        r, rf = ret_of(W, E, side), ret_of(F, E, side)
        assert W["bar"][0] == 1 and W["price"][0] == 104.0 and r[0] > 0, "[SIGN] long swing"
        assert W["bar"][1] == 1 and abs(W["price"][1] - 100.0 / 1.04) < 1e-12 and abs(r[1] - r[0]) < 1e-12, "[SIGN] short mirror"
        assert W["bar"][2] == 1 and W["price"][2] == 97.5 and r[2] < rf[2], "[SIGN] wick through FAR on bar 0 must not exit; close through it on bar 1 must"
        assert W["bar"][3] == 1 and W["price"][3] == 104.0, "[SIGN] limit before close on the same bar"
        assert not F["early"].any() and np.all(F["price"] == last), "[SIGN] no levels is the time stop"
    check(swing, far)
    fired = False
    try:
        check(swing, np.array([np.nan, np.nan, 96.0, 98.0]))     # FAR below the path: ev2 never exits
    except AssertionError:
        fired = True
    assert fired, "[SIGN] the self-test cannot fail"


# ------------------------------------------------------------------ the book
def simulate_levels(I, n_slots, seed, target, stop_close, pool_mask=None, run_targets=None):
    """D419's simulate, verbatim in every line that is not the trigger; the trigger reads per-event
    prices. run_targets (ages) turns it into the sampled-runs control: no trigger at all."""
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
    tg = np.where(np.isfinite(target), target, np.nan); sc = np.where(np.isfinite(stop_close), stop_close, np.nan)
    held = {}; held_names = set()
    gross = np.zeros(T); costs = np.zeros(T); occ = np.zeros(T, np.int32)
    ent = np.zeros(T, np.int32); frees = np.zeros(T, np.int32); refilled = np.zeros(T, np.int32)
    early_frees = np.zeros(T, np.int32)
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
            s = float(side[k])
            prev = lgE[k] if a == 0 else lgCL[k, a - 1]
            os_, hs = s * o, (s * h if s > 0 else s * l)
            trig = False; fill = None
            if run_targets is None and np.isfinite(tg[k]) and hs >= s * tg[k]:
                trig, fill = True, s * max(s * tg[k], os_)
            if trig:
                mark = s * (np.log(fill) - prev)
                gross[d] += mark; occ[d] += 1
                held.pop(k); held_names.discard(int(I["i"][k]))
                trades.append((k, st[1] + mark, a + 1, True, d, fill)); frees[d] += 1; freed.append((k, fill, a + 1, True))
                continue
            mark = s * (lgCL[k, a] - prev)
            gross[d] += mark; occ[d] += 1
            st[0] += 1; st[1] += mark; st[2] = max(st[2], hs)
            breached = run_targets is None and np.isfinite(sc[k]) and (s * c < s * sc[k])
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
                if nm in held_names or k in held:
                    continue
                if not np.isfinite(E[k]) or E[k] <= 0:
                    continue
                held[k] = [0, 0.0, side[k] * E[k]]; held_names.add(nm)
                costs[d] += cost[k]; ent[d] += 1; free -= 1; arrivals.append(k)
        for j, (kd, fill, age, early) in enumerate(freed):
            if early:
                swaps.append((kd, fill, d, age, arrivals[j] if j < len(arrivals) else -1))
        refilled[d] += min(len(freed), len(arrivals))
        early_frees[d] += len(freed)
    resid = sum(st[1] for st in held.values())
    return dict(gross=gross, costs=costs, occ=occ, ent=ent, frees=frees, refilled=refilled,
                early_frees=early_frees, trades=trades, swaps=swaps, resid=resid, d0=d0)


def levels_for(rule, L, I):
    nan = np.full(len(I["t"]), np.nan)
    tgt = L["swing"] if rule in ("SWING", "SWING+BREACH") else (L["opp"] if rule == "OPP" else nan)
    stp = L["far"] if rule in ("BREACH", "SWING+BREACH") else nan
    return tgt, stp


# ------------------------------------------------------------------ per-trade statistics
def paired(rr, rf, W, mask, E, side, label):
    d = (rr - rf)[mask]; n = d.size
    early = W["early"][mask]; hold = np.where(early, W["bar"][mask] + 1, HOLD).astype(float)
    out = dict(label=label, n=int(n), fixed_bp=float(1e4 * rf[mask].mean()), rule_bp=float(1e4 * rr[mask].mean()),
               delta_bp=float(1e4 * d.mean()), se_bp=float(1e4 * d.std(ddof=1) / np.sqrt(n)),
               early=float(early.mean()), hold=float(hold.mean()),
               bp_per_day_fixed=float(1e4 * rf[mask].mean() / HOLD), bp_per_day_rule=float(1e4 * rr[mask].mean() / hold.mean()),
               std_ratio=float(rr[mask].std() / rf[mask].std()))
    out["t"] = out["delta_bp"] / out["se_bp"] if out["se_bp"] > 0 else float("nan")
    if early.any():
        out["would_have_bp"] = float(1e4 * rf[mask][early].mean()); out["filled_at_bp"] = float(1e4 * rr[mask][early].mean())
        out["forfeit_bp"] = out["filled_at_bp"] - out["would_have_bp"]
    return out


def show(p):
    fx = f"   would-have {p['would_have_bp']:+8.2f}  filled-at {p['filled_at_bp']:+8.2f}  forfeit {p['forfeit_bp']:+6.2f}" if "would_have_bp" in p else ""
    print(f"  {p['label']:34s} n {p['n']:7,}  fixed {p['fixed_bp']:+7.2f}  rule {p['rule_bp']:+7.2f}  PAIRED {p['delta_bp']:+6.2f} ± {p['se_bp']:4.2f}  "
          f"t {p['t']:+5.1f}  early {100*p['early']:5.1f}%  hold {p['hold']:4.2f}d  bp/d {p['bp_per_day_rule']:+5.2f}  std x{p['std_ratio']:.2f}{fx}")


def perm_within_day(vals, t, mask, rng):
    """Permute vals among the masked events of each day."""
    idx = np.flatnonzero(mask)
    base = idx[np.lexsort((np.arange(idx.size), t[idx]))]
    perm = idx[np.lexsort((rng.random(idx.size), t[idx]))]
    out = vals.copy(); out[perm] = vals[base]
    return out


def distance_null(level, I, W_in, r_fixed, mask, last, n, seed):
    """T2: the level's DISTANCE in ATR is permuted within day among the masked events; each event
    then walks to the permuted distance from its own entry. Keeps the distance distribution,
    destroys the alignment with this event's structure."""
    t, side, E, ATR = I["t"], I["side"], I["E"], I["ATR"]
    dist = side * (level - E) / ATR
    obs = float(((ret_of(W_in, E, side) - r_fixed)[mask]).mean())
    rng = np.random.default_rng(seed); draws = np.empty(n); nan = np.full(len(t), np.nan)
    for b in range(n):
        dp = perm_within_day(dist, t, mask, rng)
        tgt = np.where(np.isfinite(dp), E + side * dp * ATR, np.nan)
        W = walk_levels(I["OP"], I["HI"], I["LO"], I["CL"], E, ATR, side, last, tgt, nan)
        draws[b] = ((ret_of(W, E, side) - r_fixed)[mask]).mean()
    p95 = float(np.quantile(draws, .95)); se = float(draws.std(ddof=1) / np.sqrt(n)); edge = obs - p95
    return dict(observed_bp=1e4 * obs, p5=float(1e4 * np.quantile(draws, .05)), p50=float(1e4 * np.median(draws)), p95=1e4 * p95,
                se=1e4 * se, margin_se=float(edge / se) if se > 0 else float("inf"), beats=bool(edge > 0),
                unresolved=bool(abs(edge) < 2 * se), passes=bool(edge > 0 and abs(edge) >= 2 * se))


# ------------------------------------------------------------------ control
def _ctrl_worker(args):
    n_slots, draws, run_dist = args
    _b = importlib.util.spec_from_file_location("d419w", REPO / "scripts" / "run_d419_book.py")
    Bw = importlib.util.module_from_spec(_b); sys.modules["d419w"] = Bw; _b.loader.exec_module(Bw)
    I = dict(Bw.build_inputs()); z = np.load(FLAGS); pool = I["c2"] & z["s2any"]
    rd = np.array(run_dist); nan = np.full(len(I["t"]), np.nan); out = []
    for dr in draws:
        rng = np.random.default_rng(100000 + dr)
        targets = rng.choice(rd, size=len(I["t"]))
        R = simulate_levels(I, n_slots, SEEDS[0], nan, nan, pool_mask=pool, run_targets=targets)
        S = Bw.score(I, R, n_slots); assert S["recon_rel"] < 1e-9, "[RECON] control"
        out.append((dr, S["net_bp"], S["gross_bp"], S["run"], S["turnover"]))
    return out


# ------------------------------------------------------------------ run
def run(workers):
    t0 = time.time()
    print("D423  structure exits on the second zone -- SWING, OPP, BREACH, both lenses")
    print("      the bar was committed in cb0d0a8 BEFORE this ran\n")
    assert_SIGN()
    print("  [SIGN] long swing, short mirror, wick-vs-close through FAR, limit-before-close, no-levels == time stop; and the check fires when broken")

    I, P, B, fl, M = LV.load()
    L = LV.levels(I, P)
    t, i, side, E, ATR, c2 = I["t"], I["i"], I["side"], I["E"], I["ATR"], I["c2"]
    A = fl["s2any"]; prim = A & c2; N = len(t); T = int(I["T"][0])
    yr = np.array([int(str(x)[:4]) for x in I["dates"][t]])
    last = P["CL"][np.clip(t + HOLD, 0, T - 1), i]
    OP, HI, LO, CL = I["OP"], I["HI"], I["LO"], I["CL"]
    nan = np.full(N, np.nan)
    assert int(prim.sum()) == 9411 and N == 180050, f"[STAGE0] {N} / {int(prim.sum())}"

    # [X] the level walker == D417's TP 2.0, bit for bit
    W17 = R17.walk(OP, HI, LO, CL, E, ATR, side, last)["TP2.0"]
    Wx = walk_levels(OP, HI, LO, CL, E, ATR, side, last, E + side * 2.0 * ATR, nan)
    assert np.array_equal(W17["bar"], Wx["bar"]) and np.array_equal(W17["early"], Wx["early"]) \
        and np.array_equal(W17["price"], Wx["price"]), "[X] level walker != D417 TP 2.0"
    print("  [X]    level walker given E +- 2 ATR == D417's TP 2.0 exit bar, fill and early flag on all 180,050 events")
    WF = walk_levels(OP, HI, LO, CL, E, ATR, side, last, nan, nan)
    r_fixed = ret_of(WF, E, side)
    dif = np.nanmax(np.abs(r_fixed - I["r_base"]))
    assert dif < 1e-9, f"[BASIS] FIXED walk vs r_base differ by {dif:.2e}"
    print(f"  [BASIS] no-level walk == r_base to {dif:.1e}")

    res = dict(stage0={}, per_trade={}, null={}, books={}, deltas={}, premium={}, control=None)
    for nm_, lv in (("SWING", L["swing"]), ("OPP", L["opp"]), ("FAR", L["far"])):
        f = prim & np.isfinite(lv); d = LV.dist_atr(lv, I)
        res["stage0"][nm_] = dict(coverage=float(f.sum() / prim.sum()), dist_p50=float(np.nanmedian(np.abs(d[f]))))

    # ---------------- per-trade lens
    print("\n1. PER TRADE, paired against the fixed exit")
    masks = [("ANY & cell 2", prim), ("ANY & cell 2  long", prim & (side > 0)), ("ANY & cell 2  short", prim & (side < 0)),
             ("ANY & cell 2  2018+", prim & (yr >= 2018)), ("ANY pooled", A), ("cell 2 all", c2)]
    walks = {}
    for rule in RULES[1:]:
        tgt, stp = levels_for(rule, L, I)
        W = walk_levels(OP, HI, LO, CL, E, ATR, side, last, tgt, stp); walks[rule] = W
        rr = ret_of(W, E, side)
        for lab, m in masks:
            p = paired(rr, r_fixed, W, m, E, side, f"{rule:13s} {lab}"); res["per_trade"][f"{rule}|{lab}"] = p; show(p)
        print()
    # T2: the distance-permutation null, SWING primary; OPP reported
    print("2. THE DISTANCE-PERMUTATION NULL (within day, ANY & cell 2, 200 draws)")
    for rule, lv in (("SWING", L["swing"]), ("OPP", L["opp"])):
        q = distance_null(lv, I, walks[rule], r_fixed, prim, last, N_DRAW, 423); res["null"][rule] = q
        print(f"  {rule:6s} observed {q['observed_bp']:+6.2f}   null p5 {q['p5']:+6.2f}  p50 {q['p50']:+6.2f}  p95 {q['p95']:+6.2f} (±{q['se']:.2f})   "
              f"margin {q['margin_se']:+5.1f} SE   {'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}")

    # ---------------- the book
    print("\n3. THE BOOK -- cell-2 ANY-REQUIRED, 10 slots")
    pool = prim
    R22 = M.simulate(I, N10, SEEDS[0], pool_mask=pool)
    R0 = simulate_levels(I, N10, SEEDS[0], nan, nan, pool_mask=pool)
    assert [x[:3] for x in R0["trades"]] == [x[:3] for x in R22["trades"]] and np.array_equal(R0["gross"], R22["gross"]), "[P2] no levels != D422's ANY-REQ FIXED book"
    R19 = B.simulate(I, "TP", B.N_PRIMARY, SEEDS[0])
    Rt = simulate_levels(I, B.N_PRIMARY, SEEDS[0], E + side * 2.0 * ATR, nan)
    assert [x[:3] for x in Rt["trades"]] == [x[:3] for x in R19["trades"]] and np.array_equal(Rt["gross"], R19["gross"]), "[P2] E +- 2 ATR != D419's TP book"
    print("  [P2]   no levels == D422's ANY-REQ FIXED book; E +- 2 ATR == D419's TP book (50 slots, pooled); both bit-identical")
    t1 = time.time(); series = {}
    for rule in RULES:
        tgt, stp = levels_for(rule, L, I)
        for seed in SEEDS:
            R = simulate_levels(I, N10, seed, tgt, stp, pool_mask=pool); S = B.score(I, R, N10)
            assert S["recon_rel"] < 1e-9, "[RECON]"
            series[(rule, seed)] = S["net_series"]
            if rule != "FIXED":
                res["premium"][f"{rule}_s{seed}"] = B.premium(I, R, T)
            if rule == "SWING" and seed == SEEDS[0]:
                res["run_dist_swing"] = S["run_dist"].tolist()
            res["books"][f"{rule}_s{seed}"] = {k: v for k, v in S.items() if not k.endswith("_series") and k != "run_dist"}
    print(f"  {len(res['books'])} books in {time.time()-t1:.0f}s   [RECON] all\n")
    print(f"  {'rule':14s} {'gross':>7s} {'net':>7s} {'cost':>6s} {'util':>6s} {'trades':>7s} {'run':>5s} {'early':>6s} {'per trade':>9s}   net by seed")
    dates = I["dates"]; d0 = R0["d0"]
    for rule in RULES:
        S = res["books"][f"{rule}_s{SEEDS[0]}"]
        nets = [res["books"][f"{rule}_s{s}"]["net_bp"] for s in SEEDS]
        print(f"  {rule:14s} {S['gross_bp']:+7.3f} {S['net_bp']:+7.3f} {S['cost_bp']:6.3f} {100*S['utilisation']:5.1f}% {S['trades']:7,} {S['run']:5.2f} {100*S['early_share']:5.1f}% {S['trade_mean_bp']:+9.2f}   "
              + " ".join(f"{x:+.3f}" for x in nets))
        if rule != "FIXED":
            diff = np.mean([series[(rule, s)] - series[("FIXED", s)] for s in SEEDS], axis=0)
            se, mean = B.block_boot(diff, dates[d0:])
            g = np.mean([res["books"][f"{rule}_s{s}"]["gross_bp"] - res["books"][f"FIXED_s{s}"]["gross_bp"] for s in SEEDS])
            res["deltas"][rule] = dict(gross_delta=float(g), net_delta=float(1e4 * mean), se=float(1e4 * se), t=float(mean / se) if se > 0 else float("nan"),
                                       net_abs=float(np.mean(nets)))
    print("\n  deltas vs FIXED, mean over seeds, monthly block-bootstrap SE")
    for rule, dd in res["deltas"].items():
        print(f"  {rule:14s} gross delta {dd['gross_delta']:+6.3f}   NET delta {dd['net_delta']:+6.3f} ± {dd['se']:.3f}   {dd['t']:+4.1f} SE")
    print("\n  the replacement premium (D304), seed 419")
    for rule in RULES[1:]:
        pr = res["premium"][f"{rule}_s{SEEDS[0]}"].get("avail", {})
        if "premium_bp" in pr:
            print(f"  {rule:14s} n {pr['n']:6,}  premium {pr['premium_bp']:+7.2f} ± {pr['se_bp']:.2f}   arriving {pr['arriving_bp']:+7.2f}   forfeited {pr['forfeited_bp']:+7.2f}")
        else:
            print(f"  {rule:14s} n {pr.get('n', 0)} swaps")

    # ---------------- T3's control
    print(f"\n4. THE SAMPLED-RUNS CONTROL for SWING ({N_DRAW} draws, {workers} workers)")
    np.savez_compressed(FLAGS, **fl) if not FLAGS.exists() else None
    rd = res["run_dist_swing"]
    rng = np.random.default_rng(100000); tg0 = rng.choice(np.array(rd), size=N)
    S_in = B.score(I, simulate_levels(I, N10, SEEDS[0], nan, nan, pool_mask=pool, run_targets=tg0), N10)
    jobs = [(N10, list(range(w, N_DRAW, workers)), rd) for w in range(workers)]
    with mp.Pool(workers) as pl:
        results = pl.map(_ctrl_worker, jobs)
    out = sorted(o for oo in results for o in oo)
    assert abs(out[0][1] - S_in["net_bp"]) < 1e-12, f"[CHUNK] worker draw 0 {out[0][1]} != in-process {S_in['net_bp']}"
    net = np.array([o[1] for o in out]); run = np.array([o[3] for o in out])
    obs = res["deltas"]["SWING"]["net_abs"]
    p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs - p95
    swing_run = np.mean([res["books"][f"SWING_s{s}"]["run"] for s in SEEDS])
    assert abs(run.mean() - res["books"][f"SWING_s{SEEDS[0]}"]["run"]) < 0.05, f"[NUISANCE] control run {run.mean():.3f} vs SWING {swing_run:.3f}"
    res["control"] = dict(n=int(net.size), p5=float(np.quantile(net, .05)), p50=float(np.median(net)), p95=p95, se=se, observed=obs,
                          margin_se=float(edge / se), beats=bool(edge > 0), unresolved=bool(abs(edge) < 2 * se),
                          passes=bool(edge > 0 and abs(edge) >= 2 * se), run=float(run.mean()))
    print(f"  [CHUNK] worker draw 0 == in-process;  [NUISANCE] control run {run.mean():.3f} vs SWING {swing_run:.3f}")
    print(f"  SWING net {obs:+.3f} (mean over seeds)   control p5 {res['control']['p5']:+.3f}  p50 {res['control']['p50']:+.3f}  p95 {p95:+.3f} (±{se:.3f})   "
          f"margin {edge/se:+.1f} SE   {'PASS' if res['control']['passes'] else ('UNRESOLVED' if res['control']['unresolved'] else 'FAIL')}")

    # ---------------- the bar
    p1 = res["per_trade"]["SWING|ANY & cell 2"]
    T1 = bool(p1["delta_bp"] > 0 and p1["t"] >= 2)
    T2 = bool(res["null"]["SWING"]["passes"])
    dd = res["deltas"]["SWING"]
    T3 = bool(dd["net_delta"] > 0 and dd["t"] >= 2 and res["control"]["passes"])
    res["bar"] = dict(T1=T1, T2=T2, T3=T3, clears=bool(T1 and T2 and T3))
    print("\n5. THE BAR -- SWING on ANY & cell 2")
    print(f"    T1 paired delta > 0 by 2 SE           : {T1}   ({p1['delta_bp']:+.2f} ± {p1['se_bp']:.2f}, {p1['t']:+.1f} SE)")
    print(f"    T2 beats the distance-permutation p95 : {T2}   (margin {res['null']['SWING']['margin_se']:+.1f} SE{', UNRESOLVED' if res['null']['SWING']['unresolved'] else ''})")
    print(f"    T3 book net delta > 0 by 2 SE and > ctrl  : {T3}   (delta {dd['net_delta']:+.3f} ± {dd['se']:.3f}; ctrl margin {res['control']['margin_se']:+.1f} SE)")
    print(f"    SWING {'CLEARS' if res['bar']['clears'] else 'FAILS'} the bar")
    # predictions, in the runner's quantities
    pb = res["per_trade"]["BREACH|ANY & cell 2"]; po = res["per_trade"]["OPP|ANY & cell 2"]
    print("\n6. PREDICTIONS")
    print(f"    X-a SWING delta 0..+4, inside 2 SE      : {p1['delta_bp']:+.2f}, {p1['t']:+.1f} SE")
    print(f"    X-b SWING fires 8-16%                   : {100*p1['early']:.1f}%")
    print(f"    X-c give-back after the swing -5..+5    : forfeit {p1.get('forfeit_bp', float('nan')):+.2f}")
    print(f"    X-d BREACH -5..-12, fires 25-35%        : {pb['delta_bp']:+.2f}, {100*pb['early']:.1f}%")
    print(f"    X-e OPP inside 2 SE, fires 25-35%       : {po['delta_bp']:+.2f} ({po['t']:+.1f} SE), {100*po['early']:.1f}%")
    print(f"    X-f SWING inside 2 SE of its null p95   : margin {res['null']['SWING']['margin_se']:+.1f} SE")
    print(f"    X-g book gross delta 0..+0.5, net inside 2 SE, above ctrl median below p95 : gross delta {dd['gross_delta']:+.3f}, net delta {dd['t']:+.1f} SE, "
          f"vs ctrl p50 {obs - res['control']['p50']:+.3f}, vs p95 {edge:+.3f}")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT}   total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.run:
        run(a.workers)

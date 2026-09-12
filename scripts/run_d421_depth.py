"""D421 -- the three depth conditions, both lenses. Bar committed in 73a1a9c BEFORE this ran.

    uv run python scripts/run_d421_depth.py --run [--workers 8]

THE FLAGS come from scripts/d421_depth_flags.py, committed WITH the pre-registration; the shares
it printed there are asserted here before any outcome is read. DEEP-2 (breach above) is primary.

PER TRADE   T1  mean r_base(DEEP-2) - mean r_base(not) > 0 by 2 SE; distribution, DEEP-1 beside
            it, DEEP-3's rungs and their monotonicity, cell 2, and a per-year table with a
            2010-2017 / 2018-2026 split.
THE BOOK    D419's simulator, FIXED exit, three seeds, with DEEP-2 as REFILL PRIORITY and as a
            REQUIREMENT. Priority off must reproduce D419's FIXED book bit-identically.
            T2  DEEP2-PRIORITY net > FIXED net by 2 SE (monthly block bootstrap)
            T3  DEEP2-PRIORITY net > p95 of a RANDOM-PRIORITY control -- the same COUNT promoted
                at random, 50 draws, D373 margin
The cell-2 books (10 slots) are the secondary. The declared candidate condition (record 5a) is
evaluated and printed, and it is not a gate.
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
_s = importlib.util.spec_from_file_location("d421f", REPO / "scripts" / "d421_depth_flags.py")
FL = importlib.util.module_from_spec(_s)
sys.modules["d421f"] = FL
_s.loader.exec_module(FL)

OUT = REPO / "data" / "d421_depth.json"
FLAGS = REPO / "temp" / "d421_flags.npz"
HOLD = 5
N50, N10, SEEDS = 50, 10, (419, 4190, 41900)
N_DRAW = 50
STAGE0 = dict(d1=(0.518, 0.720), d2=(0.388, 0.553))     # the record's section 2a, asserted


def load_all():
    """Main process: D419 inputs + flags, cached so workers need neither the zone builder nor
    the flag walk."""
    I, P, G = FL.load()
    B = G.B
    if FLAGS.exists():
        z = np.load(FLAGS)
        d1, d2, d3 = z["d1"], z["d2"], z["d3"]
    else:
        d1, d2, d3 = FL.flags(I, P)
        np.savez_compressed(FLAGS, d1=d1, d2=d2, d3=d3, a=I["a"], lo=I["lo"], hi=I["hi"])
    return I, P, B, d1, d2, d3


def simulate(I, n_slots, seed, prio=None, pool_mask=None):
    """D420's simulator (FIXED exit) with a refill PRIORITY: prio first, then cell 2, then random.
    prio=None is D419's ordering exactly."""
    t, side, E, cost = I["t"], I["side"], I["E"], I["cost"]
    CL, c2 = I["CL"], I["c2"]
    OP, HI, LO = I["OP"], I["HI"], I["LO"]
    T = int(I["T"][0]); N = len(t)
    rng = np.random.default_rng(seed)
    keys = (rng.random(N), ~c2) if prio is None else (rng.random(N), ~c2, ~prio)
    order = np.lexsort(keys)
    by_day = {}
    for k in order:
        if pool_mask is None or pool_mask[k]:
            by_day.setdefault(int(t[k]), []).append(int(k))
    lgE = np.log(E); lgCL = np.log(CL)
    held = {}; held_names = set()
    gross = np.zeros(T); costs = np.zeros(T); occ = np.zeros(T, np.int32); ent = np.zeros(T, np.int32)
    trades = []
    d0 = int(t.min()) + 1
    for d in range(d0, T):
        for k in list(held):
            st = held[k]; ag = st[0]
            o, h, l, c = OP[k, ag], HI[k, ag], LO[k, ag], CL[k, ag]
            nm = int(I["i"][k])
            if not (np.isfinite(o) and np.isfinite(h) and np.isfinite(l) and np.isfinite(c)):
                held.pop(k); held_names.discard(nm); trades.append((k, st[1], ag, False, d, np.nan)); continue
            s = float(side[k]); prev = lgE[k] if ag == 0 else lgCL[k, ag - 1]
            mark = s * (lgCL[k, ag] - prev); gross[d] += mark; occ[d] += 1
            st[0] += 1; st[1] += mark
            if st[0] >= HOLD:
                held.pop(k); held_names.discard(nm); trades.append((k, st[1], st[0], False, d, c))
        free = n_slots - len(held)
        if free > 0:
            for k in by_day.get(d, []):
                if free == 0:
                    break
                nm = int(I["i"][k])
                if nm in held_names or k in held or not np.isfinite(E[k]) or E[k] <= 0:
                    continue
                held[k] = [0, 0.0]; held_names.add(nm); costs[d] += cost[k]; ent[d] += 1; free -= 1
    resid = sum(st[1] for st in held.values())
    return dict(gross=gross, costs=costs, occ=occ, ent=ent, trades=trades, resid=resid, d0=d0,
                frees=np.zeros(T, np.int32), refilled=np.zeros(T, np.int32), early_frees=np.zeros(T, np.int32), swaps=[])


def stat(x, label):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if x.size < 2:
        return dict(label=label, n=int(x.size))
    lo, hi = np.quantile(x, [.01, .99])
    return dict(label=label, n=int(x.size), mean=float(1e4 * x.mean()), median=float(1e4 * np.median(x)),
                se=float(1e4 * x.std(ddof=1) / np.sqrt(x.size)), win=float(100 * (x > 0).mean()),
                trim=float(1e4 * x[(x >= lo) & (x <= hi)].mean()))


def diff(a, b, label):
    a, b = np.asarray(a, float), np.asarray(b, float); a, b = a[np.isfinite(a)], b[np.isfinite(b)]
    d = a.mean() - b.mean(); se = float(np.hypot(a.std(ddof=1) / np.sqrt(a.size), b.std(ddof=1) / np.sqrt(max(b.size, 2))))
    return dict(label=label, n_a=int(a.size), n_b=int(b.size), diff_bp=float(1e4 * d), se_bp=float(1e4 * se), t=float(d / se) if se > 0 else float("nan"))


def _ctrl_worker(args):
    n_slots, pool_is_c2, count, draws = args
    _s2 = importlib.util.spec_from_file_location("d419w", REPO / "scripts" / "run_d419_book.py")
    Bw = importlib.util.module_from_spec(_s2); sys.modules["d419w"] = Bw; _s2.loader.exec_module(Bw)
    I = dict(Bw.build_inputs()); z = np.load(FLAGS); I["a"] = z["a"]
    c2 = I["c2"]; N = len(I["t"])
    pool = c2 if pool_is_c2 else None
    base = np.flatnonzero(c2) if pool_is_c2 else np.arange(N)
    out = []
    for dr in draws:
        rng = np.random.default_rng(200000 + dr)
        prio = np.zeros(N, bool); prio[rng.choice(base, size=count, replace=False)] = True
        R = simulate(I, n_slots, SEEDS[0], prio=prio, pool_mask=pool)
        S = Bw.score(I, R, n_slots); assert S["recon_rel"] < 1e-9
        out.append((dr, S["net_bp"], S["gross_bp"], S["utilisation"]))
    return n_slots, pool_is_c2, out


def run(workers):
    t0 = time.time()
    print("D421  the three depth conditions, both lenses")
    print("      the bar was committed in 73a1a9c BEFORE this ran\n")
    I, P, B, d1, d2, d3 = load_all()
    N = len(I["t"]); c2 = I["c2"]; rb = I["r_base"]; dates = I["dates"]; T = int(I["T"][0])
    yrs = np.array([int(str(x)[:4]) for x in dates[I["t"]]])
    for lab, m, ref in (("DEEP-1", d1, STAGE0["d1"]), ("DEEP-2", d2, STAGE0["d2"])):
        assert abs(m.mean() - ref[0]) < 0.0015 and abs(m[c2].mean() - ref[1]) < 0.0015, \
            f"[STAGE0] {lab} share {m.mean():.3f}/{m[c2].mean():.3f} != record {ref}"
    print(f"  [STAGE0] flag shares reproduce the record: DEEP-1 {100*d1.mean():.1f}/{100*d1[c2].mean():.1f}%  "
          f"DEEP-2 {100*d2.mean():.1f}/{100*d2[c2].mean():.1f}%")
    R0 = simulate(I, N50, SEEDS[0]); S0 = B.score(I, R0, N50)
    R19 = B.simulate(I, "FIXED", N50, SEEDS[0])
    assert [x[:3] for x in R0["trades"]] == [x[:3] for x in R19["trades"]] and np.array_equal(R0["gross"], R19["gross"]), \
        "[P2] priority off is not D419's FIXED book"
    print(f"  P2  priority off == D419's FIXED book, bit-identical ({S0['trades']:,} trades, net {S0['net_bp']:+.3f})")

    res = dict(per_trade={}, per_year={}, books={}, bar={}, secondary={}, controls={})

    # ================= PER TRADE =================
    print(f"\n  --- PER TRADE (fixed exit return, bp) ---")
    for pop, pm in (("pooled", np.ones(N, bool)), ("cell2", c2)):
        blk = {}
        for lab, m in (("DEEP-2", d2), ("DEEP-1", d1)):
            blk[lab] = dict(inside=stat(rb[pm & m], f"{lab} yes"), outside=stat(rb[pm & ~m], f"{lab} no"),
                            gap=diff(rb[pm & m], rb[pm & ~m], f"{lab} yes - no"))
            q = blk[lab]
            print(f"  {pop:6s} {lab:7s} yes {q['inside']['mean']:+7.2f} (med {q['inside']['median']:+6.2f}, trim {q['inside']['trim']:+6.2f}, n {q['inside']['n']:6,})   "
                  f"no {q['outside']['mean']:+7.2f} (med {q['outside']['median']:+6.2f})   gap {q['gap']['diff_bp']:+7.2f} +-{q['gap']['se_bp']:.2f} ({q['gap']['t']:+5.1f} SE)")
        rungs = []
        for b, lab in ((0, "stack 1"), (1, "stack 2"), (2, "stack 3+")):
            m = pm & ((d3 == b) if b < 2 else (d3 >= 2)); s = stat(rb[m], lab); rungs.append(s)
            print(f"  {pop:6s} DEEP-3 {lab:9s} {s['mean']:+7.2f} (med {s['median']:+6.2f}, trim {s['trim']:+6.2f}, n {s['n']:6,})")
        blk["DEEP-3"] = dict(rungs=rungs, monotone=bool(rungs[0]["mean"] <= rungs[1]["mean"] <= rungs[2]["mean"]))
        print(f"  {pop:6s} DEEP-3 monotone 1 <= 2 <= 3+: {blk['DEEP-3']['monotone']}")
        # DEEP-2 within / outside DEEP-1: what the structural definition adds
        blk["DEEP-2|DEEP-1"] = dict(both=stat(rb[pm & d1 & d2], "d1 and d2"), d1_only=stat(rb[pm & d1 & ~d2], "d1 not d2"),
                                    d2_only=stat(rb[pm & ~d1 & d2], "d2 not d1"), neither=stat(rb[pm & ~d1 & ~d2], "neither"))
        q = blk["DEEP-2|DEEP-1"]
        print(f"  {pop:6s} both {q['both']['mean']:+7.2f} (n {q['both']['n']:,})   DEEP-1 only {q['d1_only']['mean']:+7.2f} (n {q['d1_only']['n']:,})   "
              f"DEEP-2 only {q['d2_only']['mean']:+7.2f} (n {q['d2_only']['n']:,})   neither {q['neither']['mean']:+7.2f} (n {q['neither']['n']:,})")
        res["per_trade"][pop] = blk

    print(f"\n  --- PER YEAR: DEEP-2 gap (yes - no), pooled ---")
    py = {}
    for y in sorted(set(yrs.tolist())):
        m = yrs == y; g = diff(rb[m & d2], rb[m & ~d2], str(y)); py[str(y)] = g
    print("  " + "  ".join(f"{y}:{q['diff_bp']:+.0f}" for y, q in py.items()))
    pos_years = sum(1 for q in py.values() if q["diff_bp"] > 0)
    h1, h2 = yrs <= 2017, yrs >= 2018
    halves = dict(first=diff(rb[h1 & d2], rb[h1 & ~d2], "2010-2017"), second=diff(rb[h2 & d2], rb[h2 & ~d2], "2018-2026"),
                  first_d1=diff(rb[h1 & d1], rb[h1 & ~d1], "d1 2010-2017"), second_d1=diff(rb[h2 & d1], rb[h2 & ~d1], "d1 2018-2026"),
                  base_first=float(1e4 * rb[h1].mean()), base_second=float(1e4 * rb[h2].mean()))
    print(f"  positive years {pos_years} of {len(py)}   |   DEEP-2 gap 2010-2017 {halves['first']['diff_bp']:+.2f} ({halves['first']['t']:+.1f} SE)   "
          f"2018-2026 {halves['second']['diff_bp']:+.2f} ({halves['second']['t']:+.1f} SE)   |   base edge halves {halves['base_first']:+.2f} / {halves['base_second']:+.2f}")
    print(f"  DEEP-1 gap by half: {halves['first_d1']['diff_bp']:+.2f} / {halves['second_d1']['diff_bp']:+.2f}")
    res["per_year"] = dict(years=py, positive_years=pos_years, halves=halves)

    # ================= THE BOOK =================
    print(f"\n  --- THE BOOK ---")
    t1 = time.time()
    specs = [("FIXED", None, None), ("DEEP2-PRIORITY", d2, None), ("DEEP2-REQUIRED", None, d2),
             ("DEEP1-PRIORITY", d1, None), ("DEEP3-PRIORITY", d3 >= 2, None)]
    for lab, n_slots, base_pool in (("N50", N50, None), ("C2N10", N10, c2)):
        for tag, prio, req in specs:
            if lab == "C2N10" and tag in ("DEEP1-PRIORITY", "DEEP3-PRIORITY"):
                continue
            pool = base_pool if req is None else (req if base_pool is None else (req & base_pool))
            for seed in SEEDS:
                R = simulate(I, n_slots, seed, prio=prio, pool_mask=pool)
                S = B.score(I, R, n_slots); assert S["recon_rel"] < 1e-9, "[RECON]"
                res["books"][f"{tag}_{lab}_s{seed}"] = S
    print(f"  {len(res['books'])} books in {time.time()-t1:.0f}s   [RECON] all")
    for lab in ("N50", "C2N10"):
        for tag, _, _ in specs:
            k = f"{tag}_{lab}_s{SEEDS[0]}"
            if k not in res["books"]:
                continue
            S = res["books"][k]
            print(f"  {lab:6s} {tag:15s} gross {S['gross_bp']:+7.3f}  net {S['net_bp']:+7.3f}  cost {S['cost_bp']:.3f}   "
                  f"trades {S['trades']:6,}  turn {100*S['turnover']:.2f}%/d  util {100*S['utilisation']:.1f}%   trade {S['trade_mean_bp']:+.2f}")

    def t2_block(lab, tags):
        out = {}
        for tag in tags:
            ds, ses, dg = [], [], []
            for s in SEEDS:
                Bk = res["books"][f"{tag}_{lab}_s{s}"]; F = res["books"][f"FIXED_{lab}_s{s}"]
                se, mean = B.block_boot(Bk["net_series"] - F["net_series"], dates[T - F["days"]:])
                ds.append(1e4 * mean); ses.append(1e4 * se); dg.append(1e4 * (Bk["gross_series"] - F["gross_series"]).mean())
            out[tag] = dict(net_delta_bp=float(np.mean(ds)), se_bp=float(np.mean(ses)), t=float(np.mean(ds) / np.mean(ses)),
                            gross_delta_bp=float(np.mean(dg)), seed_spread=float(np.ptp(ds)), pass2=bool(np.mean(ds) / np.mean(ses) > 2.0),
                            net_abs=float(np.mean([1e4 * res["books"][f"{tag}_{lab}_s{s}"]["net_series"].mean() for s in SEEDS])))
        return out
    res["bar"]["T2"] = t2_block("N50", ["DEEP2-PRIORITY", "DEEP2-REQUIRED", "DEEP1-PRIORITY", "DEEP3-PRIORITY"])
    res["secondary"]["T2"] = t2_block("C2N10", ["DEEP2-PRIORITY", "DEEP2-REQUIRED"])
    print(f"\n  --- T2: book NET minus FIXED NET, bp/bar, mean over seeds, monthly block-bootstrap SE ---")
    for lab, blk in (("N50", res["bar"]["T2"]), ("C2N10", res["secondary"]["T2"])):
        for tag, q in blk.items():
            print(f"  {lab:6s} {tag:15s} gross {q['gross_delta_bp']:+7.3f}   NET {q['net_delta_bp']:+7.3f} +-{q['se_bp']:.3f} ({q['t']:+5.1f} SE)   "
                  f"seed spread {q['seed_spread']:.3f}   book net {q['net_abs']:+.3f}   T2 {q['pass2']}")

    # ================= T3: random-priority controls =================
    cnt_p, cnt_c = int(d2.sum()), int(d2[c2].sum())
    print(f"\n  controls: {N_DRAW} draws x 2 books, {workers} workers  (promote {cnt_p:,} at random pooled, {cnt_c:,} within cell 2)")
    jobs = [(N50, False, cnt_p, list(range(w, N_DRAW, workers))) for w in range(workers)] + \
           [(N10, True, cnt_c, list(range(w, N_DRAW, workers))) for w in range(workers)]
    rng = np.random.default_rng(200000); pr0 = np.zeros(N, bool); pr0[rng.choice(np.arange(N), size=cnt_p, replace=False)] = True
    S_in = B.score(I, simulate(I, N50, SEEDS[0], prio=pr0), N50)
    with mp.Pool(workers) as pool:
        results = pool.map(_ctrl_worker, jobs)
    got = [o for n, p, oo in results if n == N50 and not p for o in oo if o[0] == 0][0]
    assert abs(got[1] - S_in["net_bp"]) < 1e-12, "[CHUNK]"
    print(f"  [CHUNK] worker draw 0 == in-process draw 0")
    for lab, n_slots, pool_is_c2 in (("N50", N50, False), ("C2N10", N10, True)):
        out = sorted(o for n, p, oo in results if n == n_slots and p == pool_is_c2 for o in oo)
        net = np.array([o[1] for o in out]); ut = np.array([o[3] for o in out])
        obs = res["books"][f"DEEP2-PRIORITY_{lab}_s{SEEDS[0]}"]
        p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs["net_bp"] - p95
        res["controls"][lab] = dict(n=int(net.size), p5=float(np.quantile(net, .05)), p50=float(np.median(net)), p95=p95, se=se,
                                    observed=obs["net_bp"], ctrl_util=float(ut.mean()), obs_util=obs["utilisation"],
                                    beats=bool(edge > 0), margin_se=float(edge / se) if se > 0 else float("inf"),
                                    unresolved=bool(abs(edge) < 2 * se), pass3=bool(edge > 0 and abs(edge) >= 2 * se))
        q = res["controls"][lab]
        print(f"  T3 {lab:6s} DEEP2-PRIORITY net {q['observed']:+7.3f}   random-priority p5 {q['p5']:+7.3f}  p50 {q['p50']:+7.3f}  p95 {q['p95']:+7.3f} (+-{se:.3f})   "
              f"margin {q['margin_se']:+5.1f} SE   T3 {q['pass3']}{'  UNRESOLVED' if q['unresolved'] else ''}")

    # ================= P4 and the bar =================
    z = np.load(FLAGS)
    nm = int(np.bincount(I["i"][d2]).argmax()); ks = np.flatnonzero(I["i"] == nm); ks = ks[np.argsort(I["t"][ks])][:12]
    print(f"\n  P4  {I['symbols'][nm]}: first 12 zones in touch order")
    for k in ks:
        print(f"      armed {dates[z['a'][k]]} touched {dates[I['t'][k]]} side {I['side'][k]:+d} zone [{z['lo'][k]:.2f},{z['hi'][k]:.2f}]  "
              f"D1 {int(d1[k])} D2 {int(d2[k])} D3 {int(d3[k])}   r_base {1e4*rb[k]:+6.0f} bp")

    T1 = bool(res["per_trade"]["pooled"]["DEEP-2"]["gap"]["t"] > 2.0)
    T2 = res["bar"]["T2"]["DEEP2-PRIORITY"]["pass2"]; T3 = res["controls"]["N50"]["pass3"]
    s1 = bool(res["per_trade"]["cell2"]["DEEP-2"]["gap"]["t"] > 2.0); s2 = res["secondary"]["T2"]["DEEP2-PRIORITY"]["pass2"]; s3 = res["controls"]["C2N10"]["pass3"]
    req_c2 = res["secondary"]["T2"]["DEEP2-REQUIRED"]
    cand = bool(req_c2["net_abs"] > 0) and bool(halves["second"]["diff_bp"] > 0)
    g = res["per_trade"]["pooled"]["DEEP-2"]["gap"]
    print(f"\n  --- THE BAR (committed 73a1a9c) ---")
    print(f"    T1 DEEP-2 beats not-DEEP-2, 2 SE                : {T1}   ({g['diff_bp']:+.2f} bp, {g['t']:+.1f} SE)")
    print(f"    T2 DEEP2-PRIORITY book net beats FIXED, 2 SE     : {T2}   ({res['bar']['T2']['DEEP2-PRIORITY']['net_delta_bp']:+.3f} bp/bar, {res['bar']['T2']['DEEP2-PRIORITY']['t']:+.1f} SE)")
    print(f"    T3 beats random-priority control                 : {T3}   (margin {res['controls']['N50']['margin_se']:+.1f} SE)")
    print(f"    secondary cell 2 (cannot clear)                  : T1 {s1}  T2 {s2}  T3 {s3}")
    print(f"    declared candidate condition (record 5a):        cell-2 REQUIRED book net {req_c2['net_abs']:+.3f}  "
          f"second-half DEEP-2 gap {halves['second']['diff_bp']:+.2f}  ->  {'MET' if cand else 'NOT MET'} (control on the REQUIRED book not run; see record)")
    print(f"\n  VERDICT: T1 {'CLEARS' if T1 else 'FAILS'}   T2 {'CLEARS' if T2 else 'FAILS'}   T3 {'CLEARS' if T3 else 'FAILS'}")
    for k_, S in res["books"].items():
        S.pop("gross_series"); S.pop("net_series"); S.pop("run_dist")
    res["bar"].update(dict(T1=T1, T2_flag=T2, T3=T3)); res["secondary"].update(dict(T1=s1, T2_flag=s2, T3=s3)); res["candidate"] = cand
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"  wrote {OUT.relative_to(REPO)}  in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if not a.run:
        ap.error("pass --run")
    run(a.workers)

"""D422 -- the second zone: same-side, the flip claim, the initial touch. Bar committed in 1c3044b
BEFORE this ran.

    uv run python scripts/run_d422_second_zone.py --run [--workers 8]

THE CONDITIONS come from scripts/d422_stack_flags.py, committed WITH the pre-registration; its
shares are asserted here before any outcome is read. STACK2-SAME is primary; FLIP is the claim.

PER TRADE   T1  SECOND HALF (2018-2026), pooled: STACK2-SAME premium over not-SAME > 0 by 2 SE
            T2  pooled: the premium beats the p95 of a WITHIN-DAY LABEL PERMUTATION (200 draws)
THE BOOK    T3  the cell-2 SAME-REQUIRED 10-slot book is net-positive over seeds AND beats the p95
                of a matched-count random-requirement control (50 draws)
CANDIDATE   T1 and T2 and T3 -- the first condition in this line that, met, satisfies the
            principal's rule for reading the holdout. FLIP's declared reading is printed.
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
_s = importlib.util.spec_from_file_location("d422f", REPO / "scripts" / "d422_stack_flags.py")
FL = importlib.util.module_from_spec(_s); sys.modules["d422f"] = FL; _s.loader.exec_module(FL)
_s2 = importlib.util.spec_from_file_location("d421r", REPO / "scripts" / "run_d421_depth.py")
R21 = importlib.util.module_from_spec(_s2); sys.modules["d421r"] = R21; _s2.loader.exec_module(R21)

OUT = REPO / "data" / "d422_second_zone.json"
FLAGS = REPO / "temp" / "d422_flags.npz"
HOLD = 5
N50, N10, SEEDS = 50, 10, (419, 4190, 41900)
N_PERM, N_DRAW = 200, 50
STAGE0 = dict(s1=0.325, s2same=(0.187, 0.245), s2any=(0.352, 0.362), s3p=0.324, flip=(0.228, 0.201))
ARMS = ("s2same", "s2any", "flip")
LABEL = dict(s2same="STACK2-SAME", s2any="STACK2-ANY", flip="FLIP", s1="STACK1", s3p="STACK3+")


def load_all():
    I, P, G = FL.load()
    B = G.B
    if FLAGS.exists():
        z = np.load(FLAGS); fl = {k: z[k] for k in z.files}
    else:
        fl = FL.flags(I, P)
        np.savez_compressed(FLAGS, **fl)
    return I, P, B, fl


stat, diff, simulate = R21.stat, R21.diff, R21.simulate


def within_day_perm(labels, t, N, rng):
    """Shuffle a boolean label among the events of each day; the day's count is preserved."""
    base = np.lexsort((np.arange(N), t))
    perm = np.lexsort((rng.random(N), t))
    out = np.zeros(N, bool); out[perm] = labels[base]
    return out


def perm_null(labels, t, r, mask, n, seed):
    rng = np.random.default_rng(seed)
    obs = r[mask & labels].mean() - r[mask & ~labels].mean()
    draws = np.empty(n)
    for k in range(n):
        lp = within_day_perm(labels, t, len(t), rng)
        draws[k] = r[mask & lp].mean() - r[mask & ~lp].mean()
    p95 = float(np.quantile(draws, .95)); se = float(draws.std(ddof=1) / np.sqrt(n)); edge = obs - p95
    return dict(observed_bp=float(1e4 * obs), p5=float(1e4 * np.quantile(draws, .05)), p50=float(1e4 * np.median(draws)),
                p95=float(1e4 * p95), se=float(1e4 * se), margin_se=float(edge / se) if se > 0 else float("inf"),
                beats=bool(edge > 0), unresolved=bool(abs(edge) < 2 * se), passes=bool(edge > 0 and abs(edge) >= 2 * se))


def concentration(r, i, yr, m):
    x = r[m]; nm = i[m]; y = yr[m]
    tot = x.sum()
    if tot <= 0 or x.size < 100:
        return dict(n=int(x.size), total_positive=bool(tot > 0))
    by = {}
    for a, b in zip(nm, x):
        by[int(a)] = by.get(int(a), 0.0) + float(b)
    v = np.sort(np.array(list(by.values())))[::-1]; half = int(np.searchsorted(np.cumsum(v), 0.5 * tot) + 1)
    byy = {}
    for a, b in zip(y, x):
        byy[int(a)] = byy.get(int(a), 0.0) + float(b)
    top_year = max(byy, key=byy.get)
    return dict(n=int(x.size), names=len(by), names_to_half=half, top1_name_share=float(v[0] / tot),
                top_year=int(top_year), top_year_share=float(byy[top_year] / tot))


def _ctrl_worker(args):
    n_slots, count, draws = args
    _b = importlib.util.spec_from_file_location("d419w", REPO / "scripts" / "run_d419_book.py")
    Bw = importlib.util.module_from_spec(_b); sys.modules["d419w"] = Bw; _b.loader.exec_module(Bw)
    I = dict(Bw.build_inputs()); c2 = I["c2"]; base = np.flatnonzero(c2)
    out = []
    for dr in draws:
        rng = np.random.default_rng(300000 + dr)
        pool = np.zeros(len(I["t"]), bool); pool[rng.choice(base, size=count, replace=False)] = True
        R = simulate(I, n_slots, SEEDS[0], pool_mask=pool)
        S = Bw.score(I, R, n_slots); assert S["recon_rel"] < 1e-9
        out.append((dr, S["net_bp"], S["gross_bp"], S["utilisation"]))
    return out


def run(workers):
    t0 = time.time()
    print("D422  the second zone -- same-side, the flip claim, the initial touch")
    print("      the bar was committed in 1c3044b BEFORE this ran\n")
    I, P, B, fl = load_all()
    N = len(I["t"]); c2 = I["c2"]; rb = I["r_base"]; t = I["t"]; dates = I["dates"]; T = int(I["T"][0])
    yr = np.array([int(str(x)[:4]) for x in dates[t]]); h2 = yr >= 2018
    for k, ref in STAGE0.items():
        m = fl[k]; ref = ref if isinstance(ref, tuple) else (ref, None)
        assert abs(m.mean() - ref[0]) < 0.0015, f"[STAGE0] {k} {m.mean():.3f} != {ref[0]}"
        if ref[1] is not None:
            assert abs(m[c2].mean() - ref[1]) < 0.0015, f"[STAGE0] {k} cell2 {m[c2].mean():.3f} != {ref[1]}"
    print(f"  [STAGE0] every flag share reproduces the record's section 2a")

    res = dict(per_trade={}, hump={}, per_year={}, perm={}, conc={}, books={}, deltas={}, control={}, bar={})

    # ================= PER TRADE =================
    print(f"\n  --- PER TRADE: premium of each arm over its complement (fixed-exit return, bp) ---")
    for arm in ARMS:
        m = fl[arm]; blk = {}
        for lab, pm in (("pooled", np.ones(N, bool)), ("2018+", h2), ("cell2", c2), ("cell2 2018+", c2 & h2)):
            blk[lab] = dict(yes=stat(rb[pm & m], "yes"), no=stat(rb[pm & ~m], "no"), gap=diff(rb[pm & m], rb[pm & ~m], lab))
            q = blk[lab]
            print(f"  {LABEL[arm]:12s} {lab:12s} yes {q['yes']['mean']:+7.2f} (med {q['yes']['median']:+6.2f}, trim {q['yes']['trim']:+6.2f}, n {q['yes']['n']:6,})   "
                  f"no {q['no']['mean']:+7.2f}   gap {q['gap']['diff_bp']:+7.2f} +-{q['gap']['se_bp']:.2f} ({q['gap']['t']:+5.1f} SE)")
        res["per_trade"][arm] = blk
    print(f"\n  --- the hump under distinct-day counting ---")
    for lab, pm in (("pooled", np.ones(N, bool)), ("cell2", c2), ("cell2 2018+", c2 & h2)):
        rungs = {k: stat(rb[pm & fl[k]], k) for k in ("s1", "s2same", "s2any", "s3p")}
        res["hump"][lab] = rungs
        print(f"  {lab:12s} " + "   ".join(f"{LABEL[k]} {rungs[k]['mean']:+7.2f} (n {rungs[k]['n']:6,})" for k in ("s1", "s2same", "s2any", "s3p")))
    fa = fl["flip"] & fl["s2any"]; na = ~fl["flip"] & fl["s2any"]
    res["flip_in_any"] = dict(flip=stat(rb[fa], "flip&any"), noflip=stat(rb[na], "any not flip"), gap=diff(rb[fa], rb[na], "flip adds to any"))
    q = res["flip_in_any"]
    print(f"  FLIP within STACK2-ANY: flip {q['flip']['mean']:+7.2f} (n {q['flip']['n']:,})   not flip {q['noflip']['mean']:+7.2f} (n {q['noflip']['n']:,})   "
          f"gap {q['gap']['diff_bp']:+7.2f} ({q['gap']['t']:+5.1f} SE)")

    print(f"\n  --- STACK2-SAME premium by year, pooled ---")
    py = {}
    for y in sorted(set(yr.tolist())):
        mm = yr == y; py[str(y)] = diff(rb[mm & fl["s2same"]], rb[mm & ~fl["s2same"]], str(y))
    print("  " + "  ".join(f"{y}:{q['diff_bp']:+.0f}" for y, q in py.items()) + f"   positive {sum(q['diff_bp'] > 0 for q in py.values())} of {len(py)}")
    res["per_year"] = py
    for arm in ARMS:
        res["conc"][arm] = concentration(rb, I["i"], yr, fl[arm])
        q = res["conc"][arm]
        if "names_to_half" in q:
            print(f"  concentration {LABEL[arm]:12s} names to half the P&L {q['names_to_half']:,} of {q['names']:,}   top name {100*q['top1_name_share']:.1f}%   "
                  f"top year {q['top_year']} {100*q['top_year_share']:.1f}%")

    print(f"\n  --- T2: within-day label permutation, {N_PERM} draws ---")
    for arm in ARMS:
        for lab, pm in (("pooled", np.ones(N, bool)), ("2018+", h2)):
            q = perm_null(fl[arm], t, rb, pm, N_PERM, seed=422)
            res["perm"][f"{arm}_{lab}"] = q
            print(f"  {LABEL[arm]:12s} {lab:8s} observed {q['observed_bp']:+7.2f}   null p5 {q['p5']:+6.2f}  p50 {q['p50']:+6.2f}  p95 {q['p95']:+6.2f} (+-{q['se']:.2f})   "
                  f"margin {q['margin_se']:+6.1f} SE   {'PASS' if q['passes'] else 'fail'}{'  UNRESOLVED' if q['unresolved'] else ''}")

    # ================= THE BOOK =================
    print(f"\n  --- THE BOOK ---")
    R0 = simulate(I, N50, SEEDS[0]); R19 = B.simulate(I, "FIXED", N50, SEEDS[0])
    assert [x[:3] for x in R0["trades"]] == [x[:3] for x in R19["trades"]], "[P2] not D419's FIXED book"
    print(f"  P2  D419's FIXED book reproduced bit-identically")
    t1 = time.time()
    for lab, n_slots, base in (("C2N10", N10, c2), ("N50", N50, np.ones(N, bool))):
        for tag, m in (("FIXED", None), ("SAME-REQ", fl["s2same"]), ("ANY-REQ", fl["s2any"]), ("FLIP-REQ", fl["flip"])):
            pool = base if m is None else (base & m)
            if lab == "N50" and m is None:
                pool = None
            for seed in SEEDS:
                R = simulate(I, n_slots, seed, pool_mask=pool); S = B.score(I, R, n_slots)
                assert S["recon_rel"] < 1e-9, "[RECON]"
                res["books"][f"{tag}_{lab}_s{seed}"] = S
    print(f"  {len(res['books'])} books in {time.time()-t1:.0f}s   [RECON] all")
    for lab in ("C2N10", "N50"):
        for tag in ("FIXED", "SAME-REQ", "ANY-REQ", "FLIP-REQ"):
            S = res["books"][f"{tag}_{lab}_s{SEEDS[0]}"]
            print(f"  {lab:6s} {tag:9s} gross {S['gross_bp']:+7.3f}  net {S['net_bp']:+7.3f}  cost {S['cost_bp']:.3f}   trades {S['trades']:6,}  "
                  f"turn {100*S['turnover']:.2f}%/d  util {100*S['utilisation']:.1f}%   trade {S['trade_mean_bp']:+.2f}")
    print(f"\n  --- net vs FIXED, mean over seeds, monthly block-bootstrap SE; and the book's own net ---")
    for lab in ("C2N10", "N50"):
        for tag in ("SAME-REQ", "ANY-REQ", "FLIP-REQ"):
            ds, ses, nets = [], [], []
            for s in SEEDS:
                Bk = res["books"][f"{tag}_{lab}_s{s}"]; F = res["books"][f"FIXED_{lab}_s{s}"]
                se, mean = B.block_boot(Bk["net_series"] - F["net_series"], dates[T - F["days"]:])
                ds.append(1e4 * mean); ses.append(1e4 * se); nets.append(1e4 * Bk["net_series"].mean())
            res["deltas"][f"{tag}_{lab}"] = dict(delta_bp=float(np.mean(ds)), se_bp=float(np.mean(ses)), t=float(np.mean(ds) / np.mean(ses)),
                                                 net_abs=float(np.mean(nets)), net_by_seed=[float(x) for x in nets], seed_spread=float(np.ptp(ds)))
            q = res["deltas"][f"{tag}_{lab}"]
            print(f"  {lab:6s} {tag:9s} delta {q['delta_bp']:+7.3f} +-{q['se_bp']:.3f} ({q['t']:+5.1f} SE)   book net {q['net_abs']:+7.3f}   by seed {[round(x, 3) for x in q['net_by_seed']]}")

    # ---- T3: matched-count random-requirement control on the cell-2 book
    count = int((c2 & fl["s2same"]).sum())
    print(f"\n  controls: {N_DRAW} random cell-2 pools of {count:,} events, {workers} workers")
    jobs = [(N10, count, list(range(w, N_DRAW, workers))) for w in range(workers)]
    rng = np.random.default_rng(300000); pl0 = np.zeros(N, bool); pl0[rng.choice(np.flatnonzero(c2), size=count, replace=False)] = True
    S_in = B.score(I, simulate(I, N10, SEEDS[0], pool_mask=pl0), N10)
    with mp.Pool(workers) as pool:
        results = pool.map(_ctrl_worker, jobs)
    out = sorted(o for oo in results for o in oo)
    assert abs(out[0][1] - S_in["net_bp"]) < 1e-12, "[CHUNK]"
    print(f"  [CHUNK] worker draw 0 == in-process draw 0")
    net = np.array([o[1] for o in out]); ut = np.array([o[3] for o in out])
    obs = res["deltas"]["SAME-REQ_C2N10"]["net_abs"]
    p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs - p95
    res["control"] = dict(count=count, n=int(net.size), p5=float(np.quantile(net, .05)), p50=float(np.median(net)), p95=p95, se=se,
                          observed_net=obs, ctrl_util=float(ut.mean()), beats=bool(edge > 0),
                          margin_se=float(edge / se) if se > 0 else float("inf"), unresolved=bool(abs(edge) < 2 * se),
                          passes=bool(edge > 0 and abs(edge) >= 2 * se))
    q = res["control"]
    print(f"  T3 control: SAME-REQ net {obs:+.3f} (mean over seeds)   random-pool p5 {q['p5']:+.3f}  p50 {q['p50']:+.3f}  p95 {q['p95']:+.3f} (+-{se:.3f})   "
          f"margin {q['margin_se']:+.1f} SE   util ctrl {100*q['ctrl_util']:.1f}%")

    # ---- P4
    nm = int(np.bincount(I["i"][fl["s2same"]]).argmax()); ks = np.flatnonzero(I["i"] == nm); ks = ks[np.argsort(t[ks])][:12]
    print(f"\n  P4  {I['symbols'][nm]}: first 12 zones in touch order")
    for k in ks:
        print(f"      touched {dates[t[k]]} side {I['side'][k]:+d} zone [{I['lo'][k]:.2f},{I['hi'][k]:.2f}]  same {fl['same'][k]} opp {fl['opp'][k]} "
              f"flip {int(fl['flip'][k])}  -> {'SAME' if fl['s2same'][k] else 'ANY' if fl['s2any'][k] else 'S1' if fl['s1'][k] else 'S3+'}   r_base {1e4*rb[k]:+6.0f} bp")

    # ================= THE BAR =================
    T1 = bool(res["per_trade"]["s2same"]["2018+"]["gap"]["t"] > 2.0)
    T2 = res["perm"]["s2same_pooled"]["passes"]
    T3 = bool(res["deltas"]["SAME-REQ_C2N10"]["net_abs"] > 0) and res["control"]["passes"]
    cand = T1 and T2 and T3
    fp = res["per_trade"]["flip"]["pooled"]["gap"]; fh = res["per_trade"]["flip"]["2018+"]["gap"]
    flip_read = ("DISMISSED on this construction: pooled premium inside 2 SE of zero" if abs(fp["t"]) < 2.0
                 else "earns its own pre-registration: pooled positive by 2 SE with a positive second half" if (fp["t"] > 2.0 and fh["diff_bp"] > 0)
                 else "positive pooled but not in the second half -- not dismissed, not earned" if fp["t"] > 2.0
                 else "NEGATIVE by more than 2 SE -- the claim has the wrong sign here")
    print(f"\n  --- THE BAR (committed 1c3044b), STACK2-SAME ---")
    g = res["per_trade"]["s2same"]["2018+"]["gap"]
    print(f"    T1 second-half premium > 0 by 2 SE          : {T1}   ({g['diff_bp']:+.2f} bp, {g['t']:+.1f} SE)")
    print(f"    T2 beats within-day permutation p95         : {T2}   (margin {res['perm']['s2same_pooled']['margin_se']:+.1f} SE)")
    print(f"    T3 cell-2 SAME-REQ book net > 0 and > ctrl  : {T3}   (net {res['deltas']['SAME-REQ_C2N10']['net_abs']:+.3f}, margin {res['control']['margin_se']:+.1f} SE)")
    print(f"    CANDIDATE (T1 and T2 and T3)                : {'MET' if cand else 'NOT MET'}")
    print(f"    FLIP, declared reading                      : {flip_read}   ({fp['diff_bp']:+.2f} bp, {fp['t']:+.1f} SE pooled; {fh['diff_bp']:+.2f} second half)")
    print(f"\n  VERDICT: T1 {'CLEARS' if T1 else 'FAILS'}   T2 {'CLEARS' if T2 else 'FAILS'}   T3 {'CLEARS' if T3 else 'FAILS'}   candidate {'MET' if cand else 'NOT MET'}")
    for k_, S in res["books"].items():
        S.pop("gross_series"); S.pop("net_series"); S.pop("run_dist")
    res["bar"] = dict(T1=T1, T2=T2, T3=T3, candidate=cand, flip_reading=flip_read)
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

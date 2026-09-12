"""D420 -- fire once per episode. Bar committed in 7cc52eb BEFORE this ran.

    uv run python scripts/run_d420_episode.py --run [--workers 8]

THE RULE (parameter-free primary): a name fires once per EPISODE. When a position on a name exits
at day e, every zone on that name alive at e -- armed at a <= e and not yet touched -- is consumed.
A zone armed after e starts a new episode. COOLDOWN(K), K in {5, 20}: the name is ineligible for K
days after any exit. Shape.

BOTH LENSES, on separate statistics:
  per trade   every event entered; per-name sequential walk classifies ENTERED vs RE-ENTRY;
              T1  mean r_first - mean r_re > 0 by 2 SE
  the book    D419's 50-slot book with the rule applied INSIDE the refill, because whether an
              earlier event was entered depends on capacity;
              T2  EPISODE net bp/bar > FIXED net by 2 SE (monthly block bootstrap, 3 seeds)
              T3  EPISODE net > p95 of a MATCHED-COUNT RANDOM EXCLUSION (50 draws, D373 margin)

THE BOOK IS D419's, NOT A SECOND ONE: with the rule off this simulator must reproduce D419's FIXED
book bit-identically -- same trade ledger, same daily series -- before any rule is switched on.
The arming days come from D413's runner and are asserted to align with D419's cached event table.
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
_s = importlib.util.spec_from_file_location("d419", REPO / "scripts" / "run_d419_book.py")
B = importlib.util.module_from_spec(_s)
sys.modules["d419"] = B
_s.loader.exec_module(B)                      # the [SPLIT] holdout guard comes with it
M, Z4, D = B.M, B.Z4, B.D

OUT = REPO / "data" / "d420_episode.json"
HOLD = B.HOLD
N_PRIMARY, N_CELL2, SEEDS = B.N_PRIMARY, B.N_CELL2, B.SEEDS
KS = (5, 20)
N_DRAW = 50


# ------------------------------------------------------------------ inputs, plus the arming day
def inputs():
    I = B.build_inputs()
    P = D.load_panel(verbose=False)
    atr = Z4.atr_of(P)
    A = Z4.run_arm(P, atr, "dep", M.THETA, M.LIFE, M.H, delta=M.DELTA)
    Z, g = A["Z"], A["good"]
    assert np.array_equal(A["tt"][g], I["t"]) and np.array_equal(Z["i"][g], I["i"]) \
        and np.array_equal(Z["side"][g], I["side"]), "[ALIGN] D413's event table does not match D419's cache"
    I = dict(I); I["a"] = Z["a"][g]
    assert np.all(I["a"] <= I["t"]), "[ALIGN] a zone armed after its own touch"
    return I


# ------------------------------------------------------------------ the per-trade lens
def classify(I, mode, K=None):
    """Per name, in touch order, every event entered (no capacity). Returns entered mask."""
    t, i, a = I["t"], I["i"], I["a"]
    order = np.lexsort((t, i))
    entered = np.zeros(len(t), bool)
    last_exit = {}
    for k in order:
        nm = int(i[k]); le = last_exit.get(nm, -10**9)
        ok = (a[k] > le) if mode == "episode" else (t[k] > le + K) if mode == "cooldown" else True
        if ok:
            entered[k] = True
            last_exit[nm] = int(t[k]) + HOLD
    return entered


# ------------------------------------------------------------------ the book, with the rule inside
def simulate(I, n_slots, seed, mode="none", K=None, excluded=None, pool_mask=None):
    """D419's simulate with FIXED exit and the entry rule applied at the refill. Everything else is
    D419's, line for line; `mode='none'` must reproduce D419's FIXED book bit-identically."""
    t, side, E, ATR, cost, a_ = I["t"], I["side"], I["E"], I["ATR"], I["cost"], I["a"]
    OP, HI, LO, CL, c2 = I["OP"], I["HI"], I["LO"], I["CL"], I["c2"]
    T = int(I["T"][0]); N = len(t)
    rng = np.random.default_rng(seed)
    order = np.lexsort((rng.random(N), ~c2))
    by_day = {}
    for k in order:
        if pool_mask is None or pool_mask[k]:
            by_day.setdefault(int(t[k]), []).append(int(k))
    lgE = np.log(E); lgCL = np.log(CL)
    held = {}; held_names = set(); last_exit = {}
    gross = np.zeros(T); costs = np.zeros(T); occ = np.zeros(T, np.int32); ent = np.zeros(T, np.int32)
    trades = []; skipped = 0; considered = 0
    d0 = int(t.min()) + 1
    for d in range(d0, T):
        for k in list(held):
            st = held[k]; ag = st[0]
            o, h, l, c = OP[k, ag], HI[k, ag], LO[k, ag], CL[k, ag]
            nm = int(I["i"][k])
            if not (np.isfinite(o) and np.isfinite(h) and np.isfinite(l) and np.isfinite(c)):
                held.pop(k); held_names.discard(nm); last_exit[nm] = d
                trades.append((k, st[1], ag, False, d, np.nan)); continue
            s = float(side[k]); prev = lgE[k] if ag == 0 else lgCL[k, ag - 1]
            mark = s * (lgCL[k, ag] - prev)
            gross[d] += mark; occ[d] += 1
            st[0] += 1; st[1] += mark
            if st[0] >= HOLD:
                held.pop(k); held_names.discard(nm); last_exit[nm] = d
                trades.append((k, st[1], st[0], False, d, c))
        free = n_slots - len(held)
        if free > 0:
            for k in by_day.get(d, []):
                if free == 0:
                    break
                nm = int(I["i"][k])
                if nm in held_names or k in held:
                    continue
                if not np.isfinite(E[k]) or E[k] <= 0:
                    continue
                considered += 1
                le = last_exit.get(nm, -10**9)
                if mode == "episode" and a_[k] <= le:
                    skipped += 1; continue
                if mode == "cooldown" and t[k] <= le + K:
                    skipped += 1; continue
                if mode == "random" and excluded[k]:
                    skipped += 1; continue
                held[k] = [0, 0.0]; held_names.add(nm)
                costs[d] += cost[k]; ent[d] += 1; free -= 1
    resid = sum(st[1] for st in held.values())
    return dict(gross=gross, costs=costs, occ=occ, ent=ent, trades=trades, resid=resid, d0=d0,
                skipped=skipped, considered=considered, frees=np.zeros(T, np.int32),
                refilled=np.zeros(T, np.int32), early_frees=np.zeros(T, np.int32), swaps=[])


def assert_ONCE(I, R):
    """[ONCE] no name holds two positions at once, and no trade in an EPISODE ledger is a
    re-entry by the rule's own definition given the ledger's own exits."""
    by_name = {}
    for k, pnl, age, early, d, fill in R["trades"]:
        by_name.setdefault(int(I["i"][k]), []).append((int(I["t"][k]), d, int(I["a"][k])))
    for nm, v in by_name.items():
        v.sort()
        for (t1, e1, a1), (t2, e2, a2) in zip(v, v[1:]):
            assert t2 > e1 - HOLD, f"[ONCE] name {nm} overlapping positions"
            assert a2 > e1, f"[ONCE] name {nm}: a trade entered on a zone armed at {a2} <= prior exit {e1}"
    return True


def stat(x, label):
    return B.X.stat(x, label)


def _ctrl_worker(args):
    n_slots, pool_is_c2, share, draws = args
    I = inputs()
    pool = I["c2"] if pool_is_c2 else None
    out = []
    for dr in draws:
        rng = np.random.default_rng(100000 + dr)
        ex = rng.random(len(I["t"])) < share
        R = simulate(I, n_slots, SEEDS[0], mode="random", excluded=ex, pool_mask=pool)
        S = B.score(I, R, n_slots)
        assert S["recon_rel"] < 1e-9
        out.append((dr, S["net_bp"], S["gross_bp"], S["utilisation"]))
    return n_slots, pool_is_c2, out


def run(workers):
    t0 = time.time()
    print("D420  fire once per episode -- is a re-entry a worse trade?")
    print("      the bar was committed in 7cc52eb BEFORE this ran\n")
    I = inputs()
    N = len(I["t"]); c2 = I["c2"]; rb = I["r_base"]; dates = I["dates"]; T = int(I["T"][0])
    print(f"  [ALIGN] D413's event table matches D419's cache; arming days attached")

    # ---- P2: the book with the rule off IS D419's FIXED book
    R0 = simulate(I, N_PRIMARY, SEEDS[0]); S0 = B.score(I, R0, N_PRIMARY)
    R19 = B.simulate(I, "FIXED", N_PRIMARY, SEEDS[0]); S19 = B.score(I, R19, N_PRIMARY)
    assert [x[:3] for x in R0["trades"]] == [x[:3] for x in R19["trades"]] and \
        np.array_equal(R0["gross"], R19["gross"]) and np.array_equal(R0["costs"], R19["costs"]), \
        "[P2] this simulator with the rule off is NOT D419's FIXED book"
    print(f"  P2  rule off == D419's FIXED book: {S0['trades']:,} trades, gross {S0['gross_bp']:+.3f}, "
          f"net {S0['net_bp']:+.3f} bp/bar, bit-identical")

    res = dict(per_trade={}, books={}, bar={}, secondary={})

    # ---- P1 + T1: the per-trade lens
    print(f"\n  --- PER TRADE: first entries vs the re-entries the rule discards ---")
    for tag, mode, K in (("EPISODE", "episode", None), ("COOLDOWN5", "cooldown", 5), ("COOLDOWN20", "cooldown", 20)):
        en = classify(I, mode, K)
        for pop, pm in (("pooled", np.ones(N, bool)), ("cell2", c2)):
            f, r = rb[pm & en], rb[pm & ~en]
            d = f.mean() - r.mean(); se = float(np.hypot(f.std(ddof=1) / np.sqrt(f.size), r.std(ddof=1) / np.sqrt(max(r.size, 2))))
            def trim(x):
                lo, hi = np.quantile(x, [.01, .99]); return float(1e4 * x[(x >= lo) & (x <= hi)].mean())
            res["per_trade"][f"{tag}_{pop}"] = dict(
                re_share=float((~en)[pm].mean()), first=stat(f, "first"), re=stat(r, "re-entry"),
                diff_bp=float(1e4 * d), se_bp=float(1e4 * se), t=float(d / se), trim_first=trim(f), trim_re=trim(r))
            q = res["per_trade"][f"{tag}_{pop}"]
            print(f"  {tag:10s} {pop:6s} re-entry share {100*q['re_share']:5.1f}%   first {q['first']['mean']:+7.2f} "
                  f"(median {q['first']['median']:+6.2f}, trim {q['trim_first']:+6.2f})   re-entry {q['re']['mean']:+7.2f} "
                  f"(median {q['re']['median']:+6.2f}, trim {q['trim_re']:+6.2f})   first - re {q['diff_bp']:+7.2f} +-{q['se_bp']:.2f} "
                  f"({q['t']:+5.1f} SE)")
        if mode == "episode":
            gap = I["t"][~en] + 0  # placeholder for P1's age-of-consumed distribution below
    # P1 detail: how long consumed zones had been alive when consumed (last_exit - a_k)
    en = classify(I, "episode")
    order = np.lexsort((I["t"], I["i"])); last_exit = {}; ages = []
    for k in order:
        nm = int(I["i"][k]); le = last_exit.get(nm, None)
        if en[k]:
            last_exit[nm] = int(I["t"][k]) + HOLD
        elif le is not None:
            ages.append(le - int(I["a"][k]))
    ages = np.array(ages)
    print(f"  P1  consumed zones had been armed {np.median(ages):.0f} days (p10 {np.quantile(ages,.1):.0f}, "
          f"p90 {np.quantile(ages,.9):.0f}) before the exit that consumed them")

    # ---- the books
    print(f"\n  --- THE BOOK, 50 slots and cell 2 ---")
    t1 = time.time()
    for n_slots, pool, lab in ((N_PRIMARY, None, "N50"), (N_CELL2, c2, "C2N10")):
        for seed in SEEDS:
            for tag, mode, K in (("FIXED", "none", None), ("EPISODE", "episode", None),
                                 ("COOLDOWN5", "cooldown", 5), ("COOLDOWN20", "cooldown", 20)):
                R = simulate(I, n_slots, seed, mode=mode, K=K, pool_mask=pool)
                S = B.score(I, R, n_slots); assert S["recon_rel"] < 1e-9, "[RECON]"
                if mode == "episode":
                    assert_ONCE(I, R)
                S["skipped"] = R["skipped"]; S["considered"] = R["considered"]
                res["books"][f"{tag}_{lab}_s{seed}"] = S
    print(f"  24 books in {time.time()-t1:.0f}s   [RECON] all;  [ONCE] on every EPISODE ledger")
    for lab in ("N50", "C2N10"):
        for tag in ("FIXED", "EPISODE", "COOLDOWN5", "COOLDOWN20"):
            S = res["books"][f"{tag}_{lab}_s{SEEDS[0]}"]
            print(f"  {lab:6s} {tag:10s} gross {S['gross_bp']:+7.3f}  net {S['net_bp']:+7.3f}  cost {S['cost_bp']:.3f}   "
                  f"trades {S['trades']:6,}  turn {100*S['turnover']:.2f}%/d  util {100*S['utilisation']:.1f}%   "
                  f"skipped {S['skipped']:,} of {S['considered']:,} considered   trade {S['trade_mean_bp']:+.2f}")

    # ---- T2: paired daily net difference, block bootstrap, mean over seeds
    def t2_block(lab):
        out = {}
        for tag in ("EPISODE", "COOLDOWN5", "COOLDOWN20"):
            ds, ses, dg = [], [], []
            for s in SEEDS:
                Bk = res["books"][f"{tag}_{lab}_s{s}"]; F = res["books"][f"FIXED_{lab}_s{s}"]
                diff = Bk["net_series"] - F["net_series"]
                se, mean = B.block_boot(diff, dates[T - F["days"]:])
                ds.append(1e4 * mean); ses.append(1e4 * se); dg.append(1e4 * (Bk["gross_series"] - F["gross_series"]).mean())
            out[tag] = dict(net_delta_bp=float(np.mean(ds)), se_bp=float(np.mean(ses)), t=float(np.mean(ds) / np.mean(ses)),
                            gross_delta_bp=float(np.mean(dg)), seed_spread=float(np.ptp(ds)), T2=bool(np.mean(ds) / np.mean(ses) > 2.0))
        return out
    res["bar"]["T2"] = t2_block("N50"); res["secondary"]["T2"] = t2_block("C2N10")
    print(f"\n  --- T2: rule NET minus FIXED NET, bp/bar, mean over seeds, monthly block-bootstrap SE ---")
    for lab, blk in (("N50", res["bar"]["T2"]), ("C2N10 (secondary)", res["secondary"]["T2"])):
        for tag, q in blk.items():
            print(f"  {lab:18s} {tag:10s} gross {q['gross_delta_bp']:+7.3f}   NET {q['net_delta_bp']:+7.3f} +-{q['se_bp']:.3f} "
                  f"({q['t']:+5.1f} SE)   seed spread {q['seed_spread']:.3f}   T2 {q['T2']}")

    # ---- T3: matched-count random exclusion, at EPISODE's per-trade re-entry share
    share_p = res["per_trade"]["EPISODE_pooled"]["re_share"]; share_c = res["per_trade"]["EPISODE_cell2"]["re_share"]
    proj = N_DRAW * 2 * 1.0
    print(f"\n  controls: {N_DRAW} draws x 2 books at ~1s = {proj/60:.1f} min serial; {workers} workers")
    jobs = []
    for n_slots, pool_is_c2, share in ((N_PRIMARY, False, share_p), (N_CELL2, True, share_c)):
        for w in range(workers):
            jobs.append((n_slots, pool_is_c2, share, list(range(w, N_DRAW, workers))))
    # prove chunk == whole on draw 0
    rng = np.random.default_rng(100000); ex0 = rng.random(N) < share_p
    S_in = B.score(I, simulate(I, N_PRIMARY, SEEDS[0], mode="random", excluded=ex0), N_PRIMARY)
    with mp.Pool(workers) as pool:
        results = pool.map(_ctrl_worker, jobs)
    got = [o for n, p, out in results if n == N_PRIMARY and not p for o in out if o[0] == 0][0]
    assert abs(got[1] - S_in["net_bp"]) < 1e-12, "[CHUNK]"
    print(f"  [CHUNK] worker draw 0 == in-process draw 0")
    res["controls"] = {}
    for lab, n_slots, pool_is_c2 in (("N50", N_PRIMARY, False), ("C2N10", N_CELL2, True)):
        out = sorted(o for n, p, oo in results if n == n_slots and p == pool_is_c2 for o in oo)
        net = np.array([o[1] for o in out]); ut = np.array([o[3] for o in out])
        obs = res["books"][f"EPISODE_{lab}_s{SEEDS[0]}"]
        p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs["net_bp"] - p95
        res["controls"][lab] = dict(share=float(share_p if lab == "N50" else share_c), n=int(net.size),
                                    p5=float(np.quantile(net, .05)), p50=float(np.median(net)), p95=p95, se=se,
                                    observed=obs["net_bp"], ctrl_util=float(ut.mean()), obs_util=obs["utilisation"],
                                    beats=bool(edge > 0), margin_se=float(edge / se) if se > 0 else float("inf"),
                                    unresolved=bool(abs(edge) < 2 * se), T3=bool(edge > 0 and abs(edge) >= 2 * se))
        q = res["controls"][lab]
        print(f"  T3 {lab:6s} EPISODE net {q['observed']:+7.3f}   random-exclusion@{100*q['share']:.1f}%  p5 {q['p5']:+7.3f}  "
              f"p50 {q['p50']:+7.3f}  p95 {q['p95']:+7.3f} (+-{se:.3f})   margin {q['margin_se']:+5.1f} SE   T3 {q['T3']}"
              f"{'  UNRESOLVED' if q['unresolved'] else ''}   util obs {100*q['obs_util']:.1f}% vs ctrl {100*q['ctrl_util']:.1f}%")

    # ---- P4: one name's episode history
    en = classify(I, "episode"); nm_counts = np.bincount(I["i"][~en]) if (~en).any() else np.zeros(1)
    nm = int(np.argmax(nm_counts)); ks = np.flatnonzero(I["i"] == nm); ks = ks[np.argsort(I["t"][ks])][:14]
    print(f"\n  P4  {I['symbols'][nm]}: its first {len(ks)} zones in touch order")
    for k in ks:
        print(f"      armed {dates[I['a'][k]]}  touched {dates[I['t'][k]]}  side {I['side'][k]:+d}  "
              f"{'ENTERED' if en[k] else 'consumed'}   r_base {1e4*rb[k]:+6.0f} bp")

    # ---- the bar
    T1 = bool(res["per_trade"]["EPISODE_pooled"]["t"] > 2.0)
    T2 = res["bar"]["T2"]["EPISODE"]["T2"]; T3 = res["controls"]["N50"]["T3"]
    s1 = bool(res["per_trade"]["EPISODE_cell2"]["t"] > 2.0); s2 = res["secondary"]["T2"]["EPISODE"]["T2"]; s3 = res["controls"]["C2N10"]["T3"]
    q = res["per_trade"]["EPISODE_pooled"]
    print(f"\n  --- THE BAR (committed 7cc52eb), EPISODE ---")
    print(f"    T1 first entries beat re-entries, 2 SE      : {T1}   ({q['diff_bp']:+.2f} bp, {q['t']:+.1f} SE)")
    print(f"    T2 EPISODE book net beats FIXED net, 2 SE   : {T2}   ({res['bar']['T2']['EPISODE']['net_delta_bp']:+.3f} bp/bar, {res['bar']['T2']['EPISODE']['t']:+.1f} SE)")
    print(f"    T3 EPISODE beats matched random exclusion   : {T3}   (margin {res['controls']['N50']['margin_se']:+.1f} SE)")
    print(f"    secondary cell 2 (cannot clear)             : T1 {s1}  T2 {s2}  T3 {s3}")
    print(f"\n  VERDICT: T1 {'CLEARS' if T1 else 'FAILS'}   T2 {'CLEARS' if T2 else 'FAILS'}   T3 {'CLEARS' if T3 else 'FAILS'}")
    for k_, S in res["books"].items():
        S.pop("gross_series"); S.pop("net_series"); S.pop("run_dist")
    res["bar"].update(dict(T1=T1, T2_flag=T2, T3=T3)); res["secondary"].update(dict(T1=s1, T2_flag=s2, T3=s3))
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

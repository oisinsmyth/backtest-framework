"""D424 -- SL, TS, TP each alone on STACK2-ANY & cell 2, both lenses. Bar committed in 05e95df BEFORE this file.

PER TRADE   D417's walker and grid, unchanged, restricted to the cell.   T1  TP 2.0 paired delta > 0 by 2 SE
THE BOOK    D419's simulator, rule by rule, on the cell-2 ANY-REQUIRED pool.
            T2  TP net - FIXED net > 0 by 2 SE (3 seeds, monthly block bootstrap) AND TP net > p95 of the
                sampled-runs control (200 draws)
usage:  uv run python -u scripts/run_d424_atr_exits_cell.py --run [--workers 8]
"""
import argparse, importlib.util, json, multiprocessing as mp, pathlib, sys, time
import numpy as np

REPO = pathlib.Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
LV = _load("d423l", "d423_exit_levels.py")
R17 = _load("d417r", "run_d417_exits.py")

OUT = REPO / "data" / "d424_atr_exits_cell.json"
FLAGS = REPO / "temp" / "d422_flags.npz"
HOLD, N10, SEEDS, N_DRAW = 5, 10, (419, 4190, 41900), 200
FAMS = ("SL", "TS", "TP", "SLTP")


def paired(rr, rf, W, mask, label):
    d = (rr - rf)[mask]; n = d.size; early = W["early"][mask]
    hold = np.where(early, W["bar"][mask] + 1, HOLD).astype(float)
    out = dict(label=label, n=int(n), fixed_bp=float(1e4 * rf[mask].mean()), rule_bp=float(1e4 * rr[mask].mean()),
               delta_bp=float(1e4 * d.mean()), se_bp=float(1e4 * d.std(ddof=1) / np.sqrt(n)), early=float(early.mean()),
               hold=float(hold.mean()), bp_per_day=float(1e4 * rr[mask].mean() / hold.mean()),
               win=float(100 * (rr[mask] > 0).mean()), std_ratio=float(rr[mask].std() / rf[mask].std()),
               max_loss=float(1e4 * rr[mask].min()))
    out["t"] = out["delta_bp"] / out["se_bp"] if out["se_bp"] > 0 else float("nan")
    if early.any():
        out["would_have_bp"] = float(1e4 * rf[mask][early].mean()); out["filled_at_bp"] = float(1e4 * rr[mask][early].mean())
        out["forfeit_bp"] = out["filled_at_bp"] - out["would_have_bp"]
    return out


def show(p):
    fx = f"   would-have {p['would_have_bp']:+8.2f}  filled-at {p['filled_at_bp']:+8.2f}  forfeit {p['forfeit_bp']:+6.2f}" if "would_have_bp" in p else ""
    print(f"  {p['label']:30s} n {p['n']:6,}  fixed {p['fixed_bp']:+6.2f}  rule {p['rule_bp']:+6.2f}  PAIRED {p['delta_bp']:+6.2f} +- {p['se_bp']:4.2f}  "
          f"t {p['t']:+5.1f}  early {100*p['early']:5.1f}%  hold {p['hold']:4.2f}d  bp/d {p['bp_per_day']:+5.2f}  win {p['win']:4.1f}%  std x{p['std_ratio']:.2f}  maxloss {p['max_loss']:+7.0f}{fx}")


def _ctrl_worker(args):
    fam, draws, run_dist = args
    Bw = _load("d419w", "run_d419_book.py")
    I = dict(Bw.build_inputs()); z = np.load(FLAGS); pool = I["c2"] & z["s2any"]
    rd = np.array(run_dist); out = []
    for dr in draws:
        rng = np.random.default_rng(100000 + dr)
        R = Bw.simulate(I, fam, N10, SEEDS[0], pool_mask=pool, run_targets=rng.choice(rd, size=len(I["t"])))
        S = Bw.score(I, R, N10); assert S["recon_rel"] < 1e-9, "[RECON] control"
        out.append((dr, S["net_bp"], S["gross_bp"], S["run"], S["turnover"]))
    return fam, out


def run(workers):
    t0 = time.time()
    print("D424  SL, TS, TP each alone on STACK2-ANY & cell 2 -- both lenses\n      the bar was committed in 05e95df BEFORE this ran\n")
    I, P, B, fl, M = LV.load()
    t, i, side, E, ATR, c2 = I["t"], I["i"], I["side"], I["E"], I["ATR"], I["c2"]
    A = fl["s2any"]; prim = A & c2; N = len(t); T = int(I["T"][0])
    yr = np.array([int(str(x)[:4]) for x in I["dates"][t]])
    assert N == 180050 and int(prim.sum()) == 9411, "[STAGE0]"
    last = P["CL"][np.clip(t + HOLD, 0, T - 1), i]
    W = R17.walk(I["OP"], I["HI"], I["LO"], I["CL"], E, ATR, side, last)
    R17.assert_FILL(W, E, ATR, side)
    r_fixed = I["r_base"]
    # [X] D417's cell-2 TP 2.0 line reproduces on the full cell 2 before the restriction
    rr = side * (np.log(W["TP2.0"]["price"]) - np.log(E)); px = paired(rr, r_fixed, W["TP2.0"], c2, "x")
    assert abs(px["rule_bp"] - 32.43) < 0.01 and abs(px["delta_bp"] - 2.17) < 0.01 and abs(100 * px["early"] - 22.1) < 0.1, f"[X] {px}"
    print(f"  [X]    D417's cell-2 TP 2.0 line reproduces: {px['rule_bp']:+.2f}, paired {px['delta_bp']:+.2f}, early {100*px['early']:.1f}%   [FILL] all rules")

    res = dict(per_trade={}, books={}, deltas={}, premium={}, control={})
    masks = [("ANY & cell 2", prim), ("ANY & cell 2  long", prim & (side > 0)), ("ANY & cell 2  short", prim & (side < 0)),
             ("ANY & cell 2  2018+", prim & (yr >= 2018)), ("ANY pooled", A), ("cell 2 all", c2)]
    print("\n1. PER TRADE, paired against the fixed exit -- D417's grid on ANY & cell 2")
    for fam, p in R17.RULES:
        key = R17.rname(fam, p); rr = side * (np.log(W[key]["price"]) - np.log(E))
        q = paired(rr, r_fixed, W[key], prim, f"{key:9s} ANY & cell 2"); res["per_trade"][f"{key}|ANY & cell 2"] = q; show(q)
    print("\n   the primaries on the other populations")
    for fam, p in R17.RULES:
        key = R17.rname(fam, p)
        if p != R17.PRIMARY.get(fam, p) and fam != "SLTP":
            continue
        rr = side * (np.log(W[key]["price"]) - np.log(E))
        for lab, m in masks[1:]:
            q = paired(rr, r_fixed, W[key], m, f"{key:9s} {lab}"); res["per_trade"][f"{key}|{lab}"] = q; show(q)
    pf = paired(r_fixed, r_fixed, dict(early=np.zeros(N, bool), bar=np.full(N, -1)), prim, "FIXED")
    res["per_trade"]["FIXED|ANY & cell 2"] = dict(pf, win=float(100 * (r_fixed[prim] > 0).mean()))
    print(f"\n  FIXED win rate on the cell {res['per_trade']['FIXED|ANY & cell 2']['win']:.1f}%")

    print("\n2. THE BOOK -- cell-2 ANY-REQUIRED, 10 slots, D419's rules")
    pool = prim
    R22 = M.simulate(I, N10, SEEDS[0], pool_mask=pool); R0 = B.simulate(I, "FIXED", N10, SEEDS[0], pool_mask=pool)
    assert [x[:3] for x in R0["trades"]] == [x[:3] for x in R22["trades"]], "[P2]"
    print("  [P2]   D419's FIXED on the pool == D422's ANY-REQ book bit-identically")
    series = {}; t1 = time.time()
    for rule in ("FIXED",) + FAMS:
        for seed in SEEDS:
            R = B.simulate(I, rule, N10, seed, pool_mask=pool); S = B.score(I, R, N10); assert S["recon_rel"] < 1e-9, "[RECON]"
            series[(rule, seed)] = S["net_series"]
            if rule != "FIXED":
                res["premium"][f"{rule}_s{seed}"] = B.premium(I, R, T)
                if seed == SEEDS[0]:
                    res.setdefault("run_dist", {})[rule] = S["run_dist"].tolist()
            res["books"][f"{rule}_s{seed}"] = {k: v for k, v in S.items() if not k.endswith("_series") and k != "run_dist"}
    print(f"  {len(res['books'])} books in {time.time()-t1:.0f}s   [RECON] all\n")
    print(f"  {'rule':8s} {'gross':>7s} {'net':>7s} {'cost':>6s} {'util':>6s} {'trades':>7s} {'run':>5s} {'early':>6s} {'per trade':>9s}   net by seed")
    d0 = R0["d0"]; dates = I["dates"]
    for rule in ("FIXED",) + FAMS:
        S = res["books"][f"{rule}_s{SEEDS[0]}"]; nets = [res["books"][f"{rule}_s{s}"]["net_bp"] for s in SEEDS]
        print(f"  {rule:8s} {S['gross_bp']:+7.3f} {S['net_bp']:+7.3f} {S['cost_bp']:6.3f} {100*S['utilisation']:5.1f}% {S['trades']:7,} {S['run']:5.2f} {100*S['early_share']:5.1f}% {S['trade_mean_bp']:+9.2f}   "
              + " ".join(f"{x:+.3f}" for x in nets))
        if rule != "FIXED":
            diff = np.mean([series[(rule, s)] - series[("FIXED", s)] for s in SEEDS], axis=0)
            se, mean = B.block_boot(diff, dates[d0:])
            g = np.mean([res["books"][f"{rule}_s{s}"]["gross_bp"] - res["books"][f"FIXED_s{s}"]["gross_bp"] for s in SEEDS])
            res["deltas"][rule] = dict(gross_delta=float(g), net_delta=float(1e4 * mean), se=float(1e4 * se), t=float(mean / se), net_abs=float(np.mean(nets)))
    print("\n  deltas vs FIXED, mean over seeds, monthly block-bootstrap SE")
    for rule, dd in res["deltas"].items():
        print(f"  {rule:8s} gross delta {dd['gross_delta']:+6.3f}   NET delta {dd['net_delta']:+6.3f} +- {dd['se']:.3f}   {dd['t']:+4.1f} SE")
    print("\n  the replacement premium (D304), seed 419")
    for rule in FAMS:
        pr = res["premium"][f"{rule}_s{SEEDS[0]}"].get("avail", {})
        print(f"  {rule:8s} n {pr.get('n', 0):6,}" + (f"  premium {pr['premium_bp']:+7.2f} +- {pr['se_bp']:.2f}   arriving {pr['arriving_bp']:+7.2f}   forfeited {pr['forfeited_bp']:+7.2f}" if "premium_bp" in pr else ""))

    print(f"\n3. SAMPLED-RUNS CONTROLS, SL / TS / TP ({N_DRAW} draws each, {workers} workers)")
    np.savez_compressed(FLAGS, **fl) if not FLAGS.exists() else None
    jobs = [(fam, list(range(w, N_DRAW, workers)), res["run_dist"][fam]) for fam in ("SL", "TS", "TP") for w in range(workers)]
    rng = np.random.default_rng(100000); tg0 = rng.choice(np.array(res["run_dist"]["SL"]), size=N)
    S_in = B.score(I, B.simulate(I, "SL", N10, SEEDS[0], pool_mask=pool, run_targets=tg0), N10)
    with mp.Pool(workers) as pl:
        results = pl.map(_ctrl_worker, jobs)
    agg = {}
    for fam, out in results:
        agg.setdefault(fam, []).extend(out)
    got = sorted(agg["SL"])[0]; assert abs(got[1] - S_in["net_bp"]) < 1e-12, "[CHUNK]"
    print("  [CHUNK] worker draw 0 == in-process")
    for fam in ("SL", "TS", "TP"):
        out = sorted(agg[fam]); net = np.array([o[1] for o in out]); run = np.array([o[3] for o in out])
        obs = res["deltas"][fam]["net_abs"]; p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs - p95
        bk_run = res["books"][f"{fam}_s{SEEDS[0]}"]["run"]
        assert abs(run.mean() - bk_run) < 0.05, f"[NUISANCE] {fam} control run {run.mean():.3f} vs {bk_run:.3f}"
        res["control"][fam] = dict(p5=float(np.quantile(net, .05)), p50=float(np.median(net)), p95=p95, se=se, observed=obs, margin_se=float(edge / se),
                                   beats=bool(edge > 0), unresolved=bool(abs(edge) < 2 * se), passes=bool(edge > 0 and abs(edge) >= 2 * se), run=float(run.mean()))
        print(f"  {fam:4s} net {obs:+.3f}   control p5 {res['control'][fam]['p5']:+.3f}  p50 {res['control'][fam]['p50']:+.3f}  p95 {p95:+.3f} (+-{se:.3f})   "
              f"margin {edge/se:+5.1f} SE   {'PASS' if res['control'][fam]['passes'] else ('UNRESOLVED' if res['control'][fam]['unresolved'] else 'FAIL')}   [NUISANCE] run {run.mean():.2f} vs {bk_run:.2f}")

    p1 = res["per_trade"]["TP2.0|ANY & cell 2"]; dd = res["deltas"]["TP"]; ct = res["control"]["TP"]
    T1 = bool(p1["delta_bp"] > 0 and p1["t"] >= 2); T2 = bool(dd["net_delta"] > 0 and dd["t"] >= 2 and ct["passes"])
    res["bar"] = dict(T1=T1, T2=T2, clears=bool(T1 and T2))
    print("\n4. THE BAR -- TP 2.0 on ANY & cell 2")
    print(f"    T1 paired delta > 0 by 2 SE          : {T1}   ({p1['delta_bp']:+.2f} +- {p1['se_bp']:.2f}, {p1['t']:+.1f} SE)")
    print(f"    T2 book net delta > 0 by 2 SE, > ctrl : {T2}   (delta {dd['net_delta']:+.3f} +- {dd['se']:.3f}, {dd['t']:+.1f} SE; ctrl margin {ct['margin_se']:+.1f} SE)")
    print(f"    TP 2.0 {'CLEARS' if res['bar']['clears'] else 'FAILS'} the bar")
    ps, pt, p10 = res["per_trade"]["SL1.5|ANY & cell 2"], res["per_trade"]["TS1.5|ANY & cell 2"], res["per_trade"]["TP1.0|ANY & cell 2"]
    print("\n5. PREDICTIONS")
    print(f"    X-a TP 2.0 -4..+3 inside 2 SE, fires 18-26%, forfeit -5..-20 : {p1['delta_bp']:+.2f} ({p1['t']:+.1f} SE), {100*p1['early']:.1f}%, forfeit {p1.get('forfeit_bp', float('nan')):+.2f}")
    print(f"    X-b SL 1.5 -8..-18 fires 28-36%; TS 1.5 -10..-20 fires 55-65% : SL {ps['delta_bp']:+.2f} {100*ps['early']:.1f}%;  TS {pt['delta_bp']:+.2f} {100*pt['early']:.1f}%")
    print(f"    X-c TP 1.0 highest win rate >58%, delta inside 2 SE            : win {p10['win']:.1f}%, {p10['delta_bp']:+.2f} ({p10['t']:+.1f} SE)")
    print(f"    X-d TP book gross -0.5..+0.3, util < 68.2%, net inside 2 SE, above ctrl p50 below p95 : gross {dd['gross_delta']:+.3f}, util {100*res['books'][f'TP_s{SEEDS[0]}']['utilisation']:.1f}%, "
          f"net {dd['t']:+.1f} SE, vs p50 {ct['observed']-ct['p50']:+.3f}, vs p95 {ct['observed']-ct['p95']:+.3f}")
    print(f"    X-e SL, TS books negative by > 2 SE                            : SL {res['deltas']['SL']['t']:+.1f} SE, TS {res['deltas']['TS']['t']:+.1f} SE")
    OUT.write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    print(f"\nwrote {OUT}   total {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    if a.run:
        run(a.workers)

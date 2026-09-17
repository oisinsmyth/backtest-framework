"""D437 stage 1 -- shock-with-state: the in-sample event study and the weighted book, against the atlas's own floors.
Spec docs/decisions/D437-shock-with-state-stage-1-the-in-sample-event-study-and-the.md (committed BEFORE this file, R8).
In-sample on the mining fixture; no holdout is read.

    uv run python -u scripts/run_d437_stage1.py --run
"""
from __future__ import annotations
import argparse, importlib.util, json, sys, time
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
A34 = _load("d434", "run_d434_atlas_volume.py"); A35 = _load("d435", "run_d435_atlas_conditional.py"); A92 = _load("d392", "run_d392_base_rate_atlas.py")
OUT = REPO / "data" / "d437_stage1.json"
HOLD, N_DRAW, N_ROT, SEED = 20, 100, 100, 437
COMP = {"A": ("mom_hi", 0, 0.40), "B": ("price_hi", 1, 0.25), "C": ("price_lo", 0, 0.15), "D": ("mom_lo", 1, 0.10)}      # state, side (0 long / 1 short), weight
WSUM = sum(v[2] for v in COMP.values())
SLOTS = (150, 100, 250)


def block_boot(x, dates, n_boot=1000, seed=7):
    mon = np.array([str(d)[:7] for d in dates]); keys, inv = np.unique(mon, return_inverse=True)
    sums = np.bincount(inv, weights=x); cnts = np.bincount(inv); rng = np.random.default_rng(seed); m = np.empty(n_boot)
    for b in range(n_boot):
        pick = rng.integers(0, keys.size, keys.size); m[b] = sums[pick].sum() / cnts[pick].sum()
    return float(m.std(ddof=1)), float(x.mean())


def weighted_series(res_by_k):
    """Weighted daily hedged deployed return, bp; an idle component contributes 0 that day (capital idle)."""
    T = len(next(iter(res_by_k.values()))["book_dep_x"]); s = np.zeros(T)
    for k, r in res_by_k.items():
        s += COMP[k][2] * np.nan_to_num(np.asarray(r["book_dep_x"], float)) * 1e4
    return s / WSUM


def per_bar_cost(db_by_k, tb_by_k):
    """Weighted 2-crossing PUB cost per bar (+ borrow per bar on shorts) from the components' own deployed and trade blocks."""
    c = 0.0
    for k, db in db_by_k.items():
        cost = db["PUB"]["hedged_2x"]["cost_bp"]
        if COMP[k][1] == 1:
            cost += tb_by_k[k]["borrow"]["mean_bp"] * db["PUB"]["hedged"]["turnover"]
        c += COMP[k][2] * cost
    return c / WSUM


def draw_state_matched(rng, ev, pool_shift, T):
    """Same daily count as ev, cells drawn from pool_shift (state, non-shock, eligible, shifted) instead."""
    out = np.zeros_like(ev); cnt = ev.sum(axis=1)
    for t in np.flatnonzero(cnt):
        avail = np.flatnonzero(pool_shift[t]); k = min(int(cnt[t]), avail.size)
        if k: out[t, rng.choice(avail, size=k, replace=False)] = True
    return out


def rotate(rng, ev, elig):
    out = np.zeros_like(ev)
    for j in np.flatnonzero(ev.any(axis=0)):
        out[:, j] = np.roll(ev[:, j], int(rng.integers(1, ev.shape[0])))
    return out & elig


def run():
    t0 = time.time()
    print("D437 STAGE 1 -- shock-with-state: the in-sample event study and the weighted book\n      the bar was committed in ee0b72a BEFORE this ran; mining fixture only; no holdout\n")
    PREP = _load("d348p", "d348_prep.py"); V59 = _load("d359r", "run_d359_loser_rally_short.py")
    P = PREP.prep(need_grids=True); T, N = P["T"], P["n"]; elig = np.asarray(P["elig"]); dates = np.array([str(x)[:10] for x in P["dates"]]); yr = np.array([int(d[:4]) for d in dates])
    sc = np.full((T, N), 50.0); idx = A92.eligible_index(elig)
    mk = A92.draw_mask(np.random.default_rng(A92.SEED), idx, (T, N), 2_000); r1 = V59.run_mirror(P, mk, sc, "cap", 20); m1, c1 = A92.score_once(V59, P, mk, 20, "long", sc)
    assert abs(m1 - float(V59.V47.pnl_bp(r1).mean())) < 1e-12 and c1 == len(r1["trades"]), "[K]"
    st = A35.state_pools_unshifted(P, elig); vp, F = A34.volume_pools_unshifted(P, elig)
    ev = {k: A35.shift(st[s] & vp["rv_x3"], elig) for k, (s, side, w) in COMP.items()}
    E = A35.shift(st["ret20_lo"], elig)
    d435 = {}
    for h in "ab": d435.update(json.load(open(REPO / "data" / f"d435_atlas_cond_{h}.json"))["cells"])
    floor = {k: d435[f"cond2|n=3000|cap=20|{'long' if side == 0 else 'short'}|pool={s}|rv_x3|conc=1.0"] for k, (s, side, w) in COMP.items()}
    print(f"  [K] kernel probe == run_d359's path;  events A {int(ev['A'].sum()):,} B {int(ev['B'].sum()):,} C {int(ev['C'].sum()):,} D {int(ev['D'].sum()):,}", flush=True)
    res = dict(components={}, weighted={}, combined={}, controls={}, rotation={}, calendar={}, E={}, bar={})

    print("\n1. THE COMPONENTS -- per trade (D359's trade_block; 2c PUB and PB; borrow on shorts) and [P2] against the D435 floors")
    R, TB, DB = {}, {}, {}
    for k, (s, side, w) in COMP.items():
        R[k] = V59.simulate(P, ev[k], sc, "cap", HOLD, side); TB[k] = V59.trade_block(P, R[k], elig, side, False); DB[k] = V59.deployed_block(R[k], P)
        tb = TB[k]; fl = floor[k]; ok = abs(tb["mean_bp"] - fl["p50"]) <= fl["sd"]
        assert ok, f"[P2] {k}: per-trade {tb['mean_bp']:+.2f} vs D435 p50 {fl['p50']:+.2f} (sd {fl['sd']:.2f})"
        borrow = tb.get("borrow", {}).get("mean_bp", 0.0)
        res["components"][k] = dict(state=s, side="short" if side else "long", weight=w, trades=tb["trades"], gross=tb["mean_bp"], median=tb["median_bp"], t=tb["t"], hold=tb["hold_mean"],
                                    two_c=tb["two_c"], commission=tb["commission_bp"], borrow=borrow, net_PUB=tb["mean_bp"] - tb["two_c"]["PUB"] - borrow, net_PB=tb["mean_bp"] - tb["two_c"]["PB"] - borrow,
                                    floor_p50=fl["p50"], floor_sd=fl["sd"], era1=tb["era1_mean_bp"], era2=tb["era2_mean_bp"], by_year={y: v["mean_bp"] for y, v in tb["by_year"].items()},
                                    deployed=dict(gross_bp=DB[k]["PUB"]["hedged"]["gross_bp"], cost2_bp=DB[k]["PUB"]["hedged_2x"]["cost_bp"], net2_bp=DB[k]["PUB"]["hedged_2x"]["net_bp"], turnover=DB[k]["PUB"]["hedged"]["turnover"], vol_bp=DB[k]["PUB"]["hedged"]["vol_bp"]))
        c = res["components"][k]
        print(f"  {k} {s:9s} {c['side']:5s} w {w:.2f}  trades {c['trades']:6,}  gross {c['gross']:+7.2f} (floor p50 {fl['p50']:+6.2f} ± {fl['sd']:.1f})  med {c['median']:+6.2f}  hold {c['hold']:4.1f}  "
              f"2c PUB {c['two_c']['PUB']:5.1f} PB {c['two_c']['PB']:5.1f}  borrow {borrow:4.1f}  NET PUB {c['net_PUB']:+6.2f}  PB {c['net_PB']:+6.2f}  | deployed gross {c['deployed']['gross_bp']:+5.2f}/bar  cost2 {c['deployed']['cost2_bp']:4.2f}  net2 {c['deployed']['net2_bp']:+5.2f}", flush=True)
    print("  [P2] every component's per-trade gross is within its D435 cell's draw sd of the cell's p50")
    print("  by year, gross per trade: " + " | ".join(f"{k}: " + " ".join(f"{y}:{v:+.0f}" for y, v in sorted(res["components"][k]["by_year"].items())) for k in ("A", "B")))

    print("\n2. THE WEIGHTED BOOK")
    g = weighted_series(R); cost = per_bar_cost(DB, TB); net = g - cost
    d0 = int(min(min(t[1] for t in R[k]["trades"]) for k in R)); gs, ns = g[d0:], net[d0:]; ds = dates[d0:]
    se_g, mg = block_boot(gs, ds); se_n, mn = block_boot(ns, ds)
    ys = np.array([int(d[:4]) for d in ds])
    res["weighted"] = dict(gross_bp=mg, gross_se=se_g, cost_bp=float(cost), net_bp=mn, net_se=se_n, sharpe_net=float(ns.mean() / ns.std(ddof=1) * np.sqrt(252)), sharpe_gross=float(gs.mean() / gs.std(ddof=1) * np.sqrt(252)),
                           by_year={str(y): float(ns[ys == y].mean()) for y in range(2010, 2027) if (ys == y).any()}, era1=float(ns[:len(ns) // 2].mean()), era2=float(ns[len(ns) // 2:].mean()))
    w_ = res["weighted"]
    print(f"  gross {mg:+.3f} ± {se_g:.3f} bp/bar   cost (2c PUB + borrow, weighted) {cost:.3f}   NET {mn:+.3f} ± {se_n:.3f} ({mn/se_n:+.1f} SE)   Sharpe net {w_['sharpe_net']:+.2f}  gross {w_['sharpe_gross']:+.2f}")
    print("  net by year: " + "  ".join(f"{y}:{v:+.2f}" for y, v in w_["by_year"].items()) + f"   era1 {w_['era1']:+.2f}  era2 {w_['era2']:+.2f}")

    print("\n3. THE COMBINED SLOT BOOKS (union, equal weight, first-come)")
    z = np.zeros_like(ev["A"]); sl, ss = ev["A"] | ev["C"], ev["B"] | ev["D"]
    for n_max in SLOTS:
        rc = V59.EB.simulate_event(P["A3"], sl, ss, sc, exit="cap", cap=HOLD, n_max=n_max, x_target=V59.X_TARGET, U=V59.U_SLOTS, hedged_series=True)
        dbc = V59.deployed_block(rc, P); h = dbc["PUB"]["hedged"]; h2 = dbc["PUB"]["hedged_2x"]
        util = float(np.nanmean(np.asarray(rc["held"], float)[d0:]) / n_max)
        res["combined"][str(n_max)] = dict(trades=len(rc["trades"]), skipped=int(np.asarray(rc["skipped"]).sum()), util=util, gross_bp=h["gross_bp"], cost2_bp=h2["cost_bp"], net2_bp=h2["net_bp"], sharpe_net2=h2["sharpe_net"])
        print(f"  n_max {n_max:3d}: trades {len(rc['trades']):6,}  refused when full {int(np.asarray(rc['skipped']).sum()):6,}  util {100*util:4.1f}%  gross {h['gross_bp']:+5.2f}/bar  cost2 {h2['cost_bp']:4.2f}  net2 {h2['net_bp']:+5.2f}  Sharpe net2 {h2['sharpe_net']:+.2f}")

    print(f"\n4. STATE-MATCHED RANDOM-EVENT BOOKS ({N_DRAW} draws): same state, same daily count, non-shock cells")
    rng = np.random.default_rng(SEED); pools = {k: A35.shift(st[s] & ~vp["rv_x3"] & elig, elig) for k, (s, side, w) in COMP.items()}
    ctrl_g, ctrl_pt = [], {k: [] for k in COMP}; t1 = time.time()
    for d in range(N_DRAW):
        Rd = {}
        for k, (s, side, w) in COMP.items():
            m = draw_state_matched(rng, ev[k], pools[k], T); Rd[k] = V59.simulate(P, m, sc, "cap", HOLD, side); ctrl_pt[k].append(float(V59.V47.pnl_bp(Rd[k]).mean()))
        ctrl_g.append(float(weighted_series(Rd)[d0:].mean()))
    ctrl_g = np.array(ctrl_g); p95 = float(np.quantile(ctrl_g, .95)); se = float(ctrl_g.std(ddof=1) / np.sqrt(N_DRAW)); edge = mg - p95
    res["controls"] = dict(weighted_gross=dict(observed=mg, p50=float(np.median(ctrl_g)), p95=p95, se=se, margin_se=edge / se, passes=bool(edge > 0 and abs(edge) >= 2 * se), unresolved=bool(abs(edge) < 2 * se)),
                           per_trade={k: dict(observed=res["components"][k]["gross"], p50=float(np.median(v)), p95=float(np.quantile(v, .95)), increment=res["components"][k]["gross"] - float(np.median(v))) for k, v in ctrl_pt.items()})
    q = res["controls"]["weighted_gross"]
    print(f"  weighted book gross {mg:+.3f} vs state-matched p50 {q['p50']:+.3f}  p95 {p95:+.3f} (±{se:.3f})   margin {q['margin_se']:+.1f} SE   {'PASS' if q['passes'] else ('UNRESOLVED' if q['unresolved'] else 'FAIL')}   ({time.time()-t1:.0f}s)")
    print("  per trade, shock vs state-matched p50: " + "  ".join(f"{k} {res['controls']['per_trade'][k]['observed']:+.1f} vs {res['controls']['per_trade'][k]['p50']:+.1f} (+{res['controls']['per_trade'][k]['increment']:.1f})" for k in COMP))

    print(f"\n5. TIME ROTATION ({N_ROT} draws): each name's events rolled by its own offset")
    rot = []; t1 = time.time()
    for d in range(N_ROT):
        Rd = {k: V59.simulate(P, rotate(rng, ev[k], elig), sc, "cap", HOLD, side) for k, (s, side, w) in COMP.items()}; rot.append(float(weighted_series(Rd)[d0:].mean()))
    rot = np.array(rot); p95r = float(np.quantile(rot, .95)); ser = float(rot.std(ddof=1) / np.sqrt(N_ROT)); edger = mg - p95r
    res["rotation"] = dict(observed=mg, p50=float(np.median(rot)), p95=p95r, se=ser, margin_se=edger / ser, passes=bool(edger > 0 and abs(edger) >= 2 * ser))
    print(f"  weighted book gross {mg:+.3f} vs rotation p50 {np.median(rot):+.3f}  p95 {p95r:+.3f} (±{ser:.3f})   margin {edger/ser:+.1f} SE   {'PASS' if res['rotation']['passes'] else 'FAIL'}   ({time.time()-t1:.0f}s)")

    print("\n6. THE CALENDAR NULL -- spacing 58-68 sessions from the name's previous shock (the quarter) vs the rest")
    x3 = A35.shift(vp["rv_x3"], elig); quarterly = np.zeros_like(x3)
    for j in range(N):
        d = np.flatnonzero(x3[:, j])
        if d.size > 1:
            sp = np.diff(d); qq = d[1:][(sp >= 58) & (sp <= 68)]; quarterly[qq, j] = True
    Rq, Rn = {}, {}
    for k, (s, side, w) in COMP.items():
        mq, mn_ = ev[k] & quarterly, ev[k] & ~quarterly
        Rq[k] = V59.simulate(P, mq, sc, "cap", HOLD, side); Rn[k] = V59.simulate(P, mn_, sc, "cap", HOLD, side)
        pq, pn = V59.V47.pnl_bp(Rq[k]), V59.V47.pnl_bp(Rn[k])
        res["calendar"][k] = dict(q_n=int(pq.size), q_gross=float(pq.mean()), n_n=int(pn.size), n_gross=float(pn.mean()), n_t=float(pn.mean() / (pn.std(ddof=1) / np.sqrt(pn.size))))
        print(f"  {k}: quarterly n {pq.size:5,} gross {pq.mean():+7.2f}   rest n {pn.size:6,} gross {pn.mean():+7.2f} ({res['calendar'][k]['n_t']:+.1f} SE)")
    gn = weighted_series(Rn)[d0:]; ctrl_n = []
    for d in range(N_DRAW):
        Rd = {k: V59.simulate(P, draw_state_matched(rng, ev[k] & ~quarterly, pools[k], T), sc, "cap", HOLD, side) for k, (s, side, w) in COMP.items()}; ctrl_n.append(float(weighted_series(Rd)[d0:].mean()))
    ctrl_n = np.array(ctrl_n); p95n = float(np.quantile(ctrl_n, .95)); sen = float(ctrl_n.std(ddof=1) / np.sqrt(N_DRAW)); edgen = float(gn.mean()) - p95n
    res["calendar"]["weighted_nonq"] = dict(gross=float(gn.mean()), p50=float(np.median(ctrl_n)), p95=p95n, se=sen, margin_se=edgen / sen, passes=bool(edgen > 0 and abs(edgen) >= 2 * sen))
    print(f"  weighted book on NON-quarterly events: gross {gn.mean():+.3f} vs state-matched p95 {p95n:+.3f} (±{sen:.3f})   margin {edgen/sen:+.1f} SE")

    print("\n7. E -- A and C split by ret20_lo")
    for k in ("A", "C"):
        Re, Rne = V59.simulate(P, ev[k] & E, sc, "cap", HOLD, 0), V59.simulate(P, ev[k] & ~E, sc, "cap", HOLD, 0); pe, pne = V59.V47.pnl_bp(Re), V59.V47.pnl_bp(Rne)
        res["E"][k] = dict(with_n=int(pe.size), with_gross=float(pe.mean()), without_n=int(pne.size), without_gross=float(pne.mean()))
        print(f"  {k}: with ret20_lo n {pe.size:5,} gross {pe.mean():+7.2f}   without n {pne.size:5,} gross {pne.mean():+7.2f}   diff {pe.mean()-pne.mean():+6.2f}")

    T1 = True; T2 = bool(mn > 0 and mn / se_n >= 2); T3 = bool(q["passes"]); T4 = bool(all(res["calendar"][k]["n_t"] >= 2 and res["calendar"][k]["n_gross"] > 0 for k in COMP) and res["calendar"]["weighted_nonq"]["passes"]); T5 = bool(res["rotation"]["passes"])
    res["bar"] = dict(T1=T1, T2=T2, T3=T3, T4=T4, T5=T5, candidate=bool(T1 and T2 and T3 and T4 and T5))
    print("\n8. THE BAR -- the weighted book")
    print(f"    T1 [P2] floors reproduce                     : {T1}")
    print(f"    T2 net (PUB + borrow) > 0 by 2 SE           : {T2}   ({mn:+.3f} ± {se_n:.3f}, {mn/se_n:+.1f} SE)")
    print(f"    T3 gross > state-matched random p95          : {T3}   (margin {q['margin_se']:+.1f} SE)")
    print(f"    T4 non-quarterly: gross > 2 SE and > its p95 : {T4}   (book margin {res['calendar']['weighted_nonq']['margin_se']:+.1f} SE)")
    print(f"    T5 gross > time-rotation p95                 : {T5}   (margin {res['rotation']['margin_se']:+.1f} SE)")
    print(f"    CANDIDATE for the holdout reads: {res['bar']['candidate']}")
    C = res["components"]; cb = res["combined"]["150"]
    wg = sum(COMP[k][2] * C[k]["gross"] for k in COMP) / WSUM; wn = sum(COMP[k][2] * C[k]["net_PUB"] for k in COMP) / WSUM; wc = sum(COMP[k][2] * C[k]["two_c"]["PUB"] for k in COMP) / WSUM
    print("\n9. PREDICTIONS")
    print(f"    X-a per trade A +38±3 B +50±3 C +32±3 D +19±3; weighted +38..+40 : {C['A']['gross']:+.1f} {C['B']['gross']:+.1f} {C['C']['gross']:+.1f} {C['D']['gross']:+.1f}; weighted {wg:+.1f}")
    print(f"    X-b 2c PUB 28-40, PB 15-25; borrow 2-8; weighted net PUB 0..+12 : PUB {wc:.1f}, PB {sum(COMP[k][2]*C[k]['two_c']['PB'] for k in COMP)/WSUM:.1f}; borrow B {C['B']['borrow']:.1f} D {C['D']['borrow']:.1f}; net {wn:+.1f}")
    print(f"    X-c state-matched weighted gross +18..+24/trade; increment +14..+22 : ctrl p50 book {q['p50']:+.3f}/bar; per-trade increments " + " ".join(f"{k}+{res['controls']['per_trade'][k]['increment']:.0f}" for k in COMP))
    print(f"    X-d quarterly +20..+40 over the rest; rest > 2 SE           : " + "  ".join(f"{k} {res['calendar'][k]['q_gross']-res['calendar'][k]['n_gross']:+.0f}" for k in COMP) + f"; T4 {T4}")
    print(f"    X-e rotation p95 < +10 per trade-equivalent                 : p95 {p95r:+.3f}/bar")
    print(f"    X-f 150-slot: util 85-95%, gross/bar +1.5..+2.2, net2 inside ±0.5 : util {100*cb['util']:.0f}%, gross {cb['gross_bp']:+.2f}, net2 {cb['net2_bp']:+.2f}")
    print(f"    X-g E: A, C with ret20_lo +10..+20 above without           : A {res['E']['A']['with_gross']-res['E']['A']['without_gross']:+.1f}  C {res['E']['C']['with_gross']-res['E']['C']['without_gross']:+.1f}")
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min   (mining fixture only; no holdout read)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    if a.run:
        run()

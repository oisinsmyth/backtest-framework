"""D440 stage 2 -- B: the high-priced short after a volume shock, under two cost lines. Spec committed in ba9131f BEFORE this file.
In-sample; no holdout.

    uv run python -u scripts/run_d440_stage2_B.py --run
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
R37 = _load("d437", "run_d437_stage1.py"); R38 = _load("d438", "run_d438_cost_axes.py")
OUT = REPO / "data" / "d440_stage2_B.json"
CAPTURE, CHASE_BP = 0.66, 9.0                 # D439: net capture of the modelled half-spread; chase per order (bp)
CAPS = (20, 40); N_DRAW = 100; SEED = 440; SIDE = 1


def passive_per_trade(tb_cell):
    return tb_cell["two_c_PUB"] * (1 - CAPTURE) + CHASE_BP + tb_cell["borrow"]


def book_lines(r, c):
    """Per-bar gross series (bp, hedged, idle = 0) and the two cost constants per bar."""
    g = np.nan_to_num(np.asarray(r["book_dep_x"], float)) * 1e4
    turn = c["turnover"]; crossed = c["dep_cost2"] + c["borrow"] * turn
    passive = c["dep_cost2"] * (1 - CAPTURE) + CHASE_BP * turn + c["borrow"] * turn
    return g, crossed, passive


def run():
    t0 = time.time()
    print("D440 STAGE 2 -- B: the high-priced short after a volume shock, two cost lines\n      the bar was committed in ba9131f BEFORE this ran; mining fixture only; no holdout\n")
    PREP = _load("d348p", "d348_prep.py"); V59 = _load("d359r", "run_d359_loser_rally_short.py")
    P = PREP.prep(need_grids=True); T, N = P["T"], P["n"]; elig = np.asarray(P["elig"]); dates = np.array([str(x)[:10] for x in P["dates"]]); yr = np.array([int(d[:4]) for d in dates])
    R38.SC = np.full((T, N), 50.0); SC = R38.SC; idx = A92.eligible_index(elig)
    mk = A92.draw_mask(np.random.default_rng(A92.SEED), idx, (T, N), 2_000); r1 = V59.run_mirror(P, mk, SC, "cap", 20); m1, c1 = A92.score_once(V59, P, mk, 20, "long", SC)
    assert abs(m1 - float(V59.V47.pnl_bp(r1).mean())) < 1e-12 and c1 == len(r1["trades"]), "[K]"
    st = A35.state_pools_unshifted(P, elig); vp, F = A34.volume_pools_unshifted(P, elig)
    ev = A35.shift(st["price_hi"] & vp["rv_x3"], elig); assert int(ev.sum()) == 12597, "[F] not D436's B"
    pool = A35.shift(st["price_hi"] & ~vp["rv_x3"] & elig, elig)
    HS = np.asarray(P["HALF"]["PUB"], float); hs_prev = np.full_like(HS, np.nan); hs_prev[1:] = HS[:-1]
    d38 = json.load(open(REPO / "data" / "d438_cost_axes.json")); cuts = d38["cuts"]["B"]
    x3 = A35.shift(vp["rv_x3"], elig); quarterly = np.zeros_like(x3)
    for j in range(N):
        d = np.flatnonzero(x3[:, j])
        if d.size > 1:
            sp = np.diff(d); quarterly[d[1:][(sp >= 58) & (sp <= 68)], j] = True
    E = A35.shift(st["ret20_lo"], elig)
    rng = np.random.default_rng(SEED); res = dict(cap={}, splits={}, bar={})
    print("  [K] kernel probe;  [F] events == D436's B (12,597);  D438's spread cuts and D437's calendar flag attached\n")

    for cap in CAPS:
        r, pnl, c = R38.cell(V59, P, elig, ev, SIDE, cap); c["passive_per_trade"] = passive_per_trade(c); c["net_passive"] = c["gross"] - c["passive_per_trade"]; c["conc"] = R38.conc(r, pnl, P, yr)
        if cap == 20:
            assert abs(c["gross"] - d38["cap"]["B|20"]["gross"]) < 1e-9, "[P2] cap-20 gross != D438's B cell"
        ctl = R38.control(V59, P, rng, ev, pool, SIDE, cap, T); c["control"] = ctl; c["increment"] = c["gross"] - ctl["p50"]; c["beats_p95"] = bool(c["gross"] > ctl["p95"])
        g, crossed, passive = book_lines(r, c); d0 = int(min(t[1] for t in r["trades"])); gs = g[d0:]; ds = dates[d0:]
        se_g, mg = R37.block_boot(gs, ds); nc, npv = gs - crossed, gs - passive
        half = d0 + (T - d0) // 2; era2 = np.arange(d0, T) >= half
        se2, m2 = R37.block_boot(npv[era2], ds[era2]); se1, m1_ = R37.block_boot(npv[~era2], ds[~era2])
        # rotation of the book gross
        rot = []
        for d in range(N_DRAW):
            rr = V59.simulate(P, R37.rotate(rng, ev, elig), SC, "cap", cap, SIDE); rot.append(float((np.nan_to_num(np.asarray(rr["book_dep_x"], float)) * 1e4)[d0:].mean()))
        rot = np.array(rot); p95r = float(np.quantile(rot, .95)); ser = float(rot.std(ddof=1) / np.sqrt(N_DRAW))
        ys = yr[d0:]
        res["cap"][str(cap)] = dict(per_trade=c, book=dict(gross=mg, gross_se=se_g, cost_crossed=crossed, cost_passive=passive, net_crossed=float(mg - crossed), net_passive=float(mg - passive), net_se=se_g,
                                                          sharpe_crossed=float(nc.mean() / nc.std(ddof=1) * np.sqrt(252)), sharpe_passive=float(npv.mean() / npv.std(ddof=1) * np.sqrt(252)),
                                                          era1_passive=m1_, era1_se=se1, era2_passive=m2, era2_se=se2, era2_start=dates[half],
                                                          by_year_passive={str(y): float(npv[ys == y].mean()) for y in range(2010, 2027) if (ys == y).any()}),
                                    rotation=dict(p50=float(np.median(rot)), p95=p95r, se=ser, margin_se=float((mg - p95r) / ser), passes=bool(mg > p95r and (mg - p95r) >= 2 * ser)))
        b = res["cap"][str(cap)]["book"]; cc = c["conc"]
        print(f"CAP {cap}")
        print(f"  per trade: n {c['trades']:,}  gross {c['gross']:+.2f} ± {c['se']:.1f}  median {c['median']:+.2f}  2c PUB {c['two_c_PUB']:.1f}  borrow {c['borrow']:.1f}   CROSSED net {c['net_PUB']:+.2f}   PASSIVE cost {c['passive_per_trade']:.1f} net {c['net_passive']:+.2f}")
        print(f"  increment over state-matched: {c['increment']:+.2f} (ctrl p50 {ctl['p50']:+.2f} p95 {ctl['p95']:+.2f} ±{ctl['se']:.2f}) {'> p95' if c['beats_p95'] else '<= p95'}")
        print(f"  book: gross {mg:+.3f} ± {se_g:.3f}/bar   crossed cost {crossed:.3f} -> net {mg-crossed:+.3f} ({(mg-crossed)/se_g:+.1f} SE)  Sharpe {b['sharpe_crossed']:+.2f}   |   passive cost {passive:.3f} -> net {mg-passive:+.3f} ({(mg-passive)/se_g:+.1f} SE)  Sharpe {b['sharpe_passive']:+.2f}")
        print(f"  passive net by era: era1 {m1_:+.3f} ± {se1:.3f}   era2 (from {dates[half]}) {m2:+.3f} ± {se2:.3f} ({m2/se2:+.1f} SE)   by year: " + " ".join(f"{y}:{v:+.1f}" for y, v in b["by_year_passive"].items()))
        print(f"  rotation: book gross {mg:+.3f} vs p95 {p95r:+.3f} (±{ser:.3f}) margin {(mg-p95r)/ser:+.1f} SE;   concentration: names to half {cc['to_half']}, top-1% share {cc['top1_share']:.0f}%, years+ {cc['years_pos']}/{cc['years']}\n", flush=True)

    print("SPLITS at cap 20 (per trade, both nets)")
    for lab, m in (("spread narrow", ev & np.isfinite(hs_prev) & (hs_prev <= cuts[0])), ("spread mid", ev & (hs_prev > cuts[0]) & (hs_prev <= cuts[1])), ("spread wide", ev & (hs_prev > cuts[1])),
                   ("on cadence", ev & quarterly), ("off cadence", ev & ~quarterly), ("ret20_lo", ev & E), ("not ret20_lo", ev & ~E)):
        r, pnl, c = R38.cell(V59, P, elig, m, SIDE, 20); c["net_passive"] = c["gross"] - passive_per_trade(c); res["splits"][lab] = c
        print(f"  {lab:14s} n {c['trades']:6,}  gross {c['gross']:+7.2f} ± {c['se']:.1f}  2c {c['two_c_PUB']:5.1f}  crossed net {c['net_PUB']:+7.2f}   passive net {c['net_passive']:+7.2f}")

    c20 = res["cap"]["20"]; b20 = c20["book"]; pt = c20["per_trade"]
    T1 = bool(pt["beats_p95"] and (pt["gross"] - pt["control"]["p95"]) >= 2 * pt["control"]["se"]); T2 = bool(b20["net_crossed"] > 0 and b20["net_crossed"] / b20["net_se"] >= 2)
    T3 = bool(b20["net_passive"] > 0 and b20["net_passive"] / b20["net_se"] >= 2); T4 = bool(b20["era2_passive"] > 0 and b20["era2_passive"] / b20["era2_se"] >= 2); T5 = bool(c20["rotation"]["passes"])
    res["bar"] = dict(T1=T1, T2=T2, T3=T3, T4=T4, T5=T5, candidate=bool(T1 and T3 and T4 and T5))
    print("\nTHE BAR (cap 20)")
    print(f"  T1 increment > state-matched p95 by 2 SE : {T1}   ({pt['gross']:+.2f} vs p95 {pt['control']['p95']:+.2f} ± {pt['control']['se']:.2f})")
    print(f"  T2 crossed net > 0 by 2 SE (reported)    : {T2}   ({b20['net_crossed']:+.3f} ± {b20['net_se']:.3f})")
    print(f"  T3 passive net > 0 by 2 SE               : {T3}   ({b20['net_passive']:+.3f} ± {b20['net_se']:.3f}, {b20['net_passive']/b20['net_se']:+.1f} SE)")
    print(f"  T4 era-2 passive net > 0 by 2 SE          : {T4}   ({b20['era2_passive']:+.3f} ± {b20['era2_se']:.3f}, {b20['era2_passive']/b20['era2_se']:+.1f} SE)")
    print(f"  T5 gross > rotation p95                  : {T5}   (margin {c20['rotation']['margin_se']:+.1f} SE)")
    print(f"  CANDIDATE for the holdouts (T1 & T3 & T4 & T5): {res['bar']['candidate']}   -- resting on D439's passive-fill assumption, as declared")
    c40 = res["cap"]["40"]; S = res["splits"]
    print("\nPREDICTIONS")
    print(f"  X-a cap 20: gross +38.8, crossed -18±3, passive +7±3; cap 40: +68.9 / +7 / +37 : {pt['gross']:+.1f} / {pt['net_PUB']:+.1f} / {pt['net_passive']:+.1f};  cap 40 {c40['per_trade']['gross']:+.1f} / {c40['per_trade']['net_PUB']:+.1f} / {c40['per_trade']['net_passive']:+.1f}")
    print(f"  X-b book cap 20: gross +2.24, crossed -0.4±0.6, passive +0.6±0.6; cap 40 passive +1.0±0.6 : gross {b20['gross']:+.2f}, crossed {b20['net_crossed']:+.2f}, passive {b20['net_passive']:+.2f} ± {b20['net_se']:.2f};  cap 40 passive {c40['book']['net_passive']:+.2f} ± {c40['book']['net_se']:.2f}")
    print(f"  X-c T1, T5 pass                                   : {T1}, {T5}")
    print(f"  X-d era 2 passive +0.8..+1.5, near 2 SE           : {b20['era2_passive']:+.2f} ± {b20['era2_se']:.2f}")
    print(f"  X-e wide tercile passive net +40..+60; narrow negative under both : wide {S['spread wide']['net_passive']:+.1f}; narrow crossed {S['spread narrow']['net_PUB']:+.1f} passive {S['spread narrow']['net_passive']:+.1f}")
    print(f"  X-f cadence flat (+41 vs +38); names to half 16-20; top-1% ~100%  : on {S['on cadence']['gross']:+.1f} off {S['off cadence']['gross']:+.1f}; {pt['conc']['to_half']} names; top-1% {pt['conc']['top1_share']:.0f}%")
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min   (no holdout read)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); a = ap.parse_args()
    if a.run:
        run()

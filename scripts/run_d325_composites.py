"""D325 -- composites of the new leaders: synergy, or repair of a weak primary?

    uv run python scripts/run_d325_composites.py --selftest
    uv run python scripts/run_d325_composites.py [--draws 100]

PRE-REGISTERED AT `7199dac`, committed before this file existed (R8).

NUMBERS HERE ARE D323's CORRECTED ONES. Its `rank_single` shorted the LEAST
extreme names of its own gate; the fix and the re-run are at `903766d`, and the
set below was amended at `fe2e500` because `rev_21` fell from 2nd to 9th.

hist_L ALONE scores +0.293 at the operating point, 7th of 13, while the confluence
built ON hist_L scores +0.549 -- a composite premium of +0.256, larger than the
spread between the top four singles, larger than dv28, larger than anything the
width work produced. No composite of the new leaders has been built.

TWO HYPOTHESES PREDICTING OPPOSITE THINGS. SYNERGY says averaging quasi-independent
signals cancels noise, so C4 -- the three strong singles together -- should be the
best book here. REPAIR says hist_L is a weak primary and the pair rescues it, so
the premium measures how bad the primary was and a composite on a STRONG primary
shows little. D324 already found the confluence puts 51.5% of its P&L in the
cheapest tercile where rsi alone puts 89.4%, so the composite DILUTES its
components -- evidence for repair. Q3 enters repair as the load-bearing
prediction, against the study.

AND THE LEADERBOARD ALREADY LEANS THAT WAY: the incumbent is a WEAK primary
carrying two STRONG pair members -- hist_L 7th at +0.293 while macd_hist (+0.482)
and rsi (+0.585) are both top four. THE DECISION THIS INFORMS is not which
composite is best but whether the composite construction should survive at all:
retrace_leg ALONE already scores +0.625 against the incumbent's +0.549, so under
repair the right move is to drop the confluence rather than rebuild it.

THE COMPOSITE CONSTRUCTION IS D295's `build_inputs`, COPIED NOT REIMPLEMENTED: a
primary selects the 25-name gate, the pair re-ranks inside it by mean percentile,
low is best on the long leg and high on the short. Assertion [1b] is what makes
the study readable -- a composite whose pair is (primary, primary) must reproduce
that primary's SINGLE-signal book bit-identically, because the mean percentile of
a signal with itself is its own percentile. If that fails, the composite and
single paths are not comparable and D323's +0.287 is not a real number.

NET SHARPE IS PRIMARY AND D324's TWO COMPOSITION STATISTICS ARE CO-PRIMARY. A
composite that wins on Sharpe while pushing the low-price share from 51.5% toward
89.4% has not improved the book, and the win condition was declared before the
numbers: beat the incumbent on net Sharpe AND do not worsen the low-price share.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


G22 = _load("d322", "d322_four_group_report.py")
Y = _load("d323", "run_d323_shortlist_at_operating_point.py")
W, D, M, SP, R, X = G22.W, G22.D, G22.M, G22.SP, Y.R, G22.X
N_BASE = Y.N_BASE

DEPTH = 2
KS = (10, 40)
# THE AMENDED SET (`fe2e500`). `rev_21` fell from 2nd to 9th once D323's
# short-leg defect was fixed, so it is replaced by `skew_63` -- MECHANICALLY, one
# name for one name, every structural role unchanged. The corrected top four are
# retrace_leg +0.625, rsi +0.585, macd_hist +0.482, skew_63 +0.467, against the
# incumbent's +0.549 and hist_L alone at +0.293.
COMPOSITES = {
    "C0_incumbent":    ("hist_L",      ("macd_hist", "rsi")),
    "C1_retrace_pair": ("retrace_leg", ("macd_hist", "rsi")),
    "C2_skew_pair":    ("skew_63",     ("macd_hist", "rsi")),
    "C3_histL_strong": ("hist_L",      ("retrace_leg", "skew_63")),
    "C4_all_strong":   ("retrace_leg", ("skew_63", "rsi")),
    "C5_rsi_primary":  ("rsi",         ("retrace_leg", "skew_63")),
}
SINGLES = ("hist_L", "retrace_leg", "skew_63", "rsi", "macd_hist")
ANN, SEED = 252.0, 20260904
OUT = REPO / "data" / "d325_composites.json"


def rank_composite(z, base, primary, pair, n, T):
    """(2, T, n) rank array. D295's `build_inputs`, copied verbatim in shape.

    The primary supplies the gate; the pair re-ranks inside it by MEAN
    PERCENTILE, low best on the long leg and high on the short -- the convention
    `op_meanrank` uses, so the selected set matches.
    """
    order_a, cnt_a, _ = R.ranked(z[primary], base)
    plan = R.LegPlan(order_a, cnt_a, N_BASE, T)
    pc = {}
    for b in pair:
        _, cb, pb = R.ranked(z[b], base)
        pc[b] = (R.pct_at(pb, cb, plan.lo, plan.cols),
                 R.pct_at(pb, cb, plan.hi, plan.cols))
    bc = np.broadcast_to(plan.cols[None, :], plan.lo.shape)
    out = []
    for si, (side, rows) in enumerate((("lo", plan.lo), ("hi", plan.hi))):
        a1, a2 = pc[pair[0]][si], pc[pair[1]][si]
        avg = (a1 + a2) / 2.0
        v = np.where(np.isnan(avg), np.inf, avg if side == "lo" else -avg)
        ordr = np.argsort(v, axis=0, kind="stable")
        pos = np.empty(ordr.shape, dtype=np.int32)
        np.put_along_axis(pos, ordr,
                          np.arange(avg.shape[0], dtype=np.int32)[:, None], axis=0)
        rk = np.full((n, T), n, dtype=np.int32)
        rk[rows.ravel(), bc.ravel()] = pos.ravel()
        out.append(rk)
    return np.ascontiguousarray(np.stack(out).transpose(0, 2, 1))


def score(A, rankT, finT, k, G4, r1T, years, dead, CLOSE, HALF):
    W.BASE_HOLD = k
    res = W.simulate(A, Y.gate_from(rankT, finT), DEPTH, True)
    if not res["trades"]:
        return None
    c = G22.costed(res, G4)
    contrib = G22.contributions(res, r1T)
    g1 = G22.group1(res, c, contrib, r1T)
    g3 = G22.group3(res, contrib, c, years, dead, CLOSE, HALF)
    return dict(cost=c, group1=g1, group3=g3, group2=G22.group2(res),
                sharpe_net=g1["sharpe_net"], net_bp=g1["net_bp_bar"],
                names_to_half=g3["names_to_half_pnl"],
                low_price_share=g3["price_low"]["share_pnl"],
                trades=G22.group2(res)["n"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=100)
    a = ap.parse_args()
    t0 = time.time()

    print("D325  composites of the new leaders")
    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T = np.asarray(A["r1T"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF = np.ascontiguousarray(
        (SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel.closes.T)
    VOL = np.full(CLOSE.shape, np.nan)
    sym = {s: i for i, s in enumerate(panel.symbols)}
    pos = {d: i for i, d in enumerate(panel.dates)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                VOL[t, i] = st.bar.volume
    finT = np.asarray(A["finT"])
    G4 = (HALF, CLOSE, X.roll_mean_T(CLOSE * VOL), finT)
    years = np.array([int(d[:4]) for d in panel.dates])
    meta = json.loads(G22.META.read_text())["symbols"]
    dead = np.array([bool(meta.get(s, {}).get("delistingDate"))
                     for s in panel.symbols])
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    d323 = json.loads((REPO / "data" / "d323_shortlist.json").read_text())
    print(f"  panel {finT.shape} ({time.time() - t0:.0f}s)")

    # ---- assertions -------------------------------------------------------
    print("\nASSERTIONS")
    # 1. C0 reproduces D323's incumbent cells.
    rk0 = rank_composite(z, base, *COMPOSITES["C0_incumbent"], n, T)
    worst = 0.0
    for k in KS:
        got = score(A, rk0, finT, k, G4, r1T, years, dead, CLOSE, HALF)
        ref = d323["incumbent"][f"k{k}/dv0"]
        worst = max(worst, abs(got["cost"]["gross_bp"] - ref["gross_bp"]))
    assert worst < 1e-9, f"[1] C0 differs from D323's incumbent by {worst:.2e} bp"
    print(f"    [1] C0 reproduces D323's incumbent at k=10 and k=40 to "
          f"{worst:.1e} bp -- the composite path is D293's")

    # 1b. THE DEGENERATE COMPOSITE. pair = (primary, primary) must reproduce the
    #     primary's SINGLE-signal book bit-identically, because the mean
    #     percentile of a signal with itself is its own percentile. If this
    #     fails, composites and singles are not comparable and D323's +0.287
    #     premium is not a real number.
    worstd = 0.0
    for s in SINGLES:
        deg = rank_composite(z, base, s, (s, s), n, T)
        sing = Y.rank_single(z, base, s, n, T)
        gd = Y.gate_from(deg, finT)
        gs = Y.gate_from(sing, finT)
        W.BASE_HOLD = 10
        rd = W.simulate(A, gd, DEPTH, True)
        rs = W.simulate(A, gs, DEPTH, True)
        d = abs(float(np.nanmean(rd["book"][rd["mask"]]))
                - float(np.nanmean(rs["book"][rs["mask"]]))) * 1e4
        worstd = max(worstd, d)
    assert worstd < 1e-9, \
        f"[1b] a degenerate composite differs from its single by {worstd:.2e} bp"
    print(f"    [1b] a composite with pair=(primary,primary) reproduces that "
          f"primary's SINGLE book to {worstd:.1e} bp, for all 4 singles --\n"
          f"         composites and singles ARE comparable")

    # 2. CAUSALITY.
    rot = np.roll(rk0, 501, axis=1)
    c1 = score(A, rk0, finT, 10, G4, r1T, years, dead, CLOSE, HALF)
    c2 = score(A, rot, finT, 10, G4, r1T, years, dead, CLOSE, HALF)
    assert abs(c1["cost"]["gross_bp"] - c2["cost"]["gross_bp"]) > 1e-9
    print(f"    [2] CAUSALITY: rotating rankT moves gross "
          f"{c1['cost']['gross_bp']:+.2f} -> {c2['cost']['gross_bp']:+.2f}")

    # S. SPREAD BASIS, in D324's corrected form.
    rts = []
    for nm, (p, pr) in COMPOSITES.items():
        c = score(A, rank_composite(z, base, p, pr, n, T), finT, 10, G4, r1T,
                  years, dead, CLOSE, HALF)
        rts.append(c["cost"]["round_trip"])
    spread = max(rts) / min(rts) - 1.0
    assert spread > 0.10, f"[S] the round trip barely moves ({spread:.1%})"
    print(f"    [S] the round trip spans {100 * spread:.0f}% across composites "
          f"({min(rts):.1f} to {max(rts):.1f}) -- data-dependent, not a constant")

    # C. COST DIMENSIONS.
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's")

    # 4. THE SELF-TEST MUST RAISE.
    broke = False
    try:
        W.BASE_HOLD = 10
        rr = W.simulate(A, Y.gate_from(rk0, finT), DEPTH, True)
        bk = rr["book"].copy()
        bk[np.flatnonzero(rr["mask"])[:200]] += 5e-4
        assert abs(float(np.nanmean(bk[rr["mask"]])) * 1e4
                   - d323["incumbent"]["k10/dv0"]["gross_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[4] reproduction passed a book handed free money"
    print("    [4] and [1] raises on a book handed free money inside the mask")

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # ---- the cells --------------------------------------------------------
    rng = np.random.default_rng(SEED)
    singles = {}
    for s in SINGLES:
        rk = Y.rank_single(z, base, s, n, T)
        for k in KS:
            singles[f"{s}/k{k}"] = score(A, rk, finT, k, G4, r1T, years, dead,
                                         CLOSE, HALF)
    cells, names, ps = {}, [], []
    print("\nTHE COMPOSITES   (net Sharpe primary; composition co-primary)")
    h = "%-17s %3s %8s %9s %9s %10s %11s %8s %8s"
    print(h % ("cell", "k", "trades", "net bp", "netSHRP", "vs C0",
               "NAMES/HALF", "LOW-PR", "p"))
    print("-" * 92)
    for nm, (p, pr) in COMPOSITES.items():
        rk = rank_composite(z, base, p, pr, n, T)
        for k in KS:
            c = score(A, rk, finT, k, G4, r1T, years, dead, CLOSE, HALF)
            nl = np.empty(a.draws)
            for i in range(a.draws):
                sh = int(rng.integers(126, T - 126))
                cn = score(A, np.roll(rk, sh, axis=1), finT, k, G4, r1T, years,
                           dead, CLOSE, HALF)
                nl[i] = cn["sharpe_net"] if cn else np.nan
            nl = nl[np.isfinite(nl)]
            pv = float((nl >= c["sharpe_net"]).sum() + 1) / (nl.size + 1)
            c.update(name=nm, primary=p, pair=list(pr), k=k, p=pv,
                     null_p50=float(np.median(nl)),
                     null_p95=float(np.quantile(nl, .95)))
            cells[f"{nm}/k{k}"] = c
            names.append(f"{nm}/k{k}"); ps.append(pv)
    c0 = {k: cells[f"C0_incumbent/k{k}"]["sharpe_net"] for k in KS}
    for nm in COMPOSITES:
        for k in KS:
            c = cells[f"{nm}/k{k}"]
            print(h % (nm, k, "%d" % c["trades"], "%+.2f" % c["net_bp"],
                       "%+.3f" % c["sharpe_net"],
                       "%+.3f" % (c["sharpe_net"] - c0[k]),
                       "%d" % c["names_to_half"],
                       "%.1f%%" % (100 * c["low_price_share"]), "%.4f" % c["p"]))

    print("\nTHE COMPOSITE PREMIUM -- each composite against its OWN primary alone")
    print("  %-17s %3s %11s %11s %11s" % ("cell", "k", "composite", "primary",
                                          "PREMIUM"))
    prem = {}
    for nm, (p, pr) in COMPOSITES.items():
        for k in KS:
            comp = cells[f"{nm}/k{k}"]["sharpe_net"]
            sole = singles[f"{p}/k{k}"]["sharpe_net"]
            prem[f"{nm}/k{k}"] = comp - sole
            print("  %-17s %3d %+11.3f %+11.3f %+11.3f"
                  % (nm, k, comp, sole, comp - sole))

    rej = Y.bh(np.array(ps), len(names))
    print(f"\n  BH q=0.10 at the nominal {len(names)}: "
          f"{', '.join(n2 for n2, r in zip(names, rej) if r) or 'NONE'}")

    # ---- predictions -------------------------------------------------------
    base_low = cells["C0_incumbent/k10"]["low_price_share"]
    q2 = all(v > 0 for v in prem.values())
    p0 = max(prem[f"C0_incumbent/k{k}"] for k in KS)
    q3 = all(prem[f"{nm}/k{k}"] < p0 for nm in
             ("C1_retrace_pair", "C2_skew_pair", "C4_all_strong",
              "C5_rsi_primary") for k in KS)
    q4 = not any(c["sharpe_net"] > c0[c["k"]]
                 and c["low_price_share"] <= base_low
                 for nm, c in cells.items() if not nm.startswith("C0"))
    best = max(cells.values(), key=lambda c: c["sharpe_net"])
    q5 = not best["name"].startswith("C4")
    q7 = any(cells[f"C3_histL_strong/k{k}"]["sharpe_net"] > c0[k] for k in KS)
    print("\nPREDICTIONS")
    for kk, v in (("Q2 every composite beats its own primary", q2),
                  ("Q3 the premium SHRINKS on stronger primaries  [load-bearing]", q3),
                  ("Q4 no composite wins on Sharpe AND holds the low-price share", q4),
                  ("Q5 C4 (all-strong) is NOT the best cell", q5),
                  ("Q7 C3 (strong pair on hist_L) beats C0", q7)):
        print(f"    {'CONFIRMED' if v else 'FALSIFIED'}  {kk}")
    print("    C0's own premium: %+.3f    best cell: %s at %+.3f"
          % (p0, best["name"], best["sharpe_net"]))

    OUT.write_text(json.dumps(dict(
        note="D325: six declared composites. Net Sharpe primary; names-to-half "
             "and low-price share co-primary (D324).",
        composites={k: [v[0], list(v[1])] for k, v in COMPOSITES.items()},
        cells=cells, singles=singles, premium=prem,
        bh_nominal=[n2 for n2, r in zip(names, rej) if r],
        predictions=dict(Q2=bool(q2), Q3=bool(q3), Q4=bool(q4), Q5=bool(q5),
                         Q7=bool(q7))), indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

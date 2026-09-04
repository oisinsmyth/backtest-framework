"""D326 -- both lenses: is the composite premium a SIGNAL effect or the slot cap?

    uv run python scripts/run_d326_both_lenses.py --selftest
    uv run python scripts/run_d326_both_lenses.py [--draws 50]

PRE-REGISTERED AT `eb3bb2a`, committed before this file existed (R8).

NONE OF D323, D324 OR D325 WAS SCORED PATH-INVARIANTLY. Every one calls simulate
with `slots` defaulting True, and the lens exists in that same function one
keyword away. Three consecutive SIGNAL studies scored entirely through the BOOK,
at the width where D306 measured contention drag at -19.12 -- the largest in its
table, and negative means the cap makes the book hold BETTER names.

SO THE QUESTION IS WHETHER D325's +0.370 COMPOSITE PREMIUM IS A SIGNAL EFFECT OR
THE CAP. If the composite is really re-ordering which two names a two-slot cap
keeps, removing the cap kills it. Q3 says it will and is load-bearing; Q7 puts the
same question to the -0.644 pair effect, which is the sharpest thing D325 found.

THE TWO LENSES ARE NEVER COMPARED ON THE SAME STATISTIC, and assertion [3]
enforces that IN CODE. The variant record carries bp/bar and never a per-trade
ranking figure; the invariant record carries per-trade and never bp/bar; the two
dicts share no key; and `rank_cells` RAISES if asked to rank one lens by the
other's statistic. FINDINGS section 10 has stated that rule since D304 and it has
never been mechanically enforced -- which is how three studies came to skip the
lens entirely.

PER-TRADE COST IS HALF THE PAIRED ROUND TRIP. `held_rt` is 4 x the median
half-spread, which is a PAIRED position -- two legs, two crossings each. A trade
in the ledger is ONE name, so it crosses twice: cost_per_trade = 2 x half = rt/2,
and that is the `2c` CLAUDE.md asks the mean move to be read against.
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


Q = _load("d325", "run_d325_composites.py")
G22, Y = Q.G22, Q.Y
W, D, M, SP, R, X = Q.W, Q.D, Q.M, Q.SP, Q.R, Q.X

DEPTH = 2
KS = (10, 20, 40)
SINGLES = ("hist_L", "retrace_leg", "skew_63", "rsi", "macd_hist")
ANN, SEED = 252.0, 20260904
OUT = REPO / "data" / "d326_both_lenses.json"

# THE STATISTIC EACH LENS MAY BE RANKED BY. Assertion [3] holds `rank_cells` to
# these, so FINDINGS section 10's rule cannot be broken by a later caller.
LEGAL = {"variant": {"net_bp_bar", "sharpe_net", "gross_bp_bar"},
         "invariant": {"net_per_trade", "median_per_trade", "t_per_trade",
                       "mean_over_2c"}}


def rank_cells(cells, lens, stat):
    """Rank one lens's cells. RAISES on the other lens's statistic."""
    if stat not in LEGAL[lens]:
        raise ValueError(
            f"[3] '{stat}' is not a {lens} statistic. FINDINGS section 10: the "
            f"two lenses are never compared on the same statistic. Legal here: "
            f"{sorted(LEGAL[lens])}")
    return sorted(cells.items(), key=lambda kv: -kv[1][stat])


def variant(A, rankT, finT, k, G4, r1T):
    """The slot-limited book. bp/bar, D318 costing, D321 [F] held turnover."""
    W.BASE_HOLD = k
    res = W.simulate(A, Y.gate_from(rankT, finT), DEPTH, True, slots=True)
    if not res["trades"]:
        return None, None
    c = G22.costed(res, G4)
    g1 = G22.group1(res, c, G22.contributions(res, r1T), r1T)
    return dict(net_bp_bar=g1["net_bp_bar"], sharpe_net=g1["sharpe_net"],
                gross_bp_bar=g1["gross_bp_bar"], round_trip=c["round_trip"],
                held_per_bar=g1["held_per_bar"], fill=g1["fill"],
                trades=len(res["trades"]), bars=g1["bars"]), res


def invariant(A, rankT, finT, k, HALF):
    """Every eligible name held, no cap. PER TRADE only -- no bp/bar exists here."""
    W.BASE_HOLD = k
    res = W.simulate(A, Y.gate_from(rankT, finT), DEPTH, True, slots=False)
    if not res["trades"]:
        return None, None
    pnl = np.array([t[3] for t in res["trades"]], float) * 1e4
    rt = W.held_rt(res, HALF)
    two_c = rt / 2.0                      # one name crosses twice, not four times
    net = float(pnl.mean()) - two_c
    sd = float(pnl.std(ddof=1))
    return dict(net_per_trade=net, gross_per_trade=float(pnl.mean()),
                median_per_trade=float(np.median(pnl)) - two_c,
                t_per_trade=float(pnl.mean() / (sd / np.sqrt(pnl.size)))
                if sd > 0 else 0.0,
                mean_over_2c=float(pnl.mean()) / two_c if two_c > 0 else 0.0,
                two_c=two_c, round_trip=rt, trades=int(pnl.size),
                held_per_bar=float(res["held"][res["mask"]].mean())), res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=50)
    a = ap.parse_args()
    t0 = time.time()

    print("D326  both lenses on the composite premium")
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
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    d325 = json.loads((REPO / "data" / "d325_composites.json").read_text())
    d323 = json.loads((REPO / "data" / "d323_shortlist.json").read_text())

    ranks = {}
    for nm, (p, pr) in Q.COMPOSITES.items():
        ranks[nm] = Q.rank_composite(z, base, p, pr, n, T)
    for s in SINGLES:
        ranks[s] = Y.rank_single(z, base, s, n, T)
    print(f"  {len(ranks)} constructions, k={KS} ({time.time() - t0:.0f}s)")

    # ---- assertions -------------------------------------------------------
    print("\nASSERTIONS")
    # 1. THE VARIANT LENS reproduces D325 and D323.
    worst = 0.0
    for nm in Q.COMPOSITES:
        for k in (10, 40):
            v, _ = variant(A, ranks[nm], finT, k, G4, r1T)
            worst = max(worst, abs(v["sharpe_net"]
                                   - d325["cells"][f"{nm}/k{k}"]["sharpe_net"]))
    for s in ("retrace_leg", "rsi"):
        for k in (10, 40):
            v, _ = variant(A, ranks[s], finT, k, G4, r1T)
            worst = max(worst, abs(v["net_bp_bar"]
                                   - d323["cells"][f"{s}/k{k}/dv0"]["net_bp"]))
    assert worst < 1e-9, f"[1] the variant lens differs by {worst:.2e}"
    print(f"    [1] the path-variant lens reproduces D325's composites and "
          f"D323's singles to {worst:.1e}")

    # 2. THE LENS BITES. A lens that changes nothing is not a lens.
    ts = time.time()
    for nm in ("C0_incumbent", "retrace_leg"):
        v, _ = variant(A, ranks[nm], finT, 10, G4, r1T)
        i, _ = invariant(A, ranks[nm], finT, 10, HALF)
        assert i["trades"] > v["trades"], \
            f"[2] {nm}: invariant takes {i['trades']} trades, variant {v['trades']}"
        assert i["held_per_bar"] > v["held_per_bar"], \
            f"[2] {nm}: invariant holds {i['held_per_bar']:.2f}, variant " \
            f"{v['held_per_bar']:.2f}"
    v, _ = variant(A, ranks["C0_incumbent"], finT, 10, G4, r1T)
    i, _ = invariant(A, ranks["C0_incumbent"], finT, 10, HALF)
    print(f"    [2] the lens BITES: C0 at k=10 holds {v['held_per_bar']:.2f} names "
          f"capped and {i['held_per_bar']:.2f} uncapped, {v['trades']:,} trades "
          f"against {i['trades']:,}")
    print(f"        (one invariant sim: {time.time() - ts:.1f}s)")

    # 3. THE LENSES ARE STRUCTURALLY SEPARATED, and the guard must RAISE.
    assert not (set(v) & set(i)) - {"round_trip", "trades", "held_per_bar"}, \
        f"[3] the two lens records share ranking fields: {set(v) & set(i)}"
    raised = False
    try:
        rank_cells({"x": i}, "invariant", "sharpe_net")
    except ValueError:
        raised = True
    assert raised, "[3] rank_cells accepted a variant statistic on the invariant lens"
    raised = False
    try:
        rank_cells({"x": v}, "variant", "net_per_trade")
    except ValueError:
        raised = True
    assert raised, "[3] rank_cells accepted an invariant statistic on the variant lens"
    print("    [3] the two records share no ranking field, and rank_cells RAISES "
          "in both directions -- FINDINGS section 10 enforced in code")

    # 4. CAUSALITY, on BOTH lenses.
    rot = np.roll(ranks["C0_incumbent"], 501, axis=1)
    v2, _ = variant(A, rot, finT, 10, G4, r1T)
    i2, _ = invariant(A, rot, finT, 10, HALF)
    assert abs(v2["net_bp_bar"] - v["net_bp_bar"]) > 1e-9
    assert abs(i2["net_per_trade"] - i["net_per_trade"]) > 1e-9
    print(f"    [4] CAUSALITY moves BOTH lenses: bp/bar "
          f"{v['net_bp_bar']:+.2f}->{v2['net_bp_bar']:+.2f}, per trade "
          f"{i['net_per_trade']:+.2f}->{i2['net_per_trade']:+.2f}")

    # S / C.
    uni = 4.0 * float(np.nanmedian(HALF[np.isfinite(HALF)]))
    rts = [variant(A, ranks[nm], finT, 10, G4, r1T)[0]["round_trip"]
           for nm in Q.COMPOSITES]
    assert max(rts) / min(rts) - 1 > 0.10, "[S] the round trip barely moves"
    d295 = json.loads((REPO / "data" / "d295_exits.json").read_text())
    b0 = [x for x in d295["rows"] if x["cell"] == "B0"][0]
    got = d295["round_trip_mean"] * b0["turnover"]
    assert abs(got - b0["cost_bar_mean"]) < 1e-9 * abs(b0["cost_bar_mean"])
    assert abs(got * 2.0 - b0["cost_bar_mean"]) > 1.0
    print(f"    [S] the round trip spans {100*(max(rts)/min(rts)-1):.0f}% across "
          f"composites, against a universe median of {uni:.1f}")
    print(f"    [C] cost dimensions: rt x turn = {got:.4f} reproduces d295's")

    # 5. THE SELF-TEST MUST RAISE.
    broke = False
    try:
        _, res = variant(A, ranks["C0_incumbent"], finT, 10, G4, r1T)
        bk = res["book"].copy()
        bk[np.flatnonzero(res["mask"])[:200]] += 5e-4
        assert abs(float(np.nanmean(bk[res["mask"]])) * 1e4
                   - d325["cells"]["C0_incumbent/k10"]["cost"]["gross_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[5] reproduction passed a book handed free money"
    print("    [5] and [1] raises on a book handed free money inside the mask")

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # ---- the cells --------------------------------------------------------
    rng = np.random.default_rng(SEED)
    V, I = {}, {}
    for nm, rk in ranks.items():
        for k in KS:
            v, _ = variant(A, rk, finT, k, G4, r1T)
            i, _ = invariant(A, rk, finT, k, HALF)
            if v is None or i is None:
                continue
            nl = np.empty(a.draws)
            for d in range(a.draws):
                sh = int(rng.integers(126, T - 126))
                iv, _ = invariant(A, np.roll(rk, sh, axis=1), finT, k, HALF)
                nl[d] = iv["net_per_trade"] if iv else np.nan
            nl = nl[np.isfinite(nl)]
            i["p"] = float((nl >= i["net_per_trade"]).sum() + 1) / (nl.size + 1)
            i["null_p50"] = float(np.median(nl))
            V[f"{nm}/k{k}"], I[f"{nm}/k{k}"] = v, i

    print("\nPATH-VARIANT -- the slot-limited book, bp/bar (never per trade)")
    print("%-20s %3s %10s %10s %9s %8s" % ("cell", "k", "net bp/bar", "netSHRP",
                                           "held/bar", "trades"))
    for nm, c in rank_cells(V, "variant", "sharpe_net"):
        print("%-20s %3d %+10.2f %+10.3f %9.2f %8d"
              % (nm.split("/")[0], c and int(nm.split("k")[-1]), c["net_bp_bar"],
                 c["sharpe_net"], c["held_per_bar"], c["trades"]))

    print("\nPATH-INVARIANT -- every eligible name, PER TRADE (never bp/bar)")
    print("%-20s %3s %11s %11s %9s %9s %8s %8s"
          % ("cell", "k", "net/trade", "median", "t", "mean/2c", "trades", "p"))
    for nm, c in rank_cells(I, "invariant", "net_per_trade"):
        print("%-20s %3d %+11.2f %+11.2f %+9.2f %9.2f %8d %8.4f"
              % (nm.split("/")[0], int(nm.split("k")[-1]), c["net_per_trade"],
                 c["median_per_trade"], c["t_per_trade"], c["mean_over_2c"],
                 c["trades"], c["p"]))

    print("\nOPPORTUNITY COST -- gross per trade, uncapped minus capped")
    print("  (negative = the CAP holds the better names, D306's drag)")
    print("  %-20s %3s %12s %12s %11s" % ("cell", "k", "uncapped", "capped", "DRAG"))
    drag = {}
    for nm in ranks:
        for k in KS:
            key = f"{nm}/k{k}"
            if key not in V:
                continue
            vg = V[key]["gross_bp_bar"]
            ig = I[key]["gross_per_trade"]
            # capped GROSS PER TRADE, computed here only for the drag column and
            # never used to rank the variant lens
            _, res = variant(A, ranks[nm], finT, k, G4, r1T)
            cg = float(np.mean([t[3] for t in res["trades"]])) * 1e4
            drag[key] = ig - cg
            print("  %-20s %3d %12.2f %12.2f %+11.2f" % (nm, k, ig, cg, ig - cg))

    # ---- predictions -------------------------------------------------------
    def best(d, pref, stat):
        c = {k: v for k, v in d.items() if k.startswith(pref)}
        return max(c.values(), key=lambda x: x[stat]) if c else None
    q3 = not (best(I, "C4_all_strong", "net_per_trade")["net_per_trade"]
              > best(I, "retrace_leg", "net_per_trade")["net_per_trade"])
    ordv = [nm for nm, _ in rank_cells(
        {k: v for k, v in V.items() if k.split("/")[0] in SINGLES},
        "variant", "sharpe_net")]
    ordi = [nm for nm, _ in rank_cells(
        {k: v for k, v in I.items() if k.split("/")[0] in SINGLES},
        "invariant", "net_per_trade")]
    rk_v = {nm: i for i, nm in enumerate(ordv)}
    rho = float(np.corrcoef([rk_v[nm] for nm in ordi],
                            np.arange(len(ordi)))[0, 1])
    q4 = rho < 0.7
    q5 = all(d < 0 for d in drag.values())
    q6 = all(V[f"retrace_leg/k20"]["sharpe_net"] >= V[f"{c}/k{k}"]["sharpe_net"]
             for c in Q.COMPOSITES for k in KS if f"{c}/k{k}" in V)
    gap_v = (V["C0_incumbent/k10"]["sharpe_net"]
             - V["C3_histL_strong/k10"]["sharpe_net"])
    gap_i = (I["C0_incumbent/k10"]["net_per_trade"]
             - I["C3_histL_strong/k10"]["net_per_trade"])
    print("\nPREDICTIONS")
    for kk, vv in (("Q3 C4 does NOT beat retrace_leg per trade  [load-bearing]", q3),
                   ("Q4 the lenses rank the singles differently (rho<0.7)", q4),
                   ("Q5 drag is negative everywhere -- the cap helps", q5),
                   ("Q6 retrace_leg k=20 beats every composite, path-variant", q6)):
        print(f"    {'CONFIRMED' if vv else 'FALSIFIED'}  {kk}")
    print("    Q4 rho = %+.3f" % rho)
    print("    Q7 the pair effect: %+.3f netSHRP in the book, %+.2f bp per trade"
          % (gap_v, gap_i))

    OUT.write_text(json.dumps(dict(
        note="D326: both lenses. Variant is bp/bar, invariant is per trade, and "
             "they are never compared on the same statistic (FINDINGS section 10).",
        variant=V, invariant=I, drag=drag, spearman_singles=rho,
        pair_effect=dict(variant_sharpe=gap_v, invariant_per_trade=gap_i),
        predictions=dict(Q3=bool(q3), Q4=bool(q4), Q5=bool(q5), Q6=bool(q6))),
        indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""D343 -- the re-listing clause: keep_v2 = keep_v1 AND isfinite(DV).

    uv run python scripts/run_d343_relisting_clause.py --selftest
    uv run python scripts/run_d343_relisting_clause.py [--draws 200]

rsi F0 k=20, retrace_leg F0 k=20 and the incumbent C0 k=5 under the D339 floor
(v1, identities to D341/D342) and the amended floor (v2), open fill, both lenses,
PB and PUB, GC+HTB. The trades the clause removes from each v1 ledger are named
with their P&L. The four groups on rsi v2, its top five with dollar-volume
percentile, and a 200-draw null with the number of distinct shifts stated.

ASSERTIONS [K][F0][R][V2][C][1][A][S][RQ][2][3][N][B][6] -- pre-reg section 5.
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


V42 = _load("d342r", "run_d342_rsi_candidate.py")     # main guarded; every alias
V35, V31, PA, V9 = V42.V35, V42.V31, V42.PA, V42.V9
V6, Y, W, D, M, SP, R, X = V42.V6, V42.Y, V42.W, V42.D, V42.M, V42.SP, V42.R, V42.X
G22, BR, V38, CEN, UF, FL = V42.G22, V42.BR, V42.V38, V42.CEN, V42.UF, V42.FL

DEPTH, N_BASE, ANN = 2, W.N_BASE, 252.0
NULL_SEED, LAG_SEED, N_LAG_BARS = [W.SEED, 343], 343, 200
CONVS = ("PB", "PUB")
OUT = REPO / "data" / "d343_relisting_clause.json"
D341_JSON = REPO / "data" / "d341_floor_and_open_fill.json"
D342_JSON = REPO / "data" / "d342_rsi_candidate.json"
D339_JSON = REPO / "data" / "d339_universe_floor.json"
SIGS = {"RSI": ("rsi", 20), "RL": ("retrace_leg", 20), "C0": (None, 5)}
gate_rows = V38.gate_rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    print("D343  the re-listing clause -- keep_v2 = keep_v1 AND isfinite(DV)")

    cache = Path(R.BC.CACHE)
    rp = REPO / "scripts" / "ragged_panel.py"
    assert cache.exists() and cache.stat().st_mtime > rp.stat().st_mtime, "[K]"
    assert str(np.load(cache, allow_pickle=False)["key"]) == R.BC.cache_key(M.B.FIXTURE), "[K] key"
    print("    [K] SCORE CACHE: key matches cache_key() with ragged_panel.py in the tuple; npz newer than the builder")

    D.build_cache(verbose=False)
    A = D.load_cache(mmap=True)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    panel, cleaned = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    g = M.P1.build_grids(panel, cleaned)
    HALF_PB = np.ascontiguousarray((SP.corwin_schultz(g["high"], g["low"], panel.live) / 2.0 * 1e4).T)
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
    DV = X.roll_mean_T(CLOSE * VOL)
    z = np.load(R.BC.CACHE, allow_pickle=False)
    base = z["warm"] & panel.live
    n, T = panel.live.shape
    cs = z["cs_spread"]
    HALF_PUB = np.full((T, n), np.nan)
    HALF_PUB[1:] = (cs[:, :-1] / 2.0 * 1e4).T
    HALF = {"PB": HALF_PB, "PUB": HALF_PUB}
    G4 = {cv: (HALF[cv], CLOSE, DV, finT) for cv in CONVS}
    last_live = PA.last_live_bar(finT)
    first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T for i in range(n)])
    years = np.array([int(d[:4]) for d in panel.dates])
    meta = json.loads(G22.META.read_text())["symbols"]
    dead = np.array([bool(meta.get(s, {}).get("delistingDate")) for s in panel.symbols])
    ev = json.loads(Path(M.B.EVENTS).read_text())
    d341 = json.loads(D341_JSON.read_text())["cells"]
    d342 = json.loads(D342_JSON.read_text())
    cen_c = float(json.loads(D339_JSON.read_text())["floor"]["census_c"])
    print(f"  panel {finT.shape}, {int(dead.sum())} delisted names ({el()})")

    dj = json.loads(V31.DEALS.read_text())
    fbars, drops, n_ok = V31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live, last_live,
                                         lambda f: f["form"] in V31.F0_FORMS)
    excl = V31.exclusion_mask(fbars, n, T, last_live)
    pct = 100.0 * (excl & finT.T).sum() / finT.sum()
    assert n_ok == V35.EXPECT_APPLIED and abs(pct - V35.EXPECT_PCT) < 0.02, f"[F0] {n_ok} / {pct:.3f}%"
    print(f"    [F0] F0 MASK: {n_ok:,} filings applied, {pct:.2f}% of live name-bars excluded")

    RAW = UF.raw_price_factor(panel, ev)
    assert np.array_equal(RAW, CEN.raw_factor(ev, panel.symbols, panel.dates)), "[R] factor"
    RAW_CLOSE = CLOSE * RAW
    keep1 = UF.floor_mask(RAW_CLOSE, DV, finT)
    keep2 = UF.floor_mask_v2(RAW_CLOSE, DV, finT)
    share1, share2 = UF.floor_share(keep1, finT), UF.floor_share(keep2, finT)
    assert abs(share1 - cen_c) < 1e-9, f"[R] v1 share {share1:.8f} != census {cen_c:.8f}"
    print(f"    [R] RAW PRICE and FLOOR v1: factor == census factor; v1 fails {100 * share1:.4f}% == census")
    # [V2]
    fin_dv = np.isfinite(DV)
    assert np.array_equal(keep2, keep1 & fin_dv), "[V2] keep_v2 != keep_v1 & isfinite(DV)"
    assert int((keep2 & ~keep1).sum()) == 0, "[V2] v2 passes something v1 fails"
    removed_share = float((keep1 & ~fin_dv & finT).sum() / finT.sum())
    assert abs((share2 - share1) - removed_share) < 1e-12, "[V2] share arithmetic"
    print(f"    [V2] keep_v2 == keep_v1 & isfinite(DV) exactly; v2 is a subset of v1; the clause removes a further "
          f"{100 * removed_share:.4f}% of live name-bars (v2 fails {100 * share2:.4f}%)")
    # [C] causality of the new clause: isfinite(DV[t]) depends only on bars <= t-1
    rng = np.random.default_rng(LAG_SEED)
    tb = rng.choice(np.arange(70, T), size=N_LAG_BARS, replace=False)
    for t in tb:
        C2, V2 = CLOSE.copy(), VOL.copy()
        C2[t:] *= 1.37
        V2[t:] *= 1.37
        DVp = X.roll_mean_T(C2 * V2)
        assert np.array_equal(np.isfinite(DVp[:t + 1]), fin_dv[:t + 1]), f"[C] bar {t}"
    print(f"    [C] CAUSALITY: perturbing every price and volume from bar t on leaves isfinite(DV) through t unchanged on "
          f"{N_LAG_BARS} sampled bars ({el()})")
    A2, fbmask, FBREP = FL.with_open_fill(A, panel, g)
    ocT, mkt_oc = A2["ocT"], A2["mkt_oc"]

    # ---- cells --------------------------------------------------------------------------------
    Q = V6.Q
    prim, pair = Q.COMPOSITES["C0_incumbent"]
    C0_KEYS = ("hist_L", "macd_hist", "rsi")

    def rank_of(nm, keep):
        sig, _k = SIGS[nm]
        if sig is None:
            zz = {kk: UF.apply_floor_replace(z[kk], keep) for kk in C0_KEYS}
            return Q.rank_composite(zz, base, prim, pair, n, T), None
        sc = UF.apply_floor_replace(np.where(excl, np.nan, z[sig]), keep)
        return Y.rank_single({sig: sc}, base, sig, n, T), sc

    def top_five(res, contrib, keep, kmax=5):
        trs = res["trades"]
        p = np.array([t[3] for t in trs])
        tot = float(p.sum())
        out = []
        for i in np.argsort(-p)[:kmax]:
            row, e0, age, pp, side = trs[i]
            out.append(dict(symbol=panel.symbols[row], side="long" if side == 0 else "short", entry=panel.dates[e0],
                            hold=int(age), pnl_bp=float(pp) * 1e4, share=float(pp / tot),
                            raw_px_prev=float(RAW_CLOSE[e0 - 1, row]), dv_pct_entry=CEN.dv_percentile(DV, finT, int(e0), int(row)),
                            dv_finite=bool(fin_dv[e0, row]), passes_keep=bool(keep[e0, row])))
        return out

    def run_cell(nm, keep, ver):
        rankT, sc = rank_of(nm, keep)
        gate = Y.gate_from(rankT, finT)
        W.BASE_HOLD = SIGS[nm][1]
        res_v = W.simulate(A2, gate, DEPTH, True, slots=True, fill="open")
        res_i = W.simulate(A2, gate, DEPTH, True, slots=False, fill="open")
        contrib = FL.contributions_fill(res_v, r1T, ocT)
        C = {cv: G22.costed(res_v, G4[cv]) for cv in CONVS}
        G1 = {cv: G22.group1(res_v, C[cv], contrib, r1T) for cv in CONVS}
        G2 = G22.group2(res_v)
        G3 = {cv: G22.group3(res_v, contrib, C[cv], years, dead, CLOSE, HALF[cv]) for cv in CONVS}
        LEGS = {cv: V9.per_leg(res_i, HALF[cv], CLOSE, r1T, mkt) for cv in CONVS}
        INV = {cv: V9.invariant_legcost(res_i, LEGS[cv]) for cv in CONVS}
        BV, _ = V38.borrow_block(res_v, C, INV, excl, CLOSE, T)
        BI, _ = V38.borrow_block(res_i, C, INV, excl, CLOSE, T)
        # trades whose entry cell fails keep_v2 (only meaningful on the v1 ledger)
        rem = [(panel.symbols[t[0]], panel.dates[t[1]], "long" if t[4] == 0 else "short", float(t[3]) * 1e4)
               for t in res_v["trades"] if not keep2[t[1], t[0]]]
        print(f"  {nm:3s} {ver}: fill {100 * C['PUB']['fill']:.1f}%, gross {C['PUB']['gross_bp']:+.2f}, PUB net {C['PUB']['net_bp']:+.2f}, "
              f"PB net {C['PB']['net_bp']:+.2f}, inv/trade PUB {INV['PUB']['net_per_trade']:+.1f}, {len(res_v['trades']):,} trades, "
              f"entries failing v2: {len(rem)} ({el()})")
        return dict(rankT=rankT, score=sc, gate=gate, res_v=res_v, res_i=res_i, contrib=contrib, C=C, G1=G1, G2=G2, G3=G3,
                    LEGS=LEGS, INV=INV, borrow=dict(variant=BV, invariant=BI), removed=rem, top5=top_five(res_v, contrib, keep))

    CELLS = {(nm, ver): run_cell(nm, kp, ver) for nm in SIGS for ver, kp in (("v1", keep1), ("v2", keep2))}

    # ---- assertions ----------------------------------------------------------------------------
    print("\nASSERTIONS")
    worst = 0.0
    for cv in CONVS:
        for nm, ref in (("RL", d341["RL/floor/open"]), ("C0", d341["C0/floor/open"])):
            c = CELLS[nm, "v1"]
            worst = max(worst, abs(c["C"][cv]["net_bp"] - ref["costed"][cv]["net_bp"]),
                        abs(c["C"][cv]["sharpe_net"] - ref["costed"][cv]["sharpe_net"]),
                        abs(c["INV"][cv]["net_per_trade"] - ref["invariant"][cv]["net_per_trade"]))
        c = CELLS["RSI", "v1"]
        worst = max(worst, abs(c["C"][cv]["net_bp"] - d342["group1"][cv]["net_bp_bar"]),
                    abs(c["C"][cv]["sharpe_net"] - d342["group1"][cv]["sharpe_net"]),
                    abs(c["INV"][cv]["net_per_trade"] - d342["invariant"][cv]["net_per_trade"]))
    assert worst < 1e-9, f"[1] {worst:.2e}"
    print(f"    [1] IDENTITY: the three v1 open-fill cells reproduce D341 (RL, C0) and D342 (rsi) to {worst:.1e}")

    RS2 = CELLS["RSI", "v2"]
    gate, sc = RS2["gate"], RS2["score"]
    rng = np.random.default_rng(LAG_SEED)
    nonempty = np.array([t for t in range(1, T) if gate_rows(gate, 0, t).size > 0])
    bars = rng.choice(nonempty, size=N_LAG_BARS, replace=False)
    n_unl = 0
    for t in bars:
        got = set(int(r) for r in gate_rows(gate, 0, int(t)))
        assert got == V38.rebuild_long_set(sc, base, finT, int(t), 1), f"[A] bar {t}"
        n_unl += V38.rebuild_long_set(sc, base, finT, int(t), 0) != got
    assert n_unl > N_LAG_BARS // 2, "[A]"
    print(f"    [A] LAG AUDIT: rsi v2's long gate rebuilt from the floored score at t-1 equals the gate on all {N_LAG_BARS} "
          f"sampled bars; the unlagged rebuild differs on {n_unl}")

    tr = RS2["res_v"]["trades"]
    pnl = np.array([t[3] for t in tr])
    rec = FL.pnl_recomputed_fill(tr, r1T, mkt, ocT, mkt_oc)
    worst_s = float(np.abs(rec - pnl).max())
    assert worst_s < 1e-12, f"[S] {worst_s:.2e}"
    ex = np.array([float((ocT[e0, row] - mkt_oc[e0]) + (r1T[e0 + 1:e0 + age, row] - mkt[e0 + 1:e0 + age]).sum())
                   for row, e0, age, _p, _s in tr])
    longs = np.array([t[4] == 0 for t in tr])
    assert (pnl[longs & (ex > 0)] > 0).all() and (pnl[~longs & (ex < 0)] > 0).all(), "[S]"
    print(f"    [S] SIGN IN MONEY: every rsi v2 trade equals the open-fill recomputation to {worst_s:.1e}; favourable paths pay positively")

    W.BASE_HOLD = 20
    res_c = W.simulate(A2, gate, DEPTH, True, slots=True, fill="open", accumulate="compound")
    assert [(t[0], t[1], t[2], t[4]) for t in tr] == [(t[0], t[1], t[2], t[4]) for t in res_c["trades"]], "[RQ]"
    pnl_c = np.array([t[3] for t in res_c["trades"]])
    assert not np.allclose(pnl, pnl_c) and abs(RS2["G1"]["PUB"]["trade_mean_bp"] - float(pnl.mean()) * 1e4) < 1e-9, "[RQ]"
    print(f"    [RQ] RIGHT QUANTITY: same {len(tr):,} entries under compound accumulation, {int((pnl != pnl_c).sum()):,} P&Ls differ; group 1 scores the summed ledger")

    res_v, contrib = RS2["res_v"], RS2["contrib"]
    resid = RS2["C"]["PUB"]["gross_bp"] - float(contrib.sum()) / RS2["C"]["PUB"]["bars"] * 1e4
    n_open = int(res_v["ent"].sum()) - len(tr)
    gap_bars, first, TT = G22.unattributed(res_v)
    assert 0 <= n_open <= 2 * DEPTH and first >= TT - 20 and abs(resid) < 1.0, f"[2] {n_open} {first} {resid}"
    broke = False
    try:
        _, f2, _ = G22.unattributed(res_v, [t for i, t in enumerate(tr) if i != len(tr) // 2])
        assert f2 >= TT - 20
    except AssertionError:
        broke = True
    assert broke, "[2]"
    print(f"    [2] RECONCILIATION: {len(tr):,} trades reconstruct gross to {resid:+.4f} bp; {n_open} open at T, none before bar {first}; rejects a ledger missing a trade")

    k1 = max(1, pnl.size // 100)
    broke = False
    try:
        _, kt, kb = G22.trim_sym(pnl, k1, k1 + 1)
        assert kt == kb
    except AssertionError:
        broke = True
    assert broke and RS2["G2"]["n_dropped_top"] == RS2["G2"]["n_dropped_bottom"], "[3]"
    print(f"    [3] the 1% trim is symmetric (k={k1}) and rejects a trim one deeper on the bottom")

    rot = Y.gate_from(np.roll(RS2["rankT"], 501, axis=1), finT)
    r_rot = W.simulate(A2, rot, DEPTH, True, fill="open")
    g_rot = float(r_rot["book"][r_rot["mask"]].mean()) * 1e4
    assert abs(g_rot - RS2["C"]["PUB"]["gross_bp"]) > 1e-9, "[N]"
    print(f"    [N] CAUSALITY: rotating the rank array by 501 bars moves gross {RS2['C']['PUB']['gross_bp']:+.2f} -> {g_rot:+.2f}")

    wb = max(c["borrow"][lens]["reconcile_worst"] for c in CELLS.values() for lens in ("variant", "invariant"))
    assert wb < 1e-9, f"[B] {wb:.2e}"
    for c in CELLS.values():
        for cv in CONVS:
            assert c["borrow"]["variant"]["gc_htb"][cv]["net_bp"] == c["C"][cv]["net_bp"], "[B]"
    print(f"    [B] BORROW: per bar x cnt1 == per trade to {wb:.1e} on all six cells; net_bp untouched")

    broke = False
    try:
        r0 = CELLS["RSI", "v1"]["res_v"]
        bk = r0["book"].copy()
        bk[np.flatnonzero(r0["mask"])[:200]] += 5e-4
        bad = G22.costed(dict(r0, book=bk), G4["PUB"])
        assert abs(bad["net_bp"] - d342["group1"]["PUB"]["net_bp_bar"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6]"
    print("    [6] and [1] raises on a book handed +5 bp on 200 masked bars")

    if a.selftest:
        print(f"\nOK  assertions pass  ({el()})")
        return 0

    # ---- what the clause removed ----------------------------------------------------------------------
    print("\n" + "=" * 100)
    print("THE CLAUSE -- per cell: v1 -> v2 PUB net bp/bar; the v1 trades whose entry fails v2")
    print("=" * 100)
    REM = {}
    for nm in SIGS:
        c1, c2 = CELLS[nm, "v1"], CELLS[nm, "v2"]
        rem = c1["removed"]
        pn = np.array([r[3] for r in rem]) if rem else np.zeros(0)
        REM[nm] = dict(n=len(rem), mean_bp=(float(pn.mean()) if pn.size else None), sum_bp=float(pn.sum()),
                       share_of_v1_pnl=(float(pn.sum() / (np.array([t[3] for t in c1["res_v"]["trades"]]).sum() * 1e4)) if pn.size else 0.0),
                       trades=rem)
        print("  %-3s PUB %+6.2f -> %+6.2f (PB %+6.2f -> %+6.2f); inv %+6.1f -> %+6.1f; trades %d -> %d; removed by the clause: %d trades, "
              "mean %+.0f bp, sum %+.0f bp = %.1f%% of the v1 ledger" % (
                  nm, c1["C"]["PUB"]["net_bp"], c2["C"]["PUB"]["net_bp"], c1["C"]["PB"]["net_bp"], c2["C"]["PB"]["net_bp"],
                  c1["INV"]["PUB"]["net_per_trade"], c2["INV"]["PUB"]["net_per_trade"], len(c1["res_v"]["trades"]), len(c2["res_v"]["trades"]),
                  REM[nm]["n"], REM[nm]["mean_bp"] or 0, REM[nm]["sum_bp"], 100 * REM[nm]["share_of_v1_pnl"]))
        for s_, d_, side_, p_ in sorted(rem, key=lambda r: -abs(r[3]))[:8]:
            print(f"        {s_:6s} {side_:5s} {d_}  {p_:+8.0f} bp")

    # ---- rsi v2: the four groups, headline -------------------------------------------------------------------
    g1, g2, g3, L, bv = RS2["G1"], RS2["G2"], RS2["G3"]["PUB"], RS2["LEGS"]["PUB"], RS2["borrow"]["variant"]
    print("\n" + "=" * 78)
    print("rsi under keep_v2 -- GROUP 1")
    print("=" * 78)
    print("  %-30s %12s %12s" % ("", "PB", "PUB"))
    for label, key, fn in (("gross bp/bar", "gross_bp_bar", "%+.2f"), ("cost bp/bar", "cost_bp_bar", "%.2f"), ("NET bp/bar", "net_bp_bar", "%+.2f"),
                           ("vol bp/bar", "vol_bp_bar", "%.1f"), ("NET Sharpe", "sharpe_net", "%+.3f"), ("gross t", "t_gross", "%+.2f"),
                           ("maxDD bp", "maxdd_bp", "%.0f"), ("held half-spread", "held_half_spread", "%.2f"), ("held price", "held_price", "$%.2f"),
                           ("2c", "two_c_bp", "%.2f"), ("mean move / 2c", "trade_mean_over_2c", "%.2fx"),
                           ("breakeven / measured", "breakeven_multiple", "%.2fx")):
        print("  %-30s %12s %12s" % (label, fn % g1["PB"][key], fn % g1["PUB"][key]))
    print("  after GC+HTB: PB %+.2f PUB %+.2f (borrow %.3f);  invariant PUB: long %+.1f, short %+.1f, both %+.1f" % (
        bv["gc_htb"]["PB"]["net_bp_borrow"], bv["gc_htb"]["PUB"]["net_bp_borrow"], bv["gc_htb"]["PUB"]["borrow_bp_bar"],
        L[0]["net"], L[1]["net"], RS2["INV"]["PUB"]["net_per_trade"]))
    print("GROUP 2 -- trades %d, mean %+.1f, MEDIAN %+.1f, win %.1f%%, payoff %.2f, skew %+.2f; trimmed %+.1f (2c %.1f); top 1%% %+.0f%%, bottom 1%% %+.0f%%" % (
        g2["n"], g2["mean_bp"], g2["median_bp"], 100 * g2["win_rate"], g2["payoff"], g2["skew"], g2["mean_trimmed_bp"], g1["PUB"]["two_c_bp"],
        100 * g2["top1_share"], 100 * g2["bottom1_share"]))
    print("GROUP 3 (PUB) -- names %d, to half %d, top 1/5/10 %.1f/%.1f/%.1f%%; years net+ %d of %d; dead %.1f%%; eras %.1f%% / %.1f%%; price LOW %.1f%%" % (
        g3["names"], g3["names_to_half_pnl"], 100 * g3["top1_name_share"], 100 * g3["top5_name_share"], 100 * g3["top10_name_share"],
        g3["years_profitable_net"], g3["years"], 100 * g3["dead"]["share_pnl"], 100 * g3["era_first_half"]["share_pnl"],
        100 * g3["era_second_half"]["share_pnl"], 100 * g3["price_low"]["share_pnl"]))
    print("  TOP FIVE (v2):")
    for t_ in RS2["top5"]:
        print("    %-6s %-5s %s hold %2d  %+8.0f bp (%4.1f%%)  raw px $%.2f  dv pct %s  dv finite %s" % (
            t_["symbol"], t_["side"], t_["entry"], t_["hold"], t_["pnl_bp"], 100 * t_["share"], t_["raw_px_prev"],
            ("%.2f" % t_["dv_pct_entry"]) if np.isfinite(t_["dv_pct_entry"]) else "NaN", t_["dv_finite"]))

    # ---- the null on rsi v2 ----------------------------------------------------------------------------------------
    ts = time.time()
    rng = np.random.default_rng(NULL_SEED)
    offs = rng.choice(np.arange(1, N_BASE), size=a.draws, replace=True)
    distinct = int(len(set(offs.tolist())))
    by_shift = {}
    for s_ in offs:
        s_ = int(s_)
        if s_ not in by_shift:
            r = W.simulate(A2, gate, DEPTH, True, shift=s_, fill="open")
            okm = r["mask"]
            b = r["book"][okm]
            by_shift[s_] = (float(b.mean()) * 1e4, float(b.mean() / b.std(ddof=1) * np.sqrt(ANN)),
                            {cv: G22.costed(r, G4[cv])["sharpe_net"] for cv in CONVS}, int(okm.sum()))
    draws = [by_shift[int(s_)] for s_ in offs if by_shift[int(s_)][3] >= 200]
    NG = np.array([d_[0] for d_ in draws]); NSG = np.array([d_[1] for d_ in draws])
    NSN = {cv: np.array([d_[2][cv] for d_ in draws]) for cv in CONVS}
    assert NG.size >= min(195, a.draws - 5), "[N] draws"
    C_ = RS2["C"]
    dv_ = {"gross_bp": [v[0] for v in by_shift.values()], "sharpe_gross": [v[1] for v in by_shift.values()],
           "sharpe_net_PB": [v[2]["PB"] for v in by_shift.values()], "sharpe_net_PUB": [v[2]["PUB"] for v in by_shift.values()]}
    scores = {"gross_bp": C_["PUB"]["gross_bp"], "sharpe_gross": C_["PUB"]["sharpe_gross"], "sharpe_net_PB": C_["PB"]["sharpe_net"],
              "sharpe_net_PUB": C_["PUB"]["sharpe_net"]}
    above = {k: int(sum(1 for x in dv_[k] if x < scores[k])) for k in dv_}
    NULL = dict(construction="rank rotation inside the 25-name gate, keep_v2, open fill", seed=NULL_SEED, draws=int(NG.size),
                distinct_shifts=distinct, above_k_of_distinct=above, gross_bp=G22.dist(NG, scores["gross_bp"]),
                sharpe_gross=G22.dist(NSG, scores["sharpe_gross"]), sharpe_net={cv: G22.dist(NSN[cv], C_[cv]["sharpe_net"]) for cv in CONVS})
    teeth = NULL["gross_bp"]["p95"] > 0
    print(f"\n    [N] {NG.size} of {a.draws} draws valid, {distinct} DISTINCT shifts of at most 24 ({time.time() - ts:.0f}s)")
    print("GROUP 4 -- THE NULL on rsi v2")
    print("  %-16s %10s %10s %10s %10s   %s" % ("statistic", "score", "p50", "p95", "max", "above k of distinct"))
    for lab, d_, key in (("gross bp/bar", NULL["gross_bp"], "gross_bp"), ("gross Sharpe", NULL["sharpe_gross"], "sharpe_gross"),
                         ("net Sharpe PB", NULL["sharpe_net"]["PB"], "sharpe_net_PB"), ("net Sharpe PUB", NULL["sharpe_net"]["PUB"], "sharpe_net_PUB")):
        print("  %-16s %10.3f %10.3f %10.3f %10.3f   %d of %d" % (lab, d_["score"], d_["p50"], d_["p95"], d_["max"], above[key], distinct))
    print(f"  the gross null has teeth (p95 > 0): {'yes' if teeth else 'NO -- R7 flag'}")

    # ---- predictions ------------------------------------------------------------------------------------------------
    nbis_in = any(panel.symbols[t[0]] == "NBIS" for t in tr)
    all_rem = [r for nm in SIGS for r in REM[nm]["trades"]]
    rem_mean = float(np.mean([r[3] for r in all_rem])) if all_rem else 0.0
    q = {}
    q["Q1"] = bool(removed_share < 0.015)
    q["Q2"] = bool(C_["PUB"]["gross_bp"] > NULL["gross_bp"]["p95"] and teeth and above["gross_bp"] >= 22 and not nbis_in)
    d_rsi = RS2["C"]["PUB"]["net_bp"] - CELLS["RSI", "v1"]["C"]["PUB"]["net_bp"]
    q["Q3"] = bool(d_rsi < 0 and d_rsi > -1.5)
    q["Q4"] = bool(abs(CELLS["RL", "v2"]["C"]["PUB"]["net_bp"] - 2.68) < 1.0 and abs(CELLS["C0", "v2"]["C"]["PUB"]["net_bp"] + 13.41) < 1.0)
    q["Q5"] = bool(rem_mean > 0)
    q["Q6"] = bool(all(np.isfinite(t_["dv_pct_entry"]) for nm in SIGS for t_ in CELLS[nm, "v2"]["top5"]))
    print("\nPREDICTIONS")
    print(f"  Q1 clause removes < 1.5% more of live name-bars: {'CONFIRMED' if q['Q1'] else 'FALSIFIED'} -- {100 * removed_share:.3f}% (v1 {100 * share1:.2f}% -> v2 {100 * share2:.2f}%)")
    print(f"  Q2 (LOAD-BEARING) rsi v2 above gross null p95, >= 22 of 24, NBIS gone: {'CONFIRMED' if q['Q2'] else 'FALSIFIED'} -- "
          f"{C_['PUB']['gross_bp']:+.2f} vs p95 {NULL['gross_bp']['p95']:+.2f} (max {NULL['gross_bp']['max']:+.2f}), above {above['gross_bp']} of {distinct}; NBIS in ledger: {nbis_in}")
    print(f"  Q3 rsi PUB net falls by < 1.5: {'CONFIRMED' if q['Q3'] else 'FALSIFIED'} -- {CELLS['RSI', 'v1']['C']['PUB']['net_bp']:+.2f} -> {RS2['C']['PUB']['net_bp']:+.2f} ({d_rsi:+.2f})")
    print(f"  Q4 RL within 1 of +2.68, C0 within 1 of -13.41: {'CONFIRMED' if q['Q4'] else 'FALSIFIED'} -- RL {CELLS['RL', 'v2']['C']['PUB']['net_bp']:+.2f}, C0 {CELLS['C0', 'v2']['C']['PUB']['net_bp']:+.2f}")
    print(f"  Q5 (against) removed trades' mean P&L > 0: {'CONFIRMED' if q['Q5'] else 'FALSIFIED'} -- {len(all_rem)} trades, mean {rem_mean:+.0f} bp")
    print(f"  Q6 no v2 top-five trade lacks a DV percentile: {'CONFIRMED' if q['Q6'] else 'FALSIFIED'}")

    def clean(o):
        if isinstance(o, dict):
            return {"/".join(k) if isinstance(k, tuple) else str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return None if not np.isfinite(o) else float(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        return o

    cells_out = {f"{nm}/{ver}": dict(costed=c["C"], group1=c["G1"], group2=c["G2"], group3=c["G3"],
                                    legs={cv: {str(s): c["LEGS"][cv][s] for s in (0, 1)} for cv in CONVS}, invariant=c["INV"],
                                    borrow=c["borrow"], top5=c["top5"], trades=len(c["res_v"]["trades"]))
                 for (nm, ver), c in CELLS.items()}
    out = dict(note="D343: keep_v2 = keep_v1 & isfinite(DV); rsi, retrace_leg, C0 under v1 (identities) and v2, open fill. "
                    "Nothing promoted; the declared universe is keep_v2 from here.",
               floor=dict(v1_share_live_fail=share1, v2_share_live_fail=share2, removed_share=removed_share, census_c=cen_c),
               cells=cells_out, removed=REM, null=NULL, teeth_gross=teeth, predictions=q, identity_worst=worst,
               reconciliation=dict(residual_bp=resid, open_positions=n_open, first_unattributed_bar=int(first)))
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({el()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

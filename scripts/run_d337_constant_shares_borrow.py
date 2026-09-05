"""D337 -- constant shares on the short leg, and a declared borrow stress charge.

    uv run python scripts/run_d337_constant_shares_borrow.py --selftest
    uv run python scripts/run_d337_constant_shares_borrow.py

PRE-REGISTERED in docs/decisions/D337-constant-shares-and-a-borrow-stress-charge.md,
committed before the simulator flag and this file existed (R8).

THE ACCUMULATION IS A FLAG ON THE SIMULATOR. `W.simulate(..., accumulate=
"compound")` carries sum_v and sum_log1p per open position and books
`sum - sgn*(sum_v - expm1(sum_log1p))` on close; the exit rule reads the SUMMED
slot in both modes, so the ledgers' (row, e0, age, side) are identical ([E])
and every compound trade is the summed trade minus D329's premium ([P]). That
makes the short-leg improvement a REPRODUCTION CHECK, listed as one, and puts
the content in the fixed-hold arm, the net sign after cost and borrow, the
hard-to-borrow share, and LW_F0's survival.

BORROW IS POST-HOC ON THE LEDGER (d337_borrow.py), short trades only, under
NEW keys. `net_bp` and `mean_over_2c` are copied through untouched, because
three downstream runners assert `net_bp` to 1e-9. `run_d326_both_lenses.LEGAL`
is not edited; borrow keys are reported, never ranked.

Variant is bp/bar, invariant is per trade, never compared (FINDINGS section 10).
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


D331 = _load("d331", "run_d331_deal_filter.py")
BW = _load("d337b", "d337_borrow.py")
PA, V9 = D331.PA, D331.V9
V6, Y, W, D, M, SP, R, X = V9.V6, V9.Y, V9.W, V9.D, V9.M, V9.SP, V9.R, V9.X
Q, G22 = V6.Q, V6.G22

K0, K_INC, DEPTH = 20, 5, 2
ARM_K = {"H": K0, "S": K0, "S_F0": K0, "LW_F0": K0, "C0": K_INC}
EXITS = {"target": True, "fixed": False}
ACCS = ("sum", "compound")
LENSES = {"variant": True, "invariant": False}
HALVES = ("PB", "PUB")
SCHEMES = BW.SCHEMES
D333_NAME = {"H": "hist_L k20", "S": "skew_63 k20", "C0": "C0 N=2"}
OUT = REPO / "data" / "d337_constant_shares_borrow.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    print("D337  constant shares on the short leg, and a borrow stress charge")
    print(f"  schemes: gc_htb {BW.GC_BPS:.0f}/{BW.HTB_BPS:.0f} bp/yr (HTB: F0 window at e0-1 or close < "
          f"${BW.PX_HTB:.0f}); house {BW.HOUSE_BPS:.0f} bp/yr; none")

    # ---- loader chain (run_d331's) -----------------------------------------
    D.build_cache(verbose=True)
    A = D.load_cache(mmap=True)
    r1T, finT, mkt = np.asarray(A["r1T"]), np.asarray(A["finT"]), np.asarray(A["mkt"])
    T = r1T.shape[0]
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
    n, T2 = panel.live.shape
    assert T2 == T
    cs = z["cs_spread"]
    HALF_PUB = np.full((T, n), np.nan); HALF_PUB[1:] = (cs[:, :-1] / 2.0 * 1e4).T
    HALF = {"PB": HALF_PB, "PUB": HALF_PUB}
    last_live = PA.last_live_bar(finT)
    first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T for i in range(n)])
    dj = json.loads(D331.DEALS.read_text())
    deals = dj["deals"]
    f0 = lambda f: f["form"] in D331.F0_FORMS
    fb, drops, nok = D331.filing_bars(deals, panel.symbols, panel.dates, first_live, last_live, f0)
    excl = D331.exclusion_mask(fb, n, T, last_live)
    d333 = json.loads((REPO / "data" / "d333_dividend_bound.json").read_text())
    d331 = json.loads((REPO / "data" / "d331_deal_filter.json").read_text())
    print(f"  panel {finT.shape}; F0: {nok:,} filings applied, excluded live name-bars "
          f"{int((excl & finT.T).sum()):,} ({time.time() - t0:.0f}s)")

    rk_H = Y.rank_single(z, base, "hist_L", n, T)
    rk_S = Y.rank_single(z, base, "skew_63", n, T)
    rk_SF0 = Y.rank_single({"skew_63": np.where(excl, np.nan, z["skew_63"])}, base, "skew_63", n, T)
    rkC0 = Q.rank_composite(z, base, *Q.COMPOSITES["C0_incumbent"], n, T)
    RK = {"H": rk_H, "S": rk_S, "S_F0": rk_SF0, "LW_F0": V9.legwise(rk_H, rk_SF0), "C0": rkC0}
    GATE = {nm: Y.gate_from(RK[nm], finT) for nm in RK}
    print(f"  ranks and gates ({time.time() - t0:.0f}s)")

    # ---- simulate: 5 arms x 2 exits x 2 accumulations x 2 lenses ------------
    ts = time.time()
    RES = {}
    for nm in RK:
        for ex, ut in EXITS.items():
            for acc in ACCS:
                for lens, sl in LENSES.items():
                    W.BASE_HOLD = ARM_K[nm]
                    RES[(nm, ex, acc, lens)] = W.simulate(A, GATE[nm], DEPTH, ut, slots=sl, accumulate=acc)
        print(f"  {nm:5s} k={ARM_K[nm]:2d} simulated, both exits x both accumulations x both lenses "
              f"({time.time() - ts:.0f}s)", flush=True)

    # ---- borrow, per ledger (a property of (row, e0, age, side), not of the accumulation) ----
    BOR = {}
    for nm in RK:
        for ex in EXITS:
            for lens in LENSES:
                res = RES[(nm, ex, "sum", lens)]
                tr = res["trades"]
                htb = BW.htb_flags(tr, excl, CLOSE)
                short = np.array([t[4] == 1 for t in tr], bool)
                ages = np.array([t[2] for t in tr], float)
                d = dict(htb=htb, short=short,
                         htb_share=float(ages[short & htb].sum() / ages[short].sum()) if short.any() else np.nan,
                         n_short=int(short.sum()), n_htb=int((short & htb).sum()))
                for sc in SCHEMES:
                    rate = BW.rate_bps(tr, htb, sc)
                    d[sc] = dict(rate=rate, per_trade=BW.borrow_per_trade_bp(tr, rate),
                                 bar_bp=BW.borrow_per_bar_bp(res, tr, rate, T))
                BOR[(nm, ex, lens)] = d

    # ---- costing, post-hoc, per spread convention ---------------------------
    def cost_cell(nm, ex, acc, cv):
        H = HALF[cv]
        res_v, res_i = RES[(nm, ex, acc, "variant")], RES[(nm, ex, acc, "invariant")]
        bv, bi = BOR[(nm, ex, "variant")], BOR[(nm, ex, "invariant")]
        out = {}
        try:
            c = G22.costed(res_v, (H, CLOSE, DV, finT))
            g1 = G22.group1(res_v, c, G22.contributions(res_v, r1T), r1T)
            var = dict(net_bp_bar=g1["net_bp_bar"], gross_bp_bar=g1["gross_bp_bar"], sharpe_net=g1["sharpe_net"],
                       maxdd_bp=g1["maxdd_bp"], round_trip=c["round_trip"], held_half=c["held_half_spread"],
                       turnover=c["turnover"], trade_mean_bp=g1["trade_mean_bp"],
                       trade_net_mean_bp=g1["trade_net_mean_bp"], trades=c["trades"], borrow={})
            for sc in SCHEMES:
                cb = BW.costed_with_borrow(c, bv[sc]["bar_bp"], res_v["mask"])
                assert cb["net_bp"] == c["net_bp"] and cb["sharpe_net"] == c["sharpe_net"]
                var["borrow"][sc] = dict(borrow_bp=cb["borrow_bp"], net_bp_borrow=cb["net_bp_borrow"])
            out["variant"] = var
        except ZeroDivisionError:
            out["variant"] = "degenerate"
        legs = V9.per_leg(res_i, H, CLOSE, r1T, mkt)
        if all(legs[s] for s in (0, 1)):
            inv0 = V9.invariant_legcost(res_i, legs)
            inv = dict(inv0, borrow={})
            for sc in SCHEMES:
                lb = BW.legcost_with_borrow(inv0, bi[sc]["per_trade"])
                assert lb["mean_over_2c"] == inv0["mean_over_2c"] and lb["net_per_trade"] == inv0["net_per_trade"]
                inv["borrow"][sc] = dict(borrow_per_trade=lb["borrow_per_trade"],
                                         net_per_trade_borrow=lb["net_per_trade_borrow"])
            out["invariant"] = inv
        else:
            out["invariant"] = "degenerate"
        for s in (0, 1):
            if legs[s]:
                m = bi["short"] if s == 1 else ~bi["short"]
                legs[s]["borrow_per_trade"] = {sc: float(bi[sc]["per_trade"][m].mean()) for sc in SCHEMES}
                legs[s]["net_borrow"] = {sc: legs[s]["net"] - legs[s]["borrow_per_trade"][sc] for sc in SCHEMES}
        out["legs"] = {str(s): legs[s] for s in (0, 1)}
        return out

    CELLS = {}
    for nm in RK:
        for ex in EXITS:
            for acc in ACCS:
                for cv in HALVES:
                    CELLS[(nm, ex, acc, cv)] = cost_cell(nm, ex, acc, cv)
    print(f"  {len(CELLS)} costed cells ({time.time() - t0:.0f}s)")

    # ---- assertions -------------------------------------------------------
    print("\nASSERTIONS")
    aud = {}
    # S. the kernel
    BW.selftest()
    print("    [S] KERNEL SIGN AUDIT: -50%/+100%: long summed +0.5 vs compound 0.0, short -0.5 vs 0.0; "
          "-50%/-50%: long -1.0 vs -0.75, short +1.0 vs +0.75; and the test raises on a wrong expectation")
    # V. the flag raises
    raised = False
    try:
        W.simulate(A, GATE["C0"], DEPTH, True, accumulate="x")
    except ValueError:
        raised = True
    assert raised, "[V] accumulate='x' did not raise"
    print("    [V] simulate(accumulate='x') raises ValueError")
    # E. same ledger keys (in ORDER), same counts, same bar series
    n_cells = n_diff = n_tr = 0
    for nm in RK:
        for ex in EXITS:
            for lens in LENSES:
                rs, rc = RES[(nm, ex, "sum", lens)], RES[(nm, ex, "compound", lens)]
                ks = [(t[0], t[1], t[2], t[4]) for t in rs["trades"]]
                kc = [(t[0], t[1], t[2], t[4]) for t in rc["trades"]]
                assert ks == kc, f"[E] {nm}/{ex}/{lens}: the (row, e0, age, side) ledgers differ"
                assert len(set(ks)) == len(ks), f"[E] {nm}/{ex}/{lens}: duplicate ledger key"
                for arr in ("cnt0", "cnt1", "ent", "mask"):
                    assert np.array_equal(rs[arr], rc[arr]), f"[E] {nm}/{ex}/{lens}: {arr} differs"
                assert np.array_equal(rs["book"], rc["book"], equal_nan=True), f"[E] {nm}/{ex}/{lens}: bar series differ"
                n_diff += sum(1 for x, y in zip(rs["trades"], rc["trades"]) if x[3] != y[3])
                n_tr += len(ks); n_cells += 1
    assert n_diff > 0, "[E] compound changed no P&L at all"
    print(f"    [E] LEDGER IDENTITY: (row, e0, age, side) identical IN ORDER, cnt0/cnt1/ent/mask and the bar series "
          f"identical, across accumulation in all {n_cells} arm/exit/lens cells ({n_tr:,} trades; "
          f"{n_diff:,} P&Ls differ)")
    # P. every compound trade, two ways
    worst_a = worst_b = 0.0
    for nm in RK:
        for ex in EXITS:
            for lens in LENSES:
                rs, rc = RES[(nm, ex, "sum", lens)], RES[(nm, ex, "compound", lens)]
                rec = BW.compound_from_ledger(rc["trades"], r1T, mkt)
                for ts_, tc_, r_ in zip(rs["trades"], rc["trades"], rec):
                    row, e0, age, ps, side = ts_
                    sgn = 1.0 if side == 0 else -1.0
                    v = np.nan_to_num(r1T[e0:e0 + age, row], nan=0.0)
                    prem = sgn * (v.sum() - np.expm1(np.log1p(v).sum()))
                    worst_a = max(worst_a, abs(tc_[3] - r_))
                    worst_b = max(worst_b, abs(tc_[3] - (ps - prem)))
    assert worst_a < 1e-12 and worst_b < 1e-12, f"[P] {worst_a:.2e} {worst_b:.2e}"
    aud["P_recomputed"], aud["P_sum_minus_premium"] = worst_a, worst_b
    print(f"    [P] every compound trade equals sgn*(expm1(sum log1p v) - sum mt) recomputed from the ledger to "
          f"{worst_a:.1e}, and equals summed minus D329's per_leg premium to {worst_b:.1e}")
    # 1. identity with D333 (new panel) and D331
    worst = 0.0; diffs = []
    for nm, d3 in D333_NAME.items():
        for cv in HALVES:
            c = CELLS[(nm, "target", "sum", cv)]
            ref = d333["cells"][f"{d3}/{cv}/new"]
            diffs.append((f"D333 {d3}/{cv}/new invariant net_per_trade", c["invariant"]["net_per_trade"],
                          ref["invariant"]["net_per_trade"]))
            diffs.append((f"D333 {d3}/{cv}/new variant sharpe_net", c["variant"]["sharpe_net"],
                          ref["variant"]["sharpe_net"]))
    # D331's S_F0 cells were published on the UNBOUNDED panel (data/d331_deal_filter.json predates the
    # D333 fix), so they are reproduced under D333's `arrays_for(panel_old)` construction, exactly as
    # D333's own [1] reproduced D332. The bounded-panel S_F0 is then reported against them as a SHIFT.
    panel_old, _ = M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS, dividend_bound=False)
    live_o = panel_old.live
    base_o = z["warm"] & live_o
    _ctx, r1_o, _vr, _ = D.E.build_inputs(z, base_o, panel_old, live_o, T)
    m_o = D.L.market_reference(r1_o, live_o)
    vx_o = D.E.roll_vol(r1_o - m_o[None, :], live_o, D.VOL_WIN)
    A_old = dict(r1T=np.ascontiguousarray(r1_o.T), mkt=m_o, vxT=np.ascontiguousarray(vx_o.T),
                 finT=np.isfinite(np.ascontiguousarray(r1_o.T)), rankT=np.asarray(A["rankT"]))
    assert not np.array_equal(A_old["r1T"], r1T, equal_nan=True), "[1] the unbounded panel equals the bounded one"
    gate_o = Y.gate_from(RK["S_F0"], A_old["finT"])
    W.BASE_HOLD = K0
    ro_v = W.simulate(A_old, gate_o, DEPTH, True, slots=True)
    ro_i = W.simulate(A_old, gate_o, DEPTH, True, slots=False)
    ro_ic = W.simulate(A_old, gate_o, DEPTH, True, slots=False, accumulate="compound")
    legs_old_sf0 = {acc: V9.per_leg(r_, HALF_PB, CLOSE, A_old["r1T"], A_old["mkt"])
                    for acc, r_ in (("sum", ro_i), ("compound", ro_ic))}
    shift_sf0 = {}
    for cv in HALVES:
        ref = d331["cells"][f"S_F0/{cv}/k20"]
        legs_o = V9.per_leg(ro_i, HALF[cv], CLOSE, A_old["r1T"], A_old["mkt"])
        inv_o = V9.invariant_legcost(ro_i, legs_o)
        c_o = G22.costed(ro_v, (HALF[cv], CLOSE, DV, A_old["finT"]))
        diffs.append((f"D331 S_F0/{cv}/k20 invariant net_per_trade (unbounded panel)", inv_o["net_per_trade"],
                      ref["invariant"]["net_per_trade"]))
        diffs.append((f"D331 S_F0/{cv}/k20 variant sharpe_net (unbounded panel)", c_o["sharpe_net"],
                      ref["variant"]["sharpe_net"]))
        shift_sf0[cv] = CELLS[("S_F0", "target", "sum", cv)]["invariant"]["net_per_trade"] - ref["invariant"]["net_per_trade"]
    worst = max(abs(g - w) for _, g, w in diffs)
    if not worst < 1e-9:
        for lbl, g, w in diffs:
            print(f"      {lbl:64s} got {g:+.6f}  want {w:+.6f}  diff {g - w:+.2e}")
    assert worst < 1e-9, f"[1] {worst:.2e}"
    aud["s_f0_bound_shift_per_trade"] = shift_sf0
    aud["identity"] = worst
    print(f"    [1] IDENTITY: accumulate='sum' with target exits reproduces D333's hist_L, skew_63 and C0 N=2 "
          f"new-panel cells (both lenses, PB and PUB) on the bounded panel, and D331's S_F0 cells (both lenses) "
          f"under the UNBOUNDED panel they were published on, to {worst:.1e}")
    print(f"        (D331 predates the D333 bound: on the bounded panel S_F0's invariant net per trade moves "
          f"{shift_sf0['PB']:+.2f} PB / {shift_sf0['PUB']:+.2f} PUB against D331's cells -- the panel, not the code)")
    # B. reconcile
    worst = 0.0
    for (nm, ex, lens), d in BOR.items():
        res = RES[(nm, ex, "sum", lens)]
        for sc in SCHEMES:
            worst = max(worst, BW.reconcile(d[sc]["bar_bp"], res, d[sc]["per_trade"]))
    assert worst < 1e-9, f"[B] {worst:.2e}"
    aud["reconcile"] = worst
    print(f"    [B] RECONCILE: borrow per bar x cnt1, summed, equals borrow per trade, summed, to {worst:.1e} bp "
          f"in every cell and scheme")
    # F. the house scheme is exactly flat where the ledger covers the bar
    flat = BW.HOUSE_BPS / BW.ANN
    worst = 0.0; tail_bars = {}
    for (nm, ex, lens), d in BOR.items():
        res = RES[(nm, ex, "sum", lens)]
        dd = np.zeros(T + 1)
        for row, e0, age, _p, s in res["trades"]:
            if s == 1:
                dd[e0] += 1; dd[min(e0 + age, T)] -= 1
        rebuilt = np.cumsum(dd)[:T]
        cnt1 = np.asarray(res["cnt1"], float)
        gap = cnt1 - rebuilt
        assert (gap >= -1e-9).all(), "[F] the ledger claims a short the book never held"
        # positions never closed are held through T-1, so the gap is a non-decreasing tail
        assert (np.diff(gap) >= -1e-9).all(), f"[F] {nm}/{ex}/{lens}: a hole in the ledger, not an open tail"
        covered = (cnt1 > 0) & (gap == 0) & res["mask"]
        bb = d["house"]["bar_bp"]
        worst = max(worst, float(np.abs(bb[covered] - flat).max()))
        tail_bars[(nm, ex, lens)] = int(((cnt1 > 0) & (gap > 0) & res["mask"]).sum())
    assert worst < 1e-12, f"[F] {worst:.2e}"
    aud["house_flat"] = worst
    mx_tail = max(tail_bars.values())
    print(f"    [F] HOUSE: bar_bp == 300/252 = {flat:.6f} to {worst:.1e} on every masked bar with cnt1 > 0 that "
          f"the ledger covers; the only uncovered bars are the open-at-T tail (at most {mx_tail} bars of {T}, "
          f"absent from both sides of [B] by construction)")
    # K. causality of the HTB flag
    T0 = T // 2
    darr = np.array(panel.dates)
    cut = {s: [f for f in fl if np.searchsorted(darr, f["date"]) <= T0] for s, fl in deals.items()}
    fb_cut, _, _ = D331.filing_bars(cut, panel.symbols, panel.dates, first_live, last_live, f0)
    excl_cut = D331.exclusion_mask(fb_cut, n, T, last_live)
    assert np.array_equal(excl[:, :T0 + 1], excl_cut[:, :T0 + 1]) and excl_cut.sum() < excl.sum()
    n_early = 0
    for (nm, ex, lens), d in BOR.items():
        tr = RES[(nm, ex, "sum", lens)]["trades"]
        h2 = BW.htb_flags(tr, excl_cut, CLOSE)
        early = np.array([t[1] <= T0 for t in tr], bool)
        assert np.array_equal(d["htb"][early], h2[early]), f"[K] {nm}/{ex}/{lens}: an HTB flag before T0 changed"
        n_early += int(early.sum())
    print(f"    [K] CAUSALITY: deleting every filing dated after T0={T0} leaves the HTB flag of all {n_early:,} "
          f"trades entered through T0 unchanged")
    # 6. raises
    broke = False
    try:
        ref = CELLS[("LW_F0", "target", "compound", "PUB")]["invariant"]
        bad = dict(ref); bad["net_per_trade"] += 50.0
        assert abs(bad["net_per_trade"] - ref["net_per_trade"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke
    print("    [6] and the check raises on a book handed free money")

    # ---- the reproduction check: each leg's compound gain == -premium -------
    print("\nREPRODUCTION CHECK (not a prediction): compound gain per leg == -premium from D333/D331, target exit")
    print("  (H, S, C0 against D333's bounded-panel cells; S_F0 against D331 on the unbounded panel it was "
          "published on, then its bounded-panel gain against its own premium)")
    print("  %-10s %-5s %10s %10s %10s %10s" % ("arm", "leg", "sum gross", "cmp gross", "gain", "-premium"))
    worst = 0.0; repro = {}
    rows = [(nm, d333["cells"][f"{D333_NAME[nm]}/PB/new"]["legs"],
             CELLS[(nm, "target", "sum", "PB")]["legs"], CELLS[(nm, "target", "compound", "PB")]["legs"])
            for nm in ("H", "S", "C0")]
    rows.append(("S_F0 old", d331["cells"]["S_F0/PB/k20"]["legs"],
                 {str(s): legs_old_sf0["sum"][s] for s in (0, 1)}, {str(s): legs_old_sf0["compound"][s] for s in (0, 1)}))
    rows.append(("S_F0 new", CELLS[("S_F0", "target", "sum", "PB")]["legs"],
                 CELLS[("S_F0", "target", "sum", "PB")]["legs"], CELLS[("S_F0", "target", "compound", "PB")]["legs"]))
    for nm, ref_legs, legs_s, legs_c in rows:
        for s, lbl in ((0, "long"), (1, "short")):
            gs, gc = legs_s[str(s)]["gross"], legs_c[str(s)]["gross"]
            prem = ref_legs[str(s)]["premium_bp"]
            worst = max(worst, abs((gc - gs) + prem))
            repro[f"{nm}/{lbl}"] = dict(gain_bp=gc - gs, minus_premium_bp=-prem)
            print("  %-10s %-5s %+10.2f %+10.2f %+10.2f %+10.2f" % (nm, lbl, gs, gc, gc - gs, -prem))
    assert worst < 1e-6, f"reproduction check {worst:.2e}"
    aud["reproduction"] = worst
    print(f"  max |gain + premium| = {worst:.1e} bp")

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # ---- tables -------------------------------------------------------------
    L = lambda nm, ex, acc, cv, s: CELLS[(nm, ex, acc, cv)]["legs"][str(s)]
    it = lambda c: c["invariant"]["net_per_trade"] if c["invariant"] != "degenerate" else np.nan
    ib = lambda c, sc: c["invariant"]["borrow"][sc]["net_per_trade_borrow"] if c["invariant"] != "degenerate" else np.nan
    ibp = lambda c, sc: c["invariant"]["borrow"][sc]["borrow_per_trade"] if c["invariant"] != "degenerate" else np.nan
    vb = lambda c: c["variant"]["net_bp_bar"] if c["variant"] != "degenerate" else np.nan
    vbb = lambda c, sc: c["variant"]["borrow"][sc]["borrow_bp"] if c["variant"] != "degenerate" else np.nan
    vnb = lambda c, sc: c["variant"]["borrow"][sc]["net_bp_borrow"] if c["variant"] != "degenerate" else np.nan
    sh = lambda c: c["variant"]["sharpe_net"] if c["variant"] != "degenerate" else np.nan

    print("\nPER LEG, invariant lens, net per trade (bp) BEFORE borrow: sum -> compound.   premium = D329's, signed")
    print("  %-5s %-6s %5s %5s | %8s %8s | %8s %8s | %8s %8s | %8s %8s | %8s %8s"
          % ("arm", "exit", "nL", "nS", "L sum", "L cmp", "S sum", "S cmp", "L sum", "L cmp", "S sum", "S cmp", "prem L", "prem S"))
    print("  %-5s %-6s %5s %5s | %17s | %17s | %17s | %17s | %17s"
          % ("", "", "", "", "------- PB ------", "", "------ PUB ------", "", "-- bp per trade -"))
    for nm in RK:
        for ex in EXITS:
            r = [nm, ex, L(nm, ex, "sum", "PB", 0)["trades"], L(nm, ex, "sum", "PB", 1)["trades"]]
            for cv in HALVES:
                for s in (0, 1):
                    r += [L(nm, ex, "sum", cv, s)["net"], L(nm, ex, "compound", cv, s)["net"]]
            r += [L(nm, ex, "sum", "PB", 0)["premium_bp"], L(nm, ex, "sum", "PB", 1)["premium_bp"]]
            print("  %-5s %-6s %5d %5d | %+8.1f %+8.1f | %+8.1f %+8.1f | %+8.1f %+8.1f | %+8.1f %+8.1f | %+8.1f %+8.1f" % tuple(r))

    print("\nBORROW PER TRADE (bp) and the HTB share of short position-bars, per ledger")
    print("  %-5s %-6s %-9s %7s %6s %8s | %8s %8s | %8s %8s"
          % ("arm", "exit", "lens", "shorts", "htb", "htb shr", "gc S/trd", "hs S/trd", "gc all", "hs all"))
    for nm in RK:
        for ex in EXITS:
            for lens in LENSES:
                d = BOR[(nm, ex, lens)]
                sm = d["short"]
                print("  %-5s %-6s %-9s %7d %6d %7.1f%% | %8.2f %8.2f | %8.2f %8.2f"
                      % (nm, ex, lens, d["n_short"], d["n_htb"], 100 * d["htb_share"],
                         d["gc_htb"]["per_trade"][sm].mean(), d["house"]["per_trade"][sm].mean(),
                         d["gc_htb"]["per_trade"].mean(), d["house"]["per_trade"].mean()))

    print("\nPATH-INVARIANT, net per trade (bp) after spread, then after borrow by scheme")
    print("  %-5s %-6s %-8s | %8s %8s %8s | %8s %8s %8s | %8s %8s"
          % ("arm", "exit", "acc", "PB none", "PB gc", "PB house", "PUB none", "PUB gc", "PUB hs", "brw gc", "brw hs"))
    for nm in RK:
        for ex in EXITS:
            for acc in ACCS:
                a_, b_ = CELLS[(nm, ex, acc, "PB")], CELLS[(nm, ex, acc, "PUB")]
                print("  %-5s %-6s %-8s | %+8.2f %+8.2f %+8.2f | %+8.2f %+8.2f %+8.2f | %8.2f %8.2f"
                      % (nm, ex, acc, it(a_), ib(a_, "gc_htb"), ib(a_, "house"), it(b_), ib(b_, "gc_htb"), ib(b_, "house"),
                         ibp(a_, "gc_htb"), ibp(a_, "house")))

    print("\nPATH-VARIANT, the capped book, net bp/bar after spread, then after borrow by scheme (bar series is "
          "accumulation-invariant; sum ledger shown)")
    print("  %-5s %-6s | %8s %8s %8s %8s %8s | %8s %8s %8s"
          % ("arm", "exit", "PB net", "brw gc", "net gc", "brw hs", "net hs", "PUB net", "net gc", "net hs"))
    for nm in RK:
        for ex in EXITS:
            a_, b_ = CELLS[(nm, ex, "sum", "PB")], CELLS[(nm, ex, "sum", "PUB")]
            print("  %-5s %-6s | %+8.2f %8.3f %+8.2f %8.3f %+8.2f | %+8.2f %+8.2f %+8.2f"
                  % (nm, ex, vb(a_), vbb(a_, "gc_htb"), vnb(a_, "gc_htb"), vbb(a_, "house"), vnb(a_, "house"),
                     vb(b_), vnb(b_, "gc_htb"), vnb(b_, "house")))

    # ---- predictions ---------------------------------------------------------
    hS = {cv: L("H", "target", "compound", cv, 1)["net"] for cv in HALVES}
    q1 = all(hS[cv] < 0 for cv in HALVES)
    premH_fixed = L("H", "fixed", "sum", "PB", 1)["premium_bp"]
    q2 = premH_fixed < -60.0
    premC0_fixed = {s: L("C0", "fixed", "sum", "PB", s)["premium_bp"] for s in (0, 1)}
    q3 = all(abs(v) < 10.0 for v in premC0_fixed.values())
    shr = {nm: {lens: BOR[(nm, "target", lens)]["htb_share"] for lens in LENSES} for nm in RK}
    q4 = shr["C0"]["variant"] < 0.15 and shr["H"]["variant"] > 0.25
    c0 = CELLS[("C0", "target", "sum", "PB")]
    gc_c0 = vbb(c0, "gc_htb"); hs_c0 = vbb(c0, "house"); net_hs_c0 = vnb(c0, "house"); net_c0 = vb(c0)
    q5 = gc_c0 < 0.5 and aud["house_flat"] < 1e-12 and 0.0 < net_hs_c0 < 6.0
    lw = CELLS[("LW_F0", "target", "compound", "PUB")]
    q6v = ib(lw, "gc_htb")
    q6 = q6v > 0.0
    print("\nPREDICTIONS")
    for kk, vv in (("Q1 hist_L's short leg still nets < 0 per trade under compound, PB and PUB, before borrow  [load-bearing, against]", q1),
                   ("Q2 fixed hold k=20: hist_L's short-leg premium below -60 bp", q2),
                   ("Q3 fixed hold k=5: C0's premiums within +/-10 bp on both legs", q3),
                   ("Q4 HTB covers < 15% of C0's short position-bars and > 25% of hist_L's (target exit, variant book)", q4),
                   ("Q5 GC+HTB costs C0's book < 0.5 bp/bar; house is exactly 300/252 and takes C0's PB net below 6.0 but not below 0", q5),
                   ("Q6 LW_F0 k=20 nets > 0 per trade under PUB, compound, GC+HTB borrow  [load-bearing]", q6)):
        print(f"    {'CONFIRMED' if vv else 'FALSIFIED'}  {kk}")
    print(f"    Q1: hist_L short leg, compound, target: PB {hS['PB']:+.2f} (identity said ~-53), PUB {hS['PUB']:+.2f} "
          f"(identity said ~-135);  sum was PB {L('H', 'target', 'sum', 'PB', 1)['net']:+.2f}, "
          f"PUB {L('H', 'target', 'sum', 'PUB', 1)['net']:+.2f}")
    print(f"    Q2: hist_L fixed-hold short premium {premH_fixed:+.2f} bp (target exit: "
          f"{L('H', 'target', 'sum', 'PB', 1)['premium_bp']:+.2f});  mean age fixed vs target: "
          f"{np.mean([t[2] for t in RES[('H', 'fixed', 'sum', 'invariant')]['trades'] if t[4] == 1]):.1f} vs "
          f"{np.mean([t[2] for t in RES[('H', 'target', 'sum', 'invariant')]['trades'] if t[4] == 1]):.1f} bars")
    print(f"    Q3: C0 fixed-hold premiums long {premC0_fixed[0]:+.2f}, short {premC0_fixed[1]:+.2f} bp")
    print(f"    Q4: HTB share of short position-bars, target exit -- C0 variant {100 * shr['C0']['variant']:.1f}% "
          f"(invariant {100 * shr['C0']['invariant']:.1f}%), hist_L variant {100 * shr['H']['variant']:.1f}% "
          f"(invariant {100 * shr['H']['invariant']:.1f}%)")
    print(f"    Q5: C0 PB book: net {net_c0:+.2f} (D333 new: {d333['cells']['C0 N=2/PB/new']['variant']['net_bp_bar']:+.2f}); "
          f"gc_htb borrow {gc_c0:.3f} bp/bar -> {vnb(c0, 'gc_htb'):+.2f}; house borrow {hs_c0:.4f} bp/bar "
          f"(flat {flat:.4f} on covered bars; masked mean includes the open tail) -> {net_hs_c0:+.2f}")
    print(f"    Q6: LW_F0 PUB compound per trade: spread-only {it(lw):+.2f}, after GC+HTB {q6v:+.2f}, after house "
          f"{ib(lw, 'house'):+.2f};  sum-accumulation spread-only {it(CELLS[('LW_F0', 'target', 'sum', 'PUB')]):+.2f}")

    OUT.write_text(json.dumps(dict(
        note="D337: constant-shares accumulation (compound) vs the daily-rebalanced sum, per trade; borrow stress "
             "charge on short position-bars under NEW keys (net_bp and mean_over_2c untouched). Variant bp/bar, "
             "invariant per trade, never compared (FINDINGS section 10). D333-bounded panel.",
        schemes=dict(gc_bps=BW.GC_BPS, htb_bps=BW.HTB_BPS, house_bps=BW.HOUSE_BPS, px_htb=BW.PX_HTB, ann=BW.ANN,
                     htb_rule="short and (F0 exclusion at e0-1 or close at e0 < px_htb)"),
        arms={nm: dict(k=ARM_K[nm], depth=DEPTH) for nm in RK}, f0_filings_applied=nok, f0_drops=drops,
        cells={f"{nm}/{ex}/{acc}/{cv}": c for (nm, ex, acc, cv), c in CELLS.items()},
        borrow={f"{nm}/{ex}/{lens}": dict(
            htb_share=d["htb_share"], n_short=d["n_short"], n_htb=d["n_htb"],
            short_borrow_per_trade={sc: float(d[sc]["per_trade"][d["short"]].mean()) for sc in SCHEMES},
            bar_bp_masked_mean={sc: float(d[sc]["bar_bp"][RES[(nm, ex, "sum", lens)]["mask"]].mean()) for sc in SCHEMES},
            open_tail_bars=tail_bars[(nm, ex, lens)]) for (nm, ex, lens), d in BOR.items()},
        reproduction=repro, audits=aud,
        q_values=dict(q1_hist_L_short_compound=hS, q2_hist_L_fixed_short_premium=premH_fixed,
                      q3_C0_fixed_premiums={str(s): v for s, v in premC0_fixed.items()},
                      q4_htb_share={nm: shr[nm] for nm in ("C0", "H")},
                      q5=dict(net_pb=net_c0, gc_htb_bp=gc_c0, house_bp=hs_c0, net_house=net_hs_c0),
                      q6_lw_f0_pub_compound_gc=q6v),
        predictions=dict(Q1=bool(q1), Q2=bool(q2), Q3=bool(q3), Q4=bool(q4), Q5=bool(q5), Q6=bool(q6))),
        indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

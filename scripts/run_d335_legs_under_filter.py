"""D335 -- the leg-wise book's legs, re-chosen under the deal filter and PUB.

    uv run python scripts/run_d335_legs_under_filter.py --selftest
    uv run python scripts/run_d335_legs_under_filter.py

PRE-REGISTERED AT `54d8d82`, committed before this file existed (R8).

D329 proved ([L]) that a leg-wise book's ledger is the union of its parents'
legs, bit-identically, on both lenses. On the path-invariant lens the best
pairing per trade is therefore the best long leg plus the best short leg, and
there is no pair effect to enumerate: 46 symmetric books give every signal's
long-leg and short-leg per-trade statistics. Multiplicity is 46 per leg,
reported as rank with the p50/p95 of the 46.

EVERY SCORE IS FILTERED BY F0 (run_d331_deal_filter: target forms DEFM14A
PREM14A SC 14D9 SC TO-T SC TO-C, 189 bars from filing or until death) before
ranking. The panel is the D333-bounded panel; the score cache is the D334
rebuild, asserted by [K] before anything runs. PUB (the published trailing
mean, D332) is primary; PB (the per-bar median) is reported beside it.

Nothing here is promoted. The best pairing, if any, is a candidate for a
separate pre-registered test.
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


V31 = _load("d331", "run_d331_deal_filter.py")
PA, V9 = V31.PA, V31.V9
V6, Y, W, D, M, SP, R, X = V9.V6, V9.Y, V9.W, V9.D, V9.M, V9.SP, V9.R, V9.X
G22 = V6.G22
EXCLUDED = V9.EXCLUDED

K0, DEPTH = 20, 2
TOP = 3
REBUILT = ("beta_63", "ivol_21", "signed_vol")          # read total_log_returns; stale pre-D334
OLD_NPZ = REPO / "temp" / "d290_scores_pre_d333.npz"
OUT = REPO / "data" / "d335_legs_under_filter.json"
EXPECT_APPLIED, EXPECT_PCT = 1719, 2.54                  # D331's second-pass F0 counts


def check_cache_landed():
    """[K] the D334 rebuild is on disk: key matches, mtime newer than ragged_panel.py, old npz kept."""
    cache = Path(R.BC.CACHE)
    rp = REPO / "scripts" / "ragged_panel.py"
    if not cache.exists():
        return False, "no score cache"
    if cache.stat().st_mtime <= rp.stat().st_mtime:
        return False, f"npz mtime {cache.stat().st_mtime:.0f} <= ragged_panel.py {rp.stat().st_mtime:.0f}"
    if not OLD_NPZ.exists():
        return False, f"{OLD_NPZ.name} missing"
    try:
        z = np.load(cache, allow_pickle=False)
        key = str(z["key"])
    except Exception as e:                                # noqa: BLE001 -- a half-written npz
        return False, f"npz unreadable: {e}"
    want = R.BC.cache_key(M.B.FIXTURE)
    if key != want:
        return False, "npz key != cache_key() (ragged_panel.py in the tuple)"
    return True, "key matches, mtime newer than ragged_panel.py, pre-D333 npz present"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    print("D335  the legs re-chosen under the deal filter and PUB")

    # ---- [K] first: nothing runs on a stale cache ----------------------------
    ok, why = check_cache_landed()
    assert ok, f"[K] score cache has not landed: {why}"
    print(f"    [K] SCORE CACHE: {why}")

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
    HALF_PUB = np.full((T, n), np.nan); HALF_PUB[1:] = (cs[:, :-1] / 2.0 * 1e4).T
    HALF = {"PB": HALF_PB, "PUB": HALF_PUB}
    last_live = PA.last_live_bar(finT)
    first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T for i in range(n)])
    d333 = json.loads((REPO / "data" / "d333_dividend_bound.json").read_text())
    pool = [s for s in z.files if s not in ("key", "warm") and s not in EXCLUDED]
    assert len(pool) == 46, f"partner pool is {len(pool)}, not 46"
    for s in ("hist_L", "skew_63", "retrace_leg") + REBUILT:
        assert s in pool, s
    print(f"  panel {finT.shape}, depth {DEPTH}, k={K0}, {len(pool)} signals ({time.time() - t0:.0f}s)")

    # ---- the F0 mask ----------------------------------------------------------
    dj = json.loads(V31.DEALS.read_text())
    deals = dj["deals"]
    fb, drops, n_ok = V31.filing_bars(deals, panel.symbols, panel.dates, first_live, last_live,
                                      lambda f: f["form"] in V31.F0_FORMS)
    excl = V31.exclusion_mask(fb, n, T, last_live)
    pct = 100.0 * (excl & finT.T).sum() / finT.sum()
    print(f"  F0: {n_ok:,} filings applied, drops {drops}; excluded live name-bars "
          f"{int((excl & finT.T).sum()):,} ({pct:.2f}% of live)")

    def filt(sig, zz=z):
        return np.where(excl, np.nan, zz[sig])

    def rank_f0(sig, zz=z):
        return Y.rank_single({sig: filt(sig, zz)}, base if zz is z else (zz["warm"] & panel.live), sig, n, T)

    def run_cell(rankT, k=K0):
        """D333's cell: variant (slots) under both HALFs, invariant (no slots) per leg under both."""
        W.BASE_HOLD = k
        gate = Y.gate_from(rankT, finT)
        out = {"variant": {}, "invariant": {}, "legs": {}}
        res_v = W.simulate(A, gate, DEPTH, True, slots=True)
        for cv in ("PB", "PUB"):
            try:
                c = G22.costed(res_v, (HALF[cv], CLOSE, DV, finT))
                g1 = G22.group1(res_v, c, G22.contributions(res_v, r1T), r1T)
                out["variant"][cv] = dict(net_bp_bar=g1["net_bp_bar"], gross_bp_bar=g1["gross_bp_bar"],
                                          sharpe_net=g1["sharpe_net"], maxdd_bp=g1["maxdd_bp"],
                                          round_trip=c["round_trip"], held_half=c["held_half_spread"])
            except ZeroDivisionError:
                out["variant"][cv] = "degenerate"
        res_i = W.simulate(A, gate, DEPTH, True, slots=False)
        for cv in ("PB", "PUB"):
            legs = V9.per_leg(res_i, HALF[cv], CLOSE, r1T, mkt)
            out["legs"][cv] = {str(s): legs[s] for s in (0, 1)}
            out["invariant"][cv] = (V9.invariant_legcost(res_i, legs)
                                    if all(legs[s] for s in (0, 1)) else "degenerate")
        return out, res_v, res_i

    leg = lambda c, cv, s: c["legs"][cv][str(s)]
    vb = lambda c, cv: c["variant"][cv]["net_bp_bar"] if c["variant"][cv] != "degenerate" else np.nan
    sh = lambda c, cv: c["variant"][cv]["sharpe_net"] if c["variant"][cv] != "degenerate" else np.nan
    it = lambda c, cv: c["invariant"][cv]["net_per_trade"] if c["invariant"][cv] != "degenerate" else np.nan

    # ---- assertions ----------------------------------------------------------------
    print("\nASSERTIONS")
    # F. the mask reproduces D331's second pass
    assert n_ok == EXPECT_APPLIED, f"[F] {n_ok} filings applied, expected {EXPECT_APPLIED}"
    assert abs(pct - EXPECT_PCT) < 0.02, f"[F] {pct:.3f}% excluded, expected {EXPECT_PCT}"
    print(f"    [F] F0 MASK: {n_ok:,} filings applied, {pct:.2f}% of live name-bars excluded -- D331's counts")
    # 1. identity: no filter, PB, D329's four arms reproduce D333's new-panel cells
    rk_raw = {s: Y.rank_single(z, base, s, n, T) for s in ("hist_L", "skew_63")}
    RK29 = {"H": rk_raw["hist_L"], "S": rk_raw["skew_63"],
            "LW": V9.legwise(rk_raw["hist_L"], rk_raw["skew_63"]),
            "RV": V9.legwise(rk_raw["skew_63"], rk_raw["hist_L"])}
    arm29 = {}
    worst = 0.0
    for nm in RK29:
        arm29[nm], _, _ = run_cell(RK29[nm])
        c3 = d333["cells"][f"{nm} k{K0}/PB/new"]
        worst = max(worst, abs(it(arm29[nm], "PB") - c3["invariant"]["net_per_trade"]),
                    abs(sh(arm29[nm], "PB") - c3["variant"]["sharpe_net"]))
    assert worst < 1e-9, f"[1] {worst:.2e}"
    print(f"    [1] IDENTITY: unfiltered, PB, H/S/LW/RV at k={K0} reproduce D333's new-panel cells to {worst:.1e}")
    # C. per-leg 2c on the four arms, both conventions
    n_c = 0
    for nm in arm29:
        for cv in ("PB", "PUB"):
            for s in (0, 1):
                L = leg(arm29[nm], cv, s)
                assert L is not None and abs(L["two_c"] - 2.0 * L["half_bp"]) < 1e-12, f"[C] {nm} {cv} {s}"
                n_c += 1
    print(f"    [C] per-leg 2c is 2 x that leg's held median half-spread on all {n_c} legs of the four arms")
    # 6. raises
    broke = False
    try:
        bad = dict(leg(arm29["LW"], "PUB", 1)); bad["net"] += 50.0
        assert abs(bad["net"] - leg(arm29["LW"], "PUB", 1)["net"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6] the check passed a leg handed free money"
    print("    [6] and the check raises on a leg handed free money")

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # ---- the per-leg table: 46 symmetric F0 books -------------------------------------
    ts = time.time()
    rk = {s: rank_f0(s) for s in pool}
    print(f"\n  {len(rk)} F0-filtered rank arrays ({time.time() - ts:.0f}s)")
    ts = time.time()
    table, RES_V, RES_I = {}, {}, {}
    for j, s in enumerate(pool):
        table[s], RES_V[s], RES_I[s] = run_cell(rk[s])
        if (j + 1) % 10 == 0:
            print(f"  {j + 1}/{len(pool)} ({time.time() - ts:.0f}s)", flush=True)
    print(f"  46 symmetric books, both lenses ({time.time() - ts:.0f}s)")
    # [C] across the whole table
    for s in pool:
        for cv in ("PB", "PUB"):
            for side in (0, 1):
                L = leg(table[s], cv, side)
                if L is not None:
                    assert abs(L["two_c"] - 2.0 * L["half_bp"]) < 1e-12, f"[C] {s} {cv} {side}"
    print("    [C] holds on every costable leg of the 46")

    # ---- rank the legs by PUB per-leg net -----------------------------------------
    def leg_rows(side):
        """(net, sig) for every leg with trades and a non-zero held half-spread under PUB."""
        rows, deg = [], []
        for s in pool:
            L = leg(table[s], "PUB", side)
            if L is None or L["half_bp"] <= 0.0:
                deg.append(s); continue
            rows.append((L["net"], s))
        return sorted(rows, reverse=True), deg

    ranked, degenerate = {}, {}
    for side, lbl in ((0, "long"), (1, "short")):
        ranked[lbl], degenerate[lbl] = leg_rows(side)
    rank_of = {lbl: {s: i + 1 for i, (_, s) in enumerate(ranked[lbl])} for lbl in ranked}
    pct_of = {lbl: dict(p50=float(np.percentile([v for v, _ in ranked[lbl]], 50)),
                        p95=float(np.percentile([v for v, _ in ranked[lbl]], 95)),
                        n=len(ranked[lbl])) for lbl in ranked}

    print("\nPER LEG, invariant, F0, k=20 -- ranked by PUB net per trade   (PB beside)")
    for side, lbl in ((0, "long"), (1, "short")):
        pr = pct_of[lbl]
        print(f"\n  {lbl.upper()} LEGS  top 10 of {pr['n']} costable ({len(degenerate[lbl])} degenerate: "
              f"{', '.join(degenerate[lbl]) or '-'});  PUB net p50 {pr['p50']:+.1f}  p95 {pr['p95']:+.1f}")
        print("  %3s %-14s %6s | %8s %8s %7s %6s %7s %8s | %8s %6s | %8s %8s"
              % ("rk", "signal", "trades", "PUB gross", "PUB net", "t", "half", "price", "premium",
                 "PB net", "PB hf", "var PUB", "Sharpe"))
        for r_, (v, s) in enumerate(ranked[lbl][:10], 1):
            L, Lb = leg(table[s], "PUB", side), leg(table[s], "PB", side)
            print("  %3d %-14s %6d | %+8.1f %+8.1f %+7.2f %6.1f %7.1f %+8.1f | %+8.1f %6.1f | %+8.2f %+8.3f"
                  % (r_, s, L["trades"], L["gross"], L["net"], L["t"], L["half_bp"], L["price"], L["premium_bp"],
                     Lb["net"], Lb["half_bp"], vb(table[s], "PUB"), sh(table[s], "PUB")))
    where = {}
    for s, lbl in (("skew_63", "short"), ("hist_L", "long"), ("retrace_leg", "long")):
        side = 0 if lbl == "long" else 1
        L = leg(table[s], "PUB", side)
        where[f"{s}/{lbl}"] = dict(rank=rank_of[lbl].get(s), of=pct_of[lbl]["n"],
                                   net=L["net"] if L else np.nan, gross=L["gross"] if L else np.nan,
                                   half_bp=L["half_bp"] if L else np.nan)
        print(f"  {s} {lbl} leg: rank {rank_of[lbl].get(s)} of {pct_of[lbl]['n']}  PUB net "
              f"{(L['net'] if L else np.nan):+.1f} (gross {(L['gross'] if L else np.nan):+.1f}, half {(L['half_bp'] if L else np.nan):.1f})")
    n_pos_short = sum(1 for v, _ in ranked["short"] if v > 0)
    print(f"  short legs netting > 0 under PUB: {n_pos_short} of {pct_of['short']['n']}")

    # ---- the nine books + the incumbent best ----------------------------------------
    top_long = [s for _, s in ranked["long"][:TOP]]
    top_short = [s for _, s in ranked["short"][:TOP]]
    books = {}
    ts = time.time()
    for L_ in top_long:
        for S_ in top_short:
            nm = f"{L_}|{S_}"
            if L_ == S_:
                books[nm] = table[L_]
                bv, bi = RES_V[L_], RES_I[L_]
            else:
                books[nm], bv, bi = run_cell(V9.legwise(rk[L_], rk[S_]))
            # L. ledgers per side equal the parents', both lenses
            for lens, rb, rp_l, rp_s in (("variant", bv, RES_V[L_], RES_V[S_]), ("invariant", bi, RES_I[L_], RES_I[S_])):
                assert V9.same_side(rb, rp_l, 0), f"[L] {lens} {nm}: long != {L_}"
                assert V9.same_side(rb, rp_s, 1), f"[L] {lens} {nm}: short != {S_}"
    print(f"\n    [L] LEG INDEPENDENCE: each of the {len(books)} pairings' side-0 ledger is its long parent's and "
          f"side-1 its short parent's, both lenses  ({time.time() - ts:.0f}s)")
    inc = table["retrace_leg"]
    print("\nTHE BOOKS -- top-3 long x top-3 short by PUB per-leg net, plus retrace_leg symmetric (F0)")
    print("  %-28s | %8s %8s %8s | %8s %8s %8s || %8s %8s | %8s %8s"
          % ("book", "PUB net/trd", "L net", "S net", "PUB bp/bar", "Sharpe", "maxDD", "PB net/trd", "PB bp/bar", "PB Sharpe", "held"))
    rows = [(f"{L_}|{S_}", books[f"{L_}|{S_}"]) for L_ in top_long for S_ in top_short] + [("retrace_leg (sym)", inc)]
    for nm, c in rows:
        md = c["variant"]["PUB"]["maxdd_bp"] if c["variant"]["PUB"] != "degenerate" else np.nan
        held = c["invariant"]["PUB"]["held_per_bar"] if c["invariant"]["PUB"] != "degenerate" else np.nan
        print("  %-28s | %+8.2f %+8.1f %+8.1f | %+8.2f %+8.3f %8.0f || %+8.2f %+8.2f | %+8.3f %8.2f"
              % (nm, it(c, "PUB"), leg(c, "PUB", 0)["net"], leg(c, "PUB", 1)["net"], vb(c, "PUB"), sh(c, "PUB"), md,
                 it(c, "PB"), vb(c, "PB"), sh(c, "PB"), held))
    best_nm = max(books, key=lambda k_: vb(books[k_], "PUB") if np.isfinite(vb(books[k_], "PUB")) else -np.inf)

    # ---- cache impact (Q6) ---------------------------------------------------------
    z_old = np.load(OLD_NPZ, allow_pickle=False)
    impact = {}
    print(f"\nCACHE IMPACT -- symmetric F0 books on the rebuilt npz vs {OLD_NPZ.name}   (variant PUB bp/bar | per-leg PUB net)")
    for s in REBUILT:
        new = table[s]
        old, _, _ = run_cell(rank_f0(s, z_old))
        changed = int(np.sum(np.nan_to_num(z[s]) != np.nan_to_num(z_old[s])))
        impact[s] = dict(new_net_bp_bar=vb(new, "PUB"), old_net_bp_bar=vb(old, "PUB"),
                         abs_delta_bp_bar=abs(vb(new, "PUB") - vb(old, "PUB")),
                         new_sharpe=sh(new, "PUB"), old_sharpe=sh(old, "PUB"),
                         new_long_net=leg(new, "PUB", 0)["net"], old_long_net=leg(old, "PUB", 0)["net"],
                         new_short_net=leg(new, "PUB", 1)["net"], old_short_net=leg(old, "PUB", 1)["net"],
                         score_cells_changed=changed)
        d_ = impact[s]
        print(f"  {s:<11} bp/bar old {d_['old_net_bp_bar']:+.2f} new {d_['new_net_bp_bar']:+.2f}  |dz| {d_['abs_delta_bp_bar']:.3f}   "
              f"long {d_['old_long_net']:+.1f} -> {d_['new_long_net']:+.1f}   short {d_['old_short_net']:+.1f} -> {d_['new_short_net']:+.1f}   "
              f"({changed:,} score cells differ)")

    # ---- predictions ----------------------------------------------------------------
    q1 = rank_of["short"].get("skew_63", 10 ** 6) > TOP
    q2 = rank_of["long"].get("hist_L", 10 ** 6) <= TOP
    q3 = rank_of["long"].get("retrace_leg", 10 ** 6) <= TOP
    q4 = n_pos_short >= 1
    q5 = vb(books[best_nm], "PUB") > vb(inc, "PUB")
    q6 = all(np.isfinite(impact[s]["abs_delta_bp_bar"]) and impact[s]["abs_delta_bp_bar"] < 1.0 for s in REBUILT)
    print("\nPREDICTIONS")
    for kk, vv in (("Q1 skew_63's short leg is NOT top-3 of 46 under F0 + PUB  [the retirement, as a test]", q1),
                   ("Q2 hist_L's long leg IS top-3 of 46 under F0 + PUB", q2),
                   ("Q3 retrace_leg's long leg is top-3 too", q3),
                   ("Q4 at least one short leg nets > 0 per trade under F0 + PUB  [against]", q4),
                   ("Q5 the best top-3 x top-3 book beats retrace_leg symmetric (F0) on PUB net bp/bar  [against]", q5),
                   ("Q6 beta_63 / ivol_21 / signed_vol move < 1 bp/bar between old and new cache", q6)):
        print(f"    {'CONFIRMED' if vv else 'FALSIFIED'}  {kk}")
    print(f"    skew_63 short rank {rank_of['short'].get('skew_63')}; hist_L long rank {rank_of['long'].get('hist_L')}; "
          f"retrace_leg long rank {rank_of['long'].get('retrace_leg')};  positive short legs {n_pos_short};  "
          f"best book {best_nm} {vb(books[best_nm], 'PUB'):+.2f} vs retrace_leg sym {vb(inc, 'PUB'):+.2f} bp/bar;  "
          f"cache |dz| " + "  ".join(f"{s} {impact[s]['abs_delta_bp_bar']:.3f}" for s in REBUILT))
    print("    top-3 long: " + "  ".join(f"{s} {v:+.1f}" for v, s in ranked["long"][:TOP])
          + "   top-3 short: " + "  ".join(f"{s} {v:+.1f}" for v, s in ranked["short"][:TOP]))

    OUT.write_text(json.dumps(dict(
        note="D335: the 46 D290 signals as symmetric books under the F0 deal filter, D333 panel, D334 cache; "
             "legs ranked by PUB per-leg net (invariant, per trade). Variant bp/bar, invariant per trade, never "
             "compared (FINDINGS 10). Books: top-3 long x top-3 short leg-wise, plus retrace_leg symmetric.",
        preregistration="54d8d82", depth=DEPTH, k=K0, filter=dict(forms=sorted(V31.F0_FORMS), window=V31.WINDOW,
                                                                    applied=n_ok, drops=drops, excluded_live_pct=pct),
        cache=dict(key_ok=True, note=why), pool=pool, excluded=list(EXCLUDED),
        d329_arms_unfiltered=arm29, identity_worst=worst,
        table=table,
        ranked={lbl: [dict(rank=i + 1, signal=s, pub_net=v) for i, (v, s) in enumerate(ranked[lbl])] for lbl in ranked},
        degenerate=degenerate, percentiles=pct_of, where=where, positive_short_legs=n_pos_short,
        top_long=top_long, top_short=top_short, books=books, incumbent_retrace_leg_f0=inc, best_book=best_nm,
        cache_impact=impact,
        predictions=dict(Q1=bool(q1), Q2=bool(q2), Q3=bool(q3), Q4=bool(q4), Q5=bool(q5), Q6=bool(q6))),
        indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

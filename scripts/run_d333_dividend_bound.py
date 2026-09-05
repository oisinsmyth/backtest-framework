"""D333 -- corporate actions booked as dividends: the bound, and the stack repriced.

    uv run python scripts/run_d333_dividend_bound.py

PRE-REGISTERED AT `7e10066`, committed before the fix and this file existed (R8).

THE FIX IS IN THE PANEL (ragged_panel.load_ragged, DIV_BOUND_RATIO = 0.10,
DIV_BOUND_FRAC = 0.5): a dividend of at least 10% of the close is applied only
if the price fell at least half of what the distribution implies; otherwise it
is dropped and logged. Every runner inherits it through load_ragged, and the
D303 derived-array cache is keyed on ragged_panel.py so it rebuilds.

THIS RUNNER BUILDS BOTH PANELS -- bound on (the new default) and bound off --
and rebuilds the derived arrays for each exactly as run_d303_reference does,
so [1] can reproduce D332's cells under the old panel and [C] can prove the
cache rebuilt under the new one. Then every cell in scope is run under both,
under both spread conventions.

NOTE ON THE SCORE CACHE. beta_63, ivol_21 and signed_vol read
panel.total_log_returns and are therefore stale in temp/d290_scores.npz
under the bound; none of them is in this study's scope and the D290 cache key
does not include ragged_panel.py. Recorded as owed, not fixed here.
"""

from __future__ import annotations

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


V9 = _load("d329", "run_d329_legwise.py")
V6, Y, W, D, M, SP, R, X = V9.V6, V9.Y, V9.W, V9.D, V9.M, V9.SP, V9.R, V9.X
Q, G22 = V6.Q, V6.G22
RP = M.RP

K0, K_INC = 20, 5
OUT = REPO / "data" / "d333_dividend_bound.json"
EXPECT_DROPPED = {"PNK", "GCI", "CLH", "MMP", "GOCOQ"}
EXPECT_KEPT = {"HLSS", "PENN", "BAX"}


def arrays_for(panel, cleaned, z):
    """r1T, mkt, vxT, finT for a panel, built as run_d303_reference.build_cache does."""
    live = panel.live
    T = live.shape[1]
    base = z["warm"] & live
    ctx, r1, vol_raw, _ = D.E.build_inputs(z, base, panel, live, T)
    m = D.L.market_reference(r1, live)
    vol_x = D.E.roll_vol(r1 - m[None, :], live, D.VOL_WIN)
    r1T = np.ascontiguousarray(r1.T)
    return dict(r1T=r1T, mkt=m, vxT=np.ascontiguousarray(vol_x.T), finT=np.isfinite(r1T))


def main() -> int:
    t0 = time.time()
    print("D333  corporate actions booked as dividends")
    panel_new, cleaned = RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)
    panel_old, _ = RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS, dividend_bound=False)
    z = np.load(R.BC.CACHE, allow_pickle=False)
    n, T = panel_new.live.shape
    dropped = panel_new.dividends_dropped
    print(f"  panels built: applied {panel_new.dividends_applied:,} (old {panel_old.dividends_applied:,}), "
          f"dropped {len(dropped)} ({time.time() - t0:.0f}s)")
    D.build_cache(verbose=True)
    A_cache = D.load_cache(mmap=True)
    A_new = arrays_for(panel_new, cleaned, z)
    A_old = arrays_for(panel_old, cleaned, z)
    for A_ in (A_new, A_old):
        A_["rankT"] = np.asarray(A_cache["rankT"])
    g = M.P1.build_grids(panel_new, cleaned)
    HALF_PB = np.ascontiguousarray((SP.corwin_schultz(g["high"], g["low"], panel_new.live) / 2.0 * 1e4).T)
    CLOSE = np.ascontiguousarray(panel_new.closes.T)
    VOL = np.full(CLOSE.shape, np.nan)
    sym = {s: i for i, s in enumerate(panel_new.symbols)}
    pos = {d: i for i, d in enumerate(panel_new.dates)}
    for s, bars in cleaned.items():
        i = sym.get(s)
        if i is None:
            continue
        for st in bars:
            t = pos.get(st.timestamp[:10])
            if t is not None:
                VOL[t, i] = st.bar.volume
    DV = X.roll_mean_T(CLOSE * VOL)
    base = z["warm"] & panel_new.live
    cs = z["cs_spread"]
    HALF_PUB = np.full((T, n), np.nan); HALF_PUB[1:] = (cs[:, :-1] / 2.0 * 1e4).T
    HALF = {"PB": HALF_PB, "PUB": HALF_PUB}
    d332 = json.loads((REPO / "data" / "d332_spread_convention.json").read_text())
    d329 = json.loads((REPO / "data" / "d329_legwise.json").read_text())
    d323 = json.loads((REPO / "data" / "d323_shortlist.json").read_text())
    thirteen = sorted({k.split("/")[0] for k in d323["cells"] if k.endswith(f"/k{K0}/dv0")})
    ev = json.loads(Path(M.B.EVENTS).read_text())
    print(f"  arrays ({time.time() - t0:.0f}s)")

    def run_cell(A_, rankT, k, depth, H, keep=None):
        W.BASE_HOLD = k
        gate = Y.gate_from(rankT, A_["finT"], keep)
        out = {}
        res_v = W.simulate(A_, gate, depth, True, slots=True)
        try:
            c = G22.costed(res_v, (H, CLOSE, DV, A_["finT"]))
            g1 = G22.group1(res_v, c, G22.contributions(res_v, A_["r1T"]), A_["r1T"])
            out["variant"] = dict(net_bp_bar=g1["net_bp_bar"], sharpe_net=g1["sharpe_net"],
                                  gross_bp_bar=g1["gross_bp_bar"], maxdd_bp=g1["maxdd_bp"])
        except ZeroDivisionError:
            out["variant"] = "degenerate"
        res_i = W.simulate(A_, gate, depth, True, slots=False)
        legs = V9.per_leg(res_i, H, CLOSE, A_["r1T"], A_["mkt"])
        out["invariant"] = V9.invariant_legcost(res_i, legs) if all(legs[s] for s in (0, 1)) else "degenerate"
        out["legs"] = {str(s): legs[s] for s in (0, 1)}
        pn = np.sort(np.array([t[3] for t in res_i["trades"]]))[::-1] * 1e4
        tot = pn.sum()
        out["top_share"] = [float(pn[:k_].sum() / tot) if tot else np.nan for k_ in (1, 5, 10)]
        return out, res_v, res_i

    # ---- assertions -------------------------------------------------------
    print("\nASSERTIONS")
    # C. the cache rebuilt under the new panel
    assert np.array_equal(np.asarray(A_cache["r1T"]), A_new["r1T"], equal_nan=True), "[C] cache r1T != new panel"
    assert np.array_equal(np.asarray(A_cache["mkt"]), A_new["mkt"], equal_nan=True), "[C] cache mkt != new panel"
    assert not np.array_equal(A_new["r1T"], A_old["r1T"], equal_nan=True), "[C] the bound changed nothing"
    print("    [C] the derived-array cache rebuilt under the bounded panel, bit-identically to a fresh build")
    # D. the dropped set
    names = {d["symbol"] for d in dropped}
    assert EXPECT_DROPPED <= names, f"[D] missing from dropped: {EXPECT_DROPPED - names}"
    assert not (EXPECT_KEPT & names), f"[D] wrongly dropped: {EXPECT_KEPT & names}"
    for d in dropped:
        assert d["ratio"] >= RP.DIV_BOUND_RATIO and (d["move"] is None or d["move"] > RP.DIV_BOUND_FRAC * d["implied"])
    # every APPLIED dividend at or above the ratio must satisfy the rule
    idx = sym; bad = 0; checked = 0
    drop_keys = {(d["symbol"], d["date"]) for d in dropped}
    for s, items in ev["dividends"].items():
        i = idx.get(s)
        if i is None:
            continue
        own = np.flatnonzero(panel_new.live[i])
        for dte, amt in items:
            t = pos.get(dte[:10])
            if t is None or amt <= 0 or not panel_new.live[i, t] or np.isnan(panel_new.closes[i, t]):
                continue
            ratio = amt / panel_new.closes[i, t]
            if ratio < RP.DIV_BOUND_RATIO or (s, dte[:10]) in drop_keys:
                continue
            k = int(np.searchsorted(own, t)); prev = panel_new.closes[i, own[k - 1]] if k > 0 else np.nan
            move = panel_new.closes[i, t] / prev - 1.0
            checked += 1
            if not (np.isfinite(move) and move <= RP.DIV_BOUND_FRAC * (-ratio / (1 + ratio))):
                bad += 1
    assert bad == 0, f"[D] {bad} applied dividends violate the rule"
    print(f"    [D] the dropped set is exactly the inconsistent set: {len(dropped)} dropped "
          f"({', '.join(sorted(names))}); {checked} applied at >= 10% all satisfy the rule; "
          f"HLSS, PENN, BAX kept")
    # Z. nothing below 10% touched
    diff = panel_new.total_log_returns - panel_old.total_log_returns
    nz = np.argwhere(np.nan_to_num(diff) != 0)
    assert len(nz) == len(dropped), f"[Z] {len(nz)} cells changed, {len(dropped)} dropped"
    for (i, t) in nz:
        d = next(x for x in dropped if x["symbol"] == panel_new.symbols[i] and pos[x["date"]] == t)
        assert abs(diff[i, t] + np.log1p(d["ratio"])) < 1e-12
    print(f"    [Z] exactly {len(nz)} return cells changed, one per dropped dividend, each by -log1p(ratio); "
          f"every dividend below 10% is applied exactly as before")
    # S. the sign audit, in money, on the PNK bar
    i_pnk, t_pnk = sym["PNK"], pos["2016-04-29"]
    ro, rn = A_old["r1T"][t_pnk, i_pnk], A_new["r1T"][t_pnk, i_pnk]
    assert ro > 3.0 and abs(rn) < 0.05, f"[S] PNK old {ro:.3f} new {rn:.3f}"
    assert (+1) * ro > (+1) * rn and (-1) * ro < (-1) * rn
    print(f"    [S] SIGN AUDIT: on the PNK bar a long was paid {100 * ro:+.0f}% and a short {-100 * ro:+.0f}%; "
          f"now both get the price move, {100 * rn:+.1f}%")
    # 1. identity under the OLD panel against D332
    prim, pair = Q.COMPOSITES["C0_incumbent"]
    rkC0 = Q.rank_composite(z, base, prim, pair, n, T)
    old_inc, _, ledger_old = run_cell(A_old, rkC0, K_INC, 2, HALF_PB)
    c2 = d332["incumbent"]["N2/PB"]["variant"]
    worst = max(abs(old_inc["variant"]["net_bp_bar"] - c2["net_bp_bar"]),
                abs(old_inc["variant"]["sharpe_net"] - c2["sharpe_net"]))
    rk = {s: Y.rank_single(z, base, s, n, T) for s in set(thirteen) | {"hist_L", "skew_63"}}
    for s in ("hist_L", "retrace_leg"):
        o, _, _ = run_cell(A_old, rk[s], K0, 2, HALF_PB)
        worst = max(worst, abs(o["invariant"]["net_per_trade"] - d332["cells"][f"{s}/PB"]["invariant"]["net_per_trade"]))
    assert worst < 1e-9, f"[1] {worst:.2e}"
    print(f"    [1] IDENTITY: under the unbounded panel the incumbent and two singles reproduce D332 to {worst:.1e}")
    # L. entries
    new_inc, _, ledger_new = run_cell(A_new, rkC0, K_INC, 2, HALF_PB)
    e_old = {(t[0], t[1], t[4]) for t in ledger_old["trades"]}; e_new = {(t[0], t[1], t[4]) for t in ledger_new["trades"]}
    print(f"    [L] the incumbent's entries: {len(e_old)} old, {len(e_new)} new, {len(e_old ^ e_new)} differ "
          f"(exits keyed on a volatility target that saw the dropped bars)")
    # 6. raises
    broke = False
    try:
        bad_r = A_new["r1T"].copy(); bad_r[t_pnk, i_pnk] += 3.56
        assert np.array_equal(bad_r, A_new["r1T"], equal_nan=True)
    except AssertionError:
        broke = True
    assert broke
    print("    [6] and the check raises on a panel handed a free dividend")

    # ---- the cells ------------------------------------------------------------
    ts = time.time()
    pct = np.full(T, np.nan)
    for t in range(T):
        v = DV[t][A_new["finT"][t] & np.isfinite(DV[t])]
        if v.size > 50:
            pct[t] = np.percentile(v, 28.0)
    keep28 = ~(DV < pct[:, None])
    RK = {"H": rk["hist_L"], "S": rk["skew_63"], "LW": V9.legwise(rk["hist_L"], rk["skew_63"]),
          "RV": V9.legwise(rk["skew_63"], rk["hist_L"])}
    cells = {}
    specs = [("C0 N=2", rkC0, K_INC, 2, None), ("C0 N=19", rkC0, K_INC, 19, None), ("C0 N=2+dv28", rkC0, K_INC, 2, keep28)]
    specs += [(f"{s} k20", rk[s], K0, 2, None) for s in thirteen]
    specs += [(f"{nm} k20", RK[nm], K0, 2, None) for nm in RK]
    for lbl, rT, k, depth, keep in specs:
        for cv in ("PB", "PUB"):
            for pn, A_ in (("old", A_old), ("new", A_new)):
                cells[(lbl, cv, pn)] = run_cell(A_, rT, k, depth, HALF[cv], keep)[0]
    print(f"\n  {len(cells)} cells ({time.time() - ts:.0f}s)")
    vb = lambda c: c["variant"]["net_bp_bar"] if c["variant"] != "degenerate" else np.nan
    sh = lambda c: c["variant"]["sharpe_net"] if c["variant"] != "degenerate" else np.nan
    it = lambda c: c["invariant"]["net_per_trade"] if c["invariant"] != "degenerate" else np.nan
    print("\nTHE STACK, unbounded -> bounded.   variant net bp/bar (Sharpe)  |  invariant net per trade")
    print("  %-18s | %8s %8s %7s %7s | %8s %8s || %8s %8s | %8s %8s"
          % ("cell", "PB old", "PB new", "Sh old", "Sh new", "PUB old", "PUB new", "PB old", "PB new", "PUB old", "PUB new"))
    for lbl, *_ in specs:
        c = {(cv, pn): cells[(lbl, cv, pn)] for cv in ("PB", "PUB") for pn in ("old", "new")}
        print("  %-18s | %+8.2f %+8.2f %+7.3f %+7.3f | %+8.2f %+8.2f || %+8.2f %+8.2f | %+8.2f %+8.2f"
              % (lbl, vb(c["PB", "old"]), vb(c["PB", "new"]), sh(c["PB", "old"]), sh(c["PB", "new"]),
                 vb(c["PUB", "old"]), vb(c["PUB", "new"]), it(c["PB", "old"]), it(c["PB", "new"]),
                 it(c["PUB", "old"]), it(c["PUB", "new"])))
    ts_o, ts_n = cells[("C0 N=2", "PB", "old")]["top_share"], cells[("C0 N=2", "PB", "new")]["top_share"]
    print("\n  incumbent top 1/5/10 trade share of P&L: old %.1f%% / %.1f%% / %.1f%%  ->  new %.1f%% / %.1f%% / %.1f%%"
          % tuple(100 * x for x in ts_o + ts_n))
    hl_o = cells[("hist_L k20", "PB", "old")]["legs"]["0"]["net"]; hl_n = cells[("hist_L k20", "PB", "new")]["legs"]["0"]["net"]
    print(f"  hist_L long leg per trade (PB): {hl_o:+.1f} -> {hl_n:+.1f}")

    # ---- predictions -------------------------------------------------------
    q1 = len(dropped) < 15
    q2 = (vb(cells[("C0 N=2", "PB", "old")]) - vb(cells[("C0 N=2", "PB", "new")]) >= 2.0) and ts_n[0] < 0.141
    q3 = all(abs(vb(cells[("retrace_leg k20", cv, "old")]) - vb(cells[("retrace_leg k20", cv, "new")])) < 1.0 for cv in ("PB", "PUB"))
    q4 = hl_o - hl_n >= 20.0
    def top2(cv, pn):
        return set(sorted(thirteen, key=lambda s: -vb(cells[(f"{s} k20", cv, pn)]) if np.isfinite(vb(cells[(f"{s} k20", cv, pn)])) else 1e9)[:2])
    q5 = all(top2(cv, "old") == top2(cv, "new") for cv in ("PB", "PUB"))
    moves = {s: vb(cells[(f"{s} k20", "PB", "old")]) - vb(cells[(f"{s} k20", "PB", "new")]) for s in thirteen}
    q6 = any(abs(v) > 3.0 for v in moves.values() if np.isfinite(v))
    conc = lambda pn: vb(cells[("C0 N=2", "PB", pn)]) - vb(cells[("C0 N=19", "PB", pn)])
    q7 = abs(conc("old") - conc("new")) < 3.0
    print("\nPREDICTIONS")
    for kk, vv in (("Q1 fewer than 15 dividends dropped", q1),
                   ("Q2 the incumbent's PB net falls >= 2 bp/bar and its top-1 share falls below 14.1%  [load-bearing]", q2),
                   ("Q3 retrace_leg moves < 1 bp/bar on either convention", q3),
                   ("Q4 hist_L's long leg per trade falls >= 20 bp  [load-bearing]", q4),
                   ("Q5 D323's top-2 at k=20 unchanged on both conventions", q5),
                   ("Q6 at least one of the thirteen moves > 3 bp/bar  [against]", q6),
                   ("Q7 concentration (N2 - N19) moves < 3 bp/bar", q7)):
        print(f"    {'CONFIRMED' if vv else 'FALSIFIED'}  {kk}")
    print(f"    dropped {len(dropped)}; incumbent PB {vb(cells[('C0 N=2', 'PB', 'old')]):+.2f} -> {vb(cells[('C0 N=2', 'PB', 'new')]):+.2f}; "
          f"hist_L long leg {hl_o:+.1f} -> {hl_n:+.1f}; concentration {conc('old'):+.2f} -> {conc('new'):+.2f}")
    print("    largest moves among the thirteen (PB bp/bar, old - new): "
          + "  ".join(f"{s} {v:+.2f}" for s, v in sorted(moves.items(), key=lambda kv: -abs(kv[1]))[:5]))

    OUT.write_text(json.dumps(dict(
        note="D333: the dividend bound (ratio >= 0.10 applied only if the price fell >= half the implied move). "
             "old = unbounded panel, new = bounded. PB/PUB spread conventions. Variant bp/bar, invariant per trade.",
        bound=dict(ratio=RP.DIV_BOUND_RATIO, frac=RP.DIV_BOUND_FRAC),
        dividends_applied=dict(old=panel_old.dividends_applied, new=panel_new.dividends_applied),
        dropped=dropped, entries_changed=len(e_old ^ e_new),
        cells={f"{a}/{b}/{c}": v for (a, b, c), v in cells.items()},
        moves_thirteen=moves,
        predictions=dict(Q1=bool(q1), Q2=bool(q2), Q3=bool(q3), Q4=bool(q4), Q5=bool(q5), Q6=bool(q6), Q7=bool(q7))),
        indent=1, default=float))
    print(f"\n  wrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""D339 -- a universe floor on price and dollar volume, as a definition and under
both semantics.

    uv run python scripts/run_d339_universe_floor.py --selftest
    uv run python scripts/run_d339_universe_floor.py [--draws 200]

PRE-REGISTERED in docs/decisions/D339-a-universe-floor-price-and-dollar-volume.md
(committed before this file existed, R8). The cells, predictions and assertions
are that record's; this file only runs them.

The floor (scripts/d339_universe_floor.py): keep[t] = RAW_CLOSE[t-1] >= $5 AND
the dv28 keep mask. RAW_CLOSE undoes the fixture's split adjustment (the census's
factor). Two semantics on the one array, never averaged: REPLACE masks the score
before ranking (the F0 filter's construction; the gate stays full) and STARVE
applies keep inside the rank cut (dv28's construction; the gate has holes).

Cells: RL0 / RL-r / RL-s (retrace_leg symmetric, F0, k=20), C0 / C0-r / C0-s (the
incumbent, unfiltered, k=5), RSI0 / RSI-r and HL0 / HL-r (rsi, hist_L, F0, k=20).
Both lenses, PB and PUB (PUB primary), D337's borrow as new keys. Four groups on
RL-r; the null is rank rotation on RL-r, 200 draws seeded [W.SEED, 339], one
simulation per draw costed under both conventions, TEETH ON THE GROSS NULL.

ASSERTIONS -- properties of code (pre-reg section 6)
  [K] [R] [F] [1] [C] [G] [W] [A] [S] [RQ] [2] [3] [N] [B] [6] -- each printed.
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


V35 = _load("d335", "run_d335_legs_under_filter.py")
V31, PA, V9 = V35.V31, V35.PA, V35.V9
V6, Y, W, D, M, SP, R, X = V35.V6, V35.Y, V35.W, V35.D, V35.M, V35.SP, V35.R, V35.X
G22 = V35.G22
BR = _load("d337b", "d337_borrow.py")
V38 = _load("d338", "run_d338_retrace_leg_candidate.py")   # main guarded; helpers reused
CEN = _load("d339c", "d339_census.py")                       # raw_factor, dv_percentile
UF = _load("d339u", "d339_universe_floor.py")
UF.bind(X, Y)

DEPTH = 2
N_BASE = W.N_BASE
NULL_SEED = [W.SEED, 339]
N_LAG_BARS, LAG_SEED = 200, 339
ANN = 252.0
CONVS = ("PB", "PUB")
OUT = REPO / "data" / "d339_universe_floor.json"
D338_JSON = REPO / "data" / "d338_retrace_leg_candidate.json"
D333_JSON = REPO / "data" / "d333_dividend_bound.json"
CENSUS_JSON = REPO / "data" / "d339_census.json"
EXPECT_APPLIED, EXPECT_PCT = V35.EXPECT_APPLIED, V35.EXPECT_PCT
gate_rows = V38.gate_rows


def same_gate(a, b):
    return all(np.array_equal(a[k], b[k]) for k in ("gateF", "gateR", "gateO"))


def top2(gate, side, t):
    return tuple(int(r) for r in gate_rows(gate, side, t)[:2])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    print("D339  a universe floor on price and dollar volume -- both semantics, eight cells")

    # ---- [K] ---------------------------------------------------------------------
    cache = Path(R.BC.CACHE)
    rp = REPO / "scripts" / "ragged_panel.py"
    assert cache.exists(), "[K] no score cache"
    assert cache.stat().st_mtime > rp.stat().st_mtime, "[K] npz older than ragged_panel.py"
    z_key = str(np.load(cache, allow_pickle=False)["key"])
    assert z_key == R.BC.cache_key(M.B.FIXTURE), "[K] npz key != cache_key() (ragged_panel.py in the tuple)"
    print("    [K] SCORE CACHE: key matches cache_key() with ragged_panel.py in the tuple; npz newer than the builder")

    # ---- data, exactly D338's prep ------------------------------------------------
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
    d338 = json.loads(D338_JSON.read_text())
    d333 = json.loads(D333_JSON.read_text())["cells"]
    census = json.loads(CENSUS_JSON.read_text())
    print(f"  panel {finT.shape}, {int(dead.sum())} delisted names ({el()})")

    # the F0 mask
    dj = json.loads(V31.DEALS.read_text())
    fb, drops, n_ok = V31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live, last_live,
                                      lambda f: f["form"] in V31.F0_FORMS)
    excl = V31.exclusion_mask(fb, n, T, last_live)
    pct = 100.0 * (excl & finT.T).sum() / finT.sum()
    assert n_ok == EXPECT_APPLIED, f"[F] {n_ok} filings applied, expected {EXPECT_APPLIED}"
    assert abs(pct - EXPECT_PCT) < 0.02, f"[F] {pct:.3f}% excluded, expected {EXPECT_PCT}"
    print(f"    [F] F0 MASK: {n_ok:,} filings applied, {pct:.2f}% of live name-bars excluded")

    # ---- the floor ------------------------------------------------------------------
    RAW = UF.raw_price_factor(panel, ev)                       # (T, n) -- CLOSE is (T, n)
    assert RAW.shape == CLOSE.shape, "[R] orientation"
    RAW_CEN = CEN.raw_factor(ev, panel.symbols, panel.dates)
    assert np.array_equal(RAW, RAW_CEN), "[R] the module's factor differs from the census's on the full grid"
    RAW_CLOSE = CLOSE * RAW
    nosplit = [s for s in panel.symbols if not ev["splits"].get(s)]
    assert nosplit and (RAW[:, sym[nosplit[0]]] == 1.0).all(), "[R] factor != 1 without splits"
    tv, iv = pos["2025-01-30"], sym["VSA"]
    assert abs(RAW_CLOSE[tv, iv] - 90.55 * 0.002) < 1e-3, f"[R] VSA raw {RAW_CLOSE[tv, iv]}"
    print(f"    [R] RAW PRICE: module factor == census factor on the full grid; factor == 1 on every bar for "
          f"{nosplit[0]} ({len(nosplit)} names without splits);\n        VSA 2025-01-30 adjusted "
          f"{CLOSE[tv, iv]:.2f} -> as traded ${RAW_CLOSE[tv, iv]:.4f}")
    keep = UF.floor_mask(RAW_CLOSE, DV, finT)
    det = UF.price_floor_detail(RAW_CLOSE, finT)
    share = UF.floor_share(keep, finT)
    px_only = UF.price_floor_pass(RAW_CLOSE, finT)
    print(f"  FLOOR: {100 * share:.2f}% of live name-bars fail (price alone "
          f"{100 * float((~px_only & finT).sum() / finT.sum()):.2f}%, dv28 alone "
          f"{100 * census['keep28_fail_share_live']:.2f}%); NaN prior close on a live name-bar: "
          f"{det['nan_prev_live_now']} (live at t-1: {det['nan_prev_live_now_and_live_prev']}, "
          f"not live at t-1: {det['nan_prev_live_now_not_live_prev']});\n         {det['live_at_bar0']} names live at "
          f"bar 0, where there is no prior close and the price floor is not applied ({el()})")

    # ---- cells --------------------------------------------------------------------------
    def f0_score(sig, kp=None):
        sc = np.where(excl, np.nan, z[sig])
        if kp is not None:
            sc = UF.apply_floor_replace(sc, kp)
        return sc

    def rank1(sig, sc):
        return Y.rank_single({sig: sc}, base, sig, n, T)

    Q = V6.Q
    prim, pair = Q.COMPOSITES["C0_incumbent"]
    C0_KEYS = ("hist_L", "macd_hist", "rsi")

    def rank_c0(kp=None):
        zz = {k: (z[k] if kp is None else UF.apply_floor_replace(z[k], kp)) for k in C0_KEYS}
        return Q.rank_composite(zz, base, prim, pair, n, T)

    def top_five(res, contrib, kmax=5):
        tr = res["trades"]
        pnl = np.array([t[3] for t in tr])
        tot = float(pnl.sum())
        order = sorted(range(len(tr)), key=lambda i: -tr[i][3])
        out = []
        for i in order[:kmax]:
            row, e0, age, p, side = tr[i]
            s = panel.symbols[row]
            seg = r1T[e0:e0 + age, row]
            j = int(e0 + np.nanargmax(np.abs(seg)))
            raw_mv = float(g["close"][row, j] / g["close"][row, j - 1] - 1.0) if j > 0 else np.nan
            dv = [d for d in ev["dividends"].get(s, []) if d[0][:10] == panel.dates[j]]
            out.append(dict(symbol=s, side="long" if side == 0 else "short", entry=panel.dates[e0], hold=int(age),
                            pnl_bp=float(p) * 1e4, share=float(p / tot) if tot != 0 else None, big_day=panel.dates[j],
                            r1=float(seg[j - e0]), raw_close_move=raw_mv, dividend=(dv[0][1] if dv else None),
                            raw_px_prev=float(RAW_CLOSE[e0 - 1, row]) if e0 > 0 else None,
                            dv_pct_entry=CEN.dv_percentile(DV, finT, int(e0), int(row)),
                            passes_keep_at_entry=bool(keep[e0, row]), contrib_bp=float(contrib[i]) * 1e4))
        return out

    def run_cell(name, gate, k, floor):
        W.BASE_HOLD = k
        res_v = W.simulate(A, gate, DEPTH, True, slots=True)
        res_i = W.simulate(A, gate, DEPTH, True, slots=False)
        contrib = G22.contributions(res_v, r1T)
        C = {cv: G22.costed(res_v, G4[cv]) for cv in CONVS}
        G1 = {cv: G22.group1(res_v, C[cv], contrib, r1T) for cv in CONVS}
        G2 = G22.group2(res_v)
        G3 = {cv: G22.group3(res_v, contrib, C[cv], years, dead, CLOSE, HALF[cv]) for cv in CONVS}
        LEGS = {cv: V9.per_leg(res_i, HALF[cv], CLOSE, r1T, mkt) for cv in CONVS}
        INV = {cv: V9.invariant_legcost(res_i, LEGS[cv]) for cv in CONVS}
        BV, _ = V38.borrow_block(res_v, C, INV, excl, CLOSE, T)
        BI, _ = V38.borrow_block(res_i, C, INV, excl, CLOSE, T)
        print(f"  {name:6s} k={k:2d} floor={floor:7s} simulated, both lenses: fill {100 * C['PUB']['fill']:.1f}%, "
              f"PUB net {C['PUB']['net_bp']:+.2f} bp/bar, {len(res_v['trades']):,} trades ({el()})")
        return dict(name=name, k=k, floor=floor, res_v=res_v, res_i=res_i, contrib=contrib, C=C, G1=G1, G2=G2, G3=G3,
                    LEGS=LEGS, INV=INV, borrow=dict(variant=BV, invariant=BI), top5=top_five(res_v, contrib),
                    fill=C["PUB"]["fill"])

    cells, gates, ranks, scores = {}, {}, {}, {}
    # retrace_leg
    scores["RL0"] = f0_score("retrace_leg")
    ranks["RL0"] = rank1("retrace_leg", scores["RL0"])
    gates["RL0"] = Y.gate_from(ranks["RL0"], finT)
    scores["RL-r"] = f0_score("retrace_leg", keep)
    ranks["RL-r"] = rank1("retrace_leg", scores["RL-r"])
    gates["RL-r"] = Y.gate_from(ranks["RL-r"], finT)
    gates["RL-s"] = UF.gate_starved(ranks["RL0"], finT, keep)
    for nm in ("RL0", "RL-r", "RL-s"):
        cells[nm] = run_cell(nm, gates[nm], 20, {"RL0": "none", "RL-r": "replace", "RL-s": "starve"}[nm])
    # the incumbent
    ranks["C0"] = rank_c0()
    gates["C0"] = Y.gate_from(ranks["C0"], finT)
    ranks["C0-r"] = rank_c0(keep)
    gates["C0-r"] = Y.gate_from(ranks["C0-r"], finT)
    gates["C0-s"] = UF.gate_starved(ranks["C0"], finT, keep)
    for nm in ("C0", "C0-r", "C0-s"):
        cells[nm] = run_cell(nm, gates[nm], 5, {"C0": "none", "C0-r": "replace", "C0-s": "starve"}[nm])
    # rsi, hist_L
    for lab, sig in (("RSI", "rsi"), ("HL", "hist_L")):
        s0 = f0_score(sig)
        ranks[lab + "0"] = rank1(sig, s0)
        gates[lab + "0"] = Y.gate_from(ranks[lab + "0"], finT)
        sr = f0_score(sig, keep)
        ranks[lab + "-r"] = rank1(sig, sr)
        gates[lab + "-r"] = Y.gate_from(ranks[lab + "-r"], finT)
        cells[lab + "0"] = run_cell(lab + "0", gates[lab + "0"], 20, "none")
        cells[lab + "-r"] = run_cell(lab + "-r", gates[lab + "-r"], 20, "replace")

    RL0, RLR, RLS = cells["RL0"], cells["RL-r"], cells["RL-s"]
    C0, C0R = cells["C0"], cells["C0-r"]

    # ---- assertions -------------------------------------------------------------------
    print("\nASSERTIONS")
    # [1] RL0 == D338; C0 == D333's new-panel cells
    worst = 0.0
    for cv in CONVS:
        worst = max(worst,
                    abs(RL0["G1"][cv]["net_bp_bar"] - d338["group1"][cv]["net_bp_bar"]),
                    abs(RL0["G1"][cv]["sharpe_net"] - d338["group1"][cv]["sharpe_net"]),
                    abs(RL0["INV"][cv]["net_per_trade"] - d338["invariant"][cv]["net_per_trade"]),
                    abs(RL0["LEGS"][cv][0]["net"] - d338["legs"][cv]["0"]["net"]),
                    abs(RL0["LEGS"][cv][1]["net"] - d338["legs"][cv]["1"]["net"]))
    assert worst < 1e-9, f"[1] RL0 vs D338 {worst:.2e}"
    worst_c = 0.0
    for cv in CONVS:
        ref = d333[f"C0 N=2/{cv}/new"]
        worst_c = max(worst_c,
                      abs(C0["G1"][cv]["net_bp_bar"] - ref["variant"]["net_bp_bar"]),
                      abs(C0["G1"][cv]["sharpe_net"] - ref["variant"]["sharpe_net"]),
                      abs(C0["INV"][cv]["net_per_trade"] - ref["invariant"]["net_per_trade"]))
    assert worst_c < 1e-9, f"[1] C0 vs D333 {worst_c:.2e}"
    print(f"    [1] IDENTITY: RL0 reproduces D338 to {worst:.1e} (variant net and Sharpe, invariant per trade, both "
          f"legs, PB and PUB);\n        C0 reproduces D333's 'C0 N=2/{{PB,PUB}}/new' to {worst_c:.1e} (variant net "
          f"and Sharpe, invariant per trade)")

    # [C] causality, second implementation
    ts = time.time()
    keep_ind = UF.keep_independent(CLOSE, VOL, RAW, finT, X.WIN)
    assert np.array_equal(keep_ind, keep), "[C] the independent floor differs from the production floor on clean data"
    rng = np.random.default_rng(339)
    bars_full = np.sort(rng.choice(np.arange(X.WIN + 2, T - 2), size=20, replace=False))
    n_bite_full = 0
    for t in bars_full:
        C2, V2 = CLOSE.copy(), VOL.copy()
        C2[t:] *= 1.37
        V2[t:] *= 1.37
        k2 = UF.keep_independent(C2, V2, RAW, finT, X.WIN)
        assert np.array_equal(k2[:t], keep[:t]), f"[C] bar {t}: the floor before t moved when data from t on was perturbed"
        n_bite_full += int((k2[t + 1:] != keep[t + 1:]).any())
    assert n_bite_full > 0, "[C] the perturbation never bit -- the check cannot fail"
    # 200 bars, production path, bar t alone perturbed: keep[t] unchanged, keep[t+1] disturbed somewhere
    bars_200 = np.sort(rng.choice(np.arange(X.WIN + 2, T - 2), size=200, replace=False))
    XV = CLOSE * VOL
    X2 = XV.copy()
    n_bite_1 = 0
    for t in bars_200:
        X2[t] = (CLOSE[t] * 1.37) * (VOL[t] * 1.37)
        DV2 = X.roll_mean_T(X2)
        X2[t] = XV[t]
        rc2 = np.stack([RAW_CLOSE[t - 1], RAW_CLOSE[t] * 1.37, RAW_CLOSE[t + 1]])
        px2 = UF.price_floor_pass(rc2, finT[t - 1:t + 2])
        kt = px2[1] & X.keep_mask(DV2[t:t + 1], finT[t:t + 1], UF.DV_PCT, True)[0]
        assert np.array_equal(kt, keep[t]), f"[C] bar {t}: keep[t] moved when bar t itself was perturbed"
        kt1 = px2[2] & X.keep_mask(DV2[t + 1:t + 2], finT[t + 1:t + 2], UF.DV_PCT, True)[0]
        n_bite_1 += int((kt1 != keep[t + 1]).any())
    assert n_bite_1 > 0, "[C] perturbing bar t never moved keep[t+1] -- the check cannot fail"
    print(f"    [C] CAUSALITY: a second implementation (per-name cumsum, per-bar percentile, never keep_mask) equals "
          f"the floor on the full grid;\n        every price and volume from bar t on x1.37 leaves keep[:t] identical "
          f"on 20 sampled bars (the perturbation moved keep after t on {n_bite_full} of 20);\n        bar t alone "
          f"x1.37 leaves keep[t] identical on 200 sampled bars (and moved keep[t+1] on {n_bite_1} of 200) "
          f"({time.time() - ts:.0f}s)")

    # [G] keep = all-True reproduces RL0 under both semantics; fill; share
    ones = np.ones_like(keep)
    sc_g = UF.apply_floor_replace(scores["RL0"], ones)
    assert np.array_equal(sc_g, scores["RL0"], equal_nan=True), "[G] all-True replace changed the score"
    rk_g = rank1("retrace_leg", sc_g)
    assert np.array_equal(rk_g, ranks["RL0"]), "[G] all-True replace changed the rank"
    g_rep = Y.gate_from(rk_g, finT)
    g_stv = UF.gate_starved(ranks["RL0"], finT, ones)
    assert same_gate(g_rep, gates["RL0"]) and same_gate(g_stv, gates["RL0"]), "[G] all-True gate differs"
    W.BASE_HOLD = 20
    for gg in (g_rep, g_stv):
        rr = W.simulate(A, gg, DEPTH, True, slots=True)
        assert np.array_equal(rr["book"], RL0["res_v"]["book"], equal_nan=True) and rr["trades"] == RL0["res_v"]["trades"], "[G] all-True book differs"
    assert RLR["fill"] == 1.0, f"[G] replace fill {RLR['fill']}"
    assert RLS["fill"] < 1.0, f"[G] starve fill {RLS['fill']}"
    cen_c = census["universe"]["overall"]["c"]
    assert abs(share - cen_c) < 1e-9, f"[G] floor share {share} vs census {cen_c}"
    print(f"    [G] GATE: keep = all-True reproduces RL0 bit-identically (rank, gate, book, ledger) under replace AND "
          f"starve; fill {100 * RLR['fill']:.1f}% under replace, {100 * RLS['fill']:.1f}% under starve;\n        the "
          f"floor's share of live name-bars {100 * share:.4f}% == census (c) {100 * cen_c:.4f}% to "
          f"{abs(share - cen_c):.1e}")

    # [W] replace and starve enter the same top-2 wherever the unfloored top-2 pass
    rng = np.random.default_rng(3390)
    q_both, q_t_only = [], []
    for t in range(2, T):
        ok2 = True
        ok_t = True
        for side in (0, 1):
            tp = top2(gates["RL0"], side, t)
            if len(tp) < 2:
                ok2 = ok_t = False
                break
            if not all(keep[t, r] for r in tp):
                ok_t = False
            if not all(keep[t, r] and keep[t - 1, r] for r in tp):
                ok2 = False
        if ok2:
            q_both.append(t)
        if ok_t:
            q_t_only.append(t)
    bars_w = rng.choice(np.array(q_both), size=200, replace=False)
    n_agree_s, n_agree_r = 0, 0
    for t in bars_w:
        for side in (0, 1):
            a0, ar, as_ = top2(gates["RL0"], side, int(t)), top2(gates["RL-r"], side, int(t)), top2(gates["RL-s"], side, int(t))
            assert set(ar) == set(a0), f"[W] bar {t} side {side}: replace top-2 {ar} vs unfloored {a0}"
            assert set(as_) == set(a0), f"[W] bar {t} side {side}: starve top-2 {as_} vs unfloored {a0}"
    n_flip = len(q_t_only) - len(q_both)          # q_both is a subset of q_t_only by construction
    print(f"    [W] on 200 sampled bars where the unfloored top-2 per side pass the floor (at t for starve and at t-1 "
          f"for replace -- the ranker lags the masked score), replace, starve and RL0 enter the SAME top-2 per side;"
          f"\n        {len(q_both):,} of {T - 2:,} bars qualify; {len(q_t_only):,} qualify on keep[t] alone "
          f"({n_flip} of those fail at t-1)")

    # [A] lag audit on RL-r's long gate
    rng = np.random.default_rng(LAG_SEED)
    nonempty = np.array([t for t in range(1, T) if gate_rows(gates["RL-r"], 0, t).size > 0])
    bars = rng.choice(nonempty, size=N_LAG_BARS, replace=False)
    n_diff_unlagged = 0
    for t in bars:
        got = set(int(r) for r in gate_rows(gates["RL-r"], 0, int(t)))
        want = V38.rebuild_long_set(scores["RL-r"], base, finT, int(t), 1)
        assert got == want, f"[A] bar {t}: gate {sorted(got)[:6]}... rebuilt {sorted(want)[:6]}..."
        if V38.rebuild_long_set(scores["RL-r"], base, finT, int(t), 0) != got:
            n_diff_unlagged += 1
    assert n_diff_unlagged > N_LAG_BARS // 2, f"[A] the unlagged rebuild agrees on {N_LAG_BARS - n_diff_unlagged} bars"
    print(f"    [A] LAG AUDIT: RL-r's long-leg gate rebuilt from the floored score at t-1 (floor at t-1, base at t) by a "
          f"direct stable argsort equals the gate on all {N_LAG_BARS} sampled bars;\n        the rebuild from the "
          f"score at t differs on {n_diff_unlagged} of them")

    # [S] sign in money, RL-r variant ledger
    res_v = RLR["res_v"]
    v_syn, mt0 = np.array([0.01, 0.02]), np.zeros(2)
    assert (v_syn - mt0).sum() > 0 and -(v_syn - mt0).sum() < 0, "[S] synthetic sign"
    rec = V38.ledger_pnl_recomputed(res_v["trades"], r1T, mkt)
    pnl_v = np.array([t[3] for t in res_v["trades"]])
    worst_s = float(np.abs(rec - pnl_v).max())
    assert worst_s < 1e-12, f"[S] {worst_s:.2e}"
    longs = np.array([t[4] == 0 for t in res_v["trades"]])
    ex = np.array([float((r1T[e0:e0 + age, row] - mkt[e0:e0 + age]).sum()) for row, e0, age, _p, _s in res_v["trades"]])
    assert (pnl_v[longs & (ex > 0)] > 0).all() and (pnl_v[~longs & (ex < 0)] > 0).all(), "[S] sign"
    print(f"    [S] SIGN IN MONEY: synthetic long over a rise +{(v_syn - mt0).sum():.2f}, short -{(v_syn - mt0).sum():.2f}; "
          f"every RL-r trade equals sgn*sum(v - mt) to {worst_s:.1e};\n        a favourable excess path pays "
          f"positively on every long and every short")

    # [RQ]
    W.BASE_HOLD = 20
    res_c = W.simulate(A, gates["RL-r"], DEPTH, True, slots=True, accumulate="compound")
    ks = [(t[0], t[1], t[2], t[4]) for t in res_v["trades"]]
    kc = [(t[0], t[1], t[2], t[4]) for t in res_c["trades"]]
    assert ks == kc, "[RQ] compound changed the ledger's entries or exits"
    pnl_c = np.array([t[3] for t in res_c["trades"]])
    assert not np.allclose(pnl_v, pnl_c), "[RQ] the two accumulations agree"
    assert abs(RLR["G1"]["PUB"]["trade_mean_bp"] - float(pnl_v.mean()) * 1e4) < 1e-9, "[RQ] group 1 scores the wrong ledger"
    print(f"    [RQ] RIGHT QUANTITY: same {len(ks):,} entries/exits under compound accumulation, "
          f"{int((pnl_v != pnl_c).sum()):,} P&Ls differ (mean {float(pnl_v.mean()) * 1e4:+.1f} vs "
          f"{float(pnl_c.mean()) * 1e4:+.1f} bp); group 1 scores the SUMMED ledger")

    # [2] reconciliation on RL-r
    contrib = RLR["contrib"]
    C = RLR["C"]
    attributed = float(contrib.sum()) / C["PUB"]["bars"] * 1e4
    resid = C["PUB"]["gross_bp"] - attributed
    n_open = int(res_v["ent"].sum()) - len(res_v["trades"])
    gap_bars, first, TT = G22.unattributed(res_v)
    assert 0 <= n_open <= 2 * DEPTH, f"[2] {n_open} positions unaccounted"
    assert first >= TT - 20, f"[2] the ledger misses held bars from bar {first} of {TT} -- a HOLE"
    assert abs(resid) < 1.0, f"[2] {resid:.4f} bp unattributed"
    ratio = float(pnl_v.mean()) / float(contrib.mean())
    assert 1.5 < ratio < 2.5, f"[2] trade P&L is {ratio:.2f}x its contribution"
    broke = False
    try:
        short = [t for i, t in enumerate(res_v["trades"]) if i != len(res_v["trades"]) // 2]
        _, f2, _ = G22.unattributed(res_v, short)
        assert f2 >= TT - 20
    except AssertionError:
        broke = True
    assert broke, "[2] the accounting accepted a ledger missing a trade"
    print(f"    [2] RECONCILIATION: {len(res_v['trades']):,} closed RL-r trades reconstruct gross to {resid:+.4f} bp; "
          f"{n_open} positions open at T ({gap_bars:.0f} position-bars, none before bar {first} of {TT});\n        "
          f"trade P&L is {ratio:.2f}x its contribution; the check rejects a ledger missing one mid-run trade")

    # [3] symmetric trim
    k1 = max(1, pnl_v.size // 100)
    broke = False
    try:
        _, kt_, kb_ = G22.trim_sym(pnl_v, k1, k1 + 1)
        assert kt_ == kb_
    except AssertionError:
        broke = True
    assert broke and RLR["G2"]["n_dropped_top"] == RLR["G2"]["n_dropped_bottom"], "[3]"
    print(f"    [3] the 1% trim is symmetric (k={k1}) and the check rejects a trim one deeper on the bottom")

    # [N] rotation moves the book
    rot = np.roll(ranks["RL-r"], 501, axis=1)
    g_rot = Y.gate_from(rot, finT)
    assert not np.array_equal(g_rot["gateF"], gates["RL-r"]["gateF"]), "[N] rotation is inert"
    r_rot = W.simulate(A, g_rot, DEPTH, True)
    gross_rot = float(r_rot["book"][r_rot["mask"]].mean()) * 1e4
    assert abs(gross_rot - C["PUB"]["gross_bp"]) > 1e-9, "[N] same book"
    print(f"    [N] CAUSALITY: rotating RL-r's rank array by 501 bars moves gross {C['PUB']['gross_bp']:+.2f} -> "
          f"{gross_rot:+.2f} bp/bar")

    # [B] borrow, every cell
    worst_b = max(max(c["borrow"]["variant"]["reconcile_worst"], c["borrow"]["invariant"]["reconcile_worst"]) for c in cells.values())
    assert worst_b < 1e-9, f"[B] reconcile {worst_b:.2e}"
    assert RLR["borrow"]["variant"]["house_flat_worst"] < 1e-12, f"[B] house {RLR['borrow']['variant']['house_flat_worst']:.2e}"
    print(f"    [B] BORROW: per bar x cnt1 == per trade to {worst_b:.1e} bp on every cell, both lenses; house == 300/252 "
          f"to {RLR['borrow']['variant']['house_flat_worst']:.1e} on RL-r's covered short bars")

    # [6] raises
    broke = False
    try:
        bk = RL0["res_v"]["book"].copy()
        bk[np.flatnonzero(RL0["res_v"]["mask"])[:200]] += 5e-4
        bad = G22.costed(dict(RL0["res_v"], book=bk), G4["PUB"])
        assert abs(bad["net_bp"] - d338["group1"]["PUB"]["net_bp_bar"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6] [1] passed a book handed free money"
    print("    [6] and [1] raises on a book handed +5 bp on 200 masked bars")

    if a.selftest:
        print(f"\nOK  assertions pass  ({el()})")
        return 0

    # ---- the null on RL-r (and RL-s if time allows) ------------------------------------
    def null_on(gate, Cc, draws):
        ts = time.time()
        rng = np.random.default_rng(NULL_SEED)
        offs = rng.choice(np.arange(1, N_BASE), size=draws)
        NG, NSG, NSN = [], [], {cv: [] for cv in CONVS}
        W.BASE_HOLD = 20
        for s_ in offs:
            r = W.simulate(A, gate, DEPTH, True, shift=int(s_))
            okm = r["mask"]
            if int(okm.sum()) < 200:
                continue
            b = r["book"][okm]
            NG.append(float(b.mean()) * 1e4)
            NSG.append(float(b.mean() / b.std(ddof=1) * np.sqrt(ANN)))
            for cv in CONVS:
                NSN[cv].append(G22.costed(r, G4[cv])["sharpe_net"])
        NG, NSG = np.array(NG), np.array(NSG)
        NSN = {cv: np.array(NSN[cv]) for cv in CONVS}
        assert NG.size >= min(195, draws - 5), f"[N] only {NG.size} valid draws"
        out = dict(construction="rank rotation inside the 25-name gate", seed=NULL_SEED, draws=int(NG.size),
                   gross_bp=G22.dist(NG, Cc["PUB"]["gross_bp"]), sharpe_gross=G22.dist(NSG, Cc["PUB"]["sharpe_gross"]),
                   sharpe_net={cv: G22.dist(NSN[cv], Cc[cv]["sharpe_net"]) for cv in CONVS},
                   seconds=time.time() - ts)
        out["teeth_gross"] = bool(out["gross_bp"]["p95"] > 0)
        return out

    NULL = {"RL-r": null_on(gates["RL-r"], RLR["C"], a.draws)}
    print(f"\n    [N] RL-r null: {NULL['RL-r']['draws']} of {a.draws} draws valid ({NULL['RL-r']['seconds']:.0f}s)")
    if time.time() - t0 + NULL["RL-r"]["seconds"] < 600:
        NULL["RL-s"] = null_on(gates["RL-s"], RLS["C"], a.draws)
        print(f"    [N] RL-s null: {NULL['RL-s']['draws']} of {a.draws} draws valid ({NULL['RL-s']['seconds']:.0f}s) -- "
              f"run because total runtime allowed (< 10 min)")
    else:
        print("    RL-s null NOT run: runtime budget exceeded")

    # ---- report ---------------------------------------------------------------------
    print("\n" + "=" * 150)
    print("PER CELL -- variant lens bp/bar (PB and PUB), invariant per trade (PUB), the top trade")
    print("=" * 150)
    print("  %-6s %-7s %5s %7s %7s %7s %7s %7s %7s %7s %8s %8s   %-6s %6s %9s %6s" % (
        "cell", "floor", "fill", "gross", "PBnet", "PUBnet", "PUBshp", "maxDD", "hs_PUB", "px", "DV$M", "inv/trd",
        "top", "share", "raw_px", "dvpct"))
    for nm, c in cells.items():
        C, tp = c["C"], c["top5"][0]
        print("  %-6s %-7s %4.0f%% %+7.2f %+7.2f %+7.2f %+7.3f %7.0f %7.2f %7.2f %8.2f %+8.1f   %-6s %5.1f%% %9s %6s" % (
            nm, c["floor"], 100 * c["fill"], C["PUB"]["gross_bp"], C["PB"]["net_bp"], C["PUB"]["net_bp"],
            C["PUB"]["sharpe_net"], C["PUB"]["maxdd_bp"], C["PUB"]["held_half_spread"], C["PUB"]["held_price"],
            C["PUB"]["held_dv"] / 1e6, c["INV"]["PUB"]["net_per_trade"], tp["symbol"], 100 * (tp["share"] or 0),
            ("$%.4f" % tp["raw_px_prev"]) if tp["raw_px_prev"] is not None else "nan",
            ("%.2f" % tp["dv_pct_entry"]) if np.isfinite(tp["dv_pct_entry"]) else "nan"))

    def print_top5(c):
        print(f"\n  TOP FIVE TRADES -- {c['name']} (floor: {c['floor']})")
        print("  %-6s %-5s %-10s %3s %9s %6s %-10s %7s %7s %6s %9s %5s %4s" % (
            "sym", "side", "entry", "hld", "pnl_bp", "share", "big_day", "r1%", "raw%", "div", "raw_px", "dvpct", "keep"))
        for r in c["top5"]:
            print("  %-6s %-5s %-10s %3d %+9.0f %5.1f%% %-10s %+7.1f %+7.1f %6s %9s %5s %4s" % (
                r["symbol"], r["side"], r["entry"], r["hold"], r["pnl_bp"], 100 * (r["share"] or 0), r["big_day"],
                100 * r["r1"], 100 * r["raw_close_move"] if np.isfinite(r["raw_close_move"]) else np.nan,
                ("%.3f" % r["dividend"]) if r["dividend"] is not None else "-",
                ("$%.4f" % r["raw_px_prev"]) if r["raw_px_prev"] is not None else "nan",
                ("%.2f" % r["dv_pct_entry"]) if np.isfinite(r["dv_pct_entry"]) else "nan", "yes" if r["passes_keep_at_entry"] else "NO"))

    def print_group1(c):
        G1, BV, BI = c["G1"], c["borrow"]["variant"], c["borrow"]["invariant"]
        ROW = "  %-34s %14s %14s"
        f2 = lambda v: "%+.2f" % v
        f3 = lambda v: "%+.3f" % v
        pc = lambda v: "%.1f%%" % (100 * v)
        print("\n" + "=" * 78)
        print(f"GROUP 1 -- {c['name']} (floor: {c['floor']}): PERFORMANCE, NET AND GROSS, PB and PUB")
        print("=" * 78)
        print(ROW % ("", "PB", "PUB"))
        for label, key, fn in (("gross bp/bar", "gross_bp_bar", f2), ("cost bp/bar", "cost_bp_bar", lambda v: "%.2f" % v),
                               ("NET bp/bar", "net_bp_bar", f2), ("vol bp/bar", "vol_bp_bar", lambda v: "%.1f" % v),
                               ("gross Sharpe", "sharpe_gross", f3), ("NET Sharpe", "sharpe_net", f3),
                               ("gross t", "t_gross", f2), ("annualised NET %", "ann_net_pct", f2),
                               ("maxDD bp", "maxdd_bp", lambda v: "%.0f" % v),
                               ("exposure (bars / panel)", "exposure_bars", pc), ("fill of 4 slots", "fill", pc),
                               ("names held per bar", "held_per_bar", lambda v: "%.2f" % v),
                               ("turnover/bar (names HELD)", "turnover_held", lambda v: "%.4f" % v),
                               ("held half-spread bp/side", "held_half_spread", lambda v: "%.2f" % v),
                               ("held median price", "held_price", lambda v: "$%.2f" % v),
                               ("held median $ volume", "held_dollar_volume", lambda v: "$%.2fM" % (v / 1e6)),
                               ("2c = rt_total / 2", "two_c_bp", lambda v: "%.2f" % v),
                               ("mean move per TRADE bp", "trade_mean_bp", f2),
                               ("mean move / 2c", "trade_mean_over_2c", lambda v: "%.2fx" % v),
                               ("BREAKEVEN half-spread /side", "breakeven_half_spread_bp_side", lambda v: "%.2f" % v),
                               ("breakeven / measured", "breakeven_multiple", lambda v: "%.2fx" % v)):
            print(ROW % (label, fn(G1["PB"][key]), fn(G1["PUB"][key])))
        print("  BORROW (new keys; net_bp untouched), variant book bp/bar:")
        for scheme in ("gc_htb", "house"):
            print("  %-10s PB net %+.2f -> %+.2f (borrow %.3f)   PUB net %+.2f -> %+.2f (borrow %.3f)" % (
                scheme, BV[scheme]["PB"]["net_bp"], BV[scheme]["PB"]["net_bp_borrow"], BV[scheme]["PB"]["borrow_bp_bar"],
                BV[scheme]["PUB"]["net_bp"], BV[scheme]["PUB"]["net_bp_borrow"], BV[scheme]["PUB"]["borrow_bp_bar"]))
        print(f"  HTB share of short position-bars {100 * BV['htb_share_short_bars']:.1f}% (variant), "
              f"{100 * BI['htb_share_short_bars']:.1f}% (invariant)")
        L = c["LEGS"]["PUB"]
        print("  invariant lens, per trade (PUB): long %+.1f net on %+.1f gross (t %.2f, %d trades); short %+.1f on %+.1f (t %.2f, %d); "
              "both %+.1f net/trade" % (L[0]["net"], L[0]["gross"], L[0]["t"], L[0]["trades"], L[1]["net"], L[1]["gross"],
                                        L[1]["t"], L[1]["trades"], c["INV"]["PUB"]["net_per_trade"]))

    # RL-r: the four groups
    print_group1(RLR)
    G2, G3 = RLR["G2"], RLR["G3"]
    print("\n" + "=" * 78)
    print("GROUP 2 -- RL-r TRADE DISTRIBUTION, BOTH TAILS TRIMMED (variant ledger)")
    print("=" * 78)
    pc = lambda v: "%.1f%%" % (100 * v)
    for label, key, fn in (("trades", "n", lambda v: "%d" % v), ("mean bp", "mean_bp", lambda v: "%+.1f" % v),
                           ("MEDIAN bp", "median_bp", lambda v: "%+.1f" % v),
                           ("mean BELOW median?", "mean_below_median", lambda v: "YES" if v else "no"),
                           ("win rate", "win_rate", pc), ("payoff", "payoff", lambda v: "%.2f" % v),
                           ("holding run mean", "holding_run_mean", lambda v: "%.2f" % v),
                           ("holding run median", "holding_run_median", lambda v: "%.1f" % v),
                           ("skew", "skew", lambda v: "%+.2f" % v), ("kurtosis (raw)", "kurtosis_raw", lambda v: "%.1f" % v),
                           ("mean EX-TOP 1%", "mean_ex_top_bp", lambda v: "%+.1f" % v),
                           ("mean EX-BOTTOM 1%", "mean_ex_bottom_bp", lambda v: "%+.1f" % v),
                           ("mean TRIMMED both", "mean_trimmed_bp", lambda v: "%+.1f" % v),
                           ("top 1% share of P&L", "top1_share", lambda v: "%+.0f%%" % (100 * v)),
                           ("bottom 1% share of P&L", "bottom1_share", lambda v: "%+.0f%%" % (100 * v))):
        print("  %-34s %14s" % (label, fn(G2[key])))
    print("\n" + "=" * 78)
    print("GROUP 3 -- RL-r WHAT THE WINNERS DEPEND ON (each cut charged ITS OWN 2c; PUB)")
    print("=" * 78)
    g3 = G3["PUB"]
    print(f"  names traded {g3['names']}, NAMES TO HALF THE P&L {g3['names_to_half_pnl']}, top 1/5/10 name share "
          f"{100 * g3['top1_name_share']:.1f}% / {100 * g3['top5_name_share']:.1f}% / {100 * g3['top10_name_share']:.1f}%")
    print(f"  years {g3['years']}: gross-positive {g3['years_profitable_gross']}, NET-positive (PUB) {g3['years_profitable_net']}; "
          f"(PB) {G3['PB']['years_profitable_net']}")
    print("  %-14s %7s %8s %8s %8s %7s %9s" % ("cut", "P&L%", "trades", "mean bp", "own 2c", "x2c", "net/trade"))
    for label, key in (("dead", "dead"), ("alive", "alive"), ("era 1st half", "era_first_half"),
                       ("era 2nd half", "era_second_half"), ("price LOW", "price_low"), ("price MID", "price_mid"),
                       ("price HIGH", "price_high")):
        x = g3[key]
        print("  %-14s %+6.1f%% %8d %+8.1f %8.1f %6.2fx %+9.1f" % (label, 100 * x["share_pnl"], x["n"], x["mean_bp"],
                                                                  x["two_c_bp"], x["mean_over_2c"], x["net_per_trade_bp"]))
    print("  price terciles cut at $%.2f / $%.2f" % tuple(g3["price_cuts"]))
    print("  by year, gross bp/bar: " + " ".join(f"{y}:{v:+.0f}" for y, v in sorted(g3["gross_by_year"].items())))
    print("\n" + "=" * 78)
    print("GROUP 4 -- THE NULL on RL-r: p50 AND p95, TEETH ON THE GROSS NULL")
    print("=" * 78)
    for cellnm, NL in NULL.items():
        print(f"  {cellnm}:")
        print("  %-18s %10s %10s %10s %10s %10s" % ("statistic", "score", "null p50", "null p95", "null max", "p"))
        for nm_, d_ in (("gross bp/bar", NL["gross_bp"]), ("gross Sharpe", NL["sharpe_gross"]),
                        ("net Sharpe PB", NL["sharpe_net"]["PB"]), ("net Sharpe PUB", NL["sharpe_net"]["PUB"])):
            print("  %-18s %10.3f %10.3f %10.3f %10.3f %10.4f" % (nm_, d_["score"], d_["p50"], d_["p95"], d_["max"], d_["p"]))
        print(f"  the GROSS null has teeth (p95 > 0 on gross bp/bar): {'yes' if NL['teeth_gross'] else 'NO -- R7 flag'}; "
              f"net-Sharpe p95 PB {NL['sharpe_net']['PB']['p95']:+.3f} PUB {NL['sharpe_net']['PUB']['p95']:+.3f} (the cost test)")
    print_top5(RLR)

    # RL-s and RL0: group 1 + top five
    print_group1(RLS)
    print_top5(RLS)
    print_group1(RL0)
    print_top5(RL0)
    print_top5(C0)
    print_top5(C0R)

    # ---- predictions --------------------------------------------------------------------
    nl = NULL["RL-r"]
    rl0_net, rlr_net, rls_net = RL0["C"]["PUB"]["net_bp"], RLR["C"]["PUB"]["net_bp"], RLS["C"]["PUB"]["net_bp"]
    tp_r, tp_c0r = RLR["top5"][0], C0R["top5"][0]
    P = {}
    P["P1"] = bool(rlr_net < 0.6 * d338["group1"]["PUB"]["net_bp_bar"])
    P["P2"] = bool(g3["top5_name_share"] < 0.30 and g3["names_to_half_pnl"] > 15)
    P["P3"] = bool(nl["gross_bp"]["score"] > nl["gross_bp"]["p95"] and nl["gross_bp"]["p95"] > 0)
    P["P4"] = bool(G2["mean_trimmed_bp"] > RLR["G1"]["PUB"]["two_c_bp"])
    P["P5"] = bool(tp_r["share"] < 0.05 and tp_r["dv_pct_entry"] > 0.28)
    P["P6"] = bool(abs(C0R["C"]["PUB"]["net_bp"] - C0["C"]["PUB"]["net_bp"]) < 3.0)
    P["P7"] = bool(tp_c0r["symbol"] != "VSA" and tp_c0r["share"] < 0.10)
    P["P8"] = bool(RLR["fill"] == 1.0 and RLS["fill"] < 0.90)
    P["P9"] = bool(rls_net < rlr_net and (rlr_net - rls_net) < (rl0_net - rlr_net))
    P["check"] = bool(abs(share - cen_c) < 1e-9)
    V = lambda k: "CONFIRMED" if P[k] else "FALSIFIED"
    print("\nPREDICTIONS (pre-reg section 4; P3 load-bearing; P6 and P9 against)")
    print(f"  P1 RL-r PUB net < 0.6 x {d338['group1']['PUB']['net_bp_bar']:+.2f} = {0.6 * d338['group1']['PUB']['net_bp_bar']:+.2f}: "
          f"{V('P1')} -- {rlr_net:+.2f} bp/bar (RL0 {rl0_net:+.2f})")
    print(f"  P2 top-5 name share < 30%, names to half > 15: {V('P2')} -- {100 * g3['top5_name_share']:.1f}%, {g3['names_to_half_pnl']}")
    print(f"  P3 (LOAD-BEARING) RL-r gross above the gross null's p95, p95 > 0: {V('P3')} -- gross {nl['gross_bp']['score']:+.3f} "
          f"vs p95 {nl['gross_bp']['p95']:+.3f} (p50 {nl['gross_bp']['p50']:+.3f}, max {nl['gross_bp']['max']:+.3f}, p {nl['gross_bp']['p']:.4f})")
    print(f"  P4 symmetric trim clears the PUB round trip: {V('P4')} -- trimmed {G2['mean_trimmed_bp']:+.1f} vs 2c "
          f"{RLR['G1']['PUB']['two_c_bp']:.1f} bp")
    print(f"  P5 RL-r top trade < 5% of ledger and DV percentile > 0.28: {V('P5')} -- {tp_r['symbol']} {100 * tp_r['share']:.2f}%, "
          f"dvpct {tp_r['dv_pct_entry']:.2f}, raw px ${tp_r['raw_px_prev']:.4f}")
    print(f"  P6 (against) |C0-r - C0| PUB net < 3: {V('P6')} -- C0 {C0['C']['PUB']['net_bp']:+.2f}, C0-r {C0R['C']['PUB']['net_bp']:+.2f}, "
          f"diff {C0R['C']['PUB']['net_bp'] - C0['C']['PUB']['net_bp']:+.2f}")
    print(f"  P7 C0-r top trade not VSA, share < 10%: {V('P7')} -- {tp_c0r['symbol']} {100 * tp_c0r['share']:.2f}% "
          f"(C0's: {C0['top5'][0]['symbol']} {100 * C0['top5'][0]['share']:.2f}%)")
    print(f"  P8 fill 100% under replace, < 90% under starve: {V('P8')} -- {100 * RLR['fill']:.2f}%, {100 * RLS['fill']:.2f}%")
    print(f"  P9 (against) RL-s < RL-r and (RL-r - RL-s) < (RL0 - RL-r): {V('P9')} -- RL0 {rl0_net:+.2f}, RL-r {rlr_net:+.2f}, "
          f"RL-s {rls_net:+.2f}; gaps {rlr_net - rls_net:+.2f} vs {rl0_net - rlr_net:+.2f}")
    print(f"  check: floor share == census 29.3% to 1e-9: {'yes' if P['check'] else 'NO'} -- {100 * share:.4f}%")

    # ---- write ----------------------------------------------------------------------------
    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return None if not np.isfinite(o) else float(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        return o

    def cell_out(c):
        return dict(name=c["name"], k=c["k"], floor=c["floor"], fill=c["fill"], costed=c["C"], group1=c["G1"], group2=c["G2"],
                    group3=c["G3"], legs={cv: {str(s): c["LEGS"][cv][s] for s in (0, 1)} for cv in CONVS},
                    invariant=c["INV"], borrow=c["borrow"], top_trades=c["top5"], trades=len(c["res_v"]["trades"]),
                    trades_invariant=len(c["res_i"]["trades"]))

    out = dict(
        note="D339: the universe floor (raw price >= $5 at t-1 AND dv28) as a definition, under REPLACE (masked score, "
             "full gate) and STARVE (keep inside the rank cut) semantics; eight cells, both lenses, PB and PUB, borrow as "
             "new keys; four groups on RL-r; rank-rotation null with teeth on the GROSS null. Variant bp/bar and invariant "
             "per trade are never compared. Under replace the floor effective at bar t is keep[t-1] (the ranker lags the "
             "masked score). Nothing is promoted.",
        floor=dict(px_min=UF.PX_MIN, dv_pct=UF.DV_PCT, share_live_failing=share,
                   share_price_only=float((~px_only & finT).sum() / finT.sum()),
                   census_c=cen_c, nan_prev_close=det,
                   nan_choice="NaN raw close at t-1 fails the price floor only if the name was live at t-1"),
        f0=dict(applied=int(n_ok), drops=drops, excluded_live_pct=float(pct)),
        identity_worst=dict(rl0_vs_d338=worst, c0_vs_d333=worst_c),
        lag_audit=dict(bars=N_LAG_BARS, unlagged_differs=int(n_diff_unlagged)),
        causality=dict(full_rebuild_bars=20, bite_after_t=int(n_bite_full), single_bar_checks=200, bite_next_bar=int(n_bite_1)),
        w_check=dict(bars_qualifying_both=len(q_both), bars_qualifying_keep_t_only=len(q_t_only)),
        cells={nm: cell_out(c) for nm, c in cells.items()},
        null=NULL,
        reconciliation=dict(residual_bp=resid, open_positions=n_open, unattributed_position_bars=gap_bars,
                            first_unattributed_bar=int(first), pnl_over_contribution=ratio),
        predictions=P)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({el()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

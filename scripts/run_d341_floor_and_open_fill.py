"""D341 -- the stack under the floor AND the open fill together.

    uv run python scripts/run_d341_floor_and_open_fill.py --selftest
    uv run python scripts/run_d341_floor_and_open_fill.py [--draws 200]

Four signals (retrace_leg F0 k=20, the incumbent k=5, rsi F0 k=20, hist_L F0
k=20) x {none, floor} x {close, open}, both lenses, PB and PUB, GC+HTB borrow.
Three corners of every square are IDENTITIES to D338 / D333 / D339 / D340; the
fourth (floor/open) is the number the programme has never had. The interaction
of the two conventions is decomposed per square. The four groups, the top-five
table with as-traded price and dollar-volume percentile, the implementation-lag
premium on the floored gate and a 200-draw null WITH ITS RESOLUTION STATED (the
rotation has at most 24 distinct shifts) on retrace_leg floor/open.

Floor: D339's replace semantics (scripts/d339_universe_floor.py). Fill: D340's
flag (scripts/d340_fill.py builds ocT / mkt_oc; the D303 cache is untouched).

ASSERTIONS  [K] [F0] [R] [1] [E] [A] [S] [RQ] [2] [3] [N] [B] [F] [6]  -- pre-reg section 4.
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


V39 = _load("d339r", "run_d339_universe_floor.py")      # main guarded; carries every alias, bound
V35, V31, PA, V9 = V39.V35, V39.V31, V39.PA, V39.V9
V6, Y, W, D, M, SP, R, X = V39.V6, V39.Y, V39.W, V39.D, V39.M, V39.SP, V39.R, V39.X
G22, BR, V38, CEN, UF = V39.G22, V39.BR, V39.V38, V39.CEN, V39.UF
FL = _load("d340f", "d340_fill.py")

DEPTH, N_BASE, ANN = 2, W.N_BASE, 252.0
NULL_SEED, LAG_SEED, N_LAG_BARS = [W.SEED, 341], 341, 200
CONVS, FILLS, FLOORS = ("PB", "PUB"), ("close", "open"), ("none", "floor")
OUT = REPO / "data" / "d341_floor_and_open_fill.json"
D338_JSON = REPO / "data" / "d338_retrace_leg_candidate.json"
D333_JSON = REPO / "data" / "d333_dividend_bound.json"
D339_JSON = REPO / "data" / "d339_universe_floor.json"
D340_JSON = REPO / "data" / "d340_open_fill.json"
CENSUS_JSON = REPO / "data" / "d339_census.json"
SIGS = {"RL": ("retrace_leg", 20), "C0": (None, 5), "RSI": ("rsi", 20), "HL": ("hist_L", 20)}
D339_NAMES = {("RL", "none"): "RL0", ("RL", "floor"): "RL-r", ("C0", "none"): "C0", ("C0", "floor"): "C0-r",
              ("RSI", "none"): "RSI0", ("RSI", "floor"): "RSI-r", ("HL", "none"): "HL0", ("HL", "floor"): "HL-r"}
gate_rows = V38.gate_rows


def exit_events(res):
    return {(t[0], t[4], t[1] + t[2]) for t in res["trades"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    print("D341  the stack under the floor AND the open fill -- sixteen cells, one new corner per square")

    # ---- [K] ---------------------------------------------------------------------
    cache = Path(R.BC.CACHE)
    rp = REPO / "scripts" / "ragged_panel.py"
    assert cache.exists() and cache.stat().st_mtime > rp.stat().st_mtime, "[K] cache older than ragged_panel.py"
    assert str(np.load(cache, allow_pickle=False)["key"]) == R.BC.cache_key(M.B.FIXTURE), "[K] npz key != cache_key()"
    print("    [K] SCORE CACHE: key matches cache_key() with ragged_panel.py in the tuple; npz newer than the builder")

    # ---- data (D338/D339's preparation) ----------------------------------------------
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
    d339 = json.loads(D339_JSON.read_text())["cells"]
    d340 = json.loads(D340_JSON.read_text())["cells"]
    census = json.loads(CENSUS_JSON.read_text())
    print(f"  panel {finT.shape}, {int(dead.sum())} delisted names ({el()})")

    dj = json.loads(V31.DEALS.read_text())
    fbars, drops, n_ok = V31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live, last_live,
                                         lambda f: f["form"] in V31.F0_FORMS)
    excl = V31.exclusion_mask(fbars, n, T, last_live)
    pct = 100.0 * (excl & finT.T).sum() / finT.sum()
    assert n_ok == V35.EXPECT_APPLIED and abs(pct - V35.EXPECT_PCT) < 0.02, f"[F0] {n_ok} / {pct:.3f}%"
    print(f"    [F0] F0 MASK: {n_ok:,} filings applied, {pct:.2f}% of live name-bars excluded")

    # ---- the floor and the open-fill arrays -----------------------------------------------
    RAW = UF.raw_price_factor(panel, ev)
    assert np.array_equal(RAW, CEN.raw_factor(ev, panel.symbols, panel.dates)), "[R] module factor != census factor"
    RAW_CLOSE = CLOSE * RAW
    keep = UF.floor_mask(RAW_CLOSE, DV, finT)
    share = UF.floor_share(keep, finT)
    cen_share = census["universe"]["all"]["c"] if "universe" in census and "all" in census["universe"] else None
    if cen_share is None:  # fall back to D339's recorded value
        cen_share = json.loads(D339_JSON.read_text())["floor"].get("share_live_fail", share)
    assert abs(share - float(cen_share)) < 1e-9, f"[R] floor share {share:.6f} != census {cen_share}"
    print(f"    [R] RAW PRICE and FLOOR: module factor == census factor on the full grid; floor fails "
          f"{100 * share:.4f}% of live name-bars == census ({el()})")
    A2, fbmask, FBREP = FL.with_open_fill(A, panel, g)
    ocT, mkt_oc = A2["ocT"], A2["mkt_oc"]
    print(f"    [F] FALLBACK: {FBREP['fallback_cells']:,} of {FBREP['priced_cells']:,} priced cells lack a usable open")

    # ---- ranks and gates ---------------------------------------------------------------------
    Q = V6.Q
    prim, pair = Q.COMPOSITES["C0_incumbent"]
    C0_KEYS = ("hist_L", "macd_hist", "rsi")

    def score_of(sig, floor):
        sc = np.where(excl, np.nan, z[sig])
        return UF.apply_floor_replace(sc, keep) if floor == "floor" else sc

    SCORE, RANK, GATE = {}, {}, {}
    for nm, (sig, k) in SIGS.items():
        for fl in FLOORS:
            if sig is None:
                zz = {kk: (UF.apply_floor_replace(z[kk], keep) if fl == "floor" else z[kk]) for kk in C0_KEYS}
                RANK[nm, fl] = Q.rank_composite(zz, base, prim, pair, n, T)
            else:
                SCORE[nm, fl] = score_of(sig, fl)
                RANK[nm, fl] = Y.rank_single({sig: SCORE[nm, fl]}, base, sig, n, T)
            GATE[nm, fl] = Y.gate_from(RANK[nm, fl], finT)
    print(f"  8 rank arrays and gates built ({el()})")

    def top_five(res, contrib, kmax=5):
        tr = res["trades"]
        pnl = np.array([t[3] for t in tr])
        tot = float(pnl.sum())
        out = []
        for i in np.argsort(-pnl)[:kmax]:
            row, e0, age, p, side = tr[i]
            s = panel.symbols[row]
            seg = r1T[e0:e0 + age, row]
            j = int(e0 + np.nanargmax(np.abs(seg)))
            out.append(dict(symbol=s, side="long" if side == 0 else "short", entry=panel.dates[e0], hold=int(age),
                            pnl_bp=float(p) * 1e4, share=float(p / tot) if tot else None, big_day=panel.dates[j],
                            r1=float(seg[j - e0]), entry_bar_r1=float(r1T[e0, row]), entry_bar_oc=float(ocT[e0, row]),
                            raw_px_prev=float(RAW_CLOSE[e0 - 1, row]) if e0 > 0 else None,
                            dv_pct_entry=CEN.dv_percentile(DV, finT, int(e0), int(row)),
                            passes_keep=bool(keep[e0, row]), contrib_bp=float(contrib[i]) * 1e4))
        return out

    def run_cell(nm, fl, fill):
        W.BASE_HOLD = SIGS[nm][1]
        gate = GATE[nm, fl]
        res_v = W.simulate(A2, gate, DEPTH, True, slots=True, fill=fill)
        res_i = W.simulate(A2, gate, DEPTH, True, slots=False, fill=fill)
        contrib = G22.contributions(res_v, r1T) if fill == "close" else FL.contributions_fill(res_v, r1T, ocT)
        C = {cv: G22.costed(res_v, G4[cv]) for cv in CONVS}
        G1 = {cv: G22.group1(res_v, C[cv], contrib, r1T) for cv in CONVS}
        G2 = G22.group2(res_v)
        G3 = {cv: G22.group3(res_v, contrib, C[cv], years, dead, CLOSE, HALF[cv]) for cv in CONVS}
        LEGS = {cv: V9.per_leg(res_i, HALF[cv], CLOSE, r1T, mkt) for cv in CONVS}
        INV = {cv: V9.invariant_legcost(res_i, LEGS[cv]) for cv in CONVS}
        BV, _ = V38.borrow_block(res_v, C, INV, excl, CLOSE, T)
        BI, _ = V38.borrow_block(res_i, C, INV, excl, CLOSE, T)
        print(f"  {nm:3s} {fl:5s}/{fill:5s} k={SIGS[nm][1]:2d}: fill {100 * C['PUB']['fill']:.1f}%, gross {C['PUB']['gross_bp']:+.2f}, "
              f"PUB net {C['PUB']['net_bp']:+.2f}, PB net {C['PB']['net_bp']:+.2f}, inv/trade PUB "
              f"{INV['PUB']['net_per_trade']:+.1f}, {len(res_v['trades']):,} trades ({el()})")
        return dict(res_v=res_v, res_i=res_i, contrib=contrib, C=C, G1=G1, G2=G2, G3=G3, LEGS=LEGS, INV=INV,
                    borrow=dict(variant=BV, invariant=BI), top5=top_five(res_v, contrib))

    CELLS = {(nm, fl, fi): run_cell(nm, fl, fi) for nm in SIGS for fl in FLOORS for fi in FILLS}
    print(f"  16 cells simulated, both lenses ({el()})")

    # ---- assertions -------------------------------------------------------------------------
    print("\nASSERTIONS")
    worst, n_id = 0.0, 0

    def hold(x, y, tag):
        nonlocal worst, n_id
        worst = max(worst, abs(x - y))
        n_id += 1
        assert abs(x - y) < 1e-9, f"[1] {tag}: {x} vs {y}"

    for nm in SIGS:
        for cv in CONVS:
            c = CELLS[nm, "none", "close"]
            if nm == "RL":
                hold(c["C"][cv]["net_bp"], d338["group1"][cv]["net_bp_bar"], f"RL none/close {cv} net vs D338")
                hold(c["C"][cv]["sharpe_net"], d338["group1"][cv]["sharpe_net"], f"RL none/close {cv} sharpe vs D338")
                hold(c["INV"][cv]["net_per_trade"], d338["invariant"][cv]["net_per_trade"], f"RL none/close {cv} inv vs D338")
            if nm == "C0":
                c3 = d333[f"C0 N=2/{cv}/new"]
                hold(c["C"][cv]["sharpe_net"], c3["variant"]["sharpe_net"], f"C0 none/close {cv} sharpe vs D333")
                hold(c["INV"][cv]["net_per_trade"], c3["invariant"]["net_per_trade"], f"C0 none/close {cv} inv vs D333")
            for fl in FLOORS:
                c9 = d339[D339_NAMES[nm, fl]]
                cc = CELLS[nm, fl, "close"]
                hold(cc["C"][cv]["net_bp"], c9["costed"][cv]["net_bp"], f"{nm} {fl}/close {cv} net vs D339")
                hold(cc["C"][cv]["sharpe_net"], c9["costed"][cv]["sharpe_net"], f"{nm} {fl}/close {cv} sharpe vs D339")
                hold(cc["INV"][cv]["net_per_trade"], c9["invariant"][cv]["net_per_trade"], f"{nm} {fl}/close {cv} inv vs D339")
            if nm in ("RL", "C0"):
                c4 = d340[nm]["open"]
                co = CELLS[nm, "none", "open"]
                hold(co["C"][cv]["net_bp"], c4["group1"][cv]["net_bp_bar"], f"{nm} none/open {cv} net vs D340")
                hold(co["C"][cv]["sharpe_net"], c4["group1"][cv]["sharpe_net"], f"{nm} none/open {cv} sharpe vs D340")
                hold(co["INV"][cv]["net_per_trade"], c4["invariant"][cv]["net_per_trade"], f"{nm} none/open {cv} inv vs D340")
    print(f"    [1] IDENTITY: {n_id} published numbers reproduced to {worst:.1e} -- D338 (RL none/close), D333 (C0), "
          f"D339 (all eight close-fill cells), D340 (RL and C0 none/open)")

    # [E] the gate is fill-invariant and entries never diverge before exits do
    for nm in SIGS:
        for fl in FLOORS:
            rc, ro = CELLS[nm, fl, "close"]["res_v"], CELLS[nm, fl, "open"]["res_v"]
            ec, eo = exit_events(rc), exit_events(ro)
            diff = ec ^ eo
            t_star = min(x[2] for x in diff) if diff else T
            d_ent = np.flatnonzero(rc["ent"] != ro["ent"])
            t_ent = int(d_ent[0]) if d_ent.size else T
            assert t_ent >= t_star, f"[E] {nm}/{fl}: entries diverge at {t_ent} before exits at {t_star}"
    print("    [E] GATE FILL-INVARIANT: for all 8 squares the two fills read one gate; entries never diverge before the exit sets do")

    # [A] lag audit on RL floor/open's long gate
    sc = SCORE["RL", "floor"]
    gate_rl = GATE["RL", "floor"]
    rng = np.random.default_rng(LAG_SEED)
    nonempty = np.array([t for t in range(1, T) if gate_rows(gate_rl, 0, t).size > 0])
    bars = rng.choice(nonempty, size=N_LAG_BARS, replace=False)
    n_unl = 0
    for t in bars:
        got = set(int(r) for r in gate_rows(gate_rl, 0, int(t)))
        assert got == V38.rebuild_long_set(sc, base, finT, int(t), 1), f"[A] bar {t}"
        n_unl += V38.rebuild_long_set(sc, base, finT, int(t), 0) != got
    assert n_unl > N_LAG_BARS // 2, "[A] the unlagged rebuild agrees too often"
    print(f"    [A] LAG AUDIT: RL floor gate rebuilt from the floored score at t-1 equals the gate on all {N_LAG_BARS} "
          f"sampled bars; the unlagged rebuild differs on {n_unl}")

    # [S] sign in money on RL floor/open
    RLFO = CELLS["RL", "floor", "open"]
    tr = RLFO["res_v"]["trades"]
    pnl = np.array([t[3] for t in tr])
    rec = FL.pnl_recomputed_fill(tr, r1T, mkt, ocT, mkt_oc)
    worst_s = float(np.abs(rec - pnl).max())
    assert worst_s < 1e-12, f"[S] {worst_s:.2e}"
    ex = np.array([float((ocT[e0, row] - mkt_oc[e0]) + (r1T[e0 + 1:e0 + age, row] - mkt[e0 + 1:e0 + age]).sum())
                   for row, e0, age, _p, _s in tr])
    longs = np.array([t[4] == 0 for t in tr])
    assert (pnl[longs & (ex > 0)] > 0).all() and (pnl[~longs & (ex < 0)] > 0).all(), "[S] sign"
    print(f"    [S] SIGN IN MONEY: every RL floor/open trade equals the open-fill recomputation to {worst_s:.1e}; "
          f"a favourable excess path pays positively on every long and every short")

    # [RQ]
    W.BASE_HOLD = 20
    res_c = W.simulate(A2, gate_rl, DEPTH, True, slots=True, fill="open", accumulate="compound")
    ks = [(t[0], t[1], t[2], t[4]) for t in tr]
    kc = [(t[0], t[1], t[2], t[4]) for t in res_c["trades"]]
    pnl_c = np.array([t[3] for t in res_c["trades"]])
    assert ks == kc and not np.allclose(pnl, pnl_c), "[RQ]"
    assert abs(RLFO["G1"]["PUB"]["trade_mean_bp"] - float(pnl.mean()) * 1e4) < 1e-9, "[RQ] group 1 scores the wrong ledger"
    print(f"    [RQ] RIGHT QUANTITY: same {len(ks):,} entries/exits under compound accumulation, "
          f"{int((pnl != pnl_c).sum()):,} P&Ls differ; group 1 scores the SUMMED ledger")

    # [2] reconciliation with contributions_fill
    res_v, contrib = RLFO["res_v"], RLFO["contrib"]
    attributed = float(contrib.sum()) / RLFO["C"]["PUB"]["bars"] * 1e4
    resid = RLFO["C"]["PUB"]["gross_bp"] - attributed
    n_open = int(res_v["ent"].sum()) - len(tr)
    gap_bars, first, TT = G22.unattributed(res_v)
    assert 0 <= n_open <= 2 * DEPTH and first >= TT - 20 and abs(resid) < 1.0, f"[2] {n_open} {first} {resid}"
    broke = False
    try:
        short = [t for i, t in enumerate(tr) if i != len(tr) // 2]
        _, f2, _ = G22.unattributed(res_v, short)
        assert f2 >= TT - 20
    except AssertionError:
        broke = True
    assert broke, "[2] accepted a ledger missing a trade"
    print(f"    [2] RECONCILIATION: {len(tr):,} RL floor/open trades reconstruct gross to {resid:+.4f} bp via contributions_fill; "
          f"{n_open} open at T, none before bar {first} of {TT}; rejects a ledger missing a trade")

    # [3]
    k1 = max(1, pnl.size // 100)
    broke = False
    try:
        _, kt, kb = G22.trim_sym(pnl, k1, k1 + 1)
        assert kt == kb
    except AssertionError:
        broke = True
    assert broke and RLFO["G2"]["n_dropped_top"] == RLFO["G2"]["n_dropped_bottom"], "[3]"
    print(f"    [3] the 1% trim is symmetric (k={k1}) and rejects a trim one deeper on the bottom")

    # [N] rotation moves the book
    rot = Y.gate_from(np.roll(RANK["RL", "floor"], 501, axis=1), finT)
    r_rot = W.simulate(A2, rot, DEPTH, True, fill="open")
    g_rot = float(r_rot["book"][r_rot["mask"]].mean()) * 1e4
    assert abs(g_rot - RLFO["C"]["PUB"]["gross_bp"]) > 1e-9, "[N] same book"
    print(f"    [N] CAUSALITY: rotating RL floor's rank array by 501 bars moves open-fill gross "
          f"{RLFO['C']['PUB']['gross_bp']:+.2f} -> {g_rot:+.2f}")

    # [B]
    wb = max(c["borrow"][lens]["reconcile_worst"] for c in CELLS.values() for lens in ("variant", "invariant"))
    assert wb < 1e-9, f"[B] {wb:.2e}"
    for c in CELLS.values():
        for cv in CONVS:
            assert c["borrow"]["variant"]["gc_htb"][cv]["net_bp"] == c["C"][cv]["net_bp"], "[B] net_bp mutated"
    print(f"    [B] BORROW: per bar x cnt1 == per trade to {wb:.1e} on all 16 cells, both lenses; net_bp untouched")

    # [6]
    broke = False
    try:
        bk = CELLS["RL", "none", "close"]["res_v"]["book"].copy()
        bk[np.flatnonzero(CELLS["RL", "none", "close"]["res_v"]["mask"])[:200]] += 5e-4
        bad = G22.costed(dict(CELLS["RL", "none", "close"]["res_v"], book=bk), G4["PUB"])
        assert abs(bad["net_bp"] - d338["group1"]["PUB"]["net_bp_bar"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6]"
    print("    [6] and [1] raises on a book handed +5 bp on 200 masked bars")

    if a.selftest:
        print(f"\nOK  assertions pass  ({el()})")
        return 0

    # ---- the squares and the interaction --------------------------------------------------------
    SQ = {}
    print("\n" + "=" * 100)
    print("THE FOUR SQUARES -- PUB net bp/bar (PB in brackets); interaction = floor/open - [none/close + dFloor + dFill]")
    print("=" * 100)
    print("  %-4s %14s %14s %14s %14s | %8s %8s %8s %10s" % ("", "none/close", "floor/close", "none/open", "FLOOR/OPEN",
                                                              "dFloor", "dFill", "additive", "INTERACT"))
    for nm in SIGS:
        v = {(fl, fi): CELLS[nm, fl, fi]["C"]["PUB"]["net_bp"] for fl in FLOORS for fi in FILLS}
        b = {(fl, fi): CELLS[nm, fl, fi]["C"]["PB"]["net_bp"] for fl in FLOORS for fi in FILLS}
        dfl = v["floor", "close"] - v["none", "close"]
        dfi = v["none", "open"] - v["none", "close"]
        add = v["none", "close"] + dfl + dfi
        inter = v["floor", "open"] - add
        SQ[nm] = dict(pub=v, pb=b, d_floor=dfl, d_fill=dfi, additive=add, interaction=inter,
                      gross={(fl, fi): CELLS[nm, fl, fi]["C"]["PUB"]["gross_bp"] for fl in FLOORS for fi in FILLS},
                      inv_pub={(fl, fi): CELLS[nm, fl, fi]["INV"]["PUB"]["net_per_trade"] for fl in FLOORS for fi in FILLS})
        f = lambda key: "%+7.2f [%+6.2f]" % (v[key], b[key])
        print("  %-4s %14s %14s %14s %14s | %+8.2f %+8.2f %+8.2f %+10.2f" % (
            nm, f(("none", "close")), f(("floor", "close")), f(("none", "open")), f(("floor", "open")), dfl, dfi, add, inter))
    print("\n  invariant PUB net per trade, same layout:")
    for nm in SIGS:
        iv = SQ[nm]["inv_pub"]
        print("  %-4s %14s %14s %14s %14s" % (nm, *["%+.1f" % iv[k] for k in (("none", "close"), ("floor", "close"),
                                                                                 ("none", "open"), ("floor", "open"))]))

    # ---- premium on the floored RL gate (close-fill floored ledger) -------------------------------
    def premium(trades):
        out = {}
        for side in (0, 1):
            sgn = 1.0 if side == 0 else -1.0
            tt = [t for t in trades if t[4] == side]
            rows_ = np.array([t[0] for t in tt]); e0_ = np.array([t[1] for t in tt])
            name = sgn * (r1T[e0_, rows_] - ocT[e0_, rows_])
            out[str(side)] = dict(n=int(name.size), name_mean_bp=float(name.mean()) * 1e4,
                                  name_median_bp=float(np.median(name)) * 1e4,
                                  t=float(name.mean() / (name.std(ddof=1) / np.sqrt(name.size))),
                                  share_positive=float((name > 0).mean()))
        return out
    PREM = {nm: premium(CELLS[nm, "floor", "close"]["res_v"]["trades"]) for nm in SIGS}
    PREM0 = {nm: premium(CELLS[nm, "none", "close"]["res_v"]["trades"]) for nm in SIGS}
    print("\n  IMPLEMENTATION-LAG PREMIUM per entry (bp), unfloored -> floored gate, long / short:")
    for nm in SIGS:
        print("  %-4s long %+6.1f -> %+6.1f (t %+.2f)   short %+6.1f -> %+6.1f (t %+.2f)" % (
            nm, PREM0[nm]["0"]["name_mean_bp"], PREM[nm]["0"]["name_mean_bp"], PREM[nm]["0"]["t"],
            PREM0[nm]["1"]["name_mean_bp"], PREM[nm]["1"]["name_mean_bp"], PREM[nm]["1"]["t"]))

    # ---- the four groups on RL floor/open ---------------------------------------------------------------
    g1, g2, g3 = RLFO["G1"], RLFO["G2"], RLFO["G3"]["PUB"]
    print("\n" + "=" * 78)
    print("GROUP 1 -- retrace_leg FLOOR/OPEN: the honest number")
    print("=" * 78)
    ROW = "  %-34s %14s %14s"
    print(ROW % ("", "PB", "PUB"))
    for label, key, fn in (("gross bp/bar", "gross_bp_bar", "%+.2f"), ("cost bp/bar", "cost_bp_bar", "%.2f"),
                           ("NET bp/bar", "net_bp_bar", "%+.2f"), ("vol bp/bar", "vol_bp_bar", "%.1f"),
                           ("gross Sharpe", "sharpe_gross", "%+.3f"), ("NET Sharpe", "sharpe_net", "%+.3f"),
                           ("gross t", "t_gross", "%+.2f"), ("maxDD bp", "maxdd_bp", "%.0f"),
                           ("exposure", "exposure_bars", "%.3f"), ("fill", "fill", "%.3f"),
                           ("held half-spread bp/side", "held_half_spread", "%.2f"), ("held median price", "held_price", "$%.2f"),
                           ("held median $ volume", "held_dollar_volume", "$%.0f"), ("2c", "two_c_bp", "%.2f"),
                           ("mean move per TRADE bp", "trade_mean_bp", "%+.2f"), ("mean move / 2c", "trade_mean_over_2c", "%.2fx"),
                           ("BREAKEVEN half-spread /side", "breakeven_half_spread_bp_side", "%.2f"),
                           ("breakeven / measured", "breakeven_multiple", "%.2fx")):
        print(ROW % (label, fn % g1["PB"][key], fn % g1["PUB"][key]))
    bv = RLFO["borrow"]["variant"]
    print("  after GC+HTB: PB %+.2f  PUB %+.2f (borrow %.3f);  house: PB %+.2f PUB %+.2f" % (
        bv["gc_htb"]["PB"]["net_bp_borrow"], bv["gc_htb"]["PUB"]["net_bp_borrow"], bv["gc_htb"]["PUB"]["borrow_bp_bar"],
        bv["house"]["PB"]["net_bp_borrow"], bv["house"]["PUB"]["net_bp_borrow"]))
    L = RLFO["LEGS"]["PUB"]
    print("  invariant PUB per trade: long %+.1f on %+.1f gross (t %.2f, %d); short %+.1f on %+.1f (t %.2f, %d); both %+.1f" % (
        L[0]["net"], L[0]["gross"], L[0]["t"], L[0]["trades"], L[1]["net"], L[1]["gross"], L[1]["t"], L[1]["trades"],
        RLFO["INV"]["PUB"]["net_per_trade"]))
    print("\nGROUP 2 -- trades %d, mean %+.1f, MEDIAN %+.1f (mean below median: %s), win %.1f%%, payoff %.2f, skew %+.2f, kurt %.1f" % (
        g2["n"], g2["mean_bp"], g2["median_bp"], "YES" if g2["mean_below_median"] else "no", 100 * g2["win_rate"],
        g2["payoff"], g2["skew"], g2["kurtosis_raw"]))
    print("  ex-top 1%% %+.1f, ex-bottom 1%% %+.1f, TRIMMED both %+.1f (vs PUB 2c %.1f); top 1%% %+.0f%%, bottom 1%% %+.0f%% of P&L" % (
        g2["mean_ex_top_bp"], g2["mean_ex_bottom_bp"], g2["mean_trimmed_bp"], g1["PUB"]["two_c_bp"],
        100 * g2["top1_share"], 100 * g2["bottom1_share"]))
    print("GROUP 3 (PUB) -- names %d, to half the P&L %d, top 1/5/10 %.1f/%.1f/%.1f%%; years net+ %d of %d (gross+ %d); dead %.1f%%; "
          "eras %+.1f / %+.1f net/trade; price LOW %.1f%% (%+.1f net/trade)" % (
              g3["names"], g3["names_to_half_pnl"], 100 * g3["top1_name_share"], 100 * g3["top5_name_share"],
              100 * g3["top10_name_share"], g3["years_profitable_net"], g3["years"], g3["years_profitable_gross"],
              100 * g3["dead"]["share_pnl"], g3["era_first_half"]["net_per_trade_bp"], g3["era_second_half"]["net_per_trade_bp"],
              100 * g3["price_low"]["share_pnl"], g3["price_low"]["net_per_trade_bp"]))
    print("  TOP FIVE, RL floor/open:")
    for tt in RLFO["top5"]:
        print("    %-6s %-5s %s hold %2d  %+8.0f bp (%4.1f%%)  entry bar r1 %+6.1f%% oc %+6.1f%%  raw px $%.2f  dv pct %.2f  keep %s" % (
            tt["symbol"], tt["side"], tt["entry"], tt["hold"], tt["pnl_bp"], 100 * (tt["share"] or 0), 100 * tt["entry_bar_r1"],
            100 * tt["entry_bar_oc"], tt["raw_px_prev"] or 0, tt["dv_pct_entry"], tt["passes_keep"]))

    # ---- the null on RL floor/open, resolution stated -------------------------------------------------------
    ts = time.time()
    rng = np.random.default_rng(NULL_SEED)
    offs = rng.choice(np.arange(1, N_BASE), size=a.draws, replace=True)
    distinct = int(len(set(offs.tolist())))
    NG, NSG, NSN = [], [], {cv: [] for cv in CONVS}
    by_shift = {}
    W.BASE_HOLD = 20
    for s_ in offs:
        s_ = int(s_)
        if s_ not in by_shift:
            r = W.simulate(A2, gate_rl, DEPTH, True, shift=s_, fill="open")
            okm = r["mask"]
            b = r["book"][okm]
            by_shift[s_] = (float(b.mean()) * 1e4, float(b.mean() / b.std(ddof=1) * np.sqrt(ANN)),
                            {cv: G22.costed(r, G4[cv])["sharpe_net"] for cv in CONVS}, int(okm.sum()))
        gb, sg, sn, nb = by_shift[s_]
        if nb < 200:
            continue
        NG.append(gb); NSG.append(sg)
        for cv in CONVS:
            NSN[cv].append(sn[cv])
    NG, NSG = np.array(NG), np.array(NSG)
    NSN = {cv: np.array(NSN[cv]) for cv in CONVS}
    assert NG.size >= min(195, a.draws - 5), f"[N] only {NG.size} valid draws"
    C_ = RLFO["C"]
    dvals = {"gross_bp": sorted(v[0] for v in by_shift.values()), "sharpe_gross": sorted(v[1] for v in by_shift.values()),
             "sharpe_net_PB": sorted(v[2]["PB"] for v in by_shift.values()), "sharpe_net_PUB": sorted(v[2]["PUB"] for v in by_shift.values())}
    above = {k: int(sum(1 for x in vs if x < sc)) for (k, vs), sc in zip(dvals.items(),
             (C_["PUB"]["gross_bp"], C_["PUB"]["sharpe_gross"], C_["PB"]["sharpe_net"], C_["PUB"]["sharpe_net"]))}
    NULL = dict(construction="rank rotation inside the 25-name gate, floor/open", seed=NULL_SEED, draws=int(NG.size),
                distinct_shifts=distinct, above_k_of_distinct=above,
                gross_bp=G22.dist(NG, C_["PUB"]["gross_bp"]), sharpe_gross=G22.dist(NSG, C_["PUB"]["sharpe_gross"]),
                sharpe_net={cv: G22.dist(NSN[cv], C_[cv]["sharpe_net"]) for cv in CONVS})
    teeth = NULL["gross_bp"]["p95"] > 0
    print(f"\n    [N] {NG.size} of {a.draws} draws valid, {distinct} DISTINCT shifts of at most 24 ({time.time() - ts:.0f}s)")
    print("GROUP 4 -- THE NULL on RL floor/open (p as 'above k of the distinct rotations', not 1/(draws+1))")
    print("  %-16s %10s %10s %10s %10s   %s" % ("statistic", "score", "p50", "p95", "max", "above k of distinct"))
    for lab, d_, key in (("gross bp/bar", NULL["gross_bp"], "gross_bp"), ("gross Sharpe", NULL["sharpe_gross"], "sharpe_gross"),
                         ("net Sharpe PB", NULL["sharpe_net"]["PB"], "sharpe_net_PB"), ("net Sharpe PUB", NULL["sharpe_net"]["PUB"], "sharpe_net_PUB")):
        print("  %-16s %10.3f %10.3f %10.3f %10.3f   %d of %d" % (lab, d_["score"], d_["p50"], d_["p95"], d_["max"], above[key], distinct))
    print(f"  the gross null has teeth (p95 > 0): {'yes' if teeth else 'NO -- R7 flag'}")

    # ---- predictions --------------------------------------------------------------------------------------------
    rl = SQ["RL"]["pub"]; c0 = SQ["C0"]["pub"]
    q = {}
    q["Q1"] = bool(rl["floor", "open"] <= 0.0)
    q["Q2"] = bool(PREM["RL"]["0"]["name_mean_bp"] < 0.5 * 44.8)
    q["Q3"] = bool(SQ["RL"]["interaction"] > 5.0)
    q["Q4"] = bool(abs(SQ["C0"]["interaction"]) < 2.0)
    q["Q5"] = bool(SQ["RSI"]["pub"]["floor", "open"] > 0.0)
    q["Q6"] = bool(SQ["HL"]["pub"]["floor", "open"] < -10.0)
    q["Q7"] = bool(C_["PUB"]["gross_bp"] > NULL["gross_bp"]["p95"] and teeth)
    tt = RLFO["top5"][0]
    q["Q8"] = bool((tt["share"] or 1) < 0.07 and (tt["raw_px_prev"] or 0) >= 5.0 and tt["dv_pct_entry"] > 0.28)
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) RL floor/open PUB net <= 0: {'CONFIRMED' if q['Q1'] else 'FALSIFIED'} -- {rl['floor', 'open']:+.2f} bp/bar "
          f"(PB {SQ['RL']['pb']['floor', 'open']:+.2f}; after GC+HTB PUB {bv['gc_htb']['PUB']['net_bp_borrow']:+.2f})")
    print(f"  Q2 floored long-leg premium < +22.4: {'CONFIRMED' if q['Q2'] else 'FALSIFIED'} -- {PREM['RL']['0']['name_mean_bp']:+.1f} "
          f"(unfloored {PREM0['RL']['0']['name_mean_bp']:+.1f}); short {PREM['RL']['1']['name_mean_bp']:+.1f}")
    print(f"  Q3 RL interaction > +5: {'CONFIRMED' if q['Q3'] else 'FALSIFIED'} -- {SQ['RL']['interaction']:+.2f} "
          f"(additive {SQ['RL']['additive']:+.2f}, actual {rl['floor', 'open']:+.2f})")
    print(f"  Q4 C0 additive within 2: {'CONFIRMED' if q['Q4'] else 'FALSIFIED'} -- interaction {SQ['C0']['interaction']:+.2f} "
          f"(additive {SQ['C0']['additive']:+.2f}, actual {c0['floor', 'open']:+.2f})")
    print(f"  Q5 (against) rsi floor/open > 0: {'CONFIRMED' if q['Q5'] else 'FALSIFIED'} -- {SQ['RSI']['pub']['floor', 'open']:+.2f} "
          f"(floor/close {SQ['RSI']['pub']['floor', 'close']:+.2f})")
    print(f"  Q6 hist_L floor/open < -10: {'CONFIRMED' if q['Q6'] else 'FALSIFIED'} -- {SQ['HL']['pub']['floor', 'open']:+.2f}")
    print(f"  Q7 RL floor/open gross above gross null p95, teeth: {'CONFIRMED' if q['Q7'] else 'FALSIFIED'} -- "
          f"{C_['PUB']['gross_bp']:+.2f} vs p95 {NULL['gross_bp']['p95']:+.2f} (max {NULL['gross_bp']['max']:+.2f}; above "
          f"{above['gross_bp']} of {distinct})")
    print(f"  Q8 top trade < 7%, raw px >= $5, dv pct > 28: {'CONFIRMED' if q['Q8'] else 'FALSIFIED'} -- {tt['symbol']} "
          f"{100 * (tt['share'] or 0):.1f}%, ${tt['raw_px_prev'] or 0:.2f}, pct {tt['dv_pct_entry']:.2f}")

    # ---- write -------------------------------------------------------------------------------------------------
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

    cells_out = {f"{nm}/{fl}/{fi}": dict(costed=c["C"], group1=c["G1"], group2=c["G2"], group3=c["G3"],
                                        legs={cv: {str(s): c["LEGS"][cv][s] for s in (0, 1)} for cv in CONVS},
                                        invariant=c["INV"], borrow=c["borrow"], top5=c["top5"],
                                        trades=len(c["res_v"]["trades"]), trades_invariant=len(c["res_i"]["trades"]))
                 for (nm, fl, fi), c in CELLS.items()}
    out = dict(note="D341: four signals x {none, floor} x {close, open}; three corners identities, the fourth new. "
                    "Variant bp/bar and invariant per trade never compared (FINDINGS section 10). Nothing promoted.",
               floor=dict(px_min=UF.PX_MIN, dv_pct=UF.DV_PCT, semantics="replace", share_live_fail=share),
               fallback=FBREP, identity=dict(count=n_id, worst=worst), squares=SQ, premium_floored=PREM,
               premium_unfloored=PREM0, cells=cells_out, null=NULL, teeth_gross=teeth, predictions=q,
               reconciliation=dict(residual_bp=resid, open_positions=n_open, first_unattributed_bar=int(first)))
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({el()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

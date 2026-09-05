"""D344 -- the hold-length check on rsi: k in {10, 20, 40} under keep_v2 and the open fill.

    uv run python scripts/run_d344_hold_length.py --selftest
    uv run python scripts/run_d344_hold_length.py [--draws 200]

One gate (the floored rsi score ranks the same way at every k), three holds. k=20
is D343's cell and an identity. Each cell: both lenses, PB and PUB, GC+HTB, the
four-group headline, the top five, and a 200-draw rotation null with its
resolution stated. The mechanism checks: turnover ~ 1/k, the held round trip
moving less than turnover (D296 / D323 [3]).

ASSERTIONS [K][F0][R][1][T][A][S][RQ][2][3][N][B][6] -- pre-reg section 4.
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


V43 = _load("d343r", "run_d343_relisting_clause.py")     # main guarded; every alias
V35, V31, PA, V9 = V43.V35, V43.V31, V43.PA, V43.V9
V6, Y, W, D, M, SP, R, X = V43.V6, V43.Y, V43.W, V43.D, V43.M, V43.SP, V43.R, V43.X
G22, BR, V38, CEN, UF, FL = V43.G22, V43.BR, V43.V38, V43.CEN, V43.UF, V43.FL

SIG, DEPTH, N_BASE, ANN = "rsi", 2, W.N_BASE, 252.0
KS = (10, 20, 40)
NULL_SEED, LAG_SEED, N_LAG_BARS = [W.SEED, 344], 344, 200
CONVS = ("PB", "PUB")
OUT = REPO / "data" / "d344_hold_length.json"
D343_JSON = REPO / "data" / "d343_relisting_clause.json"
D339_JSON = REPO / "data" / "d339_universe_floor.json"
gate_rows = V38.gate_rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    print("D344  the hold-length check on rsi -- k in {10, 20, 40}, keep_v2, open fill")

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
    d343 = json.loads(D343_JSON.read_text())
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
    keep = UF.floor_mask_v2(RAW_CLOSE, DV, finT)
    share = UF.floor_share(keep, finT)
    assert abs(share - float(d343["floor"]["v2_share_live_fail"])) < 1e-9, "[R] keep_v2 share != D343"
    print(f"    [R] RAW PRICE and FLOOR: factor == census factor; keep_v2 fails {100 * share:.4f}% of live name-bars == D343")
    A2, fbmask, FBREP = FL.with_open_fill(A, panel, g)
    ocT, mkt_oc = A2["ocT"], A2["mkt_oc"]

    sc = UF.apply_floor_replace(np.where(excl, np.nan, z[SIG]), keep)
    rankT = Y.rank_single({SIG: sc}, base, SIG, n, T)
    gate = Y.gate_from(rankT, finT)

    def top_five(res, kmax=5):
        trs = res["trades"]
        p = np.array([t[3] for t in trs])
        tot = float(p.sum())
        out = []
        for i in np.argsort(-p)[:kmax]:
            row, e0, age, pp, side = trs[i]
            out.append(dict(symbol=panel.symbols[row], side="long" if side == 0 else "short", entry=panel.dates[e0], hold=int(age),
                            pnl_bp=float(pp) * 1e4, share=float(pp / tot), raw_px_prev=float(RAW_CLOSE[e0 - 1, row]),
                            dv_pct_entry=CEN.dv_percentile(DV, finT, int(e0), int(row))))
        return out

    def run_cell(k):
        W.BASE_HOLD = k
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
        ages = np.array([t[2] for t in res_v["trades"]])
        print(f"  k={k:2d}: gross {C['PUB']['gross_bp']:+.2f}, PUB net {C['PUB']['net_bp']:+.2f} (Sharpe {C['PUB']['sharpe_net']:+.3f}), "
              f"PB net {C['PB']['net_bp']:+.2f}, turnover {C['PUB']['turnover']:.4f}, held rt PUB {C['PUB']['round_trip']:.1f}, "
              f"inv/trade PUB {INV['PUB']['net_per_trade']:+.1f}, {len(res_v['trades']):,} trades, max age {int(ages.max())} ({el()})")
        return dict(k=k, res_v=res_v, res_i=res_i, contrib=contrib, C=C, G1=G1, G2=G2, G3=G3, LEGS=LEGS, INV=INV,
                    borrow=dict(variant=BV, invariant=BI), top5=top_five(res_v), max_age=int(ages.max()), ent=int(res_v["ent"].sum()))

    CELLS = {k: run_cell(k) for k in KS}

    # ---- assertions -------------------------------------------------------------------------------
    print("\nASSERTIONS")
    ref = d343["cells"]["RSI/v2"]
    worst = 0.0
    for cv in CONVS:
        c = CELLS[20]
        worst = max(worst, abs(c["C"][cv]["net_bp"] - ref["costed"][cv]["net_bp"]),
                    abs(c["C"][cv]["sharpe_net"] - ref["costed"][cv]["sharpe_net"]),
                    abs(c["INV"][cv]["net_per_trade"] - ref["invariant"][cv]["net_per_trade"]))
    assert worst < 1e-9, f"[1] {worst:.2e}"
    print(f"    [1] IDENTITY: k=20 reproduces D343's rsi v2 cell to {worst:.1e} -- net and Sharpe under both conventions, invariant per trade")

    ents = [CELLS[k]["ent"] for k in KS]
    assert len(set(ents)) == 3 and all(CELLS[k]["max_age"] == k for k in KS), f"[T] {ents} {[CELLS[k]['max_age'] for k in KS]}"
    print(f"    [T] BASE_HOLD BITES: entries {ents[0]:,} / {ents[1]:,} / {ents[2]:,} at k=10/20/40; every ledger's max age equals its k")

    rng = np.random.default_rng(LAG_SEED)
    nonempty = np.array([t for t in range(1, T) if gate_rows(gate, 0, t).size > 0])
    bars = rng.choice(nonempty, size=N_LAG_BARS, replace=False)
    n_unl = 0
    for t in bars:
        got = set(int(r) for r in gate_rows(gate, 0, int(t)))
        assert got == V38.rebuild_long_set(sc, base, finT, int(t), 1), f"[A] bar {t}"
        n_unl += V38.rebuild_long_set(sc, base, finT, int(t), 0) != got
    assert n_unl > N_LAG_BARS // 2, "[A]"
    print(f"    [A] LAG AUDIT: the one gate all three k read, rebuilt from the floored score at t-1, equals the gate on all "
          f"{N_LAG_BARS} sampled bars; the unlagged rebuild differs on {n_unl}")

    C40 = CELLS[40]
    tr = C40["res_v"]["trades"]
    pnl = np.array([t[3] for t in tr])
    rec = FL.pnl_recomputed_fill(tr, r1T, mkt, ocT, mkt_oc)
    worst_s = float(np.abs(rec - pnl).max())
    assert worst_s < 1e-12, f"[S] {worst_s:.2e}"
    ex = np.array([float((ocT[e0, row] - mkt_oc[e0]) + (r1T[e0 + 1:e0 + age, row] - mkt[e0 + 1:e0 + age]).sum())
                   for row, e0, age, _p, _s in tr])
    longs = np.array([t[4] == 0 for t in tr])
    assert (pnl[longs & (ex > 0)] > 0).all() and (pnl[~longs & (ex < 0)] > 0).all(), "[S]"
    print(f"    [S] SIGN IN MONEY: every k=40 trade equals the open-fill recomputation to {worst_s:.1e}; favourable paths pay positively")

    W.BASE_HOLD = 40
    res_c = W.simulate(A2, gate, DEPTH, True, slots=True, fill="open", accumulate="compound")
    assert [(t[0], t[1], t[2], t[4]) for t in tr] == [(t[0], t[1], t[2], t[4]) for t in res_c["trades"]], "[RQ]"
    pnl_c = np.array([t[3] for t in res_c["trades"]])
    assert not np.allclose(pnl, pnl_c) and abs(C40["G1"]["PUB"]["trade_mean_bp"] - float(pnl.mean()) * 1e4) < 1e-9, "[RQ]"
    print(f"    [RQ] RIGHT QUANTITY: same {len(tr):,} k=40 entries under compound accumulation, {int((pnl != pnl_c).sum()):,} P&Ls differ")

    for k in KS:
        c = CELLS[k]
        res_v, contrib = c["res_v"], c["contrib"]
        resid = c["C"]["PUB"]["gross_bp"] - float(contrib.sum()) / c["C"]["PUB"]["bars"] * 1e4
        n_open = int(res_v["ent"].sum()) - len(res_v["trades"])
        gap_bars, first, TT = G22.unattributed(res_v)
        assert 0 <= n_open <= 2 * DEPTH and first >= TT - k and abs(resid) < 1.0, f"[2] k={k}: {n_open} {first} {resid}"
        c["recon"] = dict(residual_bp=resid, open_positions=n_open, first_unattributed_bar=int(first))
    broke = False
    try:
        _, f2, _ = G22.unattributed(C40["res_v"], [t for i, t in enumerate(tr) if i != len(tr) // 2])
        assert f2 >= T - 40
    except AssertionError:
        broke = True
    assert broke, "[2]"
    print("    [2] RECONCILIATION: every k's ledger reconstructs gross to < 1 bp with no hole before T-k; rejects a ledger missing a trade")

    k1 = max(1, pnl.size // 100)
    broke = False
    try:
        _, kt, kb = G22.trim_sym(pnl, k1, k1 + 1)
        assert kt == kb
    except AssertionError:
        broke = True
    assert broke and all(CELLS[k]["G2"]["n_dropped_top"] == CELLS[k]["G2"]["n_dropped_bottom"] for k in KS), "[3]"
    print("    [3] the 1% trim is symmetric in every cell and rejects a trim one deeper on the bottom")

    rot = Y.gate_from(np.roll(rankT, 501, axis=1), finT)
    r_rot = W.simulate(A2, rot, DEPTH, True, fill="open")
    g_rot = float(r_rot["book"][r_rot["mask"]].mean()) * 1e4
    assert abs(g_rot - C40["C"]["PUB"]["gross_bp"]) > 1e-9, "[N]"
    print(f"    [N] CAUSALITY: rotating the rank array by 501 bars moves k=40 gross {C40['C']['PUB']['gross_bp']:+.2f} -> {g_rot:+.2f}")

    wb = max(c["borrow"][lens]["reconcile_worst"] for c in CELLS.values() for lens in ("variant", "invariant"))
    assert wb < 1e-9 and all(c["borrow"]["variant"]["gc_htb"][cv]["net_bp"] == c["C"][cv]["net_bp"] for c in CELLS.values() for cv in CONVS), "[B]"
    print(f"    [B] BORROW: per bar x cnt1 == per trade to {wb:.1e} on all three cells; net_bp untouched")

    broke = False
    try:
        r0 = CELLS[20]["res_v"]
        bk = r0["book"].copy()
        bk[np.flatnonzero(r0["mask"])[:200]] += 5e-4
        bad = G22.costed(dict(r0, book=bk), G4["PUB"])
        assert abs(bad["net_bp"] - ref["costed"]["PUB"]["net_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6]"
    print("    [6] and [1] raises on a book handed +5 bp on 200 masked bars")

    if a.selftest:
        print(f"\nOK  assertions pass  ({el()})")
        return 0

    # ---- the three cells side by side ---------------------------------------------------------------------
    print("\n" + "=" * 100)
    print("THE HOLD -- rsi, keep_v2, open fill; variant book")
    print("=" * 100)
    print("  %-30s %14s %14s %14s" % ("", "k=10", "k=20", "k=40"))
    rows = (("gross bp/bar", lambda c: "%+.2f" % c["C"]["PUB"]["gross_bp"]),
            ("cost bp/bar PUB", lambda c: "%.2f" % c["C"]["PUB"]["cost_bp"]),
            ("NET bp/bar PUB", lambda c: "%+.2f" % c["C"]["PUB"]["net_bp"]),
            ("NET bp/bar PB", lambda c: "%+.2f" % c["C"]["PB"]["net_bp"]),
            ("NET after GC+HTB PUB", lambda c: "%+.2f" % c["borrow"]["variant"]["gc_htb"]["PUB"]["net_bp_borrow"]),
            ("vol bp/bar", lambda c: "%.1f" % c["C"]["PUB"]["vol_bp"]),
            ("NET Sharpe PUB", lambda c: "%+.3f" % c["C"]["PUB"]["sharpe_net"]),
            ("gross Sharpe", lambda c: "%+.3f" % c["C"]["PUB"]["sharpe_gross"]),
            ("maxDD bp", lambda c: "%.0f" % c["C"]["PUB"]["maxdd_bp"]),
            ("turnover/bar (names HELD)", lambda c: "%.4f" % c["C"]["PUB"]["turnover"]),
            ("held rt PUB (spread)", lambda c: "%.1f" % c["C"]["PUB"]["round_trip"]),
            ("held half-spread PUB", lambda c: "%.2f" % c["C"]["PUB"]["held_half_spread"]),
            ("held price", lambda c: "$%.2f" % c["C"]["PUB"]["held_price"]),
            ("trades", lambda c: "%d" % len(c["res_v"]["trades"])),
            ("mean move / 2c PUB", lambda c: "%.2fx" % c["G1"]["PUB"]["trade_mean_over_2c"]),
            ("breakeven / measured PUB", lambda c: "%.2fx" % c["G1"]["PUB"]["breakeven_multiple"]),
            ("invariant PUB per trade", lambda c: "%+.1f" % c["INV"]["PUB"]["net_per_trade"]),
            ("  long / short", lambda c: "%+.1f / %+.1f" % (c["LEGS"]["PUB"][0]["net"], c["LEGS"]["PUB"][1]["net"])),
            ("g2 mean / median", lambda c: "%+.0f / %+.0f" % (c["G2"]["mean_bp"], c["G2"]["median_bp"])),
            ("g2 trimmed vs 2c", lambda c: "%+.0f vs %.0f" % (c["G2"]["mean_trimmed_bp"], c["G1"]["PUB"]["two_c_bp"])),
            ("g2 top1% / bottom1%", lambda c: "%+.0f%% / %+.0f%%" % (100 * c["G2"]["top1_share"], 100 * c["G2"]["bottom1_share"])),
            ("g3 names / to half", lambda c: "%d / %d" % (c["G3"]["PUB"]["names"], c["G3"]["PUB"]["names_to_half_pnl"])),
            ("g3 years net+", lambda c: "%d of %d" % (c["G3"]["PUB"]["years_profitable_net"], c["G3"]["PUB"]["years"])),
            ("g3 dead share", lambda c: "%.1f%%" % (100 * c["G3"]["PUB"]["dead"]["share_pnl"])),
            ("top trade", lambda c: "%s %.1f%%" % (c["top5"][0]["symbol"], 100 * c["top5"][0]["share"])))
    for label, fn in rows:
        print("  %-30s %14s %14s %14s" % (label, fn(CELLS[10]), fn(CELLS[20]), fn(CELLS[40])))

    # ---- nulls, per k -------------------------------------------------------------------------------------
    NULL = {}
    for k in KS:
        ts = time.time()
        W.BASE_HOLD = k
        rng = np.random.default_rng(NULL_SEED + [k])
        offs = rng.choice(np.arange(1, N_BASE), size=a.draws, replace=True)
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
        assert NG.size >= min(195, a.draws - 5), f"[N] k={k} draws"
        C_ = CELLS[k]["C"]
        dv_ = {"gross_bp": [v[0] for v in by_shift.values()], "sharpe_gross": [v[1] for v in by_shift.values()],
               "sharpe_net_PB": [v[2]["PB"] for v in by_shift.values()], "sharpe_net_PUB": [v[2]["PUB"] for v in by_shift.values()]}
        scores = {"gross_bp": C_["PUB"]["gross_bp"], "sharpe_gross": C_["PUB"]["sharpe_gross"], "sharpe_net_PB": C_["PB"]["sharpe_net"],
                  "sharpe_net_PUB": C_["PUB"]["sharpe_net"]}
        above = {kk: int(sum(1 for x in dv_[kk] if x < scores[kk])) for kk in dv_}
        NULL[k] = dict(draws=int(NG.size), distinct_shifts=len(by_shift), above_k_of_distinct=above,
                       gross_bp=G22.dist(NG, scores["gross_bp"]), sharpe_gross=G22.dist(NSG, scores["sharpe_gross"]),
                       sharpe_net={cv: G22.dist(NSN[cv], C_[cv]["sharpe_net"]) for cv in CONVS}, teeth=bool(np.quantile(NG, .95) > 0))
        print(f"\n  NULL k={k}: {NG.size} draws, {len(by_shift)} distinct shifts ({time.time() - ts:.0f}s)")
        print("  %-16s %10s %10s %10s %10s   %s" % ("statistic", "score", "p50", "p95", "max", "above k of distinct"))
        for lab, d_, key in (("gross bp/bar", NULL[k]["gross_bp"], "gross_bp"), ("gross Sharpe", NULL[k]["sharpe_gross"], "sharpe_gross"),
                             ("net Sharpe PB", NULL[k]["sharpe_net"]["PB"], "sharpe_net_PB"), ("net Sharpe PUB", NULL[k]["sharpe_net"]["PUB"], "sharpe_net_PUB")):
            print("  %-16s %10.3f %10.3f %10.3f %10.3f   %d of %d" % (lab, d_["score"], d_["p50"], d_["p95"], d_["max"], above[key], len(by_shift)))
        print(f"  gross null has teeth: {'yes' if NULL[k]['teeth'] else 'NO'}")

    # ---- predictions ----------------------------------------------------------------------------------------
    net = {k: CELLS[k]["C"]["PUB"]["net_bp"] for k in KS}
    gross = {k: CELLS[k]["C"]["PUB"]["gross_bp"] for k in KS}
    turn = {k: CELLS[k]["C"]["PUB"]["turnover"] for k in KS}
    rt = {k: CELLS[k]["C"]["PUB"]["round_trip"] for k in KS}
    shp = {k: CELLS[k]["C"]["PUB"]["sharpe_net"] for k in KS}
    r1, r2 = turn[10] / turn[20], turn[20] / turn[40]
    rt_move = max(rt.values()) / min(rt.values()) - 1.0
    q = {}
    q["Q1"] = bool(net[40] > net[20])
    q["Q2"] = bool(net[10] < net[20])
    q["Q3"] = bool(1.7 <= r1 <= 2.3 and 1.7 <= r2 <= 2.3)
    q["Q4"] = bool(gross[10] > gross[20] > gross[40])
    q["Q5"] = bool(rt_move < 0.35)
    q["Q6"] = bool(all(gross[k] > NULL[k]["gross_bp"]["p95"] and NULL[k]["teeth"] for k in KS))
    q["Q7"] = bool(shp[40] > shp[20])
    q["Q8"] = bool(all(CELLS[k]["top5"][0]["share"] < 0.07 for k in KS))
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) PUB net k=40 > k=20: {'CONFIRMED' if q['Q1'] else 'FALSIFIED'} -- {net[40]:+.2f} vs {net[20]:+.2f}")
    print(f"  Q2 PUB net k=10 < k=20: {'CONFIRMED' if q['Q2'] else 'FALSIFIED'} -- {net[10]:+.2f} vs {net[20]:+.2f}")
    print(f"  Q3 turnover ~ 1/k within 15%: {'CONFIRMED' if q['Q3'] else 'FALSIFIED'} -- ratios {r1:.2f}, {r2:.2f}")
    print(f"  Q4 gross falls monotonically with k: {'CONFIRMED' if q['Q4'] else 'FALSIFIED'} -- {gross[10]:+.2f} / {gross[20]:+.2f} / {gross[40]:+.2f}")
    print(f"  Q5 held PUB round trip moves < 35%: {'CONFIRMED' if q['Q5'] else 'FALSIFIED'} -- {rt[10]:.1f} / {rt[20]:.1f} / {rt[40]:.1f} ({100 * rt_move:.0f}%)")
    print(f"  Q6 all three above gross null p95 with teeth: {'CONFIRMED' if q['Q6'] else 'FALSIFIED'} -- " +
          ", ".join(f"k={k} {gross[k]:+.2f} vs {NULL[k]['gross_bp']['p95']:+.2f} ({NULL[k]['above_k_of_distinct']['gross_bp']} of {NULL[k]['distinct_shifts']})" for k in KS))
    print(f"  Q7 (against) PUB net Sharpe k=40 > k=20: {'CONFIRMED' if q['Q7'] else 'FALSIFIED'} -- {shp[40]:+.3f} vs {shp[20]:+.3f}")
    print(f"  Q8 no top trade > 7%: {'CONFIRMED' if q['Q8'] else 'FALSIFIED'} -- " + ", ".join(f"k={k} {CELLS[k]['top5'][0]['symbol']} {100 * CELLS[k]['top5'][0]['share']:.1f}%" for k in KS))

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

    cells_out = {str(k): dict(costed=c["C"], group1=c["G1"], group2=c["G2"], group3=c["G3"],
                             legs={cv: {str(s): c["LEGS"][cv][s] for s in (0, 1)} for cv in CONVS}, invariant=c["INV"],
                             borrow=c["borrow"], top5=c["top5"], trades=len(c["res_v"]["trades"]), entries=c["ent"], recon=c["recon"])
                 for k, c in CELLS.items()}
    out = dict(note="D344: rsi under keep_v2 and the open fill at k in {10, 20, 40}; k=20 is D343's identity. Three cells; a k chosen "
                    "here is a parameter, not a validation. Variant bp/bar and invariant per trade never compared.",
               cells=cells_out, null=NULL, mechanism=dict(turnover=turn, turnover_ratios=[r1, r2], round_trip_pub=rt, rt_move=rt_move),
               predictions=q, identity_worst=worst)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({el()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

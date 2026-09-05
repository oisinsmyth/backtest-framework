"""D342 -- rsi under the floor and the open fill: the candidate record.

    uv run python scripts/run_d342_rsi_candidate.py --selftest
    uv run python scripts/run_d342_rsi_candidate.py [--draws 200]

One cell: rsi symmetric, depth 2, k=20, D303 target, F0, the declared floor
(replace), the open fill; both lenses, PB and PUB, GC+HTB. retrace_leg under the
same conventions is simulated beside it for the left-tail comparison only. The
four groups via D322's functions with contributions_fill; the top-five table with
as-traded price and dollar-volume percentile; the top trade's bars printed; the
per-leg implementation-lag premium; a 200-draw rotation null with the number of
distinct shifts stated on every line.

D341's group-1 to group-3 numbers for this cell are IDENTITIES here ([1]), not
findings. ASSERTIONS [K][F0][R][F][1][A][S][RQ][2][3][N][B][U][6].
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


V41 = _load("d341r", "run_d341_floor_and_open_fill.py")   # main guarded; carries every alias
V35, V31, PA, V9 = V41.V35, V41.V31, V41.PA, V41.V9
V6, Y, W, D, M, SP, R, X = V41.V6, V41.Y, V41.W, V41.D, V41.M, V41.SP, V41.R, V41.X
G22, BR, V38, CEN, UF, FL = V41.G22, V41.BR, V41.V38, V41.CEN, V41.UF, V41.FL

SIG, K0, DEPTH, N_BASE, ANN = "rsi", 20, 2, W.N_BASE, 252.0
NULL_SEED, LAG_SEED, N_LAG_BARS = [W.SEED, 342], 342, 200
CONVS = ("PB", "PUB")
OUT = REPO / "data" / "d342_rsi_candidate.json"
D341_JSON = REPO / "data" / "d341_floor_and_open_fill.json"
CENSUS_JSON = REPO / "data" / "d339_census.json"
gate_rows = V38.gate_rows


def rsi_simple(close, w=14):
    """A plain RSI on a synthetic path for [U]: 100 - 100/(1 + mean gain / mean loss)."""
    d = np.diff(close)
    up, dn = np.clip(d, 0, None), np.clip(-d, 0, None)
    return 100.0 - 100.0 / (1.0 + up[-w:].mean() / dn[-w:].mean())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    print("D342  rsi under the floor and the open fill -- the candidate record")

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
    d341 = json.loads(D341_JSON.read_text())
    census = json.loads(CENSUS_JSON.read_text())
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
    keep = UF.floor_mask(RAW_CLOSE, DV, finT)
    share = UF.floor_share(keep, finT)
    cen_c = float(json.loads((REPO / "data" / "d339_universe_floor.json").read_text())["floor"]["census_c"])  # KeyError if absent
    assert abs(share - cen_c) < 1e-9, f"[R] floor share {share:.8f} != census {cen_c:.8f}"
    print(f"    [R] RAW PRICE and FLOOR: factor == census factor; floor fails {100 * share:.4f}% of live name-bars == census")
    A2, fbmask, FBREP = FL.with_open_fill(A, panel, g)
    ocT, mkt_oc = A2["ocT"], A2["mkt_oc"]
    print(f"    [F] FALLBACK: {FBREP['fallback_cells']:,} of {FBREP['priced_cells']:,} priced cells lack a usable open ({el()})")

    # ---- the cells ------------------------------------------------------------------------
    def floored_score(sig):
        return UF.apply_floor_replace(np.where(excl, np.nan, z[sig]), keep)

    SC = {s: floored_score(s) for s in (SIG, "retrace_leg")}
    RK = {s: Y.rank_single({s: SC[s]}, base, s, n, T) for s in SC}
    GATE = {s: Y.gate_from(RK[s], finT) for s in SC}
    W.BASE_HOLD = K0

    def run_cell(gate, fill, lens_i=True):
        res_v = W.simulate(A2, gate, DEPTH, True, slots=True, fill=fill)
        res_i = W.simulate(A2, gate, DEPTH, True, slots=False, fill=fill) if lens_i else None
        contrib = G22.contributions(res_v, r1T) if fill == "close" else FL.contributions_fill(res_v, r1T, ocT)
        C = {cv: G22.costed(res_v, G4[cv]) for cv in CONVS}
        G1 = {cv: G22.group1(res_v, C[cv], contrib, r1T) for cv in CONVS}
        G2 = G22.group2(res_v)
        G3 = {cv: G22.group3(res_v, contrib, C[cv], years, dead, CLOSE, HALF[cv]) for cv in CONVS}
        out = dict(res_v=res_v, res_i=res_i, contrib=contrib, C=C, G1=G1, G2=G2, G3=G3)
        if lens_i:
            out["LEGS"] = {cv: V9.per_leg(res_i, HALF[cv], CLOSE, r1T, mkt) for cv in CONVS}
            out["INV"] = {cv: V9.invariant_legcost(res_i, out["LEGS"][cv]) for cv in CONVS}
            BV, _ = V38.borrow_block(res_v, C, out["INV"], excl, CLOSE, T)
            BI, _ = V38.borrow_block(res_i, C, out["INV"], excl, CLOSE, T)
            out["borrow"] = dict(variant=BV, invariant=BI)
        return out

    RS = run_cell(GATE[SIG], "open")                 # the candidate
    RSC = run_cell(GATE[SIG], "close", lens_i=False)  # for the premium per entry
    RL = run_cell(GATE["retrace_leg"], "open", lens_i=False)  # the tail comparison
    print(f"  cells simulated: rsi floor/open PUB {RS['C']['PUB']['net_bp']:+.2f} bp/bar, retrace_leg floor/open "
          f"{RL['C']['PUB']['net_bp']:+.2f} ({el()})")

    # ---- assertions ---------------------------------------------------------------------------
    print("\nASSERTIONS")
    c41 = d341["cells"]["RSI/floor/open"]
    r41 = d341["cells"]["RL/floor/open"]
    worst = 0.0
    for cv in CONVS:
        worst = max(worst, abs(RS["C"][cv]["net_bp"] - c41["costed"][cv]["net_bp"]),
                    abs(RS["C"][cv]["sharpe_net"] - c41["costed"][cv]["sharpe_net"]),
                    abs(RS["INV"][cv]["net_per_trade"] - c41["invariant"][cv]["net_per_trade"]),
                    abs(RL["C"][cv]["net_bp"] - r41["costed"][cv]["net_bp"]))
    g2r, g3r = RS["G2"], RS["G3"]["PUB"]
    worst = max(worst, abs(g2r["mean_trimmed_bp"] - c41["group2"]["mean_trimmed_bp"]),
                abs(g2r["top1_share"] - c41["group2"]["top1_share"]), abs(g2r["bottom1_share"] - c41["group2"]["bottom1_share"]),
                abs(g3r["names_to_half_pnl"] - c41["group3"]["PUB"]["names_to_half_pnl"]),
                abs(g3r["top5_name_share"] - c41["group3"]["PUB"]["top5_name_share"]),
                abs(g3r["years_profitable_net"] - c41["group3"]["PUB"]["years_profitable_net"]),
                abs(g3r["dead"]["share_pnl"] - c41["group3"]["PUB"]["dead"]["share_pnl"]))
    assert worst < 1e-9, f"[1] {worst:.2e}"
    print(f"    [1] IDENTITY: rsi floor/open reproduces D341 to {worst:.1e} -- net and Sharpe under PB and PUB, invariant per "
          f"trade, trimmed mean, tail shares, names to half, top-5 share, years, dead share; retrace_leg floor/open net too")

    rng = np.random.default_rng(LAG_SEED)
    gate = GATE[SIG]
    nonempty = np.array([t for t in range(1, T) if gate_rows(gate, 0, t).size > 0])
    bars = rng.choice(nonempty, size=N_LAG_BARS, replace=False)
    n_unl = 0
    for t in bars:
        got = set(int(r) for r in gate_rows(gate, 0, int(t)))
        assert got == V38.rebuild_long_set(SC[SIG], base, finT, int(t), 1), f"[A] bar {t}"
        n_unl += V38.rebuild_long_set(SC[SIG], base, finT, int(t), 0) != got
    assert n_unl > N_LAG_BARS // 2, "[A]"
    print(f"    [A] LAG AUDIT: the floored rsi long gate rebuilt from the floored score at t-1 equals the gate on all "
          f"{N_LAG_BARS} sampled bars; the unlagged rebuild differs on {n_unl}")

    tr = RS["res_v"]["trades"]
    pnl = np.array([t[3] for t in tr])
    rec = FL.pnl_recomputed_fill(tr, r1T, mkt, ocT, mkt_oc)
    worst_s = float(np.abs(rec - pnl).max())
    assert worst_s < 1e-12, f"[S] {worst_s:.2e}"
    ex = np.array([float((ocT[e0, row] - mkt_oc[e0]) + (r1T[e0 + 1:e0 + age, row] - mkt[e0 + 1:e0 + age]).sum())
                   for row, e0, age, _p, _s in tr])
    longs = np.array([t[4] == 0 for t in tr])
    assert (pnl[longs & (ex > 0)] > 0).all() and (pnl[~longs & (ex < 0)] > 0).all(), "[S] sign"
    print(f"    [S] SIGN IN MONEY: every trade equals the open-fill recomputation to {worst_s:.1e}; favourable excess paths "
          f"pay positively on every long and every short")

    res_c = W.simulate(A2, gate, DEPTH, True, slots=True, fill="open", accumulate="compound")
    assert [(t[0], t[1], t[2], t[4]) for t in tr] == [(t[0], t[1], t[2], t[4]) for t in res_c["trades"]], "[RQ] keys"
    pnl_c = np.array([t[3] for t in res_c["trades"]])
    assert not np.allclose(pnl, pnl_c) and abs(RS["G1"]["PUB"]["trade_mean_bp"] - float(pnl.mean()) * 1e4) < 1e-9, "[RQ]"
    print(f"    [RQ] RIGHT QUANTITY: same {len(tr):,} entries/exits under compound accumulation, {int((pnl != pnl_c).sum()):,} "
          f"P&Ls differ; group 1 scores the SUMMED ledger")

    res_v, contrib = RS["res_v"], RS["contrib"]
    resid = RS["C"]["PUB"]["gross_bp"] - float(contrib.sum()) / RS["C"]["PUB"]["bars"] * 1e4
    n_open = int(res_v["ent"].sum()) - len(tr)
    gap_bars, first, TT = G22.unattributed(res_v)
    assert 0 <= n_open <= 2 * DEPTH and first >= TT - K0 and abs(resid) < 1.0, f"[2] {n_open} {first} {resid}"
    broke = False
    try:
        _, f2, _ = G22.unattributed(res_v, [t for i, t in enumerate(tr) if i != len(tr) // 2])
        assert f2 >= TT - K0
    except AssertionError:
        broke = True
    assert broke, "[2]"
    print(f"    [2] RECONCILIATION: {len(tr):,} trades reconstruct gross to {resid:+.4f} bp; {n_open} open at T, none before "
          f"bar {first} of {TT}; rejects a ledger missing a trade")

    k1 = max(1, pnl.size // 100)
    broke = False
    try:
        _, kt, kb = G22.trim_sym(pnl, k1, k1 + 1)
        assert kt == kb
    except AssertionError:
        broke = True
    assert broke and RS["G2"]["n_dropped_top"] == RS["G2"]["n_dropped_bottom"], "[3]"
    print(f"    [3] the 1% trim is symmetric (k={k1}) and rejects a trim one deeper on the bottom")

    rot = Y.gate_from(np.roll(RK[SIG], 501, axis=1), finT)
    r_rot = W.simulate(A2, rot, DEPTH, True, fill="open")
    g_rot = float(r_rot["book"][r_rot["mask"]].mean()) * 1e4
    assert abs(g_rot - RS["C"]["PUB"]["gross_bp"]) > 1e-9, "[N]"
    print(f"    [N] CAUSALITY: rotating the rank array by 501 bars moves gross {RS['C']['PUB']['gross_bp']:+.2f} -> {g_rot:+.2f}")

    wb = max(RS["borrow"][lens]["reconcile_worst"] for lens in ("variant", "invariant"))
    assert wb < 1e-9 and all(RS["borrow"]["variant"]["gc_htb"][cv]["net_bp"] == RS["C"][cv]["net_bp"] for cv in CONVS), "[B]"
    print(f"    [B] BORROW: per bar x cnt1 == per trade to {wb:.1e}; net_bp untouched")

    fin = z[SIG][np.isfinite(z[SIG])]
    assert fin.min() >= 0.0 and fin.max() <= 100.0, f"[U] rsi outside [0, 100]: {fin.min()} {fin.max()}"
    path = np.array([10, 10.5, 10.2, 10.8, 11.0, 10.7, 11.3, 11.1, 11.6, 11.4, 12.0, 11.8, 12.3, 12.1, 12.6, 12.4])
    assert abs(rsi_simple(path) - rsi_simple(10 * path)) < 1e-12, "[U] scale"
    print(f"    [U] rsi lies in [{fin.min():.1f}, {fin.max():.1f}] and is unchanged when every price is multiplied by 10")

    broke = False
    try:
        bk = res_v["book"].copy()
        bk[np.flatnonzero(res_v["mask"])[:200]] += 5e-4
        bad = G22.costed(dict(res_v, book=bk), G4["PUB"])
        assert abs(bad["net_bp"] - c41["costed"]["PUB"]["net_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6]"
    print("    [6] and [1] raises on a book handed +5 bp on 200 masked bars")

    if a.selftest:
        print(f"\nOK  assertions pass  ({el()})")
        return 0

    # ---- top trades, the top trade's bars, the data gate -----------------------------------------
    def trade_rows(res, contrib_, kmax=5):
        trs = res["trades"]
        p = np.array([t[3] for t in trs])
        tot = float(p.sum())
        out = []
        for i in np.argsort(-p)[:kmax]:
            row, e0, age, pp, side = trs[i]
            s = panel.symbols[row]
            seg = r1T[e0:e0 + age, row]
            j = int(e0 + np.nanargmax(np.abs(seg)))
            raw_mv = float(g["close"][row, j] / g["close"][row, j - 1] - 1.0)
            divs = []
            for jj in range(e0, e0 + age):
                for dd in ev["dividends"].get(s, []):
                    if dd[0][:10] == panel.dates[jj]:
                        divs.append(float(dd[1]) / float(g["close"][row, jj]))
            out.append(dict(symbol=s, side="long" if side == 0 else "short", entry=panel.dates[e0], hold=int(age),
                            pnl_bp=float(pp) * 1e4, share=float(pp / tot), big_day=panel.dates[j], r1_big=float(seg[j - e0]),
                            raw_big=raw_mv, r1_raw_gap=abs(float(seg[j - e0]) - raw_mv), max_div_over_close=(max(divs) if divs else 0.0),
                            entry_bar_oc=float(ocT[e0, row]), raw_px_prev=float(RAW_CLOSE[e0 - 1, row]),
                            dv_pct_entry=CEN.dv_percentile(DV, finT, int(e0), int(row)), contrib_bp=float(contrib_[i]) * 1e4))
        return out
    TOP5 = trade_rows(res_v, contrib)
    row, e0, age, p_top, side = tr[int(np.argmax(pnl))]
    s_top = panel.symbols[row]
    print("\n" + "=" * 100)
    print("THE TOP FIVE -- rsi floor/open")
    print("=" * 100)
    for t_ in TOP5:
        print("  %-6s %-5s %s hold %2d  %+8.0f bp (%4.1f%%)  big day %s r1 %+6.1f%% raw %+6.1f%% gap %.2fpp  max div/close %.2f%%  "
              "raw px $%.2f  dv pct %.2f" % (t_["symbol"], t_["side"], t_["entry"], t_["hold"], t_["pnl_bp"], 100 * t_["share"],
                                             t_["big_day"], 100 * t_["r1_big"], 100 * t_["raw_big"], 100 * t_["r1_raw_gap"],
                                             100 * t_["max_div_over_close"], t_["raw_px_prev"], t_["dv_pct_entry"]))
    print(f"\nTHE TOP TRADE: {s_top}, {'long' if side == 0 else 'short'}, entered {panel.dates[e0]}, held {age} bars, "
          f"{p_top * 1e4:+.0f} bp = {100 * p_top / float(pnl.sum()):.2f}% of the ledger; as traded ${RAW_CLOSE[e0 - 1, row]:.2f}")
    print("  %-12s %10s %10s %10s %10s %12s %8s %8s %8s  %s" % ("date", "open", "high", "low", "close", "volume", "r1 %", "oc %", "raw %", "div"))
    bars_out = []
    for j in range(max(e0 - 1, 0), min(e0 + age, T)):
        o, h, l, c = (float(g[k][row, j]) for k in ("open", "high", "low", "close"))
        r1 = float(r1T[j, row]) if j >= e0 else np.nan
        oc = float(ocT[j, row]) if j >= e0 else np.nan
        raw = float(g["close"][row, j] / g["close"][row, j - 1] - 1.0) if j > 0 else np.nan
        dv = [dd for dd in ev["dividends"].get(s_top, []) if dd[0][:10] == panel.dates[j]]
        bars_out.append(dict(date=panel.dates[j], open=o, high=h, low=l, close=c, volume=float(VOL[j, row]), r1=r1, oc=oc, raw=raw,
                             dividend=(float(dv[0][1]) if dv else None)))
        f_ = lambda v: ("%+.1f" % (100 * v)) if np.isfinite(v) else "-"
        print("  %-12s %10.3f %10.3f %10.3f %10.3f %12.0f %8s %8s %8s  %s" % (
            panel.dates[j], o, h, l, c, VOL[j, row] if np.isfinite(VOL[j, row]) else 0, f_(r1), f_(oc), f_(raw),
            ("%.4f" % float(dv[0][1])) if dv else "-"))

    # ---- left tails: rsi vs retrace_leg, floor/open -------------------------------------------------
    def bottom_names(res, k):
        trs = res["trades"]
        p = np.array([t[3] for t in trs])
        idx = np.argsort(p)[:k]
        return set(panel.symbols[trs[i][0]] for i in idx), [(panel.symbols[trs[i][0]], panel.dates[trs[i][1]], float(p[i]) * 1e4) for i in idx]
    k_tail = max(1, len(tr) // 100)
    tail_rs, tail_rs_list = bottom_names(res_v, k_tail)
    tail_rl, tail_rl_list = bottom_names(RL["res_v"], max(1, len(RL["res_v"]["trades"]) // 100))
    shared = sorted(tail_rs & tail_rl)
    print(f"\n  LEFT TAILS: rsi's bottom {k_tail} trades span {len(tail_rs)} names; retrace_leg's bottom "
          f"{max(1, len(RL['res_v']['trades']) // 100)} span {len(tail_rl)}; shared names: {len(shared)} {shared}")
    print("  rsi bottom trades: " + ", ".join(f"{s} {d} {v:+.0f}" for s, d, v in tail_rs_list))

    # ---- premium per entry on the floored gate (close-fill ledger) ------------------------------------
    def premium(trades):
        out = {}
        for sd in (0, 1):
            sgn = 1.0 if sd == 0 else -1.0
            tt = [t for t in trades if t[4] == sd]
            rows_ = np.array([t[0] for t in tt]); e0_ = np.array([t[1] for t in tt])
            name = sgn * (r1T[e0_, rows_] - ocT[e0_, rows_])
            out[str(sd)] = dict(n=int(name.size), mean_bp=float(name.mean()) * 1e4, median_bp=float(np.median(name)) * 1e4,
                                t=float(name.mean() / (name.std(ddof=1) / np.sqrt(name.size))))
        return out
    PREM = premium(RSC["res_v"]["trades"])

    # ---- the four groups ----------------------------------------------------------------------------------
    g1, g2, g3 = RS["G1"], RS["G2"], RS["G3"]["PUB"]
    L = RS["LEGS"]["PUB"]
    bv = RS["borrow"]["variant"]
    print("\n" + "=" * 78)
    print("GROUP 1 -- rsi FLOOR/OPEN")
    print("=" * 78)
    ROW = "  %-34s %14s %14s"
    print(ROW % ("", "PB", "PUB"))
    for label, key, fn in (("gross bp/bar", "gross_bp_bar", "%+.2f"), ("cost bp/bar", "cost_bp_bar", "%.2f"),
                           ("NET bp/bar", "net_bp_bar", "%+.2f"), ("vol bp/bar", "vol_bp_bar", "%.1f"),
                           ("gross Sharpe", "sharpe_gross", "%+.3f"), ("NET Sharpe", "sharpe_net", "%+.3f"),
                           ("gross t", "t_gross", "%+.2f"), ("annualised NET %", "ann_net_pct", "%+.2f"),
                           ("maxDD bp", "maxdd_bp", "%.0f"), ("exposure", "exposure_bars", "%.3f"), ("fill", "fill", "%.3f"),
                           ("turnover/bar (names HELD)", "turnover_held", "%.4f"),
                           ("held half-spread bp/side", "held_half_spread", "%.2f"), ("held median price", "held_price", "$%.2f"),
                           ("held median $ volume", "held_dollar_volume", "$%.0f"), ("2c", "two_c_bp", "%.2f"),
                           ("mean move per TRADE bp", "trade_mean_bp", "%+.2f"), ("mean move / 2c", "trade_mean_over_2c", "%.2fx"),
                           ("BREAKEVEN half-spread /side", "breakeven_half_spread_bp_side", "%.2f"),
                           ("breakeven / measured", "breakeven_multiple", "%.2fx")):
        print(ROW % (label, fn % g1["PB"][key], fn % g1["PUB"][key]))
    print("  after GC+HTB: PB %+.2f  PUB %+.2f (borrow %.3f; HTB %.1f%% of short bars);  house: PB %+.2f PUB %+.2f" % (
        bv["gc_htb"]["PB"]["net_bp_borrow"], bv["gc_htb"]["PUB"]["net_bp_borrow"], bv["gc_htb"]["PUB"]["borrow_bp_bar"],
        100 * bv["htb_share_short_bars"], bv["house"]["PB"]["net_bp_borrow"], bv["house"]["PUB"]["net_bp_borrow"]))
    print("  invariant PUB per trade: long %+.1f on %+.1f gross (t %.2f, %d); short %+.1f on %+.1f (t %.2f, %d); both %+.1f" % (
        L[0]["net"], L[0]["gross"], L[0]["t"], L[0]["trades"], L[1]["net"], L[1]["gross"], L[1]["t"], L[1]["trades"],
        RS["INV"]["PUB"]["net_per_trade"]))
    print("  implementation-lag premium per entry on the floored gate: long %+.1f bp (t %+.2f), short %+.1f (t %+.2f)" % (
        PREM["0"]["mean_bp"], PREM["0"]["t"], PREM["1"]["mean_bp"], PREM["1"]["t"]))
    print("\nGROUP 2 -- trades %d, mean %+.1f, MEDIAN %+.1f (mean below median: %s), win %.1f%%, payoff %.2f, hold mean %.1f / median %.0f, skew %+.2f, kurt %.1f" % (
        g2["n"], g2["mean_bp"], g2["median_bp"], "YES" if g2["mean_below_median"] else "no", 100 * g2["win_rate"], g2["payoff"],
        g2["holding_run_mean"], g2["holding_run_median"], g2["skew"], g2["kurtosis_raw"]))
    print("  ex-top 1%% %+.1f, ex-bottom 1%% %+.1f, TRIMMED both %+.1f (PUB 2c %.1f); top 1%% %+.0f%%, bottom 1%% %+.0f%%; top-1%% mean %+.0f, bottom-1%% mean %+.0f" % (
        g2["mean_ex_top_bp"], g2["mean_ex_bottom_bp"], g2["mean_trimmed_bp"], g1["PUB"]["two_c_bp"], 100 * g2["top1_share"],
        100 * g2["bottom1_share"], g2["top1_mean_bp"], g2["bottom1_mean_bp"]))
    print("GROUP 3 (PUB) -- names %d, to half %d, top 1/5/10 %.1f/%.1f/%.1f%%; years net+ %d of %d (gross+ %d); dead %.1f%% of P&L (%.1f%% of trades)" % (
        g3["names"], g3["names_to_half_pnl"], 100 * g3["top1_name_share"], 100 * g3["top5_name_share"], 100 * g3["top10_name_share"],
        g3["years_profitable_net"], g3["years"], g3["years_profitable_gross"], 100 * g3["dead"]["share_pnl"], 100 * g3["dead_trade_share"]))
    print("  %-14s %7s %8s %8s %8s %7s %9s" % ("cut", "P&L%", "trades", "mean bp", "own 2c", "x2c", "net/trade"))
    for label, key in (("dead", "dead"), ("alive", "alive"), ("era 1st half", "era_first_half"), ("era 2nd half", "era_second_half"),
                       ("price LOW", "price_low"), ("price MID", "price_mid"), ("price HIGH", "price_high")):
        x = g3[key]
        print("  %-14s %+6.1f%% %8d %+8.1f %8.1f %6.2fx %+9.1f" % (label, 100 * x["share_pnl"], x["n"], x["mean_bp"], x["two_c_bp"],
                                                                  x["mean_over_2c"], x["net_per_trade_bp"]))
    print("  price terciles cut at $%.2f / $%.2f; by year PUB net: " % tuple(g3["price_cuts"]) +
          " ".join(f"{y}:{v:+.0f}" for y, v in sorted(g3["net_by_year"].items())))

    # ---- the null, resolution stated ------------------------------------------------------------------------
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
    assert NG.size >= min(195, a.draws - 5), f"[N] only {NG.size} valid draws"
    C_ = RS["C"]
    dv_ = {"gross_bp": [v[0] for v in by_shift.values()], "sharpe_gross": [v[1] for v in by_shift.values()],
           "sharpe_net_PB": [v[2]["PB"] for v in by_shift.values()], "sharpe_net_PUB": [v[2]["PUB"] for v in by_shift.values()]}
    scores = {"gross_bp": C_["PUB"]["gross_bp"], "sharpe_gross": C_["PUB"]["sharpe_gross"],
              "sharpe_net_PB": C_["PB"]["sharpe_net"], "sharpe_net_PUB": C_["PUB"]["sharpe_net"]}
    above = {k: int(sum(1 for x in dv_[k] if x < scores[k])) for k in dv_}
    NULL = dict(construction="rank rotation inside the 25-name gate, floor/open", seed=NULL_SEED, draws=int(NG.size),
                distinct_shifts=distinct, above_k_of_distinct=above, gross_bp=G22.dist(NG, scores["gross_bp"]),
                sharpe_gross=G22.dist(NSG, scores["sharpe_gross"]),
                sharpe_net={cv: G22.dist(NSN[cv], C_[cv]["sharpe_net"]) for cv in CONVS})
    teeth = NULL["gross_bp"]["p95"] > 0
    print(f"\n    [N] {NG.size} of {a.draws} draws valid, {distinct} DISTINCT shifts of at most 24 ({time.time() - ts:.0f}s)")
    print("GROUP 4 -- THE NULL (p as 'above k of the distinct rotations')")
    print("  %-16s %10s %10s %10s %10s   %s" % ("statistic", "score", "p50", "p95", "max", "above k of distinct"))
    for lab, d_, key in (("gross bp/bar", NULL["gross_bp"], "gross_bp"), ("gross Sharpe", NULL["sharpe_gross"], "sharpe_gross"),
                         ("net Sharpe PB", NULL["sharpe_net"]["PB"], "sharpe_net_PB"), ("net Sharpe PUB", NULL["sharpe_net"]["PUB"], "sharpe_net_PUB")):
        print("  %-16s %10.3f %10.3f %10.3f %10.3f   %d of %d" % (lab, d_["score"], d_["p50"], d_["p95"], d_["max"], above[key], distinct))
    print(f"  the gross null has teeth (p95 > 0): {'yes' if teeth else 'NO -- R7 flag'}")

    # ---- predictions --------------------------------------------------------------------------------------------
    q = {}
    q["Q1"] = bool(C_["PUB"]["gross_bp"] > NULL["gross_bp"]["p95"] and teeth and above["gross_bp"] >= 22)
    q["Q2"] = bool(C_["PUB"]["sharpe_net"] > NULL["sharpe_net"]["PUB"]["p95"])
    q["Q3"] = bool(all(t_["max_div_over_close"] < 0.01 and t_["r1_raw_gap"] < 0.01 and t_["raw_px_prev"] >= 5.0
                       and t_["dv_pct_entry"] > 0.28 for t_ in TOP5))
    q["Q4"] = bool(len(shared) < 4)
    q["Q5"] = bool(L[0]["net"] > L[1]["net"])
    q["Q6"] = bool(g3["era_first_half"]["share_pnl"] <= 0.65 and g3["era_second_half"]["share_pnl"] <= 0.65)
    q["Q7"] = bool(bv["gc_htb"]["PUB"]["borrow_bp_bar"] < 0.5 and bv["gc_htb"]["PUB"]["net_bp_borrow"] > 3.0)
    q["Q8"] = bool(g1["PUB"]["breakeven_multiple"] >= 1.3)
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) gross above null p95, teeth, above >= 22 of 24: {'CONFIRMED' if q['Q1'] else 'FALSIFIED'} -- "
          f"{C_['PUB']['gross_bp']:+.2f} vs p95 {NULL['gross_bp']['p95']:+.2f} (max {NULL['gross_bp']['max']:+.2f}), above {above['gross_bp']} of {distinct}")
    print(f"  Q2 net Sharpe PUB above matched-cost null p95: {'CONFIRMED' if q['Q2'] else 'FALSIFIED'} -- {C_['PUB']['sharpe_net']:+.3f} vs "
          f"p95 {NULL['sharpe_net']['PUB']['p95']:+.3f} (max {NULL['sharpe_net']['PUB']['max']:+.3f}), above {above['sharpe_net_PUB']} of {distinct}")
    print(f"  Q3 top five: no dividend >= 1%, r1 == raw, raw px >= $5, dv pct > 0.28: {'CONFIRMED' if q['Q3'] else 'FALSIFIED'} -- "
          + "; ".join(f"{t_['symbol']} div {100 * t_['max_div_over_close']:.2f}% gap {100 * t_['r1_raw_gap']:.2f}pp ${t_['raw_px_prev']:.2f} pct {t_['dv_pct_entry']:.2f}" for t_ in TOP5))
    print(f"  Q4 (against) left tails share < 4 names: {'CONFIRMED' if q['Q4'] else 'FALSIFIED'} -- {len(shared)} shared {shared}")
    print(f"  Q5 long leg per trade > short leg: {'CONFIRMED' if q['Q5'] else 'FALSIFIED'} -- long {L[0]['net']:+.1f}, short {L[1]['net']:+.1f}")
    print(f"  Q6 (against) no era half > 65%: {'CONFIRMED' if q['Q6'] else 'FALSIFIED'} -- {100 * g3['era_first_half']['share_pnl']:.1f}% / "
          f"{100 * g3['era_second_half']['share_pnl']:.1f}%")
    print(f"  Q7 GC+HTB < 0.5, PUB after > +3.0: {'CONFIRMED' if q['Q7'] else 'FALSIFIED'} -- {bv['gc_htb']['PUB']['borrow_bp_bar']:.3f}, "
          f"{bv['gc_htb']['PUB']['net_bp_borrow']:+.2f}")
    print(f"  Q8 breakeven >= 1.3x held PUB half-spread: {'CONFIRMED' if q['Q8'] else 'FALSIFIED'} -- {g1['PUB']['breakeven_half_spread_bp_side']:.1f} bp = "
          f"{g1['PUB']['breakeven_multiple']:.2f}x {g1['PUB']['held_half_spread']:.1f}")

    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple, set)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return None if not np.isfinite(o) else float(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        return o

    out = dict(note="D342: rsi symmetric F0 k=20 under the floor (replace) and the open fill -- the candidate record. "
                    "Variant bp/bar and invariant per trade never compared (FINDINGS section 10). Nothing promoted.",
               cell=dict(signal=SIG, k=K0, depth=DEPTH, filter="F0", floor="replace", fill="open"),
               identity_worst=worst, group1=g1, group2=g2, group3=RS["G3"],
               legs={cv: {str(s): RS["LEGS"][cv][s] for s in (0, 1)} for cv in CONVS}, invariant=RS["INV"], borrow=RS["borrow"],
               premium_floored=PREM, top5=TOP5, top_trade=dict(symbol=s_top, side="long" if side == 0 else "short",
                                                                entry=panel.dates[e0], hold=int(age), pnl_bp=float(p_top) * 1e4,
                                                                share=float(p_top / float(pnl.sum())), bars=bars_out),
               left_tails=dict(k=k_tail, rsi_names=sorted(tail_rs), retrace_names=sorted(tail_rl), shared=shared,
                               rsi_bottom_trades=tail_rs_list, retrace_bottom_trades=tail_rl_list),
               retrace_leg_floor_open=dict(costed=RL["C"], group2=RL["G2"]), null=NULL, teeth_gross=teeth, predictions=q,
               reconciliation=dict(residual_bp=resid, open_positions=n_open, first_unattributed_bar=int(first)), fallback=FBREP)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({el()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

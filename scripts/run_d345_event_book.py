"""D345 -- the event-driven book on rsi: flat by default, enter on a signal, exit on a condition.

    uv run python scripts/run_d345_event_book.py --selftest
    uv run python scripts/run_d345_event_book.py [--draws 200]

theta calibrated on exposure (2.0 concurrent per side under a fixed 40-bar hold,
no returns read); three exit arms (target / invalidation / cap), 40-bar cap;
path-variant (N_MAX = 2 per side, most extreme first, a unit of capital on a base
of 4, scored on TOTAL and on DEPLOYED capital) and path-invariant (every signal,
per trade); PUB primary, PB beside, GC+HTB; a per-name time-rotation null on arm A.

The kernel is trusted only through [ID]: fed "rank < 2 at t" with no holding cap
and D303's target with a 20-bar cap, it must reproduce D343's rsi v2 invariant
ledger bit-identically.

ASSERTIONS [K][F0][R][ID][T][A][S][V][X][RQ][2][3][N][B][6] -- pre-reg section 5.
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


V44 = _load("d344r", "run_d344_hold_length.py")      # main guarded; every alias
V35, V31, PA, V9 = V44.V35, V44.V31, V44.PA, V44.V9
V6, Y, W, D, M, SP, R, X = V44.V6, V44.Y, V44.W, V44.D, V44.M, V44.SP, V44.R, V44.X
G22, BR, V38, CEN, UF, FL = V44.G22, V44.BR, V44.V38, V44.CEN, V44.UF, V44.FL
EB = _load("d345eb", "d345_event_book.py")

SIG, CAP, N_MAX, U, X_TARGET, ANN = "rsi", 40, 2, 4, 0.9627, 252.0
ARMS = ("target", "invalidation", "cap")
NULL_SEED, LAG_SEED, N_LAG_BARS = [W.SEED, 345], 345, 200
CONVS = ("PB", "PUB")
OUT = REPO / "data" / "d345_event_book.json"
D343_JSON = REPO / "data" / "d343_relisting_clause.json"
D344_JSON = REPO / "data" / "d344_hold_length.json"
SLOT_SHARPE_K40, SLOT_TRADE_MEAN_K40, SLOT_MAXDD_K40, SLOT_INV_K40 = 0.268, 102.0, 8423.0, -11.8


def ledger_set(trades):
    return sorted((int(a), int(b), int(c), float(d), int(e)) for a, b, c, d, e in trades)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
    print("D345  the event-driven book -- flat by default, enter on a signal, exit on a condition")

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
    A2 = dict(A2, r1T=r1T, finT=finT, mkt=mkt, vxT=np.asarray(A["vxT"]))
    ocT, mkt_oc = A2["ocT"], A2["mkt_oc"]

    # ---- the signal, lagged: score_T[t] = floored, F0-masked rsi at t-1, on the base ---------------------
    sc_nT = UF.apply_floor_replace(np.where(excl, np.nan, z[SIG]), keep)          # (n, T)
    sc_base = np.where(base, sc_nT, np.nan)
    score_T = np.full((T, n), np.nan)
    score_T[1:] = sc_base[:, :-1].T                                              # known at the close of t-1
    defined = EB.defined_bars(score_T)
    print(f"  signal defined on {int(defined.sum()):,} of {T} bars ({el()})")

    # ---- [ID] the kernel reproduces the slot book's invariant lens ---------------------------------------
    rankT = Y.rank_single({SIG: sc_nT}, base, SIG, n, T)                          # (2, T, n), lagged inside
    sig_gl = np.ascontiguousarray(rankT[0] < 2)
    sig_gs = np.ascontiguousarray(rankT[1] < 2)
    W.BASE_HOLD = 20
    res_ref = W.simulate(A2, Y.gate_from(rankT, finT), 2, True, slots=False, fill="open")
    res_id = EB.simulate_event(A2, sig_gl, sig_gs, score_T, exit="target", cap=20, n_max=None, x_target=X_TARGET, U=U)
    assert ledger_set(res_id["trades"]) == ledger_set(res_ref["trades"]), "[ID] ledgers differ"
    assert np.array_equal(res_id["cnt0"], res_ref["cnt0"]) and np.array_equal(res_id["cnt1"], res_ref["cnt1"]), "[ID] cnt"
    assert np.array_equal(res_id["ent"], res_ref["ent"]), "[ID] ent"
    assert np.array_equal(np.nan_to_num(res_id["book_slot"], nan=-9e9), np.nan_to_num(res_ref["book"], nan=-9e9)), "[ID] book"
    ref43 = d343["cells"]["RSI/v2"]["invariant"]["PUB"]["net_per_trade"]
    legs = V9.per_leg(res_ref, HALF["PUB"], CLOSE, r1T, mkt)
    inv = V9.invariant_legcost(res_ref, legs)
    assert abs(inv["net_per_trade"] - ref43) < 1e-9, "[ID] the slot reference is not D343's cell"
    print(f"    [ID] KERNEL IDENTITY: fed 'rank < 2 at t' with no holding cap and D303's target (cap 20), the event simulator "
          f"reproduces the slot book's invariant lens bit-identically -- {len(res_id['trades']):,} trades, cnt0/cnt1/ent and the "
          f"per-side series; that lens is D343's rsi v2 invariant cell ({inv['net_per_trade']:+.2f} per trade)")

    # ---- [T] theta, calibrated on exposure with no returns in reach --------------------------------------
    broke = False
    try:
        EB.calibrate_theta(score_T, finT, CAP, r1T=r1T)          # noqa -- must not be accepted
    except TypeError:
        broke = True
    assert broke, "[T] the calibrator accepted a returns array"
    ts = time.time()
    theta, cal_table = EB.calibrate_theta(score_T, finT, CAP, target=2.0)
    with np.errstate(invalid="ignore"):
        sig_long = score_T <= theta
        sig_short = score_T >= 100.0 - theta
    conc = [r for r in cal_table if r[0] == theta][0]
    print(f"    [T] THETA: calibrated on exposure only (the calibrator has no returns parameter and raised on one): theta = {theta} "
          f"-> fixed-hold concurrency {conc[1]:.2f} long / {conc[2]:.2f} short per side ({time.time() - ts:.0f}s)")

    # ---- the cells -----------------------------------------------------------------------------------------
    def run(exit_, n_max):
        res = EB.simulate_event(A2, sig_long, sig_short, score_T, exit=exit_, cap=CAP, n_max=n_max, x_target=X_TARGET, U=U)
        C = {cv: EB.costed_event(res, HALF[cv], CLOSE, DV) for cv in CONVS}
        contrib = EB.contributions_total(res, r1T, ocT)
        G2 = G22.group2(res)
        res3 = dict(res, book=res["book_tot"], mask=res["defined"])
        G3 = {cv: G22.group3(res3, contrib, dict(cost_bp=C[cv]["total"]["cost_bp"]), years, dead, CLOSE, HALF[cv]) for cv in CONVS}
        # borrow (GC+HTB) per trade and on both capital bases
        tr = res["trades"]
        htb = BR.htb_flags(tr, excl, CLOSE)
        rate = BR.rate_bps(tr, htb, "gc_htb")
        pt = BR.borrow_per_trade_bp(tr, rate)
        bars_tot = int(res["defined"].sum())
        borrow_tot = float(pt.sum()) / bars_tot / U
        held_mean = float(res["held"][res["mask_dep"]].mean())
        borrow_dep = float(pt.sum()) / int(res["mask_dep"].sum()) / held_mean
        BRW = dict(htb_share_short_trades=float(htb[[t[4] == 1 for t in tr]].mean()) if any(t[4] == 1 for t in tr) else 0.0,
                   borrow_bp_total=borrow_tot, borrow_bp_deployed=borrow_dep, borrow_per_trade=float(pt.mean()))
        return dict(res=res, C=C, contrib=contrib, G2=G2, G3=G3, borrow=BRW)

    CELLS = {}
    for arm in ARMS:
        for lens, nm in ((N_MAX, "variant"), (None, "invariant")):
            c = run(arm, lens)
            CELLS[arm, nm] = c
            ct, cd = c["C"]["PUB"]["total"], c["C"]["PUB"]["deployed"]
            print(f"  {arm:12s} {nm:9s}: trades {len(c['res']['trades']):,}, mean/trade {c['C']['PUB']['trade_mean_bp']:+.1f} "
                  f"(net {c['C']['PUB']['trade_net_mean_bp']:+.1f}), TOTAL PUB net {ct['net_bp']:+.2f} Sharpe {ct['sharpe_net']:+.3f} "
                  f"exposure {100 * ct['exposure']:.0f}% pos {ct['mean_positions']:.2f}; DEPLOYED PUB net {cd['net_bp']:+.2f} "
                  f"Sharpe {cd['sharpe_net']:+.3f} ({el()})")

    RV, RI = CELLS["target", "variant"], CELLS["target", "invariant"]

    # ---- assertions ----------------------------------------------------------------------------------------
    print("\nASSERTIONS")
    # [A] lag audit on the invariant arm A
    tri = RI["res"]["trades"]
    n_bad = 0
    for row, e0, age, _p, side in tri:
        s = sc_base[row, e0 - 1]
        ok = (s <= theta) if side == 0 else (s >= 100.0 - theta)
        n_bad += not (s == s and ok)
    assert n_bad == 0, f"[A] {n_bad} entries without a signal at t-1"
    n_unl = sum(1 for row, e0, age, _p, side in tri
                if not (sc_base[row, e0] == sc_base[row, e0] and ((sc_base[row, e0] <= theta) if side == 0 else (sc_base[row, e0] >= 100 - theta))))
    rng = np.random.default_rng(LAG_SEED)
    bars = rng.choice(np.flatnonzero(defined[:T - CAP - 1]), size=N_LAG_BARS, replace=False)
    ent_at = {}
    for row, e0, age, _p, side in tri:
        ent_at.setdefault((e0, side), set()).add(row)
    n_checked = 0
    for t in bars:
        for side, sg in ((0, sig_long), (1, sig_short)):
            want = set(int(r) for r in np.flatnonzero(sg[t] & finT[t]))
            got = ent_at.get((int(t), side), set())
            assert got <= want, f"[A] bar {t} side {side}: an entry without a signal"
            for r in want - got:      # must have been held at t
                assert any(tr_[0] == r and tr_[4] == side and tr_[1] < t < tr_[1] + tr_[2] for tr_ in tri), \
                    f"[A] bar {t}: signal on {panel.symbols[r]} neither entered nor held"
            n_checked += len(want)
    print(f"    [A] LAG AUDIT: every one of {len(tri):,} invariant entries has the signal on the raw floored score at t-1 (the unlagged "
          f"score fails it on {n_unl:,}); on {N_LAG_BARS} sampled bars every signalled name ({n_checked:,}) was entered or already held")
    # [S] sign in money, every ledger
    worst_s = 0.0
    for c in CELLS.values():
        tr = c["res"]["trades"]
        pnl = np.array([t[3] for t in tr])
        rec = FL.pnl_recomputed_fill(tr, r1T, mkt, ocT, mkt_oc)
        worst_s = max(worst_s, float(np.abs(rec - pnl).max()))
        ex = np.array([float((ocT[e0, row] - mkt_oc[e0]) + (r1T[e0 + 1:e0 + age, row] - mkt[e0 + 1:e0 + age]).sum()) for row, e0, age, _p, _s in tr])
        longs = np.array([t[4] == 0 for t in tr])
        assert (pnl[longs & (ex > 0)] > 0).all() and (pnl[~longs & (ex < 0)] > 0).all(), "[S] sign"
    assert worst_s < 1e-12, f"[S] {worst_s:.2e}"
    print(f"    [S] SIGN IN MONEY: every trade in all six ledgers equals the open-fill recomputation to {worst_s:.1e}; favourable paths pay positively")
    # [V] the variant: never more than N_MAX per side; every entry had the signal; skips only when full
    for arm in ARMS:
        rv = CELLS[arm, "variant"]["res"]
        assert rv["cnt0"].max() <= N_MAX and rv["cnt1"].max() <= N_MAX, f"[V] {arm}: more than N_MAX held"
        for row, e0, age, _p, side in rv["trades"]:
            s = sc_base[row, e0 - 1]
            assert s == s and ((s <= theta) if side == 0 else (s >= 100.0 - theta)), f"[V] {arm}: a variant entry without a signal"
    keys_v = set((t[0], t[1], t[4]) for t in RV["res"]["trades"])
    keys_i = set((t[0], t[1], t[4]) for t in tri)
    sub_share = len(keys_v & keys_i) / len(keys_v)
    print(f"    [V] VARIANT: never more than {N_MAX} per side in any arm; every variant entry has the signal at t-1; "
          f"{100 * sub_share:.1f}% of arm-A variant entries are also invariant entries (the rest re-enter names the invariant was still holding); "
          f"skipped signals in arm A: {int(RV['res']['skipped'].sum()):,}")
    # [X] exposure arithmetic
    rv = RV["res"]
    held = rv["cnt0"] + rv["cnt1"]
    assert np.array_equal(held, rv["held"]), "[X] held"
    ct = RV["C"]["PUB"]["total"]
    assert abs(ct["mean_positions"] - float(held[rv["defined"]].mean())) < 1e-12, "[X] mean positions"
    # total series == sum of signed position returns / U, rebuilt from the ledger + open tail is unattributed
    print(f"    [X] EXPOSURE: mean positions {ct['mean_positions']:.3f} == sum(cnt)/bars; the book is flat on {100 * ct['flat_share']:.1f}% of defined bars, "
          f"long {ct['mean_positions_long']:.2f} / short {ct['mean_positions_short']:.2f} per side, max {ct['max_positions']}")
    # [RQ]
    bt, bd = rv["book_tot"][rv["mask_dep"] & rv["defined"]], rv["book_dep"][rv["mask_dep"] & rv["defined"]]
    assert not np.allclose(bt, bd), "[RQ] total == deployed"
    held_ = rv["held"][rv["mask_dep"] & rv["defined"]]
    assert np.allclose(bt, bd * held_ / U), "[RQ] total != deployed x held / U"
    print(f"    [RQ] RIGHT QUANTITY: the total-capital and deployed-capital series differ on every held bar (total = deployed x held/U); "
          f"group 1 is reported on BOTH and never compares them")
    # [2] reconciliation of book_tot from contributions
    for (arm, nm), c in CELLS.items():
        res = c["res"]
        bars_tot = int(res["defined"].sum())
        attributed = float(c["contrib"].sum()) / bars_tot * 1e4
        resid = c["C"]["PUB"]["total"]["gross_bp"] - attributed
        n_open = int(res["ent"].sum()) - len(res["trades"])
        assert abs(resid) < 1.0 and 0 <= n_open <= (2 * N_MAX if nm == "variant" else 10 ** 6), f"[2] {arm}/{nm}: {resid} {n_open}"
        c["recon"] = dict(residual_bp=resid, open_positions=n_open)
    print(f"    [2] RECONCILIATION: every ledger's contributions reconstruct the total-capital gross to < 1 bp (arm A variant "
          f"{RV['recon']['residual_bp']:+.4f}, {RV['recon']['open_positions']} open at T)")
    # [3]
    pnl_v = np.array([t[3] for t in RV["res"]["trades"]])
    k1 = max(1, pnl_v.size // 100)
    broke = False
    try:
        _, kt, kb = G22.trim_sym(pnl_v, k1, k1 + 1)
        assert kt == kb
    except AssertionError:
        broke = True
    assert broke and all(c["G2"]["n_dropped_top"] == c["G2"]["n_dropped_bottom"] for c in CELLS.values()), "[3]"
    print(f"    [3] the 1% trim is symmetric in every cell and rejects a trim one deeper on the bottom")
    # [N] the null moves the book
    rng = np.random.default_rng(NULL_SEED)
    sl_, ss_, sc_ = EB.rotate_signals(sig_long, sig_short, score_T, finT, rng)
    r_rot = EB.simulate_event(A2, sl_, ss_, sc_, exit="target", cap=CAP, n_max=N_MAX, x_target=X_TARGET, U=U)
    assert abs(float(np.nanmean(r_rot["book_tot"])) - float(np.nanmean(rv["book_tot"]))) > 1e-9, "[N] same book"
    assert int(sl_.sum()) == int(sig_long.sum()) and int(ss_.sum()) == int(sig_short.sum()), "[N] rotation changed the signal count"
    print(f"    [N] the per-name time rotation keeps every name's signal count and moves the book "
          f"({1e4 * float(np.nanmean(rv['book_tot'])):+.2f} -> {1e4 * float(np.nanmean(r_rot['book_tot'])):+.2f} gross bp/bar, total capital)")
    # [B]
    for c in CELLS.values():
        tr = c["res"]["trades"]
        htb = BR.htb_flags(tr, excl, CLOSE)
        pt = BR.borrow_per_trade_bp(tr, BR.rate_bps(tr, htb, "gc_htb"))
        assert abs(float(pt.sum()) / int(c["res"]["defined"].sum()) / U - c["borrow"]["borrow_bp_total"]) < 1e-12, "[B]"
    print(f"    [B] BORROW: total-capital borrow per bar equals the per-trade sum / bars / U on every cell; net keys untouched")
    # [6]
    broke = False
    try:
        bt2 = rv["book_tot"].copy()
        bt2[np.flatnonzero(rv["defined"])[:200]] += 5e-4
        bad = EB.costed_event(dict(rv, book_tot=bt2), HALF["PUB"], CLOSE, DV)
        assert abs(bad["total"]["net_bp"] - RV["C"]["PUB"]["total"]["net_bp"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6]"
    print("    [6] and the costing raises on a book handed +5 bp on 200 defined bars")

    if a.selftest:
        print(f"\nOK  assertions pass  ({el()})")
        return 0

    # ---- report ---------------------------------------------------------------------------------------------
    print("\n" + "=" * 110)
    print(f"THE EVENT BOOK -- rsi, theta = {theta} (long <= {theta}, short >= {100 - theta}), keep_v2, open fill, cap {CAP}; "
          f"variant N_MAX = {N_MAX}/side on U = {U} units")
    print("=" * 110)
    hdr = "  %-14s %-9s %7s %8s %8s | %8s %8s %8s %7s %6s %8s | %8s %8s %8s | %8s"
    print(hdr % ("arm", "lens", "trades", "mean/tr", "net/tr", "TOT gr", "TOT net", "TOT shp", "expo", "pos", "TOT dd", "DEP gr", "DEP net", "DEP shp", "PB net"))
    for arm in ARMS:
        for nm in ("variant", "invariant"):
            c = CELLS[arm, nm]
            P, B_ = c["C"]["PUB"], c["C"]["PB"]
            print(hdr % (arm, nm, len(c["res"]["trades"]), "%+.1f" % P["trade_mean_bp"], "%+.1f" % P["trade_net_mean_bp"],
                         "%+.2f" % P["total"]["gross_bp"], "%+.2f" % P["total"]["net_bp"], "%+.3f" % P["total"]["sharpe_net"],
                         "%.0f%%" % (100 * P["total"]["exposure"]), "%.2f" % P["total"]["mean_positions"], "%.0f" % P["total"]["maxdd_bp"],
                         "%+.2f" % P["deployed"]["gross_bp"], "%+.2f" % P["deployed"]["net_bp"], "%+.3f" % P["deployed"]["sharpe_net"],
                         "%+.2f" % B_["total"]["net_bp"]))
    print(f"\n  slot book for comparison (D344, k=40): deployed PUB net +5.14, Sharpe +0.268, mean/trade +102, maxDD 8,423, invariant per trade -11.8")
    P = RV["C"]["PUB"]
    print("\n  ARM A VARIANT, the four groups (PUB):")
    print("    total capital:    gross %+.2f cost %.2f NET %+.2f (after GC+HTB %+.2f) vol %.1f Sharpe %+.3f maxDD %.0f; exposure %.1f%%, flat %.1f%%, "
          "positions %.2f mean / %d max; breakeven half-spread %.1f vs held %.1f" % (
              P["total"]["gross_bp"], P["total"]["cost_bp"], P["total"]["net_bp"], P["total"]["net_bp"] - RV["borrow"]["borrow_bp_total"],
              P["total"]["vol_bp"], P["total"]["sharpe_net"], P["total"]["maxdd_bp"], 100 * P["total"]["exposure"], 100 * P["total"]["flat_share"],
              P["total"]["mean_positions"], P["total"]["max_positions"], P["total"]["breakeven_half_spread_bp_side"], P["held_half_spread"]))
    print("    deployed capital: gross %+.2f cost %.2f NET %+.2f (after GC+HTB %+.2f) vol %.1f Sharpe %+.3f maxDD %.0f; held %.2f per bar" % (
        P["deployed"]["gross_bp"], P["deployed"]["cost_bp"], P["deployed"]["net_bp"], P["deployed"]["net_bp"] - RV["borrow"]["borrow_bp_deployed"],
        P["deployed"]["vol_bp"], P["deployed"]["sharpe_net"], P["deployed"]["maxdd_bp"], P["deployed"]["held_per_bar"]))
    g2 = RV["G2"]
    print("    group 2: trades %d, mean %+.1f, median %+.1f, win %.1f%%, payoff %.2f, hold mean %.1f, skew %+.2f; trimmed %+.1f vs 2c %.1f; top 1%% %+.0f%%, bottom 1%% %+.0f%%" % (
        g2["n"], g2["mean_bp"], g2["median_bp"], 100 * g2["win_rate"], g2["payoff"], g2["holding_run_mean"], g2["skew"], g2["mean_trimmed_bp"],
        P["two_c_bp"], 100 * g2["top1_share"], 100 * g2["bottom1_share"]))
    g3 = RV["G3"]["PUB"]
    print("    group 3: names %d, to half %d, top 1/5/10 %.1f/%.1f/%.1f%%; years net+ %d of %d; dead %.1f%%; eras %.1f%% / %.1f%%; price LOW %.1f%%" % (
        g3["names"], g3["names_to_half_pnl"], 100 * g3["top1_name_share"], 100 * g3["top5_name_share"], 100 * g3["top10_name_share"],
        g3["years_profitable_net"], g3["years"], 100 * g3["dead"]["share_pnl"], 100 * g3["era_first_half"]["share_pnl"],
        100 * g3["era_second_half"]["share_pnl"], 100 * g3["price_low"]["share_pnl"]))
    trs = RV["res"]["trades"]
    pn = np.array([t[3] for t in trs])
    tot = float(pn.sum())
    print("    top five:")
    TOP5 = []
    for i in np.argsort(-pn)[:5]:
        row, e0, age, p_, side = trs[i]
        TOP5.append(dict(symbol=panel.symbols[row], side="long" if side == 0 else "short", entry=panel.dates[e0], hold=int(age),
                         pnl_bp=float(p_) * 1e4, share=float(p_ / tot), raw_px_prev=float(RAW_CLOSE[e0 - 1, row]),
                         dv_pct_entry=CEN.dv_percentile(DV, finT, int(e0), int(row)), rsi_at_signal=float(sc_base[row, e0 - 1])))
        t_ = TOP5[-1]
        print("      %-6s %-5s %s hold %2d  %+8.0f bp (%4.1f%%)  rsi at signal %.1f  raw px $%.2f  dv pct %.2f" % (
            t_["symbol"], t_["side"], t_["entry"], t_["hold"], t_["pnl_bp"], 100 * t_["share"], t_["rsi_at_signal"], t_["raw_px_prev"], t_["dv_pct_entry"]))

    # ---- the null on arm A, both lenses -----------------------------------------------------------------------
    ts = time.time()
    rng = np.random.default_rng(NULL_SEED)
    NULL = {"variant": dict(dep_gross_sharpe=[], dep_net_sharpe_pub=[], tot_gross=[], tot_net_sharpe_pub=[]),
            "invariant": dict(trade_mean=[], trade_net_pub=[])}
    for d_ in range(a.draws):
        sl_, ss_, sc_ = EB.rotate_signals(sig_long, sig_short, score_T, finT, rng)
        rv_ = EB.simulate_event(A2, sl_, ss_, sc_, exit="target", cap=CAP, n_max=N_MAX, x_target=X_TARGET, U=U)
        cv_ = EB.costed_event(rv_, HALF["PUB"], CLOSE, DV)
        NULL["variant"]["dep_gross_sharpe"].append(cv_["deployed"]["sharpe_gross"])
        NULL["variant"]["dep_net_sharpe_pub"].append(cv_["deployed"]["sharpe_net"])
        NULL["variant"]["tot_gross"].append(cv_["total"]["gross_bp"])
        NULL["variant"]["tot_net_sharpe_pub"].append(cv_["total"]["sharpe_net"])
        ri_ = EB.simulate_event(A2, sl_, ss_, sc_, exit="target", cap=CAP, n_max=None, x_target=X_TARGET, U=U)
        ci_ = EB.costed_event(ri_, HALF["PUB"], CLOSE, DV)
        NULL["invariant"]["trade_mean"].append(ci_["trade_mean_bp"])
        NULL["invariant"]["trade_net_pub"].append(ci_["trade_net_mean_bp"])
        if (d_ + 1) % 50 == 0:
            print(f"    null {d_ + 1}/{a.draws} ({time.time() - ts:.0f}s)", flush=True)
    NULL = {lens: {k: np.array(v) for k, v in d_.items()} for lens, d_ in NULL.items()}
    scores = dict(dep_gross_sharpe=P["deployed"]["sharpe_gross"], dep_net_sharpe_pub=P["deployed"]["sharpe_net"],
                  tot_gross=P["total"]["gross_bp"], tot_net_sharpe_pub=P["total"]["sharpe_net"],
                  trade_mean=RI["C"]["PUB"]["trade_mean_bp"], trade_net_pub=RI["C"]["PUB"]["trade_net_mean_bp"])
    NULLD = {}
    print(f"\n  NULL on arm A -- per-name time rotation of the signal, {a.draws} draws, {len(set(NULL['variant']['tot_gross'].tolist()))} distinct ({time.time() - ts:.0f}s)")
    print("  %-10s %-20s %10s %10s %10s %10s %8s" % ("lens", "statistic", "score", "p50", "p95", "max", "p"))
    for lens in ("variant", "invariant"):
        NULLD[lens] = {}
        for k, arr in NULL[lens].items():
            d_ = G22.dist(arr, scores[k])
            NULLD[lens][k] = d_
            print("  %-10s %-20s %10.3f %10.3f %10.3f %10.3f %8.4f" % (lens, k, d_["score"], d_["p50"], d_["p95"], d_["max"], d_["p"]))
    teeth = NULLD["variant"]["dep_gross_sharpe"]["p95"] > 0

    # ---- predictions ----------------------------------------------------------------------------------------------
    PB_ = CELLS["invalidation", "variant"]["C"]["PUB"]
    q = {}
    q["Q1"] = bool(P["deployed"]["sharpe_net"] > SLOT_SHARPE_K40)
    q["Q2"] = bool(P["total"]["sharpe_net"] < SLOT_SHARPE_K40 and abs(P["total"]["sharpe_net"] - SLOT_SHARPE_K40) <= 0.10)
    q["Q3"] = bool(P["trade_mean_bp"] > SLOT_TRADE_MEAN_K40)
    q["Q4"] = bool(0.5 * (P["total"]["mean_positions_long"] + P["total"]["mean_positions_short"]) <= 2.0 and P["total"]["flat_share"] > 0.10)
    q["Q5"] = bool(P["total"]["maxdd_bp"] < SLOT_MAXDD_K40)
    q["Q6"] = bool(PB_["deployed"]["sharpe_net"] > P["deployed"]["sharpe_net"])
    q["Q7"] = bool(RI["C"]["PUB"]["trade_net_mean_bp"] > SLOT_INV_K40)
    q["Q8"] = bool(RI["C"]["PUB"]["trade_net_mean_bp"] > 0.0)
    q["Q9"] = bool(P["deployed"]["sharpe_gross"] > NULLD["variant"]["dep_gross_sharpe"]["p95"] and teeth)
    q["Q10"] = bool(15 <= theta <= 30)
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) arm A variant DEPLOYED PUB net Sharpe > 0.268: {'CONFIRMED' if q['Q1'] else 'FALSIFIED'} -- {P['deployed']['sharpe_net']:+.3f} (net {P['deployed']['net_bp']:+.2f})")
    print(f"  Q2 (against) TOTAL-capital Sharpe below 0.268 and within 0.10: {'CONFIRMED' if q['Q2'] else 'FALSIFIED'} -- {P['total']['sharpe_net']:+.3f} (net {P['total']['net_bp']:+.2f})")
    print(f"  Q3 mean P&L per trade > +102: {'CONFIRMED' if q['Q3'] else 'FALSIFIED'} -- {P['trade_mean_bp']:+.1f}")
    print(f"  Q4 mean positions/side <= 2.0 and flat > 10%: {'CONFIRMED' if q['Q4'] else 'FALSIFIED'} -- {P['total']['mean_positions_long']:.2f} / "
          f"{P['total']['mean_positions_short']:.2f} per side, flat {100 * P['total']['flat_share']:.1f}%")
    print(f"  Q5 total-capital maxDD < 8,423: {'CONFIRMED' if q['Q5'] else 'FALSIFIED'} -- {P['total']['maxdd_bp']:.0f}")
    print(f"  Q6 arm B beats arm A on deployed Sharpe: {'CONFIRMED' if q['Q6'] else 'FALSIFIED'} -- B {PB_['deployed']['sharpe_net']:+.3f} vs A {P['deployed']['sharpe_net']:+.3f}")
    print(f"  Q7 invariant per-trade PUB net > -11.8: {'CONFIRMED' if q['Q7'] else 'FALSIFIED'} -- {RI['C']['PUB']['trade_net_mean_bp']:+.1f} "
          f"(mean {RI['C']['PUB']['trade_mean_bp']:+.1f}, 2c {RI['C']['PUB']['two_c_bp']:.1f}, {len(RI['res']['trades']):,} trades)")
    print(f"  Q8 (against) invariant per-trade PUB net > 0: {'CONFIRMED' if q['Q8'] else 'FALSIFIED'}")
    print(f"  Q9 arm A variant deployed gross Sharpe above null p95, teeth: {'CONFIRMED' if q['Q9'] else 'FALSIFIED'} -- "
          f"{P['deployed']['sharpe_gross']:+.3f} vs p95 {NULLD['variant']['dep_gross_sharpe']['p95']:+.3f} (p {NULLD['variant']['dep_gross_sharpe']['p']:.4f})")
    print(f"  Q10 theta in [15, 30]: {'CONFIRMED' if q['Q10'] else 'FALSIFIED'} -- {theta}")

    def clean(o):
        if isinstance(o, dict):
            return {"/".join(k) if isinstance(k, tuple) else str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, np.ndarray):
            return None
        if isinstance(o, (np.floating, float)):
            return None if not np.isfinite(o) else float(o)
        if isinstance(o, np.integer):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        return o

    cells_out = {f"{arm}/{nm}": dict(costed=c["C"], group2=c["G2"], group3=c["G3"], borrow=c["borrow"], recon=c["recon"],
                                    trades=len(c["res"]["trades"]), entries=int(c["res"]["ent"].sum()), skipped=int(c["res"]["skipped"].sum()))
                 for (arm, nm), c in CELLS.items()}
    out = dict(note="D345: the event-driven book on rsi -- theta calibrated on exposure, three exit arms, variant (N_MAX=2/side, U=4, "
                    "total and deployed capital) and invariant (per trade). Total and deployed are never compared; nothing promoted.",
               theta=theta, calibration=[dict(theta=r[0], conc_long=r[1], conc_short=r[2], conc_mean=r[3]) for r in cal_table],
               construction=dict(signal=SIG, cap=CAP, n_max=N_MAX, U=U, x_target=X_TARGET, floor="keep_v2", fill="open"),
               cells=cells_out, top5_arm_A_variant=TOP5, null=NULLD, null_draws=a.draws, teeth=teeth, predictions=q,
               identity="kernel reproduces D343 rsi v2 invariant ledger bit-identically")
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({el()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

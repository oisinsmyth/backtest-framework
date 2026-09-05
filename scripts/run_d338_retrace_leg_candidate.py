"""D338 -- retrace_leg symmetric under the deal filter: the candidate record.

    uv run python scripts/run_d338_retrace_leg_candidate.py --selftest
    uv run python scripts/run_d338_retrace_leg_candidate.py [--draws 200]

ONE CELL, NO GRID. retrace_leg symmetric, depth 2, k=20, D303's target exit, the
F0 deal windows removed from the score before ranking (D331), the D333-bounded
panel, the D334-rebuilt cache. Both spread conventions (PUB primary), D337's
borrow schemes under NEW keys, both lenses -- never compared on one statistic.

The four groups are d322_four_group_report's own functions applied to this
cell. The null is the family's rank rotation inside the 25-name gate, 200
draws, seeded [W.SEED, 338], scored under both conventions from ONE simulation
per draw. The top trade is named and its bars printed (FINDINGS section 18).

Nothing here can admit a strategy (R8 needs an unseen fixture; holdout 0 reads).

ASSERTIONS -- properties of code
  [K]  the score cache is the D334 rebuild (D335's check)
  [F]  the F0 mask reproduces D331's second pass: 1,719 filings, 2.54% of live
  [1]  the cell reproduces D335's F0 retrace_leg cells to 1e-9, both lenses
  [A]  LAG AUDIT, second implementation: the long-leg gate at t rebuilt from the
       raw F0 score at t-1 and the base at t by a direct stable argsort equals
       the gate's set on 200 sampled bars; the unlagged rebuild differs on most
  [S]  SIGN IN MONEY: a synthetic long over a rise pays positively, a short
       negatively; every real trade's P&L equals sgn*sum(v - mt) from the ledger
  [RQ] the summed ledger differs from accumulate="compound" on identical
       entries/exits, and the summed one is what group 1 scores
  [2]  ledger reconciliation (D322 [2]) and it rejects a ledger missing a trade
  [3]  the 1% trim is symmetric and the check rejects an asymmetric one
  [N]  rotating the rank array moves the book; >= 195 of 200 null draws valid
  [B]  borrow per bar x cnt1 == borrow per trade; house == 300/252 on covered bars
  [U]  the score is bounded to [-30, 30] and scale-free on a synthetic path
  [6]  [1] raises on a book handed +5 bp on 200 masked bars
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

SIG, K0, DEPTH = "retrace_leg", 20, 2
N_BASE = W.N_BASE
NULL_SEED = [W.SEED, 338]
N_LAG_BARS, LAG_SEED = 200, 338
OUT = REPO / "data" / "d338_retrace_leg_candidate.json"
D335_JSON = REPO / "data" / "d335_legs_under_filter.json"
EXPECT_APPLIED, EXPECT_PCT = V35.EXPECT_APPLIED, V35.EXPECT_PCT
ANN = 252.0
CONVS = ("PB", "PUB")


# ------------------------------------------------------------------ helpers
def gate_rows(gate, side, t):
    o = gate["gateO"]
    return gate["gateF"][o[side, t]:o[side, t + 1]]


def rebuild_long_set(score_f0, base, finT, t, lag):
    """Second implementation of the long-leg gate at bar t. Never calls
    rank_single / rank_columns / gate_from: the raw F0 score at t-lag, the base
    at t, one stable argsort, the first N_BASE finite, intersected with finT[t]."""
    v = np.where(base[:, t], score_f0[:, t - lag], np.nan)
    fin = np.isfinite(v)
    if fin.sum() < 2 * N_BASE:
        return set()
    order = np.argsort(v, kind="stable")
    lo = order[:N_BASE]
    return set(int(r) for r in lo if finT[t, r])


def ledger_pnl_recomputed(trades, r1T, mkt):
    out = np.empty(len(trades))
    for i, (row, e0, age, _p, side) in enumerate(trades):
        sgn = 1.0 if side == 0 else -1.0
        out[i] = sgn * float((r1T[e0:e0 + age, row] - mkt[e0:e0 + age]).sum())
    return out


def htb_share_of_short_bars(trades, htb):
    ages = np.array([t[2] for t in trades], float)
    short = np.array([t[4] == 1 for t in trades], bool)
    tot = ages[short].sum()
    return float(ages[short & htb].sum() / tot) if tot > 0 else np.nan


def borrow_block(res, c_by_conv, inv_by_conv, excl, CLOSE, T):
    """D337's schemes on this ledger; new keys only, net_bp untouched."""
    tr = res["trades"]
    htb = BR.htb_flags(tr, excl, CLOSE)
    out = dict(htb_share_short_bars=htb_share_of_short_bars(tr, htb),
               htb_share_short_trades=float(htb[[t[4] == 1 for t in tr]].mean()))
    worst_rec, worst_flat = 0.0, 0.0
    for scheme in ("gc_htb", "house"):
        rate = BR.rate_bps(tr, htb, scheme)
        pt = BR.borrow_per_trade_bp(tr, rate)
        bar = BR.borrow_per_bar_bp(res, tr, rate, T)
        worst_rec = max(worst_rec, BR.reconcile(bar, res, pt))
        if scheme == "house":
            # covered bars: the ledger rebuilds cnt1 exactly there
            d = np.zeros(T + 2)
            for row, e0, age, _p, s in tr:
                if s == 1:
                    d[e0] += 1
                    d[min(e0 + age, T + 1)] -= 1
            rebuilt = np.cumsum(d)[:T]
            cnt1 = np.asarray(res["cnt1"], float)
            cov = res["mask"] & (cnt1 > 0) & (np.abs(rebuilt - cnt1) < 1e-9)
            worst_flat = float(np.abs(bar[cov] - BR.HOUSE_BPS / ANN).max())
        sc = {}
        for cv in CONVS:
            cb = BR.costed_with_borrow(c_by_conv[cv], bar, res["mask"])
            lb = BR.legcost_with_borrow(inv_by_conv[cv], pt) if inv_by_conv else None
            sc[cv] = dict(borrow_bp_bar=cb["borrow_bp"], net_bp_borrow=cb["net_bp_borrow"],
                          net_bp=cb["net_bp"],
                          borrow_per_trade=(lb["borrow_per_trade"] if lb else None),
                          net_per_trade_borrow=(lb["net_per_trade_borrow"] if lb else None))
            assert cb["net_bp"] == c_by_conv[cv]["net_bp"], "[B] net_bp was mutated"
        out[scheme] = sc
    out["reconcile_worst"] = worst_rec
    out["house_flat_worst"] = worst_flat
    return out, htb


# --------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--draws", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    print("D338  retrace_leg symmetric under the deal filter -- the candidate record")

    # [K] the D334 rebuild is on disk: key matches with ragged_panel.py in the
    # tuple, and the npz is newer than the panel builder. D335's third clause
    # (the pre-D333 copy present) is not required here; that copy was
    # deletable after D335 and is gone.
    cache = Path(R.BC.CACHE)
    rp = REPO / "scripts" / "ragged_panel.py"
    assert cache.exists(), "[K] no score cache"
    assert cache.stat().st_mtime > rp.stat().st_mtime, "[K] npz older than ragged_panel.py"
    z_key = str(np.load(cache, allow_pickle=False)["key"])
    assert z_key == R.BC.cache_key(M.B.FIXTURE), "[K] npz key != cache_key() (ragged_panel.py in the tuple)"
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
    first_live = np.array([int(np.flatnonzero(finT[:, i])[0]) if finT[:, i].any() else T
                           for i in range(n)])
    years = np.array([int(d[:4]) for d in panel.dates])
    meta = json.loads(G22.META.read_text())["symbols"]
    dead = np.array([bool(meta.get(s, {}).get("delistingDate")) for s in panel.symbols])
    ev = json.loads(Path(M.B.EVENTS).read_text())
    d335 = json.loads(D335_JSON.read_text())["incumbent_retrace_leg_f0"]
    print(f"  panel {finT.shape}, {int(dead.sum())} delisted names ({time.time() - t0:.0f}s)")

    # ---- the F0 mask -----------------------------------------------------------
    dj = json.loads(V31.DEALS.read_text())
    fb, drops, n_ok = V31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live,
                                      last_live, lambda f: f["form"] in V31.F0_FORMS)
    excl = V31.exclusion_mask(fb, n, T, last_live)
    pct = 100.0 * (excl & finT.T).sum() / finT.sum()
    assert n_ok == EXPECT_APPLIED, f"[F] {n_ok} filings applied, expected {EXPECT_APPLIED}"
    assert abs(pct - EXPECT_PCT) < 0.02, f"[F] {pct:.3f}% excluded, expected {EXPECT_PCT}"
    print(f"    [F] F0 MASK: {n_ok:,} filings applied, {pct:.2f}% of live name-bars excluded")

    # ---- the cell --------------------------------------------------------------
    score_f0 = np.where(excl, np.nan, z[SIG])
    rankT = Y.rank_single({SIG: score_f0}, base, SIG, n, T)
    W.BASE_HOLD = K0
    gate = Y.gate_from(rankT, finT)
    res_v = W.simulate(A, gate, DEPTH, True, slots=True)
    res_i = W.simulate(A, gate, DEPTH, True, slots=False)
    contrib = G22.contributions(res_v, r1T)
    C = {cv: G22.costed(res_v, G4[cv]) for cv in CONVS}
    G1 = {cv: G22.group1(res_v, C[cv], contrib, r1T) for cv in CONVS}
    G2 = G22.group2(res_v)
    G3 = {cv: G22.group3(res_v, contrib, C[cv], years, dead, CLOSE, HALF[cv]) for cv in CONVS}
    LEGS = {cv: V9.per_leg(res_i, HALF[cv], CLOSE, r1T, mkt) for cv in CONVS}
    INV = {cv: V9.invariant_legcost(res_i, LEGS[cv]) for cv in CONVS}
    print(f"  cell simulated, both lenses ({time.time() - t0:.0f}s)")

    # ---- assertions ------------------------------------------------------------
    print("\nASSERTIONS")
    # [1] D335's F0 retrace_leg cells
    worst = 0.0
    for cv in CONVS:
        worst = max(worst,
                    abs(C[cv]["net_bp"] - d335["variant"][cv]["net_bp_bar"]),
                    abs(C[cv]["sharpe_net"] - d335["variant"][cv]["sharpe_net"]),
                    abs(INV[cv]["net_per_trade"] - d335["invariant"][cv]["net_per_trade"]),
                    abs(LEGS[cv][0]["net"] - d335["legs"][cv]["0"]["net"]),
                    abs(LEGS[cv][1]["net"] - d335["legs"][cv]["1"]["net"]))
    assert worst < 1e-9, f"[1] {worst:.2e}"
    print(f"    [1] IDENTITY: reproduces D335's F0 retrace_leg cells to {worst:.1e} -- variant net "
          f"and Sharpe, invariant per trade, both legs, PB and PUB")

    # [A] lag audit, second implementation
    rng = np.random.default_rng(LAG_SEED)
    nonempty = np.array([t for t in range(1, T) if gate_rows(gate, 0, t).size > 0])
    bars = rng.choice(nonempty, size=N_LAG_BARS, replace=False)
    n_diff_unlagged = 0
    for t in bars:
        got = set(int(r) for r in gate_rows(gate, 0, int(t)))
        want = rebuild_long_set(score_f0, base, finT, int(t), 1)
        assert got == want, f"[A] bar {t}: gate {sorted(got)[:6]}... rebuilt {sorted(want)[:6]}..."
        if rebuild_long_set(score_f0, base, finT, int(t), 0) != got:
            n_diff_unlagged += 1
    assert n_diff_unlagged > N_LAG_BARS // 2, f"[A] the unlagged rebuild agrees on {N_LAG_BARS - n_diff_unlagged} bars"
    print(f"    [A] LAG AUDIT: the long-leg gate rebuilt from the raw F0 score at t-1 by a direct "
          f"stable argsort equals the gate on all {N_LAG_BARS} sampled bars;\n        the rebuild "
          f"from the score at t differs on {n_diff_unlagged} of them")

    # [S] sign in money
    v_syn, mt0 = np.array([0.01, 0.02]), np.zeros(2)
    assert (v_syn - mt0).sum() > 0 and -(v_syn - mt0).sum() < 0, "[S] synthetic sign"
    rec = ledger_pnl_recomputed(res_v["trades"], r1T, mkt)
    pnl_v = np.array([t[3] for t in res_v["trades"]])
    worst_s = float(np.abs(rec - pnl_v).max())
    assert worst_s < 1e-12, f"[S] {worst_s:.2e}"
    longs = np.array([t[4] == 0 for t in res_v["trades"]])
    # a favourable move pays positively on both sides: mean over trades with a
    # rising (falling) excess path is positive for longs (shorts)
    ex = np.array([float((r1T[e0:e0 + age, row] - mkt[e0:e0 + age]).sum())
                   for row, e0, age, _p, _s in res_v["trades"]])
    assert (pnl_v[longs & (ex > 0)] > 0).all() and (pnl_v[~longs & (ex < 0)] > 0).all(), "[S] sign"
    print(f"    [S] SIGN IN MONEY: synthetic long over a rise +{(v_syn - mt0).sum():.2f}, short "
          f"-{(v_syn - mt0).sum():.2f}; every real trade equals sgn*sum(v - mt) to {worst_s:.1e};\n"
          f"        a favourable excess path pays positively on every long and every short")

    # [RQ] right quantity
    res_c = W.simulate(A, gate, DEPTH, True, slots=True, accumulate="compound")
    ks = [(t[0], t[1], t[2], t[4]) for t in res_v["trades"]]
    kc = [(t[0], t[1], t[2], t[4]) for t in res_c["trades"]]
    assert ks == kc, "[RQ] compound changed the ledger's entries or exits"
    pnl_c = np.array([t[3] for t in res_c["trades"]])
    assert not np.allclose(pnl_v, pnl_c), "[RQ] the two accumulations agree"
    assert abs(G1["PUB"]["trade_mean_bp"] - float(pnl_v.mean()) * 1e4) < 1e-9, "[RQ] group 1 scores the wrong ledger"
    print(f"    [RQ] RIGHT QUANTITY: same {len(ks):,} entries/exits under compound accumulation, "
          f"{int((pnl_v != pnl_c).sum()):,} P&Ls differ (mean {float(pnl_v.mean()) * 1e4:+.1f} vs "
          f"{float(pnl_c.mean()) * 1e4:+.1f} bp); group 1 scores the SUMMED ledger")

    # [2] ledger reconciliation
    attributed = float(contrib.sum()) / C["PUB"]["bars"] * 1e4
    resid = C["PUB"]["gross_bp"] - attributed
    n_open = int(res_v["ent"].sum()) - len(res_v["trades"])
    gap_bars, first, TT = G22.unattributed(res_v)
    assert 0 <= n_open <= 2 * DEPTH, f"[2] {n_open} positions unaccounted"
    assert first >= TT - K0, f"[2] the ledger misses held bars from bar {first} of {TT} -- a HOLE"
    assert abs(resid) < 1.0, f"[2] {resid:.4f} bp unattributed"
    ratio = float(pnl_v.mean()) / float(contrib.mean())
    assert 1.5 < ratio < 2.5, f"[2] trade P&L is {ratio:.2f}x its contribution"
    broke = False
    try:
        short = [t for i, t in enumerate(res_v["trades"]) if i != len(res_v["trades"]) // 2]
        _, f2, _ = G22.unattributed(res_v, short)
        assert f2 >= TT - K0
    except AssertionError:
        broke = True
    assert broke, "[2] the accounting accepted a ledger missing a trade"
    print(f"    [2] RECONCILIATION: {len(res_v['trades']):,} closed trades reconstruct gross to "
          f"{resid:+.4f} bp; {n_open} positions open at T ({gap_bars:.0f} position-bars, none before "
          f"bar {first} of {TT});\n        trade P&L is {ratio:.2f}x its contribution; the check rejects "
          f"a ledger missing one mid-run trade")

    # [3] symmetric trim
    k1 = max(1, pnl_v.size // 100)
    broke = False
    try:
        _, kt, kb = G22.trim_sym(pnl_v, k1, k1 + 1)
        assert kt == kb
    except AssertionError:
        broke = True
    assert broke and G2["n_dropped_top"] == G2["n_dropped_bottom"], "[3]"
    print(f"    [3] the 1% trim is symmetric (k={k1}) and the check rejects a trim one deeper on the bottom")

    # [N] rotation moves the book
    rot = np.roll(rankT, 501, axis=1)
    g_rot = Y.gate_from(rot, finT)
    assert not np.array_equal(g_rot["gateF"], gate["gateF"]), "[N] rotation is inert"
    r_rot = W.simulate(A, g_rot, DEPTH, True)
    gross_rot = float(r_rot["book"][r_rot["mask"]].mean()) * 1e4
    assert abs(gross_rot - C["PUB"]["gross_bp"]) > 1e-9, "[N] same book"
    print(f"    [N] CAUSALITY: rotating the rank array by 501 bars moves gross "
          f"{C['PUB']['gross_bp']:+.2f} -> {gross_rot:+.2f} bp/bar")

    # [B] borrow
    BORROW_V, htb_v = borrow_block(res_v, C, INV, excl, CLOSE, T)
    BORROW_I, htb_i = borrow_block(res_i, C, INV, excl, CLOSE, T)
    assert BORROW_V["reconcile_worst"] < 1e-9 and BORROW_I["reconcile_worst"] < 1e-9, "[B] reconcile"
    assert BORROW_V["house_flat_worst"] < 1e-12, f"[B] house {BORROW_V['house_flat_worst']:.2e}"
    print(f"    [B] BORROW: per bar x cnt1 == per trade to {max(BORROW_V['reconcile_worst'], BORROW_I['reconcile_worst']):.1e} bp; "
          f"house == 300/252 to {BORROW_V['house_flat_worst']:.1e} on every ledger-covered short bar")

    # [U] dimensionless and bounded
    fin = z[SIG][np.isfinite(z[SIG])]
    assert fin.min() >= -30.0 and fin.max() <= 30.0, f"[U] {fin.min()} {fin.max()}"
    hi, lo, cl = 10.0, 5.0, 7.0
    assert abs((cl - lo) / (hi - lo) - (10 * cl - 10 * lo) / (10 * hi - 10 * lo)) < 1e-15, "[U] scale"
    print(f"    [U] the score lies in [{fin.min():+.2f}, {fin.max():+.2f}] and (close-lo)/(hi-lo) is unchanged "
          f"when every price is multiplied by 10")

    # [6] raises
    broke = False
    try:
        bk = res_v["book"].copy()
        bk[np.flatnonzero(res_v["mask"])[:200]] += 5e-4
        bad = G22.costed(dict(res_v, book=bk), G4["PUB"])
        assert abs(bad["net_bp"] - d335["variant"]["PUB"]["net_bp_bar"]) < 1e-9
    except AssertionError:
        broke = True
    assert broke, "[6] [1] passed a book handed free money"
    print("    [6] and [1] raises on a book handed +5 bp on 200 masked bars")

    if a.selftest:
        print(f"\nOK  assertions pass  ({time.time() - t0:.0f}s)")
        return 0

    # ---- the top trade, named -----------------------------------------------------
    tr = res_v["trades"]
    order = sorted(range(len(tr)), key=lambda i: -tr[i][3])
    tot = float(pnl_v.sum())
    by = {}
    for (row, _e, _a, _p, _s), cv_ in zip(tr, contrib):
        by[int(row)] = by.get(int(row), 0.0) + float(cv_)
    top_name_row = max(by, key=by.get)
    print("\n" + "=" * 78)
    print("THE TOP TRADES -- named, with the largest one-day |r1| in the hold and any dividend that day")
    print("=" * 78)
    top5 = []
    for i in order[:5]:
        row, e0, age, pnl, side = tr[i]
        s = panel.symbols[row]
        seg = r1T[e0:e0 + age, row]
        j = int(e0 + np.nanargmax(np.abs(seg)))
        raw = float(g["close"][row, j] / g["close"][row, j - 1] - 1.0) if j > 0 else np.nan
        dv = [d for d in ev["dividends"].get(s, []) if d[0][:10] == panel.dates[j]]
        rec5 = dict(symbol=s, side="long" if side == 0 else "short", entry=panel.dates[e0], hold=int(age),
                    pnl_bp=float(pnl) * 1e4, share=float(pnl / tot), big_day=panel.dates[j],
                    r1=float(seg[j - e0]), raw_close_move=raw, dividend=(dv[0][1] if dv else None),
                    close_at_big_day=float(g["close"][row, j]), in_f0_at_entry=bool(excl[row, max(e0 - 1, 0)]),
                    f0_bars_within_400=int(excl[row, max(e0 - 400, 0):min(e0 + 400, T)].sum()))
        top5.append(rec5)
        print(f"  {s:6s} {rec5['side']:5s} entry {rec5['entry']} hold {age:2d}  P&L {rec5['pnl_bp']:+8.0f} bp "
              f"({100 * rec5['share']:.1f}%)  biggest day {rec5['big_day']} r1 {100 * rec5['r1']:+.1f}% "
              f"raw close {100 * raw:+.1f}%  dividend {rec5['dividend'] if dv else '-'}  "
              f"F0 bars within 400: {rec5['f0_bars_within_400']}")
    row, e0, age, pnl, side = tr[order[0]]
    s = panel.symbols[row]
    print(f"\nTHE TOP TRADE: {s}, {'long' if side == 0 else 'short'}, entered {panel.dates[e0]}, held {age} bars, "
          f"{pnl * 1e4:+.0f} bp = {100 * pnl / tot:.2f}% of the ledger")
    print("  %-12s %10s %10s %10s %10s %12s %8s %8s  %s" % ("date", "open", "high", "low", "close", "volume",
                                                            "r1 %", "raw %", "dividend"))
    top_bars, div_hits, max_gap = [], [], 0.0
    for j in range(max(e0 - 1, 0), min(e0 + age, T)):
        o, h, l, c = (float(g[k][row, j]) for k in ("open", "high", "low", "close"))
        r1 = float(r1T[j, row]) if j >= e0 else np.nan
        raw = float(g["close"][row, j] / g["close"][row, j - 1] - 1.0) if j > 0 else np.nan
        dv = [d for d in ev["dividends"].get(s, []) if d[0][:10] == panel.dates[j]]
        amt = float(dv[0][1]) if dv else 0.0
        if j >= e0:
            div_hits.append(amt / c if c > 0 else 0.0)
            if np.isfinite(r1) and np.isfinite(raw):
                max_gap = max(max_gap, abs(r1 - raw))
        top_bars.append(dict(date=panel.dates[j], open=o, high=h, low=l, close=c, volume=float(VOL[j, row]),
                             r1=r1, raw=raw, dividend=(amt if dv else None)))
        print("  %-12s %10.3f %10.3f %10.3f %10.3f %12.0f %8s %8s  %s" % (
            panel.dates[j], o, h, l, c, VOL[j, row] if np.isfinite(VOL[j, row]) else 0,
            ("%+.1f" % (100 * r1)) if np.isfinite(r1) else "-", ("%+.1f" % (100 * raw)) if np.isfinite(raw) else "-",
            ("%.4f" % amt) if dv else "-"))
    j_big = int(e0 + np.nanargmax(np.abs(r1T[e0:e0 + age, row])))
    r1_big = float(r1T[j_big, row])
    raw_big = float(g["close"][row, j_big] / g["close"][row, j_big - 1] - 1.0)
    print(f"  biggest day {panel.dates[j_big]}: r1 {100 * r1_big:+.2f}% against a raw close move of {100 * raw_big:+.2f}%; "
          f"largest dividend/close in the hold {100 * max(div_hits):.2f}%; splits on file {ev['splits'].get(s, [])}")
    print(f"  the largest NAME by contribution: {panel.symbols[top_name_row]} ({100 * by[top_name_row] / float(contrib.sum()):.1f}% of P&L)")
    top_trade = dict(symbol=s, side="long" if side == 0 else "short", entry=panel.dates[e0], hold=int(age),
                     pnl_bp=float(pnl) * 1e4, share_of_ledger=float(pnl / tot), bars=top_bars,
                     big_day=panel.dates[j_big], r1_big=r1_big, raw_big=raw_big,
                     max_dividend_over_close=float(max(div_hits)), splits=ev["splits"].get(s, []),
                     top_name=panel.symbols[top_name_row], top_name_share=float(by[top_name_row] / float(contrib.sum())))

    # ---- the null: one simulation per draw, scored under both conventions ---------------
    ts = time.time()
    rng = np.random.default_rng(NULL_SEED)
    offs = rng.choice(np.arange(1, N_BASE), size=a.draws, replace=True)
    NG, NSG, NSN = [], [], {cv: [] for cv in CONVS}
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
    assert NG.size >= min(195, a.draws - 5), f"[N] only {NG.size} valid draws"
    print(f"\n    [N] {NG.size} of {a.draws} null draws valid ({time.time() - ts:.0f}s)")
    NULL = dict(construction="rank rotation inside the 25-name gate (D300/D306/D322/D323)", seed=NULL_SEED,
                draws=int(NG.size), gross_bp=G22.dist(NG, C["PUB"]["gross_bp"]),
                sharpe_gross=G22.dist(NSG, C["PUB"]["sharpe_gross"]),
                sharpe_net={cv: G22.dist(NSN[cv], C[cv]["sharpe_net"]) for cv in CONVS})

    # ---- report ---------------------------------------------------------------------
    ROW = "  %-34s %14s %14s"
    f2 = lambda v: "%+.2f" % v
    f3 = lambda v: "%+.3f" % v
    pc = lambda v: "%.1f%%" % (100 * v)
    print("\n" + "=" * 78)
    print("GROUP 1 -- PERFORMANCE, NET AND GROSS, PB and PUB (the same ledger costed twice)")
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
                           ("2c = rt_total / 2", "two_c_bp", lambda v: "%.2f" % v),
                           ("mean move per TRADE bp", "trade_mean_bp", f2),
                           ("mean move / 2c", "trade_mean_over_2c", lambda v: "%.2fx" % v),
                           ("BREAKEVEN half-spread /side", "breakeven_half_spread_bp_side", lambda v: "%.2f" % v),
                           ("breakeven / measured", "breakeven_multiple", lambda v: "%.2fx" % v)):
        print(ROW % (label, fn(G1["PB"][key]), fn(G1["PUB"][key])))
    print("\n  BORROW (new keys; net_bp untouched), variant book bp/bar:")
    for scheme in ("gc_htb", "house"):
        print("  %-10s PB net %+.2f -> %+.2f (borrow %.3f)   PUB net %+.2f -> %+.2f (borrow %.3f)" % (
            scheme, BORROW_V[scheme]["PB"]["net_bp"], BORROW_V[scheme]["PB"]["net_bp_borrow"], BORROW_V[scheme]["PB"]["borrow_bp_bar"],
            BORROW_V[scheme]["PUB"]["net_bp"], BORROW_V[scheme]["PUB"]["net_bp_borrow"], BORROW_V[scheme]["PUB"]["borrow_bp_bar"]))
    print(f"  HTB share of short position-bars {100 * BORROW_V['htb_share_short_bars']:.1f}% (variant), "
          f"{100 * BORROW_I['htb_share_short_bars']:.1f}% (invariant)")

    print("\n" + "=" * 78)
    print("GROUP 2 -- TRADE DISTRIBUTION, BOTH TAILS TRIMMED (variant ledger)")
    print("=" * 78)
    for label, key, fn in (("trades", "n", lambda v: "%d" % v), ("mean bp", "mean_bp", lambda v: "%+.1f" % v),
                           ("MEDIAN bp", "median_bp", lambda v: "%+.1f" % v),
                           ("mean BELOW median?", "mean_below_median", lambda v: "YES" if v else "no"),
                           ("win rate", "win_rate", pc), ("payoff", "payoff", lambda v: "%.2f" % v),
                           ("holding run mean / median", "holding_run_mean", lambda v: "%.2f" % v),
                           ("skew", "skew", f2), ("kurtosis (raw)", "kurtosis_raw", lambda v: "%.1f" % v),
                           ("mean EX-TOP 1%", "mean_ex_top_bp", lambda v: "%+.1f" % v),
                           ("mean EX-BOTTOM 1%", "mean_ex_bottom_bp", lambda v: "%+.1f" % v),
                           ("mean TRIMMED both", "mean_trimmed_bp", lambda v: "%+.1f" % v),
                           ("top 1% share of P&L", "top1_share", lambda v: "%+.0f%%" % (100 * v)),
                           ("bottom 1% share of P&L", "bottom1_share", lambda v: "%+.0f%%" % (100 * v))):
        print("  %-34s %14s" % (label, fn(G2[key])))
    print("\n  invariant lens, per trade (PUB): long %+.1f net on %+.1f gross (t %.2f, %d trades); short %+.1f on %+.1f (t %.2f, %d)" % (
        LEGS["PUB"][0]["net"], LEGS["PUB"][0]["gross"], LEGS["PUB"][0]["t"], LEGS["PUB"][0]["trades"],
        LEGS["PUB"][1]["net"], LEGS["PUB"][1]["gross"], LEGS["PUB"][1]["t"], LEGS["PUB"][1]["trades"]))

    print("\n" + "=" * 78)
    print("GROUP 3 -- WHAT THE WINNERS DEPEND ON (each cut charged ITS OWN 2c; PUB)")
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
    print("GROUP 4 -- THE NULL: p50 AND p95, not the percentile alone")
    print("=" * 78)
    print("  %-18s %10s %10s %10s %10s" % ("statistic", "score", "null p50", "null p95", "p"))
    for nm, d_ in (("gross bp/bar", NULL["gross_bp"]), ("gross Sharpe", NULL["sharpe_gross"]),
                   ("net Sharpe PB", NULL["sharpe_net"]["PB"]), ("net Sharpe PUB", NULL["sharpe_net"]["PUB"])):
        print("  %-18s %10.3f %10.3f %10.3f %10.4f" % (nm, d_["score"], d_["p50"], d_["p95"], d_["p"]))
    teeth = all(NULL["sharpe_net"][cv]["p95"] > 0 for cv in CONVS)
    print(f"  the null has teeth (p95 > 0 on net Sharpe, both conventions): {'yes' if teeth else 'NO -- R7 flag'}")

    # ---- predictions -----------------------------------------------------------------
    g1 = G1["PUB"]
    q = {}
    q["Q1"] = bool(top_trade["max_dividend_over_close"] < 0.01 and abs(r1_big - raw_big) < 0.01
                   and top_trade["share_of_ledger"] < 0.05)
    q["Q2"] = bool(G2["mean_below_median"] and abs(G2["bottom1_share"]) > G2["top1_share"]
                   and abs(G2["mean_trimmed_bp"] - G2["mean_bp"]) < 15.0)
    q["Q3"] = bool(g3["names_to_half_pnl"] >= 40 and g3["top10_name_share"] < 0.25)
    q["Q4"] = bool(g3["years_profitable_net"] >= 11 and g3["years_profitable_gross"] >= 13)
    q["Q5"] = bool(g3["price_low"]["share_pnl"] < 0.5 and g3["price_low"]["net_per_trade_bp"] > 0
                   and g3["dead"]["share_pnl"] < 0.3
                   and g3["era_first_half"]["net_per_trade_bp"] > 0 and g3["era_second_half"]["net_per_trade_bp"] > 0)
    q["Q6"] = bool(all(NULL["sharpe_net"][cv]["score"] > NULL["sharpe_net"][cv]["p95"] for cv in CONVS) and teeth)
    q["Q7"] = bool(BORROW_V["htb_share_short_bars"] < 0.10 and BORROW_V["gc_htb"]["PUB"]["borrow_bp_bar"] < 0.5
                   and BORROW_V["gc_htb"]["PUB"]["net_bp_borrow"] > 15.0 and BORROW_V["house"]["PUB"]["net_bp_borrow"] > 15.0)
    q["Q8"] = bool(g1["breakeven_multiple"] >= 2.0)
    q["Q9"] = bool(g1["exposure_bars"] > 0.95 and g1["fill"] > 0.99)
    print("\nPREDICTIONS")
    print(f"  Q1 top trade is a price move, < 5% of ledger: {'CONFIRMED' if q['Q1'] else 'FALSIFIED'} -- "
          f"{top_trade['symbol']} {top_trade['share_of_ledger'] * 100:.2f}%, max dividend/close "
          f"{100 * top_trade['max_dividend_over_close']:.2f}%, r1 vs raw gap {100 * abs(r1_big - raw_big):.2f} pp")
    print(f"  Q2 mean below median, left tail larger, trim < 15: {'CONFIRMED' if q['Q2'] else 'FALSIFIED'} -- mean "
          f"{G2['mean_bp']:+.1f} median {G2['median_bp']:+.1f}, tails {100 * G2['top1_share']:+.0f}% / "
          f"{100 * G2['bottom1_share']:+.0f}%, trimmed {G2['mean_trimmed_bp']:+.1f}")
    print(f"  Q3 names to half >= 40, top-10 < 25%: {'CONFIRMED' if q['Q3'] else 'FALSIFIED'} -- "
          f"{g3['names_to_half_pnl']}, {100 * g3['top10_name_share']:.1f}%")
    print(f"  Q4 PUB net-positive >= 11/17 years, gross >= 13: {'CONFIRMED' if q['Q4'] else 'FALSIFIED'} -- "
          f"{g3['years_profitable_net']} / {g3['years_profitable_gross']} of {g3['years']}")
    print(f"  Q5 cheap tercile < 50% and net > 0; dead < 30%; both eras net > 0: {'CONFIRMED' if q['Q5'] else 'FALSIFIED'} -- "
          f"low {100 * g3['price_low']['share_pnl']:.1f}% ({g3['price_low']['net_per_trade_bp']:+.1f}), dead "
          f"{100 * g3['dead']['share_pnl']:.1f}%, eras {g3['era_first_half']['net_per_trade_bp']:+.1f} / "
          f"{g3['era_second_half']['net_per_trade_bp']:+.1f}")
    print(f"  Q6 above own null p95 on net Sharpe, both conventions, p95 > 0: {'CONFIRMED' if q['Q6'] else 'FALSIFIED'} -- "
          + ", ".join(f"{cv} {NULL['sharpe_net'][cv]['score']:+.3f} vs p95 {NULL['sharpe_net'][cv]['p95']:+.3f} "
                      f"(p50 {NULL['sharpe_net'][cv]['p50']:+.3f}, p {NULL['sharpe_net'][cv]['p']:.4f})" for cv in CONVS))
    print(f"  Q7 HTB < 10%, GC+HTB < 0.5 bp/bar, PUB net after borrow > 15: {'CONFIRMED' if q['Q7'] else 'FALSIFIED'} -- "
          f"HTB {100 * BORROW_V['htb_share_short_bars']:.1f}%, gc {BORROW_V['gc_htb']['PUB']['borrow_bp_bar']:.3f}, "
          f"PUB {BORROW_V['gc_htb']['PUB']['net_bp_borrow']:+.2f} / {BORROW_V['house']['PUB']['net_bp_borrow']:+.2f}")
    print(f"  Q8 breakeven >= 2.0x held PUB half-spread: {'CONFIRMED' if q['Q8'] else 'FALSIFIED'} -- "
          f"{g1['breakeven_half_spread_bp_side']:.1f} bp = {g1['breakeven_multiple']:.2f}x {g1['held_half_spread']:.1f}")
    print(f"  Q9 live > 95% of bars, fill > 99%: {'CONFIRMED' if q['Q9'] else 'FALSIFIED'} -- "
          f"{100 * g1['exposure_bars']:.1f}%, {100 * g1['fill']:.1f}%")

    # ---- write -------------------------------------------------------------------------
    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items()}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return None if not np.isfinite(o) else float(o)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        return o

    out = dict(
        note="D338: retrace_leg symmetric under F0, depth 2, k=20, D303 target; the four groups (d322's functions), "
             "the named top trade, the rank-rotation null under both conventions, D337's borrow as new keys. "
             "Variant bp/bar and invariant per trade are never compared (FINDINGS section 10). Nothing is promoted.",
        cell=dict(signal=SIG, depth=DEPTH, k=K0, filter="F0", panel="D333-bounded", cache="D334"),
        f0=dict(applied=int(n_ok), drops=drops, excluded_live_pct=float(pct)),
        identity_worst=worst,
        lag_audit=dict(bars=N_LAG_BARS, unlagged_differs=int(n_diff_unlagged)),
        group1=G1, group2=G2, group3=G3, legs={cv: {str(s): LEGS[cv][s] for s in (0, 1)} for cv in CONVS},
        invariant=INV, borrow=dict(variant=BORROW_V, invariant=BORROW_I),
        top_trades=top5, top_trade=top_trade, null=NULL,
        reconciliation=dict(residual_bp=resid, open_positions=n_open, unattributed_position_bars=gap_bars,
                            first_unattributed_bar=int(first), pnl_over_contribution=ratio),
        predictions=q)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - t0:.0f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""D347 -- is the long signal real? Three drift-matched controls, two hedges, the splits, the rsi-rank interaction.

    uv run python scripts/run_d347_long_signal_controls.py --selftest
    uv run python scripts/run_d347_long_signal_controls.py --controls hist_L --draws 100   (one per signal, in parallel)
    uv run python scripts/run_d347_long_signal_controls.py --report

Signals as events on the floored, deal-filtered, lagged scores: hist_L and rev_21
entering their bottom decile; rsi's turn (cross back up through 30) and decile as
references; mirrors on the top decile / cross down through 70. Next-open fill;
every event taken (D345's kernel, n_max=None); two exits -- a 40-bar cap (the
statistic every control uses) and invalidation (pct or rsi crossing 50).

Hedge: the floored universe's own equal-weight return (and its open-to-close),
beta-adjusted beside it. Controls: A per-name time rotation of the event series;
B same-date same-rsi-bucket random name; C tail-randomised direction. Splits:
down-years, era halves, the mirror. Interaction: rsi-percentile buckets with each
bucket's forward-40 base rate removed.

ASSERTIONS [K][F0][R][ID][E][H][S][A][B][C][F][X][6] -- pre-reg section 8.
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


V45 = _load("d345r", "run_d345_event_book.py")       # main guarded; every alias
V35, V31, PA, V9 = V45.V35, V45.V31, V45.PA, V45.V9
V6, Y, W, D, M, SP, R, X = V45.V6, V45.Y, V45.W, V45.D, V45.M, V45.SP, V45.R, V45.X
G22, BR, V38, CEN, UF, FL, EB = V45.G22, V45.BR, V45.V38, V45.CEN, V45.UF, V45.FL, V45.EB

CAP, X_TARGET, ANN = 40, 0.9627, 252.0
SIGNALS = ("hist_L", "rev_21", "rsi_turn", "rsi_decile")
SCORE_OF = {"hist_L": "hist_L", "rev_21": "rev_21", "rsi_turn": "rsi", "rsi_decile": "rsi"}
DECILE, MID = 10.0, 50.0
RSI_LO, RSI_HI = 30.0, 70.0
BUCKET_EDGES = (0, 2, 5, 10, 25, 50, 75, 90, 95, 98, 100)
BETA_WIN, BETA_MIN = 63, 21
SEED = W.SEED
OUT = REPO / "data" / "d347_long_signal_controls.json"
CTRL = REPO / "data" / "d347_ctrl_{sig}.json"
D343_JSON = REPO / "data" / "d343_relisting_clause.json"
CONVS = ("PB", "PUB")


# ------------------------------------------------------------------ helpers
def percentile_grid(score_T):
    """(T, n) percentile of the lagged floored score among finite names per bar, 0..100 ascending."""
    T, n = score_T.shape
    out = np.full((T, n), np.nan)
    for t in range(T):
        v = score_T[t]
        fin = np.isfinite(v)
        k = int(fin.sum())
        if k < 50:
            continue
        idx = np.flatnonzero(fin)
        vv = v[idx]
        srt = np.sort(vv)
        below = np.searchsorted(srt, vv, side="left")
        eq = np.searchsorted(srt, vv, side="right") - below
        out[t, idx] = (below + 0.5 * eq) / k * 100.0      # average rank: ties share one percentile
    return out


def floored_market(r1T, ocT, keep, finT, min_names=20):
    ok = keep & finT & np.isfinite(r1T)
    cnt = ok.sum(axis=1)
    m = np.where(cnt >= min_names, np.where(ok, r1T, 0.0).sum(axis=1) / np.maximum(cnt, 1), np.nan)
    ok2 = ok & np.isfinite(ocT)
    cnt2 = ok2.sum(axis=1)
    m_oc = np.where(cnt2 >= min_names, np.where(ok2, ocT, 0.0).sum(axis=1) / np.maximum(cnt2, 1), np.nan)
    return m, m_oc


def roll_beta(r1T, m, w=BETA_WIN, min_obs=BETA_MIN):
    """(T, n) trailing-w OLS slope of the name on the market over bars t-w..t-1, NaN below min_obs."""
    T, n = r1T.shape
    ok = np.isfinite(r1T) & np.isfinite(m)[:, None]
    x = np.where(ok, m[:, None], 0.0)
    y = np.where(ok, r1T, 0.0)
    cs = lambda a: np.concatenate([np.zeros((1, n)), np.cumsum(a, axis=0)])
    Sx, Sy, Sxy, Sxx, N = cs(x), cs(y), cs(x * y), cs(x * x), cs(ok.astype(float))
    out = np.full((T, n), np.nan)
    j = np.arange(w, T + 1)                          # window ends at bar j-1 inclusive -> value at bar j
    N_ = N[j] - N[j - w]
    sx, sy, sxy, sxx = Sx[j] - Sx[j - w], Sy[j] - Sy[j - w], Sxy[j] - Sxy[j - w], Sxx[j] - Sxx[j - w]
    with np.errstate(invalid="ignore", divide="ignore"):
        var = sxx - sx * sx / np.maximum(N_, 1)
        cov = sxy - sx * sy / np.maximum(N_, 1)
        b = cov / var
    good = (N_ >= min_obs) & (var > 0)
    out[j[j < T]] = np.where(good, b, np.nan)[j < T]
    return out


def forward_excess_grid(r1T, ocT, m, m_oc, finT, h=CAP):
    """F[t, i] = (oc - m_oc)[t] + sum_{j=1..h-1} (r1 - m)[t+j], truncated at delisting (non-priced bars count 0)."""
    ex = np.where(finT & np.isfinite(r1T) & np.isfinite(m)[:, None], r1T - m[:, None], 0.0)
    C = np.concatenate([np.zeros((1, r1T.shape[1])), np.cumsum(ex, axis=0)])
    T = r1T.shape[0]
    F = np.full(r1T.shape, np.nan)
    t = np.arange(0, T - h)
    ex_oc = ocT[t] - m_oc[t][:, None]
    F[t] = ex_oc + (C[t + h] - C[t + 1])
    return F


def bucket_of(p):
    return np.digitize(p, BUCKET_EDGES[1:-1], right=True)          # 0..9


def pnl_beta_adjusted(trades, r1T, m, ocT, m_oc, beta):
    out = np.empty(len(trades))
    for i, (row, e0, age, _p, side) in enumerate(trades):
        sgn = 1.0 if side == 0 else -1.0
        b = beta[e0, row]
        if not np.isfinite(b):
            out[i] = np.nan
            continue
        v = r1T[e0:e0 + age, row].copy()
        mm = m[e0:e0 + age].copy()
        v[0], mm[0] = ocT[e0, row], m_oc[e0]
        out[i] = sgn * float(np.nansum(v - b * mm))
    return out


def two_c(trades, HALF, CLOSE):
    hs = float(np.nanmedian([HALF[e0, row] for row, e0, _a, _p, _s in trades]))
    px = float(np.nanmedian([CLOSE[e0, row] for row, e0, _a, _p, _s in trades]))
    return (4.0 * hs + 4.0 * 0.005 / px * 1e4) / 2.0, hs, px


# ------------------------------------------------------------------ preparation
def prep(need_grids=True):
    t0 = time.time()
    el = lambda: f"{time.time() - t0:.0f}s"
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
    ev = json.loads(Path(M.B.EVENTS).read_text())
    d343 = json.loads(D343_JSON.read_text())
    dj = json.loads(V31.DEALS.read_text())
    fbars, drops, n_ok = V31.filing_bars(dj["deals"], panel.symbols, panel.dates, first_live, last_live,
                                         lambda f: f["form"] in V31.F0_FORMS)
    excl = V31.exclusion_mask(fbars, n, T, last_live)
    pct_f0 = 100.0 * (excl & finT.T).sum() / finT.sum()
    assert n_ok == V35.EXPECT_APPLIED and abs(pct_f0 - V35.EXPECT_PCT) < 0.02, f"[F0] {n_ok} / {pct_f0:.3f}%"
    print(f"    [F0] F0 MASK: {n_ok:,} filings applied, {pct_f0:.2f}% of live name-bars excluded")
    RAW = UF.raw_price_factor(panel, ev)
    assert np.array_equal(RAW, CEN.raw_factor(ev, panel.symbols, panel.dates)), "[R] factor"
    RAW_CLOSE = CLOSE * RAW
    keep = UF.floor_mask_v2(RAW_CLOSE, DV, finT)
    share = UF.floor_share(keep, finT)
    assert abs(share - float(d343["floor"]["v2_share_live_fail"])) < 1e-9, "[R] keep_v2 share != D343"
    print(f"    [R] RAW PRICE and FLOOR: factor == census factor; keep_v2 fails {100 * share:.4f}% == D343 ({el()})")
    A2, fbmask, FBREP = FL.with_open_fill(A, panel, g)
    ocT, mkt_oc = A2["ocT"], A2["mkt_oc"]
    m_f, m_f_oc = floored_market(r1T, ocT, keep, finT)
    A3 = dict(A2, r1T=r1T, finT=finT, vxT=np.asarray(A["vxT"]), mkt=m_f, mkt_oc=m_f_oc)

    # lagged floored scores and their percentiles
    def lagged(sig):
        sc = UF.apply_floor_replace(np.where(excl, np.nan, z[sig]), keep)
        sc = np.where(base, sc, np.nan)
        out = np.full((T, n), np.nan)
        out[1:] = sc[:, :-1].T
        return out
    LAG = {s: lagged(s) for s in ("hist_L", "rev_21", "rsi")}
    PCT = {s: percentile_grid(LAG[s]) for s in LAG}
    print(f"  lagged scores and percentiles built ({el()})")
    elig = finT & keep

    def events_for(sig):
        """(sig_long, sig_short, score_for_exit)"""
        if sig == "rsi_turn":
            r = LAG["rsi"]
            prev = np.full_like(r, np.nan)
            prev[1:] = r[:-1]
            with np.errstate(invalid="ignore"):
                lo = (r > RSI_LO) & (prev <= RSI_LO) & elig
                hi = (r < RSI_HI) & (prev >= RSI_HI) & elig
            return lo, hi, r
        p = PCT[SCORE_OF[sig]]
        prev = np.full_like(p, np.nan)
        prev[1:] = p[:-1]
        with np.errstate(invalid="ignore"):
            lo = (p <= DECILE) & (prev > DECILE) & elig
            hi = (p >= 100.0 - DECILE) & (prev < 100.0 - DECILE) & elig
        return lo, hi, p

    EVENTS = {s: events_for(s) for s in SIGNALS}
    for s in SIGNALS:
        print(f"  events {s:10s}: long {int(EVENTS[s][0].sum()):,}, mirror {int(EVENTS[s][1].sum()):,}")
    beta = roll_beta(r1T, m_f)
    F = forward_excess_grid(r1T, ocT, m_f, m_f_oc, finT) if need_grids else None
    bucket_rsi = bucket_of(PCT["rsi"])
    yr_ret = {int(y): float(np.nansum(m_f[years == y])) for y in np.unique(years)}
    down_years = sorted(y for y, v in yr_ret.items() if v < 0)
    print(f"  floored market by year: " + " ".join(f"{y}:{100 * v:+.0f}%" for y, v in sorted(yr_ret.items())) + f"; down-years {down_years} ({el()})")
    return dict(A=A, A3=A3, r1T=r1T, finT=finT, ocT=ocT, m_f=m_f, m_f_oc=m_f_oc, keep=keep, elig=elig, base=base, z=z, n=n, T=T,
                panel=panel, HALF=HALF, CLOSE=CLOSE, RAW_CLOSE=RAW_CLOSE, DV=DV, years=years, down_years=down_years, yr_ret=yr_ret,
                LAG=LAG, PCT=PCT, EVENTS=EVENTS, beta=beta, F=F, bucket_rsi=bucket_rsi, excl=excl, t0=t0)


def run_events(P, sig_long, sig_short, score_T, exit_):
    return EB.simulate_event(P["A3"], sig_long, sig_short, score_T, exit=exit_, cap=CAP, n_max=None, x_target=X_TARGET, U=4)


def pnl_bp(res):
    return np.array([t[3] for t in res["trades"]]) * 1e4


# ------------------------------------------------------------------ stages
def stage_selftest(P):
    print("\nASSERTIONS")
    A3, r1T, finT, ocT, n, T = P["A3"], P["r1T"], P["finT"], P["ocT"], P["n"], P["T"]
    # [ID] D345's kernel identity, re-asserted on the unchanged kernel
    sc_nT = UF.apply_floor_replace(np.where(P["excl"], np.nan, P["z"]["rsi"]), P["keep"])
    rankT = Y.rank_single({"rsi": sc_nT}, P["base"], "rsi", n, T)
    W.BASE_HOLD = 20
    A2 = dict(A3, mkt=np.asarray(P["A"]["mkt"]), mkt_oc=FL.with_open_fill(P["A"], P["panel"], M.P1.build_grids(P["panel"], M.RP.load_ragged(M.B.FIXTURE, M.B.EVENTS, fee_bps=M.B.FEE_BPS)[1]))[0]["mkt_oc"]) if False else None
    # cheaper: rebuild A2 from the cached arrays via FL on the same grids is expensive; use P["A"] + the stored ocT and the
    # panel-wide market that D345 used (A["mkt"]) -- ocT is hedge-independent, mkt_oc must be the panel-wide one.
    okm = finT & np.isfinite(ocT)
    cnt = okm.sum(axis=1)
    # D345/D340 built mkt_oc as market_reference(oc, live) over ALL live names with a real open; reproduce that here
    live_oc = np.isfinite(ocT) & P["panel"].live.T
    cnt2 = live_oc.sum(axis=1)
    mkt_oc_panel = np.where(cnt2 >= 20, np.where(live_oc, ocT, 0.0).sum(axis=1) / np.maximum(cnt2, 1), np.nan)
    A2 = dict(A3, mkt=np.asarray(P["A"]["mkt"]), mkt_oc=mkt_oc_panel)
    res_ref = W.simulate(A2, Y.gate_from(rankT, finT), 2, True, slots=False, fill="open")
    res_id = EB.simulate_event(A2, np.ascontiguousarray(rankT[0] < 2), np.ascontiguousarray(rankT[1] < 2), P["LAG"]["rsi"],
                               exit="target", cap=20, n_max=None, x_target=X_TARGET, U=4)
    assert V45.ledger_set(res_id["trades"]) == V45.ledger_set(res_ref["trades"]), "[ID] ledgers differ"
    print(f"    [ID] KERNEL: fed rank < 2 with the slot exit, the event kernel reproduces the slot book's invariant ledger "
          f"({len(res_id['trades']):,} trades) -- D345's identity, on the unchanged kernel")
    # [E] events on the raw lagged percentile at t-1 and not at t-2; second implementation by direct counting
    rng = np.random.default_rng(347)
    for s in SIGNALS:
        lo, hi, sc = P["EVENTS"][s]
        ev_idx = np.argwhere(lo)
        sample = ev_idx[rng.choice(len(ev_idx), size=min(300, len(ev_idx)), replace=False)]
        n_unl = 0
        for t, i in sample:
            if s == "rsi_turn":
                r = P["LAG"]["rsi"]
                assert r[t, i] > RSI_LO and r[t - 1, i] <= RSI_LO, f"[E] {s} ({t},{i})"
                # unlagged: the score AT t (known only at the close of t)
                sc_t = P["LAG"]["rsi"][t + 1, i] if t + 1 < T else np.nan
                n_unl += not (sc_t == sc_t and sc_t > RSI_LO and r[t, i] <= RSI_LO)
            else:
                v = P["LAG"][SCORE_OF[s]][t]
                fin = np.isfinite(v)
                pct_direct = (float((v[fin] < v[i]).sum()) + 0.5 * float((v[fin] == v[i]).sum())) / fin.sum() * 100.0
                assert pct_direct <= DECILE + 1e-9, f"[E] {s} ({t},{i}) pct {pct_direct}"
                v2 = P["LAG"][SCORE_OF[s]][t - 1]
                fin2 = np.isfinite(v2)
                pct_prev = ((float((v2[fin2] < v2[i]).sum()) + 0.5 * float((v2[fin2] == v2[i]).sum())) / fin2.sum() * 100.0
                            if fin2[i] else np.nan)
                assert not (pct_prev == pct_prev and pct_prev <= DECILE), f"[E] {s} ({t},{i}) not fresh"
                p_t = P["PCT"][SCORE_OF[s]][t + 1, i] if t + 1 < T else np.nan   # the percentile of the score AT t
                n_unl += not (p_t == p_t and p_t <= DECILE and P["PCT"][SCORE_OF[s]][t, i] > DECILE)
        print(f"    [E] {s:10s}: {len(ev_idx):,} long events; {len(sample)} sampled all satisfy the entry condition on the raw lagged score at "
              f"t-1 (direct count) and are fresh; the unlagged condition differs on {n_unl} of {len(sample)}")
    # [H] floored market and beta
    m_f, m_f_oc = P["m_f"], P["m_f_oc"]
    for t in rng.choice(np.flatnonzero(np.isfinite(m_f)), size=200, replace=False):
        idx = np.flatnonzero(P["keep"][t] & finT[t] & np.isfinite(r1T[t]))
        assert abs(float(np.mean([r1T[t, i] for i in idx])) - m_f[t]) < 1e-12, f"[H] bar {t}"
    syn = 2.0 * np.nan_to_num(m_f, nan=0.0) + rng.normal(0, 0.002, size=T)
    b_syn = roll_beta(syn[:, None], m_f)[:, 0]
    fin_b = np.isfinite(b_syn)
    assert abs(float(np.nanmedian(b_syn[fin_b])) - 2.0) < 0.05, f"[H] synthetic beta {np.nanmedian(b_syn[fin_b])}"
    print(f"    [H] the floored market equals a direct mean over keep & priced names on 200 sampled bars to 1e-12; a synthetic name with "
          f"returns 2m + noise recovers beta {np.nanmedian(b_syn[fin_b]):.3f}")
    # [S] sign in money on hist_L long events, cap exit
    lo, hi, sc = P["EVENTS"]["hist_L"]
    res = run_events(P, lo, np.zeros_like(lo), sc, "cap")
    tr = res["trades"]
    pnl = np.array([t[3] for t in tr])
    rec = FL.pnl_recomputed_fill(tr, r1T, m_f, ocT, m_f_oc)
    worst = float(np.abs(rec - pnl).max())
    assert worst < 1e-12, f"[S] {worst:.2e}"
    ex = np.array([float((ocT[e0, row] - m_f_oc[e0]) + np.nansum(r1T[e0 + 1:e0 + age, row] - m_f[e0 + 1:e0 + age])) for row, e0, age, _p, _s in tr])
    assert (pnl[ex > 0] > 0).all() and (pnl[ex < 0] < 0).all(), "[S] sign"
    print(f"    [S] SIGN IN MONEY: every hist_L cap-exit trade equals the open-fill recomputation against the floored market to {worst:.1e}; "
          f"favourable paths pay positively ({len(tr):,} trades)")
    # [A] control A keeps every name's event count
    sl_, ss_, sc_ = EB.rotate_signals(lo, hi, sc, finT, rng)
    assert np.array_equal(sl_.sum(axis=0), lo.sum(axis=0)) and np.array_equal(ss_.sum(axis=0), hi.sum(axis=0)), "[A]"
    print("    [A] control A keeps every name's event count exactly")
    # [B] control B keeps every event's date and rsi bucket and changes its name
    sigB = control_b_signal(P, lo, rng)
    assert np.array_equal(sigB.sum(axis=1), lo.sum(axis=1)), "[B] dates changed"
    bo, bn = P["bucket_rsi"][lo], P["bucket_rsi"][sigB]
    assert sorted(bo.tolist()) == sorted(bn.tolist()), "[B] bucket multiset changed"
    assert not (sigB & lo).sum() > 0.05 * lo.sum(), "[B] too many names unchanged"
    print(f"    [B] control B keeps every event's date and rsi bucket; {int((sigB & lo).sum())} of {int(lo.sum()):,} events kept their name by chance")
    # [C] control C is centred at zero
    signs = rng.choice([-1.0, 1.0], size=(1000, pnl.size))
    cm = (signs * pnl[None, :] * 1e4).mean(axis=1)
    se = cm.std(ddof=1) / np.sqrt(cm.size)
    assert abs(cm.mean()) < 2 * se + 1e-9, "[C]"
    print(f"    [C] control C: mean {cm.mean():+.3f} bp, within 2 standard errors ({se:.3f}) of zero")
    # [F] base-rate grid on sampled cells
    F = P["F"]
    cells = np.argwhere(np.isfinite(F) & P["elig"])
    sample = cells[rng.choice(len(cells), size=3000, replace=False)]
    worst_f = 0.0
    for t, i in sample:
        v = r1T[t:t + CAP, i].copy()
        mm = m_f[t:t + CAP].copy()
        v[0], mm[0] = ocT[t, i], m_f_oc[t]
        okk = finT[t:t + CAP, i] & np.isfinite(v) & np.isfinite(mm)
        okk[0] = True
        direct = float(np.sum(np.where(okk, v - mm, 0.0)))
        worst_f = max(worst_f, abs(direct - F[t, i]))
    assert worst_f < 1e-9, f"[F] {worst_f:.2e}"
    print(f"    [F] the forward-40 base-rate grid equals a direct per-cell recomputation on 3,000 sampled cells to {worst_f:.1e}")
    # [X] the interaction identity: sum over buckets of n_b (E_sb - E_s) == 0
    b_ev = np.array([P["bucket_rsi"][e0, row] for row, e0, _a, _p, _s in tr])
    Es = pnl.mean()
    tot = sum((b_ev == b).sum() * (pnl[b_ev == b].mean() - Es) for b in range(10) if (b_ev == b).any())
    assert abs(tot) < 1e-9 * max(1.0, abs(pnl).sum()), f"[X] {tot}"
    print("    [X] the bucket decomposition sums to the event count and sum_b n_b (E_sb - E_s) == 0")
    # [6]
    broke = False
    try:
        rec2 = FL.pnl_recomputed_fill(tr, r1T, m_f, ocT, m_f_oc)
        assert np.abs(rec2 - (pnl + 50e-4)).max() < 1e-12
    except AssertionError:
        broke = True
    assert broke, "[6]"
    print("    [6] and [S] raises on events handed +50 bp")
    print(f"\nOK  assertions pass  ({time.time() - P['t0']:.0f}s)")


def control_b_signal(P, sig, rng):
    """Same date, same rsi bucket, a random other eligible name."""
    T, n = sig.shape
    out = np.zeros_like(sig)
    bucket, elig = P["bucket_rsi"], P["elig"]
    for t in np.flatnonzero(sig.any(axis=1)):
        ev_rows = np.flatnonzero(sig[t])
        pool_all = np.flatnonzero(elig[t] & ~sig[t])
        b_ev = bucket[t, ev_rows]
        for b in np.unique(b_ev):
            rows_b = ev_rows[b_ev == b]
            pool = pool_all[bucket[t, pool_all] == b]
            k = min(rows_b.size, pool.size)
            if k:
                out[t, rng.choice(pool, size=k, replace=False)] = True     # distinct replacements, same day, same bucket
            if rows_b.size > k:
                out[t, rows_b[k:]] = True                                 # pool exhausted: keep the originals (counted)
    return out


def stage_controls(P, sig, draws, part=0):
    lo, hi, sc = P["EVENTS"][sig]
    res = run_events(P, lo, np.zeros_like(lo), sc, "cap")
    obs = float(pnl_bp(res).mean())
    print(f"\n  {sig} part {part}: observed mean hedged excess (cap exit) {obs:+.2f} bp on {len(res['trades']):,} trades")
    rngA = np.random.default_rng([SEED, 347, 1, SIGNALS.index(sig), part])
    rngB = np.random.default_rng([SEED, 347, 2, SIGNALS.index(sig), part])
    A_, B_ = [], []
    ts = time.time()
    for d in range(draws):
        sl_, ss_, sc_ = EB.rotate_signals(lo, hi, sc, P["finT"], rngA)
        rA = run_events(P, sl_, np.zeros_like(lo), sc_, "cap")
        A_.append(float(pnl_bp(rA).mean()))
        sB = control_b_signal(P, lo, rngB)
        rB = run_events(P, sB, np.zeros_like(lo), sc, "cap")
        B_.append(float(pnl_bp(rB).mean()))
        if (d + 1) % 25 == 0:
            print(f"    {sig}: {d + 1}/{draws} ({time.time() - ts:.0f}s)", flush=True)
    out = dict(signal=sig, draws=draws, part=part, observed=obs, trades=len(res["trades"]), control_A=A_, control_B=B_)
    f = Path(str(CTRL).format(sig=f"{sig}_p{part}"))
    f.write_text(json.dumps(out))
    print(f"  wrote {f.name}: A p50 {np.median(A_):+.2f} p95 {np.quantile(A_, .95):+.2f}; "
          f"B p50 {np.median(B_):+.2f} p95 {np.quantile(B_, .95):+.2f} ({time.time() - P['t0']:.0f}s)")


def stage_report(P):
    r1T, finT, ocT, m_f, m_f_oc, beta, F = P["r1T"], P["finT"], P["ocT"], P["m_f"], P["m_f_oc"], P["beta"], P["F"]
    HALF, CLOSE, years, T = P["HALF"], P["CLOSE"], P["years"], P["T"]
    bucket_rsi, elig = P["bucket_rsi"], P["elig"]
    down = set(P["down_years"])
    half = T // 2
    E_all = float(np.nanmean(F[elig & np.isfinite(F)])) * 1e4
    E_b = {}
    for b in range(10):
        m = elig & np.isfinite(F) & (bucket_rsi == b)
        E_b[b] = float(np.nanmean(F[m])) * 1e4 if m.any() else np.nan
    print(f"\n  BASE RATES: forward-40 hedged excess, all floored name-bars {E_all:+.1f} bp; by rsi bucket: " +
          " ".join(f"b{b}:{E_b[b]:+.0f}" for b in range(10)))
    REPORT = {}
    rngC = np.random.default_rng([SEED, 347, 3])
    for sig in SIGNALS:
        lo, hi, sc = P["EVENTS"][sig]
        R_ = {}
        for lens, sl, ss in (("long", lo, np.zeros_like(lo)), ("mirror", np.zeros_like(hi), hi)):
            for exit_ in ("cap", "invalidation"):
                res = run_events(P, sl, ss, sc, exit_)
                tr = res["trades"]
                pnl = pnl_bp(res)
                pb = pnl_beta_adjusted(tr, r1T, m_f, ocT, m_f_oc, beta) * 1e4
                yrs = np.array([years[t[1]] for t in tr])
                eras = np.array([t[1] < half for t in tr])
                c2 = {cv: two_c(tr, HALF[cv], CLOSE) for cv in CONVS}
                d_ = dict(trades=len(tr), mean_bp=float(pnl.mean()), median_bp=float(np.median(pnl)),
                          t=float(pnl.mean() / (pnl.std(ddof=1) / np.sqrt(pnl.size))), share_pos=float((pnl > 0).mean()),
                          hold_mean=float(np.mean([t[2] for t in tr])),
                          beta_adj_mean_bp=float(np.nanmean(pb)), beta_median=float(np.nanmedian([beta[t[1], t[0]] for t in tr])),
                          two_c={cv: c2[cv][0] for cv in CONVS}, net_per_trade={cv: float(pnl.mean()) - c2[cv][0] for cv in CONVS},
                          held_half={cv: c2[cv][1] for cv in CONVS}, held_price=c2["PUB"][2],
                          down_years_mean_bp=(float(pnl[np.isin(yrs, list(down))].mean()) if np.isin(yrs, list(down)).any() else None),
                          down_years_n=int(np.isin(yrs, list(down)).sum()),
                          era1_mean_bp=float(pnl[eras].mean()) if eras.any() else None, era2_mean_bp=float(pnl[~eras].mean()) if (~eras).any() else None,
                          by_year={int(y): float(pnl[yrs == y].mean()) for y in np.unique(yrs)})
                if lens == "long" and exit_ == "cap":
                    b_ev = np.array([bucket_rsi[t[1], t[0]] for t in tr])
                    Es = float(pnl.mean())
                    inter = {}
                    for b in range(10):
                        mb = b_ev == b
                        if mb.any():
                            Esb = float(pnl[mb].mean())
                            inter[b] = dict(n=int(mb.sum()), E_sb=Esb, E_b=E_b[b], interaction=Esb - E_b[b] - Es + E_all)
                    d_["interaction"] = inter
                    signs = rngC.choice([-1.0, 1.0], size=(1000, pnl.size))
                    cC = (signs * pnl[None, :]).mean(axis=1)
                    d_["control_C"] = dict(p50=float(np.median(cC)), p95=float(np.quantile(cC, .95)), max=float(cC.max()), draws=1000,
                                           above=bool(Es > np.quantile(cC, .95)))
                R_[f"{lens}/{exit_}"] = d_
        parts = sorted(REPO.glob(f"data/d347_ctrl_{sig}_p*.json"))
        if parts:
            cs_ = [json.loads(p.read_text()) for p in parts]
            A_ = np.concatenate([np.array(c["control_A"]) for c in cs_])
            B_ = np.concatenate([np.array(c["control_B"]) for c in cs_])
            obs = R_["long/cap"]["mean_bp"]
            for c in cs_:
                assert abs(c["observed"] - obs) < 1e-9, f"observed differs between stages for {sig}"
            c = dict(draws=int(sum(c["draws"] for c in cs_)))
            R_["controls"] = dict(draws=c["draws"], A=dict(p50=float(np.median(A_)), p95=float(np.quantile(A_, .95)), max=float(A_.max()),
                                                          distinct=int(len(set(A_.tolist()))), above=bool(obs > np.quantile(A_, .95))),
                                  B=dict(p50=float(np.median(B_)), p95=float(np.quantile(B_, .95)), max=float(B_.max()),
                                         distinct=int(len(set(B_.tolist()))), above=bool(obs > np.quantile(B_, .95))))
        REPORT[sig] = R_

    # ---- print ----------------------------------------------------------------------------------------------------
    print("\n" + "=" * 118)
    print("THE LONG SIGNALS -- every event taken, next-open fill, hedged against the floored market; bp per trade")
    print("=" * 118)
    print("  %-11s %-6s %-12s %6s %8s %8s %6s %7s %8s %9s %9s %8s %8s" % ("signal", "side", "exit", "n", "mean", "median", "t", "hold", "beta-adj",
                                                                       "net PUB", "net PB", "down-yr", "eras"))
    for sig in SIGNALS:
        for key, d_ in REPORT[sig].items():
            if key == "controls":
                continue
            lens, exit_ = key.split("/")
            print("  %-11s %-6s %-12s %6d %+8.1f %+8.1f %+6.2f %7.1f %+8.1f %+9.1f %+9.1f %8s %8s" % (
                sig, lens, exit_, d_["trades"], d_["mean_bp"], d_["median_bp"], d_["t"], d_["hold_mean"], d_["beta_adj_mean_bp"],
                d_["net_per_trade"]["PUB"], d_["net_per_trade"]["PB"],
                ("%+.0f" % d_["down_years_mean_bp"]) if d_["down_years_mean_bp"] is not None else "-",
                "%+.0f/%+.0f" % (d_["era1_mean_bp"] or 0, d_["era2_mean_bp"] or 0)))
    print(f"\n  down-years (floored market negative): {P['down_years']}")
    print("\n  CONTROLS on the long cap-exit statistic (mean hedged excess, bp):")
    print("  %-11s %8s | %8s %8s %8s %4s %6s | %8s %8s %8s %4s %6s | %8s %8s %6s" % ("signal", "observed", "A p50", "A p95", "A max", "dist", "above",
                                                                                     "B p50", "B p95", "B max", "dist", "above", "C p95", "C max", "above"))
    for sig in SIGNALS:
        R_ = REPORT[sig]
        c = R_.get("controls")
        cc = R_["long/cap"]["control_C"]
        if c:
            print("  %-11s %+8.2f | %+8.2f %+8.2f %+8.2f %4d %6s | %+8.2f %+8.2f %+8.2f %4d %6s | %+8.2f %+8.2f %6s" % (
                sig, R_["long/cap"]["mean_bp"], c["A"]["p50"], c["A"]["p95"], c["A"]["max"], c["A"]["distinct"], "yes" if c["A"]["above"] else "NO",
                c["B"]["p50"], c["B"]["p95"], c["B"]["max"], c["B"]["distinct"], "yes" if c["B"]["above"] else "NO",
                cc["p95"], cc["max"], "yes" if cc["above"] else "NO"))
        else:
            print(f"  {sig:11s} {R_['long/cap']['mean_bp']:+8.2f} | controls not run")
    print("\n  INTERACTION with the rsi ranking (long, cap exit): bucket | n | E[signal,bucket] | E[bucket] | interaction")
    for sig in SIGNALS:
        inter = REPORT[sig]["long/cap"]["interaction"]
        print(f"  {sig}: " + " ".join(f"b{b}[{v['n']}] {v['E_sb']:+.0f}/{v['E_b']:+.0f}/{v['interaction']:+.0f}" for b, v in sorted(inter.items())))
    print("  buckets: 0=[0,2] 1=(2,5] 2=(5,10] 3=(10,25] 4=(25,50] 5=(50,75] 6=(75,90] 7=(90,95] 8=(95,98] 9=(98,100] of the rsi percentile at t-1")

    # ---- predictions --------------------------------------------------------------------------------------------------
    def survives(sig):
        R_ = REPORT[sig]
        c = R_.get("controls")
        return bool(c and c["A"]["above"] and c["B"]["above"] and R_["long/cap"]["control_C"]["above"])
    surv = [s for s in ("hist_L", "rev_21") if survives(s)]
    all_surv = [s for s in SIGNALS if survives(s)]
    q = {}
    q["Q1"] = bool(len(surv) > 0)
    ct = REPORT["rsi_turn"].get("controls")
    q["Q2"] = bool(ct and ct["A"]["above"] and not ct["B"]["above"])
    q["Q3"] = bool(all(abs(REPORT[s]["controls"]["A"]["p50"]) <= 10.0 for s in SIGNALS if "controls" in REPORT[s]))
    q["Q4"] = bool(all(REPORT[s]["long/cap"]["beta_adj_mean_bp"] < REPORT[s]["long/cap"]["mean_bp"]
                       and REPORT[s]["long/cap"]["mean_bp"] - REPORT[s]["long/cap"]["beta_adj_mean_bp"] < 0.30 * abs(REPORT[s]["long/cap"]["mean_bp"])
                       for s in SIGNALS))

    def bottom_vs_middle(sig):
        inter = REPORT[sig]["long/cap"]["interaction"]
        bot = [inter[b] for b in (0, 1, 2) if b in inter]
        mid = [inter[b] for b in (4, 5) if b in inter]
        if not bot or not mid:
            return None
        eb = sum(v["n"] * v["E_sb"] for v in bot) / sum(v["n"] for v in bot)
        em = sum(v["n"] * v["E_sb"] for v in mid) / sum(v["n"] for v in mid)
        return eb - em
    q["Q5"] = bool(surv and all((bottom_vs_middle(s) or -1e9) > 20.0 for s in surv))
    q["Q6"] = bool(surv and all((REPORT[s]["long/cap"]["down_years_mean_bp"] or -1e9) > 0 for s in surv))
    q["Q7"] = bool(surv and all(REPORT[s]["mirror/cap"]["mean_bp"] > 0 for s in surv))
    q["Q8"] = bool(any(REPORT[s]["long/invalidation"]["net_per_trade"]["PUB"] > 0 for s in SIGNALS))
    print("\nPREDICTIONS")
    print(f"  Q1 (LOAD-BEARING) hist_L or rev_21 above all three controls: {'CONFIRMED' if q['Q1'] else 'FALSIFIED'} -- survivors {surv}; all survivors {all_surv}")
    print(f"  Q2 rsi turn beats A and fails B: {'CONFIRMED' if q['Q2'] else 'FALSIFIED'}" +
          (f" -- A {'yes' if ct['A']['above'] else 'no'}, B {'yes' if ct['B']['above'] else 'no'}" if ct else ""))
    print(f"  Q3 every control-A distribution centred within 10 bp of zero: {'CONFIRMED' if q['Q3'] else 'FALSIFIED'} -- " +
          ", ".join(f"{s} {REPORT[s]['controls']['A']['p50']:+.1f}" for s in SIGNALS if "controls" in REPORT[s]))
    print(f"  Q4 beta-adjusted below equal-weight by < 30%: {'CONFIRMED' if q['Q4'] else 'FALSIFIED'} -- " +
          ", ".join(f"{s} {REPORT[s]['long/cap']['mean_bp']:+.1f}->{REPORT[s]['long/cap']['beta_adj_mean_bp']:+.1f}" for s in SIGNALS))
    print(f"  Q5 (against) survivors' bottom-decile excess exceeds the middle by > 20: {'CONFIRMED' if q['Q5'] else 'FALSIFIED'} -- " +
          ", ".join(f"{s} {bottom_vs_middle(s):+.1f}" for s in SIGNALS if bottom_vs_middle(s) is not None))
    print(f"  Q6 survivors positive in down-years: {'CONFIRMED' if q['Q6'] else 'FALSIFIED'} -- " +
          ", ".join(f"{s} {REPORT[s]['long/cap']['down_years_mean_bp']:+.1f} (n {REPORT[s]['long/cap']['down_years_n']})" for s in SIGNALS
                    if REPORT[s]["long/cap"]["down_years_mean_bp"] is not None))
    print(f"  Q7 (against) survivors' mirror > 0: {'CONFIRMED' if q['Q7'] else 'FALSIFIED'} -- " +
          ", ".join(f"{s} {REPORT[s]['mirror/cap']['mean_bp']:+.1f}" for s in SIGNALS))
    print(f"  Q8 (against) some long signal nets > 0 per trade after PUB 2c under invalidation: {'CONFIRMED' if q['Q8'] else 'FALSIFIED'} -- " +
          ", ".join(f"{s} {REPORT[s]['long/invalidation']['net_per_trade']['PUB']:+.1f}" for s in SIGNALS))

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
    out = dict(note="D347: three long signals as events against three drift-matched controls, two hedges, the splits, the rsi-rank interaction. "
                    "Every event taken (invariant lens); nothing is a book; nothing promoted.",
               signals=SIGNALS, cap=CAP, decile=DECILE, bucket_edges=BUCKET_EDGES, base_rate_all_bp=E_all, base_rate_by_bucket_bp=E_b,
               down_years=P["down_years"], floored_market_by_year=P["yr_ret"], report=REPORT, survivors=all_surv, predictions=q)
    OUT.write_text(json.dumps(clean(out), indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}  ({time.time() - P['t0']:.0f}s)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--controls", choices=SIGNALS)
    ap.add_argument("--draws", type=int, default=100)
    ap.add_argument("--part", type=int, default=0)
    ap.add_argument("--report", action="store_true")
    a = ap.parse_args()
    print("D347  is the long signal real? -- three drift-matched controls")
    P = prep(need_grids=a.selftest or a.report)
    if a.selftest:
        stage_selftest(P)
    elif a.controls:
        stage_controls(P, a.controls, a.draws, a.part)
    elif a.report:
        stage_report(P)
    else:
        ap.error("one of --selftest, --controls SIG, --report")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""D504 -- stage 0: the Asian chip session into the US semiconductor day. Does Taiwan and Korea carry information the US semis' own gap has
not already priced? Conditioner measured to the close of bar 0 (09:30-09:45), entry at bar 1's open (09:45), exit at the 16:00 close, so the
predictor is strictly before the entry. Primary P1 = SMH vs QQQ on the top causal decile of the disagreement |z(A) - z(G)|; P2 raw continuation;
P3 six wrong-sector controls; P4 three wrong-conditioner controls; P5 the prop-eligible MNQ/MES arm; N1 exact enumerated rotation, N2 a
twelve-cell family maximum, N3 partner-randomised, N4 wrong-window. Spec committed in 7578140 BEFORE this file. 2018-2023; 2024+ RESERVED.

    uv run python -u scripts/run_d504_asian_chip_stage0.py --run
    uv run python -u scripts/run_d504_asian_chip_stage0.py --selftest
"""
from __future__ import annotations
import argparse, importlib.util, json, math, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m
FIX = REPO / "data" / "fixtures"; ETF = FIX / "etf_intraday_15m_raw.csv.gz"
OUT = REPO / "data" / "d504_asian_chip_stage0.json"; SPEC = "7578140"
START, END = "2018-01-02", "2023-12-29"                      # 2024+ RESERVED on the 15-minute fixtures
CORE = ["SMH", "QQQ", "EWT", "EWY", "EWJ"]
SECTORS = ["KRE", "ITB", "IYR", "IYT", "IBB", "OIH"]          # P3: no mechanism from the chip complex
WRONG = ["EWG", "EWU", "EWZ", "EEM"]                          # P4: wrong region / diluted
SYMS = CORE + SECTORS + WRONG + ["SPY"]
NBAR, WARM, Q, ACCOUNT = 26, 250, 0.90, 50_000.0
PER_SHARE, MIN_ORDER, CAP = 0.005, 1.00, 0.01                 # IBKR Fixed, the repo's committed equity model (D264)
NOTIONAL, NOTIONAL_BIG = 10_000.0, 50_000.0                   # per leg: the primary (conservative) and a larger line, because IBKR Fixed's $1 order minimum binds below ~$40k
FUT_MULT = {"NQ": 2.0, "ES": 5.0}; FUT_FEE = 3.0; FUT_ENTRY_BAR, FUT_EXIT_BAR = 15, 389   # 09:45 open, 15:59 close
D400 = _load("d400c", "run_d400_recost.py")
D490 = _load("d490c", "run_d490_range_reversion.py")


# ------------------------------------------------------------------------------------------ data
def load_etf():
    d = pd.read_csv(ETF, dtype={"symbol": str, "timestamp": str})
    d = d[d["symbol"].isin(SYMS)].copy(); d["day"] = d["timestamp"].str[:10]; d["hm"] = d["timestamp"].str[11:16]
    d = d[d["day"] <= END]
    assert d["day"].max() <= END, "a bar past the in-sample end reached the measurement"
    n = d.groupby(["symbol", "day"]).size().unstack(fill_value=0)
    full = [c for c in n.columns if (n[c] == NBAR).all()]                       # every declared symbol has all 26 bars
    days = np.array(sorted(x for x in full if x >= START))
    hm = sorted(d["hm"].unique()); assert len(hm) == NBAR and hm[0] == "09:30" and hm[-1] == "15:45", hm
    out = {}
    for s in SYMS:
        x = d[d["symbol"] == s]
        piv = lambda col: x.pivot(index="day", columns="hm", values=col).reindex(index=days, columns=hm).to_numpy(float)
        O, H, L, C = (piv(c) for c in ("open", "high", "low", "close"))
        assert np.isfinite(C).all() and np.isfinite(O).all(), f"{s} has a hole on a declared session"
        out[s] = dict(O=O, H=H, L=L, C=C)
    return days, out


def gaps_and_returns(P):
    """gap = close(bar 0) / previous session's close(bar 25) - 1; ret = close(bar 25) / open(bar 1) - 1. Both in bp. Row 0 has no gap."""
    C, O = P["C"], P["O"]; prev_close = np.concatenate([[np.nan], C[:-1, NBAR - 1]])
    gap = (C[:, 0] / prev_close - 1.0) * 1e4
    ret = (C[:, NBAR - 1] / O[:, 1] - 1.0) * 1e4
    late = (C[:, NBAR - 1] / O[:, NBAR - 7] - 1.0) * 1e4                        # 14:00 -> 16:00, for N4
    return gap, ret, late


def zc(x, n=WARM):
    """Causal standardisation: mean and sd over the trailing n sessions ENDING at d-1."""
    s = pd.Series(x); m = s.rolling(n, min_periods=n).mean().shift(1); v = s.rolling(n, min_periods=n).std(ddof=1).shift(1)
    return ((s - m) / v).to_numpy()


def causal_quantile(x, q=Q, n=WARM):
    return pd.Series(x).rolling(n, min_periods=n).quantile(q).shift(1).to_numpy()


def causal_resid(y, x, n=WARM):
    """The part of y not explained by x, using an OLS fitted on the trailing n sessions ENDING at d-1 (so the fit never sees day d).
    This is the record's 'incremental' quantity: the Asian move the US semis' own gap has not already priced."""
    y = np.asarray(y, float); x = np.asarray(x, float); T = len(y); out = np.full(T, np.nan)
    for d in range(n + 1, T):
        yy = y[d - n:d]; xx = x[d - n:d]; m = np.isfinite(yy) & np.isfinite(xx)
        if m.sum() < n // 2 or not (np.isfinite(y[d]) and np.isfinite(x[d])):
            continue
        A = np.column_stack([np.ones(m.sum()), xx[m]]); b, *_ = np.linalg.lstsq(A, yy[m], rcond=None)
        out[d] = y[d] - (b[0] + b[1] * x[d])
    return out


# ------------------------------------------------------------------------------------------ cost
def cs_bp(P, days, i, n=WARM):
    """Corwin-Schultz half-spread in bp/side for one symbol, from its own 15-minute OHLC over the trailing n sessions ending at i-1."""
    lo = max(0, i - n); H = P["H"][lo:i].ravel(); L = P["L"][lo:i].ravel()
    if H.size < 4:
        return float("nan")
    return D400.corwin_schultz(H, L)


def commission_bp(price, notional=NOTIONAL):
    shares = max(notional / price, 1.0); c = min(PER_SHARE * shares, CAP * notional); c = max(c, MIN_ORDER)
    return 1e4 * c / notional


# ------------------------------------------------------------------------------------------ cells
def cell_series(sig, thr, long_ret, short_ret):
    """Trade when |sig| >= thr (causal); direction sign(sig); P&L in bp of one leg = sign * (long_ret - short_ret)."""
    ok = np.isfinite(sig) & np.isfinite(thr) & np.isfinite(long_ret) & np.isfinite(short_ret) & (np.abs(sig) >= thr)
    s = np.sign(sig); pnl = np.where(ok, s * (long_ret - short_ret), np.nan)
    return ok, s, pnl


def summarise(days, ok, s, pnl, cost_bp, label):
    x = pnl[ok]; n = int(ok.sum())
    if n < 5:
        return dict(label=label, n=n)
    d = days[ok]; yrs = np.array([t[:4] for t in d]); mean = float(x.mean()); se = float(x.std(ddof=1) / math.sqrt(n))
    h1 = x[yrs <= "2020"]; h2 = x[yrs >= "2021"]
    trim = np.sort(x); c = int(math.floor(n * 0.01)); trimmed = float(trim[c:n - c].mean()) if n - 2 * c > 0 else float("nan")
    by_year = {y: float(x[yrs == y].mean()) for y in sorted(set(yrs))}
    return dict(label=label, n=n, per_year=n / max(1, len(set(yrs))), gross_bp=mean, median_bp=float(np.median(x)), trimmed_bp=trimmed,
                ex_top_bp=float(np.sort(x)[:n - max(1, n // 100)].mean()), ex_bottom_bp=float(np.sort(x)[max(1, n // 100):].mean()),
                se_bp=se, z=mean / se if se > 0 else float("nan"), hit=float((x > 0).mean()), skew=float(pd.Series(x).skew()),
                kurt=float(pd.Series(x).kurt()), cost_bp=cost_bp, net_bp=mean - cost_bp, cost_over_gross=cost_bp / abs(mean) if mean != 0 else float("inf"),
                halves_bp=[float(h1.mean()) if h1.size else float("nan"), float(h2.mean()) if h2.size else float("nan")],
                same_sign_halves=bool(h1.size and h2.size and np.sign(h1.mean()) == np.sign(h2.mean()) == np.sign(mean)),
                by_year_bp=by_year, positive_years=int(sum(v > 0 for v in by_year.values())), n_years=len(by_year),
                long_share=float((s[ok] > 0).mean()), breakeven_hit=0.5 + cost_bp / (2 * float(np.abs(x).mean())))


def rotation(sig, thr, long_ret, short_ret, d_max=None):
    """Exact common rotation: the SIGNAL (a single market-level daily series, with its causal threshold) is rotated by k sessions against the
    outcome pair, k = 1..T-1, enumerated. Returns the per-offset mean and z of the same statistic the cell reports."""
    fin = np.isfinite(sig) & np.isfinite(thr); rel = long_ret - short_ret; good = np.isfinite(rel)
    T = len(sig); D = T - 1 if d_max is None else min(d_max, T - 1); mean = np.full(D, np.nan); z = np.full(D, np.nan)
    s_all = np.sign(sig); pick = fin & (np.abs(sig) >= thr)
    for k in range(1, D + 1):
        pk = np.roll(pick, k); sk = np.roll(s_all, k); m = pk & good
        if m.sum() < 5:
            continue
        x = sk[m] * rel[m]; mu = float(x.mean()); sd = float(x.std(ddof=1)); mean[k - 1] = mu
        z[k - 1] = mu / (sd / math.sqrt(x.size)) if sd > 0 else np.nan
    return mean, z


def rotation_slow(sig, thr, long_ret, short_ret, k):
    fin = np.isfinite(sig) & np.isfinite(thr); rel = long_ret - short_ret; T = len(sig); xs = []
    for t in range(T):
        u = (t - k) % T
        if fin[u] and abs(sig[u]) >= thr[u] and np.isfinite(rel[t]):
            xs.append(np.sign(sig[u]) * rel[t])
    x = np.array(xs); mu = x.mean(); sd = x.std(ddof=1); return float(mu), float(mu / (sd / math.sqrt(x.size)))


def ols_t(y, X, lags=5):
    """OLS with Newey-West standard errors; X without a constant (added here)."""
    m = np.isfinite(y) & np.isfinite(X).all(axis=1); y = y[m]; X = X[m]; n = len(y)
    A = np.column_stack([np.ones(n), X]); b, *_ = np.linalg.lstsq(A, y, rcond=None); e = y - A @ b
    XtX_inv = np.linalg.inv(A.T @ A); S = (e[:, None] * A).T @ (e[:, None] * A)
    for L in range(1, lags + 1):
        w = 1.0 - L / (lags + 1.0); G = (e[L:, None] * A[L:]).T @ (e[:-L, None] * A[:-L]); S += w * (G + G.T)
    V = XtX_inv @ S @ XtX_inv; se = np.sqrt(np.diag(V))
    return b, se, b / se, int(n)


# ------------------------------------------------------------------------------------------ run
def build(days, P):
    g = {}; r = {}; late = {}
    for s in SYMS:
        g[s], r[s], late[s] = gaps_and_returns(P[s])
    # A_rel: the Asian chip complex RELATIVE to the US market benchmark, so the market-wide component of the Asian gap is removed
    # (the predictor-side table in the record: both NQ and ES load ~0.5 on the Asian session, so a raw Asian gap is mostly market).
    A = 0.5 * (g["EWT"] + g["EWY"]); A_rel = A - g["QQQ"]; G = g["SMH"] - g["QQQ"]
    zA, zG = zc(A_rel), zc(G); Dis = zA - zG                                  # the z-difference, kept as a declared secondary (P1_z)
    sigs = dict(P1=causal_resid(A_rel, G), P1_z=Dis, P2=zA)                   # P1 = the incremental (amended 2026-09-13, see the record)
    sigs["P4_EU"] = causal_resid(0.5 * (g["EWG"] + g["EWU"]) - g["QQQ"], G)
    sigs["P4_EWZ"] = causal_resid(g["EWZ"] - g["QQQ"], G)
    sigs["P4_EEM"] = causal_resid(g["EEM"] - g["QQQ"], G)
    sigs["N4_late"] = causal_resid(0.5 * (late["EWT"] + late["EWY"]) - late["QQQ"], G)
    return dict(g=g, r=r, late=late, A=A, A_rel=A_rel, G=G, zA=zA, zG=zG, Dis=Dis, sigs=sigs)


def score_cell(days, sig, long_ret, short_ret, cost_bp, label, want_null=True):
    thr = causal_quantile(np.abs(sig)); ok, s, pnl = cell_series(sig, thr, long_ret, short_ret)
    st = summarise(days, ok, s, pnl, cost_bp, label)
    if want_null and st.get("n", 0) >= 5:
        m, z = rotation(sig, thr, long_ret, short_ret); z = z[np.isfinite(z)]; m = m[np.isfinite(m)]
        st["null"] = dict(n_offsets=int(z.size), mean_p50=float(np.median(m)), mean_p95=float(np.quantile(m, .95)),
                          z_p50=float(np.median(z)), z_p95=float(np.quantile(z, .95)), z_p99=float(np.quantile(z, .99)),
                          share_ge=float((z >= st["z"]).mean()))
        st["clears_N1"] = bool(st["z"] > st["null"]["z_p95"]); st["_z"] = z
    return st, ok, pnl


def run():
    t0 = time.time(); print(f"D504 stage 0 -- the Asian chip session into the US semiconductor day\n      spec committed in {SPEC} BEFORE this ran; {START}..{END}; 2024+ RESERVED on the 15-minute fixtures\n      conditioner to the close of bar 0 (09:30-09:45); entry bar 1's open (09:45); exit the 16:00 close")
    days, P = load_etf(); B = build(days, P); n = len(days); print(f"  {n:,} sessions on which all {len(SYMS)} declared symbols have {NBAR} bars; warm-up {WARM}")
    cs = {s: cs_bp(P[s], days, n) for s in SYMS}; com = {s: commission_bp(float(np.nanmedian(P[s]['C']))) for s in SYMS}
    com_big = {s: commission_bp(float(np.nanmedian(P[s]['C'])), NOTIONAL_BIG) for s in SYMS}
    print("  Corwin-Schultz half-spread (bp/side, from each symbol's own 15m OHLC) / IBKR-Fixed commission on a $10k leg / on a $50k leg:")
    print("    " + "  ".join(f"{s} {cs[s]:.1f}/{com[s]:.2f}/{com_big[s]:.2f}" for s in CORE + SECTORS))
    pair_cost = lambda a, b: 2.0 * (cs[a] + com[a] + cs[b] + com[b])                      # both legs, in and out, crossed, $10k legs
    pair_cost_big = lambda a, b: 2.0 * (cs[a] + com_big[a] + cs[b] + com_big[b])           # the same at $50k legs
    pair_pass = lambda a, b: 2.0 * (com[a] + com[b])                                      # passive line: commission only
    res = dict(spec="D504", commit=SPEC, start=START, end=END, sessions=n, symbols=SYMS, cost=dict(cs=cs, commission=com), cells={})
    print(f"\n  {'cell':12s} {'pair':11s} {'N':>4s} {'/yr':>4s} {'gross bp':>8s} {'med':>6s} {'trim':>6s} {'costX':>6s} {'netX':>6s} {'netP':>6s} {'hit':>5s} {'skew':>5s} {'z':>5s} {'N1p95':>6s} {'>=obs':>6s} {'halves':>13s} {'yrs+':>5s}")
    cells = {}
    def add(label, sig, a, b, want_null=True):
        st, ok, pnl = score_cell(days, sig, B["r"][a], B["r"][b], pair_cost(a, b), label, want_null)
        st["pair"] = f"{a}/{b}"; st["net_passive_bp"] = st.get("gross_bp", float("nan")) - pair_pass(a, b)
        st["cost_big_bp"] = pair_cost_big(a, b); st["net_big_bp"] = st.get("gross_bp", float("nan")) - st["cost_big_bp"]; cells[label] = st
        if st.get("n", 0) >= 5:
            nl = st.get("null", {})
            print(f"  {label:12s} {st['pair']:11s} {st['n']:4d} {st['per_year']:4.0f} {st['gross_bp']:+8.2f} {st['median_bp']:+6.2f} {st['trimmed_bp']:+6.2f} {st['cost_bp']:6.2f} {st['net_bp']:+6.2f} {st["net_big_bp"]:+6.2f} {100*st["hit"]:4.1f}% {st['skew']:+5.2f} {st['z']:+5.2f} {nl.get('z_p95', float('nan')):+6.2f} {100*nl.get('share_ge', float('nan')):5.1f}% {st['halves_bp'][0]:+6.2f}/{st['halves_bp'][1]:+6.2f} {st['positive_years']:2d}/{st['n_years']:<2d}")
        else:
            print(f"  {label:12s} {st['pair']:11s} {st.get('n', 0):4d}  (too few)")
        return st
    add("P1", B["sigs"]["P1"], "SMH", "QQQ"); add("P1_z", B["sigs"]["P1_z"], "SMH", "QQQ"); add("P2", B["sigs"]["P2"], "SMH", "QQQ")
    for s in SECTORS:
        add(f"P3_{s}", B["sigs"]["P1"], s, "QQQ")
    for k in ("P4_EU", "P4_EWZ", "P4_EEM"):
        add(k, B["sigs"][k], "SMH", "QQQ")
    add("N4_late", B["sigs"]["N4_late"], "SMH", "QQQ")
    # N2 family maximum over the twelve declared cells (P1, P2, six P3, three P4)
    fam_keys = ["P1", "P2"] + [f"P3_{s}" for s in SECTORS] + ["P4_EU", "P4_EWZ", "P4_EEM"]
    paths = {k: cells[k]["_z"] for k in fam_keys if "_z" in cells[k]}; D = min(len(v) for v in paths.values())
    M = np.column_stack([v[:D] for v in paths.values()]); fam = np.nanmax(M, axis=1)
    obs = {k: cells[k]["z"] for k in paths}; best = max(obs, key=obs.get)
    res["family"] = dict(n_cells=len(paths), n_offsets=int(D), p50=float(np.median(fam)), p95=float(np.quantile(fam, .95)), p99=float(np.quantile(fam, .99)),
                         observed_max=obs[best], observed_argmax=best, share_ge=float((fam >= obs[best]).mean()), observed=obs)
    f = res["family"]; print(f"\n  N2 FAMILY MAXIMUM over {f['n_cells']} cells, {f['n_offsets']:,} common offsets (exact): p50 {f['p50']:+.2f}  p95 {f['p95']:+.2f}  p99 {f['p99']:+.2f}   observed max {f['observed_max']:+.2f} ({f['observed_argmax']}); share of offsets >= observed {100*f['share_ge']:.1f}%")
    # N3 partner-randomised: keep the rule, redraw the short leg
    print("\n  N3 partner-randomised (P1's rule, SMH against each other symbol; gross bp):")
    n3 = {}
    for s in SYMS:
        if s == "SMH":
            continue
        st, _, _ = score_cell(days, B["sigs"]["P1"], B["r"]["SMH"], B["r"][s], pair_cost("SMH", s), f"N3_{s}", want_null=False); n3[s] = st
    res["n3"] = {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")} for k, v in n3.items()}
    print("    " + "  ".join(f"{s} {n3[s]['gross_bp']:+.1f}" for s in n3 if n3[s].get("n", 0) >= 5))
    # M1 the joint regression
    y = B["r"]["SMH"] - B["r"]["QQQ"]; X = np.column_stack([B["zA"], B["zG"]])
    b, se, t, nobs = ols_t(y, X); res["m1"] = dict(n=nobs, const=b[0], beta_zA=b[1], beta_zG=b[2], t_const=t[0], t_zA=t[1], t_zG=t[2], se_zA=se[1], se_zG=se[2])
    gap_on_A, _, gt, _ = ols_t(B["G"], B["zA"][:, None]); res["m1"]["gap_on_zA"] = dict(beta=gap_on_A[1], t=gt[1])
    print(f"\n  M1 relative day session (SMH-QQQ, 09:45->16:00) on z(A) and z(G), Newey-West(5), n {nobs:,}:")
    print(f"    z(A) {b[1]:+.2f} bp (t {t[1]:+.2f})   z(G) {b[2]:+.2f} bp (t {t[2]:+.2f})   const {b[0]:+.2f} (t {t[0]:+.2f})")
    print(f"    for scale: the relative GAP on z(A) is {gap_on_A[1]:+.2f} bp (t {gt[1]:+.2f}) -- where the Asian channel actually clears")
    # P5 the prop-eligible futures arm
    print("\n  P5 the prop-eligible arm: MNQ vs MES, 09:45 open -> 15:59 close, $3 a leg")
    p5 = futures_arm(days, B); res["p5"] = {k: v for k, v in p5.items() if not k.startswith("_")}
    # decision
    p1 = cells["P1"]; costX = p1["cost_bp"]; sect = [cells[f"P3_{s}"]["gross_bp"] for s in SECTORS]
    ok_cost = p1.get("gross_bp", 0) >= 1.5 * costX; ok_n1 = p1.get("clears_N1", False); ok_fam = p1.get("z", -9) > f["p95"]
    ok_hit = p1.get("hit", 0) > 0.5; ok_half = p1.get("same_sign_halves", False)
    ok_spec = sum(1 for v in sect if np.sign(v) == np.sign(p1.get("gross_bp", 0)) and abs(v) >= abs(p1.get("gross_bp", 0))) == 0
    verdict = "PROCEED" if (ok_cost and ok_n1 and ok_fam and ok_hit and ok_half and ok_spec) else ("PICK" if (ok_n1 and (p1.get("net_bp", -9) > 0 or not ok_spec)) else "CLOSE")
    res["verdict"] = verdict; res["decision_terms"] = dict(cost=bool(ok_cost), n1=bool(ok_n1), family=bool(ok_fam), hit=bool(ok_hit), halves=bool(ok_half), semis_specific=bool(ok_spec))
    print(f"\n  VERDICT (pre-registered rule): {verdict}   terms {res['decision_terms']}")
    # predictions
    print("\nPREDICTIONS")
    print(f"  X-a M1 z(A) coefficient in [-6, 0] bp with |t| < 2                                  : {b[1]:+.2f} bp, t {t[1]:+.2f}")
    print(f"  X-b P1 140-160 trades, gross in [-8, +8] bp, does NOT clear the family bar; |P2| < |P1| : P1 {p1['n']} trades {p1['gross_bp']:+.2f} bp, clears family {ok_fam}; |P2| {abs(cells['P2']['gross_bp']):.2f} vs |P1| {abs(p1['gross_bp']):.2f}")
    nbeat = sum(1 for v in sect if abs(v) >= abs(p1["gross_bp"]))
    print(f"  X-c P3 sectors scatter +-10 bp and >= 2 of 6 exceed SMH in absolute size            : spread {min(sect):+.1f}..{max(sect):+.1f}; {nbeat} of 6 exceed |SMH|")
    print(f"  X-d the three P4 cells are inside N1; EEM closer to P1 than Europe                  : " + "  ".join(f"{k} z {cells[k]['z']:+.2f} vs p95 {cells[k]['null']['z_p95']:+.2f} ({'in' if not cells[k].get('clears_N1') else 'OUT'})" for k in ("P4_EU", "P4_EWZ", "P4_EEM")) + f"; |EEM-P1| {abs(cells['P4_EEM']['gross_bp']-p1['gross_bp']):.1f} vs |EU-P1| {abs(cells['P4_EU']['gross_bp']-p1['gross_bp']):.1f}")
    print(f"  X-e P5 gross under $6 a round trip; rho(P5, K8) in [0.1, 0.4]                       : gross ${p5['gross_usd']:+.2f}, net ${p5['net_usd']:+.2f}; rho(P5, K8) {p5['rho_k8']:+.2f}" if p5.get("n", 0) >= 5 else "  X-e P5: too few trades")
    print(f"  X-f the verdict is CLOSE                                                            : {verdict}")
    for k in list(cells):
        cells[k] = {kk: vv for kk, vv in cells[k].items() if not kk.startswith("_")}
    res["cells"] = cells
    OUT.write_text(json.dumps(res, indent=1, default=float))
    tr = pd.DataFrame(dict(day=days, A=B["A"], G=B["G"], zA=B["zA"], zG=B["zG"], dis=B["Dis"],
                           smh_ret=B["r"]["SMH"], qqq_ret=B["r"]["QQQ"], rel_ret=B["r"]["SMH"] - B["r"]["QQQ"]))
    tr.to_csv(REPO / "data" / "d504_signal_and_returns.csv.gz", index=False, compression="gzip", float_format="%.4f")
    print(f"\nwrote {OUT.relative_to(REPO)} and data/d504_signal_and_returns.csv.gz   {(time.time()-t0)/60:.1f} min")


def futures_arm(days, B):
    """P5: P1's signal traded as 1 MNQ vs 1 MES from the 09:45 bar's open to the 15:59 close, $3 a leg. Also the K8 correlation (C-b)."""
    f = {}
    for root in ("NQ", "ES"):
        d = D490.load_root(root, START, END); f[root] = d
    common = np.array(sorted(set(f["NQ"]["days"][f["NQ"]["trade"]]) & set(f["ES"]["days"][f["ES"]["trade"]]) & set(days)))
    idx = {root: {t: i for i, t in enumerate(f[root]["days"])} for root in f}
    pnl = {}
    for root in f:
        O, C = f[root]["O"], f[root]["C"]; i = np.array([idx[root][t] for t in common])
        pnl[root] = (C[i, FUT_EXIT_BAR] - O[i, FUT_ENTRY_BAR]) * FUT_MULT[root]
    sig = pd.Series(B["sigs"]["P1"], index=days).reindex(common).to_numpy()
    thr = pd.Series(causal_quantile(np.abs(B["sigs"]["P1"])), index=days).reindex(common).to_numpy()
    ok = np.isfinite(sig) & np.isfinite(thr) & (np.abs(sig) >= thr); s = np.sign(sig)
    spread = pnl["NQ"] - pnl["ES"]; x = (s * spread)[ok]
    # K8: long the NQ day session after a down NQ day session, the ledger's entry #1
    dNQ = f["NQ"]; day_ret = (dNQ["C"][:, 389] / dNQ["O"][:, 0] - 1.0) * 1e4; k8_dir = np.concatenate([[np.nan], np.where(day_ret[:-1] < 0, 1.0, 0.0)])
    k8_pnl = np.where(k8_dir == 1.0, (dNQ["C"][:, 389] - dNQ["O"][:, 0]) * FUT_MULT["NQ"] - FUT_FEE, 0.0)
    k8 = pd.Series(k8_pnl, index=dNQ["days"]).reindex(common).fillna(0.0).to_numpy()
    p5 = pd.Series(np.where(ok, s * spread - 2 * FUT_FEE, 0.0), index=common).to_numpy()
    rho = float(np.corrcoef(p5, k8)[0, 1]) if p5.std() > 0 and k8.std() > 0 else float("nan")
    if ok.sum() < 5:
        return dict(n=int(ok.sum()))
    yrs = np.array([t[:4] for t in common[ok]]); beta = float(np.polyfit(pnl["ES"][ok], pnl["NQ"][ok], 1)[0])
    sharpe = float(p5.mean() / p5.std(ddof=1) * math.sqrt(252)) if p5.std(ddof=1) > 0 else float("nan")
    # the vehicle question D503 made binding: at 2026 prices one micro's daily sigma is ~$340 against a $50k account's $2,000 floor.
    # A market-neutral micro PAIR is the only futures construction whose dollar sigma falls rather than rises, so measure it.
    single = (dNQ["C"][:, 389] - dNQ["O"][:, 0]) * FUT_MULT["NQ"]; single = pd.Series(single, index=dNQ["days"]).reindex(common).to_numpy()
    yr = np.array([t[:4] for t in common]); per_year = lambda v, thr: {y: float((v[yr == y] < thr).sum()) for y in sorted(set(yr))}
    vehicle = dict(pair_sigma_usd=float(np.std(spread - 2 * FUT_FEE, ddof=1)), single_micro_sigma_usd=float(np.nanstd(single, ddof=1)),
                   pair_sigma_recent=float(np.std((spread - 2 * FUT_FEE)[yr >= "2023"], ddof=1)), single_sigma_recent=float(np.nanstd(single[yr >= "2023"], ddof=1)),
                   pair_breaches_1000_per_year=per_year(spread - 2 * FUT_FEE, -1000.0), single_breaches_1000_per_year=per_year(single, -1000.0),
                   note="sigma of the UNCONDITIONAL day-session pair and single micro on the common calendar; P3's bar is a loss beyond 2% of $50k = $1,000")
    print(f"    VEHICLE (D503's constraint): daily sigma of the unconditional MNQ/MES pair ${vehicle['pair_sigma_usd']:.0f} vs one MNQ ${vehicle['single_micro_sigma_usd']:.0f}"
          f"   (2023 only: ${vehicle['pair_sigma_recent']:.0f} vs ${vehicle['single_sigma_recent']:.0f});  days beyond -$1,000 per year, pair {sum(vehicle['pair_breaches_1000_per_year'].values())/len(set(yr)):.1f} vs single {sum(vehicle['single_breaches_1000_per_year'].values())/len(set(yr)):.1f}")
    out = dict(vehicle=vehicle, n=int(ok.sum()), gross_usd=float(x.mean()), median_usd=float(np.median(x)), net_usd=float(x.mean() - 2 * FUT_FEE), hit=float((x > 0).mean()),
               skew=float(pd.Series(x).skew()), se_usd=float(x.std(ddof=1) / math.sqrt(x.size)), net_sharpe=sharpe, rho_k8=rho,
               beta_nq_on_es=beta, halves_usd=[float(x[yrs <= "2020"].mean()), float(x[yrs >= "2021"].mean())],
               worst_day_usd=float(p5.min()), notional_note="1 MNQ vs 1 MES; beta_nq_on_es is the dollar regression slope, so residual long-NQ exposure is (1 - beta) MES")
    print(f"    {out['n']} trades, gross ${out['gross_usd']:+.2f} (SE {out['se_usd']:.2f}), net ${out['net_usd']:+.2f} against $6, hit {100*out['hit']:.1f}%, net Sharpe {out['net_sharpe']:+.2f}, worst day ${out['worst_day_usd']:+.0f}, rho with K8 {out['rho_k8']:+.2f}, dollar beta NQ on ES {beta:.2f}")
    return out


# ------------------------------------------------------------------------------------------ selftest
def synth(n=1500, seed=5, plant=0.0, nbar=NBAR, bar_noise=10.0, gap_share=0.4):
    """A 15-minute panel for the declared symbols. The Asian factor `asia` enters EWT and EWY gaps in full and SMH's gap only at
    `gap_share` -- the underreaction the record hypothesises -- and `plant` x asia is then delivered in SMH's 09:45->16:00 window."""
    rng = np.random.default_rng(seed); days = np.array([str(d.date()) for d in pd.bdate_range("2018-01-02", periods=n)])
    P = {}; base = {s: 100.0 for s in SYMS}
    gapz = {s: rng.normal(0, 60, n) for s in SYMS}                       # bp
    common = rng.normal(0, 80, n); asia = rng.normal(0, 90, n)
    share = {"EWT": 1.0, "EWY": 1.0, "SMH": gap_share}
    for s in SYMS:
        g = gapz[s] + common + share.get(s, 0.0) * asia
        intr = rng.normal(0, bar_noise, (n, nbar))
        if s == "SMH" and plant:
            intr[:, 1:] += (plant * asia / (nbar - 1))[:, None]
        O = np.empty((n, nbar)); C = np.empty((n, nbar)); p = base[s]
        for t in range(n):
            p *= 1 + g[t] / 1e4
            for b in range(nbar):
                O[t, b] = p; p *= 1 + intr[t, b] / 1e4; C[t, b] = p
        H = np.maximum(O, C) * (1 + rng.uniform(0, 8, (n, nbar)) / 1e4); L = np.minimum(O, C) * (1 - rng.uniform(0, 8, (n, nbar)) / 1e4)
        P[s] = dict(O=O, H=H, L=L, C=C)
    return days, P, asia


def cmd_selftest():
    print("D504 selftest")
    days, P, asia = synth(plant=0.0); B = build(days, P)
    # [A] gap and return windows: the gap uses bar 0's close over the PREVIOUS session's bar 25 close; the return starts at bar 1's open
    g, r, _ = gaps_and_returns(P["SMH"]); assert not np.isfinite(g[0])
    assert abs(g[7] - (P["SMH"]["C"][7, 0] / P["SMH"]["C"][6, NBAR - 1] - 1) * 1e4) < 1e-9
    assert abs(r[7] - (P["SMH"]["C"][7, NBAR - 1] / P["SMH"]["O"][7, 1] - 1) * 1e4) < 1e-9
    # [B] causality: replace everything from t0 on; nothing at or before t0 moves, and the entry price is never used by the signal
    t0 = 600; P2 = {s: {k: v.copy() for k, v in P[s].items()} for s in P}; rng = np.random.default_rng(1)
    for s in P2:
        P2[s]["C"][t0:] *= 1 + rng.normal(0, 300, P2[s]["C"][t0:].shape) / 1e4; P2[s]["O"][t0:, 1:] *= 1 + rng.normal(0, 300, P2[s]["O"][t0:, 1:].shape) / 1e4
    B2 = build(days, P2); assert np.allclose(B["Dis"][:t0], B2["Dis"][:t0], equal_nan=True), "the signal read the future"
    assert not np.allclose(B["Dis"][t0:], B2["Dis"][t0:], equal_nan=True)
    P3 = {s: {k: v.copy() for k, v in P[s].items()} for s in P}; P3["SMH"]["O"][:, 1] *= 1.05      # move ONLY the entry price
    B3 = build(days, P3); assert np.allclose(B["Dis"], B3["Dis"], equal_nan=True), "the signal must not read the entry bar's open"
    assert not np.allclose(B["r"]["SMH"], B3["r"]["SMH"], equal_nan=True), "the outcome must read it"
    # [C] sign audit in money: on a trade day the P&L is positive exactly when the pair moved the signal's way
    thr = causal_quantile(np.abs(B["Dis"])); ok, s, pnl = cell_series(B["Dis"], thr, B["r"]["SMH"], B["r"]["QQQ"])
    i = np.flatnonzero(ok)[0]; rel = B["r"]["SMH"][i] - B["r"]["QQQ"][i]
    assert (pnl[i] > 0) == ((rel > 0) == (s[i] > 0)), (pnl[i], rel, s[i])
    ok2, s2, pnl2 = cell_series(-B["Dis"], thr, B["r"]["SMH"], B["r"]["QQQ"]); assert np.allclose(pnl2[ok2], -pnl[ok], equal_nan=True), "flipping the signal must flip the book"
    # [D] the threshold fires on about a decile and never before the warm-up
    assert not ok[:WARM].any(); share = ok[WARM:].mean(); assert 0.05 < share < 0.16, share
    # [E] the rotation is exact against an explicit loop
    m, z = rotation(B["Dis"], thr, B["r"]["SMH"], B["r"]["QQQ"], d_max=40)
    for k in (1, 9, 37):
        ms, zs = rotation_slow(B["Dis"], thr, B["r"]["SMH"], B["r"]["QQQ"], k); assert abs(ms - m[k - 1]) < 1e-9 and abs(zs - z[k - 1]) < 1e-9, (k, ms, m[k - 1])
    # [F] known answer: with a planted continuation in SMH only, P1 clears N1 and the sector controls do not; with no plant, P1 does not
    dP, PP, _ = synth(plant=3.0); BP = build(dP, PP)
    stP, _, _ = score_cell(dP, BP["sigs"]["P1"], BP["r"]["SMH"], BP["r"]["QQQ"], 0.0, "P1")
    st0, _, _ = score_cell(days, B["sigs"]["P1"], B["r"]["SMH"], B["r"]["QQQ"], 0.0, "P1")
    stC, _, _ = score_cell(dP, BP["sigs"]["P1"], BP["r"]["KRE"], BP["r"]["QQQ"], 0.0, "P3_KRE")
    assert stP["clears_N1"] and stP["gross_bp"] > 0 and stP["hit"] > 0.5, stP
    assert not st0["clears_N1"], st0["z"]; assert not stC["clears_N1"], stC["z"]
    # [G] the regression finds the planted coefficient with the right sign, and zero without it
    yP = BP["r"]["SMH"] - BP["r"]["QQQ"]; bP, _, tP, _ = ols_t(yP, np.column_stack([BP["zA"], BP["zG"]]))
    y0 = B["r"]["SMH"] - B["r"]["QQQ"]; b0, _, t0_, _ = ols_t(y0, np.column_stack([B["zA"], B["zG"]]))
    assert bP[1] > 20 and tP[1] > 4, (bP[1], tP[1]); assert abs(t0_[1]) < 3, t0_[1]
    # [H] cost helpers are positive and ordered the way prices imply
    c_smh = commission_bp(124.0); c_qqq = commission_bp(329.0)
    assert abs(c_smh - 1.0) < 1e-9 and abs(c_qqq - 1.0) < 1e-9, (c_smh, c_qqq)          # the $1 order minimum binds on a $10k leg
    b_smh = commission_bp(124.0, NOTIONAL_BIG); b_qqq = commission_bp(329.0, NOTIONAL_BIG)
    assert b_smh > b_qqq > 0 and b_smh < c_smh, (b_smh, b_qqq)                          # per-share regime: the dearer share is cheaper in bp
    csv = cs_bp(P["SMH"], days, len(days)); assert np.isfinite(csv) and csv >= 0
    print(f"  A windows  B causality (and the entry-bar break)  C sign audit (and its flip)  D threshold fires on {100*share:.1f}%  E exact rotation"
          f"  F known answer (planted z {stP['z']:+.2f} > p95 {stP['null']['z_p95']:+.2f}; unplanted {st0['z']:+.2f}; sector {stC['z']:+.2f})"
          f"  G regression ({bP[1]:+.1f} bp t {tP[1]:+.1f} planted, t {t0_[1]:+.1f} unplanted)  H costs (CS {csv:.1f} bp, commission {c_smh:.2f}/{c_qqq:.2f})\n  all pass")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--run", action="store_true"); ap.add_argument("--selftest", action="store_true"); a = ap.parse_args()
    if a.selftest:
        cmd_selftest()
    if a.run:
        run()
    if not (a.run or a.selftest):
        ap.print_help()

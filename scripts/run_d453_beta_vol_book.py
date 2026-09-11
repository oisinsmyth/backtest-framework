"""D453 -- issuance stage 1b: D446's book re-accounted with a per-name beta hedge and volatility-scaled weights. Same selection, same
ledger, same three controls (re-accounted the same way), same bar. Spec committed in 8b7747d BEFORE this file. In-sample; no holdout.

    uv run python -u scripts/run_d453_beta_vol_book.py --run [--quick]
    uv run python -u scripts/run_d453_beta_vol_book.py --selftest

Mark: w_i * sgn * (v_it - beta_i * m_t) with the kernel's v (ocT on the entry bar, r1T after) and m (mkt_oc on the entry bar, mkt after);
beta_i = OLS slope over the 252 bars ending the bar before entry (>= 126 pairs, else 1), clipped [0, 3]; w_i = clip(sigma_med / sigma_i,
0.25, 4), sigma over the 63 bars ending the bar before entry (>= 40, else w = 1). [K2]: beta == 1, w == 1 reproduces the kernel.
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
R46 = _load("d446", "run_d446_issuance_book.py")
OUT = REPO / "data" / "d453_beta_vol_book.json"; D446 = REPO / "data" / "d446_issuance_book.json"
BETA_WIN, BETA_MIN, BETA_LO, BETA_HI = 252, 126, 0.0, 3.0; VOL_WIN, VOL_MIN, W_LO, W_HI = 63, 40, 0.25, 4.0
CAP, N_MAX, SEED = R46.CAP, R46.N_MAX, 453; CAPTURE, CHASE_BP = R46.CAPTURE, R46.CHASE_BP


# ------------------------------------------------------------------------------------------ beta and weight panels (causal: bar t uses bars <= t-1)
def beta_panel(r1T, mkt):
    X = pd.DataFrame(r1T); m = pd.Series(mkt); both = X.notna().to_numpy() & np.isfinite(mkt)[:, None]
    Xm = X.where(pd.DataFrame(both)); mm = pd.DataFrame(np.where(both, mkt[:, None], np.nan))
    n = pd.DataFrame(both.astype(float)).rolling(BETA_WIN, min_periods=BETA_MIN).sum()
    sx = Xm.rolling(BETA_WIN, min_periods=BETA_MIN).sum(); sm = mm.rolling(BETA_WIN, min_periods=BETA_MIN).sum()
    sxm = (Xm * mm).rolling(BETA_WIN, min_periods=BETA_MIN).sum(); smm = (mm * mm).rolling(BETA_WIN, min_periods=BETA_MIN).sum()
    cov = sxm / n - (sx / n) * (sm / n); var = smm / n - (sm / n) ** 2
    b = (cov / var).to_numpy(); b = np.where(np.isfinite(b), np.clip(b, BETA_LO, BETA_HI), 1.0)
    out = np.ones_like(b); out[1:] = b[:-1]                                   # bar t uses the window ending t-1
    return out


def weight_panel(r1T, elig):
    s = pd.DataFrame(r1T).rolling(VOL_WIN, min_periods=VOL_MIN).std(ddof=1).to_numpy(); sig = np.full_like(s, np.nan); sig[1:] = s[:-1]
    med = np.array([np.nanmedian(sig[t, elig[t]]) if (elig[t] & np.isfinite(sig[t])).sum() >= 30 else np.nan for t in range(sig.shape[0])])
    w = med[:, None] / sig; w = np.where(np.isfinite(w), np.clip(w, W_LO, W_HI), 1.0)
    return w, sig, med


# ------------------------------------------------------------------------------------------ the re-accounting
def mark(A3, trades, beta, w, T):
    """(book_dep_x weighted (T,), signed_x (T,), W (T,), per-trade hedged pnl (unit weight, bp), per-trade weight, per-trade beta)."""
    r1T, mkt, ocT, mkt_oc = A3["r1T"], np.asarray(A3["mkt"], float), A3["ocT"], np.asarray(A3["mkt_oc"], float)
    sx = np.zeros(T); W = np.zeros(T); pnl = np.empty(len(trades)); wt = np.empty(len(trades)); bt = np.empty(len(trades))
    for i, (row, e0, age, _p, side) in enumerate(trades):
        sgn = 1.0 if side == 0 else -1.0; b = float(beta[e0, row]); ww = float(w[e0, row]); e1 = e0 + age
        v = np.asarray(r1T[e0:e1, row], float).copy(); v[0] = ocT[e0, row]; m = mkt[e0:e1].copy(); m[0] = mkt_oc[e0]
        x = sgn * (v - b * m); x = np.where(np.isfinite(x), x, 0.0)
        sx[e0:e1] += ww * x; W[e0:e1] += ww; pnl[i] = x.sum() * 1e4; wt[i] = ww; bt[i] = b
    book = np.where(W > 0, sx / np.maximum(W, 1e-300), 0.0) * 1e4
    return book, sx, W, pnl, wt, bt


def side_costs(V59, P, trades, wt, W):
    """Weighted round-trip cost per weighted deployed capital-bar (bp/bar): crossed and passive."""
    HS = np.asarray(P["HALF"]["PUB"], float); C = np.asarray(P["CLOSE"], float); row = np.array([t[0] for t in trades]); e0 = np.array([t[1] for t in trades])
    hs = HS[e0, row]; px = C[e0, row]; comm = 2.0 * V59.PER_SHARE / px * 1e4; spread2 = 2.0 * hs; borrow = np.asarray(V59.V49.borrow_of(P, trades)[0], float)
    fin = np.isfinite(hs) & np.isfinite(px); hs_m = np.nanmedian(hs); spread2 = np.where(fin, spread2, 2 * hs_m); comm = np.where(fin, comm, np.nanmedian(comm))
    cap_bars = W.sum(); crossed = float((wt * (spread2 + comm + borrow)).sum() / cap_bars); passive = float((wt * ((spread2 + comm) * (1 - CAPTURE) + CHASE_BP + borrow)).sum() / cap_bars)
    return dict(crossed=crossed, passive=passive, two_c_mean=float(np.mean(spread2 + comm)), borrow_mean=float(borrow.mean()), htb_share=float((borrow > 0).mean()))


def ledger_stats(V59, P, trades, beta, w, T, t_end, dates, R37):
    book, sx, W, pnl, wt, bt = mark(P["A3"], trades, beta, w, T); c = side_costs(V59, P, trades, wt, W)
    return dict(book=book, W=W, pnl=pnl, wt=wt, beta=bt, wmean=float((wt * pnl).sum() / wt.sum()), mean=float(pnl.mean()), median=float(np.median(pnl)), beta_mean=float(bt.mean()), w_mean=float(wt.mean()), **c)


def conc(trades, pnl, wt, symbols):
    contrib = wt * pnl; by = {}
    for t, x in zip(trades, contrib): by[t[0]] = by.get(t[0], 0.0) + float(x)
    v = np.sort(np.array(list(by.values())))[::-1]; tot = contrib.sum(); k = max(1, int(round(0.01 * contrib.size)))
    top = sorted(by.items(), key=lambda kv: -kv[1])[:6]
    return dict(names=len(by), to_half=int(np.searchsorted(np.cumsum(v), 0.5 * tot) + 1) if tot > 0 else None, top1_share=float(100 * np.sort(contrib)[-k:].sum() / tot) if tot > 0 else float("nan"),
                top_names=[(symbols[j], float(100 * x / tot)) for j, x in top] if tot > 0 else [])


# ------------------------------------------------------------------------------------------ the study
def run(quick=False):
    t0 = time.time(); print("D453 -- issuance stage 1b: D446's book, beta-hedged and vol-scaled; same selection, same controls, same bar\n      the spec was committed in 8b7747d BEFORE this ran; mining fixture only; no holdout\n")
    PREP = _load("d348p", "d348_prep.py"); V59 = _load("d359r", "run_d359_loser_rally_short.py"); A92 = _load("d392", "run_d392_base_rate_atlas.py"); R37 = _load("d437", "run_d437_stage1.py")
    P = PREP.prep(need_grids=True); T, N = P["T"], P["n"]; elig = np.asarray(P["elig"]).copy(); dates = np.array([str(x)[:10] for x in P["dates"]]); symbols = list(P["symbols"])
    t_end = int(np.searchsorted(dates, R46.END, side="right")); elig[t_end:] = False
    df = pd.read_csv(R46.PANEL, dtype={"fiscal_date": str, "avail_date": str, "symbol": str, "cik": str}); NS = R46.latest_ns_panel(df, symbols, dates, T); S = R46.percentile_panel(NS, elig); masks = R46.masks_from(S, elig)
    cover = np.isfinite(S).sum(axis=1); d0 = int(np.flatnonzero(cover >= 30)[0]); d46 = json.load(open(D446))
    A3 = P["A3"]; beta = beta_panel(np.asarray(A3["r1T"], float), np.asarray(A3["mkt"], float)); w, sig, med = weight_panel(np.asarray(A3["r1T"], float), elig)
    ones = np.ones((T, N)); n_draw = 10 if quick else R46.N_DRAW; step = 42 if quick else R46.ROT_STEP; rng = np.random.default_rng(SEED)
    res = dict(spec="8b7747d", d446_ledger_checked=True, sides={}, book={}, controls={}, bar={}, quick=quick)

    # the real ledgers (D446's selection) and [K2]
    R = {k: R46.simulate(V59, P, masks[k], S, CAP, side, N_MAX) for k, side in R46.SIDES.items()}
    for k in R:
        assert len(R[k]["trades"]) == d46["sides"][k]["trades"], f"[L] the {k} ledger is not D446's ({len(R[k]['trades'])} vs {d46['sides'][k]['trades']})"
        book1, _, W1, pnl1, _, _ = mark(A3, R[k]["trades"], ones, ones, T); kb = np.nan_to_num(np.asarray(R[k]["book_dep_x"], float)) * 1e4; held = W1 > 0
        assert np.allclose(book1[held], kb[held], atol=1e-9) and np.allclose(pnl1, V59.V47.pnl_bp(R[k]), atol=1e-9), f"[K2] the re-accounting at beta=1, w=1 does not reproduce the kernel on the {k} side"
    print(f"  [L] ledgers are D446's ({d46['sides']['short']['trades']:,} / {d46['sides']['long']['trades']:,} trades);  [K2] beta=1, w=1 reproduces the kernel's book and every trade's pnl to 1e-9")
    yr = np.array([int(x[:4]) for x in dates]); g_comb = np.zeros(T); cc = cp = 0.0
    for k, side in R46.SIDES.items():
        L = ledger_stats(V59, P, R[k]["trades"], beta, w, T, t_end, dates, R37); cn = conc(R[k]["trades"], L["pnl"], L["wt"], symbols)
        bk = R46.book_stats(R37, L["book"], dates, d0, L["crossed"], L["passive"], t_end); g_comb += L["book"]; cc += L["crossed"]; cp += L["passive"]
        res["sides"][k] = dict(trades=len(R[k]["trades"]), wmean=L["wmean"], mean=L["mean"], median=L["median"], beta_mean=L["beta_mean"], w_mean=L["w_mean"], two_c=L["two_c_mean"], borrow=L["borrow_mean"], htb_share=L["htb_share"],
                               cost_crossed_bar=L["crossed"], cost_passive_bar=L["passive"], book=bk, conc=cn, d446_gross=d46["sides"][k]["gross"], d446_book_gross=d46["sides"][k]["book"]["gross"], d446_crossed_bar=d46["sides"][k]["cost_crossed_bar"])
        print(f"  {k:5s}: beta mean {L['beta_mean']:.2f}  w mean {L['w_mean']:.2f}  | per trade hedged {L['mean']:+.1f} (median {L['median']:+.1f}), weighted {L['wmean']:+.1f}  [D446 {d46['sides'][k]['gross']:+.1f}]  | book gross {bk['gross']:+.3f} +- {bk['se']:.3f} [D446 {d46['sides'][k]['book']['gross']:+.3f}]  crossed {L['crossed']:.3f} [D446 {d46['sides'][k]['cost_crossed_bar']:.3f}] net {bk['net_crossed']:+.3f}  to-half {cn['to_half']}  top1% {cn['top1_share']:.0f}%  top {cn['top_names'][:3]}")
    bk = R46.book_stats(R37, g_comb, dates, d0, cc, cp, t_end); tr = R["short"]["trades"] + R["long"]["trades"]
    Ls = ledger_stats(V59, P, R["short"]["trades"], beta, w, T, t_end, dates, R37); Ll = ledger_stats(V59, P, R["long"]["trades"], beta, w, T, t_end, dates, R37)
    cn = conc(tr, np.concatenate([Ls["pnl"], Ll["pnl"]]), np.concatenate([Ls["wt"], Ll["wt"]]), symbols); bk.update(dict(to_half=cn["to_half"], top1_share=cn["top1_share"], names=cn["names"], top_names=cn["top_names"])); res["book"] = bk
    print(f"  COMBINED: gross {bk['gross']:+.3f} +- {bk['se']:.3f} [D446 {d46['book']['gross']:+.3f} +- {d46['book']['se']:.3f}]  crossed {cc:.3f} -> net {bk['net_crossed']:+.3f} ({bk['net_crossed']/bk['se']:+.1f} SE)  Sharpe {bk['sharpe_crossed']:+.2f}  passive -> net {bk['net_passive']:+.3f}  era1 {bk['era1']:+.3f} +- {bk['era1_se']:.3f}  era2 {bk['era2']:+.3f} +- {bk['era2_se']:.3f}  to-half {bk['to_half']} [D446 5]  top1% {bk['top1_share']:.0f}% [85]")
    print("  by year (net crossed): " + " ".join(f"{y}:{x:+.1f}" for y, x in bk["by_year"].items()))

    # C1 -- state-matched names at the real entry days, re-accounted
    print(f"\n  C1 state-matched ({n_draw} draws x 2 sides)", flush=True); t1 = time.time()
    cells = [R46.shift(c, elig) for c in R46.cells_of(A92, P, elig)]; pool = R46.shift(~(np.nan_to_num(S, nan=50.0) >= R46.TOP) & ~(S <= R46.BOT) & elig, elig); SC = np.full((T, N), 50.0)
    for k, side in R46.SIDES.items():
        ev = R46.entry_mask(R[k], T, N); gs = []
        for d in range(n_draw):
            rr = R46.simulate(V59, P, R46.c1_mask(R37, rng, ev, cells, pool), SC, CAP, side, None); _, _, _, pnl, wt, _ = mark(A3, rr["trades"], beta, w, T); gs.append(float((wt * pnl).sum() / wt.sum()))
        gs = np.array(gs); real = res["sides"][k]["wmean"]; sd = float(gs.std(ddof=1)); c = dict(p50=float(np.median(gs)), p95=float(np.quantile(gs, .95)), se=sd / np.sqrt(n_draw), sd=sd, increment=real - float(np.median(gs)),
                                                                                                    z_median=(real - float(np.median(gs))) / sd, z_p95=(real - float(np.quantile(gs, .95))) / sd)
        c["passes"] = bool(real > c["p95"] and (real - c["p95"]) >= 2 * c["se"]); res["controls"][f"C1_{k}"] = c
        print(f"    {k:5s}: real {real:+.1f}  C1 p50 {c['p50']:+.1f}  p95 {c['p95']:+.1f} (draw SD {sd:.0f}; real {c['z_median']:+.2f} SD above median, {c['z_p95']:+.2f} beyond p95)  {'PASS' if c['passes'] else 'fail'}   [D446 p50 {d46['controls'][f'C1_{k}']['p50']:+.1f}]  ({(time.time()-t1)/60:.1f} min)", flush=True)

    # C2 -- exact common rotation, re-accounted
    def comb_gross(masks_, S_):
        g = np.zeros(T)
        for k, side in R46.SIDES.items():
            rr = R46.simulate(V59, P, masks_[k], S_, CAP, side, N_MAX); g += mark(A3, rr["trades"], beta, w, T)[0]
        return float(g[d0:t_end].mean())
    offs = list(range(step, T - step, step)); print(f"\n  C2 rotation: {len(offs)} offsets", flush=True); t1 = time.time(); rot = []
    for i, kof in enumerate(offs):
        Sr = np.roll(S, kof, axis=0); rot.append(comb_gross(R46.masks_from(Sr, elig), Sr))
        if (i + 1) % 40 == 0:
            print(f"    {i+1}/{len(offs)}  {(time.time()-t1)/60:.1f} min", flush=True)
    rot = np.array(rot); c2 = dict(n=len(offs), p50=float(np.median(rot)), p95=float(np.quantile(rot, .95)), passes=bool(bk["gross"] > np.quantile(rot, .95)), draws=rot.tolist()); res["controls"]["C2"] = c2
    print(f"    real {bk['gross']:+.3f}  C2 p50 {c2['p50']:+.3f}  p95 {c2['p95']:+.3f}  {'PASS' if c2['passes'] else 'fail'}   [D446 p50 {d46['controls']['C2']['p50']:+.3f} p95 {d46['controls']['C2']['p95']:+.3f}]", flush=True)

    # C3 -- persistent random selector, re-accounted
    M, first = R46.transition_matrix(S, df, symbols, elig); print(f"\n  C3 persistent random selector ({n_draw} draws)", flush=True); t1 = time.time(); c3 = []
    for d in range(n_draw):
        S3 = R46.c3_panel(rng, df, symbols, dates, T, M, first, elig); c3.append(comb_gross(R46.masks_from(S3, elig), S3))
    c3 = np.array(c3); c3d = dict(n=n_draw, p50=float(np.median(c3)), p95=float(np.quantile(c3, .95)), se=float(c3.std(ddof=1) / np.sqrt(n_draw)), sd=float(c3.std(ddof=1)))
    c3d["passes"] = bool(bk["gross"] > c3d["p95"] and (bk["gross"] - c3d["p95"]) >= 2 * c3d["se"]); res["controls"]["C3"] = c3d
    print(f"    real {bk['gross']:+.3f}  C3 p50 {c3d['p50']:+.3f}  p95 {c3d['p95']:+.3f} +- {c3d['se']:.3f}  {'PASS' if c3d['passes'] else 'fail'}   [D446 p50 {d46['controls']['C3']['p50']:+.3f} p95 {d46['controls']['C3']['p95']:+.3f}]   ({(time.time()-t1)/60:.1f} min)", flush=True)

    # the bar
    T1 = bool(c2["passes"] and c3d["passes"]); T2 = bool(bk["net_crossed"] > 0 and bk["net_crossed"] / bk["se"] >= 2); T3s = res["controls"]["C1_short"]["passes"]; T3l = res["controls"]["C1_long"]["passes"]
    T4 = bool(bk["era2"] > 0 and bk["era2"] / bk["era2_se"] >= 2); T5 = bool((bk["to_half"] or 0) >= 20 and bk["top1_share"] <= 50); res["bar"] = dict(T1=T1, T2=T2, T3_short=T3s, T3_long=T3l, T4=T4, T5=T5, candidate=bool(T1 and T2 and T3s and T4 and T5))
    print(f"\nTHE BAR (combined, beta-hedged, vol-scaled, cap {CAP}, n_max {N_MAX}, crossed)\n  T1 gross > C2 p95 and > C3 p95 by 2 SE : {T1}\n  T2 net crossed > 0 by 2 SE            : {T2}   ({bk['net_crossed']:+.3f} +- {bk['se']:.3f})\n  T3 short / long                        : {T3s} / {T3l}\n  T4 era-2 net > 0 by 2 SE               : {T4}   ({bk['era2']:+.3f} +- {bk['era2_se']:.3f})\n  T5 to-half >= 20 and top 1% <= 50%      : {T5}   ({bk['to_half']}, {bk['top1_share']:.0f}%)\n  CANDIDATE: {res['bar']['candidate']}")
    ss, sl = res["sides"]["short"], res["sides"]["long"]; gme = next((x for n, x in sl["conc"]["top_names"] if n == "GME"), 0.0)
    print("\nPREDICTIONS\n" + f"  X-b C2 p50 +0.2..+0.7 (within 0.4 of C3 p50), p95 +1.5..+2.6      : C2 p50 {c2['p50']:+.2f}  C3 p50 {c3d['p50']:+.2f}  C2 p95 {c2['p95']:+.2f}\n"
          + f"  X-c gross +1.2..+2.0, SE 0.9..1.2, net +0.3..+1.2, T2 fails       : gross {bk['gross']:+.2f} +- {bk['se']:.2f}  net {bk['net_crossed']:+.2f}  T2 {T2}\n"
          + f"  X-d to-half 12..25, top1% 30..55, GME < 15% of the long leg        : {bk['to_half']}, {bk['top1_share']:.0f}%, GME {gme:.0f}%\n"
          + f"  X-e C1 p50 short -30..0 / long -10..+20; real short +30..+70, long +80..+150 : C1 {res['controls']['C1_short']['p50']:+.1f} / {res['controls']['C1_long']['p50']:+.1f};  real {ss['wmean']:+.1f} / {sl['wmean']:+.1f}\n"
          + f"  X-f beta short > 1.2, long < 0.9; w short < 0.8, long > 1.1         : beta {ss['beta_mean']:.2f} / {sl['beta_mean']:.2f};  w {ss['w_mean']:.2f} / {sl['w_mean']:.2f}")
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min   (mining fixture only; no holdout read)")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) mark(): a hand-computed trade; beta=1, w=1 equals the unit-hedge sum; the entry bar uses ocT and mkt_oc")
    T = 10; r1T = np.zeros((T, 2)); r1T[:, 0] = [0.01, 0.02, -0.01, 0.03, 0.0, 0.01, 0.02, 0.0, 0.01, 0.0]; ocT = np.full((T, 2), 0.005); mkt = np.full(T, 0.004); mkt_oc = np.full(T, 0.002)
    A3 = dict(r1T=r1T, mkt=mkt, ocT=ocT, mkt_oc=mkt_oc); trades = [(0, 2, 3, 0.0, 0)]                         # long, entry bar 2, 3 bars
    beta = np.full((T, 2), 0.5); w = np.full((T, 2), 2.0); book, sx, W, pnl, wt, bt = mark(A3, trades, beta, w, T)
    want = (0.005 - 0.5 * 0.002) + (0.03 - 0.5 * 0.004) + (0.0 - 0.5 * 0.004); assert abs(pnl[0] - want * 1e4) < 1e-9 and W[2] == 2 and W[4] == 2 and W[5] == 0 and abs(book[3] - (0.03 - 0.002) * 1e4) < 1e-9
    b1, _, _, p1, _, _ = mark(A3, [(0, 2, 3, 0.0, 1)], np.ones((T, 2)), np.ones((T, 2)), T); assert abs(p1[0] + ((0.005 - 0.002) + (0.03 - 0.004) + (0.0 - 0.004)) * 1e4) < 1e-9, "short sign"
    print(f"  pnl {pnl[0]:+.2f} bp == hand {want*1e4:+.2f}; short pnl is the negative of the hedged move [SIGN]")
    print("== (b) beta_panel: r = 2m + noise -> beta ~ 2 from bar 253; causal (bar t reads <= t-1); clipped to [0, 3]; 1 where undefined")
    rng = np.random.default_rng(0); m = rng.normal(0, 0.01, 800); r = np.column_stack([2 * m + rng.normal(0, 0.005, 800), -5 * m, np.full(800, np.nan)]); b = beta_panel(r, m)
    assert abs(b[400, 0] - 2) < 0.15 and b[0, 0] == 1.0 and b[100, 0] == 1.0 and b[400, 1] == 0.0 and b[400, 2] == 1.0, b[400]
    r2 = r.copy(); r2[300, 0] += 5.0; b2 = beta_panel(r2, m); assert b2[300, 0] == b[300, 0] and b2[301, 0] != b[301, 0], "beta is not causal"
    print(f"  beta {b[400,0]:.3f} (target 2); -5 clipped to 0; NaN column -> 1; perturbing bar 300 moves beta[301] not beta[300]")
    print("== (c) weight_panel: w = median sigma / sigma, clipped [0.25, 4], causal")
    r = rng.normal(0, 1, (400, 60)) * np.linspace(0.5, 3.0, 60)[None, :] * 0.01; elig = np.ones((400, 60), bool); w, sig, med = weight_panel(r, elig)
    assert np.all(w[200] <= 4.0) and np.all(w[200] >= 0.25) and w[200, 0] > w[200, -1] and abs(np.median(w[200]) - 1) < 0.15 and np.all(w[:VOL_MIN] == 1.0)
    r2 = r.copy(); r2[250, 0] = 1.0; w2, _, _ = weight_panel(r2, elig); assert w2[250, 0] == w[250, 0] and w2[251, 0] != w[251, 0], "w is not causal"
    print(f"  median w {np.median(w[200]):.2f}; low-vol name w {w[200,0]:.2f} > high-vol {w[200,-1]:.2f}; causal")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    if a.run:
        run(a.quick)
    else:
        cmd_selftest()

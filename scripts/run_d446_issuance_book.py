"""D446 stage 1 -- net share issuance as a persistent state: the decile slot book both sides on D444's point-in-time EDGAR counts,
through the D345 kernel, with three controls. Spec committed in 84793d8 BEFORE this file. In-sample; no holdout.

    uv run python -u scripts/run_d446_issuance_book.py --run [--quick]     # --quick: 10 draws / 42-bar rotation grid, for debugging only
    uv run python -u scripts/run_d446_issuance_book.py --selftest

Score S[t, j]: cross-sectional percentile rank (0..100) of the latest fresh first-filed NS among eligible names at bar t. Persistent
masks: in_short = S >= 90, in_long = S <= 10, shifted one bar ([F], fill at the next open); the kernel skips names already held, so a
name in its decile is entered once, held `cap` bars, exited, and re-entered the next bar if still in the decile. n_max = 40 a side
(the kernel takes the most extreme ranks first). Controls: C1 state-matched names at the real entry days; C2 the score panel rolled
by one common offset for every name over a 21-bar grid (exact within the grid); C3 a persistent random selector with the panel's own
refresh dates and empirical decile transition matrix.
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
PANEL = REPO / "data" / "d444_issuance_panel.csv.gz"; OUT = REPO / "data" / "d446_issuance_book.json"
FRESH_DAYS = 200; SCALE_GUARD = math.log(50); TOP, BOT = 90.0, 10.0; CAP, N_MAX = 126, 40; CAPS_ROBUST = (63, 252); END = "2023-12-29"
N_DRAW = 100; ROT_STEP = 21; SEED = 446; CAPTURE, CHASE_BP = 0.66, 9.0; SIDES = {"short": 1, "long": 0}


# ------------------------------------------------------------------------------------------ the score panel
def latest_ns_panel(df, symbols, dates, T):
    """NS[t, j] = the latest first-filed NS available at bar t (t_av <= t) whose fiscal date is within FRESH_DAYS of bar t; NaN else."""
    sym_i = {s: i for i, s in enumerate(symbols)}; fix = pd.to_datetime(dates); N = len(symbols); NS = np.full((T, N), np.nan)
    d = df[np.isfinite(df["NS"]) & (df["t_av"] >= 0) & ~df["flag"].astype(bool)].copy()
    med = d.groupby("symbol")["so_raw"].transform("median"); d = d[np.abs(np.log(d["so_raw"] / med)) <= SCALE_GUARD]
    d = d.sort_values(["symbol", "t_av", "fiscal_date"])
    for s, g in d.groupby("symbol"):
        j = sym_i.get(s)
        if j is None:
            continue
        tv = g["t_av"].to_numpy(); ns = g["NS"].to_numpy(); exp_ = np.searchsorted(fix, pd.to_datetime(g["fiscal_date"]) + pd.Timedelta(days=FRESH_DAYS), side="right")
        for i in range(len(tv)):
            a = int(tv[i]); b = int(min(exp_[i], tv[i + 1] if i + 1 < len(tv) else T, T))
            if b > a:
                NS[a:b, j] = ns[i]
    return NS


def percentile_panel(NS, elig):
    """S[t, j] in [0, 100] among eligible names with a finite NS at bar t; NaN elsewhere."""
    T, N = NS.shape; S = np.full((T, N), np.nan)
    for t in range(T):
        m = elig[t] & np.isfinite(NS[t]); k = int(m.sum())
        if k < 30:
            continue
        idx = np.flatnonzero(m); order = np.argsort(NS[t, idx], kind="stable"); r = np.empty(k); r[order] = np.arange(k)
        S[t, idx] = 100.0 * r / (k - 1)
    return S


def shift(m, elig):
    s = np.zeros_like(m); s[1:] = m[:-1]; return s & elig


def masks_from(S, elig):
    return dict(short=shift(np.nan_to_num(S, nan=-1.0) >= TOP, elig), long=shift((S <= BOT) & np.isfinite(S), elig))


# ------------------------------------------------------------------------------------------ the kernel
def simulate(V59, P, mask, S, cap, side, n_max):
    z = V59.zeros(mask); sl, ss = (z, mask) if side == 1 else (mask, z)
    return V59.EB.simulate_event(P["A3"], sl, ss, S, exit="cap", cap=cap, n_max=n_max, x_target=V59.X_TARGET, U=V59.U_SLOTS, hedged_series=True)


def book_series(r):
    return np.nan_to_num(np.asarray(r["book_dep_x"], float)) * 1e4


def side_stats(V59, R38, P, elig, r, side, yr):
    tb = V59.trade_block(P, r, elig, side, False); db = V59.deployed_block(r, P); pnl = V59.V47.pnl_bp(r); borrow = tb.get("borrow", {}).get("mean_bp", 0.0)
    turn = db["PUB"]["hedged"]["turnover"]; crossed = db["PUB"]["hedged_2x"]["cost_bp"] + borrow * turn; passive = db["PUB"]["hedged_2x"]["cost_bp"] * (1 - CAPTURE) + CHASE_BP * turn + borrow * turn
    return dict(trades=tb["trades"], gross=tb["mean_bp"], median=tb["median_bp"], se=float(pnl.std(ddof=1) / np.sqrt(pnl.size)) if pnl.size > 1 else float("nan"), two_c_PUB=tb["two_c"]["PUB"], borrow=borrow,
                htb_share=tb.get("borrow", {}).get("htb_share"), net_PUB=tb["mean_bp"] - tb["two_c"]["PUB"] - borrow, hold=tb["hold_mean"], turnover=turn, dep_cost2=db["PUB"]["hedged_2x"]["cost_bp"],
                cost_crossed_bar=crossed, cost_passive_bar=passive, conc=R38.conc(r, pnl, P, yr), skipped=int(np.asarray(r.get("skipped", 0)).sum()) if "skipped" in r else None), pnl


def book_stats(R37, g, dates, d0, cost_crossed, cost_passive, T):
    """T here is the END bar of the book window (exclusive): bars [d0, T) -- nothing after the sample end is scored."""
    gs = g[d0:T]; ds = dates[d0:T]; se, mg = R37.block_boot(gs, ds); half = d0 + (T - d0) // 2; era2 = np.arange(d0, T) >= half; nc = gs - cost_crossed
    se2, m2 = R37.block_boot(nc[era2], ds[era2]); se1, m1 = R37.block_boot(nc[~era2], ds[~era2]); ys = np.array([int(x[:4]) for x in ds])
    return dict(gross=mg, se=se, cost_crossed=cost_crossed, cost_passive=cost_passive, net_crossed=float(mg - cost_crossed), net_passive=float(mg - cost_passive), sharpe_crossed=float(nc.mean() / nc.std(ddof=1) * np.sqrt(252)),
                era1=m1, era1_se=se1, era2=m2, era2_se=se2, era2_start=str(dates[half]), by_year={str(y): float(nc[ys == y].mean()) for y in np.unique(ys)})


# ------------------------------------------------------------------------------------------ controls
def entry_mask(r, T, N):
    ev = np.zeros((T, N), bool)
    for t in r["trades"]:
        ev[t[1], t[0]] = True
    return ev


def cells_of(A92, P, elig):
    tp = A92.tercile_pools(P, elig); out = []
    for a in ("lo", "mid", "hi"):
        for b in ("lo", "mid", "hi"):
            for c in ("lo", "mid", "hi"):
                out.append(tp[f"price_{a}"] & tp[f"vol_{b}"] & tp[f"mom_{c}"])
    return out


def c1_mask(R37, rng, ev, cells_shifted, pool_base):
    out = np.zeros_like(ev)
    for c in cells_shifted:
        e = ev & c
        if e.any():
            out |= R37.draw_state_matched(rng, e, c & pool_base, ev.shape[0])
    return out


def transition_matrix(S, df, symbols, elig):
    """10x10 decile transition between consecutive refreshes of the same name (rows sum to 1), and the occupancy at first refresh."""
    sym_i = {s: i for i, s in enumerate(symbols)}; M = np.zeros((10, 10)); first = np.zeros(10)
    d = df[(df["t_av"] >= 0)].sort_values(["symbol", "t_av"])
    for s, g in d.groupby("symbol"):
        j = sym_i.get(s)
        if j is None:
            continue
        tv = np.unique(g["t_av"].to_numpy()); dec = [int(min(9, S[t, j] // 10)) if (elig[t, j] and np.isfinite(S[t, j])) else -1 for t in tv]
        seen = False
        for a, b in zip(dec[:-1], dec[1:]):
            if a >= 0 and b >= 0:
                M[a, b] += 1
                if not seen:
                    first[a] += 1; seen = True
    M = M / np.maximum(M.sum(axis=1, keepdims=True), 1); first = first / max(first.sum(), 1)
    return M, first


def c3_panel(rng, df, symbols, dates, T, M, first, elig):
    """A random score panel with the real refresh dates and freshness, deciles following M; the value is uniform inside the decile."""
    sym_i = {s: i for i, s in enumerate(symbols)}; fix = pd.to_datetime(dates); S = np.full((T, len(symbols)), np.nan)
    d = df[(df["t_av"] >= 0)].sort_values(["symbol", "t_av"])
    for s, g in d.groupby("symbol"):
        j = sym_i.get(s)
        if j is None:
            continue
        tv = np.unique(g["t_av"].to_numpy()); fd = g.groupby("t_av")["fiscal_date"].max().reindex(tv).to_numpy()
        exp_ = np.searchsorted(fix, pd.to_datetime(fd) + pd.Timedelta(days=FRESH_DAYS), side="right"); dec = int(rng.choice(10, p=first))
        for i in range(len(tv)):
            if i:
                dec = int(rng.choice(10, p=M[dec]))
            a = int(tv[i]); b = int(min(exp_[i], tv[i + 1] if i + 1 < len(tv) else T, T))
            if b > a:
                S[a:b, j] = 10.0 * dec + rng.uniform(0, 10)
    S[~elig] = np.nan
    return S


# ------------------------------------------------------------------------------------------ the study
def run(quick=False):
    t0 = time.time(); print("D446 STAGE 1 -- net share issuance: the decile slot book both sides, three controls\n      the bar was committed in 84793d8 BEFORE this ran; mining fixture only; no holdout\n")
    PREP = _load("d348p", "d348_prep.py"); V59 = _load("d359r", "run_d359_loser_rally_short.py"); A92 = _load("d392", "run_d392_base_rate_atlas.py"); R37 = _load("d437", "run_d437_stage1.py"); R38 = _load("d438", "run_d438_cost_axes.py")
    P = PREP.prep(need_grids=True); T, N = P["T"], P["n"]; elig = np.asarray(P["elig"]); dates = np.array([str(x)[:10] for x in P["dates"]]); yr = np.array([int(x[:4]) for x in dates]); symbols = list(P["symbols"])
    R38.SC = np.full((T, N), 50.0); idx = A92.eligible_index(elig); mk = A92.draw_mask(np.random.default_rng(A92.SEED), idx, (T, N), 2_000)
    r1 = V59.run_mirror(P, mk, R38.SC, "cap", 20); m1, c1 = A92.score_once(V59, P, mk, 20, "long", R38.SC); assert abs(m1 - float(V59.V47.pnl_bp(r1).mean())) < 1e-12 and c1 == len(r1["trades"]), "[K]"
    t_end = int(np.searchsorted(dates, END, side="right")); elig = elig.copy(); elig[t_end:] = False              # nothing after 2023-12-29 is traded or scored
    df = pd.read_csv(PANEL, dtype={"fiscal_date": str, "avail_date": str, "symbol": str, "cik": str})
    NS = latest_ns_panel(df, symbols, dates, T); S = percentile_panel(NS, elig); masks = masks_from(S, elig)
    cover = np.isfinite(S).sum(axis=1); d0 = int(np.flatnonzero(cover >= 30)[0]); ndec = {k: masks[k].sum(axis=1)[d0:t_end].mean() for k in masks}
    print(f"  [K] kernel probe;  score panel: names with a fresh NS per bar: median {np.median(cover[d0:t_end]):.0f} (first bar with >= 30: {dates[d0]});  in-decile per bar: short {ndec['short']:.0f}  long {ndec['long']:.0f};  sample ends {END}")
    res = dict(spec="84793d8", d0=str(dates[d0]), end=END, names_per_bar=float(np.median(cover[d0:t_end])), sides={}, book={}, controls={}, robust={}, bar={}, quick=quick)
    n_draw = 10 if quick else N_DRAW; step = 42 if quick else ROT_STEP; rng = np.random.default_rng(SEED)

    # 1. the two sides and the combined book
    t1 = time.time(); R = {}; g_comb = np.zeros(T); cc = cp = 0.0
    for k, side in SIDES.items():
        r = simulate(V59, P, masks[k], S, CAP, side, N_MAX); st, pnl = side_stats(V59, R38, P, elig, r, side, yr); R[k] = r; res["sides"][k] = st
        g = book_series(r); g_comb += g; cc += st["cost_crossed_bar"]; cp += st["cost_passive_bar"]
        res["sides"][k]["book"] = book_stats(R37, g, dates, d0, st["cost_crossed_bar"], st["cost_passive_bar"], t_end)
        print(f"  {k:5s} per trade: n {st['trades']:,}  gross {st['gross']:+.1f} +- {st['se']:.1f}  median {st['median']:+.1f}  hold {st['hold']:.0f}  2c PUB {st['two_c_PUB']:.1f}  borrow {st['borrow']:.1f} (HTB {100*(st['htb_share'] or 0):.0f}%)  net {st['net_PUB']:+.1f}   |   book gross {res['sides'][k]['book']['gross']:+.3f}/bar  crossed {st['cost_crossed_bar']:.3f}  net {res['sides'][k]['book']['net_crossed']:+.3f}  turnover {st['turnover']:.4f}  to-half {st['conc']['to_half']}  top1% {st['conc']['top1_share']:.0f}%")
    t_sim = (time.time() - t1) / 2; print(f"  one kernel simulation: {t_sim:.1f} s")
    bk = book_stats(R37, g_comb, dates, d0, cc, cp, t_end); pn = np.concatenate([V59.V47.pnl_bp(R["short"]), V59.V47.pnl_bp(R["long"])]); tr = R["short"]["trades"] + R["long"]["trades"]
    by = {}
    for t, x in zip(tr, pn): by[t[0]] = by.get(t[0], 0.0) + float(x)
    v = np.sort(np.array(list(by.values())))[::-1]; tot = pn.sum(); kk = max(1, int(round(0.01 * pn.size)))
    bk["to_half"] = int(np.searchsorted(np.cumsum(v), 0.5 * tot) + 1) if tot > 0 else None; bk["top1_share"] = float(100 * np.sort(pn)[-kk:].sum() / tot) if tot > 0 else float("nan"); bk["names"] = len(by); res["book"] = bk
    print(f"  COMBINED book: gross {bk['gross']:+.3f} +- {bk['se']:.3f}/bar   crossed cost {cc:.3f} -> net {bk['net_crossed']:+.3f} ({bk['net_crossed']/bk['se']:+.1f} SE)  Sharpe {bk['sharpe_crossed']:+.2f}   passive cost {cp:.3f} -> net {bk['net_passive']:+.3f}   era1 {bk['era1']:+.3f} +- {bk['era1_se']:.3f}  era2 (from {bk['era2_start']}) {bk['era2']:+.3f} +- {bk['era2_se']:.3f}   names {bk['names']}  to-half {bk['to_half']}  top1% {bk['top1_share']:.0f}%")
    print("  by year (combined net crossed): " + " ".join(f"{y}:{x:+.1f}" for y, x in bk["by_year"].items()))

    # 2. C1 -- state-matched names at the real entry days, per side
    print(f"\n  C1 state-matched names ({n_draw} draws x 2 sides)", flush=True); t1 = time.time()
    cells = [shift(c, elig) for c in cells_of(A92, P, elig)]; pool_base = shift(~(np.nan_to_num(S, nan=50.0) >= TOP) & ~(S <= BOT) & elig, elig)
    for k, side in SIDES.items():
        ev = entry_mask(R[k], T, N); gs = []
        for d in range(n_draw):
            m = c1_mask(R37, rng, ev, cells, pool_base); rr = simulate(V59, P, m, R38.SC, CAP, side, None); gs.append(float(V59.V47.pnl_bp(rr).mean()))
        gs = np.array(gs); st = res["sides"][k]; c = dict(p50=float(np.median(gs)), p95=float(np.quantile(gs, .95)), se=float(gs.std(ddof=1) / np.sqrt(n_draw)), n=int(ev.sum()))
        c["increment"] = st["gross"] - c["p50"]; c["passes"] = bool(st["gross"] > c["p95"] and (st["gross"] - c["p95"]) >= 2 * c["se"]); res["controls"][f"C1_{k}"] = c
        print(f"    {k:5s}: real {st['gross']:+.1f}  C1 p50 {c['p50']:+.1f}  p95 {c['p95']:+.1f} +- {c['se']:.1f}  increment {c['increment']:+.1f}  {'PASS' if c['passes'] else 'fail'}   ({(time.time()-t1)/60:.1f} min)", flush=True)

    # 3. C2 -- the score panel rolled by a common offset, enumerated on the grid
    offs = list(range(step, T - step, step)); print(f"\n  C2 enumerated common rotation: {len(offs)} offsets x 2 sides (~{2*len(offs)*t_sim/60:.0f} min)", flush=True); t1 = time.time(); rot = []
    for i, kof in enumerate(offs):
        Sr = np.roll(S, kof, axis=0); mr = masks_from(Sr, elig); g = np.zeros(T)
        for k, side in SIDES.items():
            g += book_series(simulate(V59, P, mr[k], Sr, CAP, side, N_MAX))
        rot.append(float(g[d0:t_end].mean()))
        if (i + 1) % 20 == 0:
            print(f"    {i+1}/{len(offs)}  {(time.time()-t1)/60:.1f} min", flush=True)
    rot = np.array(rot); c2 = dict(n=len(offs), step=step, p50=float(np.median(rot)), p95=float(np.quantile(rot, .95)), passes=bool(bk["gross"] > np.quantile(rot, .95)), draws=rot.tolist()); res["controls"]["C2"] = c2
    print(f"    real {bk['gross']:+.3f}  C2 p50 {c2['p50']:+.3f}  p95 {c2['p95']:+.3f} (exact on the grid)  {'PASS' if c2['passes'] else 'fail'}", flush=True)

    # 4. C3 -- the persistent random selector
    M, first = transition_matrix(S, df, symbols, elig); res["controls"]["C3_transition_diag"] = [float(M[i, i]) for i in range(10)]
    print(f"\n  C3 persistent random selector ({n_draw} draws x 2 sides); decile self-transition per refresh: " + " ".join(f"{M[i,i]:.2f}" for i in range(10)), flush=True); t1 = time.time(); c3 = []
    for d in range(n_draw):
        S3 = c3_panel(rng, df, symbols, dates, T, M, first, elig); m3 = masks_from(S3, elig); g = np.zeros(T)
        for k, side in SIDES.items():
            g += book_series(simulate(V59, P, m3[k], S3, CAP, side, N_MAX))
        c3.append(float(g[d0:t_end].mean()))
    c3 = np.array(c3); c3d = dict(n=n_draw, p50=float(np.median(c3)), p95=float(np.quantile(c3, .95)), se=float(c3.std(ddof=1) / np.sqrt(n_draw)), passes=bool(bk["gross"] > np.quantile(c3, .95) and (bk["gross"] - np.quantile(c3, .95)) >= 2 * c3.std(ddof=1) / np.sqrt(n_draw))); res["controls"]["C3"] = c3d
    print(f"    real {bk['gross']:+.3f}  C3 p50 {c3d['p50']:+.3f}  p95 {c3d['p95']:+.3f} +- {c3d['se']:.3f}  {'PASS' if c3d['passes'] else 'fail'}   ({(time.time()-t1)/60:.1f} min)", flush=True)

    # 5. robustness lines (reported, not gated)
    print("\n  robustness (reported, not gated):")
    for lab, cap, nmax in (("cap63", 63, N_MAX), ("cap252", 252, N_MAX), ("nmax_none", CAP, None)):
        g = np.zeros(T); c_ = 0.0; n_ = 0
        for k, side in SIDES.items():
            r = simulate(V59, P, masks[k], S, cap, side, nmax); st, _ = side_stats(V59, R38, P, elig, r, side, yr); g += book_series(r); c_ += st["cost_crossed_bar"]; n_ += st["trades"]
        b = book_stats(R37, g, dates, d0, c_, c_, t_end); res["robust"][lab] = dict(trades=n_, gross=b["gross"], se=b["se"], net_crossed=b["net_crossed"])
        print(f"    {lab:10s} trades {n_:,}  gross {b['gross']:+.3f} +- {b['se']:.3f}  net crossed {b['net_crossed']:+.3f}")

    # 6. the bar
    T1 = bool(c2["passes"] and c3d["passes"]); T2 = bool(bk["net_crossed"] > 0 and bk["net_crossed"] / bk["se"] >= 2); T3s = res["controls"]["C1_short"]["passes"]; T3l = res["controls"]["C1_long"]["passes"]
    T4 = bool(bk["era2"] > 0 and bk["era2"] / bk["era2_se"] >= 2); T5 = bool((bk["to_half"] or 0) >= 20 and bk["top1_share"] <= 50)
    res["bar"] = dict(T1=T1, T2=T2, T3_short=T3s, T3_long=T3l, T4=T4, T5=T5, candidate=bool(T1 and T2 and T3s and T4 and T5))
    print(f"\nTHE BAR (combined, cap {CAP}, n_max {N_MAX}, crossed)\n  T1 gross > C2 p95 (exact) and > C3 p95 by 2 SE : {T1}\n  T2 net crossed > 0 by 2 SE                      : {T2}   ({bk['net_crossed']:+.3f} +- {bk['se']:.3f})\n  T3 per-trade gross > C1 p95 by 2 SE, short / long: {T3s} / {T3l}\n  T4 era-2 net crossed > 0 by 2 SE                : {T4}   ({bk['era2']:+.3f} +- {bk['era2_se']:.3f})\n  T5 >= 20 names to half and top 1% <= 50%        : {T5}   ({bk['to_half']}, {bk['top1_share']:.0f}%)\n  CANDIDATE for the holdouts: {res['bar']['candidate']}")
    ss, sl = res["sides"]["short"], res["sides"]["long"]
    print("\nPREDICTIONS\n" + f"  X-a short +40..+120 per trade, long +20..+60, short median < mean : short {ss['gross']:+.1f} (median {ss['median']:+.1f})  long {sl['gross']:+.1f} (median {sl['median']:+.1f})\n"
          + f"  X-b combined gross +1.5..+3.5, SE 1.2-1.6, net +0.5..+2.5, short > long: gross {bk['gross']:+.2f} +- {bk['se']:.2f}  net {bk['net_crossed']:+.2f};  short book {ss['book']['gross']:+.2f}  long book {sl['book']['gross']:+.2f}\n"
          + f"  X-c C1 p50 ~ 0 both sides; C2 p50 ~ 0, p95 +1.5..+2.5; C3 p95 within 0.5 of C2 : C1 {res['controls']['C1_short']['p50']:+.1f} / {res['controls']['C1_long']['p50']:+.1f};  C2 {c2['p50']:+.2f} / {c2['p95']:+.2f};  C3 p95 {c3d['p95']:+.2f}\n"
          + f"  X-d T1 passes C2, coin on C3; T3 short pass, long marginal; T5 pass; T4 fail : C2 {c2['passes']} C3 {c3d['passes']}; T3 {T3s}/{T3l}; T5 {T5}; T4 {T4}\n"
          + f"  X-e cap63 within 30% of cap126; cap252 lower; nmax None 20-40% lower : cap63 {res['robust']['cap63']['gross']:+.2f}  cap252 {res['robust']['cap252']['gross']:+.2f}  none {res['robust']['nmax_none']['gross']:+.2f} vs {bk['gross']:+.2f}\n"
          + f"  X-f short HTB > 20%, borrow > 5, 2c 60-90                            : HTB {100*(ss['htb_share'] or 0):.0f}%  borrow {ss['borrow']:.1f}  2c {ss['two_c_PUB']:.1f}")
    OUT.write_text(json.dumps(res, indent=1, default=float)); print(f"\nwrote {OUT.relative_to(REPO)}   {(time.time()-t0)/60:.1f} min   (mining fixture only; no holdout read)")


# ------------------------------------------------------------------------------------------ selftest
def cmd_selftest():
    t0 = time.time(); print("== (a) the score panel: availability, freshness, the next refresh supersedes, percentile ranks, the shift")
    dates = np.array([str(d.date()) for d in pd.bdate_range("2015-01-01", "2016-12-31")]); T = dates.size; syms = ["A", "B", "C"] + [f"N{i}" for i in range(40)]; N = len(syms); elig = np.ones((T, N), bool)
    rows = [dict(symbol="A", fiscal_date="2015-03-31", t_av=100, NS=0.5, flag=False, so_raw=100.0), dict(symbol="A", fiscal_date="2015-06-30", t_av=160, NS=-0.5, flag=False, so_raw=100.0), dict(symbol="B", fiscal_date="2015-03-31", t_av=100, NS=0.0, flag=True, so_raw=100.0),
            dict(symbol="C", fiscal_date="2015-03-31", t_av=100, NS=0.1, flag=False, so_raw=100.0), dict(symbol="C", fiscal_date="2015-06-30", t_av=160, NS=0.2, flag=False, so_raw=1e9),
            dict(symbol="C", fiscal_date="2015-09-30", t_av=250, NS=0.3, flag=False, so_raw=100.0), dict(symbol="C", fiscal_date="2015-12-31", t_av=300, NS=0.3, flag=False, so_raw=100.0), dict(symbol="C", fiscal_date="2016-03-31", t_av=350, NS=0.3, flag=False, so_raw=100.0)]
    rows += [dict(symbol=f"N{i}", fiscal_date="2015-03-31", t_av=100, NS=0.01 * i, flag=False, so_raw=100.0) for i in range(40)]
    df = pd.DataFrame(rows); NS = latest_ns_panel(df, syms, dates, T)
    assert np.isnan(NS[99, 0]) and NS[100, 0] == 0.5 and NS[159, 0] == 0.5 and NS[160, 0] == -0.5 and np.isnan(NS[:, 1]).all()
    exp_a = int(np.searchsorted(pd.to_datetime(dates), pd.Timestamp("2015-06-30") + pd.Timedelta(days=FRESH_DAYS), side="right")); assert NS[exp_a - 1, 0] == -0.5 and np.isnan(NS[exp_a, 0])
    assert NS[100, 2] == 0.1 and NS[160, 2] == 0.1 and NS[250, 2] == 0.3, "the scale guard did not drop the 1e9 row (it must not supersede the prior value)"
    S = percentile_panel(NS, elig); assert S[100, 0] == 100.0 and S[160, 0] == 0.0 and np.isnan(S[50]).all() and abs(np.nanmax(S[100]) - 100) < 1e-9 and abs(np.nanmin(S[100])) < 1e-9
    m = masks_from(S, elig); assert m["short"][101, 0] and not m["short"][100, 0] and m["long"][161, 0] and not m["long"][160, 0], "[F] the mask is not shifted one bar"
    print("  ok: A visible from its t_av, superseded at the next refresh, expires 200 d after fiscal; B flagged out; C's 1e9 row guarded; S in [0,100]; masks shifted [F]")
    print("== (b) C3 transition matrix rows sum to 1; a diagonal matrix keeps every name in its decile; the random panel respects the real refresh dates")
    M = np.eye(10); first = np.full(10, 0.1); rng = np.random.default_rng(1); S3 = c3_panel(rng, df, syms, dates, T, M, first, elig)
    dec_a = np.unique(np.floor(S3[100:exp_a, 0] / 10)); assert dec_a.size == 1 and np.isnan(S3[99, 0]) and np.isnan(S3[exp_a, 0])
    M2, f2 = transition_matrix(S, df, syms, elig); assert np.allclose(M2.sum(axis=1)[M2.sum(axis=1) > 0], 1.0) and abs(f2.sum() - 1) < 1e-9
    print("  ok")
    print("== (c) C2 with offset 0 reproduces the real masks; C1 never draws a decile name and matches daily counts")
    assert all(np.array_equal(masks_from(np.roll(S, 0, axis=0), elig)[k], m[k]) for k in m)
    ev = np.zeros((T, N), bool); ev[101, 0] = True; ev[101, 5] = True; cells = [elig.copy()]; pool = shift(~(np.nan_to_num(S, nan=50.0) >= TOP) & ~(S <= BOT) & elig, elig)
    R37 = _load("d437", "run_d437_stage1.py"); c = c1_mask(R37, np.random.default_rng(2), ev, cells, pool); assert c[101].sum() == 2 and not c[101, 0] and not (c & m["short"]).any() and not (c & m["long"]).any()
    print("  ok")
    print(f"SELFTEST PASSED in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); g = ap.add_mutually_exclusive_group(required=True); g.add_argument("--run", action="store_true"); g.add_argument("--selftest", action="store_true"); ap.add_argument("--quick", action="store_true")
    a = ap.parse_args()
    if a.run:
        run(a.quick)
    else:
        cmd_selftest()

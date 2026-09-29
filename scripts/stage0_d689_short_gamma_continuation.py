"""D689 STAGE 0 -- short-gamma continuation on ES, with volatility controlled: is D684's post-hoc lead a gamma effect or
a volatility effect, is it one episode, and could it be confirmed? In-sample development on D688's panel (2016-01-05 ->
2023-12-29), plus a conditioner-only premise count on 2024-01 -> 2025-02. A go/no-go for a pre-registration, not a
verdict (the principal: "go after short-gamma days with volatility is controlled").

    uv run python scripts/stage0_d689_short_gamma_continuation.py --run --data-root "<main checkout>/data"

THE OBJECT (from D684 section 4, fixed here before the run). At each decision time t = 09:30 + j*h (t + h <= 16:00), on
a day whose G_SUM (D688: SPX GEX + the ES options book at the prior settlement, known before the open) is < 0:
  m = log P(t) - log P(t-h) (bp); hold sign(m) for h minutes; gross g = sign(m) * (P(t+h) - P(t)).
PRIMARY CELL: h = 60, k = 0 (every decision time with m != 0). Secondary: h = 30; k = 0.5 (|m| >= 0.5 sigma_h).

DECLARED STATISTICS
  V  VOLATILITY CONTROL (the principal's condition). A continuation that is merely a high-volatility effect would also
     appear on long-gamma days of the same volatility. So:
     V1  stratified difference: within deciles of the day's realised 5-minute variance up to t (known at t), the mean
         continuation g (bp) on short-gamma rows minus that on long-gamma rows, weighted by the short-gamma rows per
         decile. It is ranked against the enumerated day-rotation null of the short-gamma label (k = 10 .. n-10,
         p95 SE 0).
     V2  the same stratified on trailing sigma_d deciles instead.
     V3  a day-clustered regression of g on the short dummy with log rv_t, log sigma_d^2 and |m|/sigma_h as controls.
  C  CONCENTRATION: short-gamma gross per trade by year; without 2020-02-20 -> 04-30, without 2020, without 2022,
     without the top 1 % of trades; the top five trades named.
  B  THE BOOKS (component line, CLAUDE.md's four groups): 1 MES ($4.42) and 1 full ES ($19.24), unfiltered and with
     the expected-profit filter (a prior-only through-origin pass-through of g on |m| over short-gamma rows of EARLIER
     days, a 250-session burn-in, trade when the projected gross >= 2 x the round trip); the daily net and gross Sharpe
     and Sortino, rho with the admitted MACD arm.
  P  THE CONFIRMATION PREMISE: the number of short-gamma sessions (G_SUM < 0; and SPX-only, ES-only) in 2024-01-02 ->
     2025-02-28, from SqueezeMetrics GEX and the ES options OI and settlements ONLY. No ES bar, no intraday price and no
     return on or after 2024-01-01 is read, and nothing on or after 2025-03-01 (the vault) at all. From that count and
     the in-sample per-trade mean and sd without the crash window: the expected t on that slice (the power rule wants
     >= 1.5 before a slice is spent).
GO / NO-GO for a pre-registration (declared here):
  GO if (1) V1 at the primary cell is > 0 and above its rotation p95; (2) the primary cell's short-gamma gross per
  trade is > 0 without 2020-02-20 -> 04-30 AND without 2022, and > 0 in at least half the years with >= 20 trades;
  (3) P's expected t >= 1.5.
  "UNCONFIRMABLE ON THE CLEAN SLICE" if (1) and (2) pass but (3) fails (the vault is for the joint run only).
  Otherwise NO-GO.

Output data/d689_short_gamma_continuation.json: statistics only, no per-date GEX (SqueezeMetrics, under the permission
of 2026-09-28).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage0_d688_gamma_close as S  # noqa: E402  (D688's committed runner; importing it defines, never runs)

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d689_short_gamma_continuation.json"
D688_JSON = REPO / "data" / "d688_gamma_close.json"
PREMISE_FROM, PREMISE_TO, VAULT_FROM = "2024-01-01", "2025-02-28", "2025-03-01"
HORIZONS = (60, 30)
KS = (0.0, 0.5)
PRIMARY = (60, 0.0)
CRASH = ("2020-02-20", "2020-04-30")
N_STRATA = 10
ROT_BLOCK = 200
POWER_T = 1.5


def P(*a, **k):
    print(*a, **k, flush=True)


# ------------------------------------------------------------------ the premise reader (conditioner only; no returns)
_PW: dict = {}


def _init_premise(fx, strip_es, tcal, refs):
    _PW.update(m=S.d581(Path(fx)), fx=Path(fx), strip=strip_es, tcal=tcal, refs=refs)


def _work_premise(mine):
    mine = set(mine)
    parts = []
    for ch in pd.read_csv(_PW["fx"] / "fut_es_options_eod.csv.gz", usecols=S.OPT_COLS, dtype=S.OPT_DTYPE, chunksize=S.CHUNK, encoding="utf-8"):
        ch = ch[ch["session"].isin(mine)]
        if len(ch):
            parts.append(ch)
    opts = pd.concat(parts, ignore_index=True)
    if (opts["session"] >= VAULT_FROM).any():
        raise S.GateError("[SEAL] an option row from the vault reached the premise reader")
    if not S.oi_keyed(opts, 0):
        raise S.GateError("[LAG] an option row's OI was published after 10:00 of its session")
    return S.es_book_prior(opts, _PW["strip"], _PW["tcal"], _PW["refs"], _PW["m"])


def premise_count(data_root: Path, tcal: np.ndarray, log=P) -> dict:
    fx = data_root / "fixtures"
    st = pd.read_csv(fx / "fut_settle_strip.csv.gz", dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    st = st[(st["root"] == "ES") & (st["ref"] >= "2023-11-01") & (st["ref"] <= PREMISE_TO)].reset_index(drop=True)
    if (st["ref"] >= VAULT_FROM).any():
        raise S.GateError("[SEAL] a vault settlement reached the premise reader")
    dix = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", usecols=["date", "gex"], dtype={"date": str}, encoding="utf-8")
    dix = dix[(dix["date"] >= "2023-11-01") & (dix["date"] <= PREMISE_TO)].sort_values("date").reset_index(drop=True)
    days = np.array([d for d in tcal if PREMISE_FROM <= d <= PREMISE_TO])
    refs = np.array(sorted(st["ref"].unique()))
    strides = [days[i::S.N_WORKERS].tolist() for i in range(S.N_WORKERS)]
    with ProcessPoolExecutor(max_workers=S.N_WORKERS, initializer=_init_premise, initargs=(str(fx), st, tcal, refs)) as ex:
        book = pd.concat(list(ex.map(_work_premise, strides))).sort_index()
    dd = dix["date"].to_numpy().astype(str)
    j = np.searchsorted(dd, days) - 1
    g_spx = pd.Series(dix["gex"].to_numpy(float)[j], index=days)
    g_es = book["G_ES"].reindex(days)
    g = g_spx + g_es
    ok = np.isfinite(g.to_numpy())
    mon = pd.Series(days).str[:7].to_numpy()
    out = {"sessions": int(len(days)), "sessions_with_both_books": int(ok.sum()),
           "short_gamma_sessions": {"G_SUM": int((g[ok] < 0).sum()), "G_SPX": int((g_spx < 0).sum()), "G_ES": int((g_es[ok] < 0).sum())},
           "short_gamma_by_month_G_SUM": {mm: int(((g < 0).to_numpy() & (mon == mm)).sum()) for mm in sorted(set(mon))},
           "reads": "SqueezeMetrics GEX and ES options OI/settlements and ES settlements, 2023-11 -> 2025-02-28; no ES bar, no intraday price, no return; nothing from 2025-03-01"}
    log(f"  PREMISE 2024-01 -> 2025-02: {out['sessions']} sessions ({out['sessions_with_both_books']} with both books); short gamma: SUM {out['short_gamma_sessions']['G_SUM']}, "
        f"SPX {out['short_gamma_sessions']['G_SPX']}, ES {out['short_gamma_sessions']['G_ES']}")
    return out


# ------------------------------------------------------------------ the vol-stratified difference, batched over rotations
def stratified_diff(g, strata, day_idx, short_day, ks):
    """For each rotation k of the day-level short label: sum over strata of n_short(s) * (mean_short(s) - mean_long(s)),
    divided by the total short rows. Column 0 is k = 0."""
    n_days = len(short_day)
    O = np.zeros((len(g), N_STRATA))
    O[np.arange(len(g)), strata] = 1.0
    sum_all = O.T @ g
    cnt_all = O.sum(0)
    out = np.empty(len(ks))
    for s in range(0, len(ks), ROT_BLOCK):
        kb = ks[s:s + ROT_BLOCK]
        rot = short_day[(np.arange(n_days)[:, None] - kb[None, :]) % n_days]     # days x block
        Sh = rot[day_idx]                                                        # rows x block
        cs = O.T @ Sh
        ss = O.T @ (Sh * g[:, None])
        cl = cnt_all[:, None] - cs
        sl = sum_all[:, None] - ss
        with np.errstate(invalid="ignore", divide="ignore"):
            d = ss / cs - sl / cl
        d = np.where((cs > 0) & (cl > 0), d, 0.0)
        w = np.where((cs > 0) & (cl > 0), cs, 0.0)
        out[s:s + len(kb)] = (w * d).sum(0) / w.sum(0)
    return out


def clustered(y, cols, groups):
    X = sm.add_constant(np.column_stack(cols))
    return sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})


def four_groups(tr_gross, tr_net, tr_day, tr_side, days, n_days, arm, cost):
    E = S.d685()
    daily_n = np.bincount(tr_day, weights=tr_net, minlength=n_days)
    daily_g = np.bincount(tr_day, weights=tr_gross, minlength=n_days)
    nt = len(tr_net)
    yrs = n_days / 252.0
    out = {"trades": nt, "trades_per_year": nt / yrs, "days_traded": int((np.bincount(tr_day, minlength=n_days) > 0).sum()), "cost_rt_usd": cost}
    if nt < 5:
        return out
    out["net"] = {"sharpe_daily": E.sharpe(daily_n), "sortino_daily": E.sortino(daily_n), "total_usd": float(tr_net.sum()), "mean_per_trade_usd": float(tr_net.mean()),
                  "vol_ann_usd": float(daily_n.std(ddof=1) * math.sqrt(252)), "max_dd_usd": E.max_dd(daily_n)}
    out["gross"] = {"sharpe_daily": E.sharpe(daily_g), "sortino_daily": E.sortino(daily_g), "total_usd": float(tr_gross.sum()), "mean_per_trade_usd": float(tr_gross.mean())}
    out["mean_gross_vs_2c"] = float(tr_gross.mean() / (2 * cost))
    out["breakeven_cost_rt_usd"] = float(tr_gross.mean())
    out["hit_rate_net"] = float((tr_net > 0).mean())
    out["trade_distribution_net_usd"] = E.dist(tr_net)
    out["long_short_net_usd"] = {"long": float(tr_net[tr_side > 0].sum()), "short": float(tr_net[tr_side < 0].sum())}
    yr = np.array([days[d][:4] for d in tr_day])
    out["by_year_net_usd"] = {y: float(tr_net[yr == y].sum()) for y in sorted(set(yr))}
    srt = np.sort(tr_net)[::-1]
    tot = float(tr_net.sum())
    out["top_share_of_net"] = {str(k): (float(srt[:k].sum() / tot) if tot > 0 else None) for k in (1, 5, 10)}
    if arm is not None:
        pos = {d: i for i, d in enumerate(days)}
        x = np.array([daily_n[pos[d]] if d in pos else 0.0 for d in arm["days"]])
        out["rho_with_macd_arm"] = float(np.corrcoef(x, arm["net"])[0, 1]) if x.std() > 0 else float("nan")
    return out


# ------------------------------------------------------------------ run
def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    m581 = S.d581(data_root / "fixtures")
    I = S.load_inputs(data_root, log)
    es581 = m581.load_es(lambda *a: None)
    strip_es = I["strip"]
    refs = np.array(sorted(strip_es["ref"].unique()))
    win = [d for d in I["days"] if d >= S.IN_FROM]
    strides = [win[i::S.N_WORKERS] for i in range(S.N_WORKERS)]
    with ProcessPoolExecutor(max_workers=S.N_WORKERS, initializer=S._init, initargs=(str(I["fx"]), es581, strip_es, I["cal"], I["tcal"], refs)) as ex:
        futs = [ex.submit(S._work, (s, [])) for s in strides]
        Dfull = S.build_panel(I, log)
        outs = [f.result() for f in futs]
    prior = pd.concat([o["prior"] for o in outs]).sort_index()
    D = Dfull.join(prior[["G_ES"]], how="left")
    D = D[D.index >= S.IN_FROM]
    D["G_SUM"] = D["G_SPX"] + D["G_ES"]
    need = ["P1530", "P1600", "P1100", "P1130", "P1550", "S_prev", "sig", "V", "G_SPX", "G_ES", "A_L"] + ["P" + t.replace(":", "") for t in S.CLOCK]
    D = D[np.isfinite(D[need].to_numpy(float)).all(1)]
    S.guard_window(D.index, "D689 panel")
    days = D.index.to_numpy().astype(str)
    nd = len(days)
    sig = D["sig"].to_numpy(float); G = D["G_SUM"].to_numpy(float)
    r = 100 * np.log(D["P1530"].to_numpy(float) / D["S_prev"].to_numpy(float)); R2 = 1e4 * np.log(D["P1600"].to_numpy(float) / D["P1530"].to_numpy(float))
    f688, _ = S.gamma_regression(R2, G, r, sig, D["V"].to_numpy(float), D["A_L"].to_numpy(float), null=False)
    ref = json.loads(D688_JSON.read_text(encoding="utf-8"))["gate1"]["G1"]["beta_G"]
    if f688["beta_G"] != ref:
        raise S.GateError(f"[REPRO] beta_G {f688['beta_G']!r} vs D688's {ref!r}")
    log(f"  D688 REPRODUCED: beta_G {f688['beta_G']!r} on {nd} sessions ({time.time() - t0:.0f} s)")

    # 5-minute grid, as D684
    b = I["bars"]
    b = b[b["day"].isin(set(days))]
    close = b.pivot(index="day", columns="hhmm", values="close").reindex(days)
    op = b[b["hhmm"] == "09:30"].set_index("day")["open"].reindex(days).to_numpy(float)
    grid = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=5 * k)) for k in range(79)]
    PG = np.column_stack([op] + [close[(g - pd.Timedelta(minutes=1)).strftime("%H:%M")].to_numpy(float) for g in grid[1:]])
    L = np.log(PG)
    r5 = 1e4 * np.diff(L, axis=1)
    cum_rv = np.concatenate([np.full((nd, 1), np.nan), np.cumsum(r5 * r5, axis=1)], axis=1)
    short_day = (G < 0).astype(float)
    lsig2 = np.log(sig ** 2)
    E = S.d685()
    mes, esf = E.cost_spec("ES", "micro"), E.cost_spec("ES", "full")
    arm = E.load_arm()
    ks_rot = S.rot_ks(nd)
    in_crash = (days >= CRASH[0]) & (days <= CRASH[1])
    yr_day = np.array([d[:4] for d in days])
    res = {"spec": "D689 STAGE 0 (in-sample development + conditioner-only premise; a go/no-go, not a verdict)",
           "reproduction": {"beta_G": f688["beta_G"], "exact": True, "sessions": nd}, "costs": {"mes": mes, "es_full": esf}, "cells": {}}
    for h in HORIZONS:
        step = h // 5
        js = [j for j in range(step, 79) if j % step == 0 and j + step <= 78]
        rows = []
        for j in js:
            with np.errstate(divide="ignore", invalid="ignore"):
                lrv = np.log(cum_rv[:, j] / j)
            rows.append(pd.DataFrame({"di": np.arange(nd), "m": 1e4 * (L[:, j] - L[:, j - step]), "f": 1e4 * (L[:, j + step] - L[:, j]),
                                      "dp": PG[:, j + step] - PG[:, j], "P": PG[:, j], "lrv": lrv}))
        T = pd.concat(rows, ignore_index=True)
        T = T[np.isfinite(T[["m", "f", "dp", "lrv", "P"]].to_numpy()).all(1) & (T["m"] != 0)].reset_index(drop=True)
        di = T["di"].to_numpy(); m = T["m"].to_numpy(); f = T["f"].to_numpy(); dp = T["dp"].to_numpy(); lrv = T["lrv"].to_numpy()
        side = np.sign(m); g = side * f
        sg_h = sig[di] * math.sqrt(h / 390.0)
        sh = short_day[di] > 0
        for k in KS:
            sel = np.abs(m) >= k * sg_h
            gi, dii, lrvi, mi = g[sel], di[sel], lrv[sel], m[sel]
            C = {"rows": int(sel.sum()), "short_rows": int((sh & sel).sum())}
            # ---- V: volatility control ----
            q_rv = np.minimum((pd.Series(lrvi).rank(pct=True).to_numpy() * N_STRATA).astype(int), N_STRATA - 1)
            v1 = stratified_diff(gi, q_rv, dii, short_day, ks_rot)
            q_sg = np.minimum((pd.Series(lsig2[dii]).rank(pct=True).to_numpy() * N_STRATA).astype(int), N_STRATA - 1)
            v2 = stratified_diff(gi, q_sg, dii, short_day, ks_rot)
            v3 = clustered(gi, [short_day[dii], lrvi, lsig2[dii], np.abs(mi) / sg_h[sel]], dii)
            C["V1_stratified_by_same_day_rv_bp"] = S.blk(v1[0], v1[1:])
            C["V2_stratified_by_trailing_sigma_bp"] = S.blk(v2[0], v2[1:])
            C["V3_regression_short_dummy_bp"] = {"beta": float(v3.params[1]), "t": float(v3.tvalues[1]), "n": int(len(gi))}
            C["raw_gross_bp"] = {"short": float(gi[short_day[dii] > 0].mean()), "long": float(gi[short_day[dii] == 0].mean())}
            C["by_rv_decile_short_minus_long_bp"] = {int(q): {"short": float(gi[(q_rv == q) & (short_day[dii] > 0)].mean()) if ((q_rv == q) & (short_day[dii] > 0)).any() else None,
                                                              "long": float(gi[(q_rv == q) & (short_day[dii] == 0)].mean()) if ((q_rv == q) & (short_day[dii] == 0)).any() else None,
                                                              "n_short": int(((q_rv == q) & (short_day[dii] > 0)).sum())} for q in range(N_STRATA)}
            # ---- C: concentration (short-gamma trades) ----
            st = sh & sel
            gm = side[st] * dp[st] * mes["usd_per_point"]
            dst = di[st]
            yr = yr_day[dst]
            cr = in_crash[dst]
            def mt(x, grp):
                if len(x) < 10:
                    return {"n": int(len(x))}
                rr = sm.OLS(x, np.ones((len(x), 1))).fit(cov_type="cluster", cov_kwds={"groups": grp})
                return {"n": int(len(x)), "mean_gross_mes_usd": float(rr.params[0]), "t": float(rr.tvalues[0])}
            top = np.abs(gm) >= np.quantile(np.abs(gm), 0.99)
            C["C_concentration"] = {"all": mt(gm, dst), "ex_crash_2020_02_20_to_04_30": mt(gm[~cr], dst[~cr]), "ex_2020": mt(gm[yr != "2020"], dst[yr != "2020"]),
                                    "ex_2022": mt(gm[yr != "2022"], dst[yr != "2022"]), "ex_top1pct_abs": mt(gm[~top], dst[~top]),
                                    "by_year": {y: mt(gm[yr == y], dst[yr == y]) for y in sorted(set(yr))},
                                    "top5": [{"session": str(days[dst[i]]), "gross_mes_usd": float(gm[i])} for i in np.argsort(-np.abs(gm))[:5]]}
            byy = C["C_concentration"]["by_year"]
            elig = [y for y, v in byy.items() if v["n"] >= 20]
            pos_years = sum(1 for y in elig if byy[y]["mean_gross_mes_usd"] > 0)
            C["C_years_positive"] = {"eligible": len(elig), "positive": pos_years}
            # ---- B: books (unfiltered and EP-filtered), MES and full ES ----
            books = {}
            for lab, cs in (("mes", mes), ("es_full", esf)):
                gr = side[st] * dp[st] * cs["usd_per_point"]
                books[f"unfiltered_{lab}"] = four_groups(gr, gr - cs["cost_rt_usd"], dst, side[st], days, nd, arm, cs["cost_rt_usd"])
                # prior-only pass-through over short-gamma rows of EARLIER days; burn-in 250 sessions
                order = np.argsort(dst, kind="stable")
                x_bp = np.abs(m[st])[order]; y_bp = g[st][order]; dd = dst[order]
                cxy = np.cumsum(x_bp * y_bp); cxx = np.cumsum(x_bp * x_bp)
                first = np.searchsorted(dd, dd, side="left")                    # rows of earlier days only
                pxy = np.where(first > 0, cxy[np.maximum(first - 1, 0)], 0.0); pxx = np.where(first > 0, cxx[np.maximum(first - 1, 0)], 0.0)
                with np.errstate(invalid="ignore", divide="ignore"):
                    pi = pxy / pxx
                proj = pi * x_bp / 1e4 * T["P"].to_numpy()[st][order] * cs["usd_per_point"]
                take = (dd >= S.BURN) & np.isfinite(pi) & (proj >= S.K_EP * cs["cost_rt_usd"])
                gr_o = gr[order]
                books[f"ep_filtered_{lab}"] = four_groups(gr_o[take], gr_o[take] - cs["cost_rt_usd"], dd[take], side[st][order][take], days, nd, arm, cs["cost_rt_usd"])
                # the audit: pi at sampled rows re-derived by a loop over strictly earlier days
                for i in np.linspace(0, len(dd) - 1, 6).astype(int):
                    prv = dd < dd[i]
                    ref_pi = (x_bp[prv] * y_bp[prv]).sum() / (x_bp[prv] ** 2).sum() if prv.any() else np.nan
                    if not ((np.isnan(ref_pi) and np.isnan(pi[i])) or np.isclose(ref_pi, pi[i], rtol=1e-9)):
                        raise S.GateError(f"[PRIOR-ONLY] row {i}: pi {pi[i]!r} vs the loop's {ref_pi!r}")
            C["books"] = books
            res["cells"][f"h{h}_k{k}"] = C
            cc = C["C_concentration"]
            log(f"  h{h} k{k}: rows {C['rows']} (short {C['short_rows']}); raw gross bp short {C['raw_gross_bp']['short']:+.2f} long {C['raw_gross_bp']['long']:+.2f}")
            log(f"     V1 same-day-rv stratified short-long {C['V1_stratified_by_same_day_rv_bp']['observed']:+.2f} bp (p50 {C['V1_stratified_by_same_day_rv_bp']['p50']:+.2f}, p95 {C['V1_stratified_by_same_day_rv_bp']['p95']:+.2f}, "
                f"pct {C['V1_stratified_by_same_day_rv_bp']['pct_rank']:.3f}); V2 sigma-stratified {C['V2_stratified_by_trailing_sigma_bp']['observed']:+.2f} (pct {C['V2_stratified_by_trailing_sigma_bp']['pct_rank']:.3f}); "
                f"V3 {C['V3_regression_short_dummy_bp']['beta']:+.2f} bp (t {C['V3_regression_short_dummy_bp']['t']:+.2f})")
            log(f"     C: all ${cc['all'].get('mean_gross_mes_usd', float('nan')):+.2f} (t {cc['all'].get('t', float('nan')):+.2f}, n {cc['all']['n']}); ex-crash ${cc['ex_crash_2020_02_20_to_04_30'].get('mean_gross_mes_usd', float('nan')):+.2f} "
                f"(t {cc['ex_crash_2020_02_20_to_04_30'].get('t', float('nan')):+.2f}); ex-2020 ${cc['ex_2020'].get('mean_gross_mes_usd', float('nan')):+.2f}; ex-2022 ${cc['ex_2022'].get('mean_gross_mes_usd', float('nan')):+.2f} "
                f"(t {cc['ex_2022'].get('t', float('nan')):+.2f}); years positive {C['C_years_positive']['positive']}/{C['C_years_positive']['eligible']}")
            log("     by year: " + " ".join(f"{y}:{v.get('mean_gross_mes_usd', float('nan')):+.1f}(n{v['n']})" for y, v in cc["by_year"].items()))
            for bl, bv in books.items():
                if "net" in bv:
                    log(f"     book {bl}: {bv['trades_per_year']:.0f}/yr net Sharpe {bv['net']['sharpe_daily']:+.2f} Sortino {bv['net']['sortino_daily']:+.2f}; gross {bv['gross']['sharpe_daily']:+.2f}/{bv['gross']['sortino_daily']:+.2f}; "
                        f"mean net ${bv['net']['mean_per_trade_usd']:+.2f}; rho arm {bv.get('rho_with_macd_arm', float('nan')):+.3f}")
    # ---- P: the confirmation premise ----
    prem = premise_count(data_root, I["tcal"], log)
    pc = res["cells"][f"h{PRIMARY[0]}_k{PRIMARY[1]}"]
    ex = pc["C_concentration"]["ex_crash_2020_02_20_to_04_30"]
    # per-trade sd without the crash, and trades per short-gamma day, from the primary cell
    step = PRIMARY[0] // 5
    js = [j for j in range(step, 79) if j % step == 0 and j + step <= 78]
    mm = np.column_stack([1e4 * (L[:, j] - L[:, j - step]) for j in js]); dpp = np.column_stack([PG[:, j + step] - PG[:, j] for j in js])
    gsh = (np.sign(mm) * dpp * mes["usd_per_point"])[(short_day > 0) & ~in_crash]
    gsh = gsh[np.isfinite(gsh) & (np.sign(mm)[(short_day > 0) & ~in_crash] != 0)]
    per_day = pc["short_rows"] / max(1, int(short_day.sum()))
    n_exp = prem["short_gamma_sessions"]["G_SUM"] * per_day
    exp_t = float(ex["mean_gross_mes_usd"] / gsh.std(ddof=1) * math.sqrt(n_exp)) if n_exp > 0 else 0.0
    prem["power"] = {"in_sample_ex_crash_mean_gross_mes_usd": ex["mean_gross_mes_usd"], "per_trade_sd_mes_usd": float(gsh.std(ddof=1)), "trades_per_short_day": per_day,
                     "expected_trades_on_slice": n_exp, "expected_t_unclustered": exp_t, "power_rule": POWER_T}
    log(f"  POWER on 2024-01 -> 2025-02: {n_exp:.0f} expected short-gamma trades; expected t {exp_t:.2f} (the rule wants >= {POWER_T})")
    res["premise"] = prem
    # ---- the decision ----
    v1 = pc["V1_stratified_by_same_day_rv_bp"]
    c1 = bool(v1["observed"] > 0 and v1["above_p95"])
    cc = pc["C_concentration"]
    c2 = bool(cc["ex_crash_2020_02_20_to_04_30"].get("mean_gross_mes_usd", -1) > 0 and cc["ex_2022"].get("mean_gross_mes_usd", -1) > 0
              and pc["C_years_positive"]["positive"] * 2 >= pc["C_years_positive"]["eligible"])
    c3 = bool(exp_t >= POWER_T)
    res["decision"] = {"1_vol_controlled_above_p95": c1, "2_not_one_episode": c2, "3_power_on_clean_slice": c3,
                       "outcome": "GO" if (c1 and c2 and c3) else "UNCONFIRMABLE ON THE CLEAN SLICE" if (c1 and c2) else "NO-GO"}
    log(f"  DECISION: {res['decision']['outcome']} (1 {c1}, 2 {c2}, 3 {c3})")
    res["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.exit(run(a.data_root) if a.run else 1)

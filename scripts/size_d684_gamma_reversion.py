"""D684 SIZING -- does the long-gamma intraday reversion D683 found grow large enough, on a slower bar, to pay for a
trade? In-sample (D688's panel, 2016-01-05 -> 2023-12-29), a go/no-go for a pre-registration, not a verdict (the
principal: "I'll go with your recommendation", the recommendation being to size the prize first).

    uv run python scripts/size_d684_gamma_reversion.py --run --data-root "<main checkout>/data"

The object, for horizon h in {5, 15, 30, 60} minutes, at every decision time t = 09:30 + j*h with t + h <= 16:00:
  m = log P(t) - log P(t-h)          the move just made (bp)
  f = log P(t+h) - log P(t)          the next h minutes (bp)
  LG = 1 if G_SUM >= 0 (dealers long gamma; D688's G, known before the open)
  rv_t = the day's realised 5-minute variance from 09:30 to t (known at t); sigma_d = D688's trailing 20-session sigma
Statistics, DECLARED BEFORE THE RUN:
  S1  the reversion slope b of f on m, by G_SUM quintile, by regime, and on all days (day-clustered SEs)
  S2  the gamma gradient with the VOLATILITY CONFOUND controlled (the check D683 did not run):
        f = a + b m + c m*LG + d m*log(rv_t) + e m*log(sigma_d^2) + g log(rv_t) + h log(sigma_d^2)
      c < 0 means more reversion on long-gamma days BEYOND the volatility level. Its t is day-clustered, and it is
      ranked against the enumerated day-rotation null of LG (k = 10 .. n-10, p95 SE 0). The same with G_SUM in $bn in
      place of LG. And a double sort: b within same-day-volatility terciles, long against short gamma.
  S3  the fade, sized in money: at each decision time with |m| >= k * sigma_h (sigma_h = sigma_d sqrt(h/390), prior
      only), k in {0, 0.5, 1, 1.5, 2}, hold -sign(m) for h minutes (non-overlapping), on long-gamma days, short-gamma
      days and all days. Reported per trade: gross and net at 1 MES ($4.42) and at 1 full ES ($19.24), day-clustered
      t, hit rate, trades a year; and per book: the daily net Sharpe and Sortino.
GO / NO-GO for a pre-registration (declared here):
  GO if, for some h in {15, 30, 60} and some k, the LONG-GAMMA fade has a mean gross per trade >= 2 x the MES round
  trip ($8.84), with >= 30 trades a year and a gross day-clustered t >= 2, AND the S2 gradient c at that h has t <= -2
  and lies below the p05 of its rotation null. That is 15 cells, so a GO selects: the pre-registration must fix one
  cell and test it on data this record has not read (2024-01 onward). Otherwise NO-GO, and gamma goes only into the
  expected-profit filter's size term.

Reads nothing dated 2024-01-01 or later (D688's loaders and guards). Output data/d684_gamma_reversion_sizing.json:
statistics only, no per-date GEX (SqueezeMetrics, under the permission of 2026-09-28).
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
OUT = REPO / "data" / "d684_gamma_reversion_sizing.json"
D688_JSON = REPO / "data" / "d688_gamma_close.json"
HORIZONS = (5, 15, 30, 60)
KS = (0.0, 0.5, 1.0, 1.5, 2.0)
GO_H = (15, 30, 60)
GO_GROSS_MULT, GO_TPY, GO_T = 2.0, 30.0, 2.0
ROT_BLOCK = 100


def P(*a, **k):
    print(*a, **k, flush=True)


def clustered(y, cols, groups):
    X = sm.add_constant(np.column_stack(cols))
    return sm.OLS(y, X).fit(cov_type="cluster", cov_kwds={"groups": groups})


def mean_t_clustered(x, groups):
    """Mean of x with a day-clustered SE (regression on a constant)."""
    r = sm.OLS(x, np.ones((len(x), 1))).fit(cov_type="cluster", cov_kwds={"groups": groups})
    return float(r.params[0]), float(r.tvalues[0])


def rotation_interaction(y, m, day_idx, day_var, C, ks):
    """Slope on m * day_var[rotated] with controls C (FWL), for every rotation k; column 0 is k = 0."""
    n_days = len(day_var)
    X = np.column_stack([np.ones(len(y))] + list(C))
    Qx, _ = np.linalg.qr(X)
    ry = y - Qx @ (Qx.T @ y)
    out = np.empty(len(ks))
    for s in range(0, len(ks), ROT_BLOCK):
        kb = ks[s:s + ROT_BLOCK]
        rot = day_var[(np.arange(n_days)[:, None] - kb[None, :]) % n_days]      # days x block
        Z = m[:, None] * rot[day_idx]                                            # rows x block
        rZ = Z - Qx @ (Qx.T @ Z)
        out[s:s + len(kb)] = (rZ * ry[:, None]).sum(0) / (rZ * rZ).sum(0)
    return out


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
    log(f"  ES book rebuilt in {time.time() - t0:.0f} s")

    # ---- D688's panel, exactly as its runner filters it; reproduce beta_G first ----
    D = Dfull.join(prior[["G_ES"]], how="left")
    D = D[D.index >= S.IN_FROM]
    D["G_SUM"] = D["G_SPX"] + D["G_ES"]
    need = ["P1530", "P1600", "P1100", "P1130", "P1550", "S_prev", "sig", "V", "G_SPX", "G_ES", "A_L"] + ["P" + t.replace(":", "") for t in S.CLOCK]
    D = D[np.isfinite(D[need].to_numpy(float)).all(1)]
    S.guard_window(D.index, "sizing panel")
    days = D.index.to_numpy().astype(str)
    nd = len(days)
    sig = D["sig"].to_numpy(float); G = D["G_SUM"].to_numpy(float)
    r = 100 * np.log(D["P1530"].to_numpy(float) / D["S_prev"].to_numpy(float)); R2 = 1e4 * np.log(D["P1600"].to_numpy(float) / D["P1530"].to_numpy(float))
    f681, _ = S.gamma_regression(R2, G, r, sig, D["V"].to_numpy(float), D["A_L"].to_numpy(float), null=False)
    ref = json.loads(D688_JSON.read_text(encoding="utf-8"))["gate1"]["G1"]["beta_G"]
    if f681["beta_G"] != ref:
        raise S.GateError(f"[REPRO] beta_G {f681['beta_G']!r} vs D688's {ref!r}")
    log(f"  D688 REPRODUCED: beta_G {f681['beta_G']!r} on {nd} sessions")

    # ---- the 5-minute price grid (the price AT hh:mm = the close of the bar labelled a minute earlier; 09:30 = the open) ----
    b = I["bars"]
    b = b[b["day"].isin(set(days))]
    close = b.pivot(index="day", columns="hhmm", values="close").reindex(days)
    op = b[b["hhmm"] == "09:30"].set_index("day")["open"].reindex(days).to_numpy(float)
    grid = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=5 * k)) for k in range(79)]
    cols = [op] + [close[(g - pd.Timedelta(minutes=1)).strftime("%H:%M")].to_numpy(float) for g in grid[1:]]
    PG = np.column_stack(cols)                                                   # days x 79 (09:30 .. 16:00)
    ok_grid = np.isfinite(PG).all(1)
    log(f"  5-minute grid complete on {int(ok_grid.sum())} of {nd} sessions")
    L = np.log(PG)
    r5 = 1e4 * np.diff(L, axis=1)
    cum_rv = np.concatenate([np.full((nd, 1), np.nan), np.cumsum(r5 * r5, axis=1)], axis=1)   # realised variance 09:30 -> grid point j
    lsig2 = np.log(sig ** 2)
    LG = (G >= 0).astype(float)
    q5 = np.digitize(G, np.quantile(G, [0.2, 0.4, 0.6, 0.8]))
    E = S.d685()
    mes, esf = E.cost_spec("ES", "micro"), E.cost_spec("ES", "full")
    ks_rot = S.rot_ks(nd)
    res = {"spec": "D684 SIZING (in-sample, go/no-go for a pre-registration, not a verdict)", "reproduction": {"beta_G": f681["beta_G"], "exact": True, "sessions": nd},
           "costs": {"mes": mes, "es_full": esf}, "horizons": {}}
    go_cells = []
    for h in HORIZONS:
        step = h // 5
        js = [j for j in range(step, 79) if j % step == 0 and j + step <= 78]
        rows = []
        for j in js:
            mm = 1e4 * (L[:, j] - L[:, j - step]); ff = 1e4 * (L[:, j + step] - L[:, j])
            dp = PG[:, j + step] - PG[:, j]
            rows.append(pd.DataFrame({"di": np.arange(nd), "j": j, "m": mm, "f": ff, "dp": dp, "lrv": np.log(cum_rv[:, j] / j), "P": PG[:, j]}))
        T = pd.concat(rows, ignore_index=True)
        T = T[np.isfinite(T[["m", "f", "dp", "lrv"]].to_numpy()).all(1) & ok_grid[T["di"].to_numpy()]].reset_index(drop=True)
        di = T["di"].to_numpy(); m = T["m"].to_numpy(); f = T["f"].to_numpy(); lrv = T["lrv"].to_numpy()
        lg = LG[di]; ls = lsig2[di]; grp = di
        H = {"decision_times_per_day": len(js), "rows": int(len(T))}
        # S1 the reversion slope by state
        def slope(msk):
            if msk.sum() < 200:
                return {"n": int(msk.sum())}
            rr = clustered(f[msk], [m[msk]], grp[msk])
            return {"b": float(rr.params[1]), "t": float(rr.tvalues[1]), "n": int(msk.sum()), "mean_abs_m_bp": float(np.abs(m[msk]).mean())}
        H["S1"] = {"all": slope(np.ones(len(T), bool)), "long_gamma": slope(lg == 1), "short_gamma": slope(lg == 0),
                   "by_G_quintile": {int(q): slope(q5[di] == q) for q in range(5)}}
        # S2 the gradient beyond volatility
        C = [m, m * lrv, m * ls, lrv, ls]
        rr = clustered(f, [m, m * lg, m * lrv, m * ls, lrv, ls], grp)
        rot = rotation_interaction(f, m, di, LG, C, ks_rot)
        if not abs(rot[0] - rr.params[2]) <= 1e-9 * max(1.0, abs(rr.params[2])):
            raise S.GateError(f"[ROTATION] h {h}: the k = 0 interaction {rot[0]!r} is not the regression's {rr.params[2]!r}")
        Gbn = G / 1e9
        rr2 = clustered(f, [m, m * Gbn[di], m * lrv, m * ls, lrv, ls], grp)
        rot2 = rotation_interaction(f, m, di, Gbn, C, ks_rot)
        rv_t = np.digitize(lrv, np.quantile(lrv, [1 / 3, 2 / 3]))
        dsort = {int(v): {"long": slope((rv_t == v) & (lg == 1)), "short": slope((rv_t == v) & (lg == 0))} for v in range(3)}
        H["S2"] = {"c_m_x_LG": float(rr.params[2]), "t_c": float(rr.tvalues[2]), "b_m": float(rr.params[1]), "t_b": float(rr.tvalues[1]),
                   "d_m_x_lrv": float(rr.params[3]), "t_d": float(rr.tvalues[3]), "e_m_x_lsig2": float(rr.params[4]), "t_e": float(rr.tvalues[4]),
                   "rotation_c": S.blk(rot[0], rot[1:]),
                   "c_m_x_G_bn": float(rr2.params[2]), "t_c_G_bn": float(rr2.tvalues[2]), "rotation_c_G_bn": S.blk(rot2[0], rot2[1:]),
                   "double_sort_by_same_day_vol_tercile": dsort}
        s2_ok = bool(rr.tvalues[2] <= -GO_T and rot[0] < np.percentile(rot[1:], 5))
        # S3 the fade in money
        sg_h = np.sqrt(np.exp(ls)) * math.sqrt(h / 390.0)
        cells = {}
        for regime, rmask in (("long_gamma", lg == 1), ("short_gamma", lg == 0), ("all", np.ones(len(T), bool))):
            for k in KS:
                tr = rmask & (np.abs(m) >= k * sg_h) & (m != 0)
                nt = int(tr.sum())
                if nt < 30:
                    cells[f"{regime}_k{k}"] = {"trades": nt}
                    continue
                side = -np.sign(m[tr]); pts = side * T["dp"].to_numpy()[tr]
                g_mes = pts * mes["usd_per_point"]; g_es = pts * esf["usd_per_point"]
                mg, tg = mean_t_clustered(g_mes, grp[tr])
                n_mes = g_mes - mes["cost_rt_usd"]; n_es = g_es - esf["cost_rt_usd"]
                daily = np.bincount(grp[tr], weights=n_mes, minlength=nd); daily_es = np.bincount(grp[tr], weights=n_es, minlength=nd)
                tpy = nt / (nd / 252.0)
                cells[f"{regime}_k{k}"] = {"trades": nt, "trades_per_year": tpy, "mean_gross_mes_usd": mg, "t_gross_clustered": tg,
                                           "mean_net_mes_usd": float(n_mes.mean()), "mean_net_es_full_usd": float(n_es.mean()),
                                           "mean_gross_bp": float((side * f[tr]).mean()), "hit_rate_gross": float((g_mes > 0).mean()),
                                           "median_gross_mes_usd": float(np.median(g_mes)),
                                           "book_mes_net_sharpe": E.sharpe(daily), "book_mes_net_sortino": E.sortino(daily),
                                           "book_es_full_net_sharpe": E.sharpe(daily_es), "book_es_full_net_sortino": E.sortino(daily_es),
                                           "gross_vs_2c_mes": float(mg / (2 * mes["cost_rt_usd"]))}
                c = cells[f"{regime}_k{k}"]
                if regime == "long_gamma" and h in GO_H and mg >= GO_GROSS_MULT * mes["cost_rt_usd"] and tpy >= GO_TPY and tg >= GO_T and s2_ok:
                    go_cells.append(f"h{h}_k{k}")
        H["S3"] = cells
        res["horizons"][str(h)] = H
        s1 = H["S1"]
        log(f"  h {h:>2} min: {H['rows']} rows; b all {s1['all']['b']:+.4f} (t {s1['all']['t']:+.2f}) long {s1['long_gamma']['b']:+.4f} (t {s1['long_gamma']['t']:+.2f}) short {s1['short_gamma']['b']:+.4f} (t {s1['short_gamma']['t']:+.2f}); "
            "by quintile " + " ".join(f"{q}:{v['b']:+.3f}" for q, v in s1["by_G_quintile"].items()))
        s2 = H["S2"]
        log(f"          S2 c(m x LG) {s2['c_m_x_LG']:+.4f} (t {s2['t_c']:+.2f}, rotation pct {s2['rotation_c']['pct_rank']:.3f}, p05 {s2['rotation_c']['p05']:+.4f}); "
            f"c(m x G$bn) {s2['c_m_x_G_bn']:+.5f} (t {s2['t_c_G_bn']:+.2f}, pct {s2['rotation_c_G_bn']['pct_rank']:.3f}); m x lrv {s2['d_m_x_lrv']:+.4f} (t {s2['t_d']:+.2f})")
        log("          double sort b long/short by same-day vol tercile: " + " ".join(f"{v}:{d['long'].get('b', float('nan')):+.3f}/{d['short'].get('b', float('nan')):+.3f}" for v, d in s2["double_sort_by_same_day_vol_tercile"].items()))
        for regime in ("long_gamma", "short_gamma", "all"):
            log(f"          fade {regime:<11} " + " | ".join(
                f"k{k}: {c['trades_per_year']:.0f}/yr ${c['mean_gross_mes_usd']:+.2f} (t {c['t_gross_clustered']:+.1f}) net ${c['mean_net_mes_usd']:+.2f} ES ${c['mean_net_es_full_usd']:+.1f}"
                if "mean_gross_mes_usd" in c else f"k{k}: {c['trades']} trades" for k, c in ((k, cells[f'{regime}_k{k}']) for k in KS)))
    res["go_cells"] = go_cells
    res["decision"] = "GO" if go_cells else "NO-GO"
    res["rule"] = (f"GO if a long-gamma fade at h in {GO_H} has mean gross >= {GO_GROSS_MULT} x the MES round trip, >= {GO_TPY} trades a year, "
                   f"gross clustered t >= {GO_T}, and the S2 gradient t <= -{GO_T} below its rotation p05")
    log(f"  DECISION: {res['decision']} {go_cells}")
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

"""D690 DIAG -- the oracle filter and the accuracy assessment, on D689's candidate trades (the principal: "We need a
better way to filter for profits, make an oracle filter and the accuracy assessment"). In-sample (D688's panel,
2016-01-05 -> 2023-12-29), post hoc on spent data, a method and a diagnostic, not a verdict. The yardstick is the new
library `backtest_framework.validation.filter_oracle`.

    uv run python scripts/diag_d690_oracle_filter.py --run --data-root "<main checkout>/data"

THE CANDIDATES. Every hourly continuation on EVERY day (not only short-gamma days): at t = 10:30, 11:30, 12:30,
13:30 and 14:30, with m = the last 60 minutes' move (m != 0), hold sign(m) for 60 minutes. Gross in $ at 1 full ES
(the only size D689 found to pay; $19.24 a round trip) and at 1 MES ($4.42). Evaluation rows are those after a
250-session burn-in, the same for every filter and every oracle.

DECLARED BEFORE THE RUN
  A  THE ORACLE (hindsight; a ceiling). Take a trade iff its realised net > 0; and at the template's bar, iff its gross
     >= 2 x the round trip. The SIZE-ONLY oracle keeps the top 20 % / 40 % by the realised |next-hour move|, with the
     direction still the rule's (what a perfect size forecast, gamma's proven strength, is worth to this trade).
  B  THE PARTIAL-ORACLE CURVES (how accurate must a filter be?). A forecast of the realised gross with normal-score
     correlation rho in {0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1}, keeping the top q in {0.2, 0.4}: 200 draws each, mean
     net per trade (p05, p95), the daily net Sharpe, and the realised Spearman. rho = 0 is the null. The same for a
     partial SIZE forecast (target |f|).
  C  FIVE REAL FILTERS, prior-only (walk-forward: refit at the start of each month on rows of strictly earlier days;
     nothing before the burn-in is traded):
       R1  the regime gate: G_SUM < 0 (D689's book);
       R2  D689's expected-profit projection pi |m| on short-gamma rows (the one that failed; for reference);
       R3  LINEAR expected profit: OLS of the gross (bp) on the features below; take iff the projected $ >= 2 x RT;
       R4  LOGISTIC: P(net > 0 | features) at full ES; take iff P >= 0.5;
       R5  REGIME-CELL expected profit: the prior-only mean gross of the candidate's cell (short/long gamma x long/short
           side); take iff >= 2 x RT (D689 section 4's design point: a per-trade constant by regime, not |m|-scaled).
     Features for R3/R4 (all known at t): the short-gamma dummy, G_SUM ($bn), log realised variance to t, log sigma_d^2,
     |m| / sigma_h, sign(m), the short dummy x sign(m), four hour dummies, and sign(m) x the day's move to t (%).
     Each is scored against the oracle (net > 0 at full ES): the confusion matrix, precision, recall, balanced accuracy,
     AUC, the Spearman of its score with the gross (its place on curve B), the capture of the oracle's net, the
     calibration (projected against realised, slope; R2, R3, R5), and the book (trades a year; daily net and gross
     Sharpe and Sortino at full ES and MES; mean net). Its null: the day-rotation of its score (k = 10 .. n-10,
     enumerated), with the net Sharpe re-scored under its own take rule.
  "BETTER" (declared): a filter beats the regime gate R1 if its full-ES daily net Sharpe is higher AND above the p95 of
  its own rotation null. No threshold is tuned after the run.

Reads nothing dated 2024-01-01 or later. Output data/d690_oracle_filter.json: statistics only, no per-date GEX
(SqueezeMetrics, under the permission of 2026-09-28).
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
from sklearn.linear_model import LogisticRegression

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage0_d688_gamma_close as S  # noqa: E402  (importing defines, never runs)

from backtest_framework.validation import filter_oracle as FO  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d690_oracle_filter.json"
D688_JSON = REPO / "data" / "d688_gamma_close.json"
H = 60
BURN = 250
RHOS = (0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.5, 1.0)
QS = (0.2, 0.4)
N_DRAW = 200
SEED = 690


def P(*a, **k):
    print(*a, **k, flush=True)


def daily_stats(net_rows, take, di, days_eval_mask, nd):
    """Daily net over every evaluation session (zeros on untraded ones): Sharpe, Sortino, trades a year."""
    E = S.d685()
    d = np.bincount(di[take], weights=net_rows[take], minlength=nd)[days_eval_mask]
    ne = int(days_eval_mask.sum())
    return {"sharpe": E.sharpe(d), "sortino": E.sortino(d), "trades_per_year": float(take.sum()) / (ne / 252.0), "total": float(d.sum())}


def sharpe_fast(net_rows, take, di, days_eval_mask, nd):
    d = np.bincount(di[take], weights=net_rows[take], minlength=nd)[days_eval_mask]
    s = d.std(ddof=1)
    return float(d.mean() / s * math.sqrt(252)) if s > 0 else float("nan")


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
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
    S.guard_window(D.index, "D690 panel")
    days = D.index.to_numpy().astype(str)
    nd = len(days)
    sig = D["sig"].to_numpy(float); G = D["G_SUM"].to_numpy(float); Sp = D["S_prev"].to_numpy(float)
    r = 100 * np.log(D["P1530"].to_numpy(float) / Sp); R2 = 1e4 * np.log(D["P1600"].to_numpy(float) / D["P1530"].to_numpy(float))
    f688, _ = S.gamma_regression(R2, G, r, sig, D["V"].to_numpy(float), D["A_L"].to_numpy(float), null=False)
    ref = json.loads(D688_JSON.read_text(encoding="utf-8"))["gate1"]["G1"]["beta_G"]
    if f688["beta_G"] != ref:
        raise S.GateError(f"[REPRO] beta_G {f688['beta_G']!r} vs D688's {ref!r}")
    log(f"  D688 REPRODUCED on {nd} sessions ({time.time() - t0:.0f} s)")

    # ---- the candidates: the 5-minute grid, as D684/D689 ----
    b = I["bars"]
    b = b[b["day"].isin(set(days))]
    close = b.pivot(index="day", columns="hhmm", values="close").reindex(days)
    op = b[b["hhmm"] == "09:30"].set_index("day")["open"].reindex(days).to_numpy(float)
    grid = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=5 * k)) for k in range(79)]
    PG = np.column_stack([op] + [close[(g - pd.Timedelta(minutes=1)).strftime("%H:%M")].to_numpy(float) for g in grid[1:]])
    L = np.log(PG)
    r5 = 1e4 * np.diff(L, axis=1)
    cum_rv = np.concatenate([np.full((nd, 1), np.nan), np.cumsum(r5 * r5, axis=1)], axis=1)
    step = H // 5
    js = [j for j in range(step, 79) if j % step == 0 and j + step <= 78]
    rows = []
    for slot, j in enumerate(js):
        with np.errstate(divide="ignore", invalid="ignore"):
            lrv = np.log(cum_rv[:, j] / j)
        rows.append(pd.DataFrame({"di": np.arange(nd), "slot": slot, "m": 1e4 * (L[:, j] - L[:, j - step]), "f": 1e4 * (L[:, j + step] - L[:, j]),
                                  "dp": PG[:, j + step] - PG[:, j], "P": PG[:, j], "lrv": lrv, "rt": 100 * np.log(PG[:, j] / Sp)}))
    T = pd.concat(rows, ignore_index=True)
    T = T[np.isfinite(T[["m", "f", "dp", "lrv", "P", "rt"]].to_numpy()).all(1) & (T["m"] != 0)].sort_values(["di", "slot"], kind="stable").reset_index(drop=True)
    di = T["di"].to_numpy(); m = T["m"].to_numpy(); f = T["f"].to_numpy(); dp = T["dp"].to_numpy(); Px = T["P"].to_numpy()
    side = np.sign(m); g_bp = side * f
    short = (G < 0).astype(float)[di]
    lsig2 = np.log(sig ** 2)[di]
    sg_h = sig[di] * math.sqrt(H / 390.0)
    E = S.d685()
    mes, esf = E.cost_spec("ES", "micro"), E.cost_spec("ES", "full")
    g_es = side * dp * esf["usd_per_point"]; n_es = g_es - esf["cost_rt_usd"]
    g_mes = side * dp * mes["usd_per_point"]; n_mes = g_mes - mes["cost_rt_usd"]
    ev = di >= BURN
    days_eval = np.arange(nd) >= BURN
    log(f"  candidates: {len(T)} rows, {int(ev.sum())} after the {BURN}-session burn-in; short-gamma share {short[ev].mean():.3f}")
    res = {"spec": "D690 DIAG (post hoc, in-sample; the oracle filter and the accuracy assessment of profit filters)", "reproduction": {"beta_G": f688["beta_G"], "exact": True},
           "candidates": {"rows": int(len(T)), "eval_rows": int(ev.sum()), "eval_sessions": int(days_eval.sum()), "short_gamma_share": float(short[ev].mean())},
           "costs": {"mes": mes, "es_full": esf}}

    # ---- A: the oracles (ceilings) ----
    A = {}
    for lab, gg, nn, cs in (("es_full", g_es, n_es, esf), ("mes", g_mes, n_mes, mes)):
        ge, ne = gg[ev], nn[ev]; dve = di[ev]
        o = FO.oracle_take(ne)
        o2 = FO.oracle_take_threshold(ge, cs["cost_rt_usd"], 2.0)
        A[lab] = {"take_all": daily_stats(ne, np.ones(len(ne), bool), dve, days_eval, nd) | {"mean_net": float(ne.mean())},
                  "oracle_net_positive": daily_stats(ne, o, dve, days_eval, nd) | {"mean_net": float(ne[o].mean()), "share_taken": float(o.mean())},
                  "oracle_gross_ge_2c": daily_stats(ne, o2, dve, days_eval, nd) | {"mean_net": float(ne[o2].mean()), "share_taken": float(o2.mean())}}
        for q in QS:
            so = FO.top_fraction(np.abs(f[ev]), q)
            A[lab][f"size_only_oracle_top{int(q * 100)}"] = daily_stats(ne, so, dve, days_eval, nd) | {"mean_net": float(ne[so].mean())}
    res["A_oracles"] = A
    a = A["es_full"]
    log(f"  A (full ES): take-all net Sharpe {a['take_all']['sharpe']:+.2f} (${a['take_all']['mean_net']:+.2f}/trade); ORACLE net>0 Sharpe {a['oracle_net_positive']['sharpe']:+.1f} "
        f"(${a['oracle_net_positive']['mean_net']:+.0f}, {a['oracle_net_positive']['share_taken']:.2f} taken); size-only top20 {a['size_only_oracle_top20']['sharpe']:+.2f} "
        f"(${a['size_only_oracle_top20']['mean_net']:+.2f}), top40 {a['size_only_oracle_top40']['sharpe']:+.2f}")

    # ---- B: the partial-oracle curves ----
    Bc = {}
    ne, dve = n_es[ev], di[ev]
    for tlab, target in (("gross", g_es[ev]), ("size_abs_f", np.abs(f[ev]))):
        z = FO.normal_scores(target)
        for q in QS:
            cur = []
            for rho in RHOS:
                mn, sh, sp = [], [], []
                for _ in range(N_DRAW):
                    s = FO._partial(z, rho, rng)
                    keep = FO.top_fraction(s, q)
                    mn.append(float(ne[keep].mean())); sh.append(sharpe_fast(ne, keep, dve, days_eval, nd)); sp.append(FO.spearman(s, g_es[ev]))
                mn_a, sh_a = np.array(mn), np.array(sh)
                cur.append({"rho": rho, "mean_net_per_trade": float(mn_a.mean()), "p05": float(np.percentile(mn_a, 5)), "p95": float(np.percentile(mn_a, 95)),
                            "daily_net_sharpe_mean": float(np.nanmean(sh_a)), "daily_net_sharpe_p05": float(np.nanpercentile(sh_a, 5)),
                            "daily_net_sharpe_p95": float(np.nanpercentile(sh_a, 95)), "spearman_with_gross_mean": float(np.mean(sp))})
            Bc[f"{tlab}_q{int(q * 100)}"] = cur
            log(f"  B {tlab} q{int(q * 100)}: " + " ".join(f"rho{c['rho']}:{c['daily_net_sharpe_mean']:+.2f}(sp {c['spearman_with_gross_mean']:+.3f})" for c in cur))
    res["B_partial_oracle_curves_full_es"] = Bc

    # ---- C: the real filters (walk-forward, monthly refit on strictly earlier days) ----
    slot = T["slot"].to_numpy()
    X = np.column_stack([short, G[di] / 1e9, T["lrv"].to_numpy(), lsig2, np.abs(m) / sg_h, side, short * side,
                         (slot == 1), (slot == 2), (slot == 3), (slot == 4), side * T["rt"].to_numpy()]).astype(float)
    feat_names = ["short", "G_SUM_bn", "log_rv_t", "log_sig2", "abs_m_over_sig_h", "side", "short_x_side", "slot1", "slot2", "slot3", "slot4", "side_x_day_move"]
    mon = np.array([days[d][:7] for d in di])
    months = sorted(set(mon[ev]))
    pred_bp = np.full(len(T), np.nan); prob = np.full(len(T), np.nan); cell_usd = np.full(len(T), np.nan)
    pi2 = np.full(len(T), np.nan)
    cell = (short > 0).astype(int) * 2 + (side > 0).astype(int)
    for M in months:
        rows_m = np.flatnonzero(mon == M)
        first_day = di[rows_m].min()
        tr = di < first_day
        Xt = np.column_stack([np.ones(tr.sum()), X[tr]])
        beta = np.linalg.lstsq(Xt, g_bp[tr], rcond=None)[0]
        pred_bp[rows_m] = np.column_stack([np.ones(len(rows_m)), X[rows_m]]) @ beta
        mu, sd = X[tr].mean(0), X[tr].std(0)
        sd[sd == 0] = 1.0
        clf = LogisticRegression(max_iter=2000).fit((X[tr] - mu) / sd, n_es[tr] > 0)
        prob[rows_m] = clf.predict_proba((X[rows_m] - mu) / sd)[:, 1]
        for c in range(4):
            cm = tr & (cell == c)
            cell_usd[rows_m[cell[rows_m] == c]] = g_es[cm].mean() if cm.sum() >= 30 else np.nan
        shm = tr & (short > 0)
        x_, y_ = np.abs(m[shm]), g_bp[shm]
        pi2[rows_m] = (x_ * y_).sum() / (x_ * x_).sum() if shm.sum() >= 30 else np.nan
    # the lag audit: one month's OLS re-derived from a loop-built training set
    M0 = months[len(months) // 2]
    rows_m = np.flatnonzero(mon == M0)
    tr_loop = np.array([days[d] < days[di[rows_m].min()] for d in di])
    beta_l = np.linalg.lstsq(np.column_stack([np.ones(tr_loop.sum()), X[tr_loop]]), g_bp[tr_loop], rcond=None)[0]
    if not np.allclose(np.column_stack([np.ones(len(rows_m)), X[rows_m]]) @ beta_l, pred_bp[rows_m], rtol=1e-9, atol=1e-9):
        raise S.GateError(f"[LAG] {M0}: the walk-forward prediction is not the date-filtered refit's")
    res["audits"] = {"walk_forward_month_rederived": M0}
    to_usd = lambda bp, cs: bp / 1e4 * Px * cs["usd_per_point"]   # noqa: E731
    filters = {
        "R1_regime_gate": (short.copy(), short > 0, None),
        "R2_d689_pi_abs_m": (np.where(short > 0, pi2 * np.abs(m), -np.inf), (short > 0) & np.isfinite(pi2) & (to_usd(pi2 * np.abs(m), esf) >= 2 * esf["cost_rt_usd"]), to_usd(np.where(short > 0, pi2 * np.abs(m), np.nan), esf)),
        "R3_linear_ep": (pred_bp, to_usd(pred_bp, esf) >= 2 * esf["cost_rt_usd"], to_usd(pred_bp, esf)),
        "R4_logistic": (prob, prob >= 0.5, None),
        "R5_regime_cell_ep": (cell_usd, np.isfinite(cell_usd) & (cell_usd >= 2 * esf["cost_rt_usd"]), cell_usd),
    }
    Cres = {}
    ks = S.rot_ks(nd)
    for name, (score, take, proj) in filters.items():
        sc = np.where(np.isfinite(score), score, np.nanmin(score[np.isfinite(score)]) - 1.0)[ev]
        tk = take[ev] & np.isfinite(score[ev])
        rep = FO.assess(sc, tk, g_es[ev], n_es[ev])
        rep["book_es_full"] = daily_stats(n_es[ev], tk, di[ev], days_eval, nd) | {"mean_net": float(n_es[ev][tk].mean()) if tk.any() else None, "gross_sharpe": sharpe_fast(g_es[ev], tk, di[ev], days_eval, nd)}
        rep["book_mes"] = daily_stats(n_mes[ev], tk, di[ev], days_eval, nd) | {"mean_net": float(n_mes[ev][tk].mean()) if tk.any() else None}
        if proj is not None and np.isfinite(proj[ev]).sum() > 100:
            pm = np.isfinite(proj[ev]) & (np.abs(proj[ev]) < 1e6)
            rep["calibration_es_full"] = FO.calibration(proj[ev][pm], g_es[ev][pm], n_bins=10)
        # the rotation null: the (score, take) grid rotated across days, re-scored under the same rule
        day_take = np.zeros((nd, len(js)), bool); day_net = np.zeros((nd, len(js)))
        day_take[di[ev], slot[ev]] = tk; day_net[di[ev], slot[ev]] = n_es[ev]
        valid = np.zeros((nd, len(js)), bool); valid[di[ev], slot[ev]] = True
        null = []
        for k in ks[1:]:
            rt = np.roll(day_take, int(k), axis=0) & valid
            dn = (np.where(rt, day_net, 0.0)).sum(1)[days_eval]
            s = dn.std(ddof=1)
            null.append(dn.mean() / s * math.sqrt(252) if s > 0 else np.nan)
        rep["rotation_null_net_sharpe_es_full"] = S.blk(rep["book_es_full"]["sharpe"], np.array(null))
        Cres[name] = rep
        c, bk = rep["confusion_vs_oracle"], rep["book_es_full"]
        log(f"  C {name}: take {c['take_rate']:.3f} precision {c['precision']:.3f} (base {c['base_rate']:.3f}) recall {c['recall']:.3f} bal-acc {c['balanced_accuracy']:.3f} "
            f"AUC {rep['auc_vs_oracle_label']:.3f} Spearman {rep['spearman_score_vs_gross']:+.3f}; capture {rep['capture']['capture_of_oracle']:+.3f}; "
            f"ES net Sharpe {bk['sharpe']:+.2f} Sortino {bk['sortino']:+.2f} ({bk['trades_per_year']:.0f}/yr, ${bk['mean_net'] if bk['mean_net'] is not None else float('nan'):+.2f}) "
            f"rot pct {rep['rotation_null_net_sharpe_es_full']['pct_rank']:.3f}"
            + (f"; calib slope {rep['calibration_es_full']['slope']:+.3f}" if "calibration_es_full" in rep else ""))
    res["C_real_filters"] = Cres
    res["features"] = feat_names
    r1 = Cres["R1_regime_gate"]["book_es_full"]["sharpe"]
    res["better_than_regime_gate"] = {k: bool(v["book_es_full"]["sharpe"] > r1 and v["rotation_null_net_sharpe_es_full"]["above_p95"]) for k, v in Cres.items() if k != "R1_regime_gate"}
    log(f"  BETTER THAN THE REGIME GATE (declared rule): {res['better_than_regime_gate']}")
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

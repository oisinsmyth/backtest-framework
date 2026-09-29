"""D693 STAGE 0 -- the principal's filter for the short-gamma continuation, scored at MES (the principal, 2026-09-29, after
D692's MES oracle profile: "Short-gamma days, long only, MES book, bar at net above zero"; inputs "Against the day's
move, Volatility floor"; form "Per-cell expected profit"; gamma measure "Combined G_SUM (SPX + ES)").

    uv run python scripts/stage0_d693_short_gamma_long_filter.py --run --data-root "<main checkout>/data"

In-sample development on D688's panel (2016-01-05 -> 2023-12-29), walk-forward and prior-only. The cells were chosen
after reading D692's in-sample profile, so these numbers flatter the filter: only unseen data can confirm it.

THE UNIVERSE: D692's candidates restricted to G_SUM < 0 (SPX GEX + the ES options book at the prior settlement) and
m > 0 (the last 60 minutes rose): buy 1 MES at t (10:30 .. 14:30), sell 60 minutes later. Net = gross - $4.42.
THE ORACLE LABEL: net > 0.

THE FILTER (per-cell expected profit, declared):
  cells = alignment x volatility tercile (6 cells)
    alignment: AGAINST = the day's move so far (prior settlement -> t) is down (the last hour rose against it);
               WITH = it is up
    volatility: today's realised 5-minute variance up to t (per bar), in terciles whose edges are the 1/3 and 2/3
               quantiles of that quantity over ALL candidates (every day, both sides) of strictly earlier days
  projection for a trade in month M = the mean MES net of the UNIVERSE's trades in its cell over strictly earlier days
    (edges and means refit at the start of each month; at least 30 earlier trades in the cell, else no projection)
  take iff the projection > $0. No trade in the first 250 sessions (the burn-in, as D690).

DECLARED OUTPUTS (all at MES, on the evaluation rows after the burn-in):
  1  the oracle for the universe (net > 0): the ceiling
  2  the gate alone (every universe trade) and the filtered book: trades a year, daily net and gross Sharpe and
     Sortino, mean and median net, the day-clustered t of the mean net, hit rate, trimmed means (ex-top, ex-bottom,
     both), by year, the top five trades, and rho with the admitted MACD arm (D466/D508's arm via D685's loader)
  3  the accuracy assessment against the oracle (D690's library): confusion, precision, recall, AUC and Spearman of
     the projection, capture of the oracle's net, and the CALIBRATION slope of realised on projected net
  4  the partial-oracle curve on the universe (target: net), keeping the filter's own take share and 50 %,
     rho in {0, 0.05, 0.1, 0.2, 0.3, 0.5, 1}, 200 draws: where the filter sits for its accuracy
  5  the null: the filter's take grid rotated across days within the universe (k = 10 .. n-10, enumerated), net
     Sharpe re-scored
  6  the six cells in hindsight (full-sample means), labelled descriptive
  7  a lag audit: the projection re-derived for sampled trades from a date-filtered loop; it must fire with today's
     trades included
DECLARED READING: the filter is USEFUL IN-SAMPLE if (a) its calibration slope is > 0, (b) its net Sharpe beats the
gate alone, and (c) its net Sharpe is above the p95 of its rotation null. No threshold is tuned after the run.

Reads nothing dated 2024-01-01 or later. Output data/d693_short_gamma_long_filter.json: statistics only, no per-date
GEX (SqueezeMetrics, under the permission of 2026-09-28).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import diag_d692_oracle_profile_mes as B  # noqa: E402  (D692's candidate builder; importing defines, never runs)
import stage0_d688_gamma_close as S  # noqa: E402

from backtest_framework.validation import filter_oracle as FO  # noqa: E402

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d693_short_gamma_long_filter.json"
BURN = 250
MIN_CELL = 30
RHOS = (0.0, 0.05, 0.1, 0.2, 0.3, 0.5, 1.0)
N_DRAW = 200
SEED = 693


def P(*a, **k):
    print(*a, **k, flush=True)


def book(net, gross, take, di, days, eval_days, arm, E):
    """The four groups for a book of 1-MES trades (daily series over the evaluation sessions)."""
    nd = len(days)
    tn, tg, td = net[take], gross[take], di[take]
    dn = np.bincount(td, weights=tn, minlength=nd)[eval_days]
    dg = np.bincount(td, weights=tg, minlength=nd)[eval_days]
    ne = int(eval_days.sum())
    out = {"trades": int(take.sum()), "trades_per_year": float(take.sum()) / (ne / 252.0)}
    if take.sum() < 10:
        return out
    rr = sm.OLS(tn, np.ones((len(tn), 1))).fit(cov_type="cluster", cov_kwds={"groups": td})
    out |= {"net_sharpe": E.sharpe(dn), "net_sortino": E.sortino(dn), "gross_sharpe": E.sharpe(dg), "gross_sortino": E.sortino(dg),
            "total_net": float(tn.sum()), "mean_net": float(tn.mean()), "t_mean_net_clustered": float(rr.tvalues[0]),
            "mean_gross": float(tg.mean()), "max_dd": E.max_dd(dn), "vol_ann": float(dn.std(ddof=1) * math.sqrt(252)),
            "distribution_net": E.dist(tn)}
    yr = np.array([days[d][:4] for d in td])
    out["by_year_net"] = {y: {"trades": int((yr == y).sum()), "net": float(tn[yr == y].sum())} for y in sorted(set(yr))}
    out["top5"] = [{"session": days[td[i]], "net": float(tn[i])} for i in np.argsort(-np.abs(tn))[:5]]
    pos = {d: i for i, d in enumerate(days)}
    x = np.array([np.bincount(td, weights=tn, minlength=nd)[pos[d]] if d in pos else 0.0 for d in arm["days"]])
    out["rho_with_macd_arm"] = float(np.corrcoef(x, arm["net"])[0, 1]) if x.std() > 0 else float("nan")
    return out


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    T, nd = B.build(data_root, log)
    E = S.d685()
    mes = E.cost_spec("ES", "micro")
    cost = mes["cost_rt_usd"]
    arm = E.load_arm()
    days = np.array(sorted(set(T["day"])))
    if len(days) != nd:
        raise S.GateError("[PANEL] the candidate days are not the panel's")
    di = T["di"].to_numpy(); m = T["m"].to_numpy(); lrv = T["lrv"].to_numpy(); rt = T["rt"].to_numpy(); slot = T["slot"].to_numpy()
    side = np.sign(m)
    gross = side * T["dp"].to_numpy() * mes["usd_per_point"]
    net = gross - cost
    uni = (T["G_SUM"].to_numpy() < 0) & (side > 0)
    against = rt < 0
    eval_days = np.arange(nd) >= BURN
    ev = di >= BURN
    mon = np.array([days[d][:7] for d in di])
    # ---- the walk-forward projection ----
    proj = np.full(len(T), np.nan)
    cell_of = np.full(len(T), -1)
    months = sorted(set(mon[ev & uni]))
    for M in months:
        rows_m = np.flatnonzero((mon == M) & uni)
        first = di[rows_m].min()
        prior = di < first
        e1, e2 = np.quantile(lrv[prior], [1 / 3, 2 / 3])
        vt = np.digitize(lrv, [e1, e2])
        cell = against.astype(int) * 3 + vt
        cell_of[rows_m] = cell[rows_m]
        pu = prior & uni
        for c in range(6):
            pc = pu & (cell == c)
            if pc.sum() >= MIN_CELL:
                rm = rows_m[cell[rows_m] == c]
                proj[rm] = net[pc].mean()
    # the lag audit: sampled trades re-derived from date-filtered loops; it must fire with today's trades included
    def rederive(i, include_today=False):
        d0 = days[di[i]]
        first_day = min(days[di[j]] for j in np.flatnonzero((mon == mon[i]) & uni))
        cut = (lambda dd: dd <= d0) if include_today else (lambda dd: dd < first_day)
        pr = np.array([cut(days[x]) for x in di])
        e1, e2 = np.quantile(lrv[pr], [1 / 3, 2 / 3])
        c_i = int(against[i]) * 3 + int(np.digitize([lrv[i]], [e1, e2])[0])
        cs = pr & uni & ((against.astype(int) * 3 + np.digitize(lrv, [e1, e2])) == c_i)
        return float(net[cs].mean()) if cs.sum() >= MIN_CELL else float("nan")
    samp = [int(i) for i in rng.choice(np.flatnonzero(ev & uni & np.isfinite(proj)), 6, replace=False)]
    for i in samp:
        v = rederive(i)
        if not np.isclose(v, proj[i], rtol=1e-9, atol=1e-9):
            raise S.GateError(f"[LAG] trade {i}: projection {proj[i]!r} vs the date-filtered loop's {v!r}")
    fired = any(not np.isclose(rederive(i, include_today=True), proj[i], rtol=1e-9, atol=1e-9) for i in samp)
    if not fired:
        raise S.GateError("[LAG] the audit does not fire when today's trades are included")
    log(f"  lag audit: {len(samp)} sampled projections re-derived; fires with today's trades included")

    ue = ev & uni
    take = ue & np.isfinite(proj) & (proj > 0)
    res = {"spec": "D693 STAGE 0 (in-sample development; the principal's per-cell filter at MES)", "cost_rt_usd": cost,
           "universe": {"rows_all": int(uni.sum()), "rows_eval": int(ue.sum()), "per_year_eval": float(ue.sum()) / (eval_days.sum() / 252.0)},
           "audits": {"lag_sampled": samp, "lag_audit_fires_with_today": True}}
    # 1 the oracle
    o = ue & (net > 0)
    res["1_oracle"] = book(net, gross, o, di, days, eval_days, arm, E) | {"share_taken": float(o.sum() / ue.sum())}
    # 2 the books
    res["2_gate_alone"] = book(net, gross, ue, di, days, eval_days, arm, E)
    res["2_filtered"] = book(net, gross, take, di, days, eval_days, arm, E) | {"share_of_universe_taken": float(take.sum() / ue.sum())}
    g, f_ = res["2_gate_alone"], res["2_filtered"]
    log(f"  universe: {int(ue.sum())} eval trades ({res['universe']['per_year_eval']:.0f}/yr); ORACLE net Sharpe {res['1_oracle']['net_sharpe']:+.1f} (mean ${res['1_oracle']['mean_net']:+.2f}, {res['1_oracle']['share_taken']:.2f} taken)")
    for lab, bk in (("GATE ALONE", g), ("FILTERED", f_)):
        log(f"  {lab}: {bk['trades_per_year']:.0f}/yr; net Sharpe {bk['net_sharpe']:+.2f} Sortino {bk['net_sortino']:+.2f}; gross {bk['gross_sharpe']:+.2f}/{bk['gross_sortino']:+.2f}; "
            f"mean net ${bk['mean_net']:+.2f} (t {bk['t_mean_net_clustered']:+.2f}), median ${bk['distribution_net']['median']:+.2f}, hit {bk['distribution_net']['win_rate']:.3f}; "
            f"trimmed ${bk['distribution_net']['mean_trimmed_1pc_both']:+.2f}; max DD ${bk['max_dd']:,.0f}; rho arm {bk['rho_with_macd_arm']:+.3f}")
    log("  by year, filtered net: " + " ".join(f"{y}:{v['net']:+.0f}(n{v['trades']})" for y, v in f_["by_year_net"].items()))
    # 3 accuracy against the oracle
    pe = proj[ue]
    sc = np.where(np.isfinite(pe), pe, np.nanmin(pe) - 1.0)
    acc = FO.assess(sc, take[ue], gross[ue], net[ue])
    fin = np.isfinite(pe)
    acc["calibration"] = FO.calibration(pe[fin], net[ue][fin], n_bins=6) if np.unique(pe[fin]).size >= 2 else None
    res["3_accuracy"] = acc
    c = acc["confusion_vs_oracle"]
    log(f"  ACCURACY: take {c['take_rate']:.3f} precision {c['precision']:.3f} (base {c['base_rate']:.3f}) recall {c['recall']:.3f} bal-acc {c['balanced_accuracy']:.3f} "
        f"AUC {acc['auc_vs_oracle_label']:.3f} Spearman {acc['spearman_score_vs_gross']:+.3f}; capture {acc['capture']['capture_of_oracle']:+.3f}; "
        f"calibration slope {acc['calibration']['slope'] if acc['calibration'] else float('nan'):+.3f}")
    # 4 the partial-oracle curve
    ne_u, di_u = net[ue], di[ue]
    z = FO.normal_scores(ne_u)
    curves = {}
    for q in sorted({round(float(take.sum() / ue.sum()), 3), 0.5}):
        if q <= 0:
            continue
        cur = []
        for rho in RHOS:
            sh, sp = [], []
            for _ in range(N_DRAW):
                s = FO._partial(z, rho, rng)
                keep = FO.top_fraction(s, q)
                d = np.bincount(di_u[keep], weights=ne_u[keep], minlength=nd)[eval_days]
                sd = d.std(ddof=1)
                sh.append(d.mean() / sd * math.sqrt(252) if sd > 0 else np.nan)
                sp.append(FO.spearman(s, gross[ue]))
            cur.append({"rho": rho, "net_sharpe_mean": float(np.nanmean(sh)), "p05": float(np.nanpercentile(sh, 5)), "p95": float(np.nanpercentile(sh, 95)), "spearman_mean": float(np.mean(sp))})
        curves[f"q{q}"] = cur
        log(f"  CURVE q {q}: " + " ".join(f"rho{x['rho']}:{x['net_sharpe_mean']:+.2f}(sp {x['spearman_mean']:+.3f})" for x in cur))
    res["4_partial_oracle_curves"] = curves
    # 5 the rotation null of the take grid, within the universe
    nslots = int(slot.max()) + 1
    grid_take = np.zeros((nd, nslots), bool); grid_net = np.zeros((nd, nslots)); grid_uni = np.zeros((nd, nslots), bool)
    grid_take[di[take], slot[take]] = True; grid_net[di[ue], slot[ue]] = net[ue]; grid_uni[di[ue], slot[ue]] = True
    null = []
    for k in S.rot_ks(nd)[1:]:
        rt_ = np.roll(grid_take, int(k), axis=0) & grid_uni
        d = np.where(rt_, grid_net, 0.0).sum(1)[eval_days]
        sd = d.std(ddof=1)
        null.append(d.mean() / sd * math.sqrt(252) if sd > 0 else np.nan)
    res["5_rotation_null_net_sharpe"] = S.blk(f_["net_sharpe"], np.array(null))
    r5 = res["5_rotation_null_net_sharpe"]
    log(f"  NULL: filtered net Sharpe {f_['net_sharpe']:+.2f} against rotation p50 {r5['p50']:+.2f} p95 {r5['p95']:+.2f} (pct {r5['pct_rank']:.3f})")
    # 6 the cells in hindsight
    e1, e2 = np.quantile(lrv, [1 / 3, 2 / 3])
    cell_h = against.astype(int) * 3 + np.digitize(lrv, [e1, e2])
    names = {0: "with_low_vol", 1: "with_mid_vol", 2: "with_high_vol", 3: "against_low_vol", 4: "against_mid_vol", 5: "against_high_vol"}
    res["6_cells_hindsight_descriptive"] = {names[c_]: {"n": int((uni & (cell_h == c_)).sum()), "mean_net": float(net[uni & (cell_h == c_)].mean()) if (uni & (cell_h == c_)).any() else None,
                                                        "win_rate": float((net[uni & (cell_h == c_)] > 0).mean()) if (uni & (cell_h == c_)).any() else None} for c_ in range(6)}
    res["6_walk_forward_take_share_by_cell"] = {names[c_]: float(take[ue & (cell_of == c_)].mean()) if (ue & (cell_of == c_)).any() else None for c_ in range(6)}
    log("  CELLS (hindsight): " + " | ".join(f"{k} n{v['n']} ${v['mean_net']:+.2f} win {v['win_rate']:.2f}" for k, v in res["6_cells_hindsight_descriptive"].items() if v["n"]))
    log("  walk-forward take share by cell: " + " ".join(f"{k}:{v:.2f}" for k, v in res["6_walk_forward_take_share_by_cell"].items() if v is not None))
    # the declared reading
    cal_ok = bool(acc["calibration"] is not None and acc["calibration"]["slope"] > 0)
    res["reading"] = {"a_calibration_slope_positive": cal_ok, "b_beats_gate_alone": bool(f_["net_sharpe"] > g["net_sharpe"]),
                      "c_above_rotation_p95": bool(r5["above_p95"])}
    res["reading"]["useful_in_sample"] = bool(all(res["reading"].values()))
    log(f"  READING: {res['reading']}")
    res["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o_: o_.item() if hasattr(o_, "item") else str(o_)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.exit(run(a.data_root) if a.run else 1)

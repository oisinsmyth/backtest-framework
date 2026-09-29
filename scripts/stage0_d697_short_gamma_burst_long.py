"""D697 STAGE 0 -- the principal's move-triggered construction for the short-gamma long: a fast rise since the prior
settlement, held to the close, on 1 MES (the principal, 2026-09-29: "Move-triggered, measured since the prior
settlement, hold to close (with room for conditional exits)"; then the trigger and window).

    uv run python scripts/stage0_d697_short_gamma_burst_long.py --run --data-root "<main checkout>/data"

In-sample on D688's panel, 2016-01-05 -> 2023-12-29; nothing on or after 2024-01-01 is read. No filter is fitted: the
expected-profit filter is to be designed with the principal from this run.

THE CONSTRUCTION (every parameter the principal's):
  day        G_SUM < 0 (SPX GEX + the ES options book at the prior settlement; known before the open)
  price      P(t) at each minute of the regular session (09:30 = the open; else the close of the bar a minute before)
  level      L(t) = log P(t) - log S_prev >= 0.25 sigma_d   (sigma_d: the std of daily settlement returns over the
             20 sessions through d-1, D688's)
  speed      R15(t) = log P(t) - log P(t-15) >= 1.5 x sigma_15, sigma_15 = sigma_1m x sqrt(15), sigma_1m = the root
             mean of the prior 20 sessions' variance of 1-minute log returns (prior-only)
  crossing   the level condition must have been FALSE at some minute of the session at or before t ("must cross
             after the open": a gap above the level that never dips below it does not trade)
  window     t from 09:45 (the first minute with 15 minutes of session behind it) to 15:00 inclusive
  entry      the FIRST minute both conditions hold: buy 1 MES at P(t); one trade a day
  exit       16:00 (the close of the 15:59 bar)
  cost       $4.42 a round trip (1 MES); the bar: net > 0
DECLARED OUTPUTS
  1  the book (CLAUDE.md's four groups): trades a year, daily net and gross Sharpe and Sortino, mean and median net,
     the NW t of the mean net per trade, hit rate, payoff, skew, kurtosis, trimmed means (ex-top, ex-bottom, both), by
     year, the top five trades, max drawdown, breakeven round trip, rho with the admitted MACD arm
  2  the oracle (net > 0) on these trades: its share, mean net and Sharpe (the ceiling for the later filter)
  3  the TIME-MATCHED DRIFT CONTROL: for each trade, the mean gross of buying at the same minute on EVERY short-gamma
     day and holding to 16:00; the trade's excess over it (the trigger's information beyond the short-gamma day's
     drift from that time; D689's drift caveat)
  4  controls, not traded: the same long trigger on LONG-gamma days, and the downward mirror (level <= -0.25 sigma,
     speed <= -1.5 sigma_15, crossed after the open, short to 16:00) on short-gamma days
  5  the null: the enumerated day-rotation of the short-gamma label (k = 10 .. n-10) against the triggered long trades
     of every day, the mean net per trade; p05/p50/p95 and percentile
  6  the path for conditional exits: per trade, the maximum favourable and adverse excursion to the close, and the
     mean P&L at +15, +30, +60, +120 minutes and at the close; the trigger-time distribution
DECLARED READING (in-sample, not a verdict): the construction HAS AN EDGE WORTH FILTERING if (a) its mean net per
trade > 0, (b) its mean gross exceeds the time-matched drift control with NW t >= 2, and (c) its mean net is above the
p95 of the rotation null. No parameter is tuned after the run.

Output data/d697_short_gamma_burst_long.json: statistics only, no per-date GEX (SqueezeMetrics, under the permission of
2026-09-28).
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

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage0_d688_gamma_close as S  # noqa: E402  (importing defines, never runs)

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d697_short_gamma_burst_long.json"
D688_JSON = REPO / "data" / "d688_gamma_close.json"
LEVEL_K, SPEED_K, SPEED_WIN = 0.25, 1.5, 15
FIRST_J, LAST_J, CLOSE_J = 15, 330, 390          # minutes after 09:30: 09:45, 15:00, 16:00
TRAIL = 20
HORIZONS = (15, 30, 60, 120)


def P(*a, **k):
    print(*a, **k, flush=True)


def panel(data_root: Path, log=P):
    """D688's panel (G_SUM, S_prev, sigma_d), D688's beta_G reproduced first, and the minute price grid."""
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
    S.guard_window(D.index, "D697 panel")
    r = 100 * np.log(D["P1530"].to_numpy(float) / D["S_prev"].to_numpy(float)); R2 = 1e4 * np.log(D["P1600"].to_numpy(float) / D["P1530"].to_numpy(float))
    f688, _ = S.gamma_regression(R2, D["G_SUM"].to_numpy(float), r, D["sig"].to_numpy(float), D["V"].to_numpy(float), D["A_L"].to_numpy(float), null=False)
    ref = json.loads(D688_JSON.read_text(encoding="utf-8"))["gate1"]["G1"]["beta_G"]
    if f688["beta_G"] != ref:
        raise S.GateError(f"[REPRO] beta_G {f688['beta_G']!r} vs D688's {ref!r}")
    log(f"  D688 REPRODUCED on {len(D)} sessions ({time.time() - t0:.0f} s)")
    # the minute price grid over ALL loaded sessions (the prior-20 minute sigma needs the warm-up), then the panel's rows
    b = I["bars"]
    alld = I["days"]
    close = b.pivot(index="day", columns="hhmm", values="close").reindex(alld)
    mins = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=k)).strftime("%H:%M") for k in range(390)]
    close = close.reindex(columns=mins).ffill(axis=1)
    op = b[b["hhmm"] == "09:30"].set_index("day")["open"].reindex(alld).to_numpy(float)
    PM = np.column_stack([op, close.to_numpy(float)])                     # 391 columns: 09:30, 09:31 .. 16:00
    lr = np.diff(np.log(PM[:, 1:]), axis=1)                               # within-session 1-minute log returns
    dvar = np.nanvar(lr, axis=1, ddof=1)
    s1m = np.sqrt(pd.Series(dvar).rolling(TRAIL).mean().shift(1).to_numpy())
    pos = {d: i for i, d in enumerate(alld)}
    idx = np.array([pos[d] for d in D.index])
    return D, PM[idx], s1m[idx]


def first_trigger(L, R, lev, spd, sign):
    """The first minute in [FIRST_J, LAST_J] where sign*L >= lev, sign*R >= spd, and sign*L < lev at some minute <= t."""
    n = L.shape[0]
    j_of = np.full(n, -1)
    below = np.maximum.accumulate(sign * L < lev[:, None], axis=1)
    ok = (sign * L >= lev[:, None]) & (sign * R >= spd[:, None]) & below
    ok[:, :FIRST_J] = False
    ok[:, LAST_J + 1:] = False
    has = ok.any(1)
    j_of[has] = ok[has].argmax(1)
    return j_of


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    D, PM, s1m = panel(data_root, log)
    days = D.index.to_numpy().astype(str)
    nd = len(days)
    E = S.d685()
    mes = E.cost_spec("ES", "micro")
    cost, usd = mes["cost_rt_usd"], mes["usd_per_point"]
    arm = E.load_arm()
    Sprev = D["S_prev"].to_numpy(float); sig_d = D["sig"].to_numpy(float) / 1e4     # sigma_d in log units
    short = D["G_SUM"].to_numpy(float) < 0
    L = np.log(PM / Sprev[:, None])
    R = np.full_like(L, np.nan)
    R[:, SPEED_WIN:] = np.log(PM[:, SPEED_WIN:] / PM[:, :-SPEED_WIN])
    lev = LEVEL_K * sig_d
    spd = SPEED_K * s1m * math.sqrt(SPEED_WIN)
    valid = np.isfinite(lev) & np.isfinite(spd) & np.isfinite(PM).all(1)
    j_up = np.where(valid, first_trigger(L, R, lev, spd, +1), -1)
    j_dn = np.where(valid, first_trigger(L, R, lev, spd, -1), -1)
    # a second implementation of the trigger on sampled days (a plain loop), and it must fire on a broken rule
    def loop_trigger(i, sign, need_cross=True):
        seen = False
        for j in range(0, CLOSE_J + 1):
            if sign * L[i, j] < lev[i]:
                seen = True
            if FIRST_J <= j <= LAST_J and sign * L[i, j] >= lev[i] and sign * R[i, j] >= spd[i] and (seen or not need_cross):
                return j
        return -1
    rng = np.random.default_rng(697)
    samp = rng.choice(np.flatnonzero(valid), 40, replace=False)
    for i in samp:
        if loop_trigger(i, +1) != j_up[i] or loop_trigger(i, -1) != j_dn[i]:
            raise S.GateError(f"[TRIGGER] day {days[i]}: vectorised and loop triggers disagree")
    fired = any(loop_trigger(i, +1, need_cross=False) != j_up[i] for i in np.flatnonzero(valid & (L[:, 0] >= lev)))
    if not fired:
        raise S.GateError("[TRIGGER] the crossing audit does not fire when the crossing rule is dropped")
    log(f"  trigger audit: 40 days re-derived by a loop; the crossing rule matters on gap days")

    def trades(mask_days, j_of, sign):
        ii = np.flatnonzero(mask_days & (j_of >= 0))
        jj = j_of[ii]
        entry = PM[ii, jj]; exitp = PM[ii, CLOSE_J]
        gross = sign * (exitp - entry) * usd
        return ii, jj, gross, gross - cost

    ii, jj, gross, net = trades(short, j_up, +1)
    nt = len(ii)
    yrs = nd / 252.0
    daily = np.zeros(nd); daily[ii] = net
    dailyg = np.zeros(nd); dailyg[ii] = gross
    nwn = E.nw_mean(net, 5)
    dist = E.dist(net)
    yr = np.array([days[i][:4] for i in ii])
    book = {"trades": nt, "trades_per_year": nt / yrs, "share_of_short_gamma_days": float(nt / short.sum()),
            "net_sharpe": E.sharpe(daily), "net_sortino": E.sortino(daily), "gross_sharpe": E.sharpe(dailyg), "gross_sortino": E.sortino(dailyg),
            "mean_net": float(net.mean()), "nw_t_mean_net": nwn["t"], "mean_gross": float(gross.mean()), "breakeven_rt": float(gross.mean()),
            "total_net": float(net.sum()), "max_dd": E.max_dd(daily), "vol_ann": float(daily.std(ddof=1) * math.sqrt(252)), "distribution_net": dist,
            "by_year": {y: {"trades": int((yr == y).sum()), "net": float(net[yr == y].sum()), "mean_net": float(net[yr == y].mean())} for y in sorted(set(yr))},
            "top5": [{"session": days[ii[k]], "entry": (pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=int(jj[k]))).strftime("%H:%M"), "net": float(net[k])} for k in np.argsort(-np.abs(net))[:5]]}
    x = np.array([daily[np.searchsorted(days, d)] if d in set(days) else 0.0 for d in arm["days"]])
    book["rho_with_macd_arm"] = float(np.corrcoef(x, arm["net"])[0, 1]) if x.std() > 0 else float("nan")
    res = {"spec": "D697 STAGE 0 (in-sample; the principal's move-triggered short-gamma long, held to the close, 1 MES)", "cost_rt_usd": cost,
           "sessions": nd, "short_gamma_sessions": int(short.sum()), "audits": {"trigger_loop_days": [days[i] for i in samp[:5]], "crossing_audit_fires": True},
           "1_book": book}
    log(f"  BOOK: {nt} trades ({nt / yrs:.0f}/yr, {book['share_of_short_gamma_days']:.2f} of short-gamma days); net Sharpe {book['net_sharpe']:+.2f} Sortino {book['net_sortino']:+.2f}; "
        f"gross {book['gross_sharpe']:+.2f}/{book['gross_sortino']:+.2f}; mean net ${book['mean_net']:+.2f} (NW t {book['nw_t_mean_net']:+.2f}), median ${dist['median']:+.2f}, "
        f"hit {dist['win_rate']:.3f}, payoff {dist['payoff']:.2f}; trimmed ${dist['mean_trimmed_1pc_both']:+.2f} (ex-top ${dist['mean_ex_top_1pc']:+.2f}); "
        f"max DD ${book['max_dd']:,.0f}; rho arm {book['rho_with_macd_arm']:+.3f}")
    log("  by year: " + " ".join(f"{y}:{v['net']:+.0f}(n{v['trades']})" for y, v in book["by_year"].items()))
    # 2 the oracle
    o = net > 0
    od = np.zeros(nd); od[ii[o]] = net[o]
    res["2_oracle"] = {"share": float(o.mean()), "mean_net": float(net[o].mean()), "net_sharpe": E.sharpe(od), "trades_per_year": float(o.sum() / yrs)}
    log(f"  ORACLE: {o.mean():.3f} of trades win; mean net ${net[o].mean():+.2f}; Sharpe {res['2_oracle']['net_sharpe']:+.1f}")
    # 3 the time-matched drift control
    ctrl = np.array([np.nanmean((PM[short, CLOSE_J] - PM[short, j]) * usd) for j in jj])
    excess = gross - ctrl
    nwe = E.nw_mean(excess, 5)
    res["3_drift_control"] = {"mean_control_gross": float(ctrl.mean()), "mean_trade_gross": float(gross.mean()), "mean_excess": nwe["mean"], "nw_t_excess": nwe["t"]}
    log(f"  DRIFT CONTROL: buying at the same minutes on every short-gamma day grosses ${ctrl.mean():+.2f}; the trades ${gross.mean():+.2f}; excess ${nwe['mean']:+.2f} (NW t {nwe['t']:+.2f})")
    # 4 controls not traded
    ci, cj, cg, cn = trades(~short, j_up, +1)
    mi, mj, mg, mn = trades(short, j_dn, -1)
    res["4_controls"] = {"long_trigger_on_long_gamma_days": {"trades": int(len(ci)), "per_year": len(ci) / yrs, "mean_gross": float(cg.mean()), "mean_net": float(cn.mean()), "hit": float((cn > 0).mean())},
                         "down_mirror_short_on_short_gamma_days": {"trades": int(len(mi)), "per_year": len(mi) / yrs, "mean_gross": float(mg.mean()) if len(mg) else None, "mean_net": float(mn.mean()) if len(mn) else None, "hit": float((mn > 0).mean()) if len(mn) else None}}
    c4 = res["4_controls"]
    log(f"  CONTROLS: long trigger on long-gamma days {len(ci)} trades, gross ${cg.mean():+.2f} net ${cn.mean():+.2f}; down mirror on short-gamma days {len(mi)} trades, "
        f"gross ${c4['down_mirror_short_on_short_gamma_days']['mean_gross']:+.2f} net ${c4['down_mirror_short_on_short_gamma_days']['mean_net']:+.2f}")
    # 5 the rotation null of the short-gamma label
    trig_net = np.full(nd, np.nan)
    ai, aj, ag, an = trades(np.ones(nd, bool), j_up, +1)
    trig_net[ai] = an
    null = []
    for k in S.rot_ks(nd)[1:]:
        rot = np.roll(short, int(k))
        v = trig_net[rot & np.isfinite(trig_net)]
        null.append(v.mean() if len(v) else np.nan)
    res["5_rotation_null_mean_net"] = S.blk(float(net.mean()), np.array(null))
    r5 = res["5_rotation_null_mean_net"]
    log(f"  NULL: mean net ${net.mean():+.2f} against the rotation of the short-gamma label: p50 ${r5['p50']:+.2f} p95 ${r5['p95']:+.2f} (pct {r5['pct_rank']:.3f})")
    # 6 the path, for conditional exits
    mfe = np.array([(np.nanmax(PM[i, j:CLOSE_J + 1]) - PM[i, j]) * usd for i, j in zip(ii, jj)])
    mae = np.array([(np.nanmin(PM[i, j:CLOSE_J + 1]) - PM[i, j]) * usd for i, j in zip(ii, jj)])
    path = {}
    for h in HORIZONS:
        jx = np.minimum(jj + h, CLOSE_J)
        path[f"+{h}m"] = float(np.mean((PM[ii, jx] - PM[ii, jj]) * usd))
    path["close"] = float(gross.mean())
    tt = np.array([(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=int(j))).hour for j in jj])
    res["6_path"] = {"mean_gross_by_horizon": path, "mfe": {"mean": float(mfe.mean()), "median": float(np.median(mfe))}, "mae": {"mean": float(mae.mean()), "median": float(np.median(mae))},
                     "trigger_hour_counts": {int(h): int((tt == h).sum()) for h in sorted(set(tt))},
                     "mean_gross_by_trigger_hour": {int(h): float(gross[tt == h].mean()) for h in sorted(set(tt))}}
    log("  PATH: mean gross " + " ".join(f"{k} ${v:+.2f}" for k, v in path.items()) + f"; MFE mean ${mfe.mean():.0f} (median ${np.median(mfe):.0f}), MAE mean ${mae.mean():.0f} (median ${np.median(mae):.0f})")
    log("  trigger hour: " + " ".join(f"{h}:{res['6_path']['trigger_hour_counts'][h]}(${res['6_path']['mean_gross_by_trigger_hour'][h]:+.1f})" for h in res["6_path"]["trigger_hour_counts"]))
    # the declared reading
    res["reading"] = {"a_mean_net_positive": bool(net.mean() > 0), "b_beats_drift_control_t2": bool(nwe["mean"] > 0 and nwe["t"] >= 2),
                      "c_above_rotation_p95": bool(r5["above_p95"])}
    res["reading"]["edge_worth_filtering"] = bool(all(res["reading"].values()))
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

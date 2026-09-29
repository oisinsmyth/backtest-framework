"""D699 STAGE 0 -- the principal's log MACD on short-gamma days: a normalised 15-minute log MACD (12/26/9) on the
gap-spliced ES day-session series, long on 1 MES, in three variants with hysteresis (the principal, 2026-09-30:
"Reopen it, 15-minute bars, three variants, each signal variant plus the combine OR'd, Add hysteresis, you pick the
threshold and normalise the log MACD"). Design: docs/decisions/D699-STAGE-0-DESIGN-the-gamma-gated-15-minute-log-macd-long.md,
committed before this runner.

    uv run python scripts/stage0_d699_gamma_macd_long.py --selftest
    uv run python scripts/stage0_d699_gamma_macd_long.py --run --data-root "<main checkout>/data"

In-sample on D688's panel, 2016-01-05 -> 2023-12-29; nothing on or after 2024-01-01 is read.

THE CONSTRUCTION (the design's; nothing here is tuned)
  day        G_SUM < 0 (SPX GEX + the ES options book at the prior settlement; D688's panel, reproduced first)
  series     26 bar closes a session (09:45 .. 16:00, every 15 minutes, from the 1-minute day-session bars);
             x = the running sum of WITHIN-session 15-minute log returns; a session's first return is
             log(P 09:45 / P open); the overnight gap is dropped; sessions with an unfilled bar are skipped like a gap
  MACD       M = EMA12(x) - EMA26(x), H = M - EMA9(M), alpha = 2/(n+1), continuous across the spliced sessions
  normalise  z_H = H / (s15 * |w|), z_R = dH / (s15 * |dw|); w is H's impulse response to one return, |w| = 0.3379,
             |dw| = 0.0867; s15 = the sd of the spliced 15-minute returns of the 20 sessions before d (prior-only)
  variants   V1 HIST enter z_H > +0.5, exit z_H < -0.5; V2 ROC enter z_R > +1.0, exit z_R < -1.0; V3 OR = V1 or V2
             (each its own machine); started flat each day
  timing     decide at each bar close; entries at the 09:45 .. 15:45 closes; fill one minute after the deciding close;
             flat at 16:00; $4.42 a round trip on 1 MES, every trade
DECLARED OUTPUTS: the oracle; the book (four groups, rho with the admitted MACD arm); the time-matched drift control;
the timing null (the day-rotation of the position SCHEDULE among short-gamma days, k = 10 .. n-10, per variant and the
family maximum); the gamma-label null (reported); controls (long-gamma days, the short mirror, always-long 09:46 -> 16:00).
DECLARED READING per variant: (a) mean net per trade > 0, (b) mean gross beats the drift control at NW t >= 2,
(c) mean net per trade above the p95 of the family-maximum timing null.

Output data/d699_gamma_macd_long.json: statistics only, no per-date GEX (SqueezeMetrics, under the permission of
2026-09-28).
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import lfilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import stage0_d688_gamma_close as S  # noqa: E402  (importing defines, never runs)

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d699_gamma_macd_long.json"
D688_JSON = REPO / "data" / "d688_gamma_close.json"
FAST, SLOW, SIGN_N = 12, 26, 9
NORM_H_DECLARED, NORM_R_DECLARED = 0.3379, 0.0867
BANDS = {"V1_HIST": 0.5, "V2_ROC": 1.0}
BAR_J = np.arange(15, 391, 15)                   # the 26 bar closes, in minutes after 09:30: 09:45 .. 16:00
NB = len(BAR_J)
LAST_ENTRY_B = 24                                # 15:45
CLOSE_J = 390
TRAIL = 20
VARIANTS = ("V1_HIST", "V2_ROC", "V3_OR")


def P(*a, **k):
    print(*a, **k, flush=True)


# ------------------------------------------------------------------ the signal
def ema(x: np.ndarray, n: int) -> np.ndarray:
    """y0 = x0, y_t = a x_t + (1 - a) y_{t-1}, a = 2 / (n + 1)."""
    a = 2.0 / (n + 1)
    y, _ = lfilter([a], [1.0, -(1.0 - a)], x, zi=[(1.0 - a) * x[0]])
    return y


def hist(x: np.ndarray) -> np.ndarray:
    m = ema(x, FAST) - ema(x, SLOW)
    return m - ema(m, SIGN_N)


def kernel_norms(nlag: int = 600) -> tuple[float, float]:
    """|w| and |dw|: H's response at lag k to a unit return at lag 0 (a unit step in x), and its first difference."""
    x = np.concatenate([np.zeros(50), np.ones(nlag)])
    w = hist(x)[50:]
    dw = np.diff(np.concatenate([[0.0], w]))
    return float(np.sqrt((w ** 2).sum())), float(np.sqrt((dw ** 2).sum()))


def spliced_returns(PB: np.ndarray, splice: bool = True) -> tuple[np.ndarray, np.ndarray]:
    """PB: n x 27 (the open, then the 26 bar closes). Returns (valid, R n x 26); with splice=False the first return of a
    session is measured from the PRIOR session's 16:00 close (the gap left in; the right-quantity contrast only)."""
    valid = np.isfinite(PB).all(1) & (PB > 0).all(1)
    R = np.full((PB.shape[0], NB), np.nan)
    R[valid] = np.diff(np.log(PB[valid]), axis=1)
    if not splice:
        vi = np.flatnonzero(valid)
        R[vi[1:], 0] = np.log(PB[vi[1:], 1] / PB[vi[:-1], NB])
    return valid, R


def signals(PB: np.ndarray, splice: bool = True) -> dict:
    """z_H and z_R (n x 26, NaN off the series or without 20 prior sessions), from the spliced series."""
    nh, nr = kernel_norms()
    valid, R = spliced_returns(PB, splice)
    vi = np.flatnonzero(valid)
    r = R[vi].ravel()
    x = np.cumsum(r)
    h = hist(x)
    dh = np.diff(np.concatenate([[h[0]], h]))
    s15 = np.full(PB.shape[0], np.nan)
    for q in range(TRAIL, len(vi)):
        s15[vi[q]] = np.std(R[vi[q - TRAIL:q]].ravel(), ddof=1)
    zH = np.full((PB.shape[0], NB), np.nan); zR = np.full((PB.shape[0], NB), np.nan)
    zH[vi] = h.reshape(-1, NB); zR[vi] = dh.reshape(-1, NB)
    zH /= (s15 * nh)[:, None]; zR /= (s15 * nr)[:, None]
    return {"valid": valid, "s15": s15, "zH": zH, "zR": zR, "norm_h": nh, "norm_r": nr}


def machine(z: np.ndarray, band: float, sign: int) -> np.ndarray:
    """The hysteresis state after each bar close (n x 26): enter when sign*z > band (bars 0 .. LAST_ENTRY_B), exit when
    sign*z < -band; flat at the start of each day. NaN z changes nothing."""
    n = z.shape[0]
    on = np.zeros(n, bool)
    st = np.zeros((n, NB), bool)
    for b in range(NB):
        s = sign * z[:, b]
        enter = ~on & (s > band) & (b <= LAST_ENTRY_B)
        leave = on & (s < -band)
        on = (on | enter) & ~leave
        st[:, b] = on
    return st


def states(sig: dict, sign: int) -> dict:
    v1 = machine(sig["zH"], BANDS["V1_HIST"], sign)
    v2 = machine(sig["zR"], BANDS["V2_ROC"], sign)
    return {"V1_HIST": v1, "V2_ROC": v2, "V3_OR": v1 | v2}


def trade_list(st: np.ndarray, rows: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(row, fill-in minute, fill-out minute) for every long run in st[rows]; fills one minute after the deciding
    close; a run still open, or closed by the 16:00 bar, exits at 16:00."""
    out_i, out_a, out_b = [], [], []
    s = st[rows]
    prev = np.concatenate([np.zeros((len(rows), 1), bool), s[:, :-1]], axis=1)
    ent = s & ~prev
    ext = ~s & prev
    for r_, i in enumerate(rows):
        e = np.flatnonzero(ent[r_]); x = np.flatnonzero(ext[r_])
        for b in e:
            later = x[x > b]
            ja = BAR_J[b] + 1
            jb = min(BAR_J[later[0]] + 1, CLOSE_J) if len(later) else CLOSE_J
            out_i.append(i); out_a.append(ja); out_b.append(jb)
    return np.array(out_i, int), np.array(out_a, int), np.array(out_b, int)


# ------------------------------------------------------------------ the second implementation (the lag audit)
def loop_trades(PB: np.ndarray, rows, bands: dict, which: str, sign: int = 1) -> list:
    """Pure Python from the raw bar prices: the spliced returns, three EMA recursions, the trailing sd, the norms from an
    impulse loop, the hysteresis and the fills. Never calls the vectorised functions above."""
    def ema_loop(xs, n):
        a = 2.0 / (n + 1); out = []; y = None
        for v in xs:
            y = v if y is None else a * v + (1 - a) * y
            out.append(y)
        return out

    def hist_loop(xs):
        m = [f - s for f, s in zip(ema_loop(xs, FAST), ema_loop(xs, SLOW))]
        return [mi - si for mi, si in zip(m, ema_loop(m, SIGN_N))]

    imp = hist_loop([0.0] * 50 + [1.0] * 600)[50:]
    nh = math.sqrt(sum(v * v for v in imp))
    nr = math.sqrt(sum((imp[k] - (imp[k - 1] if k else 0.0)) ** 2 for k in range(len(imp))))
    days, rets = [], []
    for i in range(PB.shape[0]):
        row = [float(v) for v in PB[i]]
        if all(math.isfinite(v) and v > 0 for v in row):
            days.append(i); rets.append([math.log(row[k + 1] / row[k]) for k in range(NB)])
    xs, acc = [], 0.0
    for rr in rets:
        for v in rr:
            acc += v; xs.append(acc)
    h = hist_loop(xs)
    pos = {d: q for q, d in enumerate(days)}
    out = []
    for i in rows:
        q = pos.get(int(i))
        if q is None or q < TRAIL:
            continue
        s15 = statistics.stdev([v for rr in rets[q - TRAIL:q] for v in rr])
        on1 = on2 = False; held = []
        for b in range(NB):
            t = q * NB + b
            z1 = sign * h[t] / (s15 * nh)
            z2 = sign * (h[t] - (h[t - 1] if t else h[0])) / (s15 * nr)
            if not on1 and z1 > bands["V1_HIST"] and b <= LAST_ENTRY_B:
                on1 = True
            elif on1 and z1 < -bands["V1_HIST"]:
                on1 = False
            if not on2 and z2 > bands["V2_ROC"] and b <= LAST_ENTRY_B:
                on2 = True
            elif on2 and z2 < -bands["V2_ROC"]:
                on2 = False
            held.append({"V1_HIST": on1, "V2_ROC": on2, "V3_OR": on1 or on2}[which])
        was, ja = False, None
        for b in range(NB):
            if held[b] and not was:
                ja = int(BAR_J[b]) + 1
            if was and not held[b]:
                out.append((int(i), ja, min(int(BAR_J[b]) + 1, CLOSE_J))); ja = None
            was = held[b]
        if ja is not None:
            out.append((int(i), ja, CLOSE_J))
    return out


def lag_audit(st_by_variant: dict, PB, rows) -> None:
    for v in VARIANTS:
        ii, a, b = trade_list(st_by_variant[v], rows)
        vec = sorted(zip(ii.tolist(), a.tolist(), b.tolist()))
        ref = sorted(loop_trades(PB, rows, BANDS, v))
        assert vec == ref, f"[LAG] {v}: the vectorised trades ({len(vec)}) differ from the loop's ({len(ref)})"


# ------------------------------------------------------------------ the book
def book_stats(E, net, gross, ii, ja, jb, days, nd, n_univ, yrs) -> dict:
    daily = np.zeros(nd); np.add.at(daily, ii, net)
    dailyg = np.zeros(nd); np.add.at(dailyg, ii, gross)
    dist = E.dist(net) if len(net) > 1 else {}
    nwn = E.nw_mean(net, 5) if len(net) > 5 else {"t": float("nan")}
    yr = np.array([days[i][:4] for i in ii])
    crash = np.array([("2020-02-01" <= days[i] < "2020-05-01") for i in ii], bool)
    hrs = np.array([(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=int(j))).hour for j in ja])
    top = np.argsort(-np.abs(net))[:5]
    return {"trades": int(len(net)), "trades_per_year": len(net) / yrs, "exposure_of_universe_session_time": float((jb - ja).sum() / (n_univ * CLOSE_J)),
            "mean_hold_min": float((jb - ja).mean()) if len(net) else None,
            "net_sharpe": E.sharpe(daily), "net_sortino": E.sortino(daily), "gross_sharpe": E.sharpe(dailyg), "gross_sortino": E.sortino(dailyg),
            "mean_net": float(net.mean()), "mean_gross": float(gross.mean()), "nw_t_mean_net": nwn["t"], "breakeven_rt": float(gross.mean()),
            "total_net": float(net.sum()), "max_dd": E.max_dd(daily), "vol_ann": float(daily.std(ddof=1) * math.sqrt(252)), "distribution_net": dist,
            "by_year": {y: {"trades": int((yr == y).sum()), "net": float(net[yr == y].sum())} for y in sorted(set(yr))},
            "ex_feb_apr_2020": {"trades": int((~crash).sum()), "mean_net": float(net[~crash].mean()), "total_net": float(net[~crash].sum())},
            "entries_by_hour": {int(h): {"n": int((hrs == h).sum()), "mean_gross": float(gross[hrs == h].mean())} for h in sorted(set(hrs))},
            "top5": [{"session": days[ii[k]], "in": int(ja[k]), "out": int(jb[k]), "net": float(net[k])} for k in top]}, daily


def hold_matrix(ja, jb, rows_of_trade, rows):
    """n_rows x 390: 1 where the schedule of that row holds the minute return (j -> j+1)."""
    pos = {int(r): q for q, r in enumerate(rows)}
    Hm = np.zeros((len(rows), CLOSE_J))
    for i, a, b in zip(rows_of_trade, ja, jb):
        Hm[pos[int(i)], a:b] += 1.0
    return Hm


def core(PM: np.ndarray, pidx: np.ndarray, short: np.ndarray, days: np.ndarray, cost: float, usd: float, E, log=P,
         audit_days: int = 40, seed: int = 699) -> tuple[dict, dict]:
    """PM: every loaded session x 391 minute prices (09:30 open, then 09:31 .. 16:00); pidx: the panel's rows in PM;
    short: the panel's G_SUM < 0; days: the panel's dates. Returns (res, daily nets by variant, for the arm's rho)."""
    PB = PM[:, np.concatenate([[0], BAR_J])]
    sig = signals(PB)
    nh, nr = sig["norm_h"], sig["norm_r"]
    if (round(nh, 4), round(nr, 4)) != (NORM_H_DECLARED, NORM_R_DECLARED):
        raise S.GateError(f"[NORM] |w| {nh:.6f}, |dw| {nr:.6f} against the declared {NORM_H_DECLARED}, {NORM_R_DECLARED}")
    gap = signals(PB, splice=False)
    both = np.isfinite(sig["zH"]) & np.isfinite(gap["zH"])
    if np.allclose(sig["zH"][both], gap["zH"][both]):
        raise S.GateError("[QUANTITY] the spliced MACD equals the one with the gaps left in")
    nd = len(days)
    ok = sig["valid"][pidx] & np.isfinite(sig["s15"][pidx]) & np.isfinite(PM[pidx]).all(1)
    ST = states(sig, +1)
    STm = states(sig, -1)
    # the lag audit, and it must fire on a book whose decision reads the next close
    rng = np.random.default_rng(seed)
    samp = np.sort(pidx[rng.choice(np.flatnonzero(ok & short), min(audit_days, int((ok & short).sum())), replace=False)])
    lag_audit(ST, PB, samp)
    peek = {"zH": np.concatenate([sig["zH"][:, 1:], sig["zH"][:, -1:]], axis=1), "zR": np.concatenate([sig["zR"][:, 1:], sig["zR"][:, -1:]], axis=1)}
    S.expect_raise(lambda: lag_audit(states(peek, +1), PB, samp), "a book that reads the next close", log)
    log(f"  lag audit: {len(samp)} short-gamma days re-derived by a pure-Python loop from the raw prices; |w| {nh:.4f}, |dw| {nr:.4f}")
    # the sign audit, in money
    up = np.linspace(100.0, 110.0, 391)[None, :]
    if not ((up[0, CLOSE_J] - up[0, 16]) * usd > 0 and -(up[0, CLOSE_J] - up[0, 16]) * usd < 0):
        raise S.GateError("[SIGN] a long across a rise does not pay, or the mirror does not pay the opposite")

    yrs = nd / 252.0
    uni_s = ok & short
    res = {"sessions": nd, "short_gamma_sessions": int(short.sum()), "tradable_short_gamma_sessions": int(uni_s.sum()),
           "norms": {"h": nh, "r": nr}, "bands": BANDS, "variants": {}}
    dailies = {}
    mbar = PM[pidx[uni_s]].mean(0)
    rows_s = pidx[uni_s]
    trade_sets = {}
    for v in VARIANTS:
        ii, ja, jb = trade_list(ST[v], rows_s)
        if not (ja % 15 == 1).all() or not (jb > ja).all():
            raise S.GateError(f"[FILL] {v}: a fill at or before its deciding close")
        pi = np.searchsorted(pidx, ii)                                  # panel row of each trade
        gross = (PM[ii, jb] - PM[ii, ja]) * usd
        net = gross - cost
        trade_sets[v] = (ii, ja, jb)
        o = net > 0
        od = np.zeros(nd); np.add.at(od, pi[o], net[o])
        oracle = {"share": float(o.mean()), "mean_net_winners": float(net[o].mean()), "net_sharpe": E.sharpe(od), "trades_per_year": float(o.sum() / yrs)}
        bk, daily = book_stats(E, net, gross, pi, ja, jb, days, nd, int(uni_s.sum()), yrs)
        dailies[v] = daily
        ctrl = (mbar[jb] - mbar[ja]) * usd
        nwe = E.nw_mean(gross - ctrl, 5)
        res["variants"][v] = {"1_oracle": oracle, "2_book": bk,
                              "3_drift_control": {"mean_control_gross": float(ctrl.mean()), "mean_trade_gross": float(gross.mean()), "mean_excess": nwe["mean"], "nw_t_excess": nwe["t"]}}
        d = bk["distribution_net"]
        log(f"  {v}: ORACLE {o.mean():.3f} win, winners ${net[o].mean():+.2f}, Sharpe {oracle['net_sharpe']:+.1f}")
        log(f"  {v}: {bk['trades']} trades ({bk['trades_per_year']:.0f}/yr, hold {bk['mean_hold_min']:.0f} min, exposure {bk['exposure_of_universe_session_time']:.2f}); "
            f"net Sharpe {bk['net_sharpe']:+.2f} Sortino {bk['net_sortino']:+.2f}; gross {bk['gross_sharpe']:+.2f}/{bk['gross_sortino']:+.2f}; "
            f"mean net ${bk['mean_net']:+.2f} (NW t {bk['nw_t_mean_net']:+.2f}) gross ${bk['mean_gross']:+.2f}; median ${d['median']:+.2f}; hit {d['win_rate']:.3f}; "
            f"payoff {d['payoff']:.2f}; trimmed ${d['mean_trimmed_1pc_both']:+.2f} (ex-top ${d['mean_ex_top_1pc']:+.2f}, ex-bottom ${d['mean_ex_bottom_1pc']:+.2f}); maxDD ${bk['max_dd']:,.0f}")
        log(f"      drift control ${ctrl.mean():+.2f} gross; excess ${nwe['mean']:+.2f} (NW t {nwe['t']:+.2f}); ex-2020-crash mean net ${bk['ex_feb_apr_2020']['mean_net']:+.2f}; "
            "by year " + " ".join(f"{y}:{q['net']:+.0f}" for y, q in bk["by_year"].items()))
    # 4 the timing null: rotate the position SCHEDULE among the tradable short-gamma days
    dP = np.diff(PM[rows_s], axis=1) * usd                              # n_s x 390
    n_s = len(rows_s)
    ks = S.rot_ks(n_s)
    null_by_v = {}
    for v in VARIANTS:
        ii, ja, jb = trade_sets[v]
        Hm = hold_matrix(ja, jb, ii, rows_s)
        ntr = len(ii)
        G = Hm @ dP.T                                                    # G[s, i]: schedule s on day i
        direct = float(((PM[ii, jb] - PM[ii, ja]) * usd).sum())
        if abs(np.trace(G) - direct) > 1e-6 * max(1.0, abs(direct)):
            raise S.GateError(f"[NULL] {v}: the schedule matrix's diagonal {np.trace(G)} != the trades' gross {direct}")
        ar = np.arange(n_s)
        null_by_v[v] = np.array([(G[(ar + k) % n_s, ar].sum() - cost * ntr) / ntr for k in ks])
    fam = np.max(np.column_stack([null_by_v[v][1:] for v in VARIANTS]), axis=1)
    res["4_timing_null"] = {"n_offsets": int(len(ks) - 1), "family_max": {"p50": float(np.percentile(fam, 50)), "p95": float(np.percentile(fam, 95))}}
    for v in VARIANTS:
        obs = null_by_v[v][0]
        res["4_timing_null"][v] = S.blk(float(obs), null_by_v[v][1:])
        res["4_timing_null"][v]["above_family_p95"] = bool(obs > np.percentile(fam, 95))
        res["4_timing_null"][v]["pct_in_family"] = float((fam < obs).mean())
        q = res["4_timing_null"][v]
        log(f"  TIMING NULL {v}: mean net ${obs:+.2f}; own p50 ${q['p50']:+.2f} p95 ${q['p95']:+.2f} (pct {q['pct_rank']:.3f}); family-max p50 ${np.percentile(fam, 50):+.2f} p95 ${np.percentile(fam, 95):+.2f} (pct {q['pct_in_family']:.3f})")
    # 5 the gamma-label null (reported): each variant on every tradable day, the short label rotated
    uni_a = ok
    res["5_gamma_label_null"] = {}
    for v in VARIANTS:
        ii, ja, jb = trade_list(ST[v], pidx[uni_a])
        pi = np.searchsorted(pidx, ii)
        net = (PM[ii, jb] - PM[ii, ja]) * usd - cost
        dn = np.zeros(nd); np.add.at(dn, pi, net)
        dc = np.zeros(nd); np.add.at(dc, pi, 1.0)
        rs = S.rotate(short & ok, S.rot_ks(nd))                           # nd x (1 + offsets)
        rs = rs.astype(float); tot = dn @ rs; cnt = dc @ rs
        stat = np.where(cnt > 0, tot / np.maximum(cnt, 1), np.nan)
        res["5_gamma_label_null"][v] = S.blk(float(stat[0]), stat[1:])
        q = res["5_gamma_label_null"][v]
        log(f"  GAMMA-LABEL NULL {v}: ${q['observed']:+.2f} p50 ${q['p50']:+.2f} p95 ${q['p95']:+.2f} (pct {q['pct_rank']:.3f})")
    # 6 controls, not traded
    uni_l = ok & ~short
    c6 = {}
    for v in VARIANTS:
        ii, ja, jb = trade_list(ST[v], pidx[uni_l])
        g = (PM[ii, jb] - PM[ii, ja]) * usd
        c6[f"{v}_long_gamma_days"] = {"trades": int(len(g)), "per_year": len(g) / yrs, "mean_gross": float(g.mean()), "mean_net": float(g.mean() - cost)}
        ii, ja, jb = trade_list(STm[v], rows_s)
        g = -(PM[ii, jb] - PM[ii, ja]) * usd
        c6[f"{v}_short_mirror_short_gamma_days"] = {"trades": int(len(g)), "per_year": len(g) / yrs, "mean_gross": float(g.mean()), "mean_net": float(g.mean() - cost)}
    for lab, u in (("short_gamma", uni_s), ("long_gamma", uni_l)):
        g = (PM[pidx[u], CLOSE_J] - PM[pidx[u], 16]) * usd
        c6[f"always_long_0946_1600_{lab}"] = {"days": int(u.sum()), "mean_gross": float(g.mean()), "mean_net": float(g.mean() - cost), "nw_t_net": E.nw_mean(g - cost, 5)["t"]}
    res["6_controls"] = c6
    for k_, q in c6.items():
        log(f"  CONTROL {k_}: " + ", ".join(f"{a} {b:+.2f}" if isinstance(b, float) else f"{a} {b}" for a, b in q.items()))
    # the declared reading
    res["reading"] = {}
    for v in VARIANTS:
        R_ = res["variants"][v]
        rd = {"a_mean_net_positive": bool(R_["2_book"]["mean_net"] > 0),
              "b_beats_drift_control_t2": bool(R_["3_drift_control"]["mean_excess"] > 0 and R_["3_drift_control"]["nw_t_excess"] >= 2),
              "c_above_family_max_timing_p95": bool(res["4_timing_null"][v]["above_family_p95"])}
        rd["edge_worth_filtering"] = bool(all(rd.values()))
        res["reading"][v] = rd
    log(f"  READING: {res['reading']}")
    return res, dailies


# ------------------------------------------------------------------ the data
def panel(data_root: Path, log=P):
    """D688's panel (G_SUM), D688's beta_G reproduced first, and the minute price grid over EVERY loaded session."""
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
    S.guard_window(D.index, "D699 panel")
    r = 100 * np.log(D["P1530"].to_numpy(float) / D["S_prev"].to_numpy(float)); R2 = 1e4 * np.log(D["P1600"].to_numpy(float) / D["P1530"].to_numpy(float))
    f688, _ = S.gamma_regression(R2, D["G_SUM"].to_numpy(float), r, D["sig"].to_numpy(float), D["V"].to_numpy(float), D["A_L"].to_numpy(float), null=False)
    ref = json.loads(D688_JSON.read_text(encoding="utf-8"))["gate1"]["G1"]["beta_G"]
    if f688["beta_G"] != ref:
        raise S.GateError(f"[REPRO] beta_G {f688['beta_G']!r} vs D688's {ref!r}")
    log(f"  D688 REPRODUCED on {len(D)} sessions ({time.time() - t0:.0f} s)")
    b = I["bars"]
    alld = I["days"]
    S.guard_window(alld, "D699 minute grid")
    close = b.pivot(index="day", columns="hhmm", values="close").reindex(alld)
    mins = [(pd.Timestamp("2000-01-01 09:30") + pd.Timedelta(minutes=k)).strftime("%H:%M") for k in range(390)]
    close = close.reindex(columns=mins).ffill(axis=1)
    op = b[b["hhmm"] == "09:30"].set_index("day")["open"].reindex(alld).to_numpy(float)
    PM = np.column_stack([op, close.to_numpy(float)])
    pos = {d: i for i, d in enumerate(alld)}
    pidx = np.array([pos[d] for d in D.index])
    return D, PM, pidx


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    D, PM, pidx = panel(data_root, log)
    days = D.index.to_numpy().astype(str)
    E = S.d685()
    mes = E.cost_spec("ES", "micro")
    cost, usd = mes["cost_rt_usd"], mes["usd_per_point"]
    short = D["G_SUM"].to_numpy(float) < 0
    res, dailies = core(PM, pidx, short, days, cost, usd, E, log)
    arm = E.load_arm()
    pos = {d: q for q, d in enumerate(days)}
    for v in VARIANTS:
        x = np.array([dailies[v][pos[d]] if d in pos else 0.0 for d in arm["days"]])
        res["variants"][v]["2_book"]["rho_with_macd_arm"] = float(np.corrcoef(x, arm["net"])[0, 1]) if x.std() > 0 else float("nan")
    rho12 = float(np.corrcoef(dailies["V1_HIST"], dailies["V2_ROC"])[0, 1])
    res["rho_V1_V2_daily"] = rho12
    log("  rho with the admitted arm: " + " ".join(f"{v} {res['variants'][v]['2_book']['rho_with_macd_arm']:+.3f}" for v in VARIANTS) + f"; rho V1-V2 {rho12:+.3f}")
    res = {"spec": "D699 STAGE 0 (in-sample; the gamma-gated 15-minute log MACD long, three variants with hysteresis, 1 MES)", "cost_rt_usd": cost, **res}
    res["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o_: o_.item() if hasattr(o_, "item") else str(o_)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


def selftest(log=P) -> int:
    """Synthetic random-walk sessions through every path of core(), no market data read."""
    rng = np.random.default_rng(1)
    n = 400
    lr = 0.0004 * rng.standard_normal((n, 391))
    lr[:, 0] = 0.003 * rng.standard_normal(n)                          # the overnight gap
    PM = 4000.0 * np.exp(np.cumsum(lr.ravel())).reshape(n, 391)
    PM[57, 195] = np.nan                                               # an unfilled bar close: the session is skipped like a gap
    pidx = np.arange(30, n)
    days = np.array([str((pd.Timestamp("2016-01-04") + pd.Timedelta(days=int(i))).date()) for i in pidx])
    short = rng.random(len(pidx)) < 0.4
    E = S.d685()
    res, _ = core(PM, pidx, short, days, 4.42, 5.0, E, log, audit_days=15)
    for v in VARIANTS:
        t = res["variants"][v]["2_book"]["trades"] / res["tradable_short_gamma_sessions"]
        log(f"  selftest {v}: {t:.2f} trades a day (random walk)")
    log("  SELFTEST PASSED")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.exit(run(a.data_root) if a.run else selftest() if a.selftest else 1)

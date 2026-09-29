"""D671 Stage 0 (development, ES and NQ): the break of yesterday's range with a day-size forecast and fixed-sign
contraindication vetoes. Spec: docs/decisions/D671-STAGE-0-DESIGN-the-break-with-a-day-size-forecast-and-
contraindication-vetoes.md (38c33823). In-sample 2016-01-04 -> 2025-02-28; the vault is never read. Dealer gamma (GEX):
SqueezeMetrics, prior row only, never written per date (licence guard). No verdict: development.

    uv run python scripts/stage0_d671_break_construction.py --selftest
    uv run python scripts/stage0_d671_break_construction.py --run [--data-root DIR]

Layers (s.1): D666's plain break, E4 (E4w reported); a walk-forward sign-constrained day-size forecast of ln(RTH range /
ATR20) on every session (s.2); hard skips (s.3); the fixed-sign score S, veto at S <= -1 (s.4); skip the forecast's
bottom tercile; one micro. Reported (s.5): the forecast's validation, the ablation B0 -> B3 (+B3w), removed-trade nets,
a within-year random-subset placebo, the four groups, the component line, by year, and the score's parts.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import nnls

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d668_break_predictor as M  # noqa: E402

X, T = M.X, M.T
OUT = REPO / "data" / "stage0_d671_break_construction.json"
ROOTS = ("ES", "NQ")
OTHER = {"ES": "NQ", "NQ": "ES"}
SIZE_FEATS = ("g", "on_range", "rv5", "abs_gap", "event", "opex")
SIGN = np.array([1.0, 1.0, 1.0, 1.0, 1.0, -1.0])
BURN, TIER_N, Q_EXH, Q_FLOW = 250, 250, 0.80, 0.80
N_PLACEBO, N_BOOT, SEED = 1000, 500, 671
TRAIL_W = 0.375
LEAK_SPREAD = 0.08


class D671Error(RuntimeError):
    pass


hm = X.hm


# ================================================================================ the size forecast
def size_forecast(F: np.ndarray, y: np.ndarray, leak: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """Walk-forward: forecast row i from rows < i (earlier sessions) with finite values; standardised features times
    their declared sign; non-negative slopes on demeaned data; free intercept. `leak` = True is the canary (rows <= i).
    Returns (forecast, slopes per refit)."""
    n, k = F.shape
    f = np.full(n, np.nan)
    B = np.full((n, k), np.nan)
    ok = np.isfinite(F).all(axis=1) & np.isfinite(y)
    for i in range(n):
        if not np.isfinite(F[i]).all():
            continue
        tr = ok.copy()
        tr[i + 1 if leak else i:] = False
        if tr.sum() < BURN:
            continue
        Xt, yt = F[tr], y[tr]
        mu, sd = Xt.mean(axis=0), Xt.std(axis=0)
        sd[sd == 0] = 1.0
        Z = (Xt - mu) / sd * SIGN
        zm, ym = Z.mean(axis=0), yt.mean()
        b, _ = nnls(Z - zm, yt - ym)
        B[i] = b
        f[i] = ym + float(((F[i] - mu) / sd * SIGN - zm) @ b)
    return f, B


def forecast_audit(f: np.ndarray, F: np.ndarray, y: np.ndarray, sessions: np.ndarray, idx: list[int]) -> None:
    """Second implementation: training rows chosen by SESSION DATE strictly before, never by position."""
    ok = np.isfinite(F).all(axis=1) & np.isfinite(y)
    for i in idx:
        if not np.isfinite(f[i]):
            continue
        tr = ok & (sessions < sessions[i])
        Xt, yt = F[tr], y[tr]
        mu, sd = Xt.mean(axis=0), Xt.std(axis=0)
        sd[sd == 0] = 1.0
        Z = (Xt - mu) / sd * SIGN
        b, _ = nnls(Z - Z.mean(axis=0), yt - yt.mean())
        want = yt.mean() + float(((F[i] - mu) / sd * SIGN - Z.mean(axis=0)) @ b)
        if not np.isclose(want, f[i], rtol=1e-9, atol=1e-9):
            raise D671Error(f"lag: the size forecast at {sessions[i]} was fitted on rows not strictly earlier")


def tiers(f: np.ndarray, leak: bool = False) -> np.ndarray:
    """The forecast's percentile among the previous TIER_N finite forecasts (walk-forward); NaN until TIER_N exist.
    `leak` = True is the canary (includes the forecast itself)."""
    out = np.full(len(f), np.nan)
    hist: list[float] = []
    for i, v in enumerate(f):
        if not np.isfinite(v):
            continue
        if leak:
            hist.append(v)
        if len(hist) >= TIER_N:
            h = np.array(hist[-TIER_N:])
            out[i] = float((h < v).mean())
        if not leak:
            hist.append(v)
    return out


def tier_audit(t: np.ndarray, f: np.ndarray, idx: list[int]) -> None:
    fin = np.flatnonzero(np.isfinite(f))
    for i in idx:
        if not np.isfinite(t[i]):
            continue
        prev = fin[fin < i][-TIER_N:]
        if not np.isclose(float((f[prev] < f[i]).mean()), t[i], atol=1e-12):
            raise D671Error("lag: the size tier uses forecasts that are not strictly earlier")


# ================================================================================ session features
def overnight(b: pd.DataFrame, r: str, include_rth: bool = False) -> pd.DataFrame:
    """Globex high/low per session over 18:00 -> 09:29 (bars before 09:30 only). `include_rth` is the canary."""
    x = b[b["root"] == r]
    m = (x["hhmm"] >= "18:00") | (x["hhmm"] < ("09:31" if include_rth else "09:30"))
    g = x[m].groupby("session")
    return pd.DataFrame({"on_high": g["high"].max(), "on_low": g["low"].min(), "on_last_hhmm": g["hhmm"].agg(
        lambda v: max((h for h in v if h < "18:00"), default=""))})


def overnight_audit(on: pd.DataFrame) -> None:
    if (on["on_last_hhmm"] >= "09:30").any():
        raise D671Error("lag: an overnight feature read a bar at or after 09:30")


def third_friday(s: str) -> bool:
    d = pd.Timestamp(s)
    return d.weekday() == 4 and 15 <= d.day <= 21


def session_features(d: pd.DataFrame, on: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    A = d["atr20"].astype(float)
    R = (d["high"] - d["low"]) / A
    absgap = (d["open"] - d["prior_close"]).abs() / A
    o = on.reindex(d.index)
    ev = cal.reindex(d.index)
    out = pd.DataFrame({
        "R": R, "y": np.log(R.where(R > 0)),
        "g": -d["gd_spx"] / d["V20"],
        "on_range": (o["on_high"] - o["on_low"] - (d["open"] - d["prior_close"]).abs()) / A,
        "rv5": R.shift(1).rolling(5, min_periods=5).mean(),
        "abs_gap": absgap,
        "event": (ev[["fomc", "cpi", "empsit"]].fillna(False).astype(bool).any(axis=1)).astype(float),
        "opex": pd.Series([float(third_friday(s)) for s in d.index], index=d.index),
        "fomc": ev["fomc"].fillna(False).astype(bool),
        "on_high": o["on_high"], "on_low": o["on_low"],
        "gap_q80": absgap.shift(1).rolling(TIER_N, min_periods=TIER_N // 2).quantile(Q_EXH)}, index=d.index)
    return out


# ================================================================================ trade-level terms
def other_close_before(bars_o: dict | None, minute: int, canary: bool = False) -> tuple[float, int]:
    """The other root's close on its last bar starting before the entry minute (canary: at or before)."""
    if bars_o is None:
        return float("nan"), -1
    m = bars_o["m"]
    j = np.flatnonzero(m <= minute) if canary else np.flatnonzero(m < minute)
    return (float(bars_o["c"][j[-1]]), int(m[j[-1]])) if len(j) else (float("nan"), -1)


def cross_audit(used: list[int], minutes: list[int]) -> None:
    for u, mn in zip(used, minutes):
        if u >= 0 and u >= mn:
            raise D671Error("lag: the cross-index close is not from a bar before the entry")


def a7_q80(a7: pd.DataFrame) -> dict[str, pd.Series]:
    ar = a7.set_index("session").sort_index()
    return {t: ar[f"a7_{t}"].abs().shift(1).rolling(TIER_N, min_periods=TIER_N // 2).quantile(Q_FLOW) for t in M.CHECKPOINTS}


# ================================================================================ statistics
def book(tr: pd.DataFrame, k: np.ndarray, gross_col: str, years: float, usd_pt: float, sessions: pd.Index) -> dict:
    n = int(k.sum())
    if n == 0:
        return {"trades": 0}
    g = tr[gross_col].to_numpy(float)[k]
    net = g - tr["cost_bp"].to_numpy(float)[k]
    usd = net / 1e4 * tr["entry"].to_numpy(float)[k] * usd_pt
    daily = pd.Series(usd, index=tr["session"].to_numpy()[k]).reindex(sessions, fill_value=0.0)
    cum = daily.cumsum().to_numpy()
    dd = float((np.maximum.accumulate(np.r_[0.0, cum])[1:] - cum).max())
    down = math.sqrt(float(np.mean(np.minimum(daily, 0) ** 2)))
    return {"trades": n, "trades_per_year": n / years, "gross": float(g.mean()), "net": float(net.mean()),
            "net_t_hac": float(M.mean_t(net, _R)[1]) if n > 5 else float("nan"),
            "win": float((net > 0).mean()), "p_hold": float((~tr["retest"].to_numpy(bool)[k]).mean()),
            "usd_per_year": float(usd.sum() / years), "max_dd_usd": dd,
            "daily_sharpe": float(daily.mean() / daily.std(ddof=1) * math.sqrt(252)) if daily.std(ddof=1) > 0 else float("nan"),
            "daily_sortino": float(daily.mean() / down * math.sqrt(252)) if down > 0 else float("nan")}


_R: Any = None


def retest(bb: dict, i: int, D: int, L: float) -> bool:
    m, h, l = bb["m"], bb["h"], bb["l"]
    after = np.arange(i + 1, len(m))
    after = after[m[after] <= X.LAST_ENTRY]
    return bool(len(after) and ((l[after] <= L).any() if D > 0 else (h[after] >= L).any()))


# ================================================================================ build
def build(data_root: Path) -> dict[str, Any]:
    global _R
    t0 = time.time()
    costs = M.micro_costs()
    b, use, Gd, R = M.load_bars(data_root, False, ROOTS)
    _R = R
    T.MULT.update(M.MULT)
    tabs = R.session_table(b, use, roots=ROOTS)
    bars = R.bar_arrays(b)
    dix = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
    gex = dix[dix["date"] < M.RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    cal_all = pd.read_csv(data_root / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
    frames, sf = {}, {}
    for r in ROOTS:
        d = T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        d["gd_spx"] = T.gex_prior(gex, d.index)
        T.gex_lag_audit(gex, d.index[:: max(1, len(d) // 40)])
        frames[r] = d
        on = overnight(b, r)
        overnight_audit(on)
        cal = cal_all[cal_all["root"] == r].set_index("day")
        sf[r] = session_features(d, on, cal)
    jobs = [(r, frames[r], {s: bars[(r, s)] for s in frames[r].index if (r, s) in bars}, M.TICK_PTS[r], M.SEED + M.ROOTS.index(r))
            for r in ROOTS]
    with ProcessPoolExecutor(max_workers=2) as pool:
        got = {o["root"]: o for o in pool.map(M.root_trades, jobs)}
        ex = dict(pool.map(T.extract_job, [("TICK-NQ", str(T.SC_DATA / "TICK-NQ.scid"))]))
    T.assert_sealed(ex["TICK-NQ"])
    committed = json.loads((REPO / "data" / "stage0_d668_dev_es_nq.json").read_text(encoding="utf-8"))["roots"]
    a7 = pd.read_csv(M.A7_FILES[("ES", "NQ")], encoding="utf-8", dtype={"session": str})
    a7 = a7[a7["session"] < M.RESERVED_FROM]
    k8 = M.k8_daily(tabs["NQ"], frames["NQ"].index)
    out: dict[str, Any] = {"spec": "D671 (38c33823), development", "credit": "dealer gamma (GEX): SqueezeMetrics",
                           "window": [M.FIRST, "2025-02-28"], "roots": {}}
    rng = np.random.default_rng(SEED)
    b3_daily = {}
    for r in ROOTS:
        d, S_ = frames[r], sf[r]
        tr = pd.DataFrame(got[r]["rows"]).sort_values("session").reset_index(drop=True)
        if abs(tr["E4_gross"].mean() - committed[r]["gate1"]["gross_mean"]) > 1e-9:
            raise D671Error(f"{r}: does not reproduce D668's development E4")
        X.TICK = M.TICK_PTS[r]
        tr["cost_bp"] = costs[r]["cost_usd"] / costs[r]["usd_per_point"] / tr["entry"] * 1e4
        X.TRAIL_K = TRAIL_W
        tr["E4w_all"] = [s_D * (X.exit_trade(bars[(r, s)], int(i), int(s_D), float(e), float(L), float(A), 0.0, "E4")[0] / float(e) - 1) * 1e4
                         for s, i, s_D, e, L, A in zip(tr["session"], tr["i"], tr["D"], tr["entry"], tr["L"], tr["A"])]
        X.TRAIL_K = 0.25
        tr["retest"] = [retest(bars[(r, s)], int(i), int(D), float(L)) for s, i, D, L in zip(tr["session"], tr["i"], tr["D"], tr["L"])]
        # ---- the size forecast on every session
        F = S_[list(SIZE_FEATS)].to_numpy(float)
        y = S_["y"].to_numpy(float)
        sess = S_.index.to_numpy()
        f, Bs = size_forecast(F, y)
        idx = list(range(BURN, len(sess), max(1, (len(sess) - BURN) // 10)))
        forecast_audit(f, F, y, sess, idx)
        tier = tiers(f)
        tier_audit(tier, f, idx)
        # persistence-only forecast (rv5 alone), same estimator
        global SIGN
        keep_sign = SIGN
        SIGN = np.array([1.0])
        fpers, _ = size_forecast(S_[["rv5"]].to_numpy(float), y)
        SIGN = keep_sign
        fin = np.isfinite(f) & np.isfinite(y)
        sp = float(stats.spearmanr(f[fin], y[fin])[0])
        finp = np.isfinite(fpers) & np.isfinite(y)
        sp_p = float(stats.spearmanr(fpers[finp], y[finp])[0])
        ff, yy = f[fin], y[fin]
        rot = np.array([stats.spearmanr(np.roll(ff, k), yy)[0] for k in range(21, len(ff) - 21)])
        dec = pd.qcut(pd.Series(ff).rank(method="first"), 10, labels=False)
        calib = {str(int(q) + 1): float(np.exp(yy[dec.to_numpy() == q]).mean()) for q in range(10)}
        Bf = Bs[np.isfinite(Bs[:, 0])]
        size_val = {"sessions_forecast": int(fin.sum()), "spearman": sp, "spearman_persistence_only": sp_p,
                    "rotation_null": {"p50": float(np.median(rot)), "p95": float(np.quantile(rot, 0.95)), "n_offsets": int(len(rot))},
                    "calibration_mean_R_by_decile": calib,
                    "slope_positive_share": {nm: float((Bf[:, j] > 0).mean()) for j, nm in enumerate(SIZE_FEATS)},
                    "final_slopes_std": {nm: float(Bf[-1, j]) for j, nm in enumerate(SIZE_FEATS)}}
        fser, tser = pd.Series(f, index=sess), pd.Series(tier, index=sess)
        tr["f"], tr["tier"] = fser.reindex(tr["session"]).to_numpy(), tser.reindex(tr["session"]).to_numpy()
        # ---- trade-level terms
        Sx = S_.reindex(tr["session"])
        D = tr["D"].to_numpy(int)
        o, pc, A = tr["open"].to_numpy(float), tr["prior_close"].to_numpy(float), tr["A"].to_numpy(float)
        ph, pl = d["prior_high"].reindex(tr["session"]).to_numpy(float), d["prior_low"].reindex(tr["session"]).to_numpy(float)
        stop = tr["stop"].to_numpy(float)
        gap = o - pc
        t_gap = (D * gap > 0.10 * A).astype(int)
        inside = (o <= ph) & (o >= pl)
        on_h, on_l = Sx["on_high"].to_numpy(float), Sx["on_low"].to_numpy(float)
        t_probe =-np.where((((D > 0) & (on_h > stop)) | ((D < 0) & (on_l < stop))) & inside, 1, 0)
        t_exh = -np.where((D * gap > 0) & (np.abs(gap) / A > Sx["gap_q80"].to_numpy(float)), 1, 0)
        terms = {"gap_aligned": t_gap, "overnight_probe": t_probe, "exhausted_gap": t_exh}
        if r == "NQ":
            rows = pd.DataFrame({"D": D, "eb": tr["minute"].to_numpy()}, index=tr["session"].to_numpy())
            gt = {"tick": T.gate_f(ex["TICK-NQ"], "tick"), "up": {"usable": False}, "dn": {"usable": False}}
            tz = T.shocks(rows, "09:30", ex["TICK-NQ"], None, None, gt)["s_tick"].astype(float).to_numpy()
            terms["breadth_aligned"] = np.where(np.nan_to_num(tz, nan=0.0) > 0.5, 1, 0)
            ar = a7[a7["root"] == r].set_index("session")
            q80 = a7_q80(a7[a7["root"] == r])
            used_cp = [M.a7_checkpoint(int(m)) for m in tr["minute"]]
            M.a7_audit(tr, used_cp)
            sf_ = []
            for s, cp, dd_ in zip(tr["session"], used_cp, D):
                if cp is None or s not in ar.index:
                    sf_.append(0)
                    continue
                v, q = ar.at[s, f"a7_{cp}"], q80[cp].get(s, np.nan)
                sf_.append(-1 if np.isfinite(v) and np.isfinite(q) and dd_ * v > q else 0)
            terms["spent_flow"] = np.array(sf_)
        else:
            ob = OTHER[r]
            used, conf = [], []
            for s, mn, dd_ in zip(tr["session"], tr["minute"], D):
                c_o, mu_ = other_close_before(bars.get((ob, s)), int(mn))
                used.append(mu_)
                if not np.isfinite(c_o) or s not in frames[ob].index:
                    conf.append(0)
                    continue
                lvl = frames[ob].at[s, "prior_high"] if dd_ > 0 else frames[ob].at[s, "prior_low"]
                conf.append(1 if (dd_ > 0 and c_o > lvl) or (dd_ < 0 and c_o < lvl) else 0)
            cross_audit(used, list(tr["minute"].astype(int)))
            terms["cross_index"] = np.array(conf)
        Ssum = sum(terms.values())
        hard = Sx["fomc"].to_numpy(bool) | (Sx["opex"].to_numpy(float) > 0)
        if r == "ES":
            hard = hard | (D < 0)
        # ---- the ablation on the evaluation window (tier exists)
        win = np.isfinite(tr["tier"].to_numpy(float))
        ses = d.index[d.index >= tr.loc[win, "session"].min()]
        years = len(ses) / 252
        usd_pt = costs[r]["usd_per_point"]
        b0 = win
        b1 = b0 & ~hard
        b2 = b1 & (Ssum > -1)
        b3 = b2 & (tr["tier"].to_numpy(float) >= 1 / 3)
        tr["E4w"] = np.where(tr["tier"].to_numpy(float) > 2 / 3, tr["E4w_all"], tr["E4_gross"])
        abl = {"B0_base": book(tr, b0, "E4_gross", years, usd_pt, ses),
               "B1_hard_skips": book(tr, b1, "E4_gross", years, usd_pt, ses),
               "B2_score_veto": book(tr, b2, "E4_gross", years, usd_pt, ses),
               "B3_construction": book(tr, b3, "E4_gross", years, usd_pt, ses),
               "B3w_wide_trail_on_top_tier": book(tr, b3, "E4w", years, usd_pt, ses)}
        netv = (tr["E4_gross"] - tr["cost_bp"]).to_numpy(float)
        removed = {"hard_skips": book(tr, b0 & ~b1, "E4_gross", years, usd_pt, ses),
                   "score_veto": book(tr, b1 & ~b2, "E4_gross", years, usd_pt, ses),
                   "size_tier": book(tr, b2 & ~b3, "E4_gross", years, usd_pt, ses)}
        # ---- the placebo: random subsets of B0 with B3's count per year
        yrs = tr["session"].str[:4].to_numpy()
        per_year = {yv: int((b3 & (yrs == yv)).sum()) for yv in np.unique(yrs[b0])}
        pool_idx = {yv: np.flatnonzero(b0 & (yrs == yv)) for yv in per_year}
        draws = np.empty(N_PLACEBO)
        for kd in range(N_PLACEBO):
            pick = np.concatenate([rng.choice(pool_idx[yv], per_year[yv], replace=False) for yv in per_year if per_year[yv]])
            draws[kd] = netv[pick].mean()
        b3net = float(netv[b3].mean())
        q95 = [np.quantile(rng.choice(draws, len(draws)), 0.95) for _ in range(N_BOOT)]
        placebo = {"p50": float(np.median(draws)), "p95": float(np.quantile(draws, 0.95)), "p95_se": float(np.std(q95, ddof=1)),
                   "rank": float((draws < b3net).mean()), "b3_net": b3net}
        # ---- hold rate and E4 by size tier (the leak check)
        tb = np.digitize(tr["tier"].to_numpy(float), [1 / 3, 2 / 3])
        by_tier = {nm: book(tr, b0 & (tb == k), "E4_gross", years, usd_pt, ses) for k, nm in enumerate(("bottom", "middle", "top"))}
        ph_ = [by_tier[k]["p_hold"] for k in by_tier if by_tier[k].get("trades")]
        size_val["p_hold_by_tier"] = {k: by_tier[k].get("p_hold") for k in by_tier}
        size_val["directional_leak_flag"] = bool(max(ph_) - min(ph_) > LEAK_SPREAD) if ph_ else None
        # ---- the score's parts
        parts = {}
        for nm, v in terms.items():
            fire = b1 & (v != 0)
            parts[nm] = {"sign": int(np.sign(v[v != 0][0])) if (v != 0).any() else 0,
                         "share_firing": float(fire.sum() / max(b1.sum(), 1)),
                         "net_firing": float(netv[fire].mean()) if fire.any() else float("nan"),
                         "net_not_firing": float(netv[b1 & (v == 0)].mean()) if (b1 & (v == 0)).any() else float("nan")}
        parts["S_distribution"] = {str(k): int((b1 & (Ssum == k)).sum()) for k in range(-3, 3)}
        # ---- four groups, component, by year
        fg = {"B0": X.four_groups(tr[b0].reset_index(drop=True), pd.Series(tr.loc[b0, "E4_gross"].to_numpy()), pd.Series(netv[b0]),
                                   b0.sum() / years, R, r),
              "B3": X.four_groups(tr[b3].reset_index(drop=True), pd.Series(tr.loc[b3, "E4_gross"].to_numpy()), pd.Series(netv[b3]),
                                   b3.sum() / years, R, r)}
        b3_daily[r] = M.daily_usd(tr, netv, b3.astype(float), ses, usd_pt)
        by_year = {yv: {"B0": book(tr, b0 & (yrs == yv), "E4_gross", 1.0, usd_pt, ses[ses.str.startswith(yv)]),
                        "B3": book(tr, b3 & (yrs == yv), "E4_gross", 1.0, usd_pt, ses[ses.str.startswith(yv)])}
                   for yv in sorted(set(yrs[b0]))}
        out["roots"][r] = {"size_forecast": size_val, "evaluation_window_start": str(ses[0]), "ablation": abl,
                           "removed_by_layer": removed, "placebo": placebo, "by_size_tier": by_tier, "score_parts": parts,
                           "four_groups": fg, "by_year": by_year, "_tr": (tr, b3, netv, ses, usd_pt)}
    for r in ROOTS:
        tr, b3, netv, ses, usd_pt = out["roots"][r].pop("_tr")
        out["roots"][r]["component_B3"] = M.component(tr, netv, tr["E4_gross"].to_numpy(float), b3.astype(float), ses, usd_pt, k8,
                                                      {OTHER[r]: b3_daily[OTHER[r]]})
    rr = out["roots"]
    out["expectations"] = {
        "1_forecast_beats_persistence_and_rotation": {r: bool(rr[r]["size_forecast"]["spearman"] > rr[r]["size_forecast"]["spearman_persistence_only"]
                                                              and rr[r]["size_forecast"]["spearman"] > rr[r]["size_forecast"]["rotation_null"]["p95"]) for r in ROOTS},
        "1b_spearman_in_0.20_0.35": {r: bool(0.20 <= rr[r]["size_forecast"]["spearman"] <= 0.35) for r in ROOTS},
        "2_p_hold_flat": {r: (rr[r]["size_forecast"]["directional_leak_flag"] is False) for r in ROOTS},
        "3_NQ_B3_net_up_1_to_3bp_usd_within_25pct": bool(1 <= rr["NQ"]["ablation"]["B3_construction"]["net"] - rr["NQ"]["ablation"]["B0_base"]["net"] <= 3
                                                          and abs(rr["NQ"]["ablation"]["B3_construction"]["usd_per_year"] / rr["NQ"]["ablation"]["B0_base"]["usd_per_year"] - 1) <= 0.25),
        "4_ES_B3_net_negative_or_within_1bp": bool(rr["ES"]["ablation"]["B3_construction"]["net"] <= 1.0),
        "5_placebo_NQ_above_p95_ES_not": bool(rr["NQ"]["placebo"]["rank"] > 0.95 and not rr["ES"]["placebo"]["rank"] > 0.95),
        "6_some_veto_term_removes_non_negative_net": bool(any(p.get("sign", 0) < 0 and np.isfinite(p.get("net_firing", np.nan)) and p["net_firing"] >= 0
                                                              for r in ROOTS for k, p in rr[r]["score_parts"].items() if isinstance(p, dict) and "sign" in p))}
    out["runtime_min"] = round((time.time() - t0) / 60, 2)
    T.licence_guard(out)
    return out


# ================================================================================ selftest
def selftest() -> int:
    fired = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except D671Error:
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")

    rng = np.random.default_rng(3)
    n = 330
    F = rng.normal(size=(n, len(SIZE_FEATS)))
    y = F @ np.array([0.3, 0.2, 0.1, 0.0, 0.05, -0.1]) + rng.normal(0, 1, n)
    sess = np.array([str(pd.Timestamp("2016-01-04") + pd.Timedelta(days=i))[:10] for i in range(n)])
    f, _ = size_forecast(F, y)
    idx = [BURN, BURN + 31, n - 1]
    forecast_audit(f, F, y, sess, idx)
    must_raise("size forecast on its own session", lambda: forecast_audit(size_forecast(F, y, leak=True)[0], F, y, sess, idx))
    ff = rng.normal(size=600)
    t = tiers(ff)
    tier_audit(t, ff, [300, 450, 599])
    must_raise("tier with its own forecast", lambda: tier_audit(tiers(ff, leak=True), ff, [300, 450, 599]))
    b = pd.DataFrame({"root": "ES", "session": "2016-01-05", "hhmm": ["18:05", "03:00", "09:29", "09:30", "10:00"],
                      "open": 1.0, "high": [10.0, 11.0, 12.0, 50.0, 13.0], "low": [9.0, 8.0, 9.5, 1.0, 9.0], "close": 1.0, "volume": 1})
    on = overnight(b, "ES")
    overnight_audit(on)
    if on["on_high"].iloc[0] != 12.0:
        raise SystemExit("selftest: the overnight high read the wrong bars")
    must_raise("overnight reading 09:30", lambda: overnight_audit(overnight(b, "ES", include_rth=True)))
    bo = {"m": np.array([570, 571, 572, 573]), "c": np.array([1.0, 2.0, 3.0, 4.0])}
    c, u = other_close_before(bo, 572)
    cross_audit([u], [572])
    if c != 2.0:
        raise SystemExit("selftest: the cross-index close is not the bar before the entry")
    must_raise("cross-index at the entry bar", lambda: cross_audit([other_close_before(bo, 572, canary=True)[1]], [572]))
    trx = pd.DataFrame({"minute": [hm("09:50")]})
    must_raise("A7 after the entry", lambda: _a7_canary(trx))
    if not (third_friday("2024-06-21") and not third_friday("2024-06-14") and not third_friday("2024-06-28")):
        raise SystemExit("selftest: the third-Friday rule")
    print(f"selftest: {len(fired)} canaries fired: {fired}")
    return 0


def _a7_canary(trx: pd.DataFrame) -> None:
    try:
        M.a7_audit(trx, [M.a7_checkpoint(hm("09:50"), after=1)])
    except M.D668Error as e:
        raise D671Error(str(e)) from e


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.run:
        ap.print_help()
        return 1
    out = build(a.data_root)
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({r: {"size_spearman": v["size_forecast"]["spearman"], "B0": v["ablation"]["B0_base"],
                          "B3": v["ablation"]["B3_construction"], "placebo": v["placebo"]} for r, v in out["roots"].items()},
                     indent=1, default=lambda z: round(z, 3)))
    print("expectations", out["expectations"], "runtime", out["runtime_min"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

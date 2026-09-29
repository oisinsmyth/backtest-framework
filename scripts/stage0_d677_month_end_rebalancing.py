"""D677 Stage 0 -- month-end rebalancing flow on ES and ZN (pre-registration:
docs/decisions/D677-PRE-REG-month-end-rebalancing-flow-on-es-and-zn.md).

    uv run python scripts/stage0_d677_month_end_rebalancing.py --selftest
    uv run python scripts/stage0_d677_month_end_rebalancing.py --run --data-root "<main checkout>/data"

A 60/40 portfolio rebalanced at each month-end drifts over the month; s(t) = w(t) - 0.6 on the month-to-date ES and ZN
returns. The position for outcome day o (the last five trading days) is -sign(s(o-2)): the drift through the
settlement BEFORE the entry settlement (the execution lag, D677 s.2). Returns are same-contract settlement returns on
the contract held overnight. Reads 2010-06 -> 2023-12-29 only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "d677_month_end_rebalancing.json"
COSTS = REPO / "data" / "futures_costs.json"
FIRST_MONTH, LAST_MONTH = "2010-07", "2023-12"
CUTOFF = "2024-01-01"                       # nothing on or after this date may survive (s.1, s.7)
W_EQ = 0.6
N_ACTIVE = 5                                # outcome days: the last five trading days
PLACEBO = (14, 10)                          # outcome days d_{n-14} .. d_{n-10} (1-based from the end: n-14 .. n-10)
LAG = 2                                     # position for day o uses s(o - 2)
Z_PRIOR, Z_MIN = 36, 12                     # sigma_s from the prior 36 months, at least 12
BURN_IN = 24                                # Gate 2: months of prior slope before any filtered trade
K_EP = 2.0                                  # projected gross >= 2 x round-trip cost
PURGE = 2                                   # rotation offsets 2 .. M-2
NW_LAG = 4
REVERSAL_DAYS = 10
OTHER_ROOTS = ("NQ", "YM", "RTY")
ERAS = (("2010-15", 2010, 2015), ("2016-19", 2016, 2019), ("2020-23", 2020, 2023))


class GateError(AssertionError):
    """An audit refused the input. Raising, never a warning."""


def P(*a, **k):
    print(*a, **k, flush=True)


# ------------------------------------------------------------------ statistics
def nw_slope(x: np.ndarray, y: np.ndarray, lag: int = NW_LAG) -> dict:
    """OLS slope of y on x with a Newey-West (Bartlett) standard error."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    xc = x - x.mean()
    b = float(np.dot(xc, y - y.mean()) / np.dot(xc, xc))
    e = (y - y.mean()) - b * xc
    u = xc * e
    s = float(np.dot(u, u))
    for L in range(1, lag + 1):
        s += 2 * (1 - L / (lag + 1)) * float(np.dot(u[L:], u[:-L]))
    se = math.sqrt(s) / float(np.dot(xc, xc))
    return {"beta": b, "se": se, "t": b / se if se > 0 else float("nan"), "n": int(len(x))}


def nw_mean(x: np.ndarray, lag: int = NW_LAG) -> dict:
    x = np.asarray(x, float)
    d = x - x.mean()
    s = float(np.dot(d, d))
    for L in range(1, lag + 1):
        s += 2 * (1 - L / (lag + 1)) * float(np.dot(d[L:], d[:-L]))
    se = math.sqrt(s) / len(x)
    return {"mean": float(x.mean()), "se": se, "t": float(x.mean()) / se if se > 0 else float("nan"), "n": int(len(x))}


def sharpe(x) -> float:
    x = np.asarray(x, float)
    s = x.std(ddof=1)
    return float(x.mean() / s * math.sqrt(252)) if s > 0 else float("nan")


def sortino(x) -> float:
    x = np.asarray(x, float)
    dn = math.sqrt(float(np.mean(np.minimum(x, 0.0) ** 2)))
    return float(x.mean() / dn * math.sqrt(252)) if dn > 0 else float("nan")


def max_dd(x) -> float:
    eq = np.cumsum(np.asarray(x, float))
    return float(np.max(np.maximum.accumulate(np.concatenate([[0.0], eq]))[1:] - eq))


def dist(x) -> dict:
    x = np.sort(np.asarray(x, float))
    n = len(x)
    k = max(1, int(round(0.01 * n)))
    w, l_ = x[x > 0], x[x < 0]
    m, s = x.mean(), x.std(ddof=1)
    return {"n": n, "mean": float(m), "median": float(np.median(x)), "win_rate": float(np.mean(x > 0)),
            "payoff": float(w.mean() / -l_.mean()) if len(w) and len(l_) else float("nan"),
            "skew": float(np.mean(((x - m) / s) ** 3)), "kurtosis": float(np.mean(((x - m) / s) ** 4)),
            "mean_ex_top_1pc": float(x[:-k].mean()), "mean_ex_bottom_1pc": float(x[k:].mean()),
            "mean_trimmed_1pc_both": float(x[k:-k].mean())}


# ------------------------------------------------------------------ the construction (s.2)
def month_blocks(days: np.ndarray) -> list[np.ndarray]:
    """Index arrays of the trading days of each calendar month, in order."""
    mon = np.array([d[:7] for d in days])
    cuts = np.flatnonzero(mon[1:] != mon[:-1]) + 1
    return np.split(np.arange(len(days)), cuts)


def drift_signal(r_eq: np.ndarray, r_bd: np.ndarray, blocks) -> np.ndarray:
    """s(t) = w(t) - 0.6, the 60/40 weight drift since the previous month-end close, within t's month."""
    s = np.full(len(r_eq), np.nan)
    for b in blocks:
        ge = np.exp(np.cumsum(r_eq[b]))
        gb = np.exp(np.cumsum(r_bd[b]))
        s[b] = W_EQ * ge / (W_EQ * ge + (1 - W_EQ) * gb) - W_EQ
    return s


def outcome_days(block: np.ndarray, which: str) -> np.ndarray:
    n = len(block)
    if which == "treat":
        return block[n - N_ACTIVE:]
    hi, lo = PLACEBO
    return block[n - hi - 1:n - lo]                                 # d_{n-14} .. d_{n-10}, 1-based


def lagged(s: np.ndarray, idx: np.ndarray, lag: int = LAG) -> np.ndarray:
    return s[idx - lag]


# ------------------------------------------------------------------ audits (s.8)
def audit_lag(r_eq, r_bd, blocks, s_prod_lag, idx) -> None:
    """Second path: rebuild s(o-2) from returns dated at or before o-2 only, by an explicit loop."""
    month_of = {}
    for b in blocks:
        for i in b:
            month_of[int(i)] = int(b[0])
    for k, o in enumerate(idx):
        t = int(o) - LAG
        start = month_of[t]
        ge = gb = 1.0
        for u in range(start, t + 1):
            ge *= math.exp(r_eq[u])
            gb *= math.exp(r_bd[u])
        w = W_EQ * ge / (W_EQ * ge + (1 - W_EQ) * gb)
        if abs((w - W_EQ) - s_prod_lag[k]) > 1e-12:
            raise GateError(f"[LAG] position for index {o} is not s(o-{LAG}) built from returns at or before o-{LAG}")
    # and causality: altering every return from o-1 on must not move s(o-2)
    o = int(idx[len(idx) // 2])
    r2 = r_eq.copy()
    r2[o - LAG + 1:] = -r2[o - LAG + 1:] + 0.01
    s2 = drift_signal(r2, r_bd, blocks)
    if s2[o - LAG] != drift_signal(r_eq, r_bd, blocks)[o - LAG]:
        raise GateError("[LAG] s(o-2) moved when returns after o-2 changed")


def audit_sign(position_fn) -> None:
    """A month where equities outperform must short ES; a following ES decline must pay positively."""
    r_eq = np.array([0.01] * 20)
    r_bd = np.zeros(20)
    blocks = [np.arange(20)]
    s = drift_signal(r_eq, r_bd, blocks)
    idx = outcome_days(blocks[0], "treat")
    pos = position_fn(lagged(s, idx))
    pnl = pos * -0.01                                               # ES falls 1% on each outcome day
    if not (np.all(pos < 0) and np.all(pnl > 0)):
        raise GateError("[SIGN] equities overweight did not short ES, or a favourable move did not pay")


def audit_right_quantity(held: np.ndarray, naive: np.ndarray, rolled: np.ndarray) -> int:
    """Held returns equal the naive front-to-front series off roll days and differ from it on at least one."""
    ok = np.isfinite(held) & np.isfinite(naive)
    if not np.array_equal(held[ok & ~rolled], naive[ok & ~rolled]):
        raise GateError("[RIGHT QUANTITY] held and naive returns differ on a non-roll day")
    n_diff = int(np.sum(held[ok & rolled] != naive[ok & rolled]))
    if n_diff == 0:
        raise GateError("[RIGHT QUANTITY] the held series equals the roll-contaminated one on every roll day")
    return n_diff


def guard_window(days) -> None:
    if len(days) and max(np.asarray(days).astype(str)) >= CUTOFF:
        raise GateError(f"[WINDOW] a settlement dated on or after {CUTOFF} survived the filter")


def book_position(sig_lag: np.ndarray) -> np.ndarray:
    return -np.sign(sig_lag)


# ------------------------------------------------------------------ the rotation null (s.3)
def rotation_stats(sign_T, y_T, sign_P, y_P, ks) -> np.ndarray:
    """For each offset k, month m's signs are paired with month (m+k)'s outcomes. Columns: treat mean, placebo mean."""
    M = sign_T.shape[0]
    out = np.empty((len(ks), 2))
    for a, k in enumerate(ks):
        j = (np.arange(M) + k) % M
        out[a, 0] = float(np.mean(-sign_T * y_T[j]))
        out[a, 1] = float(np.mean(-sign_P * y_P[j]))
    return out


def band(obs: float, draws: np.ndarray) -> dict:
    return {"value": float(obs), "p50": float(np.quantile(draws, .5)), "p95": float(np.quantile(draws, .95)),
            "pct": float(np.mean(draws <= obs)), "n_offsets": int(len(draws)), "p95_se": 0.0}


# ------------------------------------------------------------------ data
def load(data_root: Path) -> dict:
    import pandas as pd
    fx = data_root / "fixtures"
    roots = ("ES", "ZN") + OTHER_ROOTS
    cur = pd.read_csv(fx / "fut_curve_front_next.csv.gz", usecols=["root", "ref", "front", "front_settle"])
    cur = cur[cur["root"].isin(roots) & (cur["ref"] < CUTOFF)].dropna(subset=["front_settle"])
    strip = pd.read_csv(fx / "fut_settle_strip.csv.gz")
    strip = strip[strip["root"].isin(roots) & (strip["ref"] < CUTOFF)]
    guard_window(cur["ref"])
    guard_window(strip["ref"])
    es = cur[cur.root == "ES"].set_index("ref")
    zn = cur[cur.root == "ZN"].set_index("ref")
    days = np.array(sorted(set(es.index) & set(zn.index)))
    days = days[days >= "2010-06-07"]
    S = {r: strip[strip.root == r].set_index(["contract", "ref"])["settle"] for r in roots}
    F = {r: cur[cur.root == r].set_index("ref")["front"] for r in roots}
    FS = {r: cur[cur.root == r].set_index("ref")["front_settle"] for r in roots}

    def held(r):
        """r(t) = log S_t(c) - log S_{t-1}(c), c = r's front at t-1; NaN where either settlement is missing."""
        fr = F[r].reindex(days).to_numpy()
        prev_c = np.concatenate([[None], fr[:-1]])
        prev_d = np.concatenate([[None], days[:-1]])
        a = S[r].reindex(list(zip(prev_c[1:], days[1:]))).to_numpy(float)
        b = S[r].reindex(list(zip(prev_c[1:], prev_d[1:]))).to_numpy(float)
        out = np.full(len(days), np.nan)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[1:] = np.log(a) - np.log(b)
        naive = np.full(len(days), np.nan)
        fs = FS[r].reindex(days).to_numpy(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            naive[1:] = np.log(fs[1:]) - np.log(fs[:-1])
        rolled = np.concatenate([[False], fr[1:] != fr[:-1]])
        settle_prev = b
        price_move = a - b
        return out, naive, rolled, np.concatenate([[np.nan], settle_prev]), np.concatenate([[np.nan], price_move])

    R = {r: held(r) for r in roots}
    return {"days": days, "R": R}


# ------------------------------------------------------------------ costs
def cost_spec(root: str, kind: str) -> dict:
    j = json.loads(COSTS.read_text(encoding="utf-8"))["roots"][root][kind]
    tick_usd = float(j["tick_usd"])
    cross = float(j["crossing_ticks_rt"]["d508_exec"]["value"])
    return {"symbol": j["symbol"], "usd_per_point": float(j["usd_per_point"]), "tick_usd": tick_usd,
            "commission_rt_usd": float(j["commission_rt_usd"]["value"]), "crossing_ticks_rt": cross,
            "cost_rt_usd": float(j["commission_rt_usd"]["value"]) + cross * tick_usd}


# ------------------------------------------------------------------ the run
def analyse(D: dict, arm) -> dict:
    days = D["days"]
    r_es, naive_es, rolled_es, sprev_es, move_es = D["R"]["ES"]
    r_zn, naive_zn, rolled_zn, _, _ = D["R"]["ZN"]
    if not (np.isfinite(r_es[1:]).all() and np.isfinite(r_zn[1:]).all()):
        raise GateError("[DATA] a same-contract ES or ZN return is missing on the common grid")
    rq = {"ES": audit_right_quantity(r_es, naive_es, rolled_es), "ZN": audit_right_quantity(r_zn, naive_zn, rolled_zn)}
    blocks_all = month_blocks(days)
    blocks = [b for b in blocks_all if FIRST_MONTH <= days[b[0]][:7] <= LAST_MONTH]
    months = [days[b[0]][:7] for b in blocks]
    if len(blocks[0]) and days[blocks[0][0]][:7] != FIRST_MONTH:
        raise GateError("[DATA] the first signal month is not the declared one")
    if min(len(b) for b in blocks) < PLACEBO[0] + LAG + 2:
        raise GateError("[DATA] a month is too short for the placebo window and its lag")
    r_es0 = np.where(np.isfinite(r_es), r_es, 0.0)
    r_zn0 = np.where(np.isfinite(r_zn), r_zn, 0.0)
    s = drift_signal(r_es0, r_zn0, blocks_all)

    T_idx = np.array([outcome_days(b, "treat") for b in blocks])      # M x 5
    P_idx = np.array([outcome_days(b, "plac") for b in blocks])       # M x 5
    M = len(blocks)
    sT, sP = s[T_idx - LAG], s[P_idx - LAG]
    sT_un = s[T_idx - 1]
    yT, yP = r_es[T_idx] * 1e4, r_es[P_idx] * 1e4
    audit_lag(r_es0, r_zn0, blocks_all, sT.ravel(), T_idx.ravel())

    # z: sigma_s from the prior 36 months' lagged treatment signals (at least 12)
    sig_m = np.full(M, np.nan)
    for m in range(M):
        lo = max(0, m - Z_PRIOR)
        if m - lo >= Z_MIN:
            sig_m[m] = float(np.std(sT[lo:m].ravel(), ddof=1))
    zT = sT / sig_m[:, None]
    zP = sP / sig_m[:, None]
    has_z = np.isfinite(sig_m)

    def slope(zmat, ymat, rows):
        return nw_slope(zmat[rows].ravel(), ymat[rows].ravel())

    B1 = slope(zT, yT, has_z)
    ks = np.array([0] + list(range(PURGE, M - PURGE + 1)))
    rot = rotation_stats(np.sign(sT), yT, np.sign(sP), yP, ks)
    obs_T, obs_P = rot[0]
    if obs_T != float(np.mean(-np.sign(sT) * yT)):
        raise GateError("[NULL] the rotation at k = 0 does not reproduce the observed statistic")
    B2 = band(obs_T, rot[1:, 0])
    B3 = band(obs_T - obs_P, rot[1:, 0] - rot[1:, 1])
    B2["placebo_value"] = float(obs_P)
    B2["placebo_band"] = band(obs_P, rot[1:, 1])
    gate1 = bool(B1["beta"] < 0 and B1["t"] <= -2.0 and B2["value"] > B2["p95"] and B3["value"] > B3["p95"])

    # ---- books in dollars over every trading day: unfiltered and filtered, MES and ES
    spec = {"MES": cost_spec("ES", "micro"), "ES": cost_spec("ES", "full")}
    beta_prior = np.full(M, np.nan)
    for m in range(M):
        rows = np.flatnonzero(has_z[:m])
        if len(rows) >= BURN_IN:
            beta_prior[m] = nw_slope(zT[rows].ravel(), yT[rows].ravel())["beta"]

    def book(filtered: bool, inst: str) -> dict:
        sp = spec[inst]
        pos = np.zeros(len(days))
        for m in range(M):
            for j in range(N_ACTIVE):
                o = T_idx[m, j]
                p = -np.sign(sT[m, j])
                if filtered:
                    ok = has_z[m] and np.isfinite(beta_prior[m]) and beta_prior[m] < 0
                    proj = (-beta_prior[m] * abs(zT[m, j]) / 1e4 * sp["usd_per_point"] * sprev_es[o]) if ok else 0.0
                    if not (ok and proj >= K_EP * sp["cost_rt_usd"]):
                        p = 0.0
                pos[o] = p
        gross = pos * move_es * sp["usd_per_point"]
        gross[~np.isfinite(gross)] = 0.0
        chg = np.abs(np.diff(np.concatenate([[0.0], pos])))
        cost = 0.5 * sp["cost_rt_usd"] * chg
        # the exit cost of a run is charged to its last active day (s.3 Gate 2)
        cost_book = cost.copy()
        exit_days = np.flatnonzero((np.concatenate([[0.0], pos])[:-1] != 0) & (pos == 0))
        for d_ in exit_days:
            cost_book[d_ - 1] += cost_book[d_]
            cost_book[d_] = 0.0
        net = gross - cost_book
        act = T_idx.ravel()
        traded = act[pos[act] != 0]
        in_win = (days >= f"{FIRST_MONTH}-01")
        runs = int(np.sum((np.diff(np.concatenate([[0.0], pos])) != 0) & (pos != 0)))
        yrs = np.array([int(d[:4]) for d in days])
        per_year = {int(y): float(net[in_win & (yrs == y)].sum()) for y in range(2010, 2024)}
        price = sprev_es[traded]
        terc = np.quantile(price, [1 / 3, 2 / 3]) if len(price) > 3 else [np.nan, np.nan]
        def tercile_block(lo_, hi_):
            m_ = (price >= lo_) & (price < hi_)
            return {"traded_days": int(m_.sum()), "net_mean": float(net[traded][m_].mean()) if m_.any() else float("nan"),
                    "cost_bp_mean": float(np.mean(sp["cost_rt_usd"] / (price[m_] * sp["usd_per_point"]) * 1e4))
                    if m_.any() else float("nan")}
        qe = np.array([int(days[t][5:7]) % 3 == 0 for t in traded])
        g_tr, n_tr = gross[traded], net[traded]
        return {
            "instrument": inst, "cost_rt_usd": sp["cost_rt_usd"], "traded_days": int(len(traded)), "runs": runs,
            "exposure_share_of_days": float(np.mean(pos[in_win] != 0)),
            "gross_daily": {"sharpe": sharpe(gross[in_win]), "sortino": sortino(gross[in_win]), "sum": float(gross[in_win].sum())},
            "net_daily": {"sharpe": sharpe(net[in_win]), "sortino": sortino(net[in_win]), "sum": float(net[in_win].sum()),
                          "vol_ann": float(net[in_win].std(ddof=1) * math.sqrt(252)), "max_dd": max_dd(net[in_win])},
            "per_traded_day": {"gross": dist(g_tr) if len(g_tr) > 3 else None, "net": dist(n_tr) if len(n_tr) > 3 else None,
                               "sharpe_by_own_count": float(n_tr.mean() / n_tr.std(ddof=1) * math.sqrt(len(n_tr) / (M / 12)))
                               if len(n_tr) > 3 else float("nan"),
                               "mean_abs_move_usd": float(np.mean(np.abs(g_tr))) if len(g_tr) else float("nan"),
                               "two_cost_usd": 2 * sp["cost_rt_usd"],
                               "breakeven_cost_rt_usd": float(g_tr.sum() / max(runs, 1)) if len(g_tr) else float("nan")},
            "gate2_active_day_net": nw_mean(net[T_idx.ravel()]),
            "profitable_years": int(sum(v > 0 for v in per_year.values())), "per_year_net": per_year,
            "eras_net": {e: float(net[in_win & (yrs >= a) & (yrs <= b)].sum()) for e, a, b in ERAS},
            "quarter_end_vs_other": {"qe_traded": int(qe.sum()), "qe_net_mean": float(n_tr[qe].mean()) if qe.any() else float("nan"),
                                     "other_traded": int((~qe).sum()),
                                     "other_net_mean": float(n_tr[~qe].mean()) if (~qe).any() else float("nan")},
            "price_terciles": {"low": tercile_block(-np.inf, terc[0]), "mid": tercile_block(terc[0], terc[1]),
                               "high": tercile_block(terc[1], np.inf)},
            "_net": net, "_days": days,
        }

    books = {f"{'filtered' if f else 'unfiltered'}_{i}": book(f, i) for f in (False, True) for i in ("MES", "ES")}
    fb = books["filtered_MES"]
    g2 = fb["gate2_active_day_net"]
    if fb["traded_days"] < 60:
        gate2 = "UNRESOLVED"
    else:
        gate2 = "PASS" if (g2["mean"] > 0 and g2["t"] >= 2.0) else "FAIL"
    verdict = ("SUPPORTED" if gate1 and gate2 == "PASS" else "MECHANISM ONLY" if gate1 else "NOT SUPPORTED")

    # ---- correlation with the admitted MACD arm (its days only)
    corr = None
    if arm is not None:
        pos_of = {d: i for i, d in enumerate(days)}
        for key in ("unfiltered_MES", "filtered_MES"):
            x = np.array([books[key]["_net"][pos_of[d]] if d in pos_of else 0.0 for d in arm["days"]])
            corr = corr or {}
            corr[key] = float(np.corrcoef(x, arm["net"])[0, 1]) if x.std() > 0 else float("nan")

    # ---- reported beside (s.4)
    def rot_pct(sign_mat, y_mat):
        rr = rotation_stats(sign_mat, y_mat, sign_mat, y_mat, ks)
        return band(rr[0, 0], rr[1:, 0])
    beside = {}
    beside["S_UNLAG_B1"] = slope(sT_un / sig_m[:, None], yT, has_z)
    beside["S_UNLAG_B2"] = rot_pct(np.sign(sT_un), yT)
    beside["placebo_B1"] = slope(zP, yP, has_z)
    y_zn = r_zn[T_idx] * 1e4
    beside["ZN_B1"] = slope(zT, y_zn, has_z)
    beside["ES_minus_ZN_B1"] = slope(zT, yT - y_zn, has_z)
    for r in OTHER_ROOTS:
        rr = D["R"][r][0][T_idx] * 1e4
        rows = has_z & np.isfinite(rr).all(axis=1)
        beside[f"{r}_B1"] = slope(zT, rr, rows) if rows.sum() >= 24 else None
        beside[f"{r}_B2"] = rot_pct(np.sign(sT[rows]), rr[rows]) if rows.sum() >= 24 else None
    qe_rows = np.array([int(m[5:7]) % 3 == 0 for m in months])
    beside["quarter_end_B1"] = slope(zT, yT, has_z & qe_rows)
    beside["other_months_B1"] = slope(zT, yT, has_z & ~qe_rows)
    # the reversal: z on the last outcome day's signal -> the first 10 trading days of the next month
    rev_x, rev_y = [], []
    pos_block = {days[b[0]][:7]: b for b in blocks_all}
    for m in range(M - 1):                                           # December 2023 excluded (s.4)
        if not has_z[m]:
            continue
        nb = blocks[m + 1]
        rev_x.append(zT[m, -1])
        rev_y.append(float(np.sum(r_es[nb[:REVERSAL_DAYS]])) * 1e4)
    beside["reversal_next10_B1"] = nw_slope(np.array(rev_x), np.array(rev_y), lag=1)
    for e, a, b in ERAS:
        rows = has_z & np.array([a <= int(m[:4]) <= b for m in months])
        beside[f"era_{e}_B1"] = slope(zT, yT, rows)
    beside["by_year"] = {}
    for y in range(2010, 2024):
        rows = np.array([int(m[:4]) == y for m in months])
        rz = rows & has_z
        beside["by_year"][y] = {"B1": slope(zT, yT, rz) if rz.sum() >= 6 else None,
                                "sign_book_gross_bp": float(np.mean(-np.sign(sT[rows]) * yT[rows]))}
    beside["positive_years_sign_book"] = int(sum(v["sign_book_gross_bp"] > 0 for v in beside["by_year"].values()))

    # ---- predictions (s.6)
    pr = {}
    pr["1_beta_negative"] = bool(B1["beta"] < 0)
    pr["2_size_-15_to_-5_and_t_-4_to_-2"] = bool(-15 <= B1["beta"] <= -5 and -4 <= B1["t"] <= -2)
    pr["3_placebo_flat_and_B3_iff_B1"] = bool(abs(beside["placebo_B1"]["beta"]) <= 5 and
                                              ((B3["value"] > B3["p95"]) == (B1["beta"] < 0 and B1["t"] <= -2)))
    pr["4_ZN_beta_positive"] = bool(beside["ZN_B1"]["beta"] > 0)
    pr["5_quarter_end_larger"] = bool(abs(beside["quarter_end_B1"]["beta"]) > abs(beside["other_months_B1"]["beta"]))
    pr["6_reversal_positive"] = bool(beside["reversal_next10_B1"]["beta"] > 0)
    pr["7_gate1_implies_gate2"] = bool((not gate1) or gate2 == "PASS")

    for b in books.values():
        b.pop("_net")
        b.pop("_days")
    return {"months": M, "first_month": months[0], "last_month": months[-1], "active_days": int(T_idx.size),
            "z_months": int(has_z.sum()), "right_quantity_roll_days_differ": rq,
            "B1": B1, "B2": B2, "B3": B3, "gate1": gate1, "gate2": gate2, "verdict": verdict,
            "gate2_detail": {"traded_days": fb["traded_days"], "active_day_net": g2},
            "books": books, "corr_with_macd_arm": corr, "beside": beside, "predictions": pr,
            "costs": spec, "sigma_s_last": float(sig_m[-1])}


def load_arm():
    s = importlib.util.spec_from_file_location("d667r", REPO / "scripts" / "run_d667_hike_pause_overlay.py")
    m = importlib.util.module_from_spec(s)
    sys.modules["d667r"] = m
    s.loader.exec_module(m)
    return m.load_arm()


# ------------------------------------------------------------------ self-test
def do_self_test() -> int:
    rng = np.random.default_rng(677)
    n = 22 * 30
    days = []
    import datetime as dt
    d0 = dt.date(2012, 1, 2)
    while len(days) < n:
        if d0.weekday() < 5:
            days.append(d0.isoformat())
        d0 += dt.timedelta(days=1)
    days = np.array(days)
    blocks = month_blocks(days)
    r_eq = rng.standard_normal(n) * 0.01
    r_bd = rng.standard_normal(n) * 0.003
    s = drift_signal(r_eq, r_bd, blocks)
    blocks_in = [b for b in blocks if len(b) >= PLACEBO[0] + LAG + 2]
    T_idx = np.array([outcome_days(b, "treat") for b in blocks_in]).ravel()
    audit_lag(r_eq, r_bd, blocks, s[T_idx - LAG], T_idx)
    try:
        audit_lag(r_eq, r_bd, blocks, s[T_idx - 1], T_idx)
        raise SystemExit("lag audit FAILED to fire on the unlagged signal")
    except GateError:
        pass
    P("  lag audit passes on s(o-2) and fires on s(o-1)")
    audit_sign(book_position)
    try:
        audit_sign(lambda x: np.sign(x))
        raise SystemExit("sign audit FAILED to fire on an inverted position")
    except GateError:
        pass
    P("  sign audit fires on an inverted position")
    held = rng.standard_normal(50)
    naive = held.copy()
    rolled = np.zeros(50, dtype=bool)
    rolled[[10, 30]] = True
    naive[rolled] += 0.02
    audit_right_quantity(held, naive, rolled)
    try:
        audit_right_quantity(naive, naive, rolled)
        raise SystemExit("right-quantity audit FAILED to fire on the naive series")
    except GateError:
        pass
    P("  right-quantity audit fires on the roll-contaminated series")
    guard_window(["2023-12-29"])
    try:
        guard_window(["2023-12-29", "2024-01-02"])
        raise SystemExit("window guard FAILED to fire on a 2024 row")
    except GateError:
        pass
    P("  window guard fires on a 2024 row")
    sT = rng.standard_normal((30, 5))
    yT = rng.standard_normal((30, 5))
    rot = rotation_stats(np.sign(sT), yT, np.sign(sT), yT, np.array([0, 2, 3]))
    if rot[0, 0] != float(np.mean(-np.sign(sT) * yT)):
        raise SystemExit("rotation at k=0 does not reproduce the observed statistic")
    if rot[1, 0] == rot[0, 0]:
        raise SystemExit("rotation at k=2 reproduced k=0: the null does not move")
    P("  rotation null reproduces the observed statistic at k = 0 and moves at k = 2")
    # NW slope on a planted effect
    x = rng.standard_normal(4000)
    y = -0.2 * x + rng.standard_normal(4000)
    b = nw_slope(x, y)
    if not (-0.25 < b["beta"] < -0.15 and b["t"] < -8):
        raise SystemExit(f"NW slope did not recover a planted -0.2: {b}")
    P("  NW slope recovers a planted effect")
    P("SELF-TEST PASSED")
    return 0


def do_run(data_root: Path) -> int:
    t0 = time.perf_counter()
    D = load(data_root)
    P(f"loaded {len(D['days']):,} common ES/ZN trading days {D['days'][0]} -> {D['days'][-1]} "
      f"({time.perf_counter() - t0:.1f}s)")
    arm = load_arm()
    R = analyse(D, arm)
    B1, B2, B3 = R["B1"], R["B2"], R["B3"]
    P(f"\n{R['months']} months {R['first_month']} -> {R['last_month']}, {R['active_days']} active days, "
      f"z on {R['z_months']} months; roll days where held != naive: {R['right_quantity_roll_days_differ']}")
    P("\n=== Gate 1 (gross, the mechanism) ===")
    P(f"  B1 slope {B1['beta']:+.2f} bp per 1-SD, NW t {B1['t']:+.2f} (n {B1['n']})")
    P(f"  B2 sign book {B2['value']:+.2f} bp/day; null p50 {B2['p50']:+.2f} p95 {B2['p95']:+.2f} pct {B2['pct']:.3f} "
      f"({B2['n_offsets']} offsets)")
    P(f"     placebo {B2['placebo_value']:+.2f} bp/day (pct {B2['placebo_band']['pct']:.3f})")
    P(f"  B3 treat - placebo {B3['value']:+.2f}; null p50 {B3['p50']:+.2f} p95 {B3['p95']:+.2f} pct {B3['pct']:.3f}")
    P(f"  GATE 1 {'PASS' if R['gate1'] else 'FAIL'}   GATE 2 {R['gate2']}   VERDICT {R['verdict']}")
    P("\n=== Books (daily $, 2010-07 -> 2023-12) ===")
    for k, b in R["books"].items():
        pt = b["per_traded_day"]
        P(f"  {k:<16} traded {b['traded_days']:>4} runs {b['runs']:>3}  net Sharpe {b['net_daily']['sharpe']:+.2f} "
          f"Sortino {b['net_daily']['sortino']:+.2f}  gross Sharpe {b['gross_daily']['sharpe']:+.2f}  "
          f"net ${b['net_daily']['sum']:,.0f}  maxDD ${b['net_daily']['max_dd']:,.0f}  "
          f"per-day net mean ${pt['net']['mean'] if pt['net'] else float('nan'):+.2f}  cost RT ${b['cost_rt_usd']:.2f}")
    P(f"\n  corr with the MACD arm: {R['corr_with_macd_arm']}")
    P("\n=== Beside ===")
    for k, v in R["beside"].items():
        if k in ("by_year",):
            continue
        if isinstance(v, dict) and "beta" in v:
            P(f"  {k:<22} beta {v['beta']:+.2f}  t {v['t']:+.2f}  n {v['n']}")
        elif isinstance(v, dict) and "pct" in v:
            P(f"  {k:<22} value {v['value']:+.2f}  p95 {v['p95']:+.2f}  pct {v['pct']:.3f}")
        else:
            P(f"  {k:<22} {v}")
    P("  by year (B1 beta / sign-book bp): " + "  ".join(
        f"{y}:{(v['B1']['beta'] if v['B1'] else float('nan')):+.1f}/{v['sign_book_gross_bp']:+.1f}"
        for y, v in R["beside"]["by_year"].items()))
    P("\n=== Predictions (D677 s.6) ===")
    for k, v in R["predictions"].items():
        P(f"  {k:<36} {'HELD' if v else 'BROKEN'}")
    out = {"generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "pre_registration": "docs/decisions/D677-PRE-REG-month-end-rebalancing-flow-on-es-and-zn.md",
           "window": [FIRST_MONTH, LAST_MONTH], "cutoff_exclusive": CUTOFF, **R,
           "wall_seconds": time.perf_counter() - t0}
    OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8")
    P(f"\nwrote {OUT.relative_to(REPO)} ({time.perf_counter() - t0:.0f}s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        return do_self_test()
    if a.run:
        do_self_test()
        return do_run(a.data_root)
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

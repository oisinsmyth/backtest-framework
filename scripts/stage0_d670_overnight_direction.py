"""D670 Stage 0 -- the MACD arm's mechanism built directly: carry the move since yesterday's close from 10:00 to 16:00.

    python scripts/stage0_d670_overnight_direction.py --selftest
    python scripts/stage0_d670_overnight_direction.py --run          # -> data/stage0_d670_overnight_direction.json

PRE-REGISTRATION: docs/decisions/D670-STAGE-0-DESIGN-carry-the-overnight-direction-from-ten.md (772ade0), committed
before this file existed. Evidence YM and RTY; development ES and NQ (no verdict). In sample only: every row at or after
2025-03-01 (the vault) is dropped at load and a guard raises if one survives.

P1  direction D = sign(C[09:59] - prior C[15:59]); enter at the 10:00 open, exit at the 15:59 close.
P2  a walk-forward OLS expected-profit forecast at 10:00 (seven features), pass-through pi-hat, trade when
    projected >= 2 x cost; beta_disc against N2 (features permuted within year).
P3  exit at the 15:00 open when the last completed hour moved against D.

Dealer gamma (GEX): SqueezeMetrics, used under the principal's written permission of 2026-09-28. Prior row only; no
per-date value leaves this runner (the licence guard raises on any long list in the output).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from stage0_d669_macd_mechanism import (  # noqa: E402
    dist, drift_carry, kurt, max_dd, ols_nw, permute_null, qdist, sharpe, skew, sortino, strata_labels, tstat)

OUT = REPO / "data" / "stage0_d670_overnight_direction.json"
FIXDIR = REPO / "data" / "fixtures"
COSTS = REPO / "data" / "futures_costs.json"
PREREG = "772ade0"
VAULT = "2025-03-01"
HI = "2025-02-28"
LO = {"ES": "2016-01-04", "NQ": "2016-01-04", "YM": "2016-01-04", "RTY": "2017-07-10"}
EVIDENCE, DEVELOPMENT = ("YM", "RTY"), ("ES", "NQ")
ROOTS = DEVELOPMENT + EVIDENCE
CIRCUIT = {"2020-03-09", "2020-03-12", "2020-03-16"}
ERA_0DTE = "2022-05-16"
DRAWS, SEED, N2_DRAWS = 10_000, 670, 200
BURN, PI_BURN, K_COST = 250, 40, 2.0
NW_LAGS = 5
M = lambda hh, mm: (hh - 9) * 60 + mm - 30                       # noqa: E731  minute index, 09:30 = 0
M0930, M0959, M1000, M1359, M1459, M1500, M1559 = M(9, 30), M(9, 59), M(10, 0), M(13, 59), M(14, 59), M(15, 0), M(15, 59)
HALF_HOURS = [M(10, 29) + 30 * k for k in range(12)]             # 10:29, 10:59, ... 15:59
ND = NormalDist()
FEATURES = ("f1_size", "f2_agree", "f3_orange", "f4_oeff", "f5_short_gamma", "f6_trail_vol", "f7_long")


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


def gex_path() -> Path:
    for base in (REPO, REPO.parents[2]):                          # the worktree, then the main checkout's raw cache
        p = base / "data" / "raw" / "squeezemetrics" / "DIX.csv"
        if p.exists():
            return p
    raise GateError("SqueezeMetrics DIX.csv not found in data/raw")


def micro_spec(root: str) -> dict:
    j = json.loads(COSTS.read_text(encoding="utf-8"))["roots"][root]["micro"]
    tick_usd = float(j["tick_usd"])
    cross = float(j["crossing_ticks_rt"]["d508_exec"]["value"])
    return {"symbol": j["symbol"], "tick_points": float(j["tick_points"]), "usd_per_point": float(j["usd_per_point"]),
            "tick_usd": tick_usd, "cost_rt_usd": float(j["commission_rt_usd"]["value"]) + cross * tick_usd,
            "crossing_ticks_rt": cross}


# ------------------------------------------------------------------ guards
def guard_window(days) -> None:
    if len(days) and max(np.asarray(days).astype(str)) >= VAULT:
        raise GateError(f"[VAULT] a row at or after {VAULT} was read")


def gex_prior(gex: pd.Series, sessions) -> np.ndarray:
    """The GEX row dated strictly before each session (a row for day t is computed from day t's close)."""
    dates = gex.index.to_numpy().astype(str)
    s = np.asarray(sessions).astype(str)
    pos = np.searchsorted(dates, s, side="left") - 1
    return np.where(pos >= 0, gex.to_numpy(float)[np.clip(pos, 0, None)], np.nan)


def gex_audit(gex: pd.Series, sessions, mapper=None) -> None:
    got = (mapper or gex_prior)(gex, sessions)
    ref = np.array([gex[gex.index < d].iloc[-1] if (gex.index < d).any() else np.nan for d in sessions], float)
    if not np.allclose(got, ref, equal_nan=True):
        raise GateError("[GEX] the gamma row is not the one dated before the session")


def licence_guard(obj, path="") -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            licence_guard(v, f"{path}/{k}")
    elif isinstance(obj, list):
        if len(obj) > 60:
            raise GateError(f"[LICENCE] a list of {len(obj)} values at {path}: no per-date series may leave the runner")
        for v in obj:
            licence_guard(v, path)


# ------------------------------------------------------------------ the session table
def load_sessions(root: str) -> pd.DataFrame:
    """One row per in-window session with every price the three parts read. Vault rows are dropped at load."""
    bars = pd.read_csv(FIXDIR / f"fut_{root}_rth_1m.csv.gz", encoding="utf-8",
                       dtype={"day": str, "hhmm": str, "contract": str})
    bars = bars[bars["day"] < VAULT]
    guard_window(bars["day"])
    bars = bars[bars["day"] >= "2015-12-01"]                     # a month of history for the trailing features
    mi = bars["hhmm"].str[:2].astype(int) * 60 + bars["hhmm"].str[3:].astype(int) - (9 * 60 + 30)
    bars = bars.assign(m=mi)[(mi >= 0) & (mi <= M1559)]
    days = np.array(sorted(bars["day"].unique()))
    di = np.searchsorted(days, bars["day"].to_numpy())
    grid = {}
    for col in ("open", "high", "low", "close"):
        a = np.full((len(days), M1559 + 1), np.nan)
        a[di, bars["m"].to_numpy()] = bars[col].to_numpy(float)
        grid[col] = a
    con = bars.groupby("day")["contract"].agg(lambda s: s.iloc[0]).reindex(days).to_numpy()
    O, H, L, C = grid["open"], grid["high"], grid["low"], grid["close"]
    Cf = pd.DataFrame(C).ffill(axis=1).to_numpy()                 # the last close at or before each minute
    s = pd.DataFrame({"day": days, "contract": con})
    s["prev_contract"] = np.concatenate([[None], con[:-1]])
    s["prev_c1559"] = np.concatenate([[np.nan], C[:-1, M1559]])
    for name, mm in (("o0930", M0930), ("o1000", M1000), ("o1500", M1500)):
        s[name] = O[:, mm]
    for name, mm in (("c0959", M0959), ("c1359", M1359), ("c1459", M1459), ("c1559", M1559)):
        s[name] = C[:, mm]
    s["h_open"] = np.nanmax(H[:, M0930:M0959 + 1], axis=1)
    s["l_open"] = np.nanmin(L[:, M0930:M0959 + 1], axis=1)
    s["range_day"] = np.nanmax(H, axis=1) - np.nanmin(L, axis=1)
    hh = Cf[:, HALF_HOURS]
    prev = np.column_stack([O[:, M1000], hh[:, :-1]])
    with np.errstate(invalid="ignore", divide="ignore"):
        r = np.log(hh / prev)
    s["eff"] = np.abs(np.nansum(r, axis=1)) / np.nansum(np.abs(r), axis=1)
    return s


def build_table(root: str, s: pd.DataFrame) -> pd.DataFrame:
    """Trailing features over every session, then the window and the declared drops."""
    # The prior 20 COMPLETE sessions (§4). Corrected after the first run: a rolling window over every session let one
    # early-close holiday (no 15:59 bar) blank the next 20 sessions' features, about half of each root's sessions.
    with np.errstate(invalid="ignore", divide="ignore"):
        s["ret_1016"] = np.log(s["c1559"] / s["o1000"]) * 1e4
        rel = s["range_day"] / s["c1559"]
        okA, okV = rel.notna(), s["ret_1016"].notna()
        s["A"] = rel[okA].shift(1).rolling(20, min_periods=20).mean().reindex(s.index)
        s["trail_vol"] = s["ret_1016"][okV].shift(1).rolling(20, min_periods=20).std().reindex(s.index)
    w = s[(s["day"] >= LO[root]) & (s["day"] <= HI)].copy()
    guard_window(w["day"])
    n0 = len(w)
    roll = w["contract"] != w["prev_contract"]
    cb = w["day"].isin(CIRCUIT)
    miss = w[["c0959", "o1000", "c1559", "prev_c1559"]].isna().any(axis=1)
    w["drop"] = np.select([roll, cb, miss], ["roll", "circuit", "missing"], "")
    w.attrs["drops"] = {"sessions_in_window": int(n0), "roll": int(roll.sum()), "circuit": int((cb & ~roll).sum()),
                        "missing": int((miss & ~roll & ~cb).sum())}
    return w[w["drop"] == ""].reset_index(drop=True)


def direction(c0959, prev_c1559) -> np.ndarray:
    return np.sign(np.asarray(c0959, float) - np.asarray(prev_c1559, float))


def roll_guard(t: pd.DataFrame) -> None:
    if (t["contract"] != t["prev_contract"]).any():
        raise GateError("[ROLL] a direction spans a contract change")


def causal_audit(s_row_builder, sessions: pd.DataFrame) -> None:
    """Perturb every price after 09:59 and the direction must not move."""
    base = s_row_builder(sessions)
    pert = sessions.copy()
    for c in ("o1000", "o1500", "c1359", "c1459", "c1559"):
        pert[c] = pert[c] * 1.05
    if not np.array_equal(s_row_builder(pert), base):
        raise GateError("[CAUSAL] the direction reads a price after 09:59")


def gross_bp(D, o, c) -> np.ndarray:
    return np.asarray(D, float) * (np.asarray(c, float) - np.asarray(o, float)) / np.asarray(o, float) * 1e4


def sign_audit(fn=gross_bp) -> None:
    if not (fn(1.0, 100.0, 101.0) > 0 and fn(-1.0, 100.0, 101.0) < 0 and fn(-1.0, 101.0, 100.0) > 0):
        raise GateError("[SIGN] a favourable move does not pay positively")


# ------------------------------------------------------------------ P2 machinery
def walk_forward(X: np.ndarray, y: np.ndarray, burn: int = BURN) -> np.ndarray:
    """yhat_j from OLS (intercept) on rows 0..j-1 only; NaN before the burn-in. Accumulated normal equations."""
    n = len(y)
    Z = np.column_stack([np.ones(n), X])
    outer = np.einsum("ni,nj->nij", Z, Z)
    cxx = np.cumsum(outer, axis=0) - outer                       # sums over rows strictly before j
    cxy = np.cumsum(Z * y[:, None], axis=0) - Z * y[:, None]
    b = np.einsum("nij,nj->ni", np.linalg.pinv(cxx), cxy)
    yh = np.einsum("ni,ni->n", Z, b)
    yh[:burn] = np.nan
    return yh


def wf_audit(X, y, yh, idx, include_own: bool = False) -> None:
    """A second implementation: a fresh lstsq on rows before j (or, broken, including j) at sampled sessions."""
    Z = np.column_stack([np.ones(len(y)), X])
    for j in idx:
        hi = j + 1 if include_own else j
        b = np.linalg.lstsq(Z[:hi], y[:hi], rcond=None)[0]
        if not np.isclose(Z[j] @ b, yh[j], rtol=1e-6, atol=1e-6):
            raise GateError(f"[FIT] forecast {j} is not the fit on earlier sessions only")


def pass_through(y: np.ndarray, yh: np.ndarray, burn: int = PI_BURN) -> np.ndarray:
    """pi_k = sum(y yhat) / sum(yhat^2) over EARLIER forecasts; 0 until `burn` of them exist."""
    ok = np.isfinite(yh)
    pi = np.zeros(len(y))
    num = np.cumsum(np.where(ok, y * np.nan_to_num(yh), 0.0))
    den = np.cumsum(np.where(ok, np.nan_to_num(yh) ** 2, 0.0))
    cnt = np.cumsum(ok)
    prev_num, prev_den, prev_cnt = num - np.where(ok, y * np.nan_to_num(yh), 0), den - np.where(ok, np.nan_to_num(yh) ** 2, 0), cnt - ok
    good = (prev_cnt >= burn) & (prev_den > 0)
    pi[good] = prev_num[good] / prev_den[good]
    return pi


def pi_audit(y, yh, pi, idx, include_own: bool = False) -> None:
    ok = np.isfinite(yh)
    for j in idx:
        hi = j + 1 if include_own else j
        m = ok[:hi]
        yy, hh = y[:hi][m], yh[:hi][m]
        ref = (yy @ hh) / (hh @ hh) if len(hh) >= PI_BURN and (hh @ hh) > 0 else 0.0
        if not np.isclose(ref, pi[j], rtol=1e-9, atol=1e-12):
            raise GateError(f"[PI] pass-through {j} includes an outcome it should not")


def beta_disc(y, yh) -> dict:
    ok = np.isfinite(yh)
    if ok.sum() < 30:
        return {"n": int(ok.sum()), "beta": float("nan"), "t_nw": float("nan")}
    r = ols_nw(y[ok], yh[ok][:, None], NW_LAGS)
    return {"n": int(ok.sum()), "beta": r["coef"][1], "t_nw": r["t_nw"][1], "intercept": r["coef"][0]}


def mean_t(x) -> tuple[float, float]:
    x = np.asarray(x, float)
    if len(x) < 10:
        return float(x.mean()) if len(x) else float("nan"), float("nan")
    r = ols_nw(x, np.empty((len(x), 0)), NW_LAGS)
    return float(x.mean()), float(r["t_nw"][0])


# ------------------------------------------------------------------ reporting
def book_block(t: pd.DataFrame, g: np.ndarray, net: np.ndarray, usd_net: np.ndarray, n_sessions: int, years: float,
               cost_usd: float, cost_bp: np.ndarray) -> dict:
    tpy = len(g) / years
    mg, tg = mean_t(g)
    mn, tn = mean_t(net)
    cum = usd_net
    return {"trades": int(len(g)), "trades_per_year": tpy, "exposure_share_of_sessions": len(g) / n_sessions,
            "gross_mean_bp": mg, "gross_t_nw": tg, "net_mean_bp": mn, "net_t_nw": tn,
            "gross_sharpe_per_trade_ann": sharpe_tpy(g, tpy), "gross_sortino_per_trade_ann": sortino_tpy(g, tpy),
            "net_sharpe_per_trade_ann": sharpe_tpy(net, tpy), "net_sortino_per_trade_ann": sortino_tpy(net, tpy),
            "sigma_bp": float(np.std(g, ddof=1)), "max_dd_usd": max_dd(cum), "net_total_usd": float(cum.sum()),
            "mean_cost_bp": float(np.mean(cost_bp)), "cost_rt_usd": cost_usd,
            "gross_over_cost": mg / float(np.mean(cost_bp)), "breakeven_bp_per_side": mg / 2,
            "dist_gross_bp": dist(g), "dist_net_bp": dist(net)}


def sharpe_tpy(x, tpy):
    x = np.asarray(x, float)
    s = x.std(ddof=1)
    return float(x.mean() / s * math.sqrt(tpy)) if s > 0 else float("nan")


def sortino_tpy(x, tpy):
    x = np.asarray(x, float)
    dn = np.sqrt(np.mean(np.minimum(x, 0.0) ** 2))
    return float(x.mean() / dn * math.sqrt(tpy)) if dn > 0 else float("nan")


def winners(t: pd.DataFrame, g: np.ndarray, usd: np.ndarray) -> dict:
    yr = t["day"].str[:4]
    by_year = {y: {"trades": int((yr == y).sum()), "gross_mean_bp": float(g[yr == y].mean()),
                   "net_usd": float(usd[yr == y].sum())} for y in sorted(yr.unique())}
    srt = np.sort(usd)[::-1]
    half = int(np.searchsorted(np.cumsum(srt), 0.5 * usd.sum()) + 1) if usd.sum() > 0 else None
    j = int(np.argmax(g))
    lng = t["D"].to_numpy() > 0
    pre = (t["day"] < ERA_0DTE).to_numpy()
    return {"by_year": by_year, "profitable_years": int(sum(v["net_usd"] > 0 for v in by_year.values())),
            "long": {"trades": int(lng.sum()), "gross_mean_bp": float(g[lng].mean()), "hit": float((g[lng] > 0).mean())},
            "short": {"trades": int((~lng).sum()), "gross_mean_bp": float(g[~lng].mean()),
                      "hit": float((g[~lng] > 0).mean())},
            "pre_0dte_gross_mean_bp": float(g[pre].mean()), "post_0dte_gross_mean_bp": float(g[~pre].mean()),
            "sessions_to_half_net": half,
            "top_trade": {"day": str(t["day"].iloc[j]), "direction": int(t["D"].iloc[j]), "gross_bp": float(g[j])}}


# ------------------------------------------------------------------ one root
def root_study(root: str) -> dict:
    t0 = time.time()
    spec = micro_spec(root)
    s = load_sessions(root)
    w = build_table(root, s)
    drops = w.attrs["drops"]
    n_sess = len(w)
    w["D"] = direction(w["c0959"], w["prev_c1559"])
    t = w[w["D"] != 0].reset_index(drop=True)
    roll_guard(t)
    causal_audit(lambda x: direction(x["c0959"], x["prev_c1559"]), t)
    sign_audit()
    g = gross_bp(t["D"], t["o1000"], t["c1559"])
    move = gross_bp(np.ones(len(t)), t["o1000"], t["c1559"])
    cost_bp = spec["cost_rt_usd"] / (t["o1000"].to_numpy() * spec["usd_per_point"]) * 1e4
    net = g - cost_bp
    usd_g = t["D"].to_numpy() * (t["c1559"] - t["o1000"]).to_numpy() * spec["usd_per_point"]
    usd_net = usd_g - spec["cost_rt_usd"]
    years = (pd.Timestamp(HI) - pd.Timestamp(LO[root])).days / 365.25
    sigma = float(np.std(g, ddof=1))
    mde = (1.959964 + 0.841621) * sigma / math.sqrt(len(g))
    out = {"root": root, "role": "evidence" if root in EVIDENCE else "development", "micro": spec,
           "window": [LO[root], HI], "drops": drops, "sessions_used": n_sess, "trades": int(len(t)),
           "mde_bp_80pct_power": mde}
    P(f"[{root}] {n_sess} sessions ({drops}); {len(t)} trades; sigma {sigma:.1f} bp -> MDE {mde:.2f} bp "
      f"(printed before any mean)")

    # ---- P1 and N1
    d, D = t["D"].to_numpy(float), t["D"].to_numpy(float)
    labs = strata_labels(t["day"].to_numpy())
    rng = np.random.default_rng(SEED + ROOTS.index(root))
    n1 = {}
    for name in ("week", "month"):
        grp = labs[name]
        dr = permute_null(d, move, grp, DRAWS, rng, check=True) / len(d)
        carry = drift_carry(d, move, grp) / len(d)
        q = qdist(dr, rng, float(g.mean()))
        if abs(q["mean"] - carry) > 3 * q["sd"] / math.sqrt(DRAWS):
            raise GateError(f"[PERM] {root} {name}: draw mean {q['mean']:.3f} vs carry {carry:.3f}")
        q["drift_carry_exact"] = carry
        n1[name] = q
    mg, tg = mean_t(g)
    p1 = 1 - ND.cdf(tg) if np.isfinite(tg) else float("nan")
    ex2020 = ~t["day"].between("2020-02-01", "2020-04-30").to_numpy()
    halves = {}
    for nm, Dh in (("gap", np.sign(t["o0930"] - t["prev_c1559"])), ("open", np.sign(t["c0959"] - t["o0930"]))):
        gh = gross_bp(Dh, t["o1000"], t["c1559"])
        halves[nm] = {"gross_mean_bp": float(gh.mean()), "t_nw": mean_t(gh)[1], "agreement_with_D": float((Dh == D).mean())}
    c0 = move
    out["P1"] = {"book": book_block(t, g, net, usd_net, n_sess, years, spec["cost_rt_usd"], cost_bp),
                 "one_sided_p": p1, "N1": n1, "gross_mean_ex_feb_apr_2020": float(g[ex2020].mean()),
                 "halves": halves, "C0_long_every_window": {"gross_mean_bp": float(c0.mean()), "t_nw": mean_t(c0)[1],
                                                            "hit": float((c0 > 0).mean())},
                 "winners": winners(t, g, usd_net)}
    q = n1["week"]
    out["P1"]["gate1_parts"] = {"above_n1_week_p95_by_2se": bool(mg > q["p95"] + 2 * q["p95_boot_se"]),
                                "unresolved": bool(abs(mg - q["p95"]) <= 2 * q["p95_boot_se"]),
                                "positive_ex_2020": bool(g[ex2020].mean() > 0)}
    P(f"[{root}] P1 gross {mg:+.2f} bp (t {tg:+.2f}), net {net.mean():+.2f}; N1-week p50 {q['p50']:+.2f} p95 "
      f"{q['p95']:+.2f} (SE {q['p95_boot_se']:.2f}); halves gap {halves['gap']['gross_mean_bp']:+.2f} open "
      f"{halves['open']['gross_mean_bp']:+.2f}; C0 {c0.mean():+.2f}")

    # ---- P2a: the prize
    absm, eff = np.abs(move), t["eff"].to_numpy(float)
    top_m = absm >= np.quantile(absm, 0.6)
    top_e = eff >= np.nanquantile(eff, 0.6)
    zr = (pd.Series(g).rank().to_numpy() - (len(g) + 1) / 2) / (len(g) / math.sqrt(12))
    bound = {}
    rng2 = np.random.default_rng(SEED + 100 + ROOTS.index(root))
    for rho in (0.1, 0.2, 0.3):
        vals = []
        for _ in range(200):
            sc = rho * zr + math.sqrt(1 - rho * rho) * rng2.standard_normal(len(g))
            vals.append(float(g[sc >= np.quantile(sc, 0.6)].mean()))
        bound[str(rho)] = {"mean_gross_kept_40pct": float(np.mean(vals)), "net_after_mean_cost": float(np.mean(vals) - cost_bp.mean())}
    out["P2a"] = {"oracle_top40_abs_move": float(g[top_m].mean()), "oracle_top40_efficiency": float(g[top_e].mean()),
                  "attainable_at_rank_corr": bound}

    # ---- P2b: the forecast
    gex = pd.read_csv(gex_path(), encoding="utf-8", dtype={"date": str}).set_index("date")["gex"].astype(float).sort_index()
    gv = gex_prior(gex, t["day"])
    gex_audit(gex, t["day"].iloc[:: max(1, len(t) // 40)].tolist())
    with np.errstate(invalid="ignore", divide="ignore"):
        F = pd.DataFrame({
            "f1_size": np.abs(t["c0959"] / t["prev_c1559"] - 1) / t["A"],
            "f2_agree": ((np.sign(t["o0930"] - t["prev_c1559"]) == np.sign(t["c0959"] - t["o0930"]))
                         & (np.sign(t["o0930"] - t["prev_c1559"]) != 0)).astype(float),
            "f3_orange": (t["h_open"] - t["l_open"]) / (t["A"] * t["prev_c1559"]),
            "f4_oeff": np.where(t["h_open"] > t["l_open"], np.abs(t["c0959"] - t["o0930"]) / (t["h_open"] - t["l_open"]), 0.0),
            "f5_short_gamma": (gv < 0).astype(float),
            "f6_trail_vol": t["trail_vol"],
            "f7_long": (t["D"] > 0).astype(float)})
    ok = F.notna().all(axis=1).to_numpy() & np.isfinite(gv)
    X, y, cb = F[ok].to_numpy(float), g[ok], cost_bp[ok]
    tt = t[ok].reset_index(drop=True)
    yh = walk_forward(X, y)
    fidx = np.flatnonzero(np.isfinite(yh))
    samp = fidx[np.linspace(0, len(fidx) - 1, 12).astype(int)] if len(fidx) else []
    wf_audit(X, y, yh, samp)
    pi = pass_through(y, yh)
    pi_audit(y, yh, pi, samp)
    proj = pi * np.nan_to_num(yh)
    take = np.isfinite(yh) & (proj >= K_COST * cb)
    bd = beta_disc(y, yh)
    net_ok = y - cb
    tick_bp = 2 * spec["tick_points"] / tt["o1000"].to_numpy() * 1e4
    usd_f = (tt["D"].to_numpy() * (tt["c1559"] - tt["o1000"]).to_numpy() * spec["usd_per_point"] - spec["cost_rt_usd"])
    fb = book_block(tt[take], y[take], net_ok[take], usd_f[take], n_sess, years, spec["cost_rt_usd"], cb[take]) \
        if take.sum() >= 2 else {"trades": int(take.sum())}
    fn_mean, fn_t = mean_t(net_ok[take]) if take.sum() else (float("nan"), float("nan"))
    fcast = np.isfinite(yh)
    # N2: features permuted across sessions within each year, targets fixed
    yrs = tt["day"].str[:4].to_numpy()
    rng3 = np.random.default_rng(SEED + 200 + ROOTS.index(root))
    n2_t, n2_net = np.empty(N2_DRAWS), np.empty(N2_DRAWS)
    for k in range(N2_DRAWS):
        Xp = X.copy()
        for yv in np.unique(yrs):
            ii = np.flatnonzero(yrs == yv)
            Xp[ii] = X[rng3.permutation(ii)]
        yhp = walk_forward(Xp, y)
        pip = pass_through(y, yhp)
        tk = np.isfinite(yhp) & (pip * np.nan_to_num(yhp) >= K_COST * cb)
        n2_t[k] = beta_disc(y, yhp)["t_nw"]
        n2_net[k] = float(net_ok[tk].mean()) if tk.sum() else float("nan")
    n2t_q = qdist(n2_t[np.isfinite(n2_t)], rng3, bd["t_nw"])
    coef_signs = {}
    Z = np.column_stack([np.ones(len(y)), X])
    for q_ in (0.25, 0.5, 0.75, 1.0):                             # the fitted coefficients at four points of the path
        j = min(len(y), max(BURN, int(q_ * len(y))))
        b = np.linalg.lstsq(Z[:j], y[:j], rcond=None)[0]
        coef_signs[f"fit_at_{int(q_ * 100)}pct"] = dict(zip(("intercept",) + FEATURES, map(float, b)))
    with np.errstate(invalid="ignore"):
        out["P2b"] = {
            "sessions_with_features": int(ok.sum()), "forecasts": int(fcast.sum()), "beta_disc": bd,
            "N2_beta_t": n2t_q, "N2_filtered_net": {"p50": float(np.nanquantile(n2_net, 0.5)),
                                                     "p95": float(np.nanquantile(n2_net, 0.95))},
            "filter_pass_rate": float(take.sum() / max(1, fcast.sum())), "filtered": fb,
            "filtered_net_mean_bp": fn_mean, "filtered_net_t_nw": fn_t,
            "filtered_net_plus_1_tick_each_fill": float((net_ok[take] - tick_bp[take]).mean()) if take.sum() else float("nan"),
            "removed_net_mean_bp": float(net_ok[fcast & ~take].mean()) if (fcast & ~take).sum() else float("nan"),
            "pi_hat_final": float(pi[fcast][-1]) if fcast.any() else float("nan"),
            "pi_hat_quartiles": [float(np.quantile(pi[fcast], q_)) for q_ in (0.25, 0.5, 0.75)] if fcast.any() else [],
            "corr_yhat_abs_move": float(np.corrcoef(yh[fcast], np.abs(move[ok][fcast]))[0, 1]),
            "corr_yhat_efficiency": float(pd.Series(yh[fcast]).corr(pd.Series(tt["eff"].to_numpy()[fcast]))),
            "coefficients": coef_signs}
    P(f"[{root}] P2 beta_disc {bd['beta']:+.3f} (t {bd['t_nw']:+.2f}; N2 p95 t {n2t_q['p95']:+.2f}); filter passes "
      f"{take.sum()} of {fcast.sum()}; filtered net {fn_mean:+.2f} bp (t {fn_t:+.2f}); oracle |move| "
      f"{out['P2a']['oracle_top40_abs_move']:+.1f}, eff {out['P2a']['oracle_top40_efficiency']:+.1f}")

    # ---- P3
    have = t[["o1500", "c1359", "c1459"]].notna().all(axis=1).to_numpy()
    last_hour = t["D"].to_numpy() * (t["c1459"] - t["c1359"]).to_numpy()
    ex = have & (last_hour < 0)
    g3 = np.where(ex, gross_bp(t["D"], t["o1000"], t["o1500"]), g)
    uw = have & (t["D"].to_numpy() * (t["c1459"] - t["o1000"]).to_numpy() < 0)
    g3b = np.where(uw, gross_bp(t["D"], t["o1000"], t["o1500"]), g)
    dm, dt = mean_t(g3 - g)
    net3 = g3 - cost_bp
    usd3 = g3 / 1e4 * t["o1000"].to_numpy() * spec["usd_per_point"] - spec["cost_rt_usd"]
    out["P3"] = {"exits_at_1500": int(ex.sum()), "missing_bars_held": int((~have).sum()),
                 "paired_diff_mean_bp": dm, "paired_diff_t_nw": dt, "one_sided_p": 1 - ND.cdf(dt) if np.isfinite(dt) else float("nan"),
                 "book": book_block(t, g3, net3, usd3, n_sess, years, spec["cost_rt_usd"], cost_bp),
                 "secondary_underwater": {"exits": int(uw.sum()), "paired_diff_mean_bp": mean_t(g3b - g)[0],
                                          "paired_diff_t_nw": mean_t(g3b - g)[1]}}
    P(f"[{root}] P3 {ex.sum()} exits at 15:00; paired diff {dm:+.2f} bp (t {dt:+.2f})")

    # ---- daily series for the component line (returned, never written)
    daily = pd.DataFrame({"day": w["day"], "net": 0.0, "gross": 0.0})
    daily = daily.set_index("day")
    daily.loc[t["day"], "net"] = usd_net
    daily.loc[t["day"], "gross"] = usd_g
    filt = pd.Series(0.0, index=daily.index)
    filt.loc[tt["day"][take]] = usd_f[take]
    out["component"] = {"net_sharpe_daily_usd": sharpe(daily["net"]), "gross_sharpe_daily_usd": sharpe(daily["gross"]),
                        "net_sortino_daily_usd": sortino(daily["net"]), "hit_rate": float((usd_net > 0).mean()),
                        "skew_daily_net": skew(daily["net"]), "kurtosis_daily_net": kurt(daily["net"]),
                        "filtered_net_sharpe_daily_usd": sharpe(filt) if take.sum() > 1 else float("nan")}
    out["wall_s"] = round(time.time() - t0, 1)
    return {"out": out, "daily_net": daily["net"], "daily_filtered": filt}


# ------------------------------------------------------------------ run
def k8_daily() -> pd.Series:
    s = pd.read_csv(FIXDIR / "fut_index_sessions.csv.gz", encoding="utf-8", dtype={"day": str})
    s = s[(s["root"] == "NQ") & (s["day"] < VAULT)].sort_values("day")
    guard_window(s["day"])
    prev_down = (s["p1600"] < s["p0930"]).shift(1, fill_value=False)
    pnl = np.where(prev_down, (s["p1600"] - (s["p0930"] + 0.25)) * 2.0 - 3.0, 0.0)
    k = pd.Series(pnl, index=s["day"].to_numpy())
    return k[(k.index >= "2016-01-04") & (k.index <= HI)]


def arm_daily() -> pd.Series:
    import importlib.util
    sp = importlib.util.spec_from_file_location("d508c", REPO / "scripts" / "run_d508_stretch_ranker.py")
    m = importlib.util.module_from_spec(sp)
    sys.modules["d508c"] = m
    sp.loader.exec_module(m)
    a = m.load_arm()
    return pd.Series(np.asarray(a["net"], float), index=np.asarray(a["days"]).astype(str))


def corr_on(a: pd.Series, b: pd.Series) -> dict:
    j = pd.concat([a, b], axis=1, join="inner").dropna()
    return {"rho": float(j.iloc[:, 0].corr(j.iloc[:, 1])) if len(j) > 30 else float("nan"), "overlap": int(len(j))}


def holm(ps: dict, alpha: float = 0.05) -> dict:
    items = sorted((v, k) for k, v in ps.items() if np.isfinite(v))
    passed, ok = {}, True
    for i, (p, k) in enumerate(items):
        ok = ok and p <= alpha / (len(items) - i)
        passed[k] = bool(ok)
    return passed


def run() -> dict:
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=len(ROOTS)) as ex:
        res = dict(zip(ROOTS, ex.map(root_study, ROOTS)))
    k8, arm = k8_daily(), arm_daily()
    out = {"pre_registration": PREREG, "credit": "dealer gamma (GEX): SqueezeMetrics", "vault_from": VAULT,
           "roots": {r: res[r]["out"] for r in ROOTS}}
    for r in ROOTS:
        c = out["roots"][r]["component"]
        c["rho_K8"] = corr_on(res[r]["daily_net"], k8)
        c["rho_macd_arm"] = corr_on(res[r]["daily_net"], arm)
        c["rho_other_roots"] = {o: corr_on(res[r]["daily_net"], res[o]["daily_net"])["rho"] for o in ROOTS if o != r}
        c["missing"] = "the other session's plain-break book (unmerged)"
    # ---- gates on the evidence roots
    ev = out["roots"]
    g1_p = {r: ev[r]["P1"]["one_sided_p"] for r in EVIDENCE}
    g1_holm = holm(g1_p)
    gate1 = {r: bool(g1_holm.get(r, False) and ev[r]["P1"]["gate1_parts"]["above_n1_week_p95_by_2se"]
                     and ev[r]["P1"]["gate1_parts"]["positive_ex_2020"]) for r in EVIDENCE}
    passed1 = [r for r in EVIDENCE if gate1[r]]
    unf_p = {r: 1 - ND.cdf(ev[r]["P1"]["book"]["net_t_nw"]) for r in passed1}
    unf_holm = holm(unf_p)
    g2_p = {r: 1 - ND.cdf(ev[r]["P2b"]["filtered_net_t_nw"]) if np.isfinite(ev[r]["P2b"]["filtered_net_t_nw"]) else float("nan")
            for r in passed1}
    g2_holm = holm(g2_p)
    gate2 = {}
    for r in passed1:
        b = ev[r]["P2b"]
        n_f = b["filtered"].get("trades", 0)
        gate2[r] = ("UNRESOLVED" if n_f < 30 else
                    bool(g2_holm.get(r, False) and b["beta_disc"]["beta"] > 0 and b["beta_disc"]["t_nw"] >= 2
                         and b["beta_disc"]["t_nw"] > b["N2_beta_t"]["p95"] and b["filtered_net_plus_1_tick_each_fill"] > 0))
    g3_holm = holm({r: ev[r]["P3"]["one_sided_p"] for r in EVIDENCE})
    gate3 = {r: bool(g3_holm.get(r, False) and ev[r]["P3"]["paired_diff_mean_bp"] > 0 and ev[r]["P3"]["paired_diff_t_nw"] >= 2)
             for r in EVIDENCE}
    verdict = {}
    for r in EVIDENCE:
        if not gate1[r]:
            verdict[r] = "NOT SUPPORTED"
        elif gate2.get(r) is True:
            verdict[r] = "SUPPORTED"
        elif unf_holm.get(r, False):
            verdict[r] = "RULE ONLY"
        else:
            verdict[r] = "MECHANISM ONLY"
    out["gates"] = {"gate1": gate1, "gate1_holm_p": g1_p, "gate2": gate2, "gate2_holm_p": g2_p,
                    "unfiltered_net_holm": unf_holm, "gate3": gate3, "verdict": verdict}
    # ---- predictions
    R = out["roots"]
    full_beats = sum(R[r]["P1"]["book"]["gross_mean_bp"] > max(R[r]["P1"]["halves"]["gap"]["gross_mean_bp"],
                                                                R[r]["P1"]["halves"]["open"]["gross_mean_bp"]) for r in ROOTS)
    q = R["NQ"]["P1"]
    out["predictions"] = {
        "1_NQ_gross_ge_4bp_and_clears_N1_week": bool(q["book"]["gross_mean_bp"] >= 4 and q["gate1_parts"]["above_n1_week_p95_by_2se"]),
        "2_YM_fails_gate1": bool(not gate1["YM"]),
        "3_at_most_one_evidence_root_passes_gate1": bool(sum(gate1.values()) <= 1),
        "4_full_beats_both_halves_on_3_of_4": bool(full_beats >= 3),
        "5_beta_disc_t_below_2_on_both_evidence": bool(all(not (R[r]["P2b"]["beta_disc"]["t_nw"] >= 2) for r in EVIDENCE)),
        "6_P3_positive_on_NQ_t_below_2_on_evidence": bool(R["NQ"]["P3"]["paired_diff_mean_bp"] > 0
                                                          and all(R[r]["P3"]["paired_diff_t_nw"] < 2 for r in EVIDENCE)),
        "7_long_gross_exceeds_short_every_root": bool(all(R[r]["P1"]["winners"]["long"]["gross_mean_bp"]
                                                          > R[r]["P1"]["winners"]["short"]["gross_mean_bp"] for r in ROOTS))}
    out["max_drawdown_convention"] = {"sign": "positive", "note": "max_dd_usd is a POSITIVE drawdown in US DOLLARS on the "
                                      "cumulative-sum P&L at one micro (peak minus trough), not a fraction of peak.",
                                      "record": "D542"}
    out["wall_min"] = round((time.time() - t0) / 60, 2)
    licence_guard(out)
    OUT.write_text(json.dumps(out, indent=1, default=_json), encoding="utf-8")
    P(f"gates {out['gates']}")
    P(f"predictions {out['predictions']}")
    P(f"wrote {OUT.relative_to(REPO)} in {out['wall_min']} min")
    return out


def _json(o):
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    return float(o)


# ------------------------------------------------------------------ self-test
def _raises(fn, tag, fails):
    try:
        fn()
    except GateError:
        return
    fails.append(f"{tag}: a deliberately broken input did not raise")


def selftest() -> int:
    fails: list[str] = []
    s = load_sessions("YM")
    w = build_table("YM", s)
    w["D"] = direction(w["c0959"], w["prev_c1559"])
    t = w[w["D"] != 0].reset_index(drop=True)
    guard_window(t["day"])
    _raises(lambda: guard_window(np.array(["2024-12-31", "2025-03-03"])), "vault guard", fails)
    roll_guard(t)
    rolled = t.copy()
    rolled.loc[5, "prev_contract"] = "XXX"
    _raises(lambda: roll_guard(rolled), "roll guard", fails)
    causal_audit(lambda x: direction(x["c0959"], x["prev_c1559"]), t)
    _raises(lambda: causal_audit(lambda x: direction(x["c1559"], x["prev_c1559"]), t), "causality canary", fails)
    sign_audit()
    _raises(lambda: sign_audit(lambda D, o, c: D * (o - c)), "sign audit", fails)
    # the permutation: long counts per week kept, draw mean at the exact carry; oracle and random books
    move = gross_bp(np.ones(len(t)), t["o1000"], t["c1559"])
    d = t["D"].to_numpy(float)
    grp = strata_labels(t["day"].to_numpy())["week"]
    rng = np.random.default_rng(3)
    dr = permute_null(d, move, grp, 400, rng, check=True)
    if abs(dr.mean() - drift_carry(d, move, grp)) > 3 * dr.std(ddof=1) / math.sqrt(400):
        fails.append("permutation mean is not the exact carry")
    orc = np.sign(move)
    if not float(orc @ move) > np.quantile(permute_null(orc, move, grp, 400, rng), 0.95):
        fails.append("the oracle direction does not beat the null")
    rnd = np.where(rng.random(len(d)) < 0.5, 1.0, -1.0)
    pct = (permute_null(rnd, move, grp, 400, rng) < float(rnd @ move)).mean()
    if not 0.02 < pct < 0.98:
        fails.append(f"a random direction sits at the {pct:.3f} quantile")
    # the walk-forward: a second implementation, and a fit that includes its own session raises
    rs = np.random.default_rng(5)
    X = rs.standard_normal((600, 7))
    y = X @ rs.standard_normal(7) + rs.standard_normal(600)
    yh = walk_forward(X, y)
    idx = [260, 400, 599]
    wf_audit(X, y, yh, idx)
    _raises(lambda: wf_audit(X, y, yh, idx, include_own=True), "fit canary", fails)
    pi = pass_through(y, yh)
    pi_audit(y, yh, pi, idx)
    _raises(lambda: pi_audit(y, yh, pi, idx, include_own=True), "pi canary", fails)
    # GEX: prior row only, and a same-day mapper raises
    gex = pd.Series([1.0, 2.0, 3.0, 4.0], index=["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"])
    sess = ["2020-01-03", "2020-01-06", "2020-01-07"]
    gex_audit(gex, sess)
    _raises(lambda: gex_audit(gex, sess, mapper=lambda g_, s_: g_.reindex(s_).to_numpy(float)), "GEX same-day canary", fails)
    _raises(lambda: licence_guard({"gex": list(range(100))}), "licence guard", fails)
    # holm
    if holm({"a": 0.01, "b": 0.04}) != {"a": True, "b": True} or holm({"a": 0.03, "b": 0.04}) != {"a": False, "b": False}:
        fails.append("holm")
    P(f"YM: {len(w)} sessions, {len(t)} trades, drops {w.attrs['drops']}")
    P("SELFTEST " + ("PASS" if not fails else "FAIL"))
    for f in fails:
        P("  -", f)
    return 0 if not fails else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.run:
        run()
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

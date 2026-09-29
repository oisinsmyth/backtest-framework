"""D669 Stage 0 -- where the admitted MACD arm's in-sample returns come from.

    python scripts/stage0_d669_macd_mechanism.py --selftest
    python scripts/stage0_d669_macd_mechanism.py --run          # -> data/stage0_d669_macd_mechanism.json

PRE-REGISTRATION: docs/decisions/D669-STAGE-0-DESIGN-where-the-macd-arms-returns-come-from.md (39a25d3), committed
before this file existed. The arm is built by D504's `build()`, clipped to 2016-01-04 -> 2023-12-29 exactly as D508's
`load_arm()` clips it, and simulated trade by trade with D503's `simulate_trades()`. The arm's 2024+ (spent by D503)
is never scored. Five questions: Q1 drift or timing (direction-permutation null in five strata), Q2 lookback
momentum, Q3 trend days or volatility, Q4 the price level, Q5 the deflated Sharpe and the parameter neighbourhood.

`scripts/fast_null.py` does not apply (a label permutation over trades, not a panel rotation). Its exactness rule is
kept: the permutation scorer is asserted equal to the trade-loop scorer on the unpermuted book.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path
from statistics import NormalDist

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.validation.hurdle_p import p3  # noqa: E402
from d484_offdiagonal_and_macd import (  # noqa: E402
    IMP_LEN, IMP_SIG, MACD_FAST, MACD_SIG, MACD_SLOW, SEGMENTS, SPECS, ema, impulse_macd, macd_hist, sma, smma,
    zlema)
from d491_conditional_hold import DAY_FIRST_DECIDE, LAST_SEG, simulate  # noqa: E402
from d495_agree_confluence import FIX, META, agree_signal  # noqa: E402
from d503_forward_book import series_window, simulate_trades  # noqa: E402
from d504_arm_full_history import FULL_HI, FULL_LO, M_HOLD, ROOT, build  # noqa: E402

OUT = REPO / "data" / "stage0_d669_macd_mechanism.json"
D495_JSON = REPO / "data" / "d495_agree_confluence.json"
PREREG = "39a25d3"
LO, HI = "2016-01-04", "2023-12-29"
REPRO_SESSIONS, REPRO_NET = 1876, 15423.0
NSEG = len(SEGMENTS)
DRAWS, SEED, BOOT = 10_000, 669, 1000
STRATA = ("whole", "year", "quarter", "month", "week")          # coarse -> fine
COST_MEASURED = 4.21                                             # D527's measured round trip
LOOKBACKS = {"R1h": 1, "RON": "on", "R1d": 23, "R2d": 46, "R5d": 115, "R20d": 460}
GRID = {"fast": (9, 12, 15), "slow": (20, 26, 32), "sig": (7, 9, 11), "imp": (26, 34, 42), "M": (3, 4, 5, 6, 7, 8)}
DEFAULT = {"fast": MACD_FAST, "slow": MACD_SLOW, "sig": MACD_SIG, "imp": IMP_LEN, "M": M_HOLD}
N_ALT = 250                                                      # the survey's count of cells looked at from D484
EULER = 0.5772156649015329
ND = NormalDist()


def P(*a, **k):
    print(*a, **k, flush=True)


class GateError(AssertionError):
    pass


# ------------------------------------------------------------------ statistics
def sharpe(x) -> float:
    x = np.asarray(x, float)
    s = x.std(ddof=1)
    return float(x.mean() / s * math.sqrt(252)) if s > 0 else float("nan")


def sortino(x) -> float:
    x = np.asarray(x, float)
    dn = np.sqrt(np.mean(np.minimum(x, 0.0) ** 2))
    return float(x.mean() / dn * math.sqrt(252)) if dn > 0 else float("nan")


def max_dd(x) -> float:
    eq = np.cumsum(np.asarray(x, float))
    return float(np.max(np.maximum.accumulate(np.concatenate([[0.0], eq]))[1:] - eq))


def skew(x) -> float:
    x = np.asarray(x, float)
    s = x.std()
    return float(((x - x.mean()) ** 3).mean() / s ** 3) if s > 0 else float("nan")


def kurt(x) -> float:
    """Non-excess kurtosis (a normal is 3)."""
    x = np.asarray(x, float)
    s = x.std()
    return float(((x - x.mean()) ** 4).mean() / s ** 4) if s > 0 else float("nan")


def tstat(x) -> float:
    x = np.asarray(x, float)
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 1 and x.std(ddof=1) > 0 else float("nan")


def qdist(draws: np.ndarray, rng, obs: float | None = None) -> dict:
    boot = np.array([np.quantile(rng.choice(draws, len(draws)), 0.95) for _ in range(BOOT)])
    out = {"p05": float(np.quantile(draws, 0.05)), "p50": float(np.quantile(draws, 0.5)),
           "p95": float(np.quantile(draws, 0.95)), "p95_boot_se": float(boot.std(ddof=1)),
           "mean": float(draws.mean()), "sd": float(draws.std(ddof=1)), "draws": int(len(draws))}
    if obs is not None:
        out["percentile"] = float((draws < obs).mean() * 100)
        out["margin_in_se"] = float((obs - out["p95"]) / out["p95_boot_se"]) if out["p95_boot_se"] > 0 else float("nan")
    return out


def ols_nw(y, X, lags: int) -> dict:
    """OLS with Newey-West (Bartlett) standard errors."""
    y = np.asarray(y, float)
    X = np.column_stack([np.ones(len(y)), np.asarray(X, float)])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    e = y - X @ b
    xe = X * e[:, None]
    S = xe.T @ xe
    for lag in range(1, lags + 1):
        w = 1.0 - lag / (lags + 1.0)
        G = xe[lag:].T @ xe[:-lag]
        S += w * (G + G.T)
    inv = np.linalg.inv(X.T @ X)
    se = np.sqrt(np.diag(inv @ S @ inv))
    return {"coef": b.tolist(), "se_nw": se.tolist(), "t_nw": (b / se).tolist(), "n": int(len(y)), "lags": lags}


# ------------------------------------------------------------------ the arm
def _d508():
    s = importlib.util.spec_from_file_location("d508c", REPO / "scripts" / "run_d508_stretch_ranker.py")
    m = importlib.util.module_from_spec(s)
    sys.modules["d508c"] = m
    s.loader.exec_module(m)
    return m


def load_panel() -> dict:
    """D504's build over the fixture, clipped to the window as D508's load_arm clips it; plus the continuous series."""
    meta = json.loads(Path(META).read_text(encoding="utf-8"))
    spec = json.loads(Path(SPECS).read_text(encoding="utf-8"))
    d_all = pd.read_csv(FIX, encoding="utf-8")
    pk = build(d_all, meta, spec)
    s = series_window(ROOT, d_all, meta, FULL_LO, FULL_HI)
    days_k = np.asarray(pk["days"]).astype(str)
    m = (days_k >= LO) & (days_k <= HI)
    full_rows = np.flatnonzero(pk["keep"])[m]                   # row index into the continuous (pre-keep) series
    # the contract of every bar, rebuilt exactly as series_window selects its rows (for the roll-crossing disclosure)
    d = d_all[(d_all["root"] == ROOT) & d_all["same_front"]]
    d = d[d["day"].between(FULL_LO, FULL_HI)].sort_values("day", kind="stable")
    con = np.repeat(d["contract"].to_numpy(), NSEG)
    return {"O": pk["O"][m], "C": pk["C"][m], "AGREE": pk["AGREE"][m], "days": days_k[m],
            "level": np.asarray(pk["level"], float)[m], "days_all": days_k[days_k <= HI],
            "level_all": np.asarray(pk["level"], float)[days_k <= HI], "keep": pk["keep"], "win": m,
            "full_rows": full_rows, "series": s, "con": con, "first": pk["first"], "tick_pts": pk["tick_pts"],
            "tick_usd": pk["tick_usd"], "point_usd": pk["point_usd"], "cost_ticks": pk["cost"],
            "cost_usd": pk["cost"] * pk["tick_usd"]}


def trade_table(pn: dict, sig=None, M: int = M_HOLD, cost_ticks=None) -> pd.DataFrame:
    """D503's simulate_trades on the window, with each trade's prices re-derived from the bars it names."""
    sig = pn["AGREE"] if sig is None else sig
    ck = pn["cost_ticks"] if cost_ticks is None else cost_ticks
    rows = simulate_trades(pn["O"], pn["C"], sig, pn["first"], M, ck, pn["tick_pts"])
    t = pd.DataFrame(rows, columns=["i", "entry_t", "exit_seg", "d", "net_ticks", "kind"])
    t = t.sort_values(["i", "entry_t"], kind="stable").reset_index(drop=True)
    i, et, xs = t["i"].to_numpy(), t["entry_t"].to_numpy(), t["exit_seg"].to_numpy()
    t["entry_px"] = pn["O"][i, et + 1]
    t["exit_px"] = np.where(t["kind"] == "FLATTEN", pn["C"][i, LAST_SEG], pn["O"][i, xs])
    t["m"] = (t["exit_px"] - t["entry_px"]) * pn["point_usd"]            # the window's move, signed long, $
    t["g"] = t["d"] * t["m"]                                              # gross, $
    t["net"] = t["net_ticks"] * pn["tick_usd"]
    t["bars"] = np.where(t["kind"] == "FLATTEN", LAST_SEG - et, xs - (et + 1))
    t["day"] = pn["days"][i]
    t["bp"] = t["d"] * (t["exit_px"] - t["entry_px"]) / t["entry_px"] * 1e4
    t["fee_bp"] = pn["cost_usd"] / (t["entry_px"] * pn["point_usd"]) * 1e4
    return t


def session_sum(t: pd.DataFrame, col: str, n: int) -> np.ndarray:
    return np.bincount(t["i"].to_numpy(), weights=t[col].to_numpy(float), minlength=n)


def lag_audit(pn: dict, t: pd.DataFrame, sig=None, M: int = M_HOLD) -> None:
    """A second implementation of the state machine, per session in plain Python, never calling simulate_trades."""
    sig = np.nan_to_num(pn["AGREE"] if sig is None else sig, nan=0.0)
    O, C = pn["O"], pn["C"]
    mine = []
    for i in range(O.shape[0]):
        pos, et = 0.0, -1
        for tt in range(pn["first"], LAST_SEG):
            s, px = sig[i, tt], O[i, tt + 1]
            if pos != 0 and tt - et >= M and s * pos <= 0 and np.isfinite(px):
                mine.append((i, et, tt + 1, pos))
                pos = 0.0
            if pos == 0 and s != 0 and np.isfinite(px):
                pos, et = s, tt
        if pos != 0 and np.isfinite(C[i, LAST_SEG]):
            mine.append((i, et, LAST_SEG, pos))
    theirs = list(zip(t["i"], t["entry_t"], t["exit_seg"], t["d"]))
    if sorted(mine) != sorted((int(a), int(b), int(c), float(e)) for a, b, c, e in theirs):
        raise GateError(f"[LAG] the second implementation finds {len(mine)} trades against {len(theirs)}, or "
                        "different ones")
    held = sig[t["i"].to_numpy(), t["entry_t"].to_numpy()]
    if not np.array_equal(held, t["d"].to_numpy()):
        raise GateError("[LAG] a trade's direction is not the signal at its decision bar")
    recon = t["d"] * (t["exit_px"] - t["entry_px"]) / pn["tick_pts"] - pn["cost_ticks"]
    if not np.allclose(recon.to_numpy(), t["net_ticks"].to_numpy(), atol=1e-9, rtol=0):
        raise GateError("[LAG] entry at the open of t+1 does not reproduce the simulator's P&L")


def sign_audit(point_usd: float, gross_fn=None) -> None:
    f = gross_fn or (lambda d, a, b: d * (b - a) * point_usd)
    if not (f(1.0, 100.0, 101.0) > 0 and f(-1.0, 100.0, 101.0) < 0 and f(-1.0, 101.0, 100.0) > 0):
        raise GateError("[SIGN] a favourable move does not pay positively")


# ------------------------------------------------------------------ Q1: the direction permutation
def strata_labels(days: np.ndarray) -> dict[str, np.ndarray]:
    dt = pd.to_datetime(pd.Series(days))
    iso = dt.dt.isocalendar()
    lab = {"whole": np.zeros(len(days), np.int64), "year": dt.dt.year.to_numpy(),
           "quarter": (dt.dt.year * 10 + dt.dt.quarter).to_numpy(), "month": (dt.dt.year * 100 + dt.dt.month).to_numpy(),
           "week": (iso["year"].astype(int) * 100 + iso["week"].astype(int)).to_numpy()}
    return {k: pd.factorize(v)[0] for k, v in lab.items()}


def drift_carry(d: np.ndarray, m: np.ndarray, grp: np.ndarray) -> float:
    """N1's exact expectation: sum over strata of n x mean(d) x mean(m)."""
    n = np.bincount(grp)
    sd, sm = np.bincount(grp, weights=d), np.bincount(grp, weights=m)
    ok = n > 0
    return float(np.sum(sd[ok] * sm[ok] / n[ok]))


def permute_null(d: np.ndarray, m: np.ndarray, grp: np.ndarray, draws: int, rng, check: bool = False) -> np.ndarray:
    """Permute the direction labels within each stratum; the windows, the long count per stratum and the cost stay."""
    order = np.argsort(grp, kind="stable")
    gs = grp[order]
    out = np.empty(draws)
    for k in range(draws):
        perm = np.lexsort((rng.random(len(d)), grp))
        dp = np.empty_like(d)
        dp[order] = d[perm]
        if check and k < 20:
            if not np.array_equal(gs, grp[perm]):
                raise GateError("[PERM] a label left its stratum")
            if not np.array_equal(np.bincount(grp, weights=(dp > 0)), np.bincount(grp, weights=(d > 0))):
                raise GateError("[PERM] a stratum's long count changed")
        out[k] = float(np.dot(dp, m))
    return out


# ------------------------------------------------------------------ Q2: lookback signs
def lookback_flat(lc: np.ndarray, L) -> np.ndarray:
    """sign(lc[f] - lc[f - L]) for every bar f of the continuous series; RON reads the prior session's h15 close."""
    n = len(lc)
    prev = np.full(n, np.nan)
    if L == "on":
        f = np.arange(n)
        src = (f // NSEG) * NSEG - (NSEG - LAST_SEG)          # (row - 1) * 23 + 21
        ok = src >= 0
        prev[ok] = lc[src[ok]]
    else:
        prev[L:] = lc[:-L]
    with np.errstate(invalid="ignore"):
        s = np.sign(lc - prev)
    return s                                                    # NaN where undefined


def lookback_at(lc: np.ndarray, L, flat_idx: np.ndarray) -> np.ndarray:
    """The same sign, computed only from bars <= f (used by the causality check)."""
    f = np.asarray(flat_idx)
    src = (f // NSEG) * NSEG - (NSEG - LAST_SEG) if L == "on" else f - L
    out = np.full(len(f), np.nan)
    ok = src >= 0
    with np.errstate(invalid="ignore"):
        out[ok] = np.sign(lc[f[ok]] - lc[src[ok]])
    return out


def to_panel(flat: np.ndarray, pn: dict) -> np.ndarray:
    k = len(flat) // NSEG
    return flat[:k * NSEG].reshape(k, NSEG)[pn["keep"]][pn["win"]]


# ------------------------------------------------------------------ Q5: indicators with parameters
def ema_cache(lc):
    return {n: ema(lc, n) for n in sorted(set(GRID["fast"]) | set(GRID["slow"]))}


def macd_hist_p(E: dict, lc, fast, slow, sig):
    m = E[fast] - E[slow]
    return m - ema(m, sig)


def impulse_p(lh, ll, lc, n, sig=IMP_SIG):
    hlc3 = (lh + ll + lc) / 3.0
    mi, hi, lo = zlema(hlc3, n), smma(lh, n), smma(ll, n)
    md = np.where(mi > hi, mi - hi, np.where(mi < lo, mi - lo, 0.0))
    md = np.where(np.isfinite(mi) & np.isfinite(hi) & np.isfinite(lo), md, np.nan)
    return md - sma(md, sig), md


def agree_from(ihist, md, mh, pn) -> np.ndarray:
    b1 = np.where(md == 0.0, 0.0, np.sign(ihist))
    b2 = np.sign(mh)
    return to_panel(agree_signal(b1, b2), pn)


# ------------------------------------------------------------------ Q5a: deflated Sharpe
def expected_max_sr(V: float, N: int) -> float:
    if N <= 1:
        return 0.0                                              # no search: the benchmark is zero (PSR)
    return math.sqrt(V) * ((1 - EULER) * ND.inv_cdf(1 - 1 / N) + EULER * ND.inv_cdf(1 - 1 / (N * math.e)))


def psr(sr: float, sr0: float, T: int, g3: float, g4: float) -> float:
    return ND.cdf((sr - sr0) * math.sqrt(T - 1) / math.sqrt(1 - g3 * sr + (g4 - 1) / 4 * sr * sr))


def dsr(sr: float, T: int, g3: float, g4: float, V: float, N: int) -> dict:
    s0 = expected_max_sr(V, N)
    return {"N": int(N), "V_per_session": V, "sr0_per_session": s0, "sr0_annual": s0 * math.sqrt(252),
            "dsr": psr(sr, s0, T, g3, g4)}


# ------------------------------------------------------------------ reporting helpers
def dist(x: np.ndarray) -> dict:
    x = np.asarray(x, float)
    n = len(x)
    srt = np.sort(x)
    k = int(math.floor(0.01 * n))
    wins, loss = x[x > 0], x[x < 0]
    return {"count": n, "mean": float(x.mean()), "median": float(np.median(x)), "win_rate": float((x > 0).mean()),
            "payoff": float(wins.mean() / -loss.mean()) if len(wins) and len(loss) else float("nan"),
            "skew": skew(x), "kurtosis": kurt(x),
            "mean_ex_top1pct": float(srt[:n - k].mean()) if k else float(x.mean()),
            "mean_ex_bottom1pct": float(srt[k:].mean()) if k else float(x.mean()),
            "mean_trimmed_both": float(srt[k:n - k].mean()) if k else float(x.mean()), "trim_k": k}


def performance(net_s: np.ndarray, gross_s: np.ndarray, t: pd.DataFrame, n_sessions: int, cost_usd: float) -> dict:
    pp = p3(net_s)
    mg = float(t["g"].mean()) if len(t) else float("nan")
    return {"net_sharpe": sharpe(net_s), "net_sortino": sortino(net_s), "gross_sharpe": sharpe(gross_s),
            "gross_sortino": sortino(gross_s), "net_total": float(net_s.sum()), "gross_total": float(gross_s.sum()),
            "sigma_daily": float(net_s.std(ddof=1)), "max_dd": max_dd(net_s), "worst_day": float(net_s.min()),
            "exposure_share_of_day_bars": float(t["bars"].sum() / (n_sessions * (LAST_SEG - DAY_FIRST_DECIDE))),
            "trades": int(len(t)), "mean_gross_per_trade": mg, "two_c_usd": cost_usd,
            "gross_over_2c": mg / cost_usd, "breakeven_rt_usd": mg,
            "breakeven_bp_per_side": float(t["bp"].mean() / 2) if len(t) else float("nan"),
            "hit_rate_traded_sessions": float((net_s[session_count(t, n_sessions) > 0] > 0).mean()),
            "p3a_breaches_per_year": pp["p3a_breaches_per_year"], "p3b_life_cost": pp["p3b_life_cost"]}


def session_count(t, n):
    return np.bincount(t["i"].to_numpy(), minlength=n)


def winners(net_s: np.ndarray, days: np.ndarray, t: pd.DataFrame) -> dict:
    yrs = pd.Series(net_s).groupby(pd.Series(days).str[:4]).sum()
    srt = np.sort(net_s)[::-1]
    cum = np.cumsum(srt)
    half = int(np.searchsorted(cum, 0.5 * net_s.sum()) + 1) if net_s.sum() > 0 else None
    top = t.loc[t["g"].idxmax()]
    bot = t.loc[t["g"].idxmin()]
    return {"per_year_net": {k: float(v) for k, v in yrs.items()}, "profitable_years": int((yrs > 0).sum()),
            "years": int(len(yrs)), "sessions_to_half_pnl": half,
            "top_trade": {"day": str(top["day"]), "direction": int(top["d"]), "gross": float(top["g"])},
            "worst_trade": {"day": str(bot["day"]), "direction": int(bot["d"]), "gross": float(bot["g"])},
            "top1_session_share": float(srt[0] / net_s.sum()), "top10_session_share": float(srt[:10].sum() / net_s.sum())}


def side_block(t: pd.DataFrame, n: int, side: int) -> dict:
    s = t[t["d"] == side]
    net_s = session_sum(s, "net", n)
    return {"trades": int(len(s)), "share_of_trades": float(len(s) / len(t)), "gross_total": float(s["g"].sum()),
            "net_total": float(s["net"].sum()), "hit_rate": float((s["g"] > 0).mean()),
            "mean_gross": float(s["g"].mean()), "net_sharpe_of_its_sessions": sharpe(net_s),
            "net_sortino_of_its_sessions": sortino(net_s), "gross_distribution": dist(s["g"].to_numpy())}


# ------------------------------------------------------------------ the run
def run(write: bool = True) -> dict:
    t0 = time.time()
    arm = _d508().load_arm()
    pn = load_panel()
    n = len(pn["days"])
    if not np.array_equal(np.asarray(arm["days"]).astype(str), pn["days"]):
        raise GateError("[REPRO] the panel's sessions differ from load_arm's")
    t = trade_table(pn)
    net_s, gross_s = session_sum(t, "net", n), session_sum(t, "g", n)
    gross_tk = session_sum(t.assign(gt=t["g"] / pn["tick_usd"]), "gt", n)
    if not (np.allclose(net_s, arm["net"], atol=1e-6, rtol=0) and np.allclose(gross_tk * pn["tick_usd"], arm["gross"],
                                                                                atol=1e-6, rtol=0)):
        raise GateError("[REPRO] trade rows do not sum to load_arm per session")
    if n != REPRO_SESSIONS or abs(net_s.sum() - REPRO_NET) >= 1.0 or max(pn["days"]) > HI:
        raise GateError(f"[REPRO] {n} sessions, ${net_s.sum():,.2f}")
    lag_audit(pn, t)
    sign_audit(pn["point_usd"])
    if np.allclose(net_s, gross_s):
        raise GateError("[QTY] gross equals net")
    P(f"arm reproduced: {n} sessions, ${net_s.sum():,.0f} net, {len(t)} trades; lag, sign and quantity audits pass")

    d, m, g = t["d"].to_numpy(float), t["m"].to_numpy(float), t["g"].to_numpy(float)
    G = float(g.sum())
    if abs(float(np.dot(d, m)) - G) > 1e-6:
        raise GateError("[EXACT] the permutation scorer differs from the trade-loop scorer")

    # ---- the arm in full
    res: dict = {"pre_registration": PREREG, "window": [LO, HI], "sessions": n}
    res["arm"] = {"performance": performance(net_s, gross_s, t, n, pn["cost_usd"]),
                  "trade_distribution_gross": dist(g), "trade_distribution_net": dist(t["net"].to_numpy()),
                  "holding_bars_mean": float(t["bars"].mean()),
                  "entry_hour_share": {SEGMENTS[k + 1]: float(v) for k, v in
                                       t["entry_t"].value_counts(normalize=True).sort_index().items()},
                  "exit_flatten_share": float((t["kind"] == "FLATTEN").mean()),
                  "winners": winners(net_s, pn["days"], t)}
    net_meas = gross_s - COST_MEASURED * session_count(t, n)
    res["arm"]["at_measured_cost_4.21"] = {"net_sharpe": sharpe(net_meas), "net_sortino": sortino(net_meas),
                                            "net_total": float(net_meas.sum())}
    pa = res["arm"]["performance"]
    P(f"arm: net Sharpe {pa['net_sharpe']:.3f} / Sortino {pa['net_sortino']:.3f}; gross {pa['gross_sharpe']:.3f} / "
      f"{pa['gross_sortino']:.3f}; gross/trade ${pa['mean_gross_per_trade']:.2f} ({pa['gross_over_2c']:.2f} x 2c)")

    # ---- Q1
    res["Q1"] = {"long": side_block(t, n, 1), "short": side_block(t, n, -1)}
    c0 = float(m.sum())
    c0_net_s = session_sum(t.assign(c0=t["m"] - pn["cost_usd"]), "c0", n)
    res["Q1"]["C0_long_in_every_arm_window"] = {"gross_total": c0, "net_total": float(c0_net_s.sum()),
                                                "net_sharpe": sharpe(c0_net_s), "net_sortino": sortino(c0_net_s),
                                                "hit_rate": float((m > 0).mean())}
    labs = strata_labels(t["day"].to_numpy())
    rng = np.random.default_rng(SEED)
    q1n = {}
    for name in STRATA:
        grp = labs[name]
        dr = permute_null(d, m, grp, DRAWS, rng, check=True)
        D = drift_carry(d, m, grp)
        q = qdist(dr, rng, G)
        se_mean = q["sd"] / math.sqrt(DRAWS)
        if abs(q["mean"] - D) > 3 * se_mean:
            raise GateError(f"[PERM] {name}: draw mean {q['mean']:.1f} vs analytic {D:.1f}")
        q.update({"strata": int(grp.max() + 1), "drift_carry_exact": D,
                  "smallest_timing_value_distinguishable": q["p95"] - D})
        q1n[name] = q
        P(f"N1 {name:>7} ({q['strata']:>3} strata): drift carry ${D:,.0f}; p50 ${q['p50']:,.0f} p95 ${q['p95']:,.0f} "
          f"(SE {q['p95_boot_se']:.0f}); smallest distinguishable timing ${q['p95'] - D:,.0f}")
    P(f"G (arm gross) = ${G:,.0f}")
    res["Q1"]["G"] = G
    res["Q1"]["N1"] = q1n
    drift_share = q1n["whole"]["drift_carry_exact"] / G
    passes = {k: G > v["p95"] + 2 * v["p95_boot_se"] for k, v in q1n.items()}
    unresolved = {k: abs(G - v["p95"]) <= 2 * v["p95_boot_se"] for k, v in q1n.items()}
    finest = next((k for k in reversed(STRATA) if passes[k]), "none")
    res["Q1"]["bars"] = {"Q1_T": passes["whole"], "drift_share": drift_share,
                         "Q1_D": "timing dominates" if drift_share < 0.5 else "drift dominates",
                         "Q1_H_finest_beaten": finest, "pass_by_stratum": passes, "unresolved_by_stratum": unresolved}
    P(f"Q1: drift share {drift_share:.3f}; beats: {passes}; finest {finest}")

    # ---- Q2
    s = pn["series"]
    lc = s["log_close"]
    flat_idx = pn["full_rows"][t["i"].to_numpy()] * NSEG + t["entry_t"].to_numpy()
    arm_daily = net_s
    q2 = {}
    for name, L in LOOKBACKS.items():
        sg_flat = lookback_flat(lc, L)
        sg = np.nan_to_num(sg_flat[flat_idx], nan=0.0)
        nz = sg != 0
        agree = float((sg[nz] == d[nz]).mean())
        subst = float(np.dot(sg, m))
        dis = nz & (sg != d)
        dis_g = g[dis]
        # roll crossings of the lookback window at the arm's entries
        if L == "on":
            src = (flat_idx // NSEG) * NSEG - (NSEG - LAST_SEG)
        else:
            src = flat_idx - L
        okc = src >= 0
        cross = float(np.mean(pn["con"][flat_idx[okc]] != pn["con"][src[okc]]))
        # the free-running book
        sig_p = to_panel(sg_flat, pn)
        tf = trade_table(pn, sig=np.nan_to_num(sig_p, nan=0.0))
        fn, fg = session_sum(tf, "net", n), session_sum(tf, "g", n)
        q2[name] = {"L_bars": L if L != "on" else "t+2", "agreement": agree, "undefined_or_zero": int((~nz).sum()),
                    "substitution_gross": subst, "substitution_share_of_G": subst / G,
                    "disagreement_trades": int(dis.sum()), "disagreement_arm_gross": float(dis_g.sum()),
                    "disagreement_arm_mean": float(dis_g.mean()) if dis.any() else float("nan"),
                    "disagreement_t": tstat(dis_g) if dis.sum() > 1 else float("nan"),
                    "lookback_window_crosses_a_roll_share": cross,
                    "free_running": {"net_sharpe": sharpe(fn), "net_sortino": sortino(fn), "gross_sharpe": sharpe(fg),
                                     "gross_sortino": sortino(fg), "net_total": float(fn.sum()), "trades": int(len(tf)),
                                     "hit_rate": float((tf["g"] > 0).mean()) if len(tf) else float("nan"),
                                     "skew_daily_net": skew(fn), "corr_with_arm_daily_net": float(np.corrcoef(fn, arm_daily)[0, 1]),
                                     "max_dd": max_dd(fn)}}
        r = q2[name]
        P(f"Q2 {name:>4}: agree {agree:.3f}; subst ${subst:,.0f} ({subst / G:.2f} of G); disagreement {dis.sum()} "
          f"trades, arm gross ${dis_g.sum():,.0f} (t {r['disagreement_t']:+.2f}); free-running net Sharpe "
          f"{r['free_running']['net_sharpe']:+.3f} (rho {r['free_running']['corr_with_arm_daily_net']:+.2f})")
    reduces = [k for k, v in q2.items() if v["agreement"] >= 0.80 and v["substitution_share_of_G"] >= 0.80]
    adds = [k for k, v in q2.items() if v["disagreement_arm_gross"] > 0 and v["disagreement_t"] > 2]
    nearest = max(reduces, key=lambda k: q2[k]["substitution_share_of_G"]) if reduces else None
    res["Q2"] = {"lookbacks": q2, "bars": {"Q2_R_reduces_to": reduces, "Q2_R_nearest": nearest,
                                           "Q2_A_macd_adds_beyond": adds}}

    # ---- Q3
    O, C = pn["O"], pn["C"]
    first_exec = DAY_FIRST_DECIDE + 1
    with np.errstate(invalid="ignore", divide="ignore"):
        Md = np.log(C[:, LAST_SEG] / O[:, first_exec])
        r = np.log(C[:, first_exec:LAST_SEG + 1] / O[:, first_exec:LAST_SEG + 1])
    v = np.sqrt(np.nansum(r ** 2, axis=1))
    e = np.abs(np.nansum(r, axis=1)) / np.nansum(np.abs(r), axis=1)
    traded = session_count(t, n) > 0
    yr = pd.Series(pn["days"]).str[:4].to_numpy()
    absM = np.abs(Md)
    tq = np.full(n, -1)
    tq[traded] = pd.qcut(pd.Series(absM[traded]).rank(method="first"), 5, labels=False).to_numpy()
    tqy = np.full(n, -1)
    for y in np.unique(yr):
        mm = traded & (yr == y)
        tqy[mm] = pd.qcut(pd.Series(absM[mm]).rank(method="first"), 5, labels=False).to_numpy()
    exp_g = d.mean() * m                                        # N1 whole-window expectation per trade
    ti = t["i"].to_numpy()

    def qprofile(qs):
        out = []
        for k in range(5):
            sel = qs[ti] == k
            gg = g[sel]
            out.append({"quintile": k + 1, "sessions": int((qs == k).sum()), "trades": int(sel.sum()),
                        "hit_rate": float((gg > 0).mean()), "gross_per_trade": float(gg.mean()),
                        "share_of_G": float(gg.sum() / G), "n1_expected_gross": float(exp_g[sel].sum()),
                        "mean_abs_move_bp": float(absM[qs == k].mean() * 1e4)})
        return out

    prof_g, prof_y = qprofile(tq), qprofile(tqy)
    top, bot = prof_g[4], prof_g[0]
    se_diff = math.sqrt(top["hit_rate"] * (1 - top["hit_rate"]) / top["trades"]
                        + bot["hit_rate"] * (1 - bot["hit_rate"]) / bot["trades"])
    q3t = top["share_of_G"] > 1.0 and (top["hit_rate"] - bot["hit_rate"]) > 2 * se_diff

    def zy(x):
        out = np.full(n, np.nan)
        for y in np.unique(yr):
            mm = traded & (yr == y)
            out[mm] = (x[mm] - x[mm].mean()) / x[mm].std(ddof=1)
        return out

    ze, zv = zy(e), zy(v)
    reg = ols_nw(gross_s[traded], np.column_stack([ze[traded], zv[traded]]), 5)
    q3v = reg["t_nw"][1] > 2 and abs(reg["t_nw"][2]) < 2
    tab = {}
    for en, eh in (("low_eff", False), ("high_eff", True)):
        for vn, vh in (("low_vol", False), ("high_vol", True)):
            cell = np.zeros(n, bool)
            for y in np.unique(yr):
                mm = traded & (yr == y)
                me, mv = np.median(e[mm]), np.median(v[mm])
                cell |= mm & ((e > me) == eh) & ((v > mv) == vh)
            tab[f"{en}|{vn}"] = {"sessions": int(cell.sum()), "mean_session_gross": float(gross_s[cell].mean()),
                                 "hit_rate_sessions": float((gross_s[cell] > 0).mean())}
    # monthly
    lvl = pd.Series(pn["level_all"], index=pd.to_datetime(pn["days_all"]))
    lr = np.log(lvl).diff()
    mon_last = np.log(lvl).groupby(lvl.index.to_period("M")).last()
    mret = mon_last.diff()
    msd = lr.groupby(lr.index.to_period("M")).std()
    arm_m = pd.Series(gross_s, index=pd.to_datetime(pn["days"])).groupby(pd.to_datetime(pn["days"]).to_period("M")).sum()
    mdf = pd.DataFrame({"arm": arm_m, "absret": mret.abs(), "sd": msd}).dropna()
    mreg = ols_nw(mdf["arm"].to_numpy(), mdf[["absret", "sd"]].to_numpy(), 3)
    res["Q3"] = {"quintiles_global": prof_g, "quintiles_within_year": prof_y,
                 "top_minus_bottom_hit": top["hit_rate"] - bot["hit_rate"], "se_of_difference": se_diff,
                 "session_regression_gross_on_z_eff_z_vol": reg, "two_by_two": tab,
                 "monthly_regression_gross_on_absret_sd": mreg, "months": int(len(mdf)),
                 "bars": {"Q3_T": bool(q3t), "Q3_V": bool(q3v)}}
    P(f"Q3: top quintile share {top['share_of_G']:.2f}, hit {top['hit_rate']:.3f} vs bottom {bot['hit_rate']:.3f} "
      f"(SE {se_diff:.3f}); eff t {reg['t_nw'][1]:+.2f}, vol t {reg['t_nw'][2]:+.2f}; monthly |ret| t "
      f"{mreg['t_nw'][1]:+.2f}, sd t {mreg['t_nw'][2]:+.2f}")

    # ---- Q4
    tyr = t["day"].str[:4]
    per = {}
    for y, grp in t.groupby(tyr):
        per[y] = {"trades": int(len(grp)), "gross_per_trade_usd": float(grp["g"].mean()),
                  "gross_per_trade_bp": float(grp["bp"].mean()), "fee_bp": float(grp["fee_bp"].mean()),
                  "gross_usd": float(grp["g"].sum()), "gross_bp_sum": float(grp["bp"].sum()),
                  "mean_abs_move_bp": float(absM[traded & (yr == y)].mean() * 1e4),
                  "mean_entry_price": float(grp["entry_px"].mean())}
    tot_usd, tot_bp = float(t["g"].sum()), float(t["bp"].sum())
    sh_usd = (per["2020"]["gross_usd"] + per["2022"]["gross_usd"]) / tot_usd
    sh_bp = (per["2020"]["gross_bp_sum"] + per["2022"]["gross_bp_sum"]) / tot_bp
    res["Q4"] = {"per_year": per, "share_2020_2022_usd": sh_usd, "share_2020_2022_bp": sh_bp,
                 "bars": {"Q4_P": bool(sh_bp < (2 / 3) * sh_usd)}}
    P(f"Q4: 2020+2022 share of gross: ${sh_usd:.2f} in dollars, {sh_bp:.2f} in bp")

    # ---- Q5a
    cells = json.loads(D495_JSON.read_text(encoding="utf-8"))["cells"]
    all_sr = np.array([c["net_sharpe"] for c in cells], float)
    all_sr = all_sr[np.isfinite(all_sr)] / math.sqrt(252)
    ag_sr = np.array([c["net_sharpe"] for c in cells if c["arm"] == "AGREE"], float)
    ag_sr = ag_sr[np.isfinite(ag_sr)] / math.sqrt(252)
    sr = sharpe(net_s) / math.sqrt(252)
    g3, g4 = skew(net_s), kurt(net_s)
    V = float(all_sr.var(ddof=1))
    Va = float(ag_sr.var(ddof=1))
    q5a = {"sr_annual": sharpe(net_s), "sr_per_session": sr, "T": n, "skew": g3, "kurtosis": g4,
           "psr_vs_zero": psr(sr, 0.0, n, g3, g4),
           "primary": dsr(sr, n, g3, g4, V, len(all_sr)),
           "lenient_agree_only": dsr(sr, n, g3, g4, Va, len(ag_sr)),
           "strict_N250": dsr(sr, n, g3, g4, V, N_ALT)}
    q5a["bars"] = {"Q5_D": bool(q5a["primary"]["dsr"] >= 0.95)}
    P(f"Q5a: PSR vs 0 {q5a['psr_vs_zero']:.3f}; DSR primary (N {len(all_sr)}) {q5a['primary']['dsr']:.3f} "
      f"[SR0 annual {q5a['primary']['sr0_annual']:.3f}]; N {len(ag_sr)} {q5a['lenient_agree_only']['dsr']:.3f}; "
      f"N {N_ALT} {q5a['strict_N250']['dsr']:.3f}")

    # ---- Q5b
    lh, ll = s["log_high"], s["log_low"]
    ihd, mdd = impulse_macd(lh, ll, lc)
    E = ema_cache(lc)
    if not (np.array_equal(macd_hist_p(E, lc, MACD_FAST, MACD_SLOW, MACD_SIG), macd_hist(lc), equal_nan=True)
            and all(np.array_equal(a, b, equal_nan=True) for a, b in zip(impulse_p(lh, ll, lc, IMP_LEN), (ihd, mdd)))):
        raise GateError("[GRID] the parameterised indicators do not reproduce D484's at the defaults")
    imps = {k: impulse_p(lh, ll, lc, k) for k in GRID["imp"]}
    cells_out = []
    for f_ in GRID["fast"]:
        for sl in GRID["slow"]:
            for sg_ in GRID["sig"]:
                mh = macd_hist_p(E, lc, f_, sl, sg_)
                for im in GRID["imp"]:
                    ag = agree_from(imps[im][0], imps[im][1], mh, pn)
                    for M in GRID["M"]:
                        ntk, trips = simulate(pn["O"], pn["C"], ag, pn["first"], M, pn["cost_ticks"], pn["tick_pts"])
                        ns = ntk * pn["tick_usd"]
                        cells_out.append({"fast": f_, "slow": sl, "sig": sg_, "imp": im, "M": M,
                                          "net_sharpe": sharpe(ns), "net_total": float(ns.sum()),
                                          "trips": float(np.sum(trips))})
                        if (f_, sl, sg_, im, M) == tuple(DEFAULT.values()) and not np.allclose(ns, net_s, atol=1e-6, rtol=0):
                            raise GateError("[GRID] the default cell does not reproduce the arm")
    cdf = pd.DataFrame(cells_out)
    is_def = np.all([cdf[k] == v for k, v in DEFAULT.items()], axis=0)
    nb = cdf[~is_def]["net_sharpe"].to_numpy()
    arm_sr = float(cdf[is_def]["net_sharpe"].iloc[0])
    oat = {}
    for ax in GRID:
        others = [k for k in GRID if k != ax]
        sel = np.all([cdf[k] == DEFAULT[k] for k in others], axis=0)
        oat[ax] = {str(int(r[ax])): float(r["net_sharpe"]) for _, r in cdf[sel].sort_values(ax).iterrows()}
    res["Q5"] = {"deflated_sharpe": q5a,
                 "neighbourhood": {"cells": int(len(cdf)), "arm_net_sharpe": arm_sr, "median_neighbour": float(np.median(nb)),
                                   "share_net_positive": float((nb > 0).mean()),
                                   "arm_rank_from_top": int((cdf["net_sharpe"] > arm_sr).sum() + 1),
                                   "p10_p90_neighbours": [float(np.quantile(nb, 0.1)), float(np.quantile(nb, 0.9))],
                                   "one_at_a_time": oat,
                                   "bars": {"Q5_N": "plateau" if np.median(nb) >= 0.5 * arm_sr else "spike"}}}
    cdf.to_csv(REPO / "data" / "stage0_d669_neighbourhood.csv", index=False, encoding="utf-8")
    P(f"Q5b: arm {arm_sr:.3f}, rank {res['Q5']['neighbourhood']['arm_rank_from_top']} of {len(cdf)}; median neighbour "
      f"{np.median(nb):.3f}; share positive {(nb > 0).mean():.3f}; one-at-a-time {oat}")

    # ---- POST HOC, disclosed and not pre-registered: added after the first run, which it does not change
    # (a) the deflated Sharpe with the trial variance of pure sampling noise (every trial's true Sharpe zero),
    #     the most lenient reading: the primary V also carries the roots' cost differences
    Vn = 1.0 / n
    # (b) M >= 6 cannot exit a 10:00 entry on its signal before the forced flat (t - 15 >= 6 needs t = 21, outside
    #     the loop), so M = 5 differs from hold-to-close by one exit chance, at the 15:00 open
    at15 = (t["kind"] == "SIGNAL") & (t["exit_seg"] == LAST_SEG)
    ii = t.loc[at15, "i"].to_numpy()
    skipped = t.loc[at15, "d"].to_numpy() * (pn["C"][ii, LAST_SEG] - pn["O"][ii, LAST_SEG]) * pn["point_usd"]
    m6 = cdf[np.all([cdf[k] == DEFAULT[k] for k in ("fast", "slow", "sig", "imp")], axis=0) & (cdf["M"] == 6)]
    res["post_hoc_disclosed"] = {
        "note": "not pre-registered; computed after the first run, whose numbers are unchanged",
        "dsr_noise_only_variance": {f"N{k}": dsr(sr, n, g3, g4, Vn, k) for k in (37, len(all_sr), N_ALT)},
        "exit_at_1500": {"signal_exits_at_the_1500_open": int(at15.sum()),
                         "their_share_of_trades": float(at15.mean()),
                         "last_hour_pnl_they_skipped": float(skipped.sum()),
                         "last_hour_skipped_mean": float(skipped.mean()) if len(skipped) else float("nan"),
                         "last_hour_skipped_t": tstat(skipped) if len(skipped) > 1 else float("nan"),
                         "net_total_M5": float(net_s.sum()), "net_total_M6": float(m6["net_total"].iloc[0]),
                         "net_sharpe_M6": float(m6["net_sharpe"].iloc[0])},
        "week_decomposition": {"G": G, "across_week_component_D_week": q1n["week"]["drift_carry_exact"],
                               "within_week_timing": G - q1n["week"]["drift_carry_exact"]}}
    ph = res["post_hoc_disclosed"]
    P(f"POST HOC: noise-only DSR {[round(v['dsr'], 3) for v in ph['dsr_noise_only_variance'].values()]} "
      f"(SR0 annual {[round(v['sr0_annual'], 3) for v in ph['dsr_noise_only_variance'].values()]}); 15:00 exits "
      f"{int(at15.sum())}, last hour skipped ${skipped.sum():,.0f} (t {ph['exit_at_1500']['last_hour_skipped_t']:+.2f}); "
      f"M6 net ${ph['exit_at_1500']['net_total_M6']:,.0f}")

    # ---- predictions
    L = res["Q1"]["long"]["share_of_trades"]
    res["predictions"] = {
        "1_long_share_52_to_65pct": bool(0.52 <= L <= 0.65),
        "2_drift_share_below_0.30_and_Q1T": bool(drift_share < 0.30 and passes["whole"]),
        "3_does_not_beat_within_week": bool(not passes["week"]),
        "4_Q3T_and_hit_rising": bool(q3t and all(prof_g[k + 1]["hit_rate"] >= prof_g[k]["hit_rate"] for k in range(4))),
        "5_R1d_agreement_at_least_0.75": bool(q2["R1d"]["agreement"] >= 0.75),
        "6_Q5D_fails_and_plateau": bool(not q5a["bars"]["Q5_D"] and res["Q5"]["neighbourhood"]["bars"]["Q5_N"] == "plateau"),
    }
    res["component_line"] = {"arm": {"net_sharpe": pa["net_sharpe"], "gross_sharpe": pa["gross_sharpe"],
                                     "hit_rate_traded_sessions": pa["hit_rate_traded_sessions"], "skew_daily_net": skew(net_s),
                                     "corr_with_ledger": 1.0, "note": "the ledger's only component; no new construction built"},
                             "free_running_lookbacks": {k: q2[k]["free_running"] for k in q2}}
    res["max_drawdown_convention"] = {
        "sign": "positive",
        "note": "max_dd is a POSITIVE drawdown in US DOLLARS on the cumulative-sum daily P&L curve at one MNQ "
                "(peak minus trough), not a fraction of peak.",
        "record": "D542"}
    res["wall_min"] = round((time.time() - t0) / 60, 2)
    P(f"predictions: {res['predictions']}")
    if write:
        OUT.write_text(json.dumps(res, indent=1, default=_json), encoding="utf-8")
        P(f"wrote {OUT.relative_to(REPO)} in {res['wall_min']} min")
    return res


def _json(o):
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    return float(o)


# ------------------------------------------------------------------ self-test
def _raises(fn, tag: str, fails: list):
    try:
        fn()
    except GateError:
        return
    fails.append(f"{tag}: a deliberately broken input did not raise")


def selftest() -> int:
    fails: list[str] = []
    pn = load_panel()
    n = len(pn["days"])
    t = trade_table(pn)
    net_s = session_sum(t, "net", n)
    if n != REPRO_SESSIONS or abs(net_s.sum() - REPRO_NET) >= 1.0 or max(pn["days"]) > HI:
        fails.append(f"reproduction: {n} sessions, ${net_s.sum():,.2f}")
    try:
        lag_audit(pn, t)
    except GateError as ex:
        fails.append(str(ex))
    # the lag audit fires on a signal shifted one bar late
    shifted = np.roll(pn["AGREE"], 1, axis=1)
    _raises(lambda: lag_audit(pn, t, sig=shifted), "lag audit", fails)
    # the sign audit, and it fires on an inverted gross
    sign_audit(pn["point_usd"])
    _raises(lambda: sign_audit(pn["point_usd"], lambda dd, a, b: dd * (a - b)), "sign audit", fails)
    d, m, g = t["d"].to_numpy(float), t["m"].to_numpy(float), t["g"].to_numpy(float)
    if not np.allclose(g, d * m):
        fails.append("gross is not d x m")
    rng = np.random.default_rng(1)
    labs = strata_labels(t["day"].to_numpy())
    for name in STRATA:
        grp = labs[name]
        dr = permute_null(d, m, grp, 400, rng, check=True)
        D = drift_carry(d, m, grp)
        if abs(dr.mean() - D) > 3 * dr.std(ddof=1) / math.sqrt(len(dr)):
            fails.append(f"{name}: draw mean {dr.mean():.1f} vs analytic {D:.1f}")
        if np.all(dr == float(g.sum())):
            fails.append(f"{name}: the permutation never changes G")
        oracle = np.sign(m)
        do = permute_null(oracle, m, grp, 400, rng)
        if not float(np.dot(oracle, m)) > np.quantile(do, 0.95):
            fails.append(f"{name}: the oracle book does not beat the null")
        rnd = np.where(rng.random(len(d)) < (d > 0).mean(), 1.0, -1.0)
        dn = permute_null(rnd, m, grp, 400, rng)
        pct = (dn < float(np.dot(rnd, m))).mean()
        if not 0.02 < pct < 0.98:
            fails.append(f"{name}: a random-direction book sits at the {pct:.3f} quantile")
    # a broken permutation (labels leave their stratum) must raise
    def broken_perm():
        grp = labs["month"]
        order = np.argsort(grp, kind="stable")
        perm = rng.permutation(len(d))                          # ignores the strata
        if not np.array_equal(grp[order], grp[perm]):
            raise GateError("[PERM] a label left its stratum")
    _raises(broken_perm, "permutation stratum check", fails)
    # causality of the lookbacks: perturb the bar after f
    lc = pn["series"]["log_close"].copy()
    fi = pn["full_rows"][t["i"].to_numpy()] * NSEG + t["entry_t"].to_numpy()
    for name, L in LOOKBACKS.items():
        a = lookback_flat(lc, L)[fi]
        b = lookback_at(lc, L, fi)
        if not np.array_equal(a, b, equal_nan=True):
            fails.append(f"{name}: the two lookback implementations disagree")
        for j in np.random.default_rng(7).choice(len(fi), 40, replace=False):   # every bar after f, one trade at a time
            lc2 = lc.copy()
            lc2[fi[j] + 1:] += 5.0
            if not np.array_equal(lookback_flat(lc2, L)[fi[j]], a[j], equal_nan=True):
                fails.append(f"{name}: the lookback reads a bar after its decision")
                break

    def leaky():
        lc3 = lc.copy()
        lc3[fi + 1] += 5.0
        peek = np.sign(lc3[fi + 1] - lc3[fi - 1])
        if not np.array_equal(peek, np.sign(lc[fi + 1] - lc[fi - 1]), equal_nan=True):
            raise GateError("[CAUSAL] a lookback read a future bar")
    _raises(leaky, "causality check", fails)
    # the neighbourhood's default cell equals the arm
    s = pn["series"]
    E = ema_cache(s["log_close"])
    ih, md = impulse_p(s["log_high"], s["log_low"], s["log_close"], IMP_LEN)
    ag = agree_from(ih, md, macd_hist_p(E, s["log_close"], MACD_FAST, MACD_SLOW, MACD_SIG), pn)
    if not np.array_equal(np.nan_to_num(ag), np.nan_to_num(pn["AGREE"])):
        fails.append("the parameterised AGREE differs from the arm's")
    ntk, _ = simulate(pn["O"], pn["C"], ag, pn["first"], M_HOLD, pn["cost_ticks"], pn["tick_pts"])
    if not np.allclose(ntk * pn["tick_usd"], net_s, atol=1e-6, rtol=0):
        fails.append("the default neighbourhood cell differs from the arm")
    # the deflated Sharpe: N = 1 is the PSR against zero, and it falls as N rises
    sr, g3, g4 = 0.05, -0.1, 5.0
    if abs(dsr(sr, 1876, g3, g4, 0.001, 1)["dsr"] - psr(sr, 0.0, 1876, g3, g4)) > 1e-15:
        fails.append("DSR(N=1) != PSR(0)")
    seq = [dsr(sr, 1876, g3, g4, 0.001, k)["dsr"] for k in (2, 5, 10, 50, 111, 250, 1000)]
    if not all(a > b for a, b in zip(seq, seq[1:])):
        fails.append(f"DSR does not fall with N: {seq}")
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

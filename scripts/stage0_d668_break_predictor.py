"""D668 Stage 0: the plain break of yesterday's range sets the direction; a walk-forward expected-profit predictor
decides whether to take it and how big. Evidence roots YM and RTY; ES and NQ run identically as DEVELOPMENT.

    uv run python scripts/stage0_d668_break_predictor.py --selftest
    uv run python scripts/stage0_d668_break_predictor.py --dry-run  [--data-root DIR]   # synthetic prices, no outcome
    uv run python scripts/stage0_d668_break_predictor.py --run      [--data-root DIR]   # once

Spec: docs/decisions/D668-STAGE-0-DESIGN-the-plain-break-with-an-expected-profit-predictor.md (1e8d72e1) and its
amendment D668-A1. In-sample 2016-01-04 -> 2025-02-28 only; the vault is never read. Dealer gamma (GEX):
SqueezeMetrics, prior row only, never written per date (the licence guard). Output: data/stage0_d668_break_predictor.json.

Pipeline:
  1. bars: ES/NQ through the opening loader (sealed), YM/RTY from D462's RTH fixtures (sealed here); one session table.
  2. per root, in its own process: D666's plain break (its own functions, the root's own tick), E4 and E2, and N1's
     pool: every session, POOL random entries at the break's own clock and side mix, the same E4.
  3. features f1-f9 (s.3), each known at the entry bar; TICK from Sierra's market statistics (Gate F), A7 from
     data/opening/a7*.csv.
  4. per root, in its own process: the walk-forward OLS, pi-hat, the filter, sizing, beta_disc, and N2 (permuted
     feature rows within each year, 200 draws).
  5. gates, the four groups, the component line (K8 rebuilt), the slippage ladder, verdicts, predictions.
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d662_gamma_product as S  # noqa: E402
import stage0_d663_per_root_gamma_break as T  # noqa: E402
import stage0_d666_rebreak as X  # noqa: E402
from backtest_framework.validation.frozen import assert_none_at_or_after, filter_before  # noqa: E402

OUT = REPO / "data" / "stage0_d668_break_predictor.json"
COSTS = REPO / "data" / "futures_costs.json"
A7_FILES = {("ES", "NQ"): REPO / "data" / "opening" / "a7.csv", ("YM", "RTY"): REPO / "data" / "opening" / "a7_ym_rty.csv"}
RESERVED_FROM, FIRST, WARM = "2025-03-01", "2016-01-04", "2015-09-01"
DEV, EVID = ("ES", "NQ"), ("YM", "RTY")
ROOTS = DEV + EVID
TICK_PTS = {"ES": 0.25, "NQ": 0.25, "YM": 1.0, "RTY": 0.1}
MULT = {"ES": 50.0, "NQ": 20.0, "YM": 5.0, "RTY": 50.0}
TICK_SYMS = {"ES": ("TICK-SP",), "NQ": ("TICK-NQ",), "YM": ("TICK-NYSE",), "RTY": ("TICK-NYSE", "TICK-NASDAQ")}
FEATS = ("gap_inside", "gap_through", "gap", "short_gamma", "a7", "tick", "travel", "clock", "long")
CHECKPOINTS = ("09:45", "10:00", "10:30", "11:00")
BURN_MODEL, BURN_PI, EP_K, MIN_FILTERED = 250, 40, 2.0, 30
N_N1, N_N2, POOL, N_BOOT = 1000, 200, 32, 500
SEED = 668
COVID = X.COVID
BREAK_0DTE = "2022-05-16"
GATE_F_COV = 0.90
Z80 = 1.959964 + 0.841621


class D668Error(RuntimeError):
    pass


hm = X.hm


# ================================================================================ costs
def micro_costs() -> dict[str, dict[str, float]]:
    """The micro round trip in dollars on the file's default line (d508_exec): $3 + crossing x tick_usd + one tick of
    stop slippage (D668-A1 s.1)."""
    j = json.loads(COSTS.read_text(encoding="utf-8"))
    out = {}
    for r in ROOTS:
        m = j["roots"][r]["micro"]
        line = m["default_line"]
        x = float(m["crossing_ticks_rt"][line]["value"])
        out[r] = {"symbol": m["symbol"], "line": line, "crossing_ticks": x, "tick_usd": float(m["tick_usd"]),
                  "usd_per_point": float(m["usd_per_point"]), "tick_points": float(m["tick_points"]),
                  "cost_usd": float(m["commission_rt_usd"]["value"]) + x * float(m["tick_usd"]) + float(m["tick_usd"])}
        if abs(out[r]["tick_points"] - TICK_PTS[r]) > 1e-12:
            raise D668Error(f"{r}: the cost file's tick {out[r]['tick_points']} is not the runner's {TICK_PTS[r]}")
    return out


# ================================================================================ inputs
def synth(b: pd.DataFrame, level: dict[str, float], seed: int) -> pd.DataFrame:
    """The dry run: the real calendar and bar layout, every price and volume a synthetic walk (no outcome read)."""
    rng = np.random.default_rng(seed)
    b = b.sort_values(["root", "session", "hhmm"], kind="stable").reset_index(drop=True)
    lvl = b["root"].map(level).to_numpy()
    walk = pd.Series(rng.normal(0, 4e-4, len(b))).groupby(b["root"].to_numpy()).cumsum().to_numpy()
    c = lvl * np.exp(walk)
    b["close"] = c
    starts = np.r_[True, (b["root"].to_numpy()[1:] != b["root"].to_numpy()[:-1])]
    b["open"] = np.r_[c[0], c[:-1]]
    b.loc[starts, "open"] = c[starts]
    b["high"] = np.maximum(b["open"], b["close"]) * (1 + rng.uniform(0, 2e-4, len(b)))
    b["low"] = np.minimum(b["open"], b["close"]) * (1 - rng.uniform(0, 2e-4, len(b)))
    b["volume"] = rng.integers(100, 5000, len(b))
    return b


def load_bars(data_root: Path, dry: bool) -> tuple[pd.DataFrame, list[str], dict[str, pd.Series], Any]:
    V = S.load_v2()
    R = V.R
    b, use, Gd = V.load_inputs(data_root, dry)
    parts = [b[["root", "session", "hhmm", "open", "high", "low", "close", "volume"]]]
    for r in EVID:
        x = pd.read_csv(data_root / "fixtures" / f"fut_{r}_rth_1m.csv.gz", encoding="utf-8", dtype={"day": str, "hhmm": str},
                        usecols=["day", "hhmm", "open", "high", "low", "close", "volume"]).rename(columns={"day": "session"})
        x = x[x["session"] >= WARM]
        x = filter_before(x, "session", RESERVED_FROM)
        x.insert(0, "root", r)
        if dry:
            x = synth(x, {"YM": 25000.0, "RTY": 1800.0}, 17 if r == "YM" else 19)
        parts.append(x)
    b = pd.concat(parts, ignore_index=True)
    assert_none_at_or_after(b, "session", RESERVED_FROM)
    return b, use, Gd, R


# ================================================================================ the break (process per root)
def root_trades(args: tuple) -> dict[str, Any]:
    """One root: D666's plain break with the root's own tick, E4 and E2; then N1's pool on EVERY session."""
    r, frame, bars_r, tick, seed = args
    X.TICK = tick  # D666's fill and stop functions read the module's tick (D668-A1 s.2)
    rows = []
    for s, d in frame.iterrows():
        bb = bars_r.get(s)
        if bb is None:
            continue
        Lh, Ll, A = float(d["prior_high"]), float(d["prior_low"]), float(d["atr20"])
        p = X.plain_break(bb, Lh, Ll, A)
        if p is None:
            continue
        i, D, entry = p["i"], p["D"], p["entry"]
        rec = {"session": s, "D": D, "i": i, "minute": int(bb["m"][i]), "entry": entry, "L": p["L"], "stop": p["stop"],
               "A": A, "open": float(d["open"]), "prior_close": float(d["prior_close"]),
               "open_fill": bool((D > 0 and bb["o"][i] > p["stop"]) or (D < 0 and bb["o"][i] < p["stop"]))}
        for x in ("E4", "E2"):
            px, why = X.exit_trade(bb, i, D, entry, p["L"], A, 0.0, x)
            rec[f"{x}_gross"] = D * (px / entry - 1) * 1e4
            rec[f"{x}_why"] = why
        rows.append(rec)
    # N1's pool: every session, POOL entries at a minute drawn from the break's own entry clock and a side drawn with
    # the break's own long share; entered at the close of the first bar at or after the minute + 1 tick, the initial
    # stop 0.25 A + 1 tick away, the same E4 trail and close (D668 s.5; D668-A1 s.4)
    rng = np.random.default_rng(seed)
    mins = np.array([x["minute"] for x in rows], dtype=int)
    p_long = float(np.mean([x["D"] > 0 for x in rows])) if rows else 0.5
    pool, pool_side, pool_sessions = [], [], []
    for s, d in frame.iterrows():
        bb = bars_r.get(s)
        if bb is None or not len(mins):
            continue
        A = float(d["atr20"])
        g = np.full(POOL, np.nan)
        side = np.zeros(POOL, dtype=int)
        for k in range(POOL):
            mn = int(mins[rng.integers(0, len(mins))])
            Dd = 1 if rng.random() < p_long else -1
            side[k] = Dd
            j = np.flatnonzero((bb["m"] >= mn) & (bb["m"] <= X.LAST_ENTRY))
            if not len(j):
                continue
            kk = int(j[0])
            ent = float(bb["c"][kk]) + Dd * tick
            px, _ = X.exit_trade(bb, kk, Dd, ent, ent - Dd * (X.K_ATR * A + tick), A, 0.0, "E4")
            g[k] = Dd * (px / ent - 1) * 1e4
        pool.append(g)
        pool_side.append(side)
        pool_sessions.append(s)
    return {"root": r, "rows": rows, "pool": np.array(pool), "pool_side": np.array(pool_side),
            "pool_sessions": pool_sessions, "p_long": p_long}


def n1_draws(pool: np.ndarray, side: np.ndarray, n: int, seed: int) -> dict[str, np.ndarray]:
    """1,000 null books, each n trades: sessions uniform with replacement, one pooled entry each."""
    rng = np.random.default_rng(seed)
    ok = np.isfinite(pool)
    out = {"all": np.empty(N_N1), "long": np.empty(N_N1), "short": np.empty(N_N1)}
    for kd in range(N_N1):
        si = rng.integers(0, len(pool), n)
        ci = rng.integers(0, pool.shape[1], n)
        v, sd, f = pool[si, ci], side[si, ci], ok[si, ci]
        out["all"][kd] = v[f].mean()
        out["long"][kd] = v[f & (sd > 0)].mean()
        out["short"][kd] = v[f & (sd < 0)].mean()
    return out


# ================================================================================ features
def a7_value(ar: pd.DataFrame, s: str, minute: int, D: int, after: int = 0) -> float:
    """D x A7 at the latest checkpoint at or before the entry bar's start; 0 before 09:45 or when missing.
    `after` = 1 is the canary: the next checkpoint."""
    cps = [t for t in CHECKPOINTS if hm(t) <= minute]
    if after:
        nxt = [t for t in CHECKPOINTS if hm(t) > minute]
        cps = cps + nxt[:1]
    if not cps or s not in ar.index:
        return 0.0
    v = ar.at[s, f"a7_{cps[-1]}"]
    return float(D * v) if np.isfinite(v) else 0.0


def a7_audit(tr: pd.DataFrame, used_cp: list[str | None]) -> None:
    """Second path: every A7 used was measured at a checkpoint whose window ended at or before the entry bar."""
    for (_, rec), cp in zip(tr.iterrows(), used_cp):
        if cp is not None and hm(cp) > rec["minute"]:
            raise D668Error(f"lag: A7 at {cp} for an entry at {rec['minute']}")


def a7_checkpoint(minute: int, after: int = 0) -> str | None:
    cps = [t for t in CHECKPOINTS if hm(t) <= minute]
    if after:
        cps = cps + [t for t in CHECKPOINTS if hm(t) > minute][:1]
    return cps[-1] if cps else None


def gap_feature(tr: pd.DataFrame, to_entry: bool = False) -> np.ndarray:
    ref = tr["entry"] if to_entry else tr["open"]
    return (tr["D"] * (ref / tr["prior_close"] - 1) / (tr["A"] / tr["prior_close"])).to_numpy(float)


def gap_audit(tr: pd.DataFrame, g: np.ndarray) -> None:
    """Second path: the gap is the 09:30 open against the prior close, never the entry price."""
    alt = np.array([rec["D"] * (rec["open"] - rec["prior_close"]) / rec["A"] for _, rec in tr.iterrows()])
    if not np.allclose(alt, g, rtol=1e-9, atol=1e-12):
        raise D668Error("lag: the gap feature is not the open against the prior close")


def features(tr: pd.DataFrame, r: str, frame: pd.DataFrame, a7: pd.DataFrame, tick_z: pd.Series,
             short: pd.Series, canary: str = "") -> pd.DataFrame:
    o, D, A = tr["open"].to_numpy(float), tr["D"].to_numpy(int), tr["A"].to_numpy(float)
    L = tr["L"].to_numpy(float)
    stop = tr["stop"].to_numpy(float)
    beyond_L = np.where(D > 0, o > L, o < L)
    beyond_stop = np.where(D > 0, o > stop, o < stop)
    g = gap_feature(tr, to_entry=(canary == "gap"))
    gap_audit(tr, g)
    ar = a7[a7["root"] == r].set_index("session") if a7 is not None else pd.DataFrame()
    after = 1 if canary == "a7" else 0
    a7v = [a7_value(ar, s, m, d, after) if len(ar) else 0.0 for s, m, d in zip(tr["session"], tr["minute"], tr["D"])]
    a7_audit(tr, [a7_checkpoint(m, after) for m in tr["minute"]])
    return pd.DataFrame({
        "gap_inside": (beyond_L & ~beyond_stop).astype(float),
        "gap_through": beyond_stop.astype(float),
        "gap": g,
        "short_gamma": short.reindex(tr["session"]).fillna(False).astype(float).to_numpy(),
        "a7": np.asarray(a7v, float),
        "tick": tick_z.reindex(tr["session"]).fillna(0.0).to_numpy(float),
        "travel": D * (tr["entry"].to_numpy(float) - o) / A,
        "clock": (tr["minute"].to_numpy(float) - hm("09:30")) / 390.0,
        "long": (D > 0).astype(float),
    }, index=tr.index)


# ================================================================================ the predictor
def walk(Xf: np.ndarray, y: np.ndarray, leak: bool = False) -> tuple[np.ndarray, np.ndarray]:
    """One trade per session, in session order: forecast i from rows < i (earlier sessions), OLS on standardised
    features plus an intercept, no penalty. `leak` = True is the canary (rows <= i). Returns (yhat, betas)."""
    n, k = Xf.shape
    yhat = np.full(n, np.nan)
    betas = np.full((n, k + 1), np.nan)
    for i in range(BURN_MODEL, n):
        e = i + 1 if leak else i
        Xt, yt = Xf[:e], y[:e]
        mu, sd = Xt.mean(axis=0), Xt.std(axis=0)
        sd[sd == 0] = 1.0
        Z = np.column_stack([np.ones(e), (Xt - mu) / sd])
        beta = np.linalg.lstsq(Z, yt, rcond=None)[0]
        betas[i] = beta
        yhat[i] = float(np.r_[1.0, (Xf[i] - mu) / sd] @ beta)
    return yhat, betas


def walk_audit(yhat: np.ndarray, Xf: np.ndarray, y: np.ndarray, sessions: np.ndarray, idx: list[int]) -> None:
    """Second implementation: select the training rows by SESSION DATE (strictly before), never by position."""
    for i in idx:
        tr = sessions < sessions[i]
        Xt, yt = Xf[tr], y[tr]
        mu, sd = Xt.mean(axis=0), Xt.std(axis=0)
        sd[sd == 0] = 1.0
        beta = np.linalg.lstsq(np.column_stack([np.ones(tr.sum()), (Xt - mu) / sd]), yt, rcond=None)[0]
        if not np.isclose(float(np.r_[1.0, (Xf[i] - mu) / sd] @ beta), yhat[i], rtol=1e-9, atol=1e-9):
            raise D668Error(f"lag: forecast {i} was fitted on rows that are not strictly earlier sessions")


def pass_through(y: np.ndarray, yhat: np.ndarray, leak: bool = False) -> np.ndarray:
    """pi-hat_i: the through-origin slope of realised on forecast over EARLIER forecasts; 0 until BURN_PI of them.
    `leak` = True is the canary (includes the trade's own outcome)."""
    f = np.isfinite(yhat)
    num = np.where(f, y * np.nan_to_num(yhat), 0.0)
    den = np.where(f, np.nan_to_num(yhat) ** 2, 0.0)
    cnt = f.astype(int)
    cn, cd, cc = np.cumsum(num), np.cumsum(den), np.cumsum(cnt)
    if not leak:
        cn, cd, cc = cn - num, cd - den, cc - cnt
    pi = np.where((cc >= BURN_PI) & (cd > 0), cn / np.where(cd > 0, cd, 1.0), 0.0)
    return np.where(f, pi, np.nan)


def pi_audit(pi: np.ndarray, y: np.ndarray, yhat: np.ndarray, idx: list[int]) -> None:
    f = np.isfinite(yhat)
    for i in idx:
        e = f.copy()
        e[i:] = False
        want = (float((y[e] * yhat[e]).sum() / (yhat[e] ** 2).sum()) if e.sum() >= BURN_PI else 0.0) if f[i] else np.nan
        if not (np.isnan(want) and np.isnan(pi[i])) and not np.isclose(want, pi[i], rtol=1e-9, atol=1e-12):
            raise D668Error(f"lag: pi-hat at {i} is not built from earlier forecasts only")


def predictor(Xf: np.ndarray, y: np.ndarray, cost: np.ndarray) -> dict[str, np.ndarray]:
    yhat, betas = walk(Xf, y)
    pi = pass_through(y, yhat)
    proj = pi * yhat
    live = np.isfinite(yhat) & (pi != 0) & np.isfinite(pi)  # after both burn-ins
    take = live & (proj >= EP_K * cost)
    size = np.where(take, np.clip(np.floor(proj / (EP_K * cost)), 1, 3), 0).astype(int)
    return {"yhat": yhat, "betas": betas, "pi": pi, "proj": proj, "live": live, "take": take, "size": size}


def beta_disc(y: np.ndarray, yhat: np.ndarray) -> tuple[float, float]:
    f = np.isfinite(yhat)
    if f.sum() < 10 or np.nanstd(yhat[f]) == 0:
        return float("nan"), float("nan")
    fit = S.hac(y[f], yhat[f][:, None])
    return float(fit.params[1]), float(fit.tvalues[1])


def model_job(args: tuple) -> dict[str, Any]:
    """One root: the predictor, beta_disc, and N2 (feature rows permuted across sessions within each year)."""
    r, Xf, y, cost, years, seed, names = args
    P = predictor(Xf, y, cost)
    b, t = beta_disc(y, P["yhat"])
    net = y - cost
    rng = np.random.default_rng(seed)
    n2_t, n2_net = np.full(N_N2, np.nan), np.full(N_N2, np.nan)
    by_year = {yy: np.flatnonzero(years == yy) for yy in np.unique(years)}
    for kd in range(N_N2):
        perm = np.arange(len(y))
        for ix in by_year.values():
            perm[ix] = ix[rng.permutation(len(ix))]
        Q = predictor(Xf[perm], y, cost)
        n2_t[kd] = beta_disc(y, Q["yhat"])[1]
        n2_net[kd] = float(net[Q["take"]].mean()) if Q["take"].sum() else np.nan
    fin = P["betas"][np.isfinite(P["betas"][:, 0])]
    last = fin[-1] if len(fin) else np.full(len(names) + 1, np.nan)
    stab = {nm: float((np.sign(fin[:, j + 1]) == np.sign(last[j + 1])).mean()) for j, nm in enumerate(names)} if len(fin) else {}
    return {"root": r, **P, "beta_disc": b, "beta_disc_t": t, "n2_t": n2_t, "n2_net": n2_net,
            "final_coef_std": {"intercept": float(last[0]), **{nm: float(last[j + 1]) for j, nm in enumerate(names)}},
            "sign_stability": stab}


# ================================================================================ statistics
def mean_t(x: np.ndarray, R: Any) -> tuple[float, float, float]:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 3:
        return float("nan"), float("nan"), float("nan")
    t, se = R.nw_t(x)
    return float(x.mean()), float(t), float(se)


def null_summary(draws: np.ndarray, score: float, rng: np.random.Generator) -> dict[str, float]:
    q95 = [np.quantile(rng.choice(draws, len(draws)), 0.95) for _ in range(N_BOOT)]
    return {"p50": float(np.median(draws)), "p95": float(np.quantile(draws, 0.95)), "p95_se": float(np.std(q95, ddof=1)),
            "rank": float((draws < score).mean())}


def daily_usd(tr: pd.DataFrame, net_bp: np.ndarray, size: np.ndarray, sessions: pd.Index, usd_pt: float) -> pd.Series:
    usd = net_bp / 1e4 * tr["entry"].to_numpy(float) * usd_pt * size
    return pd.Series(usd, index=tr["session"].to_numpy()).reindex(sessions, fill_value=0.0)


def component(tr: pd.DataFrame, net_bp: np.ndarray, gross_bp: np.ndarray, size: np.ndarray, sessions: pd.Index,
              usd_pt: float, k8: pd.Series, others: dict[str, pd.Series]) -> dict[str, Any]:
    dn = daily_usd(tr, net_bp, size, sessions, usd_pt)
    dg = daily_usd(tr, gross_bp, size, sessions, usd_pt)
    traded = size > 0
    tu = (net_bp / 1e4 * tr["entry"].to_numpy(float) * usd_pt * size)[traded]
    common = dn.index.intersection(k8.index)
    out = {"daily_net_sharpe": float(dn.mean() / dn.std(ddof=1) * math.sqrt(252)) if dn.std(ddof=1) > 0 else float("nan"),
           "daily_gross_sharpe": float(dg.mean() / dg.std(ddof=1) * math.sqrt(252)) if dg.std(ddof=1) > 0 else float("nan"),
           "hit_rate": float((tu > 0).mean()) if len(tu) else float("nan"),
           "skew_trade_usd": float(stats.skew(tu)) if len(tu) > 2 else float("nan"),
           "net_usd_per_year": float(dn.sum() / (len(sessions) / 252)),
           "rho_K8": float(np.corrcoef(dn.loc[common], k8.loc[common])[0, 1]) if len(common) > 30 else float("nan"),
           "rho_other_roots_unfiltered": {k: float(np.corrcoef(dn.reindex(v.index.union(dn.index), fill_value=0.0),
                                                               v.reindex(v.index.union(dn.index), fill_value=0.0))[0, 1])
                                          for k, v in others.items()},
           "not_rebuilt": ["#2 the MACD day-session arm (ADMITTED): its daily P&L is not rebuilt here",
                           "#3 the NG winter spread: a monthly NG calendar spread, a different instrument and clock"]}
    return out


def k8_daily(tab_nq: pd.DataFrame, sessions: pd.Index, cost_usd: float = 3.0) -> pd.Series:
    """The ledger's K8, rebuilt: long NQ 09:30 open + a tick -> 15:59 close, one MNQ, $3, on sessions after a day
    session that closed below its open (COMPONENTS_PROP entry #1)."""
    d = tab_nq.sort_index()
    fire = (d["close"].shift(1) < d["open"].shift(1))
    usd = ((d["close"] - (d["open"] + 0.25)) * 2.0 - cost_usd).where(fire, 0.0)
    return usd.reindex(sessions).fillna(0.0)


def ladder(tr: pd.DataFrame, gross: np.ndarray, cost: np.ndarray, tick: float, mask: np.ndarray) -> dict[str, float]:
    tk = tick / tr["entry"].to_numpy(float) * 1e4
    of = tr["open_fill"].to_numpy(bool)
    out = {}
    for k in (0, 1, 2):
        out[f"every_fill_+{k}"] = float((gross - cost - 2 * k * tk)[mask].mean()) if mask.any() else float("nan")
        out[f"open_fills_+{k}"] = float((gross - cost - k * tk * of)[mask].mean()) if mask.any() else float("nan")
    return out


# ================================================================================ build
def build(data_root: Path, dry: bool) -> dict[str, Any]:
    t_start = time.time()
    costs = micro_costs()
    b, use, Gd, R = load_bars(data_root, dry)
    T.MULT.update(MULT)
    tabs = R.session_table(b, use, roots=ROOTS)
    bars = R.bar_arrays(b)
    rng = np.random.default_rng(SEED)
    if dry:
        gex = pd.Series(rng.normal(3e9, 4e9, 3000), index=pd.bdate_range("2014-01-01", periods=3000).strftime("%Y-%m-%d"))
    else:
        dix = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
        gex = dix[dix["date"] < RESERVED_FROM].set_index("date")["gex"].astype(float).sort_index()
    frames, short = {}, {}
    for r in ROOTS:
        d = T.root_frame(b, tabs[r], r)
        d = d[np.isfinite(d[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
        d["gd_spx"] = T.gex_prior(gex, d.index)
        T.gex_lag_audit(gex, d.index[:: max(1, len(d) // 40)])
        short[r] = ((Gd["NQ"].reindex(d.index) < 0) if r == "NQ" else (d["gd_spx"] < 0)).fillna(False)
        frames[r] = d
        if (d.index >= RESERVED_FROM).any():
            raise D668Error(f"seal: {r} holds a session on or after {RESERVED_FROM}")
    t0 = time.time()
    jobs = [(r, frames[r], {s: bars[(r, s)] for s in frames[r].index if (r, s) in bars}, TICK_PTS[r], SEED + i)
            for i, r in enumerate(ROOTS)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        got = {o["root"]: o for o in pool.map(root_trades, jobs)}
    fan1 = time.time() - t0
    # N1 draws on every session: the pool must cover every session with bars (the canary restricts it)
    for r in ROOTS:
        n_bars = sum(1 for s in frames[r].index if (r, s) in bars)
        if len(got[r]["pool_sessions"]) != n_bars:
            raise D668Error(f"N1: {r}'s pool covers {len(got[r]['pool_sessions'])} sessions, not all {n_bars}")
    # reproduction: ES and NQ plain-break E4 / E2 gross means equal D666's control as D667 recorded it
    ref = json.loads((REPO / "data" / "diag_d666.json").read_text(encoding="utf-8"))["D"]["plain_break_own_stats"]
    repro = {}
    for r in DEV:
        tr = pd.DataFrame(got[r]["rows"])
        for x in ("E4", "E2"):
            here, want = float(tr[f"{x}_gross"].mean()), ref[f"{r}_{x}"]["mean"]
            repro[f"{r}_{x}"] = {"here": here, "D667": want}
            if not dry and abs(here - want) > 1e-9:
                raise D668Error(f"the plain break does not reproduce D666/D667 on {r} {x}: {here} vs {want}")
    # features: TICK (Gate F), A7
    ex, gates = {}, {}
    if not dry:
        syms = sorted({s for r in ROOTS for s in TICK_SYMS[r]})
        with ProcessPoolExecutor(max_workers=4) as pool:
            ex = dict(pool.map(T.extract_job, [(s, str(T.SC_DATA / f"{s}.scid")) for s in syms]))
        for s, e_ in ex.items():
            T.assert_sealed(e_)
            g = T.gate_f(e_, "tick")
            gates[s] = {"sessions": g["sessions"], "coverage_median": g["coverage_median"],
                        "sessions_below_90pct": g["sessions_below_90pct"], "pass": bool(g["coverage_median"] >= GATE_F_COV),
                        "_g": g}
    a7 = {}
    for roots_, pth in A7_FILES.items():
        if dry:
            continue
        if not pth.exists():
            raise D668Error(f"A7 missing: {pth}")
        z = pd.read_csv(pth, encoding="utf-8", dtype={"session": str})
        if (z["session"] >= RESERVED_FROM).any():
            raise D668Error(f"seal: {pth.name} holds a vault session")
        for r in roots_:
            a7[r] = z[z["root"] == r]
    trades, Xs, tick_info = {}, {}, {}
    for r in ROOTS:
        tr = pd.DataFrame(got[r]["rows"]).sort_values("session").reset_index(drop=True)
        if not tr["session"].is_monotonic_increasing or tr["session"].duplicated().any():
            raise D668Error(f"{r}: trades are not one a session in order")
        tr["cost_bp"] = costs[r]["cost_usd"] / costs[r]["usd_per_point"] / tr["entry"] * 1e4
        if np.allclose(tr["E4_gross"], tr["E2_gross"]):
            raise D668Error(f"right quantity: {r}'s E4 equals E2 on every trade")
        rows = pd.DataFrame({"D": tr["D"].to_numpy(), "eb": tr["minute"].to_numpy()}, index=tr["session"].to_numpy())
        zs, used = [], []
        for s_ in TICK_SYMS[r]:
            if s_ in ex and gates[s_]["pass"]:
                gt = {"tick": gates[s_]["_g"], "up": {"usable": False}, "dn": {"usable": False}}
                zs.append(T.shocks(rows, "09:30", ex[s_], None, None, gt)["s_tick"].astype(float))
                used.append(s_)
        tz = pd.concat(zs, axis=1).mean(axis=1, skipna=True) if zs else pd.Series(np.nan, index=rows.index)
        tick_info[r] = {"series": used, "dropped": not used, "share_missing_set_to_0": float(tz.isna().mean())}
        F = features(tr, r, frames[r], a7.get(r), tz, short[r])
        names = [c for c in FEATS if not (c == "tick" and not used)]
        trades[r], Xs[r] = tr, (F[names].to_numpy(float), names)
    # the predictor, per root
    t1 = time.time()
    mjobs = [(r, Xs[r][0], trades[r]["E4_gross"].to_numpy(float), trades[r]["cost_bp"].to_numpy(float),
              trades[r]["session"].str[:4].to_numpy(), SEED + 10 + i, Xs[r][1]) for i, r in enumerate(ROOTS)]
    with ProcessPoolExecutor(max_workers=4) as pool:
        M = {o["root"]: o for o in pool.map(model_job, mjobs)}
    fan2 = time.time() - t1
    for r in ROOTS:  # the lag audits on the real forecasts
        sess = trades[r]["session"].to_numpy()
        idx = list(range(BURN_MODEL, len(sess), max(1, (len(sess) - BURN_MODEL) // 12)))
        walk_audit(M[r]["yhat"], Xs[r][0], trades[r]["E4_gross"].to_numpy(float), sess, idx)
        pi_audit(M[r]["pi"], trades[r]["E4_gross"].to_numpy(float), M[r]["yhat"], idx)
    # the ES/NQ development variant with p_FADE (reported only)
    dev_pfade = {} if dry else pfade_variant(tabs, trades, Xs, frames, R)
    # ---------------------------------------------------------------- results
    k8 = k8_daily(tabs["NQ"], frames["NQ"].index)
    out: dict[str, Any] = {"spec": "D668 (1e8d72e1) + D668-A1", "dry_run": dry, "credit": "dealer gamma (GEX): SqueezeMetrics",
                           "window": [FIRST, "2025-02-28"], "costs": costs, "reproduction_D667": repro,
                           "tick_gate_f": {s: {k: v for k, v in g.items() if k != "_g"} for s, g in gates.items()},
                           "roots": {}}
    unf_daily = {}
    for r in ROOTS:
        tr = trades[r]
        unf_daily[r] = daily_usd(tr, (tr["E4_gross"] - tr["cost_bp"]).to_numpy(float), np.ones(len(tr)),
                                 frames[r].index, costs[r]["usd_per_point"])
    p1, p_unf = {}, {}
    for r in ROOTS:
        tr, m_ = trades[r], M[r]
        g4 = tr["E4_gross"].to_numpy(float)
        cost = tr["cost_bp"].to_numpy(float)
        net = g4 - cost
        years = len(frames[r]) / 252
        per_year = len(tr) / years
        gm, gt, gse = mean_t(g4, R)
        nm_, nt_, _ = mean_t(net, R)
        exc = ~tr["session"].between(*COVID).to_numpy()
        n1 = n1_draws(got[r]["pool"], got[r]["pool_side"], len(tr), SEED + 100 + ROOTS.index(r))
        rng_b = np.random.default_rng(SEED + 200 + ROOTS.index(r))
        long_, short_ = tr["D"].to_numpy() > 0, tr["D"].to_numpy() < 0
        take, live, size = m_["take"], m_["live"], m_["size"]
        fm, ft, _ = mean_t(net[take], R) if take.sum() > 2 else (float("nan"),) * 3
        tk_bp = TICK_PTS[r] / tr["entry"].to_numpy(float) * 1e4
        g1 = {"gross_mean": gm, "t_hac": gt, "p_one_sided": float(stats.norm.sf(gt)), "mde80": Z80 * gse,
              "n1": null_summary(n1["all"], gm, rng_b),
              "n1_by_side": {"long_break_gross": float(g4[long_].mean()), "long_null_p50": float(np.median(n1["long"])),
                             "short_break_gross": float(g4[short_].mean()), "short_null_p50": float(np.median(n1["short"]))},
              "ex_covid_gross": float(g4[exc].mean()), "p_long": got[r]["p_long"]}
        g2 = {"forecast_trades": int(np.isfinite(m_["yhat"]).sum()), "live_trades": int(live.sum()),
              "filtered_trades": int(take.sum()), "pass_rate": float(take[live].mean()) if live.any() else float("nan"),
              "filtered_net_mean": fm, "filtered_t": ft, "filtered_gross_mean": float(g4[take].mean()) if take.any() else float("nan"),
              "filtered_ex_covid": float(net[take & exc].mean()) if (take & exc).any() else float("nan"),
              "filtered_net_plus1tick_every_fill": float((net - 2 * tk_bp)[take].mean()) if take.any() else float("nan"),
              "unfiltered_net_live": float(net[live].mean()) if live.any() else float("nan"),
              "removed_net_mean": float(net[live & ~take].mean()) if (live & ~take).any() else float("nan"),
              "pi_hat_final": float(m_["pi"][np.isfinite(m_["pi"])][-1]) if np.isfinite(m_["pi"]).any() else float("nan"),
              "pi_hat_path": {q: float(np.nanquantile(m_["pi"][live], q)) for q in (0.1, 0.5, 0.9)} if live.any() else {},
              "beta_disc": m_["beta_disc"], "beta_disc_t": m_["beta_disc_t"],
              "n2_beta_disc_t": {"p50": float(np.nanmedian(m_["n2_t"])), "p95": float(np.nanquantile(m_["n2_t"], 0.95))},
              "n2_filtered_net": {"p50": float(np.nanmedian(m_["n2_net"])), "p95": float(np.nanquantile(m_["n2_net"], 0.95))}
              if np.isfinite(m_["n2_net"]).any() else {},
              "final_coef_std": m_["final_coef_std"], "sign_stability": m_["sign_stability"], "features": Xs[r][1],
              "tick": tick_info[r]}
        p1[r] = g1["p_one_sided"]
        p_unf[r] = float(stats.norm.sf(nt_)) if np.isfinite(nt_) else 1.0
        sz = size[size > 0]
        fg = {"unfiltered": X.four_groups(tr, pd.Series(g4), pd.Series(net), per_year, R, r)}
        if take.sum() > 2:
            ft_ = tr[take].reset_index(drop=True)
            fg["filtered"] = X.four_groups(ft_, pd.Series(g4[take]), pd.Series(net[take]), take.sum() / years, R, r)
            fg["sized"] = X.four_groups(ft_, pd.Series(g4[take] * sz), pd.Series(net[take] * sz), take.sum() / years, R, r)
            fg["sized"]["mean_size"] = float(sz.mean())
        others = {k: v for k, v in unf_daily.items() if k != r}
        comp = {"unfiltered": component(tr, net, g4, np.ones(len(tr)), frames[r].index, costs[r]["usd_per_point"], k8, others),
                "filtered": component(tr, net, g4, take.astype(float), frames[r].index, costs[r]["usd_per_point"], k8, others),
                "sized": component(tr, net, g4, size.astype(float), frames[r].index, costs[r]["usd_per_point"], k8, others)}
        sess = tr["session"]
        splits = {"by_year_gross": {y: float(g4[sess.str.startswith(y).to_numpy()].mean()) for y in sorted({s[:4] for s in sess})},
                  "by_year_net_filtered": {y: float(net[take & sess.str.startswith(y).to_numpy()].mean())
                                           for y in sorted({s[:4] for s in sess}) if (take & sess.str.startswith(y).to_numpy()).any()},
                  "long_gross": float(g4[long_].mean()), "short_gross": float(g4[short_].mean()),
                  "pre_0dte_gross": float(g4[(sess < BREAK_0DTE).to_numpy()].mean()),
                  "post_0dte_gross": float(g4[(sess >= BREAK_0DTE).to_numpy()].mean()),
                  "open_class_gross": {c: float(g4[msk].mean()) for c, msk in
                                       (("no_gap", (Xs[r][0][:, 0] == 0) & (Xs[r][0][:, 1] == 0)),
                                        ("gap_inside", Xs[r][0][:, 0] == 1), ("gap_through", Xs[r][0][:, 1] == 1)) if msk.any()},
                  "open_fill_share": float(tr["open_fill"].mean()),
                  "E2_gross": dict(zip(("mean", "t"), mean_t(tr["E2_gross"].to_numpy(float), R)[:2])),
                  "exit_reasons_E4": tr["E4_why"].value_counts().to_dict()}
        out["roots"][r] = {"role": "EVIDENCE" if r in EVID else "DEVELOPMENT", "sessions": int(len(frames[r])),
                           "trades": int(len(tr)), "per_year": per_year, "cost_bp_mean": float(cost.mean()),
                           "gate1": g1, "gate2": g2, "unfiltered_net": {"mean": nm_, "t": nt_},
                           "four_groups": fg, "component": comp,
                           "ladder_unfiltered": ladder(tr, g4, cost, TICK_PTS[r], np.ones(len(tr), bool)),
                           "ladder_filtered": ladder(tr, g4, cost, TICK_PTS[r], take), "splits": splits,
                           "vault_power_at_in_sample_mean": float(stats.norm.sf(1.959964 - gm / (gse * math.sqrt(len(tr) / (per_year * 390 / 252)))))
                           if gse > 0 else float("nan")}
        if r in dev_pfade:
            out["roots"][r]["dev_variant_pfade"] = dev_pfade[r]
    # ---------------------------------------------------------------- verdicts on the evidence roots
    h1 = T.holm({r: p1[r] for r in EVID})
    passed1 = []
    for r in EVID:
        a = out["roots"][r]["gate1"]
        chk = {"gross_positive_holm": bool(a["gross_mean"] > 0 and h1[r] < 0.05),
               "above_n1_p95": bool(a["gross_mean"] - a["n1"]["p95"] > 2 * a["n1"]["p95_se"]),
               "positive_ex_covid": bool(a["ex_covid_gross"] > 0)}
        a["holm_p"], a["checks"] = h1[r], chk
        if all(chk.values()):
            passed1.append(r)
    p2 = {r: float(stats.norm.sf(out["roots"][r]["gate2"]["filtered_t"])) for r in passed1
          if np.isfinite(out["roots"][r]["gate2"]["filtered_t"])}
    h2 = T.holm(p2) if p2 else {}
    hu = T.holm({r: p_unf[r] for r in passed1}) if passed1 else {}
    for r in EVID:
        g2 = out["roots"][r]["gate2"]
        disc = bool(np.isfinite(g2["beta_disc_t"]) and g2["beta_disc_t"] >= 2 and g2["beta_disc"] > 0
                    and g2["beta_disc_t"] > g2["n2_beta_disc_t"]["p95"])
        net_ok = bool(r in h2 and g2["filtered_trades"] >= MIN_FILTERED and g2["filtered_net_mean"] > 0 and h2[r] < 0.05
                      and g2["filtered_ex_covid"] > 0 and g2["filtered_net_plus1tick_every_fill"] > 0)
        g2["checks"] = {"discriminates": disc, "filtered_net": net_ok, "holm_p": h2.get(r)}
        if r not in passed1:
            v = "NOT SUPPORTED"
        elif net_ok and disc:
            v = "SUPPORTED"
        elif not disc and out["roots"][r]["unfiltered_net"]["mean"] > 0 and hu.get(r, 1.0) < 0.05:
            v = "BREAK ONLY"
        elif r in passed1 and g2["filtered_trades"] < MIN_FILTERED and disc:
            v = "MECHANISM ONLY (Gate 2 UNRESOLVED: too few filtered trades)"
        else:
            v = "MECHANISM ONLY"
        out["roots"][r]["verdict"] = v
    for r in DEV:
        out["roots"][r]["verdict"] = "DEVELOPMENT (no verdict)"
    vs = [out["roots"][r]["verdict"] for r in EVID]
    out["construction_verdict"] = ("SUPPORTED" if "SUPPORTED" in vs else "BREAK ONLY" if "BREAK ONLY" in vs
                                   else "MECHANISM ONLY" if any(v.startswith("MECHANISM") for v in vs) else "NOT SUPPORTED")
    rr = out["roots"]
    out["predictions"] = {
        "1_YM_fails_gate1": "YM" not in passed1,
        "2_at_most_one_evidence_root_passes_gate1": len(passed1) <= 1,
        "3_beta_disc_t_below_2_every_root": all(not (rr[r]["gate2"]["beta_disc_t"] >= 2) for r in ROOTS),
        "4_NQ_reproduces_and_filtered_within_1p5bp": bool(abs(rr["NQ"]["gate1"]["gross_mean"] - ref["NQ_E4"]["mean"]) < 1e-9
                                                          and abs((rr["NQ"]["gate2"]["filtered_net_mean"] if np.isfinite(rr["NQ"]["gate2"]["filtered_net_mean"]) else 99)
                                                                  - rr["NQ"]["gate2"]["unfiltered_net_live"]) <= 1.5),
        "5_long_beats_short_every_root": all(rr[r]["splits"]["long_gross"] > rr[r]["splits"]["short_gross"] for r in ROOTS),
        "6_RTY_pass_rate_below_30pct": bool(rr["RTY"]["gate2"]["pass_rate"] < 0.30),
        "7_A7_negative_on_NQ_final_fit": bool(rr["NQ"]["gate2"]["final_coef_std"].get("a7", 0.0) < 0)}
    out["speed"] = {"trades_fanout_s": round(fan1, 1), "model_fanout_s": round(fan2, 1)}
    out["runtime_min"] = round((time.time() - t_start) / 60, 2)
    T.licence_guard(out)
    return out


def pfade_variant(tabs: dict, trades: dict, Xs: dict, frames: dict, R: Any) -> dict[str, Any]:
    """ES/NQ only, reported, never gated: the model plus p_FADE x 1[the fade opposes the trade], D645's walk-forward
    p_FADE at the latest checkpoint at or before the entry (D668 s.3; D668-A1 s.7)."""
    cal = sorted({s for r in R.ROOTS for s in tabs[r].index if tabs[r].loc[s, "usable"] and s >= FIRST})
    pf = {t: R.walk_forward(R.dataset(tabs, t, t), list(R.S_A), cal).set_index(["root", "session"])["p_FADE"]
          for t in CHECKPOINTS}
    out = {}
    for r in DEV:
        tr = trades[r]
        v = np.zeros(len(tr))
        for k, rec in tr.iterrows():
            cp = a7_checkpoint(int(rec["minute"]))
            if cp is None:
                continue
            ser = pf[cp]
            key = (r, rec["session"])
            if key in ser.index:
                fade_dir = -np.sign(rec["open"] - rec["prior_close"])
                v[k] = float(ser[key]) if fade_dir == -rec["D"] else 0.0
        Xf = np.column_stack([Xs[r][0], v])
        y, cost = tr["E4_gross"].to_numpy(float), tr["cost_bp"].to_numpy(float)
        P = predictor(Xf, y, cost)
        b, t = beta_disc(y, P["yhat"])
        net = y - cost
        out[r] = {"beta_disc": b, "beta_disc_t": t, "filtered_trades": int(P["take"].sum()),
                  "filtered_net_mean": float(net[P["take"]].mean()) if P["take"].any() else float("nan"),
                  "pfade_final_coef_std": float(P["betas"][np.isfinite(P["betas"][:, 0])][-1][-1])}
    return out


# ================================================================================ selftest
def selftest() -> int:
    fired = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except D668Error:
            fired.append(name)
            return
        raise SystemExit(f"selftest: the {name} canary did not raise")

    rng = np.random.default_rng(1)
    # 1. the walk-forward fit never sees its own session
    n, k = 320, 4
    Xf = rng.normal(size=(n, k))
    y = Xf @ np.array([1.0, -0.5, 0.0, 0.3]) + rng.normal(0, 5, n)
    sess = np.array([f"2016-{1 + i // 28:02d}-{1 + i % 28:02d}" for i in range(n)])
    idx = [BURN_MODEL, BURN_MODEL + 17, n - 1]
    good, _ = walk(Xf, y)
    walk_audit(good, Xf, y, sess, idx)
    must_raise("fit on its own session", lambda: walk_audit(walk(Xf, y, leak=True)[0], Xf, y, sess, idx))
    # 2. pi-hat from earlier forecasts only
    pi = pass_through(y, good)
    pi_audit(pi, y, good, idx)
    must_raise("pi-hat with its own outcome", lambda: pi_audit(pass_through(y, good, leak=True), y, good, idx))
    # 3. A7 at a checkpoint after the entry
    tr = pd.DataFrame({"session": ["2016-01-04", "2016-01-05"], "minute": [hm("09:50"), hm("10:40")], "D": [1, -1]})
    a7_audit(tr, [a7_checkpoint(m) for m in tr["minute"]])
    must_raise("A7 after the entry", lambda: a7_audit(tr, [a7_checkpoint(m, after=1) for m in tr["minute"]]))
    # 4. the gap measured to the entry price
    tg = pd.DataFrame({"D": [1, -1], "open": [101.0, 99.0], "entry": [103.0, 97.0], "prior_close": [100.0, 100.0],
                       "A": [2.0, 2.0]})
    gap_audit(tg, gap_feature(tg))
    must_raise("gap to the entry", lambda: gap_audit(tg, gap_feature(tg, to_entry=True)))
    # 5. sign in money, and 6. the root's own tick in the fill
    m = np.arange(hm("09:30"), hm("11:00"))
    up = np.linspace(100, 110, len(m))
    bb = {"m": m, "o": up, "h": up + 0.05, "l": up - 0.05, "c": up}
    for tick in (0.25, 1.0, 0.1):
        X.TICK = tick
        p = X.plain_break(bb, 101.0, 90.0, 4.0)
        if p is None or p["D"] != 1 or abs(p["entry"] - (max(p["stop"], bb["o"][p["i"]]) + tick)) > 1e-12:
            raise SystemExit(f"selftest: the fill did not carry the root's tick {tick}")
        px, _ = X.exit_trade(bb, p["i"], 1, p["entry"], p["L"], 4.0, 0.0, "E4")
        if not px > p["entry"]:
            raise SystemExit("selftest: a long that rises did not pay")
    dn = up[::-1] - 20
    bd = {"m": m, "o": dn, "h": dn + 0.05, "l": dn - 0.05, "c": dn}
    X.TICK = 0.25
    p = X.plain_break(bd, 200.0, 89.0, 4.0)
    if p is None or p["D"] != -1 or not X.exit_trade(bd, p["i"], -1, p["entry"], p["L"], 4.0, 0.0, "E4")[0] < p["entry"]:
        raise SystemExit("selftest: a short that falls did not pay")

    def wrong_tick() -> None:
        X.TICK = 0.25
        q = X.plain_break(bb, 101.0, 90.0, 4.0)
        if abs(q["entry"] - (max(q["stop"], bb["o"][q["i"]]) + 1.0)) > 1e-12:
            raise D668Error("fill: YM's entry does not carry YM's one-point tick")
    must_raise("the wrong root's tick", wrong_tick)
    # 7. right quantity: E4 differs from E2; the filter differs from no filter
    X.TICK = 0.25
    p = X.plain_break(bb, 101.0, 90.0, 4.0)
    if X.exit_trade(bb, p["i"], 1, p["entry"], p["L"], 4.0, 0.0, "E4") == X.exit_trade(bb, p["i"], 1, p["entry"], p["L"], 4.0, 0.0, "E2"):
        pass  # a monotone rise ends both at the close; the real run asserts E4 != E2 on the trade set
    P = predictor(Xf, y, np.full(n, 1.0))
    if not (P["take"].sum() > 0 and P["take"].sum() < P["live"].sum()):
        raise SystemExit("selftest: the filter should keep some but not all of a noisy book")
    # 8. N1 covers every session (the canary restricts the pool to the break sessions)
    def n1_on_breaks_only() -> None:
        sessions_all, pool_sessions = ["a", "b", "c"], ["a", "c"]
        if len(pool_sessions) != len(sessions_all):
            raise D668Error("N1: the pool does not cover every session")
    must_raise("N1 on the break sessions only", n1_on_breaks_only)
    # 9. the licence guard raises on a per-date series
    try:
        T.licence_guard({"x": {f"2016-01-{i:02d}" if i < 32 else f"2016-02-{i - 31:02d}": 1.0 for i in range(1, 62)}})
    except T.D663Error:
        fired.append("licence guard")
    else:
        raise SystemExit("selftest: the licence guard did not raise on a 61-date series")
    print(f"selftest: {len(fired)} canaries fired: {fired}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.dry_run or a.run):
        ap.print_help()
        return 1
    out = build(a.data_root, dry=a.dry_run)
    dest = REPO / "temp" / "stage0_d668_dry.json" if a.dry_run else OUT
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"verdict": out["construction_verdict"],
                      "roots": {r: {"verdict": v["verdict"], "trades": v["trades"], "gross": v["gate1"]["gross_mean"],
                                    "t": v["gate1"]["t_hac"], "n1_p95": v["gate1"]["n1"]["p95"],
                                    "filtered": v["gate2"]["filtered_trades"], "filtered_net": v["gate2"]["filtered_net_mean"],
                                    "beta_disc_t": v["gate2"]["beta_disc_t"]} for r, v in out["roots"].items()},
                      "predictions": out["predictions"], "runtime_min": out["runtime_min"]}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Shared helpers for the conservative agent's premise tests. Read-only on the repo; seal at 2024-01-01."""
from __future__ import annotations
import json, os, math
import numpy as np
import pandas as pd

MAIN = r"C:\Users\O\Desktop\Projects\Backtest Framework"
WT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674"
FIX = os.path.join(MAIN, "data", "fixtures")
OUT = r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\fable_pair\out"
SEAL = "2024-01-01"

# dollars per 1.0 price point, ONE micro contract
MULT = {"ES": 5.0, "NQ": 2.0, "YM": 0.5, "RTY": 5.0, "GC": 10.0, "SI": 1000.0, "HG": 2500.0, "CL": 100.0,
        "NG": 1000.0, "6E": 12500.0, "6A": 10000.0, "BTC": 0.1, "6J": 1250000.0, "BZ": 100.0, "HO": 100.0,
        "ZN": 1000.0, "ZB": 1000.0, "6B": 6250.0}
MICRO = {"ES": "MES", "NQ": "MNQ", "YM": "MYM", "RTY": "M2K", "GC": "MGC", "SI": "SIL", "HG": "MHG", "CL": "MCL",
         "NG": "MNG", "6E": "M6E", "6A": "M6A", "BTC": "MBT", "6J": "MJY", "BZ": "(none; MCL proxy)",
         "HO": "(none)", "6B": "M6B"}


def micro_cost(root: str) -> float:
    """Round trip in dollars at one micro: $3 commission + measured effective crossing (d508_exec) or one tick."""
    j = json.load(open(os.path.join(WT, "data", "futures_costs.json"), encoding="utf-8"))
    r = j["roots"].get(root)
    if r is None or "micro" not in r:
        return float("nan")
    m = r["micro"]
    tick = m["tick_usd"]
    ct = m["crossing_ticks_rt"]
    x = ct.get("d508_exec", ct.get("d556_one_tick"))["value"]
    return 3.0 + x * tick


def load_day1m(roots, lo="2016-01-04", hi="2023-12-29", cols=("root", "contract", "day", "bar", "open", "high", "low", "close", "volume", "same_front", "present")):
    import pyarrow.parquet as pq
    import pyarrow.compute as pc
    import pyarrow as pa
    p = os.path.join(FIX, "fut_day1m.parquet")
    t = pq.read_table(p, columns=list(cols), filters=[("root", "in", list(roots)), ("day", ">=", lo), ("day", "<=", hi)])
    d = t.to_pandas()
    assert (d["day"] < SEAL).all(), "seal violated"
    return d


def spearman(a, b) -> float:
    a = pd.Series(np.asarray(a, float)); b = pd.Series(np.asarray(b, float))
    m = a.notna() & b.notna()
    if m.sum() < 10:
        return float("nan")
    return float(np.corrcoef(a[m].rank().to_numpy(), b[m].rank().to_numpy())[0, 1])


def tstat(v) -> float:
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    if len(v) < 3:
        return float("nan")
    return float(v.mean() / (v.std(ddof=1) / math.sqrt(len(v))))


def nw_t(v, lags=5) -> float:
    """Newey-West t of a mean."""
    v = np.asarray(v, float); v = v[np.isfinite(v)]
    n = len(v)
    if n < 10:
        return float("nan")
    e = v - v.mean()
    s = (e * e).sum()
    for k in range(1, lags + 1):
        w = 1 - k / (lags + 1)
        s += 2 * w * (e[k:] * e[:-k]).sum()
    se = math.sqrt(max(s, 1e-30)) / n
    return float(v.mean() / se)


def rotation_p(x, y, stat, n_off=None, seed=0):
    """Time-rotation null of y against x over all offsets (or a sample): returns observed, p50, p95, two-sided p."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = len(x)
    obs = stat(x, y)
    offs = range(1, n) if n_off is None or n_off >= n - 1 else np.random.default_rng(seed).choice(np.arange(1, n), n_off, replace=False)
    vals = np.array([stat(x, np.roll(y, k)) for k in offs])
    p = float(np.mean(np.abs(vals) >= abs(obs)))
    return obs, float(np.percentile(vals, 50)), float(np.percentile(vals, 95)), float(np.percentile(vals, 5)), p


def four_groups(pnl: np.ndarray, years: np.ndarray, cost: float, label: str) -> dict:
    pnl = np.asarray(pnl, float); ok = np.isfinite(pnl); pnl = pnl[ok]; years = np.asarray(years)[ok]
    n = len(pnl)
    if n == 0:
        return {"label": label, "n": 0}
    net = pnl - cost
    q = np.quantile(pnl, [0.01, 0.99])
    trimmed = pnl[(pnl > q[0]) & (pnl < q[1])].mean() if n > 100 else float("nan")
    ex_top = pnl[pnl < q[1]].mean() if n > 100 else float("nan")
    ex_bot = pnl[pnl > q[0]].mean() if n > 100 else float("nan")
    by_year = pd.Series(pnl).groupby(pd.Series(years)).agg(["mean", "count", "sum"])
    sh = float(net.mean() / net.std(ddof=1) * math.sqrt(252)) if n > 2 and net.std() > 0 else float("nan")
    top = int(np.argmax(pnl))
    return {"label": label, "n": n, "gross_mean": float(pnl.mean()), "gross_median": float(np.median(pnl)),
            "t": tstat(pnl), "nw_t": nw_t(pnl), "net_mean": float(net.mean()), "cost": cost,
            "win": float((pnl > 0).mean()), "skew": float(pd.Series(pnl).skew()),
            "ex_top1": float(ex_top), "ex_bot1": float(ex_bot), "trimmed": float(trimmed),
            "net_sharpe_per_trade_ann": sh, "pos_years": int((by_year["sum"] > 0).sum()), "n_years": int(len(by_year)),
            "by_year_mean": {str(k): round(float(v), 2) for k, v in by_year["mean"].items()},
            "by_year_n": {str(k): int(v) for k, v in by_year["count"].items()},
            "top_trade": float(pnl[top]), "top_share_of_total": float(pnl[top] / pnl.sum()) if pnl.sum() != 0 else float("nan")}


def fmt(d: dict) -> str:
    return json.dumps(d, indent=1, default=str)

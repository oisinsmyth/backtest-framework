"""D769 Stage 0: the PBOC yuan-fix residual and the AUD / copper (prop book; one micro, M6A / MHG).

Pre-registration: docs/decisions/D769-STAGE-0-PRE-REG-the-yuan-fix-residual-and-the-aud.md (with Amendment 1: the G2
position is sign(rho) x sign(s)).

    python scripts/stage0_d769_yuan_fix_residual.py --selftest
    python scripts/stage0_d769_yuan_fix_residual.py --extract     # 6A 6E 6J 6B 6C 6S HG front minutes, all hours, < 2024
    python scripts/stage0_d769_yuan_fix_residual.py --run         # once

Fix day t (Beijing date): F_t = 09:15 Beijing. M_t = the latest FRED noon-NY USD/CNY strictly before F_t (<= 4 days
old). Basket b_i = log P_i(before F_t) - log P_i(before noon ET of M_t's date), i in 6E 6J 6B 6A 6C 6S (<= 30 min stale,
one contract). Delta_t = log(fix_t / M_t) regressed on (1, b) over the previous 250 eligible days (OLS, walk-forward);
r_t = the out-of-sample residual; s_t = r_t - mean of the previous 20 residuals. Outcome per cell: E_t = open of the
first bar in [F+1, F+5]; y_t = close before 03:00 ET of trade date t minus E_t, in $ per micro.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import io
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
MAIN_DATA = Path("C:/Users/O/Desktop/Projects/Backtest Framework/data")
SPEC = REPO / "docs" / "decisions" / "D769-STAGE-0-PRE-REG-the-yuan-fix-residual-and-the-aud.md"
OUT = REPO / "data" / "stage0_d769_yuan_fix_residual.json"
FIX = REPO / "data" / "fixtures" / "cny_central_parity.csv"
FRED = REPO / "data" / "fixtures" / "fred_dexchus.csv"
BOOKS = REPO / "data" / "d748_component_books.csv"
TMP = Path(os.environ.get("D769_TMP", str(REPO / "temp" / "d769")))
SEAL = "2024-01-01"
SEAL_NS = int(pd.Timestamp(SEAL, tz="UTC").value)
XLO_NS = int(pd.Timestamp("2015-05-01", tz="UTC").value)
NY, BJ = ZoneInfo("America/New_York"), ZoneInfo("Asia/Shanghai")
BASKET = ("6E", "6J", "6B", "6A", "6C", "6S")
ROOTS = BASKET + ("HG",)
CELLS = {"AUD": dict(root="6A", mult=10_000.0, tick_usd=1.00, cost=4.00, cost_alt=4.41),
         "COPPER": dict(root="HG", mult=2_500.0, tick_usd=1.25, cost=4.25, cost_alt=None)}
UNITS = {"6A": (0.55, 0.85), "HG": (1.8, 5.2)}
WF, SURP, TERC_WF = 250, 20, 250
STALE_BASKET, STALE_OUT, MAX_NOON_AGE_D = 30, 10, 4
T_MIN, YEARS_MIN = 2.0, 5
REGIMES = (("2015-06..2016-12", "2015-06-01", "2016-12-31"), ("2017-01..2017-05-25", "2017-01-01", "2017-05-25"),
           ("CCF on 2017-05-26..2018-01-08", "2017-05-26", "2018-01-08"), ("CCF off 2018-01-09..2018-07-31", "2018-01-09", "2018-07-31"),
           ("CCF on 2018-08-01..2020-10-26", "2018-08-01", "2020-10-26"), ("CCF off 2020-10-27..2022-12-31", "2020-10-27", "2022-12-31"),
           ("2023", "2023-01-01", "2023-12-31"))
MONTH_CODE = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
WORKERS = 4


class D769Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D769Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ================================================================================ clock
def tz_min(day: str, hh: int, mm: int, tz: ZoneInfo) -> int:
    d = dt.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), hh, mm, tzinfo=tz).astimezone(dt.timezone.utc)
    return int(d.timestamp() // 60)


def fix_minute(day: str) -> int:
    return tz_min(day, 9, 15, BJ)


def et_wall(utc_min: int) -> dt.datetime:
    return dt.datetime.fromtimestamp(utc_min * 60, tz=dt.timezone.utc).astimezone(NY)


def trade_day_of(ts_ns: np.ndarray) -> np.ndarray:
    t = pd.to_datetime(ts_ns, utc=True).tz_convert(NY).tz_localize(None)
    wall = np.asarray((t - pd.Timestamp("1970-01-01")) // pd.Timedelta(minutes=1), dtype=np.int64)
    return ((wall + 360) // 1440).astype(np.int64)


# ================================================================================ extraction (D765/D768's, restated)
def _front_map() -> dict[tuple[str, str], str]:
    import forward_f2_c1_ledgers as FW
    bh = pd.read_csv(io.BytesIO(FW.restrict_text(MAIN_DATA / "fixtures" / "fut_breadth_hourly.csv.gz", 1, SEAL)),
                     usecols=["root", "day", "contract"], dtype={"day": str}, encoding="utf-8")
    bh = bh[bh["root"].isin(ROOTS)]
    return {(r, d): c for r, d, c in zip(bh["root"], bh["day"], bh["contract"])}


def _extract_file(path: str) -> pd.DataFrame | None:
    import databento as db
    import build_fut_breadth_hourly as BH
    fm = _front_map()
    store = db.DBNStore.from_file(path)
    w = BH.ids_of(store)
    if w is None:
        return None
    w = w[w["root"].isin(ROOTS)]
    if len(w) == 0:
        return None
    parts = []
    for arr in store.to_ndarray(count=BH.CHUNK):
        a = arr[np.isin(arr["instrument_id"], w["iid"].to_numpy(np.uint32)) & (arr["ts_event"] < SEAL_NS)
                & (arr["ts_event"] >= XLO_NS)]
        if a.size == 0:
            continue
        raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "ts": a["ts_event"].astype(np.int64),
                            "open": a["open"] * BH.PX, "close": a["close"] * BH.PX})
        j = raw.merge(w, on="iid", how="inner")
        j = j[(j["ts"].astype(np.uint64) >= j["w0"]) & (j["ts"].astype(np.uint64) < j["w1"])]
        if len(j) == 0:
            continue
        j = j.assign(dn=trade_day_of(j["ts"].to_numpy())).drop(columns=["iid", "w0", "w1"])
        keys = j[["root", "dn"]].drop_duplicates()
        keys["day"] = np.asarray(pd.to_datetime(keys["dn"].to_numpy(), unit="D").strftime("%Y-%m-%d"))
        keys["front"] = [fm.get((r, d), "") for r, d in zip(keys["root"], keys["day"])]
        j = j.merge(keys, on=["root", "dn"], how="left")
        k = j[j["contract"].to_numpy() == j["front"].to_numpy()]
        if len(k):
            parts.append(k[["root", "contract", "ts", "day", "open", "close"]].reset_index(drop=True))
    return pd.concat(parts, ignore_index=True) if parts else None


def extract() -> int:
    raw = sorted(p for d in sorted((MAIN_DATA / "raw" / "databento").glob("GLBX-*")) for p in d.glob("*.ohlcv-1m.dbn.zst"))
    print(f"{len(raw)} ohlcv-1m files", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(WORKERS) as ex:
        got = list(ex.map(_extract_file, [str(p) for p in raw]))
    sizes = [0 if g is None else len(g) for g in got]
    i = int(np.argmax(sizes))
    again = _extract_file(str(raw[i]))
    need(again is not None and again.equals(got[i]), f"chunk != whole: {raw[i].name} re-decoded serially differs")
    df = pd.concat([g for g in got if g is not None], ignore_index=True)
    need(bool((df["ts"] < SEAL_NS).all()) and bool((df["day"] < SEAL).all()), "seal: a minute on or after 2024-01-01")
    need(not df.duplicated(["root", "ts"]).any(), "duplicate minutes for a root")
    TMP.mkdir(parents=True, exist_ok=True)
    for r in ROOTS:
        x = df[df["root"] == r].sort_values("ts").reset_index(drop=True)
        x.to_parquet(TMP / f"raw_{r}.parquet", index=False)
        print(f"{r}: {len(x):,} front minutes, {x['day'].min()} -> {x['day'].max()}", flush=True)
    print(f"extract: {(time.time() - t0) / 60:.1f} min; serial re-decode of {raw[i].name} == process result", flush=True)
    return 0


# ================================================================================ prices
class Bars:
    def __init__(self, b: pd.DataFrame, root: str):
        need(bool((b["ts"] > 10**18).all()), f"{root}: a timestamp is not in nanoseconds")
        need(bool((b["ts"] < SEAL_NS).all()) and bool((b["day"] < SEAL).all()), f"seal: a {root} bar on or after 2024")
        self.root = root
        self.S = (b["ts"].to_numpy(np.int64) // 60_000_000_000).astype(np.int64)
        need(bool(np.all(np.diff(self.S) > 0)), f"{root}: bars not strictly ordered")
        self.O, self.C = b["open"].to_numpy(float), b["close"].to_numpy(float)
        self.K = b["contract"].to_numpy()
        self.D = b["day"].to_numpy()

    def before(self, t: int, stale: int) -> int | None:
        i = int(np.searchsorted(self.S, t, side="left")) - 1
        return i if i >= 0 and self.S[i] >= t - stale else None

    def open_in(self, t0: int, t1: int) -> int | None:
        j = int(np.searchsorted(self.S, t0, side="left"))
        return j if j < self.S.size and self.S[j] <= t1 else None


def check_units(close: np.ndarray, root: str) -> float:
    lo, hi = UNITS[root]
    med = float(np.median(close))
    need(lo <= med <= hi, f"units: the median {root} close {med} is outside [{lo}, {hi}]")
    return med


def last_day(contract: str, root: str, day: str) -> dt.date:
    """FX: the CME last trading day (two business days before the third Wednesday). HG: the first notice day (the last
    weekday of the month before the delivery month). Single-digit year in the trade date's decade or the next."""
    mo, yd = MONTH_CODE[contract[2]], int(contract[3:]) % 10
    y0 = int(day[:4])
    y = y0 - y0 % 10 + yd
    if y < y0:
        y += 10
    if root == "HG":
        d = dt.date(y, mo, 1) - dt.timedelta(days=1)
        while d.weekday() > 4:
            d -= dt.timedelta(days=1)
        return d
    first = dt.date(y, mo, 1)
    wed = first + dt.timedelta(days=(2 - first.weekday()) % 7 + 14)
    d, k = wed, 0
    while k < 2:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5:
            k += 1
    return d


def business_days_between(a: dt.date, b: dt.date) -> int:
    return int(np.busday_count(a, b))


# ================================================================================ the residual
def load_fix() -> pd.DataFrame:
    f = pd.read_csv(FIX, usecols=["date", "usdcny_fix"], dtype={"date": str}, encoding="utf-8")
    need(bool((f["date"] < SEAL).all()), "seal: a fix dated 2024 or later")
    need(bool(f["usdcny_fix"].between(6.0, 7.4).all()), "units: a fix outside [6.0, 7.4]")
    return f


def load_fred() -> pd.DataFrame:
    f = pd.read_csv(FRED, dtype={"date": str}, encoding="utf-8")
    need(bool((f["date"] < SEAL).all()), "seal: a FRED row dated 2024 or later")
    need(bool(f["usdcny_noon_ny"].between(6.0, 7.5).all()), "units: a FRED rate outside [6.0, 7.5]")
    f["noon_utc_min"] = [tz_min(d, 12, 0, NY) for d in f["date"]]
    return f


def residual_inputs(fix: pd.DataFrame, fred: pd.DataFrame, bars: dict[str, Bars]) -> pd.DataFrame:
    noon_t, noon_v, noon_d = fred["noon_utc_min"].to_numpy(), fred["usdcny_noon_ny"].to_numpy(float), fred["date"].to_numpy()
    rows = []
    for d, fx in zip(fix["date"], fix["usdcny_fix"]):
        F = fix_minute(d)
        k = int(np.searchsorted(noon_t, F, side="left")) - 1
        if k < 0 or F - noon_t[k] > MAX_NOON_AGE_D * 1440:
            rows.append((d, F, fx, np.nan, "", *([np.nan] * len(BASKET))))
            continue
        b = []
        for r in BASKET:
            B = bars[r]
            i1, i0 = B.before(F, STALE_BASKET), B.before(int(noon_t[k]), STALE_BASKET)
            b.append(math.log(B.C[i1] / B.C[i0]) if i1 is not None and i0 is not None and B.K[i1] == B.K[i0] else np.nan)
        rows.append((d, F, fx, float(noon_v[k]), str(noon_d[k]), *b))
    out = pd.DataFrame(rows, columns=["date", "F", "fix", "noon", "noon_date"] + [f"b_{r}" for r in BASKET])
    out["delta"] = np.log(out["fix"] / out["noon"])
    return out


def walk_forward(X: np.ndarray, y: np.ndarray, wf: int = WF) -> np.ndarray:
    """Out-of-sample residual: for row k, OLS on rows k-wf..k-1 only."""
    r = np.full(y.size, np.nan)
    for k in range(wf, y.size):
        beta, *_ = np.linalg.lstsq(X[k - wf:k], y[k - wf:k], rcond=None)
        r[k] = y[k] - X[k] @ beta
    return r


def residual_by_normal_equations(X: np.ndarray, y: np.ndarray, k: int, wf: int = WF, include_self: bool = False) -> float:
    """Second implementation (lag audit): the normal equations on the window, never calling walk_forward."""
    lo, hi = k - wf, (k + 1 if include_self else k)
    A, z = X[lo + (1 if include_self else 0):hi], y[lo + (1 if include_self else 0):hi]
    beta = np.linalg.solve(A.T @ A, A.T @ z)
    return float(y[k] - X[k] @ beta)


def lag_audit(X: np.ndarray, y: np.ndarray, r: np.ndarray, sample: list[int], include_self: bool = False) -> None:
    for k in sample:
        alt = residual_by_normal_equations(X, y, k, include_self=include_self)
        need(abs(alt - r[k]) < 1e-9, f"lag audit: residual at row {k} is {r[k]:.3e}, a second implementation gives {alt:.3e}")


def surprise(r: np.ndarray, n: int = SURP) -> np.ndarray:
    s = np.full(r.size, np.nan)
    for k in range(r.size):
        prev = r[max(0, k - n):k]
        if np.isfinite(r[k]) and prev.size == n and np.all(np.isfinite(prev)):
            s[k] = r[k] - prev.mean()
    return s


# ================================================================================ statistics
def ranks(x: np.ndarray) -> np.ndarray:
    return pd.Series(x).rank().to_numpy(float)


def rot_spearman(s: np.ndarray, y: np.ndarray) -> dict:
    rs, ry = ranks(s), ranks(y)
    rs, ry = rs - rs.mean(), ry - ry.mean()
    den = math.sqrt(float((rs * rs).sum() * (ry * ry).sum()))
    obs = float((rs * ry).sum() / den)
    null = np.array([float((np.roll(rs, k) * ry).sum() / den) for k in range(1, rs.size)])
    hi, lo = (1 + (null >= obs).sum()) / (1 + null.size), (1 + (null <= obs).sum()) / (1 + null.size)
    return {"rho": obs, "offset0": float((np.roll(rs, 0) * ry).sum() / den), "offsets": int(null.size),
            "p2_5": float(np.percentile(null, 2.5)), "p50": float(np.percentile(null, 50)), "p97_5": float(np.percentile(null, 97.5)),
            "p_two_sided": float(min(1.0, 2 * min(hi, lo)))}


def holm(p: dict[str, float], alpha: float = 0.05) -> dict[str, bool]:
    order = sorted(p, key=p.get)
    out, ok = {}, True
    for i, k in enumerate(order):
        ok = ok and p[k] <= alpha / (len(order) - i)
        out[k] = ok
    return out


def nw_t(x: np.ndarray, lags: int = 5) -> float:
    x = np.asarray(x, float)
    n = x.size
    e = x - x.mean()
    s = float((e * e).sum())
    for L in range(1, lags + 1):
        s += 2 * (1 - L / (lags + 1)) * float((e[L:] * e[:-L]).sum())
    return float(x.mean() / math.sqrt(s / n / n)) if s > 0 else float("nan")


def dist(x) -> dict:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    n = x.size
    if n < 3:
        return {"n": int(n)}
    srt = np.sort(x)
    k = int(math.floor(0.01 * n))
    sd = float(x.std(ddof=1))
    w, l = x[x > 0], x[x < 0]
    return {"n": int(n), "mean": float(x.mean()), "t": float(x.mean() / (sd / math.sqrt(n))) if sd > 0 else float("nan"),
            "median": float(np.median(x)), "win": float((x > 0).mean()), "sd": sd,
            "payoff": float(w.mean() / -l.mean()) if w.size and l.size else None,
            "skew": float(pd.Series(x).skew()), "kurt": float(pd.Series(x).kurt()),
            "mean_ex_top1": float(srt[: n - k].mean()) if k else float(x.mean()),
            "mean_ex_bottom1": float(srt[k:].mean()) if k else float(x.mean()),
            "mean_trim_both1": float(srt[k: n - k].mean()) if k else float(x.mean())}


def sharpe_sortino(x: np.ndarray) -> tuple:
    sd = x.std(ddof=1)
    dd = math.sqrt(float(np.mean(np.minimum(x, 0) ** 2)))
    return (float(x.mean() / sd * math.sqrt(252)) if sd > 0 else None, float(x.mean() / dd * math.sqrt(252)) if dd > 0 else None)


def top_third(s: np.ndarray, wf: int = TERC_WF) -> np.ndarray:
    a = np.abs(s)
    out = np.zeros(s.size, dtype=bool)
    for k in range(s.size):
        prev = a[max(0, k - wf):k]
        prev = prev[np.isfinite(prev)]
        if np.isfinite(a[k]) and prev.size >= wf * 0.9:
            out[k] = a[k] > np.percentile(prev, 100 * 2 / 3)
    return out


def position(rho_sign: int, s: np.ndarray) -> np.ndarray:
    """Amendment 1: with y ~ rho * s, the position that earns is sign(rho) * sign(s)."""
    return rho_sign * np.sign(s)


# ================================================================================ outcomes
def outcomes(inp: pd.DataFrame, B: Bars, mult: float) -> pd.DataFrame:
    rows = []
    for d, F in zip(inp["date"], inp["F"]):
        j = B.open_in(int(F) + 1, int(F) + 5)
        if j is None:
            rows.append((np.nan, np.nan, np.nan, "", 0))
            continue
        e_price, kc = float(B.O[j]), B.K[j]
        t0300, t1500 = tz_min(d, 3, 0, NY), tz_min(d, 15, 0, NY)
        i3, i15 = B.before(t0300, STALE_OUT), B.before(t1500, STALE_OUT)
        y = (B.C[i3] - e_price) * mult if i3 is not None and B.K[i3] == kc else np.nan
        yd = (B.C[i15] - e_price) * mult if i15 is not None and B.K[i15] == kc else np.nan
        a, b = B.before(int(F), STALE_OUT), B.before(int(F) + 15, STALE_OUT)
        yi = (B.C[b] - B.C[a]) * mult if a is not None and b is not None and B.K[a] == B.K[b] else np.nan
        rows.append((y, yi, yd, str(kc), int(B.S[j] - F)))
    return pd.DataFrame(rows, columns=["y", "y_imm", "y_day", "contract", "entry_lag_min"])


# ================================================================================ run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    bars = {r: Bars(pd.read_parquet(TMP / f"raw_{r}.parquet"), r) for r in ROOTS}
    meds = {r: check_units(bars[r].C, r) for r in ("6A", "HG")}
    fix, fred = load_fix(), load_fred()
    inp = residual_inputs(fix, fred, bars)
    need(bool((inp["noon_date"].map(lambda d: tz_min(d, 12, 0, NY) if d else 0) < inp["F"]).all()), "lag: a noon rate not before its fix")
    ok = np.isfinite(inp[["delta"] + [f"b_{r}" for r in BASKET]].to_numpy()).all(axis=1)
    E = inp[ok].reset_index(drop=True)
    X = np.column_stack([np.ones(len(E))] + [E[f"b_{r}"].to_numpy() for r in BASKET])
    yv = E["delta"].to_numpy()
    r = walk_forward(X, yv)
    rng = np.random.default_rng(769)
    samp = sorted(int(i) for i in rng.choice(np.arange(WF, len(E)), size=30, replace=False))
    lag_audit(X, yv, r, samp)
    E["r"] = r
    E["s"] = surprise(r)
    fitted = yv - r
    oos = np.isfinite(r)
    r2 = float(1 - np.nansum(r[oos] ** 2) / np.sum((yv[oos] - yv[oos].mean()) ** 2))
    res: dict[str, Any] = {"record": "D769", "checks": {"fix_days": int(len(fix)), "with_inputs": int(len(E)), "median_close": meds,
                                                         "walk_forward_oos_r2": r2, "lag_audit_rows": samp},
                           "model": {"r_sd_by_year": {}, "r_mean_by_year": {}, "r_ar1": None}, "cells": {}}
    yrs = E["date"].str[:4]
    for y_, g in E[oos].groupby(yrs[oos]):
        res["model"]["r_sd_by_year"][y_] = float(g["r"].std())
        res["model"]["r_mean_by_year"][y_] = float(g["r"].mean())
    rr = E["r"].to_numpy()
    m = np.isfinite(rr[1:]) & np.isfinite(rr[:-1])
    res["model"]["r_ar1"] = float(np.corrcoef(rr[1:][m], rr[:-1][m])[0, 1])
    pv, per = {}, {}
    for cell, c in CELLS.items():
        B = bars[c["root"]]
        oc = outcomes(E, B, c["mult"])
        D = pd.concat([E, oc], axis=1)
        D = D[np.isfinite(D["s"]) & np.isfinite(D["y"])].reset_index(drop=True)
        gaps = []
        for d, k in zip(D["date"], D["contract"]):
            gaps.append(business_days_between(dt.date.fromisoformat(d), last_day(k, c["root"], d)))
        need(min(gaps) > (2 if c["root"] != "HG" else 0), f"delivery: a {c['root']} front within its last-day window")
        need(bool((D["entry_lag_min"] >= 1).all()), "lag: an entry at or before the fix minute")
        s, y = D["s"].to_numpy(), D["y"].to_numpy()
        g1 = rot_spearman(s, y)
        need(math.isclose(g1["offset0"], g1["rho"], abs_tol=1e-12), "rotation offset 0 != observed")
        pv[cell] = g1["p_two_sided"]
        per[cell] = (D, g1, gaps)
    hk = holm(pv)
    for cell, (D, g1, gaps) in per.items():
        c = CELLS[cell]
        s, y = D["s"].to_numpy(), D["y"].to_numpy()
        days = D["date"].tolist()
        passed1 = bool(hk[cell])
        rho_sign = int(np.sign(g1["rho"])) if passed1 else -1
        tt = top_third(s)
        pos = position(rho_sign, s)
        g = (pos * y)[tt]
        net = g - c["cost"]
        dn = np.zeros(len(days))
        dn[tt] = net
        dg = np.zeros(len(days))
        dg[tt] = g
        eq = np.cumsum(dn)
        d_tt = np.array(days)[tt]
        yr = pd.Series(net).groupby([d[:4] for d in d_tt]).sum()
        best = yr.idxmax() if len(yr) else None
        ex_best = float(net[np.array([d[:4] != best for d in d_tt])].sum()) if best else float("nan")
        g2 = bool(passed1 and g.size and g.mean() >= c["cost"] and nw_t(g) >= T_MIN)
        g3 = bool(g2 and (yr > 0).sum() >= YEARS_MIN and ex_best > 0)
        reading = "NO DIRECTION" if not passed1 else ("DIRECTION, NO PRIZE" if not g2 else ("EPISODIC" if not g3 else "PREMISE HOLDS"))
        imm_ok = np.isfinite(D["y_imm"].to_numpy())
        day_ok = np.isfinite(D["y_day"].to_numpy())
        rr = D["r"].to_numpy()
        order = np.argsort(net)
        bk = pd.read_csv(BOOKS, dtype={"session": str}, encoding="utf-8")
        rho_b = {}
        dns = pd.Series(dn, index=days)
        for nm, gbk in bk.groupby("book"):
            sb = gbk.groupby("session")["net"].sum()
            span = [d for d in days if sb.index.min() <= d <= sb.index.max()]
            s1 = dns.reindex(span).to_numpy()
            rho_b[nm] = float(np.corrcoef(s1, sb.reindex(span, fill_value=0.0).to_numpy())[0, 1]) if len(span) > 30 and s1.std() > 0 else None
        reg = {}
        for nm, a, b_ in REGIMES:
            mm = np.array([a <= d <= b_ for d in days])
            if mm.sum() > 30:
                reg[nm] = {"n": int(mm.sum()), "rho": float(pd.Series(s[mm]).corr(pd.Series(y[mm]), method="spearman")),
                           "trade_net": float(net[mm[tt]].sum()) if (mm & tt).any() else 0.0, "trades": int((mm & tt).sum())}
        ex_aug = np.array([not d.startswith("2015-08") for d in days])
        res["cells"][cell] = {
            "reading": reading, "n": int(len(days)), "first": days[0], "last": days[-1],
            "G1": dict(g1, holm_reject=passed1),
            "G2": {"direction_rho_sign": rho_sign, "trades": int(tt.sum()), "gross": dist(g), "nw_t": nw_t(g) if g.size > 5 else None,
                   "cost": c["cost"], "passed": g2},
            "G3": {"net_by_year": {k: float(v) for k, v in yr.items()}, "years_positive": int((yr > 0).sum()), "best_year": best,
                   "net_ex_best_year": ex_best, "passed": g3},
            "trade": {"net": dist(net), "net_alt_cost": dist(g - c["cost_alt"]) if c["cost_alt"] else None,
                      "net_plus_one_tick": dist(net - c["tick_usd"]), "daily_net_sharpe_sortino": sharpe_sortino(dn),
                      "daily_gross_sharpe_sortino": sharpe_sortino(dg), "max_dd_usd": float((np.maximum.accumulate(eq) - eq).max()),
                      "breakeven_cost": float(g.mean()) if g.size else None,
                      "top5": [(str(d_tt[i]), float(net[i])) for i in order[::-1][:5]],
                      "bottom5": [(str(d_tt[i]), float(net[i])) for i in order[:5]], "rho_books": rho_b},
            "reported": {
                "is_it_news_imm": rot_spearman(s[imm_ok], D["y_imm"].to_numpy()[imm_ok]),
                "is_it_news_imm_top_third": float(pd.Series(s[imm_ok & tt]).corr(pd.Series(D["y_imm"].to_numpy()[imm_ok & tt]), method="spearman")),
                "stance_level_rho": float(pd.Series(rr).corr(pd.Series(y), method="spearman")),
                "rest_of_day_rho": float(pd.Series(s[day_ok]).corr(pd.Series(D["y_day"].to_numpy()[day_ok]), method="spearman")),
                "ex_aug_2015_rho": float(pd.Series(s[ex_aug]).corr(pd.Series(y[ex_aug]), method="spearman")),
                "size_abs_y_top_third_vs_other": [float(np.abs(y[tt]).mean()), float(np.abs(y[~tt]).mean())],
                "regimes": reg, "all_days_y": dist(y),
                "min_business_days_to_last_day": int(min(gaps))}}
    res.update({"runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "fix_sha256": sha(FIX),
                "fred_sha256": sha(FRED), "wall_s": round(time.time() - t0, 1)})
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    print(f"[D769] model: walk-forward OOS R2 {r2:.3f}; r AR(1) {res['model']['r_ar1']:.2f}; mean r by year "
          + " ".join(f"{k}:{v * 1e4:+.0f}bp" for k, v in res["model"]["r_mean_by_year"].items()))
    for cell in CELLS:
        q = res["cells"][cell]
        print(f"[D769] {cell}: {q['reading']}; rho {q['G1']['rho']:+.4f} (p2.5 {q['G1']['p2_5']:+.4f} p97.5 {q['G1']['p97_5']:+.4f}; "
              f"p {q['G1']['p_two_sided']:.3f}); n {q['n']}; trade ({'+' if q['G2']['direction_rho_sign'] > 0 else '-'}) "
              f"gross {q['G2']['gross'].get('mean', float('nan')):+.2f} t_NW {q['G2']['nw_t']}; imm rho {q['reported']['is_it_news_imm']['rho']:+.3f} "
              f"(p {q['reported']['is_it_news_imm']['p_two_sided']:.3f})")
    print(f"[D769] wall {res['wall_s']} s")
    return 0


# ================================================================================ self-test
def selftest() -> int:
    fails: list[str] = []

    def expect_raise(fn, label):
        try:
            fn()
            fails.append(f"{label} did not raise")
        except D769Error:
            pass

    # the clock: 09:15 Beijing is 20:15 ET (EST) / 21:15 ET (EDT) on the previous ET calendar day
    w1, w2 = et_wall(fix_minute("2021-01-15")), et_wall(fix_minute("2021-07-15"))
    if (w1.date().isoformat(), w1.hour, w1.minute) != ("2021-01-14", 20, 15):
        fails.append(f"09:15 Beijing on 2021-01-15 maps to {w1}")
    if (w2.date().isoformat(), w2.hour, w2.minute) != ("2021-07-14", 21, 15):
        fails.append(f"09:15 Beijing on 2021-07-15 maps to {w2}")
    if trade_day_of(np.array([fix_minute("2021-01-15") * 60_000_000_000]))[0] != (dt.date(2021, 1, 15) - dt.date(1970, 1, 1)).days:
        fails.append("the fix's CME trade date is not its Beijing date")
    # last days: 6AH1 (third Wed 2021-03-17) -> LTD Mon 2021-03-15; HGK1 -> FND Fri 2021-04-30
    if last_day("6AH1", "6A", "2021-01-10") != dt.date(2021, 3, 15):
        fails.append(f"6AH1 last trading day {last_day('6AH1', '6A', '2021-01-10')}")
    if last_day("HGK1", "HG", "2021-03-10") != dt.date(2021, 4, 30):
        fails.append(f"HGK1 first notice {last_day('HGK1', 'HG', '2021-03-10')}")
    # sign in money and the position rule (Amendment 1)
    if position(-1, np.array([-0.001]))[0] != 1:
        fails.append("position rule: rho < 0 and a stronger-yuan surprise (s < 0) is not a long")
    pnl = position(-1, np.array([-0.001]))[0] * (0.0001 * CELLS["AUD"]["mult"])
    if not math.isclose(pnl, 1.0):
        fails.append(f"sign in money: a long M6A on +0.0001 pays {pnl}, not +$1")
    if not math.isclose(-1 * 0.0005 * CELLS["COPPER"]["mult"], -1.25):
        fails.append("sign in money: a short MHG on +0.0005 does not lose $1.25")
    # the walk-forward residual and its lag audit
    rng = np.random.default_rng(769)
    n = 600
    Xs = np.column_stack([np.ones(n), rng.normal(0, 0.003, (n, len(BASKET)))])
    beta = np.array([0.0002, -0.25, -0.12, -0.05, -0.04, -0.03, -0.02])
    ys = Xs @ beta + rng.normal(0, 0.0005, n)
    rs = walk_forward(Xs, ys)
    try:
        lag_audit(Xs, ys, rs, list(range(WF, WF + 30)))
    except D769Error as ex:
        fails.append(f"lag audit raised on the truth: {ex}")
    expect_raise(lambda: lag_audit(Xs, ys, rs, list(range(WF, WF + 30)), include_self=True), "the lag audit when day t is in its own window")
    if not np.all(np.isnan(rs[:WF])) or not np.all(np.isfinite(rs[WF:])):
        fails.append("walk-forward burn-in wrong")
    # the guards
    good = pd.DataFrame({"root": "6A", "contract": "6AH1", "ts": np.array([1_600_000_000, 1_600_000_060]) * 1_000_000_000,
                         "day": "2020-09-13", "open": [0.73, 0.73], "close": [0.73, 0.73]})
    try:
        Bars(good, "6A")
    except D769Error as ex:
        fails.append(f"Bars raised on good input: {ex}")
    expect_raise(lambda: Bars(good.assign(ts=good["ts"] + (SEAL_NS - int(good["ts"].min()))), "6A"), "the seal on a 2024 bar")
    expect_raise(lambda: Bars(good.assign(ts=good["ts"] // 1000), "6A"), "the nanosecond guard")
    try:
        check_units(np.array([0.70, 0.72]), "6A"), check_units(np.array([3.1, 3.3]), "HG")
    except D769Error as ex:
        fails.append(f"the units guard raised on good prices: {ex}")
    expect_raise(lambda: check_units(np.array([70.0, 72.0]), "6A"), "the units guard on AUD in cents")
    expect_raise(lambda: check_units(np.array([310.0, 330.0]), "HG"), "the units guard on copper in cents")
    # delivery: an FX front on its last trading day is caught
    if business_days_between(dt.date(2021, 3, 15), last_day("6AH1", "6A", "2021-03-15")) > 2:
        fails.append("the delivery window does not catch a 6A front on its last trading day")
    # rotation offset 0 and the synthetic G1
    s = rng.normal(0, 1, 1700)
    y = rng.normal(0, 1, 1700)
    g = rot_spearman(s, y)
    if not math.isclose(g["offset0"], g["rho"], abs_tol=1e-12):
        fails.append("rotation offset 0 != rho")
    planted = rot_spearman(s, -0.12 * s + y)
    if planted["p_two_sided"] >= 0.05:
        fails.append(f"a planted rho -0.12 did not pass (p {planted['p_two_sided']:.3f})")
    noise = sum(rot_spearman(rng.normal(0, 1, 1700), rng.normal(0, 1, 1700))["p_two_sided"] < 0.05 for _ in range(100))
    ar_pass = 0
    for _ in range(100):
        a = np.zeros(1700)
        e = rng.normal(0, 1, 1700)
        for t in range(1, 1700):
            a[t] = 0.9 * a[t - 1] + e[t]
        ar_pass += rot_spearman(a, rng.normal(0, 1, 1700))["p_two_sided"] < 0.05
    print(f"  synthetic G1 passes: noise {noise}/100, AR(1) 0.9 signal vs independent returns {ar_pass}/100")
    if noise > 10:
        fails.append(f"noise passed G1 {noise}/100")
    if ar_pass > 10:
        fails.append(f"an AR(1) signal passed G1 {ar_pass}/100")
    # top third is walk-forward (uses only prior |s|)
    ss = np.r_[np.full(300, 1.0), 100.0]
    if not top_third(ss)[-1] or top_third(np.r_[np.full(300, 1.0), 1.0])[-1]:
        fails.append("top-third threshold wrong")
    if fails:
        for x in fails:
            print("  FAIL:", x)
        print("[D769] selftest: FAILED")
        return 1
    print("[D769] selftest: all passed")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    gx = ap.add_mutually_exclusive_group(required=True)
    gx.add_argument("--selftest", action="store_true")
    gx.add_argument("--extract", action="store_true")
    gx.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else extract() if a.extract else run())

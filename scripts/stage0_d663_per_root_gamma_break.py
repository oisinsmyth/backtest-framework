"""D663 Stage 0: per root, does the opening-range break carry further when dealers are short gamma (H1), and does the
cash market's own signed flow at the open multiply it (H2)? Written after D663's design (b4d0d3d), committed before
its one run.

    uv run python scripts/stage0_d663_per_root_gamma_break.py --selftest
    uv run python scripts/stage0_d663_per_root_gamma_break.py --dry-run --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"
    uv run python scripts/stage0_d663_per_root_gamma_break.py --run --data-root "C:/Users/O/Desktop/Projects/Backtest Framework/data"

In-sample only: bars and A4's G through run_opening_v2.load_inputs (sealed at 2025-03-01); SqueezeMetrics GEX rows dated
before 2025-03-01 (and, per session, only the row dated BEFORE the session); Sierra market statistics read only to the
first record at or after 2025-03-01 00:00 ET (the binary search reads timestamps, never a value beyond the cut).
SqueezeMetrics data (licence: docs/research/licences/squeezemetrics-dix-gex.md) -- credited in the RESULT; no per-date
series is written to any tracked path, and the output JSON is guarded to hold coefficients and statistics only.

Per root r (ES, NQ): the break is D645's B3 (asserted equal to b3_trade); F = D x ln(P60 / P_entry) x 1e4, no stop.
g = -(gamma $ per 1%) / V20 x 100 (dealer SHORT gamma over the root's prior-20-session mean RTH dollar volume):
ES from SPX GEX (primary), NQ from its own options book (A4's G; primary) and from SPX GEX (secondary).
Shocks, signed by D, over 09:30 -> the signal bar's close: TICK-SP / TICK-NQ (primary; the window's mean of
minute-sampled TICK over the sd of the same window's mean across the prior 20 sessions) and (UVOL - DVOL) /
(UVOL + DVOL) on NYSE / NASDAQ (secondary), after Gate F (the files' format, read with no outcome).
H1: F = a + b1 g; H2: F = a + b1 g + b2 s + b3 g s (HAC lag 5). Purged (+/-10) enumerated rotation of g; the midday
placebo (range 12:00-12:29, breaks 12:30-13:59, shock 12:00 -> the signal bar); tails, eras, year counts against the
rotation's own year counts; the size claim; MDE and vault power. Writes data/stage0_d663_per_root_gamma_break.json.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import tempfile
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d662_gamma_product as S  # noqa: E402  (the break, F, the batched OLS, HAC, D662's audits)

OUT = REPO / "data" / "stage0_d663_per_root_gamma_break.json"
SC_DATA = Path(r"C:\SierraChart\Data")
RESERVED_FROM = "2025-03-01"
FIRST = "2016-01-04"
MULT = {"ES": 50.0, "NQ": 20.0}
SHOCK_SYMS = {"ES": {"tick": "TICK-SP", "up": "UVOL-NYSE", "dn": "DVOL-NYSE"},
              "NQ": {"tick": "TICK-NQ", "up": "UVOL-NASDAQ", "dn": "DVOL-NASDAQ"}}
MIN0, MIN1 = 560, 840  # minute-of-day kept: 09:20 .. 13:59 (09:20-09:29 for the opening value)
REC = np.dtype([("dt", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"),
                ("v", "<u4"), ("bv", "<u4"), ("av", "<u4")])
SC_EPOCH = pd.Timestamp("1899-12-30", tz="UTC")
DAY_US = 86_400_000_000
ET = "America/New_York"
MAX_LIST = 60  # the licence guard: no list in the output may be a per-date series
Z = 1.959964


class D663Error(RuntimeError):
    pass


def hm(s: str) -> int:
    return int(s[:2]) * 60 + int(s[3:])


# ================================================================================ Sierra market statistics
def sc_us(ts: pd.Timestamp) -> int:
    return int((ts.tz_convert("UTC") - SC_EPOCH) / pd.Timedelta(microseconds=1))


def extract(path: str, cut_et: str = RESERVED_FROM) -> dict[str, Any]:
    """Minute-sampled values of a Sierra market-statistics .scid, in-sample only: the last record's close in each ET
    minute 09:20-13:59, per session. Reads records only before `cut_et` 00:00 ET."""
    m = np.memmap(path, dtype=REC, mode="r", offset=56)
    dt = m["dt"]
    lo = sc_us(pd.Timestamp("2015-11-01", tz=ET))
    hi = sc_us(pd.Timestamp(cut_et, tz=ET))
    i0, i1 = (int(x) for x in np.searchsorted(dt, [lo, hi]))
    dts = np.asarray(dt[i0:i1])
    vals = np.asarray(m["c"][i0:i1]).astype(np.float64)
    if len(dts) and dts.max() >= hi:
        raise D663Error(f"{path}: a record at or after the cut was read")
    day = dts // DAY_US
    ud, inv = np.unique(day, return_inverse=True)
    noon = pd.DatetimeIndex(SC_EPOCH + pd.to_timedelta(ud, unit="D") + pd.Timedelta(hours=16))
    off = np.array([int(t.tz_convert(ET).utcoffset() / pd.Timedelta(microseconds=1)) for t in noon], dtype=np.int64)
    et = dts + off[inv]
    sday = et // DAY_US
    minute = (et % DAY_US) // 60_000_000
    keep = (minute >= MIN0) & (minute < MIN1)
    sday, minute, vals = sday[keep], minute[keep], vals[keep]
    key = sday * 1440 + minute
    last = np.r_[np.flatnonzero(key[1:] != key[:-1]), len(key) - 1] if len(key) else np.array([], dtype=int)
    k_last, v_last = key[last], vals[last]
    sessions_d, s_idx = np.unique(k_last // 1440, return_inverse=True)
    M = np.full((len(sessions_d), MIN1 - MIN0), np.nan)
    M[s_idx, (k_last % 1440) - MIN0] = v_last
    names = [(SC_EPOCH + pd.Timedelta(days=int(d))).strftime("%Y-%m-%d") for d in sessions_d]
    return {"sessions": names, "M": M, "records": int(i1 - i0)}


def gate_f(ex: dict[str, Any], kind: str) -> dict[str, Any]:
    """Format, with no outcome read: coverage (share of 09:30-11:29 minutes holding a record, per session) and, for
    volume, whether the series is cumulative within the session and whether it resets at the open."""
    M = ex["M"]
    a, b = hm("09:30") - MIN0, hm("11:30") - MIN0
    cov = np.isfinite(M[:, a:b]).mean(axis=1)
    out: dict[str, Any] = {"sessions": len(M), "coverage_median": float(np.median(cov)),
                           "sessions_below_90pct": int((cov < 0.9).sum())}
    if kind == "vol":
        F = pd.DataFrame(M[:, a:]).ffill(axis=1).to_numpy()
        d = np.diff(F, axis=1)
        mono = np.nanmin(np.where(np.isfinite(d), d, 0.0), axis=1) >= 0
        first, lastv = F[:, 0], F[:, -1]
        ratio = np.where(lastv > 0, first / lastv, np.nan)
        out.update(cumulative_share=float(mono.mean()), open_to_1359_ratio_median=float(np.nanmedian(ratio)))
        out["cumulative"] = bool(out["cumulative_share"] >= 0.95)
        out["resets_at_open"] = bool(out["open_to_1359_ratio_median"] < 0.10)
    out["usable"] = bool(kind != "vol" or out["cumulative"])
    out["cov"] = cov  # dropped before the output is written
    return out


def ffill_rows(M: np.ndarray) -> np.ndarray:
    return pd.DataFrame(M).ffill(axis=1).to_numpy()


# ================================================================================ per-root frame
def root_frame(b: pd.DataFrame, tab: pd.DataFrame, r: str) -> pd.DataFrame:
    x = b[(b["root"] == r) & (b["hhmm"] >= "09:30") & (b["hhmm"] <= "15:59")]
    dv = (x["close"] * x["volume"] * MULT[r]).groupby(x["session"]).sum()
    close = x.groupby("session")["close"].last()
    d = tab.copy()
    d["dv"] = dv.reindex(d.index)
    d["sig20"] = (np.log(close / close.shift(1)) * 1e4).shift(1).rolling(20, min_periods=15).std().reindex(d.index)
    d["V20"] = d["dv"].shift(1).rolling(20, min_periods=15).mean()
    ok = (d["usable"] & (d.index >= FIRST) & (d.index < RESERVED_FROM)
          & np.isfinite(d[["sig20", "V20", "hi_10:00", "lo_10:00", "prior_close", "open"]]).all(axis=1))
    return d[ok]


def gex_prior(gex: pd.Series, sessions: pd.Index) -> pd.Series:
    """The GEX row dated strictly before each session (a row for day t is computed from day t's close)."""
    dates = gex.index.to_numpy()
    pos = np.searchsorted(dates, sessions.to_numpy(), side="left") - 1
    v = np.where(pos >= 0, gex.to_numpy(float)[np.clip(pos, 0, None)], np.nan)
    return pd.Series(v, index=sessions)


def gex_prior_second_path(gex: pd.Series, sessions: pd.Index) -> pd.Series:
    out = {}
    for s in sessions:
        prev = gex[gex.index < s]
        out[s] = float(prev.iloc[-1]) if len(prev) else np.nan
    return pd.Series(out).reindex(sessions)


def gex_lag_audit(gex: pd.Series, sessions: pd.Index, mapper: Callable = None) -> None:
    got = (mapper or gex_prior)(gex, sessions).to_numpy(float)
    if not np.allclose(got, gex_prior_second_path(gex, sessions).to_numpy(float), equal_nan=True):
        raise D663Error("lag: GEX is not the row dated before the session")


def assert_sealed(ex: dict[str, Any]) -> None:
    if any(s >= RESERVED_FROM for s in ex["sessions"]):
        raise D663Error("seal: an extracted session is on or after 2025-03-01")


def breaks(d: pd.DataFrame, bars: dict, r: str, window: tuple[str, str, str, str]) -> pd.DataFrame:
    a, b_, f, l = (hm(t) for t in window)
    out = []
    for s in d.index:
        bb = bars.get((r, s))
        if bb is None:
            continue
        lh = (float(d.at[s, "lo_10:00"]), float(d.at[s, "hi_10:00"])) if window == S.MORNING else S.range_of(bb, a, b_)
        if lh is None:
            continue
        br = S.find_break(bb, lh, f, l)
        if br is None:
            continue
        D, eb, entry = br
        out.append({"session": s, "D": D, "eb": eb, "entry": entry, "F": S.follow(bb, eb, D, entry)})
    return pd.DataFrame(out).set_index("session")


def b3_check(r: str, rows: pd.DataFrame, d: pd.DataFrame, bars: dict, R: Any) -> None:
    """The break, its direction and its entry equal D645's b3_trade on every session, for any root."""
    for s_, rec in rows.iterrows():
        t = R.b3_trade(bars[(r, s_)], "10:00", float(d.at[s_, "hi_10:00"]), float(d.at[s_, "lo_10:00"]))
        if t is None or t[3] != rec["D"] or t[0] != rec["entry"]:
            raise D663Error(f"B3: {r} {s_} differs from b3_trade")


def right_quantity_f(r: str, rows: pd.DataFrame, bars: dict) -> None:
    """F is measured from the entry, not from 10:00."""
    f10 = []
    for s_, rec in rows.iterrows():
        m, c = bars[(r, s_)]["m"], bars[(r, s_)]["c"]
        k10 = np.flatnonzero(m == hm("10:00"))
        f10.append(rec["D"] * math.log(c[np.flatnonzero(m <= rec["eb"] + 60)[-1]] / c[k10[0]]) * 1e4 if len(k10) else np.nan)
    f10 = np.array(f10)
    ok = np.isfinite(f10)
    if ok.any() and np.allclose(f10[ok], rows["F"].to_numpy(float)[ok]):
        raise D663Error(f"right quantity: {r}'s F from the entry equals F from 10:00")


def shocks(rows: pd.DataFrame, win_start: str, ex_tick: dict, ex_up: dict | None, ex_dn: dict | None,
           gates: dict, end_offset: int = 0) -> pd.DataFrame:
    """s_tick and s_vol per break row over [win_start, the signal bar's close) = minutes win_start .. eb - 1 + offset.
    end_offset = 1 is the lag canary (reads the entry bar's minute)."""
    a = hm(win_start) - MIN0
    out = pd.DataFrame(index=rows.index, columns=["s_tick", "s_vol"], dtype=float)
    # TICK: the window mean of minute samples, over the sd of the same window's mean across the prior 20 sessions
    tsess = pd.Index(ex_tick["sessions"])
    T = ffill_rows(ex_tick["M"])[:, a:]
    cov_ok = gates["tick"]["cov"] >= 0.9
    C = np.nancumsum(np.nan_to_num(T, nan=0.0), axis=1)
    N = np.cumsum(np.isfinite(T), axis=1)
    for s, rec in rows.iterrows():
        k = int(rec["eb"]) - hm(win_start) + end_offset  # minutes in the window
        i = tsess.get_indexer([s])[0]
        if i < 21 or k < 1 or k > T.shape[1] or not cov_ok[i]:
            continue
        mean_s = C[i, k - 1] / max(N[i, k - 1], 1)
        prior = C[i - 20:i, k - 1] / np.maximum(N[i - 20:i, k - 1], 1)
        sd = np.nanstd(prior, ddof=1)
        if np.isfinite(mean_s) and sd > 0:
            out.at[s, "s_tick"] = rec["D"] * mean_s / sd
    if ex_up is not None and ex_dn is not None and gates["up"]["usable"] and gates["dn"]["usable"]:
        U, Dn = ffill_rows(ex_up["M"]), ffill_rows(ex_dn["M"])
        us, ds = pd.Index(ex_up["sessions"]), pd.Index(ex_dn["sessions"])
        o = hm("09:30") - MIN0 - 1  # the value just before 09:30 (09:29's last record)
        for s, rec in rows.iterrows():
            iu, idn = us.get_indexer([s])[0], ds.get_indexer([s])[0]
            if iu < 0 or idn < 0:
                continue
            j = int(rec["eb"]) - 1 + end_offset - MIN0
            if win_start == "09:30":
                u0 = 0.0 if gates["up"]["resets_at_open"] else U[iu, o]
                d0 = 0.0 if gates["dn"]["resets_at_open"] else Dn[idn, o]
            else:
                u0, d0 = U[iu, hm(win_start) - MIN0 - 1], Dn[idn, hm(win_start) - MIN0 - 1]
            up, dn = U[iu, j] - u0, Dn[idn, j] - d0
            if np.isfinite(up) and np.isfinite(dn) and up + dn > 0:
                out.at[s, "s_vol"] = rec["D"] * (up - dn) / (up + dn)
    return out


# ================================================================================ statistics
def slope_batch(y: np.ndarray, Gm: np.ndarray) -> np.ndarray:
    gc = Gm - Gm.mean(axis=1, keepdims=True)
    return (gc * (y - y.mean())).sum(axis=1) / (gc ** 2).sum(axis=1)


def rotations(cal: list[str], g_all: pd.Series, idx: pd.Index) -> np.ndarray:
    T = len(cal)
    pos = pd.Index(cal).get_indexer(idx)
    if (pos < 0).any():
        raise D663Error("a row's session is outside the gamma calendar")
    gv = g_all.reindex(cal).to_numpy(float)
    offs = np.array([o for o in range(T) if o == 0 or min(o, T - o) > S.PURGE])
    return gv[(pos[None, :] + offs[:, None]) % T]


def h1(rows: pd.DataFrame, gcol: str, cal: list[str], g_all: pd.Series) -> dict[str, Any]:
    r = rows[np.isfinite(rows[gcol])]
    y, g = r["F"].to_numpy(float), r[gcol].to_numpy(float)
    f = S.hac(y, g[:, None])
    Gm = rotations(cal, g_all, r.index)
    B = slope_batch(y, Gm)
    if abs(B[0] - f.params[1]) > 1e-9 * max(1.0, abs(f.params[1])):
        raise D663Error("H1: the batched slope at offset 0 differs from statsmodels")
    null = B[1:]
    idx = r.index.to_series()
    yrs = sorted({s[:4] for s in r.index})
    yr_obs, yr_null = 0, np.zeros(len(null), dtype=int)
    by_year = {}
    for yr in yrs:
        m = idx.str.startswith(yr).to_numpy()
        if m.sum() < 30:
            continue
        sl = slope_batch(y[m], Gm[:, m])
        by_year[yr] = float(sl[0])
        yr_obs += int(sl[0] > 0)
        yr_null += (sl[1:] > 0).astype(int)
    ex = ~idx.between("2020-02-01", "2020-04-30").to_numpy()
    top = np.abs(y) >= np.quantile(np.abs(y), 0.99)
    return {"n": int(len(y)), "b1": float(f.params[1]), "t": float(f.tvalues[1]), "se": float(f.bse[1]),
            "p_one_sided": float(stats.norm.sf(f.tvalues[1])), "mde80": float((Z + 0.841621) * f.bse[1]),
            "rotation": {"offsets": int(len(null)), "rank": float((null < f.params[1]).mean()),
                         "p50": float(np.median(null)), "p95": float(np.quantile(null, 0.95))},
            "ex_covid": float(slope_batch(y[ex], g[ex][None, :])[0]),
            "ex_top1pct_absF": float(slope_batch(y[~top], g[~top][None, :])[0]),
            "by_year": by_year, "years_positive": yr_obs, "years": len(by_year),
            "years_positive_null_p50": float(np.median(yr_null)), "years_positive_null_p95": float(np.quantile(yr_null, 0.95)),
            "pre_0dte": float(slope_batch(y[(idx < "2022-05-16").to_numpy()], g[(idx < "2022-05-16").to_numpy()][None, :])[0]),
            "post_0dte": float(slope_batch(y[(idx >= "2022-05-16").to_numpy()], g[(idx >= "2022-05-16").to_numpy()][None, :])[0])}


def h2(rows: pd.DataFrame, gcol: str, scol: str, cal: list[str], g_all: pd.Series) -> dict[str, Any]:
    r = rows[np.isfinite(rows[gcol]) & np.isfinite(rows[scol])]
    y, g, s = r["F"].to_numpy(float), r[gcol].to_numpy(float), r[scol].to_numpy(float)
    f = S.hac(y, np.column_stack([g, s, g * s]))
    b = S.batched_b(y, s, g[None, :])[0]
    if not np.allclose(b, f.params, rtol=1e-9, atol=1e-12):
        raise D663Error("H2: the batched OLS differs from statsmodels")
    Gm = rotations(cal, g_all, r.index)
    B3 = S.batched_b(y, s, Gm)[:, 3]
    null = B3[1:]
    pw = {}
    for lab, m in (("short", g > 0), ("long", g <= 0)):
        ff = S.hac(y[m], s[m][:, None])
        pw[lab] = {"n": int(m.sum()), "slope": float(ff.params[1]), "se": float(ff.bse[1])}
    idx = r.index.to_series()
    ex = ~idx.between("2020-02-01", "2020-04-30").to_numpy()
    un = S.hac(y, np.column_stack([g, s, g * np.abs(s)]))
    return {"n": int(len(y)), "b3": float(b[3]), "t3": float(f.tvalues[3]), "se3": float(f.bse[3]),
            "p3_one_sided": float(stats.norm.sf(f.tvalues[3])), "mde80_b3": float((Z + 0.841621) * f.bse[3]),
            "b_all": [float(x) for x in b], "t_all": [float(x) for x in f.tvalues],
            "rotation": {"offsets": int(len(null)), "rank": float((null < b[3]).mean()),
                         "p50": float(np.median(null)), "p95": float(np.quantile(null, 0.95))},
            "piecewise": pw, "short_steeper": bool(pw["short"]["slope"] > pw["long"]["slope"]),
            "ex_covid_b3": float(S.batched_b(y[ex], s[ex], g[ex][None, :])[0, 3]),
            "unsigned_product_b3": float(un.params[3])}


def size_claim(rows: pd.DataFrame, gcol: str, gdcol: str, scol: str | None) -> dict[str, Any]:
    r = rows[np.isfinite(rows[gcol]) & (np.isfinite(rows[scol]) if scol else True)]
    move = np.abs(np.log(r["entry"] / r["open"])) * 100
    sgn = np.sign(r[gcol]) if scol is None else np.sign(r[gcol] * r[scol])
    I = sgn * r["sig20"] * np.sqrt(r[gdcol].abs() * move / r["V20"])
    f = S.hac(r["F"].to_numpy(float), I.to_numpy(float)[:, None])
    ci = f.conf_int(alpha=0.10)[1]
    return {"beta": float(f.params[1]), "ci90": [float(ci[0]), float(ci[1])], "powered_null_below_half": bool(ci[1] < 0.5),
            "mean_abs_push_bp": float(np.nanmean(np.abs(I)))}


def vault_power(b: float, se: float, n_in_sessions: int) -> float:
    se_v = se * math.sqrt(n_in_sessions / 390)
    return float(stats.norm.sf(Z - b / se_v)) if se_v > 0 else float("nan")


def holm(p: dict[str, float]) -> dict[str, float]:
    order, out, run = sorted(p, key=p.get), {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (len(order) - i) * p[k]))
        out[k] = run
    return out


# ================================================================================ the licence guard
def licence_guard(doc: Any, path: str = "") -> None:
    """The output may hold coefficients, statistics and verdicts only: any list longer than MAX_LIST, or any mapping
    keyed by dates with more than MAX_LIST entries, is a per-date series and raises."""
    if isinstance(doc, dict):
        dated = [k for k in doc if isinstance(k, str) and len(k) == 10 and k[4] == "-" and k[7] == "-"]
        if len(dated) > MAX_LIST:
            raise D663Error(f"licence: a dated series at {path or '<root>'}")
        for k, v in doc.items():
            licence_guard(v, f"{path}/{k}")
    elif isinstance(doc, (list, tuple)):
        if len(doc) > MAX_LIST:
            raise D663Error(f"licence: a list of {len(doc)} at {path}")
        for i, v in enumerate(doc):
            licence_guard(v, f"{path}[{i}]")


# ================================================================================ jobs
def analyse(job: tuple) -> dict[str, Any]:
    kind, name, rows, gcol, gdcol, scol, cal, g_all = job
    if kind == "h1":
        return {"name": name, "res": h1(rows, gcol, cal, g_all), "claim": size_claim(rows, gcol, gdcol, None)}
    return {"name": name, "res": h2(rows, gcol, scol, cal, g_all), "claim": size_claim(rows, gcol, gdcol, scol)}


def extract_job(args: tuple[str, str]) -> tuple[str, dict[str, Any]]:
    sym, path = args
    return sym, extract(path)


def build(data_root: Path, dry: bool) -> dict[str, Any]:
    t_start = time.time()
    V = S.load_v2()
    R = V.R
    b, use, Gd = V.load_inputs(data_root, dry)
    tabs = R.session_table(b, use)
    bars = R.bar_arrays(b)
    rng = np.random.default_rng(663)
    # SPX GEX (prior row only)
    if dry:
        gex = pd.Series(rng.normal(3e9, 4e9, 3000), index=pd.bdate_range("2014-01-01", periods=3000).strftime("%Y-%m-%d"))
    else:
        dix = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", encoding="utf-8", dtype={"date": str})
        dix = dix[dix["date"] < RESERVED_FROM]
        gex = dix.set_index("date")["gex"].astype(float).sort_index()
    # Sierra market statistics, in parallel processes
    syms = sorted({v for r in SHOCK_SYMS for v in SHOCK_SYMS[r].values()})
    if dry:
        ex = {}
        for sym in syms:
            sess = sorted(set(b["session"]))
            M = rng.normal(0, 300, (len(sess), MIN1 - MIN0))
            if "VOL" in sym:
                M = np.cumsum(np.abs(M), axis=1)
            ex[sym] = {"sessions": sess, "M": M, "records": int(M.size)}
    else:
        # three at a time: a 3.9 GB file's in-sample slice peaks near 3 GB of arrays, and 17.5 GB was free (2026-09-29)
        with ProcessPoolExecutor(max_workers=min(3, len(syms))) as pool:
            ex = dict(pool.map(extract_job, [(s, str(SC_DATA / f"{s}.scid")) for s in syms]))
        for e_ in ex.values():
            assert_sealed(e_)
    gates = {sym: gate_f(ex[sym], "vol" if "VOL" in sym else "tick") for sym in syms}
    doc_gates = {sym: {k: v for k, v in gt.items() if k != "cov"} for sym, gt in gates.items()}
    jobs, frames, sessions_in, F_dist, shock_cov = [], {}, {}, {}, {}
    for r in ("ES", "NQ"):
        d = root_frame(b, tabs[r], r)
        gd_spx = gex_prior(gex, d.index)
        gex_lag_audit(gex, d.index[:: max(1, len(d) // 40)])
        d["gd_spx"] = gd_spx
        d["g_spx"] = -d["gd_spx"] / d["V20"] * 100
        d["gd_own"] = Gd[r].reindex(d.index) * MULT[r] * d["prior_close"] ** 2 * 0.01
        d["g_own"] = -d["gd_own"] / d["V20"] * 100
        frames[r] = d
        sessions_in[r] = len(d)
        sy = SHOCK_SYMS[r]
        g_tick = {"tick": gates[sy["tick"]], "up": gates[sy["up"]], "dn": gates[sy["dn"]]}
        for win, start, lab in ((S.MORNING, "09:30", "morning"), (S.MIDDAY, "12:00", "midday")):
            rows = breaks(d, bars, r, win)
            if win == S.MORNING:
                b3_check(r, rows, d, bars, R)
                right_quantity_f(r, rows, bars)
            sh = shocks(rows, start, ex[sy["tick"]], ex[sy["up"]], ex[sy["dn"]], g_tick)
            if lab == "morning" and not dry:
                canary = shocks(rows, start, ex[sy["tick"]], ex[sy["up"]], ex[sy["dn"]], g_tick, end_offset=1)
                if np.allclose(canary["s_tick"].to_numpy(float), sh["s_tick"].to_numpy(float), equal_nan=True):
                    raise D663Error("lag: the shock does not change when the window reads the entry bar")
            rows = rows.join(sh).join(d[["g_spx", "g_own", "gd_spx", "gd_own", "sig20", "V20", "open"]])
            if lab == "morning":
                F_dist[r] = S.dist(rows["F"].to_numpy(float))
                shock_cov[r] = {"s_tick_finite": int(np.isfinite(rows["s_tick"]).sum()),
                                "s_vol_finite": int(np.isfinite(rows["s_vol"]).sum()), "breaks": int(len(rows))}
            primary_g = "g_spx" if r == "ES" else "g_own"
            primary_gd = "gd_spx" if r == "ES" else "gd_own"
            cal = list(d.index)
            jobs.append(("h1", f"{r}_{lab}_H1", rows, primary_g, primary_gd, None, cal, d[primary_g]))
            jobs.append(("h2", f"{r}_{lab}_H2", rows, primary_g, primary_gd, "s_tick", cal, d[primary_g]))
            # D663 s.2 Gate F: a shock whose meaning is not established is dropped before any outcome is read.
            # (2026-09-29: UVOL/DVOL are advancing/declining-ISSUE volume, a state that moves as stocks cross
            # unchanged, not a cumulative flow; the first run scheduled this job anyway and crashed on its empty
            # column before any statistic was returned.)
            if lab == "morning" and g_tick["up"]["usable"] and g_tick["dn"]["usable"]:
                jobs.append(("h2", f"{r}_{lab}_H2_vol", rows, primary_g, primary_gd, "s_vol", cal, d[primary_g]))
                if r == "NQ":
                    jobs.append(("h1", f"{r}_{lab}_H1_spx", rows, "g_spx", "gd_spx", None, cal, d["g_spx"]))
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=min(len(jobs), 8)) as pool:
        res = {o["name"]: o for o in pool.map(analyse, jobs)}
    fan_s = time.time() - t0
    for k, v in res.items():  # right quantity: the signed product is not the unsigned one
        if k.endswith("H2") and v["res"]["b3"] == v["res"]["unsigned_product_b3"]:
            raise D663Error(f"right quantity: {k}'s signed b3 equals the unsigned product's")
    # verdicts
    p1 = {r: res[f"{r}_morning_H1"]["res"]["p_one_sided"] for r in ("ES", "NQ")}
    p2 = {r: res[f"{r}_morning_H2"]["res"]["p3_one_sided"] for r in ("ES", "NQ")}
    hp1, hp2 = holm(p1), holm(p2)
    verdict = {}
    for r in ("ES", "NQ"):
        m1, pl1 = res[f"{r}_morning_H1"]["res"], res[f"{r}_midday_H1"]["res"]
        c1 = {"b1_positive_holm": bool(m1["b1"] > 0 and hp1[r] < 0.05), "rotation_rank_ge_095": bool(m1["rotation"]["rank"] >= 0.95),
              "placebo_abs_t_below_2": bool(abs(pl1["t"]) < 2), "positive_ex_covid": bool(m1["ex_covid"] > 0)}
        m2, pl2 = res[f"{r}_morning_H2"]["res"], res[f"{r}_midday_H2"]["res"]
        c2 = {"b3_positive_holm": bool(m2["b3"] > 0 and hp2[r] < 0.05), "rotation_rank_ge_095": bool(m2["rotation"]["rank"] >= 0.95),
              "placebo_abs_t_below_2": bool(abs(pl2["t3"]) < 2), "positive_ex_covid": bool(m2["ex_covid_b3"] > 0),
              "short_steeper": m2["short_steeper"]}
        verdict[r] = {"H1": {"holm_p": hp1[r], "checks": c1, "verdict": "SUPPORTED" if all(c1.values()) else "NOT SUPPORTED",
                             "vault_power": vault_power(m1["b1"], m1["se"], sessions_in[r])},
                      "H2": {"holm_p": hp2[r], "checks": c2, "verdict": "SUPPORTED" if all(c2.values()) else "NOT SUPPORTED",
                             "vault_power": vault_power(m2["b3"], m2["se3"], sessions_in[r])}}
    pred = {"1_H1_ES_right_sign_not_supported": bool(res["ES_morning_H1"]["res"]["b1"] > 0 and verdict["ES"]["H1"]["verdict"] == "NOT SUPPORTED"),
            "2_H1_NQ_not_supported": verdict["NQ"]["H1"]["verdict"] == "NOT SUPPORTED",
            "3_H2_both_not_supported": all(verdict[r]["H2"]["verdict"] == "NOT SUPPORTED" for r in ("ES", "NQ")),
            "4_placebos_inside_noise": all(abs(res[f"{r}_midday_H1"]["res"]["t"]) < 2 and abs(res[f"{r}_midday_H2"]["res"]["t3"]) < 2
                                           for r in ("ES", "NQ")),
            "5_any_pass_under_half_vault_power": all(verdict[r][h]["vault_power"] < 0.5 for r in ("ES", "NQ") for h in ("H1", "H2")
                                                     if verdict[r][h]["verdict"] == "SUPPORTED")}
    doc = {"spec": "D663 (b4d0d3d)", "dry_run": dry, "credit": "dealer gamma (GEX): SqueezeMetrics",
           "gates": doc_gates, "sessions_in_frame": sessions_in, "F_morning": F_dist, "shock_coverage": shock_cov,
           "dropped_by_gate_f": sorted(s for s, gt in gates.items() if not gt["usable"]),
           "results": {k: {"res": v["res"], "claim": v["claim"]} for k, v in res.items()},
           "verdict": verdict, "predictions": pred,
           "speed": {"jobs": len(jobs), "fanout_wall_s": round(fan_s, 2)},
           "runtime_min": round((time.time() - t_start) / 60, 2)}
    licence_guard(doc)
    return doc


# ================================================================================ selftest
def selftest() -> int:
    fired = []

    def must_raise(name: str, fn: Callable[[], Any]) -> None:
        try:
            fn()
        except (D663Error, S.D662Error):
            fired.append(name)
            return
        raise SystemExit(f"SELFTEST FAILED: {name} did not raise")

    # D662's sign and null audits, reused
    S.sign_audit()
    must_raise("sign-flipped", lambda: S.sign_audit(lambda bb, eb, D, e, horizon=60: -S.follow(bb, eb, D, e, horizon)))
    S.null_exactness()
    must_raise("null-drops-product", lambda: S.null_exactness(lambda y, s, Gm: np.concatenate(
        [S.batched_b(y, s, Gm)[:, :3], np.zeros((Gm.shape[0], 1))], axis=1)))
    # GEX: prior row only
    gex = pd.Series([1.0, 2.0, 3.0, 4.0], index=["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"])
    sess = pd.Index(["2020-01-03", "2020-01-06", "2020-01-07"])
    gex_lag_audit(gex, sess)
    must_raise("gex-same-day-canary", lambda: gex_lag_audit(gex, sess, mapper=lambda g, s: g.reindex(s)))
    # the Sierra extraction on a synthetic .scid, and the vault cut
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "SYN.scid"
        ts = pd.date_range("2024-06-03 09:25", "2024-06-03 11:00", freq="30s", tz=ET).append(
            pd.date_range("2025-03-03 09:30", periods=5, freq="1min", tz=ET))
        rec = np.zeros(len(ts), dtype=REC)
        rec["dt"] = [sc_us(t) for t in ts]
        rec["c"] = np.arange(len(ts), dtype=np.float32)
        with open(p, "wb") as fh:
            fh.write(b"\0" * 56)
            fh.write(rec.tobytes())
        e = extract(str(p))
        if e["sessions"] != ["2024-06-03"]:
            raise SystemExit(f"SELFTEST FAILED: extraction read past the cut or lost the session: {e['sessions']}")
        # 09:30's minute holds the value at 09:30:30 (index 11), the last record in that minute
        if e["M"][0, hm("09:30") - MIN0] != 11.0:
            raise SystemExit(f"SELFTEST FAILED: minute sampling is wrong ({e['M'][0, hm('09:30') - MIN0]})")
        assert_sealed(e)
        must_raise("vault-cut", lambda: assert_sealed(extract(str(p), cut_et="2025-03-04")))
        del e
    # the shock's lag canary: the window that reads the entry bar changes the shock
    rows = pd.DataFrame({"D": [1], "eb": [hm("10:06")]}, index=["2020-02-03"])
    sessions = [f"2020-01-{i:02d}" for i in range(1, 32)] + ["2020-02-03"]
    M = np.tile(np.arange(MIN1 - MIN0, dtype=float), (len(sessions), 1)) + np.arange(len(sessions))[:, None]
    ext = {"sessions": sessions, "M": M}
    gts = {"tick": {"cov": np.ones(len(sessions))}, "up": {"usable": False}, "dn": {"usable": False}}
    a_ = shocks(rows, "09:30", ext, None, None, gts)
    b_ = shocks(rows, "09:30", ext, None, None, gts, end_offset=1)
    if np.allclose(a_["s_tick"].to_numpy(float), b_["s_tick"].to_numpy(float), equal_nan=True):
        raise SystemExit("SELFTEST FAILED: the shock does not depend on its window's end")
    fired.append("shock-window-canary")
    # B3 reproduction and right quantity, per root (NQ here), with D645's own b3_trade on synthetic bars
    R = S.load_v2().R
    mm = np.arange(hm("09:30"), hm("12:00"))
    cc = np.where(mm < hm("10:00"), 100.0, 100.0 + 0.02 * (mm - hm("10:00")) + 0.3) + 0.01 * np.sin(mm)
    bb = {"m": mm, "o": cc, "h": cc + 0.05, "l": cc - 0.05, "c": cc}
    bars = {("NQ", "2020-01-02"): bb}
    dd = pd.DataFrame({"hi_10:00": [100.2], "lo_10:00": [99.8]}, index=["2020-01-02"])

    def brk(shift: int) -> pd.DataFrame:
        D, eb, e = S.find_break(bb, (99.8, 100.2), hm("10:00"), hm("11:29"), entry_shift=shift)
        return pd.DataFrame({"D": [D], "eb": [eb], "entry": [e], "F": [S.follow(bb, eb, D, e)]}, index=["2020-01-02"])

    b3_check("NQ", brk(1), dd, bars, R)
    must_raise("b3-entry-slip", lambda: b3_check("NQ", brk(0), dd, bars, R))
    right_quantity_f("NQ", brk(1), bars)
    r10 = brk(1)
    r10["F"] = r10["D"] * np.log(cc[np.flatnonzero(mm <= r10["eb"].iloc[0] + 60)[-1]] / cc[mm == hm("10:00")][0]) * 1e4
    must_raise("right-quantity-from-10", lambda: right_quantity_f("NQ", r10, bars))
    # the licence guard
    licence_guard({"b": [1.0, 2.0], "by_year": {"2016": 0.1}})
    must_raise("licence-list", lambda: licence_guard({"gex": list(range(100))}))
    must_raise("licence-dated", lambda: licence_guard({"g": {f"2019-{m:02d}-{d:02d}": 1.0
                                                             for m in range(1, 13) for d in range(1, 8)}}))
    # the Holm and vault-power arithmetic
    hp = holm({"a": 0.01, "b": 0.04})
    if not (abs(hp["a"] - 0.02) < 1e-12 and abs(hp["b"] - 0.04) < 1e-12):
        raise SystemExit("SELFTEST FAILED: Holm")
    print(f"selftest: {len(fired)} audits fire on broken inputs ({', '.join(fired)}); the clean cases pass")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--dry-run", action="store_true")
    g.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if a.run and OUT.exists():
        raise SystemExit("D663 Stage 0 runs once: its output exists")
    doc = build(a.data_root, dry=a.dry_run)
    if a.run:
        OUT.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    for r in ("ES", "NQ"):
        for h in ("H1", "H2"):
            k = f"{r}_morning_{h}"
            rr = doc["results"][k]["res"]
            coef, t = (rr["b1"], rr["t"]) if h == "H1" else (rr["b3"], rr["t3"])
            print(f"{'DRY ' if a.dry_run else ''}{k}: {doc['verdict'][r][h]['verdict']} (coef {coef:+.4f}, t {t:+.2f}, "
                  f"rank {rr['rotation']['rank']:.3f}, n {rr['n']})")
    print(f"gates: { {s: (v.get('usable'), round(v['coverage_median'], 3)) for s, v in doc['gates'].items()} }; "
          f"{doc['runtime_min']} min; {'written' if a.run else 'nothing written'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

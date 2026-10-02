"""D765 Stage 0: copper and silver at the China open. Spec: docs/decisions/D765-STAGE-0-PRE-REG-copper-and-silver-at-the-china-open.md.

    python scripts/stage0_d765_china_open.py --selftest      # SYSTEM interpreter (databento, pyarrow)
    python scripts/stage0_d765_china_open.py --extract       # HG / SI / GC / 6A front minutes, all hours, < 2024
    python scripts/stage0_d765_china_open.py --run --lines temp/d755_other_lines.csv

Every clock is a UTC minute. Beijing is UTC+8 with no DST, so 09:00 Beijing on trade date D is 01:00 UTC on D, which
is 21:00 ET (EDT) or 20:00 ET (EST) the evening before: inside CME trade date D's session. P(t) is the close of the
bar starting at t-1 (forward-filled within 3 minutes); an entry at t is the open of the first bar starting in
[t, t+3]. Nothing dated 2024-01-01 or later is decoded.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
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
SPEC = REPO / "docs" / "decisions" / "D765-STAGE-0-PRE-REG-copper-and-silver-at-the-china-open.md"
OUT = REPO / "data" / "stage0_d765_china_open.json"
TMP = Path(os.environ.get("D765_TMP", str(REPO / "temp" / "d765")))
CAL = REPO / "data" / "calendar" / "china_exchange_holidays.csv"
SEAL = "2024-01-01"
SEAL_NS = int(pd.Timestamp(SEAL, tz="UTC").value)
XLO_NS = int(pd.Timestamp("2015-12-01", tz="UTC").value)          # extraction start (the prior session of 2016-01-04)
LO, HI = "2016-01-04", "2023-12-29"
NY = ZoneInfo("America/New_York")
UTC = dt.timezone.utc
ROOTS = ("HG", "SI", "GC", "6A")
TICK = {"HG": 0.0005, "SI": 0.005, "GC": 0.10, "6A": 0.00005}       # full-size ticks (futures_costs.json)
CELLS: dict[str, dict[str, Any]] = {
    "mhg": dict(root="HG", mult=2500.0, cost=4.25, mtick_usd=1.25, night="01:00", primary=True),
    "sil": dict(root="SI", mult=1000.0, cost=8.00, mtick_usd=5.00, night="02:30", primary=True),
    "mgc": dict(root="GC", mult=10.0, cost=5.93, mtick_usd=1.00, night="02:30", primary=False),
}
WF, ROLL_N, FFILL, PRINT_TICKS = 250, 5, 3, 20
NIGHT_SUSPENDED = ("2020-02-03", "2020-05-06")                      # trade dates with no preceding SHFE night session
B_DRAWS, B_SEED = 2000, 765
WORKERS = 4


class D765Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D765Error(msg)


# ================================================================================ clocks (UTC minutes)
def dnum(day: str) -> int:
    return (dt.date.fromisoformat(day) - dt.date(1970, 1, 1)).days


def bj(day: str, hhmm: str) -> int:
    """Beijing wall time on `day` as a UTC minute (UTC+8, no DST)."""
    h, m = (int(v) for v in hhmm.split(":"))
    return dnum(day) * 1440 + (h - 8) * 60 + m


def et(day: str, hhmm: str) -> int:
    """New York wall time on `day` as a UTC minute, by zoneinfo."""
    d = dt.date.fromisoformat(day)
    h, m = (int(v) for v in hhmm.split(":"))
    u = dt.datetime(d.year, d.month, d.day, h, m, tzinfo=NY).astimezone(UTC)
    return int(u.timestamp() // 60)


def _nth_sunday(y: int, mo: int, n: int) -> dt.date:
    d = dt.date(y, mo, 1)
    d += dt.timedelta(days=(6 - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def edt_by_rule(utc_min: int) -> bool:
    """The statutory US rule (2007 on): EDT from 2nd Sunday of March 07:00 UTC to 1st Sunday of November 06:00 UTC."""
    t = dt.datetime(1970, 1, 1) + dt.timedelta(minutes=utc_min)
    s = dt.datetime.combine(_nth_sunday(t.year, 3, 2), dt.time(7))
    e = dt.datetime.combine(_nth_sunday(t.year, 11, 1), dt.time(6))
    return s <= t < e


def edt_by_zoneinfo(utc_min: int) -> bool:
    u = dt.datetime(1970, 1, 1, tzinfo=UTC) + dt.timedelta(minutes=utc_min)
    return u.astimezone(NY).utcoffset() == dt.timedelta(hours=-4)


def prev_weekday(day: str) -> str:
    d = dt.date.fromisoformat(day) - dt.timedelta(days=1)
    while d.weekday() >= 5:
        d -= dt.timedelta(days=1)
    return d.isoformat()


def add_days(day: str, k: int) -> str:
    return (dt.date.fromisoformat(day) + dt.timedelta(days=k)).isoformat()


def trade_day_of(ts_ns: np.ndarray) -> np.ndarray:
    """CME trade date (days since 1970): the ET date of wall time + 6 hours."""
    t = pd.to_datetime(ts_ns, utc=True).tz_convert(NY).tz_localize(None)
    wall = np.asarray((t - pd.Timestamp("1970-01-01")) // pd.Timedelta(minutes=1), dtype=np.int64)
    return ((wall + 360) // 1440).astype(np.int64)


# ================================================================================ calendar
def load_holidays() -> set[str]:
    with open(CAL, encoding="utf-8", newline="") as fh:
        return {r["date"] for r in csv.DictReader(fh)}


def holiday_blocks() -> list[list[str]]:
    with open(CAL, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    out: dict[str, list[str]] = {}
    for r in rows:
        out.setdefault(r["block"], []).append(r["date"])
    return [sorted(v) for v in out.values()]


# ================================================================================ extraction
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
                            "open": a["open"] * BH.PX, "high": a["high"] * BH.PX, "low": a["low"] * BH.PX,
                            "close": a["close"] * BH.PX, "volume": a["volume"].astype(np.int64)})
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
            parts.append(k[["root", "contract", "ts", "day", "open", "high", "low", "close", "volume"]].reset_index(drop=True))
    return pd.concat(parts, ignore_index=True) if parts else None


def extract() -> int:
    raw = sorted(p for d in sorted((MAIN_DATA / "raw" / "databento").glob("GLBX-*")) for p in d.glob("*.ohlcv-1m.dbn.zst"))
    print(f"{len(raw)} ohlcv-1m files", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(WORKERS) as ex:
        got = list(ex.map(_extract_file, [str(p) for p in raw]))
    # chunk == whole: one file (the largest yield) re-decoded serially must equal its process result bit for bit
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


# ================================================================================ the bar arrays
def load_root(r: str) -> dict[str, Any]:
    b = pd.read_parquet(TMP / f"raw_{r}.parquet")
    need(bool((b["ts"] > 10**18).all()), "units: a timestamp is not in nanoseconds")
    need(bool((b["ts"] < SEAL_NS).all()) and bool((b["day"] < SEAL).all()), f"seal: a {r} bar on or after 2024")
    need(bool(b["ts"].is_monotonic_increasing) and not b["ts"].duplicated().any(), f"{r}: bars not strictly ordered")
    return arrays_from(b, r)


def arrays_from(b: pd.DataFrame, r: str) -> dict[str, Any]:
    S = (b["ts"].to_numpy(np.int64) // 60_000_000_000).astype(np.int64)
    O, C = b["open"].to_numpy(float), b["close"].to_numpy(float)
    codes, uniq = pd.factorize(b["contract"])
    thr = PRINT_TICKS * TICK[r] - 1e-9
    Cp, Cn = np.r_[np.nan, C[:-1]], np.r_[C[1:], np.nan]
    iso_c = (np.abs(C - Cp) >= thr) & (np.abs(C - Cn) >= thr)
    iso_o = (np.abs(O - Cp) >= thr) & (np.abs(O - C) >= thr)
    return {"root": r, "S": S, "O": O, "C": C, "K": codes.astype(np.int32), "contracts": list(uniq), "iso_c": iso_c,
            "iso_o": iso_o, "day": b["day"].to_numpy(), "df": b}


def p_at(R: dict[str, Any], t: int) -> int | None:
    i = int(np.searchsorted(R["S"], t - 1, side="right")) - 1
    return i if i >= 0 and R["S"][i] >= t - 1 - FFILL else None


def o_at(R: dict[str, Any], t: int) -> int | None:
    j = int(np.searchsorted(R["S"], t, side="left"))
    return j if j < len(R["S"]) and R["S"][j] <= t + FFILL else None


class Px:
    """Price lookups for one session, tracking the contract and any isolated print touched."""

    def __init__(self, R: dict[str, Any]):
        self.R, self.k, self.void = R, set(), False

    def p(self, t: int) -> float:
        i = p_at(self.R, t)
        if i is None:
            return float("nan")
        self.k.add(int(self.R["K"][i]))
        self.void |= bool(self.R["iso_c"][i])
        return float(self.R["C"][i])

    def o(self, t: int) -> float:
        j = o_at(self.R, t)
        if j is None:
            return float("nan")
        self.k.add(int(self.R["K"][j]))
        self.void |= bool(self.R["iso_o"][j])
        return float(self.R["O"][j])


def leg(R: dict[str, Any], day: str, anchor: str, end: str = "15:00", entry_delay: int = 31) -> tuple[float, float, float, bool, int]:
    """x = P(anchor+30) - P(anchor), entry = open at anchor+31, y = P(end) - entry; all Beijing-clocked."""
    q = Px(R)
    a = bj(day, anchor)
    x = q.p(a + 30) - q.p(a)
    e = q.o(a + entry_delay)
    y = q.p(bj(day, end)) - e
    return x, e, y, q.void, len(q.k)


# ================================================================================ per-session quantities
def last_shfe_close(day: str, hol: set[str], night: str) -> tuple[int, str]:
    """The UTC minute of SHFE's last close before 09:00 Beijing on `day`: the previous trading day's night session end
    (`night`, Beijing, the next calendar date) when a night session ran, else that day's 15:00 day close."""
    ptd = prev_weekday(day)
    skipped = False
    while ptd in hol:
        ptd = prev_weekday(ptd)
        skipped = True
    suspended = NIGHT_SUSPENDED[0] <= day <= NIGHT_SUSPENDED[1]
    if skipped or suspended:                    # no night session on the evening before a holiday, nor in the suspension
        return bj(ptd, "15:00"), "day_close"
    return bj(add_days(ptd, 1), night), "night_close"


def session(R: dict[str, Any], day: str, hol: set[str], night: str) -> dict[str, Any]:
    q = Px(R)
    t0 = bj(day, "09:00")
    p0, p30 = q.p(t0), q.p(t0 + 30)
    e = q.o(t0 + 31)
    y15 = q.p(bj(day, "15:00")) - e
    rec: dict[str, Any] = {"day": day, "x": p30 - p0, "entry": e, "y": y15, "void": q.void, "nk": len(q.k),
                           "edt": edt_by_zoneinfo(t0), "edt_rule": edt_by_rule(t0)}
    # reported shape and variants (their own voids do not drop the session; they are NaN if a price is missing)
    s = Px(R)
    rec["y1015"] = s.p(bj(day, "10:15")) - e
    rec["y1130"] = s.p(bj(day, "11:30")) - e
    rec["ylast"] = s.p(bj(day, "15:00")) - s.p(bj(day, "14:30"))
    rec["x_rebased"] = s.p(t0 + 30) - s.p(bj(day, "09:16"))
    rec["auction"] = s.p(bj(day, "09:01")) - s.p(bj(day, "08:55"))
    # the controls and placebos: same y end (15:00 Beijing)
    for name, anchor in (("dst", "10:00" if not rec["edt"] else "08:00"), ("tokyo", "08:00"), ("brk", "10:30")):
        x_, e_, y_, v_, nk_ = leg(R, day, anchor)
        ok = np.isfinite(x_) and np.isfinite(y_) and not v_ and nk_ == 1
        rec[f"x_{name}"], rec[f"y_{name}"] = (x_, y_) if ok else (float("nan"), float("nan"))
    # the ET-fixed 21:00 ET window (an independent ET path, for the 2x2 and the right-quantity check)
    a = et(add_days(day, -1), "21:00")                                 # the evening before (Sunday for Monday)
    f = Px(R)
    fx = f.p(a + 30) - f.p(a)
    fe = f.o(a + 31)
    rec["x_etfixed"], rec["y_etfixed"] = fx, f.p(bj(day, "15:00")) - fe
    # the catch-up: g = P(09:00) - P(SHFE's last close); g_US = P(17:00 ET, the prior CME session's end) - P(that close)
    tc, kind = last_shfe_close(day, hol, night)
    c = Px(R)
    pc = c.p(tc)
    g0 = c.p(t0)
    rec["g"] = g0 - pc if len(c.k) == 1 and not c.void else float("nan")
    rec["g_kind"] = kind
    u = Px(R)
    p17 = u.p(et(prev_weekday(day), "17:00"))
    pc2 = u.p(tc)
    rec["g_us"] = p17 - pc2 if len(u.k) == 1 and not u.void and tc < et(prev_weekday(day), "17:00") else float("nan")
    return rec


def roll_flags(days: list[str], fm: dict[tuple[str, str], str], r: str) -> set[str]:
    """Sessions within ROLL_N sessions before the front contract changes (the root's weekday session list)."""
    out = set()
    lab = [fm.get((r, d), "") for d in days]
    for i, d in enumerate(days):
        if any(lab[j] != lab[i] for j in range(i + 1, min(i + 1 + ROLL_N, len(days)))):
            out.add(d)
    return out


def build_sessions(R: dict[str, Any], cell: str | None, fm: dict[tuple[str, str], str], hol: set[str]) -> tuple[pd.DataFrame, dict[str, int]]:
    r = R["root"]
    night = CELLS[cell]["night"] if cell else "02:30"
    all_days = sorted(d for (rr, d) in fm if rr == r and dt.date.fromisoformat(d).weekday() < 5)
    rolls = roll_flags(all_days, fm, r)
    days = [d for d in all_days if LO <= d <= HI]
    rows, counts = [], {"read": len(days), "holiday": 0, "roll": 0, "missing": 0, "print_void": 0, "two_contracts": 0}
    for d in days:
        rec = session(R, d, hol, night)
        rec["holiday"], rec["roll"] = d in hol, d in rolls
        need(rec["edt"] == rec["edt_rule"], f"clock: zoneinfo and the statutory rule disagree on {d}")
        if rec["holiday"]:
            why = "holiday"
        elif rec["roll"]:
            why = "roll"
        elif not (np.isfinite(rec["x"]) and np.isfinite(rec["y"])):
            why = "missing"
        elif rec["void"]:
            why = "print_void"
        elif rec["nk"] != 1:
            why = "two_contracts"
        else:
            why = "eligible"
        rec["why"] = why
        if why != "eligible":
            counts[why] += 1
        rows.append(rec)
    s = pd.DataFrame(rows)
    counts["eligible"] = int((s["why"] == "eligible").sum())
    need(counts["read"] == counts["eligible"] + sum(v for k, v in counts.items() if k not in ("read", "eligible")),
         "right quantity: sessions read != eligible + exclusions")
    # the holiday control: China closed, CME open, same clock; prices present, no void, one contract, not roll
    s["holiday_ctrl"] = s["holiday"] & ~s["roll"] & np.isfinite(s["x"]) & ~s["void"] & (s["nk"] == 1)
    need(not (s["holiday_ctrl"] & (s["why"] == "eligible")).any(), "right quantity: holiday and treatment overlap")
    return s, counts


def wf_flags(absx: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Walk-forward top third: |x_i| above the 2/3 quantile of the prior WF eligible |x| (strictly prior)."""
    n = len(absx)
    thr = np.full(n, np.nan)
    for i in range(WF, n):
        thr[i] = np.quantile(absx[i - WF:i], 2 / 3)
    return np.isfinite(thr) & (absx > thr), thr


# ================================================================================ statistics
def ranks(v: np.ndarray) -> np.ndarray:
    return pd.Series(v).rank(method="average").to_numpy(float)


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 10:
        return float("nan")
    ra, rb = ranks(a[m]), ranks(b[m])
    ra, rb = ra - ra.mean(), rb - rb.mean()
    return float(np.dot(ra, rb) / math.sqrt(np.dot(ra, ra) * np.dot(rb, rb)))


def _rot_chunk(args: tuple[np.ndarray, np.ndarray, int, int]) -> np.ndarray:
    rx, ry_ext, k0, k1 = args
    n = len(rx)
    return np.array([np.dot(rx, ry_ext[k:k + n]) for k in range(k0, k1)])


def rotation(x: np.ndarray, y: np.ndarray, chunks: int = 1) -> tuple[float, np.ndarray]:
    """Spearman rho and the exact circular rotation of y over k = 1 .. n-1 (offset 0 is the observed rho)."""
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    n = len(x)
    rx, ry = ranks(x), ranks(y)
    rx, ry = rx - rx.mean(), ry - ry.mean()
    den = math.sqrt(np.dot(rx, rx) * np.dot(ry, ry))
    ry_ext = np.r_[ry, ry]
    if chunks == 1:
        num = _rot_chunk((rx, ry_ext, 0, n))
    else:
        cuts = np.linspace(0, n, chunks + 1).astype(int)
        with ProcessPoolExecutor(chunks) as ex:
            num = np.concatenate(list(ex.map(_rot_chunk, [(rx, ry_ext, int(a), int(b)) for a, b in zip(cuts[:-1], cuts[1:])])))
    rho = num / den
    need(abs(rho[0] - spearman(x, y)) < 1e-12, "right quantity: rotation offset 0 != the observed rho")
    return float(rho[0]), rho[1:]


def two_sided_p(obs: float, dist: np.ndarray) -> float:
    n = len(dist) + 1
    hi = (1 + int((dist >= obs).sum())) / n
    lo = (1 + int((dist <= obs).sum())) / n
    return float(min(1.0, 2 * min(hi, lo)))


def holm(ps: dict[str, float]) -> dict[str, float]:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def tstat(v: np.ndarray) -> float:
    v = np.asarray(v, float)
    v = v[np.isfinite(v)]
    return float(v.mean() / (v.std(ddof=1) / math.sqrt(len(v)))) if len(v) > 2 and v.std(ddof=1) > 0 else float("nan")


def welch(a: np.ndarray, b: np.ndarray) -> float:
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return float((a.mean() - b.mean()) / se) if se > 0 else float("nan")


def ols_nw(x: np.ndarray, y: np.ndarray, lags: int = 5) -> tuple[float, float]:
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    X = np.column_stack([np.ones(len(x)), x])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    u = y - X @ beta
    Xu = X * u[:, None]
    S = Xu.T @ Xu
    for L in range(1, lags + 1):
        w = 1 - L / (lags + 1)
        G = Xu[L:].T @ Xu[:-L]
        S += w * (G + G.T)
    inv = np.linalg.inv(X.T @ X)
    V = inv @ S @ inv
    return float(beta[1]), float(beta[1] / math.sqrt(V[1, 1]))


def margin(s: pd.DataFrame, xa: str, ya: str, xb: str, yb: str, sign: float) -> dict[str, float]:
    """sign * (rho(xa, ya) - rho(xb, yb)) on the sessions where both exist; SE by a paired month-block bootstrap."""
    m = np.isfinite(s[xa]) & np.isfinite(s[ya]) & np.isfinite(s[xb]) & np.isfinite(s[yb])
    t = s[m].reset_index(drop=True)
    XA, YA, XB, YB = (t[c].to_numpy(float) for c in (xa, ya, xb, yb))
    obs = sign * (spearman(XA, YA) - spearman(XB, YB))
    mon = t["day"].str[:7].to_numpy()
    groups = [np.flatnonzero(mon == k) for k in pd.unique(mon)]
    rng = np.random.default_rng(B_SEED)
    draws = np.empty(B_DRAWS)
    for b in range(B_DRAWS):
        idx = np.concatenate([groups[i] for i in rng.integers(0, len(groups), len(groups))])
        draws[b] = sign * (spearman(XA[idx], YA[idx]) - spearman(XB[idx], YB[idx]))
    return {"n": int(len(t)), "rho_treat": spearman(XA, YA), "rho_placebo": spearman(XB, YB), "margin": float(obs),
            "se": float(draws.std(ddof=1)), "margin_over_se": float(obs / draws.std(ddof=1))}


# ================================================================================ the audits
def audit_prices(R: dict[str, Any], s: pd.DataFrame, sample: list[str]) -> None:
    """Second implementation: x, entry and y from boolean masks on the raw frame (no searchsorted, no Px, no leg)."""
    df = R["df"]
    mins = (df["ts"].to_numpy(np.int64) // 60_000_000_000)
    for d in sample:
        row = s[s["day"] == d].iloc[0]
        base = (dt.date.fromisoformat(d) - dt.date(1970, 1, 1)).days * 1440 - 8 * 60

        def close_at(hh: int, mm: int) -> float:
            t = base + hh * 60 + mm
            w = np.flatnonzero((mins >= t - 1 - FFILL) & (mins <= t - 1))
            return float(df["close"].iloc[w[-1]]) if len(w) else float("nan")

        def open_at(hh: int, mm: int) -> float:
            t = base + hh * 60 + mm
            w = np.flatnonzero((mins >= t) & (mins <= t + FFILL))
            return float(df["open"].iloc[w[0]]) if len(w) else float("nan")

        x2 = close_at(9, 30) - close_at(9, 0)
        e2 = open_at(9, 31)
        y2 = close_at(15, 0) - e2
        need(x2 == row["x"] and e2 == row["entry"] and y2 == row["y"], f"lag audit: {R['root']} {d} prices differ")


def audit_flags(absx: np.ndarray, traded: np.ndarray) -> None:
    """Second implementation of the walk-forward third: sorted lists and a hand-written linear quantile."""
    for i in range(len(absx)):
        if i < WF:
            need(not traded[i], "lag audit: a session traded before the walk-forward window filled")
            continue
        w = sorted(float(v) for v in absx[i - WF:i])
        pos = (len(w) - 1) * 2 / 3
        lo = int(math.floor(pos))
        thr = w[lo] + (w[min(lo + 1, len(w) - 1)] - w[lo]) * (pos - lo)
        need(bool(traded[i]) == bool(absx[i] > thr), f"lag audit: the traded-third flag differs at session {i}")


def audit_holidays(s: pd.DataFrame) -> None:
    with open(CAL, encoding="utf-8") as fh:
        lines = fh.read().splitlines()[1:]
    dates = {ln.split(",")[0] for ln in lines if ln}
    need(all((d in dates) == h for d, h in zip(s["day"], s["holiday"])), "lag audit: the holiday flag differs")


def sign_audit(side: float = 1.0) -> None:
    """In money: a long whose price rises pays; a short whose price falls pays; a mirrored book must raise."""
    x, y = np.array([0.01, -0.01]), np.array([0.02, -0.02])
    pnl = side * np.sign(x) * y * 2500.0
    need(bool((pnl > 0).all()), "sign audit: a continuation that kept going did not pay")


# ================================================================================ the run
def score_cell(cell: str, s: pd.DataFrame, lines: Path | None) -> dict[str, Any]:
    c = CELLS[cell]
    mult, cost = c["mult"], c["cost"]
    e = s[s["why"] == "eligible"].reset_index(drop=True)
    x, y = e["x"].to_numpy(float), e["y"].to_numpy(float)
    traded, thr = wf_flags(np.abs(x))
    audit_flags(np.abs(x), traded)
    e["traded"] = traded
    rho, dist = rotation(x, y)
    p2 = two_sided_p(rho, dist)
    out: dict[str, Any] = {"eligible": int(len(e)), "traded": int(traded.sum())}
    # C1 size
    absy = np.abs(y[traded]) * mult
    out["C1"] = {"mean_abs_y_traded": float(absy.mean()), "bar": 4 * cost, "pass": bool(absy.mean() >= 4 * cost),
                 "sd_y_traded": float(np.std(y[traded] * mult, ddof=1)),
                 "mean_abs_y_1015": float(np.nanmean(np.abs(e["y1015"].to_numpy(float)[traded])) * mult),
                 "mean_abs_y_1130": float(np.nanmean(np.abs(e["y1130"].to_numpy(float)[traded])) * mult),
                 "mean_abs_x_treatment": float(np.abs(x).mean() * mult)}
    # C2 direction
    out["C2"] = {"rho": rho, "p2_5": float(np.quantile(dist, 0.025)), "p50": float(np.quantile(dist, 0.5)),
                 "p97_5": float(np.quantile(dist, 0.975)), "offsets": int(len(dist)), "p_two_sided": p2,
                 "outside_band": bool(rho < np.quantile(dist, 0.025) or rho > np.quantile(dist, 0.975)),
                 "ols_slope_nw5": ols_nw(x, y), "rho_traded_third": spearman(x[traded], y[traded])}
    # C3(a) holidays
    h = s[s["holiday_ctrl"]]
    hx = np.abs(h["x"].to_numpy(float))
    hy_ok = np.isfinite(h["y"].to_numpy(float))
    out["C3a"] = {"n_holiday": int(len(h)), "mean_abs_x_treatment": float(np.abs(x).mean() * mult),
                  "mean_abs_x_holiday": float(hx.mean() * mult) if len(hx) else float("nan"),
                  "welch_t": welch(np.abs(x), hx) if len(hx) > 2 else float("nan"),
                  "rho_holiday": spearman(h["x"].to_numpy(float)[hy_ok], h["y"].to_numpy(float)[hy_ok]),
                  "rho_holiday_se": 1 / math.sqrt(max(int(hy_ok.sum()) - 1, 1))}
    out["C3a"]["pass"] = bool(np.isfinite(out["C3a"]["welch_t"]) and out["C3a"]["welch_t"] > 2)
    return out | {"_e": e, "_rho": rho, "_p2": p2}


def finish_cell(cell: str, s: pd.DataFrame, out: dict[str, Any], c2_pass: bool, lines: Path | None) -> dict[str, Any]:
    from stage0_d755_ecb_press_conference import book
    c = CELLS[cell]
    mult, cost = c["mult"], c["cost"]
    e = out.pop("_e")
    rho = out.pop("_rho")
    out.pop("_p2")
    sign = float(np.sign(rho)) if c2_pass and rho != 0 else 1.0
    out["side_sign"] = "continuation" if sign > 0 else "reversal"
    out["side_from"] = "C2's sign" if c2_pass else "the predicted sign (C2 failed; reported, in no reading)"
    # C3(b) and C4: signed margins against the placebos (paired month-block bootstrap)
    e2 = e.copy()
    out["C3b"] = margin(e2, "x", "y", "x_dst", "y_dst", sign)
    out["C4_tokyo"] = margin(e2, "x", "y", "x_tokyo", "y_tokyo", sign)
    out["C4_postbreak"] = margin(e2, "x", "y", "x_brk", "y_brk", sign)
    # the 2x2: Beijing-aligned vs ET-fixed 21:00 ET, EDT vs EST
    tw = {}
    for lab, msk in (("EDT", e["edt"]), ("EST", ~e["edt"])):
        tw[lab] = {"beijing": spearman(e.loc[msk, "x"].to_numpy(float), e.loc[msk, "y"].to_numpy(float)),
                   "et_fixed": spearman(e.loc[msk, "x_etfixed"].to_numpy(float), e.loc[msk, "y_etfixed"].to_numpy(float)),
                   "n": int(msk.sum())}
    out["two_by_two"] = tw
    ed = e[e["edt"]]
    need(bool(np.allclose(ed["x_etfixed"], ed["x"], equal_nan=True)) and bool(np.allclose(ed["y_etfixed"], ed["y"], equal_nan=True)),
         "right quantity: ET-fixed 21:00 differs from the Beijing-aligned window on an EDT session")
    es = e[~e["edt"]]
    need(not np.allclose(es["x_etfixed"], es["x"], equal_nan=True), "right quantity: ET-fixed equals Beijing-aligned on EST")
    # C5: the traded third, side = sign * sign(x)
    tr = e[e["traded"]].reset_index(drop=True)
    side = sign * np.sign(tr["x"].to_numpy(float))
    g = side * tr["y"].to_numpy(float) * mult
    days = tr["day"].tolist()
    yrs_span = max((pd.Timestamp(days[-1]) - pd.Timestamp(days[0])).days / 365.25, 1e-9)
    bk = book(g, days, cost, len(g) / yrs_span)
    net = g - cost
    yrs = pd.Series(net, index=[d[:4] for d in days]).groupby(level=0).sum()
    ex2 = float(net.sum() - yrs.sort_values(ascending=False).iloc[:2].sum())
    tnet = tstat(net)
    out["C5"] = {"book": bk, "t_net": tnet, "one_sided_p": float(0.5 * math.erfc(tnet / math.sqrt(2))) if np.isfinite(tnet) else 1.0,
                 "net_ex_best_two_years": ex2, "thin_book_net": float(net.mean() - 2 * c["mtick_usd"]),
                 "thin_book_breakeven": float(g.mean() - 2 * c["mtick_usd"])}
    # reported splits on the traded book
    tr = tr.assign(net=net, gross=g, side=side)
    grp = lambda m_: {"n": int(m_.sum()), "mean_net": float(tr.loc[m_, "net"].mean()) if m_.any() else None}  # noqa: E731
    dts = pd.to_datetime(tr["day"])
    sub = (tr["day"] >= NIGHT_SUSPENDED[0]) & (tr["day"] <= NIGHT_SUSPENDED[1])
    out["splits"] = {"EDT": grp(tr["edt"]), "EST": grp(~tr["edt"]), "monday": grp(dts.dt.weekday == 0),
                     "other_days": grp(dts.dt.weekday != 0), "long": grp(tr["side"] > 0), "short": grp(tr["side"] < 0),
                     "night_suspension_2020": grp(sub), "years": {y_: grp(tr["day"].str[:4] == y_) for y_ in sorted(tr["day"].str[:4].unique())}}
    srt = tr.sort_values("net")
    out["largest"] = {"losers": [(d, round(v, 2)) for d, v in zip(srt["day"][:5], srt["net"][:5])],
                      "winners": [(d, round(v, 2)) for d, v in zip(srt["day"][-5:], srt["net"][-5:])]}
    out["shape"] = {"rho_1015": spearman(e["x"].to_numpy(float), e["y1015"].to_numpy(float)),
                    "rho_1130": spearman(e["x"].to_numpy(float), e["y1130"].to_numpy(float)),
                    "rho_last_half_hour": spearman(e["x"].to_numpy(float), e["ylast"].to_numpy(float)),
                    "rho_rebased_x_0916": spearman(e["x_rebased"].to_numpy(float), e["y"].to_numpy(float)),
                    "mean_abs_auction": float(np.nanmean(np.abs(e["auction"].to_numpy(float))) * mult),
                    "rho_auction_x": spearman(e["auction"].to_numpy(float), e["x"].to_numpy(float))}
    # the catch-up (reported)
    cu = {}
    for a_, b_ in (("g", "x"), ("g", "y"), ("g_us", "y")):
        r_, d_ = rotation(e[a_].to_numpy(float), e[b_].to_numpy(float))
        cu[f"rho_{a_}_{b_}"] = {"rho": r_, "p2_5": float(np.quantile(d_, 0.025)), "p97_5": float(np.quantile(d_, 0.975)),
                                "p_two_sided": two_sided_p(r_, d_), "n": int(len(d_) + 1)}
    gx = e[np.isfinite(e["g"])]
    cu["two_by_two_mean_y_usd"] = {f"g{'+' if sg > 0 else '-'}_x{'+' if sx > 0 else '-'}":
                                   {"n": int(((np.sign(gx["g"]) == sg) & (np.sign(gx["x"]) == sx)).sum()),
                                    "mean_y": float(gx.loc[(np.sign(gx["g"]) == sg) & (np.sign(gx["x"]) == sx), "y"].mean() * mult)}
                                   for sg in (1, -1) for sx in (1, -1)}
    cu["g_kind_counts"] = e["g_kind"].value_counts().to_dict()
    sub_e = (e["day"] >= NIGHT_SUSPENDED[0]) & (e["day"] <= NIGHT_SUSPENDED[1])
    cu["night_suspension_2020"] = {"n": int(sub_e.sum()), "rho_g_x": spearman(e.loc[sub_e, "g"].to_numpy(float), e.loc[sub_e, "x"].to_numpy(float))}
    out["catch_up"] = cu
    # holiday extremes: the first session after Spring Festival and after Golden Week
    ext = []
    for blk in holiday_blocks():
        if len(blk) < 3 or blk[0][5:7] not in ("01", "02", "10"):
            continue
        after = e[e["day"] > blk[-1]].head(1)
        if len(after):
            ext.append({"after": blk[-1], "day": after["day"].iloc[0], "abs_x_usd": float(abs(after["x"].iloc[0]) * mult)})
    out["after_long_holidays"] = {"sessions": ext, "mean_abs_x_usd": float(np.mean([v["abs_x_usd"] for v in ext])) if ext else None}
    # the component line: daily net vs the ledger's lines
    if lines is not None and lines.exists():
        ol = pd.read_csv(lines, index_col=0, encoding="utf-8")
        ol.index = ol.index.astype(str)
        dnet = pd.Series(net, index=days).groupby(level=0).sum()
        alld = sorted(set(ol.index) | {d for d in dnet.index if ol.index.min() <= d <= ol.index.max()})
        out["component_corr"] = {k: float(np.corrcoef(dnet.reindex(alld, fill_value=0.0), ol[k].reindex(alld).fillna(0.0))[0, 1])
                                 for k in ol.columns}
    return out


def run(lines: Path | None) -> int:
    need(not OUT.exists(), f"{OUT.name} exists: D765 is run-once")
    t0 = time.time()
    sign_audit()
    fm = _front_map()
    hol = load_holidays()
    res: dict[str, Any] = {"spec": SPEC.name, "seal": f"nothing on or after {SEAL}", "window": [LO, HI], "cells": {}, "prints": {}}
    R = {r: load_root(r) for r in ROOTS}
    for r in ROOTS:
        yr = pd.Series(R[r]["day"]).str[:4]
        res["prints"][r] = {"isolated_close": pd.Series(R[r]["iso_c"]).groupby(yr.to_numpy()).sum().astype(int).to_dict(),
                            "isolated_open": pd.Series(R[r]["iso_o"]).groupby(yr.to_numpy()).sum().astype(int).to_dict()}
    S: dict[str, pd.DataFrame] = {}
    first: dict[str, dict[str, Any]] = {}
    for cell, c in CELLS.items():
        s, counts = build_sessions(R[c["root"]], cell, fm, hol)
        audit_holidays(s)
        el = s[s["why"] == "eligible"]
        rng_ = np.random.default_rng(765)
        audit_prices(R[c["root"]], s, sorted(rng_.choice(el["day"].to_numpy(), size=min(40, len(el)), replace=False).tolist()))
        S[cell] = s
        first[cell] = score_cell(cell, s, lines) | {"counts": counts}
        print(f"[{cell}] {counts}", flush=True)
    # Holm over the two primary cells on C2's two-sided p
    hp = holm({k: first[k]["_p2"] for k in CELLS if CELLS[k]["primary"]})
    for cell, c in CELLS.items():
        o = first[cell]
        c2 = bool(o["C2"]["outside_band"] and (hp.get(cell, o["_p2"]) < 0.05))
        o["C2"]["holm_p"] = hp.get(cell)
        o["C2"]["pass"] = c2
        res["cells"][cell] = finish_cell(cell, S[cell], o, c2, lines)
    # Holm over the two primary cells on C5's one-sided p, then the readings
    h5 = holm({k: res["cells"][k]["C5"]["one_sided_p"] for k in CELLS if CELLS[k]["primary"]})
    for cell, c in CELLS.items():
        o = res["cells"][cell]
        c5 = o["C5"]
        c5["holm_p"] = h5.get(cell)
        b = c5["book"]
        c5["pass"] = bool(b["mean_net"] > 0 and np.isfinite(c5["t_net"]) and c5["t_net"] >= 2 and (h5.get(cell, 1.0) < 0.05)
                          and c5["net_ex_best_two_years"] > 0)
        m3 = o["C3b"]["margin"]
        se3 = o["C3b"]["se"]
        m4 = [(o[k]["margin"], o[k]["se"]) for k in ("C4_tokyo", "C4_postbreak")]
        if not o["C1"]["pass"]:
            rd = "SIZE FAILURE"
        elif not o["C2"]["pass"]:
            rd = "NO DIRECTION"
        elif not o["C3a"]["pass"] or m3 <= 0:
            rd = "NOT CHINA"
        elif (0 < m3 <= 2 * se3) or any(0 < m <= 2 * se for m, se in m4):
            rd = "UNRESOLVED"
        elif any(m <= 0 for m, _ in m4):
            rd = "GENERIC"
        elif not c5["pass"]:
            rd = "NO PRIZE"
        else:
            rd = "PREMISE HOLDS"
        o["reading"] = rd if c["primary"] else f"REPORTED ONLY (would read {rd})"
        o["GO"] = bool(c["primary"] and rd == "PREMISE HOLDS")
    # 6A: the AUD's opening move against copper's and silver's (reference)
    s6, cnt6 = build_sessions(R["6A"], None, fm, hol)
    a6 = s6[s6["why"] == "eligible"].set_index("day")["x"]
    res["ref_6A"] = {"counts": cnt6}
    for cell in ("mhg", "sil"):
        e = S[cell][S[cell]["why"] == "eligible"].set_index("day")["x"]
        j = pd.concat([e, a6], axis=1, join="inner").dropna()
        res["ref_6A"][f"rho_x_{cell}_x_6A"] = {"rho": spearman(j.iloc[:, 0].to_numpy(float), j.iloc[:, 1].to_numpy(float)), "n": int(len(j))}
    res["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    for cell in CELLS:
        o = res["cells"][cell]
        print(cell, o["reading"], json.dumps({"C1": {k: o["C1"][k] for k in ("mean_abs_y_traded", "bar", "pass")},
                                              "C2": {k: o["C2"][k] for k in ("rho", "p2_5", "p97_5", "p_two_sided", "pass")},
                                              "C3a_t": o["C3a"]["welch_t"], "C3b": o["C3b"]["margin_over_se"],
                                              "C4": [o["C4_tokyo"]["margin_over_se"], o["C4_postbreak"]["margin_over_se"]],
                                              "C5": {"mean_net": o["C5"]["book"]["mean_net"], "t": o["C5"]["t_net"]}}, default=float), flush=True)
    print(f"runtime {res['runtime_min']} min", flush=True)
    return 0


# ================================================================================ self-test
def _synth_bars(days: list[str], plant: float, seed: int) -> pd.DataFrame:
    """One-minute bars over each session (18:00 ET the evening before -> 17:00 ET), a random walk, and a planted
    continuation of the 09:00-09:30 Beijing move into 15:00 Beijing (plant = share of x added, spread evenly)."""
    rng = np.random.default_rng(seed)
    rows = []
    px = 4.0
    for d in days:
        a = et(add_days(d, -1), "18:00")
        z = et(d, "17:00")
        n = z - a
        steps = rng.normal(0, 0.0005, n)
        t0, t30, t15 = bj(d, "09:00") - a, bj(d, "09:30") - a, bj(d, "15:00") - a
        cl = px + np.cumsum(steps)
        if plant and 0 < t0 < t30 < t15 < n:
            xmove = cl[t30 - 1] - cl[t0 - 1]
            add = np.zeros(n)
            add[t30:t15] = plant * xmove / (t15 - t30)
            cl = cl + np.cumsum(add)
        cl = np.round(cl / TICK["HG"]) * TICK["HG"]
        op = np.r_[px, cl[:-1]] + rng.integers(-1, 2, n) * TICK["HG"]        # opens a tick off the prior close
        ts = (np.arange(a, z, dtype=np.int64) * 60_000_000_000)
        rows.append(pd.DataFrame({"ts": ts, "open": op, "close": cl, "contract": "HGX9", "day": d}))
        px = float(cl[-1])
    return pd.concat(rows, ignore_index=True)


def selftest() -> int:
    # 1. sign in money, and the audit raises on a mirrored book
    sign_audit()
    try:
        sign_audit(-1.0)
        raise SystemExit("FAIL: the sign audit did not raise on a mirrored book")
    except D765Error:
        pass
    # 2. clocks: Beijing 09:00 = 21:00 ET (EDT) / 20:00 ET (EST); zoneinfo == the statutory rule over 2016-2023
    need(bj("2019-07-10", "09:00") == et("2019-07-09", "21:00"), "clock: EDT China open is not 21:00 ET")
    need(bj("2019-01-10", "09:00") == et("2019-01-09", "20:00"), "clock: EST China open is not 20:00 ET")
    for d in pd.date_range("2016-01-01", "2023-12-31", freq="D"):
        t = bj(d.strftime("%Y-%m-%d"), "09:00")
        need(edt_by_zoneinfo(t) == edt_by_rule(t), f"clock: zoneinfo != rule on {d.date()}")
    # 3. the night close: Monday's is Saturday 01:00 Beijing = Friday 17:00 UTC; after a holiday it is the day close
    need(last_shfe_close("2019-07-15", set(), "01:00") == (bj("2019-07-13", "01:00"), "night_close"), "night close: Monday")
    need(last_shfe_close("2019-10-08", {"2019-10-01", "2019-10-02", "2019-10-03", "2019-10-04", "2019-10-07"}, "01:00")
         == (bj("2019-09-30", "15:00"), "day_close"), "night close: after Golden Week")
    need(last_shfe_close("2020-03-10", set(), "02:30")[1] == "day_close", "night close: the 2020 suspension")
    # 4. synthetic sessions through the real session path: a planted continuation is found; the audits pass
    days = [d.strftime("%Y-%m-%d") for d in pd.bdate_range("2018-01-02", "2020-12-31")]
    b = _synth_bars(days, plant=0.6, seed=1)
    R = arrays_from(b, "HG")
    fm = {("HG", d): "HGX9" for d in days}
    rows = [session(R, d, set(), "01:00") | {"holiday": False, "roll": False} for d in days]
    s = pd.DataFrame(rows)
    s["why"] = np.where(np.isfinite(s["x"]) & np.isfinite(s["y"]) & ~s["void"] & (s["nk"] == 1), "eligible", "missing")
    s["holiday_ctrl"] = False
    el = s[s["why"] == "eligible"]
    need(len(el) > 600, f"synthetic: too few eligible sessions ({len(el)})")
    audit_prices(R, s, el["day"].head(10).tolist())
    rho, dist = rotation(el["x"].to_numpy(float), el["y"].to_numpy(float))
    need(two_sided_p(rho, dist) < 0.01 and rho > 0, f"synthetic: a planted continuation was not found (rho {rho:.3f})")
    for k in ("dst", "tokyo", "brk"):
        need(abs(spearman(el[f"x_{k}"].to_numpy(float), el[f"y_{k}"].to_numpy(float))) < rho / 2, f"synthetic: placebo {k} carried the plant")
    # 5. the lag audit raises on an entry read from the 09:30 bar's close
    bad = s.copy()
    i0 = bad.index[bad["why"] == "eligible"][0]
    d0 = bad.at[i0, "day"]
    j0 = p_at(R, bj(d0, "09:31"))
    need(float(R["C"][j0]) != bad.at[i0, "entry"], "self-test design: the 09:30 close equals the 09:31 open")
    bad.at[i0, "entry"] = float(R["C"][j0])
    try:
        audit_prices(R, bad, [d0])
        raise SystemExit("FAIL: the lag audit did not raise on an entry read from the 09:30 close")
    except D765Error:
        pass
    # 6. the traded-third audit raises when the threshold includes the current session
    absx = np.r_[np.arange(1.0, WF + 1.0), 0.0]
    thr_ok = np.quantile(absx[:WF], 2 / 3)
    absx[WF] = thr_ok + 1e-6
    good, _ = wf_flags(absx)
    audit_flags(absx, good)
    leaky = good.copy()
    leaky[WF] = bool(absx[WF] > np.quantile(absx[1:WF + 1], 2 / 3))
    need(leaky[WF] != good[WF], "self-test design: the leaky threshold did not change the flag")
    try:
        audit_flags(absx, leaky)
        raise SystemExit("FAIL: the flag audit did not raise on a threshold that includes the current session")
    except D765Error:
        pass
    # 7. noise fails C2 about 95% of the time
    rng = np.random.default_rng(7)
    fails = 0
    for _ in range(200):
        xs, ys = rng.normal(size=800), rng.normal(size=800)
        r_, d_ = rotation(xs, ys)
        fails += two_sided_p(r_, d_) >= 0.05
    need(0.90 <= fails / 200 <= 0.99, f"noise: C2 failed {fails}/200 (expected about 95%)")
    # 8. chunk == whole: the rotation on 4 processes equals the serial one bit for bit
    xs, ys = rng.normal(size=900), rng.normal(size=900)
    r1, d1 = rotation(xs, ys)
    r4, d4 = rotation(xs, ys, chunks=4)
    need(r1 == r4 and np.array_equal(d1, d4), "chunk != whole: the rotation on 4 processes differs")
    # 9. ET-fixed 21:00 equals the Beijing window on EDT sessions and differs on EST sessions
    ed, es = s[s["edt"] & (s["why"] == "eligible")], s[~s["edt"] & (s["why"] == "eligible")]
    need(np.allclose(ed["x_etfixed"], ed["x"], equal_nan=True), "right quantity: ET-fixed != Beijing on EDT (synthetic)")
    need(not np.allclose(es["x_etfixed"], es["x"], equal_nan=True), "right quantity: ET-fixed == Beijing on EST (synthetic)")
    # 10. the seal raises on a 2024 row; isolated prints are flagged
    try:
        bb = b.head(5).copy()
        bb.loc[bb.index[-1], "ts"] = SEAL_NS
        need(bool((bb["ts"] < SEAL_NS).all()), "seal: a bar on or after 2024")
        raise SystemExit("FAIL: the seal check did not raise")
    except D765Error:
        pass
    sp = b.head(50).copy()
    sp.loc[sp.index[20], "close"] += 30 * TICK["HG"]
    need(bool(arrays_from(sp, "HG")["iso_c"][20]), "print check: an isolated close was not flagged")
    print("SELFTEST OK: sign in money (raises on a mirrored book); Beijing/ET clocks and zoneinfo == the statutory rule "
          "2016-2023; SHFE's last close (Monday, after Golden Week, the 2020 suspension); a planted continuation found "
          "through the real session path with placebos clean; the lag audit raises on an entry read from the 09:30 close; "
          "the flag audit raises on a threshold that includes the current session; noise fails C2 "
          f"{fails}/200; chunk == whole on 4 processes; ET-fixed == Beijing on EDT and != on EST; the seal raises; "
          "isolated prints flagged")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--lines", type=Path, default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.extract:
        return extract()
    if a.run:
        return run(a.lines)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())

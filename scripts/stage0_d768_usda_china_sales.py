"""D768 Stage 0: China's demand footprint on the CBOT day (prop book; one micro, MZS / MZC).

Pre-registration: docs/decisions/D768-STAGE-0-PRE-REG-china-buys-soybeans-and-the-cbot-day.md

    python scripts/stage0_d768_usda_china_sales.py --selftest     # synthetic; every assertion proved to raise
    python scripts/stage0_d768_usda_china_sales.py --extract      # ZS / ZC front minutes, all hours, < 2024 (system python)
    python scripts/stage0_d768_usda_china_sales.py --run          # once

USDA FAS publishes large daily export sales at 09:00 ET, inside the CBOT grain break (08:45 -> 09:30 ET). On trade date d
(ET): O = open of the first bar starting in [09:30, 09:35]; P(14:15) = close of the last bar starting before 14:15
(<= 10 min stale); P(08:45) = the overnight's last close before 08:45 (<= 60 min stale); P_prev = the previous trade
date's last close before 14:20 (<= 10 min stale); one contract. y = (P(14:15) - O) x $5 per cent per micro;
g_break = (O - P(08:45)) x $5; g_night = (P(08:45) - P_prev) x $5.

E(d) = 1 on a fixture sale of the cell's commodity to China or unknown destinations dated d. G1: A = mean y on events
against the exact rotation of E (offsets 1..n-1), two-sided, Holm over the two cells; G2: gross >= $5.50 with NW(5)
t >= 2 in G1's direction; G3: >= 5 of 8 years net positive, positive ex-best year, no month > 25% of the net.
"""
from __future__ import annotations

import argparse
import csv
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
SPEC = REPO / "docs" / "decisions" / "D768-STAGE-0-PRE-REG-china-buys-soybeans-and-the-cbot-day.md"
OUT = REPO / "data" / "stage0_d768_usda_china_sales.json"
FIX = REPO / "data" / "fixtures" / "usda_daily_export_sales.csv"
WASDE = REPO / "data" / "fixtures" / "wasde_grains_su.csv"
BOOKS = REPO / "data" / "d748_component_books.csv"
TMP = Path(os.environ.get("D768_TMP", str(REPO / "temp" / "d768")))
SEAL = "2024-01-01"
SEAL_NS = int(pd.Timestamp(SEAL, tz="UTC").value)
XLO_NS = int(pd.Timestamp("2015-12-01", tz="UTC").value)
FIRST, LAST = "2016-01-04", "2023-12-29"
NY = ZoneInfo("America/New_York")
ROOTS = ("ZS", "ZC")
COM = {"ZS": "soybeans", "ZC": "corn"}
UNITS = {"ZS": (700.0, 1800.0), "ZC": (300.0, 800.0)}       # cents a bushel
USD_PER_CENT = 5.00                                          # one micro = 500 bushels
TICK_USD = 2.50                                              # MZS / MZC: half a cent a bushel
COST = 3.00 + TICK_USD                                       # D468 micro commission + one tick a round trip (d556_one_tick)
DEST = ("China", "unknown destinations")
T_MIN, YEARS_MIN, MONTH_MAX = 2.0, 5, 0.25
ERAS = (("pre-trade-war", "2016-01-01", "2018-07-05"), ("trade war", "2018-07-06", "2020-01-14"),
        ("Phase One", "2020-01-15", "2021-12-31"), ("2022-23", "2022-01-01", "2023-12-31"))
MONTH_CODE = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
WORKERS = 4


class D768Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D768Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ================================================================================ clock
def et_min(day: str, hh: int, mm: int) -> int:
    """UTC minute (since epoch) of hh:mm ET on calendar date `day`."""
    d = dt.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), hh, mm, tzinfo=NY).astimezone(dt.timezone.utc)
    return int(d.timestamp() // 60)


def trade_day_of(ts_ns: np.ndarray) -> np.ndarray:
    """CME trade date (days since 1970): the ET date of wall time + 6 hours (D765's rule)."""
    t = pd.to_datetime(ts_ns, utc=True).tz_convert(NY).tz_localize(None)
    wall = np.asarray((t - pd.Timestamp("1970-01-01")) // pd.Timedelta(minutes=1), dtype=np.int64)
    return ((wall + 360) // 1440).astype(np.int64)


# ================================================================================ extraction (D765's, restated for ZS / ZC)
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
                            "open": a["open"] * BH.PX, "close": a["close"] * BH.PX, "volume": a["volume"].astype(np.int64)})
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
            parts.append(k[["root", "contract", "ts", "day", "open", "close", "volume"]].reset_index(drop=True))
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
def fnd(contract: str, day: str) -> str:
    """First notice day of a grain contract: the last weekday of the month before the delivery month."""
    mo, yd = MONTH_CODE[contract[2]], int(contract[3:]) % 10
    y0 = int(day[:4])
    y = y0 - y0 % 10 + yd            # the single-digit year in the trade date's decade, or the next decade's
    if y < y0:
        y += 10
    first = dt.date(y, mo, 1)
    d = first - dt.timedelta(days=1)
    while d.weekday() > 4:
        d -= dt.timedelta(days=1)
    return d.isoformat()


def session_quantities(b: pd.DataFrame, root: str) -> pd.DataFrame:
    """One row per trade date: O, P1415, P0845, P_prev and the break count, from the front minutes of one root."""
    need(bool((b["ts"] > 10**18).all()), "units: a timestamp is not in nanoseconds")
    need(bool((b["ts"] < SEAL_NS).all()) and bool((b["day"] < SEAL).all()), f"seal: a {root} bar on or after 2024")
    S = (b["ts"].to_numpy(np.int64) // 60_000_000_000).astype(np.int64)
    need(bool(np.all(np.diff(S) > 0)), f"{root}: bars not strictly ordered")
    O, C = b["open"].to_numpy(float), b["close"].to_numpy(float)
    K = b["contract"].to_numpy()
    days = b["day"].to_numpy()
    starts = np.r_[0, np.flatnonzero(days[1:] != days[:-1]) + 1]
    ends = np.r_[starts[1:], len(days)]
    rows, prev = [], None
    for a, z in zip(starts, ends):
        d = str(days[a])
        s = S[a:z]
        t0930, t1415, t0845, t1420 = et_min(d, 9, 30), et_min(d, 14, 15), et_min(d, 8, 45), et_min(d, 14, 20)
        j = int(np.searchsorted(s, t0930, side="left"))
        o = float(O[a + j]) if j < s.size and s[j] <= t0930 + 5 else float("nan")
        i = int(np.searchsorted(s, t1415, side="left")) - 1
        p1415 = float(C[a + i]) if i >= 0 and s[i] >= t1415 - 10 else float("nan")
        i8 = int(np.searchsorted(s, t0845, side="left")) - 1
        p0845 = float(C[a + i8]) if i8 >= 0 and s[i8] >= t0845 - 60 else float("nan")
        brk = int(((s > t0845) & (s < t0930)).sum())      # the pre-registration's OPEN interval: the 08:45 bar is the overnight's close
        pprev = float("nan")
        if prev is not None and prev[1] == str(K[a]):
            pprev = prev[0]
        ip = int(np.searchsorted(s, t1420, side="left")) - 1
        close1420 = (float(C[a + ip]), str(K[a])) if ip >= 0 and s[ip] >= t1420 - 10 else None
        rows.append((d, str(K[a]), o, p1415, p0845, pprev, brk, bool((K[a:z] == K[a]).all())))
        prev = close1420
    f = pd.DataFrame(rows, columns=["day", "contract", "O", "P1415", "P0845", "Pprev", "brk", "one_contract"])
    need(bool(f["one_contract"].all()), f"{root}: a trade date spans two contracts")
    return f


def check_units(q: pd.DataFrame, root: str) -> float:
    lo, hi = UNITS[root]
    med = float(np.nanmedian(q["P1415"]))
    need(lo <= med <= hi, f"units: the median {root} close {med} is outside [{lo}, {hi}] cents")
    return med


def check_break(q: pd.DataFrame, root: str) -> float:
    fq = q[(q["day"] >= FIRST) & (q["day"] <= LAST)]
    share = float((fq["brk"] == 0).mean())
    need(share >= 0.99, f"the break: only {share:.3f} of {root} sessions have no bar starting in (08:45, 09:30) ET")
    return share


def check_delivery(f: pd.DataFrame, root: str) -> int:
    gap = [(dt.date.fromisoformat(fnd(c, d)) - dt.date.fromisoformat(d)).days for d, c in zip(f["day"], f["contract"])]
    need(min(gap) > 0, f"delivery: a {root} front used on or after its first notice day")
    return int(min(gap))


def moves(f: pd.DataFrame) -> pd.DataFrame:
    f = f[(f["day"] >= FIRST) & (f["day"] <= LAST)].copy()
    f = f[pd.to_datetime(f["day"]).dt.weekday < 5]
    f["y"] = (f["P1415"] - f["O"]) * USD_PER_CENT
    f["g_break"] = (f["O"] - f["P0845"]) * USD_PER_CENT
    f["g_night"] = (f["P0845"] - f["Pprev"]) * USD_PER_CENT
    return f[np.isfinite(f["y"])].reset_index(drop=True)


# ================================================================================ events
def load_fixture() -> pd.DataFrame:
    fx = pd.read_csv(FIX, dtype=str, keep_default_na=False, encoding="utf-8")
    need(bool((fx["date"] < SEAL).all()), "seal: a fixture row dated 2024 or later")
    return fx


def event_sets(fx: pd.DataFrame, com: str) -> dict[str, set[str]]:
    sale = fx[(fx["kind"] == "sale") & (fx["commodity"] == com)]
    ev = sale[sale["destination"].isin(DEST)]
    out = {"event": set(ev["date"]), "china": set(ev.loc[ev["destination"] == "China", "date"]),
           "unknown": set(ev.loc[ev["destination"] == "unknown destinations", "date"]),
           "big": set(ev.loc[ev["tonnes"].astype(int) >= 500_000, "date"]),
           "placebo": set(sale.loc[~sale["destination"].isin(DEST), "date"]) - set(ev["date"]),
           "cancel": set(fx.loc[(fx["kind"] == "cancel") & (fx["commodity"] == com) & fx["destination"].isin(DEST), "date"])}
    drop = set(fx.loc[(fx["title_kind"] == "retraction") & (fx["commodity"] == com), "date"])
    for _, r in fx[(fx["commodity"] == com) & (fx["dateline"] == "mismatch")].iterrows():
        gap = (dt.date.fromisoformat(r["dateline_date"]) - dt.date.fromisoformat(r["date"])).days
        if 1 <= gap <= 3:
            drop |= {r["date"], r["dateline_date"]}
    out["drop"] = drop
    return out


def flags_by_csv(path: Path, com: str, days: list[str]) -> list[int]:
    """Second implementation of the event flag: the fixture's text through the csv module, no pandas."""
    hit = set()
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if r["kind"] == "sale" and r["commodity"] == com and r["destination"] in DEST:
                hit.add(r["date"])
    return [1 if d in hit else 0 for d in days]


def lag_audit(days: list[str], e: np.ndarray, com: str, sample: list[int], path: Path = FIX) -> None:
    ref = flags_by_csv(path, com, [days[i] for i in sample])
    for i, f in zip(sample, ref):
        need(int(e[i]) == f, f"lag audit: {com} flag on {days[i]} is {int(e[i])}, the fixture text says {f}")


# ================================================================================ statistics
def rot_means(e: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.array([y[np.roll(e, k) == 1].mean() for k in range(1, e.size)])


def rotation(e: np.ndarray, y: np.ndarray) -> dict:
    A = float(y[e == 1].mean())
    null = rot_means(e, y)
    hi = (1 + (null >= A).sum()) / (1 + null.size)
    lo = (1 + (null <= A).sum()) / (1 + null.size)
    return {"A": A, "offset0": float(y[np.roll(e, 0) == 1].mean()), "offsets": int(null.size),
            "p2_5": float(np.percentile(null, 2.5)), "p50": float(np.percentile(null, 50)), "p97_5": float(np.percentile(null, 97.5)),
            "p_two_sided": float(min(1.0, 2 * min(hi, lo)))}


def delta_rotation(e: np.ndarray, x: np.ndarray) -> dict:
    """mean x on events - mean x elsewhere (NaN-aware), against the same exact rotation of the label."""
    ok = np.isfinite(x)

    def d(lab):
        m = lab == 1
        return float(x[m & ok].mean() - x[~m & ok].mean())
    obs = d(e)
    null = np.array([d(np.roll(e, k)) for k in range(1, e.size)])
    return {"delta": obs, "event_mean": float(x[(e == 1) & ok].mean()), "other_mean": float(x[(e == 0) & ok].mean()),
            "n_event": int(((e == 1) & ok).sum()), "p50": float(np.percentile(null, 50)), "p95": float(np.percentile(null, 95)),
            "p5": float(np.percentile(null, 5)),
            "p_two_sided": float(min(1.0, 2 * min((1 + (null >= obs).sum()) / (1 + null.size), (1 + (null <= obs).sum()) / (1 + null.size))))}


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


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 5:
        return float("nan")
    ra, rb = pd.Series(a[ok]).rank().to_numpy(), pd.Series(b[ok]).rank().to_numpy()
    return float(np.corrcoef(ra, rb)[0, 1])


def holm(p: dict[str, float], alpha: float = 0.05) -> dict[str, bool]:
    order = sorted(p, key=p.get)
    out, ok = {}, True
    for i, k in enumerate(order):
        ok = ok and p[k] <= alpha / (len(order) - i)
        out[k] = ok
    return out


def g3(days: np.ndarray, net: np.ndarray) -> dict:
    yr = pd.Series(net).groupby([d[:4] for d in days]).sum()
    mo = pd.Series(net).groupby([d[:7] for d in days]).sum()
    tot = float(net.sum())
    best = yr.idxmax() if len(yr) else None
    ex_best = float(net[np.array([d[:4] != best for d in days])].sum()) if best else float("nan")
    share = float(mo.max() / tot) if tot > 0 else float("inf")
    return {"years_positive": int((yr > 0).sum()), "years": int(len(yr)), "best_year": best, "net_ex_best_year": ex_best,
            "max_month_share": share, "total_net": tot,
            "pass": bool((yr > 0).sum() >= YEARS_MIN and ex_best > 0 and tot > 0 and share <= MONTH_MAX)}


# ================================================================================ the cell
def evaluate_cell(f: pd.DataFrame, sets: dict[str, set[str]]) -> dict[str, Any]:
    f = f[~f["day"].isin(sets["drop"])].reset_index(drop=True)
    days = f["day"].tolist()
    e = np.array([1 if d in sets["event"] else 0 for d in days], dtype=np.int64)
    y = f["y"].to_numpy(float)
    rot = rotation(e, y)
    need(math.isclose(rot["offset0"], rot["A"], rel_tol=0, abs_tol=1e-12), "rotation offset 0 != observed")
    return {"f": f, "days": days, "e": e, "y": y, "rot": rot}


def trade_block(days: list[str], e: np.ndarray, y: np.ndarray, side: int) -> dict[str, Any]:
    m = e == 1
    g = side * y[m]
    net = g - COST
    d_ev = np.array(days)[m]
    dn = np.zeros(len(days))
    dn[m] = net
    dg = np.zeros(len(days))
    dg[m] = g
    eq = np.cumsum(dn)
    order = np.argsort(net)
    return {"side": "long" if side == 1 else "short", "gross": dist(g), "net": dist(net), "net_plus_one_tick": dist(net - TICK_USD),
            "nw_t_gross": nw_t(g), "daily_net_sharpe_sortino": sharpe_sortino(dn), "daily_gross_sharpe_sortino": sharpe_sortino(dg),
            "max_dd_usd": float((np.maximum.accumulate(eq) - eq).max()), "breakeven_cost": float(g.mean()),
            "exposure_sessions": int(m.sum()), "of_sessions": int(len(days)),
            "by_year": {k: float(v) for k, v in pd.Series(net).groupby([d[:4] for d in d_ev]).sum().items()},
            "top5": [(str(d_ev[i]), float(net[i])) for i in order[::-1][:5]],
            "bottom5": [(str(d_ev[i]), float(net[i])) for i in order[:5]], "g3": g3(d_ev, net), "daily_net": dn}


def subset_mean(days: list[str], y: np.ndarray, keep) -> dict:
    m = np.array([keep(d) for d in days])
    return dist(y[m])


# ================================================================================ run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    fx = load_fixture()
    wasde = set(pd.read_csv(WASDE, usecols=["ReleaseDate"], dtype=str, encoding="utf-8")["ReleaseDate"])
    bk = pd.read_csv(BOOKS, dtype={"session": str}, encoding="utf-8")
    cells, checks, pvals = {}, {}, {}
    for root in ROOTS:
        com = COM[root]
        b = pd.read_parquet(TMP / f"raw_{root}.parquet")
        q = session_quantities(b, root)
        med = check_units(q, root)
        brk_share = check_break(q, root)
        fq = q[(q["day"] >= FIRST) & (q["day"] <= LAST)]
        f = moves(q)
        min_gap = check_delivery(f, root)
        sets = event_sets(fx, com)
        cell = evaluate_cell(f, sets)
        days, e, y = cell["days"], cell["e"], cell["y"]
        rng = np.random.default_rng(768)
        samp = sorted(int(i) for i in rng.choice(len(days), size=40, replace=False))
        samp += [i for i in range(len(days)) if e[i] == 1][:20]
        lag_audit(days, e, com, samp)
        lost = sorted(d for d in sets["event"] if FIRST <= d <= LAST and d not in set(f["day"]) and d not in sets["drop"])
        pvals[root] = cell["rot"]["p_two_sided"]
        cells[root] = dict(cell, sets=sets, lost=lost)
        checks[root] = {"median_close_cents": med, "break_empty_share": brk_share, "min_days_to_first_notice": min_gap,
                        "sessions_extracted": int(len(fq)), "eligible": int(len(days)), "events": int(e.sum()),
                        "events_lost_cbot_shut_or_no_price": lost, "dropped_days": sorted(sets["drop"]),
                        "lag_audit_sessions": len(samp)}
    holm_ok = holm(pvals)
    res: dict[str, Any] = {"record": "D768", "cost_rt_usd": COST, "checks": checks, "cells": {}}
    for root in ROOTS:
        c = cells[root]
        days, e, y, f, sets, rot = c["days"], c["e"], c["y"], c["f"], c["sets"], c["rot"]
        outside = rot["A"] > rot["p97_5"] or rot["A"] < rot["p2_5"]
        g1 = bool(holm_ok[root] and outside)
        side = -1 if (g1 and rot["A"] < rot["p2_5"]) else 1      # long (the news's own direction) unless G1 passes short
        tb = trade_block(days, e, y, side)
        g2 = bool(g1 and tb["gross"]["mean"] >= COST and tb["nw_t_gross"] >= T_MIN)
        g3p = bool(g2 and tb["g3"]["pass"])
        reading = "NO DIRECTION" if not g1 else ("DIRECTION, NO PRIZE" if not g2 else ("EPISODIC" if not g3p else "PREMISE HOLDS"))
        gb, gn = f["g_break"].to_numpy(float), f["g_night"].to_numpy(float)
        ev_m = e == 1
        rho_ev, rho_ot = spearman(gb[ev_m], y[ev_m]), spearman(gb[~ev_m], y[~ev_m])
        fade = -np.sign(gb[ev_m]) * y[ev_m]
        absy = np.abs(y)
        size_null = np.array([absy[np.roll(e, k) == 1].mean() / absy[np.roll(e, k) == 0].mean() for k in range(1, e.size)])
        size_ratio = float(absy[ev_m].mean() / absy[~ev_m].mean())
        rho_b = {}
        dn = pd.Series(tb.pop("daily_net"), index=days)
        for nm, gbk in bk.groupby("book"):
            sb = gbk.groupby("session")["net"].sum()
            span = [d for d in days if sb.index.min() <= d <= sb.index.max()]
            s1 = dn.reindex(span).to_numpy()
            rho_b[nm] = float(np.corrcoef(s1, sb.reindex(span, fill_value=0.0).to_numpy())[0, 1]) if len(span) > 30 and s1.std() > 0 else None
        thu = lambda d: dt.date.fromisoformat(d).weekday() == 3
        son = lambda d: d[5:7] in ("09", "10", "11")
        res["cells"][root] = {
            "reading": reading, "G1": dict(rot, holm_reject=bool(holm_ok[root]), outside_band=bool(outside), passed=g1),
            "direction": tb["side"], "G2": {"gross_mean": tb["gross"]["mean"], "nw_t": tb["nw_t_gross"], "cost": COST, "passed": g2},
            "G3": dict(tb["g3"], passed=g3p), "trade": tb,
            "reported": {
                "is_it_news_break_gap": delta_rotation(e, gb), "anticipation_overnight": delta_rotation(e, gn),
                "china_days": subset_mean(days, y, lambda d: d in sets["china"]),
                "unknown_days": subset_mean(days, y, lambda d: d in sets["unknown"]),
                "big_sale_days_500kt": subset_mean(days, y, lambda d: d in sets["big"]),
                "placebo_destinations": {"y": subset_mean(days, y, lambda d: d in sets["placebo"]),
                                         "g_break": subset_mean(days, gb, lambda d: d in sets["placebo"])},
                "cancellations": {"y": subset_mean(days, y, lambda d: d in sets["cancel"]),
                                  "g_break": subset_mean(days, gb, lambda d: d in sets["cancel"])},
                "fade": {"rho_gbreak_y_events": rho_ev, "rho_gbreak_y_other": rho_ot, "fade_gross": dist(fade)},
                "size": {"ratio": size_ratio, "null_p50": float(np.percentile(size_null, 50)), "null_p95": float(np.percentile(size_null, 95)),
                         "rank": float((size_null < size_ratio).mean())},
                "eras": {nm: subset_mean(days, y, lambda d, a=a, b_=b_: d in sets["event"] and a <= d <= b_) for nm, a, b_ in ERAS},
                "thursday_events": subset_mean(days, y, lambda d: d in sets["event"] and thu(d)),
                "other_weekday_events": subset_mean(days, y, lambda d: d in sets["event"] and not thu(d)),
                "wasde_events": subset_mean(days, y, lambda d: d in sets["event"] and d in wasde),
                "ex_wasde_events": subset_mean(days, y, lambda d: d in sets["event"] and d not in wasde),
                "sep_nov_events": subset_mean(days, y, lambda d: d in sets["event"] and son(d)),
                "other_month_events": subset_mean(days, y, lambda d: d in sets["event"] and not son(d)),
                "sep_nov_non_event_days": subset_mean(days, y, lambda d: d not in sets["event"] and son(d)),
                "all_days_y": dist(y), "non_event_days_y": dist(y[~ev_m])},
            "rho_books": rho_b}
    zs, zc = cells["ZS"], cells["ZC"]
    both = set(zs["sets"]["event"]) & set(zc["sets"]["event"])
    res["both_cells_days"] = {"n": len(both), "ZS_y": subset_mean(zs["days"], zs["y"], lambda d: d in both),
                              "ZC_y": subset_mean(zc["days"], zc["y"], lambda d: d in both)}
    res.update({"runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "fixture_sha256": sha(FIX),
                "wall_s": round(time.time() - t0, 1)})
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    for root in ROOTS:
        r = res["cells"][root]
        g = r["G1"]
        print(f"[D768] {root}: {r['reading']}; A {g['A']:+.2f} (p2.5 {g['p2_5']:+.2f} p50 {g['p50']:+.2f} p97.5 {g['p97_5']:+.2f}; "
              f"p {g['p_two_sided']:.3f}); n_ev {checks[root]['events']} of {checks[root]['eligible']}; "
              f"{r['direction']} gross {r['G2']['gross_mean']:+.2f} NW t {r['G2']['nw_t']:.2f}")
        rb = r["reported"]["is_it_news_break_gap"]
        print(f"        break gap: events {rb['event_mean']:+.2f} vs other {rb['other_mean']:+.2f} (delta {rb['delta']:+.2f}, "
              f"p95 {rb['p95']:+.2f}, p {rb['p_two_sided']:.3f})")
    print(f"[D768] wall {res['wall_s']} s")
    return 0


# ================================================================================ self-test
def selftest() -> int:
    fails: list[str] = []

    def expect_raise(fn, label):
        try:
            fn()
            fails.append(f"{label} did not raise")
        except D768Error:
            pass

    # the clock
    if et_min("2021-01-15", 9, 30) != int(dt.datetime(2021, 1, 15, 14, 30, tzinfo=dt.timezone.utc).timestamp() // 60):
        fails.append("09:30 ET != 14:30 UTC in January")
    if et_min("2021-07-15", 9, 30) != int(dt.datetime(2021, 7, 15, 13, 30, tzinfo=dt.timezone.utc).timestamp() // 60):
        fails.append("09:30 ET != 13:30 UTC in July")
    # first notice day
    if fnd("ZSN3", "2023-05-02") != "2023-06-30":
        fails.append(f"FND of ZSN3 is {fnd('ZSN3', '2023-05-02')}")
    if fnd("ZCH1", "2020-12-10") != "2021-02-26":
        fails.append(f"FND of ZCH1 is {fnd('ZCH1', '2020-12-10')}")
    # synthetic minutes: two trade dates, check the quantities and the guards
    def bars(day: str, spec: list[tuple[int, int, float, float]], contract: str = "ZSN3") -> pd.DataFrame:
        rows = []
        for hh, mm, o, c in spec:
            cal = day if hh < 18 else (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
            ts = et_min(cal, hh, mm) * 60_000_000_000
            rows.append((ROOTS[0], contract, ts, day, o, c, 10))
        return pd.DataFrame(rows, columns=["root", "contract", "ts", "day", "open", "close", "volume"])
    d1 = bars("2021-03-01", [(20, 0, 1400, 1401), (8, 44, 1402, 1403), (9, 30, 1410, 1411), (14, 14, 1420, 1425), (14, 19, 1425, 1426)])
    d2 = bars("2021-03-02", [(20, 0, 1426, 1427), (8, 40, 1430, 1432), (9, 31, 1440, 1441), (14, 10, 1438, 1436), (14, 19, 1436, 1437)])
    q = session_quantities(pd.concat([d1, d2], ignore_index=True), "ZS")
    r1, r2 = q.iloc[0], q.iloc[1]
    if not (r1["O"] == 1410 and r1["P1415"] == 1425 and r1["P0845"] == 1403 and np.isnan(r1["Pprev"])):
        fails.append(f"day 1 quantities wrong: {r1.to_dict()}")
    if not (r2["O"] == 1440 and r2["P1415"] == 1436 and r2["P0845"] == 1432 and r2["Pprev"] == 1426):
        fails.append(f"day 2 quantities wrong: {r2.to_dict()}")
    m = moves(q.assign(day=["2021-03-01", "2021-03-02"]))
    if not (math.isclose(m["y"].iloc[0], 15 * USD_PER_CENT) and math.isclose(m["g_break"].iloc[1], 8 * USD_PER_CENT)
            and math.isclose(m["g_night"].iloc[1], 6 * USD_PER_CENT)):
        fails.append("sign in money: y / g_break / g_night do not pay a rise positively")
    # sign in money for the trade: a long gains when the price rises one cent, a short loses the same
    tb = trade_block(["2021-03-01"] * 3, np.array([1, 1, 1]), np.array([USD_PER_CENT] * 3), 1)
    ts_ = trade_block(["2021-03-01"] * 3, np.array([1, 1, 1]), np.array([USD_PER_CENT] * 3), -1)
    if not (tb["gross"]["mean"] == USD_PER_CENT and ts_["gross"]["mean"] == -USD_PER_CENT):
        fails.append("sign in money: the trade's gross is not +$5 long / -$5 short on a one-cent rise")
    # the guards raise
    expect_raise(lambda: session_quantities(d1.assign(ts=d1["ts"] + (SEAL_NS - int(d1["ts"].min()))), "ZS"), "the seal on a 2024 bar")
    two_contracts = pd.concat([d1.iloc[:2], d1.iloc[2:].assign(contract="ZSK3")], ignore_index=True)
    expect_raise(lambda: session_quantities(two_contracts, "ZS"), "the one-contract guard")
    expect_raise(lambda: session_quantities(d1.assign(ts=d1["ts"] // 1000), "ZS"), "the nanosecond guard")
    # units, the break and first notice raise on broken inputs, and pass on good ones
    try:
        check_units(q, "ZS"), check_break(q, "ZS"), check_delivery(m, "ZS")
    except D768Error as ex:
        fails.append(f"a guard raised on good synthetic data: {ex}")
    expect_raise(lambda: check_units(q.assign(P1415=q["P1415"] / 100), "ZS"), "the units guard on dollars-a-bushel prices")
    with_bar = bars("2021-03-01", [(20, 0, 1400, 1401), (8, 44, 1402, 1403), (9, 0, 1404, 1405), (9, 30, 1410, 1411), (14, 14, 1420, 1425)])
    expect_raise(lambda: check_break(session_quantities(with_bar, "ZS"), "ZS"), "the break guard on a bar at 09:00 ET")
    close_bar = bars("2021-03-01", [(20, 0, 1400, 1401), (8, 45, 1402, 1403), (9, 30, 1410, 1411), (14, 14, 1420, 1425)])
    try:
        check_break(session_quantities(close_bar, "ZS"), "ZS")
    except D768Error:
        fails.append("the break guard counted the overnight's closing bar at 08:45:00 (the interval is open at 08:45)")
    expect_raise(lambda: check_delivery(m.assign(contract="ZSH1"), "ZS"), "the delivery guard on a March contract traded in March")
    # the lag audit: the fixture text against flags; flags shifted to the next release must raise
    tmp = TMP / "selftest_fixture.csv"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text("date,slug,title_kind,kind,tonnes,commodity,destination,my,source,status,dateline,dateline_date\n"
                   "2021-03-01,a,announcement,sale,132000,soybeans,China,2020/2021,full,ok,none,\n"
                   "2021-03-03,b,announcement,sale,132000,corn,unknown destinations,2020/2021,full,ok,none,\n", encoding="utf-8")
    days = ["2021-03-01", "2021-03-02", "2021-03-03"]
    e_true = np.array([1, 0, 0])
    try:
        lag_audit(days, e_true, "soybeans", [0, 1, 2], tmp)
    except D768Error as ex:
        fails.append(f"lag audit raised on the truth: {ex}")
    expect_raise(lambda: lag_audit(days, np.roll(e_true, 1), "soybeans", [0, 1, 2], tmp), "the lag audit on flags shifted a day")
    # event sets: ambiguous datelines and same-day retractions are dropped, cancellations and restatements are not events
    fx = pd.DataFrame([
        dict(date="2016-04-14", slug="x", title_kind="announcement", kind="sale", tonnes="120000", commodity="soybeans",
             destination="China", my="", source="full", status="ok", dateline="mismatch", dateline_date="2016-04-15"),
        dict(date="2022-07-15", slug="y", title_kind="retraction", kind="restated", tonnes="133000", commodity="corn",
             destination="China", my="", source="full", status="ok", dateline="none", dateline_date=""),
        dict(date="2020-01-02", slug="z", title_kind="cancellation", kind="cancel", tonnes="100000", commodity="soybeans",
             destination="China", my="", source="full", status="ok", dateline="none", dateline_date="")])
    s_soy, s_corn = event_sets(fx, "soybeans"), event_sets(fx, "corn")
    if s_soy["drop"] != {"2016-04-14", "2016-04-15"} or "2022-07-15" not in s_corn["drop"] or "2020-01-02" in s_soy["event"] \
            or "2020-01-02" not in s_soy["cancel"] or s_corn["event"]:
        fails.append(f"event sets wrong: {s_soy} / {s_corn}")
    # the rotation: offset 0 reproduces A
    rng = np.random.default_rng(768)
    n = 2000
    e = (rng.random(n) < 0.22).astype(np.int64)
    y = rng.normal(0, 60, n)
    r = rotation(e, y)
    if not math.isclose(r["offset0"], r["A"], abs_tol=1e-12):
        fails.append("rotation offset 0 != A")
    # synthetic G1: planted drift passes; noise and a clustered label against a persistent drift fail about 95 %
    planted = rotation(e, y + 25 * e)
    if not (planted["A"] > planted["p97_5"]):
        fails.append(f"a planted +$25 event drift did not pass ({planted['A']:.2f} vs p97.5 {planted['p97_5']:.2f})")
    def g1_pass(e_, y_):
        rr = rotation(e_, y_)
        return rr["A"] > rr["p97_5"] or rr["A"] < rr["p2_5"]
    noise_pass = sum(g1_pass((rng.random(n) < 0.22).astype(np.int64), rng.normal(0, 60, n)) for _ in range(100))
    # clustered label (runs of event days) against an AR(1) drift that is independent of the label
    clus_pass = 0
    for _ in range(100):
        lab = np.zeros(n, dtype=np.int64)
        i = 0
        while i < n:
            if rng.random() < 0.06:
                L = int(rng.integers(3, 12))
                lab[i:i + L] = (rng.random(min(L, n - i)) < 0.7).astype(np.int64)
                i += L
            else:
                i += 1
        drift = np.zeros(n)
        for t in range(1, n):
            drift[t] = 0.98 * drift[t - 1] + rng.normal(0, 3)
        clus_pass += g1_pass(lab, drift + rng.normal(0, 60, n))
    # seasonal: the label concentrated in Sep-Nov against a Sep-Nov drift of +$8 (the G2 bar)
    sea_days = pd.bdate_range("2016-01-04", periods=n)
    son = np.isin(sea_days.month, [9, 10, 11])
    sea_pass = 0
    for _ in range(100):
        lab = (rng.random(n) < np.where(son, 0.45, 0.12)).astype(np.int64)
        sea_pass += g1_pass(lab, 8.0 * son + rng.normal(0, 60, n))
    print(f"  synthetic G1 passes: noise {noise_pass}/100, clustered label vs AR(1) drift {clus_pass}/100, "
          f"seasonal label vs seasonal +$8 drift {sea_pass}/100")
    if noise_pass > 10:
        fails.append(f"noise passed G1 {noise_pass}/100")
    if clus_pass > 10:
        fails.append(f"a clustered label against an independent persistent drift passed G1 {clus_pass}/100")
    if sea_pass > 10:
        fails.append(f"a seasonal label against a seasonal drift passed G1 {sea_pass}/100 (the rotation does not keep the season)")
    # holm
    if holm({"ZS": 0.02, "ZC": 0.04}) != {"ZS": True, "ZC": True} or holm({"ZS": 0.03, "ZC": 0.04}) != {"ZS": False, "ZC": False}:
        fails.append("holm wrong")
    tmp.unlink(missing_ok=True)
    if fails:
        for x in fails:
            print("  FAIL:", x)
        print("[D768] selftest: FAILED")
        return 1
    print("[D768] selftest: all passed")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--extract", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else extract() if a.extract else run())

"""D773 Stage 0: GLD creation/redemption flow and the London gold morning (prop book; GC scored at one MGC).

Pre-registration: docs/decisions/D773-STAGE-0-PRE-REG-gld-flow-and-the-london-gold-morning.md

    python scripts/stage0_d773_gld_flow.py --selftest
    python scripts/stage0_d773_gld_flow.py --extract     # GC front minutes, all hours, < 2024 (system python)
    python scripts/stage0_d773_gld_flow.py --run         # once

Trade date d (CME: ET date of wall time + 6 h). f_d = tonnes(t1) - tonnes(t2), t1 > t2 the two latest GLD dates with a
numeric holding strictly before d's ET calendar date. L0 = 08:00 London, FIX = 15:00 London (zoneinfo). E = open of the
first GC bar in [L0, L0+5]; y = (P(FIX-1) - E) x $10 per MGC. Exact rotation of f against y; walk-forward top third of
|f|; position sign(rho) x sign(f) (expected sign +1 when G1 fails); cost $5.93 (D751).
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
SPEC = REPO / "docs" / "decisions" / "D773-STAGE-0-PRE-REG-gld-flow-and-the-london-gold-morning.md"
OUT = REPO / "data" / "stage0_d773_gld_flow.json"
GLD = REPO / "data" / "fixtures" / "gld_holdings_daily.csv"
BOOKS = REPO / "data" / "d748_component_books.csv"
TMP = Path(os.environ.get("D773_TMP", str(REPO / "temp" / "d773")))
SEAL = "2024-01-01"
SEAL_NS = int(pd.Timestamp(SEAL, tz="UTC").value)
XLO_NS = int(pd.Timestamp("2015-05-01", tz="UTC").value)
NY, LDN = ZoneInfo("America/New_York"), ZoneInfo("Europe/London")
ROOTS = ("GC",)
MULT, COST, TICK_USD = 10.0, 5.93, 1.00          # MGC: 10 oz, $1 a tick (0.10/oz); D751's cost line
STALE, TERC_WF, T_MIN, YEARS_MIN = 10, 250, 2.0, 5
MONTH_CODE = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
WORKERS = 4


class D773Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D773Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


# ================================================================================ clock
def tz_min(day: str, hh: int, mm: int, tz: ZoneInfo) -> int:
    d = dt.datetime(int(day[:4]), int(day[5:7]), int(day[8:10]), hh, mm, tzinfo=tz).astimezone(dt.timezone.utc)
    return int(d.timestamp() // 60)


def et_hm(utc_min: int) -> tuple[int, int]:
    w = dt.datetime.fromtimestamp(utc_min * 60, tz=dt.timezone.utc).astimezone(NY)
    return w.hour, w.minute


def trade_day_of(ts_ns: np.ndarray) -> np.ndarray:
    t = pd.to_datetime(ts_ns, utc=True).tz_convert(NY).tz_localize(None)
    wall = np.asarray((t - pd.Timestamp("1970-01-01")) // pd.Timedelta(minutes=1), dtype=np.int64)
    return ((wall + 360) // 1440).astype(np.int64)


# ================================================================================ extraction (D765/D768/D769's, restated)
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
    x = df.sort_values("ts").reset_index(drop=True)
    x.to_parquet(TMP / "raw_GC.parquet", index=False)
    print(f"GC: {len(x):,} front minutes, {x['day'].min()} -> {x['day'].max()}; extract {(time.time() - t0) / 60:.1f} min; "
          f"serial re-decode of {raw[i].name} == process result", flush=True)
    return 0


# ================================================================================ prices
class Bars:
    def __init__(self, b: pd.DataFrame):
        need(bool((b["ts"] > 10**18).all()), "a timestamp is not in nanoseconds")
        need(bool((b["ts"] < SEAL_NS).all()) and bool((b["day"] < SEAL).all()), "seal: a GC bar on or after 2024")
        self.S = (b["ts"].to_numpy(np.int64) // 60_000_000_000).astype(np.int64)
        need(bool(np.all(np.diff(self.S) > 0)), "bars not strictly ordered")
        self.O, self.C, self.K = b["open"].to_numpy(float), b["close"].to_numpy(float), b["contract"].to_numpy()

    def before(self, t: int, stale: int = STALE) -> int | None:
        i = int(np.searchsorted(self.S, t, side="left")) - 1
        return i if i >= 0 and self.S[i] >= t - stale else None

    def open_in(self, t0: int, t1: int) -> int | None:
        j = int(np.searchsorted(self.S, t0, side="left"))
        return j if j < self.S.size and self.S[j] <= t1 else None


def check_units(close: np.ndarray) -> float:
    med = float(np.median(close))
    need(1000.0 <= med <= 2200.0, f"units: the median GC close {med} is outside [1000, 2200] $/oz")
    return med


def first_notice(contract: str, day: str) -> dt.date:
    mo, yd = MONTH_CODE[contract[2]], int(contract[3:]) % 10
    y0 = int(day[:4])
    y = y0 - y0 % 10 + yd
    if y < y0:
        y += 10
    d = dt.date(y, mo, 1) - dt.timedelta(days=1)
    while d.weekday() > 4:
        d -= dt.timedelta(days=1)
    return d


# ================================================================================ the signal
def load_gld(path: Path = GLD) -> pd.DataFrame:
    g = pd.read_csv(path, dtype={"date": str}, encoding="utf-8")
    need(bool((g["date"] < SEAL).all()), "seal: a GLD row dated 2024 or later")
    g = g[pd.to_numeric(g["tonnes"], errors="coerce").notna()].copy()
    g["tonnes"] = g["tonnes"].astype(float)
    need(bool(g["tonnes"].between(500, 1500).all()), "units: tonnes outside [500, 1500]")
    return g.sort_values("date").reset_index(drop=True)


def signal_for(dates: np.ndarray, tonnes: np.ndarray, day: str, include_same_day: bool = False) -> tuple[float, str]:
    """f for trade date `day`: the change between the two latest holdings dates strictly before it (the break adds the day)."""
    k = int(np.searchsorted(dates, day, side="right" if include_same_day else "left"))
    if k < 2:
        return float("nan"), ""
    return float(tonnes[k - 1] - tonnes[k - 2]), str(dates[k - 1])


def flags_by_csv(path: Path, days: list[str]) -> list[float]:
    """Second implementation (lag audit): the fixture's text through the csv module, no pandas, no searchsorted."""
    rows = []
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            try:
                rows.append((r["date"], float(r["tonnes"])))
            except ValueError:
                pass
    out = []
    for d in days:
        prior = [x for x in rows if x[0] < d]
        out.append(prior[-1][1] - prior[-2][1] if len(prior) >= 2 else float("nan"))
    return out


def lag_audit(days: list[str], f: np.ndarray, sample: list[int], path: Path = GLD) -> None:
    ref = flags_by_csv(path, [days[i] for i in sample])
    for i, v in zip(sample, ref):
        need(math.isclose(f[i], v, abs_tol=1e-9), f"lag audit: f on {days[i]} is {f[i]}, the fixture text gives {v}")


# ================================================================================ statistics
def ranks(x: np.ndarray) -> np.ndarray:
    return pd.Series(x).rank().to_numpy(float)


def spearman(a, b) -> float:
    """Pearson of ranks over finite pairs (no scipy on the system python)."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b)
    if ok.sum() < 5:
        return float("nan")
    return float(np.corrcoef(ranks(a[ok]), ranks(b[ok]))[0, 1])


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


def position(rho_sign: int, f: np.ndarray) -> np.ndarray:
    return rho_sign * np.sign(f)


# ================================================================================ outcomes
def day_outcomes(B: Bars, d: str) -> dict:
    L0, FIX = tz_min(d, 8, 0, LDN), tz_min(d, 15, 0, LDN)
    out = {"y": np.nan, "y_auc": np.nan, "y_after": np.nan, "y_us": np.nan, "y_et": np.nan, "contract": "", "entry_lag": -1,
           "mismatch": et_hm(FIX) != (10, 0)}
    j = B.open_in(L0, L0 + 5)
    if j is None:
        return out
    e, kc = float(B.O[j]), B.K[j]
    out["entry_lag"], out["contract"] = int(B.S[j] - L0), str(kc)

    def P(t):
        i = B.before(t)
        return float(B.C[i]) if i is not None and B.K[i] == kc else np.nan
    out["y"] = (P(FIX - 1) - e) * MULT
    out["y_auc"] = (P(FIX + 5) - P(FIX - 5)) * MULT
    out["y_after"] = (P(FIX + 30) - P(FIX + 5)) * MULT
    out["y_us"] = (P(FIX - 1) - P(tz_min(d, 9, 30, NY))) * MULT
    j2 = B.open_in(tz_min(d, 3, 0, NY), tz_min(d, 3, 0, NY) + 5)       # the fixed ET clock (D751's N3 control)
    if j2 is not None and B.K[j2] == kc:
        out["y_et"] = (P(tz_min(d, 10, 0, NY) - 1) - float(B.O[j2])) * MULT
    return out


# ================================================================================ run
def run() -> int:
    need(not OUT.exists(), f"{OUT.name} exists: run-once")
    t0 = time.time()
    b = pd.read_parquet(TMP / "raw_GC.parquet")
    B = Bars(b)
    med = check_units(B.C)
    g = load_gld()
    gd, gt = g["date"].to_numpy(), g["tonnes"].to_numpy()
    prem = dict(zip(g["date"], pd.to_numeric(g["premium_pct"], errors="coerce")))
    tdays = sorted(d for d in set(b["day"]) if "2015-06-03" <= d <= "2023-12-29" and dt.date.fromisoformat(d).weekday() < 5)
    rows = []
    for d in tdays:
        f, t1 = signal_for(gd, gt, d)
        need(t1 == "" or t1 < d, f"lag: holdings dated {t1} used on {d}")
        k = int(np.searchsorted(gd, d, side="left"))
        flow_d = float(gt[k] - gt[k - 1]) if k < gd.size and gd[k] == d and k >= 1 else np.nan
        rows.append({"day": d, "f": f, "t1": t1, "flow_same_day": flow_d, "prem_prev": prem.get(t1, np.nan), **day_outcomes(B, d)})
    D = pd.DataFrame(rows)
    D = D[np.isfinite(D["f"]) & np.isfinite(D["y"])].reset_index(drop=True)
    need(bool((D["entry_lag"] >= 0).all()), "lag: an entry before the London open")
    gaps = [(first_notice(k, d) - dt.date.fromisoformat(d)).days for d, k in zip(D["day"], D["contract"])]
    need(min(gaps) > 0, "delivery: a GC front on or after its first notice day")
    days, f, y = D["day"].tolist(), D["f"].to_numpy(), D["y"].to_numpy()
    rng = np.random.default_rng(773)
    samp = sorted(int(i) for i in rng.choice(len(days), size=40, replace=False))
    lag_audit(days, f, samp)
    g1 = rot_spearman(f, y)
    need(math.isclose(g1["offset0"], g1["rho"], abs_tol=1e-12), "rotation offset 0 != observed")
    passed1 = g1["p_two_sided"] < 0.05
    rho_sign = int(np.sign(g1["rho"])) if passed1 else 1
    tt = top_third(f)
    pos = position(rho_sign, f)
    gr = (pos * y)[tt]
    net = gr - COST
    d_tt = np.array(days)[tt]
    yr = pd.Series(net).groupby([x[:4] for x in d_tt]).sum()
    full_years = yr[[k for k in yr.index if "2016" <= k <= "2023"]]
    best = yr.idxmax() if len(yr) else None
    ex_best = float(net[np.array([x[:4] != best for x in d_tt])].sum()) if best else float("nan")
    g2 = bool(passed1 and gr.size and gr.mean() >= COST and nw_t(gr) >= T_MIN)
    g3 = bool(g2 and (full_years > 0).sum() >= YEARS_MIN and ex_best > 0)
    reading = "NO DIRECTION" if not passed1 else ("DIRECTION, NO PRIZE" if not g2 else ("EPISODIC" if not g3 else "PREMISE HOLDS"))
    dn = np.zeros(len(days))
    dn[tt] = net
    dg = np.zeros(len(days))
    dg[tt] = gr
    eq = np.cumsum(dn)
    order = np.argsort(net)
    fl = D["flow_same_day"].to_numpy()
    win = {}
    for col in ("y_auc", "y_after", "y_us"):
        v = D[col].to_numpy()
        ok = np.isfinite(v)
        win[col] = {"rho": spearman(f[ok], v[ok]), "n": int(ok.sum()),
                    "top_third_gross": dist((pos * v)[tt & ok])}
    mm = D["mismatch"].to_numpy(bool)
    yet = D["y_et"].to_numpy()
    q = pd.qcut(np.abs(f), 5, labels=False, duplicates="drop")
    bk = pd.read_csv(BOOKS, dtype={"session": str}, encoding="utf-8")
    rho_b = {}
    dns = pd.Series(dn, index=days)
    for nm, gbk in bk.groupby("book"):
        sb = gbk.groupby("session")["net"].sum()
        span = [x for x in days if sb.index.min() <= x <= sb.index.max()]
        s1 = dns.reindex(span).to_numpy()
        rho_b[nm] = float(np.corrcoef(s1, sb.reindex(span, fill_value=0.0).to_numpy())[0, 1]) if len(span) > 30 and s1.std() > 0 else None
    res: dict[str, Any] = {
        "record": "D773", "reading": reading,
        "checks": {"median_gc_close": med, "eligible_days": len(days), "first": days[0], "last": days[-1],
                   "min_days_to_first_notice": int(min(gaps)), "lag_audit_days": len(samp), "mismatch_days": int(mm.sum())},
        "G1": dict(g1, passed=bool(passed1)),
        "G2": {"direction_sign": rho_sign, "trades": int(tt.sum()), "gross": dist(gr), "nw_t": nw_t(gr) if gr.size > 5 else None,
               "cost": COST, "passed": g2},
        "G3": {"net_by_year": {k: float(v) for k, v in yr.items()}, "full_years_positive": int((full_years > 0).sum()),
               "best_year": best, "net_ex_best_year": ex_best, "passed": g3},
        "trade": {"net": dist(net), "net_plus_one_tick": dist(net - TICK_USD), "daily_net_sharpe_sortino": sharpe_sortino(dn),
                  "daily_gross_sharpe_sortino": sharpe_sortino(dg), "max_dd_usd": float((np.maximum.accumulate(eq) - eq).max()),
                  "breakeven_cost": float(gr.mean()) if gr.size else None,
                  "inflow_trades": dist(gr[f[tt] > 0]), "outflow_trades": dist(gr[f[tt] < 0]),
                  "top5": [(str(d_tt[i]), float(net[i])) for i in order[::-1][:5]],
                  "bottom5": [(str(d_tt[i]), float(net[i])) for i in order[:5]], "rho_books": rho_b},
        "reported": {
            "flow_ar1_eligible": float(np.corrcoef(f[1:], f[:-1])[0, 1]),
            "rho_f_vs_same_day_flow": spearman(f, fl),
            "diagnostic_same_day_flow_vs_y_LOOKAHEAD": spearman(fl, y),
            "windows": win,
            "premium_proxy_rho": spearman(D["prem_prev"].to_numpy(), y),
            "clock_control_mismatch": {"n": int(mm.sum()), "rho_london_clock": spearman(f[mm], y[mm]),
                                       "rho_fixed_et_clock": spearman(f[mm], yet[mm])},
            "by_year_rho": {k: spearman(f[np.array([x[:4] == k for x in days])], y[np.array([x[:4] == k for x in days])])
                            for k in sorted({x[:4] for x in days})},
            "quintiles_mean_signed_y": {int(k): float(np.mean(np.sign(f[q == k]) * y[q == k])) for k in sorted(set(q))},
            "inflow_days_y": dist(y[f > 0]), "outflow_days_y": dist(y[f < 0]), "zero_flow_days_y": dist(y[f == 0]),
            "all_days_y": dist(y)},
        "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "gld_sha256": sha(GLD),
        "wall_s": round(time.time() - t0, 1)}
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1, default=lambda o: o.item() if hasattr(o, "item") else str(o))
    r = res["reported"]
    print(f"[D773] {reading}; rho {g1['rho']:+.4f} (p2.5 {g1['p2_5']:+.4f} p97.5 {g1['p97_5']:+.4f}; p {g1['p_two_sided']:.3f}); "
          f"n {len(days)}; top-third trade ({'+' if rho_sign > 0 else '-'}) gross {dist(gr).get('mean', float('nan')):+.2f} "
          f"t_NW {res['G2']['nw_t']}")
    print(f"        flow AR(1) {r['flow_ar1_eligible']:+.3f}; same-day diagnostic rho {r['diagnostic_same_day_flow_vs_y_LOOKAHEAD']:+.3f}; "
          f"premium proxy rho {r['premium_proxy_rho']:+.3f}; windows " + " ".join(f"{k}:{v['rho']:+.3f}" for k, v in r['windows'].items()))
    print(f"[D773] wall {res['wall_s']} s")
    return 0


# ================================================================================ self-test
def selftest() -> int:
    fails: list[str] = []

    def expect_raise(fn, label):
        try:
            fn()
            fails.append(f"{label} did not raise")
        except D773Error:
            pass

    # the clock
    for day, want in (("2021-01-15", (10, 0)), ("2021-07-15", (10, 0)), ("2021-03-22", (11, 0))):
        if et_hm(tz_min(day, 15, 0, LDN)) != want:
            fails.append(f"15:00 London on {day} maps to {et_hm(tz_min(day, 15, 0, LDN))} ET, not {want}")
    if et_hm(tz_min("2021-01-15", 8, 0, LDN)) != (3, 0):
        fails.append("08:00 London on 2021-01-15 is not 03:00 ET")
    if trade_day_of(np.array([tz_min("2021-01-15", 8, 0, LDN) * 60_000_000_000]))[0] != (dt.date(2021, 1, 15) - dt.date(1970, 1, 1)).days:
        fails.append("the London morning's CME trade date is not its calendar date")
    # first notice: GCJ1 -> the last business day of March 2021 (Wed 03-31)
    if first_notice("GCJ1", "2021-02-10") != dt.date(2021, 3, 31):
        fails.append(f"GCJ1 first notice {first_notice('GCJ1', '2021-02-10')}")
    # sign in money and the position rule
    if not math.isclose(position(1, np.array([3.0]))[0] * 1.0 * MULT, 10.0):
        fails.append("sign in money: a long MGC on +$1/oz does not pay +$10")
    if position(1, np.array([-2.0]))[0] != -1:
        fails.append("position: an outflow with the expected sign is not a short")
    # the signal and its lag audit
    tmp = TMP / "selftest_gld.csv"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text("date,tonnes\n2021-03-01,1000\n2021-03-02,1004\n2021-03-03,1001\n2021-03-04,US Holiday\n2021-03-05,1010\n",
                   encoding="utf-8")
    gg = load_gld(tmp)
    gd, gt = gg["date"].to_numpy(), gg["tonnes"].to_numpy()
    days = ["2021-03-03", "2021-03-04", "2021-03-05", "2021-03-08"]
    fv = np.array([signal_for(gd, gt, d)[0] for d in days])
    if not np.allclose(fv, [4.0, -3.0, -3.0, 9.0]):
        fails.append(f"signal values wrong: {fv}")
    try:
        lag_audit(days, fv, [0, 1, 2, 3], tmp)
    except D773Error as ex:
        fails.append(f"lag audit raised on the truth: {ex}")
    leak = np.array([signal_for(gd, gt, d, include_same_day=True)[0] for d in days])
    expect_raise(lambda: lag_audit(days, leak, [0, 1, 2, 3], tmp), "the lag audit when the same day's holdings are used")
    tmp24 = tmp.with_name("selftest_gld_2024.csv")
    tmp24.write_text("date,tonnes\n2023-12-29,900\n2024-01-02,900\n", encoding="utf-8")
    expect_raise(lambda: load_gld(tmp24), "the seal on a 2024 holdings row")
    expect_raise(lambda: load_gld(tmp.with_name("selftest_gld_units.csv")) if tmp.with_name("selftest_gld_units.csv").write_text(
        "date,tonnes\n2021-03-01,1.0\n", encoding="utf-8") else None, "the units guard on tonnes")
    # guards
    good = pd.DataFrame({"root": "GC", "contract": "GCJ1", "ts": np.array([1_613_000_000, 1_613_000_060]) * 1_000_000_000,
                         "day": "2021-02-11", "open": [1830.0, 1830.5], "close": [1830.5, 1831.0]})
    try:
        Bars(good)
        check_units(np.array([1830.0, 1831.0]))
    except D773Error as ex:
        fails.append(f"a guard raised on good input: {ex}")
    expect_raise(lambda: Bars(good.assign(ts=good["ts"] + (SEAL_NS - int(good["ts"].min())))), "the seal on a 2024 bar")
    expect_raise(lambda: Bars(good.assign(ts=good["ts"] // 1000)), "the nanosecond guard")
    expect_raise(lambda: check_units(np.array([18.3, 18.4])), "the units guard on gold in hundreds")
    # rotation, spearman and the synthetic G1
    rng = np.random.default_rng(773)
    s, yv = rng.normal(0, 1, 2000), rng.normal(0, 1, 2000)
    gx = rot_spearman(s, yv)
    if not (math.isclose(gx["offset0"], gx["rho"], abs_tol=1e-12) and math.isclose(spearman(s, yv), gx["rho"], abs_tol=1e-12)):
        fails.append("rotation offset 0 or the local spearman disagree with rho")
    if rot_spearman(s, 0.1 * s + yv)["p_two_sided"] >= 0.05:
        fails.append("a planted rho ~0.1 did not pass")
    noise = sum(rot_spearman(rng.normal(0, 1, 2000), rng.normal(0, 1, 2000))["p_two_sided"] < 0.05 for _ in range(100))
    ar = 0
    for _ in range(100):
        a, e = np.zeros(2000), rng.normal(0, 1, 2000)
        for t in range(1, 2000):
            a[t] = 0.25 * a[t - 1] + e[t]
        ar += rot_spearman(a, rng.normal(0, 1, 2000))["p_two_sided"] < 0.05
    print(f"  synthetic G1 passes: noise {noise}/100, AR(1) 0.25 signal vs independent returns {ar}/100")
    if noise > 10 or ar > 10:
        fails.append(f"false passes too frequent: noise {noise}, AR {ar}")
    if not top_third(np.r_[np.full(300, 1.0), 100.0])[-1] or top_third(np.r_[np.full(300, 1.0), 1.0])[-1]:
        fails.append("top-third threshold wrong")
    for p in (tmp, tmp24, tmp.with_name("selftest_gld_units.csv")):
        p.unlink(missing_ok=True)
    if fails:
        for x in fails:
            print("  FAIL:", x)
        print("[D773] selftest: FAILED")
        return 1
    print("[D773] selftest: all passed")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    gx = ap.add_mutually_exclusive_group(required=True)
    gx.add_argument("--selftest", action="store_true")
    gx.add_argument("--extract", action="store_true")
    gx.add_argument("--run", action="store_true")
    a = ap.parse_args()
    sys.exit(selftest() if a.selftest else extract() if a.extract else run())

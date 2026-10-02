"""D761 Stage 0: round-number stop cascades outside US hours, on M6E and MBT (MGC reported).
Spec: docs/decisions/D761-STAGE-0-PRE-REG-round-number-stop-cascades.md.

    python scripts/stage0_d761_round_number_cascades.py --selftest     # SYSTEM interpreter (databento, pyarrow)
    python scripts/stage0_d761_round_number_cascades.py --extract      # 6E / GC front (+6E next) minutes, all hours, < 2024
    python scripts/stage0_d761_round_number_cascades.py --run --lines temp/d755_other_lines.csv

Prices are held in integer units of each futures tick (6E 0.00005, GC $0.10, BTC $5), so every level, offset and
crossing is exact integer arithmetic. Levels are spot-equivalent: L_fut = L_spot + basis, the basis frozen per session
from the PRIOR session (6E: the front/next calendar spread scaled to expiry; BTC: CME minus Binance BTCUSDT spot; GC:
the futures grid, basis 0). Nothing dated 2024-01-01 or later is read.
"""
from __future__ import annotations

import argparse
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
SPEC = REPO / "docs" / "decisions" / "D761-STAGE-0-PRE-REG-round-number-stop-cascades.md"
OUT = REPO / "data" / "stage0_d761_round_number_cascades.json"
TMP = Path(os.environ.get("D761_TMP", str(REPO / "temp" / "d761")))     # the override is for the synthetic smoke test
SEAL = "2024-01-01"
SEAL_NS = int(pd.Timestamp(SEAL, tz="UTC").value)
NY = ZoneInfo("America/New_York")
EPOCH = dt.datetime(1970, 1, 1)
WORKERS = 8
MONTHS = "FGHJKMNQUVXZ"

# unit = the futures price tick; mtick = the traded micro's tick in units; usd = $ per unit at one micro
CELLS: dict[str, dict[str, Any]] = {
    "m6e": dict(root="6E", unit=0.00005, mtick=2, usd=0.00005 * 12500, spacing=100, band=20, step=2, half=[50],
                cost=3.0 + 1.105885654136043 * 1.25, basis="calendar", lo="2010-06-01", primary=True),
    "mbt": dict(root="BTC", unit=5.0, mtick=1, usd=5.0 * 0.1, spacing=200, band=40, step=2, half=[100],
                cost=3.0 + 2.6161168726417716 * 0.5, basis="binance", lo="2018-01-01", primary=True),
    "mgc": dict(root="GC", unit=0.10, mtick=1, usd=0.10 * 10, spacing=100, band=10, step=1, half=[30, 40, 60, 70],
                cost=3.0 + 2.9334505021406643 * 1.0, basis="none", lo="2010-06-01", primary=False),
    "m6e_fut": dict(root="6E", unit=0.00005, mtick=2, usd=0.00005 * 12500, spacing=100, band=20, step=2, half=[50],
                    cost=3.0 + 1.105885654136043 * 1.25, basis="none", lo="2010-06-01", primary=False),
}
WINDOWS = {"asia": ("18:30", "02:00"), "london": ("02:00", "08:00"), "ny_am": ("09:00", "12:30"), "ny_pm": ("12:30", "16:00")}
HOLD, BOUNCE_H, LOOK = 30, 15, 60
SLIPS = (1, 2, 4)


class D761Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D761Error(msg)


# ================================================================================ the clock
def to_wall(ts_ns: np.ndarray) -> np.ndarray:
    """ET wall-clock minutes since 1970 (naive), by zoneinfo."""
    t = pd.to_datetime(ts_ns, utc=True).tz_convert(NY).tz_localize(None)
    return np.asarray((t - pd.Timestamp(EPOCH)) // pd.Timedelta(minutes=1), dtype=np.int64)


def _nth_sunday(y: int, m: int, n: int) -> dt.date:
    d = dt.date(y, m, 1)
    d += dt.timedelta(days=(6 - d.weekday()) % 7)
    return d + dt.timedelta(weeks=n - 1)


def to_wall_by_rule(ts_ns: np.ndarray) -> np.ndarray:
    t = pd.to_datetime(ts_ns, utc=True).tz_localize(None)
    yrs = np.asarray(t.year)
    st = {y: pd.Timestamp(_nth_sunday(y, 3, 2)) + pd.Timedelta(hours=7) for y in set(yrs.tolist())}
    en = {y: pd.Timestamp(_nth_sunday(y, 11, 1)) + pd.Timedelta(hours=6) for y in set(yrs.tolist())}
    s = pd.DatetimeIndex([st[y] for y in yrs])
    e = pd.DatetimeIndex([en[y] for y in yrs])
    off = np.where((t >= s) & (t < e), -4, -5)
    loc = t + pd.to_timedelta(off, unit="h")
    return np.asarray((loc - pd.Timestamp(EPOCH)) // pd.Timedelta(minutes=1), dtype=np.int64)


def wall(day: str, hhmm: str, days_back: int = 0) -> int:
    d = dt.date.fromisoformat(day) - dt.timedelta(days=days_back)
    h, m = (int(x) for x in hhmm.split(":"))
    return int((dt.datetime(d.year, d.month, d.day, h, m) - EPOCH).total_seconds() // 60)


def trade_day(wall_min: np.ndarray) -> np.ndarray:
    """CME trade date: the ET date of wall time + 6 hours (18:00 ET opens the next date's session)."""
    return ((wall_min + 360) // 1440).astype(np.int64)


def day_str(dn: int) -> str:
    return (EPOCH + dt.timedelta(days=int(dn))).strftime("%Y-%m-%d")


def window_bounds(dn: int, w: str) -> tuple[int, int]:
    a, b = WINDOWS[w]
    d = day_str(dn)
    t0 = wall(d, a, 1) if a >= "18:00" else wall(d, a)
    t1 = wall(d, b, 1) if b >= "18:00" and b > a else wall(d, b)
    return t0, t1


# ================================================================================ contracts
def expiry_6e(code: str, near: dt.date) -> dt.date:
    """6E: two business days before the third Wednesday of the contract month (holidays ignored)."""
    mon = MONTHS.index(code[-2]) + 1
    dig = int(code[-1])
    yr = next(y for y in range(near.year - 1, near.year + 10) if y % 10 == dig)
    d = dt.date(yr, mon, 1)
    d += dt.timedelta(days=(2 - d.weekday()) % 7)
    d += dt.timedelta(weeks=2)
    k = 0
    while k < 2:
        d -= dt.timedelta(days=1)
        if d.weekday() < 5:
            k += 1
    return d


def next_6e(code: str) -> str:
    q = "HMUZ"
    m = code[-2]
    dig = int(code[-1])
    i = q.index(m)
    return code[:-2] + (q[i + 1] + str(dig) if i < 3 else "H" + str((dig + 1) % 10))


# ================================================================================ extraction
def _front_map() -> dict[tuple[str, str], str]:
    import forward_f2_c1_ledgers as FW
    bh = pd.read_csv(io.BytesIO(FW.restrict_text(MAIN_DATA / "fixtures" / "fut_breadth_hourly.csv.gz", 1, SEAL)),
                     usecols=["root", "day", "contract"], dtype={"day": str}, encoding="utf-8")
    bh = bh[bh["root"].isin(["6E", "GC"])]
    return {(r, d): c for r, d, c in zip(bh["root"], bh["day"], bh["contract"])}


def _extract_file(path: str) -> pd.DataFrame | None:
    import databento as db
    import build_fut_breadth_hourly as BH
    fm = _front_map()
    store = db.DBNStore.from_file(path)
    w = BH.ids_of(store)
    if w is None:
        return None
    w = w[w["root"].isin(["6E", "GC"])]
    if len(w) == 0:
        return None
    parts = []
    for arr in store.to_ndarray(count=BH.CHUNK):
        a = arr[np.isin(arr["instrument_id"], w["iid"].to_numpy(np.uint32)) & (arr["ts_event"] < SEAL_NS)]
        if a.size == 0:
            continue
        raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "ts": a["ts_event"].astype(np.int64),
                            "open": a["open"] * BH.PX, "high": a["high"] * BH.PX, "low": a["low"] * BH.PX,
                            "close": a["close"] * BH.PX, "volume": a["volume"].astype(np.int64)})
        j = raw.merge(w, on="iid", how="inner")
        j = j[(j["ts"].astype(np.uint64) >= j["w0"]) & (j["ts"].astype(np.uint64) < j["w1"])]
        if len(j) == 0:
            continue
        dn = trade_day(to_wall(j["ts"].to_numpy()))
        j = j.assign(dn=dn).drop(columns=["iid", "w0", "w1"])
        # the front (and 6E's next) per (root, trade date), matched by a merge on the unique keys, not per row
        keys = j[["root", "dn"]].drop_duplicates()
        keys["day"] = np.asarray(pd.to_datetime(keys["dn"].to_numpy(), unit="D").strftime("%Y-%m-%d"))
        keys["front"] = [fm.get((r, d), "") for r, d in zip(keys["root"], keys["day"])]
        keys["next"] = [next_6e(f) if (r == "6E" and f) else "" for r, f in zip(keys["root"], keys["front"])]
        j = j.merge(keys, on=["root", "dn"], how="left")
        is_front = j["contract"].to_numpy() == j["front"].to_numpy()
        is_next = (j["contract"].to_numpy() == j["next"].to_numpy()) & (j["next"].to_numpy() != "")
        keep = is_front | is_next
        if not keep.any():
            continue
        k = j[keep]
        parts.append(pd.DataFrame({"root": k["root"].to_numpy(), "leg": np.where(is_next[keep], "next", "front"),
                                   "contract": k["contract"].to_numpy(), "ts": k["ts"].to_numpy(), "day": k["day"].to_numpy(),
                                   "open": k["open"].to_numpy(), "high": k["high"].to_numpy(), "low": k["low"].to_numpy(),
                                   "close": k["close"].to_numpy(), "volume": k["volume"].to_numpy()}))
        del j, k
    return pd.concat(parts, ignore_index=True) if parts else None


def extract() -> int:
    raw = sorted(p for d in sorted((MAIN_DATA / "raw" / "databento").glob("GLBX-*")) for p in d.glob("*.ohlcv-1m.dbn.zst"))
    print(f"{len(raw)} ohlcv-1m files", flush=True)
    t0 = time.time()
    with ProcessPoolExecutor(4) as ex:                                  # 8 decoders exhausted memory (2026-10-02)
        got = [g for g in ex.map(_extract_file, [str(p) for p in raw]) if g is not None]
    df = pd.concat(got, ignore_index=True)
    need(bool((df["ts"] < SEAL_NS).all()) and bool((df["day"] < SEAL).all()), "seal: a minute on or after 2024-01-01")
    need(not df.duplicated(["root", "leg", "ts"]).any(), "duplicate minutes for a (root, leg)")
    TMP.mkdir(parents=True, exist_ok=True)
    for r in ("6E", "GC"):
        x = df[df["root"] == r].sort_values(["leg", "ts"])
        x.to_parquet(TMP / f"raw_{r}.parquet", index=False)
        print(f"{r}: {len(x):,} rows ({(x['leg'] == 'front').sum():,} front), {x['day'].min()} -> {x['day'].max()}", flush=True)
    print(f"extract: {(time.time() - t0) / 60:.1f} min", flush=True)
    return 0


# ================================================================================ cell arrays
def _bars(cell: str) -> pd.DataFrame:
    c = CELLS[cell]
    if c["root"] == "BTC":
        import forward_f2_c1_ledgers as FW
        b = pd.read_csv(io.BytesIO(FW.restrict_text(MAIN_DATA / "fixtures" / "fut_btc_1m.csv.gz", 1, SEAL)),
                        dtype={"day": str}, encoding="utf-8")
        b = b[(b["root"] == "BTC") & (b["day"] < SEAL)]
        b = b.assign(ts=pd.to_datetime(b["ts_utc"], utc=True).astype("int64"), leg="front")
    else:
        b = pd.read_parquet(TMP / f"raw_{c['root']}.parquet")
    need(bool((b["ts"] < SEAL_NS).all()), "seal: a bar on or after 2024")
    return b


def build_cell(cell: str) -> dict[str, Any]:
    """Integer-unit arrays for one cell's front series, the per-session basis, roll flags, and the filter stats."""
    c = CELLS[cell]
    b = _bars(cell)
    f = b[b["leg"] == "front"].sort_values("ts").reset_index(drop=True)
    m = to_wall(f["ts"].to_numpy())
    need(bool((m == to_wall_by_rule(f["ts"].to_numpy())).all()), f"clock: zoneinfo and the statutory rule disagree ({cell})")
    dn = trade_day(m)
    u = c["unit"]
    O, H, L, C = (np.rint(f[k].to_numpy(float) / u).astype(np.int64) for k in ("open", "high", "low", "close"))
    V = f["volume"].to_numpy(float)
    keep = dn >= (pd.Timestamp(c["lo"]) - pd.Timestamp(EPOCH)).days
    m, dn, O, H, L, C, V = (x[keep] for x in (m, dn, O, H, L, C, V))
    con = f["contract"].to_numpy()[keep]
    days = np.unique(dn)
    # the basis per session, from the PRIOR session only
    basis = {}
    if c["basis"] == "calendar":
        nx = b[b["leg"] == "next"].sort_values("ts")
        mn = to_wall(nx["ts"].to_numpy())
        dnn = trade_day(mn)
        nxv = np.rint(nx["close"].to_numpy(float) / u)
        need(bool(np.all(np.diff(mn) > 0)) and bool(np.all(np.diff(m) > 0)), "basis: minutes not strictly increasing")
        prev = None
        for d in days:
            if prev is not None:
                ds = day_str(prev)
                t0, t1 = wall(ds, "12:00"), wall(ds, "15:00")
                fa0, fa1 = np.searchsorted(m, t0), np.searchsorted(m, t1)
                na0, na1 = np.searchsorted(mn, t0), np.searchsorted(mn, t1)
                common, fi, ni = np.intersect1d(m[fa0:fa1], mn[na0:na1], return_indices=True)
                fc = con[fa0] if fa0 < len(m) else ""
                cur = con[int(np.searchsorted(dn, d))]
                if len(common) >= 10 and fc and fc == cur:              # a basis never spans a roll
                    sp = float(np.median(nxv[na0:na1][ni] - C[fa0:fa1][fi]))
                    near = dt.date.fromisoformat(day_str(d))
                    e1, e2 = expiry_6e(fc, near), expiry_6e(next_6e(fc), near)
                    T1, T2 = (e1 - near).days, (e2 - near).days
                    if T2 > T1 > 0:
                        basis[int(d)] = int(round(sp * T1 / (T2 - T1)))
            prev = d
    elif c["basis"] == "binance":
        sp = pd.read_csv(MAIN_DATA / "fixtures" / "crypto_binance_15m_raw.csv.gz", encoding="utf-8",
                         usecols=["timestamp", "symbol", "close"])
        sp = sp[(sp["symbol"] == "BTCUSDT") & (sp["timestamp"] < SEAL)]
        st = pd.to_datetime(sp["timestamp"]).dt.tz_localize("UTC") + pd.Timedelta(minutes=15)   # the bar's close time
        sm = to_wall(st.astype("int64").to_numpy())
        order = np.argsort(sm, kind="stable")
        sm, sv_all = sm[order], (sp["close"].to_numpy(float) / u)[order]
        prev = None
        for d in days:
            if prev is not None:
                ds = day_str(prev)
                t0, t1 = wall(ds, "12:00"), wall(ds, "15:00")
                s0, s1 = np.searchsorted(sm, t0, side="right"), np.searchsorted(sm, t1, side="right")
                diffs = []
                for tt, sv in zip(sm[s0:s1], sv_all[s0:s1]):
                    k = int(np.searchsorted(m, tt, side="left")) - 1               # last CME bar starting before tt
                    if k >= 0 and dn[k] == prev:
                        diffs.append(C[k] - sv)
                if len(diffs) >= 6:
                    basis[int(d)] = int(round(float(np.median(diffs))))
            prev = d
    else:
        basis = {int(d): 0 for d in days}
    # the roll week (6E deliverable): the 5 business days before the front's expiry
    roll = set()
    if c["root"] == "6E":
        for d in days:
            k = int(np.searchsorted(dn, d))
            near = dt.date.fromisoformat(day_str(d))
            e1 = expiry_6e(con[k], near)
            if 0 <= np.busday_count(near, e1) <= 5:
                roll.add(int(d))
    # filter statistics on the continuous bar series (bars, not minutes)
    rng = pd.Series((H - L).astype(float))
    vol = pd.Series(V)
    appr_r = (rng.rolling(5).mean().shift(1) / rng.rolling(60).median().shift(6)).to_numpy()
    appr_v = (vol.rolling(5).mean().shift(1) / vol.rolling(60).median().shift(6)).to_numpy()
    appr_r_canary = (rng.rolling(5).mean() / rng.rolling(60).median().shift(6)).to_numpy()   # includes bar b
    bar_r = (rng / rng.rolling(60).median().shift(1)).to_numpy()
    bar_v = (vol / vol.rolling(60).median().shift(1)).to_numpy()
    starts = np.searchsorted(dn, days, side="left")
    ends = np.searchsorted(dn, days, side="right")
    return {"cell": cell, "m": m, "dn": dn, "O": O, "H": H, "L": L, "C": C, "days": days, "starts": starts, "ends": ends,
            "basis": basis, "roll": roll, "appr_r": appr_r, "appr_v": appr_v, "appr_r_canary": appr_r_canary,
            "bar_r": bar_r, "bar_v": bar_v}


ARRAYS = ("m", "dn", "O", "H", "L", "C", "days", "starts", "ends", "appr_r", "appr_v", "appr_r_canary", "bar_r", "bar_v")


def save_cell(X: dict[str, Any]) -> None:
    d = TMP / X["cell"]
    d.mkdir(parents=True, exist_ok=True)
    for k in ARRAYS:
        np.save(d / f"{k}.npy", X[k])
    (d / "meta.json").write_text(json.dumps({"basis": {str(k): v for k, v in X["basis"].items()},
                                             "roll": sorted(X["roll"])}), encoding="utf-8")


def load_cell(cell: str) -> dict[str, Any]:
    d = TMP / cell
    X: dict[str, Any] = {k: np.load(d / f"{k}.npy", mmap_mode="r") for k in ARRAYS}
    meta = json.loads((d / "meta.json").read_text(encoding="utf-8"))
    X["basis"] = {int(k): v for k, v in meta["basis"].items()}
    X["roll"] = set(meta["roll"])
    X["cell"] = cell
    return X


# ================================================================================ events
def level_up(cprev: np.ndarray, g: np.ndarray, S: int) -> np.ndarray:
    """The lowest grid level >= cprev (grid = g + k*S)."""
    return g + -((g - cprev) // S) * S


def level_dn(cprev: np.ndarray, g: np.ndarray, S: int) -> np.ndarray:
    return g + ((cprev - g) // S) * S


def crossings(X: dict[str, Any], o: int, S: int, tick: int, a: int, z: int, g: int) -> list[tuple[int, int, int]]:
    """Vectorised: (bar index b, level L, side) for bars a+1..z-1 where close(b-1) <= L and high(b) >= L + tick (up),
    or close(b-1) >= L and low(b) <= L - tick (down). g = the session's grid offset in futures units."""
    if z - a < 2:
        return []
    cp = np.asarray(X["C"][a:z - 1])
    hb, lb = np.asarray(X["H"][a + 1:z]), np.asarray(X["L"][a + 1:z])
    gg = np.full(len(cp), g, dtype=np.int64)
    Lu = level_up(cp, gg, S)
    Ld = level_dn(cp, gg, S)
    up = hb >= Lu + tick
    dnm = lb <= Ld - tick
    out = [(a + 1 + int(i), int(Lu[i]), 1) for i in np.flatnonzero(up)]
    out += [(a + 1 + int(i), int(Ld[i]), -1) for i in np.flatnonzero(dnm)]
    return sorted(out)


def crossings_loop(X: dict[str, Any], S: int, tick: int, a: int, z: int, g: int) -> list[tuple[int, int, int]]:
    """Second implementation (never calls `crossings`): scan every grid level near each bar."""
    out = []
    for b in range(a + 1, z):
        cp, hb, lb = int(X["C"][b - 1]), int(X["H"][b]), int(X["L"][b])
        k0 = (cp - g) // S
        for k in range(k0 - 1, k0 + 3):
            Lv = g + k * S
            if cp <= Lv and hb >= Lv + tick and (Lv - S < cp):
                out.append((b, Lv, 1))
            if cp >= Lv and lb <= Lv - tick and (Lv + S > cp):
                out.append((b, Lv, -1))
    return sorted(set(out))


def px_before(X: dict[str, Any], a: int, z: int, t: int) -> float:
    j = int(np.searchsorted(X["m"][a:z], t, side="left")) - 1
    return float(X["C"][a + j]) if j >= 0 else float("nan")


def trade_exit(X: dict[str, Any], a: int, z: int, j0: int, t_entry: int, horizon: int, Lv: int, side: int, tick: int,
               cap: int, recross: bool = True) -> tuple[float, int]:
    """Exit price (units) and exit minute: the clock at t_entry + horizon (capped at `cap`), or earlier on a re-cross
    (a close back through L by one tick, from bar j0 on), exiting at the next bar's open."""
    t_end = min(t_entry + horizon, cap)
    k_end = a + int(np.searchsorted(X["m"][a:z], t_end, side="left"))       # bars [j0, k_end) start before t_end
    if recross and k_end > j0:
        cl = np.asarray(X["C"][j0:k_end])
        bad = np.flatnonzero(cl <= Lv - tick) if side > 0 else np.flatnonzero(cl >= Lv + tick)
        if len(bad):
            j = j0 + int(bad[0])
            if j + 1 < z:
                return float(X["O"][j + 1]), int(X["m"][j + 1])
            return float(X["C"][j]), int(X["m"][j])
    return px_before(X, a, z, t_end), t_end


def run_offset(args: tuple[str, int, bool]) -> dict[str, Any]:
    """Every book for one cell at one grid offset o (spot units)."""
    cell, o, detail = args
    c = CELLS[cell]
    X = load_cell(cell)
    S, tick = c["spacing"], c["mtick"]
    books: dict[str, list[dict[str, Any]]] = {}
    touches: dict[str, list[int]] = {w: [0, 0] for w in WINDOWS}
    for i, d in enumerate(X["days"]):
        d = int(d)
        if d not in X["basis"] or d in X["roll"]:
            continue
        a, z = int(X["starts"][i]), int(X["ends"][i])
        g = (o + X["basis"][d]) % S
        ds = day_str(d)
        cap = wall(ds, "16:10")
        ev = crossings(X, o, S, tick, a, z, g)
        mm = np.asarray(X["m"][a:z])
        cp = np.asarray(X["C"][a:z - 1])
        hb, lb = np.asarray(X["H"][a + 1:z]), np.asarray(X["L"][a + 1:z])
        gg = np.full(len(cp), g, dtype=np.int64)
        Lu = level_up(cp + 3 * tick, gg, S)
        Ld = level_dn(cp - 3 * tick, gg, S)
        for w in WINDOWS:
            t0, t1 = window_bounds(d, w)
            # ---- the premise gate: first touch per (L, side) in the window, bounce at +15
            inw = (mm[1:] >= t0) & (mm[1:] < t1)
            seen = set()
            for k in np.flatnonzero(inw & (hb >= Lu - tick)):
                key = (int(Lu[k]), 1)
                if key in seen:
                    continue
                seen.add(key)
                p15 = px_before(X, a, z, int(mm[k + 1]) + BOUNCE_H)
                touches[w][0] += 1
                touches[w][1] += int(p15 < Lu[k])
            for k in np.flatnonzero(inw & (lb <= Ld + tick)):
                key = (int(Ld[k]), -1)
                if key in seen:
                    continue
                seen.add(key)
                p15 = px_before(X, a, z, int(mm[k + 1]) + BOUNCE_H)
                touches[w][0] += 1
                touches[w][1] += int(p15 > Ld[k])
            # ---- crossings in the window: first per (L, side), no close beyond L in the previous 60 minutes
            first = set()
            cands = []
            for b, Lv, side in ev:
                tb = int(X["m"][b])
                if not (t0 <= tb < t1) or (Lv, side) in first:
                    continue
                first.add((Lv, side))
                k60 = a + int(np.searchsorted(mm, tb - LOOK, side="left"))
                prior = np.asarray(X["C"][k60:b - 1]) if b - 1 > k60 else np.array([], dtype=np.int64)
                if len(prior) and ((prior > Lv).any() if side > 0 else (prior < Lv).any()):
                    continue
                cands.append((b, Lv, side))
            for b, Lv, side in cands:
                ar, av = X["appr_r"][b], X["appr_v"][b]
                br, bv = X["bar_r"][b], X["bar_v"][b]
                fastA = bool(np.isfinite(ar) and np.isfinite(av) and 2 <= ar <= 15 and av >= 2)
                fastB = bool(np.isfinite(br) and np.isfinite(bv) and 3 <= br <= 15 and bv >= 3)
                fastA_can = bool(np.isfinite(X["appr_r_canary"][b]) and np.isfinite(av) and 2 <= X["appr_r_canary"][b] <= 15 and av >= 2)
                tb = int(X["m"][b])
                ob = int(X["O"][b])
                # Lens A: a resting stop at L + tick (side-mirrored)
                fills = {}
                for s in SLIPS:
                    if side > 0:
                        fills[s] = float(ob) if ob >= Lv + tick else float(min(int(X["H"][b]), Lv + tick + s * tick))
                    else:
                        fills[s] = float(ob) if ob <= Lv - tick else float(max(int(X["L"][b]), Lv - tick - s * tick))
                xA, tA = trade_exit(X, a, z, b, tb, HOLD, Lv, side, tick, cap)
                rec = {"day": ds, "w": w, "L": Lv, "side": side, "tb": tb, "fastA": fastA, "fastA_can": fastA_can,
                       "fastB": fastB, "ar": float(ar) if np.isfinite(ar) else float("nan"),
                       "lvl00": int(((Lv - X["basis"][d]) - o) % (2 * S) == 0) if cell.startswith("m6e") else -1}
                for s in SLIPS:
                    rec[f"gA{s}"] = side * (xA - fills[s]) * c["usd"]
                rec["tA_exit"] = tA
                rec["absA"] = abs(xA - fills[2]) * c["usd"]
                # Lens B: market at open(b+1) after close(b) beyond L by 2 ticks
                okB = (int(X["C"][b]) >= Lv + 2 * tick) if side > 0 else (int(X["C"][b]) <= Lv - 2 * tick)
                if okB and b + 1 < z and int(X["m"][b + 1]) < cap:
                    eB = float(X["O"][b + 1])
                    xB, tB = trade_exit(X, a, z, b + 1, int(X["m"][b + 1]), HOLD, Lv, side, tick, cap)
                    rec["gB"] = side * (xB - eB) * c["usd"]
                    rec["tB"] = int(X["m"][b + 1])
                    rec["tB_exit"] = tB
                else:
                    rec["gB"] = float("nan")
                if detail:
                    for hz in (15, 60, 120):
                        xh, _ = trade_exit(X, a, z, b, tb, hz, Lv, side, tick, cap, recross=False)
                        rec[f"g_clock{hz}"] = side * (xh - fills[2]) * c["usd"]
                    if i + 1 < len(X["days"]):
                        a2, z2 = int(X["starts"][i + 1]), int(X["ends"][i + 1])
                        rec["g_nextday"] = side * (float(X["C"][z2 - 1]) - fills[2]) * c["usd"]
                books.setdefault(w, []).append(rec)
    return {"cell": cell, "o": o, "events": books, "touches": touches}


# ================================================================================ books (one position at a time)
def book_trades(evs: list[dict[str, Any]], key_fast: str | None, lens: str) -> list[dict[str, Any]]:
    """Time-ordered events -> trades with one position at a time and a 60-minute cooldown per level."""
    out, busy_until, last_at = [], -1, {}
    for e in sorted(evs, key=lambda r: r["tb"]):
        if key_fast is not None and not e[key_fast]:
            continue
        if lens == "B" and not np.isfinite(e["gB"]):
            continue
        t_in = e["tb"] if lens == "A" else e["tB"]
        if t_in < busy_until or (e["L"] in last_at and t_in - last_at[e["L"]] < LOOK):
            continue
        busy_until = e["tA_exit"] if lens == "A" else e["tB_exit"]
        last_at[e["L"]] = t_in
        out.append(e)
    return out


def stat(trs: list[dict[str, Any]], col: str) -> float:
    v = [t[col] for t in trs]
    return float(np.mean(v)) if v else float("nan")


def tstat(x: np.ndarray) -> float:
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    return float(x.mean() / (x.std(ddof=1) / math.sqrt(len(x)))) if len(x) > 2 and x.std(ddof=1) > 0 else float("nan")


def summarise_offset(r: dict[str, Any]) -> dict[str, Any]:
    s: dict[str, Any] = {"o": r["o"], "touch": r["touches"]}
    for w, evs in r["events"].items():
        tA = book_trades(evs, "fastA", "A")
        tU = book_trades(evs, None, "A")
        tB = book_trades(evs, "fastB", "B")
        s[w] = {"A_fast_n": len(tA), "A_fast_g2": stat(tA, "gA2"), "A_unc_n": len(tU), "A_unc_g2": stat(tU, "gA2"),
                "B_fast_n": len(tB), "B_fast_g": stat(tB, "gB")}
    return s


# ================================================================================ the run
def offsets(cell: str) -> list[int]:
    c = CELLS[cell]
    return list(range(0, c["spacing"], c["step"]))


def eligible(cell: str, o: int) -> bool:
    c = CELLS[cell]
    dist = min(o % c["spacing"], c["spacing"] - o % c["spacing"])
    return dist > c["band"]


def holm(ps: dict[str, float]) -> dict[str, float]:
    items = sorted(ps.items(), key=lambda kv: kv[1])
    m, out, run = len(items), {}, 0.0
    for i, (k, p) in enumerate(items):
        run = max(run, min(1.0, (m - i) * p))
        out[k] = run
    return out


def run(lines: Path | None) -> int:
    from stage0_d755_ecb_press_conference import book
    need(not OUT.exists(), f"{OUT.name} exists: D761 is run-once")
    t0 = time.time()
    sign_audit()
    res: dict[str, Any] = {"spec": SPEC.name, "seal": f"nothing on or after {SEAL}", "cells": {}}
    for cell in CELLS:
        X = build_cell(cell)
        save_cell(X)
        res["cells"][cell] = {"sessions": int(len(X["days"])), "sessions_with_basis": int(sum(int(d) in X["basis"] for d in X["days"])),
                              "roll_excluded": len(X["roll"]), "bars": int(len(X["m"])),
                              "basis_units_median": float(np.median(list(X["basis"].values()))) if X["basis"] else None}
        print(f"[{cell}] built: {res['cells'][cell]}", flush=True)
    # lag audit: the vectorised detector against the loop on a sample of sessions (round grid)
    for cell in CELLS:
        X = load_cell(cell)
        c = CELLS[cell]
        rng_ = np.random.default_rng(761)
        idx = rng_.choice(len(X["days"]), size=min(40, len(X["days"])), replace=False)
        for i in idx:
            d = int(X["days"][i])
            if d not in X["basis"]:
                continue
            a, z = int(X["starts"][i]), int(X["ends"][i])
            g = X["basis"][d] % c["spacing"]
            need(crossings(X, 0, c["spacing"], c["mtick"], a, z, g) == crossings_loop(X, c["spacing"], c["mtick"], a, z, g),
                 f"lag: the vectorised detector differs from the loop ({cell}, {day_str(d)})")
    # every offset, every cell, over processes
    jobs = [(cell, o, o == 0) for cell in CELLS for o in offsets(cell)]
    for cell in CELLS:
        for h in CELLS[cell]["half"]:
            if not any(j[0] == cell and j[1] == h for j in jobs):
                jobs.append((cell, h, False))
    with ProcessPoolExecutor(WORKERS) as ex:
        allr = list(ex.map(run_offset, jobs, chunksize=1))
    print(f"offsets done: {(time.time() - t0) / 60:.1f} min", flush=True)
    # chunk == whole: the process results equal a serial recompute on two jobs
    for job in [("m6e", 0, True), ("mbt", 100, False)]:
        ser = summarise_offset(run_offset(job))
        par = summarise_offset(next(r for r in allr if r["cell"] == job[0] and r["o"] == job[1]))
        need(json.dumps(ser, default=float, sort_keys=True) == json.dumps(par, default=float, sort_keys=True),
             f"speed: the process result differs from the serial one ({job[:2]})")
    comp_p: dict[str, float] = {}
    for cell, c in CELLS.items():
        rs = {r["o"]: r for r in allr if r["cell"] == cell}
        summ = {o: summarise_offset(r) for o, r in rs.items()}
        R = rs[0]
        out: dict[str, Any] = res["cells"][cell]
        # premise gate (Asia): round vs half-round bounce rate
        def bounce(o: int, w: str = "asia") -> tuple[int, int]:
            n, k = rs[o]["touches"][w]
            return n, k
        nR, kR = bounce(0)
        nH = sum(bounce(h)[0] for h in c["half"])
        kH = sum(bounce(h)[1] for h in c["half"])
        pR, pH = kR / nR if nR else float("nan"), kH / nH if nH else float("nan")
        diff = 100 * (pR - pH)
        se = 100 * math.sqrt(pR * (1 - pR) / nR + pH * (1 - pH) / nH) if nR and nH else float("nan")
        gate = "PASS" if diff >= 2 else ("FAIL" if (diff < 1 and se < 0.5) else "UNRESOLVED")
        out["gate"] = {"round_touches": nR, "round_bounce": pR, "half_touches": nH, "half_bounce": pH,
                       "excess_pp": diff, "se_pp": se, "reading": gate,
                       "by_window": {w: {"round": bounce(0, w), "half": [sum(bounce(h, w)[0] for h in c["half"]),
                                                                          sum(bounce(h, w)[1] for h in c["half"])]}
                                     for w in WINDOWS}}
        # the profile: the primary statistic (Asia, Lens A fast, s = 2) at every offset
        prof = {o: summ[o]["asia"]["A_fast_g2"] if "asia" in summ[o] else float("nan") for o in sorted(summ)}
        elig = [prof[o] for o in prof if eligible(cell, o) and np.isfinite(prof[o])]
        r0 = prof[0]
        half_stat = float(np.nanmean([prof[h] for h in c["half"] if h in prof]))
        rank = float(np.mean([r0 > x for x in elig])) if elig and np.isfinite(r0) else float("nan")
        out["profile"] = {"round": r0, "half_round": half_stat, "eligible_offsets": len(elig),
                          "eligible_p50": float(np.median(elig)) if elig else None,
                          "eligible_p95": float(np.percentile(elig, 95)) if elig else None, "rank": rank,
                          "by_offset": {str(o): (round(v, 3) if np.isfinite(v) else None) for o, v in prof.items()},
                          "bounce_by_offset": {str(o): (rs[o]["touches"]["asia"][1] / rs[o]["touches"]["asia"][0]
                                                        if rs[o]["touches"]["asia"][0] else None) for o in sorted(rs)}}
        # the round grid's books in detail
        evA = R["events"].get("asia", [])
        tA = book_trades(evA, "fastA", "A")
        tU = book_trades(evA, None, "A")
        tB = book_trades(evA, "fastB", "B")
        canary_sel = {e["tb"] for e in evA if e["fastA_can"]}
        need(canary_sel != {e["tb"] for e in evA if e["fastA"]}, f"lag: the bar-b canary changed no selection ({cell})")
        g2 = np.array([t["gA2"] for t in tA], float)
        days_A = [t["day"] for t in tA]
        yrs = len(set(d[:4] for d in (t["day"] for t in tU))) or 1
        span_years = max(1.0, (pd.Timestamp(max(t["day"] for t in tU)) - pd.Timestamp(min(t["day"] for t in tU))).days / 365.25) if tU else 1.0
        out["primary"] = {"n": len(tA), "mean_gross_by_slip": {s: stat(tA, f"gA{s}") for s in SLIPS},
                          "mean_abs_move": stat(tA, "absA"), "two_bars": 2 * 2 * c["cost"],
                          "book": book(g2, days_A, c["cost"], len(tA) / span_years) if len(tA) > 3 else None,
                          "t_net": tstat(g2 - c["cost"]),
                          "net_by_slip": {s: stat(tA, f"gA{s}") - c["cost"] for s in SLIPS}}
        if len(tA) > 3:
            net = pd.Series(g2 - c["cost"], index=[d[:4] for d in days_A]).groupby(level=0).sum()
            best2 = net.sort_values().iloc[-2:].index if len(net) >= 2 else net.index
            out["primary"]["net_ex_best_two_years"] = float(net.drop(best2).sum())
            out["primary"]["years_net"] = {k: round(float(v), 2) for k, v in net.items()}
        out["unconditional_A"] = {"n": len(tU), "mean_g2": stat(tU, "gA2"), "t": tstat(np.array([t["gA2"] for t in tU]))}
        out["lens_B_fast"] = {"n": len(tB), "mean_g": stat(tB, "gB"), "t": tstat(np.array([t["gB"] for t in tB]))}
        both = [e for e in evA if np.isfinite(e["gB"])]
        out["A_minus_B_per_event"] = float(np.mean([e["gA2"] - e["gB"] for e in both])) if both else None
        out["decay_round_fastA"] = {h: stat([t for t in tA if f"g_clock{h}" in t], f"g_clock{h}") for h in (15, 60, 120)}
        out["decay_round_fastA"]["next_day_close"] = stat([t for t in tA if "g_nextday" in t], "g_nextday")
        out["windows"] = {w: {"round": summ[0].get(w), "half": [summ[h].get(w) for h in c["half"]]} for w in WINDOWS}
        if cell.startswith("m6e"):
            out["levels_00_vs_50"] = {"00": stat([t for t in tA if t["lvl00"] == 1], "gA2"), "n00": sum(t["lvl00"] == 1 for t in tA),
                                      "50": stat([t for t in tA if t["lvl00"] == 0], "gA2"), "n50": sum(t["lvl00"] == 0 for t in tA)}
        # speed terciles (approach ratio among the round grid's unconditional events), treatment vs half-round
        ar = np.array([e["ar"] for e in evA if np.isfinite(e["ar"])])
        if len(ar) > 30:
            q1, q2 = np.quantile(ar, [1 / 3, 2 / 3])
            def terc(evs: list[dict[str, Any]], lo_: float, hi_: float) -> float:
                ts_ = book_trades([e for e in evs if np.isfinite(e["ar"]) and lo_ <= e["ar"] < hi_], None, "A")
                return stat(ts_, "gA2")
            out["speed_terciles"] = {nm: {"round": terc(evA, lo_, hi_),
                                          "half": float(np.nanmean([terc(rs[h]["events"].get("asia", []), lo_, hi_) for h in c["half"]]))}
                                     for nm, lo_, hi_ in (("slow", -np.inf, q1), ("mid", q1, q2), ("fast", q2, np.inf))}
        if cell == "mbt" and tA:
            out["mbt_era"] = {"pre": stat([t for t in tA if t["day"] < "2021-05-03"], "gA2"),
                              "mbt": stat([t for t in tA if t["day"] >= "2021-05-03"], "gA2")}
        if cell.startswith("m6e") and tA:
            out["eras"] = {"2010_14": stat([t for t in tA if t["day"] < "2015-01-01"], "gA2"),
                           "2015_23": stat([t for t in tA if t["day"] >= "2015-01-01"], "gA2")}
        srt = sorted(tA, key=lambda t: t["gA2"])
        out["largest"] = {"losers": [(t["day"], round(t["gA2"], 2)) for t in srt[:3]],
                          "winners": [(t["day"], round(t["gA2"], 2)) for t in srt[-3:]]}
        if lines is not None and lines.exists() and tA:
            ol = pd.read_csv(lines, index_col=0, encoding="utf-8")
            ol.index = ol.index.astype(str)
            dnet = pd.Series(g2 - c["cost"], index=days_A).groupby(level=0).sum()
            alld = sorted(set(ol.index) | {d for d in dnet.index if ol.index.min() <= d <= ol.index.max()})
            out["component_corr"] = {k: float(np.corrcoef(dnet.reindex(alld, fill_value=0.0), ol[k].reindex(alld).fillna(0.0))[0, 1])
                                     for k in ol.columns}
        # the reading (primary cells only)
        size_ok = np.isfinite(out["primary"]["mean_abs_move"]) and out["primary"]["mean_abs_move"] >= 2 * 2 * c["cost"]
        profile_ok = np.isfinite(rank) and rank >= 0.95 and np.isfinite(r0) and r0 > half_stat
        tnet = out["primary"]["t_net"]
        out["one_sided_p_net"] = float(0.5 * math.erfc(tnet / math.sqrt(2))) if np.isfinite(tnet) else 1.0
        out["_flags"] = {"gate": gate, "profile_ok": bool(profile_ok), "size_ok": bool(size_ok)}
        if c["primary"]:
            comp_p[cell] = out["one_sided_p_net"]
    hp = holm(comp_p)
    for cell, c in CELLS.items():
        out = res["cells"][cell]
        f = out.pop("_flags")
        if not c["primary"]:
            out["reading"] = "REPORTED ONLY"
            continue
        out["holm_p"] = hp[cell]
        pr = out["primary"]
        cascade = (f["profile_ok"] and f["size_ok"] and np.isfinite(pr["t_net"]) and pr["t_net"] >= 2 and hp[cell] < 0.05
                   and pr.get("net_ex_best_two_years", -1) > 0)
        out["reading"] = ("MECHANISM ABSENT" if f["gate"] == "FAIL" else "NO PROFILE" if not f["profile_ok"]
                          else "SIZE FAILURE" if not f["size_ok"] else "CASCADE" if cascade else "NOTHING")
        out["GO"] = bool(out["reading"] == "CASCADE")
    res["runtime_min"] = round((time.time() - t0) / 60, 2)
    OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
    for cell in CELLS:
        o = res["cells"][cell]
        print(cell, o.get("reading"), json.dumps({"gate": {k: o["gate"][k] for k in ("excess_pp", "se_pp", "reading")},
                                                   "profile": {k: o["profile"][k] for k in ("round", "half_round", "rank", "eligible_p50", "eligible_p95")},
                                                   "primary": {k: o["primary"][k] for k in ("n", "mean_abs_move", "t_net")}}, default=float), flush=True)
    return 0


# ================================================================================ self-test
def _synthetic(path_units: list[int], start_wall: int, dn: int) -> dict[str, Any]:
    n = len(path_units)
    C = np.array(path_units, dtype=np.int64)
    O = np.r_[C[0], C[:-1]]
    H = np.maximum(O, C)
    L = np.minimum(O, C)
    m = np.arange(start_wall, start_wall + n, dtype=np.int64)
    one = np.ones(n)
    return {"m": m, "dn": np.full(n, dn), "O": O, "H": H, "L": L, "C": C, "days": np.array([dn]),
            "starts": np.array([0]), "ends": np.array([n]), "basis": {dn: 0}, "roll": set(),
            "appr_r": one * 3, "appr_v": one * 3, "appr_r_canary": one * 3, "bar_r": one * 4, "bar_v": one * 4}


def sign_audit(up: float = 1.0) -> None:
    """An up-cross of a round level that keeps rising pays the long (a down-cross that keeps falling pays the short)."""
    dn = (dt.date(2020, 1, 7) - EPOCH.date()).days
    t = wall("2020-01-07", "19:00", 1)
    base = 1000
    path = [base - 5] * 10 + [base + 1, base + 4] + [base + 6 + i for i in range(40)]
    if up < 0:
        path = [2 * base - p for p in path]
    X = _synthetic(path, t, dn)
    ev = crossings(X, 0, 100, 1, 0, len(path), 0)
    need(len(ev) >= 1, "sign: no crossing found on the synthetic path")
    b, Lv, side = ev[0]
    need(side > 0, "sign: a rising path did not give an up-cross")
    fill = float(min(int(X["H"][b]), Lv + 1 + 2))
    xA, _ = trade_exit(X, 0, len(path), b, int(X["m"][b]), HOLD, Lv, side, 1, t + 10_000)
    need(side * (xA - fill) > 0, "sign: a continued rise did not pay the long")


def selftest() -> int:
    fails: list[str] = []
    try:
        sign_audit()
    except D761Error as e:
        fails.append(str(e))
    try:
        sign_audit(up=-1.0)
        fails.append("sign: the audit did not raise on a mirrored book")
    except D761Error:
        pass
    # the vectorised detector equals the loop on a tie-heavy random integer path
    rng_ = np.random.default_rng(1)
    for trial in range(30):
        path = list(np.cumsum(rng_.integers(-3, 4, size=400)) + 1000)
        X = _synthetic(path, 0, 0)
        g = int(rng_.integers(0, 50))
        if crossings(X, 0, 50, 1, 0, 400, g) != crossings_loop(X, 50, 1, 0, 400, g):
            fails.append(f"detector: vectorised != loop on trial {trial}")
            break
    # Lens A != Lens B on a known event
    dn = (dt.date(2020, 1, 7) - EPOCH.date()).days
    t = wall("2020-01-07", "19:00", 1)
    path = [995] * 10 + [1010, 1012] + [1014] * 40          # the crossing bar runs past the stop: A fills 1003, B 1010
    X = _synthetic(path, t, dn)
    ev = crossings(X, 0, 100, 1, 0, len(path), 0)
    b, Lv, side = ev[0]
    fillA = float(min(int(X["H"][b]), Lv + 1 + 2))
    if fillA == float(X["O"][b + 1]):
        fails.append("right quantity: Lens A's fill equals Lens B's entry on the known event")
    # level arithmetic on negative-offset grids
    if level_up(np.array([1000]), np.array([30]), 100)[0] != 1030 or level_dn(np.array([1000]), np.array([30]), 100)[0] != 930:
        fails.append("levels: the grid arithmetic is wrong")
    # contracts
    if next_6e("6EZ9") != "6EH0" or expiry_6e("6EH4", dt.date(2014, 1, 2)) != dt.date(2014, 3, 17):
        fails.append("contracts: next or expiry wrong")
    # clock
    ts = pd.date_range("2010-06-01", "2023-12-31", freq="211min", tz="UTC").asi8
    if not (to_wall(ts) == to_wall_by_rule(ts)).all():
        fails.append("clock: zoneinfo and the statutory rule disagree")
    # holm known answer
    hp = holm({"a": 0.01, "b": 0.04})
    if abs(hp["a"] - 0.02) > 1e-12 or abs(hp["b"] - 0.04) > 1e-12:
        fails.append("holm: a known answer is wrong")
    if fails:
        print("SELFTEST FAILED:", fails)
        return 1
    print("SELFTEST OK: the sign audit in money (raises on a mirrored book); the vectorised crossing detector equals a "
          "loop implementation on tie-heavy paths; Lens A != Lens B on a known event; grid arithmetic; 6E contract "
          "roll and expiry; the UTC -> ET clock against the statutory rule 2010-2023; Holm's known answer")
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

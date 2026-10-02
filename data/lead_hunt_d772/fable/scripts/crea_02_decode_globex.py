"""Decode full-Globex 1-minute bars for roots the fixtures do not carry (6J, 6A, 6E, MES, MNQ, MGC), 2016-2023 only.

Follows scripts/build_fut_index_1m.py (D462/D520): ids labelled from the mapping WINDOW containing the bar's ts_event;
front per (root, calendar ET day) = highest full-day volume. Output: one parquet per root in ../out/ with columns
root, day(ET calendar), et(naive ET minute), contract, open, high, low, close, volume. Read-only on data/raw. SEAL: only
archive files whose span ends before 2024-01-01 are opened.

    python crea_02_decode_globex.py --workers 3
"""
import argparse, os, re, sys, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd

RAW = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento")
OUT = Path(__file__).resolve().parents[1] / "out"
JOBS = ["GLBX-20260911-VLQEMCFLUB", "GLBX-20260911-BLBKYJ9XSK", "GLBX-20260911-NF533R6P5T", "GLBX-20260911-H8W497MS6J"]
ROOTS = ("6J", "6A", "6E", "MES", "MNQ", "MGC")
OUTRIGHT = re.compile(r"^(6J|6A|6E|MES|MNQ|MGC)([FGHJKMNQUVXZ])(\d{1,2})$")
PX = 1e-9; CHUNK = 10_000_000


def files():
    fs = []
    for j in JOBS:
        for f in sorted(os.listdir(RAW / j)):
            if not f.endswith(".ohlcv-1m.dbn.zst"):
                continue
            span = f.split(".")[0].replace("glbx-mdp3-", "")
            a, b = span.split("-")
            if b >= "20240101":
                continue  # SEAL
            if b < "20160101":
                continue
            fs.append(str(RAW / j / f))
    return fs


def ids_of(store):
    rows = []
    for sym, ivs in store.metadata.mappings.items():
        m = OUTRIGHT.match(str(sym))
        if not m:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if not sid:
                continue
            s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date")
            e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
            rows.append((int(sid), m.group(1), str(sym), np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value)))
    if not rows:
        return None
    w = pd.DataFrame(rows, columns=["iid", "root", "contract", "w0", "w1"])
    assert not w.duplicated(["iid", "w0"]).any()
    return w


def label_rows(a, w):
    raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "ts": a["ts_event"].astype(np.uint64), "_i": np.arange(len(a), dtype=np.int64)})
    j = raw.merge(w, on="iid", how="inner")
    j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])]
    assert not j["_i"].duplicated().any(), "bar claimed by two windows"
    return j


def worker(path):
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); w = ids_of(store); B = []; n_in = 0
    if w is None:
        return dict(file=path, rows_in=0, kept=0, bars=None, secs=0)
    for arr in store.to_ndarray(count=CHUNK):
        n_in += len(arr)
        j = label_rows(arr, w).sort_values("_i")
        if len(j) == 0:
            continue
        a = arr[j["_i"].to_numpy()]
        ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
        B.append(pd.DataFrame({"root": j["root"].to_numpy(), "contract": j["contract"].to_numpy(),
                               "day": ts.strftime("%Y-%m-%d"), "et": ts.tz_localize(None).floor("min"),
                               "open": a["open"] * PX, "high": a["high"] * PX, "low": a["low"] * PX, "close": a["close"] * PX,
                               "volume": a["volume"].astype(np.int64)}))
    bars = pd.concat(B, ignore_index=True) if B else None
    return dict(file=Path(path).name, rows_in=n_in, kept=0 if bars is None else len(bars), bars=bars, secs=round(time.time() - t0, 1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=3); a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    fs = files(); print(len(fs), "files", flush=True)
    res = []
    with ProcessPoolExecutor(a.workers) as ex:
        for r in ex.map(worker, fs):
            print(r["file"], r["rows_in"], r["kept"], r["secs"], flush=True); res.append(r)
    bars = pd.concat([r["bars"] for r in res if r["bars"] is not None], ignore_index=True)
    # front per (root, day) by full-day volume
    dv = bars.groupby(["root", "day", "contract"], sort=False)["volume"].sum().reset_index()
    front = dv.sort_values(["root", "day", "volume", "contract"]).groupby(["root", "day"]).tail(1).rename(columns={"contract": "front"})
    bars = bars.merge(front[["root", "day", "front"]], on=["root", "day"])
    bars = bars[bars["contract"] == bars["front"]].drop(columns="front")
    bars = bars.sort_values(["root", "et"]).drop_duplicates(["root", "et"]).reset_index(drop=True)
    assert bars["et"].max() < pd.Timestamp("2024-01-01"), "SEAL"
    for root, g in bars.groupby("root"):
        g.to_parquet(OUT / f"crea_globex1m_{root}.parquet", index=False)
        print(root, len(g), g["day"].min(), g["day"].max(), flush=True)


if __name__ == "__main__":
    main()

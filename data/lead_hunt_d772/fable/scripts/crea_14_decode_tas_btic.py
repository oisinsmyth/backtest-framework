"""Decode the TAS / BTIC / TACO instruments from the ohlcv-1m archive (ALL_SYMBOLS), 2016-2023: GCT SIT HGT PLT (COMEX TAS),
EST NQT YMT (BTIC on E-minis: basis to the 16:00 cash close), ESQ NQQ (TACO: basis to the 09:30 cash open), ZBT (Treasury TAS),
BZT HOT RBT (energy TAS). Output ../out/crea_tasbtic_1m.parquet: symbol, root, kind, contract, et, open, high, low, close, volume.
Prices are OFFSETS (ticks for TAS; index points of basis for BTIC/TACO). SEAL: files reaching 2024 never opened.

    python crea_14_decode_tas_btic.py --workers 3
"""
import argparse, os, re, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd

RAW = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento")
OUT = Path(__file__).resolve().parents[1] / "out"
JOBS = ["GLBX-20260911-VLQEMCFLUB", "GLBX-20260911-BLBKYJ9XSK", "GLBX-20260911-NF533R6P5T", "GLBX-20260911-H8W497MS6J"]
PAT = re.compile(r"^(GCT|SIT|HGT|PLT|EST|NQT|YMT|ESQ|NQQ|ZBT|BZT|HOT|RBT)([FGHJKMNQUVXZ])(\d{1,2})$")
PX = 1e-9; CHUNK = 10_000_000


def files():
    fs = []
    for j in JOBS:
        for f in sorted(os.listdir(RAW / j)):
            if not f.endswith(".ohlcv-1m.dbn.zst"):
                continue
            a, b = f.split(".")[0].replace("glbx-mdp3-", "").split("-")
            if b >= "20240101" or b < "20160101":
                continue
            fs.append(str(RAW / j / f))
    return fs


def ids_of(store):
    rows = []
    for sym, ivs in store.metadata.mappings.items():
        m = PAT.match(str(sym))
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
    w = pd.DataFrame(rows, columns=["iid", "kind", "symbol", "w0", "w1"])
    assert not w.duplicated(["iid", "w0"]).any()
    return w


def worker(path):
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); w = ids_of(store); B = []; n = 0
    if w is None:
        return dict(file=Path(path).name, rows_in=0, kept=0, bars=None, secs=0)
    for arr in store.to_ndarray(count=CHUNK):
        n += len(arr)
        raw = pd.DataFrame({"iid": arr["instrument_id"].astype(np.uint32), "ts": arr["ts_event"].astype(np.uint64), "_i": np.arange(len(arr))})
        j = raw.merge(w, on="iid", how="inner"); j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])].sort_values("_i")
        if len(j) == 0:
            continue
        a = arr[j["_i"].to_numpy()]
        ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
        B.append(pd.DataFrame({"symbol": j["symbol"].to_numpy(), "kind": j["kind"].to_numpy(), "et": ts.tz_localize(None).floor("min"),
                               "open": a["open"] * PX, "high": a["high"] * PX, "low": a["low"] * PX, "close": a["close"] * PX, "volume": a["volume"].astype(np.int64)}))
    bars = pd.concat(B, ignore_index=True) if B else None
    return dict(file=Path(path).name, rows_in=n, kept=0 if bars is None else len(bars), bars=bars, secs=round(time.time() - t0, 1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=3); a = ap.parse_args()
    fs = files(); print(len(fs), "files", flush=True); res = []
    with ProcessPoolExecutor(a.workers) as ex:
        for r in ex.map(worker, fs):
            print(r["file"], r["rows_in"], r["kept"], r["secs"], flush=True); res.append(r)
    bars = pd.concat([r["bars"] for r in res if r["bars"] is not None], ignore_index=True)
    bars["root"] = bars["kind"].str[:2]; bars["contract"] = bars["symbol"].str[-2:]
    assert bars["et"].max() < pd.Timestamp("2024-01-01"), "SEAL"
    bars = bars.sort_values(["symbol", "et"]).reset_index(drop=True)
    bars.to_parquet(OUT / "crea_tasbtic_1m.parquet", index=False)
    print("rows", len(bars)); print(bars.groupby("kind").agg(rows=("et", "size"), vol=("volume", "sum"), first=("et", "min"), last=("et", "max")).to_string())
    for k, g in bars.groupby("kind"):
        print(k, "close distribution:", g["close"].describe()[["mean", "std", "min", "50%", "max"]].round(3).to_dict(), "vol by hour:", g.groupby(g["et"].dt.hour)["volume"].sum().sort_values(ascending=False).head(4).to_dict())


if __name__ == "__main__":
    main()

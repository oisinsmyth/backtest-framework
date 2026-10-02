"""Partner's (3): decode ALL CL outright 1-minute bars 2016-2023 (every month), keep per ET day the two highest-volume contracts
(front and second). Output ../out/crea_cl_two_months_1m.parquet (day, et, contract, rank, close, volume). SEAL asserted.
    python crea_22_decode_cl_second.py --workers 3"""
import argparse, os, re, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd

RAW = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento")
OUT = Path(__file__).resolve().parents[1] / "out"
JOBS = ["GLBX-20260911-VLQEMCFLUB", "GLBX-20260911-BLBKYJ9XSK", "GLBX-20260911-NF533R6P5T", "GLBX-20260911-H8W497MS6J"]
PAT = re.compile(r"^CL([FGHJKMNQUVXZ])(\d{1,2})$"); PX = 1e-9; CHUNK = 10_000_000


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
        if not PAT.match(str(sym)):
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if not sid:
                continue
            s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date"); e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
            rows.append((int(sid), str(sym), np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value)))
    return pd.DataFrame(rows, columns=["iid", "contract", "w0", "w1"]) if rows else None


def worker(path):
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); w = ids_of(store); B = []; n = 0
    for arr in store.to_ndarray(count=CHUNK):
        n += len(arr)
        raw = pd.DataFrame({"iid": arr["instrument_id"].astype(np.uint32), "ts": arr["ts_event"].astype(np.uint64), "_i": np.arange(len(arr))})
        j = raw.merge(w, on="iid", how="inner"); j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])].sort_values("_i")
        if len(j) == 0:
            continue
        a = arr[j["_i"].to_numpy()]
        ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
        B.append(pd.DataFrame({"contract": j["contract"].to_numpy(), "day": ts.strftime("%Y-%m-%d"), "et": ts.tz_localize(None).floor("min"), "close": a["close"] * PX, "volume": a["volume"].astype(np.int64)}))
    bars = pd.concat(B, ignore_index=True) if B else None
    return dict(file=Path(path).name, rows_in=n, kept=0 if bars is None else len(bars), bars=bars, secs=round(time.time() - t0, 1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=3); a = ap.parse_args()
    res = []
    with ProcessPoolExecutor(a.workers) as ex:
        for r in ex.map(worker, files()):
            print(r["file"], r["rows_in"], r["kept"], r["secs"], flush=True); res.append(r)
    bars = pd.concat([r["bars"] for r in res if r["bars"] is not None], ignore_index=True)
    dv = bars.groupby(["day", "contract"])["volume"].sum().reset_index()
    dv["rank"] = dv.groupby("day")["volume"].rank(ascending=False, method="first")
    top2 = dv[dv["rank"] <= 2][["day", "contract", "rank"]]
    bars = bars.merge(top2, on=["day", "contract"])
    assert bars["et"].max() < pd.Timestamp("2024-01-01"), "SEAL"
    bars = bars.sort_values(["day", "rank", "et"]).drop_duplicates(["contract", "et"]).reset_index(drop=True)
    bars.to_parquet(OUT / "crea_cl_two_months_1m.parquet", index=False)
    print("rows", len(bars), bars.groupby("rank").size().to_dict())


if __name__ == "__main__":
    main()

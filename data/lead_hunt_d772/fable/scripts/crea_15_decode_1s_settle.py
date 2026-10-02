"""Decode CL and NG outright ONE-SECOND bars 14:20:00-15:00:59 ET, 2017-05..2023-12 (free pull jobs UMCCWJ39BQ = CL.FUT,
S5DLBTQTSP = NG.FUT). Output ../out/crea_1s_settle_{CL,NG}.parquet: contract, et, ts, open, high, low, close, volume.
SEAL: files reaching 2024 never opened.   python crea_15_decode_1s_settle.py"""
import os, re, time
from pathlib import Path
import numpy as np
import pandas as pd
import databento as db

RAW = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento")
OUT = Path(__file__).resolve().parents[1] / "out"
JOBS = {"CL": "GLBX-20260924-UMCCWJ39BQ", "NG": "GLBX-20260924-S5DLBTQTSP"}
PX = 1e-9; CHUNK = 5_000_000


def ids_of(store, root):
    pat = re.compile(rf"^{root}([FGHJKMNQUVXZ])(\d{{1,2}})$"); rows = []
    for sym, ivs in store.metadata.mappings.items():
        if not pat.match(str(sym)):
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else getattr(iv, "symbol", None)
            if not sid:
                continue
            s = iv["start_date"] if isinstance(iv, dict) else getattr(iv, "start_date"); e = iv["end_date"] if isinstance(iv, dict) else getattr(iv, "end_date")
            rows.append((int(sid), str(sym), np.uint64(pd.Timestamp(s, tz="UTC").value), np.uint64(pd.Timestamp(e, tz="UTC").value)))
    return pd.DataFrame(rows, columns=["iid", "contract", "w0", "w1"])


def main():
    for root, job in JOBS.items():
        B = []
        for f in sorted(os.listdir(RAW / job)):
            if not f.endswith(".dbn.zst"):
                continue
            a_, b_ = f.split(".")[0].replace("glbx-mdp3-", "").split("-")
            if b_ >= "20240101":
                continue
            t0 = time.time(); st = db.DBNStore.from_file(RAW / job / f); w = ids_of(st, root); n = 0
            for arr in st.to_ndarray(count=CHUNK):
                n += len(arr)
                et = pd.to_datetime(arr["ts_event"], utc=True).tz_convert("US/Eastern")
                sec = et.hour * 3600 + et.minute * 60 + et.second
                keep = (sec >= 14 * 3600 + 20 * 60) & (sec <= 15 * 3600 + 59)
                a = arr[np.asarray(keep)]
                if len(a) == 0:
                    continue
                raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "ts": a["ts_event"].astype(np.uint64), "_i": np.arange(len(a))})
                j = raw.merge(w, on="iid", how="inner"); j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])].sort_values("_i")
                if len(j) == 0:
                    continue
                a = a[j["_i"].to_numpy()]
                B.append(pd.DataFrame({"contract": j["contract"].to_numpy(), "ts": a["ts_event"].astype(np.int64),
                                       "open": a["open"] * PX, "high": a["high"] * PX, "low": a["low"] * PX, "close": a["close"] * PX, "volume": a["volume"].astype(np.int64)}))
            print(root, f, n, round(time.time() - t0, 1), flush=True)
        d = pd.concat(B, ignore_index=True)
        d["et"] = pd.to_datetime(d["ts"], utc=True).dt.tz_convert("US/Eastern").dt.tz_localize(None)
        assert d["et"].max() < pd.Timestamp("2024-01-01"), "SEAL"
        d.to_parquet(OUT / f"crea_1s_settle_{root}.parquet", index=False)
        print(root, "rows", len(d), d["et"].min(), d["et"].max(), flush=True)


if __name__ == "__main__":
    main()

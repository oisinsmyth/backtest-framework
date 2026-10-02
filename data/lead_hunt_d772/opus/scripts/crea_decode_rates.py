"""Decode 1-minute ZN/ZB/ZF/ZT outright bars 08:00-12:05 ET, 2016..2023 (seal). System python; windowed id labelling from
the repo's build_fut_index_1m (read-only import). Output out/crea_rates_1m.parquet."""
import importlib.util, re, sys, time
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674")
RAW = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\databento")
OUT = Path(__file__).resolve().parents[1] / "out" / "crea_rates_1m.parquet"
SEAL = pd.Timestamp("2024-01-01", tz="US/Eastern")
_s = importlib.util.spec_from_file_location("build_fut_index_1m", REPO / "scripts" / "build_fut_index_1m.py")
BI = importlib.util.module_from_spec(_s); sys.modules["build_fut_index_1m"] = BI; _s.loader.exec_module(BI)
BI.OUTRIGHT = re.compile(r"^(ZN|ZB|ZF|ZT)([FGHJKMNQUVXZ])(\d{1,2})$")


def worker(path):
    import databento as db
    t0 = time.time()
    store = db.DBNStore.from_file(path)
    w = BI.ids_of(store)
    D = []
    if w is not None:
        for arr in store.to_ndarray(count=BI.CHUNK):
            j = BI.label_rows(arr, w).sort_values("_i")
            if len(j) == 0:
                continue
            a = arr[j["_i"].to_numpy()]
            ts = pd.to_datetime(a["ts_event"], utc=True).tz_convert("US/Eastern")
            hm = ts.hour * 60 + ts.minute
            k = np.asarray((ts < SEAL) & (hm >= 8 * 60) & (hm <= 12 * 60 + 5))
            if not k.any():
                continue
            D.append(pd.DataFrame({"root": j["root"].to_numpy()[k], "contract": j["contract"].to_numpy()[k],
                                   "day": ts[k].strftime("%Y-%m-%d"), "m": np.asarray(hm)[k].astype(np.int16),
                                   "close": a["close"][k] * BI.PX, "volume": a["volume"][k].astype(np.int64)}))
    return Path(path).name, (pd.concat(D, ignore_index=True) if D else None), time.time() - t0


def main():
    files = [f for f in sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name)
             if re.search(r"glbx-mdp3-(2016|2017|2018|2019|2020|2021|2022|2023)", f.name)]
    from multiprocessing import Pool
    t0 = time.time()
    with Pool(4) as p:
        res = p.map(worker, [str(f) for f in files], chunksize=1)
    df = pd.concat([r[1] for r in res if r[1] is not None], ignore_index=True)
    assert df["day"].max() < "2024-01-01"
    df = df.drop_duplicates(["root", "contract", "day", "m"], keep="last")
    df.to_parquet(OUT, index=False)
    print("rows", len(df), "secs", round(time.time() - t0, 1))
    print(df.groupby("root")["day"].agg(["min", "max", "count"]))


if __name__ == "__main__":
    main()

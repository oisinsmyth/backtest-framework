"""Decode 1-minute bars of micros and their E-mini/full parents, 2019-01..2023-12 ONLY (seal 2024-01-01).
System python (databento). Windowed id labelling borrowed (read-only import) from the repo's build_fut_index_1m.
Keeps ET 07:00-16:15 bars. Output: out/crea_micro_mini_1m.parquet (root, contract, ts_et_min, day, hhmm, close, volume).
"""
import importlib.util, re, sys, time
from pathlib import Path
import numpy as np, pandas as pd

REPO = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674")
RAW = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\databento")
OUT = Path(__file__).resolve().parents[1] / "out" / "crea_micro_mini_1m.parquet"
SEAL = pd.Timestamp("2024-01-01", tz="US/Eastern")
_s = importlib.util.spec_from_file_location("build_fut_index_1m", REPO / "scripts" / "build_fut_index_1m.py")
BI = importlib.util.module_from_spec(_s); sys.modules["build_fut_index_1m"] = BI; _s.loader.exec_module(BI)
BI.OUTRIGHT = re.compile(r"^(MES|MNQ|M2K|MYM|MGC|ES|NQ|RTY|YM|GC)([FGHJKMNQUVXZ])(\d{1,2})$")


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
            keep = (ts < SEAL)
            hm = ts.hour * 60 + ts.minute
            keep &= (hm >= 7 * 60) & (hm <= 16 * 60 + 15)
            if not keep.any():
                continue
            k = np.asarray(keep)
            D.append(pd.DataFrame({"root": j["root"].to_numpy()[k], "contract": j["contract"].to_numpy()[k],
                                   "day": ts[k].strftime("%Y-%m-%d"), "m": np.asarray(hm)[k].astype(np.int16),
                                   "close": a["close"][k] * BI.PX, "volume": a["volume"][k].astype(np.int64)}))
    df = pd.concat(D, ignore_index=True) if D else None
    return Path(path).name, df, time.time() - t0


def main():
    files = [f for f in sorted(RAW.glob("*/*.ohlcv-1m.dbn.zst"), key=lambda p: p.name)
             if re.search(r"glbx-mdp3-(2019|2020|2021|2022|2023)", f.name)]
    print(len(files), [f.name for f in files])
    from multiprocessing import Pool
    t0 = time.time()
    with Pool(4) as p:
        res = p.map(worker, [str(f) for f in files], chunksize=1)
    dfs = [r[1] for r in res if r[1] is not None]
    df = pd.concat(dfs, ignore_index=True)
    assert df["day"].max() < "2024-01-01"
    df = df.drop_duplicates(["root", "contract", "day", "m"], keep="last")
    df.to_parquet(OUT, index=False)
    print("rows", len(df), "secs", round(time.time() - t0, 1), "item", round(sum(r[2] for r in res), 1))
    print(df.groupby("root")["day"].agg(["min", "max", "count"]))


if __name__ == "__main__":
    main()

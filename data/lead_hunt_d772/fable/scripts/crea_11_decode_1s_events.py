"""A' step 3: decode ONE-SECOND bars (GLBX-20261001-Q949LNXFLK: ES NQ YM RTY MES MNQ MYM M2K parents) around every
micro/parent pause event, 2019-05..2023-12, window m0-10 min .. m0+20 min. Monthly files; only files whose month < 2024-01
are opened (SEAL). Output ../out/crea_1s_events.parquet with root, contract, ts (UTC ns), et, close, volume.

    python crea_11_decode_1s_events.py --workers 2
"""
import argparse, os, re, time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import numpy as np
import pandas as pd

RAW = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento/GLBX-20261001-Q949LNXFLK")
OUT = Path(__file__).resolve().parents[1] / "out"
OUTRIGHT = re.compile(r"^(ES|NQ|YM|RTY|MES|MNQ|MYM|M2K)([FGHJKMNQUVXZ])(\d{1,2})$")
PX = 1e-9; CHUNK = 5_000_000


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
    return pd.DataFrame(rows, columns=["iid", "root", "contract", "w0", "w1"]) if rows else None


def worker(args):
    path, windows = args   # windows: list of (t0_ns, t1_ns)
    import databento as db
    t0 = time.time(); store = db.DBNStore.from_file(path); w = ids_of(store); B = []; n = 0
    if w is None or not windows:
        return dict(file=Path(path).name, rows_in=0, kept=0, bars=None, secs=0)
    lo = np.array([a for a, b in windows], dtype=np.uint64); hi = np.array([b for a, b in windows], dtype=np.uint64)
    order = np.argsort(lo); lo = lo[order]; hi = hi[order]
    for arr in store.to_ndarray(count=CHUNK):
        n += len(arr)
        ts = arr["ts_event"].astype(np.uint64)
        # in any window? windows are non-overlapping-ish; use searchsorted on lo then check hi
        k = np.searchsorted(lo, ts, side="right") - 1
        ok = (k >= 0)
        ok[ok] = ts[ok] <= hi[k[ok]]
        a = arr[ok]
        if len(a) == 0:
            continue
        raw = pd.DataFrame({"iid": a["instrument_id"].astype(np.uint32), "ts": a["ts_event"].astype(np.uint64), "_i": np.arange(len(a))})
        j = raw.merge(w, on="iid", how="inner"); j = j[(j["ts"] >= j["w0"]) & (j["ts"] < j["w1"])].sort_values("_i")
        if len(j) == 0:
            continue
        a = a[j["_i"].to_numpy()]
        B.append(pd.DataFrame({"root": j["root"].to_numpy(), "contract": j["contract"].to_numpy(), "ts": a["ts_event"].astype(np.int64),
                               "open": a["open"] * PX, "high": a["high"] * PX, "low": a["low"] * PX, "close": a["close"] * PX, "volume": a["volume"].astype(np.int64)}))
    bars = pd.concat(B, ignore_index=True) if B else None
    return dict(file=Path(path).name, rows_in=n, kept=0 if bars is None else len(bars), bars=bars, secs=round(time.time() - t0, 1))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--workers", type=int, default=2); a = ap.parse_args()
    ev = pd.read_csv(OUT / "crea_04_status_events.csv", parse_dates=["start_et", "resume_et"])
    ev = ev[(ev["root"].isin(["MES", "MNQ", "ES", "NQ"])) & (ev["start_et"] >= "2019-05-01") & (ev["start_et"] < "2024-01-01") & (ev["secs"] >= 1) & (ev["secs"] <= 120)]
    m0 = ev["start_et"].dt.floor("min").drop_duplicates()
    utc = m0.dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").dt.tz_convert("UTC").dropna()
    wins = [(np.uint64((t - pd.Timedelta(minutes=10)).value), np.uint64((t + pd.Timedelta(minutes=20)).value)) for t in utc]
    print("events", len(m0), "windows", len(wins), flush=True)
    tasks = []
    for f in sorted(os.listdir(RAW)):
        if not f.endswith(".dbn.zst"):
            continue
        a_, b_ = f.split(".")[0].replace("glbx-mdp3-", "").split("-")
        if b_ >= "20240101" or a_ < "20190501":
            continue
        mo0 = pd.Timestamp(a_, tz="UTC"); mo1 = pd.Timestamp(b_, tz="UTC") + pd.Timedelta(days=1)
        ws = [(lo, hi) for lo, hi in wins if hi >= np.uint64(mo0.value) and lo <= np.uint64(mo1.value)]
        if ws:
            tasks.append((str(RAW / f), ws))
    print("files", len(tasks), flush=True)
    res = []
    with ProcessPoolExecutor(a.workers) as ex:
        for r in ex.map(worker, tasks):
            print(r["file"], r["rows_in"], r["kept"], r["secs"], flush=True); res.append(r)
    bars = pd.concat([r["bars"] for r in res if r["bars"] is not None], ignore_index=True)
    bars["et"] = pd.to_datetime(bars["ts"], utc=True).dt.tz_convert("US/Eastern").dt.tz_localize(None)
    assert bars["et"].max() < pd.Timestamp("2024-01-01"), "SEAL"
    bars.to_parquet(OUT / "crea_1s_events.parquet", index=False)
    print("rows", len(bars), bars.groupby("root").size().to_dict())


if __name__ == "__main__":
    main()

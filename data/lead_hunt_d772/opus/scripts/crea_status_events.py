"""Extract unscheduled status events (MarketEvent-reason PreOpen = velocity-logic style pauses; plus halts) on
outrights of key roots, 2016..2023 (seal). System python, 4 processes. Output out/crea_status_events.csv.
"""
import re, sys, time
from pathlib import Path
import numpy as np, pandas as pd

RAW = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\databento\GLBX-20260911-HSEKYEBHQ4")
OUT = Path(__file__).resolve().parents[1] / "out" / "crea_status_events.csv"
PAT = re.compile(r"^(ES|NQ|YM|RTY|MES|MNQ|GC|MGC|SI|HG|CL|MCL|NG|6E|6A|ZN|ZB)([FGHJKMNQUVXZ])(\d{1,2})$")


def worker(path):
    import databento as db
    t0 = time.time()
    store = db.DBNStore.from_file(path)
    rows = []
    for sym, ivs in store.metadata.mappings.items():
        m = PAT.match(str(sym))
        if not m:
            continue
        for iv in (ivs if isinstance(ivs, list) else [ivs]):
            sid = iv["symbol"] if isinstance(iv, dict) else iv.symbol
            s = iv["start_date"] if isinstance(iv, dict) else iv.start_date
            e = iv["end_date"] if isinstance(iv, dict) else iv.end_date
            rows.append((int(sid), m.group(1), str(sym), pd.Timestamp(s, tz="UTC").value, pd.Timestamp(e, tz="UTC").value))
    w = pd.DataFrame(rows, columns=["iid", "root", "sym", "w0", "w1"])
    keep = []
    for arr in store.to_ndarray(count=5_000_000):
        sel = ((arr["reason"] == 3) | (arr["action"] == 8) | (arr["reason"] == 2)) & (arr["action"] != 0)
        a = arr[sel]
        if len(a) == 0:
            continue
        d = pd.DataFrame({"iid": a["instrument_id"].astype(np.int64), "tsn": a["ts_event"].astype(np.int64),
                          "action": a["action"], "reason": a["reason"], "te": a["trading_event"]})
        j = d.merge(w, on="iid")
        j = j[(j.tsn >= j.w0) & (j.tsn < j.w1)]
        keep.append(j)
    out = pd.concat(keep) if keep else pd.DataFrame()
    return Path(path).name, out, time.time() - t0


if __name__ == "__main__":
    files = [f for f in sorted(RAW.glob("*.status.dbn.zst")) if re.search(r"-(2016|2017|2018|2019|2020|2021|2022|2023)0101-", f.name)]
    assert all("2024" not in f.name.split("-")[2][:4] for f in files)
    from multiprocessing import Pool
    t0 = time.time()
    with Pool(4) as p:
        res = p.map(worker, [str(f) for f in files], chunksize=1)
    df = pd.concat([r[1] for r in res if len(r[1])])
    df["et"] = pd.to_datetime(df.tsn, utc=True).dt.tz_convert("US/Eastern")
    assert df.et.max() < pd.Timestamp("2024-01-01", tz="US/Eastern")
    df.to_csv(OUT, index=False)
    print("secs", round(time.time() - t0, 1), [(r[0], round(r[2], 1)) for r in res])
    print(df.groupby(["root", "action", "reason"]).size().to_string())

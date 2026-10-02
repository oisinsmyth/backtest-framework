"""When did the ES daily 16:15-16:30 ET halt stop? Scan status files 2020-2023 (seal) for ES-outright PreOpen (action 1,
reason 1) events at 16:15 ET; print first/last date per year. System python."""
import re
from pathlib import Path
import numpy as np, pandas as pd
import databento as db

RAW = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\databento\GLBX-20260911-HSEKYEBHQ4")
pat = re.compile(r"^ES[HMUZ]\d{1,2}$")
for y in ["2020", "2021", "2022"]:
    f = next(RAW.glob(f"glbx-mdp3-{y}0101-*.status.dbn.zst"))
    store = db.DBNStore.from_file(f)
    ids = set()
    for sym, ivs in store.metadata.mappings.items():
        if pat.match(str(sym)):
            for iv in (ivs if isinstance(ivs, list) else [ivs]):
                ids.add(int(iv["symbol"] if isinstance(iv, dict) else iv.symbol))
    hits = []
    for arr in store.to_ndarray(count=5_000_000):
        k = (arr["action"] == 1) & (arr["reason"] == 1) & np.isin(arr["instrument_id"].astype(np.int64), list(ids))
        a = arr[k]
        if len(a):
            et = pd.to_datetime(a["ts_event"].astype(np.int64), utc=True).tz_convert("US/Eastern")
            sel = (et.hour == 16) & (et.minute == 15)
            hits.extend(sorted(set(et[sel].strftime("%Y-%m-%d"))))
    hits = sorted(set(hits))
    print(y, "16:15 PreOpen days:", len(hits), hits[:2], hits[-3:])

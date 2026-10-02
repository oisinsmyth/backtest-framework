"""Probe the CME status schema: what actions/reasons occur on outrights of key roots, at what ET clock? One year.
System python. Seal: the file read is <= 2023."""
import re, sys
from pathlib import Path
import numpy as np, pandas as pd
import databento as db

YEAR = sys.argv[1] if len(sys.argv) > 1 else "2019"
assert int(YEAR) <= 2023
RAW = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\databento\GLBX-20260911-HSEKYEBHQ4")
f = next(RAW.glob(f"glbx-mdp3-{YEAR}0101-*.status.dbn.zst"))
store = db.DBNStore.from_file(f)
pat = re.compile(r"^(ES|NQ|MES|MNQ|GC|MGC|CL|MCL|SI|HG|NG|6E|ZN|RTY|YM)([FGHJKMNQUVXZ])(\d{1,2})$")
rows = []
for sym, ivs in store.metadata.mappings.items():
    m = pat.match(str(sym))
    if not m:
        continue
    for iv in (ivs if isinstance(ivs, list) else [ivs]):
        sid = iv["symbol"] if isinstance(iv, dict) else iv.symbol
        s = iv["start_date"] if isinstance(iv, dict) else iv.start_date
        e = iv["end_date"] if isinstance(iv, dict) else iv.end_date
        rows.append((int(sid), m.group(1), str(sym), pd.Timestamp(s, tz="UTC").value, pd.Timestamp(e, tz="UTC").value))
w = pd.DataFrame(rows, columns=["iid", "root", "sym", "w0", "w1"])
df = store.to_df()
print(df.columns.tolist(), len(df))
df = df.reset_index()
df["iid"] = df["instrument_id"].astype(int)
df["tsn"] = pd.to_datetime(df["ts_event"]).astype("int64")
j = df.merge(w, on="iid")
j = j[(j["tsn"] >= j["w0"]) & (j["tsn"] < j["w1"])]
j["et"] = pd.to_datetime(j["ts_event"]).dt.tz_convert("US/Eastern")
j["hh"] = j["et"].dt.hour
print(j.groupby(["action", "reason"]).size().sort_values(ascending=False).head(30))
print(j.groupby(["root", "action", "reason"]).size().unstack(["action", "reason"]).fillna(0).astype(int).T.head(40))
# non-scheduled-looking: actions during RTH 10:00-15:00 ET
mid = j[(j["hh"] >= 10) & (j["hh"] < 15)]
print("mid-day events by root/action/reason")
print(mid.groupby(["root", "action", "reason", "trading_event"]).size().head(60))
j.to_pickle(Path(__file__).resolve().parents[1] / "out" / f"crea_status_{YEAR}.pkl")

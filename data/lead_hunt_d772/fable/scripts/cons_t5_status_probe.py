"""T5 probe: what does the CME `status` schema hold for 2022? Count (action, reason, trading_event) per root for the
instruments of ES, NQ, GC, CL, SI, HG, 6E, BTC, YM, RTY, NG -- looking for intraday pauses (Velocity Logic / Stop Logic
'Reserved' states) that would mark a liquidity-vacuum move. Read-only; one year file; nothing after 2023 is opened.
"""
import sys, os, json, time
import numpy as np, pandas as pd
import databento as db
P = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\databento\GLBX-20260911-HSEKYEBHQ4\glbx-mdp3-20220101-20221231.status.dbn.zst"
t0 = time.time()
store = db.DBNStore.from_file(P)
df = store.to_df()
print("rows", len(df), "cols", list(df.columns), f"{time.time()-t0:.0f}s", flush=True)
print(df.head(3).to_string(), flush=True)
# symbology: map instrument_id -> raw symbol via the store's symbology if present
try:
    sym = store.symbology
    print("symbology keys", list(sym.keys())[:5] if isinstance(sym, dict) else type(sym), flush=True)
except Exception as e:
    print("no symbology", e)
if "symbol" in df.columns:
    df["root"] = df["symbol"].astype(str).str.extract(r"^([A-Z0-9]{1,3}?)[FGHJKMNQUVXZ]\d{1,2}$")[0]
    df["root"] = df["root"].fillna(df["symbol"].astype(str).str[:2])
else:
    df["root"] = "?"
for c in ("action", "reason", "trading_event", "is_trading", "is_quoting"):
    if c in df.columns:
        print(c, df[c].value_counts().head(20).to_dict(), flush=True)
roots = ["ES", "NQ", "YM", "RTY", "GC", "SI", "HG", "CL", "NG", "6E", "BTC"]
sub = df[df.root.isin(roots)].copy()
sub["hour_et"] = pd.to_datetime(sub.index).tz_convert("America/New_York").hour if getattr(sub.index, "tz", None) is not None else -1
tab = sub.groupby(["root", "action", "reason"]).size().reset_index(name="n")
print(tab.sort_values("n", ascending=False).head(60).to_string(), flush=True)
# intraday, non-scheduled: actions during 09:30-16:00 ET excluding the scheduled daily halt hours
if "hour_et" in sub.columns:
    intr = sub[(sub.hour_et >= 9) & (sub.hour_et <= 16)]
    print("intraday 09-16 ET by root/action/reason:", flush=True)
    print(intr.groupby(["root", "action", "reason"]).size().reset_index(name="n").sort_values("n", ascending=False).head(40).to_string(), flush=True)
    intr.reset_index().to_csv(r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\fable_pair\out\cons_t5_status_2022_intraday.csv", index=False)
print("done")

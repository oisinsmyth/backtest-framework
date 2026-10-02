"""Peek at the status schema (2020 file) and the 1-second job metadata (symbols). Read-only. In-sample years only."""
import os, sys, collections
import databento as db
import pandas as pd

ROOT = r"C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento"

# --- 1-second jobs: which symbols?
for job in ["GLBX-20260924-NLQP44SHSR", "GLBX-20260924-S5DLBTQTSP", "GLBX-20260924-UMCCWJ39BQ", "GLBX-20261001-Q949LNXFLK"]:
    p = os.path.join(ROOT, job)
    fs = sorted(f for f in os.listdir(p) if f.endswith(".dbn.zst") and f.split(".")[0].replace("glbx-mdp3-", "") < "20240101")
    if not fs:
        print(job, "no in-sample files"); continue
    st = db.DBNStore.from_file(os.path.join(p, fs[0]))
    md = st.metadata
    print(job, fs[0], "schema", md.schema, "stype_in", md.stype_in, "symbols", md.symbols[:12], "n_symbols", len(md.symbols), "start", md.start, "end", md.end)

# --- status schema, the 2020 file
p = os.path.join(ROOT, "GLBX-20260911-HSEKYEBHQ4")
fs = sorted(os.listdir(p))
print("\nstatus files:", fs)
f2020 = [f for f in fs if f.startswith("glbx-mdp3-2020")][0]
st = db.DBNStore.from_file(os.path.join(p, f2020))
md = st.metadata
print("status metadata: schema", md.schema, "stype_in", md.stype_in, "stype_out", md.stype_out, "n symbols", len(md.symbols), "sample", md.symbols[:20])
df = st.to_df()
print("rows", len(df), "columns", df.columns.tolist())
print(df.head(5).to_string())
print("\naction x reason counts:")
print(df.groupby(["action", "reason"]).size().sort_values(ascending=False).head(40).to_string())
print("\ntrading_event counts:")
print(df["trading_event"].value_counts().head(20).to_string())
# ES only, during RTH ET
es = df[df["symbol"].astype(str).str.match(r"^ES[HMUZ]\d$")].copy()
es["et"] = es.index.tz_convert("America/New_York")
es["hhmm"] = es["et"].dt.strftime("%H:%M")
print("\nES rows", len(es))
rth = es[(es["hhmm"] >= "09:30") & (es["hhmm"] < "16:00")]
print("ES RTH rows", len(rth))
print(rth.groupby(["action", "reason", "trading_event"]).size().to_string())
print(rth.head(30)[["symbol", "action", "reason", "trading_event", "is_trading", "is_quoting", "et"]].to_string())
# non-scheduled events anywhere in ES
ns = es[~es["reason"].astype(str).isin(["Scheduled", "None", "GroupSchedule", "group_schedule", "scheduled"])]
print("\nES non-scheduled rows", len(ns))
print(ns.groupby(["action", "reason", "trading_event"]).size().to_string())
print(ns.head(40)[["symbol", "action", "reason", "trading_event", "is_trading", "is_quoting", "et"]].to_string())

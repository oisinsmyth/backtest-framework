import pandas as pd
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "out"
df = pd.read_csv(OUT / "crea_status_events.csv")
df = df[(df.action == 1) & (df.reason == 3)]
df["et"] = pd.to_datetime(df.tsn, utc=True).dt.tz_convert("US/Eastern")
df["min"] = df.et.dt.floor("min")
ev = df.groupby(["root", "min"]).agg(n_inst=("iid", "nunique"), syms=("sym", lambda s: ",".join(sorted(set(s))[:3]))).reset_index()
ev["yr"] = ev["min"].dt.year; ev["hr"] = ev["min"].dt.hour
print(ev.groupby(["root", "yr"]).size().unstack().fillna(0).astype(int).to_string())
print(ev.groupby(["root", "hr"]).size().unstack().fillna(0).astype(int).to_string())
print(ev.groupby("root").n_inst.describe().round(1).to_string())
print(ev[ev.root == "NQ"].head(20).to_string())
ev.to_csv(OUT / "crea_vl_events.csv", index=False)

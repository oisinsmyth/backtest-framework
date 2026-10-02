"""Probe the Databento GLBX status schema (one in-sample year) for halt / pause events."""
import sys
import databento as db
import pandas as pd
YEAR = sys.argv[1] if len(sys.argv) > 1 else "2019"
assert int(YEAR) <= 2023
P = rf"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\databento\GLBX-20260911-HSEKYEBHQ4\glbx-mdp3-{YEAR}0101-{YEAR}1231.status.dbn.zst"
store = db.DBNStore.from_file(P)
df = store.to_df()
print(df.shape); print(df.columns.tolist()); print(df.head())
for c in ["action", "reason", "trading_event", "is_trading", "is_quoting"]:
    if c in df.columns:
        print(c); print(df[c].value_counts().head(30))
print(pd.crosstab(df["action"], df["reason"]).to_string())
df.to_parquet(rf"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\opus_pair\out\cons_status_{YEAR}.parquet")

"""Premise test C, step 1: decode the CL/NG Trade-at-Settlement (CLT/NGT) one-second bars 2017-05..2023-12 from the free pull
(GLBX-20260924-NLQP44SHSR) into ../out/crea_tas_1s.parquet. Read-only; files reaching 2024 never opened (SEAL).
Prints the price convention (TAS prices are settlement offsets) and a per-year census."""
import os, time
from pathlib import Path
import numpy as np
import pandas as pd
import databento as db

RAW = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/raw/databento/GLBX-20260924-NLQP44SHSR")
OUT = Path(__file__).resolve().parents[1] / "out"
PX = 1e-9


def main():
    frames = []
    for f in sorted(os.listdir(RAW)):
        if not f.endswith(".dbn.zst"):
            continue
        a, b = f.split(".")[0].replace("glbx-mdp3-", "").split("-")
        if b >= "20240101":
            continue
        t0 = time.time(); st = db.DBNStore.from_file(RAW / f)
        df = st.to_df()
        df = df.reset_index()
        df["et"] = df["ts_event"].dt.tz_convert("US/Eastern").dt.tz_localize(None)
        df = df[["et", "symbol", "open", "high", "low", "close", "volume"]]
        frames.append(df); print(f, len(df), round(time.time() - t0, 1), flush=True)
    d = pd.concat(frames, ignore_index=True)
    assert d["et"].max() < pd.Timestamp("2024-01-01"), "SEAL"
    d["root"] = d["symbol"].str[:3]
    d.to_parquet(OUT / "crea_tas_1s.parquet", index=False)
    print("rows", len(d)); print(d["root"].value_counts().to_string())
    print("price distribution (close):"); print(d["close"].describe().to_string())
    print(d["close"].round(3).value_counts().head(25).to_string())
    d["year"] = d["et"].dt.year; d["hh"] = d["et"].dt.hour
    print(d.groupby(["root", "year"])["volume"].sum().unstack().to_string())
    print(d.groupby(["root", "hh"])["volume"].sum().unstack(fill_value=0).to_string())
    print(d.head(10).to_string())


if __name__ == "__main__":
    main()

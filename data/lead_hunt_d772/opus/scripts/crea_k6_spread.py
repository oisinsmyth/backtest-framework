"""K6 attack: the quoted MGC/GC spread at the K6 entry (Sunday-evening 18:59 bar of a Monday trade date) vs the same clock
on Tue-Fri trade dates, from the PAID china-window bbo-1m files (read-only; nothing written there). MGC 2022-2023, GC 2016-2023.
Spread in ticks (0.1) at bbo-1m snapshots 18:30..19:30 ET of the evening before the trade date. System python."""
import sys
from pathlib import Path
import numpy as np, pandas as pd
import databento as db

BASE = Path(r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\databento\china_window_2016_2023")
rows = []
for sym, years in [("MGC", ["2022", "2023"]), ("GC", ["2016", "2019", "2023"])]:
    for y in years:
        for f in sorted((BASE / f"{sym}_bbo-1m" / y).glob("*.dbn.zst")):
            td = pd.Timestamp(f.name[:10])
            assert td < pd.Timestamp("2024-01-01")
            try:
                df = db.DBNStore.from_file(f).to_df()
            except Exception as e:
                continue
            if df.empty:
                continue
            df = df.reset_index()
            tcol = "ts_recv" if "ts_recv" in df.columns else df.columns[0]
            et = pd.to_datetime(df[tcol], utc=True).dt.tz_convert("US/Eastern")
            hm = et.dt.hour * 60 + et.dt.minute
            sel = (hm >= 18 * 60 + 30) & (hm <= 19 * 60 + 30)
            s = df.loc[sel]
            if s.empty:
                continue
            spr = (s["ask_px_00"] - s["bid_px_00"]) / 0.1
            depth = s["bid_sz_00"] + s["ask_sz_00"]
            hh = hm[sel]
            for clock, lo, hi in [("18:30-18:45", 18 * 60 + 30, 18 * 60 + 45), ("18:55-19:00", 18 * 60 + 55, 19 * 60), ("19:15-19:30", 19 * 60 + 15, 19 * 60 + 30)]:
                k = (hh >= lo) & (hh < hi)
                if k.any():
                    rows.append(dict(sym=sym, td=td, dow=td.dayofweek, clock=clock, spr=float(np.nanmedian(spr[k])),
                                     sprmean=float(np.nanmean(spr[k])), depth=float(np.nanmedian(depth[k]))))
R = pd.DataFrame(rows)
R["grp"] = np.where(R.dow == 0, "Mon (Sun eve)", "Tue-Fri")
print(R.groupby(["sym", "clock", "grp"])[["spr", "sprmean", "depth"]].agg(["median", "mean", "count"]).round(2).to_string())

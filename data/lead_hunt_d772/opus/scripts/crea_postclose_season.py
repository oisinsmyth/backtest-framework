"""C5c: is the post-close-hour fade an EARNINGS effect? Split crea_postclose_fade rows (exit 10:00 next day) by
earnings season (Jan15-Feb10, Apr15-May10, Jul15-Aug10, Oct15-Nov10) vs the rest, per window and root.
Reads out/crea_postclose_fade_rows.csv (written by crea_postclose_fade.py; in-sample only)."""
import numpy as np, pandas as pd
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "out"
A = pd.read_csv(OUT / "crea_postclose_fade_rows.csv")
assert A.session.max() < "2024-01-01"
md = A.session.str[5:10]
ins = ((md >= "01-15") & (md <= "02-10")) | ((md >= "04-15") & (md <= "05-10")) | ((md >= "07-15") & (md <= "08-10")) | ((md >= "10-15") & (md <= "11-10"))
A["season"] = np.where(ins, "earn", "off")
g = A.groupby(["root", "win", "lab", "season"]).pnl.agg(["count", "mean", "median", "std"])
g["t"] = g["mean"] / g["std"] * np.sqrt(g["count"])
print(g.drop(columns="std").round(2).to_string())

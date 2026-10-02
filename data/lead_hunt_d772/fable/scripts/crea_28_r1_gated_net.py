"""Vol-gated R1 (MNG): NET by year at $4/$5/$6, top trades named, top months, daily Sharpe, both gates X=30 and X=40."""
import numpy as np, pandas as pd
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "out"
D = pd.read_csv(OUT / "crea_19_NG_days.csv").sort_values("sday").reset_index(drop=True); m = 1000.0
D["g60"] = -D["dir"] * D["y60"] * m; D["g60b"] = -D["dir"] * D["y60b"] * m
D["thr"] = D["absI"].shift(1).rolling(250, min_periods=120).quantile(2 / 3); D["top"] = D["absI"] >= D["thr"]
D["sd20"] = (D["y60"] * m).shift(1).rolling(20, min_periods=15).std(); D["month"] = D["sday"].str[:7]
for X in (30, 40):
    g = D[(D["sd20"] >= X) & D["top"]].copy()
    print(f"==== X={X}: n={len(g)}, gross y60 mean {g.g60.mean():.2f}, entry-14:30 variant {g.g60b.mean():.2f}")
    for c in (4, 5, 6):
        net = g["g60"] - c; tot = net.sum()
        by = net.groupby(g["year"]).agg(["size", "sum"]); by["share"] = (by["sum"] / tot).round(2)
        print(f"  cost ${c}: total net {tot:.0f}; by year:", {int(y): [int(r["size"]), round(r["sum"]), r["share"]] for y, r in by.iterrows()})
        # daily net Sharpe over all sessions in the span (zero on flat days)
        days = D[(D["sday"] >= g["sday"].min()) & (D["sday"] <= g["sday"].max())]["sday"]
        ser = pd.Series(0.0, index=days); ser.loc[g["sday"]] = net.to_numpy()
        print(f"     daily net Sharpe {ser.mean()/ser.std()*np.sqrt(252):.2f}; max drawdown {((ser.cumsum().cummax()-ser.cumsum()).max()):.0f}")
    top = g.nlargest(10, "g60")[["sday", "dir", "absI", "sd20", "g60"]]
    print("  top-10 trades:", [(r.sday, int(r.dir), round(r.g60)) for r in top.itertuples()], "share of gross", round(top.g60.sum() / g.g60.sum(), 2))
    mon = g.groupby("month")["g60"].sum().sort_values(ascending=False)
    print("  top months share of gross:", {k: round(v / g.g60.sum(), 2) for k, v in mon.head(3).items()})
    print("  2021 trades:", len(g[g.year == 2021]), "gross", round(g[g.year == 2021].g60.mean(), 2), "net4 sum", round((g[g.year == 2021].g60 - 4).sum()))

"""R1 follow-up (partner's (a)): walk-forward |I| tercile (threshold = 66.7th pct over the trailing 250 sessions, strictly before
today), y30/y60 by year, vol units, top-10 share, ex-2022, within-tercile dose, D630-traded days only."""
import numpy as np, pandas as pd
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "out"
D = pd.read_csv(OUT / "crea_19_NG_days.csv").sort_values("sday").reset_index(drop=True); m = 1000.0
for a, b in [("g30", "y30"), ("g60", "y60"), ("g30b", "y30b"), ("g60b", "y60b")]:
    D[a] = -D["dir"] * D[b] * m
thr = D["absI"].shift(1).rolling(250, min_periods=120).quantile(2 / 3)
W = D[D["absI"] >= thr].copy()


def st(g):
    g = np.asarray(g, float); q = np.quantile(g, [.01, .99]); s = np.sort(g); ok = (g >= q[0]) & (g <= q[1])
    return dict(n=len(g), mean=round(g.mean(), 2), t=round(g.mean() / g.std() * np.sqrt(len(g)), 2), med=round(float(np.median(g)), 2),
                trim=round(g[ok].mean(), 2), win=round((g > 0).mean(), 3), top10=round(s[-10:].sum() / g.sum(), 2) if g.sum() > 0 else None)


print("WALK-FORWARD top tercile (trailing-250 threshold), n", len(W), "per year", round(len(W) / W["year"].nunique(), 1))
for c in ["g30", "g60", "g30b", "g60b"]:
    print(" pooled", c, st(W[c]))
print(" ex-2022 pooled g30", st(W[W.year != 2022]["g30"]), " g60", st(W[W.year != 2022]["g60"]))
print(" by year: n | g30 mean,t | g60 mean,t,median | sd(y60)$ | g60/sd | share of g60 total")
tot = W["g60"].sum()
for y, g in W.groupby("year"):
    sd = D[D.year == y]["y60"].std() * m
    print("  ", y, len(g), "|", round(g.g30.mean(), 2), round(g.g30.mean() / g.g30.std() * np.sqrt(len(g)), 2), "|", round(g.g60.mean(), 2),
          round(g.g60.mean() / g.g60.std() * np.sqrt(len(g)), 2), round(g.g60.median(), 1), "|", round(sd, 1), "|", round(g.g60.mean() / sd, 3), "|", round(g.g60.sum() / tot, 2))
D["t3"] = pd.qcut(D["absI"].rank(method="first"), 3, labels=False); T = D[D.t3 == 2]
print("POOLED in-sample top tercile y60 by year:"); print(T.groupby("year")["g60"].agg(["size", "mean", "median"]).round(2).to_string())
print("pooled top tercile g60", st(T["g60"]))
W["r"] = W["absI"] / thr[W.index]; W["q"] = pd.qcut(W["r"].rank(method="first"), 3, labels=False)
print("within-WF-tercile dose (|I|/threshold terciles) g30/g60:"); print(W.groupby("q")[["g30", "g60"]].mean().round(2).to_string())
print("WF & D630-traded days:", st(W[W.traded]["g60"]), "n/yr", round(W.traded.sum() / W["year"].nunique(), 1))
# within-year terciles (each year contributes a third)
D["t3y"] = D.groupby("year")["absI"].transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False)); Y = D[D.t3y == 2]
print("WITHIN-YEAR top tercile pooled g30", st(Y["g30"]), "g60", st(Y["g60"]))
print(Y.groupby("year")[["g30", "g60"]].agg(["size", "mean"]).round(2).to_string())
W.to_csv(OUT / "crea_23_NG_wf_days.csv", index=False)

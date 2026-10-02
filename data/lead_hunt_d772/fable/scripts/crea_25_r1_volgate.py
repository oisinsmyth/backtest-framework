"""R1 with a pre-declared EX-ANTE volatility gate (partner's reframing, the principal's abstention principle):
gate_t = trailing-20-session sd of the 14:29->15:29 MNG move (dollars; sessions t-20..t-1, known at 14:29 of t) >= X,
X in {30, 40} from the arithmetic (0.15 sd/trade x sd = 1.0x / 1.5x of $4). On gated days: walk-forward top tercile |I|
(trailing-250 threshold) fade y60, by year; ungated-days book; gated-days book WITHOUT the flow signer (bottom two terciles
and all gated days signed by dir); selectivity per year; net at $4/$5/$6; top-10 share; trimmed."""
import json
import numpy as np, pandas as pd
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "out"
D = pd.read_csv(OUT / "crea_19_NG_days.csv").sort_values("sday").reset_index(drop=True); m = 1000.0
D["g60"] = -D["dir"] * D["y60"] * m; D["g30"] = -D["dir"] * D["y30"] * m; D["g60b"] = -D["dir"] * D["y60b"] * m
D["thr"] = D["absI"].shift(1).rolling(250, min_periods=120).quantile(2 / 3)
D["top"] = D["absI"] >= D["thr"]
D["sd20"] = (D["y60"] * m).shift(1).rolling(20, min_periods=15).std()
D["year"] = D["year"].astype(int)


def st(g):
    g = np.asarray(g, float); g = g[np.isfinite(g)]
    if len(g) < 5:
        return dict(n=len(g))
    q = np.quantile(g, [.01, .99]); s = np.sort(g); ok = (g >= q[0]) & (g <= q[1])
    return dict(n=len(g), mean=round(g.mean(), 2), t=round(g.mean() / g.std() * np.sqrt(len(g)), 2), med=round(float(np.median(g)), 2), trim=round(g[ok].mean(), 2),
                win=round((g > 0).mean(), 3), top10=round(s[-10:].sum() / g.sum(), 2) if g.sum() > 0 else None, net4=round(g.mean() - 4, 2), net5=round(g.mean() - 5, 2), net6=round(g.mean() - 6, 2))


res = {}
for X in (20, 30, 40):
    g_open = D["sd20"] >= X
    gated = D[g_open & D["top"]]; ungated_top = D[(~g_open) & D["top"]]
    o = dict(X=X, gated_days_share_by_year={int(y): round(float(g.mean()), 2) for y, g in g_open.groupby(D["year"])},
             gated_top_tercile_y60=st(gated["g60"]), gated_top_tercile_y30=st(gated["g30"]), gated_top_tercile_y60_entry1430=st(gated["g60b"]),
             gated_top_by_year_y60={int(y): [len(g), round(float(g["g60"].mean()), 2), round(float(g["g60"].median()), 1)] for y, g in gated.groupby("year")},
             ungated_top_tercile_y60=st(ungated_top["g60"]),
             gated_NO_flow_signer_all_days_y60=st(D.loc[g_open, "g60"]), gated_bottom_two_terciles_y60=st(D.loc[g_open & (~D["top"]) & D["thr"].notna(), "g60"]),
             gated_top_in_vol_units=round(float((gated["g60"] / gated["sd20"]).mean()), 3), ungated_top_in_vol_units=round(float((ungated_top["g60"] / ungated_top["sd20"]).mean()), 3))
    res[X] = o
    print(json.dumps(o, indent=1, default=str), flush=True)
# the gate alone as a continuous variable: fade y60 (top tercile) by sd20 quartile
T = D[D["top"] & D["sd20"].notna()].copy(); T["sq"] = pd.qcut(T["sd20"], 4, labels=False)
print("top tercile fade y60 by sd20 quartile:", {int(q): [len(g), round(float(g["sd20"].mean()), 1), round(float(g["g60"].mean()), 2), round(float((g["g60"] / g["sd20"]).mean()), 3)] for q, g in T.groupby("sq")})
(OUT / "crea_25_r1_volgate.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")

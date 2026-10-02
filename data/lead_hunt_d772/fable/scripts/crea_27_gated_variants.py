"""Ex-ante vol gates (trailing-20-session sd of the outcome leg, known before entry; thresholds from the breakeven arithmetic
cost/0.15 for 1.0x and 1.5x) applied to: (c) the TAS-signed CL fade (crea_10b W_late top tercile, y60 = 14:30->15:29; MCL
cost $5.03 -> X = $34 / $50) and (d) the LETF post-close reversal on NQ/ES (crea_24 construction, y5 and y10; MNQ $4.07 ->
X = $27 / $41; MES $4.42 -> $29 / $44). Reports gated / ungated books, by year, vol units, top-10 share."""
import json, sys
import numpy as np, pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_panels import panel
OUT = Path(__file__).resolve().parents[1] / "out"


def st(g):
    g = np.asarray(g, float); g = g[np.isfinite(g)]
    if len(g) < 5:
        return dict(n=len(g))
    q = np.quantile(g, [.01, .99]); s = np.sort(g); ok = (g >= q[0]) & (g <= q[1])
    return dict(n=len(g), mean=round(g.mean(), 2), t=round(g.mean() / g.std() * np.sqrt(len(g)), 2), med=round(float(np.median(g)), 2), trim=round(g[ok].mean(), 2),
                win=round((g > 0).mean(), 3), top10=round(s[-10:].sum() / g.sum(), 2) if g.sum() > 0 else None)


res = {}
# (c) CL TAS
D = pd.read_csv(OUT / "crea_10b_CL_days.csv").sort_values("sday").reset_index(drop=True); m = 100.0
D["y60"] = D["15:29"] - D["14:30"]; D["g60"] = -np.sign(D["Wl"]) * D["y60"] * m; D["sd20"] = (D["y60"] * m).shift(1).rolling(20, min_periods=15).std()
D["thr"] = D["Wl"].abs().shift(1).rolling(250, min_periods=120).quantile(2 / 3); D["top"] = (D["Wl"] != 0) & (D["Wl"].abs() >= D["thr"])
o = {}
for X in (34, 50):
    gate = D["sd20"] >= X; g = D[gate & D["top"]]; u = D[(~gate) & D["top"]]
    o[f"X{X}"] = dict(share_open_by_year={y: round(float(v.mean()), 2) for y, v in gate.groupby(D["year"])}, gated_top=st(g["g60"]), ungated_top=st(u["g60"]),
                      gated_by_year={int(y): [len(v), round(float(v["g60"].mean()), 2)] for y, v in g.groupby("year")}, gated_vol_units=round(float((g["g60"] / g["sd20"]).mean()), 3), ungated_vol_units=round(float((u["g60"] / u["sd20"]).mean()), 3),
                      gated_window_move_fade_control=st(-np.sign(D.loc[gate & (D.xw != 0), "xw"]) * D.loc[gate & (D.xw != 0), "y60"] * m))
res["CL_TAS_gated"] = o; print("CL_TAS_gated", json.dumps(o, indent=1, default=str), flush=True)
# (d) LETF close reversal NQ / ES
for root, m, cost in [("NQ", 2.0, 4.07), ("ES", 5.0, 4.42)]:
    P = panel(root); P = P[P["day"] >= "2016-01-04"].copy(); P["hhmm"] = P["et"].dt.strftime("%H:%M")
    def at(h, lo):
        s = P[(P["hhmm"] <= h) & (P["hhmm"] >= lo)].groupby("day").tail(1).set_index("day"); return s["close"], s["contract"]
    S = {}
    for lab, h, lo in [("p0930", "09:29", "09:00"), ("p1600", "15:59", "15:00"), ("p1605", "16:04", "15:00"), ("p1610", "16:09", "15:00")]:
        S[lab], con = at(h, lo)
    S = pd.DataFrame(S); S["contract"] = con; S = S.dropna(); S = S[S["contract"] == S["contract"].shift(1)].copy()
    S["r"] = S["p1600"] / S["p0930"] - 1; S["y5"] = S["p1605"] - S["p1600"]; S["y10"] = S["p1610"] - S["p1600"]; S["year"] = S.index.str[:4]
    S["thr"] = S["r"].abs().shift(1).rolling(250, min_periods=120).quantile(2 / 3); S["top"] = (S["r"] != 0) & (S["r"].abs() >= S["thr"])
    for h in ["y5", "y10"]:
        S[f"g{h}"] = -np.sign(S["r"]) * S[h] * m; S[f"sd20_{h}"] = (S[h] * m).shift(1).rolling(20, min_periods=15).std()
    o = dict(walkforward_top_ungated={h: st(S.loc[S["top"], f"g{h}"]) for h in ["y5", "y10"]},
             wf_top_by_year_y5={int(y): [len(v), round(float(v["gy5"].mean()), 2)] for y, v in S[S["top"]].groupby("year")})
    for X in (round(cost / 0.15), round(1.5 * cost / 0.15)):
        for h in ["y5", "y10"]:
            gate = S[f"sd20_{h}"] >= X; g = S[gate & S["top"]]; u = S[(~gate) & S["top"]]
            o[f"X{X}_{h}"] = dict(share_open={y: round(float(v.mean()), 2) for y, v in gate.groupby(S["year"])}, gated_top=st(g[f"g{h}"]), ungated_top=st(u[f"g{h}"]),
                                  gated_by_year={int(y): [len(v), round(float(v[f"g{h}"].mean()), 2)] for y, v in g.groupby("year")},
                                  gated_vol_units=round(float((g[f"g{h}"] / g[f"sd20_{h}"]).mean()), 3), ungated_vol_units=round(float((u[f"g{h}"] / u[f"sd20_{h}"]).mean()), 3))
    res[f"LETF_{root}"] = o; print(root, json.dumps(o, indent=1, default=str), flush=True)
(OUT / "crea_27_gated_variants.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")

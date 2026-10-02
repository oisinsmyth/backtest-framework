"""Partner's (3): CL front vs second month at 1 minute, 2016-2023. Signer = the K-minute change of the front-second spread
(front-specific flow); fade it in the FRONT (MCL, $100/pt) over the next H minutes; compare with the raw front move's fade
(the momentum control) and with the parallel-shift component. Windows: 09:00-14:00 ET (every 5th minute, non-overlapping
trades) and the 14:00-14:30 window separately (x = spread change 14:00->14:30, y = front 14:30->15:00)."""
import json
import numpy as np, pandas as pd
from pathlib import Path
OUT = Path(__file__).resolve().parents[1] / "out"
b = pd.read_parquet(OUT / "crea_cl_two_months_1m.parquet"); b["et"] = pd.to_datetime(b["et"])
f = b[b["rank"] == 1][["day", "et", "close"]].rename(columns={"close": "f"}); s = b[b["rank"] == 2][["et", "close"]].rename(columns={"close": "s"})
d = f.merge(s, on="et", how="inner").sort_values("et").reset_index(drop=True)
d["hhmm"] = d["et"].dt.strftime("%H:%M"); d["spr"] = d["f"] - d["s"]; d["year"] = d["day"].str[:4]
d = d[(d["day"] >= "2016-01-04") & (d["day"] <= "2023-12-29")]
print("minutes", len(d), "days", d["day"].nunique(), "median |spread|", round(float(d["spr"].abs().median()), 3))
m, cost = 100.0, 5.03


def st(g):
    g = np.asarray(g, float); g = g[np.isfinite(g)]
    if len(g) < 20:
        return dict(n=len(g))
    q = np.quantile(g, [.01, .99]); ok = (g >= q[0]) & (g <= q[1])
    return dict(n=len(g), gross=round(g.mean(), 2), t=round(g.mean() / g.std() * np.sqrt(len(g)), 2), med=round(float(np.median(g)), 2), trim=round(g[ok].mean(), 2), win=round((g > 0).mean(), 3), net=round(g.mean() - cost, 2))


res = {}
for K, H in [(30, 30), (30, 60), (15, 30)]:
    rows = []
    for day, g in d.groupby("day", sort=False):
        g = g.set_index("hhmm")
        for t0 in [f"{h:02d}:{mm:02d}" for h in range(9, 14) for mm in (0, 30)]:
            t_pre = (pd.Timestamp("2000-01-01 " + t0) - pd.Timedelta(minutes=K)).strftime("%H:%M"); t_post = (pd.Timestamp("2000-01-01 " + t0) + pd.Timedelta(minutes=H)).strftime("%H:%M")
            if t_pre in g.index and t0 in g.index and t_post in g.index:
                rows.append(dict(day=day, t0=t0, dspr=g.at[t0, "spr"] - g.at[t_pre, "spr"], dfront=g.at[t0, "f"] - g.at[t_pre, "f"], dsecond=g.at[t0, "s"] - g.at[t_pre, "s"], y=g.at[t_post, "f"] - g.at[t0, "f"]))
    R = pd.DataFrame(rows); R["year"] = R["day"].str[:4]
    nz = R[R["dspr"] != 0]
    thr = nz["dspr"].abs().quantile(2 / 3); top = nz[nz["dspr"].abs() >= thr]
    # 'front-specific' = spread moved but the parallel component did not: top |dspr| and bottom-half |dsecond|
    pure = top[top["dsecond"].abs() <= nz["dsecond"].abs().median()]
    o = dict(K=K, H=H, n=len(R), rho_dspr_y=round(float(np.corrcoef(nz["dspr"], nz["y"])[0, 1]), 3), rho_dfront_y=round(float(np.corrcoef(R["dfront"], R["y"])[0, 1]), 3), rho_dsecond_y=round(float(np.corrcoef(R["dsecond"], R["y"])[0, 1]), 3),
             sd_y_usd=round(float(R["y"].std() * m), 1), sd_dspr_ticks=round(float(nz["dspr"].std() * 100), 2),
             fade_dspr_top=st(-np.sign(top["dspr"]) * top["y"] * m), fade_dspr_all=st(-np.sign(nz["dspr"]) * nz["y"] * m),
             fade_dspr_top_pure_front_specific=st(-np.sign(pure["dspr"]) * pure["y"] * m),
             control_fade_dfront_top=st(-np.sign(R.loc[R["dfront"].abs() >= R["dfront"].abs().quantile(2 / 3), "dfront"]) * R.loc[R["dfront"].abs() >= R["dfront"].abs().quantile(2 / 3), "y"] * m),
             fade_dspr_top_years={y: [len(g), round(float((-np.sign(g["dspr"]) * g["y"] * m).mean()), 2)] for y, g in top.groupby("year")})
    res[f"K{K}_H{H}"] = o; print(json.dumps(o, indent=1, default=str), flush=True)
# settlement window
rows = []
for day, g in d.groupby("day", sort=False):
    g = g.set_index("hhmm")
    if all(t in g.index for t in ["13:59", "14:29", "14:59", "15:29"]):
        rows.append(dict(day=day, dspr=g.at["14:29", "spr"] - g.at["13:59", "spr"], dfront=g.at["14:29", "f"] - g.at["13:59", "f"], y30=g.at["14:59", "f"] - g.at["14:29", "f"], y60=g.at["15:29", "f"] - g.at["14:29", "f"]))
R = pd.DataFrame(rows); R["year"] = R["day"].str[:4]; nz = R[R["dspr"] != 0]; thr = nz["dspr"].abs().quantile(2 / 3); top = nz[nz["dspr"].abs() >= thr]
o = dict(n=len(R), rho_dspr_y30=round(float(np.corrcoef(nz["dspr"], nz["y30"])[0, 1]), 3), rho_dspr_y60=round(float(np.corrcoef(nz["dspr"], nz["y60"])[0, 1]), 3), rho_dfront_y30=round(float(np.corrcoef(R["dfront"], R["y30"])[0, 1]), 3),
         fade_top_y30=st(-np.sign(top["dspr"]) * top["y30"] * m), fade_top_y60=st(-np.sign(top["dspr"]) * top["y60"] * m), fade_all_y60=st(-np.sign(nz["dspr"]) * nz["y60"] * m),
         years_y60={y: [len(g), round(float((-np.sign(g["dspr"]) * g["y60"] * m).mean()), 2)] for y, g in top.groupby("year")})
res["settlement_window"] = o; print("SETTLEMENT", json.dumps(o, indent=1, default=str))
(OUT / "crea_26_cl_term_structure.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")

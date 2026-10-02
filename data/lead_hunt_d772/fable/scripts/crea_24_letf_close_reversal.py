"""R3: the index LETF rebalance's post-close reversal sized by the day's return. At 16:00 ET the leveraged funds (TQQQ/SQQQ,
UPRO/SPXU, TNA/TZA, UDOW/SDOW) rebalance in the DAY's direction with size ~ AUM x |r_day|; the pressure into the close
reverses after it. Trade: at the 16:00 close fade sign(r_day) [r_day = P(16:00)/P(prev 16:00) - 1 or P(16:00)/P(09:30)],
exit 16:05 / 16:10 (flat by 16:10) on MNQ/MES/M2K/MYM; cells by |r_day| tercile (pooled and within-year); controls: the
same at 15:00 (x = 09:30->15:00, y = 15:00->15:10) and at 12:00; D762's unsigned 15:50->16:00 pressure fade beside.
2016-2023 (RTY from 2018). Rotation null. Dollars per micro.

    python crea_24_letf_close_reversal.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_panels import panel
from crea_10_tas_settlement import stats, rot

OUT = Path(__file__).resolve().parents[1] / "out"
CFG = {"NQ": (2.0, 4.07), "ES": (5.0, 4.42), "RTY": (5.0, 3.76), "YM": (0.5, 3.80)}


def main():
    res = {}
    for root, (m, cost) in CFG.items():
        P = panel(root); P = P[P["day"] >= ("2018-01-01" if root == "RTY" else "2016-01-04")].copy(); P["hhmm"] = P["et"].dt.strftime("%H:%M")
        def at(h, lo):
            s = P[(P["hhmm"] <= h) & (P["hhmm"] >= lo)].groupby("day").tail(1).set_index("day"); return s["close"], s["contract"]
        S = {}
        for lab, h, lo in [("p0930", "09:29", "09:00"), ("p1200", "11:59", "11:00"), ("p1210", "12:09", "11:00"), ("p1500", "14:59", "14:00"), ("p1510", "15:09", "14:00"),
                           ("p1550", "15:49", "15:00"), ("p1600", "15:59", "15:00"), ("p1605", "16:04", "15:00"), ("p1610", "16:09", "15:00")]:
            S[lab], con = at(h, lo)
        S = pd.DataFrame(S); S["contract"] = con; S = S.dropna()
        S["prev1600"] = S["p1600"].shift(1); S["prev_con"] = S["contract"].shift(1)
        S = S[S["contract"] == S["prev_con"]].copy()
        S["r_cc"] = S["p1600"] / S["prev1600"] - 1; S["r_oc"] = S["p1600"] / S["p0930"] - 1
        S["y5"] = S["p1605"] - S["p1600"]; S["y10"] = S["p1610"] - S["p1600"]; S["x10"] = S["p1600"] - S["p1550"]
        S["c15_x"] = S["p1500"] / S["p0930"] - 1; S["c15_y"] = S["p1510"] - S["p1500"]; S["c12_x"] = S["p1200"] / S["p0930"] - 1; S["c12_y"] = S["p1210"] - S["p1200"]
        S["year"] = S.index.str[:4]
        out = dict(root=root, n=len(S), sd_y10_usd=round(float(S["y10"].std() * m), 1),
                   rho={k: round(float(np.corrcoef(S[a], S[b])[0, 1]), 3) for k, a, b in [("rcc_y10", "r_cc", "y10"), ("roc_y10", "r_oc", "y10"), ("rcc_y5", "r_cc", "y5"), ("x10_y10", "x10", "y10"), ("c15", "c15_x", "c15_y"), ("c12", "c12_x", "c12_y")]})
        for sig in ["r_cc", "r_oc"]:
            nz = S[S[sig] != 0]
            nz = nz.assign(q=pd.qcut(nz[sig].abs().rank(method="first"), 3, labels=False), qy=nz.groupby("year")[sig].transform(lambda s: pd.qcut(s.abs().rank(method="first"), 3, labels=False)))
            top = nz[nz["q"] == 2]; s = -np.sign(top[sig]).to_numpy()
            o = dict(all={h: stats(-np.sign(nz[sig]) * nz[h] * m, cost) for h in ["y5", "y10"]},
                     top_tercile={h: stats(s * top[h] * m, cost) for h in ["y5", "y10"]}, top_rot_y10=rot(s, top["y10"].to_numpy(), m),
                     top_years_y10={y: [len(g), round(float((-np.sign(g[sig]) * g["y10"] * m).mean()), 2)] for y, g in top.groupby("year")},
                     dose_y10={int(q): round(float((-np.sign(g[sig]) * g["y10"] * m).mean()), 2) for q, g in nz.groupby("q")},
                     within_year_top={h: stats(-np.sign(nz.loc[nz.qy == 2, sig]) * nz.loc[nz.qy == 2, h] * m, cost) for h in ["y5", "y10"]},
                     long_side_top=stats(top.loc[s > 0, "y10"] * m, cost), short_side_top=stats(-top.loc[s < 0, "y10"] * m, cost))
            # clock controls on the same tercile rule
            for cx, cy, lab in [("c15_x", "c15_y", "ctl_1500"), ("c12_x", "c12_y", "ctl_1200")]:
                cz = S[S[cx] != 0]; thr = cz[cx].abs().quantile(2 / 3); ct = cz[cz[cx].abs() >= thr]
                o[lab + "_top_fade10"] = stats(-np.sign(ct[cx]) * ct[cy] * m, cost)
            out[sig] = o
        out["d762_unsigned_x10_fade_top"] = stats(-np.sign(S.loc[S["x10"].abs() >= S["x10"].abs().quantile(2 / 3), "x10"]) * S.loc[S["x10"].abs() >= S["x10"].abs().quantile(2 / 3), "y10"] * m, cost)
        res[root] = out
        print(json.dumps(out, indent=1, default=str), flush=True)
    (OUT / "crea_24_letf_close_reversal.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

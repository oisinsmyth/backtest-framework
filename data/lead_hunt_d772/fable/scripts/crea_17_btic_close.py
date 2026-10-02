"""N1: BTIC-signed cash-close fade on ES/NQ/YM (MES/MNQ/MYM), 2016-2023, and the TACO-signed cash-open fade on ES/NQ.
BTIC (EST/NQT/YMT) trades at a BASIS to the 16:00 cash close; the fair basis barely moves within a day, so the change of the
BTIC volume-weighted price from the morning (09:30-12:00) to the late afternoon (14:00-15:45) is the imbalance premium:
dB > 0 = BTIC buyers paying up = their counterparties must BUY the cash close (MOC) = the close is pushed up = fade SHORT
16:00 -> 16:10 (flat before 16:10). Also the afternoon-only BTIC VWAP minus the previous day's afternoon VWAP (dB_prev).
TACO (ESQ/NQQ): basis to the 09:30 cash open; dO = overnight TACO VWAP (18:00-09:25) minus the previous afternoon BTIC VWAP;
fade 09:30 -> 09:45 with side -sign(dO). Prices from the Globex 1-minute panels (P(16:00) = close of the 15:59 bar).

    python crea_17_btic_close.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_panels import panel
from crea_10_tas_settlement import stats, rot

OUT = Path(__file__).resolve().parents[1] / "out"
CFG = {"ES": dict(btic="EST", taco="ESQ", mult=5.0, cost=4.42), "NQ": dict(btic="NQT", taco="NQQ", mult=2.0, cost=4.07), "YM": dict(btic="YMT", taco=None, mult=0.5, cost=3.80)}


def vwap(t, lo, hi):
    s = t[(t["hhmm"] >= lo) & (t["hhmm"] < hi)]
    g = s.groupby("sday").agg(V=("volume", "sum"), VK=("vk", "sum"))
    return (g["VK"] / g["V"]).rename("w"), g["V"].rename("V")


def main():
    tb = pd.read_parquet(OUT / "crea_tasbtic_1m.parquet")
    res = {}
    for root, c in CFG.items():
        P = panel(root); P = P[P["day"] >= "2016-01-04"].copy(); P["hhmm"] = P["et"].dt.strftime("%H:%M")
        def at(hhmm, lo="09:00"):
            s = P[(P["hhmm"] <= hhmm) & (P["hhmm"] >= lo)].groupby("day").tail(1).set_index("day"); return s["close"], s["contract"]
        S = {}
        for lab, h in [("p1550", "15:49"), ("p1600", "15:59"), ("p1605", "16:04"), ("p1610", "16:09"), ("p1545", "15:44")]:
            S[lab], con = at(h)
        o = {}
        for lab, h in [("o0925", "09:24"), ("o0930", "09:29"), ("o0935", "09:34"), ("o0945", "09:44"), ("o1000", "09:59")]:
            o[lab], _ = at(h, lo="09:00")
        S = pd.DataFrame(S); S["contract"] = con; S = S.join(pd.DataFrame(o)).dropna().reset_index().rename(columns={"day": "sday"})
        chg = S["contract"] != S["contract"].shift(1); near = chg | chg.shift(-1, fill_value=False) | chg.shift(1, fill_value=False); S = S[~near]
        t = tb[tb["kind"] == c["btic"]].copy(); t["hhmm"] = t["et"].dt.strftime("%H:%M"); t["sday"] = t["et"].dt.strftime("%Y-%m-%d"); t["vk"] = t["volume"] * t["close"]
        # BTIC on the SAME contract as the panel's front: require the symbol's month code to match
        t["tcode"] = t["symbol"].str[-2:]
        fm = S.set_index("sday")["contract"].str[-2:]
        t = t[t["sday"].map(fm) == t["tcode"]]
        wm, Vm = vwap(t, "09:30", "12:00"); wa, Va = vwap(t, "14:00", "15:45"); wall, Vall = vwap(t, "00:00", "15:45")
        D = S.set_index("sday").join(wm.rename("wm")).join(Vm.rename("Vm")).join(wa.rename("wa")).join(Va.rename("Va")).join(wall.rename("wall")).join(Vall.rename("Vall"))
        D["wa_prev"] = D["wa"].shift(1)
        D["dB"] = D["wa"] - D["wm"]; D["dB_prev"] = D["wa"] - D["wa_prev"]
        D["x"] = D["p1600"] - D["p1550"]; D["x15"] = D["p1600"] - D["p1545"]; D["y5"] = D["p1605"] - D["p1600"]; D["y10"] = D["p1610"] - D["p1600"]
        D["year"] = D.index.str[:4]
        m, cost = c["mult"], c["cost"]
        Dd = D.dropna(subset=["dB", "y10"]).copy()
        print(root, "days with BTIC both halves", len(Dd), "median afternoon BTIC volume", float(Dd["Va"].median()), flush=True)
        out = dict(root=root, n=len(Dd), Va_median=float(Dd["Va"].median()), dB_abs_median_pts=round(float(Dd["dB"].abs().median()), 3),
                   sd_usd={k: round(float(Dd[k].std() * m), 1) for k in ["x", "y5", "y10"]},
                   rho={f"{s}_{y}": round(float(np.corrcoef(Dd[s].fillna(0), Dd[y])[0, 1]), 3) for s in ["dB", "dB_prev", "x15"] for y in ["x", "y5", "y10"]})
        for sig in ["dB", "dB_prev"]:
            nz = Dd.dropna(subset=[sig]); nz = nz[nz[sig] != 0]
            if len(nz) < 100:
                out[f"fade_{sig}"] = dict(n=len(nz)); continue
            thr = nz[sig].abs().quantile(2 / 3); top = nz[nz[sig].abs() >= thr]; s = -np.sign(top[sig]).to_numpy()
            out[f"fade_{sig}_top"] = {h: stats(s * top[h] * m, cost) for h in ["y5", "y10"]}
            out[f"follow_{sig}_top_into_close_x"] = stats(-s * top["x"] * m, cost)
            out[f"fade_{sig}_top_rot_y10"] = rot(s, top["y10"].to_numpy(), m)
            out[f"fade_{sig}_top_years_y10"] = {yv: [len(g), round(float((-np.sign(g[sig]) * g["y10"] * m).mean()), 2)] for yv, g in top.groupby("year")}
            out[f"fade_{sig}_all_nz"] = {h: stats(-np.sign(nz[sig]) * nz[h] * m, cost) for h in ["y5", "y10"]}
            nz2 = nz.assign(q=pd.qcut(nz[sig].rank(method="first"), 5, labels=False))
            out[f"dose_{sig}"] = {int(q): dict(mean=round(float(g[sig].mean()), 3), x=round(float(g["x"].mean() * m), 2), y10=round(float(g["y10"].mean() * m), 2), n=len(g)) for q, g in nz2.groupby("q")}
        out["uncond_close_fade_x"] = {h: stats(-np.sign(Dd.loc[Dd["x"] != 0, "x"]) * Dd.loc[Dd["x"] != 0, h] * m, cost) for h in ["y5", "y10"]}
        # volume as size: |y10| by afternoon BTIC volume tercile (relative to trailing 60d median)
        Dd["Va_rel"] = Dd["Va"] / Dd["Va"].rolling(60, min_periods=20).median().shift(1)
        D3 = Dd.dropna(subset=["Va_rel"]).copy(); D3["q"] = pd.qcut(D3["Va_rel"].rank(method="first"), 3, labels=False)
        out["abs_y10_by_Va_rel_tercile"] = {int(q): round(float(g["y10"].abs().mean() * m), 2) for q, g in D3.groupby("q")}
        out["abs_x_by_Va_rel_tercile"] = {int(q): round(float(g["x"].abs().mean() * m), 2) for q, g in D3.groupby("q")}
        # TACO
        if c["taco"]:
            u = tb[tb["kind"] == c["taco"]].copy(); u["hhmm"] = u["et"].dt.strftime("%H:%M"); u["vk"] = u["volume"] * u["close"]
            u["sday"] = (u["et"] + pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d"); u["tcode"] = u["symbol"].str[-2:]
            u = u[u["sday"].map(fm) == u["tcode"]]
            wo, Vo = vwap(u[u["hhmm"] < "09:25"], "00:00", "09:25")
            E = D.join(wo.rename("wo")).join(Vo.rename("Vo"))
            E["dO"] = E["wo"] - E["wa_prev"]; E["xo"] = E["o0930"] - E["o0925"]; E["yo5"] = E["o0935"] - E["o0930"]; E["yo15"] = E["o0945"] - E["o0930"]; E["yo30"] = E["o1000"] - E["o0930"]
            Ed = E.dropna(subset=["dO", "yo15"]); Ed = Ed[Ed["dO"] != 0]
            if len(Ed) >= 100:
                thr = Ed["dO"].abs().quantile(2 / 3); top = Ed[Ed["dO"].abs() >= thr]; s = -np.sign(top["dO"]).to_numpy()
                out["taco"] = dict(n=len(Ed), Vo_median=float(Ed["Vo"].median()), rho={y: round(float(np.corrcoef(Ed["dO"], Ed[y])[0, 1]), 3) for y in ["xo", "yo5", "yo15", "yo30"]},
                                   fade_top={h: stats(s * top[h] * m, cost) for h in ["yo5", "yo15", "yo30"]},
                                   fade_top_years_yo15={yv: [len(g), round(float((-np.sign(g["dO"]) * g["yo15"] * m).mean()), 2)] for yv, g in top.groupby("year")},
                                   fade_top_rot_yo15=rot(s, top["yo15"].to_numpy(), m), sd_usd_yo15=round(float(Ed["yo15"].std() * m), 1))
            else:
                out["taco"] = dict(n=len(Ed))
        res[root] = out
        print(json.dumps(out, indent=1, default=str), flush=True)
        Dd.to_csv(OUT / f"crea_17_{root}_days.csv")
    (OUT / "crea_17_btic_close.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

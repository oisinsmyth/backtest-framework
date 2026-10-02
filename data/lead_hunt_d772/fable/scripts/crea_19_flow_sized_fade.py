"""R1: the post-settlement reversal on NG (MNG) and CL (MCL) SIZED by the leveraged funds' predicted flow |I| (D627-D630's
predictor panel, data/ledger_predicted_flow_daily.csv.gz in the main checkout; rows <= 2023-12-29 only). D630 measured the fade
unconditionally: +$29 full NG from the W_end close to +30 min against the funds' direction (t 3.98, n 1,028). Here the same leg
by |I| quintile/tercile, on traded (signal_day == 1) and all days, in dollars per MNG ($1000/pt) and MCL ($100/pt).
Legs: y30 = P(14:59) - P(14:29) [D630's W_end close], y60 = P(15:29) - P(14:29); side = -dir (dir = sign(q_est) at t0 13:50).
Also: entering at the 14:30 close instead (y30b), the TAS-sign agreement cell (crea_10b W_late), eras, years, rotation.

    python crea_19_flow_sized_fade.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_panels import panel
from crea_10_tas_settlement import stats, rot

OUT = Path(__file__).resolve().parents[1] / "out"
FLOW = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/ledger_predicted_flow_daily.csv.gz")
CFG = {"NG": dict(mult=1000.0, cost=4.00, cost_d630=5.00), "CL": dict(mult=100.0, cost=5.03, cost_d630=5.00)}


def main():
    f = pd.read_csv(FLOW)
    f = f[f["day"] <= "2023-12-29"]
    assert f["day"].max() <= "2023-12-29"
    res = {}
    for root, c in CFG.items():
        fl = f[(f["root"] == root) & (f["tau"] == "13:50")].copy()
        fl["dir"] = np.sign(fl["q_est"]); fl["absI"] = fl["I"].abs(); fl["traded"] = fl["signal_day"] == 1
        P = panel(root); P["hhmm"] = P["et"].dt.strftime("%H:%M")
        def at(h):
            s = P[(P["hhmm"] <= h) & (P["hhmm"] >= "13:00")].groupby("day").tail(1).set_index("day"); return s["close"], s["contract"]
        S = {}
        for lab, h in [("p1400", "13:59"), ("p1429", "14:28"), ("p1430", "14:29"), ("p1459", "14:58"), ("p1529", "15:28"), ("p1445", "14:44")]:
            S[lab], con = at(h)
        S = pd.DataFrame(S); S["contract"] = con; S = S.reset_index().rename(columns={"day": "sday"})
        D = fl.rename(columns={"day": "sday"}).merge(S, on="sday", how="inner").dropna(subset=["p1429", "p1459", "p1529", "dir"])
        D = D[D["dir"] != 0]
        # the panel's front must be the ledger's traded month (yyyy-mm): compare month code
        mon = {c_: i + 1 for i, c_ in enumerate("FGHJKMNQUVXZ")}
        D["front_ym"] = D["contract"].apply(lambda s: f"20{s[-1]}" if False else None)
        D["x"] = D["p1429"] - D["p1400"]; D["y30"] = D["p1459"] - D["p1429"]; D["y60"] = D["p1529"] - D["p1429"]; D["y15"] = D["p1445"] - D["p1429"]
        D["y30b"] = D["p1459"] - D["p1430"]; D["y60b"] = D["p1529"] - D["p1430"]
        D["year"] = D["sday"].str[:4]; D["era"] = np.where(D["year"] <= "2019", "17-19", np.where(D["year"] <= "2021", "20-21", "22-23"))
        m, cost = c["mult"], c["cost"]
        tas = pd.read_csv(OUT / f"crea_10b_{root}_days.csv")[["sday", "Wl"]]
        D = D.merge(tas, on="sday", how="left")
        D.to_csv(OUT / f"crea_19_{root}_days.csv", index=False)
        out = dict(root=root, n_all=len(D), n_traded=int(D["traded"].sum()), sd_usd={k: round(float(D[k].std() * m), 1) for k in ["x", "y30", "y60"]},
                   follow_into_window_traded=stats(D.loc[D["traded"], "dir"] * D.loc[D["traded"], "x"] * m, cost),
                   rho_absI_absy30=round(float(np.corrcoef(D["absI"], D["y30"].abs())[0, 1]), 3),
                   rho_signedI_y30=round(float(np.corrcoef(D["I"], D["y30"])[0, 1]), 3), rho_signedI_x=round(float(np.corrcoef(D["I"], D["x"])[0, 1]), 3))
        for sub, dd in [("traded", D[D["traded"]]), ("all", D)]:
            s = -dd["dir"].to_numpy()
            o = dict(n=len(dd))
            for h in ["y15", "y30", "y60", "y30b", "y60b"]:
                o[f"fade_{h}"] = stats(s * dd[h] * m, cost)
            o["rot_y30"] = rot(s, dd["y30"].to_numpy(), m)
            dd = dd.assign(q=pd.qcut(dd["absI"].rank(method="first"), 5, labels=False), t3=pd.qcut(dd["absI"].rank(method="first"), 3, labels=False))
            o["dose_quintile"] = {int(q): dict(n=len(g), absI_usd_full=round(float(g["absI"].mean() * m * (10 if root == "NG" else 10)), 1), follow_x=round(float((g["dir"] * g["x"] * m).mean()), 2),
                                             fade_y30=round(float((-g["dir"] * g["y30"] * m).mean()), 2), fade_y60=round(float((-g["dir"] * g["y60"] * m).mean()), 2)) for q, g in dd.groupby("q")}
            top = dd[dd["t3"] == 2]; st_ = -top["dir"].to_numpy()
            o["top_tercile"] = {h: stats(st_ * top[h] * m, cost) for h in ["y30", "y60", "y30b", "y60b"]}
            o["top_tercile_rot_y30"] = rot(st_, top["y30"].to_numpy(), m)
            o["top_tercile_years_y30"] = {y: [len(g), round(float((-g["dir"] * g["y30"] * m).mean()), 2), round(float((-g["dir"] * g["y30"] * m).sum()), 0)] for y, g in top.groupby("year")}
            o["top_tercile_eras_y30"] = {e: stats(-g["dir"] * g["y30"] * m, cost) for e, g in top.groupby("era")}
            q4 = dd[dd["q"] == 4]; sq = -q4["dir"].to_numpy()
            o["top_quintile"] = {h: stats(sq * q4[h] * m, cost) for h in ["y30", "y60", "y30b"]}
            o["top_quintile_years_y30"] = {y: [len(g), round(float((-g["dir"] * g["y30"] * m).mean()), 2)] for y, g in q4.groupby("year")}
            o["top_quintile_without_2022_y30"] = stats(-q4.loc[q4["year"] != "2022", "dir"] * q4.loc[q4["year"] != "2022", "y30"] * m, cost)
            # TAS agreement: fade side from flow == fade side from TAS (-sign(Wl))
            tw = top.dropna(subset=["Wl"]); tw = tw[tw["Wl"] != 0]
            ag = tw[np.sign(tw["Wl"]) == tw["dir"]]; dis = tw[np.sign(tw["Wl"]) == -tw["dir"]]
            o["top_tercile_TAS_agree"] = {h: stats(-ag["dir"] * ag[h] * m, cost) for h in ["y30", "y60"]}
            o["top_tercile_TAS_disagree"] = {h: stats(-dis["dir"] * dis[h] * m, cost) for h in ["y30", "y60"]}
            out[sub] = o
        res[root] = out
        print(json.dumps(out, indent=1, default=str), flush=True)
    (OUT / "crea_19_flow_sized_fade.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

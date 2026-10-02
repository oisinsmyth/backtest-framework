"""N2: TAS-offset-signed post-settlement reversal on COMEX gold / silver / copper (MGC, SIL, MHG), 2016-2023.
Settlement windows (data-available.md / D586): GC 13:29-13:30 ET, SI 13:24-13:25, HG 12:59-13:00. TAS instruments GCT/SIT/HGT
(prices = offset in ticks to the settlement). W_late = volume-weighted offset of prints in the 60 minutes ending 2 minutes
before the window end; W_all = all prints of the session to that point. Fade at the window-end close: side = -sign(W);
y5/y30/y60 = price change over the next 5/30/60 minutes. Reference: the unconditional window fade (-sign(P_end - P_end-30m)).

    python crea_16_metals_tas.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_panels import panel
from crea_10_tas_settlement import stats, rot

OUT = Path(__file__).resolve().parents[1] / "out"
CFG = {"GC": dict(kind="GCT", end="13:30", mult=10.0, cost=5.93, tick=0.1), "SI": dict(kind="SIT", end="13:25", mult=1000.0, cost=8.00, tick=0.005),
       "HG": dict(kind="HGT", end="13:00", mult=2500.0, cost=4.25, tick=0.0005)}


def hhmm_add(h, m):
    t = pd.Timestamp("2000-01-01 " + h) + pd.Timedelta(minutes=m); return t.strftime("%H:%M")


def main():
    tb = pd.read_parquet(OUT / "crea_tasbtic_1m.parquet")
    res = {}
    for root, c in CFG.items():
        P = panel(root); P = P[P["day"] >= "2016-01-04"].copy(); P["hhmm"] = P["et"].dt.strftime("%H:%M")
        end = c["end"]
        def at(hhmm):
            s = P[(P["hhmm"] <= hhmm) & (P["hhmm"] >= "11:00")].groupby("day").tail(1).set_index("day")
            return s["close"], s["contract"]
        S = {}
        for lab, off in [("p_m30", -30), ("p_m2", -2), ("p0", 0), ("p5", 5), ("p30", 30), ("p60", 60)]:
            S[lab], con = at(hhmm_add(end, off - 1))   # close of the bar ending at that minute
        S = pd.DataFrame(S); S["contract"] = con; S = S.dropna().reset_index().rename(columns={"day": "sday"})
        chg = S["contract"] != S["contract"].shift(1)
        near = chg | chg.shift(-1, fill_value=False) | chg.shift(-2, fill_value=False) | chg.shift(1, fill_value=False)
        S = S[~near]; S["tcode"] = S["contract"].str[-2:]
        t = tb[tb["kind"] == c["kind"]].copy(); t["tcode"] = t["symbol"].str[-2:]
        t["sday"] = (t["et"] + pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d"); t["hhmm"] = t["et"].dt.strftime("%H:%M")
        t["vk"] = t["volume"] * t["close"]
        cut = hhmm_add(end, -2); start_late = hhmm_add(end, -62)
        late = t[(t["hhmm"] >= start_late) & (t["hhmm"] < cut)].groupby(["sday", "tcode"]).agg(Vl=("volume", "sum"), VKl=("vk", "sum")).reset_index()
        alls = t[t["hhmm"] < cut].groupby(["sday", "tcode"]).agg(Va=("volume", "sum"), VKa=("vk", "sum")).reset_index()
        D = S.merge(late, on=["sday", "tcode"], how="left").merge(alls, on=["sday", "tcode"], how="left").fillna({"Vl": 0, "VKl": 0, "Va": 0, "VKa": 0})
        print(root, "days", len(D), "days with TAS on front", int((D["Va"] > 0).sum()), "median Va", float(D.loc[D["Va"] > 0, "Va"].median()) if (D["Va"] > 0).any() else None, flush=True)
        D = D[D["Va"] >= 20].copy()
        D["Wl"] = np.where(D["Vl"] > 0, D["VKl"] / D["Vl"].replace(0, np.nan), 0.0); D["Wa"] = D["VKa"] / D["Va"]
        D["x30"] = D["p0"] - D["p_m30"]; D["xw"] = D["p0"] - D["p_m2"]
        for h in ["5", "30", "60"]:
            D[f"y{h}"] = D[f"p{h}"] - D["p0"]
        D["year"] = D["sday"].str[:4]
        m, cost = c["mult"], c["cost"]
        out = dict(root=root, n=len(D), Wl_nonzero=int((D["Wl"] != 0).sum()), Wa_nonzero=int((D["Wa"] != 0).sum()),
                   sd_usd={k: round(float(D[k].std() * m), 1) for k in ["xw", "x30", "y5", "y30", "y60"]},
                   rho={f"{s}_{y}": round(float(np.corrcoef(D[s], D[y])[0, 1]), 3) for s in ["Wl", "Wa", "x30"] for y in ["xw", "y5", "y30", "y60"]})
        for sig in ["Wl", "Wa"]:
            nz = D[D[sig] != 0]
            if len(nz) < 100:
                out[f"fade_{sig}"] = dict(n=len(nz)); continue
            thr = nz[sig].abs().quantile(2 / 3); top = nz[nz[sig].abs() >= thr]; s = -np.sign(top[sig]).to_numpy()
            out[f"fade_{sig}_top"] = {h: stats(s * top[h] * m, cost) for h in ["y5", "y30", "y60"]}
            out[f"fade_{sig}_top_rot_y30"] = rot(s, top["y30"].to_numpy(), m)
            out[f"fade_{sig}_top_years_y30"] = {yv: [len(g), round(float((-np.sign(g[sig]) * g["y30"] * m).mean()), 2)] for yv, g in top.groupby("year")}
            out[f"fade_{sig}_all_nz"] = {h: stats(-np.sign(nz[sig]) * nz[h] * m, cost) for h in ["y30", "y60"]}
            out[f"fade_{sig}_pos_side(short)"] = stats(-nz.loc[nz[sig] > 0, "y30"] * m, cost)
            out[f"fade_{sig}_neg_side(long)"] = stats(nz.loc[nz[sig] < 0, "y30"] * m, cost)
            nz2 = nz.assign(q=pd.qcut(nz[sig].rank(method="first"), 5, labels=False))
            out[f"dose_{sig}"] = {int(q): dict(meanW=round(float(g[sig].mean()), 3), xw=round(float(g["xw"].mean() * m), 2), y30=round(float(g["y30"].mean() * m), 2), y60=round(float(g["y60"].mean() * m), 2), n=len(g)) for q, g in nz2.groupby("q")}
        out["uncond_window_fade_x30"] = {h: stats(-np.sign(D["x30"]) * D[h] * m, cost) for h in ["y30", "y60"]}
        out["uncond_window_fade_xw"] = {h: stats(-np.sign(D.loc[D["xw"] != 0, "xw"]) * D.loc[D["xw"] != 0, h] * m, cost) for h in ["y30", "y60"]}
        res[root] = out
        print(json.dumps(out, indent=1, default=str), flush=True)
        D.to_csv(OUT / f"crea_16_{root}_days.csv", index=False)
    (OUT / "crea_16_metals_tas.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

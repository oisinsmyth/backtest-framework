"""C follow-up: the fade enters at 14:30, so the TAS prints up to 14:28 are pre-entry for it. Signal variants: W_late = vol-weighted
offset of TAS prints 14:00:00-14:27:59 (the last half hour, when the dealer still has to hedge in the window); W_all28 = all
prints prior 18:00 .. 14:27:59; V_late = TAS volume 14:00-14:28 relative to its trailing 60-day median. Outcome y = P(14:59)-P(14:30),
y2 = P(15:29) - P(14:30); also the 1-minute-after leg P(14:31)-P(14:30). CL -> MCL ($100/pt, $5.03), NG -> MNG ($1000/pt, $4.00).
Expiring-month days excluded (front changes within 3 sessions). Era split."""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_panels import panel
from crea_10_tas_settlement import stats, rot

OUT = Path(__file__).resolve().parents[1] / "out"
MULT = {"CL": 100.0, "NG": 1000.0}; COST = {"CL": 5.03, "NG": 4.00}; TAS = {"CL": "CLT", "NG": "NGT"}


def main():
    tas = pd.read_parquet(OUT / "crea_tas_1s.parquet")
    res = {}
    for root in ["CL", "NG"]:
        P = panel(root); P = P[P["day"] >= "2017-05-22"].copy(); P["hhmm"] = P["et"].dt.strftime("%H:%M")
        def at(hhmm):
            s = P[(P["hhmm"] <= hhmm) & (P["hhmm"] >= "13:00")].groupby("day").tail(1).set_index("day")
            return s["close"], s["contract"]
        S = {}
        for h in ["14:00", "14:28", "14:30", "14:31", "14:35", "14:59", "15:29"]:
            S[h], con = at(h)
        S = pd.DataFrame(S); S["contract"] = con; S = S.dropna().reset_index().rename(columns={"day": "sday"})
        # exclude days within 3 sessions of a front change
        chg = S["contract"] != S["contract"].shift(1)
        near = chg | chg.shift(-1, fill_value=False) | chg.shift(-2, fill_value=False) | chg.shift(-3, fill_value=False) | chg.shift(1, fill_value=False)
        S = S[~near]
        S["tcode"] = S["contract"].str[2:]
        t = tas[tas["root"] == TAS[root]].copy(); t["tcode"] = t["symbol"].str[3:]
        t["sday"] = (t["et"] + pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d"); t["hhmm"] = t["et"].dt.strftime("%H:%M")
        t["vk"] = t["volume"] * t["close"]
        late = t[(t["hhmm"] >= "14:00") & (t["hhmm"] < "14:28")].groupby(["sday", "tcode"]).agg(Vl=("volume", "sum"), VKl=("vk", "sum")).reset_index()
        all28 = t[t["hhmm"] < "14:28"].groupby(["sday", "tcode"]).agg(Va=("volume", "sum"), VKa=("vk", "sum")).reset_index()
        D = S.merge(late, on=["sday", "tcode"], how="left").merge(all28, on=["sday", "tcode"], how="left").fillna({"Vl": 0, "VKl": 0, "Va": 0, "VKa": 0})
        D = D[D["Va"] >= 50].copy()
        D["Wl"] = np.where(D["Vl"] > 0, D["VKl"] / D["Vl"].replace(0, np.nan), 0.0); D["Wa"] = D["VKa"] / D["Va"]
        D["Vl_rel"] = D["Vl"] / D["Vl"].rolling(60, min_periods=20).median().shift(1)
        D["y"] = D["14:59"] - D["14:30"]; D["y2"] = D["15:29"] - D["14:30"]; D["y1"] = D["14:31"] - D["14:30"]; D["y5"] = D["14:35"] - D["14:30"]
        D["x"] = D["14:30"] - D["14:00"]; D["xw"] = D["14:30"] - D["14:28"]
        D["year"] = D["sday"].str[:4]
        D["era"] = np.where(D["year"] <= "2019", "2017-19", np.where(D["year"] <= "2021", "2020-21", "2022-23"))
        m = MULT[root]; c = COST[root]
        out = dict(root=root, n=len(D), Wl_nonzero=int((D["Wl"] != 0).sum()), Wa_nonzero=int((D["Wa"] != 0).sum()),
                   rho=dict(Wl_xw=round(float(np.corrcoef(D["Wl"], D["xw"])[0, 1]), 3), Wl_x=round(float(np.corrcoef(D["Wl"], D["x"])[0, 1]), 3),
                            Wl_y=round(float(np.corrcoef(D["Wl"], D["y"])[0, 1]), 3), Wl_y2=round(float(np.corrcoef(D["Wl"], D["y2"])[0, 1]), 3), Wl_y5=round(float(np.corrcoef(D["Wl"], D["y5"])[0, 1]), 3),
                            Wa_y=round(float(np.corrcoef(D["Wa"], D["y"])[0, 1]), 3), Wa_y2=round(float(np.corrcoef(D["Wa"], D["y2"])[0, 1]), 3),
                            xw_y=round(float(np.corrcoef(D["xw"], D["y"])[0, 1]), 3), x_y=round(float(np.corrcoef(D["x"], D["y"])[0, 1]), 3)),
                   sd_usd=dict(xw=round(float(D["xw"].std() * m), 1), y=round(float(D["y"].std() * m), 1), y2=round(float(D["y2"].std() * m), 1)))
        for sig in ["Wl", "Wa"]:
            nz = D[D[sig] != 0]
            thr = nz[sig].abs().quantile(2 / 3); top = nz[nz[sig].abs() >= thr]
            s = -np.sign(top[sig]).to_numpy()
            out[f"fade_{sig}_top"] = {h: stats(s * top[h] * m, c) for h in ["y1", "y5", "y", "y2"]}
            out[f"fade_{sig}_top_rot_y"] = rot(s, top["y"].to_numpy(), m)
            out[f"fade_{sig}_top_eras_y"] = {e: stats(-np.sign(g[sig]) * g["y"] * m, c) for e, g in top.groupby("era")}
            out[f"fade_{sig}_top_years_y"] = {yv: [len(g), round(float((-np.sign(g[sig]) * g["y"] * m).mean()), 2)] for yv, g in top.groupby("year")}
            out[f"fade_{sig}_all_nz"] = {h: stats(-np.sign(nz[sig]) * nz[h] * m, c) for h in ["y", "y2"]}
            out[f"fade_{sig}_pos_side(short)"] = stats(-nz.loc[nz[sig] > 0, "y"] * m, c)
            out[f"fade_{sig}_neg_side(long)"] = stats(nz.loc[nz[sig] < 0, "y"] * m, c)
            nz2 = nz.assign(q=pd.qcut(nz[sig].rank(method="first"), 5, labels=False))
            out[f"dose_{sig}"] = {int(q): dict(meanW=round(float(g[sig].mean()), 3), xw=round(float(g["xw"].mean() * m), 2), y=round(float(g["y"].mean() * m), 2), y2=round(float(g["y2"].mean() * m), 2), n=len(g)) for q, g in nz2.groupby("q")}
        # volume-size: |y| by Vl_rel tercile and the unconditional window fade sized by Vl_rel
        D2 = D.dropna(subset=["Vl_rel"]).copy(); D2["vq"] = pd.qcut(D2["Vl_rel"].rank(method="first"), 3, labels=False)
        out["absy_by_Vl_rel_tercile"] = {int(q): round(float(g["y"].abs().mean() * m), 2) for q, g in D2.groupby("vq")}
        out["window_fade_xw_by_Vl_rel_tercile"] = {int(q): stats(-np.sign(g["xw"]) * g["y"] * m, c) for q, g in D2.groupby("vq")}
        res[root] = out
        print(json.dumps(out, indent=1, default=str), flush=True)
        D.to_csv(OUT / f"crea_10b_{root}_days.csv", index=False)
    (OUT / "crea_10b_tas_late.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

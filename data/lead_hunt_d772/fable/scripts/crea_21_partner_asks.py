"""Partner's asks (1) and (2).
(1) L1 on MCL and MNG: top tercile |W_late| (TAS prints 14:00-14:28), BOTH sides, Mon-Thu only (LO/ON weekly expiry Fridays
    excluded), entries at the 14:30 1-min close and at the 14:30:01 1-s trade, holds to 14:59 / 15:29 / 15:59; gross, median,
    t, n/yr, by year (share of net), top-10 share, trimmed, net at cost and cost+1 tick. Also Fridays alone and all days.
(2) SIL TAS agreement cell (TAS sign == 12:55->13:25 window-move sign; y60): by year with 2020 share, top-10 share, trimmed,
    median, net at $8 and $13; loosened to top HALF of |W|.
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_panels import panel

OUT = Path(__file__).resolve().parents[1] / "out"


def full(g, cost, tick):
    g = np.asarray(g, float); g = g[np.isfinite(g)]
    if len(g) < 10:
        return dict(n=len(g))
    q = np.quantile(g, [0.01, 0.99]); srt = np.sort(g)
    return dict(n=len(g), gross=round(float(g.mean()), 2), t=round(float(g.mean() / g.std() * np.sqrt(len(g))), 2), median=round(float(np.median(g)), 2),
                win=round(float((g > 0).mean()), 3), trim=round(float(g[(g >= q[0]) & (g <= q[1])].mean()), 2),
                top10_share=round(float(srt[-10:].sum() / g.sum()), 2) if g.sum() > 0 else None,
                net=round(float(g.mean() - cost), 2), net_plus_tick=round(float(g.mean() - cost - tick), 2))


def years(df, gcol):
    tot = df[gcol].sum()
    return {int(y): [len(g), round(float(g[gcol].mean()), 2), round(float(g[gcol].sum() / tot), 2) if tot > 0 else None] for y, g in df.groupby("year")}


def main():
    res = {}
    # ---------- (1)
    for root, mult, cost, tick in [("CL", 100.0, 5.03, 1.0), ("NG", 1000.0, 4.00, 1.0)]:
        D = pd.read_csv(OUT / f"crea_10b_{root}_days.csv")
        P = panel(root); P["hhmm"] = P["et"].dt.strftime("%H:%M")
        p1559 = P[(P["hhmm"] <= "15:58") & (P["hhmm"] >= "15:00")].groupby("day").tail(1).set_index("day")["close"]
        D["15:59"] = D["sday"].map(p1559)
        S1 = pd.read_csv(OUT / f"crea_18_{root}_days.csv")[["sday", "entry", "y5", "y15", "y29"]].rename(columns={"entry": "e1s", "y5": "s5", "y15": "s15", "y29": "s29"})
        D = D.merge(S1, on="sday", how="left")
        D["s59"] = D["15:59"] - D["e1s"]
        D["m29"] = D["14:59"] - D["14:30"]; D["m59"] = D["15:29"] - D["14:30"]; D["m89"] = D["15:59"] - D["14:30"]
        D["wd"] = pd.to_datetime(D["sday"]).dt.dayofweek; D["year"] = D["sday"].str[:4].astype(int)
        nz = D[D["Wl"] != 0].copy(); thr = nz["Wl"].abs().quantile(2 / 3); top = nz[nz["Wl"].abs() >= thr].copy()
        top["s"] = -np.sign(top["Wl"])
        out = {}
        for lab, sub in [("MonThu", top[top["wd"] <= 3]), ("Fri", top[top["wd"] == 4]), ("AllDays", top)]:
            o = dict(n=len(sub), per_year=round(len(sub) / (sub["year"].nunique() or 1), 1))
            for h, col in [("1min_1459", "m29"), ("1min_1529", "m59"), ("1min_1559", "m89"), ("1s_1459", "s29"), ("1s_1559", "s59"), ("1s_1435", "s5"), ("1s_1445", "s15")]:
                g = (sub["s"] * sub[col] * mult)
                o[h] = full(g, cost, tick)
                if h in ("1min_1559", "1min_1529", "1s_1559"):
                    o[h + "_years"] = years(sub.assign(g=g), "g")
            # long / short
            o["long_side_1min_1559"] = full(sub.loc[sub["s"] > 0, "m89"] * mult, cost, tick); o["short_side_1min_1559"] = full(-sub.loc[sub["s"] < 0, "m89"] * mult, cost, tick)
            out[lab] = o
        # unconditional Mon-Thu window-move fade as the momentum control
        mt = D[(D["wd"] <= 3) & (D["xw"] != 0)]
        out["control_MonThu_window_move_fade_1559"] = full(-np.sign(mt["xw"]) * mt["m89"] * mult, cost, tick)
        out["control_MonThu_x1400_fade_1559"] = full(-np.sign(mt.loc[mt.x != 0, "x"]) * mt.loc[mt.x != 0, "m89"] * mult, cost, tick)
        res[f"L1_{root}"] = out
        print(root, json.dumps(out, indent=1, default=str), flush=True)
    # ---------- (2) SIL
    D = pd.read_csv(OUT / "crea_16_SI_days.csv"); m, cost, tick = 1000.0, 8.0, 5.0
    nz = D[D["Wa"] != 0].copy(); nz["year"] = nz["sday"].str[:4].astype(int)
    out = {}
    for lab, qt in [("top_third", 2 / 3), ("top_half", 0.5), ("all_nz", 0.0)]:
        thr = nz["Wa"].abs().quantile(qt) if qt > 0 else 0
        top = nz[nz["Wa"].abs() >= thr].copy() if qt > 0 else nz.copy()
        ag = top[np.sign(top["Wa"]) == np.sign(top["x30"])].copy(); dis = top[np.sign(top["Wa"]) == -np.sign(top["x30"])].copy()
        ag["g60"] = -np.sign(ag["Wa"]) * ag["y60"] * m; ag["g30"] = -np.sign(ag["Wa"]) * ag["y30"] * m; ag["g60d"] = -np.sign(ag["Wa"]) * (ag["y60"] - ag["y5"]) * m
        o = dict(n_top=len(top), n_agree=len(ag), per_year=round(len(ag) / 8, 1), agree_y60=full(ag["g60"], cost, tick), agree_y30=full(ag["g30"], cost, tick),
                 agree_y60_delayed5=full(ag["g60d"], cost, tick), agree_years_y60=years(ag, "g60"),
                 disagree_y60=full(-np.sign(dis["Wa"]) * dis["y60"] * m, cost, tick),
                 agree_eras_y60={e: full(g["g60"], cost, tick) for e, g in ag.groupby(np.where(ag["year"] <= 2019, "16-19", np.where(ag["year"] <= 2021, "20-21", "22-23")))},
                 agree_wd_y60={int(w): [len(g), round(float(g["g60"].mean()), 2)] for w, g in ag.groupby(pd.to_datetime(ag["sday"]).dt.dayofweek)})
        out[lab] = o
    res["SIL_agreement"] = out
    print("SIL", json.dumps(out, indent=1, default=str), flush=True)
    (OUT / "crea_21_partner_asks.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

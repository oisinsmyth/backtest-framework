"""Premise test C: the TAS (Trade-at-Settlement) offset as a pre-entry signer of the settlement-window move and its reversal,
CL -> MCL and NG -> MNG, 2017-05..2023-12.

TAS prints trade at settlement + k ticks (k = the price field, 0 on 89% of bars). A positive volume-weighted offset means
TAS BUYERS are paying up: the TAS seller is short-at-settlement and must buy outrights into the 14:28:00-14:30:00 ET window.
Predictor (known by 14:00 ET): W = vol-weighted mean offset of TAS prints on the front contract from the prior 18:00 to 14:00;
I = (vol at k>0 - vol at k<0) / vol; V = TAS volume. Outcomes: x = P(14:30) - P(14:00) (into the window); y = P(14:59) -
P(14:30) (the fade leg, D648's T3); y2 = P(15:29) - P(14:30). Books: (a) 'TAS-signed fade' side = -sign(W) on days with |W|
in the top tercile; (b) 'TAS-signed follow into the window' side = +sign(W) over 14:00->14:30; (c) the unconditional fade
side = -sign(x) (D648 T3 at micro size) for reference; (d) the fade conditional on sign(x) == sign(W) (TAS confirmed).
Dollars per MCL ($100/pt) and MNG ($1000/pt). Rotation null: W of day s against y of day s+k.

    python crea_10_tas_settlement.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_panels import panel

OUT = Path(__file__).resolve().parents[1] / "out"
MULT = {"CL": 100.0, "NG": 1000.0}; COST = {"CL": 5.03, "NG": 4.00}; TAS = {"CL": "CLT", "NG": "NGT"}


def stats(g, cost):
    g = np.asarray(g, float); g = g[np.isfinite(g)]
    if len(g) < 20:
        return dict(n=len(g))
    q = np.quantile(g, [0.01, 0.99])
    return dict(n=len(g), gross=round(float(g.mean()), 2), t=round(float(g.mean() / g.std() * np.sqrt(len(g))), 1), median=round(float(np.median(g)), 2),
                net=round(float(g.mean() - cost), 2), win=round(float((g > 0).mean()), 3), trim=round(float(g[(g >= q[0]) & (g <= q[1])].mean()), 2),
                top=round(float(g.max()), 1), top_share=round(float(g.max() / g.sum()), 2) if g.sum() > 0 else None)


def rot(sign, y, mult, k_max=300):
    r = [np.nanmean(sign * np.roll(y, k) * mult) for k in range(1, min(k_max, len(y) - 1))]
    return dict(p50=round(float(np.median(r)), 2), p95=round(float(np.quantile(r, 0.95)), 2))


def main():
    tas = pd.read_parquet(OUT / "crea_tas_1s.parquet")
    res = {}
    for root in ["CL", "NG"]:
        P = panel(root)
        P = P[P["day"] >= "2017-05-22"]
        # session prices at the clocks (last bar at or before)
        P["hhmm"] = P["et"].dt.strftime("%H:%M")
        def at(hhmm):
            s = P[(P["hhmm"] <= hhmm) & (P["hhmm"] >= "13:00")].groupby("day").tail(1).set_index("day")
            return s["close"], s["contract"]
        p1400, con = at("14:00"); p1428, _ = at("14:28"); p1430, _ = at("14:30"); p1459, _ = at("14:59"); p1529, _ = at("15:29")
        S = pd.DataFrame({"p1400": p1400, "p1428": p1428, "p1430": p1430, "p1459": p1459, "p1529": p1529, "contract": con}).dropna()
        # TAS prints for the day: prior 18:00 .. 14:00 ET, on the front contract (CLT + month code of the front)
        t = tas[tas["root"] == TAS[root]].copy()
        t["tcode"] = t["symbol"].str[3:]
        t["sday"] = (t["et"] + pd.Timedelta(hours=6)).dt.strftime("%Y-%m-%d")   # 18:00 -> next day
        t = t[t["et"].dt.strftime("%H:%M") < "14:00"]
        # hmm: the +6h shift maps 18:00..23:59 to the next day and 00:00..13:59 to the same day. good.
        t["k"] = t["close"]; t["vk"] = t["volume"] * t["k"]
        t["vpos"] = np.where(t["k"] > 0, t["volume"], 0); t["vneg"] = np.where(t["k"] < 0, t["volume"], 0)
        agg = t.groupby(["sday", "tcode"]).agg(V=("volume", "sum"), VK=("vk", "sum"), vpos=("vpos", "sum"), vneg=("vneg", "sum"), nbars=("volume", "size")).reset_index()
        S = S.reset_index().rename(columns={"day": "sday"})
        S["tcode"] = S["contract"].str[2:]
        D = S.merge(agg, on=["sday", "tcode"], how="left")
        D["V"] = D["V"].fillna(0)
        print(root, "days", len(D), "with TAS on front", int((D["V"] > 0).sum()), "median V", float(D.loc[D["V"] > 0, "V"].median()))
        D = D[D["V"] >= 50].copy()
        D["W"] = D["VK"] / D["V"]; D["I"] = (D["vpos"] - D["vneg"]) / D["V"]
        D["x"] = D["p1430"] - D["p1400"]; D["x28"] = D["p1428"] - D["p1400"]; D["y"] = D["p1459"] - D["p1430"]; D["y2"] = D["p1529"] - D["p1430"]
        D["year"] = D["sday"].str[:4]
        m = MULT[root]; c = COST[root]
        out = dict(root=root, n=len(D), W_nonzero=int((D["W"] != 0).sum()), W_abs_median=round(float(D["W"].abs().median()), 3),
                   I_abs_median=round(float(D["I"].abs().median()), 3),
                   rho_W_x=round(float(np.corrcoef(D["W"], D["x"])[0, 1]), 3), rho_W_y=round(float(np.corrcoef(D["W"], D["y"])[0, 1]), 3),
                   rho_W_y2=round(float(np.corrcoef(D["W"], D["y2"])[0, 1]), 3), rho_I_x=round(float(np.corrcoef(D["I"], D["x"])[0, 1]), 3),
                   rho_I_y=round(float(np.corrcoef(D["I"], D["y"])[0, 1]), 3), rho_x_y=round(float(np.corrcoef(D["x"], D["y"])[0, 1]), 3),
                   rho_V_absx=round(float(np.corrcoef(np.log(D["V"]), D["x"].abs())[0, 1]), 3), rho_V_absy=round(float(np.corrcoef(np.log(D["V"]), D["y"].abs())[0, 1]), 3),
                   sd_x_usd=round(float(D["x"].std() * m), 1), sd_y_usd=round(float(D["y"].std() * m), 1))
        nz = D[D["W"] != 0]
        thr = nz["W"].abs().quantile(2 / 3)
        top = nz[nz["W"].abs() >= thr]
        sw = np.sign(top["W"]).to_numpy()
        out["book_a_tas_fade_topW"] = stats(-sw * top["y"] * m, c)
        out["book_a_rot"] = rot(-sw, top["y"].to_numpy(), m)
        out["book_a_years"] = {y: stats(-np.sign(g["W"]) * g["y"] * m, c) for y, g in top.groupby("year")}
        out["book_a_tas_fade_topW_y2"] = stats(-sw * top["y2"] * m, c)
        out["book_b_tas_follow_into_window_topW"] = stats(sw * top["x"] * m, c)
        out["book_b_follow_14_1428"] = stats(sw * top["x28"] * m, c)
        out["book_b_rot"] = rot(sw, top["x"].to_numpy(), m)
        out["book_b_years"] = {y: stats(np.sign(g["W"]) * g["x"] * m, c) for y, g in top.groupby("year")}
        out["book_a_allW_nonzero"] = stats(-np.sign(nz["W"]) * nz["y"] * m, c)
        out["book_b_allW_nonzero"] = stats(np.sign(nz["W"]) * nz["x"] * m, c)
        sx = np.sign(D["x"]).to_numpy()
        out["book_c_uncond_fade"] = stats(-sx * D["y"] * m, c)
        out["book_c_uncond_fade_topabsx"] = stats(-np.sign(D.loc[D["x"].abs() >= D["x"].abs().quantile(2 / 3), "x"]) * D.loc[D["x"].abs() >= D["x"].abs().quantile(2 / 3), "y"] * m, c)
        conf = nz[np.sign(nz["x"]) == np.sign(nz["W"])]
        out["book_d_confirmed_fade"] = stats(-np.sign(conf["x"]) * conf["y"] * m, c)
        unc = nz[(np.sign(nz["x"]) != np.sign(nz["W"])) & (nz["x"] != 0)]
        out["book_d_unconfirmed_fade"] = stats(-np.sign(unc["x"]) * unc["y"] * m, c)
        # dose: fade gross by W tercile (signed)
        D["Wq"] = pd.qcut(D["W"].rank(method="first"), 5, labels=False)
        out["dose_fade_by_W_quintile"] = {int(q): dict(meanW=round(float(g["W"].mean()), 3), x_usd=round(float(g["x"].mean() * m), 2), y_usd=round(float(g["y"].mean() * m), 2), n=len(g)) for q, g in D.groupby("Wq")}
        # TAS volume as size predictor: |y| by V tercile
        D["Vq"] = pd.qcut(D["V"].rank(method="first"), 3, labels=False)
        out["absy_by_V_tercile"] = {int(q): round(float(g["y"].abs().mean() * m), 2) for q, g in D.groupby("Vq")}
        out["top_trade_book_a"] = None
        if len(top):
            ga = (-sw * top["y"] * m); i = int(np.argmax(ga.to_numpy()))
            out["top_trade_book_a"] = dict(day=str(top["sday"].iloc[i]), gross=round(float(ga.iloc[i]), 1), W=round(float(top["W"].iloc[i]), 2), V=int(top["V"].iloc[i]))
        res[root] = out
        print(json.dumps(out, indent=1, default=str), flush=True)
        D.to_csv(OUT / f"crea_10_{root}_days.csv", index=False)
    (OUT / "crea_10_tas_settlement.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

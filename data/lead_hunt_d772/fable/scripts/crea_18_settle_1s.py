"""N3: the settlement-window microstructure on CL/NG at ONE SECOND, 2017-05..2023. The settlement is the VWAP of outright trades
14:28:00-14:29:59 ET. dev = last trade (<= 14:29:59) - VWAP_window (ticks): the last-seconds overshoot of the benchmark. Fade at the
first trade >= 14:30:01 with side = -sign(dev); exits +1/+5/+15/+29 min. Also: the TAS-signed fade (crea_10b W_late) entered at
14:30:01 (executable) and the agreement cell (TAS sign == overshoot sign). Dollars per MCL ($100/pt) / MNG ($1000/pt).

    python crea_18_settle_1s.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_10_tas_settlement import stats, rot

OUT = Path(__file__).resolve().parents[1] / "out"
CFG = {"CL": dict(mult=100.0, cost=5.03, tick=0.01), "NG": dict(mult=1000.0, cost=4.00, tick=0.001)}


def main():
    res = {}
    for root, c in CFG.items():
        d = pd.read_parquet(OUT / f"crea_1s_settle_{root}.parquet")
        d["sday"] = d["et"].dt.strftime("%Y-%m-%d"); d["sec"] = d["et"].dt.hour * 3600 + d["et"].dt.minute * 60 + d["et"].dt.second
        # front = the contract with the most volume in 14:20-14:30 that day
        vol = d[(d["sec"] >= 14 * 3600 + 20 * 60) & (d["sec"] < 14 * 3600 + 30 * 60)].groupby(["sday", "contract"])["volume"].sum().reset_index()
        front = vol.sort_values(["sday", "volume"]).groupby("sday").tail(1).set_index("sday")["contract"]
        d = d[d["contract"] == d["sday"].map(front)].sort_values(["sday", "ts"])
        rows = []
        for sday, g in d.groupby("sday", sort=True):
            sec = g["sec"].to_numpy(); px = g["close"].to_numpy(); v = g["volume"].to_numpy()
            w = (sec >= 14 * 3600 + 28 * 60) & (sec < 14 * 3600 + 30 * 60)
            if w.sum() < 10:
                continue
            vwap = float(np.sum(px[w] * v[w]) / np.sum(v[w])); nwin = int(w.sum()); vwin = int(v[w].sum())
            def last_before(s):
                i = np.searchsorted(sec, s, side="right") - 1
                return px[i] if i >= 0 else np.nan
            def first_at(s, smax):
                i = np.searchsorted(sec, s, side="left")
                return (px[i], sec[i]) if i < len(sec) and sec[i] <= smax else (np.nan, None)
            last = last_before(14 * 3600 + 29 * 60 + 59); p1400 = last_before(14 * 3600 + 0); p1428 = last_before(14 * 3600 + 27 * 60 + 59)
            e, esec = first_at(14 * 3600 + 30 * 60 + 1, 14 * 3600 + 30 * 60 + 30)
            if not np.isfinite(e):
                continue
            rec = dict(sday=sday, contract=g["contract"].iloc[0], vwap=vwap, last=last, dev=last - vwap, entry=e, entry_sec=esec - 14 * 3600 - 30 * 60, nwin=nwin, vwin=vwin,
                       x_into=last - p1400, xw=vwap - p1428, gap_entry_last=e - last, last30=last - last_before(14 * 3600 + 29 * 60 + 29))
            for H in (1, 5, 15, 29):
                rec[f"y{H}"] = last_before(14 * 3600 + 30 * 60 + 60 * H + 59) - e
            rows.append(rec)
        D = pd.DataFrame(rows); D["year"] = D["sday"].str[:4]
        m, cost, tick = c["mult"], c["cost"], c["tick"]
        D["dev_t"] = D["dev"] / tick
        tas = pd.read_csv(OUT / f"crea_10b_{root}_days.csv")[["sday", "Wl", "Wa"]]
        D = D.merge(tas, on="sday", how="left")
        out = dict(root=root, n=len(D), entry_sec_median=float(D["entry_sec"].median()), dev_ticks=dict(p50_abs=float(D["dev_t"].abs().median()), p90_abs=float(D["dev_t"].abs().quantile(.9)), share_ge2=round(float((D["dev_t"].abs() >= 2).mean()), 3)),
                   gap_entry_last_ticks_median=float((D["gap_entry_last"] / tick).median()),
                   sd_usd={k: round(float(D[k].std() * m), 1) for k in ["dev", "y1", "y5", "y15", "y29"]},
                   rho={f"{s}_{y}": round(float(np.corrcoef(D[s].fillna(0), D[y])[0, 1]), 3) for s in ["dev", "last30", "x_into", "xw"] for y in ["y1", "y5", "y15", "y29"]})
        nz = D[D["dev"] != 0]; s = -np.sign(nz["dev"]).to_numpy()
        out["fade_dev_all"] = {h: stats(s * nz[h] * m, cost) for h in ["y1", "y5", "y15", "y29"]}
        big = nz[nz["dev_t"].abs() >= 2]; sb = -np.sign(big["dev"]).to_numpy()
        out["fade_dev_ge2ticks"] = {h: stats(sb * big[h] * m, cost) for h in ["y1", "y5", "y15", "y29"]}
        out["fade_dev_ge2_rot_y5"] = rot(sb, big["y5"].to_numpy(), m)
        out["fade_dev_ge2_years_y5"] = {yv: [len(g), round(float((-np.sign(g["dev"]) * g["y5"] * m).mean()), 2)] for yv, g in big.groupby("year")}
        nz2 = nz.assign(q=pd.qcut(nz["dev_t"].rank(method="first"), 5, labels=False))
        out["dose_dev"] = {int(q): dict(dev_t=round(float(g["dev_t"].mean()), 2), y1=round(float(g["y1"].mean() * m), 2), y5=round(float(g["y5"].mean() * m), 2), y29=round(float(g["y29"].mean() * m), 2), n=len(g)) for q, g in nz2.groupby("q")}
        # D648's T3 at 1-s executable entry: side = -sign(x_into)
        xi = D[D["x_into"] != 0]; out["fade_x_into_14:00->14:29:59"] = {h: stats(-np.sign(xi["x_into"]) * xi[h] * m, cost) for h in ["y5", "y29"]}
        # TAS-signed at the 1-s entry
        tw = D.dropna(subset=["Wl"]); tw = tw[tw["Wl"] != 0]
        if len(tw) >= 100:
            thr = tw["Wl"].abs().quantile(2 / 3); top = tw[tw["Wl"].abs() >= thr]; st_ = -np.sign(top["Wl"]).to_numpy()
            out["tas_Wl_top_fade_at_1s_entry"] = {h: stats(st_ * top[h] * m, cost) for h in ["y5", "y15", "y29"]}
            agree = top[np.sign(top["Wl"]) == np.sign(top["dev"])]; sa = -np.sign(agree["Wl"]).to_numpy()
            out["tas_top_AND_overshoot_agree"] = {h: stats(sa * agree[h] * m, cost) for h in ["y5", "y15", "y29"]}
            dis = top[np.sign(top["Wl"]) == -np.sign(top["dev"])]; sd_ = -np.sign(dis["Wl"]).to_numpy()
            out["tas_top_AND_overshoot_disagree"] = {h: stats(sd_ * dis[h] * m, cost) for h in ["y5", "y29"]}
        res[root] = out
        print(json.dumps(out, indent=1, default=str), flush=True)
        D.to_csv(OUT / f"crea_18_{root}_days.csv", index=False)
    (OUT / "crea_18_settle_1s.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

"""Premise test F: retail crowding read from the MICRO/PARENT volume ratio. When a 5-minute move in ES (NQ) is accompanied by
an abnormally high MES/ES (MNQ/NQ) contract-volume ratio, the move is retail-chased and should revert more than a move of the
same size carried by full-size contracts. 2019-05-06..2023-12-29 (micros listed 2019-05). Panels: crea_panels (ES, NQ) and
crea_02's MES/MNQ decode. Predictor uses only bars <= t. Outcome: parent return over the next 15/30 min, fade side, dollars
per one micro (MES $5/pt, MNQ $2/pt). Cells: |ret5| top quintile x ratio-z quintile (top vs bottom), RTH and off-hours.

    python crea_08_micro_share.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_panels import panel

OUT = Path(__file__).resolve().parents[1] / "out"
MULT = {"ES": 5.0, "NQ": 2.0}; COST = {"ES": 4.42, "NQ": 4.07}; MICRO = {"ES": "MES", "NQ": "MNQ"}


def stats(g, cost):
    g = np.asarray(g, float); g = g[np.isfinite(g)]
    if len(g) < 30:
        return dict(n=len(g))
    return dict(n=len(g), gross=round(float(g.mean()), 2), t=round(float(g.mean() / g.std() * np.sqrt(len(g))), 1), median=round(float(np.median(g)), 2),
                net=round(float(g.mean() - cost), 2), win=round(float((g > 0).mean()), 3))


def main():
    res = {}
    for root in ["ES", "NQ"]:
        P = panel(root)[["et", "day", "close", "volume"]].rename(columns={"close": "pc", "volume": "pv"})
        M = pd.read_parquet(OUT / f"crea_globex1m_{MICRO[root]}.parquet")[["et", "close", "volume"]].rename(columns={"close": "mc", "volume": "mv"})
        M["et"] = pd.to_datetime(M["et"])
        d = P.merge(M, on="et", how="inner")
        d = d[d["et"] >= "2019-05-06"].sort_values("et").reset_index(drop=True)
        assert d["et"].max() < pd.Timestamp("2024-01-01")
        d["b5"] = (d["et"].dt.hour * 60 + d["et"].dt.minute) // 5          # 5-minute bucket of day
        g5 = d.groupby(["day", "b5"]).agg(et=("et", "last"), pc=("pc", "last"), pv=("pv", "sum"), mv=("mv", "sum"), n=("et", "size")).reset_index()
        g5 = g5.sort_values("et").reset_index(drop=True)
        g5["ret5"] = np.log(g5["pc"]).diff()
        # same-session continuity: previous bucket within 10 minutes
        g5["gap"] = g5["et"].diff().dt.total_seconds() / 60
        g5.loc[g5["gap"] > 10, "ret5"] = np.nan
        g5["lr"] = np.log((g5["mv"] + 1) / (g5["pv"] + 1))
        # ratio z vs trailing 20 sessions at the same bucket (pre-entry): rolling by bucket over sessions
        g5 = g5.sort_values(["b5", "et"])
        grp = g5.groupby("b5")["lr"]
        mu = grp.transform(lambda s: s.shift(1).rolling(20, min_periods=10).mean())
        sd = grp.transform(lambda s: s.shift(1).rolling(20, min_periods=10).std())
        g5["z"] = (g5["lr"] - mu) / sd
        g5 = g5.sort_values("et").reset_index(drop=True)
        # forward parent returns in $ per micro: 15 and 30 min = 3 and 6 buckets ahead
        for H, k in [(15, 3), (30, 6)]:
            fwd = g5["pc"].shift(-k) - g5["pc"]
            gap = (g5["et"].shift(-k) - g5["et"]).dt.total_seconds() / 60
            fwd[gap > H + 10] = np.nan
            g5[f"y{H}"] = fwd * MULT[root]
        g5["side"] = -np.sign(g5["ret5"])
        g5["rth"] = (g5["et"].dt.strftime("%H:%M") >= "09:35") & (g5["et"].dt.strftime("%H:%M") <= "15:30")
        g5["year"] = g5["et"].dt.year
        ok = g5.dropna(subset=["ret5", "z", "y15", "y30"]).copy()
        # |ret5| top quintile within (year, rth) to avoid vol-regime mixing
        ok["absr"] = ok["ret5"].abs()
        ok["r_q"] = ok.groupby(["year", "rth"])["absr"].transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
        ok["z_q"] = ok.groupby(["year", "rth"])["z"].transform(lambda s: pd.qcut(s.rank(method="first"), 5, labels=False))
        big = ok[ok["r_q"] == 4]
        out = dict(root=root, n5=len(ok), n_big=len(big))
        for H in [15, 30]:
            big[f"g{H}"] = big["side"] * big[f"y{H}"]
            out[f"rho_z_g{H}_big"] = round(float(np.corrcoef(big["z"], big[f"g{H}"])[0, 1]), 4)
            for sess in ["RTH", "OFF"]:
                b = big[big["rth"] == (sess == "RTH")]
                cells = {}
                cells["all_big"] = stats(b[f"g{H}"], COST[root])
                cells["z_top"] = stats(b.loc[b["z_q"] == 4, f"g{H}"], COST[root])
                cells["z_bottom"] = stats(b.loc[b["z_q"] == 0, f"g{H}"], COST[root])
                cells["z_top_by_year"] = {int(y): stats(x[f"g{H}"], COST[root]) for y, x in b[b["z_q"] == 4].groupby("year")}
                # rotation: shift z_q by k sessions (reassign z from another session's same bucket)
                zt = b[b["z_q"] == 4]
                out[f"{sess}_H{H}"] = cells
            # dose: mean fade by z quintile, both sessions pooled
            out[f"dose_H{H}"] = {int(q): stats(big.loc[big["z_q"] == q, f"g{H}"], COST[root]) for q in range(5)}
        # retail share level descriptives
        out["lr_by_year"] = ok.groupby("year")["lr"].mean().round(3).to_dict()
        res[root] = out
        print(json.dumps(out, indent=1, default=str), flush=True)
    (OUT / "crea_08_micro_share.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

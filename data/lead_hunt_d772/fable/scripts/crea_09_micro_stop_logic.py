"""Premise test A': the MICRO's own Stop Logic / Velocity Logic events (MNQ, MES), 2019-05..2023. When the micro's book is
swept and paused while the parent is not, the micro closes the event minute displaced from the parent; the arbitrage pulls
it back. Predictor: the micro-parent basis at the close of the event minute (b0 = micro close - parent close) and the
micro's own 3-minute move. Outcome: micro price change over the next 1/5/15 minutes (dollars per micro) traded against
the basis sign, and the basis change itself. Also the parent-event minutes for comparison.

    python crea_09_micro_stop_logic.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_panels import panel

OUT = Path(__file__).resolve().parents[1] / "out"
MULT = {"MES": 5.0, "MNQ": 2.0}; COST = {"MES": 4.42, "MNQ": 4.07}; PARENT = {"MES": "ES", "MNQ": "NQ"}
TICK = {"MES": 0.25, "MNQ": 0.25}


def stats(g, cost):
    g = np.asarray(g, float); g = g[np.isfinite(g)]
    if len(g) < 10:
        return dict(n=len(g))
    q = np.quantile(g, [0.01, 0.99])
    return dict(n=len(g), gross=round(float(g.mean()), 2), t=round(float(g.mean() / g.std() * np.sqrt(len(g))), 1), median=round(float(np.median(g)), 2),
                net=round(float(g.mean() - cost), 2), win=round(float((g > 0).mean()), 3), trim=round(float(g[(g >= q[0]) & (g <= q[1])].mean()), 2), top=round(float(g.max()), 1))


def main():
    ev = pd.read_csv(OUT / "crea_04_status_events.csv", parse_dates=["start_et", "resume_et"])
    ev = ev[(ev["start_et"] < "2024-01-01") & (ev["secs"] >= 1) & (ev["secs"] <= 120)]
    res = {}
    for mic in ["MNQ", "MES"]:
        M = pd.read_parquet(OUT / f"crea_globex1m_{mic}.parquet"); M["et"] = pd.to_datetime(M["et"])
        P = panel(PARENT[mic])[["et", "close", "contract"]].rename(columns={"close": "pc", "contract": "pcon"})
        d = M.merge(P, on="et", how="inner").sort_values("et").reset_index(drop=True)
        d["basis"] = d["close"] - d["pc"]
        pos = {t: i for i, t in enumerate(d["et"])}
        close = d["close"].to_numpy(); pc = d["pc"].to_numpy(); con = d["contract"].to_numpy(); et = d["et"]
        e = ev[ev["root"] == mic].copy(); e["m0"] = e["start_et"].dt.floor("min"); e = e.drop_duplicates("m0")
        pe = ev[ev["root"] == PARENT[mic]].copy(); pe["m0"] = pe["start_et"].dt.floor("min"); pset = set(pe["m0"])
        rows = []
        for r in e.itertuples():
            i = pos.get(r.m0)
            if i is None or i < 5 or i + 20 >= len(close) or con[i] != r.contract:
                continue
            if (et.iloc[i + 16] - et.iloc[i]) > pd.Timedelta(minutes=25):
                continue
            b0 = close[i] - pc[i]
            pre3 = close[i] - close[i - 3]
            rec = dict(mic=mic, m0=r.m0, day=d["day"].iloc[i], hhmm=r.m0.strftime("%H:%M"), secs=r.secs, b0=b0, b0_ticks=b0 / TICK[mic], pre3=pre3,
                       bprev=float(np.mean(close[i - 3:i] - pc[i - 3:i])), joint=(r.m0 in pset))
            sb = -np.sign(b0) if b0 != 0 else 0.0
            sp = -np.sign(pre3) if pre3 != 0 else 0.0
            for H in (1, 5, 15):
                rec[f"db{H}"] = (close[i + H] - pc[i + H]) - b0                       # basis change
                rec[f"gb{H}"] = sb * (close[i + H] - close[i]) * MULT[mic]            # trade the micro against its basis
                rec[f"gp{H}"] = sp * (close[i + H] - close[i]) * MULT[mic]            # fade the micro's own 3-min move
                rec[f"gpar{H}"] = sb * (pc[i + H] - pc[i]) * MULT[mic]               # what the PARENT did (is it the micro or the parent that moves?)
            rows.append(rec)
        T = pd.DataFrame(rows)
        if len(T) == 0:
            print(mic, "no events"); continue
        T["year"] = T["m0"].dt.year; T["rth"] = (T["hhmm"] >= "09:30") & (T["hhmm"] < "16:00")
        out = dict(mic=mic, n=len(T), per_year=round(len(T) / 4.65, 1), joint_share=round(float(T["joint"].mean()), 3), median_secs=float(T["secs"].median()),
                   b0_ticks_abs_mean=round(float(T["b0_ticks"].abs().mean()), 2), b0_abs_ge2ticks=int((T["b0_ticks"].abs() >= 2).sum()),
                   rth_share=round(float(T["rth"].mean()), 3), years=T.groupby("year").size().to_dict(), hours=T.groupby(T["hhmm"].str[:2]).size().to_dict())
        Tb = T[T["b0"] != 0]
        for H in (1, 5, 15):
            out[f"H{H}"] = dict(basis_change_vs_b0_rho=round(float(np.corrcoef(Tb["b0"], Tb[f"db{H}"])[0, 1]), 3),
                                basis_closed_share=round(float((np.sign(Tb[f"db{H}"]) == -np.sign(Tb["b0"])).mean()), 3),
                                trade_vs_basis=stats(Tb[f"gb{H}"], COST[mic]), parent_move_same_side=stats(Tb[f"gpar{H}"], COST[mic]),
                                trade_vs_basis_ge2=stats(Tb.loc[Tb["b0_ticks"].abs() >= 2, f"gb{H}"], COST[mic]),
                                fade_own_move=stats(T.loc[T["pre3"] != 0, f"gp{H}"], COST[mic]),
                                micro_only_vs_basis=stats(Tb.loc[~Tb["joint"], f"gb{H}"], COST[mic]))
        # generic basis-reversion control: random minutes with |basis| >= 2 ticks and no event
        d["absb"] = d["basis"].abs()
        ctl = d[(d["absb"] >= 2 * TICK[mic])].index.to_numpy()
        ctl = ctl[(ctl > 5) & (ctl < len(d) - 20)]
        rng = np.random.default_rng(0); ctl = rng.choice(ctl, size=min(5000, len(ctl)), replace=False)
        sb = -np.sign(d["basis"].to_numpy()[ctl])
        out["control_nonevent_basis_ge2"] = {f"H{H}": stats(sb * (close[ctl + H] - close[ctl]) * MULT[mic], COST[mic]) for H in (1, 5, 15)}
        out["control_count_minutes_ge2"] = int((d["absb"] >= 2 * TICK[mic]).sum())
        res[mic] = out
        print(json.dumps(out, indent=1, default=str), flush=True)
        T.to_csv(OUT / f"crea_09_{mic}_events.csv", index=False)
    (OUT / "crea_09_micro_stop_logic.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()

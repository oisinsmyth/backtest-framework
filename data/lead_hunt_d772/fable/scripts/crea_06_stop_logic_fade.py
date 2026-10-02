"""Premise test A, step 2: does the price revert after a CME Stop Logic / Velocity Logic reserved-state event?

Events: crea_04_status_events.csv (action PreOpen/Halt + reason MarketEvent/Surveillance), restricted to the root's
FRONT contract that minute (the bar panel's contract), duration 1..120 s, one event per (root, minute).
Event minute m0 = the minute containing the event start. Cascade direction = sign(close[m0] - close[m0-3]) (the 3-minute
move into and through the pause, all known at the close of m0). Entry: close of m0 (the pause has resumed by then on
>97% of events; a 1-minute-delayed entry is reported). Exit: close of m0+H, H in 5/15/30. Dollars per one micro.
Controls: (i) rotation null (same minute-of-day, session s+k); (ii) matched placebo: the same 3-minute move size at the
same clock on the nearest prior session WITHOUT an event; (iii) RTH vs off-hours; (iv) release minutes (08:30, 10:00,
10:30, 14:00 ET) split out.

    python crea_06_stop_logic_fade.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from crea_panels import panel

OUT = Path(__file__).resolve().parents[1] / "out"
MULT = {"ES": 5.0, "NQ": 2.0, "YM": 0.5, "RTY": 5.0, "CL": 100.0, "NG": 1000.0, "GC": 10.0, "SI": 1000.0, "HG": 2500.0}
COST = {"ES": 4.42, "NQ": 4.07, "YM": 3.80, "RTY": 3.76, "CL": 5.03, "NG": 4.00, "GC": 5.93, "SI": 8.00, "HG": 4.25}
HS = [5, 15, 30]
NEWS = {"08:30", "08:31", "10:00", "10:01", "10:30", "10:31", "14:00", "14:01", "09:30", "09:31", "13:30", "13:31", "14:30", "14:31"}


def stats(g, label, cost):
    g = np.asarray(g, dtype=float); g = g[np.isfinite(g)]
    if len(g) < 10:
        return dict(label=label, n=len(g))
    q = np.quantile(g, [0.01, 0.99])
    return dict(label=label, n=len(g), gross=float(g.mean()), t=float(g.mean() / g.std() * np.sqrt(len(g))), median=float(np.median(g)),
                net=float(g.mean() - cost), win=float((g > 0).mean()), trim_both=float(g[(g >= q[0]) & (g <= q[1])].mean()),
                ex_top=float(g[g <= q[1]].mean()), ex_bottom=float(g[g >= q[0]].mean()), top=float(g.max()), top_share=float(g.max() / g.sum()) if g.sum() > 0 else None)


def run_root(root, ev):
    d = panel(root)
    d = d.set_index("et")
    idx = d.index
    pos = {t: i for i, t in enumerate(idx)}
    close = d["close"].to_numpy(); contract = d["contract"].to_numpy(); vol = d["volume"].to_numpy()
    e = ev[(ev["root"] == root) & (ev["secs"] >= 1) & (ev["secs"] <= 120)].copy()
    e["m0"] = e["start_et"].dt.floor("min")
    e = e.drop_duplicates(["m0"]).sort_values("m0")
    rows = []
    for r in e.itertuples():
        if r.m0 not in pos:
            continue
        i = pos[r.m0]
        if contract[i] != r.contract:
            continue  # not the front
        if i < 5 or i + max(HS) + 2 >= len(close):
            continue
        # same session continuity: bars within the horizon must be within 40 minutes wall-clock (skip the 17:00 break)
        if (idx[i + max(HS) + 1] - idx[i]) > pd.Timedelta(minutes=max(HS) + 10):
            continue
        pre3 = close[i] - close[i - 3]
        pre1 = close[i] - close[i - 1]
        side = -np.sign(pre3) if pre3 != 0 else 0.0
        rec = dict(root=root, m0=r.m0, day=d["day"].iloc[i], hhmm=r.m0.strftime("%H:%M"), secs=r.secs, pre3=pre3, pre1=pre1, side=side,
                   vol0=vol[i], vol_prev=vol[i - 4:i - 1].mean(), reason=r.start_reason)
        for H in HS:
            rec[f"y{H}"] = close[i + H] - close[i]
            rec[f"g{H}"] = side * (close[i + H] - close[i]) * MULT[root]
            rec[f"gd{H}"] = side * (close[i + 1 + H] - close[i + 1]) * MULT[root]
        rows.append(rec)
    T = pd.DataFrame(rows)
    if len(T) == 0:
        return None, None
    T["year"] = T["m0"].dt.year
    T["rth"] = (T["hhmm"] >= "09:30") & (T["hhmm"] < "16:00")
    T["news"] = T["hhmm"].isin(NEWS)
    # placebo: same clock, same |pre3| rank, nearest prior session without an event: use the bar at the same hhmm on the
    # previous trading day and the same side rule
    pl = []
    dayset = set(T["day"])
    days = np.array(sorted(set(d["day"])))
    dpos = {x: i for i, x in enumerate(days)}
    for r in T.itertuples():
        k = dpos.get(r.day)
        if k is None or k < 2:
            pl.append([np.nan] * len(HS)); continue
        found = None
        for back in (1, 2, 3):
            pd_ = days[k - back]
            if pd_ in dayset:
                continue
            t2 = pd.Timestamp(pd_ + " " + r.hhmm)
            if t2 in pos:
                found = pos[t2]; break
        if found is None or found < 5 or found + max(HS) + 1 >= len(close):
            pl.append([np.nan] * len(HS)); continue
        j = found
        p3 = close[j] - close[j - 3]; sd = -np.sign(p3) if p3 != 0 else 0.0
        pl.append([sd * (close[j + H] - close[j]) * MULT[root] for H in HS])
    pl = np.array(pl)
    for h, H in enumerate(HS):
        T[f"pl{H}"] = pl[:, h]
    out = dict(root=root, n=len(T), per_year=len(T) / 8, median_secs=float(T["secs"].median()),
               side_zero=int((T["side"] == 0).sum()), mean_abs_pre3_usd=float((T["pre3"].abs() * MULT[root]).mean()),
               rho_pre3_y15=float(np.corrcoef(T["pre3"], T["y15"])[0, 1]), rho_pre3_y5=float(np.corrcoef(T["pre3"], T["y5"])[0, 1]),
               cells={})
    Tn = T[T["side"] != 0]
    for H in HS:
        out["cells"][f"all_H{H}"] = stats(Tn[f"g{H}"], f"{root} all H{H}", COST[root])
        out["cells"][f"all_delay1_H{H}"] = stats(Tn[f"gd{H}"], f"{root} delay1 H{H}", COST[root])
        out["cells"][f"placebo_H{H}"] = stats(Tn[f"pl{H}"], f"{root} placebo H{H}", COST[root])
        out["cells"][f"rth_H{H}"] = stats(Tn.loc[Tn["rth"], f"g{H}"], f"{root} RTH H{H}", COST[root])
        out["cells"][f"off_H{H}"] = stats(Tn.loc[~Tn["rth"], f"g{H}"], f"{root} OFF H{H}", COST[root])
        out["cells"][f"nonnews_H{H}"] = stats(Tn.loc[~Tn["news"], f"g{H}"], f"{root} non-news H{H}", COST[root])
        out["cells"][f"news_H{H}"] = stats(Tn.loc[Tn["news"], f"g{H}"], f"{root} news H{H}", COST[root])
        # big cascades: top half of |pre3|
        thr = Tn["pre3"].abs().median()
        out["cells"][f"big_H{H}"] = stats(Tn.loc[Tn["pre3"].abs() >= thr, f"g{H}"], f"{root} big|pre3| H{H}", COST[root])
    # rotation null for H15: same minute index, session s+k
    yrs = Tn.groupby("year")["g15"].agg(["count", "mean", "sum"])
    out["years_g15"] = {int(k): [int(v["count"]), round(float(v["mean"]), 2), round(float(v["sum"]), 0)] for k, v in yrs.iterrows()}
    out["by_hour_g15"] = Tn.groupby(Tn["hhmm"].str[:2])["g15"].agg(["count", "mean"]).round(2).to_dict("index")
    top = Tn.loc[Tn["g15"].idxmax()]
    out["top_trade_g15"] = dict(day=str(top["day"]), hhmm=top["hhmm"], side=int(top["side"]), g15=float(top["g15"]), pre3=float(top["pre3"]), secs=float(top["secs"]))
    return out, T


def main():
    ev = pd.read_csv(OUT / "crea_04_status_events.csv", parse_dates=["start_et", "resume_et"])
    ev = ev[ev["start_et"] < "2024-01-01"]
    allT = []; res = {}
    for root in ["ES", "NQ", "YM", "RTY", "CL", "NG", "GC", "SI", "HG"]:
        out, T = run_root(root, ev)
        if out is None:
            print(root, "no events"); continue
        res[root] = out; allT.append(T)
        print(f"== {root}: n={out['n']} ({out['per_year']:.0f}/yr) median secs {out['median_secs']:.0f} mean|pre3| ${out['mean_abs_pre3_usd']:.1f} rho(pre3,y5) {out['rho_pre3_y5']:+.3f} rho(pre3,y15) {out['rho_pre3_y15']:+.3f}")
        for k, c in out["cells"].items():
            if "n" in c and c["n"] >= 10:
                print(f"   {c['label']:24s} n={c['n']:5d} gross=${c['gross']:+.2f} t={c['t']:+.1f} med=${c['median']:+.2f} net=${c['net']:+.2f} win={c['win']:.2f} trim=${c['trim_both']:+.2f} top={c['top']:.0f}")
        print("   years g15:", out["years_g15"]); print("   top:", out["top_trade_g15"])
        print("   by hour g15:", {k: v for k, v in out["by_hour_g15"].items() if v["count"] >= 20})
        sys.stdout.flush()
    pd.concat(allT).to_csv(OUT / "crea_06_trades.csv", index=False)
    (OUT / "crea_06_stop_logic_fade.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")


if __name__ == "__main__":
    main()

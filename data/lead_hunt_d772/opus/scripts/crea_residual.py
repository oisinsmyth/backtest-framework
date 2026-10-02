"""Premise C9: the 'lone mover'. A target's move that its usual co-movers do not share is idiosyncratic FLOW (not common
information) and reverts. Residual e = r_target - b . r_factors over a B-minute block, b fitted on the PRIOR 40 sessions'
same-clock blocks (pre-entry). Fade the target's own price over the next H minutes when |e| is in the top quintile/decile
(threshold from prior sessions). One micro. fut_day1m, 2016..2023, seal asserted.
"""
import sys
import numpy as np, pandas as pd, pyarrow.parquet as pq

FIX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures\fut_day1m.parquet"
SEAL = "2024-01-01"
B = int(sys.argv[1]) if len(sys.argv) > 1 else 30
H = int(sys.argv[2]) if len(sys.argv) > 2 else 30
# target: (factors, usd_per_point_micro, RT, last minute of the target's own session (ET minutes), first minute)
CASES = {"SI": (["GC"], 1000.0, 8.00, 13 * 60 + 25, 9 * 60), "GC": (["6E", "ZN"], 10.0, 5.93, 13 * 60 + 30, 9 * 60),
         "HG": (["ES", "6A"], 2500.0, 4.25, 13 * 60, 9 * 60 + 30), "YM": (["ES"], 0.5, 3.80, 16 * 60, 9 * 60 + 30),
         "RTY": (["ES"], 5.0, 3.76, 16 * 60, 9 * 60 + 30), "NQ": (["ES"], 2.0, 4.07, 16 * 60, 9 * 60 + 30),
         "CL": (["ES", "6E"], 100.0, 5.03, 14 * 60 + 30, 9 * 60), "6E": (["6A", "GC"], 12500.0, 4.38, 15 * 60, 9 * 60)}
roots = sorted(set(CASES) | {f for v in CASES.values() for f in v[0]})
t = pq.read_table(FIX, filters=[("root", "in", roots), ("day", ">=", "2016-01-01"), ("day", "<", SEAL)],
                  columns=["root", "day", "bar", "close", "same_front"]).to_pandas()
assert t.day.max() < SEAL
t = t[t.same_front]
P = {r: g.pivot_table(index="day", columns="bar", values="close", aggfunc="last").reindex(columns=range(420)).ffill(axis=1)
     for r, g in t.groupby("root")}
for tgt, (facs, usd, rt, mend, mbeg) in CASES.items():
    days = P[tgt].index
    for f in facs:
        days = days.intersection(P[f].index)
    recs = []
    m = mbeg
    while m + B + H <= mend:
        b0, b1, b2 = m - 540, m + B - 540, m + B + H - 540  # bar index = minute - 540; price at minute T = close of bar T-1
        def px(r, b):
            return P[r].loc[days, b - 1] if b - 1 >= 0 else P[r].loc[days, 0]
        rt_ = np.log(px(tgt, b1) / px(tgt, b0))
        X = np.column_stack([np.log(px(f, b1) / px(f, b0)) for f in facs])
        y = (px(tgt, b2) - px(tgt, b1)).values
        recs.append(pd.DataFrame({"day": days, "m": m, "r": rt_.values, "y": y, **{f"x{i}": X[:, i] for i in range(len(facs))}}))
        m += B
    R = pd.concat(recs).dropna().sort_values(["m", "day"]).reset_index(drop=True)
    xs = [f"x{i}" for i in range(len(facs))]
    # rolling prior-40-session OLS beta per clock
    E = []
    for mm, g in R.groupby("m"):
        g = g.reset_index(drop=True)
        e = np.full(len(g), np.nan)
        Xa = g[xs].values; ra = g.r.values
        for i in range(40, len(g)):
            Xw = Xa[i - 40:i]; rw = ra[i - 40:i]
            bta, *_ = np.linalg.lstsq(np.column_stack([np.ones(40), Xw]), rw, rcond=None)
            e[i] = ra[i] - bta[0] - Xa[i] @ bta[1:]
        g["e"] = e
        g["ethr80"] = pd.Series(np.abs(e)).shift(1).rolling(120, min_periods=60).quantile(0.8).values
        g["ethr90"] = pd.Series(np.abs(e)).shift(1).rolling(120, min_periods=60).quantile(0.9).values
        g["rthr80"] = pd.Series(np.abs(ra)).shift(1).rolling(120, min_periods=60).quantile(0.8).values
        E.append(g)
    R = pd.concat(E).dropna()
    R["fade_e"] = -np.sign(R.e) * R.y * usd
    R["fade_r"] = -np.sign(R.r) * R.y * usd
    line = []
    for lab, sel, col in [("all e", R.index == R.index, "fade_e"), ("|e|>q80", R.e.abs() >= R.ethr80, "fade_e"),
                          ("|e|>q90", R.e.abs() >= R.ethr90, "fade_e"),
                          ("|r|>q80 (raw-move ctrl)", R.r.abs() >= R.rthr80, "fade_r"),
                          ("|e|>q80 & e,r same sign & |r|>q80", (R.e.abs() >= R.ethr80) & (R.r.abs() >= R.rthr80) & (np.sign(R.e) == np.sign(R.r)), "fade_e")]:
        s = R.loc[sel, col]
        line.append(f"{lab}: n{len(s)} ${s.mean():+.2f} med{s.median():+.2f} t{s.mean() / s.std() * np.sqrt(len(s)):+.2f}")
    rho = R[["e", "y"]].rank().corr().iloc[0, 1]
    print(f"{tgt}~{'+'.join(facs)} B{B} H{H} RT${rt} rank-rho(e,y)={rho:+.4f} :: " + " | ".join(line))
    s = R[R.e.abs() >= R.ethr90]
    print("   q90 by year:", s.groupby(s.day.str[:4]).fade_e.mean().round(2).to_dict())

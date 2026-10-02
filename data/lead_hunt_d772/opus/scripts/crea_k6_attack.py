"""K6 attack (gold weekend reopen). For each GC session S with a prior session Sp:
gap = P(18:00 bar close, S) - P(16:59, Sp); h1 = P(18:59,S) - P(18:00 bar close,S); m = gap + h1.
Fade sign(m) / sign(gap) / sign(h1) from entries 18:29 / 18:59 / 19:29 / 19:59 to exits 09:29 / 10:59 of S, in $/MGC.
Monday sessions (Sunday reopen) vs Tue-Fri. Enumerated circular rotation null of (sign, gate) on the Monday series.
Also the D765 China-holiday overlap: Mondays whose Sunday evening is inside a long Chinese holiday are reported apart if the
holiday list exists in the repo. 2016-2023 (seal)."""
import numpy as np, pandas as pd

FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures\fut_opening_globex_1m_cl_ng_gc_si.csv.gz"
SEAL = "2024-01-01"
need = {"16:58", "16:59", "18:00", "18:01", "18:29", "18:59", "19:29", "19:59", "09:29", "10:59"}
d = pd.read_csv(FX, usecols=["root", "session", "hhmm", "close"])
d = d[(d.root == "GC") & (d.session >= "2016-01-01") & (d.session < SEAL) & d.hhmm.isin(need)]
assert d.session.max() < SEAL
P = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
P["16:59"] = P["16:59"].fillna(P["16:58"]); P["18:00"] = P["18:00"].fillna(P["18:01"])
prev = P["16:59"].shift(1)
gapd = (pd.to_datetime(pd.Series(P.index)) - pd.to_datetime(pd.Series(P.index)).shift(1)).dt.days.values
dow = pd.to_datetime(P.index).dayofweek
usd = 10.0
gap = (P["18:00"] - prev) * usd; h1 = (P["18:59"] - P["18:00"]) * usd; m = gap + h1
mon = (dow == 0) & (gapd == 3)
tf = (dow >= 1) & (dow <= 4) & (gapd == 1)
print(f"Mondays {mon.sum()}, Tue-Fri {tf.sum()}; mean|gap| Mon ${gap[mon].abs().mean():.1f} TF ${gap[tf].abs().mean():.1f}; mean|h1| Mon ${h1[mon].abs().mean():.1f} TF ${h1[tf].abs().mean():.1f}")
for sname, sig in [("m", m), ("gap", gap), ("h1", h1)]:
    for ent in ["18:29", "18:59", "19:29", "19:59"]:
        if sname in ("m", "h1") and ent < "18:59":
            continue  # m and h1 are only known at 18:59
        line = []
        for ex in ["09:29", "10:59"]:
            y = (P[ex] - P[ent]) * usd
            for lab, grp in [("Mon", mon), ("TF", tf)]:
                f = (-np.sign(sig) * y)[grp & (sig != 0)].dropna()
                line.append(f"{lab}->{ex} ${f.mean():+6.2f} t{f.mean() / f.std() * np.sqrt(len(f)):+.2f}")
        print(f"sign {sname:3s} entry {ent}: " + " | ".join(line))
# rotation null, Monday series, sign(m), entry 18:59 -> 10:59, all and q80
D = pd.DataFrame({"s": -np.sign(m), "y": (P["10:59"] - P["18:59"]) * usd, "am": m.abs()})[mon].dropna()
D["g80"] = D.am >= D.am.shift(1).rolling(50, min_periods=30).quantile(0.8)
for lab, g in [("all", np.ones(len(D), bool)), ("q80(prior 50 Mondays)", D.g80.values)]:
    s = D.s.values; y = D.y.values; T = len(y)
    obs = (s * y)[g].mean()
    nulls = np.array([(np.roll(s, k) * y)[np.roll(g, k)].mean() for k in range(1, T)])
    print(f"Monday {lab}: obs ${obs:+.2f} n{int(g.sum())} | rotation p50 {np.median(nulls):+.2f} p95 {np.percentile(nulls, 95):+.2f} rank {(nulls < obs).mean():.3f}")
f = D.s * D.y
print("Monday all by year:", f.groupby(D.index.str[:4]).agg(["count", "mean"]).round(2).to_dict("index"))
fs = f.sort_values(); k = max(1, int(round(0.01 * len(fs))))
print(f"Monday all: med {f.median():+.2f} win {100 * (f > 0).mean():.1f}% ex-top1% {fs.iloc[:-k].mean():+.2f} ex-bot1% {fs.iloc[k:].mean():+.2f} trim {fs.iloc[k:-k].mean():+.2f} skew {f.skew():+.2f}")
print("top3", fs.iloc[-3:].round(1).to_dict(), "bottom3", fs.iloc[:3].round(1).to_dict())

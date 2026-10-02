"""C19: Lead 4's mirror at the OPEN. The NYSE/Nasdaq opening auction (imbalances published from ~09:28) concentrates
index-fund and MOO demand into the 09:30 cross; futures absorb it around 09:28-09:31. Does the futures move over the
auction window revert by 10:00 / 10:30 / 11:00? x = P(09:32) - P(09:27) (closes of bars 09:31 / 09:26); entry P(09:32);
q80 gate on trailing-250 |x|. Placebo: same construction shifted to 09:45-09:50 entry 09:50. CPI/NFP days excluded (Lead 1).
Exact circular rotation null. Index roots, 2016-2023 (seal)."""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
SEAL = "2024-01-01"
ev = pd.read_csv(EVT); ev["d"] = ev.datetime_et.str[:10]
tier1 = set(ev[ev.event.isin(["CPI", "EMPSIT"])].d)
CASES = {"NQ": ("fut_opening_globex_1m.csv.gz", 2.0, 4.07), "ES": ("fut_opening_globex_1m.csv.gz", 5.0, 4.42),
         "YM": ("fut_opening_globex_1m_ym_rty.csv.gz", 0.5, 3.80), "RTY": ("fut_opening_globex_1m_ym_rty.csv.gz", 5.0, 3.76)}
need = {"09:26", "09:31", "09:44", "09:49", "09:59", "10:29", "10:59"}
cache = {}
for root, (fn, usd, rt) in CASES.items():
    if fn not in cache:
        d = pd.read_csv(f"{FXD}\\{fn}", usecols=["root", "session", "hhmm", "close"])
        d = d[(d.session >= "2016-01-01") & (d.session < SEAL)]
        cache[fn] = d[d.hhmm.isin(need)]
    d = cache[fn][cache[fn].root == root]
    assert d.session.max() < SEAL
    P = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    P = P[~P.index.isin(tier1)]
    for lab, a, b in [("auction 09:27->09:32", "09:26", "09:31"), ("placebo 09:45->09:50", "09:44", "09:49")]:
        x = P[b] - P[a]
        g = (x.abs() >= x.abs().shift(1).rolling(250, min_periods=120).quantile(0.8)) & (x != 0)
        out = []
        for ex in ["09:59", "10:29", "10:59"]:
            y = (P[ex] - P[b]) * usd
            D = pd.DataFrame({"s": -np.sign(x), "g": g, "y": y}).dropna()
            D = D[D.index >= "2017-01-01"]
            f = (D.s * D.y)[D.g.astype(bool)]
            s_, g_, y_ = D.s.values, D.g.values.astype(bool), D.y.values
            nulls = np.array([(np.roll(s_, k) * y_)[np.roll(g_, k)].mean() for k in range(1, len(y_))])
            ex22 = f[~f.index.str.startswith("2022")].mean()
            out.append(f"->{ex}: n{len(f)} ${f.mean():+.2f} med {f.median():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f} ex22 {ex22:+.2f} rank {(nulls < f.mean()).mean():.3f}")
        print(f"{root} {lab} mean|x| ${x.abs().mean() * usd:.1f}: " + " | ".join(out))

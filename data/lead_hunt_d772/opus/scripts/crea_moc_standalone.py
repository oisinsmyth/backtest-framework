"""L4 candidate as a standalone book: fade the MOC window c = P(16:00) - P(15:50) of session S (close of the 15:59 bar minus
close of the 15:49 bar), gate |c| >= trailing-250 q80 (prior sessions), enter P(18:05, S+1), exit P(08:30) or P(10:00) of S+1.
Exact circular rotation null of (sign, gate) vs the leg; year split; ex-2022; trims; and rho of its daily $ series with
Lead 2's (fade m = P(17:00)-P(16:00), q80, same entry, exit 10:00), zeros on no-trade days, and on overlap days only.
Index roots 2016-2023 (seal)."""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"
CASES = {"NQ": ("fut_opening_globex_1m.csv.gz", 2.0, 4.07), "ES": ("fut_opening_globex_1m.csv.gz", 5.0, 4.42),
         "YM": ("fut_opening_globex_1m_ym_rty.csv.gz", 0.5, 3.80), "RTY": ("fut_opening_globex_1m_ym_rty.csv.gz", 5.0, 3.76)}
need = {"15:49", "15:59", "16:58", "16:59", "18:04", "08:29", "09:59"}
cache = {}
for root, (fn, usd, rt) in CASES.items():
    if fn not in cache:
        d = pd.read_csv(f"{FXD}\\{fn}", usecols=["root", "session", "hhmm", "close"])
        d = d[(d.session >= "2016-01-01") & (d.session < SEAL)]
        cache[fn] = d[d.hhmm.isin(need)]
    d = cache[fn][cache[fn].root == root]
    assert d.session.max() < SEAL
    P = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    P["16:59"] = P["16:59"].fillna(P["16:58"])
    N = P.shift(-1)
    ok = (pd.to_datetime(pd.Series(P.index).shift(-1)) - pd.to_datetime(pd.Series(P.index))).dt.days.values <= 4
    c = P["15:59"] - P["15:49"]; m = P["16:59"] - P["15:59"]
    gc = c.abs() >= c.abs().shift(1).rolling(250, min_periods=120).quantile(0.8)
    gm = m.abs() >= m.abs().shift(1).rolling(250, min_periods=120).quantile(0.8)
    L2 = (-np.sign(m) * (N["09:59"] - N["18:04"]) * usd).where(gm & ok).reindex(P.index)
    for ex in ["08:29", "09:59"]:
        y = ((N[ex] - N["18:04"]) * usd).where(ok)
        D = pd.DataFrame({"s": -np.sign(c), "g": gc & (c != 0), "y": y}).dropna()
        D = D[D.index >= "2017-01-01"]
        f = (D.s * D.y)[D.g]
        s_, g_, y_ = D.s.values, D.g.values.astype(bool), D.y.values
        nulls = np.array([(np.roll(s_, k) * y_)[np.roll(g_, k)].mean() for k in range(1, len(y_))])
        fs = f.sort_values(); k = max(1, int(round(0.01 * len(fs))))
        ex22 = f[~f.index.str.startswith("2022")].mean()
        line = (f"{root} fade c q80 18:05->{ex}: n{len(f)} ${f.mean():+.2f} med {f.median():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f}"
                f" | ex22 {ex22:+.2f} ({ex22 / rt:.1f}x RT) trim {fs.iloc[k:-k].mean():+.2f} ex-top1% {fs.iloc[:-k].mean():+.2f}"
                f" | null p50 {np.median(nulls):+.2f} p95 {np.percentile(nulls, 95):+.2f} rank {(nulls < f.mean()).mean():.3f}")
        if ex == "09:59":
            a = f.reindex(D.index).fillna(0.0); b = L2.reindex(D.index).fillna(0.0)
            both = f.index.intersection(L2.dropna().index)
            r_all = np.corrcoef(a, b)[0, 1]
            r_ov = np.corrcoef(f.loc[both], L2.loc[both])[0, 1] if len(both) > 10 else np.nan
            line += f"\n     rho with Lead-2 daily $ (zeros on no-trade days) {r_all:+.3f}; overlap days {len(both)} of {len(f)}, rho on overlap {r_ov:+.3f}; years {f.groupby(f.index.str[:4]).mean().round(1).to_dict()}"
        print(line)

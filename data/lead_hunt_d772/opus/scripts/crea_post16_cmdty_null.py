"""VARIANT on commodities: post-EQUITY-close hour 16:00->17:00. C5 leg B (the conservative's primary): sign from m = P(16:59,S) - P(15:59,S); enter at P(09:30,S+1) (close of the
09:29 bar), exit P(11:00,S+1) (close of 10:59), fade. Leg A = 18:05 -> 10:00 for reference. Gates q80/q90 on trailing-250
|m| (prior sessions only). Year split, trims, top trades, and an ENUMERATED time-rotation null: m's sign/gate series is
shifted against the leg series by every offset k = 1..T-1 (circular), fade mean recomputed. 2016-2023 (seal)."""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"
CASES = {"SI": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", 1000.0, 8.0), "GC": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", 10.0, 5.93),
         "NG": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", 1000.0, 4.0), "HG": ("fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz", 2500.0, 4.25),
         "CL": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", 100.0, 5.03)}
need = {"15:59", "16:58", "16:59", "18:04", "08:29", "09:29", "09:59", "10:59"}
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
    gap = (pd.to_datetime(pd.Series(P.index).shift(-1)) - pd.to_datetime(pd.Series(P.index))).dt.days.values
    ok = gap <= 4
    m = (P["16:59"] - P["15:59"])
    legs = {"A 18:05->10:00": (N["09:59"] - N["18:04"]).where(ok) * usd,
            "D 18:05->08:30": (N["08:29"] - N["18:04"]).where(ok) * usd,
            "C 18:05->09:30": (N["09:29"] - N["18:04"]).where(ok) * usd}
    for q in (0.8, 0.9):
        thr = m.abs().shift(1).rolling(250, min_periods=120).quantile(q)
        gate = (m.abs() >= thr) & (m != 0)
        for lname, L in legs.items():
            D = pd.DataFrame({"s": -np.sign(m), "g": gate, "y": L}).dropna()
            D = D[D.index >= "2017-01-01"]  # after burn-in, as the conservative's run
            f = (D.s * D.y)[D.g]
            k = max(1, int(round(0.01 * len(f)))); fs = f.sort_values()
            yr = f.groupby(f.index.str[:4]).mean().round(1).to_dict()
            ex22 = f[~f.index.str.startswith("2022")].mean(); ex2022_20 = f[~f.index.str[:4].isin(["2020", "2022"])].mean()
            # enumerated rotation null: shift (sign, gate) against y
            s = D.s.values; g = D.g.values; y = D.y.values; T = len(y)
            nullm = np.empty(T - 1)
            for off in range(1, T):
                ss = np.roll(s, off); gg = np.roll(g, off)
                nullm[off - 1] = (ss * y)[gg].mean()
            rank = (nullm < f.mean()).mean()
            print(f"{root} q{int(q * 100)} {lname}: n{len(f)} ${f.mean():+.2f} med {f.median():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f}"
                  f" | ex-top1% {fs.iloc[:-k].mean():+.2f} ex-bot1% {fs.iloc[k:].mean():+.2f} trim {fs.iloc[k:-k].mean():+.2f}"
                  f" | ex22 {ex22:+.2f} ex20&22 {ex2022_20:+.2f} | null p50 {np.median(nullm):+.2f} p95 {np.percentile(nullm, 95):+.2f} rank {rank:.3f}")
            if q == 0.8 and lname.startswith("D"):
                print(f"     years {yr}; win {100 * (f > 0).mean():.1f}%; top {fs.iloc[-3:].round(1).to_dict()} bottom {fs.iloc[:3].round(1).to_dict()}")

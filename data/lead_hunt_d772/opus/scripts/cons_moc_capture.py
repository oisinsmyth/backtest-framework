"""Standalone test of the closing-auction window c = P(16:00) - P(15:50) faded overnight (L4 candidate), and its
correlation with Lead 2's trade series. Session S: c from close(15:49)->close(15:59) bars; Lead 2 m from
close(15:59)->close(16:59). Gate: |x| >= trailing-250 q80 (shifted). Legs on S+1: 18:05 -> 08:29 close, 18:05 -> 09:59 close.
Exact circular rotation null: shift the (sign*gate) vector against the leg vector by every offset 1..N-1.
In-sample sessions 2016..2023."""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"; USD = {"NQ": (2.0, 4.07), "ES": (5.0, 4.42), "YM": (0.5, 3.80), "RTY": (5.0, 3.76)}
DAY = ["15:49", "15:59", "16:59"]; EVE = ["18:05"]; MORN = ["08:29", "09:59"]
parts = []
for fn, roots in {"fut_opening_globex_1m.csv.gz": ["ES", "NQ"], "fut_opening_globex_1m_ym_rty.csv.gz": ["YM", "RTY"]}.items():
    for ch in pd.read_csv(f"{FX}\\{fn}", usecols=["root", "session", "et", "hhmm", "close"], chunksize=2_000_000):
        ch = ch[(ch.session >= "2015-10-01") & (ch.session < SEAL) & ch.hhmm.isin(DAY + EVE + MORN)]
        sd = pd.to_datetime(ch.session); bd = pd.to_datetime(ch.et.str[:10])
        ch = ch[(ch.hhmm.isin(EVE) & (sd - bd).dt.days.between(1, 4)) | (~ch.hhmm.isin(EVE) & (bd == sd))]
        parts.append(ch)
d = pd.concat(parts); assert d.session.max() < SEAL

def rot_rank(sig, leg):
    s = sig.values; l = leg.values; n = len(s); obs = np.nansum(s * l) / max(1, (s != 0).sum())
    vals = np.array([np.nansum(np.roll(s, k) * l) / max(1, (s != 0).sum()) for k in range(1, n)])
    return obs, np.median(vals), np.percentile(vals, 95), (vals < obs).mean()

for r, g in d.groupby("root"):
    usd, rt = USD[r]
    p = g.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    nx = p.shift(-1)
    c = p["15:59"] - p["15:49"]; m = p["16:59"] - p["15:59"]
    df = pd.DataFrame({"c": c, "m": m, "L08": nx["08:29"] - nx["18:05"], "L10": nx["09:59"] - nx["18:05"]}).dropna()
    df = df[df.index >= "2016-01-01"]
    tc = df.c.abs().rolling(250, min_periods=120).quantile(0.8).shift(1)
    tm = df.m.abs().rolling(250, min_periods=120).quantile(0.8).shift(1)
    sc = (-np.sign(df.c) * (df.c.abs() >= tc)).fillna(0)   # fade sign where gated, else 0
    sm = (-np.sign(df.m) * (df.m.abs() >= tm)).fillna(0)
    for leg in ["L08", "L10"]:
        L = df[leg] * usd
        pc = (sc * L)[sc != 0]; yy = pd.to_datetime(pc.index).year
        obs, p50, p95, rk = rot_rank(sc, L)
        lead2 = sm * df["L10"] * usd
        rho = np.corrcoef(sc * L, lead2)[0, 1]
        both = ((sc != 0) & (sm != 0)).sum(); agree = ((sc != 0) & (sm != 0) & (sc == sm)).sum()
        print(f"   |c| mean ${(df.c.abs()*usd)[sc!=0].mean():.2f} capture {pc.mean()/(df.c.abs()*usd)[sc!=0].mean():.3f}")
        print(f"{r} c-fade {leg}: n{len(pc)} mean {pc.mean():.2f} med {pc.median():.2f} t {pc.mean()/pc.std(ddof=1)*np.sqrt(len(pc)):.2f} "
              f"ex22 {pc[yy!=2022].mean():.2f} ex20&22 {pc[(yy!=2022)&(yy!=2020)].mean():.2f} xRT {pc.mean()/rt:.2f} | rot p50 {p50:.2f} p95 {p95:.2f} rank {rk:.3f} "
              f"| rho(daily, Lead2) {rho:.2f}; nights both gated {both}, same sign {agree} | yrs {pc.groupby(yy).mean().round(1).to_dict()}")

"""Lead-5 screen, two pre-declared families, one run.
(I) Lead 4 on commodities: the SETTLEMENT-WINDOW move (last 10 min into each root's settlement end) faded overnight
    from P(18:05,S+1) to P(10:00,S+1). Roots GC (13:30), SI (13:25), HG (13:00), CL (14:30), NG (14:30).
(II) The EUROPEAN closing auction (17:30 CET, Euronext/Xetra/LSE close ~17:30 local; clock converted per date, so the
    DST-mismatch weeks shift it in ET): c_eu = P(close_ET) - P(close_ET - 10m), faded from close_ET+5m to 12:30 and 15:30 ET
    on ES/NQ/YM/RTY and 6E; placebo the same at close_ET - 30m.
Gate q80 trailing-250 |move| (prior sessions). Exact circular rotation null. 2016-2023 (seal)."""
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"


def book(sig, y, start="2017-01-01"):
    g = (sig.abs() >= sig.abs().shift(1).rolling(250, min_periods=120).quantile(0.8)) & (sig != 0)
    D = pd.DataFrame({"s": -np.sign(sig), "g": g, "y": y}).dropna()
    D = D[D.index >= start]
    f = (D.s * D.y)[D.g.astype(bool)]
    s_, g_, y_ = D.s.values, D.g.values.astype(bool), D.y.values
    nulls = np.array([(np.roll(s_, k) * y_)[np.roll(g_, k)].mean() for k in range(1, len(y_))])
    ex22 = f[~f.index.str.startswith("2022")].mean()
    yrs = f.groupby(f.index.str[:4]).mean()
    return (f"n{len(f)} ${f.mean():+.2f} med {f.median():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f} ex22 {ex22:+.2f} "
            f"yrs>0 {(yrs > 0).sum()}/{len(yrs)} rank {(nulls < f.mean()).mean():.3f}")


print("=== (I) commodity settlement-window move, faded overnight 18:05 -> 10:00")
CAS = {"GC": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", "13:19", "13:29", 10.0, 5.93),
       "SI": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", "13:14", "13:24", 1000.0, 8.0),
       "CL": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", "14:19", "14:29", 100.0, 5.03),
       "NG": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", "14:19", "14:29", 1000.0, 4.0),
       "HG": ("fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz", "12:49", "12:59", 2500.0, 4.25)}
cache = {}
for root, (fn, a, b, usd, rt) in CAS.items():
    if fn not in cache:
        d = pd.read_csv(f"{FXD}\\{fn}", usecols=["root", "session", "hhmm", "close"])
        cache[fn] = d[(d.session >= "2016-01-01") & (d.session < SEAL)]
    d = cache[fn]
    d = d[(d.root == root) & d.hhmm.isin({a, b, "18:04", "09:59"})]
    assert d.session.max() < SEAL
    P = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
    N = P.shift(-1)
    ok = (pd.to_datetime(pd.Series(P.index).shift(-1)) - pd.to_datetime(pd.Series(P.index))).dt.days.values <= 4
    y = ((N["09:59"] - N["18:04"]) * usd).where(ok)
    print(f" {root} (RT ${rt}): " + book((P[b] - P[a]) * usd, y))

print("=== (II) European closing auction (17:30 CET) on US index micros and 6E, fade from close+5m")
CET, NY = ZoneInfo("Europe/Berlin"), ZoneInfo("America/New_York")
import pyarrow.parquet as pq
R2 = {"ES": (5.0, 4.42), "NQ": (2.0, 4.07), "YM": (0.5, 3.80), "RTY": (5.0, 3.76), "6E": (12500.0, 4.38)}
t = pq.read_table(f"{FXD}\\fut_day1m.parquet", filters=[("root", "in", list(R2)), ("day", ">=", "2016-01-01"), ("day", "<", SEAL)],
                  columns=["root", "day", "bar", "close", "same_front"]).to_pandas()
assert t.day.max() < SEAL
t = t[t.same_front]
for root, (usd, rt) in R2.items():
    P = t[t.root == root].pivot_table(index="day", columns="bar", values="close", aggfunc="last").reindex(columns=range(420)).ffill(axis=1)
    cl = {}
    for dd in P.index:
        x = pd.Timestamp(dd + " 17:30", tz=CET).tz_convert(NY)
        cl[dd] = x.hour * 60 + x.minute - 540  # bar index of the ET minute
    cbar = pd.Series(cl)
    def at(bars):
        return pd.Series([P.at[dd, int(bb) - 1] if 0 < bb <= 420 else np.nan for dd, bb in zip(P.index, bars)], index=P.index)
    for lab, off in [("EU close", 0), ("placebo -30m", -30)]:
        e = cbar + off
        c = (at(e) - at(e - 10)) * usd
        ent = at(e + 5)
        outs = []
        for exm in (210, 390):  # 12:30, 15:30 ET
            y = (P[exm - 1] - ent) * usd
            outs.append(f"->{(540 + exm) // 60}:{(540 + exm) % 60:02d} " + book(c, y))
        print(f" {root} {lab} (ET clocks {sorted(set((cbar + off + 540).astype(int)))}): " + " || ".join(outs))

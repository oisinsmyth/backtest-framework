"""Premise C12a: does the 08:30 ET macro-release reaction revert (MES/MNQ/MGC), and is it bigger than a clock placebo?
Groups: CPI, EMPSIT (events.csv), Thursday (jobless claims every Thursday), other weekdays (Mon/Tue/Wed/Fri non-CPI/EMPSIT).
Price at T = close of the bar starting T-1 (bars are bar-start stamped). x = P(08:30+K) - P(08:30). Entry P(08:30+K).
Exit P(X). Fade $ = -sign(x)*(P(X)-P(entry))*usd_per_point_micro. Clock placebos: the same with 08:30 replaced by 08:10 / 08:50.
Seal: sessions < 2024-01-01, asserted. 2016-01 .. 2023-12.
"""
import sys
import numpy as np, pandas as pd

FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
SEAL = "2024-01-01"
ev = pd.read_csv(EVT); ev["d"] = ev.datetime_et.str[:10]; ev["hm"] = ev.datetime_et.str[11:16]
cpi = set(ev[(ev.event == "CPI") & (ev.hm == "08:30")].d); nfp = set(ev[(ev.event == "EMPSIT") & (ev.hm == "08:30")].d)
print(ev.event.unique(), len(cpi), len(nfp))

SPEC = {"ES": ("fut_opening_globex_1m.csv.gz", 5.0, 4.42), "NQ": ("fut_opening_globex_1m.csv.gz", 2.0, 4.07),
        "GC": ("fut_opening_globex_1m_cl_ng_gc_si.csv.gz", 10.0, 5.93)}


def tmin(hm):
    h, m = map(int, hm.split(":")); return h * 60 + m


cache = {}
for root, (fn, usd, rt) in SPEC.items():
    if fn not in cache:
        d = pd.read_csv(f"{FX}\\{fn}", usecols=["root", "session", "hhmm", "close"])
        d = d[(d.session >= "2016-01-01") & (d.session < SEAL)]
        cache[fn] = d
    d = cache[fn]
    d = d[d.root == root]
    assert d.session.max() < SEAL
    d = d.assign(m=d.hhmm.map(tmin))
    d = d[(d.m >= 7 * 60) & (d.m <= 11 * 60)]
    P = d.pivot_table(index="session", columns="m", values="close", aggfunc="last").reindex(columns=range(420, 661)).ffill(axis=1)
    wd = pd.to_datetime(P.index).dayofweek
    grp = np.where(P.index.isin(cpi), "CPI", np.where(P.index.isin(nfp), "EMPSIT", np.where(wd == 3, "THU", "OTHER")))
    print(f"\n==== {root} (usd/pt {usd}, RT ${rt})  sessions {len(P)}")
    for t0hm in ["08:30", "08:10", "08:50"]:
        t0 = tmin(t0hm)
        for K in [1, 3]:
            for xhm in ["09:00", "09:29", "10:00"]:
                X = tmin(xhm)
                p0 = P[t0 - 1]; pe = P[t0 + K - 1]; px = P[X - 1]
                x = pe - p0; y = px - pe
                ok = np.isfinite(x) & np.isfinite(y) & (x != 0)
                fade = -np.sign(x) * y * usd
                line = []
                for g in ["CPI", "EMPSIT", "THU", "OTHER"]:
                    s = ok & (grp == g)
                    f = fade[s]
                    big = s & (np.abs(x) >= np.nanpercentile(np.abs(x[ok]), 67))
                    fb = fade[big]
                    line.append(f"{g}:n{s.sum()} ${f.mean():+.2f}/med{np.median(f):+.2f} |x|{np.abs(x[s]).mean() * usd:.0f}"
                                f" big n{big.sum()} ${fb.mean():+.2f}")
                print(f" t0 {t0hm} K{K} exit {xhm} :: " + " | ".join(line))
    # year split for the main cell: 08:30, K1, exit 09:29, THU and all-release
    t0 = tmin("08:30"); p0 = P[t0 - 1]; pe = P[t0]; px = P[tmin("09:29") - 1]
    x = pe - p0; y = px - pe; fade = -np.sign(x) * y * usd
    yr = pd.Series(P.index.str[:4], index=P.index)
    df = pd.DataFrame({"yr": yr.values, "g": grp, "fade": fade.values, "x": x.values}).dropna()
    df = df[df.x != 0]
    print(" main cell by year (fade $ mean):")
    print(df.pivot_table(index="yr", columns="g", values="fade", aggfunc="mean").round(2).to_string())

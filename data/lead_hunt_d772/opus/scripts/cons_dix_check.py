"""Independent check of the creative's DIX reversal (conservative's own construction, written before reading theirs).
DIX (SqueezeMetrics, licensed, personal to the principal; NOTHING per-date is written out) read for dates < 2024-01-01.
z_T = (DIX_T - mean_250(T)) / sd_250(T), trailing window INCLUDING T (DIX_T is published the evening of T).
Day move D_T = close(15:59 bar) - open(09:30 bar) of T (rth 1m fixture). Trade T+1: open(09:30) -> close(15:59).
Rule: long T+1 if D_T < 0 and z_T >= c; short if D_T > 0 and z_T <= -c. Controls: 'DIX agrees' (D_T<0 & z<=-c ->long,
D_T>0 & z>=c -> short, i.e. the same fade when DIX does not contradict), unconditional fade of D_T.
Reports: $ and bp of notional per year, P&L share by year, neighbouring cuts, exact rotation of z vs price days."""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
DIX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\squeezemetrics\DIX.csv"
SEAL = "2024-01-01"; USD = {"NQ": (2.0, 4.07), "ES": (5.0, 4.42), "RTY": (5.0, 3.76), "YM": (0.5, 3.80)}
dx = pd.read_csv(DIX, usecols=["date", "dix"]); dx = dx[dx.date < SEAL].set_index("date")["dix"]
assert dx.index.max() < SEAL
z = ((dx - dx.rolling(250, min_periods=120).mean()) / dx.rolling(250, min_periods=120).std())
for r, (usd, rt) in USD.items():
    d = pd.read_csv(f"{FX}\\fut_{r}_rth_1m.csv.gz", usecols=["day", "hhmm", "open", "close"])
    d = d[(d.day >= "2015-01-01") & (d.day < SEAL)]
    o = d[d.hhmm == "09:30"].set_index("day")["open"]; c = d[d.hhmm == "15:59"].set_index("day")["close"]
    df = pd.DataFrame({"o": o, "c": c}).dropna(); df["D"] = df.c - df.o
    df["nxt"] = (df.c - df.o).shift(-1) * usd; df["notional"] = df.o.shift(-1) * usd
    df["z"] = z.reindex(df.index)
    df = df[(df.index >= "2016-01-01")].dropna()
    yy = pd.to_datetime(df.index).year
    def book(c_):
        s = np.where((df.D < 0) & (df.z >= c_), 1, np.where((df.D > 0) & (df.z <= -c_), -1, 0))
        return pd.Series(s, index=df.index)
    for cut in [0.5, 0.84, 1.28]:
        s = book(cut); q = (s * df.nxt)[s != 0]; qy = pd.to_datetime(q.index).year
        bp = (s * df.nxt / df.notional * 1e4)[s != 0]
        share = (q.groupby(qy).sum() / q.sum()).round(2).to_dict()
        bpy = bp.groupby(qy).mean().round(1).to_dict(); usdy = q.groupby(qy).mean().round(1).to_dict()
        # exact rotation: shift z against price days
        zv = df.z.values; Dv = df.D.values; nv = df.nxt.values; obs = q.mean(); vals = []
        for k in range(1, len(zv)):
            zz = np.roll(zv, k); ss = np.where((Dv < 0) & (zz >= cut), 1, np.where((Dv > 0) & (zz <= -cut), -1, 0))
            vals.append(np.sum(ss * nv) / max(1, (ss != 0).sum()))
        vals = np.array(vals)
        print(f"{r} c={cut}: n{len(q)} mean ${q.mean():.2f} med {q.median():.2f} t {q.mean()/q.std(ddof=1)*np.sqrt(len(q)):.2f} "
              f"bp {bp.mean():.2f} | ex2020 ${q[qy!=2020].mean():.2f} ex20&22 ${q[(qy!=2020)&(qy!=2022)].mean():.2f} "
              f"| rot p50 {np.median(vals):.2f} p95 {np.percentile(vals,95):.2f} rank {(vals<obs).mean():.3f}")
        print(f"     $/yr {usdy}\n     bp/yr {bpy}\n     share/yr {share}")
    sa = np.where((df.D < 0) & (df.z <= -0.84), 1, np.where((df.D > 0) & (df.z >= 0.84), -1, 0)); qa = (sa * df.nxt)[sa != 0]
    su = -np.sign(df.D); qu = (su * df.nxt)[su != 0]
    print(f"{r} controls: DIX-agrees fade n{len(qa)} ${qa.mean():.2f}; unconditional fade-yesterday n{len(qu)} ${qu.mean():.2f} "
          f"bp {(su*df.nxt/df.notional*1e4)[su!=0].mean():.2f}")

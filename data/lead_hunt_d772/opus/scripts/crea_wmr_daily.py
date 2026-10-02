"""C21: the DAILY WM/R 4pm London fix (fix window 15:57:30-16:02:30 London), not D749's month-end. c = P(fix_end) - P(fix_end-15m)
in ET (London clock converted per date). Fade from fix_end+2m to 12:00 / 13:00 / 15:00 ET. Month-ends reported apart.
6E/6A/6B/6C (micros M6E, M6A, M6B, MCD), fut_day1m, 2016-2023 (seal). Exact circular rotation null; placebo at fix-60m."""
import numpy as np, pandas as pd, pyarrow.parquet as pq
from zoneinfo import ZoneInfo

FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures\fut_day1m.parquet"
SEAL = "2024-01-01"
R = {"6E": (12500.0, 4.38), "6A": (10000.0, 4.0), "6B": (6250.0, 4.0), "6C": (10000.0, 4.0)}
t = pq.read_table(FX, filters=[("root", "in", list(R)), ("day", ">=", "2016-01-01"), ("day", "<", SEAL)],
                  columns=["root", "day", "bar", "close", "same_front"]).to_pandas()
assert t.day.max() < SEAL
t = t[t.same_front]
LON, NY = ZoneInfo("Europe/London"), ZoneInfo("America/New_York")


def book(sig, y):
    g = (sig.abs() >= sig.abs().shift(1).rolling(250, min_periods=120).quantile(0.8)) & (sig != 0)
    D = pd.DataFrame({"s": -np.sign(sig), "g": g, "y": y}).dropna()
    D = D[D.index >= "2017-01-01"]
    f = (D.s * D.y)[D.g.astype(bool)]
    s_, g_, y_ = D.s.values, D.g.values.astype(bool), D.y.values
    nulls = np.array([(np.roll(s_, k) * y_)[np.roll(g_, k)].mean() for k in range(1, len(y_))])
    yrs = f.groupby(f.index.str[:4]).mean()
    return f"n{len(f)} ${f.mean():+.2f} med {f.median():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f} yrs>0 {(yrs > 0).sum()}/{len(yrs)} rank {(nulls < f.mean()).mean():.3f}"


for root, (usd, rt) in R.items():
    P = t[t.root == root].pivot_table(index="day", columns="bar", values="close", aggfunc="last").reindex(columns=range(420)).ffill(axis=1)
    fe = pd.Series({dd: (lambda x: x.hour * 60 + x.minute + 3 - 540)(pd.Timestamp(dd + " 16:00", tz=LON).tz_convert(NY)) for dd in P.index})

    def at(bars):
        return pd.Series([P.at[dd, int(b) - 1] if 0 < b <= 420 else np.nan for dd, b in zip(P.index, bars)], index=P.index)
    for lab, off in [("fix", 0), ("placebo -60m", -60)]:
        e = fe + off
        c = (at(e) - at(e - 15)) * usd
        ent = at(e + 2)
        outs = [f"->{(540 + x) // 60}:00 " + book(c, (P[x - 1] - ent) * usd) for x in (180, 240, 360)]
        print(f"{root} {lab}: " + " || ".join(outs))

"""Lead-5 probe: grains' overnight (thin, weather-driven) move faded in the liquid day session.
day5m fixture: bar index = 5-min slots from 09:00 ET; grains trade 09:30-14:20 ET. m = close of the 09:30-09:35 bar
- close of the prior session's last bar before 14:20 (14:10-14:15 bar). Entry at the 09:35 close, exit at the
11:00 / 12:00 / 14:15 close. Micro: 1/10 of the full contract (Micro Corn/Soy/Wheat 500 bu; MZL/MZM likewise),
RT = $3 + 1 micro tick (assumed). Gate q80 trailing-250 shifted. Exact circular rotation null. <= 2023."""
import numpy as np, pandas as pd, pyarrow.parquet as pq
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures\fut_day5m.parquet"
SEAL = "2024-01-01"
# full-contract $ per price unit (prices in cents/bu for ZC ZS ZW; ZL cents/lb x 60000 lb; ZM $/short ton x 100)
FULL = {"ZC": 50.0, "ZS": 50.0, "ZW": 50.0, "ZL": 600.0, "ZM": 100.0}
TICK = {"ZC": 0.25, "ZS": 0.25, "ZW": 0.25, "ZL": 0.01, "ZM": 0.1}
print(pq.ParquetFile(FX).schema_arrow)
t = pq.read_table(FX, filters=[("root", "in", list(FULL)), ("day", "<", SEAL), ("day", ">=", "2015-06-01")]).to_pandas()
assert t["day"].max() < SEAL
print(t.groupby("root").bar.agg(["min", "max"]))
for r in FULL:
    g = t[(t.root == r) & t.same_front]
    piv = g.pivot_table(index="day", columns="bar", values="close", aggfunc="last").sort_index()
    usd = FULL[r] / 10; rt = 3.0 + TICK[r] * usd
    b0935 = 6  # slot 6 = 09:30-09:35 (slot 0 = 09:00)
    b1410 = 62  # 14:10-14:15
    prev = piv[b1410].shift(1)
    m = piv[b0935] - prev
    thr = m.abs().rolling(250, min_periods=120).quantile(0.8).shift(1)
    for xs, lab in [(23, "11:00"), (35, "12:00"), (62, "14:15")]:
        L = (piv[xs] - piv[b0935]) * usd
        ok = m.notna() & L.notna() & (piv.index >= "2016-01-01") & (m != 0)
        for cut, sel in [("all", ok), ("q80", ok & (m.abs() >= thr))]:
            s = (-np.sign(m)).where(sel, 0).fillna(0); l = L.where(ok, 0).fillna(0)
            q = (s * l)[s != 0]; yy = pd.to_datetime(q.index).year
            k = (s != 0).sum(); v = np.array([np.sum(np.roll(s.values, j) * l.values) / k for j in range(1, len(s))])
            print(f"{r} (RT ${rt:.2f}) exit {lab} {cut}: n{len(q)} |m| ${(m.abs()*usd)[sel].mean():.1f} mean {q.mean():.2f} med {q.median():.2f} "
                  f"t {q.mean()/q.std(ddof=1)*np.sqrt(len(q)):.2f} rank {(v<q.mean()).mean():.3f} posyrs {(q.groupby(yy).mean()>0).sum()}/8")

"""Premise C13: cross-venue plumbing. Spot (Binance BTCUSDT) leads CME bitcoin futures (Baur & Dimpfl 2019). When the
CME future is rich/cheap against spot relative to its own recent basis, does the FUTURE revert (unhedged, one MBT)?
d_t = [log F_t - log S_t] - median over the prior 60 CME-trade minutes. Entry at the close of minute t+1 (one-minute
delay, kills stale-print artefacts in the signal minute), exit at t+1+k. Fade $ per MBT = -sign(d)*(F_exit-F_entry)*0.1.
2018-01 .. 2023-12 (seal asserted). CME BTC (5 BTC) prices; MBT = 0.1 BTC, RT $4.31.
"""
import glob, io, zipfile
import numpy as np, pandas as pd

FIX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures\fut_btc_1m.csv.gz"
BZ = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\binance\data\spot\monthly\klines\BTCUSDT\1m"
SEAL = pd.Timestamp("2024-01-01", tz="UTC")
f = pd.read_csv(FIX, usecols=["root", "ts_utc", "close", "volume"])
f = f[f.root == "BTC"]
f["ts"] = pd.to_datetime(f.ts_utc, utc=True)
f = f[(f.ts >= "2018-01-01") & (f.ts < SEAL)].set_index("ts").sort_index()
assert f.index.max() < SEAL
S = []
for z in sorted(glob.glob(BZ + r"\BTCUSDT-1m-*.zip")):
    ym = z[-11:-4]
    if not ("2018-01" <= ym <= "2023-12"):
        continue
    with zipfile.ZipFile(z) as zz:
        raw = zz.read(zz.namelist()[0])
    s = pd.read_csv(io.BytesIO(raw), header=None, usecols=[0, 4])
    S.append(s)
s = pd.concat(S); s.columns = ["ms", "spot"]
# binance switched to microseconds in 2025; in-sample is ms
s["ts"] = pd.to_datetime(s.ms, unit="ms", utc=True)
s = s.set_index("ts")["spot"]
assert s.index.max() < SEAL
f["spot"] = s.reindex(f.index)
f = f.dropna()
f["b"] = np.log(f.close) - np.log(f.spot)
f["bmed"] = f.b.shift(1).rolling(60, min_periods=40).median()
f["d"] = f.b - f.bmed
# entry: next CME print within 2 minutes; exits by CME minute-clock (asof)
idx = f.index
F = f.close
fut = F.reindex(pd.date_range(idx.min(), idx.max(), freq="1min", tz="UTC")).ffill(limit=10)
ent = fut.reindex(idx + pd.Timedelta(minutes=1)).values
out = {}
for k in [5, 15, 30, 60]:
    ex = fut.reindex(idx + pd.Timedelta(minutes=1 + k)).values
    out[k] = (ex - ent)
f["ent"] = ent
for k in out:
    f[f"r{k}"] = out[k]
f = f.dropna(subset=["d", "ent", "r5", "r15", "r30", "r60"])
f["yr"] = f.index.year
q = f.d.abs()
print("n minutes", len(f), "basis dev sd (bp)", round(f.d.std() * 1e4, 2))
for lo in [0.9, 0.99, 0.999]:
    thr = q.quantile(lo)
    sel = f[q >= thr]
    line = []
    for k in [5, 15, 30, 60]:
        pnl = -np.sign(sel.d) * sel[f"r{k}"] * 0.1
        line.append(f"k{k}: ${pnl.mean():+.2f} med {pnl.median():+.2f} t {pnl.mean() / pnl.std() * np.sqrt(len(pnl)):+.1f}")
    print(f"|d|>=q{lo} ({thr * 1e4:.1f} bp) n={len(sel)}: " + " | ".join(line))
# beta of future's own forward return on d (bp): pooled
for k in [5, 15, 30, 60]:
    y = f[f"r{k}"] / f.ent
    print(f"k{k}: slope of fwd future return on d = {np.polyfit(f.d, y, 1)[0]:+.3f}  (−1 = full convergence by the future)")
sel = f[q >= q.quantile(0.99)]
pnl = -np.sign(sel.d) * sel.r15 * 0.1
print("q99 k15 by year:", pnl.groupby(sel.yr).agg(["count", "mean"]).round(2).to_dict("index"))
print("q99 k15 by UTC hour count:", sel.index.hour.value_counts().sort_index().to_dict())

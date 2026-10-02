"""T2d: robustness of the 1-minute BTC basis fade to the creative agent's attack.
 (d) one-bar DELAY: signal db5 at minute t (closes of bars ending at t), entry at the close of the NEXT bar (t+1),
     exit h minutes after entry. Kills any alignment artefact between Databento (ts_recv) and Binance bars.
 (b) NON-OVERLAPPING book (one position at a time, 1-min grid), trades/yr, EVE-only count, top-10-trade share.
 (c) cost at $4.31 and at +1 tick ($5.31).
 Walk-forward threshold: 99th percentile of |db5| over the trailing 60 days (pre-entry).
"""
import sys, os, json, zipfile, io
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from cons_lib import *

RAW = os.path.join(MAIN, "data", "raw", "binance", "data", "spot", "monthly", "klines", "BTCUSDT", "1m")
parts = []
for y in range(2018, 2024):
    for m in range(1, 13):
        p = os.path.join(RAW, f"BTCUSDT-1m-{y}-{m:02d}.zip")
        with zipfile.ZipFile(p) as z:
            raw = z.read(z.namelist()[0])
        d = pd.read_csv(io.BytesIO(raw), header=None, usecols=[0, 4]); d.columns = ["open_time", "c"]
        d = d[pd.to_numeric(d.open_time, errors="coerce").notna()]; d["open_time"] = pd.to_numeric(d.open_time)
        d["ts"] = pd.to_datetime(d.open_time, unit="us" if d.open_time.iloc[0] > 1e14 else "ms")
        parts.append(d[["ts", "c"]])
S = pd.concat(parts, ignore_index=True).drop_duplicates("ts").set_index("ts").sort_index(); S.index = S.index + pd.Timedelta(minutes=1)
S = S[S.index < pd.Timestamp(SEAL)]
b = pd.read_csv(os.path.join(FIX, "fut_btc_1m.csv.gz"), dtype={"day": str})
b = b[(b.root == "BTC") & (b.day < SEAL) & (b.day >= "2018-01-01")]
b["end"] = pd.to_datetime(b.ts_utc) + pd.Timedelta(minutes=1); b = b.drop_duplicates("end").set_index("end").sort_index()
idx = pd.date_range(max(b.index.min(), S.index.min()), min(b.index.max(), S.index.max()), freq="1min")
F = b.reindex(idx)
g = pd.DataFrame({"F": F.close.ffill(limit=3), "traded": F.close.notna(), "contract": F.contract.ffill(limit=3), "S": S.c.reindex(idx)})
g["b"] = g.F - g.S; g["db5"] = g.b - g.b.shift(5)
g["Fe"] = g.F.shift(-1); g["traded_e"] = g.traded.shift(-1).fillna(False).astype(bool)      # entry = next bar's close
for h in (5, 15, 30):
    g[f"yd{h}"] = g.F.shift(-1 - h) - g.Fe        # delayed-entry outcome
    g[f"y{h}"] = g.F.shift(-h) - g.F               # same-bar outcome (as T2c)
ok = (g.contract == g.contract.shift(5)) & (g.contract == g.contract.shift(-31))
g = g[ok & g.traded & np.isfinite(g.db5) & np.isfinite(g.yd30)].copy()
g["year"] = g.index.year.astype(str); g["hour"] = g.index.hour
g["sess"] = g.hour.map(lambda h: "US" if 13 <= h < 21 else ("ASIA" if h < 8 else ("EU" if h < 13 else "EVE")))
g["date"] = g.index.date
res = {"n_minutes": int(len(g))}
# in-sample top-1% threshold, same-bar vs delayed
thr = g.db5.abs().quantile(0.99); z = g[g.db5.abs() > thr]
res["insample_top1pct_thr"] = float(thr)
for h in (5, 15, 30):
    res[f"same_bar_h{h}"] = {k: round(v, 2) for k, v in four_groups((-np.sign(z.db5) * z[f"y{h}"] * 0.1).to_numpy(), z.year.to_numpy(), 4.31, "").items() if isinstance(v, float)}
    res[f"delayed_h{h}"] = four_groups((-np.sign(z.db5) * z[f"yd{h}"] * 0.1).to_numpy(), z.year.to_numpy(), 4.31, f"delayed h{h}")
# walk-forward 99th pct threshold (trailing 60 days), delayed entry, NON-OVERLAPPING book
daily = g.groupby("date").db5.apply(lambda z: z.abs().to_numpy()); q = {}; arr = []
for i, dd in enumerate(daily.index):
    if i >= 60:
        q[dd] = np.quantile(np.concatenate(arr[-60:]), 0.99)
    arr.append(daily.iloc[i])
g["thr"] = g.date.map(q)
sig = g[np.isfinite(g.thr) & (g.db5.abs() > g.thr) & g.traded_e]
res["wf_top1pct_events"] = int(len(sig))
for h in (5, 15, 30):
    # non-overlapping: walk the signal minutes, take one, skip until its exit
    times = sig.index.to_numpy(); keep = np.zeros(len(sig), bool); last_exit = np.datetime64("1970-01-01")
    for i, t in enumerate(times):
        if t > last_exit:
            keep[i] = True; last_exit = t + np.timedelta64(1 + h, "m")
    s = sig[keep]
    pnl = (-np.sign(s.db5) * s[f"yd{h}"] * 0.1)
    fg = four_groups(pnl.to_numpy(), s.year.to_numpy(), 4.31, f"wf top1% delayed non-overlap h{h}")
    srt = np.sort(pnl.to_numpy())[::-1]
    fg["top10_share_of_total"] = float(srt[:10].sum() / pnl.sum()) if pnl.sum() != 0 else float("nan")
    fg["trades_per_year"] = round(len(s) / 6, 0)
    fg["net_plus_one_tick"] = float(pnl.mean() - 5.31)
    fg["by_sess_mean"] = {k: round(float(w.mean()), 2) for k, w in pnl.groupby(s.sess)}
    fg["by_sess_n_per_year"] = {k: round(len(w) / 6, 0) for k, w in pnl.groupby(s.sess)}
    fg["daily_sharpe_ann"] = float(pnl.groupby(s.date).sum().reindex(pd.Index(sorted(set(g.date)))).fillna(0).pipe(lambda d: (d - 4.31 * pnl.groupby(s.date).size().reindex(d.index).fillna(0)).mean() / (d - 4.31 * pnl.groupby(s.date).size().reindex(d.index).fillna(0)).std() * np.sqrt(365)))
    res[f"wf_nonoverlap_delayed_h{h}"] = fg
    # the same without delay (same-bar), for the delay cost
    pnl0 = (-np.sign(s.db5) * s[f"y{h}"] * 0.1)
    res[f"wf_nonoverlap_samebar_h{h}_gross"] = float(pnl0.mean())
print(fmt(res), flush=True)
json.dump(res, open(os.path.join(OUT, "cons_t2d_btc_basis_robust.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

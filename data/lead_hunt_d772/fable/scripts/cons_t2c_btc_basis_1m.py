"""T2c: the CME bitcoin futures vs Binance spot basis at ONE MINUTE, 2018-01 .. 2023-12 (read-only from data/raw/binance
monthly 1m klines; fut_btc_1m for the CME front). One MBT = 0.1 BTC, taker cost $4.31; passive-entry cost reported at
$3.00 + half the taker crossing ($0.65) = $3.65 (the exit crosses, the entry rests).
 (A) db5 = b_t - b_{t-5}, b = F - S (closes of bars ending at t). rho with yf5/15/30; top-5% fade (in-sample threshold,
     reported as such) and a walk-forward top-5% (threshold from the trailing 60 days).
 (B) Resting-limit book: fair_t = S_{t-1} + median(b over the prior 60 min). A bid rests at fair - X (ask at fair + X)
     during minute t; it fills if the futures' 1-min low <= bid (high >= ask); the fill price is the limit. Exit at the
     close h minutes later (taker). X in {40, 60, 100, 150}; h in {5, 15, 30}. Fills per year, gross per fill, by year.
     Bar-low fills are optimistic (queue position, single-lot prints); flagged.
"""
import sys, os, json, zipfile, io, glob
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from cons_lib import *

RAW = os.path.join(MAIN, "data", "raw", "binance", "data", "spot", "monthly", "klines", "BTCUSDT", "1m")
parts = []
for y in range(2018, 2024):
    for m in range(1, 13):
        p = os.path.join(RAW, f"BTCUSDT-1m-{y}-{m:02d}.zip")
        if not os.path.exists(p):
            print("missing", p); continue
        with zipfile.ZipFile(p) as z:
            name = z.namelist()[0]
            raw = z.read(name)
        d = pd.read_csv(io.BytesIO(raw), header=None, usecols=[0, 1, 2, 3, 4, 5])
        d.columns = ["open_time", "o", "h", "l", "c", "v"]
        if isinstance(d.open_time.iloc[0], str):
            d = d[pd.to_numeric(d.open_time, errors="coerce").notna()]
        d["open_time"] = pd.to_numeric(d.open_time)
        unit = "us" if d.open_time.iloc[0] > 1e14 else "ms"
        d["ts"] = pd.to_datetime(d.open_time, unit=unit)
        parts.append(d[["ts", "c", "h", "l"]])
S = pd.concat(parts, ignore_index=True).drop_duplicates("ts").set_index("ts").sort_index()
S.index = S.index + pd.Timedelta(minutes=1)        # bar END
S = S[S.index < pd.Timestamp(SEAL)]
print("spot minutes", len(S), S.index.min(), S.index.max(), flush=True)

b = pd.read_csv(os.path.join(FIX, "fut_btc_1m.csv.gz"), dtype={"day": str})
b = b[(b.root == "BTC") & (b.day < SEAL) & (b.day >= "2018-01-01")]
b["end"] = pd.to_datetime(b.ts_utc) + pd.Timedelta(minutes=1)
b = b.drop_duplicates("end").set_index("end").sort_index()
idx = pd.date_range(max(b.index.min(), S.index.min()), min(b.index.max(), S.index.max()), freq="1min")
F = b.reindex(idx)
Fc = F.close.ffill(limit=3); traded = F.close.notna()
contract = F.contract.ffill(limit=3)
Sc = S.c.reindex(idx)
g = pd.DataFrame({"F": Fc, "S": Sc, "Fl": F.low, "Fh": F.high, "traded": traded, "contract": contract, "vol": F.volume})
g["b"] = g.F - g.S
g["db5"] = g.b - g.b.shift(5)
g["bmed"] = g.b.rolling(60, min_periods=30).median().shift(1)
g["fair"] = g.S.shift(1) + g.bmed
for h in (5, 15, 30):
    g[f"yf{h}"] = g.F.shift(-h) - g.F
    g[f"ys{h}"] = g.S.shift(-h) - g.S
    g[f"Fexit{h}"] = g.F.shift(-h)
# contract continuity over [t-5, t+30]
ok = (g.contract == g.contract.shift(5)) & (g.contract == g.contract.shift(-30))
g = g[ok]
g["year"] = g.index.year.astype(str); g["hour"] = g.index.hour
g["sess"] = g.hour.map(lambda h: "US" if 13 <= h < 21 else ("ASIA" if h < 8 else ("EU" if h < 13 else "EVE")))
res = {"minutes": int(len(g)), "span": [str(g.index.min()), str(g.index.max())], "share_traded_minutes": float(g.traded.mean()),
       "sd_db5": float(g.db5.std()), "median_abs_db5": float(g.db5.abs().median()), "sd_yf5_MBT": float((g.yf5 * 0.1).std()), "sd_yf15_MBT": float((g.yf15 * 0.1).std()), "sd_yf30_MBT": float((g.yf30 * 0.1).std())}
# (A) only minutes where the futures traded at t (a real print), db5 finite
a = g[g.traded & np.isfinite(g.db5) & np.isfinite(g.yf30)]
for h in (5, 15, 30):
    res[f"rho_db5_yf{h}"] = spearman(a.db5, a[f"yf{h}"]); res[f"rho_db5_ys{h}"] = spearman(a.db5, a[f"ys{h}"])
res["rho_db5_yf15_by_year"] = {y: round(spearman(z.db5, z.yf15), 3) for y, z in a.groupby("year")}
a = a.copy(); a["dec"] = pd.qcut(a.db5.abs().rank(method="first"), 10, labels=False)
res["fade_by_decile_abs_db5"] = {int(d): {"lo": round(float(z.db5.abs().min()), 1), "n": int(len(z)), **{f"h{h}": round(float((-np.sign(z.db5) * z[f"yf{h}"] * 0.1).mean()), 2) for h in (5, 15, 30)}} for d, z in a.groupby("dec")}
for q in (0.95, 0.99):
    thr = a.db5.abs().quantile(q); z = a[a.db5.abs() > thr]
    res[f"fade_top_{int(round((1-q)*100))}pct_insample"] = {"thr": float(thr), "n": int(len(z)), **{f"h{h}": four_groups((-np.sign(z.db5) * z[f"yf{h}"] * 0.1).to_numpy(), z.year.to_numpy(), 4.31, f"top{q} h{h}") for h in (5, 15, 30)},
                                                             "by_sess_h15": {k: round(float((-np.sign(w.db5) * w.yf15 * 0.1).mean()), 2) for k, w in z.groupby("sess")}}
# walk-forward top 5%: threshold = 95th pct of |db5| over the trailing 60 calendar days
a["date"] = a.index.date
daily = a.groupby("date").db5.apply(lambda z: z.abs().to_numpy()); q = {}; arr = []
for i, dd in enumerate(daily.index):
    if i >= 60:
        q[dd] = np.quantile(np.concatenate(arr[-60:]), 0.95)
    arr.append(daily.iloc[i])
a["thr"] = a.date.map(q); sel = a[np.isfinite(a.thr) & (a.db5.abs() > a.thr)]
res["fade_top5_walkforward"] = {"n": int(len(sel)), **{f"h{h}": four_groups((-np.sign(sel.db5) * sel[f"yf{h}"] * 0.1).to_numpy(), sel.year.to_numpy(), 4.31, f"wf top5 h{h}") for h in (5, 15, 30)},
                                "by_sess_h15": {k: round(float((-np.sign(w.db5) * w.yf15 * 0.1).mean()), 2) for k, w in sel.groupby("sess")}}
# (B) resting limit book
bk = g[np.isfinite(g.fair) & g.traded & np.isfinite(g.Fexit30)]
for X in (40, 60, 100, 150):
    bid = bk.fair - X; ask = bk.fair + X
    lf = bk.Fl <= bid; sf = bk.Fh >= ask
    out = {"fills_long": int(lf.sum()), "fills_short": int(sf.sum()), "fills_per_year": round(float((lf.sum() + sf.sum()) / 6), 1)}
    for h in (5, 15, 30):
        pl = (bk[f"Fexit{h}"][lf] - bid[lf]) * 0.1; ps = (ask[sf] - bk[f"Fexit{h}"][sf]) * 0.1
        pnl = pd.concat([pl, ps]); yrs = pnl.index.year.astype(str).to_numpy()
        fg = four_groups(pnl.to_numpy(), yrs, 3.65, f"rest X={X} h={h}")
        out[f"h{h}"] = {k: (round(v, 2) if isinstance(v, float) else v) for k, v in fg.items() if k in ("n", "gross_mean", "gross_median", "t", "net_mean", "win", "trimmed", "ex_top1", "pos_years", "n_years", "by_year_mean", "top_trade")}
        out[f"h{h}"]["net_at_taker_cost"] = round(float(pnl.mean() - 4.31), 2)
    # how often both sides fill in the same minute (a wide bar: both limits hit -> ambiguous)
    out["both_sides_same_minute"] = int((lf & sf).sum())
    res[f"rest_X{X}"] = out
print(fmt(res), flush=True)
json.dump(res, open(os.path.join(OUT, "cons_t2c_btc_basis_1m.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

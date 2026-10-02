"""Premise test T2: CME bitcoin futures vs Binance spot -- does the futures' excess move over spot (the basis change)
revert in the futures? One MBT (0.1 BTC), cost $4.31. In-sample 2018-02-12 (Binance 15m start) .. 2023-12-29.
Grid: 15-minute UTC points. F_T = last CME front close at or before T (within 5 min); S_T = Binance close of the bar
starting T-15. db = (F_T - S_T) - (F_{T-15} - S_{T-15}). y_fut = F_{T+h} - F_T, y_spot = S_{T+h} - S_T, h = 15, 30, 60.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from cons_lib import *

b = pd.read_csv(os.path.join(FIX, "fut_btc_1m.csv.gz"), dtype={"day": str})
b = b[(b.root == "BTC") & (b.day < SEAL)]
b["ts"] = pd.to_datetime(b.ts_utc)
b = b.sort_values("ts")
# futures close at each 15-min grid point: bar starting at T-1 (ends at T) preferred; else last bar within 5 minutes
b["grid"] = (b.ts + pd.Timedelta(minutes=1)).dt.ceil("15min")   # the grid point this bar's END is at or before
b["lag"] = (b.grid - (b.ts + pd.Timedelta(minutes=1))).dt.total_seconds() / 60
fb = b[b.lag <= 5].groupby("grid").agg(F=("close", "last"), lag=("lag", "last"), contract=("contract", "last"), vol=("volume", "sum"))
fb = fb[fb.lag <= 5]

s = pd.read_csv(os.path.join(FIX, "crypto_binance_15m_raw.csv.gz"))
s = s[s.symbol == "BTCUSDT"].copy()
s["ts"] = pd.to_datetime(s.timestamp)
s["grid"] = s.ts + pd.Timedelta(minutes=15)   # bar close time
s = s[s.grid < pd.Timestamp(SEAL)]
ss = s.set_index("grid")["close"].rename("S")

g = fb.join(ss, how="inner")
g = g[~g.index.duplicated()]
idx = pd.date_range(g.index.min(), g.index.max(), freq="15min")
g = g.reindex(idx)
g["basis"] = g.F - g.S
g["db"] = g.basis - g.basis.shift(1)
g["bps_db"] = g.db / g.S * 1e4
for h in (15, 30, 60):
    k = h // 15
    g[f"yf{h}"] = g.F.shift(-k) - g.F
    g[f"ys{h}"] = g.S.shift(-k) - g.S
# contract continuity: same contract at T-15, T, T+h
g["c0"] = g.contract; g["cm"] = g.contract.shift(1)
ok = (g.c0 == g.cm)
for h in (15, 30, 60):
    k = h // 15
    ok &= (g.contract.shift(-k) == g.c0)
g = g[ok & np.isfinite(g.db)]
# CME hours: drop the daily halt and weekend (keep rows where F exists at T-15, T and T+60 -- already implied by finite)
g["hour_utc"] = g.index.hour
g["dow"] = g.index.dayofweek
g["year"] = g.index.year.astype(str)
g = g[np.isfinite(g.yf60) & np.isfinite(g.ys60)]
print("grid rows", len(g), g.index.min(), g.index.max(), "median |basis|", float(g.basis.abs().median()), flush=True)

res = {"n": int(len(g)), "span": [str(g.index.min()), str(g.index.max())], "cost": 4.31,
       "sd_yf15_usd_per_MBT": float((g.yf15 * 0.1).std()), "sd_yf30": float((g.yf30 * 0.1).std()), "sd_yf60": float((g.yf60 * 0.1).std()),
       "sd_db_usd": float(g.db.std()), "median_abs_db_usd": float(g.db.abs().median())}
for h in (15, 30, 60):
    res[f"rho_db_yfut{h}"] = spearman(g.db, g[f"yf{h}"])
    res[f"rho_db_yspot{h}"] = spearman(g.db, g[f"ys{h}"])
    res[f"rho_db_ydiff{h}"] = spearman(g.db, g[f"yf{h}"] - g[f"ys{h}"])
    res[f"rho_db_yfut{h}_by_year"] = {y: round(spearman(z.db, z[f"yf{h}"]), 3) for y, z in g.groupby("year")}
# plain futures reversion control: rho of the futures' own last-15-min move with the next
g["xf"] = g.F - g.F.shift(1)
res["rho_xf_yf15"] = spearman(g.xf, g.yf15); res["rho_xf_yf30"] = spearman(g.xf, g.yf30)
# the spot's own move as a predictor of the futures (catch-up): rho(xs, yf)
g["xsp"] = g.S - g.S.shift(1)
res["rho_xs_yf15"] = spearman(g.xsp, g.yf15)
# by session: US day (13:30-21:00 UTC), Asia (00:00-08:00), Europe (08:00-13:30), evening
def sess(h):
    return "US" if 13 <= h < 21 else ("ASIA" if h < 8 else ("EU" if h < 13 else "EVE"))
g["sess"] = g.hour_utc.map(sess)
res["rho_db_yf30_by_sess"] = {k: round(spearman(z.db, z.yf30), 3) for k, z in g.groupby("sess")}
res["n_by_sess"] = {k: int(len(z)) for k, z in g.groupby("sess")}
# walk-forward fade of the top third of |db| (threshold from the trailing 250 days of |db| in bps): short MBT after the
# futures rose relative to spot. Hold 30 and 60 min.
g["date"] = g.index.date
daily = g.groupby("date").bps_db.apply(lambda z: z.abs().to_numpy())
q = {}; arr = []
for i, dd in enumerate(daily.index):
    if i >= 250:
        q[dd] = np.quantile(np.concatenate(arr[-250:]), 2 / 3)
    arr.append(daily.iloc[i])
g["thr"] = g.date.map(q)
sel = g[np.isfinite(g.thr) & (g.bps_db.abs() > g.thr)]
for h in (15, 30, 60):
    pnl = (-np.sign(sel.db) * sel[f"yf{h}"] * 0.1).to_numpy()
    res[f"fade_top3rd_h{h}"] = four_groups(pnl, sel.year.to_numpy(), 4.31, f"fade |db| top third, hold {h}m")
    res[f"fade_top3rd_h{h}_by_sess"] = {k: round(float((-np.sign(z.db) * z[f"yf{h}"] * 0.1).mean()), 2) for k, z in sel.groupby("sess")}
# the same fade on the plain futures move (control)
g["thr_xf"] = g.date.map({dd: np.nan for dd in q})
daily2 = g.groupby("date").xf.apply(lambda z: (z / z.abs().max() if False else z).abs().to_numpy())
arr = []; q2 = {}
for i, dd in enumerate(daily2.index):
    if i >= 250:
        q2[dd] = np.quantile(np.concatenate(arr[-250:]), 2 / 3)
    arr.append(daily2.iloc[i])
g["thr_xf"] = g.date.map(q2)
sel2 = g[np.isfinite(g.thr_xf) & (g.xf.abs() > g.thr_xf)]
for h in (30,):
    pnl = (-np.sign(sel2.xf) * sel2[f"yf{h}"] * 0.1).to_numpy()
    res[f"control_fade_plain_xf_h{h}"] = four_groups(pnl, sel2.year.to_numpy(), 4.31, "fade |xf| top third (plain futures reversion)")
# rotation null of rho(db, yf30): rotate yf30 by k grid points, 400 sampled offsets
obs, p50, p95, p05, p = rotation_p(g.db.to_numpy(), g.yf30.to_numpy(), spearman, n_off=400)
res["rotation_rho_db_yf30"] = {"obs": obs, "p05": p05, "p50": p50, "p95": p95, "p_two_sided": p}
print(fmt(res), flush=True)
json.dump(res, open(os.path.join(OUT, "cons_t2_btc_basis.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

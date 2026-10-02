"""T2b: dose and level variants of the BTC basis reversion. Same grid as T2.
 (a) gross of the 30/60-min fade by decile of |db| (is the tail where the money is, and is it bounce?);
 (b) LEVEL deviation: dev = basis - rolling median basis over the prior 96 grid points (24h); fade the top third of |dev|;
 (c) a bounce control: require the futures' last 15-min bar to have volume >= its session median (a traded print), and a
     2-tick filter: only |db| >= 3 ticks ($15).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from cons_lib import *

b = pd.read_csv(os.path.join(FIX, "fut_btc_1m.csv.gz"), dtype={"day": str})
b = b[(b.root == "BTC") & (b.day < SEAL)]
b["ts"] = pd.to_datetime(b.ts_utc); b = b.sort_values("ts")
b["grid"] = (b.ts + pd.Timedelta(minutes=1)).dt.ceil("15min")
b["lag"] = (b.grid - (b.ts + pd.Timedelta(minutes=1))).dt.total_seconds() / 60
fb = b[b.lag <= 5].groupby("grid").agg(F=("close", "last"), lag=("lag", "last"), contract=("contract", "last"), vol=("volume", "sum"), nbars=("close", "size"))
s = pd.read_csv(os.path.join(FIX, "crypto_binance_15m_raw.csv.gz")); s = s[s.symbol == "BTCUSDT"].copy()
s["grid"] = pd.to_datetime(s.timestamp) + pd.Timedelta(minutes=15); s = s[s.grid < pd.Timestamp(SEAL)]
g = fb.join(s.set_index("grid")["close"].rename("S"), how="inner"); g = g[~g.index.duplicated()]
g = g.reindex(pd.date_range(g.index.min(), g.index.max(), freq="15min"))
g["basis"] = g.F - g.S; g["db"] = g.basis - g.basis.shift(1)
g["lvl"] = g.basis - g.basis.rolling(96, min_periods=48).median().shift(1)
for h in (15, 30, 60, 120):
    k = h // 15; g[f"yf{h}"] = g.F.shift(-k) - g.F; g[f"ys{h}"] = g.S.shift(-k) - g.S
ok = (g.contract == g.contract.shift(1))
for k in (1, 2, 4, 8):
    ok &= (g.contract.shift(-k) == g.contract)
g = g[ok & np.isfinite(g.db) & np.isfinite(g.yf120)]
g["year"] = g.index.year.astype(str); g["hour_utc"] = g.index.hour
g["sess"] = g.hour_utc.map(lambda h: "US" if 13 <= h < 21 else ("ASIA" if h < 8 else ("EU" if h < 13 else "EVE")))
res = {"n": int(len(g))}
# (a) deciles of |db|
g["dec"] = pd.qcut(g.db.abs().rank(method="first"), 10, labels=False)
tab = {}
for dcl, z in g.groupby("dec"):
    tab[int(dcl)] = {"abs_db_lo": round(float(z.db.abs().min()), 1), "n": int(len(z)),
                     **{f"fade{h}": round(float((-np.sign(z.db) * z[f"yf{h}"] * 0.1).mean()), 2) for h in (15, 30, 60, 120)},
                     "fade30_t": round(tstat((-np.sign(z.db) * z.yf30 * 0.1).to_numpy()), 2),
                     "fade30_median": round(float((-np.sign(z.db) * z.yf30 * 0.1).median()), 2)}
res["by_decile_abs_db"] = tab
# top 5% and top 2%
for q in (0.95, 0.98):
    thr = g.db.abs().quantile(q); z = g[g.db.abs() > thr]
    res[f"top_{int((1-q)*100)}pct_in_sample_threshold"] = {"thr_usd": float(thr), "n": int(len(z)),
        **{f"fade{h}": four_groups((-np.sign(z.db) * z[f"yf{h}"] * 0.1).to_numpy(), z.year.to_numpy(), 4.31, f"top {q}") for h in (30, 60)}}
# (b) level deviation
m = np.isfinite(g.lvl)
res["rho_lvl_yf30"] = spearman(g.lvl[m], g.yf30[m]); res["rho_lvl_yf60"] = spearman(g.lvl[m], g.yf60[m]); res["rho_lvl_yf120"] = spearman(g.lvl[m], g.yf120[m])
res["rho_lvl_ys60"] = spearman(g.lvl[m], g.ys60[m])
res["rho_lvl_yf60_by_year"] = {y: round(spearman(z.lvl, z.yf60), 3) for y, z in g[m].groupby("year")}
gg = g[m].copy(); gg["date"] = gg.index.date
daily = gg.groupby("date").lvl.apply(lambda z: z.abs().to_numpy()); q = {}; arr = []
for i, dd in enumerate(daily.index):
    if i >= 250:
        q[dd] = np.quantile(np.concatenate(arr[-250:]), 2 / 3)
    arr.append(daily.iloc[i])
gg["thr"] = gg.date.map(q); sel = gg[np.isfinite(gg.thr) & (gg.lvl.abs() > gg.thr)]
for h in (30, 60, 120):
    res[f"lvl_fade_top3rd_h{h}"] = four_groups((-np.sign(sel.lvl) * sel[f"yf{h}"] * 0.1).to_numpy(), sel.year.to_numpy(), 4.31, f"level fade h{h}")
# (c) bounce controls on the db fade
med_vol = g.groupby(g.index.date).vol.transform("median")
z = g[(g.db.abs() >= 15) & (g.vol >= med_vol)]
res["db_ge_3ticks_and_traded"] = {"n": int(len(z)), **{f"fade{h}": four_groups((-np.sign(z.db) * z[f"yf{h}"] * 0.1).to_numpy(), z.year.to_numpy(), 4.31, "3tick+traded") for h in (30, 60)}}
z = g[(g.db.abs() >= 30)]
res["db_ge_6ticks"] = {"n": int(len(z)), **{f"fade{h}": four_groups((-np.sign(z.db) * z[f"yf{h}"] * 0.1).to_numpy(), z.year.to_numpy(), 4.31, "6tick") for h in (30, 60)}}
# is the futures reverting, or is the futures just noisier? share of db variance that is futures vs spot:
res["sd_xf"] = float((g.F - g.F.shift(1)).std()); res["sd_xs"] = float((g.S - g.S.shift(1)).std()); res["sd_db"] = float(g.db.std())
print(fmt(res), flush=True)
json.dump(res, open(os.path.join(OUT, "cons_t2b_btc_basis_dose.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

"""T8b: is the SIL post-settlement fade's 2022-23 fade-out scale (vol) or regime? Per year: sd of y60, mean |x|, the
top-third fade in dollars and in units of sd(y60) (volatility units, D729's lens), and rho(x, y60)."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from cons_lib import *
d = load_day1m(["SI"]); d = d[d.present & d.same_front]
P = d.pivot_table(index="day", columns="bar", values="close").reindex(columns=range(420)).ffill(axis=1, limit=3)
days = list(P.index)
def pr(m): return P[m - 541].to_numpy()
x = (pr(13 * 60 + 25) - pr(12 * 60 + 55)) * 1000; y = (pr(14 * 60 + 25) - pr(13 * 60 + 25)) * 1000
f = pd.DataFrame({"day": days, "x": x, "y": y}).dropna(); f["year"] = f.day.str[:4]
s = f.x.abs().to_numpy(); thr = np.full(len(f), np.nan)
for i in range(250, len(f)):
    thr[i] = np.quantile(s[i - 250:i], 2 / 3)
f["top"] = np.isfinite(thr) & (s > thr); f["fade"] = -np.sign(f.x) * f.y
rows = []
for yr, z in f.groupby("year"):
    t = z[z.top]
    rows.append({"year": yr, "n_top": int(len(t)), "sd_y60": round(float(z.y.std()), 1), "mean_abs_x": round(float(z.x.abs().mean()), 1),
                 "rho_x_y": round(spearman(z.x, z.y), 3), "fade_top_usd": round(float(t.fade.mean()), 2) if len(t) else None,
                 "fade_top_volunits": round(float(t.fade.mean() / z.y.std()), 3) if len(t) else None, "fade_top_t": round(tstat(t.fade.to_numpy()), 2) if len(t) > 3 else None,
                 "fade_all_usd": round(float(z.fade.mean()), 2), "win_top": round(float((t.fade > 0).mean()), 3) if len(t) else None})
out = pd.DataFrame(rows)
print(out.to_string())
# half-splits of 2022-23 and of 2016-21 for the symmetric trim and the sign test
for lab, m in (("2016-21", f.year <= "2021"), ("2022-23", f.year >= "2022")):
    t = f[m & f.top]; v = t.fade.to_numpy(); q = np.quantile(v, [0.01, 0.99])
    print(lab, "n", len(t), "mean", round(v.mean(), 2), "trimmed", round(v[(v > q[0]) & (v < q[1])].mean(), 2), "median", round(float(np.median(v)), 2), "win", round((v > 0).mean(), 3), "t", round(tstat(v), 2))
out.to_json(os.path.join(OUT, "cons_t8b_sil_decay.json"), orient="records", indent=1)

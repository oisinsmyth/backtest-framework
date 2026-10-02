"""T10b: robustness of the vol-gated SIL post-settlement fade (gate = trailing-20-session sd of y60, pre-entry).
 (a) threshold ladder $60..$110 (knife-edge check); (b) 5-minute DELAYED entry (fill at the 13:30 close, exit 14:25) and
 10-minute delayed; (c) rotation null of the gated fade (rotate y60 within the gated set, exact); (d) does |x| add inside
 the gate (top half of |x| vs bottom half); (e) the clock placebo under its own gate (x = 11:55->12:25, y = 12:25->13:25);
 (f) the gate on the 1% symmetric trim and ex-top-1% means; (g) Mon-Thu vs Friday; (h) net at $8, $13, $18.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from cons_lib import *
d = load_day1m(["SI"]); d = d[d.present & d.same_front]
g = d.pivot_table(index="day", columns="bar", values="close").reindex(columns=range(420)).ffill(axis=1, limit=3)
def pr(m): return g[m - 541].to_numpy()
M = 1000.0
def build(x0, x1, delay=0):
    f = pd.DataFrame({"day": list(g.index), "x": (pr(x1) - pr(x0)) * M, "y60": (pr(x1 + 60) - pr(x1)) * M,
                      "yd": (pr(x1 + 60) - pr(x1 + delay)) * M}).dropna()
    f["year"] = f.day.str[:4]; f["dow"] = pd.to_datetime(f.day).dt.dayofweek
    f["gate"] = f.y60.rolling(20).std().shift(1)
    f["fade"] = -np.sign(f.x) * f.y60; f["faded"] = -np.sign(f.x) * f.yd
    return f
res = {}
f = build(12 * 60 + 55, 13 * 60 + 25, delay=5)
f10 = build(12 * 60 + 55, 13 * 60 + 25, delay=10)
def summ(v, yrs):
    v = np.asarray(v, float); q = np.quantile(v, [0.01, 0.99]) if len(v) > 100 else (np.nan, np.nan)
    tot = v.sum(); srt = np.sort(v)[::-1]
    ys = pd.Series(v).groupby(np.asarray(yrs)).agg(["mean", "count", "sum"])
    return {"n": int(len(v)), "per_year": round(len(v) / 8, 0), "gross": round(float(v.mean()), 2), "median": round(float(np.median(v)), 2), "t": round(tstat(v), 2), "nw_t": round(nw_t(v), 2),
            "trimmed": round(float(v[(v > q[0]) & (v < q[1])].mean()), 2) if len(v) > 100 else None, "ex_top1": round(float(v[v < q[1]].mean()), 2) if len(v) > 100 else None,
            "win": round(float((v > 0).mean()), 3), "net8": round(float(v.mean() - 8), 2), "net13": round(float(v.mean() - 13), 2), "net18": round(float(v.mean() - 18), 2),
            "top10_share": round(float(srt[:10].sum() / tot), 3) if tot > 0 else None, "max_year_share": round(float(ys["sum"].max() / tot), 3) if tot > 0 else None,
            "pos_years": int((ys["sum"] > 0).sum()), "n_years": int(len(ys)), "by_year": {k: [round(float(r["mean"]), 1), int(r["count"])] for k, r in ys.iterrows()}}
# (a) ladder
res["ladder"] = {}
for X in (60, 70, 80, 90, 100, 110):
    on = f[f.gate >= X]; res["ladder"][X] = summ(on.fade, on.year)
    print("gate >=", X, {k: v for k, v in res["ladder"][X].items() if k != "by_year"}, flush=True)
on = f[f.gate >= 80]
print("by year @80", res["ladder"][80]["by_year"])
# (b) delayed entries
res["delayed5_at80"] = summ(on.faded, on.year); on10 = f10[f10.gate >= 80]; res["delayed10_at80"] = summ(on10.faded, on10.year)
print("delayed 5m", {k: v for k, v in res["delayed5_at80"].items() if k != "by_year"}); print("delayed 10m", {k: v for k, v in res["delayed10_at80"].items() if k != "by_year"})
# (c) rotation null within the gated set: rotate y60 across gated days
xs = on.x.to_numpy(); ys = on.y60.to_numpy(); n = len(xs)
vals = np.array([(-np.sign(xs) * np.roll(ys, k)).mean() for k in range(1, n)])
res["rotation_at80"] = {"obs": float((-np.sign(xs) * ys).mean()), "p50": float(np.percentile(vals, 50)), "p95": float(np.percentile(vals, 95)), "p99": float(np.percentile(vals, 99)), "rank": float((vals < (-np.sign(xs) * ys).mean()).mean())}
print("rotation", res["rotation_at80"])
# (d) |x| inside the gate
med = on.x.abs().median(); hi = on[on.x.abs() > med]; lo = on[on.x.abs() <= med]
res["x_top_half_at80"] = summ(hi.fade, hi.year); res["x_bottom_half_at80"] = summ(lo.fade, lo.year)
print("|x| top half", {k: v for k, v in res["x_top_half_at80"].items() if k != "by_year"}); print("|x| bottom half", {k: v for k, v in res["x_bottom_half_at80"].items() if k != "by_year"})
# (e) clock placebo under its own gate
p = build(11 * 60 + 55, 12 * 60 + 25); pon = p[p.gate >= 80]; res["placebo_1225_at80"] = summ(pon.fade, pon.year)
print("placebo 12:25 gated", {k: v for k, v in res["placebo_1225_at80"].items() if k != "by_year"})
# (g) weekday
mt = on[on.dow < 4]; fr = on[on.dow == 4]; res["monthu_at80"] = summ(mt.fade, mt.year); res["fri_at80"] = summ(fr.fade, fr.year)
print("Mon-Thu", {k: v for k, v in res["monthu_at80"].items() if k != "by_year"}); print("Fri", {k: v for k, v in res["fri_at80"].items() if k != "by_year"})
# share of 2020-22 in net at 80
v = on.fade.to_numpy(); yr = on.year.to_numpy(); res["share_2020_22_at80"] = float(v[(yr >= "2020") & (yr <= "2022")].sum() / v.sum())
print("2020-22 share", res["share_2020_22_at80"])
json.dump(res, open(os.path.join(OUT, "cons_t10b_sil_gate_robust.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

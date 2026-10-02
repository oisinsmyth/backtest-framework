"""T8: SIL post-settlement fade, the control the TAS agreement cell must beat. fut_day1m SI 2016-23.
x = P(13:25) - P(12:55) (the move into the COMEX silver settlement window, 12:55 -> 13:25 ET); fade = -sign(x);
y30 = P(13:55) - P(13:25), y60 = P(14:25) - P(13:25), y90 = P(14:55) - P(13:25). One SIL = $1000/pt; cost $8 (one tick) and
$13 (+1 tick). Cells: all days; walk-forward top third of |x| (trailing 250 sessions); top half. Checks: by year with the
max-year share, top-10 share, trimmed mean, median, rotation null of rho(x,y60), Fridays vs Mon-Thu, eras, and the GC
placebo (same clocks on GC/MGC) and a clock placebo on SI (11:55->12:25 faded to 13:25).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from cons_lib import *

d = load_day1m(["SI", "GC"]); d = d[d.present & d.same_front]
P = {r: d[d.root == r].pivot_table(index="day", columns="bar", values="close").reindex(columns=range(420)).ffill(axis=1, limit=3) for r in ["SI", "GC"]}
def pr(root, days, m):
    b = m - 540 - 1
    return P[root].reindex(days)[b].to_numpy()
res = {}
def cell(root, mult, cost, x0, x1, label):
    days = list(P[root].index)
    x = (pr(root, days, x1) - pr(root, days, x0)) * mult
    out = {"label": label, "cost": cost}
    f = pd.DataFrame({"day": days, "x": x})
    for h, m in (("y30", x1 + 30), ("y60", x1 + 60), ("y90", x1 + 90)):
        f[h] = (pr(root, days, m) - pr(root, days, x1)) * mult
    f = f.dropna(); f["year"] = f.day.str[:4]; f["dow"] = pd.to_datetime(f.day).dt.dayofweek
    s = f.x.abs().to_numpy(); thr3 = np.full(len(f), np.nan); thr2 = np.full(len(f), np.nan)
    for i in range(250, len(f)):
        thr3[i] = np.quantile(s[i - 250:i], 2 / 3); thr2[i] = np.quantile(s[i - 250:i], 0.5)
    out["n"] = int(len(f)); out["sd_y60"] = float(f.y60.std()); out["mean_abs_x"] = float(f.x.abs().mean())
    out["rho_x_y30"] = spearman(f.x, f.y30); out["rho_x_y60"] = spearman(f.x, f.y60); out["rho_x_y90"] = spearman(f.x, f.y90)
    obs, p50, p95, p05, pv = rotation_p(f.x.to_numpy(), f.y60.to_numpy(), spearman)
    out["rotation_y60"] = {"obs": obs, "p05": p05, "p95": p95, "p": pv}
    for name, sel in (("all", f), ("top3rd", f[np.isfinite(thr3) & (s > thr3)]), ("tophalf", f[np.isfinite(thr2) & (s > thr2)]),
                      ("top3rd_monthu", f[np.isfinite(thr3) & (s > thr3) & (f.dow < 4)]), ("top3rd_fri", f[np.isfinite(thr3) & (s > thr3) & (f.dow == 4)])):
        for h in ("y30", "y60", "y90"):
            pnl = (-np.sign(sel.x) * sel[h]).to_numpy()
            fg = four_groups(pnl, sel.year.to_numpy(), cost, f"{name} {h}")
            if fg["n"] > 10:
                srt = np.sort(pnl)[::-1]; tot = pnl.sum()
                fg["top10_share"] = float(srt[:10].sum() / tot) if tot > 0 else float("nan")
                ys = pd.Series(pnl).groupby(sel.year.to_numpy()).sum()
                fg["max_year_share"] = float(ys.max() / tot) if tot > 0 else float("nan")
                fg["net_plus_tick"] = float(pnl.mean() - cost - (5.0 if root == "SI" else 1.0))
                fg["per_year"] = round(fg["n"] / 8, 0)
                fg["eras"] = {e: round(float(pnl[(sel.year.to_numpy() >= a) & (sel.year.to_numpy() <= b)].mean()), 2) for e, (a, b) in {"2016-18": ("2016", "2018"), "2019-21": ("2019", "2021"), "2022-23": ("2022", "2023")}.items()}
            out[f"{name}_{h}"] = {k: (round(v, 3) if isinstance(v, float) else v) for k, v in fg.items() if k in ("n", "gross_mean", "gross_median", "t", "nw_t", "net_mean", "win", "trimmed", "ex_top1", "pos_years", "n_years", "by_year_mean", "top_trade", "top10_share", "max_year_share", "net_plus_tick", "per_year", "eras")}
    return out
res["SI_settle_1255_1325"] = cell("SI", 1000.0, 8.0, 12 * 60 + 55, 13 * 60 + 25, "SIL settlement window fade")
res["SI_placebo_1155_1225"] = cell("SI", 1000.0, 8.0, 11 * 60 + 55, 12 * 60 + 25, "SIL clock placebo")
res["GC_settle_1300_1330"] = cell("GC", 10.0, 5.93, 13 * 60, 13 * 60 + 30, "MGC settlement window fade")
for k, v in res.items():
    print("=====", k, "n", v["n"], "sd_y60", round(v["sd_y60"], 1), "rho30/60/90", round(v["rho_x_y30"], 3), round(v["rho_x_y60"], 3), round(v["rho_x_y90"], 3), "rot", {a: round(b, 3) for a, b in v["rotation_y60"].items()})
    for kk in ("all_y60", "top3rd_y30", "top3rd_y60", "top3rd_y90", "tophalf_y60", "top3rd_monthu_y60", "top3rd_fri_y60"):
        print("  ", kk, v[kk])
json.dump(res, open(os.path.join(OUT, "cons_t8_sil_settle_fade.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

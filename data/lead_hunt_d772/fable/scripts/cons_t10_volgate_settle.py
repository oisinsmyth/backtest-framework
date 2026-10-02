"""T10: the vol-gate reframing, GATE ALONE (no flow signer): the post-settlement fade of the window move on NG (MNG),
CL (MCL), SI (SIL), GC (MGC), traded only when the ex-ante volatility of the response is high enough to clear the fixed
dollar cost. Gate g_t = sd over the trailing 20 sessions (strictly before t) of the post-window move y60 (window end ->
+60m) in micro dollars; thresholds declared from the breakeven arithmetic: a ~0.15-sd-per-trade effect needs sd >=
cost/0.15 for 1.0x: NG $27 (-> X = 30, 40), CL $34 (-> 35, 50), SI $53 (-> 55, 80), GC $40 (-> 40, 60).
x = P(end) - P(end-30), fade = -sign(x), y60 = P(end+60) - P(end). Report gated vs ungated, by year, n/yr, net at cost
and +1 tick, top-10 share, vol-units.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from cons_lib import *
ROOTS = {"NG": (14 * 60 + 30, 1000.0, 4.0, 1.0, (30, 40)), "CL": (14 * 60 + 30, 100.0, 5.03, 1.0, (35, 50)),
         "SI": (13 * 60 + 25, 1000.0, 8.0, 5.0, (55, 80)), "GC": (13 * 60 + 30, 10.0, 5.93, 1.0, (40, 60))}
d = load_day1m(list(ROOTS)); d = d[d.present & d.same_front]
res = {}
for root, (end, mult, cost, tick, Xs) in ROOTS.items():
    g = d[d.root == root].pivot_table(index="day", columns="bar", values="close").reindex(columns=range(420)).ffill(axis=1, limit=3)
    def pr(m): return g[m - 541].to_numpy()
    f = pd.DataFrame({"day": list(g.index), "x": (pr(end) - pr(end - 30)) * mult, "y60": (pr(end + 60) - pr(end)) * mult, "y30": (pr(end + 30) - pr(end)) * mult}).dropna()
    f["year"] = f.day.str[:4]
    f["gate"] = f.y60.rolling(20).std().shift(1)      # strictly pre-entry
    f["fade60"] = -np.sign(f.x) * f.y60; f["fade30"] = -np.sign(f.x) * f.y30
    out = {"cost": cost, "n": int(len(f)), "rho_x_y60": spearman(f.x, f.y60), "fade60_all": round(float(f.fade60.mean()), 2), "fade60_all_t": round(tstat(f.fade60), 2),
           "gate_by_year_median": {y: round(float(z.gate.median()), 1) for y, z in f.groupby("year")}}
    for X in Xs:
        on = f[f.gate >= X]; off = f[(f.gate < X) & np.isfinite(f.gate)]
        def summ(z, lab):
            v = z.fade60.to_numpy(); fg = four_groups(v, z.year.to_numpy(), cost, lab)
            srt = np.sort(v)[::-1]; tot = v.sum()
            fg["top10_share"] = float(srt[:10].sum() / tot) if tot > 0 else float("nan")
            fg["net_plus_tick"] = float(v.mean() - cost - tick) if len(v) else float("nan")
            fg["n_by_year"] = {y: int(len(w)) for y, w in z.groupby("year")}
            fg["volunits_by_year"] = {y: round(float(w.fade60.mean() / w.y60.std()), 3) for y, w in z.groupby("year") if len(w) > 5}
            fg["max_year_share"] = float(pd.Series(v).groupby(z.year.to_numpy()).sum().max() / tot) if tot > 0 else float("nan")
            fg["fade30_mean"] = float(z.fade30.mean())
            return {k: (round(b, 3) if isinstance(b, float) else b) for k, b in fg.items() if k in ("n", "gross_mean", "gross_median", "t", "net_mean", "win", "trimmed", "pos_years", "n_years", "by_year_mean", "n_by_year", "volunits_by_year", "top10_share", "net_plus_tick", "max_year_share", "fade30_mean", "top_trade")}
        out[f"gate_ge_{X}"] = summ(on, f"{root} gated >= {X}"); out[f"gate_lt_{X}"] = summ(off, f"{root} ungated < {X}")
        out[f"gate_ge_{X}"]["share_days_open"] = round(len(on) / max(1, len(on) + len(off)), 3)
    res[root] = out
    print("=====", root, "cost", cost, "rho", round(out["rho_x_y60"], 3), "fade60 all", out["fade60_all"], "t", out["fade60_all_t"], "gate median by yr", out["gate_by_year_median"])
    for X in Xs:
        print(f"  GATE >= {X}:", out[f"gate_ge_{X}"]); print(f"  gate <  {X}:", {k: v for k, v in out[f"gate_lt_{X}"].items() if k in ("n", "gross_mean", "t", "net_mean", "trimmed", "by_year_mean")})
json.dump(res, open(os.path.join(OUT, "cons_t10_volgate_settle.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

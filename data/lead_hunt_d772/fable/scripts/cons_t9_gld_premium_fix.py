"""T9: the GLD/IAU/SLV close premium to the futures-implied NAV as the AP creation/redemption proxy, signing the next
day's London PM auction window (gold, 15:00 London = 10:00 ET; silver 12:00 London is outside fut_day1m so SLV signs the
COMEX session open 09:00-10:00 as a weaker stand-in) and the fade after it.
 prem_T-1 = log(ETF close_T-1 / GC close at 15:59 ET on T-1) minus its trailing 20-day median (fee drag, basis drift).
 Gold legs on T (MGC $10/pt): A = P(fix) - P(fix-30) (into the fix), B = P(fix+30) - P(fix) (after). Sign chain: a
 PREMIUM -> APs create -> buy gold into the fix -> A up, B down. Scored: rho(prem, A), rho(prem, B); the signed trades
 sign(prem)*A and -sign(prem)*B on the top third of |prem| (walk-forward); year split; rotation null; DST placebo
 (the ET-clock 10:00 in mismatch weeks); the 11:30 ET clock placebo.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo
from cons_lib import *
NY = ZoneInfo("America/New_York"); LON = ZoneInfo("Europe/London")
etf = pd.read_csv(os.path.join(FIX, "etf_wide_daily_raw.csv.gz"), usecols=["timestamp", "symbol", "close"])
etf["day"] = etf.timestamp.str[:10]
etf = etf[(etf.day >= "2010-01-01") & (etf.day < SEAL)]
d = load_day1m(["GC", "SI"], lo="2010-06-07"); d = d[d.present & d.same_front]
P = {r: d[d.root == r].pivot_table(index="day", columns="bar", values="close").reindex(columns=range(420)).ffill(axis=1, limit=3) for r in ["GC", "SI"]}
res = {}
for sym, root, mult, cost in [("GLD", "GC", 10.0, micro_cost("GC")), ("IAU", "GC", 10.0, micro_cost("GC")), ("SLV", "SI", 1000.0, 8.0)]:
    e = etf[etf.symbol == sym].set_index("day")["close"]
    g = P[root]
    fut_close = g[418]   # bar 418 ends 15:59 ET
    j = pd.DataFrame({"etf": e}).join(fut_close.rename("fut"), how="inner").sort_index()
    j["lp"] = np.log(j.etf / j.fut)
    j["prem"] = j.lp - j.lp.rolling(20).median().shift(1)
    j["prem_bps"] = j.prem * 1e4
    days = list(g.index); pos = {dd: i for i, dd in enumerate(days)}
    rows = []
    for dd, r in j.iterrows():
        if dd not in pos or pos[dd] + 1 >= len(days) or not np.isfinite(r.prem):
            continue
        T = days[pos[dd] + 1]
        if root == "GC":
            t = pd.Timestamp(f"{T} 15:00", tz=LON).tz_convert(NY); fm = t.hour * 60 + t.minute
        else:
            fm = 9 * 60 + 30   # SLV stand-in: the COMEX 09:00->09:30 open as the 'window', 09:30->10:00 after
        row = g.loc[T]
        def pr(m):
            b = m - 541
            return row[b] if 0 <= b < 420 else np.nan
        rows.append({"T": T, "prem_bps": r.prem_bps, "fix_min": fm, "A": (pr(fm) - pr(fm - 30)) * mult, "B": (pr(fm + 30) - pr(fm)) * mult, "B60": (pr(fm + 60) - pr(fm)) * mult,
                     "A_pl": (pr(690) - pr(660)) * mult, "B_pl": (pr(720) - pr(690)) * mult})
    f = pd.DataFrame(rows).dropna(subset=["prem_bps", "A", "B"]); f["year"] = f["T"].str[:4]
    out = {"n": int(len(f)), "span": [f["T"].min(), f["T"].max()], "sd_prem_bps": float(f.prem_bps.std()), "sd_A": float(f.A.std()), "sd_B": float(f.B.std()), "cost": cost,
           "rho_prem_A": spearman(f.prem_bps, f.A), "rho_prem_B": spearman(f.prem_bps, f.B), "rho_prem_B60": spearman(f.prem_bps, f.B60.fillna(np.nan)),
           "rho_prem_A_placebo1130": spearman(f.prem_bps, f.A_pl), "rho_prem_B_placebo": spearman(f.prem_bps, f.B_pl),
           "rho_prem_A_by_year": {y: round(spearman(z.prem_bps, z.A), 3) for y, z in f.groupby("year")},
           "rho_prem_B_by_year": {y: round(spearman(z.prem_bps, z.B), 3) for y, z in f.groupby("year")}}
    s = f.prem_bps.abs().to_numpy(); thr = np.full(len(f), np.nan)
    for i in range(250, len(f)):
        thr[i] = np.quantile(s[i - 250:i], 2 / 3)
    sel = f[np.isfinite(thr) & (s > thr)]
    out["into_fix_signed_top3rd"] = four_groups((np.sign(sel.prem_bps) * sel.A).to_numpy(), sel.year.to_numpy(), cost, "sign(prem)*A")
    out["after_fix_fade_top3rd"] = four_groups((-np.sign(sel.prem_bps) * sel.B).to_numpy(), sel.year.to_numpy(), cost, "-sign(prem)*B")
    out["after_fix_fade_top3rd_60"] = four_groups((-np.sign(sel.prem_bps) * sel.B60).to_numpy(), sel.year.to_numpy(), cost, "-sign(prem)*B60")
    obs, p50, p95, p05, pv = rotation_p(f.prem_bps.to_numpy(), f.A.to_numpy(), spearman, n_off=600)
    out["rotation_A"] = {"obs": obs, "p05": p05, "p95": p95, "p": pv}
    obs, p50, p95, p05, pv = rotation_p(f.prem_bps.to_numpy(), f.B.to_numpy(), spearman, n_off=600)
    out["rotation_B"] = {"obs": obs, "p05": p05, "p95": p95, "p": pv}
    # persistence of the premium (is it a flow proxy at all?): autocorrelation of prem, and rho(prem_T-1, prem_T)
    out["prem_autocorr_1"] = float(f.prem_bps.autocorr(1))
    res[sym] = out
    gg = lambda q: {k: (round(v, 2) if isinstance(v, float) else v) for k, v in q.items() if k in ("n", "gross_mean", "gross_median", "t", "net_mean", "win", "trimmed", "pos_years", "n_years", "by_year_mean", "top_trade")}
    print("=====", sym, {k: (round(v, 3) if isinstance(v, float) else v) for k, v in out.items() if not isinstance(v, dict) or k.startswith("rot")})
    print("  rho A by year", out["rho_prem_A_by_year"]); print("  rho B by year", out["rho_prem_B_by_year"])
    print("  into-fix signed", gg(out["into_fix_signed_top3rd"])); print("  after-fix fade", gg(out["after_fix_fade_top3rd"])); print("  after-fix fade 60", gg(out["after_fix_fade_top3rd_60"]), flush=True)
json.dump(res, open(os.path.join(OUT, "cons_t9_gld_premium_fix.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

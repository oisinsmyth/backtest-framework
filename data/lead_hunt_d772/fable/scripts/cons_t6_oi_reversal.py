"""T6: does a day's move on FALLING front-month open interest (liquidation / short covering) revert the next day
session, while a move on RISING OI continues? Per-contract OI from fut_oi_expiry_cycles (last publication, ref session
T, usable T+1), day returns from fut_breadth_hourly (h09 open -> h15 close = the day session; the 'move' is the
settlement-to-settlement proxy: prev h15 close -> h15 close). Trade: next day's 09:00 -> 16:00 (h09_o -> h15_c), one
micro where a micro exists. Roots: CL NG GC SI HG 6E 6A 6B 6J ES NQ (ES/NQ OI from fut_open_interest_daily).
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from cons_lib import *

oi = pd.read_csv(os.path.join(FIX, "fut_oi_expiry_cycles.csv.gz"))
print(oi.columns.tolist(), oi.head(2).to_dict("records"), flush=True)
bh = pd.read_csv(os.path.join(FIX, "fut_breadth_hourly.csv.gz"), dtype={"day": str}, usecols=["root", "day", "contract", "same_front", "present", "h09_o", "h15_c", "h16_c"])
bh = bh[(bh.day >= "2016-01-04") & (bh.day < SEAL) & bh.present.astype(bool)]
# reference session column name guess
rcol = [c for c in oi.columns if "session" in c.lower() or "ref" in c.lower() or c == "day"][0]
ccol = [c for c in oi.columns if "contract" in c.lower() or "symbol" in c.lower()][0]
oi = oi.rename(columns={rcol: "day", ccol: "contract"})
oi["day"] = oi["day"].astype(str).str[:10]
res = {}
for root in ["CL", "NG", "GC", "SI", "HG", "6E", "6A", "6B", "6J", "ZN"]:
    b = bh[bh.root == root].sort_values("day").reset_index(drop=True)
    o = oi[oi.root == root][["day", "contract", "oi"]]
    m = b.merge(o, on=["day", "contract"], how="left")
    m["oi_prev"] = m.oi.shift(1); m["same_prev"] = m.same_front.astype(bool)
    m["doi"] = np.where(m.same_prev, (m.oi - m.oi_prev) / m.oi_prev, np.nan)
    m["ret"] = np.log(m.h15_c / m.h15_c.shift(1)); m.loc[~m.same_prev, "ret"] = np.nan
    m["nxt"] = (m.h15_c.shift(-1) - m.h09_o.shift(-1))      # next day's session move in price
    m["nxt_same"] = m.same_front.shift(-1).astype(bool)
    m = m[np.isfinite(m.doi) & np.isfinite(m.ret) & np.isfinite(m.nxt) & m.nxt_same].copy()
    mult = MULT.get(root, np.nan); cost = micro_cost(root)
    m["year"] = m.day.str[:4]
    m["nxt_usd"] = m.nxt * mult
    # cells: OI falling (bottom tercile of doi, walk-forward 250) vs rising (top tercile); sign of ret
    thr_lo = m.doi.rolling(250).quantile(1 / 3).shift(1); thr_hi = m.doi.rolling(250).quantile(2 / 3).shift(1)
    m["fall"] = m.doi < thr_lo; m["rise"] = m.doi > thr_hi
    big = m.ret.abs() > m.ret.abs().rolling(250).quantile(0.5).shift(1)
    out = {"n": int(len(m)), "cost": cost, "sd_nxt_usd": float(m.nxt_usd.std()),
           "rho_ret_nxt_all": spearman(m.ret, m.nxt), "rho_ret_nxt_fall": spearman(m.ret[m.fall], m.nxt[m.fall]), "rho_ret_nxt_rise": spearman(m.ret[m.rise], m.nxt[m.rise]),
           "rho_fall_by_year": {y: round(spearman(z.ret[z.fall], z.nxt[z.fall]), 3) for y, z in m.groupby("year")}}
    z = m[m.fall & big]; out["fade_fall_big"] = four_groups((-np.sign(z.ret) * z.nxt_usd).to_numpy(), z.year.to_numpy(), cost, f"{root} fade after fall-OI big move")
    z = m[m.rise & big]; out["follow_rise_big"] = four_groups((np.sign(z.ret) * z.nxt_usd).to_numpy(), z.year.to_numpy(), cost, f"{root} follow after rise-OI big move")
    z = m[big]; out["fade_all_big"] = four_groups((-np.sign(z.ret) * z.nxt_usd).to_numpy(), z.year.to_numpy(), cost, f"{root} fade after any big move")
    res[root] = out
    g = lambda x: {k: (round(v, 2) if isinstance(v, float) else v) for k, v in x.items() if k in ("n", "gross_mean", "gross_median", "t", "net_mean", "win", "trimmed", "pos_years", "n_years", "by_year_mean")}
    print(root, "n", out["n"], "rho all/fall/rise", round(out["rho_ret_nxt_all"], 3), round(out["rho_ret_nxt_fall"], 3), round(out["rho_ret_nxt_rise"], 3), "sd_nxt", round(out["sd_nxt_usd"], 1), flush=True)
    print("   fade_fall_big", g(out["fade_fall_big"])); print("   follow_rise_big", g(out["follow_rise_big"])); print("   fade_all_big", g(out["fade_all_big"]), flush=True)
json.dump(res, open(os.path.join(OUT, "cons_t6_oi_reversal.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

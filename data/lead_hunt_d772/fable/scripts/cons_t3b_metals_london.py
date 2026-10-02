"""T3b: (i) HG unconditional directional legs around LME ring 2 (the Fideres 'pre-official dip'): short 12:05->12:35 London,
long 12:35->13:05 / 13:35; by year, t. (ii) HG London-morning reversion dose: fade at 11:00 London by decile of |x| at
30/60/90-min holds. (iii) SI at the LBMA silver price (12:00 London) and GC at the LBMA AM auction (10:30 London), with
placebos (11:00, 15:00 London) -- same construction as T3. One micro: MHG $2500/pt, SIL $1000/pt, MGC $10/pt.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo
from cons_lib import *
LON = ZoneInfo("Europe/London")

def load_globex(file, root):
    parts = []
    for ch in pd.read_csv(os.path.join(FIX, file), usecols=["root", "session", "et", "contract", "close", "volume"], chunksize=2_000_000, dtype={"session": str}):
        ch = ch[(ch.root == root) & (ch.session < SEAL) & (ch.session >= "2016-01-04")]
        parts.append(ch)
    h = pd.concat(parts, ignore_index=True)
    h["ts"] = pd.to_datetime(h.et).dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
    h = h[h.ts.notna()]; h["utc"] = h.ts.dt.tz_convert("UTC"); h = h.sort_values("utc")
    modal = h.groupby("session").contract.agg(lambda z: z.value_counts().index[0])
    h = h[h.contract.to_numpy() == h.session.map(modal).to_numpy()]
    ser = pd.Series(h.close.to_numpy(), index=h.utc + pd.Timedelta(minutes=1)); ser = ser[~ser.index.duplicated(keep="last")]
    ser = ser.reindex(pd.date_range(ser.index.min(), ser.index.max(), freq="1min", tz="UTC")).ffill(limit=3)
    days = [s for s in sorted(h.session.unique()) if pd.Timestamp(s).dayofweek < 5]
    return ser, days

def price_at(ser, days, hhmm):
    t = pd.DatetimeIndex([pd.Timestamp(f"{d} {hhmm}", tz=LON) for d in days]).tz_convert("UTC")
    return ser.reindex(t).to_numpy()

def shift(c, m):
    hh, mm = map(int, c.split(":")); t = hh * 60 + mm + m
    return f"{t // 60:02d}:{t % 60:02d}"

res = {}
# ---------- (i) and (ii): HG
ser, days = load_globex("fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz", "HG")
yrs = np.array([d[:4] for d in days])
P = {c: price_at(ser, days, c) for c in ["11:00", "11:30", "12:05", "12:35", "13:05", "13:35", "14:05", "10:00", "10:30", "12:00", "12:30", "13:00", "13:30"]}
legs = {"short_1205_1235": -(P["12:35"] - P["12:05"]), "long_1235_1305": P["13:05"] - P["12:35"], "long_1235_1335": P["13:35"] - P["12:35"],
        "long_1235_1405": P["14:05"] - P["12:35"], "short_1200_1230": -(P["12:30"] - P["12:00"]), "long_1230_1300": P["13:00"] - P["12:30"], "long_1230_1330": P["13:30"] - P["12:30"],
        "placebo_short_1130_1200": -(P["12:00"] - P["11:30"]), "placebo_long_1100_1130": P["11:30"] - P["11:00"], "placebo_short_1030_1100": -(P["11:00"] - P["10:30"])}
o = {}
for k, v in legs.items():
    v = v * 2500
    o[k] = four_groups(v, yrs, micro_cost("HG"), k)
    o[k] = {a: (round(b, 3) if isinstance(b, float) else b) for a, b in o[k].items() if a in ("n", "gross_mean", "gross_median", "t", "nw_t", "net_mean", "win", "trimmed", "pos_years", "n_years", "by_year_mean", "top_trade")}
res["HG_directional_legs_usd_per_MHG"] = o
print("HG legs", fmt(o), flush=True)
# (ii) dose at 11:00 London: x = 10:30->11:00, y at 30/60/90
x = (P["11:00"] - P["10:30"]) * 2500
f = pd.DataFrame({"x": x, "y30": (P["11:30"] - P["11:00"]) * 2500, "y60": (P["12:00"] - P["11:00"]) * 2500, "y90": (P["12:30"] - P["11:00"]) * 2500, "year": yrs}).dropna()
f["dec"] = pd.qcut(f.x.abs().rank(method="first"), 5, labels=False)
res["HG_1100_fade_by_quintile_abs_x"] = {int(d): {"abs_x_lo": round(float(z.x.abs().min()), 1), "n": int(len(z)), **{h: round(float((-np.sign(z.x) * z[h]).mean()), 2) for h in ("y30", "y60", "y90")}, "t60": round(tstat((-np.sign(z.x) * z.y60).to_numpy()), 2)} for d, z in f.groupby("dec")}
top = f[f.x.abs() > f.x.abs().quantile(0.9)]
res["HG_1100_fade_top_decile"] = {h: four_groups((-np.sign(top.x) * top[h]).to_numpy(), top.year.to_numpy(), micro_cost("HG"), h) for h in ("y30", "y60", "y90")}
print("HG 1100 dose", fmt(res["HG_1100_fade_by_quintile_abs_x"]), flush=True)
# ---------- (iii) SI and GC
for root, file, mult, clocks in [("SI", "fut_opening_globex_1m_cl_ng_gc_si.csv.gz", 1000.0, {"lbma_silver_1200": "12:00", "placebo_1100": "11:00", "placebo_1500": "15:00", "placebo_1300": "13:00"}),
                                 ("GC", "fut_opening_globex_1m_cl_ng_gc_si.csv.gz", 10.0, {"lbma_am_1030": "10:30", "placebo_1130": "11:30", "placebo_0930": "09:30"})]:
    ser, days = load_globex(file, root); yrs = np.array([d[:4] for d in days]); cost = micro_cost(root)
    oo = {"cost": cost, "sessions": len(days)}
    for name, c in clocks.items():
        p0 = price_at(ser, days, shift(c, -30)); p1 = price_at(ser, days, c); p2 = price_at(ser, days, shift(c, 30)); p3 = price_at(ser, days, shift(c, 60))
        f = pd.DataFrame({"x": (p1 - p0) * mult, "y": (p2 - p1) * mult, "y60": (p3 - p1) * mult, "year": yrs}).dropna()
        r = {"n": int(len(f)), "mean_abs_x": round(float(f.x.abs().mean()), 1), "sd_y": round(float(f.y.std()), 1), "rho_x_y": round(spearman(f.x, f.y), 4), "rho_x_y60": round(spearman(f.x, f.y60), 4),
             "mean_x": round(float(f.x.mean()), 2), "t_x": round(tstat(f.x), 2), "mean_y": round(float(f.y.mean()), 2), "t_y": round(tstat(f.y), 2),
             "rho_by_year": {y_: round(spearman(z.x, z.y), 3) for y_, z in f.groupby("year")}}
        s = f.x.abs().to_numpy(); thr = np.full(len(f), np.nan)
        for i in range(250, len(f)):
            thr[i] = np.quantile(s[i - 250:i], 2 / 3)
        sel = f[np.isfinite(thr) & (s > thr)]
        for h in ("y", "y60"):
            fg = four_groups((-np.sign(sel.x) * sel[h]).to_numpy(), sel.year.to_numpy(), cost, f"{root} {name} fade {h}")
            r["fade_" + h] = {a: (round(b, 3) if isinstance(b, float) else b) for a, b in fg.items() if a in ("n", "gross_mean", "gross_median", "t", "net_mean", "win", "trimmed", "pos_years", "n_years", "by_year_mean", "top_trade")}
        obs, p50, p95, p05, pv = rotation_p(f.x.to_numpy(), f.y.to_numpy(), spearman)
        r["rotation"] = {"obs": round(obs, 4), "p05": round(p05, 4), "p95": round(p95, 4), "p": pv}
        oo[name] = r
        print(root, name, fmt(r), flush=True)
    res[root] = oo
json.dump(res, open(os.path.join(OUT, "cons_t3b_metals_london.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

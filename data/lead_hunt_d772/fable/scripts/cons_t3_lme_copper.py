"""Premise test T3: COMEX copper (HG, one MHG = $2500/pt) around the LME benchmark clocks, London time via zoneinfo.
Clocks (London): Ring 2 copper 12:30-12:35 (the official price is set from it, published ~12:50-13:00); LME Close 17:00
(closing prices 16:35-17:00 rings). Placebos: 11:00 and 15:00 London. Also the US 08:30 ET data clock is avoided.
x = P(c) - P(c-30m), y = P(c+30m) - P(c), where c is the clock; also y2 to c+60m. Fill at P(c).
Data: fut_opening_globex_1m_ho_rb_bz_hg_pl (HG rows, all Globex minutes, sessions 2015-09 .. 2025-02) cut < 2024.
"""
import sys, os, json, gzip
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo
from cons_lib import *

p = os.path.join(FIX, "fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz")
parts = []
for ch in pd.read_csv(p, usecols=["root", "session", "et", "contract", "close", "volume"], chunksize=2_000_000, dtype={"session": str}):
    ch = ch[(ch.root == "HG") & (ch.session < SEAL) & (ch.session >= "2016-01-04")]
    parts.append(ch)
h = pd.concat(parts, ignore_index=True)
h["ts"] = pd.to_datetime(h.et).dt.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT")
h = h[h.ts.notna()]
h["utc"] = h.ts.dt.tz_convert("UTC")
h = h.sort_values("utc")
# per session, one contract (the front): keep rows with the session's modal contract
modal = h.groupby("session").contract.agg(lambda z: z.value_counts().index[0])
h = h[h.contract.to_numpy() == h.session.map(modal).to_numpy()]
print("HG minutes", len(h), h.session.min(), h.session.max(), flush=True)
# minute series keyed by UTC minute: P(t) = close of the bar STARTING at t-1 (ending at t); ffill up to 3 min
ser = pd.Series(h.close.to_numpy(), index=h.utc + pd.Timedelta(minutes=1))
ser = ser[~ser.index.duplicated(keep="last")]
full = pd.date_range(ser.index.min(), ser.index.max(), freq="1min", tz="UTC")
ser = ser.reindex(full).ffill(limit=3)
LON = ZoneInfo("Europe/London")

def price_at(days, hhmm):
    # London-clock hhmm on each session date -> UTC minute -> price
    t = pd.DatetimeIndex([pd.Timestamp(f"{d} {hhmm}", tz=LON) for d in days]).tz_convert("UTC")
    return ser.reindex(t).to_numpy(), t

sessions = sorted(h.session.unique())
days = [s for s in sessions if pd.Timestamp(s).dayofweek < 5]
res = {"cost": micro_cost("HG"), "sessions": len(days)}
CLOCKS = {"ring2_1235": "12:35", "official_1300": "13:00", "close_1700": "17:00", "placebo_1100": "11:00", "placebo_1500": "15:00", "placebo_1600": "16:00",
          "ring1_1205": "12:05"}
for name, c in CLOCKS.items():
    hh, mm = map(int, c.split(":"))
    def shift(m):
        t = hh * 60 + mm + m
        return f"{t // 60:02d}:{t % 60:02d}"
    p0, _ = price_at(days, shift(-30)); p1, _ = price_at(days, c); p2, _ = price_at(days, shift(30)); p3, _ = price_at(days, shift(60))
    p00, _ = price_at(days, shift(-60))
    f = pd.DataFrame({"day": days, "x": (p1 - p0) * 2500, "x60": (p1 - p00) * 2500, "y": (p2 - p1) * 2500, "y60": (p3 - p1) * 2500})
    f["year"] = f.day.str[:4]
    f = f[np.isfinite(f.x) & np.isfinite(f.y) & np.isfinite(f.y60)]
    o = {"n": int(len(f)), "mean_abs_x": float(f.x.abs().mean()), "sd_y": float(f.y.std()), "sd_y60": float(f.y60.std()),
         "rho_x_y": spearman(f.x, f.y), "rho_x_y60": spearman(f.x, f.y60), "rho_x60_y": spearman(f.x60, f.y),
         "rho_by_year": {y_: round(spearman(z.x, z.y), 3) for y_, z in f.groupby("year")},
         "mean_x": float(f.x.mean()), "t_mean_x": tstat(f.x), "mean_y": float(f.y.mean())}
    # walk-forward top-third |x| fade, hold 30 and 60
    s = f.x.abs().to_numpy(); thr = np.full(len(f), np.nan)
    for i in range(250, len(f)):
        thr[i] = np.quantile(s[i - 250:i], 2 / 3)
    sel = f[np.isfinite(thr) & (s > thr)]
    o["fade_top3rd_30"] = four_groups((-np.sign(sel.x) * sel.y).to_numpy(), sel.year.to_numpy(), micro_cost("HG"), f"{name} fade 30m")
    o["fade_top3rd_60"] = four_groups((-np.sign(sel.x) * sel.y60).to_numpy(), sel.year.to_numpy(), micro_cost("HG"), f"{name} fade 60m")
    obs, p50, p95, p05, pv = rotation_p(f.x.to_numpy(), f.y.to_numpy(), spearman)
    o["rotation_rho"] = {"obs": obs, "p05": p05, "p50": p50, "p95": p95, "p": pv}
    res[name] = o
    print(name, fmt({k: v for k, v in o.items() if k not in ("fade_top3rd_30", "fade_top3rd_60")}), flush=True)
    print(name, "fade30", fmt(o["fade_top3rd_30"]), flush=True)
json.dump(res, open(os.path.join(OUT, "cons_t3_lme_copper.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

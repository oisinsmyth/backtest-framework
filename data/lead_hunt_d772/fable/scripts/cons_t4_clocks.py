"""Premise tests T4 (fut_day1m, 09:00-15:59 ET, 2016-2023), one micro each:
 D1  6E daily WM/R 16:00-London fix: x = P(fix)-P(fix-30), y = P(fix+30)-P(fix); placebo clock fix-120m; month-ends split.
 D2  NG EIA Thursday 10:30 and CL EIA Wednesday 10:30: x = P(10:32)-P(10:30), y = P(11:00)-P(10:32).
 D3  Index-roll days (BD5-BD10 of the month, per-root CME calendar) at the settlement window: x = P(end)-P(end-30),
     y = P(end+30)-P(end); CL/NG end 14:30, HG 13:00, GC 13:30, SI 13:25; roll vs non-roll.
 D4  6J Tokyo fix (09:55 JST) from the hourly breadth fixture: pre-hour vs post-hour, gotobi vs other days (crude).
"""
import sys, os, json, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo
from cons_lib import *

NY = ZoneInfo("America/New_York"); LON = ZoneInfo("Europe/London")
ROOTS = ["6E", "NG", "CL", "HG", "GC", "SI"]
d = load_day1m(ROOTS)
d = d[d.present & d.same_front]
P = {}
for r in ROOTS:
    x = d[d.root == r]
    piv = x.pivot_table(index="day", columns="bar", values="close").reindex(columns=range(420)).ffill(axis=1, limit=3)
    P[r] = piv
    print(r, piv.shape, flush=True)

def pr(root, days, minute_et):
    """P(t) for ET minute-of-day t (int or per-day array) = close of bar t-1 (bar b covers minute 540+b)."""
    piv = P[root].reindex(days)
    if np.isscalar(minute_et):
        b = minute_et - 540 - 1
        return piv[b].to_numpy() if 0 <= b < 420 else np.full(len(days), np.nan)
    out = np.full(len(days), np.nan)
    arr = piv.to_numpy()
    for i, m in enumerate(minute_et):
        b = int(m) - 540 - 1
        if 0 <= b < 420:
            out[i] = arr[i, b]
    return out

res = {}
# ---------------- D1: 6E daily fix
days = list(P["6E"].index)
fix_et = []
for dd in days:
    t = pd.Timestamp(f"{dd} 16:00", tz=LON).tz_convert(NY)
    fix_et.append(t.hour * 60 + t.minute)
fix_et = np.array(fix_et)
o = {"cost": micro_cost("6E"), "fix_et_minutes_counts": {str(k): int(v) for k, v in pd.Series(fix_et).value_counts().items()}}
for name, (dx, dy) in {"fix": (0, 0), "placebo_m120": (-120, -120)}.items():
    x = (pr("6E", days, fix_et + dx) - pr("6E", days, fix_et + dx - 30)) * 12500
    y = (pr("6E", days, fix_et + dy + 30) - pr("6E", days, fix_et + dy)) * 12500
    x15 = (pr("6E", days, fix_et + dx) - pr("6E", days, fix_et + dx - 15)) * 12500
    f = pd.DataFrame({"day": days, "x": x, "x15": x15, "y": y}).dropna()
    f["year"] = f.day.str[:4]
    f["month_end"] = [pd.Timestamp(a).is_month_end or (pd.Timestamp(b) .month != pd.Timestamp(a).month) for a, b in zip(f.day, list(f.day[1:]) + [f.day.iloc[-1]])]
    oo = {"n": int(len(f)), "mean_abs_x": float(f.x.abs().mean()), "sd_y": float(f.y.std()), "rho_x_y": spearman(f.x, f.y), "rho_x15_y": spearman(f.x15, f.y),
          "rho_by_year": {y_: round(spearman(z.x, z.y), 3) for y_, z in f.groupby("year")}}
    s = f.x.abs().to_numpy(); thr = np.full(len(f), np.nan)
    for i in range(250, len(f)):
        thr[i] = np.quantile(s[i - 250:i], 2 / 3)
    sel = f[np.isfinite(thr) & (s > thr)]
    oo["fade_top3rd"] = four_groups((-np.sign(sel.x) * sel.y).to_numpy(), sel.year.to_numpy(), micro_cost("6E"), f"6E {name} fade")
    me = f[f.month_end]
    oo["month_end_fade_all"] = four_groups((-np.sign(me.x) * me.y).to_numpy(), me.year.to_numpy(), micro_cost("6E"), "month-end fade (all)")
    obs, p50, p95, p05, pv = rotation_p(f.x.to_numpy(), f.y.to_numpy(), spearman)
    oo["rotation_rho"] = {"obs": obs, "p05": p05, "p50": p50, "p95": p95, "p": pv}
    o[name] = oo
res["D1_6E_daily_fix"] = o
print("D1", fmt(o), flush=True)

# ---------------- D2: EIA releases
ev = pd.read_csv(os.path.join(WT, "data", "calendar", "events.csv"))
print(ev.columns.tolist(), ev.iloc[0].to_dict(), flush=True)
col_type = [c for c in ev.columns if "type" in c.lower() or "event" in c.lower() or "name" in c.lower()][0]
col_date = [c for c in ev.columns if "date" in c.lower()][0]
col_time = [c for c in ev.columns if "time" in c.lower() or "clock" in c.lower()]
ev["d"] = ev[col_date].astype(str).str[:10]
for root, key in [("NG", "EIA_NGSR"), ("CL", "EIA_WPSR")]:
    e = ev[ev[col_type].astype(str).str.upper().str.contains(key)]
    if col_time:
        e = e[e[col_time[0]].astype(str).str.contains("10:30")]
    days_e = [x for x in e.d.unique() if x in P[root].index and "2016-01-04" <= x < SEAL]
    others = [x for x in P[root].index if x not in set(e.d.unique())]
    out = {"cost": micro_cost(root), "n_events": len(days_e)}
    for label, dl in [("event", days_e), ("non_event", others)]:
        m = MULT[root]
        x = (pr(root, dl, 632) - pr(root, dl, 630)) * m          # 10:30 -> 10:32
        y = (pr(root, dl, 660) - pr(root, dl, 632)) * m          # 10:32 -> 11:00
        y2 = (pr(root, dl, 690) - pr(root, dl, 632)) * m         # to 11:30
        f = pd.DataFrame({"day": dl, "x": x, "y": y, "y2": y2}).dropna(); f["year"] = f.day.str[:4]
        oo = {"n": int(len(f)), "mean_abs_x": float(f.x.abs().mean()), "sd_y": float(f.y.std()), "rho_x_y": spearman(f.x, f.y), "rho_x_y2": spearman(f.x, f.y2),
              "rho_by_year": {y_: round(spearman(z.x, z.y), 3) for y_, z in f.groupby("year")}}
        s = f.x.abs().to_numpy(); thr = np.full(len(f), np.nan)
        k = 100 if label == "event" else 250
        for i in range(k, len(f)):
            thr[i] = np.quantile(s[i - k:i], 2 / 3)
        sel = f[np.isfinite(thr) & (s > thr)]
        oo["fade_top3rd_to_1100"] = four_groups((-np.sign(sel.x) * sel.y).to_numpy(), sel.year.to_numpy(), micro_cost(root), f"{root} {label} fade")
        oo["fade_all_to_1100"] = four_groups((-np.sign(f.x) * f.y).to_numpy(), f.year.to_numpy(), micro_cost(root), f"{root} {label} fade all")
        out[label] = oo
    res[f"D2_{root}_EIA"] = out
    print("D2", root, fmt(out), flush=True)

# ---------------- D3: roll days at the settlement window
cal = pd.read_csv(os.path.join(FIX, "cme_session_calendar.csv.gz"), dtype={"date": str})
dcol = [c for c in cal.columns if c in ("date", "day", "session", "et_date")][0]
cal = cal[cal.is_trading.astype(bool)]
cal["ym"] = cal[dcol].str[:7]
cal["bd"] = cal.groupby(["root", "ym"]).cumcount() + 1
WIN_END = {"CL": 14 * 60 + 30, "NG": 14 * 60 + 30, "HG": 13 * 60, "GC": 13 * 60 + 30, "SI": 13 * 60 + 25}
for root, end in WIN_END.items():
    c = cal[cal.root == root].set_index(dcol)["bd"]
    days_r = [x for x in P[root].index if x in c.index]
    bd = c.reindex(days_r).to_numpy()
    m = MULT[root]
    x = (pr(root, days_r, end) - pr(root, days_r, end - 30)) * m
    y = (pr(root, days_r, end + 30) - pr(root, days_r, end)) * m
    y60 = (pr(root, days_r, end + 60) - pr(root, days_r, end)) * m
    f = pd.DataFrame({"day": days_r, "bd": bd, "x": x, "y": y, "y60": y60}).dropna(); f["year"] = f.day.str[:4]
    f["roll"] = (f.bd >= 5) & (f.bd <= 10)
    f["jan"] = f.day.str[5:7] == "01"
    out = {"cost": micro_cost(root), "n": int(len(f)), "n_roll": int(f.roll.sum())}
    for label, z in [("roll", f[f.roll & ~f.jan]), ("non_roll", f[~f.roll]), ("roll_jan", f[f.roll & f.jan])]:
        oo = {"n": int(len(z)), "mean_x": float(z.x.mean()), "t_x": tstat(z.x), "mean_y": float(z.y.mean()), "t_y": tstat(z.y), "mean_y60": float(z.y60.mean()), "t_y60": tstat(z.y60),
              "rho_x_y": spearman(z.x, z.y), "rho_x_y60": spearman(z.x, z.y60), "sd_y": float(z.y.std()),
              "long_after_window_by_year": {y_: round(float(w.y.mean()), 2) for y_, w in z.groupby("year")}}
        oo["fade_all"] = four_groups((-np.sign(z.x) * z.y).to_numpy(), z.year.to_numpy(), micro_cost(root), f"{root} {label} fade")
        oo["fade_60"] = four_groups((-np.sign(z.x) * z.y60).to_numpy(), z.year.to_numpy(), micro_cost(root), f"{root} {label} fade 60")
        out[label] = oo
    res[f"D3_{root}_roll_settle"] = out
    print("D3", root, fmt(out), flush=True)

# ---------------- D4: 6J Tokyo fix, hourly (crude)
bh = pd.read_csv(os.path.join(FIX, "fut_breadth_hourly.csv.gz"), dtype={"day": str})
bh = bh[(bh.root == "6J") & (bh.day >= "2016-01-04") & (bh.day < SEAL) & bh.same_front.astype(bool)]
rows = []
for _, r in bh.iterrows():
    dd = r.day
    # fix at 09:55 JST on trade date dd (JST = UTC+9) -> ET the evening before
    t = pd.Timestamp(f"{dd} 09:55", tz="Asia/Tokyo").tz_convert(NY)
    hpre = t.hour  # the hour containing the fix: 19 (EST) or 20 (EDT); pre = that hour's o->c (ends 5 min after fix), post = next hour
    h1 = f"h{hpre:02d}"; h2 = f"h{(hpre + 1) % 24:02d}"
    try:
        xpre = (r[h1 + "_c"] - r[h1 + "_o"]) * MULT["6J"]; ypost = (r[h2 + "_c"] - r[h2 + "_o"]) * MULT["6J"]
    except KeyError:
        continue
    day_t = pd.Timestamp(dd)
    rows.append({"day": dd, "x": xpre, "y": ypost, "gotobi": day_t.day % 5 == 0 or (day_t.dayofweek == 4 and ((day_t + pd.Timedelta(days=1)).day % 5 == 0 or (day_t + pd.Timedelta(days=2)).day % 5 == 0)), "year": dd[:4]})
f = pd.DataFrame(rows).dropna()
out = {"n": int(len(f)), "note": "x = 6J move (USD per JPY, $ per MJY) over the ET hour containing the 09:55 JST fix; y = next hour. 6J UP = JPY up = USDJPY DOWN. Importer USD buying -> 6J down into the fix, up after.",
       "all": {"n": int(len(f)), "mean_x": float(f.x.mean()), "t_x": tstat(f.x), "mean_y": float(f.y.mean()), "t_y": tstat(f.y), "rho_x_y": spearman(f.x, f.y), "sd_y": float(f.y.std())},
       "gotobi": {"n": int(f.gotobi.sum()), "mean_x": float(f[f.gotobi].x.mean()), "t_x": tstat(f[f.gotobi].x), "mean_y": float(f[f.gotobi].y.mean()), "t_y": tstat(f[f.gotobi].y), "rho_x_y": spearman(f[f.gotobi].x, f[f.gotobi].y)},
       "non_gotobi": {"n": int((~f.gotobi).sum()), "mean_x": float(f[~f.gotobi].x.mean()), "t_x": tstat(f[~f.gotobi].x), "mean_y": float(f[~f.gotobi].y.mean()), "t_y": tstat(f[~f.gotobi].y), "rho_x_y": spearman(f[~f.gotobi].x, f[~f.gotobi].y)}}
out["fade_all"] = four_groups((-np.sign(f.x) * f.y).to_numpy(), f.year.to_numpy(), 3.0 + 2 * 1.25, "6J fix-hour fade (MJY $, cost guess $5.50)")
res["D4_6J_tokyo_fix_hourly"] = out
print("D4", fmt(out), flush=True)
json.dump(res, open(os.path.join(OUT, "cons_t4_clocks.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

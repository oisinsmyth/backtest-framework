"""Premise test T1: intraday idiosyncratic (partner-residual) reversion in metals and energy, one micro.

For SI (partner GC), HG (partner GC), CL (partner BZ), GC (partner SI): at 30-minute grid points t inside the liquid
session, x_own = own 30-min move, x_p = partner's 30-min move, r = x_own - beta*x_p with beta from the trailing 60
sessions (pre-entry), y = own move over the next 30 min. Spearman rho of y with r, x_own, x_p; dollar fade of the
walk-forward top third of |r| and of |x_own| (the plain D499-style reversion, as the control).
In-sample 2016-01-04 .. 2023-12-29. P(t) = close of the bar ending at t. Fill at P(t) (optimistic by half a spread;
the cost line carries the crossing).
"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(__file__))
import numpy as np, pandas as pd
from cons_lib import *

PAIRS = [("SI", "GC", 30, 240), ("HG", "GC", 30, 240), ("HG", "SI", 30, 240), ("CL", "BZ", 30, 300), ("GC", "SI", 30, 240),
         ("NG", "CL", 30, 300)]
# grid: minutes-from-09:00 of the ENTRY t; windows [t-30, t] and [t, t+30]; last entry so that t+30 <= session end
ROOTS = sorted({a for p in PAIRS for a in p[:2]})
d = load_day1m(ROOTS)
d = d[d["present"] & d["same_front"]]
print("rows", len(d), "roots", d.root.unique(), flush=True)

# close grid: pivot per root -> day x bar close (bar b ends at minute 540+b+1); P(t) with t minutes after 09:00 = close of bar t-1
P = {}
for r in ROOTS:
    x = d[d.root == r]
    piv = x.pivot_table(index="day", columns="bar", values="close")
    piv = piv.reindex(columns=range(420))
    piv = piv.ffill(axis=1, limit=3)          # tolerate up to 3 missing minutes
    P[r] = piv
    print(r, piv.shape, flush=True)

res = {}
for own, part, step, end in PAIRS:
    days = P[own].index.intersection(P[part].index)
    po, pp = P[own].loc[days], P[part].loc[days]
    entries = list(range(60, end - 30 + 1, step))   # first entry 10:00 (window 09:30-10:00), stride 30 min
    rows = []
    for t in entries:
        a0, a1, a2 = po[t - 1 - 30].to_numpy(), po[t - 1].to_numpy(), po[t - 1 + 30].to_numpy()
        b0, b1 = pp[t - 1 - 30].to_numpy(), pp[t - 1].to_numpy()
        xo = np.log(a1 / a0); xp = np.log(b1 / b0); y = np.log(a2 / a1)
        rows.append(pd.DataFrame({"day": days, "t": t, "xo": xo, "xp": xp, "y": y, "p1": a1, "p2": a2}))
    f = pd.concat(rows).sort_values(["day", "t"]).reset_index(drop=True)
    f = f[np.isfinite(f.xo) & np.isfinite(f.xp) & np.isfinite(f.y)]
    # trailing beta from the previous 60 sessions' pairs (strictly before the day)
    udays = sorted(f.day.unique())
    beta = {}
    g = f.groupby("day")
    sxy = g.apply(lambda z: float((z.xo * z.xp).sum())); sxx = g.apply(lambda z: float((z.xp * z.xp).sum()))
    sxy = sxy.reindex(udays); sxx = sxx.reindex(udays)
    cxy = sxy.rolling(60).sum().shift(1); cxx = sxx.rolling(60).sum().shift(1)
    b = (cxy / cxx)
    f["beta"] = f.day.map(b)
    f = f[np.isfinite(f.beta)]
    f["r"] = f.xo - f.beta * f.xp
    f["year"] = f.day.str[:4]
    mult = MULT[own]
    # dollar move of the next 30 min per micro
    f["ydol"] = (f.p2 - f.p1) * mult
    out = {"pair": f"{own}~{part}", "n": int(len(f)), "sessions": int(f.day.nunique()), "beta_median": float(f.beta.median()),
           "rho_r_y": spearman(f.r, f.y), "rho_xo_y": spearman(f.xo, f.y), "rho_xp_y": spearman(f.xp, f.y),
           "rho_r_y_by_year": {y_: round(spearman(z.r, z.y), 3) for y_, z in f.groupby("year")},
           "rho_xo_y_by_year": {y_: round(spearman(z.xo, z.y), 3) for y_, z in f.groupby("year")},
           "sd_ydol": float(f.ydol.std()), "mean_abs_ydol": float(f.ydol.abs().mean()), "cost": micro_cost(own)}
    # walk-forward top third of |r| (threshold = 66.7th pct of |r| over the previous 250 sessions) -> fade
    for sig in ["r", "xo"]:
        s = f[sig].abs()
        thr = s.groupby(f.day).mean()  # placeholder; compute true quantile per day over trailing sessions
        dq = f.groupby("day")[sig].apply(lambda z: z.abs().to_numpy())
        # trailing-250-session 2/3 quantile
        q = {}
        arr = []
        dl = list(dq.index)
        for i, dd in enumerate(dl):
            if i >= 250:
                pool = np.concatenate(arr[-250:])
                q[dd] = np.quantile(pool, 2 / 3)
            arr.append(dq.iloc[i])
        f["thr_" + sig] = f.day.map(q)
        sel = f[np.isfinite(f["thr_" + sig]) & (s > f["thr_" + sig])]
        pnl = -np.sign(sel[sig]) * sel.ydol   # fade: short after an up move
        out["fade_top3rd_" + sig] = four_groups(pnl.to_numpy(), sel.year.to_numpy(), micro_cost(own), f"fade |{sig}| top third, {own}")
        # by entry clock
        out["fade_top3rd_" + sig + "_by_clock"] = {str(540 + t): round(float((-np.sign(z[sig]) * z.ydol).mean()), 2) for t, z in sel.groupby("t")}
    # increment: fade |r| top third restricted to rows where |xo| is NOT in its top third (the residual's own information)
    m = np.isfinite(f.thr_r) & (f.r.abs() > f.thr_r) & np.isfinite(f.thr_xo) & (f.xo.abs() <= f.thr_xo)
    sel = f[m]; pnl = -np.sign(sel.r) * sel.ydol
    out["fade_r_only_not_xo"] = four_groups(pnl.to_numpy(), sel.year.to_numpy(), micro_cost(own), "fade |r| top third where |xo| not top third")
    # rotation null of rho(r,y): rotate y by whole sessions (block) -- 300 offsets
    ys = f.groupby("day").y.apply(list)
    print(fmt(out), flush=True)
    res[out["pair"]] = out

json.dump(res, open(os.path.join(OUT, "cons_t1_resid_reversion.json"), "w", encoding="utf-8"), indent=1, default=str)
print("done")

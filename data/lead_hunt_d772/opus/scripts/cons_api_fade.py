"""Premise: the API crude-inventory survey (16:30 ET, the evening before EIA's 10:30 WPSR) moves CL in the thin
post-settlement book; the official EIA number corrects the noisy survey. API day = EIA_WPSR date - 1 calendar day
(holiday weeks shift both). m = close(16:59 bar) - close(16:29 bar) of API day D (session D).
Entry at the 18:05 close (opens session D+1, the EIA day: flat-by-16:10 compliant); exits 10:29 (pre-EIA), 11:00, 12:00.
Placebo: same construction on non-API days. Also MOVE m2 = close(16:34)-close(16:29). $/MCL. In-sample <= 2023."""
import numpy as np, pandas as pd
FX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
SEAL = "2024-01-01"; USD, RT = 100.0, 5.03
ev = pd.read_csv(EVT); ev = ev[(ev.datetime_et < SEAL) & (ev.event == "EIA_WPSR")]
api = set((pd.to_datetime(ev.datetime_et.str[:10]) - pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d"))
HMD = ["16:29", "16:34", "16:59"]; HMN = ["18:05"]; HMX = ["10:29", "11:00", "12:00"]
parts = []
for ch in pd.read_csv(f"{FX}\\fut_opening_globex_1m_cl_ng_gc_si.csv.gz", usecols=["root", "session", "et", "hhmm", "close"], chunksize=2_000_000):
    ch = ch[(ch.root == "CL") & (ch.session >= "2015-12-01") & (ch.session < SEAL) & ch.hhmm.isin(HMD + HMN + HMX)]
    sd = pd.to_datetime(ch.session); bd = pd.to_datetime(ch.et.str[:10])
    ch = ch[(ch.hhmm.isin(HMN) & (sd - bd).dt.days.between(1, 4)) | (~ch.hhmm.isin(HMN) & (bd == sd))]
    parts.append(ch)
d = pd.concat(parts); assert d.session.max() < SEAL
p = d.pivot_table(index="session", columns="hhmm", values="close", aggfunc="last").sort_index()
nx = p.shift(-1)  # next session (D+1)
for mlab, m in [("16:29->16:59", p["16:59"] - p["16:29"]), ("16:29->16:34", p["16:34"] - p["16:29"])]:
    isapi = pd.Series(p.index.isin(list(api)), index=p.index)
    thr = m.abs().where(isapi).rolling(100, min_periods=30).quantile(0.5).shift(1)
    for x in HMX:
        pnl = -np.sign(m) * (nx[x] - nx["18:05"]) * USD
        ok = pnl.notna() & (m != 0) & (p.index >= "2016-01-01")
        for lab, mm in [("API", ok & isapi), ("API top50", ok & isapi & (m.abs() >= thr)), ("PLACEBO", ok & ~isapi)]:
            q = pnl[mm]; yy = pd.to_datetime(q.index).year
            print(f"m {mlab} exit {x} {lab:10s}: n{len(q)} |m| ${(m.abs()*USD)[mm].mean():.1f} mean {q.mean():.2f} med {q.median():.2f} "
                  f"t {q.mean()/q.std(ddof=1)*np.sqrt(len(q)):.2f} ex20 {q[yy!=2020].mean():.2f} 16-19 {q[yy<2020].mean():.2f} "
                  f"20-23 {q[yy>=2020].mean():.2f} posyrs {(q.groupby(yy).mean()>0).sum()}/8")
    # follow the API move from 16:59 to 18:05 (the halt) -- descriptive only, not tradeable

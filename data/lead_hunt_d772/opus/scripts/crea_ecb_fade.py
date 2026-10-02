"""C20: Lead 1's mechanism on a second tier-1 family: ECB decisions (release 13:45 CET to 2022-07, 14:15 after; presser
45 min later) land while US cash equities are SHUT. (A) impulse = P(dec+5) - P(dec), enter P(dec+5), exit 11:00 ET.
(B) impulse = P(09:30) - P(dec), enter P(09:30), exit 11:00 (the cash-open repricing leg). Placebo: same ET clocks on
non-ECB Thursdays (non CPI/NFP). CPI/NFP-coincident ECB days dropped. ES/NQ/YM/RTY, 2016-2023 (seal)."""
import numpy as np, pandas as pd
from zoneinfo import ZoneInfo

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
CAL = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar"
SEAL = "2024-01-01"
ecb = pd.read_csv(f"{CAL}\\ecb_meetings.csv")
ev = pd.read_csv(f"{CAL}\\events.csv"); ev["d"] = ev.datetime_et.str[:10]
tier1 = set(ev[ev.event.isin(["CPI", "EMPSIT"])].d)
ecb = ecb[(ecb.date >= "2016-01-01") & (ecb.date < SEAL) & ~ecb.date.isin(tier1)]
CET, NY = ZoneInfo("Europe/Berlin"), ZoneInfo("America/New_York")
dec = {}
for _, r in ecb.iterrows():
    h, m = map(int, r.decision_release_time_cet.split(":"))
    t = pd.Timestamp(r.date + f" {h:02d}:{m:02d}", tz=CET).tz_convert(NY)
    dec[r.date] = t.hour * 60 + t.minute
print("ECB days", len(dec), "ET decision clocks", pd.Series(dec).value_counts().to_dict())
CASES = {"NQ": ("fut_opening_globex_1m.csv.gz", 2.0), "ES": ("fut_opening_globex_1m.csv.gz", 5.0),
         "YM": ("fut_opening_globex_1m_ym_rty.csv.gz", 0.5), "RTY": ("fut_opening_globex_1m_ym_rty.csv.gz", 5.0)}
cache = {}
for root, (fn, usd) in CASES.items():
    if fn not in cache:
        d = pd.read_csv(f"{FXD}\\{fn}", usecols=["root", "session", "hhmm", "close"])
        d = d[(d.session >= "2016-01-01") & (d.session < SEAL) & (d.hhmm >= "06:30") & (d.hhmm <= "11:00")]
        cache[fn] = d
    d = cache[fn][cache[fn].root == root]
    assert d.session.max() < SEAL
    d = d.assign(mm=d.hhmm.str[:2].astype(int) * 60 + d.hhmm.str[3:].astype(int))
    P = d.pivot_table(index="session", columns="mm", values="close", aggfunc="last").reindex(columns=range(390, 661)).ffill(axis=1)
    wd = pd.to_datetime(P.index).dayofweek
    res = {}
    for lab in ("A", "B"):
        rows_e, rows_p = [], []
        for s in P.index:
            is_e = s in dec
            if not is_e and not (wd[P.index.get_loc(s)] == 3 and s not in tier1):
                continue
            t = dec.get(s, 465)  # placebo Thursdays at 07:45
            row = P.loc[s]
            if lab == "A":
                x = row[t + 4] - row[t - 1]; ent = row[t + 4]
            else:
                x = row[569] - row[t - 1]; ent = row[569]
            y = row[659] - ent
            if np.isfinite(x) and np.isfinite(y) and x != 0:
                (rows_e if is_e else rows_p).append((s, -np.sign(x) * y * usd))
        fe = pd.Series(dict(rows_e)); fp = pd.Series(dict(rows_p))
        res[lab] = (f"ECB n{len(fe)} ${fe.mean():+.2f} med {fe.median():+.2f} t {fe.mean() / fe.std() * np.sqrt(len(fe)):+.2f} "
                    f"yrs>0 {(fe.groupby(fe.index.str[:4]).mean() > 0).sum()}/{fe.index.str[:4].nunique()} | placebo Thu n{len(fp)} ${fp.mean():+.2f}")
    print(f"{root}: (A dec+5 -> 11:00) {res['A']}\n      (B 09:30 -> 11:00) {res['B']}")

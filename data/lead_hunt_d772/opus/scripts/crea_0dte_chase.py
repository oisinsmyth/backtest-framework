"""C25 (declared before running): option-market plumbing / participant flow. Same-day-expiring (16:00 PM) ES-family options:
call share s_T = C/(C+P) of vol_to_1530 (midnight->15:29 volume, fut_es_options_eod). z = (s_T - mean_60)/sd_60 over prior
expiry sessions. Hypothesis: when same-day option buyers CHASE the day's move (call-heavy on an up day, put-heavy on a down day),
the move is crowd-driven and dealers' hedges of those short options pushed it; it reverts on T+1. Trade T+1 09:30->16:00
(day leg, outside the overnight closure), fading r_T = P(15:30,T) - P(09:30,T), only on chase days (|z| >= 0.84 in the move's
direction). Controls: 'counter' days (option flow against the move) and all expiry days. MES/MNQ/M2K/MYM. 2016-2023 (seal)."""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
SEAL = "2024-01-01"
o = pd.read_csv(f"{FXD}\\fut_es_options_eod.csv.gz", usecols=["session", "right", "expiry_date", "expiry_hhmm", "vol_to_1530"])
o = o[(o.session < SEAL) & (o.expiry_date == o.session) & (o.expiry_hhmm == "16:00")].dropna(subset=["vol_to_1530"])
assert o.session.max() < SEAL
v = o.pivot_table(index="session", columns="right", values="vol_to_1530", aggfunc="sum").fillna(0.0)
s = v["C"] / (v["C"] + v["P"])
s = s[(v["C"] + v["P"]) > 0]
z = (s - s.shift(1).rolling(60, min_periods=40).mean()) / s.shift(1).rolling(60, min_periods=40).std()
print("expiry sessions with volume:", len(s), s.index.min(), s.index.max(), "median call share", round(s.median(), 3))


def st(f, lab):
    f = f.dropna()
    yrs = f.groupby(f.index.str[:4]).mean()
    return f"{lab} n{len(f)} ${f.mean():+.2f} med {f.median():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f} yrs>0 {(yrs > 0).sum()}/{len(yrs)}"


for root, usd in [("NQ", 2.0), ("ES", 5.0), ("RTY", 5.0), ("YM", 0.5)]:
    d = pd.read_csv(f"{FXD}\\fut_{root}_rth_1m.csv.gz", usecols=["day", "hhmm", "close"])
    d = d[(d.day >= "2016-01-01") & (d.day < SEAL) & d.hhmm.isin({"09:30", "15:29", "15:59"})]
    assert d.day.max() < SEAL
    P = d.pivot_table(index="day", columns="hhmm", values="close", aggfunc="last").sort_index()
    r = P["15:29"] - P["09:30"]; N = P.shift(-1); y = (N["15:59"] - N["09:30"]) * usd
    zz = z.reindex(P.index)
    chase = ((r > 0) & (zz >= 0.84)) | ((r < 0) & (zz <= -0.84))
    counter = ((r > 0) & (zz <= -0.84)) | ((r < 0) & (zz >= 0.84))
    fade = -np.sign(r) * y
    print(f"{root}: " + st(fade[chase], "CHASE fade") + " | " + st(fade[counter], "counter fade") + " | " + st(fade[zz.notna()], "all expiry days fade"))

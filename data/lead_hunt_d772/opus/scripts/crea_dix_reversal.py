"""C24 (declared before running): the dark-pool index as a participant-side REVERSION predictor. DIX_T = SqueezeMetrics' dark-pool
short-volume ratio for day T (FINRA short volume, published the evening of T; we act on it only at T+1 09:30, the day leg,
which is NOT the closed overnight leg). Market makers short dark-pool prints to fill customer BUYING, so a high DIX on a DOWN
day says customers absorbed the decline; prediction: day T's move reverts on T+1. Construction: r_T = day-session move
(16:00 - 09:30) of T; z = (DIX_T - mean_60) / sd_60 of prior days; trade on T+1 09:30 -> 16:00 (also -> 11:00) the FADE of r_T,
only when DIX contradicts the move (r_T<0 & z>=+0.84 -> long; r_T>0 & z<=-0.84 -> short). Controls: the fade on all days, and
the fade when DIX agrees. Plus the unconditional DIX direction (long if z high). MES/MNQ/M2K/MYM, 2016-2023 (seal; licensed file
read in place, nothing per-date written)."""
import numpy as np, pandas as pd

FXD = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
DIX = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\squeezemetrics\DIX.csv"
SEAL = "2024-01-01"
x = pd.read_csv(DIX, usecols=["date", "dix"], dtype={"date": str})
x = x[x.date < SEAL].set_index("date").dix
z = (x - x.shift(1).rolling(60, min_periods=40).mean()) / x.shift(1).rolling(60, min_periods=40).std()
R = {"ES": 5.0, "NQ": 2.0, "RTY": 5.0, "YM": 0.5}


def st(f, lab):
    f = f.dropna()
    yrs = f.groupby(f.index.str[:4]).mean()
    return f"{lab} n{len(f)} ${f.mean():+.2f} med {f.median():+.2f} t {f.mean() / f.std() * np.sqrt(len(f)):+.2f} yrs>0 {(yrs > 0).sum()}/{len(yrs)}"


for root, usd in R.items():
    d = pd.read_csv(f"{FXD}\\fut_{root}_rth_1m.csv.gz", usecols=["day", "hhmm", "close"])
    d = d[(d.day >= "2016-01-01") & (d.day < SEAL) & d.hhmm.isin({"09:30", "10:59", "15:59"})]
    assert d.day.max() < SEAL
    P = d.pivot_table(index="day", columns="hhmm", values="close", aggfunc="last").sort_index()
    r = P["15:59"] - P["09:30"]
    N = P.shift(-1)
    yD = (N["15:59"] - N["09:30"]) * usd; yM = (N["10:59"] - N["09:30"]) * usd
    zz = z.reindex(P.index)
    fadeD = -np.sign(r) * yD; fadeM = -np.sign(r) * yM
    contra = ((r < 0) & (zz >= 0.84)) | ((r > 0) & (zz <= -0.84))
    agree = ((r < 0) & (zz <= -0.84)) | ((r > 0) & (zz >= 0.84))
    dirn = np.sign(zz.where(zz.abs() >= 0.84)) * yD
    print(f"{root}: " + st(fadeD[contra], "contra->16:00") + " | " + st(fadeM[contra], "contra->11:00") + " | " +
          st(fadeD[agree], "agree->16:00") + " | " + st(fadeD, "all-days fade->16:00") + " | " + st(dirn, "DIX-direction->16:00"))

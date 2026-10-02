"""Premise C1: does an ABNORMAL micro (retail) share of volume during a move predict that the move reverts?
Pairs: MES/ES, MNQ/NQ, M2K/RTY, MYM/YM, MGC/GC. 2019-05-06 .. 2023-12-29 (seal asserted).
Blocks of B minutes in RTH 09:30-15:59 ET. x = mini move over block (points); share = micro vol / (10 * mini vol)... we
use share = micro_vol / (micro_vol + 10*mini_vol)  [contract-notional share], z = log(share / median same-block share
over the PRIOR 20 sessions) -- pre-entry only. y = move over the next H minutes from block end. Fade pnl per micro =
-sign(x) * y * usd_pt. Reports the beta of y on x by z tercile and the fade $ in the top-z tercile with |x| >= q.
"""
import sys
import numpy as np, pandas as pd
from pathlib import Path

OUT = Path(__file__).resolve().parents[1] / "out"
df = pd.read_parquet(OUT / "crea_micro_mini_1m.parquet")
assert df["day"].max() < "2024-01-01"
PAIRS = {"ES": ("MES", 5.0, 4.42), "NQ": ("MNQ", 2.0, 4.07), "RTY": ("M2K", 5.0, 3.76), "YM": ("MYM", 0.5, 3.80),
         "GC": ("MGC", 10.0, 5.93)}
B = int(sys.argv[1]) if len(sys.argv) > 1 else 30
H = int(sys.argv[2]) if len(sys.argv) > 2 else 30
M0, M1 = 570, 960  # 09:30 .. 16:00 (GC: still RTH equity clock; GC liquid then)


def front(d):
    v = d.groupby(["day", "contract"])["volume"].sum().reset_index()
    f = v.sort_values(["day", "volume"]).groupby("day").tail(1)[["day", "contract"]]
    return d.merge(f, on=["day", "contract"])


res = []
for mini, (mic, usd, rt) in PAIRS.items():
    a = front(df[(df.root == mini) & (df.m >= M0) & (df.m < M1)])
    b = front(df[(df.root == mic) & (df.m >= M0) & (df.m < M1)])
    C = a.pivot(index="day", columns="m", values="close").reindex(columns=range(M0, M1)).ffill(axis=1)
    VA = a.pivot(index="day", columns="m", values="volume").reindex(columns=range(M0, M1)).fillna(0)
    VB = b.pivot(index="day", columns="m", values="volume").reindex(index=C.index, columns=range(M0, M1)).fillna(0)
    days = C.index[C.index >= "2019-05-06"]
    C, VA, VB = C.loc[days], VA.loc[days], VB.loc[days]
    nb = (M1 - M0) // B
    recs = []
    for k in range(nb):
        s0, s1 = M0 + k * B, M0 + (k + 1) * B  # block [s0, s1)
        if s1 + H > M1:
            break
        p0 = C[s0 - 1] if s0 - 1 in C.columns else C[s0].copy()  # price at s0 ~ close of bar s0-1 (first block: open proxy)
        if s0 == M0:
            p0 = C[s0]  # 09:30 bar close as start for the first block (conservative: skips the opening print)
        p1 = C[s1 - 1]
        p2 = C[s1 + H - 1]
        va = VA.loc[:, s0:s1 - 1].sum(axis=1)
        vb = VB.loc[:, s0:s1 - 1].sum(axis=1)
        share = vb / (vb + 10 * va)
        base = share.shift(1).rolling(20, min_periods=15).median()  # PRIOR sessions only
        recs.append(pd.DataFrame({"day": days, "blk": k, "x": p1 - p0, "y": p2 - p1, "share": share,
                                  "z": np.log(share / base), "vol": va}))
    R = pd.concat(recs).reset_index(drop=True).dropna()
    R = R[(R.x != 0)]
    R["root"] = mini
    # vol-normalise x by trailing same-block |x| (prior 20 sessions) for a size gate
    R = R.sort_values(["blk", "day"])
    R["ax_base"] = R.groupby("blk")["x"].transform(lambda s: s.abs().shift(1).rolling(20, min_periods=15).median())
    R["xn"] = R.x / R.ax_base
    R = R.dropna()
    R["zt"] = R.groupby("blk")["z"].transform(lambda s: pd.qcut(s.rank(method="first"), 3, labels=False))
    R["pnl"] = -np.sign(R.x) * R.y * usd
    res.append(R)
    print(f"\n== {mini}/{mic}  B={B} H={H}  n={len(R)}  median share={R.share.median():.3f}")
    for zt in [0, 1, 2]:
        S = R[R.zt == zt]
        beta = np.polyfit(S.x, S.y, 1)[0]
        rho = S[["x", "y"]].rank().corr().iloc[0, 1]
        big = S[S.xn.abs() >= 1.5]
        print(f"  z-tercile {zt}: n={len(S)} beta={beta:+.4f} rank-rho={rho:+.4f} | fade all ${S.pnl.mean():+.2f} "
              f"(med {S.pnl.median():+.2f}) | |xs|>=1.5 n={len(big)} fade ${big.pnl.mean():+.2f} med {big.pnl.median():+.2f}"
              f" t={big.pnl.mean() / big.pnl.std() * np.sqrt(len(big)):+.2f}")
    top = R[(R.zt == 2) & (R.xn.abs() >= 1.5)]
    print("  top-z & big: by year", top.groupby(top.day.str[:4])["pnl"].agg(["count", "mean"]).round(2).to_dict("index"))

A = pd.concat(res)
A.to_parquet(OUT / f"crea_micro_share_B{B}_H{H}.parquet", index=False)

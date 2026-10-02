"""Premise test B: cross-index residual reversion at 1-15 minutes on ES/NQ/YM/RTY (traded unhedged, one micro).

Predictor at minute t (pre-entry only): z = (sum of last K minutes of residual return of root i vs the other three) /
trailing-20-session sd of that K-minute residual sum. Hedge beta from the 20 prior sessions. Fade when |z| >= Z.
Outcome: own-price change over the next H minutes in dollars per micro (unhedged), entry at the close of bar t.
Also the 1-bar-delayed entry, the hedged outcome, the session-rotation null, year split, top trade.
In-sample 2018-01-02..2023-12-29 (RTY clean from 2018). SEAL asserted.

    python crea_03_cross_index_residual.py
"""
import json, sys
from pathlib import Path
import numpy as np
import pandas as pd

FIX = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/fixtures")
OUT = Path(__file__).resolve().parents[1] / "out"
ROOTS = ["ES", "NQ", "YM", "RTY"]
MULT = {"ES": 5.0, "NQ": 2.0, "YM": 0.5, "RTY": 5.0}          # $ per index point, one micro
COST = {"ES": 4.42, "NQ": 4.07, "YM": 3.80, "RTY": 3.76}      # round trip, D762's lines
LO, HI = "2018-01-02", "2023-12-29"
K, H, Z, LOOK = 15, 15, 2.0, 20
BAD = {"2020-03-09", "2020-03-12", "2020-03-16", "2020-03-18"}


def load():
    mats = {}
    days = None
    for r in ROOTS:
        df = pd.read_csv(FIX / f"fut_{r}_rth_1m.csv.gz", usecols=["day", "hhmm", "close", "volume"])
        df = df[(df["day"] >= LO) & (df["day"] <= HI) & (~df["day"].isin(BAD))]
        assert df["day"].max() < "2024-01-01", "SEAL"
        n = df.groupby("day").size()
        full = n[n == 390].index
        df = df[df["day"].isin(full)]
        piv = df.pivot(index="day", columns="hhmm", values="close")
        mats[r] = piv
        days = piv.index if days is None else days.intersection(piv.index)
    days = days.sort_values()
    C = np.stack([mats[r].loc[days].to_numpy(dtype=float) for r in ROOTS])  # [4, S, 390]
    hhmm = list(mats["ES"].columns)
    return C, np.array(days), hhmm


def main():
    C, days, hhmm = load()
    S = C.shape[1]
    print("sessions", S, days[0], days[-1], flush=True)
    R = np.diff(np.log(C), axis=2)                      # [4, S, 389] minute log returns (bar j+1 vs j)
    res = {}
    trades_all = []
    for i, root in enumerate(ROOTS):
        oth = np.mean(np.delete(R, i, axis=0), axis=0)   # [S, 389] equal-weighted other three
        ri = R[i]
        # trailing beta over LOOK prior sessions (pooled minutes), pre-entry
        beta = np.full(S, np.nan)
        for s in range(LOOK, S):
            x = oth[s - LOOK:s].ravel(); y = ri[s - LOOK:s].ravel()
            beta[s] = np.dot(x, y) / np.dot(x, x)
        u = ri - beta[:, None] * oth                      # residual minute returns
        # K-minute residual sum ending at minute index j (return index), cumulative
        cu = np.cumsum(u, axis=1)
        sumK = np.full_like(u, np.nan)
        sumK[:, K:] = cu[:, K:] - cu[:, :-K]
        # trailing sd from the prior LOOK sessions (non-overlapping K-blocks)
        sd = np.full(S, np.nan)
        for s in range(LOOK, S):
            blk = sumK[s - LOOK:s, K::K]
            sd[s] = np.nanstd(blk)
        z = sumK / sd[:, None]
        # forward own return over H minutes (log) and forward residual; outcome index j -> price at close index j+1
        # return index j corresponds to price index j+1 (close of bar j+1). Entry at close index p = j+1; exit p+H.
        P = C[i]
        fwd = np.full_like(u, np.nan); fwd_res = np.full_like(u, np.nan); fwd_d1 = np.full_like(u, np.nan)
        # own dollar move: P[p+H]-P[p]
        for j in range(K, 389 - H - 1):
            p = j + 1
            fwd[:, j] = (P[:, p + H] - P[:, p]) * MULT[root]
            fwd_d1[:, j] = (P[:, p + 1 + H] - P[:, p + 1]) * MULT[root]
            fwd_res[:, j] = np.sum(u[:, j + 1:j + 1 + H], axis=1) * 1e4   # bp, hedged
        valid = ~np.isnan(z) & ~np.isnan(fwd)
        # entry window: 09:45..15:30 (price index p from 15 to 360)
        jj = np.arange(389)
        win = (jj >= K) & (jj + 1 <= 360)
        valid &= win[None, :]
        # correlations
        zz = z[valid]; ff = fwd[valid]; fr = fwd_res[valid]
        rho_own = np.corrcoef(zz, ff)[0, 1]; rho_res = np.corrcoef(zz, fr)[0, 1]
        # trades: fade when |z|>=Z, non-overlapping within session
        T = []
        for s in range(LOOK, S):
            j = K
            while j <= 359:
                if valid[s, j] and abs(z[s, j]) >= Z:
                    side = -np.sign(z[s, j])
                    T.append((s, j, side, side * fwd[s, j], side * fwd_d1[s, j], side * fwd_res[s, j], z[s, j]))
                    j += H + 1
                else:
                    j += 1
        T = pd.DataFrame(T, columns=["s", "j", "side", "gross", "gross_d1", "res_bp", "z"])
        T["day"] = days[T["s"].to_numpy()]; T["year"] = T["day"].str[:4]; T["hhmm"] = [hhmm[j + 1] for j in T["j"]]
        T["root"] = root
        g = T["gross"].to_numpy()
        # rotation null: outcome read from session s+k, same minute, same side
        rot = []
        for k in range(1, 201):
            s2 = (T["s"].to_numpy() + k) % S
            rot.append(np.nanmean(T["side"].to_numpy() * fwd[s2, T["j"].to_numpy()]))
        rot = np.array(rot)
        yr = T.groupby("year")["gross"].agg(["count", "mean", "sum"])
        top = T.loc[T["gross"].idxmax()]
        q = np.quantile(g, [0.01, 0.99])
        out = dict(root=root, n=len(T), per_year=len(T) / (S / 252), rho_z_own=rho_own, rho_z_res=rho_res,
                   gross_mean=g.mean(), gross_median=float(np.median(g)), gross_t=g.mean() / g.std() * np.sqrt(len(g)),
                   gross_d1_mean=T["gross_d1"].mean(), res_bp_mean=T["res_bp"].mean(), res_bp_t=T["res_bp"].mean() / T["res_bp"].std() * np.sqrt(len(T)),
                   net_mean=g.mean() - COST[root], cost=COST[root], win=float((g > 0).mean()),
                   trim_ex_top=g[g <= q[1]].mean(), trim_ex_bottom=g[g >= q[0]].mean(), trim_both=g[(g >= q[0]) & (g <= q[1])].mean(),
                   rot_p50=float(np.median(rot)), rot_p95=float(np.quantile(rot, 0.95)), rot_share_ge=float((rot >= g.mean()).mean()),
                   years=yr.round(2).to_dict("index"), top_trade=dict(day=top["day"], hhmm=top["hhmm"], side=int(top["side"]), gross=float(top["gross"]), z=float(top["z"])),
                   long_mean=T.loc[T["side"] > 0, "gross"].mean(), short_mean=T.loc[T["side"] < 0, "gross"].mean(),
                   sd_fwd_usd=float(np.nanstd(fwd[valid])))
        res[root] = out
        trades_all.append(T)
        print(json.dumps({k: v for k, v in out.items() if k != "years"}, default=float), flush=True)
        print(yr.to_string(), flush=True)
    # by |z| decile for ES: own fwd mean and residual fwd mean (dose-response), pooled
    (OUT / "crea_03_cross_index_residual.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    pd.concat(trades_all).to_csv(OUT / "crea_03_trades.csv", index=False)


if __name__ == "__main__":
    main()

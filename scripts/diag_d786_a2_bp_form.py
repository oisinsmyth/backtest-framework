"""Scratch formation look (in-sample, already read by D786; the principal: "Profile the bp form, then decide").
Family A in basis points, with the bar FIXED in bp so it moves with volatility, not with the index's price:
- sigma_bp: 20-session sd of daily log returns x 1e4, through the state's cut (L4 through S, the others through S-1);
- gross_bp: the trade's gross $ / (the cut session's close x $ per point) x 1e4;
- beta_bp: expanding through-origin slope of gross_bp on sigma_bp over EARLIER trades (>= 30);
- proj_bp = beta_bp x sigma_bp; take when proj_bp >= 2 x the book's median round trip in bp (one fixed number a book).
Reported per index book: take/skip and terciles, with and without 2020/2022, and the skip share by year."""
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

WT = Path("C:/Users/O/Desktop/Projects/Backtest Framework/.claude/worktrees/after-d674")
sys.path.insert(0, str(WT / "scripts"))
sys.path.insert(0, str(WT / "src"))
import diag_d786_abstention_oracle as A  # noqa: E402

OUT = WT / "data" / "diag_d786_a2_bp_form.json"


def stats(v):
    n = len(v)
    return {"n": int(n), "mean_net": round(float(v.mean()), 2) if n else None,
            "se": round(float(v.std(ddof=1) / math.sqrt(n)), 2) if n > 1 else None, "total": round(float(v.sum()), 0)}


def split(y, col):
    t, s = y.loc[y[col], "net"], y.loc[~y[col], "net"]
    sp = float(t.mean() - s.mean()) if len(t) and len(s) else float("nan")
    se = math.sqrt(t.var(ddof=1) / len(t) + s.var(ddof=1) / len(s)) if len(t) > 1 and len(s) > 1 else float("nan")
    return {"take": stats(t), "skip": stats(s), "spread": round(sp, 2), "z": round(sp / se, 2) if se == se and se > 0 else None}


def main():
    books, cost = A.load_books()
    closes = {r: A.daily_closes(r) for r in ("NQ", "RTY")}
    out = {}
    for b in ("D737", "NQ_F2", "C1", "D776", "L4"):
        c = closes[A.ROOT[b]]
        same = c["contract"] == c["contract"].shift(1)
        lr = np.log(c["close"] / c["close"].shift(1)).where(same)
        st = pd.DataFrame({"sigma_bp": lr.rolling(A.SIG_N, min_periods=A.SIG_N - 5).std() * 1e4, "px": c["close"]})
        o = A.at_lag(st, books[b].index, A.LAG[b])
        y = books[b].copy()
        y["sigma_bp"], y["px"] = o["sigma_bp"], o["px"]
        y["gross_bp"] = y["gross"] / (y["px"] * A.MULT[A.ROOT[b]]) * 1e4
        y["cost_bp"] = cost[b] / (y["px"] * A.MULT[A.ROOT[b]]) * 1e4
        y["proj_bp"] = A.beta_proj(y["gross_bp"].to_numpy(float), y["sigma_bp"].to_numpy(float))
        bar = 2 * float(y["cost_bp"].median())
        y = y[y["proj_bp"].notna()].copy()
        y["take"] = y["proj_bp"] >= bar
        y["year"] = y.index.str[:4]
        ex = y[~y["year"].isin(["2020", "2022"])]
        terc = pd.qcut(y["proj_bp"].rank(method="first"), 3, labels=["low", "mid", "high"])
        out[b] = {"bar_bp": round(bar, 3), "trades": int(len(y)), "all": split(y, "take"), "ex_2020_2022": split(ex, "take"),
                  "terciles": {k: stats(y.loc[terc == k, "net"]) for k in ("low", "mid", "high")},
                  "skip_share_by_year": (~y["take"]).groupby(y["year"]).mean().round(2).to_dict(),
                  "corr_proj_bp_with_sigma_bp": round(float(y["proj_bp"].corr(y["sigma_bp"])), 3)}
        a, e = out[b]["all"], out[b]["ex_2020_2022"]
        print(f"{b:6s} bar {bar:.2f}bp | take {a['take']['n']} {a['take']['mean_net']} / skip {a['skip']['n']} {a['skip']['mean_net']}"
              f" spread {a['spread']} z {a['z']} | ex20/22 spread {e['spread']} z {e['z']} | skip by year {out[b]['skip_share_by_year']}")
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

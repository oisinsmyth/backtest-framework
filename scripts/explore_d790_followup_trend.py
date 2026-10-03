"""D790 follow-up (looks taken AFTER seeing D790's run; disclosed): is the trend family about the open, or the session?

    python scripts/explore_d790_followup_trend.py

Decomposes D790's leads (the open stretching along x away from SMA200 / SMA50):
  1. the regime (above / below the SMA) x the open's direction (away from / toward the SMA): fade gross, taker and
     passive, and the session's own move y signed toward the SMA;
  2. rho(-dist, y) unconditionally: does the 09:31-15:00 session lean back toward the SMA whatever the open did?
  3. the leads' correlation with g's opposition (S = -sign(x) g, the debate's A1) and with g_US's (D786's candidate 2);
  4. long and short fades in the lead's top third.
In-sample 2016-2023; nothing on or after 2024-01-01 (D786's build). Writes data/explore_d790_followup_trend.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import stage0_d765_china_open as C  # noqa: E402
import stage0_d767_china_open_fade_filter as F7  # noqa: E402
import stage0_d786_china_open_five_filters as D86  # noqa: E402
import explore_d790_china_open_anatomy as A  # noqa: E402

OUT = REPO / "data" / "explore_d790_followup_trend.json"


def cell(g, m, cost):
    v = g[m & np.isfinite(g)]
    return {"n": int(len(v)), "mean_gross": round(float(v.mean()), 2) if len(v) else None,
            "mean_net": round(float(v.mean() - cost), 2) if len(v) else None, "t_gross": round(F7.tstat(v), 2)}


def main() -> int:
    D86.WORKERS = 6                                             # 14 readers ran out of memory here once
    B = D86.build()
    D86.reproduce(B)
    e = B["e"]
    R = B["roots"]["GC"]
    F = A.session_features(R, e)
    G = A.trend_features(R, B["sess"]["mgc"], e, F)
    x, y = e["x"].to_numpy(float), e["y"].to_numpy(float)
    sx = np.sign(x)
    gt = e["gross"].to_numpy(float)
    gp = np.where(e["filled"].to_numpy(bool), e["gross_p"].to_numpy(float), np.nan)
    cp = B["cost_p"]
    res = {}
    for n, col in ((200, "T1u_dist_sma200"), (50, "T2u_dist_sma50")):
        dist = G[col].to_numpy(float)
        above = dist > 0
        away = np.sign(dist) == sx                                 # the open moved further from the average
        ok = np.isfinite(dist)
        tbl = {}
        for rn, rm in (("above", above), ("below", ~above)):
            for dn, dm in (("open_away", away), ("open_toward", ~away)):
                m = ok & rm & dm
                tbl[f"{rn}_{dn}"] = {"taker": cell(gt, m, 5.93), "passive": cell(gp, m, cp),
                                     "mean_y_toward_sma_usd": round(float((-np.sign(dist[m]) * y[m] * 10).mean()), 2)}
        res[f"sma{n}"] = {"two_by_two": tbl,
                          "rho_minus_dist_with_y_unconditional": C.spearman(-dist, y),
                          "rho_minus_dist_with_x": C.spearman(-dist, x),
                          "share_above": float(above[ok].mean())}
    s_a1 = -sx * e["g"].to_numpy(float)
    s_gus = -sx * e["g_us"].to_numpy(float)
    for col in ("T1s_along_x_sma200", "T2s_along_x_sma50", "T3s_along_x_sma20", "T6s_ret20_along_x"):
        f = G[col].to_numpy(float)
        res[col] = {"rho_with_g_opposition_A1": C.spearman(f, s_a1), "rho_with_gus_opposition_c2": C.spearman(f, s_gus),
                    "rho_with_absx": C.spearman(f, np.abs(x))}
        sel = F7.wf_select(f)
        res[col]["walk_forward_third"] = {"taker": cell(gt, sel, 5.93), "passive": cell(gp, sel, cp),
                                          "long_fades_passive": cell(gp, sel & (sx < 0), cp),
                                          "short_fades_passive": cell(gp, sel & (sx > 0), cp),
                                          "years_passive_net": {yy: cell(gp, sel & (e["year"].to_numpy() == yy), cp)["mean_net"]
                                                                for yy in sorted(set(e["year"]))}}
    res["corr_T1s_T2s_T3s_T6s"] = pd.DataFrame({c: G[c] for c in ("T1s_along_x_sma200", "T2s_along_x_sma50",
                                                                  "T3s_along_x_sma20", "T6s_ret20_along_x")}).corr("spearman").round(3).to_dict()
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1, default=str)
    print(json.dumps(res, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())

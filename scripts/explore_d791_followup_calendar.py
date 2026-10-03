"""D791 follow-up (a look taken AFTER seeing D791's run; disclosed): is the walk-forward ridge the season again?

    uv run --no-sync python scripts/explore_d791_followup_calendar.py

Re-runs D791's walk-forward ridge with all features and without the calendar features (month sine and cosine,
weekday, the US clock), each against 500 shuffled-label runs (50 left the p95 too noisy: 0.049 against 0.060 on two seeds). Reports the passive top-third book, the month balance of
its picks, and its net in and out of Dec-Mar. Reads D791's feature cache only. Writes
data/explore_d791_followup_calendar.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import explore_d791_oracle_patterns as M  # noqa: E402

OUT = REPO / "data" / "explore_d791_followup_calendar.json"
CALENDAR = ("month_sin", "month_cos", "weekday", "est_clock")
WINTER = (12, 1, 2, 3)


def main() -> int:
    X = pd.read_csv(M.FEAT, dtype={"day": str, "year": str}, encoding="utf-8")
    with open(M.META, encoding="utf-8") as fh:
        cost = json.load(fh)["cost_p"]
    allf = [c for c in X.columns if c not in M.NON_FEATURES]
    oos = np.isin(X["year"].to_numpy(), M.TEST_YEARS)
    g = X["gross"].to_numpy(float)
    gp = X["gross_p"].to_numpy(float)
    filled = X["filled"].to_numpy(bool)
    mon = pd.to_datetime(X["day"]).dt.month.to_numpy()
    win = np.isin(mon, WINTER)
    out = {}
    for nm, fs in (("all_features", allf), ("no_calendar", [c for c in allf if c not in CALENDAR])):
        w = M.walk_forward(X, fs, "ridge")
        sp = M.spearman(w["pred"][oos], g[oos])
        nul = np.array([M.spearman(M.walk_forward(X, fs, "ridge", 5000 + i)["pred"][oos], g[oos]) for i in range(500)])
        bk = M.book(X, w["take"], cost)
        t = w["take"] & oos & filled
        pool = oos & filled
        ms = pd.Series(mon[t]).value_counts(normalize=True).reindex(range(1, 13), fill_value=0)
        ps = pd.Series(mon[pool]).value_counts(normalize=True).reindex(range(1, 13), fill_value=0)
        out[nm] = {"oos_rho": sp, "null_p95": float(np.quantile(nul, 0.95)), "rank": float((nul < sp).mean()),
                   "passive_book": bk["passive"], "taker_book": bk["taker"],
                   "month_gap_pp": float(100 * (ms - ps).abs().max()),
                   "decmar_share_selected_vs_pool": [float(win[t].mean()), float(win[pool].mean())],
                   "passive_mean_net_decmar": float((gp[t & win] - cost).mean()),
                   "passive_mean_net_aprnov": float((gp[t & ~win] - cost).mean()),
                   "passive_total_net_aprnov": float((gp[t & ~win] - cost).sum()),
                   "n_features": len(fs)}
        p = out[nm]["passive_book"]
        print(f"{nm}: OOS rho {sp:+.4f} (null p95 {out[nm]['null_p95']:+.4f}) | passive n {p['n']} net {p['mean_net']:+.2f} "
              f"t {p['t_net']:.2f} years {p['profitable_years']} | month gap {out[nm]['month_gap_pp']:.1f} | Dec-Mar share "
              f"{out[nm]['decmar_share_selected_vs_pool'][0]:.3f} vs {out[nm]['decmar_share_selected_vs_pool'][1]:.3f} | net Dec-Mar "
              f"{out[nm]['passive_mean_net_decmar']:+.2f} Apr-Nov {out[nm]['passive_mean_net_aprnov']:+.2f}", flush=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1, default=str)
    return 0


if __name__ == "__main__":
    sys.exit(main())

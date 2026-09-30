"""D719 post-hoc correction: the exit price against the official settlement, in TICKS (the runner divided the price gap
by the tick's DOLLAR value instead of its price size, so its 'share within 2 ticks' of 1.0 on every root is void).
Reported only; D719's gates never read it. In-sample, the same cache and code as the runner.

    uv run python scripts/diag_d719_exit_check_fix.py
Writes data/diag_d719_exit_check_fix.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage1_d719_commodity_settlement_f2 as R  # noqa: E402

OUT = REPO / "data" / "diag_d719_exit_check_fix.json"


def main() -> int:
    s = pd.read_csv(R.STRIP, dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    out = {}
    for r in R.ROOTS:
        L = R.load(r)
        cl = R.cost_lines(r)
        tick_pts = cl["full"]["tick_usd"] / cl["full"]["usd_per_point"]
        T, W = R.hm(R.W_END[r], -30), R.W_END[r]
        X = R.core(L["close"], L["open"], R.BAND_OPEN[r], T, W, cl["full"]["usd_per_point"], L["exclude"])
        F = R.M.f2_on(X)
        sr = s[(s["root"] == r) & (s["ref"] >= R.IN_FROM) & (s["ref"] <= R.IN_END)].set_index(["contract", "ref"])["settle"]
        sess = X.index.to_numpy(str)[F["window"]]
        px = X["P_exit"].to_numpy(float)[F["window"]]
        st = sr.reindex(list(zip(L["contract"].reindex(sess).to_numpy(str), sess))).to_numpy(float)
        ok = np.isfinite(st)
        dist = np.abs(px[ok] - st[ok]) / tick_pts
        out[r] = {"tick_points": tick_pts, "matched": int(ok.sum()), "unmatched": int((~ok).sum()),
                  "median_ticks": float(np.median(dist)), "p90_ticks": float(np.quantile(dist, 0.9)),
                  "share_within_2_ticks": float((dist <= 2 + 1e-9).mean()), "flag_below_0.8": bool((dist <= 2 + 1e-9).mean() < 0.8)}
        print(r, out[r])
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

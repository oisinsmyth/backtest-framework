"""D727 POST HOC (declared as such in the D727 result): is NQ's first-crossing book a new component, or the MACD arm /
NQ F2 again? Daily net correlation of D727's NQ first-crossing books (k 1.0, 1.5) with the admitted MACD arm (D669's
trade table on the cut fixture, via D720's build_arm) and NQ F2 (D716's in-sample book, via D720's build_f2), on the
common NQ sessions to 2023-12-29. Reported only; it changes no D727 reading.

    uv run python scripts/diag_d727_overlap.py --data-root <checkout>/data   # -> data/diag_d727_overlap.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402
import stage0_d727_trend_curve as T  # noqa: E402

OUT = REPO / "data" / "diag_d727_overlap.json"


def first_crossing_daily(pn: dict, ob: dict, k: float, usd_pt: float, cost: float) -> pd.Series:
    z = ob["z"]
    hit = np.abs(z) >= k
    first = np.where(hit.any(axis=1), hit.argmax(axis=1), -1)
    rows = np.arange(len(pn["days"]))
    side = np.where(first >= 0, np.sign(z[rows, np.clip(first, 0, None)]), 0.0)
    entry = ob["Pt"][rows, np.clip(first, 0, None)]
    net = np.where(side != 0, side * (ob["close"] - entry) * usd_pt - cost, 0.0)
    return pd.Series(net, index=pn["days"])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    import stage1_d711_f2_mechanism as M711
    cl = M711.cost_line("NQ")
    pn = T.load_root("NQ", a.data_root)
    ob = T.objects(pn)
    books = {f"first_k{k}": first_crossing_daily(pn, ob, k, float(cl["usd_per_point"]), float(cl["cost"]))
             for k in (1.0, 1.5)}
    arm, _ = Z.build_arm()
    f2, _ = Z.build_f2()
    cal = pd.Index(pn["days"])
    arm_d = arm.groupby("day")["net1"].sum().reindex(cal).fillna(0.0)
    f2_d = f2.groupby("day")["net1"].sum().reindex(cal).fillna(0.0)
    out = {"post_hoc": True, "sessions": int(len(cal)), "window": [str(cal[0]), str(cal[-1])], "rho": {}}
    for nm, s in books.items():
        out["rho"][nm] = {"macd_arm": float(np.corrcoef(s, arm_d)[0, 1]), "nq_f2": float(np.corrcoef(s, f2_d)[0, 1]),
                          "same_day_share_with_arm": float(((s != 0) & (arm_d != 0)).sum() / max(1, (s != 0).sum()))}
        comb = s + arm_d
        out["rho"][nm]["book_plus_arm_net_sharpe"] = Z.sharpe(comb.to_numpy())
        out["rho"][nm]["arm_alone_net_sharpe_on_this_calendar"] = Z.sharpe(arm_d.to_numpy())
    OUT.write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())

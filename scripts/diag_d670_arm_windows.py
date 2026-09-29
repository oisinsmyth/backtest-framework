"""D670 diagnostic, POST HOC and disclosed: where does D669's 92 % substitution come from, if the plain rule is flat?

    python scripts/diag_d670_arm_windows.py        # -> data/diag_d670_arm_windows.json

D669 found that the sign of the move since the prior 16:00 close (RON), placed on the admitted MACD arm's own trade
windows, earns 92 % of the arm's gross (NQ, 2016-01-04 -> 2023-12-29). D670 found the same sign traded plainly from
10:00 to 16:00 earns about 1 bp a trade. This splits the plain rule on the arm's own fixture and sessions by what the
arm did that day, to locate the gap. Same window as D669 (2016-2023, the arm's spent in-sample); nothing new is read.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from stage0_d669_macd_mechanism import (  # noqa: E402
    LAST_SEG, NSEG, load_panel, lookback_flat, session_sum, trade_table, tstat)

OUT = REPO / "data" / "diag_d670_arm_windows.json"
ENTRY_1000 = 15                                                   # decision at the h09 close, fill at the h10 open


def block(x: np.ndarray) -> dict:
    x = np.asarray(x, float)
    return {"sessions": int(len(x)), "mean_usd": float(x.mean()) if len(x) else float("nan"),
            "total_usd": float(x.sum()), "t": tstat(x) if len(x) > 2 else float("nan"),
            "hit": float((x > 0).mean()) if len(x) else float("nan")}


def main() -> int:
    pn = load_panel()
    n = len(pn["days"])
    t = trade_table(pn)
    lc = pn["series"]["log_close"]
    ron_flat = lookback_flat(lc, "on")
    ron = np.nan_to_num(ron_flat[pn["full_rows"] * NSEG + ENTRY_1000], nan=0.0)          # RON at 10:00, per session
    O, C = pn["O"], pn["C"]
    rule = ron * (C[:, LAST_SEG] - O[:, ENTRY_1000 + 1]) * pn["point_usd"]            # gross, $, 10:00 -> 16:00
    first = t.groupby("i").first()
    has1000 = np.zeros(n, bool)
    armdir = np.zeros(n)
    idx = first.index.to_numpy()
    has1000[idx] = first["entry_t"].to_numpy() == ENTRY_1000
    armdir[idx] = first["d"].to_numpy()
    traded = np.zeros(n, bool)
    traded[idx] = True
    agree = has1000 & (armdir == ron)
    # the arm's own gross on its sessions, and the 10:00 -> 16:00 part of the 10:00-entry trades
    arm_gross = session_sum(t, "g", n)
    out = {"note": "POST HOC, disclosed; NQ 2016-2023 on D669's hourly fixture; gross dollars at one MNQ",
           "plain_rule_all_sessions": block(rule[ron != 0]),
           "arm_enters_at_1000": block(rule[has1000 & (ron != 0)]),
           "arm_enters_at_1000_same_direction_as_RON": block(rule[agree]),
           "arm_enters_at_1000_opposite_direction": block(rule[has1000 & (armdir == -ron) & (ron != 0)]),
           "arm_enters_later_or_not_at_all": block(rule[~has1000 & (ron != 0)]),
           "arm_no_trade": block(rule[~traded & (ron != 0)]),
           "arm_own_gross_on_1000_entry_sessions": block(arm_gross[has1000]),
           "arm_own_gross_on_later_entry_sessions": block(arm_gross[traded & ~has1000]),
           "share_of_sessions_arm_enters_at_1000": float(has1000.mean())}
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    for k, v in out.items():
        print(k, v)
    return 0


if __name__ == "__main__":
    sys.exit(main())

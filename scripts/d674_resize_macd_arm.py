"""D674 -- resizing the admitted MACD arm after D669/D670/D673: at the micro floor, the size lever is the account.

    python scripts/d674_resize_macd_arm.py          # -> data/d674_resize_macd_arm.json

AN ANALYSIS of committed objects, not a study (as D505). No signal is chosen or sharpened. The principal ruled
"resize it" on 2026-09-29 after D669-D673 found the arm's Sharpe to be the top of its family (neighbourhood median
0.24 net) with no portable mechanism. One MNQ is the smallest contract that exists, so the arm's dollar risk per
day cannot fall; what can change is the account it trades in, which sets the drawdown barrier and the daily-loss cap
that one MNQ is measured against, and the expectation the book carries.

THE DECLARED RULE (written before any number below was computed):
  * expectation: Sharpe 0.24 (D669's neighbourhood median), with 0.72 (the admitted figure) and 0.00 beside it;
  * daily sigma: the arm's 2025-2026 sigma at one MNQ ($391 / $386, D504), the current price level;
  * for every plan in D386's list, at one MNQ: V (expected dollars paid out less fees, per evaluation), P(pass),
    P(paid), from D386's published-rules lifecycle model; and P3a (days beyond 2 % of the account a year) on the
    arm's own daily net 2016-2026 and 2025-2026 (a re-description of read data for a vehicle decision, as D504 did);
  * the RECOMMENDED plan maximises V at Sharpe 0.24 among plans whose P3a on 2025-2026 is <= 1.0, and V at 0.24 must
    be > 2 SE above zero; if no plan qualifies, the recommendation is that no account carries the arm at its
    re-estimated edge.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

from backtest_framework.validation.hurdle_p import p3  # noqa: E402

OUT = REPO / "data" / "d674_resize_macd_arm.json"
SHARPES = {"re_estimated_0.24": 0.24, "admitted_0.72": 0.7236, "zero": 0.0}
N_PATHS, DAYS = 8_000, 600


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


def arm_daily() -> pd.Series:
    """The frozen arm's daily net at one MNQ, 2016-01-04 onward (D504's build, D491's simulator)."""
    D484 = _load("d484c", "d484_offdiagonal_and_macd.py")
    D491 = _load("d491c", "d491_conditional_hold.py")
    D495 = _load("d495c", "d495_agree_confluence.py")
    D504 = _load("d504c", "d504_arm_full_history.py")
    meta = json.loads(D495.META.read_text(encoding="utf-8"))
    spec = json.loads(D484.SPECS.read_text(encoding="utf-8"))
    pk = D504.build(pd.read_csv(D495.FIX, encoding="utf-8"), meta, spec)
    days = np.asarray(pk["days"]).astype(str)
    m = days >= D504.USABLE_LO
    net, _ = D491.simulate(pk["O"][m], pk["C"][m], pk["AGREE"][m], pk["first"], D504.M_HOLD, pk["cost"], pk["tick_pts"])
    return pd.Series(net * pk["tick_usd"], index=days[m])


def main() -> int:
    d386 = _load("d386", "d386_full_lifecycle.py")
    daily = arm_daily()
    recent = daily[daily.index >= "2025-01-01"]
    sigma = float(recent.std(ddof=1))
    print(f"arm daily net: {len(daily)} sessions 2016+ (${daily.sum():,.0f}); 2025-2026 sigma ${sigma:.0f}")
    rows = []
    for p in d386.PLANS:
        r = {"plan": f"{p.firm} {p.size // 1000}k", "size": p.size, "fee_eval": p.fee_eval, "monthly": p.monthly,
             "target": p.target, "dd_fund": p.dd_fund, "kind_fund": p.kind_fund,
             "p3a_2016_2026": p3(daily.to_numpy(), account=float(p.size))["p3a_breaches_per_year"],
             "p3a_2025_2026": p3(recent.to_numpy(), account=float(p.size))["p3a_breaches_per_year"],
             "barrier_in_daily_sigma": p.dd_fund / sigma}
        for lab, s in SHARPES.items():
            sim = d386.simulate(p, s, sigma, n_paths=N_PATHS, days=DAYS)
            r[lab] = {k: float(sim[k]) for k in ("V", "V_se", "p_pass", "p_paid", "paid_mean", "fund_days_med")}
        rows.append(r)
        print(f"  {r['plan']:<28} fee {p.fee_eval:>6.0f}{'/mo' if p.monthly else '   '} dd {p.dd_fund:>5.0f} "
              f"({r['barrier_in_daily_sigma']:.1f} sd)  P3a {r['p3a_2025_2026']:.2f}/yr  "
              f"V@0.24 {r['re_estimated_0.24']['V']:+6.0f}+-{r['re_estimated_0.24']['V_se']:.0f}  "
              f"V@0.72 {r['admitted_0.72']['V']:+6.0f}  V@0 {r['zero']['V']:+6.0f}  "
              f"pass@0.24 {r['re_estimated_0.24']['p_pass']:.0%} paid@0.24 {r['re_estimated_0.24']['p_paid']:.0%}")
    ok = [r for r in rows if r["p3a_2025_2026"] <= 1.0
          and r["re_estimated_0.24"]["V"] > 2 * r["re_estimated_0.24"]["V_se"]]
    rec = max(ok, key=lambda r: r["re_estimated_0.24"]["V"]) if ok else None
    out = {"rule": "max V at Sharpe 0.24 among plans with P3a(2025-2026) <= 1.0 and V > 2 SE",
           "sigma_2025_2026": sigma, "sessions": int(len(daily)), "plans": rows,
           "qualifying": [r["plan"] for r in ok], "recommended": rec["plan"] if rec else None}
    OUT.write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    print(f"qualifying: {out['qualifying']}\nrecommended: {out['recommended']}\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

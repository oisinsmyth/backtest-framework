"""D445 -- what the Rapid floor-lock fork costs, since the documentation cannot close it.

    uv run python scripts/d445_floor_lock.py

D386's open item 4 asked whether MFFU's Rapid floor lock is automatic or purchased. The primary
sources were read (D445 record, section 1) and they CONTRADICT:

    help centre, Rapid 25k AND 50k   "Max Loss Lock at $100. Once your trailing Max Loss
                                      reaches $100, it locks there."          -> AUTOMATIC
    /plans/rapid                     "once your balance is +$100 above your starting balance
                                      AFTER YOUR FIRST PAYOUT, the floor locks and stops
                                      trailing upward permanently."           -> PURCHASED
    Terms of Service                  SILENT. "Drawdown" is defined once, as "Loss thresholds
                                      for the Account, including daily or trailing limits",
                                      and the lock is never specified.

So the fork cannot be settled from MFFU's own publications, and the binding document is the one
that does not address it. This runner does the next best thing: it prices the fork.

AUTOMATIC   lock_fund = dd + 100        the floor freezes the moment the trailing level is
                                        reached, whether or not a payout has been taken.
                                        This is what D386 and D440 have both been assuming.
PURCHASED   lock_fund = None,           the floor trails forever until a payout is taken, and
            post_payout_floor = +100    only then freezes. Strictly harsher.

Both are expressible in D386's existing Plan structure with no change to the simulator, which is
the reason this is a two-line study rather than a model rewrite.

NO HURDLE IS CLAIMED AND NO CANDIDATE IS SCORED. This is a MEASUREMENT of how much one
unresolved sentence of vendor documentation is worth, on the measured path D440 built.
"""

from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import d386_full_lifecycle as D386          # noqa: E402
import d440_lifecycle as D440               # noqa: E402

OUT = REPO / "data" / "d445_floor_lock.json"
N_PATHS, DAYS = 8_000, 600


def variants(plan):
    """The two readings, as Plan objects. Nothing else differs."""
    auto = plan                                   # lock_fund = dd + 100, as shipped
    purchased = dataclasses.replace(
        plan,
        lock_fund=None,                           # never freezes from trailing alone
        post_payout_floor=plan.fund_start + 100.0,  # freezes only once a payout is taken
    )
    return {"AUTOMATIC": auto, "PURCHASED": purchased}


def main() -> int:
    h = pd.read_csv(D440.HOLDS_CSV)
    base = [p for p in D386.PLANS if p.firm == "MFFU Rapid EOD" and p.size == 50_000][0]
    vs = variants(base)

    # the two readings must actually be different objects, or the study measures nothing
    assert vs["AUTOMATIC"].lock_fund is not None and vs["PURCHASED"].lock_fund is None
    assert vs["PURCHASED"].post_payout_floor == 100.0
    assert vs["AUTOMATIC"].post_payout_floor is None

    print("D445 -- pricing the Rapid floor-lock fork\n")
    print(f"  MFFU Rapid EOD 50K, measured path, {N_PATHS:,} paths, {DAYS} days\n")
    print(f"  {'sym':<5}{'rule':<8}{'reading':<11}{'V':>8}{'frac':>7}"
          f"{'fund_yr':>9}{'p_pass':>8}{'p_paid':>8}{'payouts':>9}")

    rows, best = [], {}
    for sym in D440.ODR.SYMBOLS:
        g = h[h["symbol"] == sym].reset_index(drop=True)
        for rule in ("static", "voltgt"):
            for name, plan in vs.items():
                cells = [D440.run_cell(g, plan, f, rule, "MEASURED", N_PATHS, DAYS)
                         for f in D386.RISK_FRACS]
                b = max(cells, key=lambda x: x["V"])
                best[(sym, rule, name)] = b
                rows += [dict(c, symbol=sym, rule=rule, reading=name) for c in cells]
                print(f"  {sym:<5}{rule:<8}{name:<11}{b['V']:>8,.0f}{100 * b['frac']:>6.1f}%"
                      f"{b['fund_days_mean'] / 252:>9.2f}{b['p_pass']:>8.3f}"
                      f"{b['p_paid']:>8.3f}{b['n_payouts_mean']:>9.2f}")

    print("\n  WHAT THE SENTENCE IS WORTH -- PURCHASED minus AUTOMATIC")
    print(f"  {'sym':<5}{'rule':<8}{'dV':>9}{'dV %':>9}{'d fund_yr':>11}{'d p_paid':>10}")
    for sym in D440.ODR.SYMBOLS:
        for rule in ("static", "voltgt"):
            a, p = best[(sym, rule, "AUTOMATIC")], best[(sym, rule, "PURCHASED")]
            dv = p["V"] - a["V"]
            pct = (dv / abs(a["V"]) * 100) if a["V"] else float("nan")
            print(f"  {sym:<5}{rule:<8}{dv:>+9,.0f}{pct:>+8.1f}%"
                  f"{(p['fund_days_mean'] - a['fund_days_mean']) / 252:>+11.2f}"
                  f"{p['p_paid'] - a['p_paid']:>+10.3f}")

    # ------------------------------------------------------------------------------------
    # THE INTERACTION, and it is the point. The fork can only bite on accounts that REACH the
    # lock. Under the measured path almost none do. Under D386's Gaussian -- the model that
    # raised the open item in the first place -- many more do, so the same sentence should be
    # worth more there. If it is, the two open items are not independent.
    # ------------------------------------------------------------------------------------
    print("\n  THE SAME FORK UNDER D386's GAUSSIAN, at the measured path's own mean and vol")
    print(f"  {'sym':<5}{'reading':<11}{'V':>8}{'p_paid':>9}{'payouts':>9}   (static sizing)")
    for sym in D440.ODR.SYMBOLS:
        g = h[h["symbol"] == sym].reset_index(drop=True)
        gv = {}
        for name, plan in vs.items():
            cells = [D440.run_cell(g, plan, f, "static", "GAUSS", N_PATHS, DAYS)
                     for f in D386.RISK_FRACS]
            b = max(cells, key=lambda x: x["V"])
            gv[name] = b
            rows += [dict(c, symbol=sym, rule="static", reading=name, provider="GAUSS")
                     for c in cells]
            print(f"  {sym:<5}{name:<11}{b['V']:>8,.0f}{b['p_paid']:>9.3f}"
                  f"{b['n_payouts_mean']:>9.2f}")
        d = gv["PURCHASED"]["V"] - gv["AUTOMATIC"]["V"]
        pct = (d / abs(gv["AUTOMATIC"]["V"]) * 100) if gv["AUTOMATIC"]["V"] else float("nan")
        print(f"  {'':<5}{'dV':<11}{d:>+8,.0f}{pct:>+8.1f}%")

    pd.DataFrame(rows).to_json(OUT, orient="records", indent=1)
    print(f"\nwrote {OUT.relative_to(REPO)}  ({len(rows)} cells)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

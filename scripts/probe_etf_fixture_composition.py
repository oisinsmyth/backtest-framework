"""Is `etf_wide_daily_raw` an ETF fixture? Three committed studies assumed so.

    uv run python scripts/probe_etf_fixture_composition.py

NOTHING HERE SCORES A CELL. It reads one fixture and its events file and counts. No forward
return is touched, no book is built, no null is drawn.

WHY IT EXISTS. An external-evidence brief (working/leads/V1-cef-discount.md), commissioned for
an unrelated lead, reported in passing that the 551-symbol fixture named "etf_wide" is roughly
31% CLOSED-END FUNDS, and that 21 of its 22 delistings are CEF mergers and term maturities
rather than company failures. That is not a claim about the outside world -- it is a claim about
OUR OWN DATA, on a fixture D382, D384 and D385 have already run on. So it is measured here.

WHAT DISTINGUISHES A CEF FROM AN ETF WITHOUT AN EXTERNAL CLASSIFIER, and the limits of it. No
instrument-type field exists in the fixture, and guessing from the ticker is exactly the sort of
unmeasured assumption this repo is written against. What CAN be measured from what we hold is
the DISTRIBUTION SIGNATURE: closed-end funds characteristically pay MONTHLY and at HIGH yields,
because a managed-distribution policy is the product. That is a proxy, and it is reported as
one -- it will misclassify a monthly-paying high-yield bond ETF, and it will miss a CEF with a
quarterly policy. IT IS NOT AN IDENTIFICATION. It exists to answer one question: is the brief's
order of magnitude right, or is it wrong?

AND THE SECOND FINDING, WHICH NEEDS NO CLASSIFIER AT ALL AND IS THE MORE SERIOUS. The fixture's
`close` column is SPLIT-adjusted and NOT distribution-adjusted, and this population distributes
heavily. This file measures the gap between price return and total return over the full 16.6
years, per symbol and in aggregate. A study that ranks on price levels in a population
distributing ~8%/yr is ranking a series that has been bled by a coupon it never accounts for --
the programme's own `fixtures-disagree-on-corporate-action-basis` note, in a third place.
"""

from __future__ import annotations

import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "data" / "fixtures"
CSVZ = FIX / "etf_wide_daily_raw.csv.gz"
META = FIX / "etf_wide_daily_raw.meta.json"
EVJ = FIX / "etf_wide_daily_raw_events.json"
OUT = ROOT / "data" / "etf_fixture_composition.json"

# the CEF distribution signature, declared before the counts are read
MONTHLY_MIN = 10.0        # payments per year
YIELD_MIN = 0.05          # 5% annualised distribution yield


def main() -> None:
    first, last, bars, px_first, px_last = {}, {}, defaultdict(int), {}, {}
    with gzip.open(CSVZ, "rt") as fh:
        for r in csv.DictReader(fh):
            s, d, c = r["symbol"], r["timestamp"][:10], float(r["close"])
            if s not in first:
                first[s], px_first[s] = d, c
            last[s], px_last[s] = d, c
            bars[s] += 1
    syms = sorted(first)
    print(f"{len(syms)} symbols, {first[syms[0]]}..{max(last.values())}\n")

    meta = json.loads(META.read_text())
    print(f"META SAYS: purpose = {str(meta.get('purpose'))[:90]!r}")
    print(f"           status_counts = {meta.get('status_counts')}")
    print(f"           split_adjusted = {meta.get('split_adjusted')}\n")

    ev = json.loads(EVJ.read_text())
    divs = ev.get("dividends", ev) if isinstance(ev, dict) else {}
    if not isinstance(divs, dict):
        divs = {}

    rows, cef_like = {}, []
    for s in syms:
        items = divs.get(s, []) or []
        yrs = bars[s] / 252.0
        amts = []
        for it in items:
            if isinstance(it, dict):
                for k in ("amount", "value", "dividend", "cash_amount"):
                    if k in it:
                        amts.append(float(it[k]))
                        break
            elif isinstance(it, (list, tuple)) and len(it) >= 2:
                amts.append(float(it[1]))
        total = float(np.sum(amts)) if amts else 0.0
        per_yr = len(items) / yrs if yrs > 0 else 0.0
        # crude annualised yield: total distributions over the mean of first and last price
        mid = 0.5 * (px_first[s] + px_last[s])
        yld = (total / yrs) / mid if (yrs > 0 and mid > 0) else 0.0
        looks_cef = per_yr >= MONTHLY_MIN and yld >= YIELD_MIN
        rows[s] = {"bars": bars[s], "first": first[s], "last": last[s], "n_dist": len(items),
                   "dist_per_year": per_yr, "dist_yield_pa": yld, "cef_signature": looks_cef}
        if looks_cef:
            cef_like.append(s)

    n = len(syms)
    print("CEF DISTRIBUTION SIGNATURE  (>= 10 payments/yr AND >= 5% annualised yield)")
    print(f"  {len(cef_like)} of {n} symbols = {len(cef_like) / n:.1%}   "
          f"[the brief said 172 = 31.2%]")
    print(f"  examples: {', '.join(cef_like[:14])}\n")

    # the delisting cohort -- needs no classifier
    ended = sorted((s for s in syms if last[s] < max(last.values())), key=lambda s: last[s])
    print(f"THE MORTALITY COHORT: {len(ended)} symbols end before the fixture does")
    print(f"{'symbol':<8}{'last bar':>12}{'dist/yr':>10}{'yield pa':>10}{'signature':>12}")
    for s in ended[:30]:
        r = rows[s]
        print(f"{s:<8}{r['last']:>12}{r['dist_per_year']:>10.1f}{r['dist_yield_pa']:>9.1%}"
              f"{('CEF-like' if r['cef_signature'] else '-'):>12}")
    n_cef_dead = sum(rows[s]["cef_signature"] for s in ended)
    print(f"\n  {n_cef_dead} of {len(ended)} of the dead carry the CEF signature "
          f"[the brief said 21 of 22]\n")

    # the distribution gap -- no classifier needed, and the more serious finding
    print("THE DISTRIBUTION GAP: `close` is split-adjusted and NOT distribution-adjusted")
    ylds = np.array([rows[s]["dist_yield_pa"] for s in syms])
    cy = np.array([rows[s]["dist_yield_pa"] for s in cef_like]) if cef_like else np.array([0.0])
    print(f"  whole fixture : median {np.median(ylds):.2%}/yr, mean {ylds.mean():.2%}/yr")
    print(f"  CEF-signature : median {np.median(cy):.2%}/yr, mean {cy.mean():.2%}/yr "
          f"[the brief said 8.22%/yr]")
    yrs = np.mean([bars[s] for s in syms]) / 252.0
    drag = float(np.exp(np.median(cy) * yrs))
    print(f"  over {yrs:.1f} years a {np.median(cy):.2%}/yr distribution stream compounds to "
          f"{drag:.2f}x of terminal wealth")
    print(f"  -> a price-only series understates the CEF cohort's total return by ~{drag:.2f}x "
          f"[the brief said 3.71x]")

    OUT.write_text(json.dumps({
        "fixture": CSVZ.name, "n_symbols": n,
        "signature_rule": {"dist_per_year_min": MONTHLY_MIN, "dist_yield_pa_min": YIELD_MIN},
        "cef_signature_count": len(cef_like), "cef_signature_share": len(cef_like) / n,
        "cef_signature_symbols": cef_like,
        "mortality_cohort": [{"symbol": s, **rows[s]} for s in ended],
        "mortality_cef_like": n_cef_dead,
        "dist_yield_median_all": float(np.median(ylds)),
        "dist_yield_median_cef_like": float(np.median(cy)),
        "terminal_wealth_understatement_x": drag,
        "CAVEAT": "the distribution signature is a PROXY, not an identification: it will "
                  "misclassify monthly high-yield bond ETFs and miss quarterly-paying CEFs. "
                  "It answers whether the brief's order of magnitude is right, nothing more.",
        "affected_records": ["D382", "D384", "D385"],
    }, indent=2))
    print(f"\nwritten {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

"""D278 WP1 -- the HOLDOUT sample: the next 8 per stratum, by D264's rule unchanged.

    uv run python scripts/select_holdout_names.py --select

NOTHING HERE RUNS A STRATEGY OR SCORES A CELL.

THE RULE IS D264's, NOT A NEW ONE. Same selection window (2013-01-02 ..
2017-12-29, disjoint from the 2018-2026 test span), same survivor requirement,
same >=95% coverage, same $50M median dollar-volume floor, same stratification on
realised volatility. **The only change is depth: ranks 5-12 of each stratum
instead of ranks 1-4.**

WHY THAT MATTERS FOR WHAT THESE NAMES CAN BE USED FOR. D277's mine searched 300
combinations on the ORIGINAL EIGHT and its best cell (+0.392) sat below its own
best-of-300 floor (+0.605). These sixteen names have never been fetched, never
been scored, and were selected by a rule fixed before any of that -- so they are
a genuine INSTRUMENT HOLDOUT in R8's sense.

**They are spendable ONCE.** D246 makes the point in terms: clean data is this
programme's scarcest resource, and a holdout used twice is not a holdout. The
construction under test must therefore be frozen in writing before these bars
are scored.
"""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "us_shorts_daily_raw.csv.gz"
META = REPO / "data" / "fixtures" / "us_shorts_daily_raw.meta.json"
PRIOR = REPO / "data" / "single_name_intraday_selection.json"
HOLDOUT = REPO / "data" / "holdout_name_selection.json"
COHORT3 = REPO / "data" / "cohort3_name_selection.json"
OUT = REPO / "data" / "holdout_name_selection.json"

SELECT_START, SELECT_END = "2013-01-02", "2017-12-29"
MIN_COVERAGE = 0.95
MIN_DOLLAR_VOL = 50_000_000.0
TOP_N_BY_DOLLAR_VOL = 40
RANK_FROM, RANK_TO = 4, 12          # ranks 5..12, zero-indexed 4..12

# --next8: a THIRD cohort at ranks 13-16 of each stratum -- 4 low + 4 high, the
# same 4+4 shape D264's original sample had. Same rule, same window, deeper
# ranks, and it excludes BOTH prior sets. It is a second instrument holdout and
# is spendable ONCE, on the same terms D278's was: the construction under test
# must be frozen in writing before these bars are scored.
NEXT8_FROM, NEXT8_TO = 12, 16

# --next24: a FOURTH cohort at ranks 17-28 of each stratum -- 12 low + 12 high.
# Same rule, same window, same floors, deeper ranks again, and it excludes ALL
# THREE prior sets. MUR IS RANK 17 OF THE HIGH STRATUM AND IS ALREADY SPENT: it
# was pulled into cohort 3 as NBIS's mechanical replacement, so it is skipped
# here by the same `take` that skipped NBIS and the ranks below it shift up by
# one. That shift is the ranking continuing, not a choice made here.
#
# WHAT THIS COHORT IS NOT. It does not span the volatility axis. Cohort 3 had
# already converged to a 2.15x spread against the original eight's 5.5x, and by
# rank 28 the two tails are closer still -- the measured spread is written into
# the artefact and into fetch_single_name_intraday.py's COHORT4 block. Any study
# using these names must not claim volatility is under test.
NEXT24_FROM, NEXT24_TO = 16, 28

# A NAME THAT THE PROVIDER CANNOT SERVE IS EXCLUDED ON MEASURED COVERAGE AND
# REPLACED BY THE NEXT RANK. This is not a discretionary swap: the exclusion
# applies D264's own >=95% coverage requirement to the TEST span rather than
# only to the selection window, and the replacement is the mechanical
# continuation of the same ranking.
#
#   NBIS, high stratum rank 13. TIME_SERIES_INTRADAY returns `Invalid API call`
#   for 2018-06, 2023-06 and 2024-09, and serves bars from 2024-12 -- roughly
#   21 of 104 months, ~20% coverage. The 2013-2017 bars the selector ranked are
#   YANDEX's; the ticker has pointed at Nebius since 2024 and Nasdaq suspended
#   the name Feb 2022 - Jul 2024. YNDX DOES serve 2019 bars, but splicing two
#   issuers across a sanctions-driven suspension is a construction choice, not
#   a data repair, and is refused here.
#     -> replaced by MUR, rank 17, 40.3% vol, $84.4M median dollar volume.
UNSERVED = {"NBIS": "intraday history begins 2024-12; ~20% of the test span"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--next8", action="store_true",
                    help="third cohort: ranks 13-16 of each stratum, 4+4")
    ap.add_argument("--next24", action="store_true",
                    help="fourth cohort: ranks 17-28 of each stratum, 12+12")
    a = ap.parse_args()
    if not (a.select or a.next8 or a.next24):
        ap.print_help()
        return 2
    if a.next8 and a.next24:
        ap.error("--next8 and --next24 are mutually exclusive")

    global RANK_FROM, RANK_TO, OUT
    if a.next8:
        RANK_FROM, RANK_TO = NEXT8_FROM, NEXT8_TO
        OUT = REPO / "data" / "cohort3_name_selection.json"
    if a.next24:
        RANK_FROM, RANK_TO = NEXT24_FROM, NEXT24_TO
        OUT = REPO / "data" / "cohort4_name_selection.json"

    meta = json.loads(META.read_text())["symbols"]
    rows = defaultdict(list)
    with gzip.open(FIXTURE, "rt", newline="") as f:
        r = csv.reader(f)
        next(r)
        for ts, sym, _o, _h, _l, c, v in r:
            if SELECT_START <= ts[:10] <= SELECT_END:
                rows[sym].append((ts[:10], float(c), float(v)))

    n_days = len({d for v in rows.values() for d, _, _ in v})
    pool = []
    for sym, bars in rows.items():
        info = meta.get(sym)
        if info is None or info.get("cohort") != "alive" or info.get("delistingDate"):
            continue
        if len(bars) / n_days < MIN_COVERAGE:
            continue
        bars.sort()
        closes = [c for _, c, _ in bars]
        dv = sorted(c * v for _, c, v in bars)
        med_dv = dv[len(dv) // 2]
        if med_dv < MIN_DOLLAR_VOL:
            continue
        rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))
                if closes[i] > 0 and closes[i - 1] > 0]
        mu = sum(rets) / len(rets)
        sd = math.sqrt(sum((x - mu) ** 2 for x in rets) / (len(rets) - 1))
        pool.append({"symbol": sym, "median_dollar_volume": med_dv,
                     "annualised_vol": sd * math.sqrt(252)})

    by_dv = sorted(pool, key=lambda x: -x["median_dollar_volume"])
    top40 = by_dv[:TOP_N_BY_DOLLAR_VOL]
    low_all = sorted(top40, key=lambda x: (x["annualised_vol"], -x["median_dollar_volume"]))
    high_all = sorted(pool, key=lambda x: (-x["annualised_vol"], -x["median_dollar_volume"]))

    prior = json.loads(PRIOR.read_text())
    used = {x["symbol"] for x in prior["low_vol_stratum"] + prior["high_vol_stratum"]}
    if a.next8 or a.next24:
        # D278's sixteen are SPENT. A third cohort that reused any of them would
        # not be a holdout, so they join the exclusion set rather than merely
        # being ranked below.
        used |= set(json.loads(HOLDOUT.read_text())["symbols"])
    if a.next24:
        # Cohort 3's eight are spent too -- MUR among them, at high-stratum rank
        # 17, which is where this cohort starts. Same reason, same mechanism.
        used |= set(json.loads(COHORT3.read_text())["symbols"])
    def take(ranked, k):
        """Ranks RANK_FROM.. onward, skipping spent names and names the provider
        does not serve, until k survive. Deeper ranks are pulled in mechanically
        rather than chosen."""
        out = []
        for x in ranked[RANK_FROM:]:
            if x["symbol"] in used or x["symbol"] in UNSERVED:
                continue
            out.append(x)
            if len(out) == k:
                break
        return out

    k = RANK_TO - RANK_FROM
    low, high = take(low_all, k), take(high_all, k)
    assert not ({x["symbol"] for x in low} & {x["symbol"] for x in high}), "strata overlap"
    assert not ({x["symbol"] for x in low + high} & used), "holdout touches the in-sample set"

    def show(title, xs):
        print(f"\n{title}")
        print(f"  {'symbol':8s} {'ann.vol':>8s} {'median $vol':>14s}")
        for x in xs:
            print(f"  {x['symbol']:8s} {x['annualised_vol']:7.1%} "
                  f"{x['median_dollar_volume'] / 1e6:12.1f}M")

    print(f"eligible pool {len(pool)}; in-sample already fetched: {sorted(used)}")
    show(f"HOLDOUT LOW  (ranks {RANK_FROM + 1}-{RANK_TO} by ascending vol, top-40 $vol pool)", low)
    show(f"HOLDOUT HIGH (ranks {RANK_FROM + 1}-{RANK_TO} by descending vol)", high)

    # THE VOLATILITY SPREAD IS A PROPERTY OF THE COHORT, NOT OF THE RULE, and it
    # shrinks as the ranks deepen: the original eight spanned 5.5x, cohort 3
    # 2.15x. Measured and recorded here so no study can quietly claim this
    # cohort puts the volatility axis under test.
    vols = [x["annualised_vol"] for x in low + high]
    vlo, vhi = min(vols), max(vols)
    spread = vhi / vlo
    print(f"\nVOLATILITY SPREAD  {vlo:.1%} .. {vhi:.1%}  = {spread:.2f}x"
          f"   (original eight 5.5x, cohort 3 2.15x)")
    if spread < 3.0:
        print("  THIS COHORT DOES NOT SPAN THE VOLATILITY AXIS. The strata are "
              "labels\n  on adjacent ranks, not on distinct volatility regimes. "
              "No study using\n  these names may claim volatility is under test.")

    OUT.write_text(json.dumps({
        "purpose": "instrument holdout for D278; scores nothing",
        "rule": (f"D264's, unchanged; ranks {RANK_FROM + 1}-{RANK_TO} of each "
                 f"stratum instead of 1-4"),
        "selection_window": [SELECT_START, SELECT_END],
        "in_sample_excluded": sorted(used),
        "excluded_unserved": UNSERVED,
        "volatility_spread": {
            "min_annualised_vol": vlo, "max_annualised_vol": vhi,
            "spread_x": spread,
            "reference": {"original_eight_x": 5.5, "cohort3_x": 2.15},
            "SPANS_THE_VOLATILITY_AXIS": bool(spread >= 3.0),
            "note": ("The spread narrows monotonically as the ranks deepen. At "
                     "ranks 17-28 the 'low' and 'high' strata are labels on "
                     "adjacent ranks of one distribution, not on distinct "
                     "volatility regimes. This cohort does NOT span the "
                     "volatility axis and no study using it may claim otherwise."),
        },
        "low": low, "high": high,
        "symbols": [x["symbol"] for x in low + high],
    }, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print(f"\nHOLDOUT: {' '.join(x['symbol'] for x in low + high)}")
    print(f"fetch cost: {len(low + high)} symbols x 104 months = "
          f"{len(low + high) * 104:,} requests, ~{len(low + high) * 104 / 66:.0f} min")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""D264 WP1 -- the sample-selection rule for the single-name intraday fixture.

    uv run python scripts/select_single_name_intraday.py --select

NOTHING IN THIS FILE RUNS A STRATEGY, SCORES A CELL OR PROPOSES A RULE.
It reads the DAILY single-name fixture (D252) and names eight tickers.

=========================================================================
WHY THE RULE IS FIXED BEFORE THE INTRADAY DATA EXISTS
=========================================================================

The study under design tests a SHORT book on single names at fifteen minutes.
If the sample were chosen after looking at intraday returns, the study would be
a search dressed as a test. So the rule is committed here, run once, and its
output frozen into the fetcher as a literal tuple.

THE SELECTION WINDOW IS DISJOINT FROM THE TEST WINDOW.
  select on  2013-01-02 .. 2017-12-29   (daily bars, already committed)
  test on    2018-01-02 .. 2026-08-26   (15-minute bars, not yet fetched)

D247 ran the ETF intraday shorts on exactly 2018-01-02 .. 2026-08-26, so the
spans match and the two results are directly comparable. Selecting on 2013-2017
means no statistic that picks a name can have seen a bar the study scores.

=========================================================================
THE RULE
=========================================================================

  1. SURVIVOR ONLY -- cohort must be 'alive' at the span end. NOT a preference:
     `TIME_SERIES_INTRADAY` serves NOTHING for a delisted ticker (probed
     2026-09-01: TWTR/FRC/SIVB/AABA all return `Invalid API call`, 155 bytes,
     against AAPL's clean 546 bars / 26.0 per session). The daily endpoint DOES
     serve dead names, which is how D252 built a 35.7%-dead fixture. The
     intraday one does not. This is a PROVIDER LIMIT, and the bias it injects is
     declared in the pre-registration, not here.

  2. COVERAGE -- >= 95% of the selection window's trading days present. A name
     that half-existed in 2013-2017 is not a name whose 2013-2017 statistics
     mean anything.

  3. LIQUIDITY -- median(close x volume) over the selection window >= $50M/day.
     The study's binding constraint is a COST WALL (D247: breakeven 0.13 bp/side
     against ~1.6 bp charged). A name whose spread swamps the question cannot
     answer it. $50M is set here, once, and not swept.

  4. STRATIFY ON REALISED VOLATILITY, annualised sd of daily log close-to-close
     returns over the selection window:

       LOW  stratum -- the 4 LOWEST-vol names among the top 40 by dollar volume
       HIGH stratum -- the 4 HIGHEST-vol names passing the liquidity screen

     Volatility is the axis the study is ABOUT (FINDINGS 1b: a short pays a
     variance tax scaling with sigma^2; FINDINGS 2: idiosyncratic variance is
     where the short edge lives). Stratifying on it deliberately spans the
     trade-off so the screen reveals WHICH END BINDS. That is a declared design
     axis, not a fitted parameter -- and it is computed on data the study never
     scores.

  5. Ties broken by higher dollar volume. The full ranked pool is written out so
     the choice is auditable rather than asserted.
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
OUT = REPO / "data" / "single_name_intraday_selection.json"

SELECT_START, SELECT_END = "2013-01-02", "2017-12-29"
TEST_START, TEST_END = "2018-01-02", "2026-08-26"

MIN_COVERAGE = 0.95
MIN_DOLLAR_VOL = 50_000_000.0
TOP_N_BY_DOLLAR_VOL = 40       # the pool the LOW stratum is drawn from
N_PER_STRATUM = 4


def load_selection_window():
    """(date, close, volume) per symbol, selection window only."""
    rows = defaultdict(list)
    with gzip.open(FIXTURE, "rt", newline="") as f:
        r = csv.reader(f)
        head = next(r)
        assert head == ["timestamp", "symbol", "open", "high", "low", "close", "volume"], head
        for ts, sym, _o, _h, _l, c, v in r:
            if SELECT_START <= ts[:10] <= SELECT_END:
                rows[sym].append((ts[:10], float(c), float(v)))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    a = ap.parse_args()
    if not a.select:
        ap.print_help()
        return 2

    meta = json.loads(META.read_text())
    sym_meta = meta["symbols"]
    rows = load_selection_window()

    all_dates = sorted({d for v in rows.values() for d, _, _ in v})
    n_days = len(all_dates)
    print(f"selection window {SELECT_START} .. {SELECT_END}: {n_days} trading days, "
          f"{len(rows)} symbols with at least one bar")

    pool, rejected = [], defaultdict(int)
    for sym, bars in rows.items():
        info = sym_meta.get(sym)
        if info is None:
            rejected["no_meta"] += 1
            continue
        if info.get("cohort") != "alive" or info.get("delistingDate") is not None:
            rejected["not_a_survivor"] += 1
            continue
        if len(bars) / n_days < MIN_COVERAGE:
            rejected["coverage"] += 1
            continue
        bars.sort()
        closes = [c for _, c, _ in bars]
        dv = sorted(c * v for _, c, v in bars)
        med_dv = dv[len(dv) // 2]
        if med_dv < MIN_DOLLAR_VOL:
            rejected["liquidity"] += 1
            continue
        rets = [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))
                if closes[i] > 0 and closes[i - 1] > 0]
        mu = sum(rets) / len(rets)
        sd = math.sqrt(sum((x - mu) ** 2 for x in rets) / (len(rets) - 1))
        pool.append({"symbol": sym, "median_dollar_volume": med_dv,
                     "annualised_vol": sd * math.sqrt(252), "n_bars": len(bars),
                     "coverage": len(bars) / n_days,
                     "exchange": info.get("exchange")})

    print(f"eligible pool: {len(pool)}   rejections: {dict(rejected)}")

    by_dv = sorted(pool, key=lambda x: -x["median_dollar_volume"])
    top40 = by_dv[:TOP_N_BY_DOLLAR_VOL]
    low = sorted(top40, key=lambda x: (x["annualised_vol"], -x["median_dollar_volume"]))[:N_PER_STRATUM]
    high = sorted(pool, key=lambda x: (-x["annualised_vol"], -x["median_dollar_volume"]))[:N_PER_STRATUM]

    assert not ({x["symbol"] for x in low} & {x["symbol"] for x in high}), "strata overlap"

    def show(title, xs):
        print(f"\n{title}")
        print(f"  {'symbol':8s} {'ann.vol':>8s} {'median $vol':>14s} {'cover':>7s}")
        for x in xs:
            print(f"  {x['symbol']:8s} {x['annualised_vol']:7.1%} "
                  f"{x['median_dollar_volume'] / 1e6:12.1f}M {x['coverage']:6.1%}")

    show("LOW-VOL STRATUM (4 lowest vol of the top 40 by dollar volume)", low)
    show("HIGH-VOL STRATUM (4 highest vol clearing the $50M liquidity floor)", high)
    show("top 40 by dollar volume, for audit", top40)

    OUT.write_text(json.dumps({
        "purpose": "sample selection for the single-name 15m intraday fixture; scores nothing",
        "rule": {"selection_window": [SELECT_START, SELECT_END],
                 "test_window": [TEST_START, TEST_END],
                 "survivor_only_reason": "TIME_SERIES_INTRADAY serves no delisted ticker (probed 2026-09-01)",
                 "min_coverage": MIN_COVERAGE, "min_median_dollar_volume": MIN_DOLLAR_VOL,
                 "top_n_by_dollar_volume": TOP_N_BY_DOLLAR_VOL, "n_per_stratum": N_PER_STRATUM},
        "eligible_pool_size": len(pool), "rejections": dict(rejected),
        "low_vol_stratum": low, "high_vol_stratum": high,
        "top40_by_dollar_volume": top40,
    }, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    print("\nSAMPLE: " + " ".join(x["symbol"] for x in low + high))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

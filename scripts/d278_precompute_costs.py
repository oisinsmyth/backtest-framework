"""D278 WP2 -- the holdout's cost schedule and split timeline, computed BEFORE
the intraday bars land.

    uv run python scripts/d278_precompute_costs.py

NO STRATEGY, NO CELL, NO RETURN. Two things only:

  1. THE COST BAR the holdout will face, from each name's median close.
  2. THE SPLIT ADJUSTMENT TIMELINE, from the events sidecar already fetched.

WHY IT IS WORTH DOING NOW RATHER THAN AFTER. D264 recorded, post-hoc, that IBKR
charges PER SHARE, so commission in basis points is inversely proportional to
price: RH at $245 cost 0.20 bp/side while CLF at $12 cost 4.15. **The holdout's
high-volatility stratum contains BB and RIG, which trade in single digits.** If
their commission is far above the in-sample HIGH stratum's, the holdout faces a
HIGHER cost bar than the study it is replicating -- and that is a fact about the
test, not about the result, so it must be known in advance.

PRICE SOURCE. The committed DAILY fixture, over the intraday span. That is the
same fixture the selection rule already read, so nothing new is exposed, and the
cost model reads PRICE, never a return. **The figures here are a PREVIEW: the
study's actual cost comes from the intraday panel's own median close, exactly as
D264's did.** Any material gap between the two is itself worth seeing.
"""

from __future__ import annotations

import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DAILY = REPO / "data" / "fixtures" / "us_shorts_daily_raw.csv.gz"
HOLD = REPO / "data" / "holdout_name_selection.json"
EVENTS = REPO / "data" / "fixtures" / "holdout_intraday_15m_raw_events.json"
INSAMPLE = REPO / "data" / "single_name_intraday_summary.json"
OUT = REPO / "data" / "d278_cost_preview.json"

SPAN_START, SPAN_END = "2018-01-01", "2026-08-31"
NOTIONAL = 10_000_000.0 / 57.0          # D247's per-position figure, as D264 froze it
IBKR_PER_SHARE, IBKR_MIN, IBKR_CAP = 0.005, 1.00, 0.01
HALF_SPREAD = {"low": 1.5, "high": 4.5}  # D264's, unchanged


def commission_bps(price):
    shares = NOTIONAL / price
    c = min(IBKR_PER_SHARE * shares, IBKR_CAP * NOTIONAL)
    return 1e4 * max(c, IBKR_MIN) / NOTIONAL


def main() -> int:
    h = json.loads(HOLD.read_text())
    low = [x["symbol"] for x in h["low"]]
    high = [x["symbol"] for x in h["high"]]
    stratum = {**{s: "low" for s in low}, **{s: "high" for s in high}}
    want = set(stratum)

    closes, dvol = defaultdict(list), defaultdict(list)
    with gzip.open(DAILY, "rt", newline="") as f:
        r = csv.reader(f)
        next(r)
        for ts, sym, _o, _hi, _lo, c, v in r:
            if sym in want and SPAN_START <= ts[:10] <= SPAN_END:
                closes[sym].append(float(c))
                dvol[sym].append(float(c) * float(v))

    print("HOLDOUT COST PREVIEW -- from the committed DAILY fixture, 2018-2026")
    print(f"per-position notional ${NOTIONAL:,.0f} (D247's, as D264 froze it)\n")
    print(f"  {'sym':6s} {'str':5s} {'median px':>10s} {'commission':>11s} "
          f"{'+spread':>8s} {'= c':>7s} {'median $vol':>13s}")
    rows, per_str = [], defaultdict(list)
    for s in low + high:
        if not closes[s]:
            print(f"  {s:6s} NOT IN THE DAILY FIXTURE -- cost unknown until the panel builds")
            continue
        px = sorted(closes[s])[len(closes[s]) // 2]
        dv = sorted(dvol[s])[len(dvol[s]) // 2]
        comm = commission_bps(px)
        c = comm + HALF_SPREAD[stratum[s]]
        per_str[stratum[s]].append(c)
        rows.append({"symbol": s, "stratum": stratum[s], "median_close": px,
                     "commission_bps": comm, "cost_bps": c, "median_dollar_vol": dv})
        print(f"  {s:6s} {stratum[s]:5s} {px:10.2f} {comm:10.2f}b "
              f"{HALF_SPREAD[stratum[s]]:7.1f}b {c:6.2f}b {dv / 1e6:11.1f}M")

    ins = json.loads(INSAMPLE.read_text())["anatomy"]
    print(f"\n{'stratum':8s} {'HOLDOUT mean c':>15s} {'2c':>8s} | "
          f"{'IN-SAMPLE 2c':>13s} | {'ratio':>7s}")
    bars = {}
    for st in ("low", "high"):
        mc = sum(per_str[st]) / len(per_str[st])
        c2 = 2 * mc
        in2 = 2 * sum(ins[st.upper()]["cost_bps_per_side"].values()) / len(
            ins[st.upper()]["cost_bps_per_side"])
        bars[st] = c2
        print(f"{st.upper():8s} {mc:14.2f}b {c2:7.2f}b | {in2:12.2f}b | {c2 / in2:6.2f}x")
    allc = sum(sum(per_str[s]) for s in per_str) / sum(len(per_str[s]) for s in per_str)
    bars["all"] = 2 * allc
    in_all = 2 * sum(ins["ALL"]["cost_bps_per_side"].values()) / len(
        ins["ALL"]["cost_bps_per_side"])
    print(f"{'ALL':8s} {allc:14.2f}b {2 * allc:7.2f}b | {in_all:12.2f}b | "
          f"{2 * allc / in_all:6.2f}x")

    cheap = [r for r in rows if r["commission_bps"] > 3.0]
    if cheap:
        print(f"\n  NAMES WHOSE COMMISSION ALONE EXCEEDS 3 bp/side "
              f"(D264's post-hoc price finding, now binding):")
        for r in sorted(cheap, key=lambda x: -x["commission_bps"]):
            print(f"    {r['symbol']:6s} ${r['median_close']:7.2f} -> "
                  f"{r['commission_bps']:.2f} bp/side")

    ev = json.loads(EVENTS.read_text())
    print(f"\nSPLIT TIMELINE -- back-adjustment factors from the fetched sidecar")
    for sym, sp in sorted(ev["splits"].items()):
        if sp:
            print(f"  {sym:6s} " + ", ".join(f"{d[:10]} x{r}" for d, r in sp)
                  + f"   -> bars before that date are DIVIDED by "
                    f"{math.prod(float(r) for _, r in sp):.4f}")
    nd = {s: len(v) for s, v in ev["dividends"].items() if v}
    print(f"\n  dividends in span: {sum(nd.values())} across {len(nd)} names "
          f"(reinvested on the ex-date bar by `load_panel`)")

    OUT.write_text(json.dumps({"per_symbol": rows, "cost_bars_2c": bars,
                               "notional": NOTIONAL, "half_spread": HALF_SPREAD,
                               "source": "daily fixture preview; final cost comes from "
                                         "the intraday panel's own median close"}, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

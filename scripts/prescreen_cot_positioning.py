"""PRE-SCREEN: does CFTC positioning predict returns at a weekly horizon?

    uv run python scripts/prescreen_cot_positioning.py

**THIS IS A PRE-SCREEN, NOT A STUDY.** No rule is proposed, no hurdle is run, no
null is computed, no cell is admitted to any book. It follows D250 and D251's
inversion — measure the conditional first, against a bar stated BEFORE looking,
and only pay for a full pre-registration if it clears. That inversion has run
twice in this programme and paid both times.

WHY THIS IS WORTH RUNNING BEFORE SPENDING ANYTHING
--------------------------------------------------
`docs/research/futures-data/data-purchase-proposal.md` §7.5 puts a staged ladder
in front of the smart-money question. This is rung 1, it is free, and the data is
already committed. **If positioning carries nothing here, the ~$205 Databento
purchase loses most of its motivation** — the tick version tests the same premise
at 1/8th the statistical power.

THE PANEL, MEASURED BEFORE THE DESIGN WAS FIXED
------------------------------------------------
COT has no returns in it, so each contract is paired with its tracking ETF from
`universe_daily_extended_raw` (57 ETFs, 2009-11-11 -> 2026-08-26):

    ES/SPY  NQ/QQQ  RTY/IWM  YM/DIA  GC/GLD  SI/SLV
    CL/USO  NG/UNG  ZB/TLT   ZN/IEF  ZF/SHY

  11 instruments, 9,232 weekly observations, 16.2 years
  mean pairwise rho 0.284, EFFECTIVE INSTRUMENTS 3.76
  effective breadth-years 61.1  ->  MDE on Sharpe ~ 0.21

For contrast: D261's index spreads ran at effective breadth **1.17**, and the
$145 tick option would have given **MDE 1.65**. This is the best-powered thing
the prop track has had, and it costs nothing.

**The basis is a real limitation and is stated, not hidden.** Positioning is on
the futures; the return is on the tracking ETF. They are the same underlying
exposure but not the same instrument — USO in particular is a notoriously poor
CL tracker through contango. A pass here is a FEASIBILITY BOUND, not a result.

THE SIGNAL — every parameter fixed here, before any look
---------------------------------------------------------
```
net(t)      = (long - short) / open_interest        per category, scale-free
z(t)        = ( net(t) - mean_156(net) ) / sd_156(net)      PRIOR 156 weeks only
```

**156 weeks (3 years) is the standard COT-index lookback order and is NOT swept.**
A sweep across windows is exactly the search D225 was caught doing.

**TWO CATEGORIES, chosen because they ARE the hypothesis** — the professional
speculator against the small trader:

    TFF (financials)     leveraged_money   vs   nonreportable
    DISAGG (physicals)   managed_money     vs   nonreportable

**TWO HORIZONS: 1 week and 4 weeks.** Not a sweep.

So 2 categories x 2 horizons = **4 cells**, each pooled across 11 instruments.

R9 — THE LAG IS THE WHOLE POINT
--------------------------------
COT is surveyed at Tuesday's close and published **Friday 15:30 ET**. A study
keying on `report_date` reads Tuesday's positions on Tuesday and is three days of
look-ahead. **The forward return is measured from the first ETF session STRICTLY
AFTER `release_date_nominal`**, so the rule acts on information it could have had.

Rows before 1993 carry no release date and are excluded by construction.

THE BAR, STATED BEFORE LOOKING — and stated as EXPOSURE x EDGE
----------------------------------------------------------------
D250's correction is binding here: a screening target stated as an EDGE is the
wrong quantity, because **`gross = exposure x edge`** and a selectivity dial moves
the two in exact opposition. So:

  1. **MONOTONE.** The five quintiles must be ordered in the predicted direction.
     A non-monotone body is what closed D250, and the extreme bucket being best
     while the body is empty is a tail artefact, not a signal.
  2. **GROSS >= 2%/yr.** Exposure x edge, at the exposure the quintile rule
     actually implies. Same bar D251 could not reach.
  3. **NOT 2020.** Reported separately and never pooled away. Three studies in
     this programme have inverted sign once 2020 was removed.

**Failing any of the three closes the rung for this construction.** No threshold
sweep, no second lookback, no extra category added afterwards — that would be the
search this design exists to avoid.

R10 — CONCURRENCY IS REPORTED BESIDE THE TABLE
-----------------------------------------------
How many of the 11 instruments sit in the extreme bucket at once, against a
per-symbol-rotated baseline. **If they all fire together the signal is a market
timer wearing a cross-sectional name**, which is exactly what D249 found for the
wedge and what R10 was written to catch.

WHAT THIS CANNOT ESTABLISH
--------------------------
Feasibility only. ETF proxies, not futures. No costs charged (breakeven reported
instead). No null, no deflation, no hurdle. **A pass buys a pre-registration, not
a position.**
"""

from __future__ import annotations

import csv
import gzip
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
COT = REPO / "data" / "fixtures" / "cftc_cot_raw.csv.gz"
ETF = REPO / "data" / "fixtures" / "universe_daily_extended_raw.csv.gz"
OUT = REPO / "data" / "cot_prescreen_summary.json"

PAIRS = [("ES", "SPY"), ("NQ", "QQQ"), ("RTY", "IWM"), ("YM", "DIA"),
         ("GC", "GLD"), ("SI", "SLV"), ("CL", "USO"), ("NG", "UNG"),
         ("ZB", "TLT"), ("ZN", "IEF"), ("ZF", "SHY")]

# category -> (family it lives in, predicted direction of the Q1-Q5 spread)
#
# DIRECTION IS DECLARED BEFORE THE RUN, per D251's lesson: without it a
# wrong-signed spread can be re-read as a right-signed one after the fact.
#
#   professional speculators (leveraged money / managed money): the classic COT
#   reading is that extremes MEAN-REVERT -- crowded longs precede weakness. So
#   HIGH z predicts LOW forward return, and Q1-Q5 is POSITIVE.
#
#   small traders (nonreportable): the retail crowd is the one to fade, same
#   sign for the same reason.
CATEGORIES = {
    "leveraged_money": ("tff", +1),
    "managed_money": ("disaggregated", +1),
    "nonreportable_tff": ("tff", +1),
    "nonreportable_disagg": ("disaggregated", +1),
}

LOOKBACK = 156          # weeks; NOT swept
HORIZONS = (1, 4)       # weeks; NOT swept
N_QUINTILES = 5
MIN_GROSS_PCT = 2.0     # the bar, stated above


def load_etf() -> dict:
    px = defaultdict(dict)
    with gzip.open(ETF, "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            px[r["symbol"]][r["timestamp"][:10]] = float(r["close"])
    return px


def load_cot() -> dict:
    """(symbol, family, category) -> {release_date: net/OI}. Release-dated only."""
    out: dict = defaultdict(dict)
    with gzip.open(COT, "rt", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            rel = r["release_date_nominal"]
            if not rel or not r["open_interest"]:
                continue
            try:
                oi = float(r["open_interest"])
                lo = float(r["long"]) if r["long"] else 0.0
                sh = float(r["short"]) if r["short"] else 0.0
            except ValueError:
                continue
            if oi <= 0:
                continue
            out[(r["symbol"], r["family"], r["category"])][rel] = (lo - sh) / oi
    return out


def forward_return(px: dict, sessions: list, rel: str, weeks: int) -> float | None:
    """R9: the first session STRICTLY AFTER the release, held `weeks` weeks."""
    i = np.searchsorted(sessions, rel, side="right")
    j = i + 5 * weeks
    if i >= len(sessions) or j >= len(sessions):
        return None
    a, b = px[sessions[i]], px[sessions[j]]
    if a <= 0 or b <= 0:
        return None
    return math.log(b / a)


def main() -> int:
    px = load_etf()
    cot = load_cot()
    sessions_of = {e: sorted(px[e]) for _s, e in PAIRS}

    results: dict = {}
    for cat, (family, direction) in CATEGORIES.items():
        cot_cat = cat.split("_tff")[0].split("_disagg")[0]
        rows: list[tuple] = []          # (z, fwd_h1, fwd_h4, symbol, release)
        for sym, etf in PAIRS:
            series = cot.get((sym, family, cot_cat), {})
            if len(series) < LOOKBACK + 20:
                continue
            rels = sorted(series)
            vals = np.array([series[d] for d in rels])
            sess = sessions_of[etf]
            for k in range(LOOKBACK, len(rels)):
                win = vals[k - LOOKBACK:k]
                sd = win.std(ddof=1)
                if sd <= 0:
                    continue
                z = (vals[k] - win.mean()) / sd
                f1 = forward_return(px[etf], sess, rels[k], 1)
                f4 = forward_return(px[etf], sess, rels[k], 4)
                if f1 is None or f4 is None:
                    continue
                rows.append((z, f1, f4, sym, rels[k]))

        if not rows:
            results[cat] = {"n": 0, "note": "no usable observations"}
            continue

        z = np.array([r[0] for r in rows])
        cuts = np.quantile(z, np.linspace(0, 1, N_QUINTILES + 1)[1:-1])
        bucket = np.searchsorted(cuts, z)

        cell: dict = {"n": len(rows), "direction_declared": direction}
        for hi, h in enumerate(HORIZONS, start=1):
            fwd = np.array([r[hi] for r in rows])
            per_q = [float(fwd[bucket == q].mean()) for q in range(N_QUINTILES)]
            ann = [v * 52.0 / h * 100 for v in per_q]
            spread = ann[0] - ann[-1]
            # Monotone in the DECLARED direction: for +1 we expect Q1 highest.
            seq = ann if direction > 0 else ann[::-1]
            monotone = all(a >= b for a, b in zip(seq, seq[1:]))

            # gross = exposure x edge. The quintile rule is long Q1, short Q5,
            # so exposure is 2/5 of the panel and the edge is the spread.
            exposure = 2.0 / N_QUINTILES
            gross = exposure * spread

            # 2020, never pooled away.
            is2020 = np.array([r[4][:4] == "2020" for r in rows])
            ex2020 = fwd[~is2020]
            b2020 = bucket[~is2020]
            sp_ex = ((ex2020[b2020 == 0].mean() - ex2020[b2020 == N_QUINTILES - 1]
                      .mean()) * 52.0 / h * 100)

            cell[f"h{h}"] = {
                "quintiles_ann_pct": [round(v, 2) for v in ann],
                "spread_q1_q5_ann_pct": round(spread, 2),
                "monotone_in_declared_direction": bool(monotone),
                "exposure": exposure,
                "gross_ann_pct": round(gross, 3),
                "clears_gross_bar": bool(gross >= MIN_GROSS_PCT),
                "spread_ex_2020_ann_pct": round(sp_ex, 2),
                "sign_survives_ex_2020": bool(np.sign(sp_ex) == np.sign(spread)),
            }

        # R10 concurrency: how many instruments in the extreme bucket at once.
        by_rel: dict = defaultdict(int)
        for (zz, _f1, _f4, sym, rel), b in zip(rows, bucket):
            if b == 0 or b == N_QUINTILES - 1:
                by_rel[rel] += 1
        counts = np.array(list(by_rel.values())) if by_rel else np.array([0])
        cell["concurrency"] = {
            "mean_instruments_in_extreme_bucket": round(float(counts.mean()), 2),
            "max": int(counts.max()),
            "of_possible": len(PAIRS),
            "note": ("R10. If they fire together the signal is a market timer "
                     "wearing a cross-sectional name -- D249's finding."),
        }
        results[cat] = cell

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({
        "design": {
            "pairs": PAIRS, "lookback_weeks": LOOKBACK, "horizons": HORIZONS,
            "quintiles": N_QUINTILES, "gross_bar_pct": MIN_GROSS_PCT,
            "lag": "first ETF session strictly after release_date_nominal (R9)",
        },
        "results": results,
    }, indent=1) + "\n", encoding="utf-8")

    # ---- report
    for cat, cell in results.items():
        if not cell.get("n"):
            print(f"\n{cat}: {cell.get('note')}")
            continue
        print(f"\n{cat}  ({cell['n']:,} observations)")
        for h in HORIZONS:
            c = cell[f"h{h}"]
            q = "  ".join(f"{v:+7.2f}" for v in c["quintiles_ann_pct"])
            print(f"  h={h}w  Q1..Q5 ann%: {q}")
            print(f"         spread {c['spread_q1_q5_ann_pct']:+7.2f}   "
                  f"gross {c['gross_ann_pct']:+6.2f}%   "
                  f"monotone {str(c['monotone_in_declared_direction']):5}  "
                  f"bar {str(c['clears_gross_bar']):5}")
            print(f"         ex-2020 spread {c['spread_ex_2020_ann_pct']:+7.2f}   "
                  f"sign survives {c['sign_survives_ex_2020']}")
        cc = cell["concurrency"]
        print(f"  R10: mean {cc['mean_instruments_in_extreme_bucket']} of "
              f"{cc['of_possible']} in an extreme bucket at once, max {cc['max']}")

    print(f"\nwrote {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

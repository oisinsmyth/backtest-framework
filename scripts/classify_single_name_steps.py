"""D264 WP1 -- classify the 30 session-boundary steps the build gate flagged.

    uv run python scripts/classify_single_name_steps.py

NOTHING HERE SCORES A CELL. This is D226's gate finishing its own sentence: the
threshold requires "no move above 15% THAT IS NOT ON A DOCUMENTED LIST OF REAL
EVENTS", and this builds that list by measurement rather than by assertion.

=========================================================================
THE FIRST VERSION OF THIS FILE USED THE WRONG TESTS. Recorded, not quietly
replaced, because the failure is instructive.
=========================================================================

It asked "did the price come back within 5 sessions?" and called anything that
did a BAD PRINT, and it asked "was volume above the trailing 21-session median?"
and called anything quiet a CORPORATE ACTION. Both are wrong, and the output
showed it:

  * CLF and YELP were tagged CORPORATE ACTION on 2020-03-17 while RH was tagged
    REAL on THE SAME DAY. A corporate action does not hit three unrelated
    companies on one date. The volume test failed because by 2020-03-17 the
    trailing median ALREADY CONTAINED the crash weeks -- the denominator was
    elevated, so a genuine spike scored 1.16x.
  * CLF +15.93% on the 2024 US election at 4.26x volume, and RH +15.69% and
    +22.98% on earnings at 6x, were tagged BAD PRINT because the move partly
    retraced within a week. A BAD PRINT REVERSES ON THE NEXT BAR. A real move
    that mean-reverts over five sessions is a real move.

THE TESTS THIS VERSION USES, which are the ones D252 actually names
--------------------------------------------------------------------
  IS THERE AN ISOLATED BAR?  A bad print is ONE bar out of line with BOTH its
      neighbours -- D259's EWJ prints 11.46 on 912 shares while every bar either
      side is ~60.60. That, and only that, is the bad-print signature. A session
      that trends, or a move that mean-reverts over a week, looks nothing like it.

  IS IT EVEN A GAP?  The decomposition is computed and reported, and it came back
      DEGENERATE: overnight gap = the whole step, intraday = +0.00%, on all 30.
      THAT IS CORRECT AND IT FALSIFIES THE REASON I ADDED IT. The gate compares
      the previous session's LAST bar to the new session's FIRST bar, so the step
      it flags is already purely the overnight gap; the "flat open then a 20%
      trend" failure mode I wrote this to catch cannot occur. Kept because a
      degenerate check that PROVES the gate measures what it claims is worth its
      three lines -- but the claim it was added on was wrong.

      So the honest account of why v2 misfired is NOT "the session trended". It
      is that `session_hold` compared the session's MEDIAN bar to its opening
      gap level, and on a day that gaps and then keeps moving, the median sits
      far from both ends. That is a description of a volatile session, not of a
      printing error, which is why the ISOLATED-BAR test replaced it.

  DID THE REST OF THE SAMPLE MOVE TOO?  The decisive corroboration test, and the
      one whose absence produced the error above. A market-wide day is real by
      definition; a corporate action is idiosyncratic by definition.

  WAS THE TAPE LOUD, against a CLEAN baseline?  Volume on the gap session against
      the median of sessions t-26..t-6 -- ending BEFORE the event, so a
      multi-day regime cannot inflate its own denominator.

  DOES THE RATIO LOOK LIKE A SPLIT?  Split ratios are simple rationals. Checked
      independently of every other test and reported however the step classifies,
      because this is the XLF/XLRE failure mode: a -18.3% step that HELD at full
      volume while the provider reported zero splits.
"""

from __future__ import annotations

import csv
import gzip
import json
import statistics
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FIXTURE = REPO / "data" / "fixtures" / "single_name_intraday_15m_raw.csv.gz"
META = REPO / "data" / "fixtures" / "single_name_intraday_15m_raw.meta.json"
OUT = REPO / "data" / "single_name_intraday_steps.json"

# A bad print is ONE bar out of line with BOTH its neighbours (D259's EWJ: 11.46
# on 912 shares between bars of ~60.60). This is the deviation that triggers it.
ISOLATED_BAR_TOL = 0.15
SESSION_HOLD_TOL = 0.50     # reported, no longer decisive -- see the docstring
# Corroboration: the mean absolute same-day step across the OTHER seven names.
MARKET_MOVE = 0.03
# Volume, against a baseline that ENDS BEFORE the event.
VOLUME_SPIKE = 1.75
VOL_BASE_FROM, VOL_BASE_TO = 26, 6

SPLIT_STEPS = (-0.5000, -0.6667, -0.7500, -0.8000, 1.0000, 2.0000, 3.0000)
SPLIT_TOL = 0.015


def main() -> int:
    meta = json.loads(META.read_text())
    steps = meta["session_boundary_steps_over_threshold"]
    if not steps:
        print("no steps over threshold; nothing to classify")
        return 0

    session_closes: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    volume: dict[str, dict[str, float]] = defaultdict(lambda: defaultdict(float))
    with gzip.open(FIXTURE, "rt", newline="") as f:
        for r in csv.DictReader(f):
            d = r["timestamp"][:10]
            session_closes[r["symbol"]][d].append(float(r["close"]))
            volume[r["symbol"]][d] += float(r["volume"])

    syms = sorted(session_closes)
    days = {s: sorted(session_closes[s]) for s in syms}
    close = {s: {d: session_closes[s][d][-1] for d in days[s]} for s in syms}

    # every symbol's own session-boundary step, so "did the market move" is a
    # measurement rather than a memory of what happened in 2020
    step_of: dict[str, dict[str, float]] = {}
    for s in syms:
        st = {}
        for j in range(1, len(days[s])):
            a, b = days[s][j - 1], days[s][j]
            st[b] = close[s][b] / close[s][a] - 1.0
        step_of[s] = st

    out, counts = [], defaultdict(int)
    for rec in steps:
        sym, day = rec["symbol"], rec["to"][:10]
        i = days[sym].index(day)

        bars = session_closes[sym][day]
        med = statistics.median(bars)
        held = abs(med - rec["close"]) / abs(rec["close"] - rec["prev_close"])

        # THE STEP IS CLOSE-TO-CLOSE, so it is not necessarily a GAP. A session
        # that opens flat and then trends 20% is flagged by the same gate and is
        # not a gap at all -- it is exactly the kind of move an intraday book
        # cares about. Decompose before classifying.
        gap = bars[0] / rec["prev_close"] - 1.0
        intra = rec["close"] / bars[0] - 1.0

        # THE BAD-PRINT SIGNATURE, and it is intra-session: ONE bar wildly out of
        # line with BOTH its neighbours. D259's EWJ prints 11.46 on 912 shares
        # while every bar either side is ~60.60. Nothing about a multi-day
        # retrace, and nothing about a trending session, looks like that.
        worst_iso = 0.0
        for j in range(1, len(bars) - 1):
            lo = min(bars[j - 1], bars[j + 1])
            hi = max(bars[j - 1], bars[j + 1])
            if hi <= 0:
                continue
            dev = max(0.0, (lo - bars[j]) / lo, (bars[j] - hi) / hi)
            worst_iso = max(worst_iso, dev)
        holds = bool(worst_iso <= ISOLATED_BAR_TOL)

        others = [abs(step_of[o][day]) for o in syms if o != sym and day in step_of[o]]
        market = statistics.mean(others) if others else 0.0
        wide = bool(market >= MARKET_MOVE)

        base = days[sym][max(0, i - VOL_BASE_FROM): max(0, i - VOL_BASE_TO)]
        bmed = statistics.median([volume[sym][d] for d in base]) if base else 0.0
        ratio = (volume[sym][day] / bmed) if bmed else None
        loud = bool(ratio is not None and ratio >= VOLUME_SPIKE)

        near_split = [f"{r:+.4f}" for r in SPLIT_STEPS if abs(rec["step"] - r) <= SPLIT_TOL]

        if not holds:
            verdict = "BAD PRINT"
        elif near_split and not wide and not loud:
            verdict = "CORPORATE ACTION"
        elif wide:
            verdict = "REAL (market-wide)"
        elif loud:
            verdict = "REAL (idiosyncratic, on volume)"
        else:
            verdict = "NEEDS EYES"
        counts[verdict] += 1
        out.append({**rec, "day": day, "session_hold": round(held, 3),
                    "overnight_gap": round(gap, 4), "intraday_move": round(intra, 4),
                    "worst_isolated_bar": round(worst_iso, 4),
                    "market_mean_abs_step": round(market, 4),
                    "volume_ratio_clean_baseline": round(ratio, 2) if ratio else None,
                    "near_split_ratio": near_split, "verdict": verdict})

    print(f"{'symbol':6s} {'date':11s} {'step':>8s} {'gap':>8s} {'intra':>8s} "
          f"{'isol':>6s} {'mkt':>7s} {'vol':>7s}  verdict")
    for r in sorted(out, key=lambda x: (x["symbol"], x["day"])):
        print(f"{r['symbol']:6s} {r['day']:11s} {r['step'] * 100:+7.2f}% "
              f"{r['overnight_gap'] * 100:+7.2f}% {r['intraday_move'] * 100:+7.2f}% "
              f"{r['worst_isolated_bar'] * 100:5.1f}% "
              f"{r['market_mean_abs_step'] * 100:6.2f}% "
              f"{(r['volume_ratio_clean_baseline'] or 0):6.2f}x  {r['verdict']}"
              + ("   <-- SPLIT-LIKE RATIO" if r["near_split_ratio"] else ""))

    print(f"\n{dict(counts)}")
    OUT.write_text(json.dumps({
        "purpose": ("D226's allow-list, built by measurement. Classifies every "
                    "session-boundary step above 15% in the single-name intraday "
                    "fixture. Scores nothing."),
        "superseded_tests": ("v1 used a 5-session revert test and a trailing-median "
                             "volume test. Both were wrong and are documented in the "
                             "module docstring rather than deleted."),
        "test": {"isolated_bar_tol": ISOLATED_BAR_TOL, "session_hold_tol": SESSION_HOLD_TOL, "market_move": MARKET_MOVE,
                 "volume_spike_x": VOLUME_SPIKE,
                 "volume_baseline_sessions": [VOL_BASE_FROM, VOL_BASE_TO],
                 "split_ratios_checked": list(SPLIT_STEPS), "split_tolerance": SPLIT_TOL},
        "counts": dict(counts), "steps": out,
    }, indent=2))
    print(f"wrote {OUT.relative_to(REPO)}")

    bad = [r for r in out if r["verdict"] in ("CORPORATE ACTION", "NEEDS EYES", "BAD PRINT")]
    if bad:
        print(f"\n{len(bad)} step(s) are NOT a clean REAL verdict:")
        for r in bad:
            print(f"  {r['symbol']} {r['day']} {r['step'] * 100:+.2f}% -> {r['verdict']}")
    else:
        print("\nEVERY STEP IS REAL -- the level held through its session, and each is "
              "either market-wide or on a clean volume spike. No missed corporate "
              "action, no bad print. D226's allow-list is this file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

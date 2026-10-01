# D749 STAGE 0 RESULT — NOTHING: EUR/USD moves enough into the month-end London fix to pay, but not in the direction the month's US equity return predicts; whatever existed before the 2015 fix reform is gone after it

*2026-10-01. One run of `scripts/stage0_d749_month_end_fix.py --run` under the system interpreter. The
[pre-registration](D749-STAGE-0-PRE-REG-the-month-end-london-fix-on-m6e.md) (`023eac55`) was committed before the
runner, and the runner (`f8720705`) before its run.*
- **Output:** `data/stage0_d749_month_end_fix.json`.

## 0. Checks

- **The seal:** 6E was read with a parquet filter (root 6E, day < 2024-01-01), and SPY's keys were restricted before
  2024.
- **The clock:**
  - the zoneinfo fix time equals the statutory-rule implementation on every event and placebo day, and on every
    business day 2011–2023 in the self-test;
  - 14 month-ends fall in a daylight-saving-mismatch week (fix at 12:00 ET).
- **The sign:** it equals its loop twin on a sample, and the same-day-close canary changed some signs.
- **Sign audit in money:** a rise pays the long.
- **Right quantity:** P ≠ R, and no placebo day is a month-end.
- **The events:** 156 month-ends; 4 were dropped for a roll or a flagged session, leaving 152 scored. 594 placebo days.
- **One deviation, disclosed:** the component line's subprocess (the D737 twin / NQ F2 / C1 daily nets under the
  project interpreter) failed when launched from the system interpreter: uv could not resolve its Python.
  - The same two steps were then run directly from the shell, on the same inputs, and the figures in §3 come from
    that. No D749 figure was re-run.

## 1. The result

One M6E, P = the 30 minutes into the fix, signed by SPY's month-to-date return.

| | value |
|---|---|
| trades | 152 (100 long, 52 short) |
| **mean gross** | **+\$0.59 (t 0.28)** |
| mean net (\$4.38 cost) | −\$3.79 |
| N1 sign rotation (151 offsets): p50 / p95 / p | −\$1.04 / +\$2.34 / 0.23 |
| N2 placebo days −5…−2 (594) | +\$0.27 (t 0.38); month-end minus placebo, Welch t 0.15 |
| **O1: mean \|move\|** | **\$19.76, 2.3 × the \$8.76 bar** (quartiles \$8.75 / \$17.50 / \$27.50) |

- **Reading: NOTHING.** NO ROOM is false: a perfectly signed rule would clear the bar.
- **FLOW PRESENT is false on every leg:** t 0.28 against 2; the score sits inside the rotation (p 0.23); and it
  equals the placebo days.
- **GO is false.**

**The eras** (the fix window widened from 1 to 5 minutes in February 2015, after the 2013 scandal):

| era | month-ends | mean gross | t |
|---|---|---|---|
| 2011 → Jan 2015 | 47 | +\$4.47 | +1.49 |
| Feb 2015 → 2023 | 105 | −\$1.14 | −0.42 |

**The other splits:**
- quarter-ends +\$2.99 (t 0.97, n 52); other month-ends −\$0.66 (n 100);
- **N3, the clock control (n 14):** the window into the real 12:00 fix is +\$2.86, and the ET-clock 11:00 window is
  −\$1.96. That is the direction a London flow would show, on 14 events.

## 2. The four groups (P)

- **Performance:**
  - net Sharpe −0.51, Sortino −0.61 (12 a year), gross Sharpe +0.08;
  - max drawdown \$603; total net −\$576;
  - the breakeven cost is \$0.59, against \$4.38;
  - exposure 30 minutes a month.
- **Trade distribution:**
  - median net −\$2.20, win rate 0.45, payoff 0.82, skew −1.04, kurtosis 5.4;
  - ex-top −\$4.65, ex-bottom −\$2.51, trimmed −\$3.36.
- **What it depends on:**
  - 5 of 13 years positive; 2021 (−\$259) and 2022 (−\$159) are the worst;
  - the long side (US equities up, so sell dollars) loses: −\$1.74 gross on 100;
  - the short side makes +\$5.07 on 52.
- **Nulls:** the rotation p50 is −\$1.04 and p95 +\$2.34, so the score is inside it. The placebo is decisive in the
  negative: month-ends are not different.

## 3. The component line

- Net Sharpe −0.51, hit rate 0.45, skew −1.04, gross +\$0.59 against net −\$3.79.
- **On the 152 event days:**

  | line | days it also traded | its same-day net sum | ρ with D749's event net |
  |---|---|---|---|
  | D737's twin | 80 | −\$112.9 | +0.10 |
  | NQ F2 | 13 | −\$43.9 | +0.03 |
  | C1 | 10 | +\$781.2 | −0.03 |

## 4. Predictions against the outcome

- **This session:** about 20% → NOTHING ✓.
- **The Fable agent:** 35% → NOTHING.
- Both anticipated the post-2015 fade, and it is what the eras show.

## 5. Reading

- **The flow as published is not in EUR/USD futures 2011–2023 at the 30-minute horizon.**
  - The size is there: the window moves about \$20 a micro.
  - The sign is not.
  - Pre-reform the point estimate was positive (+\$4.47, t 1.49); after the 2015 reform it is negative. That is
    consistent with a known, front-run flow that was arbitraged away, or spread over a longer window, once the fix
    was reformed.
- **An observation, POST HOC and not a lead: the 30 minutes AFTER the fix move against the month's sign.**
  - The fade R grosses +\$4.78 a trade at t 4.03 on 152.
  - It was a reported leg, not the hypothesis, and it has no placebo or rotation control.
  - **It cannot pay at micro size even if real:** \$4.78 gross against the \$8.76 bar, net +\$0.40.
  - It is recorded so it is not rediscovered as new. A full-size 6E version is outside the principal's micro-only
    ruling.

## 6. Next

- **The reading is NOTHING.** Closing it is the principal's call (R15).
- **The next ideas from the same round:** the gold 10:00 fix (MGC), and the London Metal Exchange official price on
  copper (MHG), on the principal's word. Gotobi is under the micro bar by its own sizing.

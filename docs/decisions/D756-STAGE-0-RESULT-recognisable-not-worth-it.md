# D756 STAGE 0 RESULT — RECOGNISABLE, NOT WORTH IT: a reverting day is worth +\$34 to a 10:00 fade if known, but the best pre-open variable (a small gap) finds them with 36 % precision against the 43.5 % the fade needs

*2026-10-02. Prop book.*
- *Pre-registration: [D756](D756-STAGE-0-PRE-REG-mean-reverting-days.md) (68a96d74).*
- *Runner: `scripts/stage0_d756_reverting_days.py`, committed before its run (9e161926). One plumbing fix (65a08ccd)
  came after an attempt that stopped at the seal check, before any label, prize or predictor was computed.*
- *Output: `data/stage0_d756_reverting_days.json`. Wall 22 s.*
- *Sessions: ES and NQ 1,941; YM 1,938; RTY 1,557 (from 2017-08), through 2023-12-29.*
- *The known answer held (D727's panel counts); the label's 1/3 per root-year held; the overnight range matched the
  RTH front contract on every session; the lag audit and its canary held; vector == loop on 50 offsets for each
  predictor.*

## 0. The prize (Z holds)

The 10:00 fade of the move since the open, held to 15:59, one micro, net:

| | n | mean | t | median | win |
|---|---|---|---|---|---|
| **reverting days (RD, known after the fact)** | 2,440 | **+\$34.19** | 24.6 | +\$19.74 | 75.1 % |
| other days | 4,890 | −\$26.33 | −10.7 | −\$35.16 | 31.5 % |
| every day | 7,330 | −\$6.19 | −3.5 | −\$6.92 | 46.0 % |

**Per root** (RD / other): ES +\$29.86 / −\$23.37; NQ +\$53.57 / −\$43.31; YM +\$24.70 / −\$14.19;
RTY +\$27.06 / −\$23.91.

**What the prize means:**
- **On a reverting day the fade pays,** about 7× its cost. **On the other two-thirds it loses,** and every day
  together loses: the fade is negative unconditionally, matching D746 and D752.
- **p\* = 0.435.** A selector must pick days of which at least 43.5 % are reverting days for the fade to break even.
  The base rate is 33.3 %.

## 1. The predictors (Holm over seven; two-sided, against the exact rotation)

| predictor | lift (expected − opposite) | precision, expected cell | p | Holm | verdict |
|---|---|---|---|---|---|
| P-a overnight range | +0.025 | 0.347 | 0.148 | 0.59 | NOT PREDICTABLE |
| **P-b gap ÷ σ_oc** | **+0.048** | **0.364** | 0.007 | **0.043** | **RECOGNISABLE, NOT WORTH IT** |
| P-c previous E | **−0.048** | 0.316 | 0.005 | 0.033 | **WRONG SIGN** (significant, reversed) |
| P-d previous range | −0.031 | 0.313 | 0.068 | 0.34 | NOT PREDICTABLE |
| P-e volatility level | +0.004 | 0.332 | 0.83 | 1.00 | NOT PREDICTABLE |
| P-f event day | +0.002 | 0.333 | 0.93 | 1.00 | NOT PREDICTABLE |
| P-g GEX > 0 | +0.026 | 0.336 | 0.22 | 0.65 | NOT PREDICTABLE |

The rotation null's p05 to p95 is about ±0.028 throughout.

**P-b, the gap.** A small open gap (bottom tercile) is followed by a reverting day 36.4 % of the time, against
30.5–32.4 % after a large one. It is consistent on all four roots:

| root | lift | RD rate, smallest-gap tercile |
|---|---|---|
| ES | +0.063 | 0.368 |
| NQ | +0.053 | 0.363 |
| YM | +0.042 | 0.366 |
| RTY | +0.030 | 0.355 |

**It is real and well short of the 43.5 % needed.**

**P-c, the previous day's shape, is significant in the opposite direction to the one declared.** A reverting day
is *more* likely after an efficient (trending) day: 0.366–0.377 on ES, NQ and YM after the top tercile of previous
E, against 0.293–0.332 after the bottom tercile. Day types *alternate* rather than persist. **By the declared rule
this is WRONG SIGN, not a pass.** Even its favourable cell (about 0.36) is below p\*.

**Reading: RECOGNISABLE, NOT WORTH IT.**

## 2. Predictions against outcomes

| | predicted | outcome |
|---|---|---|
| P1 | Z holds (P 0.8) | **held:** +\$34.19, t 24.6 |
| P2 | p\* above 0.5 | **missed:** 0.435 |
| P3 | NOT PREDICTABLE or RECOGNISABLE, NOT WORTH IT (P 0.9) | **held.** But the passing variable is the gap, not the size variables I named (P-e, P-d, P-g) |
| | P(PREDICTABLE AND WORTH IT) ≈ 0.05 | not |

## 3. What follows

**No trading rule follows from this record.** Reverting days are recognisable before the open, but the best single
variable lifts the hit rate from 33 % to 36 %, and the fade needs 43.5 %.

**Two leads, POST HOC and not evidence:**
- **The gap and the previous day's shape are both significant** (one as declared, one reversed). A selector that
  combines them, a small gap after a trending day, could plausibly gain a few more points of precision.
- **Day types alternate.**

Testing either would be a new pre-registration, with the combination declared before any look. It would be read
only on the held 2024-01 → 2025-02 slice, on the principal's word: this record has spent the in-sample for these
seven variables.

**The intraday mean-reversion closure on the index micros (D746, D747, D752) stands for trading.** This record
reopened it for classification only.

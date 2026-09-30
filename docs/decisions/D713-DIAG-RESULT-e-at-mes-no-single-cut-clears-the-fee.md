# D713 DIAG RESULT — E's MES oracle: 48.0% of its trades win after the $4.42 round trip against a 49.5% breakeven; the edge concentrates on the deepest short-gamma days, on hours that go with the day, and at 13:30–14:30, but no single bucket clears the fee beyond what 58 buckets produce by chance

*2026-09-30. One run of `scripts/diag_d713_e_oracle_mes.py` (61 s). Its
[design record](D713-DIAG-DESIGN-the-mes-oracle-profile-of-e.md) (`04782293`) was committed before the runner, and the
runner before the run.*
- **Reproduction:** D712's rule path, 4,245 trades, T +$3.0952, exactly.
- **What it is:** hindsight and descriptive. Nothing is fitted or traded. In-sample, 2016–2023.
- **Output:** `data/d713_e_oracle_mes.json`.

## The whole set (one MES, $4.42)

- 4,245 trades on 859 ES-book short-gamma sessions (531 a year).
- **Gross +$3.16, net −$1.26.** The timing term is +$3.10 (t 3.18).
- **WIN 48.0%.** Winners average +$44.30 and losers −$43.36, so **breakeven needs 49.5%**: a cut must lift the win
  rate by about 1.5 points.
- **BAR 43.5%** (gross ≥ $8.84).
- **Multiplicity:** 58 buckets. Under no effect, the largest |t| has a median of 2.52 and a 95th percentile of 3.33.

## The profile (mean gross and its t; mean net; the timing term T)

| bucket | trades a year | WIN | gross (t) | net | T (t) |
|---|---:|---:|---|---:|---|
| **clock 10:30** | 107 | .513 | +3.36 (1.37) | −1.06 | +3.43 (1.40) |
| clock 11:30 | 107 | .484 | +2.53 (1.23) | −1.89 | +2.24 |
| **clock 12:30** | 106 | .453 | +0.99 (0.52) | −3.43 | +1.17 |
| **clock 13:30** | 106 | .468 | **+5.03 (2.42)** | **+0.61** | +4.95 (2.39) |
| clock 14:30 | 106 | .483 | +3.91 (1.57) | −0.51 | +3.69 |
| long / short | 280 / 251 | .501 / .457 | +4.36 (3.33) / +1.83 (1.25) | −0.06 / −2.59 | +2.98 / +3.23 |
| **with the day** (the last hour's sign = the day's sign to t) | 390 | .497 | **+4.01 (3.53)** | −0.41 | +3.85 (3.40) |
| against the day | 139 | .435 | +1.08 (0.56) | −3.34 | +1.30 |
| **G_ES quintile 0 (most short)** | 106 | .504 | **+5.34 (1.86)** | **+0.92** | +5.51 (1.95) |
| G_ES quintile 1 / 2 / 3 | 106 each | .483 / .507 / .496 | +4.10 / +2.92 / +4.06 | −0.32 / −1.50 / −0.36 | |
| **G_ES quintile 4 (least short)** | 106 | .412 | **−0.60 (−0.35)** | −5.02 | −0.69 |
| SPX also short (G_SUM < 0) / SPX long | 374 / 157 | .493 / .450 | +3.77 (2.93) / +1.72 (1.34) | −0.65 / −2.70 | |
| last hour's size, terciles | 174 each | .473 / .460 / .503 | +2.53 / +3.77 / +2.72 | −1.89 / −0.65 / −1.70 | flat |
| today's volatility to t, terciles | 177 each | .452 / .490 / .500 | +2.64 / +3.33 / +3.52 | −1.78 / −1.09 / −0.90 | BAR .377 → .481 |
| ES price, terciles | 177 each | .448 / .489 / .504 | +0.93 / +4.70 / +3.86 | −3.49 / +0.28 / −0.56 | |

**By year** (net a trade): 2016 −2.01, 2017 −4.29, 2018 −1.33, 2019 −3.11, 2020 −1.30, 2021 −1.07, 2022 −1.33,
**2023 +1.95**. Gross is positive in every year; net is positive only in 2023.

**Clock × side:** the strongest cell is 14:30 long, +$8.77 gross (t 2.71), net +$4.35, 56 a year. But 14:30 short is
−$1.56. Its timing term (+$3.54) is ordinary, so the cell is mostly the late-day up-drift.

**Clock × last hour's size:** no clock shows a consistent size gradient. For example, 13:30 runs +3.86 / +4.66 / +6.69
and 14:30 runs +3.74 / +6.11 / +0.62.

## The hold-length profile (descriptive; different constructions from E)

| construction | trades a year | gross (t) | net | WIN | daily net Sharpe (Sortino) |
|---|---:|---|---:|---:|---|
| E, held 60 minutes | 531 | +3.16 (3.22) | −1.26 | .480 | −0.46 (−0.62) |
| same entries held 120 minutes (overlapping) | 531 | +2.56 (1.76) | −1.86 | .490 | −0.45 |
| same entries held to 16:00 (overlapping) | 531 | +4.49 (2.24) | +0.07 | .505 | +0.01 |
| **the 10:30 decision only, held to 16:00** | 107 | +1.61 (0.28) | −2.81 | .521 | −0.18 (−0.23) |
| **the 13:30 decision only, held to 16:00** | 106 | +7.02 (1.67) | **+2.60** | .499 | **+0.22 (+0.34)** |

- **The 13:30-to-close hold nets positive in 4 of 8 years.** 2022 contributes +$3,789 of its +$2,205 total.
- **It passes through 15:30 → 16:00,** D707's F2 clock. It is recorded here descriptively, and it is not a
  candidate.

## What it says

1. **The 1.5-point win-rate gap is the whole problem.** E's side choice is real, but its trades pay the $4.42 round trip
   only about half the time.
2. **Three places hold more of the edge than the rest, and all three point the mechanism's way:**
   - **Deeper short gamma.** The G_ES quintiles run +$5.34 (most short), +4.10, +2.92, +4.06, then −$0.60 (least short).
     The least-short fifth carries nothing, and SPX also short beats SPX long (+3.77 against +1.72).
   - **Hours that go with the day:** +$4.01 (t 3.53) against +$1.08. This is 73% of the trades.
   - **Later clocks:** 13:30 is +$5.03 and 14:30 +$3.91. 12:30 is +$0.99.
3. **Only the with-the-day cut is above the multiplicity bar,** and it is too broad to clear the fee alone: net −$0.41.
   Every bucket that nets positive is a small cell at t 1.9–2.7, which is where 58 buckets put their best cells by
   chance.
4. **The size of the last hour does not rank the trades,** as D689 found: bigger moves do not continue more. Today's
   volatility raises the BAR rate (.377 → .481) and the gross only slightly.
5. **One longer hold a day does not rescue it** at 10:30. At 13:30-to-close it nets +$2.60 a trade on 106 a year, but it
   is one year's result (2022) and it sits on F2's clock.

**Any cut built from this needs:**
- its edges declared prior-only;
- a fresh pre-registration;
- a null that prices the selection from this 58-bucket table.

Which cuts to test is the principal's call.

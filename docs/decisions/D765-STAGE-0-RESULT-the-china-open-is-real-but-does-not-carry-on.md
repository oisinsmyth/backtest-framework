# D765 STAGE 0 RESULT — NO DIRECTION on MHG and SIL: the China open is real size, but its first half hour does not carry on into the SHFE close; if anything it reverses, and gold's reversal is the only one that beats a placebo

*2026-10-02. One run of `scripts/stage0_d765_china_open.py --run` (0.36 minutes), after one `--extract` (3.0 minutes).*
- **The order:** the [pre-registration](D765-STAGE-0-PRE-REG-copper-and-silver-at-the-china-open.md) (`9d174f98`)
  came before the runner (`c6a47a62`), and the runner before its extraction and its one run.
- **Output:** `data/stage0_d765_china_open.json` (statistics only).
- Before the run, the whole run path was exercised on synthetic bars.
- **The priors were:** PREMISE HOLDS about 10% (MHG) and 8–12% (SIL); a direction on at least one cell about 50%,
  positive (continuation) given a pass about 60%.

## 0. Checks

- **The extraction:** HG, SI, GC and 6A front minutes, 2015-12 → 2023-12-29.
  - 2.69–2.85M minutes per root, about 1,330 per session: these books print almost every minute.
  - Re-decoding the 2021 file serially gave a result identical to the process result.
- **Sessions (MHG; SIL and MGC within 2):**
  - 2,074 read = 1,731 eligible + 139 China holidays + 193 roll week + 9 missing prices + 2 isolated-print voids +
    0 two-contract.
  - The walk-forward third begins once 250 eligible sessions exist (2017). That gives 499 trades on MHG, 456 on SIL
    and 482 on MGC.
- **The seal:** nothing on or after 2024-01-01 was decoded.
- **The clock:** zoneinfo equals the statutory rule on every session.
- **The lag audit:**
  - a pandas-mask second implementation re-derived x, entry and y on 40 sampled sessions per cell;
  - a hand-written quantile re-derived every traded-third flag;
  - the holiday flag was re-read from the CSV. All equal.
- **Right quantity:**
  - the ET-fixed 21:00 window equals the Beijing-aligned one on every EDT session, and differs on EST;
  - holiday ∩ treatment = ∅;
  - rotation offset 0 = the observed ρ.
- **Isolated prints** (20+ ticks from both neighbouring closes): HG 1–88 a year, SI 1–162 (162 in 2020), GC 5–1,129
  (2020's volatility: \$2 is 20 ticks). They voided only 2–4 sessions a cell.

## 1. China's clock is real: the size checks pass

| | MHG | SIL | MGC (reported) |
|---|---|---|---|
| mean \|x\| (09:00 → 09:30 Beijing), SHFE days | \$17.92 | \$45.53 | \$16.13 |
| the same window on China's holidays (CME open) | \$13.42 (n 127) | \$28.67 (n 124) | \$11.24 (n 125) |
| Welch t (C3a) | **3.53** | **6.30** | 5.15 |
| the first session after Spring Festival or Golden Week (15) | \$32.92 | \$69.00 | \$24.47 |
| **C1:** mean \|y\| on the traded third (to 15:00 Beijing) against 2 × 2c | **\$43.50** vs \$17.00 | **\$106.68** vs \$32.00 | \$39.76 vs \$23.72 |
| the same at 10:15 / 11:30 | \$18.77 / \$28.35 | \$48.49 / \$71.05 | \$18.85 / \$24.90 |

- **The opening half-hour is a third to three-fifths larger when Shanghai trades than when it does not.** After the
  long holidays it is 1.5–1.8× larger.
- **The opening moves co-move with the AUD:** ρ(x_HG, x_6A) is 0.35 and ρ(x_SI, x_6A) is 0.30. That is a common
  China factor.
- **There is room for a trade:** the hold to 15:00 moves 5–7 × 2c.

## 2. Direction: none on the primaries, and the sign that shows is reversal

| | ρ(x, y) | rotation p2.5 / p50 / p97.5 | two-sided p (Holm) | C2 | traded-third ρ | OLS slope, NW(5) t |
|---|---|---|---|---|---|---|
| **MHG** | **−0.026** | −0.048 / −0.000 / +0.048 | 0.29 (0.29) | fail | −0.016 | −0.54 |
| **SIL** | **−0.046** | −0.046 / +0.000 / +0.045 | 0.054 (0.108) | fail (just inside the band) | −0.109 | −1.75 |
| MGC (reported) | **−0.063** | −0.045 / +0.000 / +0.047 | 0.007 | pass (reversal) | −0.096 | −2.51 |

- **The readings:** **MHG NO DIRECTION, SIL NO DIRECTION.** GO false.
- **Continuation, the predicted sign, appears nowhere.** Jin et al.'s SHFE copper result (2002–2013, the first
  half-hour predicting the last) does not appear on CME copper in 2016–2023: ρ to the last half-hour is −0.029.
- **The shape (ρ of x with y at each horizon):**

  | | 10:15 | 11:30 | 15:00 | the 09:16 re-based x |
  |---|---|---|---|---|
  | MHG | −0.01 | −0.02 | −0.03 | −0.02 |
  | SIL | −0.02 | −0.04 | −0.05 | −0.03 |

  So the yuan fix at 09:15 is not the driver.
- **The auction move** (08:55 → 09:01) correlates 0.27–0.37 with x: it is part of x, not separate from it.

## 3. The controls (C3b, C4): reported for all three; they gate nothing on the primaries

Signed margins (sign = C2's direction where C2 passed, else continuation) over a paired month-block bootstrap SE.

| | C3b daylight-saving placebo | C4 Tokyo open (08:00 Beijing) | C4 post-break (10:30) |
|---|---|---|---|
| MHG | −0.91 SE | −0.17 SE | −2.72 SE |
| SIL | −1.75 SE | −0.76 SE | −2.16 SE |
| **MGC (reversal)** | **+3.07 SE** (ρ −0.064 against +0.050) | **+3.31 SE** (against +0.047) | +1.84 SE (against +0.015) |

- **Gold would read UNRESOLVED** (reported only). Its opening reversal beats the daylight-saving and Tokyo placebos by
  more than 3 SE, but the post-break placebo by only 1.84 SE.
- **The 2×2** (ρ; Beijing-aligned against ET-fixed 21:00 ET):

  | | EDT, Beijing | EDT, ET-fixed | EST, Beijing | EST, ET-fixed (= 10:00 Beijing) |
  |---|---|---|---|---|
  | MHG | −0.042 | −0.042 | +0.001 | +0.062 |
  | SIL | −0.021 | −0.021 | **−0.097** | +0.126 |
  | MGC | −0.025 | −0.025 | **−0.142** | +0.084 |

  - **POST HOC:** silver's and gold's reversal sits mostly in the EST months (n about 590, SE about 0.04), when the
    China open is at 20:00 ET. The window an hour later, at 10:00 Beijing, continues instead.
  - This was not a declared split. It is reported as a lead, not a finding.

## 4. The books: all four groups (the traded third; side = continuation on MHG and SIL as declared after C2 failed, reversal on MGC)

| | MHG | SIL | MGC (reversal) |
|---|---|---|---|
| trades | 499 | 456 | 482 |
| **mean gross / net** | **−\$1.28 / −\$5.53** | **−\$16.61 / −\$24.61** | **+\$4.25 / −\$1.69** |
| t gross / t net | −0.46 / −1.99 | −2.07 / −3.07 | 1.61 / −0.64 |
| Sharpe net / gross; Sortino net | −0.76 / −0.18; −1.02 | −1.18 / −0.80; −1.42 | −0.25 / +0.62; −0.34 |
| max drawdown | \$2,906 | \$11,402 | \$1,483 |
| mean \|gross\| vs 2c | \$43.50 (5.1×) | \$106.68 (6.7×) | \$39.76 (3.4×) |
| breakeven cost; the thin-book line | none; net −\$8.03 | none; net −\$34.61 | \$4.25 against \$5.93; net −\$3.69 |
| median net; win rate; payoff | −\$4.25; 45.7%; 0.92 | −\$18.00; 41.9%; 0.87 | −\$2.43; 48.1%; 0.99 |
| skew; kurtosis | 0.19; 4.3 | −1.49; 14.6 | 0.09; 5.4 |
| net ex-top 1% / ex-bottom 1% / trimmed | −7.99 / −3.25 / −5.71 | −31.43 / −14.36 / −21.14 | −4.01 / +0.59 / −1.74 |
| profitable years; net without the best two | 2 of 7; −\$3,646 | 0 of 7; −\$10,250 | 2 of 7; −\$1,256 |
| largest trades | 2022-03-08 +\$340.75; 2021-03-11 −\$269.25 | 2020-08-07 +\$787; 2020-07-28 −\$1,383 | 2022-03-08 +\$337.07; 2020-03-09 −\$301.93 |
| splits (mean net) | EDT −7.14, EST −1.81; Mon −1.16 | EDT −20.78, EST −32.28 | EDT −6.06, **EST +7.62** (154) |
| 2020 night suspension | +\$1.50 (35) | +\$39.33 (30) | −\$11.48 (31) |

- **C5 fails on every cell.**
- **POST HOC, the arithmetic of silver's mirror:** silver's continuation lost \$16.61 gross, so the fade would gross
  +\$16.61 and net +\$8.61 against \$8.00.
  - But without its top 1% of trades it nets −\$1.64, and on the thin-book line it is −\$1.39. Its median is +\$2.00.
  - Its winners would be the 2020 silver trades. It is not a construction, and is recorded so nobody re-derives it.
- MHG's mirror nets −\$2.97.

## 5. The catch-up variant (reported, in no reading): the open reverses the US afternoon, it does not catch up

| | ρ(g, x): CME since SHFE's last close → the opening half-hour | ρ(g, y) | ρ(g_US, y): the US afternoon alone → y |
|---|---|---|---|
| MHG | −0.032 (p 0.21) | +0.017 | +0.005 |
| SIL | **−0.060 (p 0.018)** | +0.011 | +0.047 (p 0.052) |
| MGC | **−0.089 (p 0.001)** | +0.031 | +0.052 (p 0.048) |

- **The sign of the "catch-up" is the opposite of the principal's hypothesis.** Shanghai's first half-hour leans
  against the move CME made while it was shut. It does not extend it. Nothing carries into y.
- **The sign(g) × sign(x) table of mean y:** MHG +\$4.97 when g > 0 and x < 0; SIL +\$11.87 in the same cell.
  These are small samples of a reversal-of-the-reversal, and are not read.

## 6. The component line (prop book; dollars at one micro)

| | net Sharpe / Sortino | hit | skew | gross beside net | ρ D737 twin / NQ F2 / C1 |
|---|---|---|---|---|---|
| MHG (continuation) | −0.76 / −1.02 | 45.7% | 0.19 | −\$1.28 / −\$5.53 | +0.03 / +0.02 / −0.01 |
| SIL (continuation) | −1.18 / −1.42 | 41.9% | −1.49 | −\$16.61 / −\$24.61 | −0.03 / +0.01 / −0.02 |
| MGC (reversal) | −0.25 / −0.34 | 48.1% | 0.09 | +\$4.25 / −\$1.69 | +0.03 / +0.08 / +0.03 |

- The clock is uncorrelated with the ledger, as expected. None of the three is a component.

## 7. The reading

- **Declared:** MHG **NO DIRECTION**, SIL **NO DIRECTION**, GO false. MGC (reported) would read UNRESOLVED, with no
  prize: \$4.25 gross against \$5.93.
- **What was learned:**
  1. **The China open is a real event on CME metals.** The opening half-hour is 34–59% larger when Shanghai trades,
     and 1.5–1.8× after its long holidays. It co-moves with the AUD (ρ 0.30–0.35).
  2. **It has no carry-on.** Jin et al.'s SHFE continuation does not cross to CME copper in 2016–2023. The sign that
     appears is reversal, of both the opening half-hour (gold, borderline silver) and the US-afternoon move (gold,
     silver). That is the repo's off-hours pattern again (D499): the thin overnight book reverses, by less than a
     round trip.
  3. **Only gold's reversal beats a placebo,** and it grosses \$4.25 against \$5.93.
  4. **POST HOC leads, not findings:** the EST-month concentration of the silver and gold reversal, and the mirror
     arithmetic of the silver fade. Both are recorded so they are not re-derived as discoveries.
- **Recommendation:** close D765's line for the prop book. A fade of the China open is the only construction left in
  it, and on gold, its best cell, it does not pay the round trip. Closing it is the principal's call.

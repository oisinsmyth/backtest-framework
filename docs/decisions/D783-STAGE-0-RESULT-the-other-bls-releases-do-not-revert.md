# D783 STAGE 0 RESULT — NO EFFECT in every cell: the other BLS releases at 08:30 do not revert like CPI and the jobs report. PPI's +$15.51 is 2022 alone, the year PPI was a headline inflation print

*2026-10-03. One run of `scripts/stage0_d783_bls_0830_fade.py --run` (72 seconds).*
- **The order:** the [pre-registration](D783-STAGE-0-PRE-REG-fade-the-other-bls-0830-releases.md) (`512ba435`) came
  before the runner (`20f457ab`), and the runner before its one run. The calendar is [D782](D782-FIXTURE-the-other-bls-releases-at-0830.md).
- **Output:** `data/stage0_d783_bls_0830_fade.json` (statistics only).

## 0. Checks

- **The imported study reproduced D775's primary first:** 186 trades, mean gross +\$34.88.
- **The panel:**
  - 192 CPI/EMPSIT sessions dropped;
  - every cell's day count as declared (96/96/64/32/288), and no cell on a CPI/EMPSIT day.
- **D775's own assertions ran inside each study:**
  - the lag audit (40 sampled release days, an explicit-loop second implementation);
  - rotation offset 0;
  - read = used + exclusions;
  - the placebo differs from the treatment;
  - the loader's seal at 2024-01-01.
- **The self-test:**
  - the calendar loader keeps only in-window 08:30 rows of the cell;
  - the removal drops exactly the named sessions;
  - D775's sign audit raises on a mirrored book.

## 1. The cells

| cell | root | days used | mean gross (t) | rotation p50 / p95; rank | reading |
|---|---|---|---|---|---|
| **PPI (primary)** | **MNQ** | 95 | **+\$15.51 (1.22)** | −\$3.34 / +\$21.98; 0.890 | **NO EFFECT** |
| PPI | MES | 89 | +\$1.08 (0.14) | −\$1.10 / +\$14.01; 0.592 | NO EFFECT |
| PPI | MYM | 93 | −\$0.75 (−0.11) | +\$1.24 / +\$12.16; 0.389 | NO EFFECT |
| PPI | M2K | 70 | −\$2.49 (−0.31) | +\$1.25 / +\$13.71; 0.330 | NO EFFECT |
| IMPEXP | MNQ | 91 | +\$10.53 (0.70) | −\$3.64 / +\$21.71; 0.804 | NO EFFECT |
| PROD | MNQ | 64 | −\$17.62 (−0.77) | −\$3.41 / +\$25.40; 0.220 | NO EFFECT |
| ECI | MNQ | 31 | −\$22.13 (−0.69) | −\$3.82 / +\$39.30; 0.234 | NO EFFECT |
| ALL (pooled) | MNQ | 281 | +\$2.20 (0.24) | −\$2.99 / +\$10.11; 0.744 | NO EFFECT |

- **The readings:** NO EFFECT everywhere (G1 fails first). GO false.
- **The pre-registered decision (§4) applies:** PPI failed G1 and N, and the pool failed N. **So the Census, BEA and DOL
  schedules are not fetched;** on this evidence the effect is specific to CPI and the jobs report.
- **PPI on MNQ with D775's days kept** is unchanged at +\$15.51 (rotation p95 +\$25.61, rank 0.844): NO EFFECT.
- **The predictions:**
  - "PPI +\$8 to +\$15, t near 1; G1 at risk": right.
  - "The minor releases NO EFFECT": right.
  - "The high-|x| tercile carries the PPI cell": right in sign (+\$30.97 against +\$2.75 low), but nothing is
    significant.

## 2. PPI on MNQ: what the +$15.51 is

- **It is 2022.** By year:

| 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | **2022** | 2023 |
|---|---|---|---|---|---|---|---|
| −\$4.04 | −\$8.92 | +\$5.67 | −\$0.25 | −\$40.77 | +\$16.38 | **+\$148.62** (12 trades, 83% won) | +\$2.71 |

  - **Without 2022 the mean gross is −\$3.73.** The top five trades include four from 2022 (2022-05-12 +\$571).
- **The mechanism's signature is there, but small:**
  - the part before the cash open lost −\$6.36 (t −1.17);
  - the part after it earned +\$21.87 (t 1.78);
  - the 09:30 entry, declared secondary and not gated, earned +\$21.87 gross (t 1.78).
- **The null controls:**
  - the year × weekday draws ranked 0.928 (p95 +\$18.32, SE 0.42);
  - the year × impulse-decile draws ranked 0.919 (p95 +\$19.29, SE 0.34).
  - Not decisive.
- **The principal's year test passed on the win-rate branch** (6 of 8 years at 50% or more). The volatility-adjusted
  branch failed: 2016–19 −0.065 against 2020–23 +0.149.

## 3. All four groups (PPI × MNQ)

| | |
|---|---|
| mean gross / net; median net | +\$15.51 / +\$11.44; +\$2.93 |
| net Sharpe / Sortino; gross Sharpe | 0.34 / 0.57; 0.45 |
| exposure; maximum drawdown; total net | 5.2% of days; \$1,156; +\$1,087 |
| mean \|move\| against the round trip; breakeven cost | \$88.06 against \$4.07; \$15.51 |
| win; payoff; skew; kurtosis | 51.6%; 1.27; +0.96; 3.82 |
| net ex-top 1% / ex-bottom 1% / trimmed | +\$5.48 / +\$14.29 / +\$8.30 |
| impulse sign | up +\$22.67 (36); down +\$11.14 (59) |
| \|x\| terciles | +\$2.75 / +\$12.73 / +\$30.97 |
| five largest / worst, net | 2022-05-12 +\$571, 2022-01-13 +\$289, 2022-11-15 +\$248, 2021-05-13 +\$232, 2022-04-13 +\$229 / 2021-12-14 −\$257, 2023-04-13 −\$249, 2022-03-15 −\$246, 2021-01-15 −\$226, 2018-10-10 −\$192 |
| component line, daily ρ | D737's twin +0.009, NQ F2 +0.069, C1 +0.029 |
| G2 | net t 0.90; net −\$795 without 2021–22; mean gross without 2022 −\$3.73 |

## 4. The reading

- **Declared:** NO EFFECT in every cell. GO false. The Census/BEA/DOL extension is not recommended.
- **What it says about D775's mechanism:**
  - The fade is not a general property of 08:30 releases.
  - It appears where the release is the market's focus: CPI and the jobs report always, and PPI in 2022, when
    inflation was the market's question. That is consistent with the mechanism (a large, attention-driven headline
    impulse that the cash open re-prices), but it is a reading after the fact. "When is a release the focus" was not
    pre-registered, and a rule for it would have to be stated before it is tested.
  - It does not weaken D775's in-sample result, and D776's vault read is unchanged. Nothing after 2023 was read.
- **Recommendation:** close the BLS-extension construction, and do not source the Census, BEA or DOL schedules for
  this line. Both are the principal's call.

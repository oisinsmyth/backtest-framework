# D780 STAGE 0 RESULT — NO PRIZE: gold's weekend reopen fade passes the principal's year test, but without 2020 it nets +$2.73 a trade, and five Mondays are 91% of its net. Base L4 is the stronger slot-10 candidate on every comparison

*2026-10-03. One run of `scripts/stage0_d780_gold_weekend_reopen_fade.py --run` (34 seconds).*
- **The order:** the [pre-registration](D780-STAGE-0-PRE-REG-fade-gold-s-weekend-reopen-on-mgc.md) (`50d264d5`) came
  before the runner (`2e5cd6c4`), and the runner before its one run.
- **Output:** `data/stage0_d780_gold_weekend_reopen_fade.json` (statistics only).

## 0. Checks

- **The counts:** 410 Monday sessions 2016–2023, of which 384 were scored. 6 roll weekends were dropped, and 20 had a
  missing price or m = 0.
- **The pair's version reproduced exactly** (roll weekends kept): n 390, +\$15.93, t 2.31.
- **Right quantity:**
  - every scored session is a Monday;
  - the primary differs from the pair's version only on roll weekends;
  - rotation offset 0 equals the observed;
  - nothing on or after 2024-01-01.
- **The lag audit:** an explicit-loop second implementation re-derived the prior close, m, the contract check, the
  side and the fade on 40 sampled Mondays; all equal.
- **Base L4 reproduced D778's base book** (280 trades, +\$15.84) for the component line and the power.
- **The self-test:**
  - a planted reversion passes G1 and N; a continuation fails G1;
  - a roll weekend is dropped; an evening row dated the session itself is dropped;
  - the second implementation raises on a broken side;
  - chunk = whole; the power function; the whole study runs end to end.

## 1. The gates

| | value | gate |
|---|---|---|
| **G1** | **384 trades, +\$15.47 gross / +\$9.54 net, t 2.21** | pass |
| **N** (exact rotation, 383 offsets) | p50 −\$0.28, p95 +\$10.57, rank 0.995 | pass |
| **Y** | win ≥ 50% in 7 of 8 years; volatility-adjusted > 0 in 8 of 8; 2016–19 0.12 against 2020–23 0.19 | **pass** (both branches) |
| **G2** | **net t 1.37**; net +\$385 without 2019 and 2020; **mean gross without 2020 +\$8.66**; trimmed +\$12.16 (bar \$11.86) | **fail** (net t; without the best year) |

**Reading: NO PRIZE. GO false.** The predictions held: G1 and N passed, G2 failed, and Y was the open gate (it passed).

## 2. What the edge depends on

**2020 and five Mondays:**

| | all | without 2020 |
|---|---|---|
| trades | 384 | 335 |
| mean gross / net | +\$15.47 / +\$9.54 | **+\$8.66 / +\$2.73** |
| net t | 1.37 | **0.44** |
| trimmed mean, net | +\$6.23 | **+\$0.19** |

- **2020 earned +\$62.04 a trade** (49 Mondays). The other years earned +\$3.17 to +\$16.98.
- **The five largest Mondays are 91% of the total net:**
  - 2020-11-09 +\$1,001 (the vaccine announcement);
  - 2023-12-04 +\$947 (the Sunday spike and collapse);
  - 2022-06-13 +\$503;
  - 2020-03-16 +\$475; 2020-04-06 +\$425.
  - Net without the top 1% is +\$1.94; the median net is +\$2.07.
- **So the year test passes on direction, not on size.** Most Mondays are a little positive. The money is a handful
  of news weekends.

**The legs (fade \$ per MGC, all scored Mondays):**

| | 19:00 → 21:00 | 21:00 → 03:00 | 03:00 → 11:00 |
|---|---|---|---|
| all years | +3.01 (t 1.50) | +6.65 (t 2.25) | +5.81 (t 1.00) |
| without 2020 | +2.64 | +5.92 | **+0.10** |

- **The London/New York leg is zero without 2020,** confirming the documentation session's figure. 2020 alone put
  +\$44.84 a Monday into it.
- **The Asian session (21:00 → 03:00) is the steadiest leg,** positive in 7 of 8 years. It is the leg that overlaps
  D765's China-open reversal. The pair's kill list required the reopen's first two hours to be positive: they are,
  at +\$3.01 but t 1.50.

**The Monday drift and the sides:**
- Gold fell from Sunday 19:00 to Monday 11:00 by \$8.78 a Monday on average (in MGC dollars).
- So fading a weekend rise (short) earned +\$24.77 and fading a fall (long) +\$6.56. Net of the drift, the two sides
  are equal (+\$16.0 and +\$15.3). The fade is symmetric; the drift tilts it.

**Size:** |m| terciles +\$0.45 / +\$9.73 / +\$36.23 gross. The large weekend moves carry it.

## 3. All four groups

| | |
|---|---|
| mean gross / net; median net | +\$15.47 / +\$9.54; +\$2.07 |
| net Sharpe / Sortino; gross Sharpe | 0.48 / 0.83; 0.77 |
| exposure; maximum drawdown; total net | 18.6% of sessions; \$1,517; +\$3,665 |
| mean \|move\| against the round trip; breakeven cost | \$84.43 against \$5.93; \$15.47 |
| win; payoff; skew; kurtosis | 54.4%; 1.18; +1.90; 13.86 |
| net ex-top 1% / ex-bottom 1% / trimmed | +\$1.94 / +\$13.87 / +\$6.23 |
| by year, gross (win) | 2016 +\$7.00 (51%), 2017 +\$3.98 (57%), 2018 +\$3.17 (50%), 2019 +\$16.98 (60%), **2020 +\$62.04** (61%), 2021 +\$12.59 (55%), 2022 +\$7.08 (54%), 2023 +\$9.49 (47%) |
| five worst | 2020-09-21 −\$564, 2022-04-25 −\$361, 2020-08-17 −\$341, 2020-07-27 −\$339, 2021-01-04 −\$305 |
| reported variants | the 09:29 exit +\$12.67 (t 2.06); **the q80 gate +\$39.42 (151 trades, t 2.77, net t 2.36)** |

- **The q80 variant is not a candidate here.**
  - It was reported, not gated, and the pair saw its in-sample numbers before this record.
  - Choosing it now would be selection after seeing.
  - It is the same 2020-heavy book with the small Mondays removed (the |m| terciles above).
- **The component line:** daily ρ with base L4 +0.026, D775 −0.002, D777's MNQ book −0.014, D737's twin −0.045,
  NQ F2 −0.003, C1 +0.038.

## 4. Slot 10: L3 against base L4

**On the same gate and the same power calculation:**

| | L3 (MGC) | base L4 (M2K) |
|---|---|---|
| in-sample trades; per-trade sd | 384; \$137.00 | 280; \$107.36 |
| net per trade; net t | +\$9.54; 1.37 | +\$12.08; 1.88 |
| best year; net without it | 2020; **+\$2.73** | 2020; **+\$6.32** |
| the year test (Y) | pass (7/8 win, 8/8 volatility-adjusted) | pass (5/6 win) |
| net Sharpe / Sortino | 0.48 / 0.83 | 0.81 / 1.25 |
| vault trades, 2024-01-01 → 2026-09-18 (est.) | 131 | 133 |
| **P(pass), true edge = in-sample net** | **31%** | **51%** |
| **P(pass), true edge = net without the best year** | **15%** | **27%** |
| P(pass), true edge = zero | 10% | 10% |

- The gate is a D776-style one (≥ 40 trades, net > 0, one-sided t ≥ 1.2816), by normal approximation.
- D776's rotation-p95 gate is not modelled, so both figures are slightly optimistic.
- **Base L4 is ahead on every row except the year test,** where both pass. Their ρ is +0.026, so they would
  diversify each other, but there is one slot.

## 5. The reading

- **Declared:** NO PRIZE. GO false.
- **What L3 is:** a weekend-news reversion in gold, real by its null (rank 0.995) and positive in direction most
  years. Its size above the cost comes from 2020 and a handful of news Mondays.
- **Recommendation:**
  - L3 does not take slot 10 over base L4. Keep it as an open lead, a measurement, with 2020 as its carrier.
  - If slot 10 is to be filled, base L4 is the candidate. Its freeze would need a pre-registration and an RTY build of
    the vault fixture.
  - Both are the principal's call.

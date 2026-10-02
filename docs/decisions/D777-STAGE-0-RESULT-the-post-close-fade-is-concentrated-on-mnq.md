# D777 STAGE 0 RESULT — CONCENTRATED on MNQ, NO EFFECT on MES, M2K and MYM; GO false: the post-close hour does give back overnight (exact null rank 0.998, b_m t −3.25), but on NQ it misses the principal's year test by one year on each branch, and no confirmable root reaches t 2

*2026-10-02. One run of `scripts/stage0_d777_post_close_fade.py --run` (22 seconds).*
- **The order:** the [pre-registration](D777-STAGE-0-PRE-REG-fade-the-post-close-hour-of-the-index-futures.md)
  (`9a31ffb9`) came before the runner (`3c41cdb0`), and the runner before its one run.
- **Output:** `data/stage0_d777_post_close_fade.json` (statistics only).
- **The in-sample data had been read before this record (D772).** A pass would have fixed the construction, not proved
  it.

## 0. Checks

- **Sessions read = traded + gated out + each exclusion,** asserted per root:

| root | sessions | traded | gated out | warm-up | zero move | missing bar | no next session |
|---|---|---|---|---|---|---|---|
| NQ | 2,062 | 409 | 1,439 | 118 | 23 | 72 | 1 |
| ES | 2,062 | 407 | 1,407 | 120 | 60 | 67 | 1 |
| RTY | 1,671 | 294 | 1,110 | 81 | 30 | 155 | 1 |
| YM | 2,062 | 396 | 1,429 | 119 | 36 | 81 | 1 |

- **The lag audit:** an explicit-loop second implementation re-derived m, the threshold, the gate, the side and the
  fade on 40 sampled trades per root from the raw rows; all equal.
- **D775's book was rebuilt from these bars with D775's own functions,** and asserted at 186 / +\$34.88, for the overlap
  ρ.
- **Right quantity:**
  - rotation offset 0 equals the observed on every root;
  - the gated book differs from the ungated one;
  - nothing on or after 2024-01-01.
- **The self-test:**
  - a Friday pairs with Monday;
  - a planted reversal passes G1, N and M, and a continuation fails G1;
  - a huge same-day |m| leaves that day's threshold unchanged;
  - the second implementation raises on a broken side;
  - chunk = whole;
  - the sign audit raises on a mirrored book.

## 1. The gates

| root | G1: mean gross, t | N: exact rotation p50 / p95, rank | M: b_m (HC1 t); b_day; b_aft | Y | G2 | reading |
|---|---|---|---|---|---|---|
| **MNQ** | **+\$24.99, t 2.41** | −\$1.33 / +\$13.43, **0.998** | **−0.390 (−3.25)**; +0.041 (+1.34); −0.124 (−2.10) | **fail** (5 of 7 years, need 6, on both branches) | pass | **CONCENTRATED** |
| MES | +\$10.90, t 1.58 | −\$0.75 / +\$9.33, 0.971 | −0.295 (−1.90) | fail | fail | NO EFFECT |
| M2K | +\$10.90, t 1.89 | −\$0.53 / +\$7.93, 0.984 | **−0.331 (−2.17)** | fail | fail | NO EFFECT |
| MYM | +\$8.48, t 1.30 | −\$1.40 / +\$6.26, 0.974 | −0.246 (−1.42) | fail | fail | NO EFFECT |

**GO is false.** MNQ is not SUPPORTED, and no confirmable root (M2K or MYM) passes G1, N and M. M2K misses on G1 alone
(t 1.89).

- **MNQ's Y in detail** (full years 2017–2023):
  - (i) win rate ≥ 50% in 5 of 7 (2017 47.1%, 2020 48.7%);
  - (ii) volatility-adjusted mean > 0 in 5 of 7 (2017 −0.10σ, 2020 −0.07σ), and the halves are 0.072σ against
    0.121σ (the ratio would pass).
  - It fails both branches by one year.
- **MNQ's G2 passes:**
  - net +\$20.92 (t 2.02);
  - +\$1,739 without 2021 and 2022;
  - +\$13.30 gross without 2022;
  - trimmed +\$24.63, against a bar of \$8.14.
- **The predictions:**
  - MNQ G1, N and M: right.
  - "The risk is Y and G2": Y failed; G2 passed as predicted.
  - M2K G1, N and M: G1 missed (t 1.89, the stated risk).
  - MYM fails: right.

## 2. What the effect is (all four roots agree on its shape)

| | MNQ | MES | M2K | MYM |
|---|---|---|---|---|
| **fading a post-close FALL** (long overnight) | **+\$58.32 (t 3.25, 172)** | +\$21.36 (1.84) | **+\$24.99 (2.89)** | +\$15.38 (1.36) |
| fading a post-close rise (short) | +\$0.80 (0.07, 237) | +\$2.28 | −\$0.90 | +\$4.28 |
| \|m\| top tercile | **+\$70.89 (3.07)** | +\$27.11 (1.65) | **+\$32.56 (3.17)** | +\$22.91 (1.60) |
| \|m\| low / mid terciles | +\$5.77 / −\$1.55 | +\$5.06 / +\$0.45 | +\$6.21 / −\$6.06 | −\$5.28 / +\$7.83 |
| q90 gate: mean, t, rotation rank | +\$42.93, 2.81, 0.9995 | +\$23.10, 2.03, 0.996 | +\$19.26, 2.47, 0.994 | +\$10.88, 1.09, 0.964 |
| hold split: 18:05 → 09:30 / 09:30 → 10:00 | +\$20.52 (2.34) / +\$6.51 (1.18) | +\$8.94 / +\$4.38 | +\$7.58 / +\$3.33 | +\$7.13 / +\$1.87 |
| leg B (09:30 → 11:00) alone: mean, rotation rank | +\$8.55, 0.889 | +\$6.45, 0.949 | +\$0.54, 0.539 | +\$0.94, 0.630 |
| placebo: the 18:05 → 20:00 move faded the same way | +\$2.91 (0.30) | −\$0.32 | +\$0.18 | −\$2.26 |

- **The give-back is real and specific to the post-close hour.** The cash-shut placebo is zero on every root, and every
  root beats its exact rotation (0.971–0.998).
- **The mechanism is right-signed on all four** (b_m −0.25 to −0.39, against an afternoon b of −0.10 to −0.12, and a
  day b ≥ 0).
- **It is a large-move effect.** The top |m| tercile carries it everywhere; the lower two are about zero.
- **It is almost all on falls.** Fading a post-close fall (buying it) earns; fading a rise earns about nothing. The same
  asymmetry appeared in D775 (down impulses +\$50.52 against +\$22.55).
  - A long-only overnight leg also collects the overnight drift, and this test cannot separate the two.
  - The rotation null keeps the side mix (a net short tilt, 237 rises against 172 falls on NQ) and still ranks it at
    0.998. So the drift is not the whole of it, but the asymmetry is not explained.
- **It happens overnight, not at the open.** The 09:30 → 11:00 leg alone stays inside its null on every root.

## 3. When it worked (MNQ)

| | n | mean gross | win | volatility-adjusted |
|---|---|---|---|---|
| 2016 (partial) | 16 | +\$8.31 | 62.5% | +0.08σ |
| 2017 | 51 | −\$3.96 | 47.1% | −0.10σ |
| 2018 | 89 | +\$10.57 | 50.6% | +0.12σ |
| 2019 | 40 | +\$22.45 | 55.0% | +0.17σ |
| 2020 | 76 | +\$0.51 | 48.7% | −0.07σ |
| 2021 | 43 | +\$38.58 | 65.1% | +0.19σ |
| 2022 | 60 | **+\$92.96** | 58.3% | +0.29σ |
| 2023 | 34 | +\$34.57 | 58.8% | +0.17σ |

**The exchange's settlement clock** (all roots agree):

| period | MNQ | MES | M2K | MYM |
|---|---|---|---|---|
| before 2020-10-26 (16:15 settle, halt) | +\$12.12 (264) | +\$5.69 | +\$12.60 | +\$4.47 |
| 2020-10-26 → 2021-06-25 (16:00 settle, halt) | −\$20.36 (29) | −\$41.12 | +\$3.88 | −\$32.93 |
| **after 2021-06-25 (no halt)** | **+\$65.62 (t 2.72, 116)** | **+\$35.54 (2.52)** | +\$10.80 | **+\$25.68 (2.30)** |

- **On the index roots it is mostly a post-2021-06 effect.** That period holds 2022. The pair's natural-experiment
  reading (the transient moved with the exchange's clock) fits, but it is confounded with 2022's volatility.
- **By weekday (MNQ):** Tuesday nights +\$52.80 (t 2.20), Thursday +\$41.12 (2.17), Monday −\$4.52, Wednesday +\$5.08,
  Friday (a weekend hold) +\$12.11. Thursday is the strongest night on MES and MYM too. This is the pair's flagged
  conditioner, reported and not gated.

## 4. The four groups (MNQ)

| | |
|---|---|
| mean gross / net; median gross / net | **+\$24.99 / +\$20.92**; +\$9.00 / +\$4.93 |
| net Sharpe / Sortino (daily); gross Sharpe | **0.74 / 1.21**; 0.89 |
| maximum drawdown; total net (2016–23) | **\$2,054**; +\$8,556 |
| exposure (sessions traded) | 22.1% (about 51 a year) |
| mean \|gross\| against the cost; breakeven | \$141.24 against \$4.07; \$24.99 |
| win; payoff; skew; kurtosis | 54.0%; 1.22; +0.41; 3.08 |
| net ex-top 1% / ex-bottom 1% / trimmed | +\$13.48 / +\$28.00 / +\$20.56 |
| five largest | 2022-01-25 +\$891.93, 2020-03-20 +\$799.43, 2020-03-12 +\$706.93, 2022-03-08 +\$696.43, 2022-04-05 +\$688.43 |
| five worst | 2020-03-13 −\$832.57, 2021-03-08 −\$705.57, 2022-05-04 −\$684.57, 2022-10-06 −\$559.57, 2020-11-04 −\$519.07 |

- **The component line:** daily ρ with D775's book +0.077 (36 trades fall on the night before a D775 release); with
  D737's twin −0.032; with NQ F2 +0.100; with C1 −0.012.
- **The drawdown is twice D775's** (\$2,054 against \$1,036), on twice the trades.

## 5. The reading

- **Declared:**
  - MNQ CONCENTRATED; MES, M2K and MYM NO EFFECT. **GO false.**
  - It does not go to a vault slot. M2K and MYM, the roots where a confirmation would be possible, do not pass G1.
- **What it established:**
  1. **The post-close hour of the index futures gives back overnight.** That is real on every root: an exact null rank
     0.97–0.998, the regression's b_m negative everywhere, and a cash-shut placebo of zero.
  2. **Its money is in large post-close falls, held overnight,** and mostly since the exchange removed the 16:15 halt
     (2021-06).
  3. **On MNQ it fails the principal's year test by one year on each branch,** with 2017 and 2020 below water.
- **Not tested, and post hoc if pursued** (each was seen in this run):
  - the fall-only side;
  - the q90 gate;
  - the post-2021-06 regime;
  - the Tuesday/Thursday nights.
  - The rules for any of them would be chosen on this data, and the only unread data that could confirm the overnight
    hold is M2K's and MYM's 2024+.
- **Recommendation:** close the post-close fade as a construction, and keep the mechanism finding. Closing is the
  principal's call.

## ADDENDUM, 2026-10-02 — the breakdowns NET of cost

*The principal: "Are those all gross figures? No net?"; "Add the net breakdown to D777 as an addendum".*

- **Where the numbers come from:** §1–§3's splits are gross. Each figure below is derived from
  `data/stage0_d777_post_close_fade.json` with no new run.
  - net = gross − the root's fixed round trip (MNQ \$4.07, M2K \$3.76, MES \$4.42, MYM \$3.80).
  - Each net t = gross t × (mean − cost) / mean. That is exact, because a fixed cost leaves the standard deviation
    unchanged.
- **Already net in §1 and §4:** G2, the Sharpe and Sortino, the drawdown and the totals.
- **The hold split (§2) is not netted:** the cost is paid once per trade, not per leg.

**Headline (one micro a trade):**

| root | mean net (t) | median net | trimmed net | net Sharpe / Sortino | total net 2016–23 | max drawdown |
|---|---|---|---|---|---|---|
| **MNQ** | **+\$20.92 (2.02)** | +\$4.93 | +\$20.56 | 0.74 / 1.21 | +\$8,556 | \$2,054 |
| M2K | +\$7.14 (1.24) | +\$1.99 | +\$7.32 | 0.53 / 0.79 | +\$2,100 | \$992 |
| MES | +\$6.48 (0.94) | +\$6.83 | +\$6.59 | 0.35 / 0.51 | +\$2,639 | \$2,709 |
| MYM | +\$4.68 (0.72) | −\$2.05 | +\$4.28 | 0.27 / 0.41 | +\$1,855 | \$1,989 |

**MNQ by year, net (t):** 2016 (partial) +\$4.24 (0.29); 2017 −\$8.03 (−1.03); 2018 +\$6.50 (0.54); 2019 +\$18.38
(1.01); 2020 −\$3.56 (−0.14); 2021 +\$34.51 (0.93); 2022 +\$88.89 (2.21); 2023 +\$30.50 (0.93).

**The splits, net (t):**

| split | MNQ | M2K | MES | MYM |
|---|---|---|---|---|
| fading a post-close FALL | **+\$54.25 (3.02)** | **+\$21.23 (2.46)** | +\$16.94 (1.46) | +\$11.58 (1.02) |
| fading a post-close rise | −\$3.27 (−0.29) | −\$4.66 (−0.62) | −\$2.14 (−0.26) | +\$0.48 (0.06) |
| \|m\| top tercile | **+\$66.82 (2.89)** | **+\$28.80 (2.80)** | +\$22.69 (1.38) | +\$19.11 (1.33) |
| \|m\| low / mid terciles | +\$1.70 / −\$5.62 | +\$2.45 / −\$9.82 | +\$0.64 / −\$3.97 | −\$9.08 / +\$4.03 |
| before 2020-10-26 | +\$8.05 (0.78) | +\$8.84 (1.19) | +\$1.27 (0.16) | +\$0.67 (0.08) |
| 2020-10-26 → 2021-06-25 | −\$24.43 (−0.44) | +\$0.12 (0.01) | −\$45.54 (−1.58) | −\$36.73 (−1.07) |
| after 2021-06-25 | **+\$61.56 (2.55)** | +\$7.04 (0.70) | **+\$31.12 (2.21)** | +\$21.88 (1.96) |
| first half / second half | +\$4.96 (0.71) / +\$35.60 (1.89) | +\$9.41 (1.69) / +\$6.08 (0.75) | +\$6.36 (1.26) / +\$6.60 (0.52) | −\$1.78 (−0.39) / +\$11.22 (0.92) |
| Tuesday / Thursday nights | +\$48.73 (2.03) / +\$37.05 (1.96) | +\$3.44 / +\$15.71 | +\$7.56 / **+\$32.49 (2.29)** | +\$0.33 / **+\$29.59 (2.45)** |
| Monday / Wednesday / Friday nights | −\$8.59 / +\$1.01 / +\$8.04 | −\$17.25 / +\$14.89 / +\$12.58 | −\$19.84 / +\$4.76 / −\$6.56 | −\$1.74 / +\$11.36 / −\$17.82 |
| the q90 gate | +\$38.86 (2.54) | +\$15.50 (1.99) | +\$18.68 (1.64) | +\$7.08 (0.71) |
| leg B (09:30 → 11:00) alone | +\$4.48 (0.54) | −\$3.22 (−0.72) | +\$2.03 (0.43) | −\$2.86 (−0.73) |
| the 18:05 → 20:00 placebo | −\$1.16 | −\$3.58 | −\$4.74 | −\$6.06 |

**What net adds to §5's reading:**
- **Fading a post-close rise loses after cost** on MNQ, M2K and MES, and is about zero on MYM. The tradeable side is the
  fall alone: +\$54.25 a trade on MNQ, +\$21.23 on M2K.
- **The lower two |m| terciles net about zero or less on every root.** All the net is in the top third.
- **Before 2020-10 the net is thin on the index roots** (MNQ +\$8.05; MES and MYM about \$1). After 2021-06 it is
  +\$22 to +\$62 on three of the four roots.
- **Each of these splits was seen in this run,** so a rule built on any of them would be chosen on this data. The
  reading (CONCENTRATED, GO false) and the recommendation are unchanged.

# D761 STAGE 0 RESULT — NO PROFILE on M6E and MBT as declared; on clean 6E data (POST HOC) round levels do carry the stop-band profile, but the move is a third of the bar, so nothing pays

*2026-10-02. One run of `scripts/stage0_d761_round_number_cascades.py --run` (2.13 minutes), then one POST HOC re-run
from 2016 (2.1 minutes).*
- **The order:** the [pre-registration](D761-STAGE-0-PRE-REG-round-number-stop-cascades.md) (`aa6888e9`) came before
  the runner (`35c90643`); the runner's fix (`1d3519e4`) came before the scored run. The declared output and the
  POST HOC flag (`d891a74d`) were committed before the re-run.
- **Outputs:** `data/stage0_d761_round_number_cascades.json` (declared) and
  `data/stage0_d761_round_number_cascades_posthoc_since2016.json` (POST HOC). Statistics only.
- **The priors were:** M6E about 10–15%, MBT about 20%, MGC about 6%, and the premise gate passing on M6E about 55%.

## 0. Checks and disclosures

- **A first `--run` stopped before any statistic.**
  - MBT's lag canary found an empty selection, because the BTC fixture's timestamps parsed at microsecond resolution:
    every MBT bar fell in 1970.
  - The same session showed that 6E's basis covered only 2,219 of 3,491 sessions, because the next contract trades
    thinly early in the cycle.
  - Both were fixed in `1d3519e4` before the scored run. Only the cells' session counts had been printed.
  - **The basis rule changed in that fix:** a session without 10 matched front/next minutes carries the same front
    contract's latest measured carry rate × its own days to expiry, never across a roll. The result is 2,219 measured
    sessions, 1,104 carried, and 3,323 of 3,491 covered.
- **Sessions:**
  - M6E: 3,491 (3,323 with a basis, 218 in the excluded roll week);
  - MBT: 1,551 (1,500 with a basis; median CME − Binance basis \$30);
  - MGC: 3,487.
- **The seal:** no kept row is dated on or after 2024-01-01.
- **The clock:** zoneinfo against the statutory rule on every bar.
- **Lag:**
  - the vectorised crossing detector equals the loop implementation on 40 sampled sessions per cell;
  - the canary (Lens A's filter including bar b) changed the selected set in every cell;
  - the basis reads only the prior session.
- **Sign, in money:** an up-cross that keeps rising pays the long. The audit raises on a mirrored book.
- **Speed:** all 300 grid offsets (50 M6E, 100 MBT, 100 MGC, 50 futures-grid 6E) ran on 8 processes. Chunk ==
  whole was proved by a serial recompute of (M6E, 0) and (MBT, 100).
- **The self-test passes:** Lens A ≠ Lens B on a known event, the grid arithmetic, 6E roll and expiry, and Holm.

## 1. A data defect found after the run: 6E's off-market prints before 2016

The trades were examined after the run. M6E NY pm lost \$14 a trade gross on EVERY grid; 40% of its trades exited on
the crossing minute, losing \$32 each. The cause is in the data, not the runner.

| 6E front one-minute bars | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017–23 (each) |
|---|---|---|---|---|---|---|---|---|
| high or low 20+ pips beyond BOTH neighbouring closes | 5,960 | 12,315 | 9,126 | 6,717 | 5,947 | 7,117 | 35 | 2–17 |
| off-market close (20+ pips from both neighbours) | 482 | 880 | 916 | 667 | 817 | 727 | 21 | 0–6 |

- **What they look like:** often one stale price repeated across minutes. On 2010-06-07, 18:48–18:52, a high of 1.1966
  appears three times. On 2011-10-10 at 13:11, a bar opened about 270 pips above the prior minute's close and closed at it.
- **The likely cause** is CME calendar-spread leg prints, which were priced off the outright market before about
  2015. This is not verified.
- **The other cells:** BTC has 0 such bars (at a $1,000 threshold) and GC 34 in 14 years (at $10). **MBT's and MGC's readings are clean.**
- **What it does to M6E 2010–15:**
  - phantom crossings and touches;
  - Lens A fills at an off-market open;
  - range-based speed filters read the spikes.
  - **M6E's declared reading below is computed on contaminated data.** It stands as the declared reading, and §3
    reports the clean-era re-run beside it.
- **D755** (closed) read only 6E opens and closes. About 0.25% of 2010–15 bars carry an off-market close, and its
  treatment and placebo hours are equally exposed. Its reading is unlikely to move, but it was read on the same
  archive.

## 2. The premise gate (no P&L): round levels do not bounce more than half-round ones

| cell (Asia, declared) | round bounce | half-round bounce | excess | SE | gate |
|---|---|---|---|---|---|
| M6E | 61.9% (2,586) | 62.9% (2,699) | **−1.00 pp** | 1.33 | UNRESOLVED |
| MBT | 46.0% (1,650) | 48.3% (1,616) | **−2.33 pp** | 1.75 | UNRESOLVED |
| MGC (reported) | 54.3% | 56.0% | −1.72 pp | 0.78 | UNRESOLVED |
| 6E futures grid (reported) | 59.7% | 62.4% | −2.67 pp | 1.26 | UNRESOLVED |

- **No cell passes or fails as declared.** FAIL needs an excess below 1 point with an SE under 0.5, and Asia alone
  cannot reach that SE.
- **POST HOC, all four windows pooled** (binomial SE; touches within a session are correlated, so these SEs are too
  small):
  - M6E −0.60 (0.53);
  - MBT −1.55 (0.92);
  - MGC −1.95 (0.37);
  - 6E futures −0.59 (0.51).
  - From 2016: M6E −0.75 (0.83), MGC −1.64 (0.48).
- **Every point estimate has the wrong sign for Osler's take-profit wall** (+1.5 to +4.5). At a 15-minute horizon,
  round levels are broken through slightly MORE often than half-round ones, not bounced from.

## 3. The profile (the reading): exact enumeration of every grid offset, SE 0

Lens A s = 2 mean signed gross per trade, Asia, fast approach.

| cell | round | half-round | eligible offsets p50 / p95 | rank | stop band (excl. 0) vs outside it (descriptive) | reading |
|---|---|---|---|---|---|---|
| **M6E, declared** (2010-06 → 2023) | −\$3.26 | −\$3.94 | −\$3.36 / −\$3.06 | **0.66** (29) | −\$2.60 vs −\$3.46 | **NO PROFILE** |
| **MBT, declared** (2018 → 2023) | −\$1.49 | −\$1.39 | −\$2.25 / −\$0.92 | **0.78** (59) | −\$0.91 vs −\$2.38 | **NO PROFILE** |
| M6E, POST HOC from 2016 | **−\$1.39** | −\$2.83 | −\$2.50 / −\$2.04 | **1.00** | −\$1.51 vs −\$2.49 | SIZE FAILURE (would be) |
| MGC, declared (reported) | −\$0.50 | −\$2.24 | −\$2.31 / −\$1.58 | **1.00** (79) | −\$1.27 vs −\$2.32 | — |
| MGC, from 2016 | −\$1.29 | −\$3.48 | −\$3.58 / −\$2.05 | 1.00 | −\$1.86 vs −\$3.45 | — |
| 6E futures grid, declared | −\$3.13 | −\$3.22 | −\$3.13 / −\$2.33 | 0.55 | −\$3.02 vs −\$3.06 | — |
| 6E futures grid, from 2016 | −\$2.40 | −\$2.23 | −\$1.95 / −\$1.12 | 0.10 | −\$2.18 vs −\$1.86 | — |

- **On the declared readings:** both primary cells are **NO PROFILE**, GO false, Holm p 1.0 for both.
  - M6E's round grid ranks 0.66 among the offsets outside the stop band, though it beats its half-round control by
    \$0.68.
  - MBT's ranks 0.78, and it is below its half-round control.
- **What the clean data shows (POST HOC):** where the price is referenced to the round number the stop book sits on,
  the levels matter, and the price referenced to nothing does not.
  - **On clean 6E (2016 on), the spot-equivalent round grid is the best of all 29 eligible offsets** (−\$1.39 against
    p95 −\$2.04). In gold, the \$10 grid is the best of 79 in both periods.
  - **The futures-round 6E grid has no profile** (rank 0.10 from 2016). It is the same price with the basis left out.
    So the effect follows the SPOT level, which is where Osler's bank stop book sits, not the level a CME chart shows.
  - In every spot-referenced cell, the offsets inside the stop band beat those outside it by \$0.9–1.6 a trade. On
    the futures grid they do not.
  - **The exact round level is not the peak inside the band.** The best offsets sit 2–4 pips beside it on 6E
    (−\$0.90 at 3 pips below, from 2016) and \$80 below on BTC (+\$1.20). That is consistent with Osler's stops
    sitting a little beyond the number. The declared statistic took the exact level.
  - **A caution on the offset count:** adjacent offsets share most events, so the curve is smooth and its offset
    count overstates its information.
- **So Osler's mechanism appears to exist in these futures, but only at about \$1–1.5 per crossing,** relative to an
  arbitrary grid. Every grid loses money gross, because the stop entry pays the crossing and the re-cross exit pays
  the whipsaw.

## 4. The primary books: all four groups (Lens A s = 2, Asia, fast approach; one micro)

| | M6E declared | M6E from 2016 (POST HOC) | MBT declared |
|---|---|---|---|
| trades | 425 | 199 | 210 |
| **mean gross / net** | **−\$3.26 / −\$7.64** | **−\$1.39 / −\$5.77** | **−\$1.49 / −\$5.79** |
| gross at s = 1 / 2 / 4 | −2.63 / −3.26 / −4.04 | −0.95 / −1.39 / −1.85 | −1.15 / −1.49 / −2.08 |
| t gross / t net | −5.12 / −12.0 | −2.31 / −9.61 | −1.05 / −4.08 |
| Sharpe net / gross; Sortino net | −3.26 / −1.39; −3.17 | −3.41 / −0.82; −3.39 | −1.68 / −0.43; −2.61 |
| max drawdown (= total net) | \$3,248 | \$1,153 | \$1,217 |
| **mean \|move\| over the hold vs 2c (bar 2 × 2c)** | \$8.61 vs \$8.76 (\$17.52) | **\$6.01** vs \$8.76 | \$11.58 vs \$8.62 (\$17.24) |
| breakeven cost | none (gross < 0) | none | none |
| median net; win rate; payoff | −\$8.76; 15.1%; 1.13 | −\$7.51; 14.1%; 1.30 | −\$8.06; 12.4%; 3.01 |
| skew; kurtosis | −0.45; 10.6 | 2.58; 10.0 | 3.25; 15.6 |
| net ex-top 1% / ex-bottom 1% / trimmed | −8.15 / −7.01 / −7.52 | −6.21 / −5.57 / −6.01 | −6.94 / −5.41 / −6.56 |
| profitable years | 0 of 14 | 0 of 8 | 0 of 6 |
| net without its best two years | −\$3,140 | −\$1,041 | −\$1,171 |
| eras | 2010–14 −\$5.13 gross; 2015–23 −\$1.76 | — | pre-MBT −\$6.56; MBT era (from 2021-05) **+\$1.28** gross |
| largest trades | 2010-11-10 −\$78.75; 2010-11-08 +\$69.38 | 2020-03-31 −\$23.75; 2018-08-10 +\$48.75 | 2021-04-23 −\$47.00; 2022-03-09 +\$140.00 |
| unconditional (no speed filter) | 1,549 at −\$3.69 (t −9.6) | 691 at −\$1.31 (t −4.5) | 837 at +\$0.09 (t 0.15) |

- **On size:**
  - The bar is \$17.52 (M6E) and \$17.24 (MBT). On clean data M6E's crossings move \$6 over the hold: a third of the
    bar, and less than one round trip. **That is a SIZE FAILURE before any direction.**
  - MBT moves \$11.58: two-thirds of the bar.
  - The MBT era's +\$1.28 gross is a quarter of its \$4.31 cost.
- **The holding:** the 30-minute clock or the re-cross. Diagnostic: on Asia's round-grid events (declared data, all speeds), the mean hold is 11.6
  minutes on M6E, and 20% exit on the crossing minute.

## 5. Reported in no reading

- **Lens B (market at open(b+1)), fast:**
  - M6E −\$0.79 (t −0.79, 276); from 2016 −\$2.18 (100);
  - MBT −\$1.22 (160);
  - MGC +\$1.82 (t 1.75, 679).
- **A − B per event:** M6E +\$1.52, MBT +\$3.87, MGC +\$5.79. That is how much of the run happens inside the crossing
  minute, and Lens A's stop is the only way to own it.
- **Decay (M6E round, fast, Lens A s = 2):**
  - +15 min −\$2.45, +60 −\$1.80, +120 −\$2.23, next day's close −\$1.19.
  - MBT: −\$0.82, −\$2.22, −\$1.56, −\$21.94.
- **The windows, round minus half-round, Lens A fast, \$ a trade:**

  | | Asia | London | NY am | NY pm |
  |---|---|---|---|---|
  | M6E, declared | +0.68 | −0.71 | +0.55 | −1.16 |
  | M6E, from 2016 | +1.44 | +0.53 | +1.01 | −1.01 |
  | MBT | −0.09 | **+2.77** | −0.41 | **+4.50** |
  | MGC | +1.74 | +3.58 | −0.38 | +3.72 |

  - The SE of a 200-trade difference is about \$2 on MBT.
  - MBT London is the only positive gross round cell among the primaries: +\$2.87 on 200 trades, below its \$4.31
    cost.
- **The fingerprints:**
  - **50s ≥ 00s holds:** M6E 50s −\$2.80 against 00s −\$3.68; from 2016, −\$1.09 against −\$1.66.
  - **Asia ≥ London holds on M6E** (+1.44 against +0.53 from 2016) **and fails on MBT.**
  - **NY pm ≥ NY am fails on M6E** and holds on MBT.
- **The speed terciles, round against half-round (\$):**
  - M6E from 2016: slow −1.68 / −2.11; mid −0.95 / −1.92; fast −1.51 / −2.93. The round grid wins in every tercile,
    so it is not a volatility gate.
  - MBT: slow −0.04 / −0.31; mid −1.10 / −0.73; fast +0.35 / −1.79.
- **MGC**, \$5.93 a round trip:
  - net −\$6.44, Sharpe −1.62, 2 of 14 years positive;
  - its largest winner is the 2021-08-09 Asia flash crash, +\$504.

## 6. The component line (prop book; dollars at one micro)

| | net Sharpe / Sortino | hit | skew | gross beside net | ρ D737 twin / NQ F2 / C1 |
|---|---|---|---|---|---|
| M6E Asia | −3.26 / −3.17 | 15.1% | −0.45 | −\$3.26 / −\$7.64 | +0.05 / −0.02 / −0.02 |
| MBT Asia | −1.68 / −2.61 | 12.4% | 3.25 | −\$1.49 / −\$5.79 | −0.00 / −0.00 / +0.01 |

- **It is uncorrelated with everything in the ledger, and it loses \$5–8 a trade.** It is not a component.

## 7. The reading

- **Declared:** M6E **NO PROFILE**, MBT **NO PROFILE**, GO false.
- **POST HOC, M6E on clean data:** SIZE FAILURE. The profile is present, but the move is a third of the bar.
- **What was learned:**
  1. **Round-number stop clustering is visible in CME futures, referenced to SPOT.** It shows in 6E's spot-equivalent
     grid (not its futures grid) and in gold's \$10 grid: the stop band beats arbitrary levels by about \$1–1.5 per
     crossing. This is Osler's size, and a quarter to a third of a micro's round-trip cost.
  2. **The take-profit wall is not there.** Round levels are crossed slightly more often than half-round ones, in all
     four cells.
  3. **The thin session does not enlarge it.** Asia's crossings on clean 6E move \$6 over the hold.
  4. **MBT** has no round-number profile at \$1,000 levels in Asia. Its forced-liquidation story does not show at this
     grid.
  5. **6E's raw minute bars before 2016 are unusable for high, low or stop logic** without a print filter (§1).
- **Recommendation:** close D761's line, since no rule built on round-number crossings can pay a micro's round trip
  out of a \$1–1.5 relative effect on a negative base. Closing it is the principal's call.

## 8. CLOSED

*2026-10-02, the principal: "Close this we need more ideas here what do you think?"*
- **D761 is closed:** round-number stop cascades give no trade on M6E, MBT or MGC at micro size, in any session.
- **Don't re-propose:**
  - the stop entry beyond a round level (with or without the speed filter);
  - the market entry after the crossing bar;
  - the bounce or fade at round levels;
  - a shift of the level into the stop band. The best in-band offset is still gross-negative on M6E, and +\$1.20
    on MBT against a \$4.31 cost.
- **What stays recorded:**
  - the POST HOC mechanism facts: the round-number profile follows the spot level, at about \$1–1.5 a crossing;
  - round levels are not walls at 15 minutes;
  - 6E's pre-2016 off-market prints (§1).

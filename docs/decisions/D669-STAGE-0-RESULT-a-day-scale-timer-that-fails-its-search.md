# D669 STAGE 0 RESULT — the MACD arm earns by carrying the direction of the move since yesterday's close into days that trend, not by drift, the price level or volatility; and its 0.72 Sharpe does not survive the search that chose it

*Design: [D669](D669-STAGE-0-DESIGN-where-the-macd-arms-returns-come-from.md) (`39a25d3`), committed before the runner
existed (R8). Runner `scripts/stage0_d669_macd_mechanism.py`. Numbers in
[`data/stage0_d669_macd_mechanism.json`](../../data/stage0_d669_macd_mechanism.json); the 486-cell grid is in
[`data/stage0_d669_neighbourhood.csv`](../../data/stage0_d669_neighbourhood.csv). **A measurement on the admitted arm,
which admits and retires nothing. Window 2016-01-04 → 2023-12-29; the arm's 2024+ (spent by D503) was not read.**
The runner was run three times. The second run only added a block marked post hoc (§7), and every pre-registered line of
its log is identical to the first. The third followed an encoding declaration on two file calls, and its JSON is
identical to the second's.*

## The answer in one line

**The arm is a timer, not a drift harvester.**
- **Where its direction comes from.** At entry it takes, three times in four, the sign of NQ's move since the prior
  16:00 close. That sign alone, placed on the arm's own trades, earns 92 % of the arm's gross.
- **Where it earns.** On days that trend efficiently from 10:00 to 16:00. The top fifth of days by move carries 114 %
  of the gross; the bottom three-fifths lose.
- **What it is not.** It is not NQ's drift (drift carry −1 % of the gross). It is not the price level (the concentration
  is the same in basis points). It is not session volatility (on the same day, efficiency matters and volatility does
  not).

**The overfitting concern is supported on the two parameters the search selected:**
- the deflated Sharpe is 0.003 against D495's 111 cells, and at most 0.43 even if every trial were pure noise;
- the neighbourhood is a spike: the median of 485 neighbours is 0.24 against the arm's 0.72, rank 13 of 486;
- the spike lies on the impulse length and on the minimum hold. The MACD's own lengths are a plateau.

## 1. The arm (one MNQ, $3.50 a round trip, all 1,876 sessions)

Reproduced exactly from the trade rows: 1,876 sessions, $15,423 net and 1,908 trades. It passed the lag audit (a
second implementation of the state machine), the sign audit (in money) and the quantity audit.

**Performance**

| | net | gross |
|---|---|---|
| Sharpe / Sortino | **0.724 / 1.069** | 1.039 / 1.557 |
| total | $15,423 | $22,110 |
| at D527's measured $4.21 | 0.660 / 0.972, $14,077 | |

- Exposure is 80.5 % of the day-session bars, the daily σ is $180, the maximum drawdown $7,814 and the worst day
  −$1,315.
- The mean gross per trade is **$11.59, 3.31 × the $3.50 round trip**. Breakeven is 3.06 bp a side.
- P3a is 0.27 breaches a year and P3b 0.22.

**The trade distribution**

| per trade | mean | median | win | payoff | skew | kurtosis | ex-top 1 % | ex-bottom 1 % | trimmed both |
|---|---|---|---|---|---|---|---|---|---|
| gross | $11.59 | $4.75 | 52.4 % | 1.11 | 0.12 | 8.2 | $4.54 | $18.74 | $11.69 |
| net | $8.08 | $1.25 | 50.5 % | 1.13 | 0.12 | 8.2 | $1.03 | $15.23 | $8.19 |

- The symmetric trim keeps the mean ($8.19 against $8.08), so both tails are fat rather than one tail carrying the
  book.
- The mean sits above the median, so the right tail matters.
- The mean hold is 4.7 bars. 66.6 % of entries are at 10:00, and 75.4 % of exits are the 16:00 flat.

**What the winners depend on**
- Profitable years: 4 of 8 (2018, 2020, 2021, 2022). **Ten sessions reach half the net, and the top ten make 53 %.**
- The best trade is a short on 2022-08-26, the day of Powell's Jackson Hole speech: +$1,035.
- The worst trade is a short on 2022-10-13, the hot-CPI reversal: −$984.

## 2. Q1 — timing, not drift, and the information lives at the scale of a day

| side | trades | share | gross | hit | mean | median | payoff | net Sharpe of its sessions |
|---|---|---|---|---|---|---|---|---|
| long | 918 | 48.1 % | $15,007 | 59.8 % | $16.35 | $16.75 | 0.89 | 0.785 |
| short | 990 | 51.9 % | $7,103 | 45.6 % | $7.18 | −$7.00 | 1.35 | 0.238 |

- The arm is short slightly more often than long.
- **The longs win often; the shorts win seldom but big.** The short side's median trade loses $7, and its payoff is
  1.35.
- **C0, long in every one of the arm's windows:** gross $7,904, hit rate 56.9 %, net $1,217, net Sharpe 0.056. That is
  what the windows carry without direction.

**The direction-permutation null N1** (labels permuted within the stratum, 10,000 draws each, seed 669):

| stratum | strata | drift carry (exact) | p50 | p95 (SE) | G's percentile | G above p95 |
|---|---|---|---|---|---|---|
| whole | 1 | −$298 | −$405 | $12,560 (185) | 99.77 | +52 SE |
| year | 8 | −$303 | −$459 | $12,800 (150) | 99.75 | +62 SE |
| quarter | 32 | −$1,142 | −$1,226 | $11,862 (157) | 99.85 | +65 SE |
| month | 96 | −$2,613 | −$2,504 | $10,338 (162) | 99.93 | +72 SE |
| week | 417 | −$10,052 | −$9,972 | $2,198 (173) | 100.00 | +115 SE |

**G = $22,110. Q1-T passes.**
- **Drift share −0.013** (Q1-D: timing dominates). The arm's direction carries no net drift: it is long in windows that
  rise and short in windows that fall. NQ's upward drift contributes nothing.
- **Q1-H: the finest stratum beaten is the week**, so the direction information varies within a week, from day to
  day.
- **The week-level component is negative (−$10,052).** In weeks where the arm leans long, the 10:00–16:00 windows tend
  to fall. Its timing within the week is therefore worth $32,162, of which $10,052 is given back across weeks. This is
  disclosed, not claimed: it is in the shape of the overnight-against-intraday tug of war, and this record did not test
  it.

## 3. Q2 — the direction is the move since yesterday's close; the MACD adds nothing measurable beyond it

| lookback | agreement | substitution gross (share of G) | disagreements: trades, arm gross, t | free-running: net Sharpe (gross), ρ with the arm |
|---|---|---|---|---|
| R1h (last hour) | 63.9 % | $15,122 (0.68) | 685, $3,430, +0.70 | 0.356 (0.745), 0.13 |
| **RON (since the prior 16:00 close)** | **76.1 %** | **$20,367 (0.92)** | **455, $853, +0.23** | **0.434 (0.767), 0.43** |
| R1d | 55.9 % | $4,513 (0.20) | 838, $8,784, +1.59 | −0.033 (0.322), 0.06 |
| R2d | 48.4 % | −$2,587 (−0.12) | 979, $12,022, +1.97 | −0.632 (−0.308), −0.18 |
| R5d | 46.3 % | $6,401 (0.29) | 1,020, $8,030, +1.38 | −0.329 (−0.035), −0.09 |
| R20d | 46.9 % | $6,866 (0.31) | 1,009, $7,626, +1.35 | −0.070 (0.203), −0.00 |

**Q2-R does not fire.** RON's agreement, 76.1 %, is below the 80 % bar, although its substitution share, 0.92, is well
above its bar. **Q2-A does not fire for any lookback.** The nearest is R2d, at t 1.97.

What the table says:
- **The arm's direction is not multi-day momentum.** It agrees with the 1-, 2-, 5- and 20-day signs about half the time.
- **Its direction is close to RON's**, the move from the prior 16:00 close to the decision bar: overnight plus the cash
  open when it decides at 10:00.
- **Where the MACD departs from RON (455 trades), its choice earns $853, t 0.23.** That is nothing measurable.
- **RON as its own free-running rule scores 0.434 net.** RON's direction on the arm's own trades earns 92 % of the
  gross, so the rest of the arm's value is in its machinery: when it is in the market and when it exits (§7b).

Roll crossings: none for lookbacks up to 46 bars; 3.8 % of R5d windows and 29.2 % of R20d windows cross one.

## 4. Q3 — trend days, not volatility

**The global quintiles of |10:00 → 16:00 move|:**

| quintile | mean \|move\| | trades | hit | gross per trade | share of G | N1's expected gross |
|---|---|---|---|---|---|---|
| 1 | 8 bp | 372 | 43.8 % | −$8.26 | −0.14 | −$54 |
| 2 | 26 bp | 372 | 46.8 % | −$7.14 | −0.12 | −$68 |
| 3 | 48 bp | 381 | 50.9 % | −$4.29 | −0.07 | −$284 |
| 4 | 84 bp | 388 | 55.7 % | $11.20 | 0.20 | −$277 |
| 5 | 185 bp | 395 | **64.1 %** | **$63.62** | **1.14** | $385 |

- **Within-year quintiles** give the same profile: hit rates of 43.0 / 48.5 / 47.8 / 58.5 / 63.3 %, and a top-quintile
  share of 0.99.
- **Q3-T passes.** The top quintile carries 114 % of G, and its hit rate beats the bottom's by 20.2 points (SE 3.5).
- **On the quiet days the arm is wrong more often than a coin (43.8 %).**

**The session regression** (the arm's gross on efficiency and volatility, each z-scored within year, 1,708 traded
sessions, Newey-West 5): efficiency **+$30.6, t 6.64**; volatility +$4.5, t 0.57. **Q3-V passes.**

The 2 × 2 table (mean session gross by within-year halves):

| | low volatility | high volatility |
|---|---|---|
| low efficiency | −$7.74 (hit 45.2 %) | **−$28.00 (41.2 %)** |
| high efficiency | $33.59 (61.0 %) | $53.24 (61.9 %) |

**Volatile days that chop are the arm's worst cell.**

**The month** (96 months, Newey-West 3): |the month's return| t −0.76; **its daily σ t +6.48.** Volatile months pay
because they hold the efficient trend days, which is why 2020 and 2022 carry the book. **2023, high-σ in dollars
(D504), made $552 gross**: volatility is where trend days occur, not the condition itself.

## 5. Q4 — not the price level

| year | gross per trade | in bp | fee in bp | mean \|move\| in bp | gross |
|---|---|---|---|---|---|
| 2016 | $2.90 | 3.55 | 3.85 | 52 | $677 |
| 2017 | $2.18 | 1.66 | 3.07 | 33 | $518 |
| 2018 | $6.61 | 4.83 | 2.51 | 79 | $1,600 |
| 2019 | $0.24 | −0.12 | 2.31 | 49 | $56 |
| **2020** | **$40.40** | **21.91** | 1.75 | 98 | **$9,575** |
| 2021 | $10.91 | 4.63 | 1.22 | 62 | $2,674 |
| **2022** | **$27.14** | **11.52** | 1.38 | 119 | **$6,459** |
| 2023 | $2.27 | 0.96 | 1.24 | 70 | $552 |

**2020 and 2022 hold 72.5 % of the gross in dollars and 68.0 % in bp. Q4-P fails:** the concentration is the edge,
not the contract's size. The falling fee is real: 2016–2017 were cost-dead, with gross below the fee in bp. But the
fee did not make the good years.

## 6. Q5 — the search

**The deflated Sharpe.** The arm's per-session Sharpe is 0.0456 (0.724 annual), over T 1,876, with skew −0.05 and
kurtosis 9.6. Its probabilistic Sharpe against zero is 0.975.

| trial set | N | benchmark SR₀ (annual) | DSR |
|---|---|---|---|
| **D495's cells (primary)** | 111 | 1.750 | **0.003** |
| AGREE cells only (lenient) | 37 | 1.545 | 0.013 |
| survey count (strict) | 250 | 1.935 | 0.000 |

**Q5-D fails.** The primary variance carries the roots' cost differences as well as noise, which inflates SR₀; §7a
removes that and the arm still fails.

**The neighbourhood** (486 cells, identical sessions and cost):
- the arm's 0.724 ranks **13th**;
- the median neighbour scores **0.240**, the 10th–90th percentiles −0.007 to 0.595, and 86.2 % of neighbours are net
  positive;
- **Q5-N reads "spike".**

The one-at-a-time profiles through the default:

| axis | values → net Sharpe |
|---|---|
| MACD fast | 9: 0.834 · **12: 0.724** · 15: 0.713 |
| MACD slow | 20: 0.772 · **26: 0.724** · 32: 0.637 |
| MACD signal | 7: 0.780 · **9: 0.724** · 11: 0.710 |
| **impulse length** | 26: **0.173** · **34: 0.724** · 42: **0.371** |
| **minimum hold M** | 3: 0.526 · 4: 0.620 · **5: 0.724** · 6, 7, 8: **0.403** (identical) |

- **The MACD's own lengths form a plateau.**
- **The spike is the impulse length and the hold.** The impulse length is a published default, but it was the
  variant's presence that D495 selected. M = 5 was the edge of D495's grid.
- **M ≥ 6 gives identical books.** A 10:00 entry cannot exit on its signal before the forced flat once M ≥ 6, so
  M = 5 differs from holding to the close by exactly one exit chance: the 15:00 open (§7b).

## 7. Post hoc, disclosed and not pre-registered

Computed after the first run, from the same objects. Nothing in §1–§6 moved.

**(a) The deflated Sharpe with pure-noise trial variance** (V = 1/T, every trial's true Sharpe zero; the most lenient
reading):

| N | SR₀ (annual) | DSR |
|---|---|---|
| 37 | 0.791 | 0.43 |
| 111 | 0.941 | 0.28 |
| 250 | 1.040 | 0.20 |

**Even if the trials differed only by noise, the best of 37 would be expected to reach 0.79**, above the arm's 0.72.

**(b) The 15:00 exit.**
- 469 trades (24.6 %) exit on the signal at the 15:00 open.
- **The last hour they skipped would have lost $4,455** (mean −$9.50, t −2.08).
- M = 5 nets $15,423 against $8,967 at M = 6. The one exit chance is worth $6,456, about 0.32 of Sharpe.

When the signal has turned against a position by 15:00, the last hour continues against it. That fits D581 and D640's
finding that the close continues its prior hour (b +0.10, t 2.9). It is also exactly the kind of one-bar edge a grid
edge selects.

## 8. Component line and nulls

| construction | net Sharpe (gross) | hit | skew of daily net | ρ with the arm |
|---|---|---|---|---|
| the arm (the ledger's only component; nothing new built) | 0.724 (1.039) | 50.6 % of traded sessions | −0.05 | 1 |
| RON free-running | 0.434 (0.767) | 50.2 % | −0.02 | 0.43 |
| R1h free-running | 0.356 (0.745) | 51.6 % | 0.06 | 0.13 |
| R1d / R2d / R5d / R20d free-running | −0.033 / −0.632 / −0.329 / −0.070 | 51.1 / 50.4 / 52.2 / 53.4 % | | 0.06 / −0.18 / −0.09 / −0.00 |

- **The nulls are distributions.** N1's p50 and p95 with the p95's bootstrap SE are in §2. No margin is within 2 SE,
  so none is UNRESOLVED.
- N1's smallest distinguishable timing value, printed before G, was $12,858 over the whole window.

## 9. The predictions

| | prediction | outcome |
|---|---|---|
| 1 | longs are 52–65 % of trades | **FAILED**: 48.1 % |
| 2 | drift share < 0.30 and Q1-T passes | held: −0.013, +52 SE |
| 3 | the arm does not beat the within-week permutation | **FAILED**: +115 SE |
| 4 | Q3-T holds, with the hit rate rising across quintiles | held |
| 5 | R1d agrees on ≥ 75 % of trades | **FAILED**: 55.9 % (RON: 76.1 %) |
| 6 | Q5-D fails and Q5-N reads plateau | **FAILED**: Q5-D fails, but Q5-N reads spike |

Two of six held. I expected a slow trend-follower. The arm is a day-scale timer.

## 10. What this decides

**The mechanism, named in sample.**
- The arm carries the direction of the move since yesterday's close (overnight plus the cash open) through the day
  session.
- It profits on the days that keep going in an efficient trend. Those days cluster in volatile months, which is why two
  years carry the window.
- It exits a quarter of its trades at 15:00, when its signal has turned, and that exit is worth about 0.32 of its
  Sharpe.
- Drift, the price level and session volatility are each ruled out as the source.
- **No unread NQ slice remains, so none of this can be confirmed out of sample on NQ.**

**The principal's overfitting concern: supported, and located.**
- The MACD lengths are robust.
- The arm's 0.72 is the upper tail of its family. The median neighbour is 0.24, and the deflated Sharpe fails even
  under pure noise.
- The spike lies on the two choices the search made: the impulse variant's length, and a hold that buys one exit at
  15:00.
- **A fair in-sample expectation for this construction is closer to 0.24 than to 0.72 net.**

**Proposals, each the principal's to make (R15). Nothing is changed by this record.**
1. **Amend the arm's qualification in `BOOK_PROP.md`** with the mechanism and the neighbourhood median, so that the
   book's expected Sharpe is not read from the selected cell.
2. **Treat "RON direction, day session, exit when the signal turns by 15:00" as a candidate for a new component's
   pre-registration.** It must be on roots whose unread slices are checked first: every open seal is listed before a new
   reader. The MACD adds nothing measurable beyond RON's direction; the machinery around it is the open question.

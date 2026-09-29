# D685 RESULT — MECHANISM ONLY: the month-end rebalancing signal replicates on ES futures (−14 bp per 1-SD, t −3.2, above its null and its placebo), but it fades after 2018, the bond leg does not move, it does not reverse, and no book clears net

*Renumbered from D677 to D685 on 2026-09-29 before this branch (`wt/after-d674`) merged main, which holds a different D677. Commit messages and the recorded outputs in `data/` keep the old number.*

*2026-09-29. One run of `scripts/stage0_d685_month_end_rebalancing.py` (`64fdede9`) under
[D685's pre-registration](D685-PRE-REG-month-end-rebalancing-flow-on-es-and-zn.md) (`6306644c`), 3 s. Output
`data/d685_month_end_rebalancing.json`. Window: 162 months, 2010-07 → 2023-12, 810 active days. No settlement dated
on or after 2024-01-01 was read.*

## The answer in one line

**Gate 1 passes, Gate 2 fails, so the verdict is MECHANISM ONLY.**
- **Gate 1:** the lagged 60/40 drift predicts ES over the last five trading days at −14.06 bp per 1-SD (NW t −3.22),
  close to the published −17. The sign book beats its enumerated month-rotation null (99.4th percentile) and its
  mid-month placebo (97.5th).
- **Gate 2:** no book clears net. This is not cost: an MES round trip is $4.42 against an average daily move of $93.
  It is noise and fade. The filtered MES book nets $4.06 per active day at t 1.04.
- **Against the mechanism:** the sign book lost money in each of 2019–2022, ZN does not move, and the month-end move
  continues rather than reverting.

## 1. The mechanics held

- **Data:** 3,414 common ES/ZN trading days, 2010-06-07 → 2023-12-29.
  - Every same-contract return is present on ES, ZN, NQ and YM. RTY is used from its first finite month (2017).
  - The held series differs from the naive front-to-front series on 55 ES and 54 ZN roll days, as it must.
- **Audits:** all fired on their broken inputs in the self-test, and passed on the real data:
  - the lag audit: an explicit-loop second path, against the 810 lagged positions;
  - the sign audit in money;
  - right quantity;
  - the window guard;
  - the rotation's identity at k = 0.
- **The null** is exact: 159 month offsets (k = 2 … 160), so the p95's SE is zero.
- **z** exists from the 13th month onward: 150 months, 750 active days.

## 2. Gate 1: the mechanism (gross)

| bar | value | null p50 | null p95 | pct | passes |
|---|---:|---:|---:|---:|---|
| **B1** slope, bp per 1-SD | **−14.06** (NW t **−3.22**, n 750) | — | — | — | **yes** (β < 0, t ≤ −2) |
| **B2** sign book, bp per active day | **+7.17** | −2.09 | +3.77 | 0.994 | **yes** |
| the placebo's own sign book (mid-month) | −3.43 | | | 0.264 | — |
| **B3** treatment − placebo | **+10.61** | −0.41 | +7.67 | 0.975 | **yes** |

- **The paper's unlagged form** (S-UNLAG) is a little stronger: −15.38, t −3.65; the sign book is +8.55 at the 99.4th
  percentile. The execution lag costs about 1.3 bp per 1-SD.
- **The same mechanism on the other index roots (reported, not gated):**
  - YM: −14.51, t −3.22; sign book at the 100th percentile.
  - NQ: −11.94, t −2.28; 98.1st.
  - RTY: −8.89, t −1.45; 76.7th. That is 2017 onward, and small caps.
  - ES−ZN at equal notional: −14.05, t −2.94. That is the ES leg alone, because ZN is flat.

## 3. Gate 2: tradeability (net, filtered by expected profit)

**The filtered MES book:**
- **The statistic:** 447 traded days in 117 runs. Its net mean per active day is **+$4.06, NW t 1.04** (n 810).
  Gate 2 needs t ≥ 2, so it **fails**.
- **The filter adds nothing:** the filtered MES book has a net Sharpe of 0.24, against 0.26 unfiltered.
- **Cost is not what binds:** the mean |move| per traded day is $112.6 against 2c = $8.84, and the breakeven round
  trip is $32.5 against the $4.42 paid.

## 4. The component line and the four groups

Daily dollar P&L over every trading day, 2010-07 → 2023-12 (zero when flat). The house cost convention: MES costs
$4.42 a round trip, full ES $19.24.

| book | traded days / runs | exposure | net Sharpe | net Sortino | gross Sharpe | net $ | vol/yr | maxDD |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| unfiltered MES | 810 / 198 | 23.9% | **+0.26** | +0.39 | +0.32 | +4,069 | 1,155 | 3,626 |
| filtered MES | 447 / 117 | 13.2% | +0.24 | +0.36 | +0.28 | +3,286 | 1,011 | 2,566 |
| unfiltered ES | 810 / 198 | 23.9% | +0.29 | +0.44 | +0.32 | +45,617 | 11,551 | 35,208 |
| filtered ES | 549 / 138 | 16.2% | +0.24 | +0.37 | +0.26 | +34,724 | 10,706 | 26,504 |

- **Correlation with the ledger:** with the admitted MACD arm's daily net (2016–2023) it is **−0.035** (unfiltered
  MES) and **+0.007** (filtered MES).
- **Per traded day, unfiltered MES:**

  | per traded day | mean | median | win rate | payoff | skew | kurtosis | ex-top 1% | ex-bottom 1% | trimmed 1% both tails |
  |---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
  | gross | **+$6.10** | +$2.50 | 51.4% | 1.06 | +0.16 | 8.7 | **+$0.12** | +$11.94 | **+$5.95** |
  | net | +$5.02 | +$1.27 | 50.9% | 1.06 | | | −$0.97 | +$10.87 | +$4.87 |

  - **The top 1% of days** (8 days) carry nearly all the mean.
  - **But the symmetric trim keeps it** (+$5.95 against +$6.10), and the median is positive. This is a thin
    two-sided book, not a lottery book.
- **What the winners depend on:**
  - **Era, strongly:**

    | | 2010–15 | 2016–19 | 2020–23 |
    |---|---:|---:|---:|
    | unfiltered MES net | +$2,579 | +$2,513 | **−$1,023** |
    | B1 slope | −18.3 (t −2.18) | −13.7 (t −2.31) | −10.2 (t −1.22) |

  - **By year:** the sign book's gross (bp) was negative in **2019, 2020, 2021 and 2022** (−4.1, −1.8, −6.8, −7.2)
    and +11.1 in 2023. 10 of 14 years were positive.
  - **Price terciles:** the high-price third is negative (−$3.14 a day). But that is the same late era (the price
    rose through time), not cost: cost is 2.3–6.1 bp in every tercile.
  - **Quarter-end against the other months:** the slope is larger at quarter-ends (−17.6, t −2.77, against −12.1,
    t −2.04). The per-day book is not larger there ($3.99 against $5.54).

## 5. What does not fit the mechanism

1. **The bond leg is flat.** ZN's slope is −0.01 (t −0.01). Rebalancers who sell equities buy bonds, so ZN should
   rise when s > 0. Either the bond buying lands in cash Treasuries, longer duration or other markets, or the ES
   effect is not rebalancing flow alone.
2. **No reversal.** Over the first 10 trading days of the next month, the slope on the last active day's z is
   **−49.2 bp (t −1.97)**: the month-end decline **continues**. Temporary price pressure from a flow should revert,
   and the paper reports that it does. A continuing move is closer to information, or to a slower flow than the
   calendar one.
3. **The placebo points the other way:** +9.63 (t 0.71). It is not significant, and B3 passes by a margin, but it is
   outside the ±5 bp I predicted.

## 6. Predictions

| # | prediction | outcome |
|---|---|---|
| 1 | β < 0 on ES | **HELD** (−14.06) |
| 2 | β between −15 and −5, t between −4 and −2 | **HELD** (−14.06, t −3.22) |
| 3 | placebo β within ±5, and B3 iff B1 | **BROKEN**: placebo +9.63 (not significant); B3 and B1 both pass |
| 4 | ZN β > 0 | **BROKEN**: −0.01 |
| 5 | quarter-end \|β\| larger | **HELD** (17.6 against 12.1) |
| 6 | the next 10 days reverse (β > 0) | **BROKEN**: −49.2, continuation |
| 7 | if Gate 1 passes, Gate 2 passes | **BROKEN**: fails at t 1.04, on noise and fade, not cost |

## 7. What this decides, and the confirmation question

**The mechanism is real in this sample and weaker than it was.** The published effect replicates on futures
2010–2023 at about 80% of its size, beats a placebo at a time the flow does not trade, and holds on three of four
index roots.

**Three things argue against building on it:**
- it faded to nothing across 2019–2022;
- the flow's other leg (bonds) and its signature (reversal) are absent;
- no book clears net at t 2, and the component line (net Sharpe 0.26) is under the ledger's 0.4–0.6 range.

**The declared confirmation is weak at the effect now measured.**
- It is 2024-01 → 2025-02 plus the joint-run vault.
- At this record's −14 bp, the expected t is about 1.1 on the clean slice and about 1.65 with the vault.
- The vault is after the paper's publication (2025), and the last in-sample era is already flat.
- Spending it would most likely return a number near zero whether or not the effect survives.

**Proposals, each the principal's (R15):**
1. **Record the mechanism as MECHANISM ONLY, and do not spend 2024-01 → 2025-02 on it now.** The line is not closed:
   the fact of the month-end equity flow stands.
2. **Enter it in `COMPONENTS_PROP.md` as SCORED, NOT ENTERED**, with the component line above: net Sharpe 0.26, ρ
   −0.04 with the arm.
3. **If a successor is wanted, it should explain the two misfits first:** why ZN is flat, and why the move continues.
   It should not re-tune this signal. A study of where the bond leg's flow lands, or whether the continuation is
   month-end information, would have a mechanism of its own.

## 8. CLOSED by the principal, 2026-09-29

"Ok close no need for 2024+ data." **The line is closed under R15 with D686 and D687;** see D687 §5.
- **The bond-leg question of proposal 3 is answered by D687:** the leg is in the long bond (ZB +8.6, t 2.09 in
  2010–15), not ZN.
- **The continuation is weak in every era.**

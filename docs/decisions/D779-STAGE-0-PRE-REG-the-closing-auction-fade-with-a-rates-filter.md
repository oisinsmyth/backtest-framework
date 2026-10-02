# D779 STAGE 0 PRE-REG — the M2K closing-auction fade (D772's Lead 4) with a rates filter: does skipping the fall-side buys on days the 10-year Treasury future fell remove 2022's losers without removing the other years' winning dip-buys?

*2026-10-03. The principal: "I would like to understand the mechanics of why L4 fails after that date?"; "In that case
it deserves a place in the vault then? no? whats your options?"; on option 3, "Pre-reg 3 build and run it please".*

- **What it is:** a Stage 0 test of D772's Opus Lead 4 with one rates filter, both fixed here before the runner
  exists. It admits nothing.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the
  result separately.
- **The prop book's rules:**
  - one micro, entered 18:05 ET (the next trading day's open) and exited 10:00 ET, flat long before 16:10;
  - fully algorithmic; one position.
- **The overnight closure does not apply** (the principal's 2026-10-02 ruling: signed fades are outside it).

## 0. What is already known, and why a pass is weak evidence

- **[D778](D778-STAGE-0-RESULT-the-trend-filter-removes-the-best-trades.md)'s base L4 book (M2K, 280 trades,
  2018–2023):**
  - +\$15.84 gross / +\$12.08 net, gross t 2.47, net t 1.88;
  - net −\$15 in total without 2020 and 2021;
  - by year, net: 2018 +\$4.47, 2019 +\$2.16, 2020 +\$27.02, 2021 +\$24.82, **2022 −\$13.06**, 2023 +\$11.26.
  - So base L4 fails G2 on its own.
  - D778's trend filter removed the fall-side buys in downtrends. They were the book's best trades in every year
    but 2022.
- **The main session's mechanics look (2026-10-03, scratch, not a record), M2K:**
  - From 16:00 to the next 10:00, the closing-auction move gave back 52–72% of its size in every period except 2022,
    where it gave back 2.5%.
  - In 2022 the correlation of the closing move with the overnight outcome turned positive (+0.088, against −0.06 to
    −0.18 elsewhere). The fall-side buys lost −\$32.79 a trade.
  - The halt-removal timing change moved a few dollars of the give-back into the 16:00–17:00 hour. That is not the
    cause.
  - Closing moves have no day-to-day persistence.
- **The mechanism this filter tests:**
  - A closing-auction drop on a day the 10-year Treasury future FELL (yields rose) is the market repricing rates. That
    is information, which the overnight session extends.
  - A closing-auction drop on a day Treasuries did not fall is one-off flow, which reverts.
  - 2022 had many of the first kind.
- **This filter was proposed AFTER seeing 2022, which this test cannot unsee.**
  - Two things are different from D778:
    - **The relation between the Treasury move and L4's outcome has NOT been computed by anyone in this programme.**
    - **The conditioner is a daily state, not a year label.** Its share of sessions by year was measured before this
      record, with no outcome joined. The 09:30→16:00 move fell on 52% of 2022's sessions against 42–49% in every
      other year. So the filter removes about half the fall-side buys in every year; it cannot remove 2022 by
      construction.
  - **The window was chosen on resolution alone, from that same outcome-free measurement:**

| ZN window, 2016–2023 | zero change | median \|move\| | sessions with a fall |
|---|---|---|---|
| 15:50 → 16:00 | 24.4% | 1 tick | 33.5% |
| 15:00 → 16:00 | 11.6% | 2 ticks | 41.1% |
| **09:30 → 16:00 (the primary)** | **3.1%** | **9 ticks** | **45.9%** |

  - The test can FAIL in three ways:
    - (i) the removed trades earn;
    - (ii) a rotation of the same flag does as well (§3, F(b));
    - (iii) in the years other than 2022, the filter removes fall-side buys that did as well as the ones it kept
      (§3, F(c)).
  - It cannot prove the filter works. Only unread data can (M2K and ZN from 2024 on).
- **The root:** M2K was chosen after D772 saw four roots. MES, MYM and MNQ are reported under the same rules.

## 1. The construction (fixed here)

- **The equity bars and the base trade are D778's, unchanged** (`stage0_d778_auction_fade_trend_filter.frame`):
  - c = close(15:59 bar) − close(15:49 bar) on session S;
  - the gate: |c| ≥ the 80th percentile of |c| over the 250 prior sessions (at least 120);
  - side = −sign(c); entry at the close of S+1's 18:04 bar, exit at the close of its 09:59 bar;
  - the micro lines: M2K \$5 / \$3.76, MES \$5 / \$4.42, MYM \$0.50 / \$3.80, MNQ \$2 / \$4.07.
  - **The sessions are D778's valid sessions,** including its 200-session warm-up exclusion. So the base book is
    D778's base book exactly, and the runner asserts it: M2K 280 trades, mean gross +\$15.84.
- **The rates state:**
  - from `fut_day1m.parquet`, root ZN, the bar with index 29 (09:29 ET, start-stamped, so its close is the 09:30
    price) and the bar with index 419 (its close is the 16:00 price), on the ET calendar day of session S;
  - **ZFELL = close(419) − close(29) < 0, with both bars on the same contract.**
  - A session with either bar missing, or with the bars on different contracts, has no reading. **Its trade is
    kept.**
  - The state is known at 16:00 of S, before the 18:05 entry.
  - Only ZN days before 2024-01-01 are read (asserted).
- **F1, the filter (primary):** drop every base trade that buys a fall (c < 0, side long) on a ZFELL session. Fades of
  rises, and fall-side buys on other sessions, are kept.

## 2. Reported beside the gates (not gated)

- **The other ZN windows:** the same filter with the 15:50 → 16:00 and the 15:00 → 16:00 moves (a strict fall).
- The base book, F1 and the other windows on MES, MYM and MNQ.
- The removed trades by year and their mean; the share of fall-side buys removed by year.
- The fall and rise sides; 2022's cell; the drift-adjusted give-back.
- **All four groups for each traded book**, as D778 (gross and net, Sharpe and Sortino, maximum drawdown, the mean
  |move| against the cost, the breakeven cost; count, mean, median, win rate, payoff, skew, kurtosis, the symmetric
  1% trims, the five largest and worst trades named; years, sides, |c| terciles, the settlement-clock regimes;
  p50, p95 and the rank).
- **The component line:** the daily ρ with D775's book, D777's (closed) MNQ book, and D737's twin, NQ F2 and C1.

## 3. The gates (M2K primary)

| gate | condition |
|---|---|
| **G1** | the F1 book's mean gross > 0 with t ≥ 2 |
| **N** | the F1 book's mean gross above the p95 of the exact time rotation of its signal (side × gate × kept) against the outcomes, every offset (SE 0) |
| **F, the filter** | (a) the trades F1 removes have a negative mean gross; AND (b) Δ = mean gross (F1) − mean gross (base) is above the p95 of Δ when the ZFELL flag series is rotated circularly against the sessions, every offset (SE 0); AND (c) **outside 2022**, the removed trades' mean gross is below the mean gross of the fall-side buys F1 keeps |
| **Y, the principal's test** | (i) the F1 book's win rate ≥ 50% in at least three-quarters of the full years; OR (ii) its volatility-adjusted mean > 0 in at least three-quarters of them AND 2016–19's ≥ half of 2020–23's |
| **G2** | the F1 book's mean net > 0 with t ≥ 2; net > 0 without its best two years; the mean gross without 2022 AND the 1%/1% trimmed mean each ≥ 2 × \$3.76 |

- **F(c) is the test of the mechanism in the other years.** If rate-repricing drops continue overnight, they should
  do worse than the other drops in every year, not only in 2022.
- **A session with no ZN reading** counts as not-ZFELL in the rotation too. The rotation moves the flag series,
  missing readings included.
- **The volatility-adjusted return and the full years:** as D778.
- **The readings, in order:**

| reading | condition |
|---|---|
| **NO EFFECT** | G1 fails |
| **NOT ABOVE NULL** | N fails |
| **FILTER ADDS NOTHING** | F fails (any of a, b, c) |
| **CONCENTRATED** | Y fails |
| **NO PRIZE** | G2 fails |
| **SUPPORTED** | all pass |

- **GO = M2K SUPPORTED.** It starts a confirmation conversation, and that conversation needs:
  - the last free programme slot (10);
  - an RTY build of the vault opening fixture through 2026-09-18;
  - ZN minute bars through 2026-09-18 (the day1m fixture ends 2026-09-09).
  - It admits nothing.
- **If it is not SUPPORTED,** base L4 stays an open lead. The main session's recommendation would be to record it
  forward, not to freeze it.

## 4. Predictions and priors

- **F(a) passes:** 2022's fall-side buys on ZFELL days lose.
- **F(c) is the gate at risk:** outside 2022, a fall on a rising-yield day may revert as well as any other fall.
  Late 2018's and 2020's sell-offs were not rate-led.
- **G2 is also at risk:** the base book's net t is 1.88. Removing about half the fall-side buys shrinks the sample,
  so the filtered book needs a markedly higher mean to clear net t 2.
- **The prior:** M2K SUPPORTED about 15%. NO PRIZE or FILTER ADDS NOTHING (through F(c)) are the expected failures.

## 5. Runner assertions

- **Lag:**
  - c, the gate, the side and ZFELL use bars closed by 16:00 of S;
  - the threshold uses prior sessions only.
  - A second implementation (explicit loops over raw rows, including the raw ZN rows) re-derives c, ZFELL, the kept
    decision and the fade on 40 sampled base trades.
- **Sign, in money:** a closing fall followed by an overnight rise pays the long fade; a mirrored book raises.
- **Right quantity:**
  - the base book reproduces D778's: on M2K, 280 trades and mean gross +\$15.84;
  - rotation offset 0 equals the observed, for N and for F(b);
  - base trades = F1 trades + removed trades;
  - the filtered book differs from the base;
  - nothing on or after 2024-01-01, equity or ZN.
- **The self-test:**
  - a planted continuation of fall-side buys on ZFELL days is removed, and the filter passes F;
  - a filter on a flag that tracks nothing fails F;
  - ZFELL uses no price after 16:00 of S;
  - the second implementation raises on a broken decision;
  - chunk = whole;
  - the whole study runs end to end on a synthetic panel.

## 6. Output

- `scripts/stage0_d779_auction_fade_rates_filter.py`;
- `data/stage0_d779_auction_fade_rates_filter.json` (statistics only).
- The result is a separate record.

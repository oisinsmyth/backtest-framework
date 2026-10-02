# D778 STAGE 0 PRE-REG — the M2K closing-auction fade (D772's Lead 4) with a trend filter: does skipping the fall-side buys while the index is below its 200-session average remove the losing regime without removing the edge?

*2026-10-03. The principal: "Look at L4"; "Is their a mechanical reason for this?"; "Test that, pre-reg build and run
plase".*

- **What it is:** a Stage 0 test of D772's Opus Lead 4 with one trend filter, both fixed here before the runner exists.
  It admits nothing.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the
  result separately.
- **The prop book's rules:**
  - one micro, entered 18:05 ET (the next trading day's open) and exited 10:00 ET, flat long before 16:10;
  - fully algorithmic; one position.
- **The overnight closure does not apply** (the principal's 2026-10-02 ruling: signed fades are outside it).

## 0. What is already known, and why this test is weak evidence even if it passes

- **The main session's look (2026-10-02/03, scratch, not a record), M2K, 2017-07 → 2023:**
  - 304 trades, +\$15.78 gross / +\$12.02 net (t 2.65 gross), exact rotation rank 0.998;
  - the win rate is at least 50% in every year 2018–2023.
- **The fall/rise split, by period:**

| | fading a closing FALL (long) | fading a closing RISE (short) |
|---|---|---|
| M2K 2016–19 / 2020–21 / **2022** / 2023 | +\$21 / +\$44 / **−\$33** / +\$26 | −\$5 / +\$4 / +\$6 / +\$4 |
| MNQ 2016–19 / 2020–21 / **2022** / 2023 | +\$14 / +\$60 / **−\$58** / +\$75 | −\$6 / −\$3 / **+\$52** / +\$16 |

- **The mechanical reading that motivates the filter:**
  - Buying a sharp fall into the closing auction earns when that selling is one-off forced flow.
  - It loses when the selling is a trend, as in 2022's bear market (the overnight drift was negative, and the falls
    continued).
  - So the filter skips the fall-side buys while the index is in a downtrend.
- **This filter was proposed AFTER seeing 2022's by-side split, which this test cannot unsee.**
  - A 200-session average marks 2022 as a downtrend almost all year, so the filter will remove 2022's losing fall-side
    buys by construction.
  - The in-sample test can still FAIL in two ways:
    - (i) if the filter also removes the fall-side buys that earned in other downtrends (late 2018, March–June
      2020, early 2023);
    - (ii) if a filter on a random rotation of the same trend state does as well (§3, gate F).
  - It cannot prove the filter works. Only unread data can: M2K 2024+, which is unread.
- **The root:** M2K was chosen after D772 saw four roots. MES, MYM and MNQ are reported with the same rules.

## 1. The construction (fixed here)

- **Bars:** `fut_opening_globex_1m_ym_rty` (RTY, YM) and `fut_opening_globex_1m` (ES, NQ).
  - One-minute bars, stamped at their START, on each session's front.
  - Sessions 2016-01-01 → 2023-12-31; RTY from 2017-07-10.
  - D777's panel conventions throughout (`stage0_d777_post_close_fade.panel`): S+1 at most four calendar days after S;
    stray old-dated rows dropped.
- **The base trade, L4 (as the main session's look):**
  - c = close(15:59 bar) − close(15:49 bar) on session S (the 16:00 price minus the 15:50 price);
  - the gate: |c| ≥ the 80th percentile of |c| over the 250 prior sessions (at least 120);
  - side = −sign(c); entry at the close of S+1's 18:04 bar, exit at the close of its 09:59 bar;
  - gross = side × (exit − entry) × \$ per point.
  - The micro lines: M2K \$5 / \$3.76, MES \$5 / \$4.42, MYM \$0.50 / \$3.80, MNQ \$2 / \$4.07.
- **The trend state:**
  - a back-adjusted index of the root's 16:00 prices: the cumulative sum of ln(close(15:59)_S / close(15:59)_{S−1}),
    with the return set to 0 on a session whose front differs from the previous session's;
  - its 200-session simple average, including S;
  - **DOWN = the index on S below that average.**
  - Known at 16:00 of S, before the 18:05 entry.
- **F1, the filter (primary):** drop every base trade that buys a fall (c < 0, side long) on a DOWN session. Fades of
  rises and fall-side buys in UP states are kept.
- **The comparison base:** the unfiltered L4 book on the same sessions. Sessions without a trend state (the first 200)
  are excluded from both.

## 2. Reported beside the gates (not gated)

- **F2, a volatility filter (secondary):** drop fall-side buys on a session whose 20-session realised volatility of
  the daily returns above is above its own 250-session median AND above its value 20 sessions earlier ("rising
  volatility").
- The base book, F1 and F2 on MES, MYM and MNQ.
- The removed trades by year and their mean.
- The fall and rise sides; 2022's cell.
- The drift-adjusted give-back (the unconditional 18:05 → 10:00 mean removed from each side).
- **All four groups for each traded book:**
  - **Performance:** gross and net, Sharpe and Sortino (daily, zero on untraded days), maximum drawdown, the mean
    |move| against the cost, the breakeven cost.
  - **Trade distribution:** count, mean, median, win rate, payoff, skew, kurtosis, the symmetric 1% trims, and the
    five largest and five worst trades named.
  - **What the winners depend on:** years, sides, |c| terciles, and the settlement-clock regimes.
  - **Nulls:** p50, p95 and the rank.
- **The component line:** the daily ρ with D775's book, D777's (closed) MNQ book, and D737's twin, NQ F2 and C1.

## 3. The gates (M2K primary)

| gate | condition |
|---|---|
| **G1** | the F1 book's mean gross > 0 with t ≥ 2 |
| **N** | the F1 book's mean gross above the p95 of the exact time rotation of its signal (side × gate × kept) against the outcomes, every offset (SE 0) |
| **F, the filter** | (a) the trades F1 removes have a negative mean gross; AND (b) the improvement Δ = mean gross (F1) − mean gross (base) is above the p95 of Δ when the DOWN flag series is rotated circularly against the sessions, every offset (SE 0). The rotation keeps the DOWN share and its persistence and breaks only its timing |
| **Y, the principal's test** | (i) the F1 book's win rate ≥ 50% in at least three-quarters of the full years; OR (ii) its volatility-adjusted mean > 0 in at least three-quarters of them AND 2016–19's ≥ half of 2020–23's |
| **G2** | the F1 book's mean net > 0 with t ≥ 2; net > 0 without its best two years; the mean gross without 2022 AND the 1%/1% trimmed mean each ≥ 2 × \$3.76 |

- **The volatility-adjusted return:** as D777 (gross ÷ the 60-prior-session standard deviation of the unsigned
  outcome).
- **The full years:** those after the first year with trades.
- **The readings, in order:**

| reading | condition |
|---|---|
| **NO EFFECT** | G1 fails |
| **NOT ABOVE NULL** | N fails |
| **FILTER ADDS NOTHING** | F fails |
| **CONCENTRATED** | Y fails |
| **NO PRIZE** | G2 fails |
| **SUPPORTED** | all pass |

- **GO = M2K SUPPORTED.** It starts a confirmation conversation. That conversation needs:
  - the last free programme slot (10), or the forward recorder (which does not carry RTY);
  - and an RTY build of the vault opening fixture through 2026-09-18.
  - It admits nothing.

## 4. Predictions and priors

- **F(a) passes:** 2022's fall-side buys dominate the removed trades.
- **F(b) is the gate at risk:** a rotated DOWN flag also removes some losing fall-side buys, and the true filter also
  removes 2020's and 2018's winning ones.
- **G1, N and G2 pass**, given the base book's in-sample numbers.
- **The priors:** M2K SUPPORTED about 30%. FILTER ADDS NOTHING is the expected failure. And a pass is weak evidence (§0).

## 5. Runner assertions

- **Lag:**
  - c, the gate and the side use bars closed by 16:00 of S;
  - the trend state uses 16:00 prices up to S, and the threshold prior sessions only;
  - a second implementation (explicit loops over raw rows) re-derives c, the gate, the trend state and the filtered
    decision on 40 sampled trades.
- **Sign, in money:** a closing fall followed by an overnight rise pays the long fade; a mirrored book raises.
- **Right quantity:**
  - rotation offset 0 equals the observed, for N and for F;
  - base trades = F1 trades + removed trades;
  - the filtered book differs from the base;
  - nothing on or after 2024-01-01.
- **The self-test:**
  - a planted downtrend-continuation on fall-side buys is removed and the filter passes F;
  - a filter on a random flag fails F(b);
  - the trend state uses no later price;
  - the second implementation raises on a broken decision;
  - chunk = whole;
  - the whole study runs end to end on a synthetic panel.

## 6. Output

- `scripts/stage0_d778_auction_fade_trend_filter.py`;
- `data/stage0_d778_auction_fade_trend_filter.json` (statistics only).
- The result is a separate record.

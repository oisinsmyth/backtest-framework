# D758 STAGE 0 RESULT — NOTHING: CME bitcoin's weekend gap does not fill; Monday's path reaches the mirror level more often than Friday's close, but neither side of the trade pays

*2026-10-02. One run of `scripts/stage0_d758_btc_weekend_gap.py --run` (0.24 minutes). The
[pre-registration](D758-STAGE-0-PRE-REG-the-cme-bitcoin-weekend-gap.md) (`219f5741`) was committed before the runner,
and the runner (`999cdc84`) before its run.*
- **Output:** `data/stage0_d758_btc_weekend_gap.json` (statistics only).
- Before the run, the whole run path was exercised on synthetic random-walk sessions. There, fill and mirror touch
  rates came out equal, as they should.

## 0. Checks

- **The seal:** the BTC fixture was read as text with `day` < 2024-01-01, and every kept timestamp is asserted before
  2024.
- **The clock:** zoneinfo equals the statutory US rule on every bar.
  - On 91.3% of weekends the first bar prints at 18:00 ET exactly (median 0 minutes late).
  - The median entry is at 18:06.
- **Lag:** G reads no bar starting at or after 18:05. The canary that includes the 18:05 bar changed some signs.
- **Sign, in money:** a down-gap followed by a rise pays the fade, and the audit raises on a mirrored book.
- **Right quantity:**
  - 302 weekends read = 287 scored + 13 with no bar in the first five minutes + 2 with a zero gap;
  - no weekend crossed a contract roll;
  - no placebo is a weekend.
- **Holiday reopens:** 15, of which 13 were scored, −\$0.23 gross. Reported, in no reading.

## 1. The oracles: there is room, and the gap is real

| | weekends (287) | placebo reopens after the daily halt (1,028) |
|---|---|---|
| mean \|move\|, entry → Monday 09:30, one MBT | **\$59.99** (7.0 × 2c) | \$46.26 |
| mean \|G\| | **\$50.74** | \$12.27 |
| \|G\| / the previous session's range, median | **0.34** | 0.07 |

- **NO ROOM: false. NOT SPECIAL: false** (Welch t 2.31).
- **The weekend gap is about four times a weekday reopen's.** It is a third of Friday's whole range.

## 2. Direction and the touch test

| | n | mean gross | t |
|---|---|---|---|
| **P, the fade s = −sign(G), 18:06 → 09:30** | 287 | **−\$4.24** | −0.65 |
| N1, the enumerated sign rotation (286 offsets) | | p05 −\$9.43 / p50 −\$0.44 / p95 +\$12.12 | p_up 0.74 |
| N2, placebo reopens | 1,028 | −\$3.74 | −1.45; Welch (weekend − placebo) −0.07 |
| exit at 16:00 instead | 287 | −\$4.43 | −0.59 |
| the day-session version (the gap still open at 09:30, faded 09:31 → 16:00) | 284 | +\$3.06 | 0.81 |

**The touch test (18:06 → 09:30):**

| | fill (trades at Friday's close) | mirror (trades at R + G) | fill only / mirror only | sign test p |
|---|---|---|---|---|
| **weekends** | **43.6%** | **53.7%** | **52 / 81** | **0.015** |
| placebo reopens | 85.9% | 83.4% | 156 / 130 | |

- **The reading: NOTHING.**
  - FILL fails every leg. The folklore runs backwards: Monday's path reaches the level beyond the gap more often than
    it returns to Friday's close (81 against 52 discordant weekends, p 0.015). The placebo reopens lean slightly the
    other way (+2.5 points).
  - CONTINUATION passes its touch leg only. The signed mean (−\$4.24, t −0.65) is above N1's p05 and does not differ
    from the placebo (Welch −0.07).
  - So the path extends the gap more often than it fills it, but the 09:30 price does not end on the extension's
    side often enough to pay.
- **The folklore's own trade** (fade with a resting exit at Friday's close): it wins 57.1% of weekends with a median
  of +\$2.50, but the mean is **−\$9.90 (t −1.92)**. The target bracket buys a win rate and pays for it in the left
  tail (D752).
- **By |G| tercile:** fill rates of 0.68 / 0.40 / 0.23 against mirror rates of 0.79 / 0.54 / 0.28, with mean gross
  −\$0.92 / −\$2.44 / −\$9.36. The larger the gap, the less it fills, and the more the fade loses (not significant).

## 3. The four groups (P)

1. **Performance:**
   - net at \$4.31: Sharpe −0.53, Sortino −0.74; gross Sharpe −0.26 (annualised by 47.8 weekends a year);
   - mean net −\$8.55; −\$10.71 at 1.5× cost and −\$12.86 at 2×;
   - total net −\$2,454; max drawdown \$2,882;
   - exposure: about 15.4 hours on one session a week;
   - the mean |move| is 7.0 × 2c, and the breakeven cost is negative. **A signal failure, not a cost failure.**
2. **Trade distribution:**
   - 287 trades; mean net −\$8.55, median −\$5.31; win rate 0.40, payoff 1.11; skew +0.46, kurtosis 9.9;
   - net means ex-top 1% −\$14.16, ex-bottom 1% −\$3.65, trimmed −\$9.27;
   - the largest trades are all in 2021, when bitcoin was near \$60,000:
     - losers 2021-01-11 (−\$514), 2021-02-08 (−\$504), 2021-07-26 (−\$387);
     - winners 2021-02-22 (+\$624), 2021-04-26 (+\$576), 2021-09-20 (+\$381).
3. **What it depends on:**
   - **years (net):** 2018 −\$82, 2019 −\$285, 2020 −\$304, 2021 +\$664, 2022 −\$1,125, 2023 −\$1,322 (1 of 6
     positive);
   - **price:** a dollar trade scales with bitcoin's price, so 2021 dominates both tails;
   - **eras:** before MBT's listing +\$0.68 (n 154, t 0.08); the MBT era −\$9.94 (n 133, t −0.98);
   - **the calm split (#5's question):** Mondays in the calm-NQ gate move more, \$79.62 against \$47.96 mean
     |move|, but carry no direction (+\$0.22, n 109, against −\$6.98, n 178).
4. **Nulls:**
   - N1 is enumerated (SE 0): 74% of the rotations score at or above P, with p50 −\$0.44 and p95 +\$12.12. It is
     decisive against FILL.
   - N2: weekend and weekday reopens are indistinguishable on the fade (Welch −0.07).

**The component line:** net Sharpe −0.53, hit rate 0.40, skew +0.46, gross −\$4.24 beside net −\$8.55. The daily ρ
on the Monday trade dates (287) is +0.07 with D737's twin, −0.01 with NQ F2 and +0.04 with C1.

## 4. Reading

- **"CME gaps fill" is false here, and backwards on the path.** From 2018 to 2023, the Monday session to 09:30
  reached Friday's close on 44% of weekends and the equally distant level beyond the gap on 54%. A fade that waits for
  the fill wins often and loses on average.
- **No trade.** Neither the fade nor the follow pays at 09:30, at 16:00, or in the day session.
- **For #5:** BTC does move more on calm-NQ Mondays (\$80 against \$48), which repeats the hot-root table. But the
  weekend gap gives that size no direction.
- **POST HOC, not a lead:** the touch asymmetry (mirror > fill, p 0.015) is the only significant number. It says the
  weekend move tends to keep going briefly, not where Monday ends. A path trade on it (for example a stop-entry at
  the mirror) would be a new construction, and its own pre-registration on held data.
- GO is false. Nothing is admitted; the result is the principal's to close (R15).

## 5. CLOSED

*2026-10-02, the principal: "Close, merge and push".*
- **D758 is closed:** CME bitcoin's weekend gap gives no intraday trade on MBT. It neither fills nor continues to
  Monday 09:30 or 16:00.
- **Don't re-propose:**
  - the gap fade, with or without a target at Friday's close;
  - the follow;
  - the day-session fade of the gap left at 09:30.
- **What stays recorded:**
  - the size facts: the weekend gap is about four times a weekday reopen's; calm-NQ Mondays move more;
  - the POST HOC touch asymmetry (the mirror reached more often than the fill), which is not pursued.

# D777 STAGE 0 PRE-REG — fade the index futures' post-cash-close hour (16:00 → 17:00) from the 18:05 reopen to 10:00: is a price set after the stocks stop trading repriced overnight and at the next cash open?

*2026-10-02. The principal: "Pre-reg the post-close fade as D777".*

- **What it is:** a Stage 0 test of D772's Opus Lead 2. It fixes one construction, its nulls, its mechanism check and
  the principal's year test before anything unseen is read. It admits nothing.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the
  result separately.
- **The prop book's rules:**
  - one micro, entered 18:05 ET (the next trading day's open) and exited 10:00 ET, flat long before 16:10;
  - fully algorithmic; one position per root.
- **The overnight closure does not apply.** The principal ruled on 2026-10-02 (BOOK_PROP; D772 §1): signed fades of
  the index overnight leg are NOT inside the 2026-09-12 closure. This trade's P&L is −sign(m) × the overnight return,
  so it collects no drift. **The spent slice still binds** (§7).

## 0. What is already known, and what this test can and cannot claim

- **The in-sample data has been read.** D772's Opus pair found this construction in a search (the post-close hour,
  two placebo hours, two sub-windows, q80 and q90 gates, four exits, four roots).
- **Their numbers (q80, exit 10:00):**

| root | per micro | rank, exact rotation | notes |
|---|---|---|---|
| MNQ | **+\$24.62** | 0.997 | median +\$8.25, t 2.31; ex-2022 +\$13.37; ex-2020-and-2022 +\$17.11 |
| MES | +\$12.63 | 0.985 | |
| M2K | +\$11.07 | 0.992 | |
| MYM | +\$9.07 | 0.979 | ex-2022 only +\$2.37 |

- **The mechanism regression (NQ, every session):** the 18:05 → 10:00 move on the post-close move m, the day's move
  and the afternoon's move. b_m −0.39 (t −3.30), b_day +0.04 (t +1.39), b_afternoon −0.13 (t −2.24).
  - So a post-close point gives back about three times what an afternoon point does, and the day itself does not
    revert. That rules out K8, the daily reversal.
- **The placebos:** the other cash-shut windows (18:05 → 08:29, in slices) do not revert cleanly on any index root.
- **What did not hold:**
  - the same rule after each commodity's own settlement continues;
  - the 09:30 → 11:00 leg alone ranks only 0.878 on NQ;
  - about half of NQ's profit is 2022;
  - 2017–19 is 1.9× the cost on MNQ.
- **So this Stage 0 is not evidence that the effect exists.** Its jobs are:
  1. to fix the construction;
  2. to run the exact null on every root;
  3. to make the mechanism regression a gate;
  4. to apply the principal's year test;
  5. to name the roots on which a confirmation is possible.

## 1. The mechanism (what the test is about)

- **At 16:00 the constituent stocks stop trading.** For the next hour the index future is the only liquid instrument
  for index risk, with no cash or ETF arbitrage behind it and a thinner book.
- **What lands there:** post-close news, the residue of the closing auction, hedges of late fills.
- **Prediction:** the price it sets there is transient, and is corrected overnight and at the next cash open.
- **The same structure as D775:** a price made while the cash venue is shut.
- **The exchange moved this clock twice:**
  - settlement moved from 16:15 to 16:00 on 2020-10-26;
  - the daily 16:15–16:30 halt ended on 2021-06-25.
  - The pair found that the transient part moved with them. Reported as a natural experiment, not gated.

## 2. The construction

- **Bars:** each root's one-minute bars from `fut_opening_globex_1m` (ES, NQ) and `fut_opening_globex_1m_ym_rty` (YM,
  RTY).
  - Sessions 2016-01-01 → 2023-12-31; RTY's fixture starts 2017-07-10.
  - Each session is the Globex span from the evening before, 18:00, to 16:59 ET, on that session's front contract.
  - Bars are stamped at their START, so "the close of bar hh:mm" is the price at hh:mm + 1 minute.
  - Rows whose clock date is more than four days from their session are dropped (stray old-dated rows).
- **On session S:** m = close(16:59 bar; the 16:58 bar if 16:59 is missing) − close(15:59 bar). That is the 17:00
  price minus the 16:00 price.
- **The gate:** |m| at or above the 80th percentile of |m| over the 250 prior sessions (at least 120; strictly before
  S).
- **The trade, on session S+1** (the next trading day; at most four calendar days later):
  - side = −sign(m);
  - entry at the close of S+1's 18:04 bar (the 18:05 price, the evening of S);
  - exit at the close of S+1's 09:59 bar (the 10:00 price);
  - gross = side × (exit − entry) × the micro's \$ per point; net = gross − the round trip.
- **The micro lines:**

| micro | \$ per point | round trip |
|---|---|---|
| MNQ | \$2 | \$4.07 |
| MES | \$5 | \$4.42 |
| M2K | \$5 | \$3.76 |
| MYM | \$0.50 | \$3.80 |

- **Excluded (counted):**
  - a zero m;
  - a missing 15:59, 16:59/16:58, 18:04 or 09:59 bar;
  - S+1 more than four calendar days after S.
  - Entry and exit are both on S+1's front, so a roll cannot split the trade.
- **This is the measured version:** D772's script `crea_postclose_fade.py` used the same bars, gate and fills.

## 3. The gates (applied to each root)

| gate | condition |
|---|---|
| **G1, the effect** | mean gross > 0 with t ≥ 2 |
| **N, the null** | mean gross above the p95 of the exact time rotation: the signal series (side and gate) shifted circularly by k sessions against the outcome series, for every k = 1 … S − 1 (SE 0) |
| **M, the mechanism** | in the OLS over every valid session of y = (S+1's 10:00 − 18:05 move) on m, the day's move (S's 16:00 − 09:30) and the afternoon's (S's 16:00 − 13:00), b_m < 0 with heteroskedasticity-robust (HC1) t ≤ −2 |
| **Y, the principal's test** (D772 §1) | **either** (i) the win rate ≥ 50% in at least three-quarters of the root's full years, **or** (ii) the volatility-adjusted mean > 0 in at least three-quarters of them AND the first half's volatility-adjusted mean ≥ half the second half's |
| **G2, the prize** | mean net > 0 with t ≥ 2; net > 0 without its best two years; the mean gross without 2022 AND the 1%/1% trimmed mean gross each ≥ 2 × the round trip |

- **The volatility-adjusted return:** gross ÷ the standard deviation of the unsigned outcome (S+1's 10:00 − 18:05
  move × \$ per point) over the 60 prior sessions (at least 40). The halves are 2016–19 and 2020–23 (2017-07 → 2019
  for RTY).
- **The readings, in order:**

| reading | condition |
|---|---|
| **NO EFFECT** | G1 fails |
| **NOT ABOVE NULL** | N fails |
| **NO MECHANISM** | M fails |
| **CONCENTRATED** | Y fails |
| **NO PRIZE** | G2 fails |
| **SUPPORTED** | all pass |

- **GO = MNQ SUPPORTED, AND M2K or MYM passing G1, N and M.**
  - A pass must be confirmable. This trade on NQ and ES cannot be confirmed: their 2024+ 18:00 → 09:00 slice is spent
    (§7). So the second condition asks that a confirmable root carries the effect in-sample.
  - GO starts a confirmation conversation. It admits nothing.

## 4. Reported beside the gates (not gated)

- **The declared secondary, leg B:** the same side, from S+1's 09:29 close to its 10:59 close.
- **The hold split:** 18:05 → 09:30, then 09:30 → 10:00.
- **The q90 gate.**
- **The settlement regimes:** before 2020-10-26; 2020-10-26 → 2021-06-25; after.
- **The weekday split,** including the Tuesday/Thursday nights the pair flagged.
- **The nights before a D775 release day:** their count, and the ρ of the two books' daily P&L.
- **The cash-shut placebo** (the 18:05 → 20:00 move faded the same way).
- **All four groups for each root's book:**
  - **Performance:** gross and net, Sharpe and Sortino (daily, zero on untraded days), maximum drawdown, the mean
    |move| against the cost, the breakeven cost.
  - **Trade distribution:** count, mean, median, win rate, payoff, skew, kurtosis, the symmetric 1% trims, and the
    five largest and five worst trades named.
  - **What the winners depend on:** years, halves, m's sign, |m| terciles, weekend against weekday holds.
  - **Nulls:** p50, p95 and the rank.
- **The component line:** net Sharpe and Sortino, hit rate, skew, gross beside net, and the daily ρ with D737's twin,
  NQ F2, C1 (`temp/d755_other_lines.csv`) and D775's book.

## 5. Predictions and priors

- **MNQ:** G1, N and M pass (the numbers are known).
- **The risk is Y and G2.** 2017–19 was thin (1.9× cost), and the trimmed and ex-2022 means must each reach 2 × \$4.07.
  D772 had them at +\$21.59 and +\$13.37, so G2 should pass.
- **M2K:** G1, N and M pass (t about 2 is the risk).
- **MYM:** fails G2 on the ex-2022 mean.
- **The priors:** MNQ SUPPORTED about 45%; GO about 30%.

## 6. Runner assertions

- **Lag:**
  - m, the gate and the side use bars closed by 17:00 of S, and the threshold uses prior sessions only;
  - entry is at 18:05 on S+1;
  - a second implementation (explicit loops over the raw bar rows) re-derives m, the gate, the side and the gross on
    40 sampled trades per root.
- **Sign, in money:** an up post-close move followed by a fall overnight pays the fade; a mirrored book raises.
- **Right quantity:**
  - rotation offset 0 equals the observed;
  - read = traded + gated out + each exclusion;
  - the gated book differs from the ungated one;
  - nothing on or after 2024-01-01.
- **The self-test:**
  - synthetic sessions fade correctly across a weekend;
  - the threshold uses no same-day value;
  - the second implementation raises on a broken side;
  - chunk = whole for the rotation;
  - the whole study runs end to end on a synthetic panel.

## 7. The confirmation (designed here; it needs the principal's word)

- **NQ and ES:** their 2024+ 18:00 → 09:00 slice was read by D473 (BOOK_PROP: "spent"). This trade's 18:05 → 09:30
  part cannot be confirmed there. Only leg B (09:30 → 11:00, the day leg, unread) can, and in-sample leg B is weak
  (rank 0.878 on NQ).
- **M2K and MYM 2024+ are unread** ("every other root"). Leg A can be confirmed there:
  - in the joint vault on a programme slot (only slot 10 is free);
  - or on the forward recorder, which carries YM's full Globex minutes from 2026-10-01, not RTY's.
- **The result record computes the power of each route** from the in-sample per-trade dispersion.

## 8. Output

- `scripts/stage0_d777_post_close_fade.py`;
- `data/stage0_d777_post_close_fade.json` (statistics only).
- The result is a separate record.

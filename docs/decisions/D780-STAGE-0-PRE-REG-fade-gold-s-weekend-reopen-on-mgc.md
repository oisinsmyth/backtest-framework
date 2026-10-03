# D780 STAGE 0 PRE-REG — gold's weekend reopen (D772's Lead 3): does fading the Friday-close → Sunday-first-hour move on MGC into the Monday US morning pass the gates base L4 is measured against, so the two can be compared for programme slot 10?

*2026-10-03. The principal, on slot 10: "Remind me on L3?"; "Close 11 a year is too smal]" (C10, the debate's
19:00–20:59 breach fade, closed); "OK do stage 0 L3".*

- **What it is:** a Stage 0 test of D772's Opus Lead 3, fixed here before the runner exists. It admits nothing.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the
  result separately.
- **The prop book's rules:**
  - one micro (MGC, \$10 a point, \$5.93 a round trip);
  - entered Sunday 19:00 ET, which is Monday's trade date, and exited Monday 10:59 ET, flat long before 16:10;
  - fully algorithmic; one position; no weekend hold.
- **Why now:** programme slot 10 is the last free slot. Base L4 (M2K, D778's base book) and L3 are the two candidates.
  The principal asked for L3's Stage 0 before choosing.

## 0. What is already known: this test re-measures seen numbers

**This is not a discovery test.** Every number below was seen in-sample before this record. The Stage 0 puts L3 on the
same gates and the same four-group record as base L4, and adds the by-year test the principal set. Its likely
outcome is largely predictable (§4).

- **D772, the Opus pair (all Mondays, fade to 10:59, roll weekends kept):**
  - n 390, +\$15.93 gross per MGC, median +\$8.00, t 2.31, all 8 years' means positive;
  - 2020 = 43% of the P&L; 2017 +\$2.54, below the cost;
  - win 53.5%, skew +1.97; trimmed +\$14.55;
  - exact rotation rank 1.000 (p50 +\$0.02, p95 +\$11.18);
  - top trades 2020-11-09 +\$1,007 (the vaccine Monday), 2023-12-04 +\$953, 2022-06-13 +\$509;
  - gated at q80, +\$35.15 (t 2.59); exit 09:29, +\$12.88;
  - of seven GC off-hours windows, only the reopen reverts; the family test across 18 other roots failed (gold only).
  - The pair's own kill list for a confirmation: rotation rank < 0.95; ex-top-1% mean < 1.5× RT; the ex-2020-type
    mean < 1.5× RT; the 18:59 → 21:00 part of the hold ≤ 0.
- **The documentation session's gold debate (`working/gold_debate/`, gitignored), roll weekends dropped:**
  - L3 reproduced: n 389, +\$16.78, median +\$10, Newey-West t 2.26;
  - **the hold split by clock (fade \$ per MGC), 93 Mondays that breached Friday's range and 296 that did not:**

| | 19:00 → 20:59 | 21:00 → 02:59 | 03:00 → 10:59 |
|---|---|---|---|
| breach Mondays | +13.19 | +9.59 | −1.60 |
| inside Mondays | +0.49 | +5.19 | +9.71 |

  - The breach part (C10, 19:00 → 20:59) was closed by the principal on its event count (about 11 a year).
  - The documentation session reports that **the London/New York leg is about \$0 without 2020.** That figure is
    taken from its message, not re-derived here, and is treated as seen.
- **What that implies for this test:**
  - The whole-hold mean is not in doubt; G1 and N will very likely pass.
  - **G2 will very likely fail:** the implied net t is about 2.31 × (15.93 − 5.93) / 15.93 ≈ 1.45, below 2.
  - The open questions are the principal's year test (Y) and the full four-group record for the slot-10 comparison.

## 1. The construction (fixed here)

- **Bars:** `fut_opening_globex_1m_cl_ng_gc_si.csv.gz`, root GC.
  - One-minute bars, stamped at their START, on each session's front; "the close of bar hh:mm" is the price at
    hh:mm + 1 minute.
  - A session's evening bars (18:00 → 23:59) carry the calendar date before it, one to four days earlier; stray
    old-dated rows are dropped.
  - Sessions 2015-12-01 → 2023-12-31 are loaded. Monday sessions 2016-01-01 → 2023-12-31 are scored. Nothing on or after
    2024-01-01 is read (asserted).
- **The trade, on every Monday session S (the pair's definition):**
  - P = the 16:59 bar's close on the session before S (normally Friday);
  - m = close(S's evening 18:59 bar, the 19:00 print) − P;
  - side = −sign(m), entered at that 19:00 print;
  - exit at the close of S's 10:59 bar (the 11:00 price);
  - gross = side × (exit − entry) × \$10.
- **A Monday is scored when:**
  - all three prices exist;
  - m ≠ 0;
  - **all three bars are on one contract.** A roll weekend is dropped: its m would be a roll gap, not a move.
- **Reported beside the primary (not gated):**
  - the pair's version (roll weekends kept);
  - the 09:29 exit;
  - the q80-gated variant (|m| ≥ the 80th percentile of the 250 prior sessions' reopen moves, the pair's gate);
  - the hold split at 20:59 and 02:59 (the three legs above), all Mondays and by year;
  - ex-2020 numbers throughout.

## 2. Reported beside the gates

- **All four groups for the book:**
  - **Performance:** gross and net, Sharpe and Sortino (daily, zero on untraded days), maximum drawdown, the mean |move|
    against the cost, the breakeven cost.
  - **Trade distribution:** count, mean, median, win rate, payoff, skew, kurtosis, the symmetric 1% trims, and the five
    largest and five worst trades named.
  - **What the winners depend on:** years; the |m| terciles; the side (fading a weekend rise or fall); the legs.
  - **Nulls:** p50, p95 and the rank.
- **The component line:** the daily ρ (on the Monday the trade closes) with base L4 (D778's base book), D775's book,
  D777's (closed) MNQ book, and D737's twin, NQ F2 and C1.
- **The vault power for slot 10, for L3 and base L4 side by side:**
  - against a D776-style gate (≥ 40 trades, mean net > 0 and one-sided t ≥ 1.2816);
  - each line's trade count in 2024-01-01 → 2026-09-18 (from its in-sample rate) and its in-sample per-trade sd;
  - at three true edges: the in-sample net, the net without the best year, and zero.
  - A normal approximation, stated as such.

## 3. The gates

| gate | condition |
|---|---|
| **G1** | the mean gross > 0 with t ≥ 2 |
| **N** | the mean gross above the p95 of the exact time rotation of the side series against the outcomes over the scored Mondays, every offset (SE 0) |
| **Y, the principal's test** | (i) the win rate ≥ 50% in at least three-quarters of the full years; OR (ii) the volatility-adjusted mean > 0 in at least three-quarters of them AND 2016–19's ≥ half of 2020–23's |
| **G2** | the mean net > 0 with t ≥ 2; net > 0 without the best two years; **the mean gross without the best year** ≥ 2 × \$5.93; the 1%/1% trimmed mean ≥ 2 × \$5.93 |

- **The volatility-adjusted return:** the gross ÷ the standard deviation of the unsigned outcome (exit − entry, in \$)
  over the 20 prior scored Mondays (at least 12). Mondays without it are excluded from (ii) only.
- **The full years:** 2016–2023 (eight).
- **G2's third item differs from D778's** ("without 2022"). L3's concentration is 2020, so the item drops the
  best-contributing year, whichever it is. It is otherwise the same bar.
- **The readings, in order:**

| reading | condition |
|---|---|
| **NO EFFECT** | G1 fails |
| **NOT ABOVE NULL** | N fails |
| **CONCENTRATED** | Y fails |
| **NO PRIZE** | G2 fails |
| **SUPPORTED** | all pass |

- **GO = SUPPORTED.** It admits nothing.
- **Whatever the reading, the slot-10 choice stays the principal's.** The result lays out both lines on the same
  gates and the same power calculation.

## 4. Predictions and priors

- G1 and N pass (seen).
- **Y is the open gate.** The yearly means are all positive, but the win rate is 53.5% overall and the volatility-adjusted
  version has not been computed.
- G2 fails on net t (about 1.45) and, plausibly, on the without-best-year mean.
- **The prior:** SUPPORTED about 5%. NO PRIZE is the expected reading.

## 5. Runner assertions

- **Lag:**
  - m and the side use bars closed by 19:00 Sunday; the volatility scale uses prior Mondays only.
  - A second implementation (explicit loops over raw rows) re-derives P, m, the contract check, the side and the
    fade on 40 sampled Mondays.
- **Sign, in money:** a weekend rise followed by a fall to 11:00 pays the short fade; a mirrored book raises.
- **Right quantity:**
  - rotation offset 0 equals the observed;
  - the primary differs from the pair's version only on roll weekends;
  - every scored session is a Monday;
  - nothing on or after 2024-01-01.
- **The self-test:**
  - a planted reversion passes G1 and N;
  - a planted continuation fails G1;
  - a roll weekend is dropped;
  - the second implementation raises on a broken side;
  - chunk = whole for the rotation;
  - the whole study runs end to end on a synthetic panel.

## 6. Output

- `scripts/stage0_d780_gold_weekend_reopen_fade.py`;
- `data/stage0_d780_gold_weekend_reopen_fade.json` (statistics only).
- The result is a separate record.

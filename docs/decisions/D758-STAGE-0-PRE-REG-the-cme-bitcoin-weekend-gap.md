# D758 STAGE 0 PRE-REG — the CME bitcoin weekend gap on MBT: does Monday's session fill the gap to Friday's close, or extend it?

*2026-10-02. The principal: "Lets do #5" (a calm-day line outside the index micros); "Test the weekend gap, assume it
does allow MBT".*
- **What it is:** a premise check. It chooses no rule.
- **The order (R8):** this record is committed before the runner exists; the runner before its one run; the result
  separately.
- **The prop book's rules:** one MBT, held inside one CME session (Sunday 18:00 ET → Monday), flat long before Monday
  16:10 ET. The principal's assumption that the account allows MBT is recorded, not verified.

## 0. The mechanism and what is known

- **The structure:** CME bitcoin futures stop at 17:00 ET on Friday and reopen at 18:00 ET on Sunday, while spot
  bitcoin trades all weekend. The futures reopen at a gap G to Friday's close.
- **Two competing predictions, both reported:**
  - **FILL** (the widely repeated retail claim that "CME gaps fill"): price returns to Friday's close during the
    Monday session, so fading the gap pays.
  - **CONTINUATION:** the weekend move is information (spot price discovery the futures could not take part in), and
    the Monday session extends it.
  - A third reading, **neither**, is the efficient-market default: the gap is the price, and Monday is a random walk
    from it.
- **Why it might be a calm-day component (#5):**
  - on calm-NQ days, BTC's 09:00 → 15:00 |move| is 1.25 × its other days (the hot-root table, 2026-10-02,
    descriptive);
  - the BTC era (2018–2023) may confound that ratio: crypto's 2018 bear market fell in calm equity years.
    The calm split is reported, not part of any reading.
- **The repo:** no study on the weekend gap, on any root.
  - CME bitcoin intraday has been touched only by D580 (the funding clock, NOT SUPPORTED), D506 (the MACD arm, net
    −\$2.59 a trade) and D528 (2025–26 data only).
  - The nearest structural analogue is D725 (crossing yesterday's levels on NQ). Those levels were sticky zones, not
    launch points, and its mirror-level control is reused here.
- **The prior** (before any run): about 10–15%. The folklore is loud, and loud folklore is usually either arbitraged
  or never real.

## 1. Data, seal, conventions

- **The bars:** `data/fixtures/fut_btc_1m.csv.gz` (D580): BTC, the front contract per CME trade date, one-minute bars
  keyed by `ts_utc` (bar start). The `day` column is the CME trade date.
  - **Read as text, restricted on `day` < 2024-01-01** (`forward_f2_c1_ledgers.restrict_text`). Every kept row's
    timestamp is also asserted before 2024-01-01.
  - **A bar prints only when the contract trades** (59% of open minutes). Prices are carried forward between bars, and
    a "touch" is a traded high or low.
- **The seal:** nothing dated 2024-01-01 or later is read, for BTC or any other input.
- **The clock:** `ts_utc` is converted to America/New_York with zoneinfo.
  - This is checked against a statutory-rule second implementation (US: the second Sunday of March to the first
    Sunday of November).
  - Every session's first bar is reported against 18:00 ET.
- **Prices:** P(t) is the close of the last bar starting before t (carried forward). An entry at t fills at the open
  of the first bar starting at or after t; the entry minute is recorded.
- **Size and cost:** one MBT (0.1 bitcoin; a \$5 tick on the price is \$0.50).
  - The round trip is \$3 + the d508_exec crossing (2.616 ticks) = **\$4.31**.
  - 1.5× and 2× are reported, because Sunday-evening spreads are wider than the day-session ones the line was
    measured on.
  - **The prize bar is 2 × cost = \$8.62.**
  - MBT listed in 2021-05. Before that, MBT dollars are computed on the BTC price, because a 0.1-bitcoin contract did
    not trade. The MBT era is reported separately.

## 2. The events

- **A weekend event:** a CME trade date whose session opens on a Sunday (ET), where the previous trade date is the
  Friday two days earlier.
  - F = P(Friday 17:00 ET), the last traded price of Friday's session.
  - **The same contract is required on both sides.** A weekend where Friday's and Monday's front contracts differ
    (a roll) is excluded, and the count is reported.
- **Holiday reopens** (any other session gap of 24 hours or more) are reported separately and are not in any reading.
- **The window:** in-sample, CME trade dates 2018-01-01 → 2023-12-31 (six years; the December 2017 launch weeks are
  excluded).

## 3. The construction

- **The gap:** R = P(Sunday 18:05 ET), the price after the first five minutes; G = R − F.
- **The trade (primary):** the FADE, s = −sign(G).
  - Entry: the open of the first bar at or after 18:06 ET.
  - Exit: P(Monday 09:30 ET).
  - The statistic is the mean signed gross per weekend. A positive mean reads fill; a negative one reads
    continuation.
- **The mechanism read, path-based (the touch test):**
  - **fill:** the Monday session (from 18:06 to 09:30) trades at F;
  - **mirror:** it trades at R + G, the level the same distance on the other side.
  - Under no effect, a driftless path touches both equally often. FILL predicts fill > mirror; CONTINUATION predicts
    mirror > fill.
  - The test is the paired difference of the two touch indicators, with an exact two-sided sign test on the
    discordant weekends.
- **Reported (no reading):**
  - exit at Monday 16:00 ET instead of 09:30;
  - the folklore's own trade: the fade with its target at F (exit at F if touched, else 09:30). It is reported with
    its win rate and its mean; a target bracket buys a win rate (D752);
  - the day-session version: the gap still open at Monday 09:30 (F against P(09:30)), faded from 09:31 to 16:00;
  - |G| terciles; the MBT era (2021-05-03 →) against the years before.

## 4. Controls and nulls

- **N1, the sign rotation (primary, enumerated, SE 0):** s rotated circularly across the weekends, every offset; the
  statistic is the mean signed gross.
- **N2, the placebo reopens:**
  - every Monday–Thursday reopen after the daily one-hour halt (18:00 ET), with F = the last price before the halt;
  - the same R, G, s, entry rule and an exit 15.4 hours later (09:30 ET the next morning);
  - the same touch test.
  - The weekend fade must beat the placebo fade (Welch t ≥ 1.64), and the weekend touch difference must exceed the
    placebo's.
- **The eras (reported):** each year 2018–2023; before and after MBT's listing.
- **The calm split (reported):** Mondays in and out of D754's walk-forward calm-NQ gate (NQ rv20 lowest third).

## 5. Oracles (first)

- **O1, the size:** the mean |P(09:30) − entry| in MBT dollars on weekend events, against the placebo and the \$8.62
  bar.
  - **NO ROOM** if it is below \$8.62.
  - **NOT SPECIAL** (reported) if it does not exceed the placebo's (Welch t ≥ 2).
- **O2, the gap's size:** the mean |G| in dollars and in units of the Friday session's range; the weekend's against
  the placebo's.

## 6. Readings (declared now)

| reading | condition |
|---|---|
| **NO ROOM** | O1 below \$8.62. Recorded first |
| **FILL** | the fade's mean signed gross > 0 at t ≥ 2, **and** above N1's p95, **and** above N2's (Welch t ≥ 1.64), **and** the fill touches exceed the mirror touches (sign test p < 0.05) |
| **CONTINUATION** | the fade's mean signed gross < 0 at t ≤ −2, **and** below N1's p05, **and** below N2's (Welch t ≤ −1.64), **and** the mirror touches exceed the fill touches (p < 0.05) |
| **NOTHING** | otherwise |

**GO to a rule design with the principal** requires all of:
- FILL or CONTINUATION, and not NO ROOM;
- the winning side's mean net > 0 at \$4.31;
- ≥ 4 of the 6 years positive (net), and the largest year < 50% of the total;
- the MBT era's (2021-05 →) mean in the same direction > 0.

GO starts the design conversation; it admits nothing.

**Reported, all four groups:**
- gross and net at \$4.31, 1.5× and 2×; Sharpe and Sortino (annualised by the events a year); max drawdown;
  the mean move against 2c; the breakeven cost;
- count, mean, median, win rate, payoff, skew, kurtosis, the symmetric trims, and the largest trades named;
- years, eras, |G| terciles, the calm split, N1's p50 and p95, N2;
- **the component line:** net Sharpe, hit rate, skew, gross beside net, and the daily ρ (on the Monday trade date)
  with D737's twin, NQ F2 and C1 over their span.

## 7. Runner assertions

- **Lag:**
  - G reads no bar starting at or after 18:05 ET; a canary that includes that bar must change some signs;
  - the entry is at or after 18:06.
- **The clock:** zoneinfo against the statutory-rule implementation on every event and placebo timestamp.
- **Sign, in money:** a synthetic down-gap followed by a rise pays the fade (long), and the audit raises on a
  mirrored book.
- **Right quantity:**
  - the fill and mirror levels differ;
  - no placebo is a weekend event;
  - the events used plus those excluded (roll, missing bars) equal the weekends read.
- **The seal:** no kept row has a day or timestamp on or after 2024-01-01.

## 8. Output

- `scripts/stage0_d758_btc_weekend_gap.py`;
- `data/stage0_d758_btc_weekend_gap.json` (statistics only).
- The result is a separate record.

# D749 STAGE 0 PRE-REG — the month-end London 4pm fix on M6E: do foreign holders of hedged US equities move EUR/USD into the WM/Reuters fix, in the direction the month's US equity return dictates?

*2026-10-01. The principal: "I would like the some new ideas"; "Don't like any of those can think of some more, have
a fable 5.1 agent think of some also"; "Pre-reg D749 and run the month-end fix oracle".*
- **How the idea was found:** this session and a Fable 5.1 agent each drafted a list independently (this session's
  was written to the scratchpad before reading the agent's). Both ranked this idea first.
- **What it is:** a premise check, oracle first. It chooses no rule.
- **The order (R8):** this record is committed before the runner exists, the runner before its one run, and the result
  separately.
- **The prop book's rules:** one M6E, held 30 minutes inside the day session, so it is flat long before 16:10.

## 0. The mechanism and what is known

- **The mechanism (Melvin & Prins 2015, "Equity hedging and exchange rates at the London 4 p.m. fix").** Foreign
  investors who hold US equities with a currency hedge must top up the hedge at month-end, and the trades execute at
  the WM/Reuters 4 p.m. London fix.
  - When US equities have risen over the month, their dollar exposure has grown, so they sell dollars into the fix.
  - The dollar therefore weakens (EUR/USD rises) into the fix, with a partial reversal after.
  - The flow is forced, it is dated, and its sign is known before the window.
- **Nothing in this repo has traded it.** A search found no study on a London, Tokyo or Shanghai clock. The fix
  appears only as a label: D675's flow-intensity F6, and D709's note that silver funds once struck at the fix.
  - The nearest work, D685/D686 (the month-end 60/40 rebalancing drift on ES and ZN, MECHANISM ONLY, fading), is a
    different market and a different flow.
- **The prior** (before any run): this session about 20%, the Fable agent 35%. The 2015 widening of the fix window
  (1 → 5 minutes), and the flow being widely known since 2013, both argue it has faded.

## 1. Data, seal, conventions

- **Bars:** `fut_day1m.parquet`, 6E, 09:00–16:00 ET one-minute bars on the front contract (D506; the front from
  `fut_breadth_hourly`).
  - Read with a parquet filter on root ∈ {6E} and day < 2024-01-01, so no later row is materialised.
  - Sessions must have `present` and `same_front` true (no roll inside the session).
- **The window:** 2011-01-01 → 2023-12-31 (6E's first clean year is 2011). The seal: nothing dated 2024-01-01 or
  later is read, for any input.
- **The sign:** SPY's daily close (`data/raw/alphavantage/daily/SPY.json.gz`, keys before 2024-01-01).
  - The month-to-date return is the prior trading day's close over the last close of the previous month, minus 1.
  - **D = +1 (long M6E, i.e. long EUR/USD) if it is > 0; −1 if < 0.** Everything is known before the window opens.
- **The fix clock:** 16:00 Europe/London converted to America/New_York for each date. That is normally 11:00 ET, and
  **12:00 ET in the weeks when US and UK daylight saving differ** (most October month-ends, some in March).
- **The trade, P (pre-fix, primary):**
  - enter at the open of the bar that starts 30 minutes before the fix;
  - exit at the close of the bar that starts 1 minute before the fix (the price at the fix's start).
- **Reported:**
  - P+ (exit 3 minutes after the fix, past the post-2015 five-minute window);
  - R (the post-fix fade): −D from the fix bar's open to 30 minutes after.
- **Size and cost:** one M6E (€12,500; a tick of 0.0001 is \$1.25).
  - The round trip is \$3 + the d508_exec crossing (1.106 ticks) = **\$4.38**.
  - **The prize bar is 2 × cost = \$8.76.**
- **The events:** the last 6E session of each calendar month, about 156 in all. Quarter-ends (March, June, September,
  December) are reported separately.

## 2. Controls and nulls

- **N1, the sign-rotation null (primary, enumerated, SE 0):** the D series is rotated circularly across the month-ends
  (offsets 1 … n − 1), and the statistic is the mean signed gross. It asks whether the month's own equity sign beats a
  sign from another month on the same windows.
- **N2, the placebo days:**
  - the same window, at each day's own fix clock, on business days −5 … −2 before each month-end;
  - each with its own D (SPY's month-to-date return to its prior close).
  - The flow is month-end-specific, so the month-end mean must exceed the placebo mean.
- **N3, the clock control (reported; small n):** on the daylight-saving-mismatch month-ends, the window ending at the
  real fix (12:00 ET) against the window ending at 11:00 ET. A London flow moves with London; an ET artefact does not.
- **Eras (reported):** before and after the February 2015 fix reform (window widened to 5 minutes).

## 3. Oracles (first; they can kill it)

- **O1, the perfect-sign ceiling:** the mean |window move| in dollars, less cost. If the mean |move| < 2 × cost
  (\$8.76), no sign rule can pay: **NO ROOM**.
- **O3, the size at stake:** the median |move| and its quartiles in dollars, for P and R.

## 4. Readings (declared now)

| reading | condition |
|---|---|
| **NO ROOM** | the mean \|P move\| < \$8.76. Recorded first |
| **FLOW PRESENT** | P's mean signed gross > 0 at t ≥ 2 (month-ends are independent; plain t), **and** above N1's p95, **and** above the placebo mean (difference > 0, Welch t ≥ 1.64) |
| **NOTHING** | otherwise |

**GO to a rule design with the principal** requires all of:
- FLOW PRESENT, and not NO ROOM;
- mean net > 0 at one M6E;
- ≥ 8 of the 13 years positive, and the largest year < 50% of the total;
- the post-2015 era's mean signed gross > 0.

GO starts the design conversation; it admits nothing.

**Reported, all four groups:**
- gross and net; Sharpe and Sortino (annualised by 12 trades a year); max drawdown;
- the mean move against 2c, and the breakeven cost;
- count, mean, median, win rate, payoff, skew, kurtosis, and the symmetric trims;
- the years, quarter-ends against other month-ends, and long against short;
- the eras, N1's p50 and p95, N2's mean and t, N3;
- the component line: net Sharpe, hit rate, skew, gross beside net, and the same-day P&L of D737's twin, NQ F2 and
  C1 on the event days.

## 5. Runner assertions

- **Lag:**
  - D uses only SPY closes strictly before the event day, re-derived from the raw file on a sample;
  - a canary using the event day's own close must change some D;
  - the window's bars all start before the fix.
- **The clock:** for a sample of dates, the fix in ET equals 16:00 London converted independently (UTC offsets
  computed by hand from the rule: last Sunday of March/October in the UK; second Sunday of March and first Sunday of
  November in the US).
- **Sign, in money:** a synthetic rise with D = +1 pays +, and with D = −1 pays −.
- **Right quantity:** P ≠ R; the mismatch month-ends exist (> 0); the placebo days do not include month-ends.

## 6. Output

`scripts/stage0_d749_month_end_fix.py` and `data/stage0_d749_month_end_fix.json` (statistics only). The result is a
separate record.

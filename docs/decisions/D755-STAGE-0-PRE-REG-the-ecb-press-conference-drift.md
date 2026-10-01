# D755 STAGE 0 PRE-REG — the ECB press-conference drift on M6E: does EUR/USD keep moving through the press conference in the direction the policy statement set?

*2026-10-02. The principal: "Close D754, then lets go back to the other ideas that the agents found"; "Run the
hot-root table then pre-reg the ECB as D755". The idea is the Fable 5.1 reasoning agent's #4 from the calm-bull round
(2026-10-02).*
- **What it is:** a premise check. It chooses no rule.
- **The order (R8):** this record is committed before the calendar fixture and the runner exist. The fixture and the
  runner are committed before the one run, and the result separately.
- **The prop book's rules:** one M6E, held about an hour inside one session (08:30–09:45 ET at the latest), flat long
  before 16:10.

## 0. The mechanism and what is known

- **The mechanism (the agent's):**
  - The ECB publishes its decision as a press release, then holds a press conference 30 minutes later.
  - The Q&A releases information sequentially, and mostly in the direction the statement already set (forward
    guidance and the balance of risks).
  - Option dealers hedge the realised move, and macro funds scale into the day's direction after the conference
    rather than at the release.
  - **The prediction:** the move from the release to the conference's start (J) continues through the conference.
- **The competing prediction:** the conference walks the statement back (in the Draghi years a common reading),
  which would be a reversal. Both signs are reported. Only continuation is the hypothesis.
- **The repo:** no study on the ECB, on a central-bank press conference, or on a European clock (searched
  2026-10-02).
  - The nearest work: D749 (the London fix on M6E, NOTHING) and D710 (the US Treasury auction, MECHANISM ONLY).
  - FOMC days were used only as gates or vetoes (D494, D671, D702, D743).
- **The size, from the hot-root table** (2026-10-02, descriptive; scratchpad `hot_roots.py`):
  - M6E is the weakest mover of the micros, with an average 09:00 → 15:00 |move| of \$27 to \$34, against a \$8.76
    bar.
  - An average hour is about \$10–13, so **the trade pays only if ECB press-conference hours are much larger than an
    average hour**. O1 below is the first test.
- **The prior** (before any run): about 15–20%. The agent said 20%. Power is the main risk: about 130 meetings over
  2011–2023.

## 1. Step 1 — the ECB calendar fixture (built and committed before the runner)

- **The file:** `data/calendar/ecb_meetings.csv`, one row per Governing Council monetary-policy meeting with a press
  conference, 2011-01-01 → 2023-12-31.
- **Columns:**
  - the date;
  - the published decision release time (CET/CEST);
  - the press-conference start time;
  - the decision itself (rate change, or none);
  - the source URL and the access time.
- **The source:** the ECB's own monetary-policy decision and press-conference pages (ecb.europa.eu), as D585 did for
  the US releases.
  - Where the ECB changed its timetable, each row carries the time that applied that day, with a source.
  - Any row that cannot be sourced is excluded and listed, never estimated.
- **Rules for the fixture:**
  - only dates and clock times;
  - no price, no surprise measure, no analyst expectation.
- It gets its own `.meta.json` (row count, the sources, and the excluded rows).

## 2. Data, seal, conventions

- **The bars:** 6E (EUR/USD futures, front contract) one-minute OHLCV, 06:00 → 12:00 ET on each event and placebo
  day.
  - Read from the raw Databento ohlcv-1m archive under the system interpreter: `fut_day1m` starts at 09:00 ET, which
    is too late.
  - The front contract per day is `fut_breadth_hourly`'s 6E contract, not re-elected.
  - Each record is restricted by its timestamp before 2024-01-01 at read time.
- **The seal:** nothing dated 2024-01-01 or later is read, for 6E or any other input.
- **The clock:**
  - each ECB time is converted from Europe/Frankfurt to America/New_York per date (zoneinfo). This is checked against
    a statutory-rule implementation (EU: last Sunday of March / October; US: second Sunday of March / first Sunday of
    November).
  - T_d = the decision release, T_p = the press conference start, both in ET minutes.
- **Prices:** P(t) is the close of the bar starting at t − 1 (the price at t). An entry at t fills at the open of the
  bar starting at t.
- **Size and cost:** one M6E (€12,500; a 0.0001 tick is \$1.25).
  - The round trip is \$3 + the d508_exec crossing (1.106 ticks) = **\$4.38**, with 1.5× (\$5.07) reported, since the
    window is before the US open.
  - **The prize bar is 2 × cost = \$8.76.**

## 3. The construction

- **The signal:** J = P(T_p) − P(T_d) (the statement's reaction up to the conference's start); s = sign(J).
- **The trade (primary):** s from T_p + 2 minutes (the bar's open) to T_p + 60 minutes (the price at that minute).
  That is about 58 minutes, roughly the conference plus its aftermath.
- **Reported:**
  - the gated trade, |J| ≥ 25 pips (\$31 at one M6E);
  - the exit at T_p + 30;
  - the fade (−s), and E-pre (s from T_d + 5 to T_p, the drift before the conference).

## 4. Controls and nulls

- **N1, the sign rotation (primary, enumerated, SE 0):** s rotated circularly across the meetings, every offset; the
  statistic is the mean signed gross.
- **N2, the placebo Thursdays:**
  - the same Frankfurt clock on Thursdays with no ECB meeting (the Council meets on Thursdays);
  - the same J and s construction, and the same trade;
  - the ECB mean must exceed the placebo mean (Welch t ≥ 1.64).
- **N3, the FOMC replication on M6E (reported, never in the reading):** statement 14:00 ET, press conference
  14:30 ET (D585's `events.csv`; FOMC press conferences held quarterly before 2019, every meeting after). The same
  construction.
- **The eras (reported):** Trichet (to 2011-10), Draghi (2011-11 → 2019-10), Lagarde (2019-11 →).

## 5. Oracles (first)

- **O1, the size:** the mean |trade move| in dollars on ECB days, against placebo Thursdays and against the \$8.76
  bar.
  - **NO ROOM** if the ECB-day mean |move| < \$8.76.
  - **NOT SPECIAL** (reported) if it does not exceed the placebo by Welch t ≥ 2.
- **O3:** the |move| quartiles.

## 6. Readings (declared now)

| reading | condition |
|---|---|
| **NO ROOM** | O1's ECB-day mean \|move\| < \$8.76. Recorded first |
| **CONTINUATION** | the mean signed gross > 0 at t ≥ 2 (meetings are independent; plain t), **and** above N1's p95, **and** above N2's placebo mean (Welch t ≥ 1.64) |
| **REVERSAL** (reported, not the hypothesis) | the mean signed gross < 0 at t ≤ −2 and below N1's p05. It would be a premise for a separate pre-registration only |
| **NOTHING** | otherwise |

**GO to a rule design with the principal** requires all of:
- CONTINUATION, and not NO ROOM;
- mean net > 0 at \$4.38;
- ≥ 8 of the 13 years positive, and the largest year < 50% of the total;
- the Lagarde era's mean signed gross > 0.

GO starts the design conversation; it admits nothing.

**Reported, all four groups:**
- gross and net at both cost lines; Sharpe and Sortino (annualised by the meetings a year); max drawdown;
- the mean move against 2c, and the breakeven cost;
- count, mean, median, win rate, payoff, skew, kurtosis, and the symmetric trims;
- the years, the eras, rate-change meetings against no-change meetings, N1's p50 and p95, N2, and N3;
- **the component line:** net Sharpe, hit rate, skew, gross beside net, and the daily ρ with D737's twin, NQ F2 and
  C1 (their in-sample daily nets).

## 7. Runner assertions

- **Lag:**
  - J reads no bar starting at or after T_p, and a canary including the T_p bar must change some s;
  - the entry is at T_p + 2, after J's last bar.
- **The clock:** zoneinfo against the statutory-rule implementation on every event and placebo day. Mismatch weeks
  exist only if the fixture has meetings in them, and that count is reported.
- **Sign, in money:** a synthetic rise pays the long M6E.
- **Right quantity:**
  - the trade window differs from J's;
  - no placebo day is an ECB day;
  - the fixture rows used equal the rows read.

## 8. Output

- `data/calendar/ecb_meetings.csv` and its `.meta.json` (step 1);
- `scripts/stage0_d755_ecb_press_conference.py`;
- `data/stage0_d755_ecb_press_conference.json` (statistics only).
- The result is a separate record.

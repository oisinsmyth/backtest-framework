# D755 STAGE 0 RESULT — NOTHING: ECB press-conference hours are three times an ordinary Thursday's on M6E, but the statement's reaction does not set their direction

*2026-10-02. One scored run of `scripts/stage0_d755_ecb_press_conference.py --run` (under a second). The
[pre-registration](D755-STAGE-0-PRE-REG-the-ecb-press-conference-drift.md) (`05fcf67f`) was committed before the
calendar fixture and the runner (`data/calendar/ecb_meetings.csv`, the runner and its fix: up to `0485c2af`), and they
were committed before the run.*
- **Output:** `data/stage0_d755_ecb_press_conference.json` (statistics only).
- **An earlier attempt stopped on a TypeError** in the placebo loop, after the event rows were built and before any
  statistic was computed, printed or written. The fix (`0485c2af`) casts the days to str. The whole run path was then
  exercised on synthetic prices before the one scored run.

## 0. Checks

- **The seal:** the 6E minutes were extracted from the raw ohlcv-1m archive with `ts_event` < 2024-01-01, and the
  cache is asserted before 2024 on read. Nothing dated 2024 or later was read.
- **The calendar:** 120 meetings, 2011-01-13 → 2023-12-14 (12 a year to 2014, 8 after). The hash matches its
  `.meta.json`.
  - Each row's date, decision and press-conference clock come from that meeting's ECB release.
  - The decision clock (13:45 CET; 14:15 from 2022-07-21) is the ECB's published schedule, not a per-meeting quote
    (disclosed in each row and in `SOURCES.md`).
  - A second, independent pass re-fetched six seeded rows and the timing release; all matched.
- **The clock:** zoneinfo equals the statutory-rule implementation on every event (and on every business day
  2011–2023 in the self-test).
  - Four meetings fall in the weeks when Frankfurt and New York are 5 hours apart: 2011-11-03, 2020-03-12,
    2020-10-29 and 2023-03-16. Their hold runs an hour later (to 10:30–10:45 ET), outside the pre-registration's
    "09:45 at the latest". That sentence assumed the 6-hour gap.
- **Lag:** J reads no bar starting at or after T_p; the canary that includes the T_p bar changed some signs. The entry
  is at T_p + 2.
- **Sign, in money:** a rising statement reaction goes long, and a continued rise pays it. The audit raises on a
  mirrored book (self-test).
- **Right quantity:**
  - the rows used plus the rows without bars equal the rows read (117 + 3 = 120);
  - no placebo day is an ECB day.
- **Without bars:** 2012-03-08, 2013-07-04 (a US holiday) and 2015-04-15 (a day the front-contract map does not
  cover).

## 1. The oracle first: there is room

| | ECB days (117) | placebo Thursdays (529) |
|---|---|---|
| mean \|move\|, T_p + 2 → T_p + 60, one M6E | **\$56.54** | \$17.24 |
| against 2c (\$8.76) | **6.45×** | 1.97× |

- **NO ROOM: false.** The ECB hour is 6.5 times the bar.
- **NOT SPECIAL: false.** It is 3.3 times the placebo (Welch t 9.06).
- **O3, the |move| quartiles:** \$20.00 / \$45.63 / \$82.50.
- **The hot-root table's worry is answered:** M6E is a poor mover on an ordinary hour, but not in this hour. The
  size premise holds.

## 2. The direction: none

| | n | mean gross | t |
|---|---|---|---|
| **P, s = sign(J), T_p + 2 → T_p + 60** | 117 | **−\$5.98** | −0.89 |
| N1, the enumerated sign rotation (116 offsets) | | p05 −\$8.18 / p50 +\$0.45 / p95 +\$10.85 | p_up 0.89 |
| N2, placebo Thursdays | 529 | +\$0.24 | 0.22; Welch (ECB − placebo) −0.91 |
| gated, \|J\| ≥ 25 pips | 37 | −\$13.89 | −0.98 |
| the exit at T_p + 30 | 117 | −\$1.99 | −0.35 |
| N3, FOMC on M6E (scheduled 14:00 statements, 2019–2023) | 39 | −\$8.00 | −0.91 |

- **The reading: NOTHING.**
  - CONTINUATION fails every leg: the mean is negative, its t is −0.89, and it sits below the rotation's p50.
  - REVERSAL fails too: t −0.89 is not ≤ −2, and −\$5.98 is above N1's p05 (−\$8.18).
  - The statement's reaction agrees with the hour's direction on 49.6% of meetings.
- **E-pre is VOID, not a result.** As pre-registered it scores s from T_d + 5 to T_p. But s = sign(J), and J is
  measured over T_d → T_p, so it overlaps the very window it scores. The +\$12.83 (t 6.51) is that overlap. The flaw
  is the pre-registration's own, caught here and not used.
- **N3's scope:** the pre-registration did not name the FOMC years. The runner used the scheduled 14:00 statements of
  2019–2023, the years when every meeting had a press conference. N3 is reported only.

## 3. The four groups (P)

1. **Performance (net at \$4.38 beside gross):**
   - net Sharpe −0.43, Sortino −0.55; gross Sharpe −0.25 (annualised by 9 meetings a year);
   - mean net −\$10.36; at 1.5× cost −\$12.55; total net −\$1,212; max drawdown \$1,936;
   - per-trade standard deviation ≈ \$73;
   - exposure: 58 minutes on 9 days a year;
   - the mean |move| is 6.45× 2c, and the breakeven cost is negative (−\$5.98): **a signal failure, not a cost
     failure.**
2. **Trade distribution:**
   - 117 trades; mean net −\$10.36, median −\$4.38; win rate 0.45, payoff 0.83; skew +0.05, kurtosis 0.52;
   - ex-top 1% −\$12.10, ex-bottom 1% −\$8.55, trimmed −\$10.29;
   - the largest trades are named both ways: losers 2012-08-02 (−\$216), 2016-03-10 (−\$206), 2014-02-06 (−\$146);
     winners 2015-12-03 (+\$196), 2015-01-22 (+\$170), 2011-06-09 (+\$165).
3. **What it depends on:**
   - **years:** 4 of 13 positive (2011, 2015, 2016, 2023); the largest-year share is undefined, since the total is
     negative;
   - **eras:** Trichet +\$38.62 (n 10, t 1.43), Draghi −\$13.80 (n 74, t −1.54), Lagarde −\$1.95 (n 33, t −0.21);
   - **decisions:** cuts −\$33.63 (n 10), hikes +\$8.85 (n 12), no change −\$4.94 (n 95).
4. **Nulls:** N1 is enumerated (SE 0): 89% of the rotations score at or above P (p_up 0.89), with p50 +\$0.45 and
   p95 +\$10.85. The null is decisive against continuation. N2 is not beaten.

**The component line:** net Sharpe −0.43, hit rate 0.45, skew +0.05, gross −\$5.98 beside net −\$10.36. The daily ρ
over the other lines' span (2016-02-24 → 2023, 63 ECB days) is −0.01 with D737's twin, −0.03 with NQ F2 and −0.01 with
C1.

## 4. Reading

- **ECB hours are large and real, but have no direction from the statement.** The press conference moves EUR/USD
  three times an ordinary Thursday's hour, but the move from the release to the conference does not say which way.
  The hour neither continues the statement's reaction nor reverses it.
- **The Draghi-era lean toward reversal** (−\$13.80, t −1.54), and the two largest losers (2012-08-02, 2016-03-10,
  both conferences remembered for walking back the statement), are the competing prediction's shape. They are below
  its declared bar, and **POST HOC: not a lead.** A reversal premise would need its own pre-registration, and the
  Lagarde era (−\$1.95) does not carry it.
- **What the record leaves:** a size fact, not a direction. ECB press-conference hours are a known, scheduled
  high-|move| window on M6E (\$56 against \$17). Under the standing memory, confluences can predict size and not
  direction: this is one more case.
- GO is false. Nothing is admitted; the result is the principal's to close (R15).

## 5. CLOSED

*2026-10-02, the principal: "Close D755 and push it".*
- **D755 is closed:** the statement-to-conference move does not set the direction of the ECB press-conference hour
  on M6E.
- **Don't re-propose:**
  - the continuation trade on sign(J);
  - its gated (|J| ≥ 25 pips) and 30-minute variants.
- **What stays recorded:**
  - **the size fact:** a scheduled hour 3.3 times an ordinary Thursday's, and 6.5 times 2c;
  - **the calendar fixture:** it is reusable;
  - **the post hoc Draghi-era reversal lean:** recorded, not pursued.

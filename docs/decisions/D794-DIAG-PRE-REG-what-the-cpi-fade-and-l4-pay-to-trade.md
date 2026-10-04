# D794 DIAG PRE-REGISTRATION — what the CPI/jobs-report fade (D776) and base L4 (D781) actually pay to trade: the quoted spread at their own fill seconds, against the crossing their cost lines assume

*2026-10-04.*
- *The principal: "Start the fill-cost measurement", then "Yes buy the \$24 set".*
- *Numbered D794: the China-open session holds D793 and was told.*
- ***Committed before the analysis script exists and before any quote is read.*** *The quotes being bought
  (`scripts/fetch_fill_cost_quotes.py`, manifest `data/fill_cost_quotes_manifest.csv`) are in-sample only, 2016–2023.*

## 0. Why

**Both frozen lines charge \$3 plus an assumed crossing** (D694's `cost_lines`: \$3 + crossing ticks × tick value):

| line | micro | tick | assumed crossing, round trip | cost line |
|---|---|---:|---:|---:|
| D776, the CPI/jobs-report fade | MNQ | \$0.50 | **2.134 ticks** | \$4.067 |
| D781, base L4 | M2K | \$0.50 | **1.514 ticks** | \$3.757 |

**The crossings were measured on ordinary bars, not at these lines' fills.** D776 enters at the 08:34 bar's close,
four minutes after a CPI or jobs-report print, when the book may be thin and wide. L4 enters at the 18:05 reopen.
The memory rule applies: measure the spread at the strategy's own fill timestamps.

**This changes no freeze and no gate.** It answers whether a vault or forward pass would survive real fills, and gives
the forward ledgers a measured cost to report beside the frozen one.

## 1. The fills (each line's own definition, unchanged)

| line | entry | exit | trades |
|---|---|---|---|
| D776 | the close of the 08:34 bar (the last price before 08:35:00 ET), release days | the close of the 11:00 bar (before 11:01:00) | D775's 186 in-sample trades |
| L4 | the close of the 18:04 bar (before 18:05:00 ET) on the evening the exit session opens | the close of the 09:59 bar (before 10:00:00) | D778's 280 base-book trades |

**The fill second** is the last whole second before each boundary: 08:34:59, 10:59:59 or 11:00:59 as D775's bar
labels resolve, 18:04:59 and 09:59:59. The script reads the bar convention from D775's and D778's own `BARS` and
states it.

**The symbols:**
- **Primary:** the micros the lines trade, MNQ and M2K. They exist from 2019-05-06, so these are 108 of D776's
  trades and 232 of L4's.
- **Reference:** the full-size NQ and RTY over all trades. They are used to check, on the overlap years, whether the
  full-size spread predicts the micro's.

## 2. The measures (fixed now)

1. **The quoted spread at each fill second,** in ticks, from `bbo-1s`: ask − bid of the 1-second record covering
   the fill second. If that second has no record, the last record before it, at most 5 s old. Otherwise the fill is
   reported as missing and never filled in.
2. **The measured crossing per trade, round trip,** in ticks: (spread at entry + spread at exit) / 2. A marketable
   order pays half the spread on each side.
3. **The effective crossing,** from `tbbo`. For each fill, take the trades printed in the 5 s after the fill second:
   - each trade's distance from the prevailing mid, in ticks, on the side a marketable order would take;
   - their median per fill, reported beside measure 2 as the realised half-spread;
   - the touch size (bid and ask size) at the fill. Size matters only if the touch is below one lot, which at one
     micro is not expected.
4. **The measured cost line:** \$3 + the mean measured crossing (measure 2) × \$0.50. Also its p50 and p90 across
   trades.
5. **Each line's in-sample mean net, re-computed at the measured cost,** beside the frozen one:
   - D776: \$30.81 at \$4.07, gross \$34.88;
   - L4: \$12.08 at \$3.76, gross \$15.84;
   - the breakeven crossing in ticks.

**Splits:** by year; for D776, CPI against EMPSIT; for L4, the entry against the exit leg. **A control:** the same
clock on the line's non-trade days, on the full-size reference only (not bought for the micros). This tells whether
the fill's spread is the event's or the clock's.

## 3. How it is read (fixed now)

| reading | when |
|---|---|
| **COST LINE HOLDS** | the measured mean crossing (measure 2) is at or below the assumed (2.134 MNQ, 1.514 M2K) |
| **COST LINE UNDERSTATES** | it is above the assumed. The report gives the measured cost line and the re-computed mean net |
| **THE LINE DOES NOT BOOK** | the re-computed in-sample mean net at the measured cost is ≤ 0 |

**Consequences:**
- None of these readings edits D776, D781, D792 or any freeze. A frozen line is scored at its frozen cost.
- **COST LINE UNDERSTATES:** the forward ledgers report the measured cost beside the frozen one, on the principal's word.
- **THE LINE DOES NOT BOOK:** that is written into the line's components-ledger entry before the joint run. Any
  change to the line is the principal's call.

**Predictions:**

| # | prediction |
|---|---|
| 1 | D776's 08:34 entry spread on MNQ is wider than its 11:00 exit spread |
| 2 | D776's measured crossing is above 2.134 ticks (COST LINE UNDERSTATES), but the line still books (its gross is about 8× its cost) |
| 3 | L4's measured crossing is at or below 1.514 ticks (COST LINE HOLDS); 18:05 and 10:00 are not event clocks |
| 4 | the full-size spread in ticks is narrower than the micro's on the overlap years |

## 4. Seals

- **Only 2016-01-01 → 2023-12-31 quotes are read.** The purchase asserts it per window, and the script asserts it
  again on every record.
- **The trades come from D775's and D778's in-sample frames** (the frozen runners' own loaders, sealed at 2023-12-31).

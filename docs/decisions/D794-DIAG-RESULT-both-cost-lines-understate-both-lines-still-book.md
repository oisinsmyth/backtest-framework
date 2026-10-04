# D794 DIAG RESULT — both cost lines understate the crossing at their own fills, and both lines still make money: D776 by \$0.13 a trade (immaterial), base L4 by \$1.24 (its 18:05 reopen is wide)

*2026-10-04.*
- *Pre-registration: [D794](D794-DIAG-PRE-REG-what-the-cpi-fade-and-l4-pay-to-trade.md) (f14b71f8).*
- *Runner: `scripts/diag_d794_fill_cost.py`. Output: `data/diag_d794_fill_cost.json`.*
- *Quotes: 3,406 windows of `tbbo` and `bbo-1s`, in-sample only, \$24.89 (`data/fill_cost_quotes_manifest.csv`; the files
  are in `data/raw/databento/fill_cost_2016_2023/`, PAID, do not delete).*

## 1. The readings

| line | micro, trades | assumed crossing (round trip) | **measured crossing, mean** (p50 / p90) | cost line: assumed → measured | mean net, these trades: assumed → measured | breakeven crossing | **reading** |
|---|---|---:|---:|---:|---:|---:|---|
| D776, the CPI/jobs-report fade | MNQ, 108 (2019-05 → 2023) | 2.134 ticks | **2.394** (2.25 / 3.5) | \$4.067 → **\$4.197** | \$48.42 → **\$48.29** | 99 ticks | **COST LINE UNDERSTATES** |
| D781, base L4 | M2K, 218 of 232 | 1.514 ticks | **3.984** (3.0 / 6.5) | \$3.757 → **\$4.992** | \$13.51 → **\$12.28** | 28.5 ticks | **COST LINE UNDERSTATES** |

**Neither reads THE LINE DOES NOT BOOK.** No freeze, gate or record changes.

**Each line's frozen in-sample answer is untouched:** D776 \$30.81 at \$4.07; L4 \$12.08 at \$3.76. The table's means
are on the micro era only (from 2019-05), where both lines' gross is higher.

## 2. The legs (ticks; MNQ and M2K tick = \$0.50)

| | entry spread, mean (p50 / p90) | exit spread, mean (p50 / p90) | realised half-spread, entry / exit (tbbo, median per fill, then mean) |
|---|---|---|---|
| D776 MNQ, 08:35:00 / 11:01:00 | **2.89** (3 / 5) | 1.90 (2 / 3) | 1.31 / 0.70 → **2.01 round trip** |
| D776 NQ reference, 186 | 2.85 (2 / 6) | 1.69 (2 / 3) | 1.20 / 0.69 |
| L4 M2K, 18:05:00 / 10:00:00 | **4.89** (3 / 7) | 3.08 (2 / 6) | 1.86 (100 fills) / 1.72 → **3.59 round trip** |
| L4 RTY reference, 280 | 3.73 (3 / 6) | 2.34 (2 / 4) | 1.36 (120) / 0.90 |

**D776.**
- **The cost is at the entry.** Four minutes after the print the MNQ spread is 2.9 ticks on average and one tick only
  11% of the time. By 11:00 it is back to 1.9.
- The prints a marketable order would have hit (tbbo) cost less than the quoted crossing: 2.01 ticks against 2.39.
  Takers trade inside the quoted spread when the book is moving.
- CPI (2.36) and the jobs report (2.43) are alike. 2022 is the widest year (2.73).
- **The difference from the cost line is \$0.13 a trade against a \$52.49 gross.**

**L4.**
- **The cost is the 18:05 reopen.** M2K's spread averages 4.9 ticks there and is one tick 6% of the time.
- The 10:00 exit is wider than expected for the day session too (3.1 ticks, p50 2), on a contract that is thin.
- **The widest fill is the Sunday reopen of 2020-03-15,** the evening of the Fed's emergency cut: a 190-tick (19-point)
  spread, a crossing of 100 ticks. That trade grossed +\$499 at the bar close.
  - Without it, the mean crossing is **3.54 ticks** and the cost line **\$4.77** (reported beside; the declared mean
    keeps it).
  - March 2020 holds the next four widest entries.
- 2020 is the widest year (5.07); 2019 is the narrowest (2.40).

## 3. The predictions

| # | prediction | outcome |
|---|---|---|
| 1 | D776's entry spread is wider than its exit spread | **held** (2.89 against 1.90) |
| 2 | D776 reads COST LINE UNDERSTATES but still books | **held** (2.39 against 2.13; breakeven 99 ticks) |
| 3 | L4 reads COST LINE HOLDS (18:05 and 10:00 are not event clocks) | **failed**: 3.98 against 1.51; the reopen is wide and the micro is thin |
| 4 | the full-size spread in ticks is narrower than the micro's on the overlap years | **split**: L4 yes (RTY 3.17 against M2K 4.04, n 206, ρ 0.72); D776 no (NQ 2.88 against MNQ 2.39, n 108, ρ 0.62) |

## 4. What it means for the frozen lines

**D776.** The measured cost moves its net by 0.3%. Nothing to do.

**L4 (slot 10), the components ledger's #8:**
- The measured cost is \$1.24 a trade more than its frozen line, about 9% of its micro-era net. Its vault gate is read
  at its frozen cost, as declared.
- **A vault PASS by a thin margin would not survive real fills.** On its in-sample base book (net t 1.88 at \$3.76),
  a \$1.24 higher cost lowers the mean net from \$12.08 to about \$10.84, and the t in proportion, to about 1.69.
- D792's assembled book carries L4 at one micro, so the same gap applies there.

**The pre-registered consequence of COST LINE UNDERSTATES:** the forward ledgers report the measured cost beside the
frozen one, **on the principal's word**. Nothing has been changed.

## 5. Deviations and corrections, disclosed

1. **The clock control was not computed.** The pre-registration named the same clock on non-trade days, from the
   full-size reference. The purchase covered trade days only. A quote for those windows is a free call if wanted.
2. **A date bug, found and fixed before this result.**
   - The window rule dated L4's entry evening to Friday for trades exiting on a Monday, when Globex reopens Sunday at
     18:00.
   - The first purchase therefore bought 91 empty Friday-evening windows (43 M2K, 48 RTY; each schema, \$0), and the
     first analysis run read those entries as missing.
   - The rule was corrected in `probe_fill_cost_quotes.py` and the runner. The Sunday windows were bought (182 files,
     \$0.15), and the analysis was re-run; this result is the re-run.
   - The first run's figures for L4 (crossing 3.40, cost \$4.70) excluded the Sunday reopens, which are wider.
3. **14 of 232 M2K entries have no quote within 5 s of 18:05** (stale or empty book) and are excluded. A book with no
   quote is a thin one, so the measured mean is, if anything, low.
4. **Five degraded days** carry a Databento data-quality flag: 2019-03-26, 2020-02-27, 2020-02-28, 2020-06-30 and
   2020-07-01. They are kept.

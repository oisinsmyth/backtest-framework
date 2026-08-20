# D161 — The resampling contract: exact OHLCV on 00:00-UTC buckets, with a day-level drop policy that makes equal window counts a theorem

**Status:** Committed
**Date:** 2026-08-19
**Category:** Data layer
**Source:** Cost-frequency frontier session

## Decision

`research.breakout_intraday.resample` aggregates 1h bars into `target_minutes` buckets:

    open   = first constituent open      high  = max constituent high
    low    = min constituent low         close = last constituent close
    volume = sum of constituent volumes

Buckets are keyed on `(UTC date, minute-of-day // target_minutes)`, so they anchor to
00:00 UTC whenever `target_minutes` divides 1440 — which `Frequency.__post_init__`
enforces rather than assumes, and which every bucket's first timestamp is checked against.
A bucket that does not receive its full complement of source bars **raises**; it never
emits a bar of the wrong duration wearing the right timestamp.

The drop policy for provider gaps is **day-level and shared across frequencies**:

> A UTC day that the provider does not serve in full is dropped at EVERY frequency.

Every frequency then holds exactly `complete_days × 1440/minutes` bars, so — with the
walk-forward sizes scaled by the same `bars_per_day` (D162) — the window count
`floor((days − 252 − 63)/63) + 1` does not depend on the frequency at all. `window_count`
takes no frequency argument, and `run_frontier` asserts the equality against every single
run regardless.

**The 1h → 1d resample does NOT reconcile with the committed daily fixture, and the
discrepancy is reported as a finding rather than absorbed into a tolerance.**

## Rationale

**Why the drop policy is day-level and not bucket-level.** The provider skips the odd
hour: 5 short days for BTC and 6 for ETH out of 729. Dropping only the incomplete bucket
would leave each frequency with a *different* calendar — 1h would keep 23 of a day's
hours, 6h would lose one 6-hour bucket, 1d would lose the whole day — and the study would
then be comparing spans as much as frequencies. Dropping the day everywhere costs 0.7% of
the sample and buys the one property the whole design rests on.

It also makes the incomplete-bucket guard unreachable in the study, which is the point: a
silently-short bar becomes impossible rather than merely unlikely (Pillar 1). The guard is
still tested directly, by handing it a day it was not allowed to reject.

**What the reconciliation found.** Over the 494–495 overlapping days:

- **open and close** differ by a median of about 2 basis points with **no sign bias**
  (roughly 50% either way) — the signature of two independent aggregations of one market.
- **high and low are one-sided almost totally.** The resampled high sits at or below the
  provider's own daily high on 99.8% of days; the resampled low at or above its daily low
  on about 90%. Mean daily range from resampled hourly bars is 3.37% against the
  provider's 3.44% on BTC (5.37% against 5.50% on ETH), and the resampled range is
  narrower on 99% of days.

**yfinance's daily crypto bar is not the aggregate of its own hourly bars.** The hourly
feed does not contain the day's true extremes, so a correctly-resampled daily bar can only
ever be an inner bound on the true range. That is a provider fact and it is recorded as
one — including its direction of bias on this study, which points the wrong way: the
breakout rule triggers on `max(high)` and exits on `min(low)`, so understated highs lower
the entry level and overstated lows raise the exit level, and both produce *more* trading
than the provider's own daily bars would. The 1d rung is therefore an anchor for the
ladder above it, never a reproduction of `BREAKOUT_RESULTS.md`, and the report says so.

**A test pins the negative.** `test_the_1h_to_1d_resample_does_not_reconcile_with_the_
provider_daily_fixture` asserts that closes agree exactly on fewer than 20% of days and
that the high/low bias is present. If the two ever start reconciling, the reconciliation
section of the report is wrong and must be rewritten — which is precisely what a test is
for. A tolerance quietly widened until the comparison passed would have hidden a real
property of the data behind a number nobody would ever look at again.

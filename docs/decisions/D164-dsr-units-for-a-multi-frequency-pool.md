# D164 — For a multi-frequency trial pool, D98's shared period is the CALENDAR DAY, not the bar

**Status:** Committed
**Date:** 2026-08-19
**Category:** Validation & research integrity
**Source:** Cost-frequency frontier session

## Decision

The cost-frequency frontier computes a DSR per (symbol, cost tier) whose pool is every
(design × frequency) configuration at that cell. Before the DSR is computed, **every
cell's out-of-sample equity curve is collapsed to end-of-UTC-day NAV**, and the observed
SR, the pooled metric (`sharpe_daily`) and T are all per calendar day.

A configuration whose out-of-sample equity curve is flat — it never traded, so its Sharpe
is ±inf — **raises** rather than being dropped from the pool.

## Rationale

**Why the obvious choice is wrong.** D98's units contract says the logged metric, the
observed SR and T must all be in the same per-period, non-annualised units, and the pairs
and breakout studies satisfied it with per-bar (daily) Sharpes over T bars. That works
because every trial in those pools had the same bar. Here they do not: a 1h bar and a 1d
bar are not the same period, so pooling per-bar Sharpes would mix quantities differing by
a factor of √24 — **exactly the units bug D98 exists to prevent**, inflating SR0 and
driving the DSR toward zero for a reason that has nothing to do with the strategies.

**Why collapsing to the calendar day is the right fix rather than a convenience.** Because
D161 gives every frequency the identical out-of-sample calendar, the day-collapsed curves
all have the same length. One period (the day), one T (441 days here), one unit, for every
member of the pool — the contract satisfied rather than dodged. It is also the unit the
strategy's owner actually experiences: nobody holds a position for "one bar", they hold it
for days.

**Why a flat curve raises instead of being skipped.** `sharpe` returns sign(mean excess) ×
inf on a zero-variance series (D49: a flat series at a positive risk-free rate is
infinitely bad risk-adjusted). Silently dropping such a trial from the pool would shrink N,
which is the precise failure D98's "select on identity fields, never on the presence of a
metric" rule forbids. So it fails loudly and names the offending configuration, and the
study's answer is to widen the span or drop the rung — a stated choice, not an invisible
one.

**What the resulting numbers mean, which is not what they look like.** This pool is
genuinely heterogeneous: a daily trend follower and an hourly one are not near-duplicates
the way twelve neighbouring plateau cells were in `BREAKOUT_RESULTS.md` (D116). A large
V[{SRn}] raises the noise floor SR0 sharply, so this DSR deflates hard — 0.0012 to 0.71
across the eight (symbol, tier) cells, all far below 0.95. That is the statistic behaving
correctly on the multiplicity it was given. It is also **not the interesting output of this
study**, which selected no configuration and tuned no parameter: the ladder is the result,
not its best cell. Standing reading, inherited from D90/D116: DSR below 0.95 means "no
demonstrated edge"; DSR at or above 0.95 does not mean the reverse.

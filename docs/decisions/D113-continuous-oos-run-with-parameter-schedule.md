# D113 — Walk-forward as one continuous OOS run with a parameter schedule, not chained windows

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Breakout study session

## Decision

Each (symbol, variant, cost tier) in the breakout study is **one continuous backtest** over
the union of the walk-forward test windows, not one backtest per window with capital
chained across them (the pattern `research/pairs_study.py` uses).

The walk-forward structure still defines the study:

- the out-of-sample span starts exactly where window 0's **training** slice ends, so no OOS
  bar is ever inside any training slice;
- per-window returns are sliced out of the continuous stream for per-window trial rows and
  per-window Sharpes;
- anything **fitted** is fitted on a training slice only and applied to that window's test
  bars through a parameter **schedule** — `ScheduledBreakout` holds
  `[(start_index, strategy_config), …]` in absolute run-series indices, swaps configuration
  at window boundaries, and carries the open position across the swap.

The warm-up prefix is exactly `strategy.warm_up_bars()` bars, chosen so the strategy's own
warm-up guard keeps it flat for the entire prefix. `run_variant` **raises** if any fill
lands inside the prefix, rather than trusting the arithmetic.

## Rationale

Chained windows are cheap for a mean-reverting strategy holding for days. For a trend
follower holding for weeks-to-months they are not: every window boundary would force the
book flat, return the position to cash **with no exit cost**, and then require a brand-new
breakout before the trend could be re-entered. On a study whose entire question is whether
tens of basis points of fees matter, an artifact worth several percent a year — in an
unknown direction — is disqualifying.

The parameter schedule is what makes it possible to keep walk-forward's actual guarantee
(fit only on training data) without the seam. It is not a weakening: parameters change at
exactly the same bars they would in a chained design, on exactly the same training
information. What changes is that the *position* is allowed to survive the boundary, the
way a real book would.

The warm-up-prefix rule is the other half. Setting the prefix length equal to the
strategy's own warm-up requirement means the strategy is provably standing aside for all of
it — so, unlike the pairs study's fixed-`lookback` prefix, there is no window in which
prefix trading could contribute in-sample P&L to the reported curve. The runtime assertion
exists because "provably" should be checked, not asserted.

**Consequence for comparability:** the breakout study's stitched curves are not
methodologically identical to the pairs studies', and the two are not directly comparable
on that axis. That is the correct trade — the pairs artifacts are history and are not
rewritten (D105's rule), and the difference is documented here and in the report rather
than smoothed over.

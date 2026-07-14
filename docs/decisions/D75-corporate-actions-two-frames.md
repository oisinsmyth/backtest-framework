# D75 — Corporate actions: two price frames, event-flow brick slot, split scaling, naive timestamps

**Status:** Committed
**Date:** 2026-07-14
**Category:** Data layer
**Source:** Implementation session (Step 7)

## Decision

**Empirical finding that reshaped the design** (verified on XOP's 2020-03-30 1-for-4
reverse split in our own fixture): yfinance's `auto_adjust=False` data is NOT
as-traded raw — prices *and* dividend amounts arrive **already split-adjusted**
(close continuous 32.12 → 32.01 across the ex-date where the true traded price was
~$8.03; the dividend series is smooth 0.40/0.38/0.311 where as-declared amounts would
show a 4× discontinuity). So the provider frame IS the correct signal series as-is,
and the true frame is *reconstructed*:

- `as_traded_from_adjusted(bars, splits)`: true(t) = adjusted(t) × Π(ratio of splits
  with ex-date > t). Execution — fills, commissions, impact, carry — uses this frame
  (D6's "fills/commissions from raw prices"). The pre-split commission gate shows why:
  the same $32,120 order is 4,000 real shares at $8.03, not 1,000 phantom shares at
  $32.12 — a 4× per-share commission difference.
- `as_declared_dividends(dividends, splits)`: same transform, derived from cash-flow
  invariance (true_qty × true_div ≡ adj_qty × adj_div).
- `split_adjusted()` (the inverse direction) is kept for true-frame sources.

**Engine wiring**: `EventFlowBrick` protocol + `CostStack.event_flow_bricks` (4th
slot) — signed cash on ex-dates in `(prev, curr]`, longs credited / shorts debited
(`DividendFlow`). **Not scaled by the D8 sweep**: a dividend is an economic transfer,
not a friction — so the 0× baseline is "zero frictions, flows retained", not an empty
stack. `run_backtest` gains `splits_by_instrument` (positions — broker and virtual
books — scale by the ratio on ex-dates, before the D67 snapshot step so NAV marks
post-split shares at post-split prices) and `view_bars_by_instrument` (strategies see
the continuous adjusted frame; a view series missing an aligned timestamp is a loud
error, never a silent raw-bar substitution).

**Timestamps are normalized to naive exchange-local wall time at the data boundary**:
daily-bar identity is the exchange-local date, and D33's calendar-day carry must not
become DST-sensitive (a Fri→Mon weekend is exactly 3.0 days of borrow, not 71/73
UTC-hours depending on the season).

## Rationale

The original plan assumed `auto_adjust=False` returned as-traded prices and had the
adjustment running in the opposite direction; the data said otherwise, and the data
won. Reading the actual frame out of the fixture (rather than trusting provider
documentation or memory — my recalled split date was also wrong, June vs the actual
2020-03-30) is the anti-self-deception pillar applied to one's own assumptions. The
two-frame separation makes D6's sentence literal, and the sigma double-adjustment bug
it exposed (0.038 vs the correct 0.027 — a fabricated −139% "return" on the split
date) would have silently mis-calibrated the impact model forever if the frames had
stayed implicit.

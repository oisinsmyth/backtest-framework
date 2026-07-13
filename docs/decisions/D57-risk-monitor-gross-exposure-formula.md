# D57 — RiskMonitor's exposure formula and simulate-then-check pre-trade design

**Status:** Committed
**Date:** 2026-07-13
**Category:** Portfolio layer
**Source:** Implementation session (Step 4)

## Decision

`gross_exposure(positions, prices, instruments)` (`engine/risk.py`) is the sum of
**absolute** notional across every position — a long and a short of equal size add
their exposures rather than netting to zero. `RiskMonitor.pretrade_check()` doesn't
duplicate the limit logic: it simulates the position a proposed order would produce
(`current + delta`) and calls the exact same exposure calculation `evaluate()` uses,
just without a `bar_index`.

## Rationale

D30 says risk checks should run "per-bar at portfolio level" and names gross exposure as
the example limit, but doesn't write out the formula. Summing absolute values rather
than netting longs against shorts was chosen because that's what "gross exposure" means
in the pairs-trading context this framework exists for — D5's own rationale states
"market-neutral pairs run ~200% gross exposure," which is only a meaningful number if a
$100 long + $100 short position counts as $200 of exposure, not $0. Netting would make
the limit meaningless for exactly the strategy shape (D22, the pairs study) the
framework is being built for.

Reusing one exposure function for both `evaluate()` (per-bar, no order involved) and
`pretrade_check()` (simulate-then-check) rather than writing separate logic for each
call site means the two can't silently drift apart — a future change to what counts as
"exposure" (e.g. adding margin offsets for genuinely hedged pairs) only has one place to
change, and both the pre-trade gate and the continuous per-bar monitor stay consistent
by construction rather than by remembering to update both.

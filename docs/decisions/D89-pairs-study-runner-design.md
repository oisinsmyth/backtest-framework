# D89 — Study runner design: one multi-strategy run per window, warm-up prefix, chaining, research boundary

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Implementation session (Phase G kickoff)

## Decision

`research/pairs_study.py` — a new `research/` package explicitly labeled as Phase G
study code, keeping the frozen framework surface distinct (the timetable freezes the
framework at Phase G except bug fixes; study glue versions per study, not per
framework release).

- **One multi-strategy `run_backtest` per (window, multiplier)**: the top-N selected
  pairs run as N `ZScorePairsStrategy` instances sharing a single portfolio —
  `ConstantSplitAllocator` splits capital, and D27's netting handles legs shared
  across pairs (two pairs long the same ETF net internally instead of paying costs
  twice). No new engine machinery: this is the Step 3/4 architecture doing precisely
  what it was designed for.
- **Warm-up prefix**: each window's run receives the last `lookback` TRAIN bars
  prepended to its test bars. The strategy's own warm-up guard keeps it flat through
  the prefix (structurally: fewer than lookback+1 visible bars → zero weights), so
  the first possible trade is the first true test bar. Backward-looking data only —
  no leak — and it eliminates the alternative's flaw (a cold OOS start wastes half
  of each 63-bar window warming up).
- **Window chaining**: window *i*'s starting cash = window *i−1*'s final NAV at the
  same multiplier. The stitched curve compounds like one continuously-run account;
  the invariant "stitched returns compound starting cash to final NAV exactly" is
  the headline test.
- Frames per D75 throughout: selection and views on the provider (split-adjusted)
  frame; execution/costs/NAV on reconstructed as-traded prices with split-scaled
  positions and declared-frame dividend flows.

## Rationale

Every alternative to the multi-strategy design (running pairs separately and summing
curves) double-counts costs on shared legs and can't represent the real capital
constraint of one account. The warm-up prefix and chaining choices both follow from
the same principle: the stitched OOS curve should be something an account could
actually have experienced — anything else quietly flatters or degrades the result in
ways a reviewer would have to reverse-engineer.

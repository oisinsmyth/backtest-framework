# D103 — Fill timing: next-bar-open mode alongside the same-bar-close convention (audit F3)

**Status:** Committed
**Date:** 2026-07-14
**Category:** Execution / fill logic
**Source:** Audit remediation session (AUDIT_REPORT.md finding F3)

## Decision

`run_backtest` gains `fill_timing: "close" | "next_open"` (default `"close"`,
byte-preserving every baseline), threaded through `StudyConfig.fill_timing` and
hashed with every trial.

- **"close"** — the historical convention: orders decided at bar *t* fill at bar
  *t*'s own close. Deliberately matched to vectorbt in the D79 reconciliation, so
  it stays the reference mode; but it is optimistic for mean reversion, because
  the entry always catches exactly the close that triggered the signal.
- **"next_open"** — decisions at bar *t* become pending orders that fill at bar
  *t+1*'s OPEN: the strategy never trades at a price its signal has seen. Stated
  semantics, each tested: fills precede the bar's signal step (sizing sees
  updated books); orders decided on the final bar never fill; pending order
  quantities scale with splits in the gap (they were sized in pre-split share
  terms); carry still accrues close-to-close on positions held at the previous
  close — fills land at the open, one instant into the gap, a stated
  approximation rather than intra-gap carry segmentation; the D101 pre-trade
  gate evaluates at decision time against decision-bar closes.

Verified by a hand-computed golden scenario (pending → open fill → NAV-driven
re-size → unfilled final exit) and property invariants: every next_open fill
lands at its bar's open, never on the first bar, and the zero-cost shadow
accountant generalizes to `ΔNAV = position·Δclose + filled_today·(close − open)`.

## Rationale

The audit's F3: all five published studies inherit the same-bar-close
convention, and v2's "+19.03% gross edge at 0×" partially rests on it, with no
sensitivity mode anywhere in the codebase. D9/D11's fill-assumption menu was
never built (nothing to rename, nothing to compare) — this is the first genuine
second fill assumption, and it is the conservative one: for a z-score entry the
next open is the first price a real order could plausibly receive. The
convention-sensitivity study (D105) runs the v2 configuration under both modes
and publishes the delta as its own artifact, per the house one-variable rule —
the published artifacts are history, not something to rewrite.

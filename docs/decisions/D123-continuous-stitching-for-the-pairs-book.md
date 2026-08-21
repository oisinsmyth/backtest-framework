# D123 — The pairs study runs continuously too, and the chained seam is priced rather than argued about

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Crypto pairs study session

## Decision

Each (variant, cost tier) in the BTC/ETH pairs study is **one continuous out-of-sample
backtest** over the union of the walk-forward test windows — the breakout study's pattern
(D113), not `research/pairs_study.py`'s chained windows (D89).

The walk-forward structure still defines the study: the OOS span starts exactly where
window 0's **training** slice ends, per-window returns are sliced out of the continuous
stream for per-window trial rows and per-window Sharpes, and the training slices are what
the cointegration diagnostic (D125) is computed on. Nothing in this study is fitted, so —
unlike D113's `ScheduledBreakout` — no parameter schedule is needed: each variant is one
fixed configuration across the whole span.

The warm-up prefix is exactly `lookback` bars, chosen so `ZScorePairsStrategy`'s own guard
(fewer than `lookback + 1` visible bars → flat) keeps it provably flat throughout.
`run_variant` **raises** if any fill lands in the prefix rather than trusting the
arithmetic — the same rule and the same runtime assertion as D113.

**And the alternative is run anyway.** `stitch="chained"` reproduces the D89 pattern
(one `run_backtest` per window, capital chained window to window, a fresh strategy
instance each time) and ships as a `convention`-group sensitivity row in the artifact. On
the reference tier it returns −96.7% against the continuous run's −98.0%, with 52 round
trips against 40.

## Rationale

D113 chose continuous for a trend follower and explicitly said the chained seam is *cheap*
for mean reversion, whose trades last days. That reasoning is sound and it is not the whole
story for this strategy, because a pairs book crossing a window boundary loses two things,
not one:

1. **A free liquidation.** The window ends with the book marked at the close; the next
   window starts in cash. The position teleports out with no exit fee, no borrow, and no
   margin interest. Over 43 boundaries with the book in a position roughly half the time,
   that is on the order of twenty round-trip exits the strategy never pays for — on a study
   whose entire cost table is the point.

2. **The strategy's own hysteresis state.** `ZScorePairsStrategy._side` is per-run mutable
   state (D69), and it is the *mechanism* of the hysteresis band: between `exit_z` and
   `entry_z` the strategy holds whatever side it already had. A fresh instance per window
   starts at `_side = 0`, so every boundary silently converts "hold through the band" into
   "stand aside until |z| clears `entry_z` again". That is a **signal** artifact, not a
   cost artifact, and it has no analogue in the breakout study, whose `ScheduledBreakout`
   deliberately copies `_in_position` across a parameter swap. It shows up directly in the
   measured numbers: the chained run takes *more* round trips (52 vs 40) at *lower*
   exposure (45.5% vs 51.7%) — more entries, less time held, which is exactly what losing
   the band produces.

Neither effect is small, and their signs point in opposite directions (the free
liquidations flatter, the lost hysteresis is ambiguous), which is precisely why the
sensitivity row exists rather than a paragraph asserting the net is negligible. D105's
rule applied to a new axis: measure the convention, publish the delta.

**Comparability consequence, stated in both directions.** These curves are
methodologically identical to `BREAKOUT_RESULTS.md`'s and **not** identical to
`docs/results/pairs_study_v1/v2/v3.md`'s. The published pairs artifacts are history and
are not rewritten (D105's rule). A reader comparing this study to those should read the
`stitch_chained` row first; a reader comparing it to the breakout study should not need
to adjust for stitching at all — but must still account for the fact that the two studies
do not share a sample (D124's alignment note).

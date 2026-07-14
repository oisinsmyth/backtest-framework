# D96 — Gross exposure study: leg_weight as the single variable, the margin threshold as the mechanism

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Implementation session (gross exposure study)

## Decision

`research/gross_sweep.py` runs one D95 capacity study per `leg_weight` — thin
composition, no new machinery. The choices that carry it:

1. **leg_weight is the single variable.** Book gross when all pairs are in trade
   is 2·lw·NAV. The per-component scaling is stated up front so the measurement
   has a prediction to check: edge ≈ ∝ lw; spread/borrow ∝ lw; **margin
   interest = rate × max(2·lw − 1, 0) — a piecewise THRESHOLD that collapses at
   gross ≤ NAV instead of scaling down**; impact drag ∝ lw^1.5 (falls faster
   than the edge); the $1/order commission minimums constant (lower gross makes
   small accounts strictly worse).
2. **Grid bounds are justified, not defaulted.** lw ∈ {0.25, 0.5, 0.75, 1.0}
   brackets the threshold (below / at / above / the D95 baseline); AUM ∈
   {$100k … $10M} because the capacity analysis already showed both tails and
   lower gross worsens the small end a fortiori. The lw = 1.0 column reproduces
   the capacity artifact's rows — a built-in cross-check.
3. **`trial_prefix` on `run_capacity_study`** (default "capacity" preserves the
   D95 artifact's trial ids byte-for-byte) so all cells share one registry
   without collisions.
4. **Per-lw gross references** (0× plain-stack sanity runs at $100M) measure how
   the edge actually scales with lw — compounding and rounding keep it from
   exactly ∝ lw — giving each column an honest numerator.
5. **DSR-honesty rule for razor-thin positives**: if any cell clears, it is
   reported as a configuration with positive expected net that is statistically
   indistinguishable from zero under the program's multiplicity (D90, now five
   studies) — never as a demonstrated edge.

An empirical detail discovered by the tests and kept in the artifact: exactly AT
the threshold (lw = 0.5), whole-share rounding and NAV drift nudge gross past
NAV on scattered bars, so margin drag is trace-positive rather than exactly
zero. It still collapses by orders of magnitude versus lw = 1.0 — the threshold
claim survives contact with the simulator's honesty about rounding; "exactly
zero" needs gross strictly below NAV.

## Rationale

D95 closed the AUM axis: no account size clears at 200% gross, and the binding
constraint is the cost floor, half of which is margin interest. The floor's
nonlinearity is the one remaining untested lever inside the strategy's own
configuration — first-order arithmetic at the $300k optimum puts lw = 0.5 at
edge ≈ +1.0%/yr against drag ≈ 0.8–1.1%/yr, sign unknown. A sign-unknown
first-order forecast is exactly what the framework exists to measure rather
than argue about.

**The measurement landed on the positive side of the razor — with a sharper
negative underneath.** Five low-gross cells clear absolute real costs (best:
lw 0.5 at $300k, +0.12%/yr net vs +1.03%/yr gross); the margin matrix confirms
the threshold collapse (0.866%/yr at lw 1 → exactly 0 below the threshold). But
against the study's 4% risk-free rate the best cell's stitched Sharpe is −1.61:
the strategy underperforms T-bills by ≈3.9%/yr. The refined program headline is
therefore two-sided and stronger than "doesn't clear costs": **at low gross the
edge can just pay for its own implementation, but it cannot pay for the capital
it occupies.** One modeling honesty note recorded with it: the simulator
credits no interest on idle cash — a gross ≤ 100% book is mostly idle cash, so
real-account absolute returns would sit closer to rf, but that return belongs
to the risk-free rate, not the strategy.

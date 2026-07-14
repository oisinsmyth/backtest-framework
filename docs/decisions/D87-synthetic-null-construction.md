# D87 — Synthetic nulls: random-walk spread, not OU; test calibration; block-paths exposure

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Implementation session (Step 12)

## Decision

`validation/synthetic.py::cointegrated_looking_pair`: ln A is a common random walk;
ln B = ln A − s where **s is itself a random walk** with small steps. The pair
visually tracks (the "cointegrated-looking" part), but the spread is a martingale,
so any timing rule has expected profit exactly zero — **an Ornstein-Uhlenbeck
(genuinely mean-reverting) spread would be the WRONG null**, because a
mean-reversion strategy has real gross edge against it; the null must look like the
opportunity while containing none of it. The D23 gate runs the z-score strategy at
zero cost across 40 seeded null pairs: mean P&L ≈ 0 within 2.5 standard errors plus
an absolute bound, with a non-vacuousness assertion (the strategy really traded).
Per the gate: if this profits, stop everything.

**Test calibration, recorded because the first version tripped it:** at the
strategy's default ±100%/leg, per-pair OOS return volatility on independent
1.5%/day random walks is ~20%, making any absolute bound on a 20-sample mean
meaningless — the initial run "failed" with a −4.3% mean that was ~1σ of pure noise.
The gates run at leg_weight 0.25 (50% gross) with 30 samples so the ≈0 claim has
teeth. The zero-edge property is leverage-invariant; this is test calibration, not
result shopping — the same distinction D74 drew for validator thresholds.

Also: `analytics/monte_carlo.py` now exposes `block_bootstrap_paths` (the generator
`block_bootstrap_percentiles` always used internally — additive, seeded output
byte-identical, confirmed by the existing same-seed test). The shuffle-vs-block
U-gate uses it: on an AR(1) series with ρ=0.6, shuffled paths' lag-1 autocorrelation
collapses below 0.05 while block-bootstrap paths retain >0.35 — the quantified
reason D23 demoted the returns-shuffle.

## Rationale

A null that secretly contains the effect under test validates nothing; a null that
lacks the visual signature tests the wrong hypothesis. Random-walk-spread is the
unique construction that keeps the signature and removes the effect. Writing down
the calibration episode matters for the same reason D74's was written down: a
"failing" honesty gate whose failure is a mis-calibrated bound trains its operator
to loosen bounds reflexively — the fix must be reasoned in the open, with the
leverage-invariance argument that makes it calibration rather than convenience.

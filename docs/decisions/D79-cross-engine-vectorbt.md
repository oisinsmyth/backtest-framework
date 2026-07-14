# D79 — Cross-engine reconciliation via vectorbt target-percent; precomputed-weights design

**Status:** Committed
**Date:** 2026-07-14
**Category:** Testing
**Source:** Implementation session (Step 8)

## Decision

D41's reference engine is **vectorbt 1.1.0** (`Portfolio.from_orders` with
`size_type='targetpercent'`), chosen because its per-bar target-percent re-sizing is
architecturally the same convention as this engine's weight × current-NAV sizing
(D27/D61) — making penny-exact agreement *achievable* rather than requiring a
divergence model. backtesting.py was the planned fallback; not needed (vectorbt
installed and ran cleanly against Python 3.12 / pandas 3.0.3).

**Design: both engines consume the identical precomputed MA(10)/MA(30) target-weight
schedule** — signal code is excluded from the comparison entirely, so any divergence
is a simulator disagreement. Conventions matched deliberately (fractional shares both
sides, proportional fees only, fills at signal-bar close, target weight 0.6): the
full table, the result, and its caveats live in
**`docs/verification/cross_engine_reconciliation.md`**.

**Result: penny-exact.** 2,515 bars, 1,370 trades in each engine (every re-size
decision agreed), final values identical to the micro-cent, max curve divergence
1.3e-12 relative — float noise. The divergence table is empty.

**A real convention difference found and documented rather than papered over:** at
~full investment (target weight ≈ 1.0), vectorbt reserves fees out of the purchase
while this engine charges fees to cash after sizing. The comparison deliberately runs
at 0.6, below the boundary; the difference is now a known fact for any future
full-investment work.

The test (`tests/integration/test_cross_engine.py`) lives in the normal offline suite
— D41's "re-run on every simulator-touching change" is automatic, not a policy.

## Rationale

Choosing a reference engine with a *different* re-sizing philosophy (hold-until-exit)
would have manufactured divergence that reflects convention, not correctness, and the
reconciliation doc would have become an essay in explaining away differences. Matching
conventions first and then demanding exact agreement is the stronger test: with every
knob equalized, any residual gap would have been a genuine bug in one engine or the
other. There wasn't one.

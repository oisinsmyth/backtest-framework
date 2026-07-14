# D68 — Cost sweep harness: per-brick scaling wrappers, strategy factories, minimal markdown tearsheet

**Status:** Committed
**Date:** 2026-07-14
**Category:** Cost architecture
**Source:** Implementation session (Step 6)

## Decision

- `costs.scaling.scaled_cost_stack(stack, m)` wraps every brick in all three slots
  with a wrapper multiplying that brick's output by `m` — structure preserved, so a
  scaled stack keeps D54's additive/order-invariant guarantees and `0×` is provably
  equivalent to an empty `CostStack()` (asserted through full backtests, synthetic
  and real).
- `engine.sweep.run_cost_sweep` takes strategies as a **factory** (zero-arg callable
  returning fresh instances), not as instances — strategies may hold per-run state
  (ZScorePairsStrategy's current side, D69), and a reused instance would leak one
  multiplier run's state into the next. The API makes the leak impossible rather
  than warning against it (Pillar 1). A counting-factory test pins one call per
  multiplier.
- The gate's "tearsheet" is satisfied by a minimal markdown sweep table (multiplier,
  final NAV, net P&L, return, max drawdown — plain equity-curve arithmetic only).
  Sharpe/rf (D49), beta (D37), and sample-size-gated tails (D36) are Step 9's
  statistics and are deliberately not imitated here.

## Rationale

Per-brick wrappers over "multiply the summed total" because the per-brick structure
is what makes the 0×-equivalence provable brick-by-brick and keeps a future
per-brick attribution report possible without re-architecting. Factory-not-instance
follows directly from making strategies stateful in the same chunk — the two
decisions arrived together and the API records their interaction. D8's own rationale
("does it survive 2× costs is the single most informative output") is the reason the
sweep exists at all; the harness adds no cleverness beyond running the identical
scenario N times.

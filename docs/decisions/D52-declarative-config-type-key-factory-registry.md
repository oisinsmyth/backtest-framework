# D52 — Declarative config shape: `{"type": ..., ...params}` + a generic FactoryRegistry

**Status:** Committed
**Date:** 2026-07-13
**Category:** Backtest engine
**Source:** Implementation session (Step 2)

## Decision

Every declarative config dict that names a swappable implementation uses the shape
`{"type": "<name>", ...params}`, and is built via a `FactoryRegistry` (one instance per
kind of thing being configured) that maps `type` values to factory functions. A
`SimConfig` is a plain dict of named sub-configs (e.g. `{"carry_model": {...},
"fill_model": {...}}`), validated eagerly against a fixed set of required/allowed
top-level keys before any sub-factory runs.

Implemented now (`src/backtest_framework/config/`) against two pieces of behaviour that
already exist from Step 1 — carry accrual (D33) and stop fills (D10) — specifically to
prove the mechanism in isolation, not to pre-build Step 3's CostStack. `CarryModel` and
`FillModel` in this module are demonstration vehicles and are expected to be absorbed
into the real cost bricks when Step 3 (D1, D2, D12) lands.

## Rationale

D35 says configs must be "plain data (dicts/strings — e.g. `{"cost_model": "ibkr_v1"}`)"
but doesn't specify a schema convention — that gap needed filling to write any code at
all. The `{"type": ..., ...params}` shape was chosen because:

- It generalizes cleanly to D1's CostStack (an ordered list of `{"type": "sqrt_impact",
  ...}`-shaped bricks) and D12's Instrument abstraction, both still to come in Step 3 —
  reusing this pattern there rather than a bespoke one avoids two incompatible config
  dialects living in the same codebase.
- A single generic `FactoryRegistry` class (rather than one bespoke validate-and-build
  function per model type) means the "fail loudly, name the bad key" behaviour required
  by the Step 2 verification gate is written once and inherited everywhere, instead of
  being reimplemented — and possibly forgotten — per model type.
- Keeping `CarryModel`/`FillModel` explicitly out of the CostStack's future namespace
  (and saying so in their docstrings) avoids the Step 2 work quietly becoming an
  unplanned partial implementation of Step 3, which R2's timeboxing exists to prevent.

This is exactly the kind of schema/architecture choice Pillar 5 of `PHILOSOPHY.md` flags
as needing a written decision rather than an implicit default nobody chose on purpose —
in this case because the *next* few config types (Step 3's cost bricks) will either
follow this convention or fork from it, and that's worth being a deliberate choice.

# D55 — Pipeline sizing design: stateless Sizer, capital-by-strategy as an external input

**Status:** Committed
**Date:** 2026-07-13
**Category:** Signals & strategy interface

**Source:** Implementation session (Step 3)

## Decision

`pipeline/sizing.py` implements D27 as plain functions/stateless classes over explicit
dict arguments, not a stateful `Portfolio`/`Book` class:

- `Sizer` holds no per-strategy state; `size_targets(targets, current_positions,
  capital_by_strategy, prices, instruments)` is a pure function of its arguments.
- `capital_by_strategy` is a required input the caller supplies — this module does not
  decide how much capital each strategy gets. That decision belongs to D31's Allocator
  (Step 4's bare-bones constant-split stand-in), which doesn't exist yet.
- Per-strategy virtual books (D46) are plain `dict[(strategy_id, instrument_id), float]`
  position maps, updated by `apply_virtual_orders` — no dedicated `VirtualBook` class.
- Netting (`net_orders`) operates purely on the virtual-order dict already produced by
  `size_targets`; it doesn't need to know about capital, prices, or instruments at all.
- Already-at-target positions produce *no entry* in the virtual-orders dict (not a
  zero-quantity `Order`) — "no churn" falls out of the data shape rather than needing a
  filter step downstream to remember to apply.

## Rationale

D27's own text names the pieces ("a central sizer/allocator converts targets to
orders") but conflates two decisions that D31 (written earlier in the same document)
already separates: capital allocation across strategies is the Allocator's job, weight-
to-quantity conversion within a strategy's allocated capital is the sizer's job. Keeping
`Sizer` ignorant of *how* `capital_by_strategy` was decided — just taking it as an input
— means Step 4 can drop in the real (if still bare-bones) Allocator later without
touching this module at all.

Staying functional (dicts in, dicts out) rather than building a `Portfolio`/`VirtualBook`
class now avoids pre-building Step 4's territory (structural guards, `RiskMonitor`,
`Allocator`) or Step 6+'s full engine — everything Step 3 needs to prove (target weights
produce exact expected orders, no-churn, cross-strategy netting, one sizer driving
multiple strategies unmodified) is expressible as pure functions over plain data, so
that's as far as this step goes. The moment a real engine needs to hold this state
across bars, it can wrap these functions rather than needing them rewritten.

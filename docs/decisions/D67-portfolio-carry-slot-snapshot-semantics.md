# D67 — Portfolio-level carry slot on CostStack; start-of-bar snapshot semantics

**Status:** Committed
**Date:** 2026-07-13
**Category:** Backtest engine
**Source:** Implementation session (Step 5)

## Decision

`CostStack` gains a third slot, `portfolio_carry_bricks` (additive, default empty —
every existing stack and the frozen D53 baseline are untouched, confirmed by
re-running them). Same `CarryCostBrick` interface as the per-leg slot; what differs
is the **caller's contract**: per-leg bricks get each held instrument's own notional
as base (borrow, dividends, funding — D2's carry family), portfolio bricks are
charged once per bar on a base only the engine can compute. For `MarginInterest`
(D5) that base is `max(gross_exposure − NAV, 0)` — the borrowed portion of the book —
reusing the existing `engine.risk.gross_exposure` rather than a second formula that
could drift from the risk monitor's (same one-formula argument as D57).

`run_backtest` takes one **start-of-bar snapshot** (positions, prices, NAV, gross)
*before* deducting any carry, then applies per-leg bricks and portfolio bricks from
that snapshot. Without this, per-leg carry deductions would shrink NAV mid-step and
change the margin base, making the charge depend on brick application order — the
exact ordering-sensitivity `CostStack`'s additive-bricks guarantee (D54) promises
away.

## Rationale

D5 defines margin interest on "(gross exposure − capital)", which no per-leg call can
compute — the engine loop had exactly one carry concept and needed a second. A
separate slot (rather than a fatter `CarryCostBrick` interface carrying portfolio
context into every per-leg brick) keeps the existing bricks and their tests untouched
and makes the semantic difference structural: a brick in the wrong slot gets the
wrong base *visibly at config time*, not through a subtle interface misuse. "Capital"
is interpreted as current NAV, consistent with D61's capital-is-current-NAV choice
for sizing — one meaning of "capital" in the loop, not two.

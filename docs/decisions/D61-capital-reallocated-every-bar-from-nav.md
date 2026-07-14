# D61 — Capital is reallocated every bar from current NAV, not fixed at the start

**Status:** Committed
**Date:** 2026-07-13
**Category:** Portfolio layer
**Source:** Implementation session (post-Phase B, pre-Step 5)

## Decision

In `run_backtest` (`engine/backtest.py`), `Allocator.allocate()` is called every bar
with the portfolio's *current* NAV, not a value fixed at the start of the backtest. A
strategy that's made money is sized against more capital next bar; one that's lost
money gets less.

## Rationale

Neither D31 (the Allocator stand-in) nor D27 (the sizing pipeline) specifies how often
capital gets reallocated — Step 3's test-only harness sidestepped the question
entirely by fixing capital at `starting_cash` for its whole run, which was fine for a
single hardcoded scenario but isn't a real answer for a reusable loop. Reallocating
from current NAV every bar is the more honest default: a backtest that let a
strategy's position size drift away from what its actual current equity could support
would be quietly overstating or understating real deployable capital, which is exactly
the kind of silent-drift bug D33 and D42 exist to prevent in their own domains.

This is a real behavioural choice, not a free refactor — it changes what
`Sizer.desired_quantity` computes on every bar after the first. Verified explicitly
(not assumed) that it still reproduces `test_step3_golden_master_equity_curve`'s exact
numbers; the trace is in `tests/integration/test_backtest_loop.hand.txt`. If a future
strategy's behavior depends on this choice in a way that matters, that's a signal this
decision needs revisiting in writing, not silently working around.

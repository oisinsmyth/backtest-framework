# D53 — "Refactor regression" gate reinterpreted for greenfield conditions

**Status:** Committed
**Date:** 2026-07-13
**Category:** Backtest engine
**Source:** Implementation session (Step 3)

## Decision

`VERIFICATION_SCHEME.md`'s Step 3 gate — "a pre-refactor golden backtest (frozen
snapshot, old cost assumptions expressed as bricks) reproduces its equity curve through
the new architecture" — is reinterpreted as: **since there is no pre-refactor engine in
this project, build one hand-computed golden-master scenario through the new
CostStack/Instrument/pipeline architecture, and treat it as the frozen baseline any
future refactor of these three components must reproduce.**

Implemented as `tests/golden/test_step3_refactor_regression.py` /
`.hand.txt` — one strategy, one instrument, three bars, constant price (so every dollar
of NAV change is attributable to costs alone, which doubles as an independent
cross-check of the bar-by-bar arithmetic).

## Rationale

The verification scheme was written assuming a specific project history — the design
review sessions that produced D1–D49 talk about "the current imperfect version" of the
framework being refactored (R1's own wording), implying a working engine already
existed. This project's actual repository started from the doc suite alone; Step 1 and
Step 2 built pure functions and a registry, not a broker or portfolio. There is
genuinely nothing to reconcile Step 3's new architecture against.

Rather than silently skip this gate (which the "no false affordances" pillar of
`PHILOSOPHY.md` argues against — a checked-off gate that wasn't really met is worse than
an honestly reinterpreted one) or over-correct by building a full production
Portfolio/broker class just to have something to regress against (which would be Step
4+ scope pulled forward, against R2's timebox), the gate is re-scoped to what's actually
achievable and useful right now: establish *a* golden master, so that when Step 5's real
cost bricks replace today's toy ones, or Step 4's engine subsumes today's test-only
`run_mini_backtest` harness, there's a concrete equity curve to check against instead of
vibes. `run_mini_backtest` itself stays confined to the test file — it is explicitly not
promoted to `src/`, so it can't be mistaken for (or accidentally block) the real engine
Step 4 onward will build.

This is the kind of deliberate, visible deviation from a written gate that
`PHILOSOPHY.md`'s "using this document" section asks for: say so explicitly rather than
letting it pass quietly.

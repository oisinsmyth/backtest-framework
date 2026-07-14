# D77 — THE golden master covers the engine as built; BacktestResult gains fills/cash instrumentation

**Status:** Committed
**Date:** 2026-07-14
**Category:** Testing
**Source:** Implementation session (Step 8)

## Decision

THE golden master (`tests/golden/test_the_golden_master.py` + `.hand.txt`) asserts a
five-bar SHORT-side scenario — weekend (3 calendar days of borrow+margin, D33),
dividend ex-date debiting the short (D6's marquee case), ~120% gross so margin
interest has a live and *drifting* base, NAV-driven re-size fills (D61) including one
that triggers IBKR's $1 minimum — every fill, commission, carry accrual, flow, cash
and NAV per bar, line by line, against an independent calculator that never imports
the framework.

**Deliberate scope deviation from the gate's wording (D53 discipline): no
gap-through-stop.** The engine places no stop orders — strategies emit target
weights, filled at close (D27). Gap-through-stop has its own golden gate at unit
level since Step 1 (`test_stop_fill_gap_through`, D10). Wiring stop orders into the
engine solely to satisfy one clause of a gate written before the architecture existed
would be Step-3-grade engine surgery smuggled into a testing step; the engine
integration belongs to whatever future step makes stops an engine feature.

**Instrumentation (additive):** `BacktestResult` gains `fills` (timestamp,
instrument, signed qty, price, trade cost) and `cash_curve` — required for
line-by-line golden assertions and the D40 invariants, and what Step 9's per-strategy
attribution will read. Frozen baselines re-run unchanged.

## Rationale

A golden master that tests a hypothetical engine validates nothing; one that pins the
engine as built catches every future regression in what actually runs. The short side
was chosen because it exercises the maximum number of bricks simultaneously —
long-side coverage is a strict subset of the same code paths plus the (long-credited)
dividend sign, which the D6 gate tests separately.

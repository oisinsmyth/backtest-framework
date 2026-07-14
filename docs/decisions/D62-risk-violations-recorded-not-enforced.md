# D62 — RiskMonitor violations are recorded, not enforced, in run_backtest

**Status:** Committed / Deferred
**Date:** 2026-07-13
**Category:** Portfolio layer
**Source:** Implementation session (post-Phase B, pre-Step 5)

## Decision

`run_backtest` calls `RiskMonitor.evaluate()` every bar when `risk_limits` is given and
appends any `RiskViolation` to `BacktestResult.violations` — but does nothing else. The
trade that caused (or coincided with) the violation still executes; there is no
corrective order and no halt. `tests/integration/test_backtest_loop.py::
test_run_backtest_records_risk_violation_without_halting` asserts this explicitly (the
position still ends up at the size that triggered the violation), so it's a checked
fact, not an implicit gap someone has to discover by reading code.

## Rationale

D30's own text names "corrective orders or halt flags" as what a violation should
produce, so building only detection is a real, visible scope cut, not the finished
behaviour D30 describes — recorded here rather than left for someone to assume
detection implies enforcement. Building actual corrective-order generation or a halt
mechanism needs design work this chunk's scope (unblock Step 5/6) doesn't call for:
what a "corrective order" should look like depends on portfolio-level decisions
(unwind proportionally? unwind the worst offender? halt new entries only?) that have
no validated strategy yet to inform them — the same argument D31 already made for
deferring real allocation logic. Detection-only is enough to prove the wiring is
correct and to make violations visible to whoever inspects a `BacktestResult`;
enforcement is deferred, explicitly, per R3.

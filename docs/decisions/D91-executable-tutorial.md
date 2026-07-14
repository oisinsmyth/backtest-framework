# D91 — The tutorial's code is executed by the test suite, not merely written

**Status:** Committed
**Date:** 2026-07-14
**Category:** Testing
**Source:** Implementation session (documentation)

## Decision

`docs/TUTORIAL.md` is the start-to-output usage guide. Every ```python fence whose
first line is `# runnable` is extracted and executed **verbatim, in document order,
in one shared namespace** by `tests/integration/test_tutorial.py` (with `WORKDIR`
injected as a temp directory). Nine blocks cover the whole pipeline: hello-world
backtest, the real cost stack with automated calibration, a custom strategy against
the `Strategy` protocol, clean→validate→snapshot including a live quarantine
refusal, the cost sweep with monotonicity asserted, trial logging, the analytics
tearsheet including the insufficient-data honesty string, walk-forward selection +
the DSR paper example, and a miniature end-to-end study. Network-dependent snippets
are shown unmarked and reference the scripts that own them.

## Rationale

This repo already established that documentation rots unless a test bites it (the
D82 strategy-label grep, the D84 options-doc section check). A tutorial is the
highest-rot-risk document in any codebase — every API change invalidates it silently
and the damage lands on the newest user, who can't tell a typo from a breaking
change. Executing the examples is the strongest available guarantee: if
`sharpe()` gains an argument or `run_backtest` renames a parameter, CI fails with
the block number and the exception, and the fix is forced to touch the tutorial in
the same commit as the API. The shared-namespace design mirrors how a reader
actually follows a tutorial (each block builds on the last), so what's tested is
what's experienced.

# D50 — Project scaffolding: uv package manager, src-layout, pytest + hypothesis

**Status:** Committed
**Date:** 2026-07-13
**Category:** Tooling
**Source:** Implementation session (Step 1 kickoff)

## Decision

Use `uv` for environment and dependency management, a `src/backtest_framework/` layout
(not flat), and `pytest` + `hypothesis` as the test stack (`hypothesis` covers the P
property/invariant test type from `VERIFICATION_SCHEME.md`). Python `>=3.12`.

## Rationale

None of this was specified anywhere in the original planning docs — they describe *what*
gets tested (U/G/P/I/X per `VERIFICATION_SCHEME.md`) but not the tooling that runs it.
Rather than let that stay an implicit default, it's picked once and recorded:

- `uv` was already installed and available on this machine; it's a single fast tool for
  venv + dependency resolution + lockfile, which keeps the setup story simple.
- src-layout prevents accidentally importing the package from the repo root instead of
  the installed package — a common source of "works on my machine, fails once packaged"
  bugs, and cheap to set up correctly from the start rather than migrate to later.
- `pytest` is the de facto standard and the property-based test type in the verification
  scheme (Step 1's calendar-accrual invariant, and more later) needs `hypothesis`
  specifically — no other library in the ecosystem covers that test type as directly.

This is exactly the kind of decision Pillar 5 of `PHILOSOPHY.md` says should be written
down rather than left as an implicit default that nobody chose on purpose.

# D28 — Regime models obey the same fitting rule as pair selection: fit inside the walk-forward training window only, structurally enforced (regime module receives training data via the same guarded accessor as strategies)

**Status:** Committed
**Date:** 2026-07-07
**Category:** Signals & strategy interface
**Source:** Session 2 — full-framework review

## Decision

Regime models obey the same fitting rule as pair selection: fit inside the walk-forward training window only, structurally enforced (regime module receives training data via the same guarded accessor as strategies).

## Rationale

Regime detection is the easiest overfit vector in the codebase ("works except in high-vol regimes" is usually discovered by looking at when it lost money). If the framework doesn't structurally prevent full-sample regime fitting, the module is a foot-gun.

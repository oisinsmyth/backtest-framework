# D60 — TimestampedBar wraps Bar rather than extending Bar's schema

**Status:** Committed
**Date:** 2026-07-13
**Category:** Data & portfolio layers
**Source:** Implementation session (post-Phase B, pre-Step 5)

## Decision

`data.bars.TimestampedBar` is `(timestamp: datetime, bar: Bar)`, wrapping the existing
`simulator.fills.Bar` unchanged, rather than adding a `timestamp` field directly to
`Bar`.

## Rationale

`Bar` is constructed directly in `simulator/fills.py` (D10's stop-fill logic),
`costs/bricks.py`'s golden tests, and roughly a dozen other call sites across Steps
1–4 — none of which need a timestamp attached; only the engine loop (carry accrual,
D33) and data fetching do. Adding a required field would force every existing call
site to supply a value it has no use for; adding it as optional would create a field
that's silently required in real usage but typed as if it weren't — a small instance
of exactly the "no false affordances" problem D48 warns about. Wrapping instead of
extending means `Bar` stays exactly what Steps 1–4 already tested it to be, and only
the new code that actually needs timestamps (the data source, the engine loop) carries
the extra type.

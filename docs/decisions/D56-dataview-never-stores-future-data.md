# D56 — DataView is constructed holding only visible bars, never given future ones

**Status:** Committed
**Date:** 2026-07-13
**Category:** Backtest engine
**Source:** Implementation session (Step 4)

## Decision

`DataView` (`engine/dataview.py`) does not wrap the full bar series with an index
cursor that gates access. Instead, `build_data_view(all_bars, up_to_index)` — engine-side
code, with legitimate access to the full series — slices it down and constructs a
`DataView` holding *only* `all_bars[0 : up_to_index + 1]`. Bars beyond that index are
never passed to the object at all. Strategy code only ever receives what
`build_data_view` returns, never `all_bars` itself.

## Rationale

D32 asks for something that "physically cannot return bars beyond the current index,"
which is a stronger claim than "hides them behind a leading underscore." Python doesn't
have real private attributes — `view._anything` is one `getattr` away regardless of
naming convention — so an implementation that stores the full series and gates access
via an index check is still just an honour system with extra steps: a bug, a
`vars(view)` walk, or a determined attacker gets the future data anyway, because it's
sitting right there in memory reachable from the object.

Constructing the object with only the safe subset closes that gap structurally rather
than procedurally: there is no future data anywhere in the object's `__dict__`, so no
attribute walk, reflection trick, or "cheating strategy" can produce it — not because
access is denied, but because it was never granted. This is Pillar 1 of `PHILOSOPHY.md`
("trust is structural, not agreed-upon") applied about as literally as it can be.

The cost is that DataView is immutable and a fresh one is constructed per bar
(`build_data_view` is called by the engine every step) rather than one long-lived object
with a mutable cursor — a small, worthwhile trade for the guarantee. `tests/integration/
test_dataview_lookahead_guard.py` exercises this directly: even deliberately reading the
"private" `_visible_bars` field yields only what was already visible.

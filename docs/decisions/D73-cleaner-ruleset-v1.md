# D73 — Cleaner ruleset clean-v1: drop-and-report, never rewrite; permanence discriminates prints from crashes

**Status:** Committed
**Date:** 2026-07-14
**Category:** Data layer
**Source:** Implementation session (Step 7)

## Decision

`data.cleaner.clean()` (D25) returns `(cleaned, CleaningReport)`; the ruleset id
(`clean-v1`) travels in the report and the snapshot meta. Four rules, all
**drop-and-report — the cleaner never rewrites a price**: non-finite OHLC; low > high
beyond 1e-9 relative tolerance; zero/negative volume; spike-and-revert (|bar return|
> 40% that reverts to within 10% of the pre-spike level by the next bar). A large
move that *sticks* is kept: permanence is the discriminator between a bad print and
a real crash — XOP's genuine −37% day (2020-03-09) survives, a 50%-up-and-back
glitch doesn't.

## Rationale

Fabricating values is D45's sin (forward-filled prices that fills then execute
against); dropping a bar is honest, and the alignment layer already handles the
resulting hole correctly — carry spans the gap (D33/D63), trading skips it. Silent
cleaning makes "strategy result" indistinguishable from "cleaning artifact" (D25's
own words), so every drop is a reported, versioned event attached to the snapshot.
On the real 2015–2024 XLE/XOP fixture, clean-v1 made **zero changes** — reported as
zero, which is itself information about the data source.

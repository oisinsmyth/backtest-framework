# D111 — Volume-confirmation filter NOT built: `Bar` carries no volume, and neither workaround is acceptable

**Status:** Superseded by [D168](D168-volume-rides-inside-the-dataview.md), 2026-08-21
**Date:** 2026-08-18
**Category:** Signals & strategy interface
**Source:** Breakout study session

> **DISPOSITION, 2026-08-21.** This deferral is **closed**. The interface change scoped
> below was built as designed: volume rides inside `DataView` as an aligned,
> optionally-present series constructed sliced exactly as bars are, with three explicitly
> distinguishable states so that "this instrument has no volume" and "somebody forgot to
> wire volume through" are never the same observation. `VolumeConfirmationFilter` exists,
> is registered, and faces the same keep/drop rule as the other filters; feature F2 is
> computable. See [D168](D168-volume-rides-inside-the-dataview.md).
>
> The record below is left exactly as written on 2026-08-18 — it is the reasoning that
> justified NOT faking the filter for three months, and the "what would need to be true"
> section is what the build then followed. Rewriting it to match the outcome would erase
> the more useful half.

## Decision

The breakout study's specified volume-confirmation filter — "trigger bar volume > 1.5× the
20-day average volume" — is **not implemented**, and no `VolumeConfirmationFilter` class
exists to imply otherwise. The gap is recorded here and in
[`BREAKOUT_RESULTS.md`](../results/BREAKOUT_RESULTS.md) rather than worked around. The study's
other three filters are implemented and measured in full.

## Rationale

`Bar` (`simulator/fills.py`) carries open/high/low/close and nothing else.
`TimestampedBar` adds only a timestamp. `DataView` — the structural look-ahead guard
strategies receive (D32) — hands out `Bar` objects. Volume *is* fetched, cleaned,
validated and stored in snapshots, but it stops at the data layer: `csv_fixture.py` states
outright that "TimestampedBar carries no volume field (D59/D60), and inventing one here
would be a false affordance (D48)".

Two workarounds exist, and both are worse than the missing filter:

1. **Add volume to `Bar` / `TimestampedBar` / `DataView`.** A schema change to the
   framework's most load-bearing type, rippling through the simulator, the cost bricks,
   the golden masters and the D79 cross-engine reconciliation. That is framework work with
   its own verification gate, not something a strategy study does on the way past — and
   the study brief explicitly forbade modifying existing interfaces.
2. **Pass a volume series into the strategy's constructor.** This hands strategy code
   full-sample data sitting outside the DataView guard: exactly the look-ahead hole D32
   exists to close, opened invisibly, since nothing would fail and the resulting numbers
   would look entirely reasonable.

The honest state is "specified, blocked, not faked". The change needed is small and
well-defined — a volume field on `TimestampedBar`, threaded through `build_data_view` so
strategies see it under the same guard as prices, with the cleaner/validator already
carrying the data — but it is a framework decision, and per R3 the deferral is written
down rather than left implicit. Until it lands, no code claims the capability.

## What would need to be true to build it

**Scoped in full, 2026-08-18: see [`docs/volume_extension.md`](../volume_extension.md).**

The short version, which corrects the first guess written above. The change is *not* a
`TimestampedBar` schema change — volume on `TimestampedBar` still would not reach a
strategy, because `DataView` holds `Bar` objects. It is an **optional aligned volume series
inside `DataView` itself**, constructed sliced the way bars already are, with
`build_data_view` and `run_backtest` gaining optional parameters that leave every existing
call site untouched.

The plumbing is around sixty lines. The verification is the cost, and it is planned rather
than discovered: extending the D32 reflection audit to the new surface, extending the
no-look-ahead property test to volume, a hand-computed golden master for a volume-gated
entry, and the D79 cross-engine reconciliation (which re-runs automatically, since it lives
in the normal offline suite). Roughly eight hours — about one week of this project's budget.

The design also names a distinction this record's original framing missed: **"this
instrument has no volume" (spot FX, an index) and "somebody forgot to wire volume through"
must not be the same observation.** The first returns `None` silently and correctly; the
second must be loud, or a volume filter quietly rejects every entry and returns a
plausible, wrong result. `NaN` — which the fixture loader yields for a blank cell, and which
compares `False` against everything — is normalised out at construction so it can never
reach a strategy.

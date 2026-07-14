# D64 — Strategy and run_backtest generalized to multi-instrument, single is the N=1 case

**Status:** Committed
**Date:** 2026-07-13
**Category:** Backtest engine
**Source:** Implementation session (multi-instrument alignment for pairs)

## Decision

`Strategy.generate_targets` changes from `(view: DataView) -> list[TargetWeight]` to
`(views: Mapping[str, DataView]) -> list[TargetWeight]` — one `DataView` per
instrument the strategy might trade. `ScheduledWeightStrategy` changes from
`(strategy_id, instrument_id, weight)` to `(strategy_id, weights_by_instrument:
Mapping[str, Sequence[float]])`. `run_backtest` changes from `(bars, instrument_id,
...)` to `(bars_by_instrument: Mapping[str, Sequence[TimestampedBar]], ...)`, aligning
via `align_bars` (D63) internally and building each instrument's `DataView` from its
own aligned bar sequence. A single-instrument backtest is now just a one-entry mapping
— not a separate code path.

Carry still accrues per instrument independently (each leg's own signed notional as
its own `FlatRateCarry` base amount), not netted against aggregate gross exposure —
that toy-brick boundary is unchanged from D54; real net-exposure margin interest is
D5's job (Step 5), not this chunk. `DataView` itself (D32/D56) is untouched — only what
gets built and handed to strategies changed.

Both are breaking changes, not additive. `tests/unit/test_strategy.py` and
`tests/integration/test_backtest_loop.py` (including the Step 3/D53 golden-master
reproduction test) were migrated in place and re-run to confirm identical results
under the new signatures before anything new was added — the same discipline used for
the Step 2→3 `CarryModel` migration (D54).

## Rationale

This mirrors the precedent D55 and D58 already set for `capital_by_strategy`: rather
than build a parallel "multi-instrument strategy" interface alongside the existing
single-instrument one, the existing interface is generalized so single-instrument is
the trivial case of the general one. Two interfaces for "one instrument" vs "several"
would mean every future engine change (a new field on `BacktestResult`, a new
per-instrument check) needs writing twice and keeping in sync, or strategies split into
two incompatible families depending on which interface they were written against —
exactly the kind of duplicated-logic risk Pillar 4 of `PHILOSOPHY.md` (composability)
warns against. A breaking change to an interface that's one implementation session old,
caught and fixed now with full regression verification, is far cheaper than carrying
two parallel shapes forward into Step 5 and beyond.

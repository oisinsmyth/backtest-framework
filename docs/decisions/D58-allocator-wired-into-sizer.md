# D58 — Allocator interface, and wiring ConstantSplitAllocator into Sizer

**Status:** Committed
**Date:** 2026-07-13
**Category:** Portfolio layer
**Source:** Implementation session (Step 4)

## Decision

`Allocator` (`engine/allocator.py`) is a one-method `Protocol`:
`allocate(total_capital, strategy_ids) -> dict[str, float]`. `ConstantSplitAllocator`
is the only implementation: an even split, holding no state, so capital changes are
reflected the instant `allocate()` is called again — there's nothing to go stale.

Its output is proven (`tests/unit/test_allocator.py::
test_allocator_output_feeds_sizer_capital_by_strategy_unmodified`) to plug directly into
`pipeline.sizing.Sizer.size_targets`'s `capital_by_strategy` parameter, with no glue
code in between.

## Rationale

D31 already specifies the shape (constant split, stable interface, commit to nothing
clever) — the only real decisions left were the exact method signature and, more
importantly, actually closing the loop D55 (Step 3) left open on purpose: `Sizer` was
built to take `capital_by_strategy` as an external input specifically because deciding
it wasn't Step 3's job. Building `Allocator` without also proving it satisfies that
exact contract would leave the "closes the loop" claim untested — anyone could have
written an incompatible `Allocator` and nothing would have caught it. The wiring test is
cheap and turns a design intention into a checked fact.

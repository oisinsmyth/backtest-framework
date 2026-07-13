# Options Extension — Scoping Doc (Stub)

**Status: stub.** This file exists so `OptionStub`'s `NotImplementedError` messages
point at a real path instead of a dead link. The full scoping write-up (why options were
deferred, what "done" looks like, the margin/pricing/Greeks/assignment work involved) is
Step 11's job per [`VERIFICATION_SCHEME.md`](VERIFICATION_SCHEME.md) and
[`DEVELOPMENT_TIMETABLE.md`](../DEVELOPMENT_TIMETABLE.md) — not written yet.

See [D16](decisions/D16-options-implemented-as-a-well-formed.md) for the original
decision and rationale: a well-formed stub now (real dataclass fields, correct contract-
multiplier arithmetic), hard parts (margin, pricing, Greeks, assignment) raising
`NotImplementedError` rather than a fabricated number, full scoping doc later.

What exists today: `backtest_framework.instruments.option_stub.OptionStub`
(`notional()`, `tradeable_quantity()`, and `carry_components()` work; 
`margin_requirement()` raises, pointing here).

# D100 — carry_components() is consulted, not decorative (audit F24)

**Status:** Committed
**Date:** 2026-07-14
**Category:** Instruments / Cost architecture
**Source:** Audit remediation session (AUDIT_REPORT.md finding F24)

## Decision

`Instrument.carry_components()` — part of D12's committed interface — was never
read by any production code: the engine applied every per-leg carry brick and
every event-flow brick to every position regardless of what the instrument
declared, so an instrument declaring `()` (the OptionStub) would still have been
charged borrow by a stack containing a BorrowFee brick. Now:

- Per-leg carry bricks and event-flow bricks may declare the carry component they
  model as a `component: ClassVar[str]` — `BorrowFee` declares `"borrow"`,
  `DividendFlow` declares `"dividend"`. Bricks declaring no component (the toy
  `FlatRateCarry`) are generic and always apply.
- `CostStack.carry_cost` accepts `components: tuple[str, ...] | None`; the engine
  passes the held instrument's `carry_components()`. `CostStack.event_flow`
  filters by the instrument's declaration directly (it already receives the
  instrument). `components=None` means "no instrument context" and applies
  everything — the pre-D100 behaviour, kept for direct callers.
- The scaling (D68) and recording (D95) wrappers forward the inner brick's
  `component` so a scaled or recorded stack filters identically to the plain one
  — without this, the 0×-equivalence and recorder-transparency identities would
  silently diverge from the unwrapped stack's behaviour.
- `MarginInterest` is untouched: it lives in the portfolio slot (D67), which has
  no per-instrument context by design.

## Rationale

No committed artifact changes: `Equity` declares `("margin_interest", "borrow",
"dividend")`, which covers every brick used by every study, golden master, and
gate — the filter is a no-op for everything that exists today. The point is the
interface's honesty (D48 applied to our own protocol): a method that promises
"names of the carry cost types applicable to this instrument" either governs
behaviour or it lies. The alternative — deleting the method — would have amended
D12's committed interface to escape implementing it. Choosing enforcement now,
while it changes nothing, means the first non-equity instrument (crypto's funding
component, D14) gets correct carry semantics by declaration instead of by
remembering to special-case the engine.

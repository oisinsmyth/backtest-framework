# D16 — Options implemented as a well-formed stub: real dataclass fields + contract multiplier logic, NotImplementedError on hard parts (margin, pricing, Greeks, assignment), pointing at docs/options_extension.md

**Status:** Deferred
**Date:** 2026-07-07
**Category:** Instruments
**Source:** Session 1 — initial design review

## Decision

Options implemented as a well-formed stub: real dataclass fields + contract multiplier logic, NotImplementedError on hard parts (margin, pricing, Greeks, assignment), pointing at docs/options_extension.md.

## Rationale

The put-spread thesis is unrepresentable without an options wing (pricing, per-contract commissions, 5–10%+ spreads on illiquid strikes), which is months of work + paid data. A committed shape + written scoping rationale reads as maturity; a half-built module reads as sprawl.

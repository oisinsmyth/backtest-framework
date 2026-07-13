# D27 — Pipeline boundary changes to signal → target weight → orders. Strategies output desired portfolio weights; a central sizer/allocator converts targets to orders

**Status:** Committed
**Date:** 2026-07-07
**Category:** Signals & strategy interface
**Source:** Session 2 — full-framework review

## Decision

Pipeline boundary changes to signal → target weight → orders. Strategies output desired portfolio weights; a central sizer/allocator converts targets to orders.

## Rationale

Welding alpha ("XLE rich vs XOP") to implementation ("sell 43 shares") inside each strategy prevents reusing sizing logic, prevents comparing signals independent of sizing, and prevents netting orders across strategies (A buying what B sells should cancel internally, not pay costs twice). This is the standard architecture (Carver) and the single biggest interface change in the framework — cost of fixing grows with every strategy written, so it lands early.

# D07 — FX handled in two parts: FXConversionCost trade brick now; full multi-currency accounting deferred, with unhedged FX exposure reported as a tearsheet line item

**Status:** Committed / Deferred
**Date:** 2026-07-07
**Category:** Cost architecture
**Source:** Session 1 — initial design review

## Decision

FX handled in two parts: FXConversionCost trade brick now; full multi-currency accounting deferred, with unhedged FX exposure reported as a tearsheet line item.

## Rationale

Base currency (EUR/GBP) vs USD positions creates real conversion costs and a hidden currency bet, but full multi-currency accounting is a large lift. Label the blind spot now, close it later.

# D12 — Introduce Instrument abstraction: positions/fills reference instrument objects, not ticker strings. Interface: notional(), margin_requirement(), carry_components(), tradeable_quantity(), quote_currency

**Status:** Committed
**Date:** 2026-07-07
**Category:** Instruments
**Source:** Session 1 — initial design review

## Decision

Introduce Instrument abstraction: positions/fills reference instrument objects, not ticker strings. Interface: notional(), margin_requirement(), carry_components(), tradeable_quantity(), quote_currency.

## Rationale

The framework currently hard-codes "everything is a share of stock"; making that assumption explicit and swappable is what enables multi-asset support. Do in the same refactor as CostStack (same surgery, one anaesthetic).

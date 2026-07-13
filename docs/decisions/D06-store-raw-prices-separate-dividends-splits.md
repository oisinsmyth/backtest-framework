# D06 — Store raw prices + separate dividends/splits table; compute returns from adjustments but fills/commissions from raw prices; add DividendFlow carry brick (credits longs, debits shorts)

**Status:** Committed
**Date:** 2026-07-07
**Category:** Cost architecture
**Source:** Session 1 — initial design review

## Decision

Store raw prices + separate dividends/splits table; compute returns from adjustments but fills/commissions from raw prices; add DividendFlow carry brick (credits longs, debits shorts).

## Rationale

Adjusted prices silently corrupt historical cost math (commissions computed on rewritten notionals) and shorts pay dividends (XLE ~3% yield matters to pairs P&L). Blocking for any trustworthy pairs result.

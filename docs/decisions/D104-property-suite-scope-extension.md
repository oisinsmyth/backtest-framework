# D104 — Property-suite scope extension: signed positions, real OHLC bars, unconditional accountants (audit F14)

**Status:** Committed
**Date:** 2026-07-14
**Category:** Testing
**Source:** Audit remediation session (AUDIT_REPORT.md finding F14)

## Decision

The D40/D78 invariant suite's scenario domain was narrower than the gate text
implied: single-instrument, long-only weights (0–0.9), flat OHLC bars
(open = high = low = close) — so "every fill within its bar's range" was
tautological at the engine level, shorts had no property coverage at all, and
the flat-commission leak test's assertion sat inside an `if` that silently
passed whenever commissions shifted the NAV-driven sizing (vacuous for exactly
the examples where the arithmetic was most at risk). Changes:

1. **`ohlc_scenarios`**: generated bars now carry genuine structure (opens gap
   off the previous close; highs/lows bracket both) and weights span
   **[−0.9, +0.9]** — fills-reconcile-to-position and the zero-cost shadow
   accountant now hold across short and mixed books, not just long-only.
2. **The commission leak test is unconditional**: instead of comparing against a
   zero-cost run and skipping on divergence, it asserts the per-bar identity on
   the charged run itself — `ΔNAV = position·Δclose − $10 × fills this bar` —
   which cannot be vacuously satisfied.
3. **Carry joins the shadow accountant**: with `FlatRateCarry` as the only cost,
   `ΔNAV = position·Δclose − position·close·rate/365` per daily bar — pinning
   the engine's D67 carry-base convention (current bar's close) as a tested
   fact rather than a code comment.
4. **next_open properties** (D103): every fill at its bar's open, never on the
   first bar; determinism; and the generalized shadow accountant
   `ΔNAV = position·Δclose + filled_today·(close − open)`.

## Rationale

The invariants D40 promised were true but over-verified on a domain that
excluded the book shapes the framework actually researches (a pairs book is
half short by construction). Extending the generators is cheap; the
unconditional accountant identities are strictly stronger than the
comparative test they replace, and each one that passes converts an engine
convention from documentation into a machine-checked fact.

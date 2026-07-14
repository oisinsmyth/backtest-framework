# D106 — Conventions pinned: share rounding, carry mark timing, bootstrap block length (audit F15/F25/F29)

**Status:** Committed
**Date:** 2026-07-14
**Category:** Backtest engine / Analytics
**Source:** Audit remediation session (AUDIT_REPORT.md findings F15, F25, F29)

## Decision

Three implicit conventions the audit found undocumented are now stated, tested
where cheap, and deliberately left unchanged — changing any of them would move
every committed golden master and study artifact for zero informational gain:

1. **Share rounding is round-half-to-even to the NEAREST whole share (F15).**
   `Equity.tradeable_quantity` uses Python's `round()` — banker's rounding — so a
   desired quantity rounds up roughly half the time, and a 100%-weight target can
   momentarily hold slightly more notional than capital; `apply_fill` performs no
   cash-sufficiency check (negative cash is possible at extreme weights and is
   treated as implicit margin, consistent with the D62/D107 posture that risk is
   observational until a study needs enforcement — `enforce_pretrade`, D101, is
   the available gate). Floor-toward-zero would be the conservative alternative;
   adopting it now would silently shift every fill in every published artifact
   (e.g. the golden master's −1253-share re-size becomes −1252), so the existing
   convention is pinned by test (`test_instruments.py`) instead. Revisit only
   with a study-version bump.

2. **Carry and margin bases mark at the CURRENT bar's close (F25).** Carry over
   the gap (prev, curr] is charged on the position held at prev close, valued at
   curr's close — mildly anticipatory relative to charging on prior marks, but
   consistent, hand-verified in THE golden master, and now pinned by a property
   test (`test_no_nav_leaks_with_carry`, D104) rather than living only in a code
   comment. D67's "start-of-bar snapshot" language means "before any deductions
   or fills this step", not "at the previous bar's prices" — recorded here so the
   two readings can't be confused again.

3. **Monte Carlo block length defaults to 20 bars (F29).** D81 named the value
   without a rationale. The reasoning, recorded: 20 trading days ≈ one calendar
   month, comfortably longer than the lag structure a daily mean-reversion
   strategy trades (the z-score lookback's autocorrelation horizon) while short
   enough that a ~2,500-bar sample still supplies ~125 distinct blocks. The
   usual n^(1/3) rule of thumb gives ~14 for that sample size — same order of
   magnitude; the default is a stated choice, overridable per call, not a fitted
   parameter. No block-length sensitivity is run because no published conclusion
   is within an order of magnitude of flipping on bootstrap percentiles.

## Rationale

An undocumented convention is a decision someone made without noticing; each of
these is now either machine-checked (1, 2) or reasoned in writing (3). Keeping
the behaviour identical is deliberate: these are disclosure fixes, and the house
rule (D76/D103) is that behaviour changes ship as new study versions, not as
silent history rewrites.

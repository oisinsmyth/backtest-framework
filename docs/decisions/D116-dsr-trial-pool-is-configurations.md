# D116 — For a parameter-swept study the DSR trial pool is configurations, not windows

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Breakout study session

## Decision

The breakout study computes a DSR per (symbol, cost tier) whose trial pool {SRn} is **every
strategy variant's out-of-sample daily Sharpe at that (symbol, tier)** — 19 configurations
per cell. Pool membership is selected on identity fields in the logged config
(`row_kind == "variant"`, matching symbol and tier), never on the presence of a metric
(D98's rule). Per-window rows carry `row_kind="window"` and are excluded by that same
predicate.

Units follow D98 exactly: the logged `oos_sharpe_daily`, the observed SR handed to the PSR,
and T are all per-period (daily, non-annualised).

## Rationale

The pairs studies pooled one row per walk-forward window, and that was right *for them*:
they varied no parameters, so their windows were their trials. This study varies twelve
parameter grid cells, four filter increments, two sizing policies and one fitted-selection
scheme. Bailey & López de Prado's N is the number of **configurations** tried, and here
there genuinely are many, so pooling windows would answer a question nobody asked while
leaving the actual multiplicity uncounted.

**What the resulting numbers do and do not mean.** The DSRs come out near 1.0 at every
tier, and the mechanical reason is visible in the plateau surface: 19 variants whose
Sharpes cluster tightly give a tiny V[{SRn}], so SR0 — the noise floor a selected best
result must clear — barely rises, and almost nothing is deflated away. That is DSR working
correctly on the multiplicity it was given.

It is also why the report refuses to read those numbers as vindication. The pool counts 19
configurations. It does not count the 4,896 in-training-window parameter fits (fits, not
out-of-sample trials — but each is a setting that was looked at), the cross-symbol
multiplicity, or the largest term of all: the decision to test a trend follower on the two
crypto assets that survived, taken with a decade of crypto trend already visible. The
standing reading, inherited from D90 and restated here: **DSR < 0.95 means "no demonstrated
edge"; DSR ≥ 0.95 does not mean the reverse.**

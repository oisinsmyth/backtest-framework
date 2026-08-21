# D142 — For a fixed-rule cross-sectional study the DSR trial pool is the symbols

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Breakout universe session

## Decision

The universe study computes a DSR per cost tier whose trial pool {SRn} is **every
symbol's out-of-sample daily Sharpe at that tier** — N = 63. Pool membership is selected on
identity fields in the logged config (`row_kind == "symbol"`, matching tier, matching
trial-id prefix), never on the presence of a metric (D98's rule). Benchmark rows carry
`row_kind="benchmark"` and per-window rows `row_kind="window"`; both are in the registry as
the program-level multiplicity record (D90) and are excluded by that same predicate.

Units follow D98 exactly: the logged `oos_sharpe_daily`, the observed SR handed to the PSR,
and T are all per-period (daily, non-annualised).

A non-finite Sharpe anywhere in the pool **raises**. It is neither imputed nor dropped —
imputing distorts V and dropping distorts N, which is the failure D98 fixed one layer up.
The first run of this study did raise, on a stablecoin, and the fix was a policy clause
rather than a fudge ([D144](D144-peg-screen-added-after-first-run.md)).

## Rationale

D116 set the breakout study's pool to *configurations*, because that study swept
configurations and its windows were not its trials. This study sweeps none (D141) — one
fixed rule everywhere — so pooling configurations would give N = 1, and pooling windows
would answer a question nobody asked. Its multiplicity lives entirely in the
cross-section: 63 coins were run at a fixed rule, and the best of 63 will look good
whether or not anything is there. That is precisely the selection Bailey & López de Prado's
N is meant to count.

**What the pool is not**, stated in the report next to the number:

- the **roster construction** — a hand-assembled list, in 2026, of coins someone
  remembered. That is the largest uncounted term, and no statistic computed inside the
  document can deflate it;
- the **4 cost tiers** — the same run at a different fee is a sensitivity point, not an
  independent trial (D98);
- the **23 configurations** the BTC/ETH study evaluated before this one fixed its baseline.
  That multiplicity is upstream of this study's rule and is inherited by it (D141);
- the decision to ask the crypto question at all, in 2026, with a decade of visible trend.

**Standing reading, inherited from D90 and D116:** a DSR below 0.95 means "no demonstrated
edge"; a DSR above 0.95 does **not** mean the reverse.

## What the numbers came out as, and why the report leads with the pool rather than the DSR

The DSRs land near 0.96 at every tier, and the best-symbol column is the reason to
distrust them: the highest cross-sectional daily Sharpe belongs to `LUNA1-USD` — a token
this study labels *delisted* — over 881 out-of-sample bars, about 2.4 years and the short
end of the universe. A selected best-of-63 on a short span from an asset that no longer
trades is the least robust number in the document. The report prints it inside the
multiplicity section rather than in a headline, with that sentence attached.

# D141 — One fixed configuration across the whole cross-section; the universe is the only variable

**Status:** Committed
**Date:** 2026-08-18
**Category:** Validation & research integrity
**Source:** Breakout universe session

## Decision

The universe study runs **exactly one strategy configuration** — `plateau_40_10`, the
BTC/ETH study's baseline (n_entry=40, n_exit=10, inverse-vol sizing at a 40% annual vol
target, no filters) — on every admitted symbol at all four cost tiers. No per-coin
parameter sweep, no per-coin filter increments, no in-training selection. Nothing in this
study is fitted.

Everything that computes a number is imported unmodified from
`research.breakout_study`: `run_variant`, `run_benchmark`,
`run_constant_fraction_benchmark`, `breakout_config`, `CostTier`, `DEFAULT_TIERS`,
`annual_breakdown`, `start_date_sensitivity`, `sharpe_difference_bootstrap`.
`research/breakout_universe.py` contains selection policy, aggregation and rendering, and
nothing else. An integration test asserts that every logged config in the registry is
byte-identical to `breakout_config(40, 10)`.

## Rationale

**Sweeping per coin would multiply the multiplicity for no gain.** The BTC/ETH study
already computed the 12-cell plateau surface, measured its spike-versus-plateau gap, and
found in-training parameter selection *lost* to fixing 40/10 a priori. Re-sweeping 12 cells
across 63 coins would be 756 configurations evaluated to re-answer a settled question,
and the resulting DSR pool would be dominated by grid noise instead of by the thing this
study actually varies.

**The cross-section is the variable, and one variable at a time is this project's rule**
(D92's "one variable per version", applied here). Holding the rule fixed is what lets the
hit-rate tables be read as a statement about instruments rather than about tuning.

**It also makes the DSR pool honest.** With one configuration, the multiplicity is entirely
cross-sectional, which is exactly what [D142](D142-dsr-pool-is-the-cross-section.md) pools.
A per-coin sweep would have mixed two different kinds of trial in one pool and made N
uninterpretable.

## The cost of this choice, stated

The baseline being inherited means this cross-section evaluates a rule that was, in a small
way, already fitted to two of its own members — BTC and ETH were the data on which 40/10
was selected. That is an inherited optimism the cross-section cannot remove, and it is
listed in the report's standing caveats rather than left implicit. The mitigation available
without re-introducing multiplicity is the one the report uses: report where BTC and ETH
rank inside the cross-section, so a reader can see how much of the original result was the
instrument choice.

# D560 — Every reported Sharpe carries a Sortino beside it (R17), and the five runners of 2026-09-19 are re-run under it

**Status:** Committed
**Date:** 2026-09-19
**Category:** Reporting rule
**Source:** the principal's mandate, verbatim: *"all runs, simulations etc. will provide a Sortino
ratio along with the Sharpe ratio."*

## Decision

Recorded as [R17](../RULES.md#r17) in the standing rules. Wherever a run, simulation, null,
bootstrap or record reports a Sharpe, it reports the Sortino of the same series beside it, under
the same convention: same returns, same risk-free rate (zero for a futures book), same periods per
year; `analytics.metrics.sortino` — mean excess over the root mean of the squared negative excess
returns taken over **all** observations, annualised by √(periods per year); +inf with no downside
and a positive mean (serialised as null), 0.0 otherwise.

## Where it is wired, so it cannot be forgotten

| site | what changed |
|---|---|
| `scripts/run_d555_tsmom_replication.py` | `sortino()` beside `sharpe()`; `stats_block` carries `"sortino"`; `enumerate_null(..., with_sortino=True)` returns a Sortino column of the same rotated books; `sortino_null_block` gives observed / p05 / p50 / p95 on the purged offsets |
| `scripts/run_d556_carry_timing.py`, `run_d557_xs_term_structure.py`, `run_d558_xs_momentum.py`, `run_d559_double_sort.py` | every cell's `null_n1.per_cell[...]["sortino"]` block; every `stats_block` inherits the key |
| `src/backtest_framework/research/terrain_strategies.py` | `"sortino"` beside `"sharpe"` in the buy-and-hold summary, zero-rf like its neighbour |
| `src/backtest_framework/research/breakout_study.py`, `breakout_intraday.py`, `crypto_pairs_study.py` | `sortino_annual` beside `sharpe_annual` on the result classes, same rf and periods |
| `tests/unit/test_sortino_beside_sharpe.py` | pins the runner's Sortino to the library's, the null block's shape, and the classes' surface |
| `CLAUDE.md` *Reporting a result* §1 | "Sharpe AND Sortino, always together" |

## What it does not change

The pre-registered PASS statistics of D555–D559 remain the Sharpe, and the ledger's C-a bar
remains a Sharpe bar. The Sortino is reported beside them, not substituted. The five runners were
re-run under the rule; every previously written number in their artifacts is unchanged to the byte
(the re-run's non-regression check compares every pre-existing key), and each RESULT record
carries a dated addendum with the Sortino of its declared cells. Runners frozen before
2026-09-19 are not edited (D543).

## Because

A two-sided fat-tailed book and a negatively-skewed one can share a Sharpe and differ in what a
trailing-drawdown account lives through — D556's carry book had skew −0.20 and lost 4.1% in
March 2020 while the trend book made 21%. Sharpe is blind to which tail the variance sits in;
the prop hurdles (P1, P3) are about the left tail, and the Sortino is the ratio that sees it.

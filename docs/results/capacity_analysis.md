# Capacity analysis — where does the v2 edge clear real costs?

**Date produced:** 2026-07-14 · **Snapshot:**
`54d4e476c0560d473fc1539e8540e0fa1ab371a69dad2f02b9bc6eae9cd671fd` · **Method (D95):** the byte-identical v2 study
([pairs_study_v2.md](pairs_study_v2.md) — cointegration selection, 1:1 hedge per
v3's verdict) run at 9 log-spaced account sizes with the REAL,
unscaled cost stack. The multiplier sweep (D8) scales all frictions uniformly and
cannot see size; here the bricks themselves produce the size dependence — IBKR's
$1/order minimum binds small accounts, √-impact (fraction ∝ √(Q/ADV)) binds large
ones, spread/borrow/margin are scale-invariant rates. Selection depends only on
train views, so every level trades the SAME pairs on the same dates: the levels
differ only through costs and whole-share rounding. Amounts are USD. **Trials
logged:** 385 (`data/capacity_study_registry.sqlite`).

## Net return by account size (1× real costs)

| AUM | Net return (9yr) | Net /yr | Max drawdown | Max participation (symbol) |
|---|---|---|---|---|
| $10k | -20.06% | -2.53% | 22.34% | 0.02% (EWL) |
| $30k | -10.69% | -1.28% | 18.33% | 0.05% (EWL) |
| $100k | -6.43% | -0.76% | 16.18% | 0.15% (EWL) |
| $300k | -5.77% | -0.68% | 15.98% | 0.46% (EWL) |
| $1M | -8.98% | -1.07% | 16.59% | 1.52% (EWL) |
| $3M | -15.49% | -1.91% | 18.84% | 4.55% (EWL) |
| $10M | -26.85% | -3.51% | 28.07% | 15.02% (EWL) |
| $30M | -41.03% | -5.86% | 41.59% | 44.35% (EWL) |
| $100M | -59.05% | -9.70% | 59.21% | 143.33% (EWL) |

## Where the money goes — drag decomposition (annualized, % of average NAV)

| AUM | IBKRCommission | PercentOfNotionalSpread | SqrtImpact | BorrowFee | MarginInterest | Total |
|---|---|---|---|---|---|---|
| $10k | 3.165% | 0.377% | 0.128% | 0.106% | 0.861% | 4.637% |
| $30k | 1.724% | 0.376% | 0.226% | 0.106% | 0.864% | 3.297% |
| $100k | 0.997% | 0.376% | 0.415% | 0.106% | 0.866% | 2.760% |
| $300k | 0.612% | 0.376% | 0.720% | 0.106% | 0.866% | 2.680% |
| $1M | 0.432% | 0.376% | 1.304% | 0.106% | 0.864% | 3.082% |
| $3M | 0.378% | 0.376% | 2.221% | 0.106% | 0.862% | 3.944% |
| $10M | 0.364% | 0.376% | 3.933% | 0.106% | 0.857% | 5.636% |
| $30M | 0.365% | 0.375% | 6.519% | 0.106% | 0.851% | 8.216% |
| $100M | 0.372% | 0.374% | 11.107% | 0.106% | 0.842% | 12.800% |

## The finding

**No AUM level clears real costs.** The hump is real and lands where the cost structure predicts — commission minimums punish the small end, √-impact the large end, with the optimum at $300k (-5.77% over the study, -0.68%/yr) — but the whole curve sits below zero. The arithmetic at the optimum: the gross edge is ≈+2.01%/yr; the scale-invariant floor (spread + borrow + margin interest on ~200% gross) is 1.35%/yr by itself, and the size-aware frictions (commission + impact) still add 1.33%/yr at the optimum — 2.68%/yr of total drag against +2.01%/yr of edge. The largest single fixed lever is margin interest (0.87%/yr at the retail 6% rate): to first order, even FREE margin funding would lift the optimum only to ≈+0.19%/yr. The honest conclusion: this edge, at this gross exposure, does not clear real frictions at any account size — the binding constraint is the cost floor of running a ~200% gross book, not any one size-dependent friction.

For reference, the same strategy is **+19.03% gross** (0× costs) — measured at
$100M in this run's sanity check: +19.04%, confirming gross is
scale-invariant up to rounding and the spread between levels is pure cost
structure. (The sanity run's 1× leg reproduces the recorded $100M level:
-59.05% vs -59.05%.)

## Caveats

- **√-law extrapolation**: the square-root impact model is an empirical fit from
  institutional execution data; the max-participation column reports how far each
  level pushes it. Levels trading a large fraction of a symbol's ADV are model
  extrapolation, not measurement — treat the large-AUM rows as increasingly
  approximate.
- **Full-sample σ/ADV calibration** (D66) — the standing mild look-ahead in cost
  parameters, never in signal.
- **Retail rate assumptions held fixed across scale**: 6% margin interest and
  25bps borrow are retail-grade at every level. Institutions fund cheaper — a
  large account's true drag table would shrink the MarginInterest/BorrowFee
  columns. Stated, not modeled.
- **Whole-share rounding** is a real small-account friction and part of the
  small-AUM rows' honest story (positions of ~tens of shares are lumpy).
- **DSR is not the object here**: these are cost diagnostics of ONE strategy at
  varying account size, not new signal trials. They are still logged to the
  registry, so they count toward the program-level multiplicity record (D90).
- Standing data caveats unchanged (single-source D26, XLF-spinoff encoding D88).

## Reproduction

`uv run python scripts/run_capacity_analysis.py` — offline, deterministic.
Recorder transparency (attribution provably does not perturb the run) and the
two-sided direction property are tested in `tests/unit/test_capacity.py` and
`tests/integration/test_capacity_study.py`.

# Gross exposure study — does lower gross clear the cost floor?

**Date produced:** 2026-07-14 · **Snapshot:**
`54d4e476c0560d473fc1539e8540e0fa1ab371a69dad2f02b9bc6eae9cd671fd` · **Method (D96):** the byte-identical v2 study
([capacity_analysis.md](capacity_analysis.md) machinery, D95) across
**leg_weight ∈ {0.25, 0.5, 0.75, 1} × AUM ∈
{$100k, $300k, $1M, $3M, $10M}**, real
unscaled costs. One variable: leg_weight (book gross when all pairs are in trade
= 2·lw·NAV). The mechanism under test is the **margin threshold** — interest
accrues on max(gross − NAV, 0), so at gross ≤ NAV it collapses instead of
scaling down, while the edge scales ≈∝ lw, spread/borrow ∝ lw, impact ∝ lw^1.5,
and the $1/order commission minimums don't shrink at all. AUM below $100k is
omitted a fortiori: minimums already dominate there at lw 1 and lower gross
strictly worsens that end. The lw 1 column reproduces the capacity artifact's
rows (same computation — a built-in cross-check). Amounts are USD. **Trials
logged:** 980 (`data/gross_sweep_registry.sqlite`).

## Net return per year (1× real costs)

| AUM | lw 0.25 (gross 50%) | lw 0.5 (gross 100%) | lw 0.75 (gross 150%) | lw 1 (gross 200%) |
|---|---|---|---|---|
| $100k | -0.12% | -0.03% | -0.18% | -0.76% |
| $300k | +0.04% | +0.12% | -0.04% | -0.68% |
| $1M | +0.07% | +0.06% | -0.26% | -1.07% |
| $3M | +0.00% | -0.22% | -0.80% | -1.91% |
| $10M | -0.21% | -0.84% | -1.91% | -3.51% |

## The mechanism: margin drag (annualized, % of average NAV)

| AUM | lw 0.25 (gross 50%) | lw 0.5 (gross 100%) | lw 0.75 (gross 150%) | lw 1 (gross 200%) |
|---|---|---|---|---|
| $100k | 0.000% | 0.000% | 0.220% | 0.866% |
| $300k | 0.000% | 0.000% | 0.220% | 0.866% |
| $1M | 0.000% | 0.000% | 0.219% | 0.864% |
| $3M | 0.000% | 0.000% | 0.219% | 0.862% |
| $10M | 0.000% | 0.000% | 0.217% | 0.857% |

At and below the 100% gross threshold (lw ≤ 0.5) margin does not halve — it
collapses. Trace amounts at lw 0.5 are real: whole-share rounding and NAV drift
nudge gross past NAV on scattered bars.

## Total drag (annualized, % of average NAV)

| AUM | lw 0.25 (gross 50%) | lw 0.5 (gross 100%) | lw 0.75 (gross 150%) | lw 1 (gross 200%) |
|---|---|---|---|---|
| $100k | 0.628% | 1.061% | 1.693% | 2.760% |
| $300k | 0.488% | 0.901% | 1.561% | 2.680% |
| $1M | 0.447% | 0.961% | 1.778% | 3.082% |
| $3M | 0.519% | 1.246% | 2.335% | 3.944% |
| $10M | 0.733% | 1.875% | 3.471% | 5.636% |

## Gross reference per column (0×, plain stack, $100M)

| leg_weight | Book gross | Gross return (9yr, 0×) | Gross /yr |
|---|---|---|---|
| 0.25 | 50% | +4.64% | +0.52% |
| 0.5 | 100% | +9.37% | +1.03% |
| 0.75 | 150% | +14.17% | +1.53% |
| 1 | 200% | +19.04% | +2.01% |

## The finding

**5 cells clear absolute real costs: lw 0.25 @ $300k (+0.04%/yr), lw 0.25 @ $1M (+0.07%/yr), lw 0.25 @ $3M (+0.00%/yr), lw 0.5 @ $300k (+0.12%/yr), lw 0.5 @ $1M (+0.06%/yr).** The margin threshold did what the arithmetic predicted — the drag collapses below 100% gross rather than halving (see the margin matrix) — and every positive cell lives in the low-gross columns. The best is lw 0.5 at $300k: +0.12%/yr net against a +1.03%/yr gross edge.

**But clearing costs is not clearing the hurdle.** Against the study's 4% risk-free rate, the best cell's stitched Sharpe is -1.61 — it underperforms T-bills by ≈3.88%/yr, decisively, not marginally. Two honest notes cut opposite ways: (1) the simulator credits no interest on idle cash, and a gross ≤ 100% book is MOSTLY idle cash, so a real account sweeping cash into bills would recover much of that gap — but that return belongs to the risk-free rate, not to the strategy; (2) after five studies of program-level multiplicity (D90), even a genuinely thin positive edge would be statistically indistinguishable from zero. What this study establishes: at low gross the edge can just pay for its own implementation — it cannot pay for the capital it occupies.

## Caveats

Inherited from the capacity analysis (D95): √-law participation boundary
(smaller books push it less — the low-lw columns are the model's comfort zone),
full-sample σ/ADV calibration (D66), retail margin/borrow rates held fixed,
whole-share rounding at small sizes. Program-level multiplicity (D90) now spans
five studies; any thin positive here is subject to it in full.

## Reproduction

`uv run python scripts/run_gross_sweep.py` — offline, deterministic. The margin
threshold collapse, ~linear spread scaling, and registry non-collision are
tested in `tests/integration/test_gross_sweep.py`.

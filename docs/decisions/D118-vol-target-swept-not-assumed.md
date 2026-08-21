# D118 — The vol target is swept, and it is a risk dial rather than a Sharpe improvement

**Status:** Committed
**Date:** 2026-08-18
**Category:** Signals & strategy interface
**Source:** Breakout study review session

## Decision

`InverseVolatilityWeight`'s `target_annual_vol` is swept over
{20%, 30%, 40%, 60%, 80%} as first-class study variants (`voltarget_*`), registered as
trials like any other configuration, and reported as a ladder rather than a single
number.

The report's claim about it changes accordingly: the target is described as **a drawdown
purchase priced in return**, not as a risk-adjusted improvement.

## Rationale

The first version of this study picked a 40% target, ran everything at it, and never
tested it. That is the one thing D109's own plateau analysis exists to prevent, applied
inconsistently: the entry and exit windows got a 12-cell surface and an explicit
spike-versus-plateau test, while the parameter that determines how much capital is at risk
on every single trade got a value and a sentence of justification.

The sweep is unambiguous on this data. Total annualised Sharpe spread across the whole
ladder is ~0.09 on BTC — an order of magnitude inside the ±0.4 bootstrap band D120
establishes — so no target level is distinguishable from any other on risk-adjusted
grounds. What the target does move, and move a lot, is the return/drawdown pair: at a 20%
target BTC returns ~+3,000% with a 30% max drawdown, at 80% it returns ~+6,900% with 48%.

Against no vol targeting at all (`sizing_fixed_1.0`, always fully invested when long) the
40% baseline gives up roughly 29% of terminal wealth to buy about 5 percentage points less
drawdown, for a Sharpe change of +0.04 that cannot be distinguished from zero.

**So the honest statement is: pick the level from the drawdown you can tolerate, and do not
claim it improves the risk-adjusted result.** The original write-up implied otherwise by
reporting a single target with no ladder beside it — which is exactly the failure mode
the plateau surface was introduced to catch elsewhere in the same study.

## Consequence

The DSR trial pool per (symbol, tier) grows from 19 configurations to 23 (D116). That is
the correct direction: more configurations were genuinely evaluated, and the multiplicity
count should say so.

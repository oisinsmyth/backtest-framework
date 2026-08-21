# D165 — The crossover is read three ways, and the load-bearing reading splices a cost curve measured here onto a gross edge measured over ten years

**Status:** Committed
**Date:** 2026-08-19
**Category:** Analytics
**Source:** Cost-frequency frontier session

## Decision

The crossover frequency — the headline of the whole study — is the **coarsest (slowest)
bar at which the cost curve has risen above the trend edge**, read three ways, all fixed
before the numbers were looked at and all reported:

1. **In-sample Sharpe.** Net annualised Sharpe at `taker_40bp` at or below zero.
2. **In-sample cost share.** Costs at or above 100% of gross P&L.
3. **Spliced.** **Cost drag in Sharpe units** — annual fee drag ÷ annual volatility,
   measured *here* — at or above the gross annualised Sharpe measured over 2015–2025 daily
   bars in `BREAKOUT_RESULTS.md` at `maker_0bp` (BTC 1.27, ETH 0.84, imported as constants
   in `REFERENCE_GROSS_SHARPE`).

Reading (3) is the one the verdict is read off. The splice is labelled at every point of
use.

## Rationale

**Why one reading was not enough, discovered by running it.** The 730 days yfinance serves
are 2024-08 to 2026-08, and over that span a long-only crypto trend follower loses money at
*every* frequency including daily and at *every* cost tier including the free one. So
reading (1) returns "1d" for all four (symbol, design) ladders — a true statement that
answers a different question. It cannot separate "costs killed the edge" from "there was no
edge in this window to kill." Reading (2) is worse: `cost_share_of_gross` has P&L in its
denominator, so it is undefined near zero gross and meaningless below it, and its ladder is
visibly non-monotone for that reason alone.

**Why the spliced reading is legitimate rather than a fudge.** The two halves of a
cost-frequency frontier are not measured with the same precision, and pretending otherwise
is the error this study most needed to avoid:

- **The cost half is near-deterministic.** Turnover is a function of the rule and the bar
  size. `fee_drag_annual` — costs ÷ average equity ÷ years — has no P&L in it at all, and
  the integration suite checks it equals turnover × fee rate.
- **The edge half is barely measured.** 441 out-of-sample days buys a Sharpe standard error
  of about ±0.91. Estimating a gross edge from it would be theatre.

So the cost curve is taken from where it is well measured, the gross edge from where *it*
is well measured, and the two are compared in one unit. The conversion is first-order —
Sharpe ≈ (μ − rf)/σ, so `c` per year of fees costs about `c/σ` of Sharpe — and it is
**cross-checked against the directly measured gross-minus-net wedge** at every cell: they
agree to within 0.047 of a Sharpe at the 20 cells whose wedge is below one Sharpe point,
and diverge by up to 0.37 (15% relative) at the four fastest Design B rungs, where `c`
reaches 60–75% of capital a year and a first-order approximation has no business being
exact. Both facts are printed.

**What reading (3) assumes, and which way the assumption points.** It assumes the gross
edge does not change with the rule's horizon. That is **exact for Design A**, whose signal
really is the same 40-day/10-day breakout at every frequency. For **Design B it is
generous, knowingly**: a 40-bar entry at 2h is an 80-hour breakout, and this repo's own
plateau surface says the short-horizon cells are the weaker ones. Combined with a fee-only
cost model that charges no spread, no slippage and no impact (D114), **every distortion in
the study points the same way**, and the conclusion is stated as a bound rather than a
point: the reported crossover is an **upper bound** on how fast this rule can be traded,
and the true crossover is at a coarser bar, never a finer one.

**The answer this rule produced.** Design B crosses at **2h on both symbols
independently**, with 4h the finest bar that still clears; Design A never crosses at any
rung down to 1h, peaking at a cost drag of 0.27 against a gross Sharpe of 1.27 on BTC and
0.19 against 0.84 on ETH. Which means `BREAKOUT_RESULTS.md`'s "fees are not the binding
constraint" **survives intact for the 40-day signal at any sampling rate**, and fails
decisively for the shortened-horizon rule below roughly 4-hourly bars.

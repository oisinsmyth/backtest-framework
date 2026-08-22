# D185 — Charging the rebalancing cost: the test D183 set for itself

**Status:** PRE-REGISTERED — implementation committed, **study not yet run**
**Date:** 2026-08-22
**Category:** Analytics
**Source:** D183 closed by naming this as "the test of it, not a caveat on it"

> Written and committed **before** the study runs. Predictions falsifiable and dated by git.
> A result section will be appended and nothing above it edited.

## The question

D183 found a cross-sectional long portfolio at **+1.275** Sharpe (full span) and **+0.927**
(≥5 coins live), against **+1.191 / +0.733** for a daily-rebalanced equal-weight universe.
The strategy's own contribution is therefore **+0.084 / +0.194** — small enough that D183's
benchmark section said outright that an un-charged turnover cost could erase it.

Each coin's trading costs are charged inside its own book. What has never been charged is
**moving capital between coins** to hold equal weights, every day.

## What is charged, and to whom

One-way turnover, `0.5 * Σ |drifted weight − target weight|`, at the project's existing
cost ladder — **0 / 10 / 25 / 40 bp**, the same four levels as `bs.DEFAULT_TIERS`, so this
is read on a scale already in use rather than a number invented here. `taker_40bp` is the
reference: moving capital between small-cap alts on a daily schedule is a taker fill.

**The benchmark is charged too.** The equal-weight universe rebalances daily as well;
charging only the strategy would rig the comparison. Buy-and-hold is charged nothing after
its initial purchase, because it does not trade again.

**A flat book holds cash, and moving cash is free.** The turnover measure gets this right
without special-casing: a flat book reports exactly 0.0, so its slice does not drift. What
remains over-charged is a flat book joining or leaving the live set, counted as a full slice
traded when it was cash — and over-charging is the right direction for a test built to
threaten a result.

## The predictions

**H1 — the strategy's absolute Sharpe falls materially, below +1.00 on the full span, at
40 bp.** Predicted **TRUE**.

**H2 — the EDGE over the equal-weight universe WIDENS with cost rather than narrowing, and
there is no break-even.** Predicted **TRUE**, and it is the counterintuitive one.

The mechanism: the benchmark holds every coin every day, so its slices are always drifting
apart at full crypto volatility. The strategy's books are **flat roughly half the time**,
and a flat book contributes no drift. The benchmark should therefore turn over
substantially more — perhaps twice as much — and a cost charged to both should hurt it
faster.

If H2 holds, the correct reading is **not** "the cost does not matter". It is that the
strategy's edge over this particular benchmark is partly an edge in *turnover*, which is a
real and unglamorous source of advantage, while its absolute return still falls at every
tier. A strategy that wins by trading less is still winning, but it is winning something
different from what a breakout signal was supposed to deliver.

**What would falsify each:** H1, a full-span Sharpe at or above +1.00 at 40 bp. H2, an edge
that narrows as cost rises, or a break-even below 1000 bp.

**Track record:** mechanism-first predictions falsified four times, confirmed four times.
H1 predicts a cost and those have all held. H2 predicts a *relative* benefit via a cost
asymmetry, which is a new category here.

## What this cannot settle

A turnover charge is not a liquidity model. It says nothing about whether the required size
could be traded in these coins at all — the capacity question — and small-cap alts are
exactly where it could not. It also leaves D183's other two debts outstanding: the deflated
Sharpe against the 30-configuration pool that produced the baseline, and an out-of-sample
test on a cross-section this one does not contain.

---

# RESULT — appended 2026-08-22, after the run. Nothing above this line was edited.

**Status: H1 FALSIFIED. H2 FALSIFIED as stated, and confirmed in substance.**

**The rebalancing cost does not erase D183's edge. It barely touches it.**

## What was measured

| Book | Annual turnover | 0 bp | 10 bp | 25 bp | **40 bp** |
|---|---|---|---|---|---|
| **LONG portfolio (strategy)** | **1.8×** | +1.277 | +1.271 | +1.261 | **+1.252** |
| Equal-weight universe | **4.8×** | +1.196 | +1.191 | +1.182 | **+1.174** |
| BTC buy & hold | 0.0× | +1.096 | +1.096 | +1.096 | +1.096 |

**Strategy edge over the equal-weight universe: +0.081 → +0.080 → +0.079 → +0.078.**

**Break-even: 972 bp** — roughly **24× the reference tier**.

## H1 — FALSIFIED

Predicted the strategy's full-span Sharpe would fall below +1.00 at 40 bp. It falls from
**+1.277 to +1.252** — a loss of **0.025**, not the 0.28 the prediction required.

Turnover is far lower than I assumed: **1.8× a year**, which at 40 bp one-way is **0.72% a
year** in cost. Against a book with ~25% annual volatility that is worth about 0.03 of
Sharpe, and that is exactly what showed up.

## H2 — FALSIFIED as stated

Predicted the edge would **widen** with cost and that there would be **no** break-even. The
edge **narrows**, very slightly (+0.081 → +0.078), and a break-even exists at 972 bp.

**The turnover half of the reasoning was right.** The strategy turns over 1.8× against the
benchmark's 4.8× — the ~2.7× asymmetry predicted, and for the predicted reason: the
strategy's books are flat roughly half the time and a flat book's slice does not drift.

**The conclusion drawn from it was wrong, and the error is worth keeping.** I reasoned about
turnover and ignored the denominator. A cost's damage to a *Sharpe* is `cost ÷ volatility`,
not cost alone:

| | Annual cost at 40 bp | Annual vol (approx.) | Sharpe drag |
|---|---|---|---|
| Strategy | 0.72% | ~25% | 0.025 |
| Equal-weight universe | 1.92% | ~85% | 0.022 |

**The benchmark turns over 2.7× more and pays almost exactly the same Sharpe penalty,
because it is 3.4× more volatile.** Turnover and volatility scale together across these two
books, so the comparison is very nearly cost-invariant. That is not a coincidence of this
sample — a book that holds volatile things all the time both drifts more and has more
volatility to divide by.

**In RETURN terms the original intuition does hold.** The strategy gives up 7% of its total
return at 40 bp (+2,908% → +2,709%); the benchmark gives up 17% (+72,808% → +60,530%). The
cost asymmetry is real and it shows up where it is not divided by volatility.

## What this settles, and what it does not

**D183's edge survives the test D183 set for it.** The +0.081 like-for-like edge over a
daily-rebalanced equal-weight universe is essentially unchanged at every plausible cost, and
would need a **972 bp** one-way charge to disappear. The un-charged rebalancing cost was the
largest stated threat to that result, and it is now measured and small.

**The edge is still small.** +0.078 at the reference tier. Surviving a cost does not make it
large, and it remains the difference between +1.252 and +1.174 on a bull-dominated crypto
decade.

**Drawdown is untouched by the charge** — 28.8% → 29.3% — so the finding D183 called the
real one is unaffected.

**Two of D183's three debts remain outstanding.** The deflated Sharpe against the
30-configuration pool that produced the underlying baseline, and an out-of-sample test on a
cross-section this one does not contain. Only the rebalancing cost is now paid.

**And a turnover charge is not a liquidity model.** Nothing here says the required size
could be traded in these coins at all. At 1.8× annual turnover on a 62-coin equal-weight
book of small-cap alts, capacity is the next question and it is a harder one than cost.

## The methodological note worth keeping

**I predicted the mechanism correctly and the outcome wrongly, for the second time in this
project.** D178 identified re-entry as a real effect and mis-ranked it; here the turnover
asymmetry is real, measured, and almost exactly as large as predicted — and it produces
none of the consequence predicted, because the quantity it feeds into has a denominator I
did not think about.

The general form: **a correct mechanism plus the wrong normalisation is a wrong
prediction.** Sharpe is a ratio, and reasoning about its numerator alone will keep producing
confident, well-argued, wrong answers.

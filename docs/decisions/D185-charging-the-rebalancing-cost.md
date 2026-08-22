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

# D196 — Trading the terrain levels, against the same strategy on random levels

**Status:** Pre-registered — written and committed BEFORE the run, with a disclosure
**Date:** 2026-08-23
**Category:** Validation & research integrity
**Source:** S5/S5b (c641880, 62b6c38), and the observation that a strategy can read a score the null harness cannot

> A result section will be appended and nothing above it edited.

## A disclosure, first, because it changes how everything below should be read

**One cell was run before this document existed.** Sizing the grid required measuring a
cell, and D194's runtime estimate had been wrong by 6× precisely because I guessed instead
of measuring. So I measured — and in doing so saw a number.

What I saw: `touch_horizon` on BTC at S5's primary configuration produced a real Sharpe
essentially identical to its null mean, around the **48th percentile** of 500 draws, on
296 real trades against a null mean of 371. That was under a per-trade Sharpe which has
since been replaced by a curve-based one, so the exact figure will not reproduce; the
qualitative reading — one strategy, one symbol, indistinguishable from random — will.

I cannot un-see it, and writing predictions while pretending otherwise would make every
prediction here worthless. So it is stated, and the predictions below are written knowing
it. This follows D144's precedent: an amendment made after seeing data, recorded with its
reason rather than folded in silently.

What the cell does **not** cover: `bounce_rr` under either fill assumption, ETH, S5b, or
the buy-and-hold hurdle. Those are genuinely unseen.

## Why a strategy test rather than the reaction harness

`terrain_nulls.py` measures whether price *behaves* differently at a sensor's levels —
three reaction statistics, **no costs**. This measures whether *trading* them beats
trading random levels, in money, after fees. Costs are what have killed nearly everything
in this project and the reaction test could never see them.

There is also a mechanical reason. S5b's decay lives in the level **score**, and
`run_null → sensor_levels → levels_at` returns prices — verified identical for S5 and S5b
on all 314 rebuild dates at both decay values. **The reaction harness cannot see S5b at
all.** A strategy can. Without this change of structure S5b is untestable.

## The null is the same strategy, not no strategy

Every arm runs identical rules, costs and sizing; only the level set differs, drawn by
`pseudo_levels`, which already matches count and span. Design choices therefore largely
cancel — a bad exit rule is a bad exit rule in both arms.

**What pairing does not cancel** is D189's H2 confound: real levels sit where price has
repeatedly been, random ones do not, so the real arm may find more entries near price
regardless of skill. Trade counts are reported per arm. Note the sizing cell showed the
real arm taking *fewer* trades than the null (296 vs 371), which is the opposite of what
H2 predicts — worth watching rather than concluding from.

## What is run

Three strategies, on S5 and S5b, BTC and ETH, daily 2015–2025.

| | entry | exit | new parameters |
|---|---|---|---|
| `touch_horizon` | close enters the band | `HORIZON` bars | **none** |
| `bounce_rr` | limit at the level | stop at far band edge, target 2R/3R, trail after 1R | target R only |
| `level_stop` | *deferred* — modifies an existing book's stop, so it belongs in the breakout harness, not here |

Everything else is inherited: `HORIZON`=5, `TRAIL_LOOKBACK`=10 (this is `trail_10`, the
incumbent D174 benchmarked `swing_k2` against), `MAX_HOLD`=60 as a backstop so a level
that never resolves cannot turn the test into buy-and-hold.

**Both fill assumptions run, and the pessimistic one carries the verdict** (D9): *"touch
!= fill and bar-level limit fills are adversely selected."* Adverse selection is the whole
risk for a bounce strategy — you are reliably filled on the levels price blows through.

**Intrabar ordering is pessimistic.** When a bar covers both stop and target, the stop is
taken. OHLC does not say which came first and resolving it favourably manufactures an edge.

Primary configuration, named now: **S5, k=2, cluster_atr=0.5, lookback 180 daily bars**,
decay 0.25 for S5b. Everything else is sensitivity.

## The bar

Two hurdles, both required, on the primary configuration, on **both** symbols:

1. **Beat the null by ≥ +0.10 Sharpe** over the null mean. Same floor and grounding as
   D195: D185 put the entire rebalancing machinery at 0.025 Sharpe and D183's portfolio
   edge was +0.075. Below +0.10 is inside the noise of effects this project has already
   shown it cannot resolve.
2. **Beat buy-and-hold** on Sharpe over the span actually traded. D188's lesson — the
   portfolio's edge had to be measured against a matched basket, not against zero. A
   strategy that beats random levels and loses to holding the asset has found nothing
   worth doing.

Sharpe is computed from the **per-bar equity curve**, marked to market while a position is
open, so it is comparable to buy-and-hold. A per-trade Sharpe annualised by trade
frequency would flatter a strategy that trades rarely — the exact defect the final report
records in the inverse-vol weighting.

## Multiplicity

2 sensors × 2 symbols × (`touch_horizon` + `bounce_rr` × 2 targets × 2 fills) = **40
cells**, each against 500 null draws. Its own ledger; this is a different hypothesis from
the terrain programme's 147 looks, though it uses the same sensor family.

## Predictions

**H1 — every strategy fails the null hurdle on at least one symbol.** Predicted **TRUE**,
high confidence. Partly informed by the disclosed cell, so it is worth less than the
others and is labelled accordingly.

**H2 — `bounce_rr` is materially worse under `TRADE_THROUGH` than under `TOUCH`.**
Predicted **TRUE**, high confidence, and this one is unseen. If the gap is large it is the
most useful output of the run: it prices the adverse selection D9 named, and it is a
number this project has never measured despite D9 existing since July.

**H3 — nothing beats buy-and-hold.** Predicted **TRUE**, high confidence. Crypto's drift
over 2015–2025 is the thing every long-only rule here has failed to beat.

**H4 — S5b is indistinguishable from S5.** Predicted **TRUE**, moderate confidence. Only
5–11% of level-observations are pierced at all, and only 15.2% of BTC rebuilds reorder. A
mechanism that touches a tenth of the map should not move a Sharpe, and if it does the
first suspicion should be noise rather than signal.

**The interesting failure mode**, stated in advance: if `bounce_rr` beats its null under
`TOUCH` and fails under `TRADE_THROUGH`, that is not a marginal result — it is the
strategy being profitable only on fills it would not have received.

## What a pass would and would not mean

It would mean these levels are tradeable in a way random levels are not, after costs, on
one asset class in one decade. It would **not** establish supply and demand as the
mechanism — `tests` scores a level by how often price returned to it, so a high-scoring
level is by construction a price the market revisits, and that confound is sharper in S5
than it was in S1.

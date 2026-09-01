# D211 — the structure programme is closed

**Status:** Committed
**Date:** 2026-08-24
**Category:** Validation & research integrity
**Source:** the stop condition D204 fixed, triggered by D210; WP6's audit confirms it

## The stop

> **The five components of `STRUCTURE_MODEL.md`, mechanised as it defines them, are closed
> on BTC/ETH 15m bars as a source of tradeable directional signal.** No further statistic,
> sizing rule, exit policy, threshold, bar size or symbol will be pre-registered on them.

Same form as D194's stop for S1 and D203's for the S6 map, and the same reason: the ladder
of refinements is infinite, and leaving it open makes "the last reading wasn't the right
one" an escape hatch that can be pulled forever.

## Why now rather than after one more reading

The pre-registration fixed it in advance: *"no component clearing the promotion criteria
ends the programme here as a reportable negative; WP5 does not run."* D210 is that
condition. The temptation to continue was real and specific — **three features cleared the
unconditional promotion bar on both symbols**, and a costed backtest of them would have
produced a number.

They were one quantity under three names, rank-correlated +0.79 to +0.88 with each other,
all reporting the arithmetic identity `MFE_R = excursion / risk`. Holding leg size constant,
every one of them collapsed to at most 0.13 with no sign agreement anywhere.

D203 is the record of what continuing looks like: five refinements, each better than its
predecessor, not one of them moving the null.

## WP6 confirms the verdict is not a property of one cell

The whole pre-registered grid — `k` in {2, 3} x touch band in {0.5, 1.0} ATR, both symbols,
8 cells:

- the largest rank correlation any feature reaches inside any stop-width quintile ranges
  **0.10 to 0.15**, against a bar of 0.2. Not one cell produces a promotable feature;
- **stacking the filters helps at zero cost in 0 of 8 cells**;
- the base arm's zero-cost mean R ranges **+0.013 to +0.093** — indistinguishable from zero
  everywhere.

H7 predicted at low confidence that the verdict would be stable across the grid. Confirmed,
with the caveat WP6 states about itself: **a verdict stable because the effect is zero is a
weaker demonstration than one stable while an effect is present.** This grid shows the
absence is robust; it cannot show that a presence would have been.

## The record

| | what was claimed | the verdict |
|---|---|---|
| C1 change of character | the trigger | fails the both-symbols rule; BTC at the 66th percentile of its rotation null, ETH negative |
| C2 the flipped level | support becomes resistance | negative against a matched placebo, both symbols, matched or not |
| C3 the golden ratio | 0.618 is special | ranks 4 of 8; loses to 0.691 and 0.724 in 97%+ of draws |
| C4 the fair value gap | price returns to the imbalance | 100th percentile unmatched, **+0.006 / −0.006** depth-matched |
| C5 RSI, the control | a supporting filter | beat all three structural components, then collapsed with them |

And three findings that stand whatever one thinks of the components: the course's 5R
break-even is 22.3–28.4% at 40 bps rather than the 20% it claims; 27–44% of base-arm trades
cost at least their whole risk to trade; and the confluence stack **raises** friction and is
**worse at zero cost** than no filters at all.

## What is not closed

The components are reusable and several are pinned by test: the BOS/CHoCH state machine with
D173's lag, the fair-value-gap detector, the R-unit excursion, and the two matched controls.

Nor is this a claim about price action as a concept, or about the course as practised by a
human. **The mechanised version is not the thing being taught.** A negative here does not
refute the course, and — the point that matters more — a positive would not have vindicated
it. What was tested is whether the claims survive being written down precisely enough for a
machine to find them.

## Ledger

**86 looks on one hypothesis**, never reset. WP0/WP1/WP2 contribute zero — a
pre-registration, a detector suite and a census are not tests. WP5 never ran.

Two post-hoc analyses are disclosed rather than folded in: the depth-matched null (D208) and
the stop-width control (D210). Both were designed after seeing a result, both are counted in
full, and both made the verdict harsher rather than kinder — which is worth stating because
it is the opposite of the failure mode post-hoc analysis is feared for.

Terrain's 259 looks are disclosed adjacent and separately counted. D204's pre-committed
inheritance rule — if the flipped level had been the only survivor, D196's 20 looks would
join this total — did not trigger, because the flipped level did not survive either.

---

## CROSS-SCREEN at futures cost, 2026-08-29 — [R12](../RULES.md#r12). The stop stands.

**Raised because [D206](D206-the-census-kills-the-courses-arithmetic-before-any-backtest.md)'s
headline is a COST statement** — *"a 40 bps round trip costs 0.40% of price; the median stop is
0.41%. The cost of trading is roughly the entire distance to the stop"* — **and the prop track's
cost is roughly two hundred times smaller.** R12 requires a cost-based closure to be re-costed
before it stands, and on its face this is the strongest such case in the repo.

**It does not stand, because the programme did not close on cost. It closed at ZERO cost:**

> **"the base arm's zero-cost mean R ranges +0.013 to +0.093 — indistinguishable from zero
> everywhere"**
> **"stacking the filters helps at ZERO COST in 0 of 8 cells"**

**The components were measured frictionless and had no signal.** Removing the cost wall removes an
objection that was never load-bearing for the verdict — D206's arithmetic killed the *course's*
claim about break-even hit rates, not the components.

**Nor is the timeframe the missing dimension.** The programme ran on **BTC/ETH 15-minute bars** —
already intraday.

**And the per-component record is worse than "no edge":**

| | |
|---|---|
| C1 change of character | 66th percentile of its own rotation null on BTC, negative on ETH |
| C2 the flipped level | **negative against a matched placebo**, both symbols |
| C4 the fair value gap | 100th percentile unmatched, **±0.006 depth-matched** |
| C5 **RSI, the control** | **beat all three structural components** |

**[D208](D208-one-variable-explains-the-whole-strategy.md) explains the lot: retracement depth is
the one variable, and the structure is a proxy for it.**

**The stop is UNCHANGED.** The only dimension a cross-screen could reopen is the cost wall, and the
verdict never rested on it. **Re-running this on futures would be the infinite-refinement ladder
D211 exists to stop**, and the one previous stop override in this repo — D214's — returned *"0 of 12
cells clear... best observed Sharpe −2.28."*

# D437 — shock-with-state, stage 1: the in-sample event study and the weighted book, against the atlas's own floors

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. This is
the **first look at forward returns** for the construction D436 stage 0 continued. **In-sample on
the mining fixture; no holdout is read.** D400–D436 used, D407–D410 and D390–D399 reserved.

## 1. The construction (D436, unchanged)

Events: a 3× volume bar (`rv_x3`) in a state at the close of `t−1`, placed at `t`, filled at `t`'s
open — D434's pools, D435's states, `[F]`-aligned. Four components with weights fixed in `7380bcf`:

| | event → side | weight | D435 cell p50 (the floor) | state's own p50 |
|---|---|---|---|---|
| A | shock in `mom_hi` → long | 0.40 | +38.4 | +23.1 |
| B | shock in `price_hi` → short | 0.25 | +50.3 (short) | +17.5 (short) |
| C | shock in `price_lo` → long | 0.15 | +32.4 | +19.2 |
| D | shock in `mom_lo` → short | 0.10 | +19.5 (short) | +9.0 (short) |

Held to a 20-bar cap, one position per name, next-open fill, market-hedged (the floored market,
as the atlas). E (`ret20_lo`) is a reported split of A and C, not a size. **A name-day in two
components is held once; the component *books* below are separate, so the weighted combination
realises "the sum of the weights" for A&C and B&D exactly.**

## 2. The kernel, the costs, the books

**Kernel:** `d345_event_book.simulate_event` through `run_d359`'s wrappers — the same kernel that
produced every D435 cell, so the floors and the study are one path (`[K]`: `score_once` on a
2,000-event probe equals `run_d359`'s path to 0.0).

**Per trade:** `run_d359.trade_block` — gross bp per trade (hedged), **2c under PUB (primary) and
PB**, IBKR commission, **D337's `gc_htb` borrow on the short components**, net = gross − 2c −
borrow. Both conventions printed; the bar reads PUB.

**Books:** each component's own book (every event, cap 20, hedged series on); the **weighted book**
= Σ wₖ · (component k's daily hedged deployed return) / Σ wₖ, with the cost line built the same
way from the components' deployed cost lines (`deployed_block`, 2-crossing, PUB). Reported beside
it: the **combined 150-slot two-sided book** (union of events, `n_max = 150`, equal weight,
first-come — the kernel carries no priority), with 100 and 250 as shape.

## 3. Nulls — every one declared here, none chosen after

1. **`[P2]` the floors:** each component's per-trade gross must equal its D435 cell's p50 within
   the cell's draw sd (the component *is* the pool; this is a reproduction, and it is asserted).
2. **State-matched random-event books** (the shock's increment): for each component, 100 draws of
   random eligible cells from the *same state* with the *same daily count* as the component's
   events, run through the same kernel; the weighted combination of those draws is the control
   for the weighted book. This is D435's cell in book form and it is what separates "a volume
   shock in this state" from "this state".
3. **Time rotation:** each name's event series rolled by its own random offset (100 draws), the
   weighted book recomputed — do *these* days matter.
4. **Calendar null:** events whose spacing from the name's previous shock is 58–68 sessions
   (the earnings quarter, 15.4% of spacings in stage 0) against the rest — per-trade gross, both
   sides, and the weighted book on the non-quarterly events alone.

## 4. The bar — the weighted book

- **T1** `[P2]` holds for all four components.
- **T2** the weighted book's **net** (PUB, commission, borrow) per bar > 0 by 2 SE (monthly block
  bootstrap of the daily net series).
- **T3** the weighted book's **gross** above the p95 of the state-matched random-event books
  (D373's margin).
- **T4** the non-quarterly events' per-trade gross > 0 by 2 SE **and** the weighted book on them
  alone above its state-matched p95 — the effect is not only earnings.
- **T5** the weighted book's gross above the p95 of the time-rotation null.

**T1–T5 → a candidate for the holdout reads (holdout 1, then holdout 2, once each, both unseen
by this line).** T3 failing with T2 passing = the book is the states' momentum and price base
rates with a volume timer that adds nothing — a named outcome, read as written.

## 5. Predictions (computed from D435 and D436; MODERATE — the per-trade numbers are
reproductions, the book and the nulls are new)

- **X-a** per-trade gross: A **+38 ± 3**, B **+50 ± 3**, C **+32 ± 3**, D **+19 ± 3** (the
  cells); weighted **+38 to +40**. `[P2]` holds.
- **X-b** 2c under PUB **28 to 40 bp** per trade (the states are mixed: high-priced names cheap
  to trade, cheap names dear), PB 15–25; borrow on B and D **2 to 8 bp**; weighted **net +0 to
  +12** per trade under PUB. T2 is a coin — declared.
- **X-c** the state-matched random-event books' weighted gross **+18 to +24** per trade (the
  states' own base rates at the weights); the shock's increment **+14 to +22**; T3 passes.
- **X-d** quarterly events (≈15%) gross **+20 to +40 higher** than the rest; the rest still
  positive at 2 SE and above their state-matched floor; T4 passes.
- **X-e** the rotation null's p95 sits **below +10**; T5 passes.
- **X-f** the 150-slot combined book: utilisation **85–95%**, gross per bar per position **+1.5
  to +2.2**, net under PUB **inside ±0.5 of zero** — the equal-weight union is the weighted book
  without its weights, and about as good.
- **X-g** E: A and C events with `ret20_lo` gross **+10 to +20 above** those without.

X-b is the study — whether a base rate that clears cost on paper clears it under the repo's
own cost model; X-c is the principal's hypothesis from D435 made a book.

## 6. Not in scope

Any holdout; any change to the weights or events; exits; sizing beyond equal weight; the 15m
fixtures. Thirty-seventh look by object; the first forward-return look at this construction.

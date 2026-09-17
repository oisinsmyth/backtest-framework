# D424 — stop loss, trailing stop and take profit, each alone, on the second-zone cell, both lenses

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D424-stop-loss-trailing-stop-and-take-profit-alone-on-the-second-zone-cell-both-lenses.md`. The H1 above is the full title.*

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. D400–D423
used, D407–D410 and D390–D399 reserved. **No holdout.** Daily bars only.

## 1. The question

The principal asks whether D417's three ATR-multiple exits — a stop loss, a trailing stop, a take
profit — **each on its own, with no other stop**, improve the best cell this line has:
**STACK2-ANY ∧ cell 2** (9,411 trades, gross +44.84, net +16.04; the cell-2 ANY-REQUIRED 10-slot
book, net +0.99/+1.51/+1.20 by seed). D417 ran these on the base cell 2 (26,024) and D419 through
a full-pool book; D423 ran structure levels on this cell. None has run ATR multiples on this cell.

## 2. What is fixed, and the prior in numbers

Entry at the touch-day close, five-session clock kept (these are early exits inside it), D413's
neutral cost, D417's walker unchanged (`RULES`: SL 1.0/1.5/2.5, TS 1.0/1.5/2.5, TP 1.0/2.0/3.0,
SL+TP 1.5/2.0), D419's simulator unchanged with the ANY-REQUIRED cell-2 pool. `[X]`: D417's
`daily_arm` on this event table reproduces D417's cell-2 table for `TP 2.0` (+32.43, +2.17,
22.1%) before the cell is restricted; `[P2]`: D419's `FIXED` on the pool reproduces D422's
ANY-REQ book bit-identically.

```
D417, base cell 2 (26,024)   PAIRED    SE    early   would-have   filled-at
SL 1.5                       -10.84   -6.2   31.2%    -439.04     -473.8
TS 1.5                       -13.10   -6.0   58.6%    -181.52     -203.9
TP 2.0                        +2.17   +1.7   22.1%    +617.19     +627.0
D423, this cell: SWING (3.2 ATR)  -3.03, early 10.7%, forfeit -28 -- the reachers keep running
D423, this book: every early exit lowered utilisation; the pool is 2.25 events/day for 10 slots
```

## 3. The bar — TP 2.0 is the primary (R14: the only family with a positive prior)

- **T1** paired delta `TP 2.0 − FIXED` on ANY ∧ cell 2 exceeds zero by 2 SE (paired SE).
- **T2** on the cell-2 ANY-REQUIRED 10-slot book, three seeds, `TP` net minus `FIXED` net exceeds
  zero by 2 SE (monthly block bootstrap) **and** the `TP` book's net exceeds the p95 of D419's
  sampled-runs control (200 draws, D373's margin).

SL 1.5 and TS 1.5 run through the same two tests and are reported, not gated; the sweep is shape.
Reported beside: long/short, 2018+, pooled ANY and cell 2 all; the forfeit decomposition; the
replacement premium; utilisation.

## 4. Predictions (LOW confidence; the arithmetic is D417 × D423's forfeit scaling)

- **X-a** TP 2.0 delta on the cell **−4 to +3 bp**, inside 2 SE; fires **18–26%**; the forfeit
  is **negative, −5 to −20** — D417's +10 on the base cell turns negative here because this
  cell's reachers keep running (D423: −28 at 3.2 ATR). T1 fails.
- **X-b** SL 1.5 delta **−8 to −18**, fires 28–36%; TS 1.5 delta **−10 to −20**, fires 55–65%.
- **X-c** TP 1.0 has the highest win rate (>58%) and a delta inside 2 SE of zero — D417's shape.
- **X-d** the TP book: gross delta **−0.5 to +0.3**, utilisation below FIXED's 68.2%, net delta
  inside 2 SE of zero; above its control's median, below its p95. T2 fails.
- **X-e** the SL and TS books net-negative deltas by more than 2 SE.

## 5. Not in scope

No holdout, no 15m, no change to entry, hold, cost or cell, no disposition. Twenty-fourth look by
object; twenty-three of twenty-three before it failed their bar.

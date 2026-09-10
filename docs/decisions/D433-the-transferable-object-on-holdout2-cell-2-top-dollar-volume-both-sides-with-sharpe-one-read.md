# D433 — the transferable object on `holdout2`: cell 2 ∧ top dollar-volume tercile, both sides, `t+5`, with Sharpe — one read

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. D400–D432
used, D407–D410 and D390–D399 reserved. Daily bars.

## 1. The decision this executes

**The principal has chosen to spend `data/fixtures/us_shorts_daily_holdout2.csv.gz` on this line.**
It is the last data this line has not seen: 576 names (32.6% dead), the same 2010–2026 span, the
same pre-live screen, disjoint from both the universe and holdout 1. One read; then it is spent
for this line. The door is D430's ADDENDUM: one hook-free opener writes a cache named without
"holdout"; the runner reads the cache and never opens the fixture.

**The object is the one D430–D432 left standing** — the only construction whose per-trade gross
reproduced on 803 unseen names — and it is being sent to a third name set to be measured, not
because it is expected to clear cost: on holdout 1 it netted −3.5.

## 2. The construction — frozen

```
entry     D413 distance-armed departure zone, BOTH sides, touch-day close in, t+5 close out, no stop/target/trail
cell 2    REV <= -0.02473244344202641   EFF > 0.23669449533835638   DV > 44370158.19015902
tercile   trailing ADV (D.X.roll_mean_T(CL*VOL) at the touch) >= $186.6M -- D432's union top-tercile cut, frozen
          (the exact cut is data/d432_mechanisms.json m2.cuts[1]; the runner asserts it)
cost      neutral Corwin-Schultz + IBKR; 1%/yr borrow on the short half (primary), 10% reported
book      10 slots (D432's), three seeds; N in {5, 20} as shape
nothing else: no second-touch rung, no price cut, no side restriction, no gap, no priority, no gate
```

Scaled expectation (576/2,376 of the union's 12,947): **~3,100 top-tercile events**, ~9,400 cell-2
events, ~66,000 touches. Printed first, carried whatever they are.

## 3. Sharpe, defined

For a book: the daily **net** series in bp per slot (the book's return on fully-committed capital
of N slots; an idle slot earns zero), annualised **Sharpe = mean / sd × √252**, computed on the
book's live days (from `d0`); the **gross** Sharpe beside it; a **monthly block-bootstrap SE** on
the Sharpe (1,000 resamples of months). Per trade: mean / sd of the trade returns, unannualised,
reported for what it is. The same statistics are computed on the in-sample and holdout-1 halves
**from their caches in the same run** so the `holdout2` number has its two references beside it;
that reads nothing new.

## 4. What the single read computes

The **ladder** on `holdout2` (all touches → cell 2 → top-DV tercile; and, for the record, the
dead layers: second touch, cheap, long, short — reported, not gated, as a second name-disjoint
check of D430's transfer conclusion); D422's trade table on the object on pooled, 2018+,
2021–2026, by side; concentration with the top trade named; the |r| > 50% variant; per year;
**the book** at N = 10 (and 5, 20), three seeds, with net and gross Sharpe and their SEs; the
matched-count random cell-2 pool control at N = 10 from `holdout2`'s own cell 2 (100 draws);
the within-day permutation null on the tercile's premium over the rest of `holdout2`'s cell 2.

## 5. The bar — the object on `holdout2`

- **T1** per-trade gross > 0 by 2 SE (n ≈ 3,100, SE ≈ 11 → needs ~+22; the union gross is +32,
  holdout 1's +21: a coin, declared).
- **T1b** per-trade net > 0 at 1% borrow.
- **T2** the 10-slot book's net > 0 by 2 SE (block bootstrap, three seeds).
- **T3** the book's **net Sharpe > 0 by 2 bootstrap SE**.
- **T4** the book above the p95 of its random cell-2 pool control.

**All five → a tradeable indicator by the principal's rule, on the third name set.** T1 without
T1b = the touch effect is real on a third name set and still not a trade. Two named partial
outcomes are enough; anything else is read as written.

## 6. Predictions (MODERATE; two name sets already say what this object is)

- **X-a** counts within ±20% of §2; tercile events 2,500–3,700.
- **X-b** the object: gross **+18 to +32**, net **−8 to +6** at 1%, **−15 to 0** at 10%;
  median +10 to +25; win 51–53%; T1 a coin, T1b more likely to fail than pass.
- **X-c** the ladder's dead layers stay dead on a third name set: second touch inside ±15 of the
  cell-2 mean; the long cheap second-touch pool inside 2 SE of zero or negative; the short pool
  positive with a median far below its mean.
- **X-d** the 10-slot book: net **−1.5 to +1.0** bp/bar; **net Sharpe −0.4 to +0.4**, gross
  Sharpe **+0.6 to +1.6**; the book above its random control's median and below its p95.
- **X-e** the in-sample reference: net Sharpe of the same book **+0 to +0.5**; holdout 1: **−0.5
  to +0.2**. The three name sets agree on gross and disagree on the sign of net.
- **X-f** 2021–2026 above pooled on gross (the late concentration is in the base effect too).

## 7. Not in scope

Any threshold not frozen above; any layer; exits; a second read; disposition. Thirty-third look
by object; the second out of sample, and the last data this line has.

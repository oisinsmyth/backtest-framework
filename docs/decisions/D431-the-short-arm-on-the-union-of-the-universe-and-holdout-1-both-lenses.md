# D431 — the short arm on the union of the universe and holdout 1, both lenses

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. D400–D430
used, D407–D410 and D390–D399 reserved. Daily bars.

## 1. What this is, said so it cannot be over-read

**Both fixtures are spent for this line.** `us_shorts_daily_raw` (1,573 names) is where D412–D429
were built; `us_shorts_daily_holdout` (803 names) was read once in D430. Their union — 2,376
names, 2010–2026 — is in-sample from here on. **A pass here is in-sample evidence and cannot make
a candidate.** The only unseen data left is `holdout2`, which is not touched.

**The arm is chosen on the holdout's own result.** D430's ladder showed the long half of the
cheap second-touch pool inverting on new names (−29) while the short half held (+58 against +90
in-sample). Choosing the short arm now is selecting on the holdout; its +58 is therefore part of
the evidence for the arm, not a test of it. Said here, carried into the result.

## 2. The construction — D428's pool, short side, on the union

```
zones     D413, frozen (THETA 1.0, LIFE 60, H 5, DELTA 1.0); touch-day close in, t+5 close out, no stop
cell 2    the frozen in-sample cuts (REV <= -0.02473244344202641, EFF > 0.23669449533835638, DV > 44370158.19015902)
rung      STACK2-ANY (D422's counter);  price < 38.50639133333333;  gap 3-20
side      SHORT only (supply zones).  The LONG arm reported beside it for symmetry.
priority  opposite-side prior 3-10 back, short -- reported; a priority did nothing in D428/D429
cost      neutral Corwin-Schultz + IBKR + borrow on every trade: 1%/yr PRIMARY, 10%/yr reported (cheap names are where hard-to-borrow lives)
union     each fixture through the parametrised pipeline from its own cached panel; events pooled on a union calendar;
          name indices offset so the book's one-per-name rule never confuses an in-sample name with a holdout name
slots     N = 3 PRIMARY -- expected 0.43 events/day, occupancy ~2.1, occupancy/N 0.7;  N in {2, 4, 5} as shape
seeds     419, 4190, 41900
```

**Stage 0, from numbers already on record (D428 §2, D430 §2):** in-sample short pool 1,233,
holdout short pool 550 → **union 1,783**; long 1,416 + 667 = 2,083; the whole cheap second-touch
pool 2,649 + 1,217 = 3,866. The runner prints the actual union counts first and asserts the two
halves reproduce D428's and D430's counts exactly.

## 3. Measured

**Per trade:** D422's table on the union short pool — pooled, 2018+, 2021–2026 — and on each
fixture's half separately; net at 1% and 10% borrow; the trim, ex-top, ex-bottom, **top-1% share
of P&L** (the short half has been tail-carried in every table so far); the priority sub-cell; the
|r| > 50% variant; concentration with the top trade named and its bars; per year. The long arm on
the union, for symmetry. **The ladder on the union**, both sides, so the base effect's union
number is on record beside D430's.

**The book:** `sim4` at N ∈ {2, 3, 4, 5}, three seeds, with and without the priority, at 1% and
10% borrow; block-bootstrap SE on the three windows; `[P2]` the union simulator on the in-sample
half alone reproduces D428's `PRIO-b10`/`PRIO` books... **no** — D428's books were the *long*
arm and the full pool; the reproduction is of D428's **full-pool** N=3 book on the in-sample half
(pool = both sides), bit-identical, and of D430's N=2 long book on the holdout half.

**Controls at N = 3:** matched-count random pools of the union's cell-2 **short** events, one per
name, no priority, 100 draws (one worker measured first); D422's within-day permutation on the
short pool's premium over the union's other cell-2 short events, 200 draws.

## 4. The bar — N = 3, short, priority, 1% borrow

- **T1** per-trade gross > 0 by 2 SE on the union short pool (n ≈ 1,783; SE ≈ 17 → needs ~+35).
- **T1b** net > 0 at 1% **and** at 10% borrow.
- **T2** the N=3 book's net > 0 by 2 SE at 1% borrow (three seeds, monthly block bootstrap).
- **T3** the N=3 book above the p95 of the random short-pool control (D373's margin).

**All four hold → the short arm passes an in-sample bar on 2,376 names — which is all it can be.
It is not a candidate; a candidate would need `holdout2`, and this record does not open it.**

## 5. Predictions (MODERATE; both halves' per-trade numbers are already known)

- **X-a** union short pool 1,783 exactly; gross **+75 to +85** (1,233 × 89.7 + 550 × 58.4 over
  1,783 = +80.0), median **+10 to +20**, win 50–53%, payoff > 1.3; net **+40 to +50** at 1%,
  **+20 to +32** at 10%; the top 1% of trades **> 45% of P&L** — a lottery at a positive mean.
- **X-b** the permutation null passes (it is driven by the in-sample half).
- **X-c** the union ladder: all touches +9 to +11; cell 2 +24 to +28; second touch +25 to +35;
  the long union pool +40 to +50 (+80 and −29 weighted).
- **X-d** the N=3 short book **+3 to +5** net/bar at 1%, **+1.5 to +3.5** at 10%, positive on
  every seed; utilisation 45–60%; T3 passes; the priority inside its noise.
- **X-e** 2018+ and 2021–2026 below pooled on the union (the holdout's short half was weakest
  late); at least one of the two negative on the holdout half alone.
- **X-f** the holdout half of the short pool alone: gross +58.4 (known), book at N=2 on that
  half inside ±2 of zero.

## 6. Not in scope

`holdout2`; any change to thresholds, hold, exits or the cut; the long arm as a bar; disposition.
Thirty-first look by object; the union is spent data.

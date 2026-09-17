# D423 RESULT — the first bounce is not resistance: every structure exit forfeits, and the swing target is exactly its distance

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D423-RESULT-the-first-bounce-is-not-resistance-every-structure-exit-forfeits-and-the-target-is-its-distance.md`. The H1 above is the full title.*

**FAILS THE BAR on T1, T2 and T3.** Pre-registration `cb0d0a8` predates the runner and this file
(R8). **The ledger does not move. Nothing was admitted. No holdout was read.** Daily bars only.

Cost: 379 s (15 books in 3 s; 200 control books on 8 processes; 400 null walks).

```
[SIGN]  long swing, short LOG mirror, wick-vs-close through FAR, limit-before-close, no levels ==
        time stop -- and the check fires when FAR is moved below the path
[X]     the level walker given E +- 2 ATR == D417's TP 2.0 exit bar, fill and early flag, all 180,050
[BASIS] the no-level walk == r_base to 0.0
[P2]    no levels == D422's ANY-REQ FIXED book; E +- 2 ATR == D419's TP book -- both bit-identical
[RECON] all 15 books;  [CHUNK] worker draw 0 == in-process;  [NUISANCE] control run 4.786 vs SWING 4.792
```

The first `[SIGN]` fired on my test, not the walker: I had written the short's mirror in *price*
(96) where the log mirror of +4% is 100/1.04. Fixed in the test.

---

## 1. The bar — SWING on ANY ∧ cell 2 (9,411)

```
T1  paired delta vs FIXED            -3.03 ± 1.57 bp     -1.9 SE    FAIL
T2  vs distance-permutation null     observed -3.03   null p5 -4.20  p50 -2.86  p95 -1.48 (±0.06)   -26.3 SE   FAIL
T3  book net delta vs FIXED          -0.322 ± 0.296 bp/bar   -1.1 SE
    book net vs sampled-runs ctrl    +0.914  vs  p50 +0.804  p95 +1.355 (±0.021)   -21.1 SE   FAIL
```

**Every structure exit is negative on the primary cell, and the swing sits at the median of its
own distance null.** Permute which event gets which swing distance — keep the distances, destroy
the alignment with this event's structure — and the null is *centred* on −2.86 with the observed at
−3.03. **The first bounce's high is worth exactly what a target at 3.2 ATR is worth. D418 found
the zone's edge knows nothing beyond its distance as a stop; this is the same fact as a target.**

---

## 2. THE MECHANISM — the trades that reach the swing keep going

```
                              PAIRED     SE     early   would-have   filled-at   forfeit
SWING      ANY & cell 2       -3.03   -1.9    10.7%     +758.28     +729.97     -28.31
OPP        ANY & cell 2       -5.49   -2.1    22.7%     +308.86     +284.63     -24.23
BREACH     ANY & cell 2       -6.61   -2.8    27.4%     -397.23     -421.40     -24.17
SWING+BR   ANY & cell 2       -9.86   -3.5    37.7%      -76.57     -102.73     -26.16
```

**D417's target forfeited nothing (+5 bp after TP 2.0). The swing forfeits 28.** X-c extrapolated
one fact about one distance to a different distance and was wrong by the amount that matters:
a trade that travels 3.2 ATR inside five sessions is the cell's strongest trade, and it does not
stop at the last bounce's high — **it goes through it by 28 bp more before `t+5`.** That is the
answer to the principal's question in one number: **on the second zone, the first bounce's high is
not resistance. It is where the trend resumes.** The tested opposite-side level (OPP) forfeits the
same 24 bp on the 23% that reach it; the breach forfeits 24 bp of recovery on the 27% it cuts,
exactly D417's stop mechanism with a close-only trigger, and worse in the second half (−11.13,
−3.6 SE). Combined, the two structures forfeit on 38% of trades for −9.86.

**Long and short do not differ in sign** — SWING long −1.70, short −4.62; BREACH long −8.08,
short −4.85 — so D422's shape difference between the sides does not rescue an exit on either.

Pooled ANY and cell 2 all: SWING +0.28 and −0.11, OPP −0.72 and +0.94, all inside 1 SE — **on the
wider populations the structures are noise; on the cell that pays, they cost.** The better the
trades, the more an early exit forfeits.

---

## 3. THE BOOK — the target cannot recycle on a thin pool

```
cell-2 ANY-REQUIRED, 10 slots      gross     net     cost    util    run    early   per trade   net by seed
FIXED                             +4.889  +0.993   3.896   68.2%   5.00    0.0%    +35.85     +0.99 +1.51 +1.20
SWING                             +4.817  +0.819   3.998   66.9%   4.79   11.2%    +34.49     +0.82 +0.98 +0.95
OPP                               +4.373  +0.206   4.168   62.9%   4.34   22.0%    +30.17     +0.21 +0.11 +0.58
BREACH                            +4.444  +0.155   4.289   64.6%   4.33   23.0%    +29.80     +0.16 +0.14 -0.01
SWING+BREACH                      +4.034  -0.342   4.376   63.1%   4.13   33.7%    +26.42     -0.34 +0.17 +0.00

deltas vs FIXED (3 seeds, monthly block bootstrap)   gross     NET
SWING                                                -0.228   -0.322 ± 0.296   -1.1 SE
OPP                                                  -0.686   -0.939 ± 0.512   -1.8 SE
BREACH                                               -0.762   -1.142 ± 0.417   -2.7 SE
SWING+BREACH                                         -0.825   -1.293 ± 0.511   -2.5 SE
```

**Every exit lowers gross AND utilisation.** D419's mechanism — a freed slot refilled at once
with a fresh front-loaded entry — had its precondition on a full pool (99.9% same-day refill). The
ANY-REQUIRED pool is 2.25 events a day against ten slots: a slot freed early *idles* (utilisation
68.2% → 66.9%), so the swap premium (+35 ± 37 on 479 swaps, noise) never accrues at the book level
and the forfeit does. **On a required book, an early exit is a cost twice: the forfeit, and the
empty slot.**

The sampled-runs control says what D419's said: SWING (+0.914) sits above random exits at the same
turnover (p50 +0.804, +0.11) and far below the p95 — the target carries a little information about
*which* trade to leave and not enough to pay for leaving. And the control's median is itself
0.19 below FIXED: **random early exits cost this book; informed ones cost slightly less.**

---

## 4. Predictions — three of seven

| | prediction | outcome |
|---|---|---|
| X-a | SWING 0..+4, inside 2 SE | **half** — inside 2 SE, but −3.03, below the range |
| X-b | fires 8–16% | correct, 10.7% |
| **X-c** | give-back after the swing −5..+5 | **wrong — −28.31; the reachers keep running** |
| X-d | BREACH −5..−12, fires 25–35% | correct, −6.61, 27.4% |
| X-e | OPP inside 2 SE, fires 25–35% | wrong — −2.1 SE, 22.7% |
| **X-f** | SWING inside 2 SE of its null p95 | **wrong on the gate, right on the claim** — 26 SE *below* p95, at the null's median: structure = distance |
| X-g | book gross Δ 0..+0.5, net inside 2 SE, above ctrl median, below p95 | mostly — gross Δ −0.23 (wrong sign), the rest as stated |

X-c is the lesson: D417's "the target forfeits nothing" was a fact about a 2-ATR target on the
base cell, and I carried it to a 3.2-ATR target on the best cell as if it were a fact about
targets. **The forfeit scales with the distance because the trades that reach a far level are
the ones still moving.**

---

## 5. What this leaves

1. **The `t+5` clock with no exit remains the best exit found, now against ATR multiples (D417),
   the zone as a stop (D418), the target through the book (D419), and three structures through
   both lenses (this).** Six exit constructions; none beats it; the reason is the same each
   time — inside the hold the expected remaining move is positive in every state, including
   *at the prior high*.
2. **"Structure knows nothing beyond its distance" now holds on both ends of the trade.**
3. **On a thin required pool the book cannot recycle**, which removes the one mechanism (D419's
   swap premium) by which an early exit could have paid.
4. The entry rung (STACK2-ANY ∧ cell 2) is untouched by this: D422 §7 item 2 stands as the only
   pre-registration this line has earned.

**Disposition is the principal's.**

---

## 6. R13

Twenty-third look by object on price levels. No new data spent.

**Evidence:** `data/d423_structure_exits.json` (per-trade tables on six populations, both nulls,
15 books, the deltas, the premium ledgers, the control). Runner
`scripts/run_d423_structure_exits.py`; levels `scripts/d423_exit_levels.py`, committed with the
pre-registration.

# D433 RESULT — on a third name set the touch effect reproduces a third time, and nothing built on it clears cost: net Sharpe is zero on all three

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D433-RESULT-on-a-third-name-set-the-touch-effect-reproduces-a-third-time-and-nothing-built-on-it-clears-cost-net-sharpe-zero-on-all-three.md`. The H1 above is the full title.*

**FAILS: T1, T1b, T2, T3, T4 all fail.** Pre-registration `8d27f03` predates the runner and this
file (R8). **This was the one read of `us_shorts_daily_holdout2.csv.gz` for this line (SHA-256
`7e31c04642fb46a949e230cf536c6e62d9a13bbbe1418552c10b025bfa363364`); it is spent. Both holdouts
are now spent for this line; there is no unseen data left. The ledger does not move. Nothing was
admitted.**

Cost: 255 s from the opener's cache (opener 10 s); one worker measured at 944 MB. **Disclosed:**
the three reference books (§3) were run once in a dry check *before* the read to exercise the new
Sharpe code on spent caches; their numbers were therefore seen before `holdout2` was opened, and
X-d's gross-Sharpe range was already known to be too high. The record carries both.

```
[CUT]    the frozen tercile cut equals D432's artefact
[P2]     D432's top-DV cell-2 book reproduces on every seed
[COUNTS] 576 names; touches 67,416  cell 2 9,896  TOP-DV 3,281  (expected ~66,000 / ~9,400 / ~3,100)  -- within 5%
         holdout2's own cell-2 medians (not used): REV -0.02472  EFF 0.2348  DV $48.2M   vs frozen -0.02473 / 0.2367 / $44.4M
[RECON]  12 books;  [CHUNK]
```

---

## 1. The bar — the object on `holdout2`

```
T1   gross > 0 by 2 SE            +13.43 ± 10.41    +1.3 SE     FAIL
T1b  net > 0 at 1% borrow         -10.94  (10%: -19.04)          FAIL
T2   book net > 0 by 2 SE         -0.777 ± 0.767                 FAIL   (seeds -0.71 -0.79 -0.84)
T3   book net Sharpe > 0 by 2 SE  -0.19 ± 0.19   (gross +0.14)   FAIL
T4   book > random cell-2 p95     p50 -0.736  p95 +0.103 (±0.060)   -14.6 SE   FAIL   (the book IS the random median)
per-trade null: the tercile's premium over the rest of cell 2  -6.78 vs p95 +18.88   FAIL
```

---

## 2. Three name sets, one ladder

```
                          in-sample (1,573)   holdout 1 (803)   holdout 2 (576)
all touches                  +9.81               +10.09            +12.99
cell 2                      +30.26               +18.10            +17.96
top-DV tercile of cell 2    +37.90               +21.34            +13.43
second touch & cell 2       +44.84                +6.21            +17.14
+ cheap                     +86.48               +16.61            +27.54
long pool                   +79.93               -28.68            -21.03
short pool                  +89.71               +58.39            +53.97   (median +12 / +18 / 0)
```

**The departure-zone touch effect has now reproduced on three disjoint name sets: +9.8, +10.1,
+13.0 gross per touch, on 180k, 92k and 67k events.** It is the one durable fact in thirty-three
studies. Cell 2 halves the events and roughly doubles the mean on all three (+30 / +18 / +18). The
dollar-volume tercile, which added on the first two sets, **subtracts on the third** (+13 against
cell 2's +18; its within-day premium is −7 against a null p95 of +19) — the cost lever's gross
side was the spent names too. Above cell 2, the second touch is +45 / +6 / +17, cheap +86 / +17 /
+28, the long pool +80 / −29 / −21: **on both unseen name sets the long arm is negative, and on
both the short arm has a positive mean on a median of about zero.** D430's transfer conclusion
is confirmed by a second name set: what was layered on the base did not travel.

---

## 3. Sharpe — the number the principal asked for

```
top-DV cell 2, 10 slots, 1% borrow        net/bar         Sharpe net        Sharpe gross    daily sd    util
in-sample (1,573 names)                  +0.33 ± 1.28     +0.05 ± 0.21        +0.53          96 bp     57%
holdout 1 (803)                          -0.14 ± 0.99     -0.03 ± 0.22        +0.38          72 bp     36%
holdout 2 (576)                          -0.78 ± 0.77     -0.19 ± 0.19        +0.14          64 bp     28%
holdout 2, 2021-2026                     -1.84            -0.35
holdout 2 at 10% borrow                  -1.25 ± 0.77     -0.31 ± 0.19
holdout 2, N=5 / N=20                    -1.44 / -0.29    -0.25 / -0.13       +0.13 / +0.19
```

**Net Sharpe is zero to two decimals on the spent names and negative on both unseen sets.** Gross
Sharpe is +0.5, +0.4, +0.1 — a real mean of two to three basis points a day per slot against a
daily standard deviation of sixty to a hundred. That ratio is the shape of the whole line, and no
slot count changes it (N=20 has the smallest sd and the same sign). The ten-slot book on
`holdout2` sits at the median of random cell-2 pools of the same count; its per-trade gross of
+11 does not cover a 24 bp round trip on any of the three sets except, marginally, the first.

**Concentration on `holdout2`:** the object's P&L is 128 names with two to half of it; in 2018+
the total is negative and the top name (FTAI) and top year (2025) are larger than the whole,
which is what the ratios are saying. The top trade is MDB, short at 159.06 on 2020-03-05, covered
at 111.55 — the March 2020 crash, real, 8.1% of P&L on its own. By year the object is positive
11 of 17 and its second half is the worse half (2018+ gross −0.3; 2021–2026 −0.1).

---

## 4. Predictions — three and two halves of six

| | prediction | outcome |
|---|---|---|
| X-a | tercile events 2,500–3,700 | 3,281 ✓ |
| X-b | gross +18..+32, net −8..+6 | **+13.4 / −10.9 — below both; the tercile subtracted** |
| X-c | dead layers stay dead on a third set | ✓ all three parts (second touch ≈ cell 2; long −21; short median 0) |
| X-d | book net −1.5..+1.0; net Sharpe −0.4..+0.4; gross Sharpe +0.6..+1.6; above p50, below p95 | net ✓; net Sharpe ✓; **gross Sharpe +0.14 (and the references were already 0.4–0.5)**; at p50, not above |
| X-e | references net Sharpe 0..+0.5 / −0.5..+0.2 | ✓ |
| X-f | 2021–2026 gross above pooled | **−0.05 vs +13.4** |

The gross-Sharpe range was the miss with a lesson: I wrote "+0.6 to +1.6" from a gross of +3
bp/bar without computing the daily standard deviation, which the spent caches held. Computed, it
is ~100 bp, and the ratio is 0.5 before any holdout is read. Same error as D432's, smaller stakes.

---

## 5. What this leaves

1. **The line is at the end of its data.** Both holdouts are spent for it; the mining fixture and
   both holdouts have now each been read once by this construction, and there is nothing unseen
   left to test on. Any further study on these fixtures is in-sample on all 2,952 names.
2. **The durable fact:** a distance-armed departure-zone touch, held five sessions, earns +10 to
   +13 bp gross across three disjoint name sets; cell 2 makes that +18 to +30. **Nothing in
   thirty-three studies converted it into a trade at modelled cost**, and the modelled cost (24
   to 34 bp) has been checked against nothing but the OHLC.
3. **What did not travel, twice:** the second-touch rung, the price cut, long-only, the gap
   structure, the dollar-volume tercile's gross side, every exit, every gate. **The short arm's
   positive tail-carried mean travelled twice and is not bookable either time.**
4. **Net Sharpe of the best transferable object: +0.05, −0.03, −0.19.**
5. **The one lever this line never measured is execution** — passive fills at the zone against
   the crossed-spread cost model — and it is the only thing that could move a +13 gross / 24 cost
   object, because everything on the gross side has now been tried on three name sets.

**Disposition is the principal's.**

---

## 6. R13

Thirty-third look by object on price levels; **the second out-of-sample read, and the last data
this line had.** `us_shorts_daily_holdout2.csv.gz` is spent for this line.

**Evidence:** `data/d433_oos2.json`. Opener `scripts/d433_oos2_loader.py` (the only code that
touched the file); runner `scripts/run_d433_holdout2.py`.

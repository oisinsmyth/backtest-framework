# D437 RESULT — the volume timer adds to the state in-sample (+10 SE over state-matched events, +22 SE over rotated days), and the book cannot pay the repo's own spread

**NOT A CANDIDATE: T1, T3, T5 pass; T2 and T4 fail.** Pre-registration `ee0b72a` predates the
runner and this file (R8). **In-sample on the mining fixture; no holdout was read. Nothing is
admitted.** 9.0 min, one process.

```
[K]   the kernel probe equals run_d359's path to 0.0
[P2]  every component's per-trade gross lies within its D435 cell's draw sd of the cell's p50
```

---

## 1. The bar — the weighted book

```
T1  [P2] the floors reproduce                        PASS
T2  net (2c PUB + borrow) > 0 by 2 SE                -1.666 ± 0.462 bp/bar   -3.6 SE      FAIL
T3  gross > state-matched random-event p95           +1.540 vs p95 +1.302 (±0.024)   +10.1 SE   PASS
T4  non-quarterly events: every component > 2 SE and the book > its p95   A +3.5, B +3.5, C +2.0, D +1.3 SE; book +12.2 SE   FAIL (on D)
T5  gross > time-rotation p95                        +1.540 vs +0.795 (±0.033)   +22.5 SE   PASS
```

**The signal is real in-sample and the book is not a trade at the repo's cost model.** Both
halves of that sentence are the result.

---

## 2. Per trade — the shock adds to the state, and the spread takes twice what the shock adds

```
                       trades   gross   floor p50   median   2c PUB   2c PB   borrow   NET PUB   NET PB   state-matched p50   increment
A  mom_hi   long  .40  10,495   +36.8    +38.4       +6.2     61.6     40.8     0.0     -24.8     -4.0        +26.5            +10.3
B  price_hi short .25   9,851   +38.8    +50.3      +14.1     52.2     36.8     4.9     -18.3     -3.0        +16.2            +22.5
C  price_lo long  .15  11,836   +23.0    +32.4       +3.8     75.4     49.2     0.0     -52.4    -26.3        +19.5             +3.4
D  mom_lo   short .10  10,257   +18.7    +19.5      +11.9     66.0     42.9     4.8     -52.1    -29.0        +18.7              0.0
weighted                        +33.0                          61.7     41.3              -30.6    -8.3
```

**What the volume timer adds over a random event in the same state:** +10 in A, **+22 in B**, +3
in C, nothing in D. That is the content of D435's finding made a study, and it is confirmed by
the state-matched control at +10 SE and by the rotation null at +22 SE: these days matter, and
they matter beyond what the state alone gives. **D adds nothing** — the bottom-momentum short is
the state's own drift with a volume label on it — and C adds three basis points on the cheapest,
widest names in the universe.

**What the spread takes:** 52 to 75 bp per trade under PUB, 37 to 49 under PB. Both are the
studies' own numbers (`trade_block`, the cached Corwin–Schultz half-spreads of the names *held*),
and both are far above the 24–34 the zone line's neutral estimator had put on cell-2 names. D359
§1 had already said the loser decile's names cost **40 to 47 bp a side** under PUB; these are
those names. X-b predicted 28–40 for the round trip. **No component nets positive under either
convention; the best, B, is −3 under PB.** Deployed, every component's 2-crossing net is negative.

---

## 3. The books

```
weighted book (0.40/0.25/0.15/0.10)   gross +1.540 ± 0.462 /bar   cost 3.206   NET -1.666 ± 0.462   Sharpe net -0.85, gross +0.78
net by year: negative in 13 of 17; positive 2020 +0.6, 2021 +1.3, 2024 +0.4, 2026 +2.2
combined, equal weight, per-side slot cap:  150: 36,139 trades, 884 refused, gross +1.01, net2 -2.16, Sharpe -1.55
                                            100: 31,037, 7,196 refused, net2 -2.20;   250: 36,894, 0 refused, net2 -2.16
```

The weighted book earns 1.5 bp a bar gross — a gross Sharpe of +0.78 on a hedged book, which is
the best gross ratio this atlas-derived work has produced — and pays 3.2 to trade. The equal-
weight union earns 1.0 (the weights do something: the two components that add, A and B, get
0.65 of the capital). The slot cap is per side in this kernel (utilisation reads 117% of 150
because both sides count), so the book is ~175 positions at the median, and the cap does not
bind until 100 a side.

---

## 4. The calendar null — the longs' premium is NOT earnings; the shorts' partly is

```
                     quarterly (58-68 from the prior shock)      the rest
A  mom_hi   long     n 1,760   +1.4                              n 9,108   +42.7  (+3.5 SE)
B  price_hi short    n 1,721  +41.0                              n 8,459   +37.9  (+3.5 SE)
C  price_lo long     n 1,804   -3.1                              n 10,472  +26.0  (+2.0 SE)
D  mom_lo   short    n 1,763  +37.6                              n 8,894   +15.9  (+1.3 SE)
weighted book on the non-quarterly events alone: gross +1.693 vs its state-matched p95 +1.363   +12.2 SE
```

X-d predicted quarterly events +20 to +40 *above* the rest (post-earnings drift). **For the longs
it is the reverse:** a volume shock in a top-momentum name on its earnings cadence is worth
nothing (+1.4), and off the cadence it is worth +43. The long-side premium is the non-earnings
shock — the news run, the inclusion, the analyst day — and the earnings shock in a winner is
already priced. For the shorts the quarterly event *is* the drift (B +41, D +38): a high-priced
or losing name that shocks on its earnings keeps falling. T4 fails only on D's non-quarterly
t-stat (+1.3); the book on non-quarterly events beats its own control by 12 SE.

**E** (the 20-day-loser tilt) is worth +8 in A and **+18 in C** — the one place C has something.

---

## 5. Predictions — three of seven

| | prediction | outcome |
|---|---|---|
| X-a | per trade A +38, B +50, C +32, D +19 (±3); weighted +38..+40 | A +36.8 ✓, D +18.7 ✓; **B +38.8, C +23.0** (inside the cells' sd, outside ±3); weighted +33 |
| **X-b** | 2c PUB 28–40; net PUB 0..+12 | **PUB 61.7; net −30.6** — the cost model was misjudged by half |
| X-c | state-matched +18..+24; increment +14..+22; T3 passes | increments A +10, B +22, C +3, D 0; T3 ✓ |
| **X-d** | quarterly +20..+40 above the rest | **longs: −41, −29; shorts: +3, +22** |
| X-e | rotation p95 low; T5 passes | ✓ |
| X-f | 150-slot: net2 inside ±0.5 | −2.16 |
| X-g | E +10..+20 | A +8, C +18 ✓ |

Two misses matter. **X-b:** I carried the zone line's neutral-CS cost (24–34) into a construction
judged under the D345 kernel's PUB convention, which the D359 record had already put at 40–47 bp
a side for these names. That was readable before the pre-registration. **X-d:** the earnings
story was the natural one and the data say the longs' premium lives *off* the earnings cadence.

---

## 6. What this leaves

1. **In-sample, the volume shock carries information beyond its state and beyond its day** —
   +10 and +22 bp per trade over state-matched events in A and B, +10 SE and +22 SE against the
   two declared nulls. That is more than the zone line's second touch ever showed against a
   null that tested the right thing, and it is the first result in this line whose nulls were
   *state-matched* rather than universe-wide.
2. **At the repo's own cost model it is not a trade.** 2c PUB of 52–75 against a gross of
   +19 to +39; the weighted book −1.7 a bar, negative in 13 of 17 years. Under the looser PB
   convention the best component is −3. The gap is the spread of the names held, not the
   signal.
3. **The two components that carry it are A and B; C and D are their states.** A construction
   would be A + B, weights 0.6 / 0.4, and B's premium is partly earnings drift.
4. **The longs' premium is off-earnings and the shorts' is on-earnings** — a structural fact a
   stage-2 pre-registration would have to carry (a calendar-split book, both sides), and a
   reason the two sides may not be one strategy.
5. **The cost lever, again.** A +37 gross event in names whose round trip is 60 bp is a trade
   only under passive execution — the same unmeasured lever the zone line ended on.

**Not a candidate for the holdouts on the terms declared. Disposition is the principal's.**

---

## 7. R13

Thirty-seventh look by object; the first forward-return look at this construction; no holdout.

**Evidence:** `data/d437_stage1.json`. Runner `scripts/run_d437_stage1.py`.

# D418 RESULT — the zone knows nothing beyond its distance, and a close through it is not an invalidation

**FAILS THE BAR on all three questions.** Pre-registration `7f9902e` predates the runner and this
file (R8). **The ledger does not move. Nothing was admitted. No holdout was read (the principal's
standing decision).** D413's 180,050 / 26,024 reproduce exactly (P1).

Cost: twelve seconds.

---

## 1. The walker was not trusted, and then it was

A structure stop needs a walker that takes an explicit per-event *level* rather than D417's ATR
multiplier. Given `entry − 1.5·ATR` as its level, it **reproduces D417's `SL1.5` exit bar and price
bit-identically on all 180,050 events** (`[X]`), and `[SIGN]` asserted before any data that a valid
demand entry stopped at the edge loses where the fixed exit won, that a close through the edge is
invalid, and that the short mirror is exact — where the first version of that assertion expected
the short's stop at the zone's *lower* edge and the walker, correctly, put it at the top.

---

## 2. Stage 0 — where the close actually sits, and it is not where I said

```
                      entered      dropped      distance to stop, ATR (p10/50/90)
ST-edge   pooled      174,339       3.2%           0.80 / 1.59 / 2.67
ST-edge   cell 2       24,385       6.3%           0.64 / 1.47 / 2.52
ST-mid    pooled      162,089      10.0%           0.31 / 0.86 / 1.66
ST-buf    pooled      176,145       2.2%           1.02 / 1.83 / 2.91
```

**The touch-day close sits near the zone's NEAR edge.** The far edge is therefore a full
zone-width away — **1.59 ATR on the median event**, which is D412's zone width (1.59 ATR) and,
within a rounding, the distance D417 already tested. X-a predicted 0.8–1.2 ATR and X-b predicted
25–45% of closes already through the zone; **it is 1.59 ATR and 3.2%.** D414's "continuation
through the close" in cell 2 was 35 bp — a tenth of an ATR — which continues past the *touch
point*, not through the *zone*.

---

## 3. The bar — ST-edge, pooled

```
                                         paired delta      SE
T1  stop vs the fixed exit               -4.78 ± 0.74    -6.5     FAIL
T2  stop vs the distance-permuted control -0.30 ± 0.44    -0.7     FAIL
T3  entered vs dropped, fixed-exit return -10.74 ± 9.61   -1.1     FAIL

rule +8.09 bp   early 31.4%   std ×0.88   bp/day +1.91   win 45.2%
would-have (fixed) on the stopped trades  -401.31        filled-at  -416.55
D417's SL 1.5 on the SAME entered events  -4.51 bp, early 31.6%
```

### 3a. T2 is the answer to the question asked

**A stop at the zone's far edge does what a stop at the same distance placed anywhere does.** The
control permutes each event's ATR-unit distance across events — the distance distribution is
preserved to `0.0`, the link to the zone destroyed — and the paired difference is **−0.30 bp at
−0.7 SE.** The structure carries no information beyond how far away it is.

The mid-zone stop is *worse* than its distance control, **−2.86 at −5.7 SE**: the middle of the
zone is where the bounce is happening, and a stop there is a stop placed inside the move. The
buffer stop is +0.63 at +1.6 SE against its control — inside noise.

### 3b. T1 is D417 again, at the same distance

−4.78 against D417's −4.51 on the same events. The stopped trades would have finished at −401 and
the stop filled them at −417: **they recovered 15 bp after breaching the zone**, the same recovery
D417 found after a 1.5-ATR drop (16 bp). **The breach conditional does not make the expected
remaining move negative.** Conditional on price going through the level the trade was built on,
it still, on average, comes back a little — which is what D412 and D413's *later touches pay
more* already said about this construction's levels.

### 3c. T3 — the validity filter has the wrong sign, weakly

**The events whose close was already through the zone had a HIGHER fixed-exit return** — +23.62
against +12.87 for the entered ones — by 10.74 bp at **−1.1 SE**, on 5,711 dropped events. The
buffer variant, which drops the 2.2% that closed *decisively* through, sees +31.51 against +12.81
at −1.6 SE. In cell 2 the difference is +4.41 at +0.3 SE.

**Nothing here is significant, and it is stated that way.** But the direction is consistent across
variants and it is the opposite of the thesis: a close through the zone reads as a deep oversold
state that bounces, not as an invalidation. That is D416's late-stall population — the collapses
that came back — seen from the entry side. **X-e predicted the filter would clear; it did not, and
its point estimate runs the other way.**

---

## 4. Cell 2 — the declared secondary

```
                       vs fixed          vs control        filter (entered − dropped)
ST-edge      -12.09 ± 2.04 (-5.9)    -0.98 ± 1.31 (-0.7)     +4.41 ± 17.34 (+0.3)
ST-mid       -18.51 ± 2.70 (-6.9)    -1.63 ± 1.36 (-1.2)     -0.76 ± 10.37 (-0.1)
ST-buf        -9.44 ± 1.80 (-5.2)    +0.53 ± 1.10 (+0.5)     -5.56 ± 19.60 (-0.3)
```

The stop forfeits 40% of cell 2's edge for a 12% cut in standard deviation, the zone adds nothing
over its distance, and the filter is noise. The stopped trades in cell 2 recovered **35 bp** after
the breach — twice the pooled figure, as in D417 — because cell 2's bounce is stronger.

---

## 5. Predictions — two of six, and the four misses are all about the structure

| | prediction | outcome |
|---|---|---|
| **X-a** | median distance 0.8–1.2 ATR | **wrong — 1.59.** The close sits at the near edge, not inside |
| **X-b** | 25–45% dropped, more in cell 2 | **wrong on size — 3.2% / 6.3%**; right that cell 2 is higher |
| X-c | T1 fails | correct — −6.5 SE |
| X-d | T2 fails, inside 2 SE | correct — −0.7 SE |
| **X-e** | T3 passes — a close through the zone is the continuation | **wrong — the dropped events did better, at −1.1 SE** |
| **X-f** | cell 2 filter effect > 5 bp | **wrong** — +4.41 at +0.3 SE |

**Both correct predictions were "it fails". Everything I predicted about the structure itself —
where the close sits, how often it breaches, what a breach means — was wrong.** My picture had the
touch-day close deep in the zone or through it; it is at the near edge, and it almost never goes
through. That picture came from D414's intraday continuation, which is real and is a tenth of an
ATR, and I scaled it to a zone-width without checking.

---

## 6. What five execution studies have established

| question | answer | record |
|---|---|---|
| enter before the close? | no — −35 bp in cell 2 | D414 |
| enter on an intraday confirmation? | no — worse price than the clock | D415 |
| enter after the close, on a stall? | no — the bounce is front-loaded | D416 |
| exit early on a stop, trail or target? | no — the remaining move is never negative | D417 |
| **place the stop on the zone?** | **no — the zone knows nothing beyond its distance, and a close through it is not an invalidation** | **D418** |

**Entry at the touch-day close, exit at the close of `t+5`, no stop.** Five studies from five
sides; D413's trade as declared, untouched at either end. **The zone is the thing that says where
to enter. It has nothing to say about where to leave, and its breach is not the signal the thesis
says it is.**

**Disposition is the principal's.**

---

## 7. R13

Eighteenth look by object; fifth on execution; no new data spent.

**Evidence:** `data/d418_zone_stop.json` — every variant, pooled and cell 2, with the control, the
filter, the would-have/filled-at pair, and D417's stop on the same entered events. Runner
`scripts/run_d418_zone_stop.py`, whose walker is asserted bit-identical to D417's before it is used.

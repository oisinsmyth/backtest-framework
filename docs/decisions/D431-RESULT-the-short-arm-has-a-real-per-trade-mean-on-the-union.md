# D431 RESULT — the short arm has a real per-trade mean on the union, and a book cannot collect it, because the mean is a tail

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D431-RESULT-the-short-arm-has-a-real-per-trade-mean-on-the-union-and-a-book-cannot-collect-it-because-the-mean-is-a-tail.md`. The H1 above is the full title.*

**FAILS THE IN-SAMPLE BAR: T1 and T1b pass, T2 and T3 fail.** Pre-registration `7f2dd15` predates
the runner and this file (R8). **Both fixtures were already spent for this line; no fixture was
opened (both panels from their caches); `holdout2` untouched. The ledger does not move. Not a
candidate — the pre-registration said a pass here could not have been one either.**

Cost: 264 s; one worker measured at 995 MB.

```
[STAGE0] the halves reproduce D413/D428/D430's counts
[P2]     the union simulator reproduces D428's full-pool N=3 book on the in-sample half and D430's N=2 long book on the holdout half, every seed
[UNION]  2,376 names, 4,190 dates, 272,233 touches; short pool 1,783 (as predicted exactly), long 2,083, priority 202
[RECON]  39 books;  [CHUNK]
```

---

## 1. The bar — N = 3, short, priority, 1% borrow

```
T1   gross > 0 by 2 SE           +80.05 ± 16.14     +5.0 SE    PASS
T1b  net > 0 at 1% and 10%       +45.39 / +27.53               PASS
T2   book net > 0 by 2 SE        +1.543 ± 1.954     +0.8 SE    FAIL
T3   book > random short p95     p50 −0.652  p95 +1.890 (±0.160)   −2.2 SE   FAIL
```

**The per-trade lens says yes at 5 SE; the book lens says the book is a random draw of cell-2
shorts.** Both are the same fact seen from two sides, and the trade table says why.

---

## 2. Per trade — a large mean that lives in one trade in a hundred

```
                          n      gross   median   NET(1%)  NET(10%)   win    payoff   trim    ex-top1%   top-1% share of P&L
short pool             1,783    +80.05   +14.2    +45.4    +27.5    50.8%   1.38    +69.0    +47.4         41.4%
  in-sample half       1,233    +89.71   +12.2    +55.8    +37.9    50.4%   1.46    +75.9    +54.8         39.6%
  holdout half           550    +58.39   +17.8    +22.1     +4.3    51.6%   1.22    +53.8    +31.9         46.0%
  2018+                  929    +96.13   +14.2    +61.0    +43.1
  2021–2026              596   +106.43   +35.9    +69.3    +51.4
priority sub-cell        202   +119.53   +33.2    +81.7    +63.9    51.5%   1.65   +111.7    +97.7         19.1%
LONG pool (symmetry)   2,083    +45.15   +80.1    +10.0    +10.0    56.8%   0.92    +52.7    +18.9         58.6%

concentration          names   to half   top1   top5   top10   years+   top name   top year
short pool               457      12     8.9%  29.9%  46.4%   13/17     RVMD       2022  20.9%
short 2021–2026          246       5    20.1%  56.4%  83.7%    4/6      RVMD       2022  46.9%
```

**A median of +14 under a mean of +80: the short arm is the lottery D422 said it was**, on both
halves. The top 1% of trades — eighteen of them — are 41% of the P&L; removing them takes the
mean from +80 to +47, and the holdout half's from +58 to +32 (its top 1% is 46%). RVMD's +62%
(a real event, 19.3M shares on the gap day) is 4.3% of the whole pool's P&L on its own; in
2021–2026 five names are half the P&L and 2022 alone is 47%.

**The holdout half held its sign in every window** (+58 pooled, +78 in 2018+, +90 in 2021+),
which is what made the arm worth this look — and the pre-registration said that number is now
part of the evidence for the arm, not a test of it. X-e predicted the late windows below pooled;
they are above, on both halves. **The short arm's premium is late-concentrated like everything
else in this line, and unlike the long arm it did not invert on new names.**

**Cost is a third of the gross at 1% borrow and half at 10%.** Cheap short names are where
hard-to-borrow lives; the 10% figure is not the pessimistic case, it is the plausible one, and
at it the holdout half nets +4.

---

## 3. The book — every slot count positive on every seed, and none of them worth 2 SE

```
N   arm         gross    net    cost   util   trades  per trade   net by seed             pooled ± SE      2018+ ± SE      2021-26 ± SE
2   PRIO       +7.084  +3.482  3.601  49.5%    816     +71.55    +3.48 +2.54 +2.53    +2.85 ± 2.32    +4.16 ± 3.80    +5.51 ± 4.92
3   PRIO       +4.890  +1.846  3.043  43.0%  1,063     +56.87    +1.85 +1.71 +1.07    +1.54 ± 1.95    +2.19 ± 3.21    +2.98 ± 3.98
4   PRIO       +4.735  +2.176  2.558  36.9%  1,218     +64.08    +2.18 +2.06 +2.06    +2.10 ± 1.55    +2.97 ± 2.45    +3.13 ± 3.12
5   PRIO       +4.173  +1.982  2.191  31.9%  1,314     +65.44    +1.98 +2.05 +2.01    +2.01 ± 1.30    +2.86 ± 2.02    +3.17 ± 2.59
3   PRIO-b10   +4.890  +0.311  4.579  43.0%  1,063     +56.87    +0.31 +0.18 −0.47    +0.01 ± 1.96
2   HOLDOUT-HALF (N=2, the holdout's shorts alone)                 +0.15 +0.38 +0.20    +0.24 ± 1.50
random cell-2 SHORT pools of 1,783 at N=3:  p50 −0.652  p95 +1.890  -- the book is above the random median and below its p95
```

**The book's per-trade net at N = 3 is +57 and it nets +1.5 a bar**, because a three-slot book
takes 1,063 of the 1,783 trades in a random order, and whether it holds the eighteen trades that
are 41% of the P&L is a coin it flips once per seed: +1.85, +1.71, +1.07. The bootstrap SE of
1.95 is that coin. At 10% borrow the same book is +0.01. **The holdout half's shorts, booked
alone, are +0.24 ± 1.50 — nothing** — while their per-trade mean is +58. The priority sub-cell
is +120 per trade and the priority is worth −0.36 a bar: it promotes 202 events on a book that
is 57% empty.

**A tail-carried mean does not book.** D422 read the short side's shape and said "lottery"; D428
sized the book to a pool and found the same for shorts at 10% borrow; this is the same object at
2,376 names with the arm alone: the per-trade statistic passes any per-trade gate you set, and
the path-variant lens — the one that would have to hold the positions — cannot tell it from a
random draw of cell-2 shorts. **Both lenses were the point, and here they disagree in the way
that decides it.**

---

## 4. Predictions — three of six

| | prediction | outcome |
|---|---|---|
| X-a | n 1,783; gross +75..+85; median +10..+20; payoff > 1.3; net +40..+50 / +20..+32; top-1% > 45% | all as stated except the top-1% share at 41% |
| X-b | null passes | +9.0 SE ✓ |
| X-c | ladder +9..+11 / +24..+28 / +25..+35; long +40..+50 | +12.2 / +26.2 / +31.9 / +45.2 ✓ |
| **X-d** | book +3..+5 at 1%, +1.5..+3.5 at 10%, T3 passes | **+1.54; +0.01; T3 fails** |
| **X-e** | late windows below pooled; a negative on the holdout half | **above, on both halves** |
| X-f | holdout half +58.4; its N=2 book inside ±2 | ✓ / +0.24 ± 1.50 ✓ |

X-d is the miss that matters, and the reason is in §3: I predicted the book from the per-trade
mean × trades per bar, and the per-trade mean is not the number a slot-limited book earns from a
tail-carried pool — it earns the *median trade* plus whatever fraction of the tail its slots
happen to hold.

---

## 5. What this leaves

1. **The short arm has a real per-trade mean on 2,376 names (+80 gross, +45 net at 1% borrow,
   +5 SE), positive on the holdout half in every window** — and it is 41% one trade in a
   hundred, and a book of any size between two and five slots cannot collect it at 2 SE, nor
   beat a random draw of cell-2 shorts. At a plausible borrow it nets nothing.
2. **The union ladder is now on record:** touches +12.2, cell 2 +26.3, second touch +31.9,
   cheap +64.4, gap +61.3; short +80.1, long +45.2 (the long carrying its −29 holdout half). The
   base effect and cell 2 hold on 2,376 names; the second touch's +32 on the union is +6 on the
   holdout half alone (D430).
3. **Both lenses disagreeing is the finding.** A per-trade gate would admit this arm; the book
   says it is a lottery ticket with a positive expected value that a small book cannot buy enough
   of. Neither lens is wrong; the object is the kind that needs both.
4. **`holdout2` is unspent and nothing here is a reason to open it.**

**Disposition is the principal's.**

---

## 6. R13

Thirty-first look by object on price levels; spent data throughout. No new data spent.

**Evidence:** `data/d431_shorts_union.json`. Runner `scripts/run_d431_shorts_union.py`
(D430's parametrised pipeline on both cached panels; union on a common calendar).

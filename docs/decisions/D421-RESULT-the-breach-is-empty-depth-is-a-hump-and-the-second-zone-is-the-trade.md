# D421 RESULT — the breach above is empty, depth is a hump not a gradient, and the second zone is the trade

**FAILS THE BAR on all three gates, on both books. The declared candidate condition is NOT MET.**
Pre-registration `73a1a9c` predates the runner and this file (R8). **The ledger does not move.
Nothing was admitted. No holdout was read (the principal's standing decision).**

Cost: 244 s, of which 15 s were the 24 books and most of the rest the flag walk.

```
[STAGE0]  the runner's flag shares equal the record's, to the decimal
P2        priority off == D419's FIXED book, bit-identical (40,977 trades, net -3.616)
[RECON]   every book;  [CHUNK]  worker draw 0 == in-process
```

---

## 1. THE PRIMARY IS EMPTY — the breached zone above carries nothing

```
pooled   DEEP-2 yes  +13.34 (median +9.97,  trim +15.68, n 69,857)
         DEEP-2 no   +13.13 (median +7.82)                              gap  +0.21 ± 3.05   +0.1 SE   T1 FAIL
cell 2   DEEP-2 yes  +28.38 (median +18.85)   no  +32.60 (median +25.14)  gap  -4.22 ± 7.46   -0.6 SE
```

**"A higher zone was touched and breached" is worth two tenths of a basis point.** X-b said it
would pay +20–25, more than a re-entry; it pays *less* than one (+13.34 against DEEP-1's +16.70),
and in cell 2 it is below the events that lack it.

**The decomposition says why, and it is the finding of the per-trade lens:**

```
                      both D1 and D2    DEEP-1 only     DEEP-2 only     neither
pooled                    +16.81           +16.57          +4.95        +10.86
                        (n 49,431)       (n 43,844)     (n 20,426)    (n 66,349)
cell 2                    +30.97           +31.18          +6.59        +34.05
```

**The breach adds nothing to the re-entry** (+16.81 against +16.57) **and on its own it is the
worst cell in the table** — +4.95 pooled, +6.59 in cell 2. A name whose zone above was breached
*without* a recent trade on it is a name that broke down and kept going. The structural story —
"the stack above has failed, this is the next level down" — has the sign backwards: a failed
stack is not a deeper support, it is the absence of one. What D420 found was never about the
breach. It was about the *recent trade*.

---

## 2. DEPTH IS A HUMP, NOT A GRADIENT — and the second zone is the trade

```
                stack 1        stack 2        stack 3+
pooled          +9.81          +20.14         +10.52          monotone: NO
                (med +5.60)    (med +12.44)   (med +9.09)
                (trim +9.21)   (trim +17.58)  (trim +12.55)
                n 58,477       n 54,759       n 66,814
cell 2          +29.87         +45.62         +17.88          monotone: NO
                (med +24.73)   (med +27.62)   (med +14.93)
                (trim +28.50)  (trim +39.02)  (trim +19.63)
                n 7,974        n 8,170        n 9,880
```

X-c predicted `3+ > 2 > 1`. **It is `2 > 3+ ≈ 1`.** The second zone in twenty sessions pays twice
the first; the third or later pays *no more than the first* pooled and **less than the first in
cell 2.** Medians and symmetric trims agree at every rung. The hump is not a tail.

**This is the sharpest selection number the line has produced, and it is selected.** It is one
rung of three, read after the fact, on the fixture every study since D413 has used. It is handed
over as exactly that: **stack-2 events in cell 2 pay +45.62 bp (median +27.62) on 8,170 events**,
against a ~23 bp neutral round trip — **~2× coverage per trade** — and it has faced no null, no
out-of-sample test, and no book of its own. It is not promoted. It is the number to write the
next pre-registration around, if the principal wants one, and the per-year table in §3 is the
first thing that pre-registration would have to survive.

**Read with D420 and D416, the hump says something about the mechanism.** A second zone in a
decline is a *pullback into structure after a first bounce failed* — the population D416's late
stalls bounced hardest from. A third-or-later zone is a *trend*, and the zone is no longer a level
in it. Depth helps once.

---

## 3. THE PER-YEAR TABLE — the premium is front-loaded in time, like the base edge

```
DEEP-2 gap by year   2010 +15  2011 +46  2012  +3  2013  -5  2014  +9  2015  +8  2016  -4  2017  -5
                     2018 +31  2019  -6  2020 -100 2021 +37  2022 +14  2023 -29  2024 +10  2025  -6  2026 +6
positive years  10 of 17
DEEP-2 gap by half     2010-2017  +6.36 (+1.7 SE)      2018-2026  -4.10 (-0.9 SE)
DEEP-1 gap by half     2010-2017 +10.03                2018-2026  +5.16
base edge by half      2010-2017 +18.56                2018-2026  +8.93
```

**The breach premium is not there in the second half.** The re-entry premium is — halved, from
+10.03 to +5.16, in step with the base edge halving from +18.56 to +8.93. X-f asked whether the
depth premium was in both halves *unlike* the base edge; **it is in both halves *like* the base
edge**, shrinking with it. Whatever this construction is, it was larger before 2018.

---

## 4. THE BOOK — priority does nothing, requirement trades less

```
50 slots            gross     net     cost    trades   turnover    util    per trade
FIXED              +2.817   -3.616   6.434    40,977   19.90%/d   99.5%     +14.16
DEEP2-PRIORITY     +2.468   -3.880   6.348    40,983   19.90%/d   99.5%     +12.40
DEEP2-REQUIRED     +2.815   -2.599   5.414    35,898   17.43%/d   87.2%     +16.15
DEEP1-PRIORITY     +3.162   -3.384   6.547    40,977   19.90%/d   99.5%     +15.89
DEEP3-PRIORITY     +1.985   -4.424   6.409    40,975   19.90%/d   99.5%     +9.98
```

| | net Δ vs FIXED, mean over seeds | SE | outcome |
|---|---|---|---|
| **DEEP2-PRIORITY** | **−0.316** | 0.561 | **T2 FAIL**, −0.6 SE |
| DEEP2-REQUIRED | **+0.958** | 0.746 | +1.3 SE — **and its gross is −0.055: the whole gain is cost** |
| DEEP1-PRIORITY | +0.244 | 0.477 | +0.5 SE — the only priority with a positive sign |
| DEEP3-PRIORITY | −0.612 | 0.600 | −1.0 SE |

**Putting the breached names at the front of the queue makes the book worse** — it promotes the
+4.95 population. Against fifty books that promote the same *number* of events at random, it is
below the median on the 50-slot book (**T3 FAIL, −6.5 SE**) and far below on cell 2 (−18.8 SE):
**random priority beats the structural one.**

**The one positive line is the requirement, and it is D419 §7 again, measured a third time.** The
DEEP2-REQUIRED book has the *same gross per bar* as FIXED (+2.815 against +2.817) at **87%
utilisation instead of 99.5%**, so it pays 5.41 instead of 6.43 in cost and nets a basis point
better. **It did not select better trades — its gross is identical. It took fewer of them.**
D419 said turnover is where the cost lives; D420's random-thinning control said fewer trades is
better net by cost; this says it a third way. The lever is real and it is not depth.

### 4a. Cell 2, and the declared candidate condition

```
10 slots            gross     net     cost    util    per trade      Δ net vs FIXED
FIXED              +4.590   -0.718   5.308   92.3%    +24.85
DEEP2-PRIORITY     +3.348   -1.862   5.210   92.3%    +18.12         +0.259 ± 0.726 (seed spread 2.5)
DEEP2-REQUIRED     +2.408   -1.774   4.182   76.9%    +15.65         -0.034 ± 1.177
```

**Record §5a required the cell-2 DEEP2-REQUIRED book to be net-positive, to beat its control,
and the premium to show in the second half. It is net −1.363 over seeds, the second-half DEEP-2
gap is −4.10, and the control was not needed. NOT MET, on all three.** This construction is not a
holdout candidate.

---

## 5. Predictions — none held cleanly, and the misses are all the same miss

| | prediction | outcome |
|---|---|---|
| **X-b** | DEEP-2 pays more than DEEP-1, +20–25 | **wrong** — +13.34, *less* than DEEP-1; DEEP-2-only is +4.95 |
| **X-c** | DEEP-3 monotone | **wrong** — a hump; the second zone pays double, the third no more than the first |
| X-d | priority raises net ~+0.5, still negative | **half** — right sign for DEEP-1 (+0.24), wrong for DEEP-2 (−0.32) |
| **X-e** | cell-2 REQUIRED net-positive | **wrong** — −1.363 |
| X-f | depth premium in both halves, unlike the base edge | **half** — DEEP-1 yes, DEEP-2 no; and *like* the base edge, not unlike |

**For the third time today my picture of the zone stack was wrong** — D418 (the close sits at
the near edge, not deep), D420 (re-entries are half the events, not a fifth), and now this (a
breached zone above is a breakdown, not a support; depth helps once, not cumulatively). Each time
the structural intuition said *more structure, more edge*, and each time the data said the edge
sits at one specific place in the structure and nowhere else. The predictions that held across
the four depth-adjacent studies were the arithmetic ones — cost, utilisation, turnover — and the
ones that failed were the ones about what the structure *means*.

---

## 6. What this leaves

1. **The structural definition is closed by measurement.** "Breach above" adds nothing to
   "recent trade on the name" and on its own is the worst population in the table.
2. **Depth helps once.** Stack 2 pays +20 pooled / +46 in cell 2; stack 3+ pays like stack 1.
   Selected, un-nulled, front-loaded in time like everything else here — and the single sharpest
   selection number the line has. If the principal wants to pursue selection, this is the rung,
   and the pre-registration would have to declare it in advance and survive §3.
3. **On the book, selection did nothing and thinning did the only positive thing** — for the
   third study running. A book that holds fewer positions at the same gross per trade is better
   net by exactly its cost saving. **That is a statement about how many trades to take, not which.**
4. **The base edge halved between the two halves of the sample, and every premium found halved
   with it.** Whatever survives a holdout will be the second-half number, and the second-half
   number is +8.93 gross against ~27 of cost.

**Disposition is the principal's.**

---

## 7. R13

Twenty-first look by object on price levels. **Twenty-one of twenty-one have failed their bar.**
No new data spent.

**Evidence:** `data/d421_depth.json` — both lenses, all three definitions and their overlap, the
per-year table, 24 books, 100 control books. Runner `scripts/run_d421_depth.py`; flags
`scripts/d421_depth_flags.py`, committed with the pre-registration.

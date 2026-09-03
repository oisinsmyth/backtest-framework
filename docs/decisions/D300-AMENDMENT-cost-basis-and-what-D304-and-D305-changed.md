# D300 FIRST AMENDMENT — the cost basis, and what D304 and D305 changed

**Status:** AMENDMENT to `D300-book-width-and-a-declared-conditioner-screen.md`
(pre-registered at `ed523f0`). Made **before the runner exists**. No result has
been seen.
**Date:** 2026-09-03

---

## 1. The cost basis, corrected twice over

**Cost is `rt × turn`.** `run_d299_ladder.py` and `run_d301_stack.py` both shipped
`turn * 2.0 * rt` and double-charged every cost column; `run_d295_exits.py:277`
is the correct form and reconciles to its own published 52.1893 exactly.
Assertion `[C]` enforces it against that fixed point and must reject the doubled
form.

**The round trip is the median-based figure, ~100–107 bp.** D302 established that
the 260 bp mean is a left-truncation artefact: unclamping Corwin–Schultz gives a
mean of **−19.47 bp**, so no mean is usable, while the median is **invariant to
the clamp** at 26.31 bp per side. Three independent computations now agree —
D302's 106.7, D303's 106.7, D305's 100.1. **The mean is carried in the output
labelled as the artefact it is.**

## 2. Report the price and spread of the names held at each depth

D302 measured a **2× cost tilt** on this book — held names at a **$21.00** median
price against the universe's **$36.85**, and **26.31 bp** of half-spread against
**13.20**. D304's tilt study is the next one on the list, and D300 generates its
baseline for free. **Held median price and held median half-spread are reported
per depth.**

## 3. WITHDRAWN: the claim that the refill pool is a separate axis

The original record and FINDINGS §10 both said the refill pool was its own axis
and a one-line change to a real 25-deep bench. **[D304](../../scripts/d304_two_lenses.py)
showed that is false.** A 19-slot book drawing from the 25-name gate is
**bit-identical** to one drawing from the top 19 — same 30,242 trades, same
+24.2 bp/trade, same +12.00 bp/bar — because refill only runs when a slot is free
and a drifted-out name **holds its slot**, so the bench is never consulted.

**So there is no pool axis to add**, and D300 stands as written on that point.
The related worry — that letting the pool track `N` welds concentration to bench
depth — was also misstated: with the pool equal to the slots at every `N`, bench
depth is **constant at zero**, so `N` varies concentration cleanly and nothing is
confounded.

## 4. D305 gives this study a prior, and it is against Q2

Three of D305's arms accidentally ran partial books, and the pattern is
monotone:

| implied book | gross/bar | **per position** | vol | maxDD | Sharpe |
|---|--:|--:|--:|--:|--:|
| 38.0 | +12.00 | +12.01 | 238.5 | 8,320 | **+0.799** |
| 33.1 | +11.56 | +13.28 | 252.0 | 10,554 | +0.728 |
| 30.6 | +10.84 | +13.48 | 258.1 | 11,734 | +0.667 |
| 29.8 | +13.45 | +17.13 | 259.7 | 12,163 | +0.822 |
| 18.8 | +12.47 | **+25.22** | **309.7** | **16,145** | +0.639 |

**Per-position gross rises monotonically as the book shrinks, and volatility
rises with it faster than the mean does.** Sharpe mostly falls.

**These are NOT top-N books** — they hold whoever was not blocked, so they are a
confounded preview and not evidence. But they sharpen D300's **Q2**, which
predicted the Sharpe peak at `N` ∈ [5, 10]: **the prior now says the Sharpe peak
sits at or near the full book, and the mean peak sits at the smallest N.** Q2 is
left standing as pre-registered rather than rewritten — it was committed before
this evidence existed and it may simply be wrong.

## 5. Unchanged

The grid (`N` per leg ∈ {2, 3, 5, 7, 10, 14, 19}, no exits), both statistics
primary, the rank-rotation null, the bottom-`N` directional diagnostic, Arm 2's
four declared conditioners with rotation nulls and BH-FDR across 28, and every
prediction and stop condition.

**No holdout testing. Programme total remains 0.**

# D394 ADDENDUM 5 — CHOP genuinely improves the *shape*, and makes the *net* worse: gross up 6×, cost up 47%

**Status:** ADDENDUM 5. **DESCRIPTIVE** — no null, no hurdle, nothing selected, fitted or admitted
(R15). **Nothing closed.**
**Date:** 2026-09-09 · Runner: `scripts/run_d394_chop_shape.py` · Artifact:
`data/d394_chop_shape.json` · 47 s · **Holdout reads: 0.**

**The decisive comparison is CHOP against HIVOL, not against ALL.** CHOP is `hivol AND loER`, so
comparing it to the whole book confounds two filters. The question is whether the **ER axis adds
anything on top of the volatility effect** Addendum 2 already measured.

---

## 1. The four cohorts, cap 5, no exit rule

| | **ALL** | **HIVOL** | **CHOP_ER5** | **CHOP_ER21** |
|---|--:|--:|--:|--:|
| trades | 24,777 | 8,260 | 2,751 | 2,573 |
| **mean** | **+4.72** | **+9.70** | **+21.10** | **+28.39** |
| median | +0.88 | +1.38 | +9.54 | +6.18 |
| std | 498 | 657 | 580 | 666 |
| t | +1.49 | +1.34 | +1.91 | +2.16 |
| win rate | 50.15% | 50.15% | 50.82% | **50.41%** |
| avg win / loss | +323 / −316 | +447 / −430 | +418 / −389 | +471 / −422 |
| **payoff** | 1.024 | 1.039 | 1.075 | **1.117** |
| **skew** | +0.33 | +0.55 | +0.62 | **+1.39** |
| excess kurtosis | +20.5 | +13.6 | +7.9 | +18.8 |
| **trim BOTH 1%** | **+3.68** | **+6.93** | **+17.68** | **+22.86** |
| min / max | −7,673 / +9,299 | −7,673 / +9,299 | **−3,061** / +5,565 | −3,201 / +9,299 |

---

## 2. The ER axis IS doing something, and it survives the honest test

**Against HIVOL — the comparison that isolates it — CHOP_ER21 lifts the mean from +9.70 to
+28.39.** That is not the volatility effect relabelled.

**And it survives symmetric trimming**, which is the test that matters on a two-sided fat-tailed
book: **+6.93 → +22.86.** Roughly 80% of the improvement is in the body, not the tails.

**The improvement comes from PAYOFF, not from hit rate.** Win rate is flat across every cohort
(50.15% → 50.41%); the payoff moves **1.024 → 1.039 → 1.117**, and skew moves **+0.33 → +1.39**.
**Winners get bigger relative to losers.** That is the first cohort in this study whose shape is
genuinely asymmetric rather than a scaled copy of the book.

**The worst loss is also truncated:** CHOP_ER5's minimum is **−3,061** against the book's −7,673 —
though CHOP_ER21 keeps the +9,299 GME trade, so the right tail is not.

---

## 3. AND IT MAKES THE NET WORSE — the cost rises faster than the edge

| | ALL | HIVOL | CHOP_ER5 | **CHOP_ER21** |
|---|--:|--:|--:|--:|
| held price | $44.64 | $31.19 | $30.00 | **$29.90** |
| half-spread | 29.62 | 41.77 | 42.45 | **43.67** |
| **round trip** | **61.48** | 86.74 | 88.24 | **90.68** |
| **NET** | **−56.76** | −77.04 | −67.14 | **−62.29** |
| ratio | 0.08× | 0.11× | 0.24× | **0.31×** |

> **CHOP_ER21 earns 6× the gross of the unfiltered book and loses MORE money per trade:
> −62.29 against −56.76.**

Gross rose **+23.67**; the round trip rose **+29.20**. **The filter selects into names that are
cheaper ($29.90 vs $44.64) and wider (43.67 vs 29.62 bp a side) — it buys edge with cost, at a
losing exchange rate.**

**Both readings belong in the record.** The **ratio** improves nearly fourfold (0.08× → 0.31×),
which is real progress toward covering costs and would matter if the cost were fixed. **The net is
what a book actually earns, and it went backwards.** This is [Addendum 6](D393-ADDENDUM-6-the-ten-cells-and-the-price-split.md)'s
finding a third time: **the edge lives where trading is dearest.**

---

## 4. What this does NOT overturn

**[Addendum 4](D394-ADDENDUM-4-the-vol-x-path-efficiency-taxonomy.md) still stands and it is the
binding constraint on believing any of §2.** CHOP_ER21's **+28.39 was the best of 36 searched
cells, against a best-of-36 noise floor of +32.96.** It does not clear.

**So §2 describes the shape of a cell that has not been shown to be real.** Its t of +2.16 on 2,573
trades is an uncorrected statistic; after the multiplicity of the search that produced it, it is
not evidence.

**What would be needed to believe it:** a pre-registration naming `hivol ∩ loER_21` and its
direction in advance, on a fresh construction, with A′/B/B_s/C run against it — and it would still
have to explain why a 0.31× ratio is worth pursuing when 1.0× is the bar.

---

## 5. What is worth carrying regardless

1. **The ER axis produces the first genuinely asymmetric cohort in this study** — payoff 1.117,
   skew +1.39, truncated worst loss — where nine earlier observables produced only scaled copies
   of the book. **Whether that survives its own multiplicity is untested; the shape itself is a
   measurement.**
2. **A filter can raise gross 6× and lower net.** Any future filter on this universe must be
   scored on **net and ratio together**, because gross alone would have called this a success.
3. **Hit rate is immovable.** Every cohort sits at 50.1–50.8%. **On this construction the edge is
   entirely in relative magnitude, never in frequency.**

---

**Status footer.** Descriptive. No null, no holdout read, nothing admitted, nothing retired.
`docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.

# D298 RESULT — combining adds a little, and half the factorial was one book

**Status:** RESULT. Pre-registered at `13ed483`, runner at `04a9dcb`, both
committed before this file existed (R8).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0. Programme total: 0.**

---

## 1. Q2 FIRED EXACTLY, AND IT GOVERNS EVERYTHING ELSE

```
S=reversion + P=stop    vs S=reversion alone:  0.00% of held bars differ
S=reversion + P=target  vs S=reversion alone:  0.00% of held bars differ
S=reversion + P=both    vs S=reversion alone:  0.00% of held bars differ
```

**Not "under 5%" as predicted — zero.** The book is pinned at 19 slots and the
composite selects exactly 19, so a price exit can only fire on a name that is
still selected, and that name is re-entered on the same bar. **Adding a price
exit to the signal exit changes nothing whatsoever.**

**So the 16 cells are 10 distinct books.** All four `S=reversion/P=*/O=on` cells
are the same book (Sharpe +0.840, mean +11.10, maxDD 4,940) and all four
`/O=off` are another (+0.706). **Any count over the 16 cells overstates by
roughly a third**, including the headline "9 of 16 at p < 0.05".

## 2. The factorial

| cell | Sharpe | vs ctrl | **vs BEST PART** | mean | maxDD | expo | p |
|---|--:|--:|--:|--:|--:|--:|--:|
| **S=none / P=target / O=on** | **+0.863** | +0.351 | **+0.036** | +11.21 | 6,290 | 78.7% | 0.0348 |
| S=none / P=both / O=on | +0.842 | +0.329 | +0.074 | +10.64 | 5,464 | 72.4% | 0.0149 |
| **S=rev / P=target / O=on** ← mandated | +0.840 | +0.327 | **+0.012** | +11.10 | 4,940 | 66.9% | 0.0348 |
| S=rev / P=none/stop/both / O=on | +0.840 | +0.327 | +0.112 | +11.10 | **4,940** | 66.9% | 0.015–0.045 |
| **S=none / P=target / O=off** | +0.828 | +0.315 | +0.315 | **+12.49** | 9,548 | 100% | **0.0050** |
| S=none / P=both / O=off | +0.768 | +0.255 | +0.255 | +11.65 | 8,971 | 100% | 0.0299 |
| S=none / P=none / O=on | +0.728 | +0.215 | +0.215 | +8.72 | **3,607** | 71.6% | 0.0299 |
| S=rev / P=* / O=off | +0.706 | +0.194 | −0.122 … +0.194 | +11.27 | 9,841 | 100% | 0.075–0.179 |
| S=none / P=stop / O=off | +0.523 | +0.011 | +0.011 | +7.82 | 7,535 | 100% | 0.841 |
| **CONTROL** | **+0.512** | — | — | +7.54 | 9,374 | 100% | — |
| S=none / P=stop / O=on | +0.478 | −0.034 | −0.250 | +5.73 | 6,897 | 69.4% | 0.503 |

## 3. Combining adds — but a little, and not the mandated stack

**The best cell is `profit target + overlay` at Sharpe +0.863**, against the best
single part (`target` alone) at **+0.828**. **The interaction is +0.036 — a 4%
increment on a 62% improvement over the control.** p = 0.0348.

**The mandated cell is not the best.** `reversion + target + overlay` reaches
**+0.840**, beaten by the same stack with the reversion exit *removed*
(**+0.863**). And by §1 its `P=target` does nothing at all — it is arithmetically
`reversion + overlay`, and its "+0.012 over its best part" is the whole
contribution of both position exits together.

**What does the work is the profit target and the overlay.** The signal exit
(`reversion`) is the weakest of the three alone (+0.706, p = 0.095 — it does not
even clear its own null here) and adding it to `target + overlay` *lowers*
Sharpe from +0.863 to +0.840.

**And one cell is worse than doing nothing:** `stop + overlay` at +0.478 against
the control's +0.512.

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | no combination beats the best of its parts | **FALSIFIED, narrowly.** The best does, by +0.036 at p = 0.0348. Three distinct books beat their best part by more than +0.03 |
| **Q2** | `reversion + price` holds nearly identical names — under 5% differ | **CONFIRMED ABSOLUTELY — 0.00%.** Stronger than predicted, and it voids the price axis wherever the signal exit is on |
| **Q3** | the overlay composes additively | **CONFIRMED** — its increment is +0.215 alone, +0.035 on target, +0.134 on reversion, +0.074 on both. Positive on three of four, and the one exception is `stop` |
| **Q4** | the mandated cell beats the control and not the overlay alone | **HALF WRONG.** It beats the control (+0.327) *and* the overlay alone (+0.112) — but not `target + overlay` (−0.023), and its own price axis contributes exactly nothing |
| **Q5** | cost rises monotonically with each axis | **CONFIRMED** — 27.1 (control) → 46.1 (full stack) bp/bar |
| **Q6** | the best cell contains the overlay | **CONFIRMED** — the top three all do |

## 5. The number that dwarfs the rest

**Cost per bar is 27–46 bp against a gross mean of +7.5 to +12.5 bp.** This
column includes the base book's own position turnover, which D297's overlay-only
cost column excluded — so it is not comparable to D297's 0.661 bp/bar, and it is
the more complete figure.

**Every cell in this study loses money net of measured cost, by a factor of two
to four.** The Sharpe improvements are real and they are gross. **The cost
question decides all of it, and it is unresolved between 0.24× and 0.60×.**

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: 16 declared cells — **10 distinct books** — each against a composite
matched null of 200 draws. Nine cells clear p < 0.05 against 0.80 expected, but
duplicates inflate that; on distinct books it is **six of ten**.

## Stop

**Combining is not closed** — the best stack beats its best part at p = 0.0348,
which is what the study asked.

**The price axis IS closed on this book**, and for a mechanical reason rather
than an empirical one: at 19 slots and 19 selected it cannot change a holding.
Testing it needs a **deeper bench** — 19 slots drawn from `hist_L`'s 25 — which
is a different book and needs its own pre-registration.

**And the cost question now blocks three results:** D293's candidate, D297's
overlay, and this.

## Files

`data/d298_combined.json` · `scripts/run_d298_combined.py`

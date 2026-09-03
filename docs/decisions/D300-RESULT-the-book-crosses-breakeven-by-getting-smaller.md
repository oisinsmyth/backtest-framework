# D300 RESULT — the book crosses breakeven by getting smaller

**Status:** RESULT. Pre-registered at `ed523f0`, amended at `ce34daf`, runner at
`3e1a4dd`'s successor, all committed before this file existed (R8).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. The result

**Cost per bar is invariant to `N` — turnover is 0.2003 at every depth, spread
0.0000 — while gross per bar rises 3.79× as the book concentrates.** That is the
whole finding, and it is mechanical rather than fitted.

Net uses **each depth's own held-name spread**, which is CLAUDE.md's rule and
which the runner's own column got wrong by applying N=19's round trip everywhere:

| N | held | gross | vol | **Sharpe** | maxDD | held ½-spread | rt | **net** | p_gross | bottom-N |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **2** | 4 | **+28.57** | 588.9 | **+0.770** | 12,901 | **21.68** | 86.7 | **+11.20** | 0.0050 | −4.18 |
| 3 | 6 | +18.83 | 467.4 | +0.640 | 17,089 | 22.83 | 91.3 | **+0.55** | 0.0547 | −6.91 |
| 5 | 10 | +16.53 | 379.6 | +0.691 | 16,775 | 20.58 | 82.3 | **+0.04** | 0.0846 | −0.08 |
| 7 | 14 | +13.67 | 328.0 | +0.661 | 17,803 | 22.23 | 88.9 | −4.14 | 0.0050 | −5.32 |
| 10 | 20 | +9.30 | 297.2 | +0.497 | 15,997 | 24.09 | 96.4 | −10.00 | 0.0647 | −6.43 |
| 14 | 28 | +9.12 | 259.0 | +0.559 | 11,630 | 24.30 | 97.2 | −10.34 | 0.0050 | −3.16 |
| **19** | 38 | +7.54 | 233.6 | +0.512 | **9,374** | 26.67 | 106.7 | **−13.82** | 0.0547 | +1.54 |

**The book crosses breakeven between N = 5 and N = 3, and is clearly positive at
N = 2.** Every depth clears BH-FDR at q = 0.10 against the rank-rotation null
(sorted p = 0.0050, 0.0050, 0.0050, 0.0547, 0.0547, 0.0647, 0.0846 against
thresholds 0.0143 … 0.100).

## 2. Why concentration wins twice

```
N=19 -> N=2     gross  x3.79     vol  x2.52     Sharpe  x1.50
                sqrt(38/4) = 3.08 if positions were independent
```

**Vol rises by less than independence predicts.** The 38-name book's positions
are positively correlated, so it never got the diversification its size suggests
— which means shrinking it costs less volatility than the square root implies,
while the mean rises with the rank profile. Concentration is favourable on both
terms at once.

**And it partly fixes the cost tilt for free.** D302 found the book holding
**$23.72**-median names at **26.67 bp** of half-spread against a universe at
$36.85 and 13.20. At N = 2 the held names are **$75.95** at **21.68 bp** — the
top of the ranking is *pricier and tighter*, so the tilt D304 was written to
attack is substantially a symptom of holding 19 deep.

## 3. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | gross per position falls monotonically with N | **CONFIRMED** — +271 / +119 / +63 / +37 / +18 / +12 / +8 bp, no inversion |
| **Q2** | **Sharpe does NOT peak at the smallest N; the peak lands at N ∈ [5,10]** *(against)* | **FALSIFIED.** Sharpe peaks at **N = 2** (+0.770). The diversification loss I expected to dominate does not, because the book was never diversified |
| **Q3** | cost/bar near-invariant to N — 0.85–0.95× at N=5 | **CONFIRMED, more strongly than stated** — turnover is *identical* to four decimals at every depth, and cost falls further still once each depth's own held spread is used (0.81× at N=2) |
| **Q4** | top-N beats a rank-rotated set at every depth | **CONFIRMED** — all seven clear BH at q = 0.10 |
| **Q5** | bottom-N is worse than the control at every depth | **CONFIRMED at six of seven.** N=19 reads +1.54 because the bottom 19 of a 25-name gate shares 13 names with the top 19 — the two sets cannot separate at that depth |
| **Q6** | *(Arm 2, conditioners)* | **NOT RUN.** Arm 2 is deferred; this record covers Arm 1 only |
| **Q7** | *(Arm 2)* | **NOT RUN** |

## 4. What this does NOT establish, stated plainly

**Four positions is not a portfolio.** At N = 2, **7 names of 663 produce half the
P&L**, vol is 2.5× the incumbent's and maxDD is 38% worse (12,901 against 9,374).
A book that can be halved by two names going wrong is not the same object as one
that cannot, whatever its Sharpe says.

**The p-values are non-monotone** — 0.0050 at N=2, 0.0547 at N=3, 0.0846 at N=5,
0.0050 at N=7 — which is not what a clean monotone effect produces. The
rank-rotation null is noisy at small N, where it compares two arbitrary names
against the top two, and 200 draws is thin for that. **The ordering of depths by
p-value should not be read as meaningful; only the family-level result should.**

**Borrow and impact are still unmodelled.** Spread is a floor. A short book of
four names at $76 has less impact risk than one of nineteen at $24, but borrow on
the short leg has never been priced anywhere in this programme.

**And this is a screen on mined data.** R14's ladder is unchanged: a
pre-registered out-of-sample test on a fixture never seen is what would make this
a candidate, and the holdout remains unread at 0.

## 5. Where it leaves the programme

**The cost question that blocked four studies is answered, and the answer was
book width.** Not the estimator, not the exits, not the overlay: the book was
simply too wide for its own edge profile, and every exit study since D295 has
been optimising the wrong axis on a book that could not pay for itself at any
exit rule.

**D304's tilt study is largely pre-empted** — concentration moves held price from
$24 to $76 and half-spread from 26.67 to 21.68 without a filter. A filter study
should now be scoped against the concentrated book, not the incumbent.

**And D305's confounded cells make sense in hindsight**: the arms that
accidentally shrank the book looked better *because* they shrank it, and
`R rank<=5`'s +0.19 net at 18.8 positions sits exactly where this table's N=10
row (20 positions, −10.00) says a top-N book of that size would not. Blocking
re-entry buys concentration inefficiently; choosing `N` buys it directly.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: 7 declared depths, each against a rank-rotation null at 200 draws on
**both** statistics, plus 7 bottom-N directional diagnostics. All 7 clear BH-FDR
at q = 0.10. Arm 2 (the four declared conditioners) was **not run** and remains
pre-registered.

## Stop

**Arm 1 is answered. `N` is not a research variable to keep tuning — it is the
axis that decides whether this book is tradeable at all**, and the principal's
standing ruling applies: dedicated capital takes the best gross `N`, shared
capital the best Sharpe `N`. Here they coincide at N = 2, which is the
uncomfortable part.

**Next is not another parameter.** The candidate is a concentrated book at N ∈
{2, 3, 5}, and what it needs is the concentration risk priced — name-level
attribution, era splits, and the borrow that has never been charged — before
anything approaches R8's out-of-sample test.

## Files

`data/d300_width.json` · `scripts/run_d300_width.py` · `temp/d300_run.log`

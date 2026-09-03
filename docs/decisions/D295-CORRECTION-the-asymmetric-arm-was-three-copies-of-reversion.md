# D295 CORRECTION — the asymmetric arm was three copies of reversion

**Status:** CORRECTION to `D295-RESULT-the-anti-pattern-won-and-the-book-was-pinned.md`.
The record is not edited; this stands beside it (books and records are amended in
writing, never quietly changed).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0.**

---

## What is wrong

D295 reported **6 of 19 cells beating their own null p95**. That count is
inflated by duplicates and by one pathological null. **The real figure is two.**

### B5 `asymmetric` is B1 `reversion`, bit-identically

```
          bp (12 dp)            trades   run    run_win  run_lose  turnover
B1        11.274806037178       35,734   3.39    2.95     3.90     0.295
B5@1.0    11.274806037178       36,708   3.30    3.69     2.92     0.303
B5@1.5    11.274806037178       32,351   3.74    3.82     3.64     0.267
B5@2.0    11.274806037178       29,751   4.06    4.06     ...      0.245
```

**Identical returns to twelve decimal places across three parameter levels and
against a different rule, while the trade counts differ by 7,000.**

`asymmetric` is `cum <= -param*u OR not sel[row,t]`. The second clause forces
`held ⊆ selected`, and the book refills to 19 from a selected set of exactly 19,
so **the holdings are the top-19 every bar whatever the stop does**. A stopped
name that is still selected is re-entered on the same bar. The parameter moves
the ledger and cannot move the book.

**This is the pinning, sitting in D295 three studies before D298 measured it at
0.00%.** It was visible in D295's own output as three identical numbers and was
not recognised.

### C3 `idle_spread` passes against a null that loses money

`d_bp = +0.25` against a null **p95 of −0.40**. The control loses money, so
being less bad than it is not evidence. This is R7's named pathology — the
fourth case of it in this programme.

## The corrected count

| | |
|---|---|
| D295 as published | **6 of 19** beat their own p95 |
| distinct books among those six | **3** — B1/B5 are one book, B6@1.0, C3 |
| after removing the pathological null | **2** |

**The two real ones are `reversion` (B1) and `profit_target` at 1.0× vol
(B6@1.0).** Every study since has been built on the second of them, so nothing
downstream is invalidated — but the screen was narrower than the record says.

## What does not change

D295's verdict. `n_pass` was **0** and remains 0; it failed on `beats_floor`
(1 of 20), not on the null count. The anti-pattern finding — that the rules
which work cut *winners* while the "trim losers, let winners run" rule adds
nothing — is unaffected and is if anything strengthened, since B5 was the other
cell that appeared to combine a stop with a signal exit and it turns out to have
contained no stop at all.

## How it was found

While assembling D301's layer-by-layer comparison, the four `beats_null` cells
were listed and three of them carried the same number.

**A cheap guard would have caught it:** assert that a cell's book differs from
every other cell's book, or that a parameter axis moves the book and not only the
ledger. D295's assertion [3] checked that the *uncapped* rules hold longer than
the baseline; it did not check that a capped rule's parameter changes what is
held. That check is added to every runner from D303 on.

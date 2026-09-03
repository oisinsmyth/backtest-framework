# D299 CORRECTION — the cost column was overstated, not understated

**Status:** CORRECTION to
`D299-RESULT-the-family-acted-and-there-was-nothing-there.md`, §6.
The record is not edited; this stands beside it.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0.**

---

## What is wrong

D299 §6 says its cost column was **understated by 1.57×** because the runner used
the universe-wide mean half-spread (39.81 bp) instead of the names actually held
(62.31 bp). The direction of that substitution is right. **The conclusion is
wrong, because the runner had a second error going the other way and I did not
find it until D302.**

`run_d299_ladder.py` computed

```python
cost_bar_bp = float(turn * 2.0 * rt_bp)        # WRONG
```

against `run_d295_exits.py:277`, which is correct:

```python
cost_bar_mean = rt_mean * turn
```

**`rt` is a full pair round trip and `turn` is the fraction of pairs entering per
bar, so the product is the cost.** The `* 2.0` double-charged it. D295's
published control reconciles exactly — `260.7 × 0.200 = 52.19`, which is what
D295 reports — and the doubled form gives 104.38.

## The corrected figure

| | |
|---|--:|
| D299 reported (control cell) | 63.8 bp/bar |
| correct: `rt_held × turn` = `260.2 × 0.200` | **52.0 bp/bar** |
| **so the published figure was** | **overstated by 1.22×** |

The two errors partly offset: the universe spread understated by 0.61× and the
`* 2.0` overstated by 2×, netting to 1.22× too high. **§6's "understated by
1.57×" should read "overstated by 1.22×".**

## What does not change

**No verdict.** D299's statistic is Sharpe, which carries no cost, and cost was
reported not gating. The family closed on 1 of 24 cells against 1.2 expected,
zero BH discoveries, and a treatment that lost to its own deliberately-invalid
control. None of that touches the cost column.

The same `* 2.0` was in `run_d301_stack.py`. **It was in no other runner** —
`run_d295_exits.py`, `run_d298_combined.py` and `run_d297_overlay.py` are all
correct, and D290 through D298 are unaffected. Both bugged files were written on
2026-09-03.

## Why it survived

**Nothing checked the cost arithmetic.** D299 carries seven assertions — the lag
audit and a variant that must fail it, the sign audit, the bit-identical
reference cancellation, null matching with a control that must fail the
persistence check, reconciliation to the trade ledger, transposed versus
column-major reads, and a self-test that must raise on a book handed free money.
The one column with a bug in it was the one column nothing asserted against.

Added to every runner from D303 on:

```
[C] COST DIMENSIONS. At k = 5, turnover must equal 1/k to floating point and
    cost_bar must equal rt * turn, cross-checked against D295's published
    52.19 bp at rt = 260.7 -- and the assertion must FAIL on a doubled formula.
```

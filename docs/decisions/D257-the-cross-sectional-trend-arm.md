# D257 — The cross-sectional trend arm, on a name holdout

**Status:** Pre-registered — committed BEFORE the runner exists
**Date:** 2026-08-29
**Area:** Strategy research

---

## Provenance — a screen result, chosen after looking, stated plainly

**This candidate came out of a decomposition of [D256](D256-the-book-on-single-names.md)'s run, not
out of a hypothesis.** The sequence was: split each book's return into timing and selection, notice
that S2's selection component on single names is **+0.612 against its long-flat +0.324**, and build
the dollar-neutral book that the selection term already is.

**That is exactly the situation that has killed every strong screen result in this programme** —
D235's seven cells, D240's A2 at the 99.6th percentile, D251's five cleared spreads. **Nothing
below should be read as validated until the holdout says so.**

What is already measured, and what makes it worth a pre-registration rather than a shrug:

| | |
|---|---:|
| SN S2-neutral Sharpe, full universe, after two-leg costs | **+0.607** |
| rho with the committed ETF book | **−0.132** (block bootstrap p05 −0.205, p95 −0.069) |
| **rho with the ETF S2 arm — the "same signal in a hat" test** | **+0.118** |
| diversification bar `rho x SR_A` | **−0.109**, cleared |
| combined book at equal risk weight | **+1.091** against **+0.831** |
| `g_lo` IC, 21-bar, overlap-corrected t | **+0.0247, t = +2.4** |
| residual participation ratio, single names | **74.35** |
| *control: SN S1-neutral* | *−0.517* |

---

## The rule — frozen, exactly as measured

```
state_i(t)  = g_lo > 0 AND g_hi > 0          S2's uptrend state, k=3, window 252
pos_i(t)    = enter at onset, exit at age 63 or when the state ends
f(t)        = mean(pos) over LIVE names
w_i(t)      = (pos_i(t) - f(t)) / n_live(t)  <- sums to ZERO by construction
```

Charged on **two-leg gross turnover** at 5 bp per side. **No parameter is varied. One cell per
cohort.**

## The split — pinned before the run, by a non-performance rule

**Names are shuffled once with seed `20260829` and split 50/50.** Cohort A is the screen, cohort B
is the **holdout and carries the verdict**. The seed is fixed here, in this file, before the runner
exists; **no symbol enters or leaves either cohort for any reason connected to its returns.**

## The measurement problem this design creates, stated before it can be mistaken for a result

**Halving the universe halves breadth, and `IR ~ IC x sqrt(breadth)`.** Residual participation
ratio 74.35 becomes roughly 37, so **a perfectly reproducing signal should score about
`0.607 / sqrt(2) = 0.43` on each half.** A validation Sharpe of 0.43 is therefore a **PASS**, not a
32% degradation.

**So the primary comparable is IC, which is breadth-independent.** The Sharpe comparison is
reported breadth-adjusted, and the raw Sharpes are reported beside it so nobody quotes the wrong
one.

## Hurdles

- **H — carries the verdict, on cohort B.** Matched-count rotation null at **≥95th percentile on
  Sharpe AND money**, rotated within each symbol's own live window.
- **G — the generality test.** Cohort B's IC must have the **same sign** as cohort A's and lie
  within a factor of two of it. **A signal that ranks one random half of the market and not the
  other is not a signal.**
- **V — positive net CAGR** after two-leg costs, per D253.
- **Breakeven cost as a headline**, per D253's treatment of borrow. The full-universe book returns
  **+0.48%/yr at 0.79% vol**; the Sharpe is respectable and the money is thin, so the cost at which
  this dies must be stated, not buried.
- **R10 concurrency**, and effective breadth reported per cohort rather than assumed to halve.
- **rho with the committed ETF book, recomputed on cohort B alone**, with the paired block
  bootstrap. The diversification condition is re-evaluated there.

## Predictions

| | prediction | confidence |
|---|---|---|
| **W-a** | **Cohort B's IC is within a factor of two of cohort A's, same sign.** This is the real test | **~60%** |
| **W-b** | **Both cohorts score near 0.43**, not near 0.607 — breadth, not decay | **~70%** |
| **W-c** | **Cohort B clears H on both legs** | **~50%** |
| **W-d** | **rho with the ETF book stays negative on cohort B** | **~70%** |
| **W-e** | **Breakeven cost is under 20 bp per side** — thin money, and this is where it dies if it dies | **~65%** |

**W-c at 50% is honest rather than modest.** Five signals were examined and this construction was
chosen after seeing the decomposition; the base rate for a post-hoc screen result surviving a null
in this programme is roughly one in eight.

## Stop

**If cohort B fails H, or fails G, this is CLOSED** — no re-split, no second seed, no alternative
neutralisation, no move to a time holdout as a second chance. **A holdout spent is spent.**

**If it passes**, it is still not admitted: a passing name holdout earns a **time** holdout as a
separate registration, because [D243](D243-the-book-on-extended-history.md) established that
instrument generality and era robustness are different properties and S1 has one without the other.

## Ledger

| count | N |
|---|---:|
| fresh — 1 cell x 2 cohorts | 2 |
| + the decomposition that found it: 5 signals x 2 universes, plus 3 timing/selection splits x 2 | 18 |
| + carried from D256 | 46,028 |
| **total** | **46,046** |

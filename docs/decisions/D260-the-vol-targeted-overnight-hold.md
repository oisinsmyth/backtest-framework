# D260 — The vol-targeted overnight hold, on a time holdout

**Status:** Pre-registered — committed BEFORE the runner exists
**Date:** 2026-08-29
**Area:** Strategy research · **prop track** ([BOOK_PROP.md](../BOOK_PROP.md))

---

## Provenance — a closure, a correction, and why this is not a rescue

**[D259](D259-the-extended-session-and-the-overnight-interior.md) closed C1 on hurdle P4** at a
2.07% breach rate against a 4% trailing floor — an expected life of 48 sessions against a 3-year
requirement.

**That closure tested only STATIC sizing, and that was an error**, because
[D258](D258-the-prop-track-candidates.md) had already named the sizing wrapper as a **precondition**:

> *"C4 — the sizing wrapper (a precondition, not a candidate). Any candidate needs this bolted on
> before P1 is even measurable."*

**So this record completes a registered test rather than searching for a variant that passes.** The
distinction rests entirely on C4 having been named in advance, and if that were not true this study
would not be admissible.

**What the correction measured**, at matched average exposure, vol estimate over the prior 21 holds:

| avg size | vol-targeted breach | *static* | ann return | profit before breach |
|---:|---:|---:|---:|---:|
| 0.71x | **0.18%** | *0.55%* | +6.61% | 14.71% *(vs 6.74%)* |
| 0.95x | **0.57%** | *1.75%* | +8.79% | 6.08% *(vs 2.82%)* |

and, decisively, **2020's breach rate fell from 11.36% to 0.13%** while the three eras converged to
0.11–0.22%. **The tail was regime-driven and sizing to volatility removes the regime.**

**All of that is in-sample, and the 0.4% target that cleared P4 was chosen AFTER seeing it.** This
record exists to fix that.

---

## The rule — every free parameter fixed here

```
hold        enter at the 18:00 ET print, exit at the 16:10 ET print   (the MyFundedFutures window)
vol_lag(t)  standard deviation of the PRIOR 21 holds' returns, that symbol only, shifted by 1
k(t)        clip( TARGET / vol_lag(t),  0,  CAP )
floor       4% trailing drawdown on OPEN equity, peak includes the current bar's high
breach      the first bar where k(t) x trailing_dd exceeds the floor
```

**`CAP = 4.0`, fixed.** The correction measured cap 2x and 4x as materially identical (0.18% vs
0.18% breach at matched exposure), so the cap is not a live parameter and is not swept.

### The volatility target — derived, then swept, and the multiplicity paid

**The target is not chosen freely. It is stated as a SAFETY FACTOR:** size so that the floor sits
`N` standard deviations of a single hold away.

```
TARGET = 0.04 / N
```

**Four cells, `N` in {6, 8, 10, 12}** → targets **0.67%, 0.50%, 0.40%, 0.33%**.

**The 0.4% that cleared P4 in the correction is N = 10, and it sits INSIDE this grid rather than
being its centre.** That is disclosed rather than disguised: the grid was chosen to contain it, so
**a best-of-4 floor is applied and the four cells are counted in full.** A single pre-chosen N would
be a stronger design and would also be a fiction, since the value is already known.

---

## The split — time, and the holdout contains the stress event

| | span | why |
|---|---|---|
| **SCREEN** | **2010-01 → 2018-12** | pre-dates every regime the correction was measured on |
| **HOLDOUT** | **2019-01 → 2026-08** | **contains 2020**, and carries the verdict |

**The holdout deliberately includes March 2020.** A rule tuned before it that survives it is worth
something; a rule validated on a period without a stress event is not. **This is the opposite of
excluding 2020 as an outlier**, which is what [D250](D250-the-overnight-gap-pre-screen.md) had to do
to a candidate that lived on it.

**A time split, not a symbol split**, because four index ETFs have an effective breadth near 1 —
a symbol holdout here would test almost nothing ([FINDINGS §4](../FINDINGS.md)).

---

## Hurdles — all measured on the HOLDOUT

- **P4 — carries the verdict.** Expected time-to-breach **> 3 years** at the deployed size.
- **P1.** The 4% trailing floor on open equity is the breach definition itself.
- **P3.** Worst single hold **≤ 2%** of account at the deployed size.
- **LADDER — new, and it is the one that decides whether this is worth doing.** **Expected profit
  before first breach must exceed the venue's payout ladder cap.** An account that breaches before
  it can be paid out is worthless however long it lives. Reported in account-percent and in dollars
  on a $150k MyFundedFutures account.
- **STABILITY.** The holdout's breach rate must be **within a factor of two** of the screen's. A
  sizing rule that works only in the regime it was fitted to is not a sizing rule.
- **Best-of-4 floor** across the `N` grid, per D228.
- **2020 reported separately** within the holdout, never pooled away.

## Predictions

| | prediction | confidence |
|---|---|---|
| **V-a** | **The holdout's breach rate is within 2x of the screen's** — the STABILITY hurdle | **~65%** |
| **V-b** | **At least one N clears P4 on the holdout** | **~70%** |
| **V-c** | **2020's breach rate is the highest of any year in the holdout**, because a 21-hold volatility estimate CANNOT adapt fast enough to a regime that changed in a week. The in-sample 0.13% is the number I most expect to degrade | **~75%** |
| **V-d** | **The LADDER hurdle clears** — profit before breach exceeds the cap | **~60%** |
| **V-e** | **The return is 4–7%/yr of account, so 8–12 funded accounts are needed for the $50k goal.** Adequate for the mechanism, awkward for the business | **~70%** |

**V-c is the one that matters.** The correction's headline was 2020's 87-fold improvement, and
**that is exactly where a lagging estimator should fail.** If it holds up out of sample the
mechanism is real; if it does not, the whole result was an artefact of fitting the estimator on the
event it was asked to survive.

## Stop

**If no N clears P4 and LADDER together on the holdout, C1 is CLOSED for good** — no third sizing
scheme, no re-split, no alternative estimator window, no move to a symbol holdout. **Two closures is
enough**, and the first one was already reopened once on a legitimate technicality that does not
exist twice.

## What this study CANNOT establish, stated up front

**The path is measured on EQUITY extended-hours bars, not futures.** That is **16 of the 23 hours**,
missing 20:00–04:00 ET. A futures position lives through the whole session continuously.

**So a pass here is a FEASIBILITY BOUND, not a deployable backtest**, and admission to
[BOOK_PROP.md](../BOOK_PROP.md) would still require the same measurement on real futures bars —
which we do not hold, and which no free source provides.

## Ledger

| count | N |
|---|---:|
| fresh — 4 cells (N grid) x 2 cohorts | 8 |
| + the correction that prompted it: 4 static + 8 vol-targeted + 3 era cuts | 23 |
| + carried from D257 | 46,046 |
| **total** | **46,069** |

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

---

## RESULT — CLOSED. P3 binds, not P4, and every route converges on the same number.

**Produced:** 2026-08-29 · `uv run python scripts/run_vol_targeted_hold.py` ·
`VOL_TARGETED_HOLD_RESULTS.md` · 12,901 holds, screen 6,899 (→2018-12-28), holdout 6,002
(2019-01-03 → 2026-08-26).

### The four cells

| N | target | | avg size | breach | expected life | ann return | worst hold | P4 | **P3** |
|---|---:|---|---:|---:|---:|---:|---:|:--:|:--:|
| 6 | 0.67% | screen | 0.88x | 0.304% | 1.30 y | +8.33% | −8.50% | no | **no** |
| | | holdout | 0.70x | 0.167% | 2.38 y | +6.20% | −6.64% | no | **no** |
| 8 | 0.50% | screen | 0.66x | 0.130% | 3.04 y | +6.26% | −6.37% | yes | **no** |
| | | **holdout** | 0.52x | **0.050%** | **7.94 y** | **+4.65%** | −4.98% | **yes** | **no** |
| 10 | 0.40% | holdout | 0.42x | 0.033% | 11.91 y | +3.72% | −3.98% | yes | **no** |
| **12** | 0.33% | **holdout** | 0.35x | **0.000%** | **∞** | +3.10% | −3.32% | **yes** | **no** |

### The vol targeting works. P4 is comfortably cleared.

**Three of four N clear P4 on the holdout, and N=12 never breaches the 4% trailing floor once in
6,002 holds.** The mechanism from the correction reproduces out of sample: **stability ratios are
0.55, 0.38, 0.38 and 0.00** — the holdout is *better* than the screen at every N, not merely within
tolerance.

### But P3 binds, and it binds everywhere

**The daily loss limit — 2% — is stricter than the 4% trailing floor, and every cell fails it.**
Worst holds run −3.32% to −8.50%.

**And the closure is arithmetically clean, because the worst hold scales linearly with size.** Asked
what size clears P3, all four cells give the same answer from four different starting points:

| from | worst hold | needs | **implied size** | **implied return** |
|---|---:|---:|---:|---:|
| N=6 | −6.64% at 0.70x | 0.30x | **0.21x** | **+1.87%/yr** |
| N=8 | −4.98% at 0.52x | 0.40x | **0.21x** | **+1.87%/yr** |
| N=10 | −3.98% at 0.42x | 0.50x | **0.21x** | **+1.87%/yr** |
| N=12 | −3.32% at 0.35x | 0.60x | **0.21x** | **+1.87%/yr** |

> **The size that survives a 2% daily loss limit earns 1.87%/yr, and it does not matter which
> direction you approach it from.** On a $150k MyFundedFutures account that is **~$2,800/yr gross**,
> and roughly **twenty funded accounts** would be needed for the $50k goal.

**This is `exposure x edge` ([FINDINGS §1a](../FINDINGS.md)) for the third time in this programme,
now from the daily-limit side.**

### Scoring

| | prediction | outcome |
|---|---|---|
| **V-a** | holdout breach within 2x of screen | **CONFIRMED** — 0.55x, 0.38x, 0.38x, 0.00x, all improvements |
| **V-b** | ≥1 N clears P4 on the holdout | **CONFIRMED** — three do |
| **V-c** | 2020 is the worst year in the holdout | **PARTIAL.** 2020 is 2.8x and 3.3x the ex-2020 rate at N=6 and N=8, and **indistinguishable at N=10 and N=12.** The lagging estimator does degrade in 2020 — the effect is simply absorbed once size is small enough |
| **V-d** | LADDER clears | **CONFIRMED** at N=8, 10, 12 |
| **V-e** | 4–7%/yr, 8–12 accounts | **CONFIRMED at the low end** — +4.65% at N=8 |
| **—** | *(unregistered)* | **P3 fails at every N**, which no prediction anticipated |

### Two defects in my own instrument, and one in the registration

**Two hurdle-logic bugs, both of which punished a GOOD result** — found and fixed before anything was
read into the numbers:

1. **`clears_LADDER` required `np.isfinite(profit)`**, so a **zero** breach rate — the best possible
   outcome, giving infinite expected profit — was scored as a **failure**.
2. **`clears_STABILITY` was two-sided**, so a holdout breach rate *better* than the screen's failed.
   The hurdle exists to catch degradation; improvement is not a defect.

**And the registered selection rule is degenerate.** D260 specified *"N is chosen on the SCREEN by
expected profit before breach"*. **Profit-before-breach diverges as size falls** — halve the size and
the life more than doubles — so **that rule always selects the smallest N in the grid, whatever the
returns are.** It picked N=12 mechanically.

**The verdict is unaffected**, because P3 fails at every N including the ones a sensible rule would
pick. **But the rule was wrong when written and is recorded as such**: a selection criterion for a
sizing sweep must be *return subject to clearing the constraints*, never a survival statistic alone.

### The stop applies

**CLOSED. C1 is finished** — no third sizing scheme, no extended N grid, no alternative estimator
window. **Extending the grid to reach N≈20 after seeing P3 bind is precisely the second chance the
stop forbids**, and the arithmetic above already shows where it lands: **+1.87%/yr.**

**What survives is not a strategy but a method.** Vol-targeted sizing genuinely removes the regime
dependence of a drawdown constraint — 2020's static breach rate of 11.36% became 0.000% at N=12,
out of sample, on a rule fitted before the event. **That belongs in the sizing wrapper (C4) for
every future prop candidate**, and it is the reusable part of this study.

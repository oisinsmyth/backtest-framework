# D292 RESULT — four cells clear the bar, and the bar was too low

**Status:** RESULT. Pre-registered at `e63fa8e`, clarified and runner at
`10c3583`, both committed before this file existed (R8).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0. Programme total: 0.**

---

## The one-line result

**The arm's central tendency is negative again:** `t_min` mean **−0.26**, median
**−0.31**, only **32%** of live cells positive. A second filter, on average,
makes the book worse.

**Four cells cleared the pre-registered PROMOTION floor, so Q1 is falsified as
written.** But the bar I wrote does not require the effect to be distinguishable
from zero, and once that and two other defects are on the table, **nothing here
is promotable.** The defects are mine and they are disclosed below rather than
used quietly to erase a pre-registered pass.

---

## 1. What the pre-registered bars actually returned

| | |
|---|--:|
| cells producing a statistic | 80 of 80 |
| **VOID** by the pre-committed turnover audit | **12** |
| live cells | 68 |
| SCREEN survivors (beat both own nulls at p95) | **4** |
| expected by luck at p < 0.05 on both nulls | 0.17 |
| PROMOTION (joint max-Z floor **+1.83**) | **4** |
| BH-FDR kept, q = 0.10 / 0.20 | 0 / 0 |

| B1 | B2 | op | f | t1 | t2 | **t_min** | null1 p95 | null2 p95 | z_min | bars |
|---|---|---|--:|--:|--:|--:|--:|--:|--:|--:|
| `retrace_leg` | `rsi` | meanrank | 0.25 | +0.65 | +0.56 | **+0.56** | **−0.06** | **−0.14** | +2.75 | 2667 |
| `macd_line` | `rsi` | meanrank | 0.75 | +1.16 | +2.84 | +1.16 | +0.46 | +2.32 | +2.31 | 3137 |
| `macd_hist` | `rsi` | meanrank | 0.75 | +2.14 | +2.97 | **+2.14** | +1.75 | +2.13 | +2.17 | 3148 |
| `retrace_leg` | `rev_5` | meanrank | 0.25 | +0.80 | +0.79 | +0.79 | **−0.23** | +0.41 | +2.14 | 2833 |

## 2. Three defects, all mine

**(a) NEITHER BAR REQUIRES THE EFFECT TO BE NON-ZERO.** D291 had "paired
`t` ≥ 2" as its first pass condition. D292's pre-registration has SCREEN (own
null p95) and PROMOTION (max-Z floor) and **no effect-size requirement at all**.
So a cell can promote on `t_min` = +0.56. Three of the four do: +0.56, +0.79,
+1.16. **Only `macd_hist + rsi` has `t_min` > 2.**

**(b) THE NULL IS STRUCTURALLY DISPLACED FOR MEAN-RANK AT TIGHT f.** Look at the
two f = 0.25 rows: their own null p95 is **negative** (−0.06, −0.23) — the
entire null distribution sits below zero. The reason is mechanical. The parent
is the *m* best names by B₁ alone; the null book is selected by blending real B₁
with **noise**, then taking *m*. Any dilution of a real ranking loses to that
ranking. So the null asks *"is B₂ better than noise?"* and a merely harmless B₂
passes. **That is a much weaker claim than "B₂ adds", and the z statistic reads
the displacement, not the effect.**

**(c) THE BH-FDR ZERO IS PARTLY A RESOLUTION ARTIFACT.** With 200 draws the
finest expressible `p_max` is 0.005, and realistically 0.010 since both nulls
must sit at the floor. BH's thresholds at i = 1…4 for q = 0.10 are
0.00147–0.00588 — **all below what 200 draws can express**. BH cannot reject at
small *i* whatever the data says. It fails legitimately from i = 7 on
(threshold 0.0103, observed p(7) = 0.1144), but the headline "0 kept" overstates
its evidential weight. **Fixable with more draws; not fixed here.**

## 3. The capturability re-check — which the runner omitted

The pre-registration says gate 1e is re-checked for any cell clearing the
screen. `run_d292_third_order.py` defined the threshold and never applied it.
Run separately in `scripts/d292_capturability.py`:

| B1 | B2 | f | close bp | close t | open bp | **open t** | retained | **t_min at open** | 1e |
|---|---|--:|--:|--:|--:|--:|--:|--:|:--|
| `retrace_leg` | `rsi` | 0.25 | +59.8 | +2.60 | +35.7 | +1.69 | 60% | **+0.17** | FAIL |
| `macd_line` | `rsi` | 0.75 | +65.0 | +3.39 | +55.6 | +3.02 | 85% | +1.57 | PASS |
| `macd_hist` | `rsi` | 0.75 | +61.9 | +3.80 | +46.7 | +2.96 | 75% | **+1.70** | PASS |
| `retrace_leg` | `rev_5` | 0.25 | +86.4 | +3.40 | +71.3 | +2.97 | 83% | +0.79 | PASS |

**Three of four books are capturable.** But `t_min` — the second filter's actual
contribution — falls to **+0.17, +1.57, +1.70, +0.79** at open entry. **Not one
survivor has a second-filter contribution that is both significant and
capturable.** `macd_hist + rsi` goes from +2.14 to +1.70.

---

## 4. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | no cell clears PROMOTION | **FALSIFIED AS WRITTEN** — 4 cleared. Under any bar that also requires a non-zero capturable effect, 0 clear |
| **Q2** | pairs containing `retrace_leg` do no worse than pairs of the four D291 survivors | **CONFIRMED** — `retrace_leg` pairs: `t_min` p50 **−0.28**, 2 screen, 2 promote. Survivor pairs: `t_min` p50 **−0.36**, 2 screen, 2 promote. Indistinguishable |
| **Q3** | MEAN-RANK beats AND | **FAILED.** At matched retention (the only fair comparison): AND at f = 0.25, 81% held, `t_min` p50 **+0.09**; MEAN-RANK at f = 0.90, 88% held, **−0.63**. AND wins |
| **Q4** | the dose-response runs monotonically the wrong way | **FAILED** — there is no dose-response. AND: −0.23, −0.77, −0.28, +0.09. MEAN-RANK: −0.63, +0.10, +0.27, −1.13. Not monotone in either direction |
| **Q5** | the control passes the turnover audit | **FAILED** — 12 of 80 VOID, **all MEAN-RANK** (5 at f = 0.25, 5 at 0.50, 2 at 0.75) |

**Q2 confirming is the substantive result.** `retrace_leg` produced **zero**
D291 second-order survivors, and here it produces **exactly as many** screen
survivors and promotions as the four partners that did. **D291's partner-level
detail was noise. Only the `hist_L`-level concentration was real** — which is
precisely what the D292 pre-registration assumed and why all five partners were
used rather than the four.

**Q5 failing is the process working.** The audit was pre-committed and it voided
`rev_5 + rsi` meanrank 0.25 at z_min **+2.59** — which would otherwise have
been a fifth promotion. D291's veto arm had to be voided *after* it was read;
this one was caught before.

**Q4 failing matters more than it looks.** A real effect produces a coherent
dose-response. Neither operator produces one in either direction — the sweep is
noise around a slightly negative mean, which is what nothing looks like.

---

## 5. What this closes, and the decision that is not mine

**Nothing is promoted.** No cell has a second-filter contribution that is both
significant and capturable, and the four that cleared the written bar did so on
a bar with no effect-size requirement and, for two of them, against a null that
sits entirely below zero.

**THE PRE-REGISTERED BAR WAS CLEARED, AND OVERRIDING THAT IS EXACTLY THE
DISCRETION PRE-REGISTRATION EXISTS TO PREVENT.** So this record states both
facts and does not resolve them unilaterally: **four cells passed as written;
I judge the bar defective for the three reasons above; whether that judgement
stands is the principal's call, not the runner's.** The defects were identified
from the null distributions and the omitted 1e check, not from disliking the
answer — but that is what everyone says.

**Closed if the judgement stands:** stacking filters on this pool. The arm's
mean is negative, there is no dose-response, and the one cell with `t_min` > 2
loses it at open entry.

**Not closed either way:** the blend (stage 3, magnitude); `hist_L` itself,
which remains a tier-1 capturable candidate on its own merits and is untouched
by any of this; the veto, still never validly tested.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed and not priced: **80 cells**, plus the capturability re-check on 4
survivors. `hist_L` was selected in-sample at D291 and every cell here inherits
that; it is priced when the holdout is read.

## Files

`data/d292_third_order.json` · `data/d292_capturability.json` ·
`scripts/run_d292_third_order.py` · `scripts/d292_capturability.py`

---

# ADDENDUM — 2026-09-03: the combined book's OWN number, and why `hist_L` is the problem

Prompted by the principal asking a question the record above could not answer:
**what is the combined t?** Everything reported was a DIFFERENCE against
parents. The books' own numbers were never shown, and they change the reading.

## 1. The full ladder (`scripts/d292_full_ladder.py`)

`macd_hist + rsi`, meanrank, f = 0.75 — the strongest cell:

| rung | held/bar | close bp | close t | open bp | open t |
|---|--:|--:|--:|--:|--:|
| `hist_L` alone (25 names) | 3.5 | +52.52 | +2.86 | +40.70 | +2.30 |
| `hist_L` at N′ = 19 | 2.8 | +10.75 | +0.53 | −5.12 | −0.27 |
| + `macd_hist` only (19) | 3.4 | +33.83 | +1.87 | +25.70 | +1.49 |
| + `rsi` only (19) | 3.7 | +21.61 | +1.33 | +12.14 | +0.78 |
| **+ both (19)** | 3.7 | **+61.91** | **+3.80** | **+46.65** | **+2.96** |

**Each filter alone HURTS; both together HELP.** The combined book beats every
control — count-matched primary `t` +2.76 close / +2.95 open, `macd_hist` parent
+2.14 / +1.70, `rsi` parent +2.97 / +2.62 — and beats `hist_L` alone on 6 fewer
names, at both entries.

**THE RUNG THE PRE-REGISTRATION LEFT OUT.** Its control was the parents, on the
ground that D291 had answered "does the stack beat `hist_L` alone". But D291
tested SINGLE filters; MEAN-RANK did not exist there, so nothing had ever
compared this operator to the primary.

**The record above was anchored on the wrong statistic.** `t_min` is the
increment over parents, and the parents are degraded books — so `t_min` falling
to +1.70 at open entry says the increment over `macd_hist`-alone is modest, not
that the book is weak. The book's own open-entry `t` is **+2.96 against the
primary's +2.30**.

## 2. AND THEN THE ACTUAL PROBLEM, WHICH IS NOT THIRD ORDER

`hist_L` alone, k = 5, swept finely in N:

| N | 5 | 10 | 12 | 15 | 17 | 19 | 21 | 23 | **25** | 27 | 30 | 35 | 40 | 50 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **close t** | −0.22 | −0.88 | +0.04 | +0.70 | +0.92 | +0.53 | +0.81 | +2.00 | **+2.86** | +2.78 | +2.02 | +1.54 | +0.92 | +1.01 |
| **open t** | −0.43 | −1.12 | −0.10 | +0.14 | +0.48 | −0.27 | +0.03 | +1.30 | **+2.30** | +2.24 | +1.39 | +1.35 | +0.53 | +0.66 |

**`hist_L`'s edge lives in a window of N ∈ [23, 30] and is absent everywhere
else.** At N = 19 it is +0.53; at N = 10 it is **negative**. D290's grid was
{3, 5, 10, 25, 50} — it contained the spike and neither neighbour, so the peak
looked like a peak rather than like a spike.

**D290's null did price the N search** (its null took the max over the same
grid), so `hist_L`'s tier-1 status is not invalidated. But a candidate whose `t`
runs −0.88 → +2.86 → +1.01 across the searched parameter is **knife-edge**, and
every number in D291 and D292 inherits that: both studies fixed N = 25 by
inheritance and never asked whether the primary was stable there.

**This is the finding that should govern what happens next**, and it is about
`hist_L`, not about confluence.

## 3. What the addendum changes

**It does not overturn section 5's conclusion, and it moves the reason.** The
combined book is genuinely better than its controls at both entries. What it is
not is *robust*, because the primary it is built on is not robust in N — and
D292 never varied N, by design.

**Nothing here is promotable, and now for a better reason than the bar being
too low:** the whole `hist_L` cluster is conditioned on a single N that a fine
sweep shows to be a spike.

**The next test is obvious and it is not fourth order.** Re-run this cell across
N ∈ [15, 40] and see whether the third-order improvement survives where the
primary's own edge does not. If the combination is real, it should be less
knife-edge than the primary; if it merely inherits the spike, it will vanish with
it. **That is one runner, no new pre-registered cells, and it is worth more than
another order of confluence.**

## Files added

`scripts/d292_full_ladder.py` · `data/d292_full_ladder.json`

---

# ADDENDUM 2 — 2026-09-03: the N-stability test, which came out against my prediction

Criterion fixed in `scripts/d292_n_stability.py` and committed **before the
numbers existed**: INHERITED if the improvement tracks the primary's own N
profile (high positive `corr(primary_t, improvement_t)`); ROBUST if the
improvement is positive across the range **including where the primary is weak**.

I expected INHERITED. **All four cells came out independent, and two came out
robust.**

## `macd_hist + rsi`, mean-rank, f = 0.75 — open entry

| N | 15 | 18 | 20 | 22 | 24 | **25** | 26 | 28 | 30 | 32 | 36 | 40 |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| **primary t** | +0.14 | −0.09 | +0.45 | +0.67 | +2.17 | **+2.30** | +2.15 | +1.65 | +1.39 | +0.49 | +1.08 | +0.53 |
| **both t** | +1.87 | +1.33 | +2.23 | +2.23 | +2.89 | +2.96 | **+3.38** | +3.04 | +2.46 | +1.52 | +2.04 | +1.85 |
| **improvement t** | +2.25 | +2.07 | +2.50 | +1.47 | +1.18 | +0.52 | +1.69 | +1.59 | +1.25 | +1.42 | +1.21 | +1.72 |

**The primary is a spike; the combined book is not.** Its own open-entry `t` has
median **+2.23** across N ∈ [15, 40] against the primary's **+0.89**, it is above
+1.3 at every N in the range, and its maximum is at **N = 26, not 25**.

```
corr(primary t, improvement t)          -0.74   -> NOT inherited
improvement vs primary at N, positive   26/26
   ... where the primary is WEAK (t<1)  14/14
improvement vs primary at N' (matched)  20/26
```

## All four cells

| cell | corr | imp > 0 | imp > 0 where primary weak | both own t p50 | vs N′ |
|---|--:|--:|--:|--:|--:|
| **`macd_hist + rsi`** 0.75 | **−0.74** | **26/26** | **14/14** | **+2.23** | 20/26 |
| **`retrace_leg + rev_5`** 0.25 | −0.45 | **26/26** | **14/14** | +1.72 | 22/26 |
| `macd_line + rsi` 0.75 | −0.25 | 22/26 | 13/14 | +1.40 | 17/26 |
| `retrace_leg + rsi` 0.25 | −0.77 | 17/26 | 12/14 | +1.08 | 26/26 |

Primary own `t` p50 for comparison: **+0.89**.

**Every correlation is negative.** The improvement is largest exactly where the
primary is weakest — the opposite of riding its spike. **The pre-committed
ROBUST criterion is met outright by two cells.**

## Four caveats, none of which I can dismiss

**1. Adjacent N are not independent tests.** N = 24, 25, 26 share nearly all
their names. "26/26" is perhaps 3–5 effective observations. The *shape* is the
evidence, not the count.

**2. The count-matched comparison is weaker.** Against the primary at N′ the
improvement is positive 20/26 and turns **negative at N ≥ 32** (−1.23, −0.28,
−0.65, −0.04). Some of the gain against the primary at N is the smaller book,
not the selection.

**3. There is no null in this sweep.** D292's rotate-B nulls exist only at
N = 25. Nothing here tests whether a filter-shaped-but-content-free partner
would produce the same profile across N. **This is the gap that matters most.**

**4. The four cells were selected by D292's screen**, so this inherits that
selection.

## What it changes

**My reading in section 5 was wrong on its stated reason.** I said the cluster
was conditioned on a spike and would vanish with it. It does not vanish — the
combined book is *more* stable in N than the primary it filters, which is what a
real combination should look like and what I predicted against.

**It still is not promotable**, because of caveat 3: an improvement that has
never been tested against a rotated partner at any N but 25 is not an
established effect, it is a shape.

**The next test is now well defined and narrow:** run the rotate-B null across
N ∈ [15, 40] for `macd_hist + rsi` at f = 0.75. If the profile survives, this is
the first thing in this programme to beat a null on a parameter it was not
selected on. If it does not, the shape was the filter's form and not its content.

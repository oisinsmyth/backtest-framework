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

# D250 — The overnight gap as an intraday short signal: a pre-screen

**Status:** Screened and CLOSED — no rule proposed, no hurdle run, no null computed
**Date:** 2026-08-28
**Area:** Strategy research

---

## What this is, and what it deliberately is not

**This is a pre-screen, not a study.** It exists because [D248](D248-the-strength-filtered-intraday-short.md)
cost a full pre-registration, a runner, a test module and three build-time amendments to establish
that a relationship did not exist — and the relationship could have been falsified in twenty minutes
by measuring it correctly first.

**So the order is inverted on purpose.** Measure the conditional first, cheaply, R9- and R10-compliant.
Only if it clears a stated economic bar does it earn a pre-registration.

**No verdict is claimed and no hurdle was run.** What is claimed is that the candidate is not worth a
runner, and the arithmetic for why.

---

## The candidate, and why it was the best one available

[D247](D247-the-short-side-at-fifteen-minutes.md) established the one structural fact that makes an
equity short arm conceivable on this universe:

| | annualised |
|---|---:|
| **overnight** (prev close → open) | **+8.59%** |
| **intraday** (open → close) | **−0.36%** |

**Essentially all equity drift accrues overnight**, so an intraday-only book faces no drift headwind.
D238's structural objection to shorting is answered by the calendar. What D247 and D248 then failed to
supply is a *signal*: four Impulse MACD constructions have now failed at 15 minutes, and D247 diagnosed
why — a 34-bar Impulse is **1.3 sessions** at this sampling rate.

**The overnight gap was chosen because it is the only candidate conditioned on something this programme
has measured rather than hoped for.** If overnight is where the drift lives, then a large adverse gap is
that carrier delivering the opposite of its usual, which is a genuinely different state from anything
tried. It also bounds turnover by construction — at most one entry per session per name.

---

## The construction

```
gap[s]  = log( first_bar_close[s] / last_bar_close[s-1] )     realised at bar 1 of session s
z[s]    = gap[s] / sd( gap[s-63 .. s-1] )                     STRICTLY lagged normaliser
fwd[s]  = log( last_bar_close[s] / first_bar_close[s] )       measured from bar 1 onward
```

**The conditioning variable and the measured return share no bar — R9 is satisfied by construction,
not by assertion.** `z` is scale-free, per D232's finding that dollar-denominated quantities smuggle in
the price level.

57 ETFs × 55,726 bars → **2,156 sessions**, 2018-01-02 → 2026-08-26, **119,244 live (symbol, session)
cells**. Costs 1.85 bp/side; one entry plus one exit is **3.7 bp per session**, which is **−8.90%/yr**
if traded every session. That is the cost wall, restated in this study's units.

---

## Result 1 — the body of the distribution is empty

| quintile | z range | n | annualised |
|---|---|---:|---:|
| Q1 most gapped **down** | ≤ −0.70 | 23,849 | **+4.19%** |
| Q2 | −0.70 … −0.16 | 23,849 | +0.12% |
| Q3 ~flat | −0.16 … +0.27 | 23,848 | +2.84% |
| Q4 | +0.27 … +0.79 | 23,849 | −1.93% |
| Q5 most gapped **up** | ≥ +0.79 | 23,849 | +4.03% |
| **all** | | 119,244 | **+1.82%** |

**Spread Q1 − Q5 = +0.15%, non-monotone.** The most-gapped-down bucket is the *best* of the five, and
the only negative bucket is Q4. There is no relationship to trade.

---

## Result 2 — the tail looked like a rescue, and this is the part worth recording

Tightening the cut produces a large and monotone effect:

| cut | cells | % of live | distinct days | **top-5 days** | held-bar | **gross** | costs | **net** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| z ≤ −1.5 | 8,016 | 6.72% | 1,222 | 3.2% | +0.56% | −0.04% | 0.62% | **−0.66%** |
| z ≤ −2.0 | 4,180 | 3.51% | 751 | 5.9% | **−11.53%** | +0.39% | 0.33% | **+0.06%** |
| z ≤ −2.5 | 2,236 | 1.88% | 472 | 10.6% | **−21.99%** | +0.40% | 0.17% | **+0.22%** |
| z ≤ −3.0 | 1,278 | 1.07% | 287 | 17.8% | **−37.52%** | +0.39% | 0.10% | **+0.29%** |

**The held-bar edge triples and the gross return does not move.** It is pinned at ~0.4%/yr across
every cut. This is the finding, and it generalises far beyond this candidate:

> **`gross = exposure x edge`, and a selectivity dial moves the two factors in exact opposition.**
> Tightening a threshold raises the conditional edge by shrinking the population it is measured on.
> **Selectivity cannot create gross return. It can only redistribute it into fewer, larger trades** —
> which helps costs and nothing else. Best case here: **+0.29%/yr.**

---

## Result 3 — and it is one year

The top ten sessions hold **30.6%** of the `z ≤ −3.0` cells: 2020-03-16 (50 of 57 ETFs), 2020-03-09
(49), 2020-03-12 (49), 2025-04-04 (40), 2020-02-24 (39).

**Excluding 2020, the sign inverts on both cuts:**

| cut | with 2020 | **without 2020** |
|---|---:|---:|
| z ≤ −2.0 | −11.53% | **+24.90%** |
| z ≤ −3.0 | −37.52% | **+13.54%** |

**The entire tail effect is the COVID crash.** A short conditioned on it is not a strategy; it is a
levered bet that March 2020 recurs.

---

## R10's first prospective use, and it fired

| | mean names | max | sessions over 20 names |
|---|---:|---:|---:|
| **actual** | 11.1 | **56** of 57 | **18.1%** |
| *rotated* | 11.1 | *21* | *0.1%* |

**Clustering ratio 4.08x.** Gaps synchronise because everything gaps down together, so 1,278 cells are
a few dozen mornings. **[R10](../RULES.md) was written after D249 as an autopsy; this is the first time
it was applied before a result was reported, and it is what made the concentration check the obvious
next step rather than an afterthought.**

---

## Two corrections to the proposal's own framing

**1. The screening target was specified as the wrong quantity.** The bar was stated as *"a held-bar
edge around −15%/yr"*, calibrated against the ~25% exposure D247's arm ran at. **The tail cleared that
bar at −37.52% and was still worthless**, because the cut that produced it holds 1.07% of cells.
**A screening target must be stated as `exposure x edge`, never as the edge alone.** Any future
pre-screen states the product.

**2. The tail cut is a search, and it is counted as one.** The quintile table failed and the tail
looked like a rescue. **That is the complement-chasing shape D246 Constraint 3 exists to forbid**, and
what stopped it being reported as promising was running the concentration diagnostic *before* writing
it up rather than after. The four tail cuts, four concentration cuts and the 2020 exclusion are all
declared in the ledger below.

---

## What is closed

**The overnight gap as an intraday short signal on this universe.** Not the intraday short — D247's
`−4.27%` held-bar result stands and the horizon remains open. What is closed is this conditioning
variable, on three independent grounds: **flat in the body, sign-unstable in the tail, and capped at
+0.29%/yr even taking the contaminated number at face value.**

**Cost:** roughly twenty minutes, against D248's full pre-registration, runner, test module and four
build-time amendments for the same class of answer. **That ratio is the argument for pre-screening.**

## Ledger

| count | N |
|---|---:|
| 5 quintile cells | 5 |
| 4 tail cuts | 9 |
| 4 concentration cuts + the 2020 exclusion | 14 |
| carried from D249 | 45,922 |
| **total** | **45,936** |

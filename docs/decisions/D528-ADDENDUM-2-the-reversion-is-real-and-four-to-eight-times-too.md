# D528 ADDENDUM 2 — the reversion is real, replicates across scales, and is 4–8× too small

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D528-ADDENDUM-2-the-reversion-is-real-and-four-to-eight-times-too-small.md`. The H1 above is the full title.*

Date: 2026-09-14. Runners: `working/d528_why_zero.py`, `working/d528_does_it_decelerate.py`.

**This amends ADDENDUM 1, which is wrong on its central claim.** Nothing admitted (R15). The
reserved slice (2026-04-11 → 2026-09-09) remains UNREAD. Exploratory and multiplicity-laden: 20
cells were inspected, and the disposition below rests on the one cell that needed no selection.

---

## 0. Why this exists

The principal read ADDENDUM 1 and said the result was fighting his intuition — he expected the
causal rolling detector to do **better** than the stale one, not nothing. He was right, and two
defects in ADDENDUM 1 explain the gap. Both are mine.

### 0.1 I tested the wrong statistic

The standing criterion in this programme is a positive **GROSS mean per trade above the nulls.**
ADDENDUM 1 compared **P(target)** against the null and then reported the **observed** P&L. It never
computed the null's P&L. Those are different tests, and the mechanism in the gap is real:

**A hitting probability is structurally blind to a small drift.** Reversion of 0.04σ cannot move
P(target) measurably, but it is exactly what a P&L comparison would see. ADDENDUM 1's headline —
"the arrangement of the signs adds nothing" — was an artefact of the instrument, not a fact about
the market.

### 0.2 My classifier was pointed the wrong way

`crossings ≥ 2` of the **held** level means price oscillated about the *previous* window's line
extrapolated forward — i.e. **the extrapolation worked**, which is trend persistence. I was
selecting continuation and then betting on reversion. It is the **worst** of the ten cells, and at
s=3 it is −4.52 ticks below its own null (t −1.69) and g(20) = **−0.3253σ**.

### 0.3 And a third: both fill conventions are biased, by comparable amounts

On a sign-shuffled path optional stopping forces gross expectancy to be **exactly zero** for any
bounded stop/target rule. Measured on 12,976 null trades:

| convention | gross | vs truth |
|---|---:|---|
| REAL — exit at the mid on the bar the stop was breached | **−1.819** tk | −14.0 SE |
| IDEAL — exit at the stop price | **+1.037** tk | +8.0 SE |

They **bracket** zero, width 2.86 ticks. On real data the null's realised-fill gross runs −2.3 to
−9.2 ticks for the same reason (mean loss is ~1.6× the stop distance). **So ADDENDUM 1's "NET real
−6.77" was mostly convention, not performance.** Only a real-vs-null difference taken at the *same*
convention is meaningful, and both are carried below.

---

## 1. The corrected result: reversion exists

`g(k) = −s·(P[t+k] − P[t])/σ`, so `g > 0` is reversion. Real minus its own sign shuffle, over
**every** admitted excursion — no exit rule, no overlap rule, no fill convention, hence ~100× the
sample of a P&L test. Drift-aligned (`s·slope < 0`, the principal's rule), 2σ entry, flat-mean
level, no classifier.

| scale | n_exc | g(1) | t | g(5) | t | g(10) | t |
|---|---:|---:|---:|---:|---:|---:|---:|
| s=1 | 35,816 | **+0.0410σ** | **+3.9** | +0.0430 | +2.0 | +0.0570 | +1.9 |
| s=3 | 11,660 | **+0.0276σ** | +1.6 | +0.0578 | +1.5 | +0.0405 | +0.7 |

Same sign, same order of magnitude, at two scales, on a block bootstrap over (root, day) sessions.
**Price does revert after an aligned 2σ extreme.** This is the cell that required no selection —
the loosest one — so it carries no multiplicity debt.

## 2. And it is 4–8× too small

| scale | mean σ | mean cost | g(1) | g(5) | g(10) |
|---|---:|---:|---:|---:|---:|
| s=1 | 7.64 tk | 2.415 tk/RT | +0.313 tk = **13.0%** of a round trip | +0.328 = 13.6% | +0.435 = 18.0% |
| s=3 | 10.63 tk | 2.422 tk/RT | +0.294 tk = **12.1%** | +0.615 = 25.4% | +0.431 = 17.8% |

The geometry agrees. MFE/MAE over the next 20 bars — the ratio **any** target/stop rule inherits,
and therefore prior to choosing one — is **1.011 against a null of 1.000** in the high-power cell.
**A 1% geometric asymmetry cannot pay a round trip that costs 7–30% of the target distance.**

### 2.1 This corrects ADDENDUM 1 §3, which asked the wrong question

ADDENDUM 1 concluded "the trade is not a cost failure, so no cost-side fix can reach it", because
perfect reversion pays `|y|` — median 31 ticks against 1.06–4.99 of crossing, i.e. 7–30×.

**That is true and it is the wrong question.** The *realised* excess is 0.3–0.6 ticks, about **2% of
the perfect-reversion payoff.** So the principal's feasibility test is correct as a **necessary**
condition and is **non-binding by a factor of roughly 50** at this operating point. It cannot
discriminate here. **The construction IS cost-bound — on its realised edge, not on its
hypothetical one.**

## 3. No classifier improves it, and the best-looking one does not replicate

Every filtered cell has a **lower** t than the unfiltered cell: they cut n by 10–200× without
raising the per-excursion effect.

| cell | s=1 MFE/MAE real / null | s=3 MFE/MAE real / null |
|---|---|---|
| none, flat (n 35,816 / 11,660) | 1.011 / 1.000 | 0.989 / 1.000 |
| cross2, line — **mine** | 1.034 / 0.994 | **0.930 / 0.998** |
| ac1neg, flat | 1.054 / 0.978 | 0.860 / 0.976 |
| **traverse, flat** (n 169 / 50) | **1.369 / 1.040** | **0.788 / 1.014** |
| traverse, line (n 672 / 212) | 1.104 / 1.000 | 0.920 / 1.016 |

`traverse` — the principal's "reliability with which price travels the full width of the range" —
is the best cell at s=1 by a distance, with real overshoot 2.687 against a null of 3.130, and
g(20) = +0.873σ. **It inverts at s=3**, on n=50 and n=212. Best t across all 20 cells was +1.67.
**That is the tail of twenty looks, and it is recorded as such rather than promoted.**

The one directionally consistent secondary reading: **the flat-mean level beat the trend-extended
one on the P&L difference in 8 of 10 classifier×scale pairs**, which supports the concern that
`lvl = a₂ + b₂·H` inflates `|y|` under the alignment rule — extrapolating the line pushes the level
*away* from the price. Not significant individually; consistent in sign.

---

## 4. Disposition

**The construction stays closed, but for the opposite reason to the one ADDENDUM 1 gave.** Not
"there is nothing there" — there **is** something there, at t +3.9 in the highest-power cell, and
it replicates in sign and magnitude at a second scale. It is simply **4–8× below the crossing
cost**, and no filter tested raises it.

**ADDENDUM 1's headline claim is withdrawn.** "The arrangement of the signs adds nothing" is false;
the arrangement is worth about +0.04σ per aligned extreme. What is true is that it is worth about
a third of a tick.

**Still no component line**, and now for a measured reason rather than an assumed one: the edge is
+0.3 to +0.6 ticks against 2.4 of cost, so net per-trade expectancy is negative at any size the
account can trade.

### 4.1 What this changes about the route

The **passive** route named in ADDENDUM 1 §8.2 is now quantified rather than speculative, and the
arithmetic is no longer hopeless. The edge is 12–25% of a *crossed* round trip. A construction that
crosses neither side does not pay that 2.4 ticks — it pays adverse selection and non-fills instead,
which are **unmeasured here.** So the question is precise: **does resting both sides retain more
than ~25% of a crossed round trip's cost?** If yes the edge is live; if no it is not. That is a
measurement on `tbbo`/`mbo`, not another detector.

### 4.2 What does NOT follow

- **No classifier is worth carrying forward** on this evidence, including the principal's
  `traverse`, until it survives a scale at which it has power. Its s=1 numbers are the largest in
  the study and they invert at s=3.
- **The axis is not closed** (only the principal closes an avenue), and this addendum closes one
  construction plus one *statistic* — P(target) should not be used again for this question.
- The reserved slice is **not spent** and is not the right instrument for a sub-cost effect anyway:
  confirming a 0.3-tick edge out of sample would establish something true and untradeable.

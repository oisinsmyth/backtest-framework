# D303 RESULT — the reference is adopted, and the band is not

**Status:** RESULT. Pre-registered at `c5dbfce`, runner at `a4c23f5`, fixed at
`653a3cb`, all committed before this file existed (R8).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 1. The decision

**`excess@matched/flat` is adopted as the base for D300, D304, D305 and D306**,
by the decision rule declared before the numbers were seen:

> *indistinguishable → adopt the referenced rule anyway, on correctness grounds.*

It is indistinguishable. The paired per-bar difference is **−0.49 bp at
t = −0.42** on 3,187 common bars — the referenced rule is very slightly behind
on the mean and nowhere near separable.

| | raw@1.0/flat | **excess@matched/flat** |
|---|--:|--:|
| gross bp/bar | +12.49 | **+12.00** |
| t | +2.94 | +2.84 |
| Sharpe | +0.828 | +0.799 |
| **maxDD** | 9,548 | **8,320** (−13%) |
| **years profitable** | 11 of 14 | **13 of 14** |
| triggers | 12,226 | 12,226 (matched exactly) |
| p vs its own null | 0.0050 | 0.0100 |

**It gives up 0.49 bp of mean and buys a 13% smaller drawdown and two more
profitable years.** That is not a result — the mean difference is noise — but it
is the correct specification, and adopting it costs nothing measurable.

**The calibrated multiplier is 0.9627** (flat) and 0.9687 (sqrt), matching the
raw rule's trigger count to **+0.00%**. Q7 confirmed: below 1.0, because
idiosyncratic vol is smaller than total vol — though only by 4%, which is itself
the 6.1% variance share showing up in the scale.

## 2. Q1 — the runner measured the wrong quantity, and the right one confirms

The runner reported **Jaccard 0.432**, against D297's premise measurement of
**0.721**. That looked like a load-bearing prediction failing. It was not.

**D297's premise decomposed a FIXED holding path** — it asked, of each held
position-bar, whether an idio-referenced rule would fire on that same position.
**D303's two rules produce different books**: once one exits a position the
other keeps, the holdings diverge and the exit sets are drawn from different
populations. The two numbers measure different things.

`scripts/d303_q1_split.py` separates them:

| | flat | sqrt |
|---|--:|--:|
| positions held by raw | 30,239 | 28,260 |
| positions held by excess | 30,242 | 28,251 |
| **held by BOTH** | 21,746 (56.1%) | 21,096 (59.6%) |
| jaccard over all triggers *(what the runner reports)* | 0.432 | 0.425 |
| **jaccard on SHARED positions** *(comparable to 0.721)* | **0.732** | **0.691** |

**0.732 against D297's 0.721.** Q1 is confirmed once measured on the comparable
quantity, and the implementation is the object D297 measured.

**And the gap between the two numbers is itself the finding.** The rules agree on
**73%** of the decisions they both face, and the books still end up sharing only
**56%** of their positions. Small per-decision differences compound: a divergent
exit frees a slot that refills differently, and the paths separate from there.
Any future comparison of two exit rules on this book has to say which of the two
quantities it is reporting.

## 3. The √age band fails, and it was my addition

| cell | gross | Sharpe | triggers | age at trigger | p |
|---|--:|--:|--:|--:|--:|
| raw@1.0/**flat** | +12.49 | +0.828 | 12,226 | 2.54 | **0.0050** |
| excess@matched/**flat** | +12.00 | +0.799 | 12,226 | 2.53 | **0.0100** |
| excess@1.0/**sqrt** | +9.20 | +0.611 | 6,559 | 2.08 | 0.363 |
| raw@1.0/**sqrt** | +8.18 | +0.553 | 6,911 | 2.07 | **0.746** |
| CONTROL | +7.54 | +0.512 | — | — | — |

**Every √age cell fails its own null**, and the raw one fails it completely at
p = 0.746 — barely above the control. The constant-Z band takes 4.3 bp off the
gross and the p-value from 0.005 to 0.75.

**Q4 is therefore half-failed**: both flat cells clear their nulls, neither sqrt
cell does.

**Q5 is falsified in direction.** I predicted the √age band would fire *later* in
a position's life. It fires **earlier** — mean age 2.07 against flat's 2.54 — and
the mechanism is obvious in hindsight: the two bands are equal at age 1 and the
√age band is *wider* thereafter, so it triggers a subset of flat's triggers,
namely the early ones. The lower trigger share (6,911 vs 12,226) was predicted
correctly; the direction of the age shift was not.

**What this means for D305.** The band was added to this study to protect the k
sweep, on the argument that a flat threshold on a cumulative sum gets
mechanically easier to hit as a position ages. That argument is unchanged and
still applies at k = 20. But **the band cannot be carried into D305 as the
default when it fails its null at k = 5.** D305 must run both shapes at every
`k`, with the flat band as the incumbent, and the √age band earns its place only
if the crossover it predicts actually appears.

## 4. Q6 — mixed, and reported as mixed

The referenced rule's advantage by market-volatility tercile (excess@matched
minus raw, bp/bar):

| band | low | mid | high |
|---|--:|--:|--:|
| flat | +0.99 | **−3.48** | +1.01 |
| sqrt | +0.11 | −0.82 | **+3.46** |

I predicted the advantage would concentrate in the top tercile — the only regime
where a 6.1% variance share is large enough to move a decision. **That holds
clearly for the √age band (+3.46) and not for the flat band**, where the biggest
effect is a *disadvantage* in the middle tercile. On three cells with no null
behind them, this is a hint and not a finding.

## 5. Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | Jaccard 0.65–0.80, reproducing 0.721 | **CONFIRMED at 0.732** — but only once measured on shared positions; the runner's own metric was the wrong one |
| **Q2** | referenced gross within ±15% of +12.49 | **CONFIRMED** — +12.00, −3.9% |
| **Q3** | neither beats the other, p > 0.05 paired *(against)* | **CONFIRMED** — largest \|t\| across four comparisons is 0.89 |
| **Q4** | both clear their own null | **HALF FAILED** — both flat cells do, neither sqrt cell does |
| **Q5** | √age fires later, lower trigger share *(against)* | **HALF FALSIFIED** — trigger share yes, direction no: it fires *earlier*, 2.07 vs 2.54 |
| **Q6** | advantage concentrates in high market vol *(against)* | **MIXED** — clear for sqrt (+3.46), absent for flat |
| **Q7** | matched multiplier below 1.0 | **CONFIRMED** — 0.9627 and 0.9687 |

## 6. A bug in the first run, caught by its own output

The first run reported a matched multiplier of **0.0200 producing ZERO
triggers** against the raw rule's 12,226. A smaller threshold giving fewer fires
is impossible, which is what made it visible.

`calibrate()` called `simulate(..., want_x=False)` on the **excess** rule. That
flag skips accumulating `cum_x` — precisely the quantity the excess rule tests —
so the rule never fired and the bisection ran to its lower bracket.

**The optimisation was correct for what it was written for.** The null uses
`sampled_runs`, which never reads `cum_x`, and assertion [6] proved that path
bit-identical. What [6] did not do was test the flag on the rule where it *is*
wrong. **A guard that covers only the case where a flag is safe is not a guard.**

Fixed at `653a3cb`: `simulate()` refuses `want_x=False` with `ref="excess"` at
the door, and [6] now requires that refusal *and* that the excess rule actually
fires. Void from the first run: the two `excess@matched` cells and the two
Jaccards involving them. Unaffected: `raw@1.0/*`, `excess@1.0/*`, all six nulls,
and the assertion block.

## 7. Cost, unchanged and still decisive

Held-name half-spread **mean 65.05 / median 26.67 bp, 41.5% clamped to zero** —
reproducing D302 to two decimals. Round trip **106.7 bp** on the median, which
D302 established is the defensible figure; the 260.2 mean is a truncation
artefact.

**Every cell is net-negative**: the adopted base is **+12.00 gross against 26.67
cost = −14.67 bp/bar**, a ratio of **0.450**, needing **2.22×**. The reference
fix did not move that and was never going to — it is a correctness step, not a
lever.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: 7 declared cells, each against its own holding-run-matched null at
200 draws, plus four paired comparisons. Four cells clear p < 0.05 against 0.35
expected — but they are two books measured twice (flat raw and flat excess,
which are 73%-agreeing variants), not four independent findings.

## Stop

**The reference question is closed.** The referenced rule is adopted; it is
indistinguishable from the incumbent and is the correct specification.

**The band question is open and moves to D305**, where it must be run at every
`k` rather than assumed.

**Next: D300, book width**, on the adopted base — though note D300's Arm 1 runs
with no exits at all, so the adopted rule does not enter it.

## Files

`data/d303_reference.json` · `scripts/run_d303_reference.py` ·
`scripts/d303_q1_split.py` · `temp/d303_run.log`

# D312 — vol-targeted breadth

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## Why, and why despite an argument against it

Three studies have closed a time-varying concentration — D299's ladder, D308's
discrete width, D311's continuous λ — and all three asked the same question:
**which breadth EARNS most right now.** D311 measured why that fails:

```
N_eff = 2 vs N_eff = 10
  MEAN difference   +3.94 bp/bar    full-sample  t = 0.42
  VOL  difference  +310.35 bp       across-block t = 6.37
```

**Volatility is measured about fifteen times better than the mean.** A rule keyed
on the thing with `t = 6.37` is a different proposition from one keyed on the
thing with `t = 0.42`.

**This study asks a risk question, not a return-timing question:** hold the
book's volatility near a target by varying breadth — widen when risk is above
target, concentrate when below.

**I argued against running it and the principal overruled that, correctly.** My
argument was that widening to cut risk also dilutes the edge, whereas scaling
exposure cuts risk without touching it, so exposure-scaling weakly dominates —
and exposure-scaling is D297's overlay, which D306 measured as helping a wide
book (+0.213 Sharpe at N=19) and hurting a concentrated one (−0.153 at N=2).
**That is an argument, not a measurement, and this programme has a record of
arguments that did not survive contact with a null.** So the domination claim is
made a *declared arm* rather than a premise.

## The three arms, all matched on realised volatility

| arm | mechanism |
|---|---|
| **F — fixed** | constant `N_eff`; volatility floats. The baseline |
| **B — vol-targeted breadth** | vary `N_eff` to hold book vol near target; always fully invested |
| **E — vol-targeted exposure** | constant `N_eff`, scale exposure to hold book vol near target |

**E is the arm that tests my own argument.** If it dominates B, the argument was
right and breadth is the wrong risk lever. If it does not, the argument was
wrong.

## The rule, and it must be causal

At each bar, using **only data through `t−1`**:

```
for each N_eff level:  v_j(t)  =  trailing 63-bar sd of that level's book return
B: choose the level whose v_j(t) is closest to the target
E: hold the baseline level, scale exposure by  target / v_base(t),  capped at 2.0
```

**The vol-versus-breadth relationship is re-estimated in the trailing window at
every bar, never fitted once on the full sample.** Assertion [3] holds this to a
peeking variant that must differ.

**Targets are declared, not searched:** the four full-sample volatilities of
`N_eff` ∈ {2, 5, 10, 19} from D310. Each vol-targeted arm is then compared to the
**fixed level that has that same average volatility** — matched on realised risk,
so the only question is whether *holding* risk constant beats *letting it float*.

**4 targets × 3 arms = 12 cells.** `N_eff` moves on the D311 grid of 15 levels;
transitions charged from the weight vectors as `Σ|Δw|/2 × rt`.

## Statistics

**Sharpe is primary here**, unusually for this programme, because the arms are
matched on average volatility and the question is what that buys. **Net bp/bar is
reported beside it**, and so is **realised vol dispersion** — the sd of the
trailing-63 vol series — which is what the rule is actually controlling and the
only thing it is certain to move.

Cost uses each cell's own held-name round trip; the mean-based figure is carried
as the truncation artefact D302 showed it to be.

## The null

**Circular rotation of the realised `N_eff` path** (arm B) and of the exposure
path (arm E): same number of moves, same sizes, same persistence, applied at
unrelated times. That asks whether **de-risking WHEN THE BOOK IS ACTUALLY VOLATILE**
beats de-risking for the same amount, in the same pattern, at random moments.

**This is D297's null and it is the right one here**, where D308c's Jensen-gap
null was right for an oracle. **The two answer different questions and are not
interchangeable** — this study has no oracle and no max-picking, so there is no
Jensen gap to price.

200 draws, both statistics, BH-FDR at q = 0.10 across the 12 cells.

## Predictions

Three are against.

| | prediction |
|---|---|
| **Q1** | every vol-targeted cell's realised vol lands within 10% of its target — mechanical; if not, the rule is not doing what it is named |
| **Q2** | both B and E cut the **dispersion** of realised vol by more than half against F. Also mechanical, and the only effect guaranteed |
| **Q3** | **E beats B on net at every target.** *This is my own argument, entered as a prediction so it can be falsified* |
| **Q4** | **B does not beat the vol-matched fixed level on Sharpe at any target.** *Against the study* — **load-bearing** |
| **Q5** | **the `N_eff` path under B IS persistent** — lag-1 ρ above 0.5 — because market volatility is persistent. This is the mechanical difference from D308 and D311, whose return-optimal paths were anti-persistent or barely autocorrelated |
| **Q6** | transitions cost under 5% of gross, since λ moves smoothly — D311 measured 2.5% |
| **Q7** | **at the tightest target, E hurts**, reproducing D306's −0.153 Sharpe from the overlay on a concentrated book. If E helps there instead, D306's overlay finding needs revisiting |
| **Q8** | B beats F on Sharpe at the **widest** target and not at the tightest — vol control is worth more where the book is already diversified |

Q4 is load-bearing. **Q3 and Q7 are my own reasoning entered as falsifiable
claims**; if both fail, the case against this study was wrong and the record
should say so plainly.

## Stop conditions

- **Q4 confirms and Q3 confirms** → breadth is the wrong risk lever, exposure is
  the right one, and the family closes with the argument vindicated.
- **Q4 confirms and Q3 fails** → neither lever works on this book; close, and the
  reason is the book rather than the lever.
- **Q4 fails** → vol-targeted breadth earns something, and it needs its own
  confirmation before anything else: benchmarked against the vol-matched fixed
  level, never against the incumbent.
- **Q1 fails** → the rule is misimplemented and nothing else is read.

## Assertions

1. **[1] Reproduction.** Arm F must reproduce D310's and D311's published cells
   at every shared level, to floating point.
2. **[2] The target is hit.** Realised vol within 10% of target for every
   vol-targeted cell, and the *fixed* arm's vol must differ from its target by
   more than the targeted arm's — otherwise there was nothing to control.
3. **[3] CAUSALITY.** The rule uses only data through `t−1`, and a deliberately
   peeking variant that uses bar `t`'s own return in the vol estimate **must
   produce a different book**. A causality audit that cannot fail proves nothing.
4. **[4] Transitions** are zero when `N_eff` never moves and monotone in
   |Δ log N_eff|.
5. **[5] Every cell is a distinct book.**
6. **[6] The null matches** — rotated paths have the same move count and the same
   |Δ| distribution as the treatment's, to within sampling error.
7. **[C] Cost dimensions** against d295's published 52.1893, doubled form
   rejected.
8. **[7] The self-test raises** on a deliberately broken book, corrupting bars
   inside the mask.

## Scope

**Out:** the exits — D306 showed them separable from width and D310's target arm
is contaminated by a cooldown; the entry signal; the gate; `k`; and any
return-conditioned choice of breadth, which D299, D308 and D311 have closed
three times.

**This study varies breadth on RISK, never on expected return.** If it works it
works for that reason, and the record should not be read as reopening the
return-timing question.

## Files

`docs/decisions/D312-vol-targeted-breadth.md` (this record) · runner and data to
follow, in separate commits.

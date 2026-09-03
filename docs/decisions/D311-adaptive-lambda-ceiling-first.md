# D311 — adaptive λ, ceiling first

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## The question

D310 built a book whose concentration is one continuous parameter — exponential
weights `w_j ∝ exp(−λ j)`, reported as effective breadth `N_eff = 1/Σw²` — and
**held λ fixed for the whole sample**. The realised `N_eff` is constant to three
decimals, every year. Nothing compresses or relaxes.

**Should it?** The intuition is that a cross-sectional edge is worth
concentrating into when the cross-section is dispersed and worth spreading when
it is not.

## WHY THIS IS NOT ALREADY CLOSED BY D308

D308 tested a time-varying **discrete** width and closed on a ceiling null: the
oracle's gain over the best static width was **below** what a structureless draw
with the same means, sds and correlations produced — 113% to 145% of it — at
every horizon from 21 to 504 bars.

**Its oracle explored seven discrete books and nothing else.** A continuous λ is
a different object in one way that matters: **a small change in a conditioner
produces a small change in the weights**, where D308's argmax jumped between
corners. Estimation noise translates into position drift rather than into
switching 19 names for 2.

**The expectation is nonetheless that this closes the same way.** The Jensen-gap
argument does not care whether the choice set is discrete or continuous, and the
finer the grid the *larger* the gap from picking a max. **That is what Stage 1
tests, and it is why Stage 1 runs first.**

## Stage 1 — THE CEILING, WITH ITS NULL, BOTH IN THE SAME STAGE

D308's pre-registration said *"Stage 1 has no null: an oracle is an upper bound
by construction."* **That was wrong** — true of the oracle, false of the gain over
the baseline, which is the reported number. It cost a result that had to be
corrected. **Here the null is part of Stage 1 and no ceiling is reported without
it.**

```
oracle(f)  =  choose λ with hindsight, once per f bars, to maximise the objective
ceiling    =  oracle net  −  best FIXED λ net
```

**Decision frequencies `f` ∈ {21, 63, 126, 252}.** Transitions charged throughout,
solved exactly by Viterbi over the λ grid rather than greedily.

### The λ grid

**15 levels of `N_eff`: 2, 2.5, 3, 4, 5, 6, 7, 8, 10, 12, 14, 17, 20, 22, 25.**
Finer than D308's seven, deliberately — it is what "continuous" means in
practice, and **a finer grid makes the noise ceiling larger, not smaller**, which
the null must and does absorb.

### The null, and it is D308c's fourth construction, not its first three

**Multivariate normal on the observed mean vector and covariance matrix of the
block-net series.** Means, sds and the cross-λ correlations preserved; no timing
structure by construction.

**Three constructions were tried in D308c and failed, and they are not to be
retried:**

| | why it failed |
|---|---|
| standardise per level, permute across levels within a block | preserves marginals only in expectation — 364 bp of mean drift on 51 blocks |
| two-way ANOVA on the level×block interaction | 43.6% sd drift; the block main effect is dominated by the most concentrated level's own volatility |
| independent circular rotation per level | marginals exact but co-movement destroyed, 0.755 → −0.002, inflating the max so far that every cell returned p = 1.0000 |

**The lesson, carried forward explicitly: the oracle's gain does not depend on
the temporal ORDER of blocks at all.** It is a within-block cross-sectional max,
so permuting rows changes nothing. **Any null that destroys order is answering a
question the oracle never asked.** The quantity to null is the Jensen gap of the
joint distribution.

## Stage 2 — PERSISTENCE, measured on a continuous parameter

**λ is ordinal and continuous, so exact-match run length is the wrong statistic.**
D308 used it and it treated `N=2 → N=3` as exactly as much of a switch as
`N=2 → N=19`; the ordinal measures then disagreed with it on two of four
families.

Reported here: **lag-1 autocorrelation of `log N_eff*(block)`**, **mean
|Δ log N_eff|**, and both against a shuffle of the same path. Run length is
reported as a secondary diagnostic only.

**A conditioner can only help if λ*(t) persists longer than a transition takes to
amortise** — and transitions are far cheaper here than in D308, which is this
construction's one real advantage and is measured rather than assumed.

## Stage 3 — CONDITIONERS, only if Stages 1 and 2 both survive

**Target variable is the concentration premium**, not the level of returns:

```
premium(t)  =  A(N_eff=2, t)  −  A(N_eff=25, t)
```

**Four conditioners, declared, all lagged:** cross-sectional return dispersion
(X1), signal separation between rank 2 and rank 19 (X2), breadth (X3), and
X1 × X2 (X4). Spearman against `premium(t)`, each versus a **circular rotation
of the conditioner** — these are strongly autocorrelated and a textbook p-value
assumes independence that does not exist. BH-FDR at q = 0.10 across all
combinations.

**Stage 3's output is a hypothesis.** No rule is built in this study.

## Scope — one family, and why

**The exits are out entirely.** D306 established width and exits separable, and
D310's target arm is contaminated: its exit blocks a name for `k` bars, which is
D305's cooldown rather than D306's immediate re-entry, and D305 measured that as
harmful. **One family (`none`), one axis (λ), no confound.**

Also out: the entry signal, the gate, `k`, and the no-trade band, which D310
showed only bites above `N_eff` ≈ 10 and would add an axis to a study that
already has two.

## Statistics

**Net bp/bar and Sharpe, both primary and reported separately.** They disagree
and will give different λ*(t) paths — D310 put net's optimum at `N_eff = 2` and
**Sharpe's at `N_eff = 10`**, where the exponential scheme showed the clean hump
the hard cut was too jagged to reveal.

Cost is `Σ|Δw|/2 × rt` per leg per bar, with `rt` on the names actually held.

## Predictions

Four are against.

| | prediction |
|---|---|
| **Q1** | the uncharged oracle beats the best fixed λ by > 30 bp/bar at f=21 — mechanical, a harness check |
| **Q2** | **the charged oracle's gain is BELOW the MVN null's median at every f.** *Against the study* — **load-bearing**, and it is what D308c found for the discrete case |
| **Q3** | **transitions cost under 20% of the uncharged gain at f=21** — far less than a discrete 19→2 jump, because λ moves the weights smoothly. This is the construction's one genuine advantage over D308 |
| **Q4** | **lag-1 autocorrelation of log N_eff\*(block) is under 0.20 at f=63** *(against)* |
| **Q5** | the 15-level grid produces a **larger** raw ceiling than D308's 7-level did, at matched f — more alternatives, bigger max. A check that the Jensen mechanism is understood, not a finding |
| **Q6** | **no conditioner survives BH at q = 0.10** *(against)* |
| **Q7** | X1, cross-sectional dispersion, is the strongest of the four |
| **Q8** | **the Sharpe-optimal λ path is more persistent than the net-optimal one** — Sharpe is the smoother statistic. D308 predicted this and never evaluated it |

Q2 and Q4 are load-bearing.

## Stop conditions

- **Q2 confirms** → **close.** The ceiling is noise and no conditioner can beat
  it. Stages 2 and 3 do not run.
- **Q4 confirms** → close, whatever Stage 1 showed.
- **both fail** → Stage 3 runs, and its output is a hypothesis needing its own
  pre-registration, benchmarked against **the best fixed λ** — never against the
  incumbent, or it banks D310's concentration result as its own.

## Assertions

1. **[1] Reproduction.** At fixed λ, every level in D310's grid must reproduce
   D310's published net and Sharpe to floating point.
2. **[2] The degenerate oracle.** An oracle allowed one λ for the whole sample
   must **equal the best fixed λ exactly**.
3. **[3] Transitions** are zero when λ never moves and **monotone in
   |Δ log N_eff|**.
4. **[4] Nesting.** Uncharged, a shorter `f` cannot be worse than a longer one.
5. **[N1]** the null's draws reproduce each level's mean within sampling error,
   **[N2]** its sd within 10%, and **[N3]** its cross-level correlation within
   0.02 — the three checks that took D308c four attempts to satisfy.
6. **[C] Cost dimensions** against d295's published 52.1893, doubled form
   rejected.
7. **[7]** the self-test raises on a deliberately broken book, corrupting bars
   **inside the mask**.

## Files

`docs/decisions/D311-adaptive-lambda-ceiling-first.md` (this record) · runner and
data to follow, in separate commits.

# D291 — Confluence at stage 1: gate and veto, both pure selection

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-02
**Area:** Strategy research · **personal track**

**Stage 1 spends nothing scarce. Nothing is closed, nothing is promoted, and the
holdout is not read.**

---

## Why this is not a repeat of the D288 post-closure probe

That probe tested **symmetric equal-N AND gates** — top-25 ∧ top-25 — which is
the one parametrisation guaranteed to collapse. `N²/M` left **0.76 names per
bar**, 16 of 18 partners degenerated to 1–2 names, and **0 of 18 beat their
size-matched control.** It failed on parametrisation, not on the idea.

Three things have also changed since:

- **Capturability is now a gate** (1e). Building confluence on `close_in_range`
  or `lower_wick` is dead on arrival — their edges are 100% overnight and vanish
  at open entry. Filtering an artifact more precisely still yields an artifact.
- **Gate 1g measured a specific defect worth vetoing**: `price_log`'s long leg is
  **33.5% dead names against 10.7% short**.
- **The control for a veto is not a smaller N.** It is *random removal of the
  same count*, which is a materially better comparison.

## Selection, not sizing — and this fixes the operator

The book is **equal-weight within each leg**, so magnitude is discarded at the
sizing step regardless. A blended score would change *which* names are picked and
then the book flattens all of them to the same weight — an incoherent use of the
information. Magnitude earns its keep by changing position **size**, and size is
stage 3.

| level | operation | uses |
|---|---|---|
| **stage 1 (here)** | **gate** and **veto** — selection | the ordering |
| stage 3 | weighted blend, conviction scaling | the magnitude |

**A NEGATIVE RESULT HERE DOES NOT CLOSE THE BLEND.** If the mechanism is
measurement error — two noisy reads of one thing — the gate is a *strictly worse
estimator* than the blend, because it keeps the sign and throws away the
magnitude. Reading "gating failed" as "combining adds nothing" would repeat
D288's error of killing a candidate with the wrong instrument. **Stated here, in
advance, as a limit on what this study can conclude.**

## The pool: capturable only

Thirteen tier-1 spread candidates from D290 — `min z > 0` on all three nulls,
`CV t > 0`, and **open-entry `t` ≥ 2**:

`choch_dist`, `dist_52w_high`, `dist_lvn`, `hist_L`, `macd_hist`, `macd_line`,
`on_persist`, `price_log`, `retrace_leg`, `rev_21`, `rev_5`, `rsi`, `skew_63`.

Their within-bar Spearman matrix is measured over **570,770 name-bars where all
thirteen are finite** (`data/d291_pair_matrix.json`). D290's earlier probe covered
only the top 14 by CV and left 4 of these unpaired.

**Measuring this matrix is not a look at the holdout or at returns.** It is a
correlation between two *scores*; no return enters it. It is what makes the rules
below declarable with a knowable count instead of a guess.

**Effective independent dimension: 4.89 of 13** (participation ratio of the
correlation eigenvalues). Roughly five distinct things wearing thirteen names —
which is exactly why the multiplicity floor must be empirical rather than a
Bonferroni over 272.

## Deciding: a declared RULE, not a hand-picked list

Hand-picking pairs after seeing D290's numbers is post-hoc and unpriceable. A
rule is declarable in advance and its count is knowable, so a floor can price it.

| | rule | mechanism |
|---|---|---|
| **G — gate** | ρ ∈ **[0.35, 0.65]**, both capturable | the measurement-error window: high enough that they read the same thing, low enough to add information. `A = S + e₁`, `B = S + e₂` gives ρ = var(S)/(var(S)+var(e)), so this band is roughly half common signal |
| **V — veto** | A has a **dead-leg gap > 10pp**; B has **\|ρ\| < 0.30** to that A | B must measure something A does not — **risk, not return**. A veto needs only to identify a *bad subset* of A's picks, which is a far weaker requirement than B having its own edge |

**Both thresholds were fixed on the partial matrix and were not moved after the
full one was measured.**

**Rule G resolves to 23 pairs in band.** The construction is asymmetric in A and
B, so each is two ordered cells → **46**. Top of band: `hist_L + macd_hist` 0.64,
`retrace_leg + rev_21` 0.63, `rev_5 + rsi` 0.62, `choch_dist + dist_52w_high`
0.61.

**Rule V resolves to exactly three A's**, the only candidates whose long leg
holds materially more delisted names than its short leg:

| A | long dead | short dead | gap | filters B |
|---|---:|---:|---:|---:|
| `price_log` | 33.5% | 10.7% | **+22.9pp** | 11 |
| `dist_52w_high` | 36.7% | 20.3% | **+16.4pp** | 5 |
| `choch_dist` | 37.9% | 27.0% | **+10.9pp** | 6 |

→ **22 veto cells.**

**68 cells × 4 thresholds = 272.** The sweep is **f ∈ {0.9, 0.75, 0.5, 0.25}** —
the fraction of B's ranking retained. Survivors ≈ N × f, so at N=25 and f=0.5 the
book holds ~12 names rather than the 0.76 that sank the D288 probe.

**Disclosed:** the gate pairs cluster in one momentum family. 272 cells is not
272 independent tests, which is the whole reason the floor is drawn from the
null's own joint distribution below.

## Testing: the PAIRED DIFFERENCE is the statistic

The D288 probe reported the confluence's own number and compared it to the
control by eye. That is the wrong test.

```
per bar:   Δ[t] = confluence_return[t] − control_return[t]
statistic: t on Δ
```

Paired bar by bar, so the common market move cancels. **The confluence's own `t`
is NOT the statistic. Δ is.**

| operator | control |
|---|---|
| **gate** | A alone at **N′ = the mean surviving count**, paired bar by bar |
| **veto** | **random removal of the same count** from A's leg, repeated **50×** for a distribution; the veto is placed in it as a permutation p-value. One random draw is noise |

**The confluence-specific null:** rotate **B** within its own live bars, hold A
fixed. Preserves B's turnover and coverage, destroys only its alignment — so it
asks whether B's *content* matters or whether any B-shaped filter would do. None
of D290's three nulls asks this.

**Sequencing, to keep the compute honest and bounded:** condition 1 is cheap and
runs on all 272. The rotate-B null runs on all 272 as well — it has to, because
the floor is its joint max. Open-entry re-tests run only on cells that clear
both.

## Pass conditions — all four

1. **Δ > 0 with paired `t` ≥ 2** against its own control
2. beats the **rotate-B** null
3. **still capturable** — open-entry `t` ≥ 2 after filtering
4. above the **empirical best-of-272 floor**: run the rotate-B null across **all
   272 cells at once**, take the **max Δ-`t` per draw**, and require the observed
   cell to clear that distribution's **95th percentile**. Because the draws share
   the real correlation structure, this prices 272 correlated tests *correctly* —
   a Bonferroni over 272 would over-penalise ~5 effective dimensions, and an
   uncorrected `t ≥ 2` would under-penalise them. **One object serves both
   condition 2 and condition 4**

**Reported, never gating:** turnover per bar, mean holding run, dead-name share
per leg (1g), and where the peak sits in the sweep (1i).

**Validity check, run first:** gating A with itself must reproduce A exactly. If
it does not, the harness is wrong and no cell below is readable.

---

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **Q1** | **NO cell beats its control at paired t ≥ 2.** 0 of 18 did in the D288 probe, and the honest prior after that is that better parametrisation does not change the answer | **AGAINST** | **moderate-high** |
| **Q2** | **The veto outperforms the gate**, because a veto needs only to find a bad subset while a gate needs B to carry its own edge | for veto | moderate |
| **Q3** | The dead-name veto **cuts the long-leg dead share by ≥ 10pp**. A mechanical check: if the veto does not do what it claims, its result is uninterpretable | for | high |
| **Q4** | **Any cell that beats its control FAILS the rotate-B null** — the gain is concentration, not B's content | **AGAINST** | moderate |
| **Q5** | **No cell clears its measured cost**, even where it beats its control | **AGAINST** | moderate-high |

**Q1 and Q4 are the load-bearing ones**, and both are against the construction.
**What would falsify Q4: a cell beating its control that also beats a rotated B** —
that would be the first evidence in this programme that two signals carry more
than one.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

In-sample looks disclosed and not priced, per D289's amended convention: **272
cells** (68 declared ordered pairs × 4 thresholds), on top of D290's 51 and its
post-hoc probes. The count is large and **declared before the runner exists**,
which is precisely what lets condition 4 price it. **No primitive here has touched the holdout**; every candidate remains
holdout-eligible.

## Stop

**If nothing beats its control, gate and veto are closed for this pool** — no
third operator, no re-cut of the rules, no widened ρ band.

**And that closure does not extend to the blend**, for the reason stated above.

## Not attempted here

Three-way and higher confluence, threshold selection on a single score (tested
and rejected at `ad0eb05` — the day's score gap does not predict the day's
return), and the cost-side universe filter, which shrinks the universe in the
direction gate 1g says the dead names concentrate.

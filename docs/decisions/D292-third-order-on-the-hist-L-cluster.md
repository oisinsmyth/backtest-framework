# D292 — third order on the `hist_L` cluster

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Stage 1 spends nothing scarce. Nothing is closed, nothing is promoted, and the
holdout is not read.**

---

## What licenses this study, stated exactly

D291 found **one** thing that survived a multiplicity-aware test: `hist_L` held
**6 of the 14** second-order survivors, and only **0.5%** of null draws produce
that much concentration in any candidate.

**That licenses "`hist_L` responds to gating". It does NOT license "these
partners are the good ones."** Among `hist_L`'s five gate-band partners the
ordering is nearly flat, and the survivor split is an artifact of where the
p = 0.05 line happens to fall:

| partner | ρ to `hist_L` | cells | best z | survivors |
|---|--:|--:|--:|--:|
| `rsi` | 0.617 | 4 | +2.27 | 2 |
| `macd_line` | 0.414 | 4 | +1.89 | 1 |
| `rev_5` | 0.415 | 4 | +1.69 | 2 |
| **`retrace_leg`** | 0.599 | 4 | **+1.55** | **0** |
| `macd_hist` | 0.636 | 4 | **+1.48** | 1 |

**`retrace_leg` produced no survivor and still out-scores `macd_hist`, which
produced one.** So this study uses **all five partners**, not the four that
survived. Selecting on the survivor split would be selecting on noise, and the
D291 amendment says so in as many words.

## The question

Second order asked: *does one filter add to `hist_L`?* Answer: `t` ≈ +1.0
typically, nothing promotable, but a real concentration.

Third order asks the next thing and only the next thing:

> **Does a SECOND filter add anything over the first?**

Not "does the stack beat `hist_L` alone" — D291 answered that. The control is
therefore **the parents**, not the primary.

## Construction

`A` = `hist_L`, fixed. **N = 25, k = 5**, inherited from its D290 spread peak
(spread `t` +2.86, open-entry `t` +2.30). Neither is re-swept.

Filters: all five gate-band partners → **C(5,2) = 10 pairs**.

**Two operators, declared because they ask different things:**

| | operator | why both |
|---|---|---|
| **AND** | keep names in the top **g = √f** of *both* B₁ and B₂ | conjunctive. `g = √f` so combined retention ≈ f — **the count is matched to second order rather than collapsing**, which is the N²/M failure that sank D288's probe |
| **MEAN-RANK** | average the two percentiles, keep the top **f** | compensatory: strong on one can carry mediocre on the other. Count is exact by construction |

**MEAN-RANK averages RANKS, not magnitudes**, so it remains selection and stays
inside stage 1's remit. The magnitude blend is still stage 3 and is not tested
here.

`f ∈ {0.90, 0.75, 0.50, 0.25}`.

**10 pairs × 2 operators × 4 fractions = 80 cells.**

## The statistic: it must add to BOTH parents

For a cell built from B₁ and B₂, the two parents are `hist_L` gated by B₁ alone
and by B₂ alone, **each rebuilt at the third-order cell's own surviving count**
so all three books are the same size.

```
per bar:    D1[t] = third_order[t] - parent_B1[t]
            D2[t] = third_order[t] - parent_B2[t]
statistic:  t_min = min( t(D1), t(D2) )
```

**The minimum, not the better of the two.** Picking the parent it beats would be
choosing the comparison after seeing it, and a stack that beats its weaker parent
while losing to its stronger one has added nothing.

## The null: rotate the ADDED filter, hold the other

Rotate B₂ within each name's own live bars — coverage, turnover and
autocorrelation preserved, alignment destroyed — while B₁ stays real. That asks
whether **B₂'s content** adds to B₁, rather than whether any second filter of
that shape would. Then symmetrically with B₁ rotated. **A cell must beat both
nulls**, 200 draws each.

## TWO BARS, DECLARED SEPARATELY — the D291 amendment applied

D291 pre-registered a single family-wise floor and then had to amend it, because
a floor that controls the chance of *any* false positive answers the wrong
question for a stage that makes no claim. Both bars are declared here, in
advance, with what each licenses:

| bar | threshold | what it licenses |
|---|---|---|
| **SCREEN** | the cell's own null p95, on both nulls | **carrying forward only.** Expected false positives are stated with the count, and a survivor is never described as a finding |
| **PROMOTION** | the **joint max-Z** floor at p95 over all 80 cells | a stage-2 candidate |

**Max-Z, not max-t.** D291's cells differed ~7× in the spread of their own
nulls, so a flat `t` floor demanded z ≈ +8 of a tight-null cell and z ≈ +1.5 of
a wide-null one. Standardise each cell by its own null first, then take the
per-draw maximum.

**Reported beside the screen count:** Benjamini-Hochberg at q = 0.10 and 0.20,
because the shortlist question is what fraction of what I carry is noise.

## THE AUDIT THAT RUNS BEFORE ANY NUMBER IS READ

D291's veto arm was scored and only then found to be void: the control churned
2.42× as hard as the treatment, and every statistic in it was measured on fresh
entries. **That audit runs first here, and its outcome is pre-committed:**

> For every cell, the control's fresh entries per bar must sit within
> **0.80–1.25×** the treatment's. **A cell outside that band is VOID and is
> reported as void, not as a result** — whichever way its number points.

Also reported, never gating: turnover per bar, mean holding run, dead-name share
per leg (1g), and where the peak sits in the sweep (1i). **Capturability
re-checked** at open entry (1e) for any cell clearing the screen.

---

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **Q1** | **No cell clears the PROMOTION floor.** Second order produced nothing promotable and the effect being chased is smaller, not larger | **AGAINST** | **high** |
| **Q2** | **Pairs containing `retrace_leg` do no worse than pairs of the four survivors.** The second-order survivor split was where p = 0.05 fell, not a real partner ordering | **AGAINST** | **moderate-high** |
| **Q3** | **MEAN-RANK beats AND.** Two correlated noisy reads of one thing are better combined compensatorily than conjunctively; AND discards a name for one weak read | for MEAN-RANK | moderate |
| **Q4** | **The dose-response runs the wrong way again** — `t_min` falls monotonically as `f` tightens, as it did at second order | **AGAINST** | moderate |
| **Q5** | **The control passes the turnover audit** (unlike D291's veto), because both treatment and parent are persistent selectors | for | high |

**Q2 is the load-bearing one, and it is against.** If pairs built on
`retrace_leg` perform like pairs built on `rsi`, then D291's partner-level
detail was noise and only the `hist_L`-level concentration was real. **That is
falsifiable and I expect it to fail.**

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed and not priced: **80 cells**, on top of D291's 272 and its four
post-hoc diagnostics, D290's 51, and D288's 31. The `hist_L` cluster was
selected on in-sample data, that selection is inherited by every cell here, and
**it is priced when the holdout is eventually read — not before.**

## Stop

**If no cell clears the SCREEN on both nulls, stacking filters is closed for
this pool** — no fourth order, no third operator, no widened partner set.

**If cells clear the SCREEN but none clears PROMOTION**, that is the same
outcome D291 had, and it licenses exactly one thing: carrying them, labelled as
unconfirmed, with the expected false count attached.

**Neither outcome closes:** the blend (stage 3, magnitude, different estimator);
`hist_L` itself, which is a tier-1 capturable candidate on its own merits and is
untouched by this; or the veto, still never validly tested.

## Not attempted here

Third order with a different primary — the D291 concentration finding is about
`hist_L` specifically and nothing licenses a general sweep. Partners outside the
ρ band. Any use of magnitude.

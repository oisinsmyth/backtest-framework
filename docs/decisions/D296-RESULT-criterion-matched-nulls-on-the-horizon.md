# D296 RESULT — criterion-matched nulls: the k=5 cell licenses only its `t`

**Status:** RESULT. Runs the null R14's fourth amendment (`eedc111`) demanded and
D294 explicitly left unpriced.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0. Programme total: 0.**

Work executed by a delegated agent; scripts `d296_criterion_matched_nulls.py`
and `d296_peak_resolution.py`, data in `data/d296_*.json`. Its caveats are
reproduced below in full rather than summarised away.

---

## Why this study exists

R14's fourth amendment: *"a grid-max null prices the search for max `t`;
selecting k on any other criterion is a different search over the same grid and
needs its own null."* D294 read D293's grid on gross and on cost coverage and
found different peaks. Those peaks were unpriced. This prices them.

## 1. The fine grid — gross maximises at k = 18

Grid refined to 24 horizons (D290's 12 ∪ [11, 26]), confluence at N = 25,
spread.

| k | gross bp | t | bp/bar | × mean | × robust | open t |
|--:|--:|--:|--:|--:|--:|--:|
| 3 | +44.04 | +3.45 | **+14.68** | 0.169 | 0.418 | +2.37 |
| **5** | +61.91 | **+3.80** | +12.38 | 0.238 | 0.588 | +2.96 |
| 13 | +84.84 | +3.38 | +6.53 | 0.325 | 0.805 | +2.71 |
| 16 | +85.45 | +3.23 | +5.34 | 0.328 | 0.811 | +2.55 |
| **18** | **+92.31** | +3.20 | +5.13 | **0.354** | **0.876** | +2.60 |
| 20 | +71.06 | +2.26 | +3.55 | 0.273 | 0.674 | +1.76 |

**The principal predicted `t` at k=5 and gross "at or slightly above 16–18".
Both hold: `t` peaks at 5, gross at 18.**

**A structural correction to the amendment.** At fixed N the round trip does not
depend on k, so **max gross and max cost coverage are the SAME argmax** — the
amendment's table implied three distinct searches and there are **two**. Cost
coverage differs from gross only in the *null*, because a null book holds
different names and therefore faces a different round trip. The agent's
assertion [8] verifies this: hold the round trip fixed and the cost-coverage z
collapses onto gross's exactly.

## 2. The criterion-matched nulls, 200 draws each

Same search space priced four times; grid max taken **on the criterion being
matched**; verdict is the worst of the three nulls.

| criterion | k | observed | binding null p95 | z | p | verdict |
|---|--:|--:|--:|--:|--:|:--|
| max **t** | 5 | +3.798 | +2.80 | **+2.61** | 0.005 | **CLEARS** |
| max **gross** | 18 | +92.31 | +78.8 | **+2.29** | 0.040 | **CLEARS, marginally** |
| max **× mean CS** | 18 | +0.3542 | **+0.3541** | +1.77 | 0.050 | **FAILS** |
| max **× robust CS** | 18 | +0.8761 | +0.935 | +1.66 | 0.075 | **FAILS** |

Rotation is the binding null on every criterion. Permutation is far the weakest
on gross and cost (z +14.0 / +7.6 / +6.4).

**D294's "cost coverage 1.38× better at k=16" does not survive its own null.**

**And the mechanism is measurable rather than inferred.** The null's round trip
is *cheaper* than the observed book's — robust p50: rotation **86.5**,
permutation **52.8**, observed **105.4**. The confluence holds names at roughly
twice the universe median half-spread, so a random book gets 1.2–2× the cost
coverage free, and that eats the observed margin.

## 3. THE FINDING: the k=5 cell licenses only its `t`

Value of each report at the k selected by each criterion, against a null running
the *same* selection:

| select by | k | report | observed | min z | worst p | verdict |
|---|--:|---|--:|--:|--:|:--|
| t | 5 | t | +3.798 | +2.61 | 0.005 | CLEARS |
| t | 5 | **gross** | +61.91 | **+1.36** | **0.090** | **fails** |
| t | 5 | **× robust** | +0.588 | +0.93 | 0.180 | **fails** |
| gross | 18 | t | +3.205 | +2.25 | 0.015 | CLEARS |
| gross | 18 | gross | +92.31 | +2.29 | 0.040 | CLEARS |
| gross | 18 | × robust | +0.876 | +1.66 | 0.075 | fails |

**Every gross and cost number quoted for the k=5 cell in D290, D293 and D294 is
unpriced.** Its `t` clears at p = 0.005; its gross (+61.91) and cost coverage
(0.588×) are indistinguishable from what the same `t`-maximising search produces
on null data. **A `t`-matched pricing licenses the `t` number and nothing else.**

**The reverse does not hold**: the gross peak's `t` (+3.205 at k=18) clears the
`t`-matched null at p = 0.015. **Moving to k=18 costs nothing on `t` and doubles
the null-passing margin on gross** — which, under R14's fourth amendment, is a
fact for the deployment decision rather than a new pick.

## 4. Caveats the agent flagged, reproduced not smoothed

**(a) The gross null is endpoint-dependent, and this is a limitation not a
footnote.** In 200 draws the null's argmax on gross lands modally at **k = 40**
for all three nulls: gross accumulates with k and so does its variance, so a max
over cells of unequal variance is a max over the longest horizon. The observed
search only landed at 18 because the observed long horizons turn negative
(k=40 = −40.2 bp). **Extend the grid to k=60 and the null gets harder; truncate
at 26 and it gets easier.** The `t` criterion is variance-normalised and does
not have this problem, so **"gross CLEARS at p=0.040" is endpoint-dependent in a
way the `t` verdict is not.**

**(b) The peak's LOCATION is not resolved.** Level SE is 28.8 bp; a paired test
cannot separate k=18 from **k=12–20** at 95%; a moving-block bootstrap (block 40,
2000 resamples) has k=18 winning only **51.4%** of resamples, k=13 21%, k=16 8%.
**Read it as "gross peaks somewhere in 13–19".** The edge-density peak is
likewise unresolved within k = 1–3 (k=2 observed, 28.9% of resamples).

**(c) The `t` null is not as decisive as D293's headline implies on this grid.**
One rotation draw of 200 exceeded the observed max (+3.806 vs +3.798) — p=0.005
is 1/200, not 0/200. R7's warning applies.

**(d) The profile is jagged in [21, 26]** (+30.7 / +45.5 / +30.7 / +34.3 / +29.7).
Adjacent horizons share nearly all their path, so a 15 bp oscillation there is
larger than sampling explains. Outside the plateau, does not affect the peak,
**unresolved.**

**(e) A round-trip inconsistency that moves no verdict.** Observed and the
rotation/permutation nulls measure cost over *membership* cells; the tail null
re-deals sides among pooled *fresh entries* and has no membership, so it uses
entry cells (observed robust: 105.4 membership, 113.1 entry; tail null p50
113.2, cost-matched by construction). The tail binds on no criterion.

**(f) z here is not comparable to D293's** — this grid fixes N=25 and spread,
where D293's grid-max also ranged over 5 N and 3 constructions.

## 5. What changes

**R14's fourth amendment is CORRECT and now has its null.** It said selecting k
on a non-`t` criterion needs its own null; run, the cost-coverage criterion
fails and the `t` criterion's gross claim fails. The amendment was not
pedantry — it was load-bearing.

**Every cost-coverage number in D290, D293, D294 and D295 inherits caveat (a)
and section 3.** They are descriptions of the observed book, not claims that
survive their own search.

**Nothing here changes the D293 verdict**, which rested on `t`, name-split CV
and open-entry capturability — all of which are `t`-shaped and correctly priced.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: 24 horizons × 4 criteria × 3 nulls × 200 draws, at fixed N=25 and
spread. Two distinct searches, not four — see §1.

## Discipline

The agent's runner carries D293's four assertions imported verbatim, plus four
of its own: the refined grid reproduces D290's 12 forward-return arrays
bit-identically and D294's published profile to <1e-9; the `tail_events` rewrite
and the vectorised rotation are bit-identical to what they replace; right-quantity
on the *added* horizons (fwd[11], fwd[16], fwd[26] each equal an independent
k-bar accumulation and differ from fwd[k−1]); and the fixed-round-trip identity
of §1. 200 draws × 3 nulls in 207 s on 8 threads.

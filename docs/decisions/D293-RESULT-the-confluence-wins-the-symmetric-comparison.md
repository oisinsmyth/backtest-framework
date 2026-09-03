# D293 RESULT — the confluence wins the symmetric comparison

**Status:** RESULT. Pre-registered at `49f8730`, corrected at `1e942ab`, runner
at `037a176`, all committed before this file existed (R8).
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0. Programme total: 0.**

---

## The result

**The confluence clears conditions 1–3 on the spread construction, and it beats
`hist_L` alone head-to-head on the same ladder. Q2 — the load-bearing
prediction, that the margin would not survive a symmetric comparison — is
FALSIFIED.**

### Conditions 1–3

| candidate | con | N | k | bp | t | rot z | perm z | tail z | **min z** | CV t | open t | kept | 1–3 |
|---|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|:--|
| **confluence** | **spread** | 25 | 5 | **+61.91** | **+3.80** | +2.58 | +2.86 | +3.23 | **+2.58** | **+1.35** | **+2.96** | 75% | **PASS** |
| `hist_L` | spread | 25 | 5 | +52.52 | +2.86 | +1.60 | +1.96 | +1.60 | +1.60 | +0.98 | +2.30 | 77% | PASS |
| confluence | long | 50 | 40 | +255.44 | +9.53 | −0.53 | **−16.55** | −0.61 | −16.55 | +10.76 | +8.09 | 83% | fail |
| `hist_L` | long | 50 | 40 | +245.98 | +9.09 | −1.61 | **−21.90** | −0.30 | −21.90 | +10.32 | +7.71 | 84% | fail |
| confluence | short | 3 | 3 | −6.88 | −0.10 | −0.99 | +1.55 | +0.64 | −0.99 | −0.84 | +1.46 | — | fail |
| `hist_L` | short | 3 | 10 | −19.75 | −0.25 | −1.28 | +1.95 | +0.60 | −1.28 | −1.22 | +0.61 | — | fail |

**The confluence is further from its nulls than its primary on every one:**
min z **+2.58 against +1.60**, CV **+1.35 against +0.98**, open-entry
**+2.96 against +2.30**.

### Condition 4 — head to head, same grid, same nulls

| construction | confluence | `hist_L` alone | winner |
|---|---|---|:--|
| **spread** | N=25 k=5 **+61.91** bp, t **+3.80** | N=25 k=5 +52.52 bp, t +2.86 | **confluence** |
| long | N=50 k=40 +255.44, t +9.53 | N=50 k=40 +245.98, t +9.09 | confluence (both fail) |
| short | N=3 k=3 −6.88, t −0.10 | N=3 k=10 −19.75, t −0.25 | confluence (both fail) |

**Both candidates peak at the SAME cell** — N=25, k=5. The grid maximum moved
neither, so the comparison is as clean as this design can make it: same grid,
same nulls, same code path, one flag apart. **The confluence wins condition 4.**

## The long book is market drift, again

`+255.44 bp` at `t +9.53` with a **permutation z of −16.55**. The long book is
beaten into the ground by a null that preserves each bar's cross-sectional
distribution and destroys only which name holds which score. That is D290's
finding — fifty of fifty-one long books were drift — reproducing exactly, and
it is why conditions 1–3 are applied per construction rather than to a headline.

## Predictions

| | prediction | outcome |
|---|---|---|
| **Q1** | the confluence clears 1–3 | **CONFIRMED** on spread (min z +2.58, CV +1.35, open t +2.96, 75% retained) |
| **Q2** | **it does NOT clear condition 4** | **FALSIFIED.** It wins on all three constructions, and both candidates peak at the same cell so the win is not a grid artifact |
| **Q3** | rotation is the binding null, not tail | **CONFIRMED** for the confluence (rot +2.58 is the minimum of +2.58/+2.86/+3.23) |
| **Q4** | the composite's peak N is not 25 | **FALSIFIED.** It peaks at N=25, k=5 — the same cell as its primary |
| **Q5** | cost still fails by more than 4× | **CONFIRMED under the mean** (0.238×, fails 4.2×), **not under the robust estimates** (~0.59×, fails 1.7×) — the same unresolved split as the correction |

**Three of five predictions wrong, and the two that mattered most.** I have now
predicted against this candidate at every stage — the N-stability test, the null
across N, and the symmetric head-to-head — and it has survived all three.

## Gate 1g, reported not gating

| | held | turnover | run | dead long | dead short | half mean | half median |
|---|--:|--:|--:|--:|--:|--:|--:|
| confluence | 19.0 | **19.4%** | **5.2** | 24.8% | 26.6% | 64.7 | 26.9 |
| `hist_L` | 25.0 | 14.1% | 7.1 | 26.4% | 28.6% | 69.4 | 28.4 |

**The confluence trades 37% more often**, which is the cost the extra selection
buys its edge with. Its holding run of 5.2 bars now **matches its k=5 horizon**,
where `hist_L`'s 7.1 overshot — a coherence the primary did not have.

Both peaks are **interior** (gate 1i). Era spread `t`: confluence **+2.52 /
+1.37 / +2.64** across pre-2020 / 2020 / post-2020, against `hist_L`'s
**+1.11 / +1.07 / +2.62** — the confluence is positive in all three eras and
materially stronger in the first.

## One disclosure about the nulls

`hist_L`'s tail z here is **+1.60** against D290's **+2.73** for the same
candidate. The tail null is implemented slightly differently: this file pools
the composite's **fresh entries** and re-deals the sides, where D290 pooled
**membership** and then took fresh entries. **Both candidates received the
identical treatment, so condition 4 is unaffected**, but the absolute z values
in this table are not directly comparable to D290's.

## What this establishes, and what it does not

**ESTABLISHED: the mechanism is real on this fixture.** Combining two partners
over a primary produces an effect that beats three nulls, generalises across
names, survives entry at the open, and beats the primary it filters on a
symmetric grid. That is the question four studies circled and it now has an
answer.

**NOT ESTABLISHED: that anything here is tradeable.** The candidate covers
between **0.238×** and **0.597×** of its measured round trip depending on how
Corwin–Schultz is aggregated, and 41.9% of held cells clamp to zero in that
estimator. **The cost question is unchanged and remains the binding one.**

**NOT ESTABLISHED: that it survives data it has never seen.** Everything
upstream was selected in-sample — `hist_L` from 51 candidates, the pair from 80
cells, `f` from 4 values. Under R14's amendment that selection is free *given*
a later clean read, and no clean read has happened. **Holdout reads: 0.**

## Stop

Per the pre-registration: passing all four conditions **establishes the
mechanism and does not make it tradeable. The next step is a cost question, not
a statistics question.**

Confluence is **not closed** — it is the first operator in this programme to
clear a symmetric test. Whether it goes further is a decision about the cost
estimate, which needs a spread source this fixture cannot provide.

## Ledger

| | |
|---|---:|
| **holdout reads spent** | **0** |
| holdout reads, whole programme | **0** |

Disclosed: 5 N × 12 k × 3 constructions = **180 cells per candidate, 360 total**,
priced by the same grid-max nulls D290 used on its 51.

## Files

`data/d293_candidate.json` · `scripts/run_d293_candidate.py` ·
`scripts/d293_cost_breakdown.py` · `data/d293_cost_breakdown.json`

# D290 — Stage 1 re-run: 51 candidates, three constructions, three nulls

**Status:** PRE-REGISTERED. Committed **before the runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-02
**Area:** Strategy research · **personal track**

---

## What this is, and what it is not

**A stage-1 re-run under [D289](D289-the-promotion-pipeline.md)'s ladder as
amended.** D288's numbers are **not carried as verdicts** — its gate A read as a
verdict and was in fact a triage decision under a criterion that has since been
withdrawn. Every candidate is re-evaluated from scratch.

**Stage 1 consumes nothing scarce, so nothing here is closed and nothing is
gated.** The output is a **ranking**, not a pass/fail. The holdout is not read.

**Confluence is OUT OF SCOPE for this run, by the principal's instruction.**
Combination work needs separate authorisation and is not attempted here.

## What changed since D288, and why each change

| change | why |
|---|---|
| **three constructions** — long-only, short-only, spread, each with its own null and cost bar | D288 reported both legs only *descriptively*. `hist_L` at N=25 k=25 was long +205.4, short +149.1 — the short leg **loses 149 bp**, which the +56.3 spread hides. The short-only column is the personal track's actual objective and nothing has ever evaluated it |
| **three nulls** per construction | rotation alone flatters any signal whose edge is a factor tilt — the D283/D284 failure |
| **t-based, not magnitude-based** | D289's amendment: stage 1 tests existence, not sufficiency |
| **name-split CV** as the ranking statistic | the holdout is a **disjoint name set**, so the free in-sample proxy for it is a name split, not a time split |
| **era split reported** | `FINDINGS.md` §6 records three sign inversions in a day and calls era-splitting reflexive. D288 never did it |
| **N swept to 3** | `FINDINGS.md` §9: *"the operative variable is not the instrument's listing status — it is how many you hold at once"* |
| **18 new candidates** | D288's list was chosen by code availability, not hypothesis quality |

---

## The 51 candidates

| axis | n | candidates |
|---|--:|---|
| **A** price | 7 | `hist_L` `md` `macd_line` `macd_hist` `trailing_return` `rsi` `impulse_nodz` |
| **B** intrabar shape | 7 | `upper_wick` `lower_wick` `wick_asym` `body_frac` `close_in_range` `range_frac` `gap_frac` |
| **C** volume structure | 5 | `rel_vol` `vol_z` `dollar_vol` `vol_trend` `signed_vol` |
| **D** volume profile | 4 | `dist_hvn` `dist_lvn` `mass_here` `mass_imbalance` |
| **E** range / volatility | 5 | `atr_norm` `cs_spread` `rvol21` `vol_ratio` `range_over_atr` |
| **F** overnight vs intraday | 5 | `on_mean` `id_mean` `on_share` `on_minus_id` `on_persist` |
| **G** documented anomalies | 10 | `max_ret_21` `ivol_21` `beta_63` `rev_5` `rev_21` `mom_252_21` `skew_63` `amihud_21` `price_log` `dist_52w_high` |
| **H** harvested instruments | 8 | `fvg_dist` `fvg_signed` `struct_trend` `retrace_leg` `choch_dist` `park_vol_21` `gk_minus_cc` `gap_reversal` |

`rsi` and `impulse_nodz` were built for D288 and **disclosed there as never
screened**. They are screened now. All 51 are unlagged; the book lags once.

Built and audited at `d641d68`. Three defects were caught during that build and
are recorded there — a **fixture-level look-ahead in `price_log`** that the
truncation audit structurally could not see, a **non-row-local market return**
that process chunking would have silently corrupted, and **frozen-tape ATR
blowups** in three H scores. All three are fixed with assertions that fire on
regression.

## The three constructions, each scored independently

1. **Long-only** — the N lowest. Net long, so it carries beta; the rotation null
   carries the same average exposure, which keeps that comparison honest.
2. **Short-only** — the N highest. **Pays borrow on top of the round trip.**
3. **Spread** — dollar-neutral. Removes the `−μ` drift term, which is why D285's
   factor-neutral produced the programme's first positive gross Sharpe.

**Cost bars differ and are not shared.** Round trip from D285's measured
Corwin–Schultz on the names actually **held** — 33.81 bp/side — recomputed here
for each construction's own held set rather than inherited.

**The short leg's null loses money.** A random short book pays the drift, so a
short candidate can post a positive z against a null that is itself losing.
`FINDINGS` R7's corollary logs **four cases of a losing random control at the
100th percentile**. Therefore: **for the short-only construction, z is reported
beside the absolute level, always, and z alone is never read as success.**

## The three nulls, all universal

| null | preserves | destroys | catches |
|---|---|---|---|
| **rotation** — per-symbol time shift within own live bars | turnover, autocorrelation, coverage | return alignment | signals whose timing adds nothing |
| **within-bar permutation** — shuffle the score across names inside a bar | cross-sectional dispersion, market regime | name alignment | signals that are not cross-sectional at all |
| **tail-randomised** — pool the 2N most extreme by the candidate's own score, assign sides at random | **the nuisance, by construction** | only the directional claim | factor tilts — the D283/D284 failure |

**The tail-randomised control needs no per-axis judgement**, which is why it is
preferred to declaring a nuisance per candidate: drawing from the candidate's
*own* extremes matches whatever it selects on automatically. It is D283's
instrument (`run_factor_neutral.neutral_book(..., tail=True)`), which measured a
tail tax of **−14.68/−9.80/−6.58 bp against a directional +4.75/+4.66/+3.60** —
a whole-universe control beaten by the tax alone.

One shared offset vector per draw across all candidates, so the draws are
comparable and the across-candidate max falls out of the same run.

## The ranking statistic

**Rank on `min(z_rotation, z_permutation, z_tail)` — the binding constraint —
computed on NAME-SPLIT CV, not pooled.** Declared now so there is no shopping for
the flattering null later.

Names are split by the same pinned permutation; select on half A, score on half
B, over re-randomised splits. **Pooled in-sample t is meaningless as a level**
once the search is unlimited; the name split is the free statistic that is not.

**The pattern across the three nulls is reported per candidate**, because each
failure names a different defect: beats rotation but not permutation → the edge
is *when* it fires, not *which names*, and for a cross-sectional book that is
disqualifying by construction; beats both but not tail-randomised → **the edge is
the factor tilt**.

Also reported, none of them gates: **era split** (pre-2020 / 2020 / post-2020),
**N ∈ {3, 5, 10, 25, 50}**, coverage in warm cells, and **z beside the raw
effect** — a z of 8 on a 6 bp effect and a z of 8 on a 90 bp effect rank
identically and are different animals.

---

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **P1** | `hist_L` reproduces D286's band (+25.6/+56.3/+28.3 bp, t +2.86) on the spread construction | neutral — *validity check; a miss makes the run VOID, not negative* | very high |
| **P2** | the name split **shrinks the top candidate's pooled t by ≥ 40%** | **against my own instrument** | moderate-high |
| **P3** | **NO candidate clears its floor on SHORT-ONLY** — the construction the personal track actually wants | **AGAINST** | **moderate-high** |
| **P4** | axis E and G's risk terms (`ivol_21`, `beta_63`, `max_ret_21`) **beat rotation and FAIL tail-randomised** — the D283/D284 signature | for the diagnostic, against the candidates | moderate-high |
| **P5** | at least one candidate clears on **spread** | for | moderate |
| **P6** | `close_in_range` replicates across the name split at ≥ 60% of its pooled t | for | moderate |

**P3 is load-bearing.** It says the short side remains unreachable even after
doubling the candidate count and adding the documented short-side anomalies.
**What falsifies it: any candidate whose short-only leg is negative in absolute
terms and clears its tail-randomised null at N ≤ 25.**

**P4 is the one I most expect to be right and most want to be wrong** — if the
risk terms survive the tail-randomised control, the tail tax is not the whole
story and D283's finding needs revisiting.

## Ledger, under D289's amended convention

**The ledger counts HOLDOUT READS, not in-sample looks.**

| | |
|---|---:|
| **holdout reads spent by this study** | **0** |
| holdout reads spent to date, whole programme | **0** |

In-sample looks are **disclosed, not priced**: 51 fresh; D288's 177; the 308
post-closure overlay and confluence probes. Selection on a fixture already spent
does not invalidate a later test on one never touched — it lowers the prior that
the survivor is real, which is a reason to be sceptical, not a bar to clear.

**Contamination ledger:** no primitive in this study has touched the holdout in
any form. Every one of the 51 remains holdout-eligible.

## Stop conditions

**Nothing is closed by this study.** A candidate that ranks badly is ranked
badly; stage 1 spends nothing, so there is nothing to protect by closing it.

What this study *can* conclude: **the ordering**, the null-failure pattern per
candidate, and the shortlist that would be worth carrying to stage 2 — which
requires the principal's decision, not this record's.

---

# AMENDMENT, 2026-09-02 — the ranking statistic, made affordable

**Made BEFORE the runner was written and before any number was produced.** The
original text is left standing.

## What was wrong with it

The record specified ranking on `min(z_rotation, z_permutation, z_tail)`
**computed on name-split CV**. Costed: the rotation and permutation nulls each
require a fresh column sort per draw (~1.5 s on a 1,573 x 4,187 panel), so
`51 candidates x 2 re-ranking nulls x 100 draws x K splits` is tens of hours.
The tail-randomised null is cheap — it reuses the observed ordering and
randomises only the side — but the other two dominate.

## What replaces it

**Two instruments, both kept, each answering the question it is good at:**

| | statistic | question | cost |
|---|---|---|---|
| **primary ranking** | **name-split CV**: pick the peak cell on half A, score that cell on half B, over K = 10 re-randomised splits; report the mean half-B `t` | *does it generalise to names it has not seen?* — the holdout's own structure | cheap |
| **diagnostic** | **min(z) across the three nulls**, on the full panel, 100 draws | *is it better than chance, given turnover, regime and its own factor tilt?* | ~35 min |

**A candidate is flagged INTERESTING only if it ranks high on half-B CV **and**
carries `min(z) > 0` across all three nulls.** Neither alone is sufficient: CV
without the nulls cannot tell a real effect from a nuisance tilt that also
generalises, and nulls without CV are measured on the sample that selected the
cell.

**The null-failure PATTERN is still reported per candidate**, unchanged — it is
the most diagnostic output of the study and costs nothing extra once the nulls
are run.

**Draws are 100, not 200.** D288 used 200 and the p95 was stable; 100 is
sufficient for a z and halves the run. Stated rather than quietly chosen.

**Nothing else changes** — three constructions, three nulls, era split,
N ∈ {3, 5, 10, 25, 50}, short-only z reported beside its absolute level, and
confluence still out of scope.

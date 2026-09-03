# D308 CORRECTION — the ceiling was less than noise, and N=2 is not always interior

**Status:** CORRECTION to `D308-RESULT-a-large-ceiling-that-nothing-can-reach.md`.
The record is not edited; this stands beside it.
**Date:** 2026-09-03
**Area:** Strategy research · **personal track**

**Holdout reads spent: 0.**

---

## 1. Stage 1 had no null, and it needed one

D308's pre-registration said *"Stage 1 has no null: an oracle is an upper bound by
construction."* **That is true of the oracle and false of the gain over static**,
which is the number the result reported as "+18.7 to +26.6 bp" and called
promising.

**With the null it should have had, the observed ceiling is BELOW what pure noise
produces, in all eight cells:**

| family | f | static | observed | null p50 | null p95 | p |
|---|--:|--:|--:|--:|--:|--:|
| none | 21 | +11.20 | +51.79 | +57.30 | +68.08 | 0.808 |
| none | 63 | +11.20 | +29.89 | +32.29 | +45.61 | 0.637 |
| target | 21 | +15.25 | +54.87 | +70.15 | +83.39 | 0.994 |
| target | 63 | +15.25 | +35.39 | +39.83 | +53.02 | 0.719 |
| none+overlay | 21 | +7.77 | +46.54 | +59.06 | +69.25 | 0.980 |
| none+overlay | 63 | +7.77 | +30.45 | +36.78 | +48.19 | 0.828 |
| target+overlay | 21 | +8.57 | +51.31 | +70.17 | +80.84 | 1.000 |
| target+overlay | 63 | +8.57 | +35.19 | +42.55 | +53.99 | 0.860 |

**Pure noise, with the same means, sds and cross-width correlations, produces
113% to 144% of the observed gain.** The ceiling is the Jensen gap of taking a
max over seven correlated noisy series, and the real data delivers slightly
*less* of it than a structureless draw.

**D308's closure stands. Its Stage 1 reading — "obviously promising" — does
not.**

## 2. It took three null constructions, and the failures are the lesson

| construction | why it failed |
|---|---|
| standardise per width, permute across widths within a block | preserves the marginals only **in expectation**; `[N1]` caught **364 bp** of mean drift on 51 blocks, larger than the effect being measured |
| two-way ANOVA, permute the width×block interaction down each column | `[N2]` caught **43.6% sd drift** — the block main effect is itself dominated by N=2's volatility, so the interaction is not orthogonal to it within a column |
| independent circular rotation per width | marginals exact, but it destroyed the **co-movement**: correlation 0.755 → −0.002, inflating the max-of-seven so much that every cell returned p = 1.0000 and the test was uninformative |
| **multivariate normal on the observed mean and covariance** | **means, sds and correlation (0.755 → 0.758) all preserved, no timing structure by construction** |

**The realisation that made the last one right, and it took two failures to see:
the oracle's gain over static does not depend on the temporal ORDER of blocks at
all.** It is a within-block cross-sectional max, so permuting rows changes
nothing. What generates it is that in some blocks a width other than the
static-best happens to win — which noise produces whenever there is
cross-sectional dispersion.

**Every null that destroyed order was answering a question the oracle never
asked.** The quantity to null was the Jensen gap of the joint distribution.

## 3. N=2 is interior for the no-exit families and NOT for the target families

D300 and D306 both found the optimum at N=2, the **smallest width ever tested**,
so it sat on the grid boundary and had never been shown to be interior. N=1 was
measured (`scripts/d309_n1_static.py`), with `held_per_bar` confirmed at exactly
2.000 and the N=2 cells reproducing D306 **bit-identically**:

| family | N=1 net | N=2 net | Δnet | N=1 Sharpe | N=2 Sharpe | ΔSharpe |
|---|--:|--:|--:|--:|--:|--:|
| none | −2.22 | +11.20 | **−13.42** | 0.350 | 0.770 | −0.420 |
| none+overlay | +2.42 | +7.83 | −5.40 | 0.389 | 0.617 | −0.228 |
| **target** | **+21.17** | +15.25 | **+5.92** | 0.626 | 0.754 | −0.128 |
| **target+overlay** | **+18.30** | +8.69 | **+9.61** | 0.562 | 0.562 | +0.001 |

**The no-exit families get clearly worse at N=1** — `none` turns net-negative and
its t-stat falls to 1.25 — so **N=2 is a genuine interior optimum there** and
D300's boundary worry is resolved for that arm.

**The target families do not.** `target` reaches **+21.17 net at N=1**, the
highest net figure in the programme.

**Three reasons not to celebrate it:**

- **Sharpe falls** — 0.754 → 0.626 — because volatility rises from 692 to 912 bp.
  The extra net is bought with risk, not edge.
- **The round trip drops from 73.2 to 62.2 bp**, so part of the gain is the same
  own-spread artefact D307 identified. Charged N=2's round trip instead, N=1's
  net is **+18.53**, and the advantage narrows from +5.92 to **+3.28**.
- **A two-position book** has maxDD 14,918, halved trade counts, and no
  diversification worth the name.

**And the boundary has simply moved**: N=1 is now the edge of the grid for the
target families, and there is nothing below it.

## What changes

- **D308's stop stands** — time-varying width is closed, now on a null rather
  than on a walk-forward that could not have succeeded.
- **The static optimum is family-dependent**: N=2 for the no-exit arms, N=1 or 2
  for the target arms with the choice turning on net-versus-Sharpe.
- **The walk-forward remains held**, as instructed. It was a bad test and it has
  not been rerun.

## Files

`data/d308c_ceiling_null.json` · `scripts/d308c_ceiling_null.py` ·
`data/d309_n1_static.json` · `scripts/d309_n1_static.py`

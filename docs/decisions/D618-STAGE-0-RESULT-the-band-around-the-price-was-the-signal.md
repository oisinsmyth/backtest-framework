# D618 STAGE 0 RESULT — nothing survives the construction screens, and the one thing that looked like it survived was the band

**Pre-registration:** [`D618`](D618-PRE-REG-the-sharpened-0DTE-ladder-range-or-independence.md), committed
before the runner existed, amended once (also before the runner) to carry its control set.
**Runner:** `scripts/stage0_d618_sharpened_ladder.py` · **artifact:** `data/stage0_d618_sharpened_ladder.json`
· 53.4 s · in-sample 2016-01-04 → 2023-12-29, 1,993 ES sessions, a 0DTE PM ladder on 1,263 of them,
267,676 (session, strike) cells. **No session at or after 2024-01-01 was read.**

## VERDICT

> **THE FAMILY IS DEGENERATE.** Of **72 cells**, **none** passes the four pre-registered construction
> screens, so **no return was scored for any cell in the specified family**. The line stays closed.

And the finding that matters more than the verdict:

> **The interior solution appeared, and it was the circularity.** On the runner's first pass the band was
> centred on **P1530** — which is the pre-registered *break*, not the specification — and four cells passed
> every screen, one of them clearing both its own nulls. Re-anchoring the band where the record says it
> belongs, on the **prior settlement**, takes those same cells from sd 0.62–1.04σ to 5.57–5.59σ, from
> corr(DAY0) −0.19/−0.21 to **−0.54**, and from 3.05–3.54× their flat-weight placebo to **1.00×**.
> Selecting the strike set around the current price manufactured *both* the independence and the apparent
> weight information. It is D614's grid artefact wearing a different coat.

## 1. The screens, which are the study

Applied to every cell before any return was read. The band is centred on the **prior settlement**, as the
record specifies.

| cell | sd (σ) | sd / flat placebo | corr(DAY0) | grid R² | strikes | fails |
|---|---:|---:|---:|---:|---:|---|
| `doi \| all \| w10` | **19.012** | 1.51 | −0.142 | 0.002 | 220 | S1b |
| `doi \| all \| w30` | **13.077** | 1.52 | −0.134 | 0.003 | 220 | S1b |
| `gamma_oi \| all \| w10 \| pre` | 5.713 | 0.24 | −0.536 | 0.005 | 220 | S1b, S2 |
| `gamma_doi \| all \| w10 \| pre` | 5.641 | 0.48 | −0.506 | 0.008 | 220 | S1b, S2 |
| `gamma_oi \| 3step \| w10 \| pre` | 5.590 | **1.00** | −0.543 | 0.007 | 6 | S1b, S2 |
| `gamma_oi \| 1step \| w10 \| pre` | 5.572 | 1.01 | −0.543 | 0.007 | 2 | S1b, S2, S4 |
| `vol_noon \| all \| w30` (D614's object) | 3.114 | 0.56 | −0.480 | 0.004 | 220 | S1b, S2 |

Three separate reasons nothing passes, and the third was not anticipated:

**The day's move, as expected.** Every gamma-weighted and volume-weighted cell anchored pre-session
carries corr(DAY0) between **−0.45 and −0.54**, against a ceiling of 0.40. D614's own conditioner sits in
the middle of that range at −0.480. The mechanism is the one the stress test named: a strike landscape
fixed before the session, differenced against the current price, *is* the day's return with a sign flip.

**The weights do nothing, which is new.** The flat-weight placebo — the unweighted centroid of the same
strikes the cell's weight is positive on — is as dispersed as the weighted centroid, or more so. Ratios run
**0.22 to 1.01** across the pre-session-anchored family. A ratio at 1.00 means the centroid's variation is
entirely *which strikes carry weight*, not *how much* they carry. The gamma kernel is under three strikes
wide at thirty minutes, so once the strike set is fixed the weights have almost nothing left to say.

**The ladder's extent — a third source of variance.** `doi|all` has enormous range (**sd 13.1σ on the
half-hour, 19.0σ on the ten minutes**) and is genuinely *independent* of the day's move (**−0.134**,
**−0.142**) with no grid sawtooth (R² 0.002–0.003). It falsifies prediction 1 on that prediction's literal
two-condition terms. But its flat-weight ratio is **1.52**, so the dispersion is the geometry of the listed
ladder — where open interest and its changes live, which is out in the tail puts, hundreds of points from
the price — and not a statement about position concentration. **S1b is the only screen that catches this,
and it was added as the "self-calibrating half" of a floor whose absolute half would have passed the cell
at thirteen sigma and called it signal.**

## 2. What the endogenous band did, measured

The pre-registered break, scored so the size of the illusion is on the record. It carries **no verdict
weight**; it is reported because the runner ran it first and because the difference is the paper's point.

| the same cell | band on the prior settle (the specification) | band on P1530 (the break) |
|---|---:|---:|
| `gamma_oi \| 3step \| w10 \| pre` sd | 5.590σ | **0.913σ** |
| …corr(DAY0) | **−0.543** | **−0.210** |
| …sd / flat placebo | **1.00** | **3.05** |
| `gamma_doi \| 3step \| w10 \| pre` sd / corr / ratio | 5.574σ / −0.542 / 1.00 | 1.040σ / −0.194 / 3.48 |
| cells passing all four screens | **0** | **4** |

The two bands are genuinely different objects: they select a different strike set on **90.7 %** of the
1,263 sessions, with a median Jaccard overlap of **0.333**. Centring on the current price is not a
refinement of centring on the settle; it throws away two thirds of the selection and replaces it with a
function of the day's return.

Scored anyway, with every null and bar (no verdict weight):

| artefact cell | c | NW t | shift-null rank | flip-null rank | expected move | clears $4.25? |
|---|---:|---:|---:|---:|---:|---|
| `gamma_oi \| 3step \| w10 \| pre` | −1.863 | −1.98 | **0.966, above p95** | **0.974, above p95** | $1.86 | no |
| `gamma_oi \| 3step \| w30 \| pre` | −2.838 | −1.03 | 0.881 | 0.731 | $1.90 | no |
| `gamma_doi \| 3step \| w10 \| pre` | −0.789 | −1.48 | 0.790 | 0.855 | $0.92 | no |
| `gamma_doi \| 3step \| w30 \| pre` | −0.575 | −0.41 | 0.353 | 0.297 | $0.45 | no |

**One artefact cell clears both of its own nulls.** That is what this study would have reported as a
candidate had the band anchor gone unchecked, and it is exactly why the multiplicity bar exists: on the
endogenous pass the **family maximum |t| was 2.336 against a family-max null p95 of 2.608** (rank 0.920),
while each cell's *own* p95 ran 1.93–2.04. Looking at four cells costs about 0.57 of t, and that gap alone
sinks it. The economic bar is not close either: the best expected move is **$1.90 against a $4.25 round
trip**, a factor of 2.2 short.

And the sign: **every coefficient is negative**, repulsion, where the mechanism predicts attraction.
Prediction 5 is falsified in the same direction as D614's.

## 3. The predictions, against what happened

| # | prediction | outcome |
|---|---|---|
| 1 | no cell has both range (sd ≥ 1.0σ) and independence (\|corr\| ≤ 0.40) | **falsified on its literal terms** by `doi\|all\|w30` and `doi\|all\|w10` — and both fail S1b, so the range is the ladder's extent. The prediction was right about the conclusion and wrong about there being only two sources of variance. |
| 2 | `\|gamma\|×\|Δoi\|` unbanded passes the measurement floor | **held** — sd **0.529σ**, corr **−0.048**. The stress test predicted ≈0.24σ; it is twice that. |
| 3 | every band of 2 steps or fewer fails S3 or S4 | **held, all 18 of them** — 2-step bands hold a median of 4 strikes against a floor of 5; 1-step bands hold 2, with grid R² 0.26–0.71. |
| 4 | Δ-OI is not independent of the conditioners already measured | **held** — corr **+0.523** with the OI-weighted centroid (the stress test said +0.659, measured on an unchecked delta) and **+0.335** with the volume centroid. |
| 5 | if a cell is scored the coefficient is positive | **falsified** — every coefficient is negative. |

## 4. The Δ-OI gate

The one improvement that addresses why D614 failed, and the gate it had to clear. The residualised
coefficient is **+0.0820** against **−0.0008** with those two controls removed — so the raw association is
nil and the two absorb offsetting parts. Nothing in either number is a signal, and the gate never had to
adjudicate "volume in disguise" because no Δ-OI cell reached scoring.

**D616's column earned its commit.** Of 12,594,319 option rows, **339,359 were refused because the two
`oi_ref_session` values were not adjacent**, against **31,589** refused by the session calendar alone — so
**ten times as many bad pairs were invisible** to the calendar and only the reference date could see them.
423,441 had no prior row at all; 11,799,930 deltas were admitted. The zero-delta share is **0.4850**, close
to the 0.428 the stress test measured, and against a revision rate under 2.5 % it confirms the zeros are
genuine "no position change" rather than staleness.

Settlement-implied vol inverted on **0.9809** of attempted rows, median **0.312**.

## 5. Corrections made inside the run, all of them

Nine. Four changed a number that would have been published, and one changed the verdict.

1. **The band anchor.** The runner first banded on P1530, the pre-registered *break*. Fixed to the prior
   settlement. **This changed the verdict** from "a cell clears both its nulls" to "no cell passes".
2. **The null comparison.** The shift null compared the **signed** observed coefficient against an
   **absolute** null, making every rank 0.000 by construction. Fixed to |obs| against |null|; the ranks
   moved to 0.353–0.966.
3. **The verdict logic** conflated "has range and independence" with "passes the screens", and so called a
   cell that fails the placebo floor a reason to go forward. Split into three separate questions.
4. **`vol_to_1530` is not D614's comparator.** The record's weight table names it as such; D614's object
   was the **noon** cutoff, which is why D613's panel exists. Both are carried, named apart, and the family
   is **72 cells, not the 64** the record counted.
5. **The record contains an internal tension** — §3 says a failing cell is not scored against returns, §7
   says the estimator ladder is reported for every cell. Resolved toward §3, since scoring a failing cell
   means reading the outcome the screens exist to protect.
6. **The additivity tolerance** is stated as 1e-12 in the record, which is log units; the runner works in
   basis points, so the equivalent bar is 1e-8 and the runner uses 1e-9. Measured deviation **2.9e-12 bp**.
7. **The right-quantity check** first required R10 ≠ R30 on over 99 % of sessions and fired on real data: a
   genuinely flat 15:30→15:50 leg makes them equal, which is a countable event, not a bug. Replaced by a
   declared ceiling on the coincidence share; an accidental `R10 = R30` takes it to 1.0 and fires.
8. **The permutation audit's break was wrong.** It asserted that flat weights should raise, when flat
   weights are legitimately skipped. The break that tests something is a *reduction that lost the pairing*
   (`centroid_unpaired`), which is permutation-invariant while returning a plausible number — the bug class
   a total cannot see. Flat weights now raise as a check that cannot fire (D613's lesson).
9. **A key-name error** read `se_ladder`'s OLS entry under the wrong key, and **the component line** is
   computed on the best artefact cell, labelled, because nothing in the specified family was scored and
   CLAUDE.md requires a component line for anything scored against returns.

## 6. The component line

Computed inside the runner on the **artefact** cell `gamma_oi|3step|w30|pre|ENDOGENOUS_BAND`, at one MES
and the cost that size pays ($4.25 a round trip), n 1,221. **It carries no verdict weight**; it is here
because it is the only construction any return was scored for, and because a construction scored against
returns gets a component line whatever it turns out to be.

| direction | gross Sharpe | gross Sortino | net Sharpe | net Sortino | gross $/session | net $/session | hit | payoff | skew | maxDD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| attraction | −0.034 | −0.046 | **−1.234** | **−1.714** | −$0.12 | −$4.37 | 0.486 | 1.011 | +1.15 | $5,398 |
| repulsion | +0.034 | +0.040 | **−1.166** | **−1.414** | +$0.12 | −$4.13 | 0.495 | 0.989 | −1.15 | $5,260 |

ρ with the admitted MACD day-session arm: **+0.055** over 1,162 overlapping sessions. Gross is
indistinguishable from zero in both directions, so this is not a cost failure — there is nothing for cost
to destroy. Drawdown convention: **positive dollars from peak** (D542).

## 7. What the six sharpenings bought

| # | change | what it did |
|---|---|---|
| 1 | gamma weight | removed the confound only by collapsing the range; `WEIGHTS BITE` **fired on it as the record predicted**, median \|K_w − P1530\| **1.355 points** against a 2.0-point floor |
| 2 | Δ open interest | the only change addressing the named defect; gave the family its one independent, wide conditioner — whose width is the **ladder's extent** (flat ratio 1.52), and whose association with the close is nil |
| 3 | near the money | every band of ≤2 steps fails on support or sawtooth, as predicted; the 3-step band only "worked" when centred on the current price, which is the artefact |
| 4 | ten minutes | sd(R10)/sd(R30) = **0.6584**, confirming the stress test's 0.659; no cell's statistic improved and the economics worsened |
| 5 | aggressor side | built as [D617](D617-FIXTURE-the-ES-option-signed-flow-census-from-the-tbbo-year.md)'s census, scored nothing; unsigned share **0.000166**, agreement **0.999983** |
| 6 | short straddle | not reached — no cell survived to be expressed, and the record's five infeasibility reasons stand unchanged |

## 8. What is spent, and what this closes

**Nothing was scored on the specified family, so the in-sample window was read for construction statistics
only** — dispersions, correlations, grid R², strike counts — plus returns for the four artefact cells,
which are disclosed above. The **ES day-session 2024+ slice stays unread**; D617's census window stays
unspent for every return-bearing construction.

**The axis of "signed distance from the price to a weighted strike" closes for ES 0DTE**, and it closes on
a construction argument rather than on a coefficient: the object's variance is the day's own move, or the
strike grid's relation to the current price, or the listed ladder's extent, and none of the three is a
statement about dealer positioning. Any future attempt on this axis has to name which of those three its
dispersion comes from and show it is none of them. Nothing here is pre-registered again without a fixture
that changes that arithmetic — per-strike dealer inventory, which no source on this disk carries.

The principal's six sharpenings are all measured. Two of them (the Δ-OI position weight and the aggressor
side) were the ones that addressed the real defect, and both are now data layers this repository has and
did not have before.

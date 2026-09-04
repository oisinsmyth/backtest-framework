# D315 — below the corner, and the rule the algebra derives

**Status:** PRE-REGISTERED. Committed **before either runner exists** (R8).
Nothing here is a result.
**Date:** 2026-09-04
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**

---

## 0. What D314 derived, and the two things it owes

[D314](D314-the-algebra-of-width.md) fitted three curves to sixteen published
widths and found:

```
vol(N)^2 = 2,396 + 1,201,745/N      rho = 0.0020,   so  vol = sigma/sqrt(N)
net(N)   = 5.96 - 2.38 ln N         edge dilutes 1.58x faster than cost falls
Sharpe   = sqrt(N) * net(N) / sigma
ln N*    = -n0/n1 - 2               =>  N* = 1.66,  BELOW the grid floor of 2
```

**Two claims are owed a test, and this record pre-registers both.**

**Stage A — the corner is below 2, and nothing has ever run there.** `N* = 1.66`
is an extrapolation outside the fitted range. It is checked by running the widths
directly.

**Stage B — the derived rule.** `ln N*(t) = −n0(t)/n1(t) − 2` has **no free
parameters**, and the whole question of whether width should vary reduces to how
often `−n0(t)/n1(t)` exceeds `ln 2 + 2 = 2.693`. It sits at **2.509**
full-sample.

**Stage A runs first and Stage B is conditional on it.** If the dilution curve
does not continue below 2, the derivation's extrapolation is wrong and Stage B is
built on a curve that does not exist.

---

# Stage A — below the corner

## A.1 The grid

`N_eff ∈ {1.0, 1.15, 1.3, 1.45, 1.6, 1.75, 1.9}` added below the existing floor,
with **2.0, 2.5, 3.0, 5.0 carried unchanged as anchors** so the new points are
continuous with the published surface.

`N_eff = 1.0` is one name per side and sits at `solve_lam`'s λ bound; it is
included as the extreme rather than as a candidate.

## A.2 Predictions — and the headline one is that this gains almost nothing

**D314's fit does not predict a meaningful improvement below 2. It predicts a
flat corner.** Evaluating `√N · net(N)` on the fitted curve:

| N_eff | 1.00 | 1.25 | 1.50 | **1.66** | 1.75 | 2.00 |
|---|--:|--:|--:|--:|--:|--:|
| fitted `√N·net` | 5.964 | 6.075 | 6.126 | **6.130** | 6.129 | 6.104 |

**The predicted gain from N\* over N=2 is 0.4%**, and the *measured* value at
N=2 (6.183) already exceeds the fitted optimum. **So the honest expectation is
that Stage A finds nothing worth having**, and that is stated before running it.

| | prediction |
|---|---|
| **QA1** | **net keeps rising monotonically below N_eff = 2**, reaching 5.5–6.5 bp/bar at N_eff = 1. *If net turns down, the dilution curve breaks and D314's extrapolation is wrong* |
| **QA2** | **net Sharpe peaks in [1.4, 2.0]** and the peak beats N=2 by **less than 5%**. *Against — this is the load-bearing prediction that the corner is FLAT and the whole axis is not worth more work* |
| **QA3** | **cost(N) breaks ABOVE its fitted line below N_eff = 2.** *Against.* At N_eff → 1 every rank change at the top swaps the whole book, so turnover should rise faster than `23.51 − 4.12 ln N` predicts. This is the most likely way the extrapolation fails |
| **QA4** | ρ stays statistically zero below 2 — refitting `vol² = a + b/N` on the extended grid leaves ρ under 0.01 and σ within 5% of 1,097 bp |
| **QA5** | **N_eff = 1.0 is NOT the best cell** on net Sharpe. If it is, the optimum is at the true boundary and the log-linear net curve is wrong, not merely extrapolated |
| **QA6** | the extended fit's `N*` lands within **±0.3** of D314's 1.66 |

## A.3 Statistics and null

**Net Sharpe primary, net bp/bar beside it**, gross and cost reported separately
so QA3 is readable. Full reporting groups 1 and 4; groups 2 and 3 inherited from
D310 as in D313.

**Null: the rank-rotation control of D300** — circular shift of rank assignment
within the gate, matched on count and persistence. **A concentrated book needs it
more than a wide one**, since at N_eff = 1 the book is one name and a null that
does not preserve persistence would be trivially beaten. 200 draws, BH-FDR at
q = 0.10 across the new cells.

## A.4 Assertions

1. **[A1]** the anchor levels 2.0, 2.5, 3.0, 5.0 reproduce D310/D312
   **bit-identically** — the extended grid must not disturb the published surface.
2. **[A2]** `N_eff` is achieved: `1/Σw²` equals each target to 1e-9, and the
   weight vector is monotone decreasing in rank.
3. **[A3]** turnover is recomputed, not inherited, and `cost = rt × turn` with the
   doubled form rejected against d295's 52.1893.
4. **[A4]** at `N_eff = 1.0` the book holds exactly one name per side to within
   1e-9 of weight, and its return equals the top-ranked name's spread return.
   **This is the check that the extreme is what it claims to be.**
5. **[A5]** every cell a distinct book.
6. **[A6]** the null matches on count and persistence, and **a deliberately
   broken book inside the mask raises**.

## A.5 Stop conditions

- **QA1 fails** → the dilution curve does not extend below 2; D314's `N*` is
  withdrawn as an extrapolation and **Stage B does not run**, since it fits the
  same curve.
- **QA2 confirms** (peak beats N=2 by <5%) → **the corner is real and flat, the
  width axis closes for a derived reason**, and Stage B runs only to price how
  often the optimum moves — not as a candidate strategy.
- **QA2 fails** (peak beats N=2 by >5% *and* survives its null) → there is a
  material width gain below the floor that six studies missed. It needs its own
  confirmation before anything else.
- **QA3 confirms strongly** (cost at N_eff = 1 more than 20% above its fitted
  line) → report the corrected `N*` from the broken-cost fit; that number, not
  1.66, is the derived optimum.

---

# Stage B — the derived rule, conditional on Stage A

## B.1 The rule, with no free parameters

At each bar, on a trailing 252-bar window using only data through `t−1`:

```
fit   net_j(window) = n0(t) + n1(t) * ln N_j     over the grid levels
then  ln N*(t) = -n0(t)/n1(t) - 2,   clipped to the grid
```

**252 bars is declared, not searched.** It matches D313's calibration window, and
no second window is tried; if 252 is wrong the rule fails and the record says so.

## B.2 Predictions

| | prediction |
|---|---|
| **QB1** | `−n0(t)/n1(t)` exceeds **2.693** on **fewer than 25%** of bars — the optimum is above N=2 only rarely. *Sets up QB2* |
| **QB2** | **the derived rule does not beat fixed N_eff = 2 on net Sharpe.** *Against — load-bearing* |
| **QB3** | the derived rule **beats D312's and D313's vol-targeted arms** at every target. *For the derivation* — if the algebra is right, keying on cost-to-opportunity should beat keying on σ(t) |
| **QB4** | the rule's `N*(t)` path is **less variable** than D313's arm B path (fewer changes, longer runs), because it keys on a slow-moving ratio |
| **QB5** | with the window set to the whole sample, the rule reproduces D314's `N* = 1.66` to ±0.05. *A harness check* |

## B.3 Null and statistics

**Circular rotation of the realised `N*(t)` path**, as in D312 and D313 — same
move count, sizes and persistence at unrelated times. 200 draws, net Sharpe and
net bp/bar, BH-FDR q = 0.10.

**QB2's bar is the one D313's Q3 got wrong:** "does not beat" here means **does
not beat while being profitable and surviving its own null.** A cell that beats
the baseline by losing less does not falsify QB2. That wording is fixed in
advance because D313's was not.

## B.4 Assertions

1. **[B1]** causality — `n0`, `n1` read only through `t−1`, and a peeking variant
   **must produce a different book**.
2. **[B2]** the full-sample window reproduces D314's fit coefficients exactly.
3. **[B3]** transitions charged from the weight vectors, zero on a constant path,
   monotone in |Δ log N_eff|.
4. **[B4]** the null matches move count and |Δ| distribution.
5. **[B5]** cost dimensions against d295's 52.1893, doubled form rejected.
6. **[B6]** a deliberately broken book inside the mask raises.

---

## Scope

**Out:** the entry signal; the exits; the gate; `k`; return-conditioned breadth
(closed three times); vol-conditioned breadth (closed by D312 and D313, and
explained by D314); and the combined B+E arm.

**`N_eff < 1` is not meaningful** and is not tested.

**Neither stage is a strategy proposal.** D314 predicts the corner is flat and
QA2 and QB2 both say so. **If both confirm, the width axis closes for a derived
reason rather than five empirical ones, and the entry signal — frozen since D293
— is what remains.**

## Files

`docs/decisions/D315-below-the-corner-and-the-derived-rule.md` (this record) ·
runners and data to follow, in separate commits. Prior evidence:
`data/d314_width_algebra.json`.

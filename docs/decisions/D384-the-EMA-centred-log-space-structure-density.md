# D384 — the EMA-centred log-space structure density: does it have shape a shuffle cannot produce?

**Date:** 2026-09-08
**Kind:** **STAGE-0 PREMISE CHECK.** Measures one property of a construction. **Scores no cell, tests no signal, admits nothing, reads no holdout.** A signal screen on this family, if it earns one, needs its own pre-registration.
**Pre-registered under R8 — committed before the runner exists. Result committed separately.**

---

## 0. The idea, and what is actually new in it

**The proposal (the principal's, 2026-09-08): build the price-structure density in a coordinate
centred on a moving average, in log space, so it is price-invariant and reads in percentages.**

**The density machinery already exists. The coordinate does not.** `VolumeProfileSensor` (S1) and
`SwingSupplyDemandSensor` (S5) both emit a `PriceDensity` over **absolute price buckets**, width
derived from ATR. Nothing in this repo has ever built one in a normalised, detrended coordinate.

**Three problems the coordinate change addresses, each of which the repo already complains about:**

1. **Cross-name comparability, currently impossible.** SPY at $600 and GDXJ at $25 have incomparable
   price grids, so densities cannot be pooled or ranked across names. In `log(P) − log(EMA)` both live
   on the same percentage axis.
2. **Staleness.** `ragged_profile.py`: *"Price moves several ATR in five weeks, so the distance would
   be measured in a stale unit against a stale node."* A node at $380 is meaningless once price is
   $600. **Centring detrends the coordinate by construction.**
3. **Cost.** `ragged_structure_scores.py` records S5 being dropped for runtime — *"0.17 ms × 4,137,239
   bars, i.e. ~12 minutes of pure-Python single-threaded work"* — because the profile is rebuilt from
   the last W bars **every bar**. §1's recursive form is **O(bandwidth) per bar**, which puts the
   richest sensor back within reach.

### And what this record does NOT assume

**The span census already ran** ([`data/d383_span_census.json`](../../data/d383_span_census.json),
commit `8ea8404`): median span **3**, single-bucket share **3.3%**, **0.000%** of densities degenerate.
**So the incumbent hard-bucket profile is NOT broken**, and the smudge below is an improvement rather
than a repair. Any gain is attributable to the method, and *"the buckets were degenerate"* is
explicitly **not** available as a motivation.

---

## 1. The construction, frozen

**The coordinate.** For price `P` and a single decay `λ`:

```
x_t  =  log(P_t) − log(EMA_λ(P)_t)
```

Approximately the percentage deviation from the EMA. Price-invariant and dimensionless.

**The density — exponentially weighted, kernel-smoothed, recursive:**

```
f_t(u)  =  λ · f_{t−1}(u)  +  (1 − λ) · K( u − x_t )
```

with `K` Gaussian. **EMA and density share the same `λ`, and that is the point rather than a
convenience:** if the density forgets exponentially and the centring forgets arithmetically, the two
objects carry different memory profiles and the coordinate's memory no longer matches the density's.
**One decay governs both**, which is what collapses three parameters (MA length, density lookback,
window shape) into one.

**The moving frame, and the exact fix for it.** `x_t` is measured from an origin that itself moves, so
mass accumulated at `t−1` sits in a stale frame and the recursion above is *not* literally correct.
**The density is held in its own frame and carried with a scalar offset**, shifted each bar by the
EMA's own log-change. Translating a density is an index shift, not a re-accumulation, so the
recursion and the stationarity both survive. `[FRAME]` proves it.

**The bandwidth is not a free parameter.** Silverman's rule on the trailing distribution of `x`,
recomputed on the same exponential weights. Declared, not swept.

### AMENDMENT to §1 and §2, 2026-09-08 — the additive term was under-defined, and the bandwidth should not have been fixed

*Written before the runner exists, so this is still a pre-registration under R8. Both paragraphs above
are left standing. Raised by the principal, and both points are theirs.*

#### (a) THE ADDITIVE TERM. §1 defines only the simplest member and calls it "the density"

The recursion above places **one unit of mass per bar at the close's deviation** — a *time* density,
how long price spent at each percentage from its EMA. **The proposal was a family**, and each member
is a different additive term. The general form, with the frame shift moved into the equation where it
belongs:

```
f_t(u)  =  λ · f_{t−1}(u + δ_t)  +  (1 − λ) · w̃_t · A(u ; c_t)
δ_t     =  log(EMA_t) − log(EMA_{t−1})
```

**A type is a (weight, location) pair.** `w̃_t` is *how much* mass the bar contributes; `A(u; c_t)` is
*where* it goes.

| type | weight `w_t` | location |
|---|---|---|
| **time** (the base case) | 1 | the close's deviation |
| volume profile | volume | **the bar's range** in deviation space |
| dollar volume | close × volume | range |
| swing low / swing high | 1 on a confirmed pivot (`k ∈ SWING_K`) | the pivot's deviation |
| N-bar lowest low / highest high | 1 when the bar is the extreme of N | that low/high's deviation |
| gap | 1 on a gap | the gap's span |
| wide-range | 1 above a range threshold | range |

**`w̃_t` is the weight NORMALISED per name** — `w_t` divided by its own exponentially-weighted mean.
Without this a high-volume name yields a "denser" density than a low-volume one and **§4.5's
comparability claim, which is the entire point of the coordinate, fails.**

**The range-spread and the kernel compose in closed form.** For a bar covering `[a, b]` in deviation
space with bandwidth `h`, the additive term is a uniform convolved with a Gaussian:

```
A(u) = [ Φ((u − a)/h) − Φ((u − b)/h) ] / (b − a)
```

Exact, no numerical convolution — **and as `b → a` it converges to the plain kernel `K(u − a)/h`.**
So the point-mass types are the degenerate case of the range-spread ones, **one code path covers the
whole family**, and `[REC]`/`[FRAME]` need proving only once.

**What this stage 0 actually tests is the base case — the time density, unit weight, point location.**
P1 asks whether the *coordinate* carries shape a shuffle cannot produce, and that question is cleanest
on the simplest member. **The family is enumerated here so that a later screen inherits it rather than
inventing it**: under [R14's addition](../RULES.md#r14) the choice of function is itself a free
parameter, so types picked after seeing this result would be fitted, and these are declared.

#### (b) THE BANDWIDTH SHOULD BE SWEPT, AND FIXING IT RISKS A FALSE NEGATIVE

§2 declares the bandwidth fixed and sweeps only `λ`. **That is the wrong call**, for a reason that
does not affect fairness but does affect what the study can see.

**If the smudge is too wide, the observed density and the null density both collapse into smooth
hills, the distance between them goes to nearly zero, and P1 fails — because of the bandwidth, not
because the market has no structure.** Too narrow and both are spiky and the distance is dominated by
sampling noise. The comparison stays *fair* at any bandwidth, since observed and null share it. **The
risk is blindness, not bias**, and a fixed bandwidth would leave it undetectable.

**Amended: bandwidth is swept as a multiplier on the Silverman baseline — {0.5×, 1×, 2×} — reported
and never picked**, and P2's shape reading applies to it as it does to `λ`. Three correlated points,
so the floor cost is close to nothing.

**And the baseline is floored at the bar's own resolution:**

```
h  =  max(  Silverman(σ_EW of x),  median bar range in deviation units  )
```

Both terms come from the data and neither is chosen. **The floor has a physical meaning: we do not
claim to resolve structure finer than a single bar can locate**, which is the same concern D194's span
census measures for the incumbent buckets.

---

## 2. Parameters — one swept, everything else declared or tied

| | | |
|---|---|---|
| **MA type** | **EMA** | **DECLARED.** Coherence with the density's own kernel (§1). A type is a discrete choice with no natural ordering, so a sweep of it would be unreadable — [R14's addition of 2026-09-08](../RULES.md#r14) |
| **density memory** | **= the EMA's `λ`** | **TIED.** Not an independent parameter |
| **bandwidth** | Silverman on the trailing `x` | **DECLARED**, canonical rule |
| **`λ`** | **half-life ∈ {5, 10, 20, 40, 80, 160} bars** | **SWEPT, six log-spaced, REPORTED AND NEVER PICKED.** The one knob, and the sweep is there to **read the shape** — monotone, hump, or knife-edge |

**Why `λ` is the honest one to sweep.** It is the only parameter that changes the coordinate itself,
and it is continuous, so its sweep produces a readable shape. Neighbouring half-lives are
near-duplicates, so the multiplicity cost is sublinear — measured in D382 at a **4% spread from p50 to
max across 38 correlated cells**.

**And it can be selected without ever touching returns.** §4 reports, for each `λ`, the **stationarity
of `x` itself** — autocorrelation half-life and variance stability across sub-periods. That is a
property of the coordinate, computed with no forward return and no strategy, and there is a genuine
optimum rather than a monotone: a fast EMA makes `x` very stationary and trivial, a slow one makes it
informative and non-stationary. **A return-blind criterion for a coordinate parameter is worth more
than a fitted one, and this record reports it whether or not it agrees with anything else.**

---

## 3. The null — and the load-bearing one keeps volatility clustering

**The premise this study exists to check: does the density have shape that the return distribution
alone cannot produce?**

**A density centred on its own EMA will peak at 0% no matter what**, because price spends most of its
time near its own moving average. That peak is arithmetic. Without a null, *"support at the mean"*
would be a guaranteed and worthless finding — and it is exactly the shape a reader would over-read.

| | what it destroys | what it keeps |
|---|---|---|
| **N1 — iid bootstrap of the name's own returns** | all serial structure, including volatility clustering | the return distribution exactly: volatility, skew, kurtosis |
| **N2 — iid bootstrap of STANDARDISED returns, re-scaled by the observed conditional volatility path** | **directional structure only** | the return distribution **and volatility clustering** |

**N2 is load-bearing.** Volatility clustering alone will bend the density — fat stretches spread mass
wider — so a difference against N1 is expected and proves little. **N2 is the null that isolates
directional structure**, and any claim rests on it. N1 is reported as the loose bound, the same
strict/loose pairing D380 used.

**Both nulls are per name**, resampling that name's own returns, so nothing is compared across
instruments with different distributions.

---

## 4. What is measured

**Primary:** the **total-variation distance** between the observed density `f_t` and the null's mean
density `g_t`, sampled over bars and pooled per name, per `λ`. Bounded in [0, 1] and interpretable.

**Reported beside it, and the third is the one that makes the result readable:**

1. **Mode count** of `f_t` — unimodal, or bimodal with price in a valley. A second mode is a claim
   about structure that a single distance cannot express.
2. **The excess-mass profile**: observed minus null mass as a function of `u`, so **where** the
   difference sits is visible rather than inferred. A bump at ±2% means something different from a
   sharper peak at 0%.
3. **The stationarity of `x`** per `λ` (§2) — autocorrelation half-life and cross-period variance
   ratio, computed **return-blind**.
4. **The span census analogue for the kernel form**, against the incumbent's committed median span 3 /
   3.3% single-bucket, so the smudge's effect on the degeneracy that D194 gates is *measured* rather
   than assumed away.
5. **Cross-name comparability, which is the coordinate's whole claim**: the dispersion of `x`'s
   distribution across the 551 names. If the coordinate works, per-name distributions of `x` should be
   far more alike than per-name distributions of absolute price ever are.

---

## 5. The decision rules

**This study admits nothing and scores no strategy. Its outcomes are verdicts on a premise.**

**P1 — is there shape a shuffle cannot produce?** Observed TV distance against **N2**'s distribution,
per `λ`. Cleared where the observed exceeds N2's p95 by more than 2 SE.

**P2 — is it a scale or an artefact?** The **shape of P1 across the six half-lives**. A smooth hump or
a monotone trend is a scale; **a single clearing half-life with neighbours inside the null is a
knife-edge and is reported UNRESOLVED, not as a result.**

**P3 — does the coordinate deliver comparability?** §4.5. If per-name `x` distributions are not
materially more alike than per-name price distributions, **the coordinate has not done the one thing
it was proposed for**, whatever P1 says.

**P4 — the return-blind λ.** Report the half-life that maximises §4.3's stationarity, and **whether it
agrees with P1's**. Agreement is corroboration from an independent criterion; disagreement is
recorded, not reconciled.

**If P1 fails at every half-life, the family is closed before a single feature is built.** That is the
point of running this first.

---

## 6. Assertions

| tag | what it proves |
|---|---|
| **`[FRAME]`** | the offset-carried recursion equals a **from-scratch** re-accumulation in the current frame, to a stated tolerance, on a sample of bars. The moving-origin fix of §1 is where this construction is most likely to be quietly wrong |
| **`[REC]`** | the recursive EW density equals a direct exponentially-weighted sum over the full history, to a stated tolerance — the analogue of D377's `[REC]`, which fired at 1e-3 and found a real specification error |
| **`[CAUSAL]`** | `f_t` and `x_t` read **no bar after `t`**, proved on a probe where a future bar is set to an extreme and neither may move |
| **`[NULL]`** | N2 reproduces the observed **volatility path** and the observed **return distribution** to stated tolerances, and destroys autocorrelation — a null that fails to keep what it claims to keep is not the null this record names |
| **`[SPLIT]`** | mining only; the reserved window is unreachable, default-deny, no override |
| **`[GATE]`** | an **explicit** `assert_gates_passed` call — D383's amendment found `load_panel` does not make one, and this record does not assume any loader does |
| **`[X]`** | every audit raises on a deliberately broken input, including a density that peeks forward and a null that has silently kept the return ordering |

---

## 7. Fixture, split, and search cost

**`data/fixtures/etf_wide_daily_raw.csv.gz`** — 551 names, 2,516 mined bars, gated `e22350a`.
**Daily first, and the reason is breadth, not validity:** the span census (`8ea8404`) removed the
15-minute objection, so frequency is now purely a question of how many names the comparability claim
(§4.5, P3) can be tested on — **551 against 57**. 15m is the natural successor and needs its own
record.

**Split unchanged from D382: mining → 2019-12-31, RESERVED 2020-01-01 onward, untouched.**

**This is a second look at a window D382 already mined.** Under the principal's ruling of 2026-09-07 a
brand-new construction may mine spent in-sample data provided nothing crosses into a holdout; the cost
is the **prior**, not validity. **Disclosed, and it is a real cost: the reserved window is what the
prior is spent against.**

**Search cost: one swept parameter over six correlated grid points, on a premise check that scores no
cell.** Under [R13](../RULES.md#r13) no strategy ledger is touched — there is no strategy.

---

## 8. Predictions

| | |
|---|---|
| **Q1** | **the observed density beats N1 at every half-life, and that proves nothing** — volatility clustering alone bends the shape. Recorded so a reader cannot mistake the loose bound for the result |
| **Q2** | **against N2 the margin is much smaller**, and I expect it to clear at the **long** half-lives (80, 160) and not the short ones: short-horizon deviation from a fast EMA is close to noise |
| **Q3** | **P2 shows a monotone trend in half-life, not a hump.** A hump would be the interesting outcome and a knife-edge the suspicious one |
| **Q4** | **P3 passes comfortably** — per-name `x` distributions far more alike than per-name price distributions. This is the coordinate's easiest claim and if it fails, the idea is wrong at the root |
| **Q5** | **the kernel form cuts the single-bucket share well below the incumbent's 3.3%**, and its span analogue exceeds 3 |
| **Q6** | **AGAINST myself: P4's return-blind optimum DISAGREES with P1's best half-life.** Two criteria selecting the same parameter for different reasons rarely agree, and if they do agree I will suspect I have fitted one to the other |
| **Q7** | `[FRAME]` and `[REC]` both hold on the first run. If `[FRAME]` fails, the moving-origin fix is wrong and §1 is wrong with it |

---

## 9. What would make me abandon this

- **`[FRAME]`, `[REC]` or `[CAUSAL]` fails** → the construction is not what §1 describes. Stop, fix,
  publish nothing.
- **`[NULL]` fails** → N2 does not preserve what it claims, so P1 is measuring the null's defect.
  Rebuild the null before reading any verdict.
- **P1 fails at every half-life** → the density carries no shape a volatility-matched shuffle cannot
  produce. **Close the family here, before any feature is built, and write it as the close.**
- **P3 fails** → the coordinate does not deliver comparability, which is the one thing it was proposed
  for. Report that plainly even if P1 clears; a structured density that is not comparable across names
  is not the object this record set out to build.

---

*Pre-registered 2026-09-08. Runner does not exist at the time of this commit (R8). Stage 0: it scores
no cell and admits nothing. The reserved window is guarded default-deny with no override.*
